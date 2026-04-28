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

"""Kubernetes VIP failover test case for OMNIA.

This module verifies that when the control plane holding the VIP is rebooted:
1. The node comes back online
2. Cloud-init completes successfully
3. The node returns to Ready state
4. The VIP fails over to another control plane
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
from automation_library.kubernetes.functions.k8s_func import get_oim_operations

# Module-level shared state
_reboot_state = {
    "virtual_ip": "",
    "vip_node": None,
    "vip_node_ip": "",
    "vip_node_hostname": "",
    "remaining_nodes": [],
    "watcher_host": "",
}

# Pytest fixtures
@pytest.fixture(scope="module", name="oim_ops")
def _oim_ops_fixture():
    """Fixture to provide OIMOperations instance."""
    try:
        ops = get_oim_operations()
    except (OSError, KeyError, RuntimeError, ValueError) as e:
        pytest.skip(f"Unable to initialize OIM operations: {str(e)}")
    try:
        yield ops
    finally:
        ops.close()

# =============================================================================
# VIP FAILOVER SCENARIO
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(33)
def test_reboot_vip_control_plane(oim_ops):
    """TC33: Reboot the kube control-plane that has the VIP assigned."""
    log = TestLogger("Reboot VIP-holding control-plane")
    log.check("Reading virtual_ip_address from high_availability_config.yml")
    
    result = oim_ops.reboot_vip_control_plane()
    
    if not result["success"]:
        log.failed(result["message"])
        pytest.skip(result["message"])
    
    # Store state for subsequent tests
    _reboot_state["virtual_ip"] = result["virtual_ip"]
    _reboot_state["vip_node"] = result["vip_node"]
    _reboot_state["vip_node_ip"] = result["vip_node"]["admin_ip"]
    _reboot_state["vip_node_hostname"] = result["vip_node"].get("hostname") or result["vip_node"]["admin_ip"]
    _reboot_state["remaining_nodes"] = result["remaining_nodes"]
    _reboot_state["watcher_host"] = result["watcher_host"]
    
    log.check(f"VIP {result['virtual_ip']} is on {_reboot_state['vip_node_hostname']} ({_reboot_state['vip_node_ip']})")
    log.check(f"Rebooting {_reboot_state['vip_node_hostname']}...")
    log.passed(result["message"])

@pytest.mark.negative
@pytest.mark.order(34)
def test_verify_vip_failover(oim_ops):
    """TC34: Verify the VIP has failed over to another control-plane."""
    log = TestLogger("Verify VIP failover")
    
    if not _reboot_state["virtual_ip"]:
        pytest.skip("TC35 did not store VIP info")
    
    virtual_ip = _reboot_state["virtual_ip"]
    original_node_ip = _reboot_state["vip_node_ip"]
    remaining_nodes = _reboot_state["remaining_nodes"]
    
    log.check(f"Verifying VIP {virtual_ip} has moved to one of the remaining control-planes...")
    
    success, message, new_holder = oim_ops.verify_vip_failover_to_remaining_nodes(
        virtual_ip=virtual_ip,
        original_node_ip=original_node_ip,
        remaining_nodes=remaining_nodes,
    )
    
    if success and new_holder:
        new_hostname = new_holder.get("hostname") or new_holder.get("admin_ip")
        new_ip = new_holder.get("admin_ip")
        log.check(f"VIP {virtual_ip} is now on {new_hostname} ({new_ip})")
        log.passed(message)
    else:
        log.failed(message)
    
    assert success, message


@pytest.mark.negative
@pytest.mark.order(35)
def test_verify_cloud_init_after_reboot(oim_ops):
    """TC35: Verify cloud-init completes successfully on the rebooted control-plane."""
    log = TestLogger("Verify cloud-init after reboot")
    
    if not _reboot_state["vip_node_ip"]:
        pytest.skip("TC35 did not store VIP node info")
    
    node_ip = _reboot_state["vip_node_ip"]
    hostname = _reboot_state["vip_node_hostname"]
    
    log.check(f"Waiting for {hostname} ({node_ip}) to come back online...")
    online_result = oim_ops.wait_for_node_online_via_omnia_core(node_ip, hostname)
    log.check(online_result["message"])
    
    if not online_result["success"]:
        log.failed(online_result["message"])
        assert False, online_result["message"]
    
    log.check(f"Verifying cloud-init on {hostname}...")
    log.check("Checking /var/log/cloud-init-output.log for 'Cloud-Init finished successfully after the reboot'")
    
    cloud_init_result = oim_ops.verify_cloud_init_on_node(node_ip, hostname)
    
    if cloud_init_result["success"]:
        log.passed(cloud_init_result["message"])
    else:
        log.check(f"Last 50 lines of cloud-init log:\n{cloud_init_result.get('log_tail', 'N/A')}")
        log.failed(cloud_init_result["message"])
    
    assert cloud_init_result["success"], cloud_init_result["message"]

@pytest.mark.negative
@pytest.mark.order(36)
def test_verify_node_ready_after_reboot(oim_ops):
    """TC36: Verify the rebooted control-plane is in Ready state."""
    log = TestLogger("Verify node is in Ready state")
    
    if not _reboot_state["vip_node"]:
        pytest.skip("TC33 did not store VIP node info")
    
    vip_node = _reboot_state["vip_node"]
    watcher_host = _reboot_state["watcher_host"]
    hostname = _reboot_state["vip_node_hostname"]
    node_ip = _reboot_state["vip_node_ip"]
    
    log.check(f"Checking 'kubectl get nodes' from {watcher_host} for {hostname} Ready status...")
    
    # Check current node status without waiting (cloud-init already waited)
    rc, out, _ = oim_ops._ssh_from_omnia_core(watcher_host, "kubectl get nodes --no-headers")
    
    if rc != 0:
        log.failed(f"Failed to run kubectl get nodes from {watcher_host}")
        assert False, f"Failed to run kubectl get nodes from {watcher_host}"
    
    # Find the node in output
    node_found = False
    node_status = "NotFound"
    for line in (out or "").splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        name, status = parts[0], parts[1]
        if hostname and (name == hostname or hostname in name):
            node_found = True
            node_status = status
            break
        elif node_ip and (name == node_ip or node_ip in name):
            node_found = True
            node_status = status
            break
    
    if not node_found:
        log.failed(f"Node {hostname} ({node_ip}) not found in kubectl get nodes output")
        assert False, f"Node {hostname} ({node_ip}) not found in kubectl get nodes output"
    
    if node_status == "Ready":
        log.passed(f"Node {hostname} is in Ready state")
    else:
        log.failed(f"Node {hostname} is in {node_status} state (expected Ready)")
        assert False, f"Node {hostname} is in {node_status} state (expected Ready)"

