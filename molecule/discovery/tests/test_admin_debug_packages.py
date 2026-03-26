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
Admin Debug Packages Test Cases.

Test cases:
1. Check admin_debug_packages entry in software_config.json (pass/skip)
2. Check packages are present in admin_debug_packages.json (pass/skip)
3. Verify all packages from admin_debug_packages.json are installed on nodes

Package list read from:
    /opt/omnia/input/project_default/config/x86_64/rhel/10.0/admin_debug_packages.json

Each package checked via: rpm -q <pkg> on each node via SSH.

Usage:
    ./run_molecule.sh discovery verify    # Verify only
"""

import pytest
from automation_library.core import TestLogger
from automation_library.discovery.functions import (
    verify_admin_debug_packages_config,
    get_packages_from_json,
    verify_debug_packages_installed,
)
from automation_library.discovery.messages import (
    ADMIN_DEBUG_TEST_NAMES as TEST_NAMES,
    ADMIN_DEBUG_LOG_MSGS as LOG_MSGS,
    ADMIN_DEBUG_ASSERT_MSGS as ASSERT_MSGS,
)


# =============================================================================
# TEST CASE 1: CONFIG CHECK (PASS / SKIP)
# =============================================================================

def test_admin_debug_packages_config(host):
    """
    Test Case 1: Check if admin_debug_packages is present in
    software_config.json. PASS if present, SKIP if not present.
    """
    log = TestLogger(TEST_NAMES["config_check"])

    log.check(
        "Checking software_config.json for admin_debug_packages entry"
    )
    result = verify_admin_debug_packages_config(host)

    log.check(f"software_config.json exists: {result['config_exists']}")
    log.check(f"admin_debug_packages present: {result['present']}")

    if result["present"]:
        log.passed(
            "admin_debug_packages is present in software_config.json",
            "Configuration check passed"
        )
    else:
        log.skipped(
            result["error"],
            "Skipping - admin_debug_packages not in "
            "software_config.json"
        )
        pytest.skip(result["error"])


# =============================================================================
# TEST CASE 2: PACKAGES PRESENT IN JSON (PASS / SKIP)
# =============================================================================

def test_admin_debug_packages_json(host):
    """
    Test Case 2: Check packages are present in admin_debug_packages.json.
    PASS if packages found, SKIP if empty (skips test case 3 as well).
    """
    log = TestLogger(TEST_NAMES["json_check"])

    log.check("Checking admin_debug_packages.json for package list")
    packages = get_packages_from_json(host)

    log.check(f"Packages found: {len(packages)}")

    if packages:
        log.check(f"Package list ({len(packages)} packages):")
        for pkg in packages[:10]:
            log.check(f"  - {pkg}")
        if len(packages) > 10:
            log.check(f"  ... and {len(packages) - 10} more")
        log.passed(
            f"{len(packages)} packages found in "
            "admin_debug_packages.json",
            "JSON package list check passed"
        )
    else:
        log.skipped(
            "admin_debug_packages.json is empty or not found",
            "Skipping - no packages to verify"
        )
        pytest.skip(
            "admin_debug_packages.json is empty or not found"
        )


# =============================================================================
# TEST CASE 3: PACKAGE INSTALLATION CHECK
# =============================================================================

def test_debug_packages_installed(host):
    """
    Test Case 3: Verify all packages from admin_debug_packages.json
    are installed.

    Reads package list from:
        /opt/omnia/input/project_default/config/x86_64/rhel/10.0/
        admin_debug_packages.json

    For each node, runs: rpm -q <pkg> per package via SSH.
    Results grouped by functional_group.
    """
    log = TestLogger(TEST_NAMES["packages_installed"])

    log.check(
        "Verifying debug packages installation on all cluster nodes"
    )
    result = verify_debug_packages_installed(host)

    if result.get("skipped"):
        log.skipped(result["error"], "Skipped")
        pytest.skip(result["error"])

    log.check(f"Total nodes: {result['total_nodes']}")
    log.check(f"Packages to verify: {result['package_count']}")
    log.check("Package source: admin_debug_packages.json")
    log.check("")

    failed_nodes = []

    for func_group, nodes in result.get(
        "results_by_group", {}
    ).items():
        log.check(
            f"═══ {func_group} ({len(nodes)} nodes) ═══"
        )
        for node in nodes:
            hostname = node["hostname"]
            admin_ip = node.get("admin_ip", "")
            installed_count = node.get("installed_count", 0)
            missing_count = node.get("missing_count", 0)
            total_pkgs = installed_count + missing_count

            if missing_count == 0:
                log.check(
                    f"  ✔ {hostname} ({admin_ip}): "
                    f"{installed_count}/{total_pkgs} "
                    "packages INSTALLED"
                )
            else:
                failed_nodes.append(hostname)
                log.check(
                    f"  ✘ {hostname} ({admin_ip}): "
                    f"{installed_count}/{total_pkgs} "
                    "packages installed"
                )
                for pkg in node.get("missing_packages", []):
                    log.check(
                        f"      ✘ {pkg} : NOT INSTALLED"
                    )
        log.check("")

    if result["success"]:
        log.passed(
            LOG_MSGS["packages_success"].format(
                node_count=result["total_nodes"],
                package_count=result["package_count"]
            ),
            "All debug packages installed on all nodes"
        )
    else:
        log.failed(
            LOG_MSGS["packages_failed"].format(
                failed_count=len(failed_nodes),
                total_count=result["total_nodes"]
            ),
            f"Failed nodes: {', '.join(failed_nodes)}"
        )

    assert result["success"], ASSERT_MSGS["packages_missing"].format(
        failed_nodes=", ".join(failed_nodes),
        total_nodes=result["total_nodes"],
        missing_summary=result.get("error", "")
    )
