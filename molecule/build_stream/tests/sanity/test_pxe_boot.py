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
PXE Boot Node Connectivity and Cloud-Init Verification (v2.1).

After the build pipeline's deploy-and-validate stage PXE boots the nodes,
these tests verify:
  1. Node connectivity - all nodes from PXE mapping are reachable (ping + SSH)
  2. Cloud-init status - cloud-init has completed on all reachable nodes

In v2.1, PXE boot is part of the single build pipeline
(deploy-and-validate CI/CD stage). In v2.2, it is a separate deploy pipeline.

This test uses the core module's verify_nodes_connectivity() with a
two-phase approach:
  Phase 1: Quick parallel check of all nodes (no retry)
  Phase 2: Retry only failed nodes with full retry logic (10 min ping, 5 min SSH)

Cloud-init verification:
  Polls "cloud-init status" on each reachable node (120 retries x 5s = 10m per node)
"""

import pytest

from automation_library.core import (
    TestLogger,
    is_build_stream_enabled,
    clear_connectivity_cache,
    verify_nodes_connectivity,
    verify_cloudinit_status,
)
from automation_library.discovery.functions import (
    get_all_slurm_nodes,
    get_k8s_nodes,
)

from automation_library.build_stream.functions import (
    skip_if_build_stream_not_enabled,
    get_latest_job,
)
from automation_library.build_stream.vars.build_stream_vars import (
    JOB_STATE_FAILED,
)
from automation_library.build_stream.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# MODULE-LEVEL STATE
# =============================================================================

_pxe_state = {
    "all_nodes": [],
    "reachable_nodes": [],
    "unreachable_nodes": [],
    "connectivity_checked": False,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _skip_if_build_failed(host, log):
    """Skip test if the build pipeline job failed."""
    job_result = get_latest_job(host)
    if job_result["success"]:
        if job_result["job_state"] == JOB_STATE_FAILED:
            log.skipped(
                "Build pipeline failed",
                f"Job {job_result['job_id']} state is {JOB_STATE_FAILED}"
            )
            pytest.skip(f"Build pipeline failed: Job {job_result['job_id']}")
    else:
        log.skipped("Could not get job state", job_result.get("error", ""))
        pytest.skip("Could not verify job state")


def _get_all_target_nodes(host):
    """
    Get all target nodes from PXE mapping file.

    Collects Slurm nodes and K8s nodes from the PXE mapping.
    Each node dict has at minimum: hostname, admin_ip, functional_group.
    """
    if _pxe_state["all_nodes"]:
        return _pxe_state["all_nodes"]

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    _pxe_state["all_nodes"] = all_nodes
    return all_nodes


def _group_nodes_by_functional_group(nodes):
    """Group nodes by functional_group for display."""
    groups = {}
    for node in nodes:
        fg = node.get("functional_group", "unknown")
        if fg not in groups:
            groups[fg] = []
        groups[fg].append(node)
    return groups


# =============================================================================
# TEST 30: PXE Boot Node Connectivity
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(30)
def test_pxe_boot_node_connectivity(host):
    """
    Verify all PXE-booted nodes are reachable via ping and SSH.

    Uses two-phase connectivity check:
      Phase 1: Quick parallel check (all nodes, no retry)
      Phase 2: Retry only failed nodes (10 min ping timeout, 5 min SSH timeout)

    Nodes are read from the PXE mapping file via the discovery module.
    """
    log = TestLogger(TEST_NAMES["pxe_boot_connectivity"])
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_failed(host, log)

    all_nodes = _get_all_target_nodes(host)

    if not all_nodes:
        log.skipped(
            TEST_LOG_MSGS["pxe_no_nodes"],
            "No nodes found in PXE mapping file. Check PXE mapping configuration."
        )
        pytest.skip(SKIP_MSGS["no_nodes_in_pxe_mapping"])

    # Group for display
    grouped = _group_nodes_by_functional_group(all_nodes)

    log.check(f"Checking connectivity to {len(all_nodes)} nodes...")

    # Clear cache for fresh check
    clear_connectivity_cache()

    # Full connectivity check with retry
    conn_result = verify_nodes_connectivity(host, all_nodes, use_cache=False)
    _pxe_state["connectivity_checked"] = True

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

    _pxe_state["reachable_nodes"] = reachable_nodes
    _pxe_state["unreachable_nodes"] = unreachable_nodes

    # Build details grouped by functional group
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
            conn_r = next(
                (r for r in conn_result["results"] if r["hostname"] == hostname),
                None
            )
            if conn_r and conn_r["reachable"]:
                details_lines.append(f"    PASS {hostname} ({admin_ip})")
            else:
                error = conn_r.get("error", "unreachable") if conn_r else "unreachable"
                details_lines.append(f"    FAIL {hostname} ({admin_ip}): {error}")

    details = "\n".join(details_lines)

    if len(unreachable_nodes) == 0:
        log.passed(
            TEST_LOG_MSGS["pxe_connectivity_ok"].format(count=len(reachable_nodes)),
            details
        )
    else:
        log.failed(
            TEST_LOG_MSGS["pxe_connectivity_fail"].format(
                unreachable=len(unreachable_nodes),
                total=len(all_nodes)
            ),
            details
        )
        unreachable_hosts = ", ".join(n["hostname"] for n in unreachable_nodes)
        assert False, TEST_ASSERT_MSGS["pxe_connectivity_failed"].format(
            error=f"Unreachable: {unreachable_hosts}"
        )


# =============================================================================
# TEST 31: PXE Boot Cloud-Init Verification
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(31)
def test_pxe_boot_cloudinit_status(host):
    """
    Verify cloud-init has completed on all reachable PXE-booted nodes.

    Checks "cloud-init status" on each reachable node and waits for
    "status: done" with retry logic (120 retries x 5 seconds = 10m per node).

    Nodes that were unreachable in the connectivity test are reported
    as failures without re-checking.
    """
    log = TestLogger(TEST_NAMES["pxe_boot_cloudinit"])
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_failed(host, log)

    all_nodes = _get_all_target_nodes(host)

    if not all_nodes:
        log.skipped(
            TEST_LOG_MSGS["pxe_no_nodes"],
            "No nodes found in PXE mapping file."
        )
        pytest.skip(SKIP_MSGS["no_nodes_in_pxe_mapping"])

    # Use cached connectivity results if available
    if _pxe_state["connectivity_checked"]:
        reachable_nodes = _pxe_state["reachable_nodes"]
        unreachable_nodes = _pxe_state["unreachable_nodes"]
    else:
        # If connectivity test was skipped, do a quick check
        reachable_nodes = all_nodes
        unreachable_nodes = []

    if not reachable_nodes and unreachable_nodes:
        log.failed(
            TEST_LOG_MSGS["pxe_cloudinit_fail"].format(
                failed=len(unreachable_nodes), total=len(all_nodes)
            ),
            f"All {len(unreachable_nodes)} nodes are unreachable"
        )
        assert False, TEST_ASSERT_MSGS["pxe_cloudinit_failed"].format(
            error="All nodes unreachable"
        )

    log.check(f"Checking cloud-init status on {len(reachable_nodes)} reachable nodes...")

    cloudinit_result = verify_cloudinit_status(host, reachable_nodes)

    # Build details
    details_lines = [
        f"Reachable nodes checked: {len(reachable_nodes)}",
        f"Unreachable (skipped): {len(unreachable_nodes)}",
        "",
        "Cloud-init Results:",
    ]

    cloudinit_failed = []
    for ci_r in cloudinit_result.get("results", []):
        hostname = ci_r.get("hostname", "")
        status = ci_r.get("status", "unknown")
        if ci_r.get("success"):
            details_lines.append(f"  PASS {hostname}: {status}")
        else:
            error = ci_r.get("error", "")
            details_lines.append(f"  FAIL {hostname}: {status} - {error}")
            cloudinit_failed.append(hostname)

    if unreachable_nodes:
        details_lines.append("")
        details_lines.append("Unreachable nodes (not checked):")
        for node in unreachable_nodes:
            details_lines.append(
                f"  SKIP {node['hostname']} ({node['admin_ip']}): "
                f"{node.get('error', 'unreachable')}"
            )

    details = "\n".join(details_lines)

    total_failed = len(cloudinit_failed) + len(unreachable_nodes)

    if total_failed == 0:
        log.passed(
            TEST_LOG_MSGS["pxe_cloudinit_ok"].format(count=len(reachable_nodes)),
            details
        )
    else:
        log.failed(
            TEST_LOG_MSGS["pxe_cloudinit_fail"].format(
                failed=total_failed, total=len(all_nodes)
            ),
            details
        )

        fail_parts = []
        if cloudinit_failed:
            fail_parts.append(f"Cloud-init failed: {', '.join(cloudinit_failed)}")
        if unreachable_nodes:
            fail_parts.append(
                f"Unreachable: {', '.join(n['hostname'] for n in unreachable_nodes)}"
            )

        assert False, TEST_ASSERT_MSGS["pxe_cloudinit_failed"].format(
            error="; ".join(fail_parts)
        )
