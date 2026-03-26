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
Admin Debug Packages Functions.

This module contains verification functions for admin debug packages.
Functions follow the return dictionary pattern with success, error keys.
"""

import json
from typing import Dict, Any, List

from automation_library.core import (
    get_functional_groups_from_pxe_mapping,
    get_nodes_info,
    run_on_remote_node,
    run_in_container,
)
from .vars import (
    SOFTWARE_CONFIG_PATH,
    ADMIN_DEBUG_PACKAGES_JSON,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_nodes_by_functional_group(host) -> Dict[str, List[Dict[str, str]]]:
    """Get all nodes grouped by functional_group (role)."""
    functional_groups = get_functional_groups_from_pxe_mapping(host)
    result = {}
    for fg in sorted(functional_groups):
        nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
        if nodes:
            result[fg] = nodes
    return result


def _run_command_on_node(host, admin_ip: str, command: str) -> Dict[str, Any]:
    """Run a command on a node via SSH using core's run_on_remote_node."""
    cmd = run_on_remote_node(host, command, admin_ip)
    return {"success": cmd.rc == 0, "output": cmd.stdout.strip(), "error": cmd.stderr.strip()}


# =============================================================================
# CONFIGURATION VERIFICATION
# =============================================================================

def verify_admin_debug_packages_config(host) -> Dict[str, Any]:
    """
    Check if admin_debug_packages entry is present in software_config.json.

    Returns:
        Dict with:
        - present: bool - whether admin_debug_packages key exists
        - config_exists: bool
        - error: str
    """
    cmd = run_in_container(host, f"test -f {SOFTWARE_CONFIG_PATH}")
    if cmd.rc != 0:
        return {
            "present": False,
            "config_exists": False,
            "error": f"software_config.json not found at {SOFTWARE_CONFIG_PATH}",
        }

    cmd = run_in_container(host, f"cat {SOFTWARE_CONFIG_PATH}")
    if cmd.rc != 0:
        return {
            "present": False,
            "config_exists": True,
            "error": f"Failed to read software_config.json: {cmd.stderr}",
        }

    try:
        config = json.loads(cmd.stdout)
    except json.JSONDecodeError as e:
        return {
            "present": False,
            "config_exists": True,
            "error": f"Invalid JSON: {e}",
        }

    # Check in softwares array: {"name": "admin_debug_packages", ...}
    softwares = config.get("softwares", [])
    present = any(
        s.get("name") == "admin_debug_packages" for s in softwares
        if isinstance(s, dict)
    )
    return {
        "present": present,
        "config_exists": True,
        "error": "" if present else "admin_debug_packages not found in softwares list",
    }


# =============================================================================
# PACKAGE LIST FROM JSON FILE
# =============================================================================

def get_packages_from_json(host) -> List[str]:
    """
    Read package names from admin_debug_packages.json inside omnia_core container.

    Path: /opt/omnia/input/project_default/config/x86_64/rhel/10.0/admin_debug_packages.json

    Returns:
        List of package name strings. Returns empty list if file not found.
    """
    cmd = run_in_container(host, f"cat {ADMIN_DEBUG_PACKAGES_JSON}")
    if cmd.rc != 0:
        return []

    try:
        data = json.loads(cmd.stdout)
        cluster_pkgs = data.get("admin_debug_packages", {}).get("cluster", [])
        return [p["package"] for p in cluster_pkgs if p.get("package")]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


# =============================================================================
# PACKAGE INSTALLATION VERIFICATION
# =============================================================================

def _check_packages_on_node(
    host, admin_ip: str, packages: List[str],
) -> Dict[str, Any]:
    """
    Check which packages are installed on a single node.

    Runs 'rpm -q $pkg' for each package individually via SSH,
    exactly matching the shell script logic:
        if rpm -q $pkg &>/dev/null; then INSTALLED else NOT INSTALLED

    Returns:
        Dict with installed, missing lists and counts.
    """
    installed = []
    missing = []

    for pkg in packages:
        result = _run_command_on_node(host, admin_ip, f"rpm -q {pkg}")
        if result["success"] and "is not installed" not in result["output"]:
            installed.append(pkg)
        else:
            missing.append(pkg)

    return {
        "installed": installed,
        "missing": missing,
        "installed_count": len(installed),
        "missing_count": len(missing),
    }


def verify_debug_packages_installed(host) -> Dict[str, Any]:
    """
    Verify all debug packages are installed on all cluster nodes.

    Reads package list from admin_debug_packages.json inside omnia_core container.

    For each node, runs 'rpm -q <pkg>' per package via SSH.
    Results are grouped by functional_group (role).

    Returns:
        Dict with success, total_nodes, package_count, results_by_group, etc.
    """
    packages = get_packages_from_json(host)

    nodes_by_group = get_nodes_by_functional_group(host)

    if not nodes_by_group:
        return {
            "success": False,
            "skipped": True,
            "total_nodes": 0,
            "package_count": len(packages),
            "packages": packages,
            "results_by_group": {},
            "error": "No nodes found in PXE mapping",
        }

    results_by_group = {}
    all_success = True
    total_nodes = 0
    failed_nodes = []

    for func_group, nodes in nodes_by_group.items():
        group_results = []

        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")
            total_nodes += 1

            if not admin_ip:
                group_results.append({
                    "hostname": hostname,
                    "admin_ip": "",
                    "installed_packages": [],
                    "missing_packages": packages.copy(),
                    "installed_count": 0,
                    "missing_count": len(packages),
                    "error": "No IP address",
                })
                all_success = False
                failed_nodes.append(hostname)
                continue

            check = _check_packages_on_node(host, admin_ip, packages)

            node_ok = check["missing_count"] == 0
            if not node_ok:
                all_success = False
                failed_nodes.append(hostname)

            group_results.append({
                "hostname": hostname,
                "admin_ip": admin_ip,
                "installed_packages": check["installed"],
                "missing_packages": check["missing"],
                "installed_count": check["installed_count"],
                "missing_count": check["missing_count"],
                "error": "" if node_ok else f"Missing {check['missing_count']} packages",
            })

        results_by_group[func_group] = group_results

    return {
        "success": all_success,
        "skipped": False,
        "total_nodes": total_nodes,
        "package_count": len(packages),
        "packages": packages,
        "results_by_group": results_by_group,
        "failed_nodes": failed_nodes,
        "error": "" if all_success else f"{len(failed_nodes)} nodes have missing packages",
    }


__all__ = [
    "get_nodes_by_functional_group",
    "get_packages_from_json",
    "verify_admin_debug_packages_config",
    "verify_debug_packages_installed",
]
