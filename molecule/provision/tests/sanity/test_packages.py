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
Provision - Node Package Verification Test Cases.

Runs AFTER cloud-init test (order=2) to verify all required packages
are installed on every provisioned node.

Package lists are derived using the SAME logic as build_image_x86_64 playbook:
  - Reads base image YAML (rhel-<arch>_base-10.0.yaml) from IMAGE_CONFIG_YAML_DIR
    inside omnia_core container via load_container_file (core utility)
  - Finds per-functional-group image YAML
    (rhel-<functional_group>_<uuid>-image-build-10.0.yaml)
  - Combines base packages + compute packages (deduplicated)
  - SSHes to each node and verifies via rpm -qa
  - Reports packages below each node name: INSTALLED (✓ pkg → version)
    and NOT INSTALLED (✗ pkg) - same format as test_build_image_x86_64.py

Test cases:
1. Verify build_stream pipeline stage 'validate-image-on-test' COMPLETED (when enabled)
2. Verify all required packages are installed on all nodes
3. TC-AP01: Per-FG Packages - Positive Tests (8 functional groups)
4. TC-AP02: Per-FG Packages - Negative Tests (wrong packages on wrong nodes)
5. TC-AP03: OS Packages on All Nodes (common packages)
6. TC-AR01: additional_repos SSL Configuration
7. TC-AR02: additional_repos Sync Policy (always vs partial)
8. TC-AP04: aarch64 Additional Packages Support
"""

import pytest

from automation_library.core import (
    TestLogger,
    is_build_stream_enabled,
    get_build_stream_job_id,
    STAGE_VALIDATE_IMAGE,
)
from molecule.conftest import build_stream_job_state
from automation_library.provision.functions import (
    get_all_slurm_nodes,
    get_k8s_nodes,
    verify_node_packages,
)
from automation_library.provision.messages import (
    TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS,
    SKIP_MSGS,
    AP_TEST_NAMES, AP_TEST_LOG_MSGS, AP_TEST_ASSERT_MSGS, AP_SKIP_MSGS,
)
from automation_library.provision.vars.common_vars import FORCE_PROVISION_VALIDATE_FAILED


# =============================================================================
# 1. BUILD STREAM JOB STAGE VALIDATION (first test — gates all others)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(0)
def test_build_stream_job_stage(host):
    """
    Test 1: When build_stream is enabled, verify the validate-image-on-test
    pipeline stage completed successfully before checking node packages.

    - Reads build_stream_job_id override from omnia_test_config.yml if set.
    - Falls back to the latest job in build_stream_db otherwise.
    - Prints the exact DB stage_state if not COMPLETED.
    - Skipped when build_stream is disabled.
    """
    stage = STAGE_VALIDATE_IMAGE
    log = TestLogger(TEST_NAMES["build_stream_job_stage"].format(stage=stage))
    
    if not is_build_stream_enabled(host):
        log.skipped("Build stream is disabled in software_config.json", "Test skipped - build stream not enabled")
        pytest.skip(LOG_MSGS["build_stream_disabled_skip"])

    result = get_build_stream_job_id(host, stage_name=stage)
    job_id = result.get("job_id") or "unknown"
    job_state = result.get("job_state") or "NOT FOUND"
    source = result.get("source", "database")

    # Set shared state so autouse fixture in conftest.py can skip remaining tests
    build_stream_job_state["checked"] = True
    build_stream_job_state["success"] = result["success"]
    build_stream_job_state["job_id"] = job_id
    build_stream_job_state["job_state"] = job_state
    build_stream_job_state["error"] = result.get("error", "")

    log.check(LOG_MSGS["build_stream_job_checking"].format(stage=stage, source=source))

    if result["success"]:
        log.passed(
            LOG_MSGS["build_stream_job_ok"].format(
                stage=stage, job_id=job_id, source=source
            )
        )
    else:
        # Check if force flag is enabled
        if FORCE_PROVISION_VALIDATE_FAILED:
            log.skipped(
                f"Build stream validation BYPASSED (FORCE_PROVISION_VALIDATE_FAILED=True)",
                f"WARNING: Tests will run on unvalidated images!\n"
                f"Stage '{stage}' is {job_state} (job_id: {job_id})\n"
                f"To disable force mode, set FORCE_PROVISION_VALIDATE_FAILED = False\n"
                f"in automation_library/provision/vars/common_vars.py"
            )
            # Mark as success so autouse fixture allows remaining tests
            build_stream_job_state["success"] = True
            build_stream_job_state["forced"] = True
            return
        else:
            log.failed(
                LOG_MSGS["build_stream_job_failed"].format(
                    stage=stage, state=job_state, job_id=job_id
                ),
                result.get("error", "")
            )
            # Use pytest.fail() so this test shows as FAILED (not skipped)
            # Remaining tests will be SKIPPED via autouse fixture
            pytest.fail(
                ASSERT_MSGS["build_stream_job_stage_failed"].format(
                    stage=stage, job_id=job_id, state=job_state
                )
            )


# =============================================================================
# 2. NODE PACKAGE VERIFICATION TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_node_packages_installed(host):
    """
    Test Case 1: Verify all required packages are installed on all nodes.

    Runs after cloud-init (order=2) - nodes are confirmed booted before this.

    For each node in PXE mapping:
    - Reads base image YAML + per-functional-group image YAML from
      IMAGE_CONFIG_YAML_DIR inside omnia_core (same YAMLs build_image_x86_64 uses)
    - Combines base + compute packages (deduplicated)
    - SSHs to node and verifies via rpm -qa
    - Reports INSTALLED and NOT INSTALLED packages below each node name

    Skips if no nodes are found in PXE mapping.
    """
    log = TestLogger(TEST_NAMES["node_packages"])

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    if not all_nodes:
        log.skipped(
            SKIP_MSGS["no_nodes_for_packages"],
            "Test skipped - no nodes in PXE mapping"
        )
        pytest.skip(SKIP_MSGS["no_nodes_for_packages"])

    log.check(
        f"Verifying packages on {len(all_nodes)} nodes "
        f"(packages from image YAMLs in IMAGE_CONFIG_YAML_DIR - same source as build_image)"
    )

    result = verify_node_packages(host, all_nodes)

    # Build detailed per-node output - same format as test_build_image_x86_64.py
    details_lines = []
    for node_result in result.get("results", []):
        hostname = node_result["hostname"]
        found_pkgs = node_result.get("found_packages", [])
        missing_pkgs = node_result.get("missing_packages", [])
        expected = len(found_pkgs) + len(missing_pkgs)
        found = len(node_result.get("found_packages", []))
        status = "\u2713" if node_result["success"] else "\u2717"

        details_lines.append(f"{status} {hostname}: {found}/{expected} packages")

        pkg_details = node_result.get("package_details", [])
        installed = [p for p in pkg_details if p["status"] == "installed"]
        not_installed = [p for p in pkg_details if p["status"] == "missing"]

        if installed:
            details_lines.append(f"    INSTALLED ({len(installed)}):")
            for pkg in installed:
                details_lines.append(f"      \u2713 {pkg['expected']} \u2192 {pkg['found']}")

        if not_installed:
            details_lines.append(f"    NOT INSTALLED ({len(not_installed)}):")
            for pkg in not_installed:
                details_lines.append(f"      \u2717 {pkg['expected']}")

        if node_result.get("error") and not node_result["success"]:
            details_lines.append(f"    Error: {node_result['error']}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            LOG_MSGS["packages_ok"].format(count=result["total"]),
            details
        )
    else:
        log.failed(
            LOG_MSGS["packages_fail"].format(
                failed=result["failed"], total=result["total"]
            ),
            details
        )
        assert False, ASSERT_MSGS["packages_failed"].format(
            failed_nodes=", ".join(result["nodes_missing_packages"]),
            details=details
        )


# =============================================================================
# 3. ADDITIONAL_PACKAGES.JSON PER-FG SCOPING TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(120)
def test_per_fg_packages_positive(host):
    """
    TC-AP01: Verify FG-specific packages are installed on correct FG nodes.
    
    Tests that packages defined in additional_packages.json for each functional
    group are installed ONLY on nodes with that functional group.
    
    Functional groups tested (8 total):
    - service_kube_control_plane_first
    - service_kube_control_plane
    - service_kube_node
    - slurm_control_node
    - slurm_node
    - login_node
    - login_compiler_node
    - os (tested separately)
    """
    log = TestLogger(AP_TEST_NAMES["per_fg_packages_positive"])
    
    from automation_library.provision.functions import (
        is_additional_packages_enabled,
        get_additional_packages_by_fg,
        verify_per_fg_packages_positive,
    )
    from automation_library.core import get_nodes_info
    
    # Check prerequisite: additional_packages must be enabled in software_config.json
    if not is_additional_packages_enabled(host):
        log.skipped(
            "additional_packages not enabled in software_config.json",
            "Enable by adding to softwares array and configuring additional_packages section"
        )
        pytest.skip("additional_packages not enabled in software_config.json")
    
    # Load packages per FG
    fg_packages = get_additional_packages_by_fg(host, arch="x86_64")
    
    if not fg_packages:
        log.skipped(AP_SKIP_MSGS["no_additional_packages"], "")
        pytest.skip(AP_SKIP_MSGS["no_additional_packages"])
    
    # Get nodes grouped by FG
    # Note: additional_packages.json uses base names (slurm_control_node)
    # but PXE mapping uses names with arch suffix (slurm_control_node_x86_64)
    nodes_by_fg = {}
    for fg_name in fg_packages.keys():
        if fg_name != "os":
            # Map to PXE name with architecture suffix
            pxe_fg_name = f"{fg_name}_x86_64"
            nodes = get_nodes_info(host, search_by="functional_group", search_value=pxe_fg_name)
            if nodes:
                nodes_by_fg[fg_name] = nodes
    
    if not nodes_by_fg:
        log.skipped("No nodes found for functional groups", "")
        pytest.skip("No nodes")
    
    log.check(f"Testing {len(fg_packages)} functional groups")
    
    result = verify_per_fg_packages_positive(host, nodes_by_fg, fg_packages)
    
    details = [f"FG package tests: {result['total_tests']}", ""]
    for r in result["test_results"]:
        status = "\u2713" if r["success"] else "\u2717"
        details.append(
            f"  {status} {r['fg']} ({r['node']}): "
            f"{len(r['installed'])}/{r['packages']} packages"
        )
        if r["missing"]:
            details.append(f"      Missing: {', '.join(r['missing'])}")
    
    if not result["success"]:
        log.failed("Some FG packages missing", "\n".join(details))
        assert False, "FG-specific packages not installed correctly"
    
    log.passed("All FG packages installed correctly", "\n".join(details))


@pytest.mark.sanity
@pytest.mark.order(121)
def test_per_fg_packages_negative(host):
    """
    TC-AP02: Verify FG-specific packages are NOT on wrong FG nodes.
    
    Negative tests to ensure package scoping is enforced:
    - K8s packages should NOT be on Slurm nodes
    - Slurm packages should NOT be on K8s nodes
    - Compiler packages should NOT be on regular login nodes
    """
    log = TestLogger(AP_TEST_NAMES["per_fg_packages_negative"])
    
    from automation_library.provision.functions import (
        is_additional_packages_enabled,
        get_additional_packages_by_fg,
        verify_per_fg_packages_negative,
    )
    from automation_library.core import get_nodes_info
    
    # Check prerequisite
    if not is_additional_packages_enabled(host):
        log.skipped(
            "additional_packages not enabled in software_config.json",
            "Enable by adding to softwares array"
        )
        pytest.skip("additional_packages not enabled")
    
    # Load packages per FG
    fg_packages = get_additional_packages_by_fg(host, arch="x86_64")
    
    if not fg_packages:
        log.skipped(AP_SKIP_MSGS["no_additional_packages"], "")
        pytest.skip(AP_SKIP_MSGS["no_additional_packages"])
    
    # Get nodes grouped by FG
    # Map to PXE names with architecture suffix
    nodes_by_fg = {}
    for fg_name in fg_packages.keys():
        if fg_name != "os":
            pxe_fg_name = f"{fg_name}_x86_64"
            nodes = get_nodes_info(host, search_by="functional_group", search_value=pxe_fg_name)
            if nodes:
                nodes_by_fg[fg_name] = nodes
    
    if not nodes_by_fg:
        log.skipped("No nodes found for functional groups", "")
        pytest.skip("No nodes")
    
    log.check("Testing negative cases (wrong packages on wrong nodes)")
    
    result = verify_per_fg_packages_negative(host, nodes_by_fg, fg_packages)
    
    details = [f"Negative tests: {result['total_tests']}", ""]
    for r in result["test_results"]:
        status = "\u2713" if r["success"] else "\u2717"
        details.append(
            f"  {status} {r['test_fg']} should NOT have {r['wrong_fg']} packages"
        )
        if r["unexpected"]:
            details.append(f"      Unexpected: {', '.join(r['unexpected'])}")
    
    if not result["success"]:
        log.failed("Wrong packages found on nodes", "\n".join(details))
        assert False, "FG scoping violated - wrong packages on wrong nodes"
    
    log.passed("All negative tests passed - no wrong packages", "\n".join(details))


@pytest.mark.sanity
@pytest.mark.order(122)
def test_os_packages_on_all_nodes(host):
    """
    TC-AP03: Verify OS packages are installed on ALL nodes.
    
    Packages in the "os" functional group should be installed on every node
    regardless of their specific functional group.
    """
    log = TestLogger(AP_TEST_NAMES["os_packages_all_nodes"])
    
    from automation_library.provision.functions import (
        is_additional_packages_enabled,
        get_additional_packages_by_fg,
        verify_os_packages_on_all_nodes,
    )
    
    # Check prerequisite
    if not is_additional_packages_enabled(host):
        log.skipped(
            "additional_packages not enabled in software_config.json",
            "Enable by adding to softwares array"
        )
        pytest.skip("additional_packages not enabled")
    
    # Load packages
    fg_packages = get_additional_packages_by_fg(host, arch="x86_64")
    os_packages = fg_packages.get("os", [])
    
    if not os_packages:
        log.skipped("No OS packages configured", "")
        pytest.skip("No OS packages")
    
    # Get ALL nodes
    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes
    
    if not all_nodes:
        log.skipped("No nodes available", "")
        pytest.skip("No nodes")
    
    log.check(f"Verifying {len(os_packages)} OS packages on {len(all_nodes)} nodes")
    
    result = verify_os_packages_on_all_nodes(host, all_nodes, os_packages)
    
    details = [
        f"OS packages: {len(os_packages)}",
        f"Nodes tested: {result['total_nodes']}",
        "",
        "Per-node results:"
    ]
    for r in result["node_results"]:
        status = "\u2713" if r["success"] else "\u2717"
        details.append(
            f"  {status} {r['hostname']} ({r['fg']}): "
            f"{len(r['installed'])}/{len(os_packages)} packages"
        )
        if r["missing"]:
            details.append(f"      Missing: {', '.join(r['missing'])}")
    
    if not result["success"]:
        log.failed("OS packages missing on some nodes", "\n".join(details))
        assert False, "OS packages not on all nodes"
    
    log.passed("All OS packages on all nodes", "\n".join(details))


# =============================================================================
# 4. ADDITIONAL_REPOS SSL CONFIGURATION TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(130)
def test_additional_repos_ssl_config(host):
    """
    TC-AR01: Verify Pulp RPM remotes have correct TLS/SSL configuration.

    Queries all Pulp RPM remotes and verifies:
    - HTTPS remotes have tls_validation enabled
    - Remotes with custom SSL certs have ca_cert/client_cert/client_key set
    """
    log = TestLogger(AP_TEST_NAMES["additional_repos_ssl"])

    from automation_library.provision.functions import (
        verify_pulp_repos_ssl_config,
    )

    result = verify_pulp_repos_ssl_config(host)

    if result["total_tests"] == 0:
        log.skipped("No Pulp RPM remotes found", "")
        pytest.skip("No Pulp RPM remotes")

    details = [
        f"Repos tested: {result['total_tests']}",
        f"HTTPS repos: {result.get('https_count', 0)}",
        f"Custom SSL repos: {result.get('custom_ssl_count', 0)}",
        "",
    ]
    for r in result["test_results"]:
        status = "\u2713" if r["success"] else "\u2717"
        ssl_info = f"tls={r['tls_validation']}"
        if r["has_ca_cert"]:
            ssl_info += ", ca_cert=yes"
        if r["has_client_cert"]:
            ssl_info += ", client_cert=yes"
        details.append(
            f"  {status} {r['repo']} ({r['url_scheme']}): {ssl_info}"
        )
        if r["error"]:
            details.append(f"      Error: {r['error']}")

    if not result["success"]:
        log.failed("TLS/SSL configuration incorrect", "\n".join(details))
        assert False, "Some Pulp remotes have incorrect TLS/SSL config"

    log.passed("All Pulp repos have correct TLS/SSL config", "\n".join(details))


# =============================================================================
# 5. ADDITIONAL_REPOS SYNC POLICY TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(131)
def test_additional_repos_sync_policy(host):
    """
    TC-AR02: Verify Pulp repo sync policy matches software_config.json repo_config.

    Reads repo_config ("partial" or "always") from software_config.json and
    verifies that ALL Pulp remotes have the corresponding sync policy:
    - "always"  → Pulp policy "immediate"
    - "partial" → Pulp policy "on_demand"
    """
    log = TestLogger(AP_TEST_NAMES["additional_repos_policy"])

    from automation_library.provision.functions import (
        get_repo_config,
        verify_pulp_repos_sync_policy,
    )

    # Read repo_config from software_config.json
    repo_config = get_repo_config(host)

    if not repo_config:
        log.skipped("repo_config not set in software_config.json", "")
        pytest.skip("No repo_config in software_config.json")

    log.check(f"Verifying Pulp sync policy for repo_config={repo_config!r}")

    result = verify_pulp_repos_sync_policy(host, repo_config)

    if result["total_tests"] == 0:
        log.skipped("No Pulp remotes found", "")
        pytest.skip("No Pulp remotes to verify")

    details = [
        f"repo_config (software_config.json): {repo_config}",
        f"Expected Pulp policy: {result['expected_policy']}",
        f"Repos tested: {result['total_tests']}",
        "",
    ]
    for r in result["test_results"]:
        status = "\u2713" if r["success"] else "\u2717"
        details.append(
            f"  {status} {r['repo']}: "
            f"expected={r['expected']}, actual={r['actual']}"
        )
        if r["error"]:
            details.append(f"      Error: {r['error']}")

    if not result["success"]:
        log.failed("Sync policy mismatch on some repos", "\n".join(details))
        assert False, "Pulp repo sync policy does not match repo_config"

    log.passed("All Pulp repos have correct sync policy", "\n".join(details))


# =============================================================================
# 6. AARCH64 ADDITIONAL PACKAGES TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(140)
def test_aarch64_additional_packages(host):
    """
    TC-AP04: Verify aarch64 additional packages support.
    
    Tests that aarch64 additional_packages.json is properly configured
    and contains packages for ARM architecture nodes.
    """
    log = TestLogger(AP_TEST_NAMES["aarch64_packages"])
    
    from automation_library.provision.functions import (
        is_additional_packages_enabled,
        get_additional_packages_by_fg,
    )
    
    # Check prerequisite
    if not is_additional_packages_enabled(host):
        log.skipped(
            "additional_packages not enabled in software_config.json",
            "Enable by adding to softwares array with aarch64 arch"
        )
        pytest.skip("additional_packages not enabled")
    
    # Load aarch64 packages
    fg_packages = get_additional_packages_by_fg(host, arch="aarch64")
    
    if not fg_packages:
        log.skipped(AP_SKIP_MSGS["no_aarch64_config"], "")
        pytest.skip(AP_SKIP_MSGS["no_aarch64_config"])
    
    log.check(f"Verifying aarch64 packages for {len(fg_packages)} functional groups")
    
    details = [
        f"Functional groups: {len(fg_packages)}",
        "",
        "Packages per FG:"
    ]
    
    total_packages = 0
    for fg_name, packages in fg_packages.items():
        details.append(f"  {fg_name}: {len(packages)} packages")
        total_packages += len(packages)
    
    details.append(f"\nTotal packages: {total_packages}")
    
    if total_packages == 0:
        log.failed("No packages configured for aarch64", "\n".join(details))
        assert False, "aarch64 additional_packages.json is empty"
    
    log.passed(f"aarch64 packages configured ({total_packages} total)", "\n".join(details))
