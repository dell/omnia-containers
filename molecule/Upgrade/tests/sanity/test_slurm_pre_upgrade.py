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
import time
import pytest

from automation_library.core import TestLogger, run_in_container, load_container_file, get_nodes_info, get_functional_groups_from_pxe_mapping
from automation_library.upgrade_and_rollback.functions.slurm_upgrade_func import (
    verify_slurm_pre_upgrade,
    capture_slurm_pre_upgrade_state,
    save_slurm_pre_upgrade_state,
    _get_slurm_control_nodes,
)
from automation_library.upgrade_and_rollback.vars.slurm_upgrade_vars import (
    UPGRADE_MANIFEST_PATH,
)
from automation_library.slurm.vars.slurm_vars import (
    LOGIN_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
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
    Test Case 01: Capture timestamp and Slurm cluster state before upgrade.

    Verifies:
      - upgrade_manifest.yml component_status.slurm is NOT "completed"
        (FAIL if completed, PASS otherwise)

    Captures:
      - Pytest host machine timestamp (for uptime comparison post-upgrade)
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

    # Get timestamp from pytest host machine (not container)
    host_timestamp = int(time.time())
    _pre_upgrade_baseline["oim_timestamp"] = host_timestamp

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
        f"    Pytest host timestamp: {host_timestamp}",
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

    # Gather slurm control nodes
    log.check("Gathering slurm control nodes")
    control_nodes = _get_slurm_control_nodes(host)
    control_nodes_list = [
        {
            "hostname": node.get("hostname", ""),
            "admin_ip": node.get("admin_ip", ""),
            "functional_group": node.get("functional_group", "")
        }
        for node in control_nodes
    ]
    print(f"    Slurm control nodes: {len(control_nodes_list)}", flush=True)
    for node in control_nodes_list:
        print(f"      - {node['hostname']} ({node['admin_ip']})", flush=True)

    # Gather login nodes (both login_node and login_compiler_node)
    log.check("Gathering login nodes")
    all_groups = get_functional_groups_from_pxe_mapping(host)
    login_nodes = []
    
    for fg in all_groups:
        if LOGIN_NODE_FUNCTIONAL_GROUP in fg or LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP in fg:
            fg_nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
            login_nodes.extend(fg_nodes)
    
    login_nodes_list = [
        {
            "hostname": node.get("hostname", ""),
            "admin_ip": node.get("admin_ip", ""),
            "functional_group": node.get("functional_group", "")
        }
        for node in login_nodes
    ]
    print(f"    Login nodes: {len(login_nodes_list)}", flush=True)
    for node in login_nodes_list:
        print(f"      - {node['hostname']} ({node['admin_ip']})", flush=True)

    # Save baseline with timestamp on host filesystem (where pytest runs)
    baseline_data = {
        "oim_timestamp": host_timestamp,
        "slurm_state": state,
        "control_nodes": control_nodes_list,
        "login_nodes": login_nodes_list,
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
