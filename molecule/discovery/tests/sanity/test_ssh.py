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
Discovery SSH Verification Test Cases.

Test cases for verifying passwordless SSH connectivity:
1. Node connectivity pre-check (ping + SSH with retry)
2. SSH from OIM to nodes via admin IP
3. SSH from OIM to nodes via hostname
4. SSH from omnia_core to nodes via admin IP
5. SSH from omnia_core to nodes via hostname
"""

import pytest
from automation_library.core import (
    TestLogger,
    verify_nodes_connectivity,
    get_connectivity_cache,
    get_reachable_nodes,
    get_unreachable_nodes,
)
from automation_library.discovery.functions import (
    get_all_slurm_nodes,
    get_k8s_nodes,
    verify_ssh_from_core,
    verify_ssh_from_oim,
)


# =============================================================================
# NODE CONNECTIVITY PRE-CHECK (run first with retry)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_node_connectivity_precheck(host):
    """
    Test Case 1: Verify all nodes are reachable (ping + SSH) with retry.
    
    This test runs first and checks connectivity to all nodes with:
    - Ping retry: 20 minutes (240 retries x 5 seconds)
    - SSH retry: 5 minutes (60 retries x 5 seconds)
    
    Results are cached for use by subsequent tests.
    """
    log = TestLogger("Verify node connectivity (ping + SSH)")

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    if not all_nodes:
        log.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    log.check(f"Checking connectivity to {len(all_nodes)} nodes (ping + SSH with retry)")

    result = verify_nodes_connectivity(host, all_nodes)

    # Build details
    details_lines = [
        f"Total nodes: {result['total']}",
        f"Reachable: {result['reachable_count']}",
        f"Unreachable: {result['unreachable_count']}",
        "",
    ]

    for node_result in result["results"]:
        hostname = node_result["hostname"]
        admin_ip = node_result["admin_ip"]
        if node_result["reachable"]:
            details_lines.append(f"  ✓ {hostname} ({admin_ip}): reachable")
        else:
            if not node_result["ping_ok"]:
                details_lines.append(f"  ✗ {hostname} ({admin_ip}): not pingable")
            else:
                details_lines.append(f"  ✗ {hostname} ({admin_ip}): ping OK but SSH failed")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(f"All {result['total']} nodes are reachable", details)
    else:
        log.failed(
            f"{result['unreachable_count']} of {result['total']} nodes unreachable",
            details
        )

    assert result["success"], (
        f"{result['unreachable_count']} nodes are unreachable. "
        "Check node status and network connectivity."
    )


# =============================================================================
# OIM SSH TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_ssh_from_oim_via_admin_ip(host):
    """
    Test Case 2: Verify passwordless SSH from OIM to nodes via admin IP.
    """
    log = TestLogger("Verify passwordless SSH from OIM via admin IP")

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    if not all_nodes:
        log.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    log.check(f"Testing SSH from OIM to {len(all_nodes)} nodes using admin IP")

    result = verify_ssh_from_oim(host, all_nodes, use_hostname=False)

    if result["success"]:
        log.passed(
            f"SSH working to all {result['total']} nodes via admin IP",
            result["details"]
        )
    else:
        log.failed(f"SSH failed for {result['failed']} nodes", result["details"])

    assert result["success"], f"SSH failed for: {', '.join(result['failed_nodes'])}"


@pytest.mark.sanity
@pytest.mark.order(3)
def test_ssh_from_oim_via_hostname(host):
    """
    Test Case 3: Verify passwordless SSH from OIM to nodes via hostname.
    """
    log = TestLogger("Verify passwordless SSH from OIM via hostname")

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    if not all_nodes:
        log.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    log.check(f"Testing SSH from OIM to {len(all_nodes)} nodes using hostname")

    result = verify_ssh_from_oim(host, all_nodes, use_hostname=True)

    if result["success"]:
        log.passed(
            f"SSH working to all {result['total']} nodes via hostname",
            result["details"]
        )
    else:
        log.failed(f"SSH failed for {result['failed']} nodes", result["details"])

    assert result["success"], f"SSH failed for: {', '.join(result['failed_nodes'])}"


# =============================================================================
# OMNIA_CORE SSH TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_ssh_from_core_via_admin_ip(host):
    """
    Test Case 4: Verify passwordless SSH from omnia_core to nodes via admin IP.
    """
    log = TestLogger("Verify passwordless SSH from omnia_core via admin IP")

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    if not all_nodes:
        log.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    log.check(f"Testing SSH from omnia_core to {len(all_nodes)} nodes using admin IP")

    result = verify_ssh_from_core(host, all_nodes, use_hostname=False)

    if result["success"]:
        log.passed(
            f"SSH working to all {result['total']} nodes via admin IP",
            result["details"]
        )
    else:
        log.failed(f"SSH failed for {result['failed']} nodes", result["details"])

    assert result["success"], f"SSH failed for: {', '.join(result['failed_nodes'])}"


@pytest.mark.sanity
@pytest.mark.order(5)
def test_ssh_from_core_via_hostname(host):
    """
    Test Case 5: Verify passwordless SSH from omnia_core to nodes via hostname.
    """
    log = TestLogger("Verify passwordless SSH from omnia_core via hostname")

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    if not all_nodes:
        log.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    log.check(f"Testing SSH from omnia_core to {len(all_nodes)} nodes using hostname")

    result = verify_ssh_from_core(host, all_nodes, use_hostname=True)

    if result["success"]:
        log.passed(
            f"SSH working to all {result['total']} nodes via hostname",
            result["details"]
        )
    else:
        log.failed(f"SSH failed for {result['failed']} nodes", result["details"])

    assert result["success"], f"SSH failed for: {', '.join(result['failed_nodes'])}"
