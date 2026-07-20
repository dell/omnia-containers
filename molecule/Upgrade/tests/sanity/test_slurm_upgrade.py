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
"""

import pytest

from automation_library.core import TestLogger
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
)
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
def test_run_slurm_upgrade(host):
    """
    Test Case 10: Trigger the Slurm upgrade playbook if needed.

    This test runs only if TC-09 determined that slurm is in "pending" or
    "in-progress" state. It executes ``ansible-playbook upgrade.yml --tags slurm``
    inside the omnia_core container and polls for completion.
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
