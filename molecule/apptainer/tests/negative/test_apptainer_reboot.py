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

"""Apptainer negative (reboot) test cases for OMNIA (MD-928).

TC29 - NFS mount and SIF files accessible after compute node reboot
TC30 - Apptainer container job runs successfully after node reboot
TC31 - download_container_image.sh works correctly after node reboot
"""

import os
import sys
import time

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../.."),
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
from automation_library.core import TestLogger
from automation_library.apptainer.functions.apptainer_func import (
    get_slurm_nodes,
    get_slurm_control_nodes,
    verify_nfs_and_sif_accessible_after_reboot,
    verify_container_execution_post_reboot,
    verify_download_script_works_after_reboot,
    _safe_run,
)
from automation_library.apptainer.vars.apptainer_vars import (
    REBOOT_WAIT_ONLINE_TIMEOUT,
    REBOOT_WAIT_ONLINE_POLL_INTERVAL,
    REBOOT_POST_SETTLE_DELAY,
)

# =============================================================================
# Module-level state – tracks which nodes were rebooted so TC30/TC31 can
# operate on the same nodes that TC29 rebooted.
# =============================================================================
_REBOOTED_NODES: list = []


# =============================================================================
# REBOOT HELPER
# =============================================================================

def _reboot_node_and_wait(host, node: dict) -> dict:
    """Issue 'reboot' on the node and poll until it comes back online.

    Returns a dict with keys: hostname, admin_ip, rebooted, online, error.
    """
    hostname = node.get("hostname", "unknown")
    admin_ip = node.get("admin_ip", "")

    if not admin_ip:
        return {"hostname": hostname, "admin_ip": admin_ip,
                "rebooted": False, "online": False, "error": "No admin IP"}

    reboot_cmd = _safe_run(host, "nohup reboot -f &", admin_ip)
    if reboot_cmd.rc not in (0, 255):
        return {"hostname": hostname, "admin_ip": admin_ip,
                "rebooted": False, "online": False,
                "error": f"Reboot command failed (rc={reboot_cmd.rc}): {reboot_cmd.stderr.strip()}"}

    time.sleep(15)

    start = time.time()
    online = False
    while time.time() - start < REBOOT_WAIT_ONLINE_TIMEOUT:
        ping = _safe_run(
            host,
            f"ping -c 1 -W 3 {admin_ip} > /dev/null 2>&1 && echo UP",
            admin_ip,
        )
        if "UP" in ping.stdout or ping.rc == 0:
            online = True
            break
        time.sleep(REBOOT_WAIT_ONLINE_POLL_INTERVAL)

    if not online:
        return {"hostname": hostname, "admin_ip": admin_ip,
                "rebooted": True, "online": False,
                "error": f"Node did not come back within {REBOOT_WAIT_ONLINE_TIMEOUT}s"}

    time.sleep(REBOOT_POST_SETTLE_DELAY)
    return {"hostname": hostname, "admin_ip": admin_ip,
            "rebooted": True, "online": True, "error": ""}


# =============================================================================
# TC28 – NFS mount and SIF files accessible after node reboot
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(28)
def test_nfs_and_sif_accessible_after_node_reboot(host):
    """TC28: Reboot a compute node; verify NFS mount and SIF files are accessible on recovery."""
    global _REBOOTED_NODES

    log = TestLogger("Verify NFS mount and SIF accessible after compute node reboot")

    compute_nodes = get_slurm_nodes(host)
    if not compute_nodes:
        pytest.skip("No slurm compute nodes found – skipping reboot test")

    target_node = compute_nodes[0]
    hostname = target_node.get("hostname", "unknown")
    admin_ip = target_node.get("admin_ip", "")

    log.check(f"Rebooting compute node: {hostname} ({admin_ip})")
    reboot_status = _reboot_node_and_wait(host, target_node)

    if not reboot_status["rebooted"]:
        pytest.fail(f"Could not reboot {hostname}: {reboot_status['error']}")

    if not reboot_status["online"]:
        pytest.fail(f"Node {hostname} did not come back online: {reboot_status['error']}")

    log.check(f"Node {hostname} is back online — checking NFS and SIF files")

    _REBOOTED_NODES = [target_node]

    result = verify_nfs_and_sif_accessible_after_reboot(host, _REBOOTED_NODES)

    for detail in result.get("details", []):
        log.check(f"  {detail.get('hostname', '?')}: "
                  f"nfs_mounted={detail.get('nfs_mounted', False)} | "
                  f"sif_accessible={detail.get('sif_accessible', False)} | "
                  f"sif_count={detail.get('sif_files_found', 0)} | "
                  f"apptainer_exec_rc={detail.get('apptainer_exec_rc', '?')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC29 – Container execution post reboot
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(29)
def test_container_execution_post_reboot(host):
    """TC29: Submit Apptainer container job after node has been rebooted; verify COMPLETED."""
    log = TestLogger("Test Apptainer container execution post reboot")
    log.check("Submitting single-node Apptainer sbatch after reboot")

    result = verify_container_execution_post_reboot(host)

    log.check(f"  Job ID: {result.get('job_id', 'N/A')} | State: {result.get('job_state', 'N/A')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC30 – download_container_image.sh works correctly after reboot
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(30)
def test_download_script_works_after_reboot(host):
    """TC30: After reboot verify download_container_image.sh is present, executable, and passes bash -n."""
    log = TestLogger("Verify download_container_image.sh works correctly after reboot")
    log.check("Checking script presence, executable bit, image list, and syntax on rebooted node")

    result = verify_download_script_works_after_reboot(host)

    details = result.get("details", {})
    log.check(f"  Hostname: {details.get('hostname', 'N/A')}")
    log.check(f"  Script path: {details.get('script_path', 'N/A')}")
    log.check(f"  Script found: {details.get('script_found', False)}")
    log.check(f"  Executable: {details.get('is_executable', False)}")
    log.check(f"  Image list found: {details.get('list_found', False)}")
    log.check(f"  Syntax OK: {details.get('syntax_ok', False)}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]
