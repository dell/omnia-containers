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
Discovery Test Cases.

This module contains pytest test cases for verifying discovery playbook execution.
Tests verify node SSH connectivity, OpenCHAMI registration, configuration files,
and passwordless SSH setup.

Test cases:
1. Verify all PXE mapping nodes are reachable via SSH
2. Verify nodes are discovered in OpenCHAMI SMD
3. Verify nodes.yaml file exists and is valid
4. Verify passwordless SSH is configured to all nodes
5. Verify BMC group data file is created
6. Verify node hostnames match PXE mapping
7. Verify discovery process completed successfully

Usage:
    ./run_molecule.sh discovery test      # Run playbook + verify
    ./run_molecule.sh discovery verify    # Verify only
"""

import pytest
from automation_library.core import TestLogger
from automation_library.discovery.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.discovery.functions import (
    verify_nodes_ssh_reachable,
    verify_ochami_nodes_discovered,
    verify_nodes_yaml_file,
    verify_passwordless_ssh,
    verify_node_hostnames,
    # New validation functions
    validate_node_boot,
    validate_bmc_group_csv,
    validate_all_services,
    validate_all_sinfo,
    validate_all_ldap,
    validate_kubernetes_nodes,
)


# =============================================================================
# DISCOVERY TEST CASES
# =============================================================================

def test_nodes_ssh_reachable(host):
    """
    Test Case 1: Verify all nodes from PXE mapping are reachable via SSH.
    Results grouped by functional_group (role).
    """
    log = TestLogger(TEST_NAMES["nodes_ssh_reachable"])

    log.check("Testing SSH connectivity to all nodes from PXE mapping")
    result = verify_nodes_ssh_reachable(host)

    log.check(f"Total nodes: {result['total_count']}")
    log.check("")

    # Display results grouped by functional group
    for func_group, nodes in result.get("results_by_group", {}).items():
        log.check(f"═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            hostname = node["hostname"]
            admin_ip = node["admin_ip"]
            ssh_ok = node.get("ssh_via_ip", False)
            status = "✓" if ssh_ok else "✗"
            output = node.get("output", "")[:40]
            log.check(f"  {status} {hostname} ({admin_ip}) → {output}")
        log.check("")

    if result["success"]:
        log.passed(
            LOG_MSGS["nodes_ssh_success"].format(count=result["total_count"]),
            f"All {result['total_count']} nodes are reachable"
        )
    else:
        log.failed(
            LOG_MSGS["nodes_ssh_failed"].format(
                failed_count=result["failed_count"],
                total_count=result["total_count"]
            ),
            f"Failed nodes: {', '.join(result['failed_nodes'])}"
        )

    assert result["success"], ASSERT_MSGS["nodes_ssh_failed"].format(
        failed_nodes=", ".join(result["failed_nodes"]),
        total_count=result["total_count"],
        success_count=result["success_count"],
        failed_count=result["failed_count"],
        first_failed_ip=(
            result["failed_nodes"][0].split("(")[1].rstrip(")")
            if result["failed_nodes"] else ""
        ),
    )


def test_ochami_nodes_discovered(host):
    """
    Test Case 2: Verify nodes are discovered in OpenCHAMI SMD.
    Shows detailed SMD component information.
    """
    log = TestLogger(TEST_NAMES["ochami_nodes_discovered"])

    log.check("Querying OpenCHAMI SMD for discovered nodes")
    result = verify_ochami_nodes_discovered(host)

    log.check(f"Expected nodes from PXE: {result['total_count']}")
    log.check(f"Discovered in SMD: {result['discovered_count']}")
    log.check(f"BMC components: {result.get('bmc_count', 0)}")
    log.check("")

    # Show PXE mapping nodes by group
    log.check("═══ PXE Mapping Nodes ═══")
    for func_group, nodes in result.get("nodes_by_group", {}).items():
        log.check(f"  {func_group}:")
        for node in nodes:
            log.check(f"    - {node['hostname']} ({node['admin_ip']})")
    log.check("")

    # Show SMD components
    log.check("═══ SMD Components (Type=Node) ═══")
    for comp in result.get("smd_components", []):
        log.check(f"  - xname: {comp['xname']}, role: {comp['role']}, nid: {comp['nid']}")
    log.check("")

    if result["success"]:
        log.passed(
            LOG_MSGS["ochami_success"].format(count=result["total_count"]),
            "All nodes discovered in OpenCHAMI SMD"
        )
    else:
        log.failed(
            LOG_MSGS["ochami_failed"].format(
                missing_count=result.get("missing_count", 0),
                total_count=result["total_count"]
            ),
            result.get("error", "Unknown error")
        )

    assert result["success"], ASSERT_MSGS["ochami_nodes_missing"].format(
        missing_nodes=result.get("error", ""),
        total_count=result["total_count"],
        discovered_count=result["discovered_count"],
        missing_count=result.get("missing_count", 0)
    )


def test_nodes_yaml_file(host):
    """
    Test Case 3: Verify nodes.yaml file exists and is valid.
    Shows detailed nodes.yaml content.
    """
    log = TestLogger(TEST_NAMES["nodes_yaml_exists"])

    log.check("Checking nodes.yaml file")
    result = verify_nodes_yaml_file(host)

    log.check(f"File path: {result['path']}")
    log.check(f"Nodes in file: {result['nodes_count']}")
    log.check("")

    # Show expected nodes from PXE mapping
    log.check("═══ Expected Nodes (from PXE mapping) ═══")
    for func_group, nodes in result.get("nodes_by_group", {}).items():
        log.check(f"  {func_group}:")
        for node in nodes:
            log.check(f"    - {node['hostname']} ({node['admin_ip']})")
    log.check("")

    # Show nodes.yaml content
    log.check("═══ nodes.yaml Content ═══")
    for node in result.get("nodes_yaml_content", []):
        log.check(f"  - name: {node['name']}")
        log.check(f"    xname: {node['xname']}")
        log.check(f"    group: {node['group']}")
        log.check(f"    nid: {node['nid']}")
        log.check(f"    bmc_ip: {node['bmc_ip']}")
        if node.get("interfaces"):
            for iface in node["interfaces"]:
                ip_addrs = iface.get("ip_addrs", [])
                for ip in ip_addrs:
                    log.check(f"    interface: {ip.get('name', '')} = {ip.get('ip_addr', '')}")
        log.check("")

    if result["success"]:
        log.passed(
            LOG_MSGS["nodes_yaml_exists"],
            f"File contains {result['nodes_count']} nodes"
        )
    else:
        if "not found" in result["error"].lower():
            log.failed(
                LOG_MSGS["nodes_yaml_missing"].format(path=result["path"]),
                result["error"]
            )
            assert False, ASSERT_MSGS["nodes_yaml_missing"].format(path=result["path"])
        else:
            log.failed(
                LOG_MSGS["nodes_yaml_invalid"].format(error=result["error"]),
                f"Missing nodes: {', '.join(result['missing_nodes'])}"
            )
            assert False, ASSERT_MSGS["nodes_yaml_invalid"].format(
                path=result["path"],
                error=result["error"],
                missing_nodes=", ".join(result["missing_nodes"])
            )


def test_passwordless_ssh(host):
    """
    Test Case 4: Verify passwordless SSH is configured to all nodes.
    Tests SSH via BOTH hostname AND IP address.
    Results grouped by functional_group (role).
    """
    log = TestLogger(TEST_NAMES["passwordless_ssh"])

    log.check("Testing passwordless SSH to all nodes (via IP and hostname)")
    result = verify_passwordless_ssh(host)

    log.check(f"Total nodes: {result['total_count']}")
    log.check("")

    # Display results grouped by functional group
    for func_group, nodes in result.get("results_by_group", {}).items():
        log.check(f"═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            hostname = node["hostname"]
            admin_ip = node["admin_ip"]
            ssh_ip = "✓" if node.get("ssh_via_ip") else "✗"
            ssh_host = "✓" if node.get("ssh_via_hostname") else "✗"
            log.check(f"  {hostname} ({admin_ip})")
            log.check(f"    SSH via IP: {ssh_ip}  |  SSH via hostname: {ssh_host}")
        log.check("")

    if result["success"]:
        log.passed(
            LOG_MSGS["passwordless_ssh_success"].format(count=result["total_count"]),
            "All nodes accessible without password"
        )
    else:
        log.failed(
            LOG_MSGS["passwordless_ssh_failed"].format(
                failed_count=result["failed_count"],
                total_count=result["total_count"]
            ),
            f"Failed nodes: {', '.join(result['failed_nodes'])}"
        )

    assert result["success"], ASSERT_MSGS["passwordless_ssh_failed"].format(
        failed_nodes=", ".join(result["failed_nodes"]),
        total_count=result["total_count"],
        success_count=result["success_count"],
        failed_count=result["failed_count"],
        first_failed_ip=(
            result["failed_nodes"][0].split("(")[1].rstrip(")")
            if result["failed_nodes"] else ""
        ),
    )


def test_node_hostnames(host):
    """
    Test Case 6: Verify node hostnames match PXE mapping.
    Results grouped by functional_group (role).
    """
    log = TestLogger(TEST_NAMES["node_hostnames"])

    log.check("Verifying hostnames on all nodes")
    result = verify_node_hostnames(host)

    log.check(f"Total nodes: {result['total_count']}")
    log.check("")

    # Display results grouped by functional group
    for func_group, nodes in result.get("results_by_group", {}).items():
        log.check(f"═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            expected = node["expected"]
            actual = node["actual"]
            match = node["match"]
            status = "✓" if match else "✗"
            log.check(f"  {status} {expected} ({node['admin_ip']})")
            log.check(f"    Expected: {expected}  |  Actual: {actual}")
        log.check("")

    if result["success"]:
        log.passed(
            LOG_MSGS["node_hostnames_success"].format(count=result["total_count"]),
            "All hostnames match PXE mapping"
        )
    else:
        log.failed(
            LOG_MSGS["node_hostnames_failed"].format(
                mismatch_count=result["mismatch_count"],
                total_count=result["total_count"]
            ),
            result.get("error", "")
        )

    # Get first failed node for error message
    first_failed = None
    for nodes in result.get("results_by_group", {}).values():
        for node in nodes:
            if not node["match"]:
                first_failed = node
                break
        if first_failed:
            break

    assert result["success"], ASSERT_MSGS["node_hostnames_mismatch"].format(
        mismatch_count=result["mismatch_count"],
        total_count=result["total_count"],
        mismatch_details=result.get("error", ""),
        first_failed_ip=first_failed["admin_ip"] if first_failed else "",
        expected_hostname=first_failed["expected"] if first_failed else ""
    )


# =============================================================================
# NODE BOOT AND PACKAGE VALIDATION TESTS
# =============================================================================

def test_node_boot(host):
    """Test Case 8: Verify all nodes have booted successfully."""
    log = TestLogger("Node Boot Validation")

    log.check("Checking if all nodes are booted and reachable")
    result = validate_node_boot(host)

    log.check(f"Total: {result['total_count']} | Booted: {result['booted_count']}")
    log.check("")

    for func_group, nodes in result.get("results_by_group", {}).items():
        log.check(f"═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            status = "✓" if node["booted"] else "✗"
            uptime = node.get("uptime", "")[:50] if node["booted"] else node.get("error", "")
            log.check(f"  {status} {node['hostname']} → {uptime}")
        log.check("")

    if result["success"]:
        log.passed(f"All {result['booted_count']} nodes booted", "Nodes are operational")
    else:
        log.failed(f"{len(result['failed_nodes'])} nodes not booted", str(result["failed_nodes"]))

    assert result["success"], f"Nodes not booted: {result['failed_nodes']}"


def test_bmc_group_csv(host):
    """Test Case 9: Verify BMC group CSV with detailed content."""
    log = TestLogger("BMC Group CSV Validation")

    log.check("Checking BMC group CSV file")
    result = validate_bmc_group_csv(host)

    log.check(f"Path: {result['path']}")
    log.check(f"BMC entries: {result['bmc_count']}")
    log.check("")

    if result["bmc_entries"]:
        log.check("═══ BMC Entries (first 10) ═══")
        for entry in result["bmc_entries"][:10]:
            log.check(f"  - BMC={entry['bmc_ip']}, Group={entry['group']}")
        log.check("")

    if result["success"]:
        log.passed(f"BMC CSV valid with {result['bmc_count']} entries", "File is valid")
    else:
        log.failed("BMC CSV validation failed", result["error"])

    assert result["success"], f"BMC CSV error: {result['error']}"


# =============================================================================
# CONSOLIDATED VALIDATION TESTS (All nodes, grouped by functional group)
# =============================================================================

def test_all_services(host):
    """Test Case 10: Verify sssd, munge, slurmd services on ALL nodes."""
    log = TestLogger("Service Validation (All Nodes)")

    log.check("Checking sssd, munge, slurmd on all nodes")
    result = validate_all_services(host)

    if result.get("skipped"):
        log.skipped(result["error"], "No nodes found")
        pytest.skip("No nodes found in PXE mapping")

    failed_nodes = []
    for func_group, nodes in result.get("group_results", {}).items():
        log.check(f"\n═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            hostname = node["hostname"]
            services = node.get("services", {})
            node_ok = all(s["active"] for s in services.values())
            status = "✓" if node_ok else "✗"
            log.check(f"  {status} {hostname} ({node.get('admin_ip', '')})")
            for svc_name, svc_data in services.items():
                svc_status = "✓" if svc_data["active"] else "✗"
                log.check(f"      {svc_status} {svc_name}: {svc_data['output']}")
            if not node_ok:
                failed_nodes.append(hostname)

    log.check("")
    if result["success"]:
        log.passed("All services active on all nodes", "sssd, munge, slurmd running everywhere")
    else:
        log.failed(f"Services failed on: {', '.join(failed_nodes)}", result["error"])

    assert result["success"], f"Services failed: {result['error']}"


def test_all_sinfo(host):
    """Test Case 11: Verify sinfo command works on ALL nodes."""
    log = TestLogger("Slurm sinfo Validation (All Nodes)")

    log.check("Running sinfo on all nodes")
    result = validate_all_sinfo(host)

    if result.get("skipped"):
        log.skipped(result["error"], "No nodes found")
        pytest.skip("No nodes found in PXE mapping")

    failed_nodes = []
    for func_group, nodes in result.get("group_results", {}).items():
        log.check(f"\n═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            hostname = node["hostname"]
            status = "✓" if node["success"] else "✗"
            log.check(f"  {status} {hostname}:")
            if node["success"]:
                for line in node["output"].split('\n')[:10]:
                    log.check(f"      {line}")
            else:
                log.check(f"      Error: {node['error']}")
            if not node["success"]:
                failed_nodes.append(hostname)

    log.check("")
    if result["success"]:
        log.passed("sinfo working on all nodes", "Slurm cluster visible from all nodes")
    else:
        log.failed(f"sinfo failed on: {', '.join(failed_nodes)}", result["error"])

    assert result["success"], f"sinfo failed: {result['error']}"


def test_all_ldap(host):
    """Test Case 12: Verify LDAP users accessible on ALL nodes."""
    log = TestLogger("LDAP Validation (All Nodes)")
    log.check("Checking LDAP users (UID >= 1000) on all nodes")
    result = validate_all_ldap(host)

    if result.get("skipped"):
        log.skipped(result["error"], "No nodes found")
        pytest.skip("No nodes found in PXE mapping")

    failed_nodes = []
    for func_group, nodes in result.get("group_results", {}).items():
        log.check(f"\n═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            hostname = node["hostname"]
            status = "✓" if node["success"] else "✗"
            users = node.get("users", [])
            if users:
                user_list = ", ".join(users[:5])
                extra = f" (+{len(users)-5} more)" if len(users) > 5 else ""
                log.check(f"  {status} {hostname}: {len(users)} users [{user_list}{extra}]")
            else:
                log.check(f"  {status} {hostname}: {node.get('error', 'No users')}")
            if not node["success"]:
                failed_nodes.append(hostname)

    log.check("")
    if result["success"]:
        log.passed("LDAP working on all nodes", "Directory users accessible everywhere")
    else:
        log.failed(f"LDAP failed on: {', '.join(failed_nodes)}", result["error"])

    assert result["success"], f"LDAP failed: {result['error']}"


# =============================================================================
# KUBERNETES VALIDATION TEST
# =============================================================================

def test_kubernetes_nodes(host):
    """Test Case 13: Verify K8s nodes via kubectl get nodes -A."""
    log = TestLogger("Kubernetes Nodes Validation (All Control Planes)")

    log.check("Running 'kubectl get nodes -A' on all kube control plane nodes")
    result = validate_kubernetes_nodes(host)

    if result.get("skipped"):
        log.skipped(result["error"], "No kube control plane nodes in PXE mapping")
        pytest.skip("No kube control plane nodes in PXE mapping")

    failed_cps = []
    for cp in result.get("control_plane_results", []):
        hostname = cp["hostname"]
        admin_ip = cp.get("admin_ip", "")
        log.check(f"\n═══ {hostname} ({admin_ip}) ═══")

        if not cp["success"]:
            log.check(f"  ✗ Error: {cp['error']}")
            failed_cps.append(hostname)
            continue

        log.check(f"  Total K8s nodes: {cp['total_nodes']} | Ready: {cp['ready_count']}")
        log.check(f"  {'NAME':<20} {'STATUS':<10} {'ROLES':<18} {'AGE':<10} {'VERSION'}")
        log.check(f"  {'-'*20} {'-'*10} {'-'*18} {'-'*10} {'-'*10}")
        for k8s_node in cp.get("k8s_nodes", []):
            status_icon = "✓" if k8s_node["status"].lower() == "ready" else "✗"
            log.check(
                f"  {status_icon} {k8s_node['name']:<18} {k8s_node['status']:<10} "
                f"{k8s_node['roles']:<18} {k8s_node['age']:<10} {k8s_node['version']}"
            )

        if cp.get("not_ready"):
            failed_cps.append(hostname)

    log.check("")
    if result["success"]:
        total = sum(
            cp.get("total_nodes", 0)
            for cp in result["control_plane_results"]
        )
        log.passed(
            f"All K8s nodes Ready ({total} nodes)",
            "Cluster is healthy",
        )
    else:
        log.failed(f"K8s issues on: {', '.join(failed_cps)}", result["error"])

    assert result["success"], f"Kubernetes failed: {result['error']}"
