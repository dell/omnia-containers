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
Discovery Cloud-Init Verification Test Cases.

First test to run - verifies OS provisioning completed successfully on all nodes.
For diskless OS deployments, cloud-init is used for provisioning.

Test cases:
1. Verify cloud-init completed successfully on all nodes (no errors)
"""

import pytest
from automation_library.core import TestLogger
from automation_library.discovery.functions import (
    get_all_slurm_nodes,
    get_k8s_nodes,
    verify_cloudinit_status,
)


@pytest.mark.order(1)
def test_cloudinit_completed(host):
    """
    Test Case 1: Verify cloud-init completed successfully on all nodes.

    This is the FIRST test to run - confirms OS provisioning is complete.
    For diskless OS, cloud-init handles provisioning.

    Checks:
    - cloud-init status is 'done'
    - No errors in cloud-init status
    - Reports any warnings/recoverable errors
    """
    log = TestLogger("Verify cloud-init completed on all nodes")

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    if not all_nodes:
        log.skipped("No nodes found in PXE mapping", "Check PXE mapping file")
        pytest.skip("No nodes found in PXE mapping")

    log.check(f"Checking cloud-init status on {len(all_nodes)} nodes")

    result = verify_cloudinit_status(host, all_nodes)

    # Build detailed output
    details_lines = [f"Nodes checked: {result['total']}"]
    for node_result in result.get("results", []):
        status_icon = "✓" if node_result["success"] else "✗"
        details_lines.append(f"{status_icon} {node_result['hostname']}")
        details_lines.append(f"    Status: {node_result['status']}")
        if node_result.get("errors"):
            details_lines.append(f"    Errors: {node_result['errors']}")
        if node_result.get("warnings"):
            details_lines.append(f"    Warnings: {node_result['warnings'][:100]}...")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(f"Cloud-init completed on all {result['total']} nodes", details)
    else:
        failed_nodes = [r["hostname"] for r in result["results"] if not r["success"]]
        log.failed(f"Cloud-init failed on {len(failed_nodes)} nodes", details)

    assert result["success"], f"Cloud-init failed on: {', '.join(failed_nodes)}"
