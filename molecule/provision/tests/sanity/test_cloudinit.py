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
Provision Cloud-Init Verification Test Cases.

This is the FIRST test in provision - verifies:
1. Node connectivity (ping + SSH) with retries
2. Cloud-init status on reachable nodes

Results are cached for subsequent tests.
"""

import pytest
from automation_library.core import (
    TestLogger,
    clear_connectivity_cache,
    verify_nodes_connectivity,
    verify_cloudinit_status,
)
from automation_library.provision.functions import (
    get_all_slurm_nodes,
    get_k8s_nodes,
)


def _group_nodes_by_functional_group(nodes):
    """Group nodes by functional_group."""
    groups = {}
    for node in nodes:
        fg = node.get("functional_group", "unknown")
        if fg not in groups:
            groups[fg] = []
        groups[fg].append(node)
    return groups


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(1)
def test_node_connectivity_and_cloudinit(host):
    """
    Test Case 1: Verify node connectivity and cloud-init status.

    This is the FIRST test - does full connectivity check with retry,
    then checks cloud-init on reachable nodes.

    Steps:
    1. Check ping + SSH connectivity with retries
    2. For reachable nodes, check cloud-init status
    3. Report unreachable nodes as failures
    4. Cache results for subsequent tests
    """
    log = TestLogger("Verify node connectivity and cloud-init status")

    # Clear cache for fresh check
    clear_connectivity_cache()

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    if not all_nodes:
        log.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    # Group nodes by functional group for display
    grouped = _group_nodes_by_functional_group(all_nodes)

    log.check(f"Checking connectivity to {len(all_nodes)} nodes")

    # Full connectivity check with retry
    conn_result = verify_nodes_connectivity(host, all_nodes, use_cache=False)

    # Separate reachable and unreachable
    reachable_nodes = []
    unreachable_nodes = []
    for r in conn_result["results"]:
        node = next((n for n in all_nodes if n["hostname"] == r["hostname"]), None)
        if node:
            if r["reachable"]:
                reachable_nodes.append(node)
            else:
                unreachable_nodes.append({**node, "error": r.get("error", "unreachable")})

    # Build connectivity details grouped by functional group
    details_lines = [
        f"Total nodes: {len(all_nodes)}",
        f"Reachable: {len(reachable_nodes)}",
        f"Unreachable: {len(unreachable_nodes)}",
        "",
        "Connectivity Results:",
    ]

    for fg, nodes in grouped.items():
        details_lines.append(f"  [{fg}]")
        for node in nodes:
            hostname = node["hostname"]
            admin_ip = node["admin_ip"]
            conn_r = next((r for r in conn_result["results"] if r["hostname"] == hostname), None)
            if conn_r and conn_r["reachable"]:
                details_lines.append(f"    ✓ {hostname} ({admin_ip}): reachable")
            else:
                error = conn_r.get("error", "unreachable") if conn_r else "unreachable"
                details_lines.append(f"    ✗ {hostname} ({admin_ip}): {error}")

    # Check cloud-init only on reachable nodes
    cloudinit_failed = []
    if reachable_nodes:
        details_lines.append("")
        details_lines.append("Cloud-init Status:")

        cloudinit_result = verify_cloudinit_status(host, reachable_nodes)

        # Group cloudinit results by functional group
        for fg, nodes in grouped.items():
            fg_results = []
            for node in nodes:
                hostname = node["hostname"]
                ci_r = next(
                    (r for r in cloudinit_result.get("results", []) if r["hostname"] == hostname),
                    None
                )
                if ci_r:
                    fg_results.append(ci_r)

            if fg_results:
                details_lines.append(f"  [{fg}]")
                for ci_r in fg_results:
                    status_icon = "✓" if ci_r["success"] else "✗"
                    retries = ci_r.get("retries", 0)
                    retry_info = f" (after {retries} retries)" if retries > 0 else ""
                    details_lines.append(
                        f"    {status_icon} {ci_r['hostname']}: {ci_r['status']}{retry_info}"
                    )
                    if ci_r.get("errors"):
                        details_lines.append(f"        Errors: {ci_r['errors']}")
                    if not ci_r["success"]:
                        cloudinit_failed.append(ci_r["hostname"])

    details = "\n".join(details_lines)

    # Determine overall success
    all_success = len(unreachable_nodes) == 0 and len(cloudinit_failed) == 0

    if all_success:
        log.passed(
            f"All {len(all_nodes)} nodes reachable, cloud-init completed",
            details
        )
    else:
        error_parts = []
        if unreachable_nodes:
            error_parts.append(f"{len(unreachable_nodes)} unreachable")
        if cloudinit_failed:
            error_parts.append(f"{len(cloudinit_failed)} cloud-init failed")
        log.failed(f"Node check failed: {', '.join(error_parts)}", details)

        # Build failure message
        fail_msgs = []
        if unreachable_nodes:
            fail_msgs.append(
                f"Unreachable: {', '.join(n['hostname'] for n in unreachable_nodes)}"
            )
        if cloudinit_failed:
            fail_msgs.append(f"Cloud-init failed: {', '.join(cloudinit_failed)}")

        assert False, "; ".join(fail_msgs)
