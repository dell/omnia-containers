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
Discovery Slurm Test Cases.

Test cases for verifying Slurm cluster:
1. Services on slurm_control_node (slurmctld, slurmdbd, munge, mariadb, sssd if enabled)
2. Services on slurm_node (slurmd, munge, sssd if enabled)
3. Services on login_node (slurmd, munge, sssd if enabled)
4. Services on login_compiler_node (slurmd, munge, sssd if enabled)
5. Cross-node SSH between all Slurm nodes
6. sinfo shows all compute nodes
7. OpenMPI installation (if enabled in software_config.json)
8. UCX installation (if enabled in software_config.json)
9. LDAP slapd.conf configuration (if OpenLDAP enabled)
"""

import pytest
from automation_library.core import TestLogger, check_nodes_reachability
from automation_library.discovery.functions import (
    get_all_slurm_nodes,
    get_slurm_control_nodes,
    get_slurm_compute_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
    is_openldap_enabled,
    is_ldms_enabled,
    skip_if_openmpi_not_enabled,
    skip_if_ucx_not_enabled,
    skip_if_openldap_not_enabled,
    verify_services_on_nodes,
    verify_cross_node_ssh,
    verify_sinfo_nodes,
    verify_openmpi_installed,
    verify_ucx_installed,
    apply_slapd_conf_and_verify,
    build_service_details,
)
from automation_library.discovery.vars import (
    SLURM_CONTROL_SERVICES,
    SLURM_NODE_SERVICES,
    LOGIN_NODE_SERVICES,
    DISCOVERY_REACHABILITY_RETRY,
    DISCOVERY_REACHABILITY_INTERVAL,
)
from automation_library.discovery.messages import TEST_ASSERT_MSGS as ASSERT_MSGS


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(10)
def test_slurm_control_node_services(host):
    """
    Test Case 10: Verify services on slurm_control_node.

    Services: slurmctld, slurmdbd, munge, mariadb
    If OpenLDAP enabled: sssd
    If LDMS enabled: ldmsd.sampler
    """
    log = TestLogger("Verify slurm_control_node services")

    nodes = get_slurm_control_nodes(host)
    if not nodes:
        log.skipped("No slurm_control_node in PXE mapping", "Check PXE mapping file")
        pytest.skip("No slurm_control_node in PXE mapping")

    # Check reachability with retry
    reach = check_nodes_reachability(
        host, nodes,
        retry_limit=DISCOVERY_REACHABILITY_RETRY,
        retry_interval=DISCOVERY_REACHABILITY_INTERVAL
    )

    # Report unreachable nodes
    if reach["unreachable"]:
        unreachable_details = []
        for node in reach["unreachable"]:
            unreachable_details.append(
                f"  ✗ {node['hostname']} ({node['admin_ip']}): not reachable"
            )
        log.check(f"Unreachable nodes ({len(reach['unreachable'])}):")
        for detail in unreachable_details:
            print(detail)

    openldap_enabled = is_openldap_enabled(host)
    ldms_enabled = is_ldms_enabled(host)

    services = list(SLURM_CONTROL_SERVICES)
    if openldap_enabled:
        services.append("sssd")
    if ldms_enabled:
        services.append("ldmsd.sampler")

    # Build note for enabled features
    notes = []
    if openldap_enabled:
        notes.append("openldap")
    if ldms_enabled:
        notes.append("ldms")
    note_str = f" ({', '.join(notes)} enabled)" if notes else ""

    log.check(f"Checking services on {len(reach['reachable'])} slurm_control_node{note_str}")

    if reach["reachable"]:
        result = verify_services_on_nodes(host, reach["reachable"], services)
        details = build_service_details(result)
    else:
        result = {"success": False, "failed_details": ["No reachable nodes"]}
        details = "No reachable nodes to check"

    # Fail if any unreachable or service check failed
    if reach["unreachable"] or not result["success"]:
        fail_parts = []
        if reach["unreachable"]:
            fail_parts.append(
                f"Unreachable: {', '.join(n['hostname'] for n in reach['unreachable'])}"
            )
        if not result["success"]:
            fail_parts.append(f"Services failed: {', '.join(result['failed_details'])}")
        log.failed("slurm_control_node services check failed", details)
        assert False, "; ".join(fail_parts)

    log.passed("All services running on slurm_control_node", details)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(11)
def test_slurm_node_services(host):
    """
    Test Case 11: Verify services on slurm_node (compute nodes).

    Services: slurmd, munge
    If OpenLDAP enabled: sssd
    If LDMS enabled: ldmsd.sampler
    """
    log = TestLogger("Verify slurm_node services")

    nodes = get_slurm_compute_nodes(host)
    if not nodes:
        log.skipped("No slurm_node in PXE mapping", "Check PXE mapping file")
        pytest.skip("No slurm_node in PXE mapping")

    # Check reachability with retry
    reach = check_nodes_reachability(
        host, nodes,
        retry_limit=DISCOVERY_REACHABILITY_RETRY,
        retry_interval=DISCOVERY_REACHABILITY_INTERVAL
    )

    if reach["unreachable"]:
        log.check(f"Unreachable nodes ({len(reach['unreachable'])}):")
        for node in reach["unreachable"]:
            print(f"  ✗ {node['hostname']} ({node['admin_ip']}): not reachable")

    openldap_enabled = is_openldap_enabled(host)
    ldms_enabled = is_ldms_enabled(host)

    services = list(SLURM_NODE_SERVICES)
    if openldap_enabled:
        services.append("sssd")
    if ldms_enabled:
        services.append("ldmsd.sampler")

    notes = []
    if openldap_enabled:
        notes.append("openldap")
    if ldms_enabled:
        notes.append("ldms")
    note_str = f" ({', '.join(notes)} enabled)" if notes else ""

    log.check(f"Checking services on {len(reach['reachable'])} slurm_node{note_str}")

    if reach["reachable"]:
        result = verify_services_on_nodes(host, reach["reachable"], services)
        details = build_service_details(result)
    else:
        result = {"success": False, "failed_details": ["No reachable nodes"]}
        details = "No reachable nodes to check"

    if reach["unreachable"] or not result["success"]:
        fail_parts = []
        if reach["unreachable"]:
            fail_parts.append(
                f"Unreachable: {', '.join(n['hostname'] for n in reach['unreachable'])}"
            )
        if not result["success"]:
            fail_parts.append(f"Services failed: {', '.join(result['failed_details'])}")
        log.failed("slurm_node services check failed", details)
        assert False, "; ".join(fail_parts)

    log.passed("All services running on slurm_node", details)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(12)
def test_login_node_services(host):
    """
    Test Case 12: Verify services on login_node.

    Services: slurmd, munge
    If OpenLDAP enabled: sssd
    If LDMS enabled: ldmsd.sampler
    """
    log = TestLogger("Verify login_node services")

    nodes = get_login_nodes(host)
    if not nodes:
        log.skipped("No login_node in PXE mapping", "Check PXE mapping file")
        pytest.skip("No login_node in PXE mapping")

    # Check reachability with retry
    reach = check_nodes_reachability(
        host, nodes,
        retry_limit=DISCOVERY_REACHABILITY_RETRY,
        retry_interval=DISCOVERY_REACHABILITY_INTERVAL
    )

    if reach["unreachable"]:
        log.check(f"Unreachable nodes ({len(reach['unreachable'])}):")
        for node in reach["unreachable"]:
            print(f"  ✗ {node['hostname']} ({node['admin_ip']}): not reachable")

    openldap_enabled = is_openldap_enabled(host)
    ldms_enabled = is_ldms_enabled(host)

    services = list(LOGIN_NODE_SERVICES)
    if openldap_enabled:
        services.append("sssd")
    if ldms_enabled:
        services.append("ldmsd.sampler")

    notes = []
    if openldap_enabled:
        notes.append("openldap")
    if ldms_enabled:
        notes.append("ldms")
    note_str = f" ({', '.join(notes)} enabled)" if notes else ""

    log.check(f"Checking services on {len(reach['reachable'])} login_node{note_str}")

    if reach["reachable"]:
        result = verify_services_on_nodes(host, reach["reachable"], services)
        details = build_service_details(result)
    else:
        result = {"success": False, "failed_details": ["No reachable nodes"]}
        details = "No reachable nodes to check"

    if reach["unreachable"] or not result["success"]:
        fail_parts = []
        if reach["unreachable"]:
            fail_parts.append(
                f"Unreachable: {', '.join(n['hostname'] for n in reach['unreachable'])}"
            )
        if not result["success"]:
            fail_parts.append(f"Services failed: {', '.join(result['failed_details'])}")
        log.failed("login_node services check failed", details)
        assert False, "; ".join(fail_parts)

    log.passed("All services running on login_node", details)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(13)
def test_login_compiler_node_services(host):
    """
    Test Case 13: Verify services on login_compiler_node.

    Services: slurmd, munge
    If OpenLDAP enabled: sssd
    If LDMS enabled: ldmsd.sampler
    """
    log = TestLogger("Verify login_compiler_node services")

    nodes = get_login_compiler_nodes(host)
    if not nodes:
        log.skipped("No login_compiler_node in PXE mapping", "Check PXE mapping file")
        pytest.skip("No login_compiler_node in PXE mapping")

    # Check reachability with retry
    reach = check_nodes_reachability(
        host, nodes,
        retry_limit=DISCOVERY_REACHABILITY_RETRY,
        retry_interval=DISCOVERY_REACHABILITY_INTERVAL
    )

    if reach["unreachable"]:
        log.check(f"Unreachable nodes ({len(reach['unreachable'])}):")
        for node in reach["unreachable"]:
            print(f"  ✗ {node['hostname']} ({node['admin_ip']}): not reachable")

    openldap_enabled = is_openldap_enabled(host)
    ldms_enabled = is_ldms_enabled(host)

    services = list(LOGIN_NODE_SERVICES)
    if openldap_enabled:
        services.append("sssd")
    if ldms_enabled:
        services.append("ldmsd.sampler")

    notes = []
    if openldap_enabled:
        notes.append("openldap")
    if ldms_enabled:
        notes.append("ldms")
    note_str = f" ({', '.join(notes)} enabled)" if notes else ""

    log.check(f"Checking services on {len(reach['reachable'])} login_compiler_node{note_str}")

    if reach["reachable"]:
        result = verify_services_on_nodes(host, reach["reachable"], services)
        details = build_service_details(result)
    else:
        result = {"success": False, "failed_details": ["No reachable nodes"]}
        details = "No reachable nodes to check"

    if reach["unreachable"] or not result["success"]:
        fail_parts = []
        if reach["unreachable"]:
            fail_parts.append(
                f"Unreachable: {', '.join(n['hostname'] for n in reach['unreachable'])}"
            )
        if not result["success"]:
            fail_parts.append(f"Services failed: {', '.join(result['failed_details'])}")
        log.failed("login_compiler_node services check failed", details)
        assert False, "; ".join(fail_parts)

    log.passed("All services running on login_compiler_node", details)


# =============================================================================
# CROSS-NODE SSH TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(14)
def test_cross_node_ssh(host):
    """
    Test Case 14: Verify passwordless SSH between all Slurm cluster nodes.

    Shows detailed output grouped by source node.
    """
    log = TestLogger("Verify cross-node SSH between Slurm nodes")

    all_nodes = get_all_slurm_nodes(host)
    if len(all_nodes) < 2:
        log.skipped("Less than 2 Slurm nodes", "Need at least 2 nodes")
        pytest.skip("Less than 2 Slurm nodes")

    # Check reachability with retry
    reach = check_nodes_reachability(
        host, all_nodes,
        retry_limit=DISCOVERY_REACHABILITY_RETRY,
        retry_interval=DISCOVERY_REACHABILITY_INTERVAL
    )

    if reach["unreachable"]:
        log.check(f"Unreachable nodes ({len(reach['unreachable'])}):")
        for node in reach["unreachable"]:
            print(f"  ✗ {node['hostname']} ({node['admin_ip']}): not reachable")

    log.check(f"Testing cross-node SSH for {len(reach['reachable'])} reachable Slurm nodes")

    if reach["reachable"]:
        result = verify_cross_node_ssh(host)
    else:
        result = {"success": False, "total_pairs": 0, "failed": 0, "failed_pairs": []}

    # Fail if any unreachable or SSH failed
    if reach["unreachable"] or not result["success"]:
        fail_parts = []
        if reach["unreachable"]:
            fail_parts.append(
                f"Unreachable: {', '.join(n['hostname'] for n in reach['unreachable'])}"
            )
        if not result["success"]:
            fail_parts.append(f"SSH failed: {result['failed']} pairs")
        log.failed("Cross-node SSH test failed", "; ".join(fail_parts))
        assert False, "; ".join(fail_parts)

    # Build detailed output grouped by source node
    details_lines = [f"Total pairs tested: {result['total_pairs']}"]
    for node_result in result.get("node_results", []):
        src_status = "✓" if node_result["all_ok"] else "✗"
        details_lines.append(f"{src_status} From {node_result['source']}:")
        for target in node_result["targets"]:
            tgt_status = "✓" if target["success"] else "✗"
            details_lines.append(f"    {tgt_status} → {target['hostname']}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(f"Cross-node SSH working for all {result['total_pairs']} pairs", details)
    else:
        log.failed(f"Cross-node SSH failed for {result['failed']} pairs", details)

    assert result["success"], f"Cross-node SSH failed: {', '.join(result['failed_pairs'][:5])}"


# =============================================================================
# SINFO AND SOFTWARE TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(15)
def test_sinfo_nodes(host):
    """
    Test Case 15: Verify sinfo shows exactly the compute nodes from PXE mapping.

    Fails if any expected node is missing OR if any extra node is found.
    """
    log = TestLogger("Verify sinfo shows compute nodes")

    result = verify_sinfo_nodes(host)

    if not result["expected"]:
        log.skipped("No slurm_node in PXE mapping", "Check PXE mapping file")
        pytest.skip("No slurm_node in PXE mapping")

    if result.get("error"):
        log.failed("sinfo check failed", result["error"])
        assert False, result["error"]

    # Build details
    details_lines = [
        f"Expected: {', '.join(result['expected'])}",
        f"Found: {', '.join(result['found'])}",
    ]
    if result["missing"]:
        details_lines.append(f"Missing: {', '.join(result['missing'])}")
    if result["extra"]:
        details_lines.append(f"Extra (not in PXE mapping): {', '.join(result['extra'])}")

    details = "\n".join(details_lines)

    error_parts = []
    if result.get("missing"):
        error_parts.append(f"missing: {', '.join(result['missing'])}")
    if result.get("extra"):
        error_parts.append(f"extra: {', '.join(result['extra'])}")

    if result["success"]:
        log.passed(f"sinfo shows exactly {len(result['expected'])} compute nodes", details)
    else:
        log.failed(f"sinfo node mismatch - {'; '.join(error_parts)}", details)

    err_msg = '; '.join(error_parts) if error_parts else 'unknown'
    assert result["success"], f"sinfo mismatch: {err_msg}"


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(19)
def test_openmpi_installed(host):
    """
    Test Case 16: Verify OpenMPI is installed and version matches software_config.json.

    Skips if OpenMPI is not enabled in software_config.json.
    """
    log = TestLogger("Verify OpenMPI installation")

    skip_if_openmpi_not_enabled(host, log)

    result = verify_openmpi_installed(host)

    if result.get("error") and "No login_compiler_node" in result["error"]:
        log.skipped("No login_compiler_node in PXE mapping", result["error"])
        pytest.skip(result["error"])

    # Build details with version info
    details_lines = [f"Installed version: {result['version']}"]
    if result.get("expected_version"):
        details_lines.append(f"Expected version: {result['expected_version']}")
        if result.get("version_match"):
            details_lines.append("Version match: ✓")
        else:
            details_lines.append("Version match: ✗")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(f"OpenMPI installed: {result['version']}", details)
    else:
        error = result.get('error', 'Unknown error')
        log.failed("OpenMPI verification failed", f"{error}\n{details}")
        assert False, result.get("error", "OpenMPI verification failed")


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(20)
def test_ucx_installed(host):
    """
    Test Case 17: Verify UCX is installed and version matches software_config.json.

    Skips if UCX is not enabled in software_config.json.
    """
    log = TestLogger("Verify UCX installation")

    skip_if_ucx_not_enabled(host, log)

    result = verify_ucx_installed(host)

    if result.get("error") and "No login_compiler_node" in result["error"]:
        log.skipped("No login_compiler_node in PXE mapping", result["error"])
        pytest.skip(result["error"])

    # Build details with version info
    details_lines = [f"Installed version: {result['version']}"]
    if result.get("expected_version"):
        details_lines.append(f"Expected version: {result['expected_version']}")
        if result.get("version_match"):
            details_lines.append("Version match: ✓")
        else:
            details_lines.append("Version match: ✗")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(f"UCX installed: {result['version']}", details)
    else:
        log.failed("UCX verification failed", f"{result.get('error', 'Unknown error')}\n{details}")
        assert False, result.get("error", "UCX verification failed")


# =============================================================================
# LDMS PLUGIN CONFIGURATION TEST (if enabled in software_config.json)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(18)
def test_ldms_sampler_plugins(host):
    """
    Test Case 18: Verify LDMS sampler plugins match telemetry_config.yml.

    Skips if LDMS is not enabled in software_config.json.
    Checks that exactly the plugins defined in telemetry_config.yml are configured
    on each Slurm node - no missing, no extra plugins.
    """
    from automation_library.discovery.functions import verify_ldms_sampler_plugins

    log = TestLogger("Verify LDMS sampler plugins configuration")

    if not is_ldms_enabled(host):
        log.skipped("LDMS not enabled in software_config.json", "Test skipped")
        pytest.skip("LDMS not enabled in software_config.json")

    result = verify_ldms_sampler_plugins(host)

    if result.get("error"):
        log.failed("LDMS plugin check failed", result["error"])
        assert False, result["error"]

    log.check(f"Checking LDMS plugins: {', '.join(result['expected_plugins'])}")

    # Build detailed output
    details_lines = [f"Expected plugins: {', '.join(result['expected_plugins'])}"]
    for node_result in result.get("node_results", []):
        status_icon = "✓" if node_result["success"] else "✗"
        details_lines.append(f"{status_icon} {node_result['hostname']}")
        details_lines.append(f"    Configured: {', '.join(node_result['configured_plugins'])}")
        if node_result.get("missing_plugins"):
            details_lines.append(f"    Missing: {', '.join(node_result['missing_plugins'])}")
        if node_result.get("extra_plugins"):
            details_lines.append(f"    Extra: {', '.join(node_result['extra_plugins'])}")
        if node_result.get("param_mismatches"):
            for mismatch in node_result["param_mismatches"]:
                details_lines.append(f"    Param mismatch: {mismatch}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("LDMS plugins configured correctly on all nodes", details)
    else:
        failed_nodes = [n["hostname"] for n in result["node_results"] if not n["success"]]
        log.failed(f"LDMS plugin mismatch on {len(failed_nodes)} nodes", details)

    assert result["success"], f"LDMS plugin mismatch on: {', '.join(failed_nodes)}"


# =============================================================================
# LDAP TESTS (if enabled in software_config.json)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(19)
def test_ldap_slapd_configuration(host):
    """
    Test Case 19: Apply external slapd.conf and verify LDAP service.

    Skips if OpenLDAP is not enabled in software_config.json.

    This test:
    1. Gets external_slapd_conf_path and ldap_server_ip from omnia_test_config.yml
    2. Backs up existing slapd.conf
    3. Copies new slapd.conf to /opt/omnia/auth/slapd.conf
    4. Restarts omnia_auth container
    5. Waits for container to be stable (30 seconds)
    6. Verifies LDAP server IP is accessible - FAILS if not accessible
    """
    log = TestLogger("Apply slapd.conf and verify LDAP service")

    skip_if_openldap_not_enabled(host, log)

    log.check("Applying external slapd.conf and verifying LDAP service")

    result = apply_slapd_conf_and_verify(host)

    if result["success"]:
        log.passed("LDAP slapd.conf applied and service verified", result["details"])
    else:
        log.failed("LDAP slapd.conf test failed", result["error"])
        assert False, f"LDAP test failed: {result['error']}"


@pytest.mark.sanity
@pytest.mark.order(16)
def test_ldap_user_login_from_oim(host):
    """
    Test Case 20: Verify LDAP users can SSH login from OIM.

    Skips if OpenLDAP is not enabled in software_config.json.

    Reads ldap_credentials from omnia_test_config.yml (format: "user1:pwd1,user2:pwd2").
    Tests SSH login from OIM to slurm_control_node, login_node, login_compiler_node.
    Note: slurm_node is tested separately (PAM blocks login).
    """
    from automation_library.discovery.functions import verify_ldap_user_login_from_oim

    log = TestLogger("Verify LDAP user SSH login from OIM")

    skip_if_openldap_not_enabled(host, log)

    log.check("Testing LDAP user SSH login from OIM")

    result = verify_ldap_user_login_from_oim(host)

    if result.get("error") and "not set in omnia_test_config" in result["error"]:
        log.skipped("LDAP credentials not configured", result["error"])
        pytest.skip(result["error"])

    if result.get("error") and "No slurm_control_node" in result["error"]:
        log.skipped("No nodes in PXE mapping", result["error"])
        pytest.skip(result["error"])

    # Build details with functional group headings and per-user results
    ldap_users = result.get("ldap_users", [])
    details_lines = [f"LDAP users: {', '.join(ldap_users)}"]
    for func_group, nodes in result.get("results_by_group", {}).items():
        details_lines.append("")
        details_lines.append(f"[{func_group}]")
        for node_result in nodes:
            node_status = "✓" if node_result["success"] else "✗"
            hostname = node_result['hostname']
            admin_ip = node_result['admin_ip']
            details_lines.append(f"  {node_status} {hostname} (IP: {admin_ip})")
            for user_result in node_result.get("user_results", []):
                user_status = "✓" if user_result["success"] else "✗"
                user = user_result['user']
                msg = user_result['message']
                details_lines.append(f"      {user_status} {user}: {msg}")

    details = "\n".join(details_lines)

    if result["success"]:
        groups = result.get("results_by_group", {})
        total_nodes = sum(len(nodes) for nodes in groups.values())
        log.passed(f"LDAP user login successful on {total_nodes} nodes from OIM", details)
    else:
        log.failed("LDAP user login failed from OIM", details)
        assert False, result.get("error", "LDAP login failed")


@pytest.mark.sanity
@pytest.mark.order(17)
def test_ldap_user_login_from_core(host):
    """
    Test Case 21: Verify LDAP users can SSH login from omnia_core container.

    Skips if OpenLDAP is not enabled in software_config.json.

    Reads ldap_credentials from omnia_test_config.yml (format: "user1:pwd1,user2:pwd2").
    Tests SSH login from omnia_core container to slurm_control_node,
    login_node, login_compiler_node.
    Note: slurm_node is tested separately (PAM blocks login).
    """
    from automation_library.discovery.functions import verify_ldap_user_login_from_core

    log = TestLogger("Verify LDAP user SSH login from omnia_core")

    skip_if_openldap_not_enabled(host, log)

    log.check("Testing LDAP user SSH login from omnia_core container")

    result = verify_ldap_user_login_from_core(host)

    if result.get("error") and "not set in omnia_test_config" in result["error"]:
        log.skipped("LDAP credentials not configured", result["error"])
        pytest.skip(result["error"])

    if result.get("error") and "No slurm_control_node" in result["error"]:
        log.skipped("No nodes in PXE mapping", result["error"])
        pytest.skip(result["error"])

    # Build details with functional group headings and per-user results
    ldap_users = result.get("ldap_users", [])
    details_lines = [f"LDAP users: {', '.join(ldap_users)}"]
    for func_group, nodes in result.get("results_by_group", {}).items():
        details_lines.append("")
        details_lines.append(f"[{func_group}]")
        for node_result in nodes:
            node_status = "✓" if node_result["success"] else "✗"
            hostname = node_result['hostname']
            admin_ip = node_result['admin_ip']
            details_lines.append(f"  {node_status} {hostname} (IP: {admin_ip})")
            for user_result in node_result.get("user_results", []):
                user_status = "✓" if user_result["success"] else "✗"
                user = user_result['user']
                msg = user_result['message']
                details_lines.append(f"      {user_status} {user}: {msg}")

    details = "\n".join(details_lines)

    if result["success"]:
        groups = result.get("results_by_group", {})
        total_nodes = sum(len(nodes) for nodes in groups.values())
        log.passed(f"LDAP login OK on {total_nodes} nodes from omnia_core", details)
    else:
        log.failed("LDAP user login failed from omnia_core", details)
        assert False, result.get("error", "LDAP login failed")


@pytest.mark.sanity
@pytest.mark.order(18)
def test_pam_slurm_adopt(host):
    """
    Test Case 22: Verify PAM slurm_adopt blocks login on slurm_node.

    Skips if OpenLDAP is not enabled in software_config.json.

    PAM slurm_adopt is default behavior on slurm_node - LDAP users cannot login
    unless they have an active job running.
    Expected message: "Access denied by pam_slurm_adopt: you have no active jobs on this node"
    """
    from automation_library.discovery.functions import verify_pam_slurm_adopt

    log = TestLogger("Verify PAM slurm_adopt on slurm_node")

    skip_if_openldap_not_enabled(host, log)

    log.check("Testing PAM slurm_adopt behavior on slurm_node")

    result = verify_pam_slurm_adopt(host)

    if result.get("error") and "not set in omnia_test_config" in result["error"]:
        log.skipped("LDAP credentials not configured", result["error"])
        pytest.skip(result["error"])

    if result.get("error") and "No slurm_node" in result["error"]:
        log.skipped("No slurm_node in PXE mapping", result["error"])
        pytest.skip(result["error"])

    # Build details with functional group headings
    ldap_users = result.get("ldap_users", [])
    details_lines = [f"LDAP user: {', '.join(ldap_users)}"]
    for func_group, nodes in result.get("results_by_group", {}).items():
        details_lines.append("")
        details_lines.append(f"[{func_group}]")
        for node_result in nodes:
            status = "✓" if node_result["success"] else "✗"
            blocked = " (blocked)" if node_result.get("login_blocked") else ""
            details_lines.append(f"  {status} {node_result['hostname']}{blocked}")
            details_lines.append(f"      IP: {node_result['admin_ip']}")
            details_lines.append(f"      {node_result['message']}")

    details = "\n".join(details_lines)

    if result["success"]:
        total_nodes = sum(len(nodes) for nodes in result.get("results_by_group", {}).values())
        log.passed(f"PAM correctly blocking login on {total_nodes} slurm nodes", details)
    else:
        log.failed("PAM slurm_adopt not working correctly", details)
        assert False, result.get("error", "PAM test failed")


@pytest.mark.sanity
@pytest.mark.order(23)
def test_pam_slurm_adopt_session_termination(host):
    """
    Test Case 23: Verify PAM slurm_adopt session termination behavior.

    Skips if OpenLDAP is not enabled in software_config.json.

    This test:
    1. For each submit node (slurm_control_node, login_node, login_compiler_node):
       - Copies job.sh (40s sleep) to the submit node via root SSH
       - Submits the job as ldapuser targeting a compute node
       - Waits for job to start RUNNING
       - Tries ldapuser login to compute node during active job
       - Waits for job to complete
       - Verifies ldapuser login is blocked after job ends (auto-logout)
    2. Displays the actual PAM / disconnect messages for each submit node
    """
    from automation_library.discovery.functions import verify_pam_slurm_adopt_session_termination

    log = TestLogger("Verify PAM slurm_adopt session termination behavior")

    skip_if_openldap_not_enabled(host, log)

    log.check("Submitting jobs from all submit nodes, verifying PAM behavior on compute node")

    result = verify_pam_slurm_adopt_session_termination(host)

    # Handle skip conditions
    if result.get("error") and "not set in omnia_test_config" in result["error"]:
        log.skipped("LDAP credentials not configured", result["error"])
        pytest.skip(result["error"])

    if result.get("error") and ("No slurm" in result["error"] or "No slurm_control_node" in result["error"]):
        log.skipped("Required nodes not in PXE mapping", result["error"])
        pytest.skip(result["error"])

    # Build details for display - one block per submit node matching old format
    ldap_user_str = ', '.join(result.get('ldap_users', []))
    details_lines = []

    for submit_hostname, node_result in result.get("results_by_submit_node", {}).items():
        details_lines.append(f"LDAP user: {ldap_user_str}")
        details_lines.append(
            f"Submit node ({node_result.get('node_type', '')}): "
            f"{submit_hostname} (IP: {node_result.get('admin_ip', '')})"
        )
        if node_result.get("compute_hostname"):
            details_lines.append(
                f"Compute node: {node_result['compute_hostname']} "
                f"(IP: {node_result.get('compute_ip', '')})"
            )
        details_lines.append(f"Job ID: {node_result.get('job_id', '')}")

        if node_result.get("error"):
            details_lines.append(f"✗ Error: {node_result['error']}")
            details_lines.append("")
            continue

        details_lines.append("")

        # Login during job
        if node_result.get("login_during_job"):
            details_lines.append("Login during active job: ALLOWED (session adopted) ✓")
        else:
            details_lines.append("Login during active job: BLOCKED ✗")
        if node_result.get("login_during_job_message"):
            details_lines.append(f"  {node_result['login_during_job_message']}")

        details_lines.append("")

        # Login after job
        if node_result.get("session_terminated_after_job"):
            details_lines.append("Login after job ended: BLOCKED (auto-logout) ✓")
        else:
            details_lines.append("Login after job ended: NOT BLOCKED ✗")
        if node_result.get("post_job_block_message"):
            details_lines.append(f"  {node_result['post_job_block_message']}")

        details_lines.append("")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("PAM slurm_adopt session termination verified", details)
    else:
        log.failed("PAM session termination not working", details)
        assert False, ASSERT_MSGS["pam_session_failed"].format(
            details=result.get("error", result.get("details", ""))
        )
