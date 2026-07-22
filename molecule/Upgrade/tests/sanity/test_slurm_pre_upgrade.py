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
Slurm Pre-Upgrade Test Cases.

Pre-upgrade tests that capture and verify Slurm cluster state before upgrade.
These tests run before the upgrade gate and capture baseline metrics for
post-upgrade comparison.

Test Cases:
  TC-01. Capture OIM system time and Slurm cluster state before upgrade
  TC-02. Verify Slurm cluster is healthy before upgrade
"""

import json
import pytest

from automation_library.core import TestLogger, run_in_container, load_container_file
from automation_library.core.functions.host_func import run_on_remote_node
from automation_library.upgrade_and_rollback.functions.slurm_upgrade_func import (
    verify_slurm_pre_upgrade,
    capture_slurm_pre_upgrade_state,
    save_slurm_pre_upgrade_state,
    _get_slurm_control_nodes,
    _get_slurm_compute_nodes,
)
from automation_library.upgrade_and_rollback.vars.slurm_upgrade_vars import (
    UPGRADE_MANIFEST_PATH,
)
from automation_library.upgrade_and_rollback.messages.slurm_upgrade_msgs import (
    SLURM_UPGRADE_TEST_NAMES as TEST_NAMES,
    SLURM_UPGRADE_LOG_MSGS as LOG,
)

# Module-level state for pre-upgrade baseline
_pre_upgrade_baseline = {
    "oim_timestamp": None,
    "slurm_state": None,
    "baseline_saved": False,
}


# =============================================================================
# TC-01: CAPTURE OIM TIME AND SLURM STATE BEFORE UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_capture_oim_time_and_slurm_state(host):
    """
    Test Case 01: Capture OIM system time and Slurm cluster state before upgrade.

    Verifies:
      - upgrade_manifest.yml component_status.slurm is NOT "completed"
        (FAIL if completed, PASS otherwise)
      - Slurm node uptimes are less than the time difference between
        start and end OIM timestamps

    Captures:
      - Current OIM system time (for uptime comparison post-upgrade)
      - Running jobs (job IDs, states, users, nodes)
      - Node states (hostnames, states, CPUs, memory)
      - Service status (slurmctld, slurmd, munge)
      - Slurm version
      - Cluster configuration

    Saves baseline to /tmp/slurm_pre_upgrade_baseline.json for post-upgrade
    uptime verification.
    """
    global _pre_upgrade_baseline

    log = TestLogger(TEST_NAMES["pre_upgrade_capture"])
    log.check(LOG["capturing_pre_upgrade"])

    # Check upgrade_manifest.yml - fail if slurm status is "completed"
    log.check("Checking upgrade_manifest.yml for slurm status")
    manifest = load_container_file(host, UPGRADE_MANIFEST_PATH)
    
    if manifest:
        component_status = manifest.get("component_status", {})
        slurm_status = component_status.get("slurm", "pending")
        print(f"    Slurm status in manifest: {slurm_status}", flush=True)
        
        if slurm_status == "completed":
            log.failed(
                "Slurm upgrade already completed",
                f"component_status.slurm is '{slurm_status}' - pre-upgrade test should run before upgrade"
            )
            pytest.fail(
                f"Pre-upgrade test failed: Slurm upgrade status is '{slurm_status}'. "
                "This test must run BEFORE the upgrade completes."
            )
        else:
            log.passed(f"Slurm status is '{slurm_status}' (not completed)")
    else:
        print("    upgrade_manifest.yml not found (acceptable for pre-upgrade)", flush=True)

    # Get initial OIM system time
    time_result = run_in_container(host, "date +%s")
    if time_result.rc != 0:
        log.failed("Failed to capture OIM system time", time_result.stderr)
        pytest.fail(f"Could not get OIM time: {time_result.stderr}")

    try:
        oim_timestamp_start = int(time_result.stdout.strip())
    except ValueError:
        log.failed("Invalid OIM timestamp", time_result.stdout)
        pytest.fail(f"Invalid timestamp format: {time_result.stdout}")

    _pre_upgrade_baseline["oim_timestamp"] = oim_timestamp_start

    # Capture Slurm state
    capture_result = capture_slurm_pre_upgrade_state(host)

    if not capture_result["success"]:
        log.failed(capture_result["message"], capture_result.get("error", ""))
        pytest.fail(
            f"Failed to capture pre-upgrade state: {capture_result.get('error', '')}"
        )

    state = capture_result.get("state", {})
    _pre_upgrade_baseline["slurm_state"] = state

    print(
        f"    OIM Timestamp (start): {oim_timestamp_start}",
        flush=True,
    )
    print(
        f"    Jobs: {len(state.get('jobs', []))}, "
        f"Nodes: {len(state.get('nodes', []))}, "
        f"Version: {state.get('slurm_version', 'unknown')}",
        flush=True,
    )

    if state.get("jobs"):
        print("    Running jobs:", flush=True)
        for job in state["jobs"]:
            print(
                f"      - JobID: {job['job_id']} | State: {job['state']} | "
                f"User: {job['user']} | Nodes: {job['nodes']}",
                flush=True,
            )

    if state.get("services"):
        print("    Services:", flush=True)
        for service, status in state["services"].items():
            print(f"      - {service}: {status}", flush=True)

    # Get end OIM system time for uptime verification
    time_result_end = run_in_container(host, "date +%s")
    if time_result_end.rc != 0:
        log.failed("Failed to capture end OIM system time", time_result_end.stderr)
        pytest.fail(f"Could not get end OIM time: {time_result_end.stderr}")

    try:
        oim_timestamp_end = int(time_result_end.stdout.strip())
    except ValueError:
        log.failed("Invalid end OIM timestamp", time_result_end.stdout)
        pytest.fail(f"Invalid end timestamp format: {time_result_end.stdout}")

    time_elapsed = oim_timestamp_end - oim_timestamp_start
    print(
        f"    OIM Timestamp (end): {oim_timestamp_end}",
        flush=True,
    )
    print(
        f"    Time elapsed during capture: {time_elapsed} seconds",
        flush=True,
    )

    # Verify Slurm node uptimes are less than time_elapsed
    log.check("Verifying Slurm node uptimes")
    
    control_nodes = _get_slurm_control_nodes(host)
    compute_nodes = _get_slurm_compute_nodes(host)
    all_slurm_nodes = control_nodes + compute_nodes
    
    failed_nodes = []
    passed_nodes = []
    
    for node in all_slurm_nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")
        
        if not hostname or not admin_ip:
            continue
        
        # Get node uptime in seconds
        node_uptime_cmd = "cat /proc/uptime | awk '{print int($1)}'"
        try:
            node_uptime_result = run_on_remote_node(host, node_uptime_cmd, admin_ip)
        except RuntimeError:
            print(f"    {hostname}: SSH connection failed", flush=True)
            failed_nodes.append((hostname, "SSH connection failed"))
            continue
        
        if node_uptime_result.rc != 0:
            print(
                f"    {hostname}: Failed to get uptime ({node_uptime_result.stderr})",
                flush=True,
            )
            failed_nodes.append((hostname, node_uptime_result.stderr))
            continue
        
        try:
            node_uptime = int(node_uptime_result.stdout.strip())
        except ValueError:
            print(
                f"    {hostname}: Invalid uptime format ({node_uptime_result.stdout})",
                flush=True,
            )
            failed_nodes.append((hostname, "Invalid uptime format"))
            continue
        
        # Verify uptime is less than elapsed time
        if node_uptime < time_elapsed:
            passed_nodes.append((hostname, node_uptime))
            print(
                f"    {hostname}: uptime {node_uptime}s < elapsed {time_elapsed}s ✓",
                flush=True,
            )
        else:
            failed_nodes.append(
                (hostname, f"uptime {node_uptime}s >= elapsed {time_elapsed}s")
            )
            print(
                f"    {hostname}: uptime {node_uptime}s >= elapsed {time_elapsed}s ✗",
                flush=True,
            )
    
    # Fail if any nodes have uptime >= elapsed time
    if failed_nodes:
        error_msg = (
            f"Node uptime verification failed: {len(failed_nodes)} node(s) have "
            f"uptime >= {time_elapsed}s or failed checks: "
            f"{', '.join([n[0] for n in failed_nodes])}"
        )
        log.failed("Node uptime check failed", error_msg)
        pytest.fail(error_msg)
    
    log.passed(
        f"All {len(passed_nodes)} Slurm node(s) have uptime < {time_elapsed}s"
    )

    # Save baseline with timestamp on host filesystem (where pytest runs)
    baseline_data = {
        "oim_timestamp": oim_timestamp_start,
        "slurm_state": state,
    }

    baseline_file_path = "/tmp/slurm_pre_upgrade_baseline.json"

    try:
        with open(baseline_file_path, "w") as f:
            json.dump(baseline_data, f, indent=2)

        _pre_upgrade_baseline["baseline_saved"] = True
        log.passed(
            LOG["state_saved"].format(file_path=baseline_file_path)
        )

    except Exception as exc:
        log.failed("Error saving baseline", str(exc))
        pytest.fail(f"Error saving baseline: {exc}")


# =============================================================================
# TC-02: VERIFY SLURM CLUSTER HEALTH BEFORE UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_slurm_pre_upgrade_verify(host):
    """
    Test Case 02: Verify Slurm cluster is healthy before upgrade.

    Checks:
      - Slurm control node is reachable
      - slurmctld service is active
      - All compute nodes are in idle state
      - No running jobs
    """
    log = TestLogger(TEST_NAMES["pre_upgrade_verify"])
    log.check(LOG["verifying_pre_upgrade"])

    result = verify_slurm_pre_upgrade(host)

    if result.get("control_node"):
        print(
            f"    Control node: {result['control_node'].get('hostname')} "
            f"({result['control_node'].get('admin_ip')})",
            flush=True,
        )
    if result.get("compute_nodes"):
        print(f"    Compute nodes: {len(result['compute_nodes'])}", flush=True)
        for node in result["compute_nodes"]:
            print(
                f"      - {node['hostname']}: {node['state']} "
                f"({'idle' if node['idle'] else 'NOT idle'})",
                flush=True,
            )

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"], result.get("error", ""))
        pytest.fail(result.get("error", "Slurm cluster not ready for upgrade"))
