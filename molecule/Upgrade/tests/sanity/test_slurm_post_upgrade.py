# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Slurm Upgrade Verification Test Cases.

Post-upgrade tests that validate the Slurm cluster state after the
``upgrade_slurm`` Ansible role has executed. These tests map directly
to the role's task files:

  Gate (run first):
    TC-09. Read oim_metadata + upgrade_manifest → decide skip / trigger / proceed
    TC-10. Trigger upgrade playbook if slurm not yet completed

  slurm_backup.yml:
    TC-11. Verify Slurm NFS share is mounted on OIM
    TC-12. Verify slurm.conf exists in NFS backup
    TC-13. Verify MySQL datadir exists in NFS backup
    TC-14. Verify HPC tools tracking files cleaned up

  check_slurm_cluster.yml:
    TC-15. Verify no active jobs on Slurm cluster
    TC-16. Verify all compute nodes are in idle state

  Post-upgrade service & job health:
    TC-17. Verify slurmctld active on control nodes
    TC-18. Verify slurmd active on compute nodes
    TC-19. Verify munge active on all Slurm nodes
    TC-20. Verify srun job succeeds post-upgrade
    TC-21. Verify sbatch job succeeds post-upgrade

  Post-upgrade job history verification:
    TC-22. Verify last job ID persisted after upgrade

  Post-upgrade uptime verification:
    TC-23. Verify Slurm nodes uptime is less than pre-upgrade baseline
"""

import json
import time
import pytest

from automation_library.core import TestLogger, run_in_container
from automation_library.upgrade_and_rollback.functions.slurm_upgrade_func import (
    check_slurm_upgrade_state,
    run_slurm_upgrade,
    verify_slurm_nfs_mount,
    verify_slurm_conf_backup,
    verify_mysql_datadir_backup,
    verify_hpc_tracking_cleanup,
    verify_no_running_jobs,
    verify_all_nodes_idle,
    verify_slurmctld_post_upgrade,
    verify_slurmd_post_upgrade,
    verify_munge_post_upgrade,
    verify_sbatch_post_upgrade,
    verify_srun_post_upgrade,
    _get_slurm_control_nodes,
)
from automation_library.core.functions.host_func import run_on_remote_node, get_nodes_info
from automation_library.upgrade_and_rollback.messages.slurm_upgrade_msgs import (
    SLURM_UPGRADE_TEST_NAMES as TEST_NAMES,
    SLURM_UPGRADE_LOG_MSGS as LOG,
    SLURM_UPGRADE_ASSERT_MSGS as ASSERT,
    SLURM_UPGRADE_SKIP_MSGS as SKIP,
)


# =============================================================================
# MODULE-LEVEL STATE
# =============================================================================
# _gate_passed controls whether downstream tests run at all.
_gate_passed: bool = False
# _nfs_mount_point is set by TC-11 and shared with TC-12, TC-13, TC-14.
_nfs_mount_point: str = ""
_nfs_check_passed: bool = False


# =============================================================================
# HELPERS
# =============================================================================

def _skip_if_gate_not_passed():
    """Skip test if the upgrade gate did not pass."""
    if not _gate_passed:
        pytest.skip(SKIP["gate_not_passed"])


def _skip_if_no_nfs():
    """Skip test if NFS mount check did not pass."""
    if not _nfs_check_passed:
        pytest.skip(SKIP["nfs_not_configured"])


# =============================================================================
# TC-09: UPGRADE GATE — CHECK METADATA + MANIFEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_upgrade_gate(host):
    """
    Test Case 09: Read oim_metadata.yml and upgrade_manifest.yml to determine
    whether to skip, trigger, or proceed with Slurm upgrade verification.

    Logic:
      1. Read oim_metadata.yml → check for previous_omnia_version
         - If not set: not an upgrade scenario → SKIP all tests
      2. Read upgrade_manifest.yml → check component_status.slurm
         - If "completed": proceed with verification tests
         - If "skipped": skip all tests
         - If "pending" or "in-progress": trigger upgrade (TC-10)
      3. If manifest missing: upgrade not initiated → SKIP all tests
    """
    global _gate_passed

    log = TestLogger(TEST_NAMES["upgrade_gate"])
    log.check(LOG["reading_metadata"])

    gate_result = check_slurm_upgrade_state(host)

    if not gate_result["success"]:
        log.failed(gate_result["message"], gate_result.get("error", ""))
        pytest.fail(
            ASSERT["metadata_read_failed"].format(
                error=gate_result.get("error", ""),
            )
        )

    if gate_result["should_skip"]:
        reason = ""
        if not gate_result["is_upgrade"]:
            reason = SKIP["not_upgrade"]
        elif gate_result["slurm_status"] == "skipped":
            reason = SKIP["slurm_skipped"]
        elif not gate_result.get("manifest_found"):
            reason = SKIP["manifest_missing"]
        else:
            reason = SKIP["gate_not_passed"]

        log.passed(gate_result["message"])
        pytest.skip(reason)

    if gate_result["needs_upgrade"]:
        log.passed(gate_result["message"])
        log.check(LOG["triggering_upgrade"])
        return

    _gate_passed = True
    log.passed(gate_result["message"])


# =============================================================================
# TC-10: RUN SLURM UPGRADE PLAYBOOK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
@pytest.mark.skip(reason="Slurm upgrade playbook trigger skipped for manual execution")
def test_run_slurm_upgrade(host):
    """
    Test Case 10: Trigger the Slurm upgrade playbook if needed.

    This test runs only if TC-09 determined that slurm is in "pending" or
    "in-progress" state. It executes ``ansible-playbook upgrade.yml --tags slurm``
    inside the omnia_core container and polls for completion.

    Currently skipped; upgrade is expected to be run outside the test framework.
    """
    global _gate_passed

    gate_result = check_slurm_upgrade_state(host)

    if not gate_result["needs_upgrade"]:
        pytest.skip("Slurm upgrade not needed (already completed or skipped)")

    log = TestLogger(TEST_NAMES["run_slurm_upgrade"])
    log.check(LOG["triggering_upgrade"])

    def progress_callback(elapsed):
        log.check(LOG["upgrade_running"].format(elapsed=elapsed))

    upgrade_result = run_slurm_upgrade(host, progress_callback=progress_callback)

    if upgrade_result["success"]:
        log.passed(LOG["upgrade_completed"].format(rc=upgrade_result["rc"]))
        _gate_passed = True
    else:
        log.failed(upgrade_result["error"], upgrade_result.get("output", ""))
        if "timeout" in upgrade_result["error"].lower():
            pytest.fail(
                ASSERT["upgrade_timeout"].format(
                    timeout=3600,
                )
            )
        else:
            pytest.fail(
                ASSERT["upgrade_playbook_failed"].format(
                    rc=upgrade_result["rc"],
                    output=upgrade_result.get("output", "")[:500],
                )
            )


# =============================================================================
# TC-11: VERIFY SLURM NFS MOUNT
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_slurm_nfs_mount(host):
    """
    Test Case 11: Verify the Slurm NFS share is mounted on OIM.

    Reads omnia_config.yml for slurm_cluster nfs_storage_name,
    resolves mount_point from storage_config.yml, and checks it is mounted.
    """
    _skip_if_gate_not_passed()

    global _nfs_mount_point, _nfs_check_passed

    log = TestLogger(TEST_NAMES["nfs_mount"])
    log.check(LOG["checking_nfs"])

    result = verify_slurm_nfs_mount(host)

    if result.get("mount_point"):
        print(f"    Mount point: {result['mount_point']}", flush=True)
    if result.get("source"):
        print(f"    Source: {result['source']}", flush=True)

    if result["success"]:
        _nfs_mount_point = result["mount_point"]
        _nfs_check_passed = True
        log.passed(result["message"])
    else:
        log.failed(result["message"], result.get("error", ""))
        if "config" in result.get("error", "").lower():
            pytest.fail(
                ASSERT["nfs_config_error"].format(error=result["error"])
            )
        else:
            pytest.fail(ASSERT["nfs_not_mounted"])


# =============================================================================
# TC-12: VERIFY SLURM.CONF BACKUP IN NFS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(12)
def test_slurm_conf_backup(host):
    """
    Test Case 12: Verify slurm.conf exists in the control node's NFS backup.

    Checks {nfs_mount}/slurm/{ctld_hostname}/etc/slurm/slurm.conf.
    """
    _skip_if_gate_not_passed()
    _skip_if_no_nfs()

    log = TestLogger(TEST_NAMES["slurm_conf_backup"])

    result = verify_slurm_conf_backup(host, _nfs_mount_point)

    if result.get("ctld_hostname"):
        print(f"    Control node: {result['ctld_hostname']}", flush=True)
    if result.get("path"):
        log.check(LOG["checking_slurm_conf"].format(path=result["path"]))

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"], result.get("error", ""))
        if "directory not found" in result.get("error", ""):
            pytest.fail(
                ASSERT["ctld_dir_missing"].format(
                    path=result.get("path", ""),
                    nfs_mount=_nfs_mount_point,
                )
            )
        else:
            pytest.fail(
                ASSERT["slurm_conf_missing"].format(
                    path=result.get("path", ""),
                )
            )


# =============================================================================
# TC-13: VERIFY MYSQL DATADIR BACKUP IN NFS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(13)
def test_mysql_datadir_backup(host):
    """
    Test Case 13: Verify MySQL datadir exists in NFS backup.

    Checks for ibdata1 or mysql/ system database directory.
    """
    _skip_if_gate_not_passed()
    _skip_if_no_nfs()

    log = TestLogger(TEST_NAMES["mysql_datadir_backup"])

    result = verify_mysql_datadir_backup(host, _nfs_mount_point)

    if result.get("path"):
        log.check(LOG["checking_mysql"].format(path=result["path"]))
    print(
        f"    ibdata1: {result.get('ibdata_exists', False)}, "
        f"mysql/: {result.get('mysql_db_exists', False)}",
        flush=True,
    )

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"], result.get("error", ""))
        pytest.fail(
            ASSERT["mysql_missing"].format(path=result.get("path", ""))
        )


# =============================================================================
# TC-14: VERIFY HPC TOOLS TRACKING FILES CLEANED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(14)
def test_hpc_tracking_cleanup(host):
    """
    Test Case 14: Verify HPC tools tracking files were removed during upgrade.

    The upgrade_slurm role removes .done_cuda and cuda/bin/nvcc tracking files.
    """
    _skip_if_gate_not_passed()
    _skip_if_no_nfs()

    log = TestLogger(TEST_NAMES["hpc_tracking_cleanup"])
    log.check(LOG["checking_hpc_tracking"])

    result = verify_hpc_tracking_cleanup(host, _nfs_mount_point)

    if result["success"]:
        log.passed(result["message"])
    else:
        for f in result.get("remaining_files", []):
            print(f"    Still present: {f}", flush=True)
        log.failed(result["message"], result.get("error", ""))
        pytest.fail(
            ASSERT["hpc_tracking_present"].format(
                files=", ".join(result.get("remaining_files", [])),
                mount_point=_nfs_mount_point,
            )
        )


# =============================================================================
# TC-15: VERIFY NO RUNNING JOBS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(15)
def test_no_running_jobs(host):
    """
    Test Case 15: Verify no active jobs are running on the Slurm cluster.

    The upgrade_slurm role aborts if jobs are running; this test confirms
    the cluster is quiesced post-upgrade.
    """
    _skip_if_gate_not_passed()

    log = TestLogger(TEST_NAMES["no_running_jobs"])
    log.check(LOG["checking_running_jobs"])

    result = verify_no_running_jobs(host)

    if result.get("job_count", -1) >= 0:
        print(f"    Running jobs: {result['job_count']}", flush=True)

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"], result.get("error", ""))
        if result.get("job_count", -1) > 0:
            pytest.fail(
                ASSERT["running_jobs"].format(count=result["job_count"])
            )
        else:
            pytest.fail(
                ASSERT["squeue_failed"].format(error=result.get("error", ""))
            )


# =============================================================================
# TC-16: VERIFY ALL COMPUTE NODES IDLE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(16)
def test_all_nodes_idle(host):
    """
    Test Case 16: Verify all Slurm compute nodes are in idle state.

    The upgrade_slurm role requires all nodes idle before proceeding.
    """
    _skip_if_gate_not_passed()

    log = TestLogger(TEST_NAMES["all_nodes_idle"])
    log.check(LOG["checking_idle"])

    result = verify_all_nodes_idle(host)

    # Log per-node state details
    for detail in result.get("details", []):
        state_str = detail.get("state", "unknown")
        print(
            f"    {detail['hostname']}: {state_str}",
            flush=True,
        )

    if result["success"]:
        log.passed(result["message"])
    else:
        non_idle = result.get("non_idle_nodes", [])
        log.failed(result["message"], result.get("error", ""))
        if non_idle:
            pytest.fail(
                ASSERT["non_idle_nodes"].format(
                    count=len(non_idle),
                    nodes=", ".join(non_idle),
                )
            )
        elif "sinfo failed" in result.get("error", ""):
            pytest.fail(
                ASSERT["sinfo_failed"].format(error=result.get("error", ""))
            )
        else:
            pytest.fail(
                ASSERT["no_compute_nodes"]
            )


# =============================================================================
# TC-17: VERIFY SLURMCTLD ACTIVE POST-UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(17)
def test_slurmctld_active_post_upgrade(host):
    """
    Test Case 17: Verify slurmctld service is active on control nodes
    after upgrade.
    """
    _skip_if_gate_not_passed()

    log = TestLogger(TEST_NAMES["slurmctld_active"])
    log.check("Checking slurmctld service on control nodes")

    result = verify_slurmctld_post_upgrade(host)

    for detail in result.get("details", []):
        status = "active" if detail["active"] else "NOT active"
        log.check(LOG["checking_service"].format(
            service="slurmctld",
            hostname=detail["hostname"],
            ip=detail["admin_ip"],
        ))
        print(
            f"    {detail['hostname']}: slurmctld {status} [{detail['output']}]",
            flush=True,
        )

    if result["success"]:
        log.passed(result["message"])
    else:
        failed = [d["hostname"] for d in result.get("details", []) if not d["active"]]
        log.failed(result["message"], result.get("error", ""))
        pytest.fail(
            ASSERT["slurmctld_inactive"].format(nodes=", ".join(failed))
        )


# =============================================================================
# TC-18: VERIFY SLURMD ACTIVE POST-UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(18)
def test_slurmd_active_post_upgrade(host):
    """
    Test Case 18: Verify slurmd service is active on compute nodes
    after upgrade.
    """
    _skip_if_gate_not_passed()

    log = TestLogger(TEST_NAMES["slurmd_active"])
    log.check("Checking slurmd service on compute nodes")

    result = verify_slurmd_post_upgrade(host)

    for detail in result.get("details", []):
        status = "active" if detail["active"] else "NOT active"
        print(
            f"    {detail['hostname']}: slurmd {status} [{detail['output']}]",
            flush=True,
        )

    if result["success"]:
        log.passed(result["message"])
    else:
        failed = [d["hostname"] for d in result.get("details", []) if not d["active"]]
        log.failed(result["message"], result.get("error", ""))
        pytest.fail(
            ASSERT["slurmd_inactive"].format(nodes=", ".join(failed))
        )


# =============================================================================
# TC-19: VERIFY MUNGE ACTIVE POST-UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(19)
def test_munge_active_post_upgrade(host):
    """
    Test Case 19: Verify munge service is active on all Slurm nodes
    (control + compute) after upgrade.
    """
    _skip_if_gate_not_passed()

    log = TestLogger(TEST_NAMES["munge_active"])
    log.check("Checking munge service on all Slurm nodes")

    result = verify_munge_post_upgrade(host)

    for detail in result.get("details", []):
        status = "active" if detail["active"] else "NOT active"
        print(
            f"    {detail['hostname']}: munge {status} [{detail['output']}]",
            flush=True,
        )

    if result["success"]:
        log.passed(result["message"])
    else:
        failed = [d["hostname"] for d in result.get("details", []) if not d["active"]]
        log.failed(result["message"], result.get("error", ""))
        pytest.fail(
            ASSERT["munge_inactive"].format(nodes=", ".join(failed))
        )


# =============================================================================
# TC-20: VERIFY SRUN JOB POST-UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(20)
def test_srun_post_upgrade(host):
    """
    Test Case 20: Verify srun job completes successfully from the control
    node after upgrade.
    """
    _skip_if_gate_not_passed()

    log = TestLogger(TEST_NAMES["srun_post_upgrade"])
    log.check(LOG["submitting_srun"])

    result = verify_srun_post_upgrade(host)

    if result.get("output"):
        print(f"    Output: {result['output']}", flush=True)
    if result.get("num_nodes"):
        print(f"    Nodes: {result['num_nodes']}", flush=True)

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"], result.get("error", ""))
        pytest.fail(
            ASSERT["srun_failed"].format(error=result.get("error", ""))
        )


# =============================================================================
# TC-21: VERIFY SBATCH JOB POST-UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(21)
def test_sbatch_post_upgrade(host):
    """
    Test Case 21: Verify sbatch job submits and completes from the control
    node after upgrade. Confirms the scheduler is fully operational.
    """
    _skip_if_gate_not_passed()

    log = TestLogger(TEST_NAMES["sbatch_post_upgrade"])
    log.check(LOG["submitting_sbatch"])

    result = verify_sbatch_post_upgrade(host)

    if result.get("job_id"):
        print(
            f"    Job ID: {result['job_id']} | State: {result.get('job_state', '')}",
            flush=True,
        )

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"], result.get("error", ""))
        pytest.fail(
            ASSERT["sbatch_failed"].format(error=result.get("error", ""))
        )


# =============================================================================
# TC-22: VERIFY LAST JOB ID PERSISTED AFTER UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(22)
def test_verify_last_job_id_post_upgrade(host):
    """
    Test Case 22: Verify the last job ID from pre-upgrade is still accessible
    after upgrade.

    Reads /tmp/slurm_pre_upgrade_baseline.json (created by TC-01 in
    test_slurm_pre_upgrade.py) and verifies that the last job ID captured
    before upgrade is still present in the Slurm accounting database after
    the upgrade completes.
    """
    _skip_if_gate_not_passed()

    log = TestLogger("Verify last job ID persisted post-upgrade")
    log.check("Verifying Slurm job history preserved during upgrade")

    # Load pre-upgrade baseline from host filesystem
    baseline_file_path = "/tmp/slurm_pre_upgrade_baseline.json"

    try:
        with open(baseline_file_path, "r") as f:
            baseline_data = json.load(f)
        last_job_id = baseline_data.get("last_job_id")
    except FileNotFoundError:
        log.failed(
            "Pre-upgrade baseline not found",
            f"Could not read {baseline_file_path}",
        )
        pytest.skip(
            "Pre-upgrade baseline not available — skipping job ID verification"
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        log.failed("Invalid baseline data", str(exc))
        pytest.fail(f"Failed to parse baseline: {exc}")

    if not last_job_id:
        log.passed("No job ID to verify (no jobs existed before upgrade)")
        pytest.skip("No pre-upgrade job ID captured — skipping verification")

    print(f"    Pre-upgrade last job ID: {last_job_id}", flush=True)

    # Get control node to query sacct
    control_nodes = _get_slurm_control_nodes(host)
    if not control_nodes:
        log.failed("No control node found", "Cannot query job accounting")
        pytest.fail("No slurm control node found for job verification")

    control_ip = control_nodes[0].get("admin_ip", "")
    control_hostname = control_nodes[0].get("hostname", "unknown")

    print(f"    Querying control node: {control_hostname} ({control_ip})", flush=True)

    # Query sacct for the specific job ID
    sacct_cmd = f"sacct -n -X -j {last_job_id} --format=JobID,State,ExitCode 2>&1"

    try:
        sacct_result = run_on_remote_node(host, sacct_cmd, control_ip)
    except RuntimeError as exc:
        log.failed("SSH connection failed", str(exc))
        pytest.fail(f"Cannot connect to control node: {exc}")

    if sacct_result.rc != 0:
        log.failed(
            f"Job ID {last_job_id} not found after upgrade",
            sacct_result.stderr,
        )
        pytest.fail(
            f"Job accounting query failed for job {last_job_id}: {sacct_result.stderr}"
        )

    job_info = sacct_result.stdout.strip()
    if not job_info:
        log.failed(
            f"Job ID {last_job_id} not found in accounting database",
            "Job history may not have been preserved during upgrade",
        )
        pytest.fail(
            f"Job ID {last_job_id} not found in Slurm accounting database after upgrade"
        )

    print(f"    Job found: {job_info}", flush=True)
    log.passed(
        f"Job ID {last_job_id} successfully verified in accounting database after upgrade"
    )


# =============================================================================
# TC-23: VERIFY SLURM NODES UPTIME IS LESS THAN PRE-UPGRADE BASELINE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(23)
def test_slurm_nodes_uptime_post_upgrade(host):
    """
    Test Case 23: Verify Slurm nodes uptime is less than pre-upgrade baseline.

    Compares node uptime against the baseline captured in test_slurm_pre_upgrade.py.
    This verifies that nodes were rebooted during the upgrade process.

    Reads /tmp/slurm_pre_upgrade_baseline.json (created by TC-01 in
    test_slurm_pre_upgrade.py) and checks that all Slurm nodes have uptime
    less than the time elapsed since the baseline was captured.
    """
    _skip_if_gate_not_passed()

    log = TestLogger("Verify Slurm nodes uptime post-upgrade")
    log.check("Verifying Slurm nodes were rebooted during upgrade")

    # Load pre-upgrade baseline from host filesystem
    baseline_file_path = "/tmp/slurm_pre_upgrade_baseline.json"

    try:
        with open(baseline_file_path, "r") as f:
            baseline_data = json.load(f)
        baseline_timestamp = baseline_data.get("oim_timestamp")
        baseline_compute_nodes = baseline_data.get("slurm_state", {}).get("nodes", [])
        baseline_control_nodes = baseline_data.get("control_nodes", [])
        baseline_login_nodes = baseline_data.get("login_nodes", [])
    except FileNotFoundError:
        log.failed(
            "Pre-upgrade baseline not found",
            f"Could not read {baseline_file_path}",
        )
        pytest.skip(
            "Pre-upgrade baseline not available — skipping uptime verification"
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        log.failed("Invalid baseline data", str(exc))
        pytest.fail(f"Failed to parse baseline: {exc}")

    if not baseline_timestamp:
        log.failed("No baseline timestamp", "baseline data missing oim_timestamp")
        pytest.fail("Baseline timestamp not found")

    # Get current time from pytest host machine (same source as baseline)
    current_timestamp = int(time.time())
    time_elapsed = current_timestamp - baseline_timestamp

    print(
        f"    Baseline timestamp (pytest host): {baseline_timestamp}",
        flush=True,
    )
    print(
        f"    Current timestamp (pytest host): {current_timestamp}",
        flush=True,
    )
    print(
        f"    Time elapsed since baseline: {time_elapsed} seconds ({time_elapsed // 60} minutes)",
        flush=True,
    )

    # Prepare all nodes to check: compute, control, and login nodes
    all_nodes_to_check = []
    
    # Add compute nodes from slurm_state
    for node in baseline_compute_nodes:
        all_nodes_to_check.append({
            "hostname": node.get("hostname", ""),
            "admin_ip": None,  # Will look up
            "type": "compute"
        })
    
    # Add control nodes
    for node in baseline_control_nodes:
        all_nodes_to_check.append({
            "hostname": node.get("hostname", ""),
            "admin_ip": node.get("admin_ip", ""),
            "type": "control"
        })
    
    # Add login nodes
    for node in baseline_login_nodes:
        all_nodes_to_check.append({
            "hostname": node.get("hostname", ""),
            "admin_ip": node.get("admin_ip", ""),
            "type": "login"
        })
    
    print(
        f"    Total nodes to check: {len(all_nodes_to_check)} "
        f"(compute: {len(baseline_compute_nodes)}, "
        f"control: {len(baseline_control_nodes)}, "
        f"login: {len(baseline_login_nodes)})",
        flush=True,
    )

    # Check each node's uptime
    failed_nodes = []
    passed_nodes = []

    for node_info in all_nodes_to_check:
        hostname = node_info.get("hostname", "")
        admin_ip = node_info.get("admin_ip", "")
        node_type = node_info.get("type", "unknown")
        
        if not hostname:
            continue

        # Get admin IP if not already available (for compute nodes)
        if not admin_ip:
            try:
                node_lookup = get_nodes_info(host, search_by="hostname", search_value=hostname)
                if not node_lookup:
                    print(f"    {hostname} ({node_type}): Could not find node info", flush=True)
                    continue

                admin_ip = node_lookup[0].get("admin_ip", "")
                if not admin_ip:
                    print(f"    {hostname} ({node_type}): No admin IP found", flush=True)
                    continue
            except Exception as exc:
                print(f"    {hostname} ({node_type}): Error looking up node: {exc}", flush=True)
                continue

        # Get node uptime in seconds
        node_uptime_cmd = "cat /proc/uptime"
        try:
            node_uptime_result = run_on_remote_node(host, node_uptime_cmd, admin_ip)
        except RuntimeError:
            print(f"    {hostname} ({node_type}): SSH connection failed", flush=True)
            failed_nodes.append((hostname, "SSH connection failed"))
            continue
        
        if node_uptime_result.rc != 0:
            print(
                f"    {hostname} ({node_type}): Failed to get uptime ({node_uptime_result.stderr})",
                flush=True,
            )
            failed_nodes.append((hostname, node_uptime_result.stderr))
            continue

        try:
            node_uptime = int(float(node_uptime_result.stdout.split()[0]))
        except (ValueError, IndexError):
            print(
                f"    {hostname} ({node_type}): Invalid uptime format ({node_uptime_result.stdout})",
                flush=True,
            )
            failed_nodes.append((hostname, "Invalid uptime format"))
            continue

        # Verify uptime is less than elapsed time
        if node_uptime < time_elapsed:
            passed_nodes.append((hostname, node_uptime))
            print(
                f"    {hostname} ({node_type}): uptime {node_uptime}s < elapsed {time_elapsed}s ✓",
                flush=True,
            )
        else:
            failed_nodes.append(
                (hostname, f"uptime {node_uptime}s >= elapsed {time_elapsed}s")
            )
            print(
                f"    {hostname} ({node_type}): uptime {node_uptime}s >= elapsed {time_elapsed}s ✗",
                flush=True,
            )

    # Report results
    if not failed_nodes:
        message = (
            f"All {len(passed_nodes)} Slurm nodes were rebooted "
            f"(uptime < {time_elapsed}s)"
        )
        log.passed(message)
    else:
        message = (
            f"{len(passed_nodes)} nodes passed, {len(failed_nodes)} nodes failed: "
            f"{', '.join([n[0] for n in failed_nodes])}"
        )
        log.failed(message, "Some nodes were not rebooted or uptime check failed")
        pytest.fail(message)
