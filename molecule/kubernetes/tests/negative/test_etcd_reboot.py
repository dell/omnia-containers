# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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

"""etcd local disk post-reboot test cases for OMNIA.

This module verifies etcd local disk state after rebooting a control plane node:
1. Reboot a control plane node
2. Wait for node to come back online
3. Wait for cloud-init to complete
4. TC-F09: Verify etcd-fstab-update.sh ran on subsequent boot (timestamp-aware)
5. TC-F05 post-reboot: Verify fstab entry and mount persisted across reboot
6. TC-F06 post-reboot: Verify etcd is still using local disk (not NFS)
7. Verify etcd cluster health after reboot
"""

import os
import sys

# Add the project root to the Python path
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../.."),
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
from automation_library.core import TestLogger
from automation_library.etcd_local_disk.functions.etcd_func import get_etcd_operations
from automation_library.etcd_local_disk.vars.etcd_vars import ETCD_MOUNT_PATH
from automation_library.kubernetes.functions.k8s_func import get_oim_operations

# Module-level shared state for reboot tests
_reboot_state = {
    "rebooted_ip": "",
    "rebooted_hostname": "",
    "reboot_time": "",
    "remaining_nodes": [],
}


# Pytest fixtures
@pytest.fixture(scope="module", name="etcd_ops")
def _etcd_ops_fixture(host):
    """Fixture to provide EtcdLocalDiskOperations instance."""
    try:
        ops = get_etcd_operations(host=host)
    except (OSError, KeyError, RuntimeError, ValueError) as e:
        pytest.skip(f"Unable to initialize etcd operations: {str(e)}")
    yield ops


@pytest.fixture(scope="module", name="etcd_enabled")
def _etcd_enabled_fixture(etcd_ops):
    """Fixture to check if etcd_on_local_disk is enabled."""
    enabled, message = etcd_ops.is_etcd_on_local_disk_enabled()
    return enabled


@pytest.fixture(scope="module", name="oim_ops")
def _oim_ops_fixture():
    """Fixture to provide OIMOperations instance for etcd cluster health."""
    try:
        ops = get_oim_operations()
    except (OSError, KeyError, RuntimeError, ValueError) as e:
        pytest.skip(f"Unable to initialize OIM operations: {str(e)}")
    try:
        yield ops
    finally:
        ops.close()


# =========================================================================
# Step 1: Reboot a Control Plane Node
# =========================================================================

@pytest.mark.negative
@pytest.mark.etcd
@pytest.mark.order(201)
def test_etcd_reboot_control_plane(etcd_ops, etcd_enabled):
    """Reboot a control plane node for post-reboot etcd validation.

    Priority: P0
    """
    log = TestLogger("etcd post-reboot: Reboot control plane node")

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping reboot tests")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check("Selecting a control plane node to reboot")
    result = etcd_ops.reboot_control_plane_node()

    if not result["success"]:
        log.failed(result["message"])
        pytest.skip(result["message"])

    # Store state for subsequent tests
    _reboot_state["rebooted_ip"] = result["rebooted_ip"]
    _reboot_state["rebooted_hostname"] = result["rebooted_hostname"]
    _reboot_state["reboot_time"] = result["reboot_time"]
    _reboot_state["remaining_nodes"] = result["remaining_nodes"]

    log.check(
        f"Rebooting {result['rebooted_hostname']} ({result['rebooted_ip']})"
    )
    log.passed(result["message"])


# =========================================================================
# Step 2: Wait for Node Online
# =========================================================================

@pytest.mark.negative
@pytest.mark.etcd
@pytest.mark.order(202)
def test_etcd_wait_node_online(etcd_ops, etcd_enabled):
    """Wait for the rebooted control plane node to come back online.

    Priority: P0
    """
    log = TestLogger("etcd post-reboot: Wait for node online")

    if not etcd_enabled:
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    if not _reboot_state["rebooted_ip"]:
        pytest.skip("Reboot test did not run - no node to wait for")

    node_ip = _reboot_state["rebooted_ip"]
    hostname = _reboot_state["rebooted_hostname"]

    log.check(f"Waiting for {hostname} ({node_ip}) to come back online...")
    result = etcd_ops.wait_for_node_online(node_ip, hostname)

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =========================================================================
# Step 3: Wait for Cloud-Init
# =========================================================================

@pytest.mark.negative
@pytest.mark.etcd
@pytest.mark.order(203)
def test_etcd_wait_cloud_init(etcd_ops, etcd_enabled):
    """Wait for cloud-init to complete on the rebooted node.

    Priority: P0
    """
    log = TestLogger("etcd post-reboot: Wait for cloud-init")

    if not etcd_enabled:
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    if not _reboot_state["rebooted_ip"]:
        pytest.skip("Reboot test did not run - no node to check")

    node_ip = _reboot_state["rebooted_ip"]
    hostname = _reboot_state["rebooted_hostname"]

    log.check(f"Waiting for cloud-init to complete on {hostname}...")
    result = etcd_ops.wait_for_cloud_init(node_ip, hostname)

    if result["success"]:
        log.passed(result["message"])
    else:
        if result.get("log_tail"):
            log.check(
                f"Last lines of cloud-init log:\n{result['log_tail']}"
            )
        log.failed(result["message"])

    assert result["success"], result["message"]


# =========================================================================
# Step 4: TC-F09 Post-Reboot: Subsequent Boot fstab Update (Timestamp)
# =========================================================================

@pytest.mark.negative
@pytest.mark.etcd
@pytest.mark.order(204)
def test_tc_f09_subsequent_boot_post_reboot(etcd_ops, etcd_enabled):
    """TC-F09: Verify etcd-fstab-update.sh ran after reboot (timestamp-aware).

    This test validates that the subsequent boot script actually executed
    on THIS boot by comparing log modification time against reboot time.

    Maps To: SB-009
    Priority: P0
    """
    log = TestLogger(
        "TC-F09 post-reboot: Verify etcd-fstab-update.sh ran after reboot"
    )

    if not etcd_enabled:
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    if not _reboot_state["reboot_time"]:
        pytest.skip("Reboot test did not run - no reboot time available")

    reboot_time = _reboot_state["reboot_time"]
    rebooted_node = _reboot_state["rebooted_hostname"]
    log.check(
        f"Verifying etcd-fstab-update.sh log was updated after reboot"
        f" on {rebooted_node} (reboot time: {reboot_time})"
    )

    success, message, details = (
        etcd_ops.verify_subsequent_boot_fstab_update_post_reboot(
            reboot_time, target_node=rebooted_node,
        )
    )

    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message


# =========================================================================
# Step 5: TC-F05 Post-Reboot: fstab + Mount Persistence
# =========================================================================

@pytest.mark.negative
@pytest.mark.etcd
@pytest.mark.order(205)
def test_tc_f05_fstab_mount_post_reboot(etcd_ops, etcd_enabled):
    """TC-F05 post-reboot: Verify fstab entry and mount persisted across reboot.

    Maps To: SB-005, VC-009
    Priority: P0
    """
    log = TestLogger(
        "TC-F05 post-reboot: Verify fstab and mount persist after reboot"
    )

    if not etcd_enabled:
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    if not _reboot_state["rebooted_ip"]:
        pytest.skip("Reboot test did not run - no node to check")

    rebooted_node = _reboot_state["rebooted_hostname"]
    log.check(
        f"Verifying UUID-based fstab entry and active mount for"
        f" {ETCD_MOUNT_PATH} on {rebooted_node} after reboot"
    )
    success, message, details = etcd_ops.verify_fstab_and_mount(
        target_node=rebooted_node,
    )

    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message


# =========================================================================
# Step 6: TC-F06 Post-Reboot: etcd Still on Local Disk
# =========================================================================

@pytest.mark.negative
@pytest.mark.etcd
@pytest.mark.order(206)
def test_tc_f06_etcd_local_disk_post_reboot(etcd_ops, etcd_enabled):
    """TC-F06 post-reboot: Verify etcd is still using local disk after reboot.

    Maps To: SB-006, VC-010
    Priority: P0
    """
    log = TestLogger(
        "TC-F06 post-reboot: Verify etcd still on local disk after reboot"
    )

    if not etcd_enabled:
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    if not _reboot_state["rebooted_ip"]:
        pytest.skip("Reboot test did not run - no node to check")

    rebooted_node = _reboot_state["rebooted_hostname"]
    log.check(
        f"Verifying etcd uses local disk at {ETCD_MOUNT_PATH}"
        f" on {rebooted_node} (not NFS) after reboot"
    )
    success, message, details = etcd_ops.verify_etcd_using_local_disk(
        target_node=rebooted_node,
    )

    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message


# =========================================================================
# Step 7: etcd Cluster Health Post-Reboot
# =========================================================================

@pytest.mark.negative
@pytest.mark.etcd
@pytest.mark.order(207)
def test_etcd_cluster_health_post_reboot(oim_ops, etcd_enabled):
    """Verify etcd cluster is healthy after control plane reboot.

    Uses the k8s OIMOperations.verify_etcd_cluster_health() which runs
    etcdctl endpoint health inside each etcd pod individually.

    Priority: P0
    """
    log = TestLogger(
        "etcd post-reboot: Verify etcd cluster health after reboot"
    )

    if not etcd_enabled:
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    if not _reboot_state["rebooted_ip"]:
        pytest.skip("Reboot test did not run - no reboot performed")

    log.check("Checking etcd cluster endpoint health after reboot")
    success, message, output = oim_ops.verify_etcd_cluster_health()

    if success:
        log.passed(message, output)
    else:
        log.failed(message, output)
    assert success, message
