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

Runs AFTER test_cloudinit.py (order 2-5).
Test cases for verifying passwordless SSH connectivity:
2. SSH from OIM to nodes via admin IP
3. SSH from OIM to nodes via hostname
4. SSH from omnia_core to nodes via admin IP
5. SSH from omnia_core to nodes via hostname

All tests use 2 retries for unreachable nodes and fail (not skip)
if nodes are unreachable.
"""

import pytest
from automation_library.core import (
    TestLogger,
    check_nodes_reachability,
)
from automation_library.discovery.functions import (
    get_all_slurm_nodes,
    get_k8s_nodes,
    verify_ssh_from_core,
    verify_ssh_from_oim,
)
from automation_library.discovery.vars import (
    DISCOVERY_REACHABILITY_RETRY,
    DISCOVERY_REACHABILITY_INTERVAL,
)


def _get_all_nodes(host):
    """Get all nodes from PXE mapping."""
    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    return slurm_nodes + k8s_nodes


def _group_nodes_by_functional_group(nodes):
    """Group nodes by functional_group."""
    groups = {}
    for node in nodes:
        fg = node.get("functional_group", "unknown")
        if fg not in groups:
            groups[fg] = []
        groups[fg].append(node)
    return groups


# =============================================================================
# OIM SSH TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(5)
def test_ssh_from_oim_via_admin_ip(host):
    """
    Test Case 2: Verify SSH from OIM to nodes via admin IP.
    Uses cached connectivity with 2 retries for unreachable nodes.
    Fails if any nodes are unreachable.
    """
    logger = TestLogger("Verify SSH from OIM via admin IP")

    all_nodes = _get_all_nodes(host)

    if not all_nodes:
        logger.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    # Check reachability (uses cache, 2 retries for unreachable)
    reach = check_nodes_reachability(
        host, all_nodes,
        retry_limit=DISCOVERY_REACHABILITY_RETRY,
        retry_interval=DISCOVERY_REACHABILITY_INTERVAL
    )

    # Build details grouped by functional group
    grouped = _group_nodes_by_functional_group(all_nodes)
    details_lines = []

    # Report unreachable nodes first
    if reach["unreachable"]:
        unreachable_count = len(reach['unreachable'])
        retry_count = DISCOVERY_REACHABILITY_RETRY
        details_lines.append(
            f"Unreachable nodes ({unreachable_count}) - after {retry_count} retries:"
        )
        for node in reach["unreachable"]:
            fg = node.get("functional_group", "unknown")
            hostname = node['hostname']
            admin_ip = node['admin_ip']
            details_lines.append(f"  [{fg}] ✗ {hostname} ({admin_ip}): not reachable")
        details_lines.append("")

    logger.check(f"Testing SSH to {len(reach['reachable'])} reachable nodes")

    # Test SSH on reachable nodes
    if reach["reachable"]:
        result = verify_ssh_from_oim(host, reach["reachable"], use_hostname=False)

        details_lines.append(f"SSH Results ({result['total']} nodes):")
        failed_nodes = result.get("failed_nodes", [])
        for fg, nodes in grouped.items():
            reachable_hostnames = [r["hostname"] for r in reach["reachable"]]
            fg_nodes = [n for n in nodes if n["hostname"] in reachable_hostnames]
            if fg_nodes:
                details_lines.append(f"  [{fg}]")
                for node in fg_nodes:
                    hostname = node["hostname"]
                    if hostname in failed_nodes:
                        details_lines.append(f"    ✗ {hostname}: SSH failed")
                    else:
                        details_lines.append(f"    ✓ {hostname}: SSH OK")
    else:
        result = {"success": False, "failed_nodes": []}

    details = "\n".join(details_lines)

    # Fail if any unreachable or SSH failed
    if reach["unreachable"] or not result["success"]:
        fail_parts = []
        if reach["unreachable"]:
            unreachable_hosts = [n['hostname'] for n in reach['unreachable']]
            fail_parts.append(f"Unreachable: {', '.join(unreachable_hosts)}")
        if result.get("failed_nodes"):
            fail_parts.append(f"SSH failed: {', '.join(result['failed_nodes'])}")
        logger.failed(f"SSH test failed", details=details)
        assert False, "; ".join(fail_parts)

    logger.passed(f"SSH successful to all {result['total']} nodes", details=details)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(6)
def test_ssh_from_oim_via_hostname(host):
    """
    Test Case 3: Verify SSH from OIM to nodes via hostname.
    Uses cached connectivity with 2 retries for unreachable nodes.
    Fails if any nodes are unreachable.
    """
    logger = TestLogger("Verify SSH from OIM via hostname")

    all_nodes = _get_all_nodes(host)

    if not all_nodes:
        logger.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    reach = check_nodes_reachability(
        host, all_nodes,
        retry_limit=DISCOVERY_REACHABILITY_RETRY,
        retry_interval=DISCOVERY_REACHABILITY_INTERVAL
    )

    grouped = _group_nodes_by_functional_group(all_nodes)
    details_lines = []

    if reach["unreachable"]:
        unreachable_count = len(reach['unreachable'])
        retry_count = DISCOVERY_REACHABILITY_RETRY
        details_lines.append(
            f"Unreachable nodes ({unreachable_count}) - after {retry_count} retries:"
        )
        for node in reach["unreachable"]:
            fg = node.get("functional_group", "unknown")
            hostname = node['hostname']
            admin_ip = node['admin_ip']
            details_lines.append(f"  [{fg}] ✗ {hostname} ({admin_ip}): not reachable")
        details_lines.append("")

    logger.check(f"Testing SSH to {len(reach['reachable'])} reachable nodes")

    if reach["reachable"]:
        result = verify_ssh_from_oim(host, reach["reachable"], use_hostname=True)

        details_lines.append(f"SSH Results ({result['total']} nodes):")
        failed_nodes = result.get("failed_nodes", [])
        for fg, nodes in grouped.items():
            reachable_hostnames = [r["hostname"] for r in reach["reachable"]]
            fg_nodes = [n for n in nodes if n["hostname"] in reachable_hostnames]
            if fg_nodes:
                details_lines.append(f"  [{fg}]")
                for node in fg_nodes:
                    hostname = node["hostname"]
                    if hostname in failed_nodes:
                        details_lines.append(f"    ✗ {hostname}: SSH failed")
                    else:
                        details_lines.append(f"    ✓ {hostname}: SSH OK")
    else:
        result = {"success": False, "failed_nodes": []}

    details = "\n".join(details_lines)

    if reach["unreachable"] or not result["success"]:
        fail_parts = []
        if reach["unreachable"]:
            unreachable_hosts = [n['hostname'] for n in reach['unreachable']]
            fail_parts.append(f"Unreachable: {', '.join(unreachable_hosts)}")
        if result.get("failed_nodes"):
            fail_parts.append(f"SSH failed: {', '.join(result['failed_nodes'])}")
        logger.failed(f"SSH test failed", details=details)
        assert False, "; ".join(fail_parts)

    logger.passed(f"SSH successful to all {result['total']} nodes", details=details)


# =============================================================================
# OMNIA_CORE SSH TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(7)
def test_ssh_from_core_via_admin_ip(host):
    """
    Test Case 4: Verify SSH from omnia_core to nodes via admin IP.
    Uses cached connectivity with 2 retries for unreachable nodes.
    Fails if any nodes are unreachable.
    """
    logger = TestLogger("Verify SSH from omnia_core via admin IP")

    all_nodes = _get_all_nodes(host)

    if not all_nodes:
        logger.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    reach = check_nodes_reachability(
        host, all_nodes,
        retry_limit=DISCOVERY_REACHABILITY_RETRY,
        retry_interval=DISCOVERY_REACHABILITY_INTERVAL
    )

    grouped = _group_nodes_by_functional_group(all_nodes)
    details_lines = []

    if reach["unreachable"]:
        unreachable_count = len(reach['unreachable'])
        retry_count = DISCOVERY_REACHABILITY_RETRY
        details_lines.append(
            f"Unreachable nodes ({unreachable_count}) - after {retry_count} retries:"
        )
        for node in reach["unreachable"]:
            fg = node.get("functional_group", "unknown")
            hostname = node['hostname']
            admin_ip = node['admin_ip']
            details_lines.append(f"  [{fg}] ✗ {hostname} ({admin_ip}): not reachable")
        details_lines.append("")

    logger.check(f"Testing SSH to {len(reach['reachable'])} reachable nodes")

    if reach["reachable"]:
        result = verify_ssh_from_core(host, reach["reachable"], use_hostname=False)

        details_lines.append(f"SSH Results ({result['total']} nodes):")
        failed_nodes = result.get("failed_nodes", [])
        for fg, nodes in grouped.items():
            reachable_hostnames = [r["hostname"] for r in reach["reachable"]]
            fg_nodes = [n for n in nodes if n["hostname"] in reachable_hostnames]
            if fg_nodes:
                details_lines.append(f"  [{fg}]")
                for node in fg_nodes:
                    hostname = node["hostname"]
                    if hostname in failed_nodes:
                        details_lines.append(f"    ✗ {hostname}: SSH failed")
                    else:
                        details_lines.append(f"    ✓ {hostname}: SSH OK")
    else:
        result = {"success": False, "failed_nodes": []}

    details = "\n".join(details_lines)

    if reach["unreachable"] or not result["success"]:
        fail_parts = []
        if reach["unreachable"]:
            unreachable_hosts = [n['hostname'] for n in reach['unreachable']]
            fail_parts.append(f"Unreachable: {', '.join(unreachable_hosts)}")
        if result.get("failed_nodes"):
            fail_parts.append(f"SSH failed: {', '.join(result['failed_nodes'])}")
        logger.failed(f"SSH test failed", details=details)
        assert False, "; ".join(fail_parts)

    logger.passed(f"SSH successful to all {result['total']} nodes", details=details)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(9)
def test_ssh_from_core_via_hostname(host):
    """
    Test Case 5: Verify SSH from omnia_core to nodes via hostname.
    Uses cached connectivity with 2 retries for unreachable nodes.
    Fails if any nodes are unreachable.
    """
    logger = TestLogger("Verify SSH from omnia_core via hostname")

    all_nodes = _get_all_nodes(host)

    if not all_nodes:
        logger.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    reach = check_nodes_reachability(
        host, all_nodes,
        retry_limit=DISCOVERY_REACHABILITY_RETRY,
        retry_interval=DISCOVERY_REACHABILITY_INTERVAL
    )

    grouped = _group_nodes_by_functional_group(all_nodes)
    details_lines = []

    if reach["unreachable"]:
        unreachable_count = len(reach['unreachable'])
        retry_count = DISCOVERY_REACHABILITY_RETRY
        details_lines.append(
            f"Unreachable nodes ({unreachable_count}) - after {retry_count} retries:"
        )
        for node in reach["unreachable"]:
            fg = node.get("functional_group", "unknown")
            hostname = node['hostname']
            admin_ip = node['admin_ip']
            details_lines.append(f"  [{fg}] ✗ {hostname} ({admin_ip}): not reachable")
        details_lines.append("")

    logger.check(f"Testing SSH to {len(reach['reachable'])} reachable nodes")

    if reach["reachable"]:
        result = verify_ssh_from_core(host, reach["reachable"], use_hostname=True)

        details_lines.append(f"SSH Results ({result['total']} nodes):")
        failed_nodes = result.get("failed_nodes", [])
        for fg, nodes in grouped.items():
            reachable_hostnames = [r["hostname"] for r in reach["reachable"]]
            fg_nodes = [n for n in nodes if n["hostname"] in reachable_hostnames]
            if fg_nodes:
                details_lines.append(f"  [{fg}]")
                for node in fg_nodes:
                    hostname = node["hostname"]
                    if hostname in failed_nodes:
                        details_lines.append(f"    ✗ {hostname}: SSH failed")
                    else:
                        details_lines.append(f"    ✓ {hostname}: SSH OK")
    else:
        result = {"success": False, "failed_nodes": []}

    details = "\n".join(details_lines)

    if reach["unreachable"] or not result["success"]:
        fail_parts = []
        if reach["unreachable"]:
            unreachable_hosts = [n['hostname'] for n in reach['unreachable']]
            fail_parts.append(f"Unreachable: {', '.join(unreachable_hosts)}")
        if result.get("failed_nodes"):
            fail_parts.append(f"SSH failed: {', '.join(result['failed_nodes'])}")
        logger.failed(f"SSH test failed", details=details)
        assert False, "; ".join(fail_parts)

    logger.passed(f"SSH successful to all {result['total']} nodes", details=details)
