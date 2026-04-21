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
1. SSH from OIM to nodes via admin IP
2. SSH from OIM to nodes via hostname
3. SSH from omnia_core to nodes via admin IP
4. SSH from omnia_core to nodes via hostname
"""

import pytest
from automation_library.core import TestLogger
from automation_library.discovery.functions import (
    get_all_slurm_nodes,
    get_k8s_nodes,
    verify_ssh_from_core,
    verify_ssh_from_oim,
)


# =============================================================================
# OIM SSH TESTS (run first)
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
