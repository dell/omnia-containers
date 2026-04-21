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
# pylint: disable=import-error

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

    details_lines = [
        f"software_config.json exists: {result['config_exists']}",
        f"admin_debug_packages present: {result['present']}"
    ]
    details = "\n".join(details_lines)

    if result["present"]:
        log.passed(
            "admin_debug_packages is present in software_config.json",
            details
        )
    else:
        log.skipped(
            result["error"],
            details
        )
        pytest.skip(result["error"])

# =============================================================================
def test_admin_debug_packages_json(host):
    """
    Test Case 2: Check packages are present in admin_debug_packages.json.
    PASS if packages found, SKIP if empty (skips test case 3 as well).
    """
    log = TestLogger(TEST_NAMES["json_check"])

    log.check("Checking admin_debug_packages.json for package list")
    packages = get_packages_from_json(host)

    if packages:
        details_lines = [
            f"Packages found: {len(packages)}",
            "",
            "Package list:"
        ]
        for pkg in packages:
            details_lines.append(f"  - {pkg}")
        details = "\n".join(details_lines)

        log.passed(
            f"{len(packages)} packages found in "
            "admin_debug_packages.json",
            details
        )
    else:
        details = "admin_debug_packages.json is empty or not found"
        log.skipped(
            "admin_debug_packages.json is empty or not found",
            details
        )
        pytest.skip(
            "admin_debug_packages.json is empty or not found"
        )

# =============================================================================
def test_debug_packages_installed(host):  # pylint: disable=too-many-locals
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

    failed_nodes = []
    details_lines = [
        f"Total nodes: {result['total_nodes']}",
        f"Packages to verify: {result['package_count']}",
        "Package source: admin_debug_packages.json",
        ""
    ]

    for func_group, nodes in result.get(
        "results_by_group", {}
    ).items():
        details_lines.append(f"[{func_group}]")
        for node in nodes:
            hostname = node["hostname"]
            admin_ip = node.get("admin_ip", "")
            installed_count = node.get("installed_count", 0)
            missing_count = node.get("missing_count", 0)
            total_pkgs = installed_count + missing_count

            if missing_count == 0:
                status = "✓"
                details_lines.append(
                    f"  {status} {hostname} ({installed_count}/{total_pkgs} packages)"
                )
                details_lines.append(f"      IP: {admin_ip}")
                details_lines.append("      All packages installed")
            else:
                failed_nodes.append(hostname)
                status = "✗"
                details_lines.append(
                    f"  {status} {hostname} ({installed_count}/{total_pkgs} packages)"
                )
                details_lines.append(f"      IP: {admin_ip}")
                details_lines.append(
                    f"      Missing {missing_count} package(s):"
                )
                for pkg in node.get("missing_packages", []):
                    details_lines.append(f"          - {pkg}")
        details_lines.append("")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            LOG_MSGS["packages_success"].format(
                node_count=result["total_nodes"],
                package_count=result["package_count"]
            ),
            details
        )
    else:
        log.failed(
            LOG_MSGS["packages_failed"].format(
                failed_count=len(failed_nodes),
                total_count=result["total_nodes"]
            ),
            details
        )

    assert result["success"], ASSERT_MSGS["packages_missing"].format(
        failed_nodes=", ".join(failed_nodes),
        total_nodes=result["total_nodes"],
        missing_summary=result.get("error", "")
    )
