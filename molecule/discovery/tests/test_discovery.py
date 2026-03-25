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
    verify_nodes_yaml_file,
    verify_passwordless_ssh,
    verify_node_hostnames,
    # New validation functions
    validate_node_boot,
    validate_bmc_group_csv,
    validate_slurm_sinfo,
    validate_slurm_services,
    validate_ldap_login_non_slurm,
    validate_ldap_login_slurm_nodes,
    validate_kubernetes_nodes,
)


# =============================================================================
# DISCOVERY TEST CASES
# =============================================================================

def test_nodes_ssh_reachable(host):
    """
    Verify all nodes from PXE mapping are reachable via SSH.
    Results grouped by functional_group (role).
    """
    log = TestLogger(TEST_NAMES["nodes_ssh_reachable"])

    log.check("Testing SSH connectivity to all nodes from PXE mapping →")
    result = verify_nodes_ssh_reachable(host)

    log.check(f"Total nodes: {result['total_count']} →")
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


def test_nodes_yaml_file(host):
    """
    Verify nodes.yaml file exists and is valid.
    Shows detailed nodes.yaml content.
    """
    log = TestLogger(TEST_NAMES["nodes_yaml_exists"])

    log.check("Checking nodes.yaml file →")
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
    Verify passwordless SSH is configured to all nodes.
    Tests SSH via BOTH hostname AND IP address.
    Results grouped by functional_group (role).
    """
    log = TestLogger(TEST_NAMES["passwordless_ssh"])

    log.check("Testing passwordless SSH to all nodes (via IP and hostname) →")
    result = verify_passwordless_ssh(host)

    log.check(f"Total nodes: {result['total_count']} →")
    log.check("")

    # Display results grouped by functional group
    for func_group, nodes in result.get("results_by_group", {}).items():
        log.check(f"═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            hostname = node["hostname"]
            admin_ip = node["admin_ip"]
            ssh_ip = "✓" if node.get("ssh_via_ip") else "✗"
            ssh_host = "✓" if node.get("ssh_via_hostname") else "✗"
            log.check(f"  {hostname} ({admin_ip}) →")
            log.check(f"    SSH via IP: {ssh_ip}  →  SSH via hostname: {ssh_host}")
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
    Verify node hostnames match PXE mapping.
    Results grouped by functional_group (role).
    """
    log = TestLogger(TEST_NAMES["node_hostnames"])

    log.check("Verifying hostnames on all nodes →")
    result = verify_node_hostnames(host)

    log.check(f"Total nodes: {result['total_count']} →")
    log.check("")

    # Display results grouped by functional group
    for func_group, nodes in result.get("results_by_group", {}).items():
        log.check(f"═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            expected = node["expected"]
            actual = node["actual"]
            match = node["match"]
            status = "✓" if match else "✗"
            log.check(f"  {status} {expected} ({node['admin_ip']}) →")
            log.check(f"    Expected: {expected}  →  Actual: {actual}")
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
    """Verify all nodes have booted successfully."""
    log = TestLogger("Node Boot Validation")

    log.check("Checking if all nodes are booted and reachable →")
    result = validate_node_boot(host)

    log.check(f"Total: {result['total_count']} | Booted: {result['booted_count']} →")
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
    """Verify BMC group CSV against PXE mapping and OIM BMC IP."""
    log = TestLogger("BMC Group CSV Validation")

    log.check("Checking BMC group CSV against PXE mapping →")
    result = validate_bmc_group_csv(host)

    log.check(f"Path: {result['path']}")
    log.check(f"BMC entries in CSV: {result['bmc_count']}")
    log.check(f"PXE mapping nodes: {result.get('pxe_node_count', 0)}")
    log.check("")

    if result["bmc_entries"]:
        log.check("═══ BMC Entries (first 10) ═══")
        for entry in result["bmc_entries"][:10]:
            log.check(
                f"  - BMC={entry['bmc_ip']}, "
                f"Group={entry['group']} → "
                f"Parent={entry['parent']}"
            )
        if result["bmc_count"] > 10:
            log.check(f"  ... and {result['bmc_count'] - 10} more")
        log.check("")

    if result.get("missing_groups"):
        log.check("═══ Missing Groups ═══")
        for item in result["missing_groups"]:
            log.check(
                f"  ✗ {item['hostname']}: "
                f"group={item['group_name']} not in CSV →"
            )
        log.check("")

    if result.get("missing_parents"):
        log.check("═══ Missing Parents ═══")
        for item in result["missing_parents"]:
            log.check(
                f"  ✗ {item['hostname']}: "
                f"parent={item['parent_service_tag']} not in CSV →"
            )
        log.check("")

    oim_ip = result.get("oim_bmc_ip", "")
    if oim_ip:
        status = "✗" if result.get("oim_bmc_missing") else "✓"
        log.check(f"OIM BMC IP: {status} {oim_ip} →")
        log.check("")

    if result["success"]:
        log.passed(
            f"BMC CSV valid: {result['bmc_count']} entries, "
            f"{result.get('pxe_node_count', 0)} PXE nodes checked",
            "All groups, parents, and OIM BMC IP verified"
        )
    else:
        log.failed("BMC CSV validation failed", result["error"])

    assert result["success"], f"BMC CSV error: {result['error']}"


# =============================================================================
# CONSOLIDATED VALIDATION TESTS (All nodes, grouped by functional group)
# =============================================================================

def test_all_services(host):
    """Verify Slurm services on Slurm nodes only."""
    log = TestLogger("Service Validation (Slurm Nodes Only)")

    log.check("Checking Slurm services on Slurm nodes only →")
    result = validate_slurm_services(host)

    if result.get("skipped"):
        log.skipped(result["error"], "No Slurm nodes found")
        pytest.skip("No Slurm nodes found in PXE mapping")

    failed_nodes = []
    for func_group, nodes in result.get("group_results", {}).items():
        log.check(f"\n═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            hostname = node["hostname"]
            services = node.get("services", {})
            node_ok = node.get("node_ok", False)
            status = "✓" if node_ok else "✗"
            log.check(f"  {status} {hostname} ({node.get('admin_ip', '')})")
            for svc_name, svc_data in services.items():
                svc_status = "✓" if svc_data["active"] else "✗"
                log.check(f"      {svc_status} {svc_name}: {svc_data['output']} →")
            if not node_ok:
                failed_nodes.append(hostname)

    log.check("")
    if result["success"]:
        log.passed(
            "All Slurm services active on Slurm nodes", 
            "sssd, munge, slurmd/slurmctld running on Slurm nodes"
        )
    else:
        log.failed(f"Services failed on: {', '.join(failed_nodes)}", result["error"])

    assert result["success"], f"Services failed: {result['error']}"


def test_all_sinfo(host):
    """Verify sinfo command works on Slurm nodes only."""
    log = TestLogger("Slurm sinfo Validation (Slurm Nodes Only)")

    log.check("Running sinfo on Slurm nodes only →")
    result = validate_slurm_sinfo(host)

    if result.get("skipped"):
        log.skipped(result["error"], "No Slurm nodes found")
        pytest.skip("No Slurm nodes found in PXE mapping")

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
                log.check(f"      Error: {node['error']} →")
            if not node["success"]:
                failed_nodes.append(hostname)

    log.check("")
    if result["success"]:
        log.passed("sinfo working on all Slurm nodes", "Slurm cluster visible from Slurm nodes")
    else:
        log.failed(f"sinfo failed on: {', '.join(failed_nodes)}", result["error"])

    assert result["success"], f"sinfo failed: {result['error']}"


def test_ldap_login_non_slurm(host):
    """Verify LDAP user can SSH login on non-slurm nodes.

    Non-slurm nodes (login, kube_control_plane, etc.) should always
    allow LDAP user SSH login.
    Reads ldap_user and ldap_password from user_config.yml.
    """
    log = TestLogger("LDAP Login - Non-Slurm Nodes")
    log.check("Testing LDAP user SSH login on non-slurm nodes →")
    result = validate_ldap_login_non_slurm(host)

    if result.get("skipped"):
        log.skipped(result["error"], "Skipped")
        pytest.skip(result["error"])

    ldap_user = result.get("ldap_user", "")
    log.check(f"LDAP user: {ldap_user} →")
    log.check("")

    failed_nodes = []
    for func_group, nodes in result.get("group_results", {}).items():
        log.check(f"═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            hostname = node.get("hostname", "")
            login_ok = node.get("login_success", False)
            status = "✓" if login_ok else "✗"
            detail = node.get("output", "") if login_ok else node.get("error", "Login failed")
            log.check(f"  {status} {hostname} ({node.get('admin_ip', '')}): {detail} →")
            if not login_ok:
                failed_nodes.append(hostname)
        log.check("")

    if result["success"]:
        log.passed("LDAP login works on all non-slurm nodes", f"User: {ldap_user}")
    else:
        log.failed(f"LDAP login failed on: {', '.join(failed_nodes)}", result["error"])

    assert result["success"], f"LDAP login failed: {result['error']}"


def test_ldap_login_slurm_nodes(host):
    """Verify LDAP user login behavior on slurm nodes.

    On slurm compute nodes (pam_slurm_adopt):
    - If LDAP user has NO running jobs -> SSH login should be BLOCKED
    - If LDAP user has running jobs -> SSH login should be ALLOWED
    Reads ldap_user and ldap_password from user_config.yml.
    """
    log = TestLogger("LDAP Login - Slurm Nodes")
    log.check("Testing LDAP user SSH login behavior on slurm compute nodes →")
    result = validate_ldap_login_slurm_nodes(host)

    if result.get("skipped"):
        log.skipped(result["error"], "Skipped")
        pytest.skip(result["error"])

    ldap_user = result.get("ldap_user", "")
    log.check(f"LDAP user: {ldap_user} →")
    log.check("")

    failed_nodes = []
    for func_group, nodes in result.get("group_results", {}).items():
        log.check(f"═══ {func_group} ({len(nodes)} nodes) ═══")
        for node in nodes:
            hostname = node.get("hostname", "")
            correct = node.get("correct", False)
            job_info = "has jobs" if node.get("has_jobs") else "no jobs"
            login_info = "login OK" if node.get("login_success") else "login blocked"
            expected_info = "should allow" if node.get("expected_login") else "should block"
            log.check(
                f"  {'✓' if correct else '✗'} {hostname}: "
                f"{job_info} | {login_info} | {expected_info} →"
            )
            if not correct:
                log.check(f"      Error: {node.get('error', '')} →")
                failed_nodes.append(hostname)
        log.check("")

    if result["success"]:
        log.passed(
            "LDAP login behavior correct on all slurm nodes",
            f"User: {ldap_user} - pam_slurm_adopt working as expected",
        )
    else:
        log.failed(f"Incorrect behavior on: {', '.join(failed_nodes)}", result["error"])

    assert result["success"], f"LDAP slurm login: {result['error']}"


# =============================================================================
# KUBERNETES VALIDATION TEST
# =============================================================================

def test_kubernetes_nodes(host):
    """Verify K8s nodes via kubectl get nodes -A."""
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
        log.check(f"\n═══ {hostname} ({admin_ip}) ═══ →")

        if not cp["success"]:
            log.check(f"  ✗ Error: {cp['error']} →")
            failed_cps.append(hostname)
            continue

        log.check(f"  Total K8s nodes: {cp['total_nodes']} → Ready: {cp['ready_count']}")
        log.check(f"  {'NAME':<20} {'STATUS':<10} {'ROLES':<18} {'AGE':<10} {'VERSION'}")
        log.check(f"  {'-'*20} {'-'*10} {'-'*18} {'-'*10} {'-'*10}")
        for k8s_node in cp.get("k8s_nodes", []):
            log.check(
                f"                {k8s_node['name']:<18} {k8s_node['status']:<10} "
                f"{k8s_node['roles']:<18} {k8s_node['age']:<10} {k8s_node['version']} →"
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
