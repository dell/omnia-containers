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
Discovery Module - Slurm Functions.

Functions for Slurm cluster verification: services, cross-node SSH, sinfo, OpenMPI/UCX.
"""

from typing import Dict, Any, List

import pytest

from automation_library.core import (
    run_on_remote_node,
    is_software_enabled,
    get_nfs_client_mount_path,
)
from ..vars import (
    SSH_OPTS,
    OPENMPI_BIN_PATH,
    UCX_BIN_PATH,
    LDMS_SAMPLER_SERVICE,
    LDMS_SAMPLER_CONF_PATH,
    LDMS_SAMPLER_ENV_PATH,
)
from ..messages import SKIP_MSGS
from .common_func import (
    get_slurm_control_nodes,
    get_slurm_compute_nodes,
    get_login_compiler_nodes,
    get_all_slurm_nodes,
)


# =============================================================================
# ENABLE CHECK FUNCTIONS
# =============================================================================

def is_openmpi_enabled(host) -> bool:
    """Check if OpenMPI is enabled in software_config.json."""
    return is_software_enabled(host, "openmpi")


def is_ucx_enabled(host) -> bool:
    """Check if UCX is enabled in software_config.json."""
    return is_software_enabled(host, "ucx")


# =============================================================================
# SKIP FUNCTIONS
# =============================================================================

def skip_if_openmpi_not_enabled(host, log):
    """Skip test if OpenMPI is not enabled in software_config.json."""
    if not is_openmpi_enabled(host):
        msg = SKIP_MSGS["openmpi_not_enabled"]
        log.skipped(msg, SKIP_MSGS["skip_detail_not_enabled"].format(software="OpenMPI"))
        pytest.skip(msg)


def skip_if_ucx_not_enabled(host, log):
    """Skip test if UCX is not enabled in software_config.json."""
    if not is_ucx_enabled(host):
        msg = SKIP_MSGS["ucx_not_enabled"]
        log.skipped(msg, SKIP_MSGS["skip_detail_not_enabled"].format(software="UCX"))
        pytest.skip(msg)


# =============================================================================
# SERVICE OUTPUT FORMATTING HELPERS
# =============================================================================

def format_service_status(svc_info: dict) -> str:
    """Format service status as 'active/enabled' or 'inactive/disabled'."""
    active = "active" if svc_info["active"] else "inactive"
    enabled = "enabled" if svc_info["enabled"] else "disabled"
    return f"{active}/{enabled}"


def build_service_details(result: dict) -> str:
    """
    Build formatted service details output with functional group.

    Args:
        result: Dict from verify_services_on_nodes with 'results' list

    Returns:
        Formatted string with service status per node
    """
    details_lines = []
    for node_result in result["results"]:
        status = "✓" if node_result["all_ok"] else "✗"
        func_group = node_result.get("functional_group", "")
        hostname = node_result['hostname']
        details_lines.append(f"{status} {hostname} ({func_group})")
        for svc, svc_info in node_result["services"].items():
            svc_status = "✓" if svc_info["ok"] else "✗"
            # Use status_text if available, otherwise format from active/enabled
            status_text = svc_info.get("status_text", format_service_status(svc_info))
            details_lines.append(f"    {svc_status} {svc}: {status_text}")
    return "\n".join(details_lines)


# =============================================================================
# SERVICE VERIFICATION FUNCTIONS
# =============================================================================

def verify_services_on_nodes(
    host, nodes: List[Dict[str, str]], services: List[str]
) -> Dict[str, Any]:
    """
    Verify services are active and enabled on a list of nodes.

    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip and hostname
        services: List of service names to check

    Returns:
        Dict with success, results list, failed_details
    """
    results = {
        "success": True,
        "total": len(nodes),
        "failed": 0,
        "failed_details": [],
        "results": [],
    }

    for node in nodes:
        admin_ip = node.get("admin_ip", "")
        hostname = node.get("hostname", "")
        functional_group = node.get("functional_group", "")

        node_result = {
            "hostname": hostname,
            "functional_group": functional_group,
            "all_ok": True,
            "services": {},
        }

        for service in services:
            # Check if service exists first
            check_cmd = (
                f"systemctl list-unit-files {service}.service 2>/dev/null | grep -q {service}"
            )
            cmd_exists = run_on_remote_node(host, check_cmd, admin_ip)
            service_exists = cmd_exists.rc == 0

            if not service_exists:
                # Service not installed/available
                node_result["services"][service] = {
                    "exists": False,
                    "active": False,
                    "enabled": False,
                    "ok": False,
                    "status_text": "not available (not installed)",
                }
                node_result["all_ok"] = False
                continue

            # Check both active and enabled status
            cmd_active = run_on_remote_node(
                host, f"systemctl is-active {service} 2>/dev/null", admin_ip
            )
            cmd_enabled = run_on_remote_node(
                host, f"systemctl is-enabled {service} 2>/dev/null", admin_ip
            )

            is_active = cmd_active.rc == 0 and "active" in cmd_active.stdout
            is_enabled = cmd_enabled.rc == 0 and "enabled" in cmd_enabled.stdout
            actual_status = cmd_active.stdout.strip() if cmd_active.stdout else "unknown"

            # Build status text
            if is_active and is_enabled:
                status_text = "active/enabled"
            elif is_active and not is_enabled:
                status_text = "active/disabled"
            else:
                status_text = f"{actual_status} (expected: active)"

            node_result["services"][service] = {
                "exists": True,
                "active": is_active,
                "enabled": is_enabled,
                "ok": is_active,  # Service is OK if active
                "status_text": status_text,
            }

            if not is_active:
                node_result["all_ok"] = False

        results["results"].append(node_result)
        if not node_result["all_ok"]:
            results["failed"] += 1
            results["success"] = False
            for svc, status in node_result["services"].items():
                if not status["ok"]:
                    results["failed_details"].append(f"{hostname}: {svc} not running")

    return results


# =============================================================================
# CROSS-NODE SSH VERIFICATION
# =============================================================================

def verify_cross_node_ssh(host) -> Dict[str, Any]:
    """
    Verify passwordless SSH between all Slurm cluster nodes.

    Tests all permutations: from each node to every other node.
    Groups results by source node for detailed output.

    Returns:
        Dict with success, total_pairs, failed, failed_pairs, node_results
    """
    results = {
        "success": True,
        "total_pairs": 0,
        "failed": 0,
        "failed_pairs": [],
        "node_results": [],  # Grouped by source node
    }

    all_nodes = get_all_slurm_nodes(host)
    if len(all_nodes) < 2:
        return results

    # Group results by source node
    for src in all_nodes:
        src_hostname = src.get("hostname", "")
        src_ip = src.get("admin_ip", "")
        src_result = {
            "source": src_hostname,
            "targets": [],
            "all_ok": True,
        }

        for dst in all_nodes:
            if src == dst:
                continue

            results["total_pairs"] += 1
            dst_ip = dst.get("admin_ip", "")
            dst_hostname = dst.get("hostname", "")

            # Cleanup old SSH key on source node
            cleanup_cmd = f"ssh-keygen -R {dst_ip} 2>/dev/null || true"
            run_on_remote_node(host, cleanup_cmd, src_ip)

            # SSH from src to dst via nested SSH
            nested_cmd = f"ssh {SSH_OPTS} root@{dst_ip} hostname"
            cmd = run_on_remote_node(host, nested_cmd, src_ip)
            ok = cmd.rc == 0 and dst_hostname in cmd.stdout

            src_result["targets"].append({
                "hostname": dst_hostname,
                "success": ok,
            })

            if not ok:
                results["failed"] += 1
                results["failed_pairs"].append(f"{src_hostname} → {dst_hostname}")
                results["success"] = False
                src_result["all_ok"] = False

        results["node_results"].append(src_result)

    return results


# =============================================================================
# SINFO VERIFICATION
# =============================================================================

def verify_sinfo_nodes(host) -> Dict[str, Any]:
    """
    Verify sinfo shows exactly the compute nodes from PXE mapping.

    Only checks slurm_node functional group - not control or login nodes.
    Fails if:
    - Any expected node is missing from sinfo
    - Any extra node is found in sinfo that's not in PXE mapping

    Returns:
        Dict with success, expected, found, missing, extra
    """
    results = {
        "success": True,
        "expected": [],
        "found": [],
        "missing": [],
        "extra": [],
    }

    # Get expected compute nodes only
    compute_nodes = get_slurm_compute_nodes(host)
    results["expected"] = [n.get("hostname", "") for n in compute_nodes]

    if not results["expected"]:
        return results

    # Get sinfo from control node
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        results["success"] = False
        results["error"] = "No slurm_control_node found"
        return results

    control_ip = control_nodes[0].get("admin_ip", "")
    cmd = run_on_remote_node(host, "sinfo -h -N -o '%N'", control_ip)

    if cmd.rc != 0:
        results["success"] = False
        results["error"] = f"sinfo failed: {cmd.stderr}"
        return results

    # Parse sinfo output
    for line in cmd.stdout.strip().split('\n'):
        node_name = line.strip()
        if node_name and node_name not in results["found"]:
            results["found"].append(node_name)

    # Find missing nodes (expected but not in sinfo)
    for expected in results["expected"]:
        if expected not in results["found"]:
            results["missing"].append(expected)
            results["success"] = False

    # Find extra nodes (in sinfo but not expected)
    for found in results["found"]:
        if found not in results["expected"]:
            results["extra"].append(found)
            results["success"] = False

    return results


# =============================================================================
# OPENMPI/UCX VERIFICATION
# =============================================================================

def get_software_version(host, software_name: str) -> str:
    """Get expected version of a software from software_config.json."""
    from automation_library.core import load_input_file, SOFTWARE_CONFIG_FILE

    config = load_input_file(host, SOFTWARE_CONFIG_FILE)
    softwares = config.get("softwares", [])

    for sw in softwares:
        if sw.get("name") == software_name:
            return sw.get("version", "")
    return ""


def _verify_hpc_software(
    host, software_name: str, bin_path: str, version_flag: str
) -> Dict[str, Any]:
    """
    Verify an HPC software is installed and version matches software_config.json.

    Generic function for OpenMPI, UCX, etc. Checks on first login_compiler_node.

    Args:
        host: Testinfra host object
        software_name: Name in software_config.json (e.g., "openmpi", "ucx")
        bin_path: Relative path under NFS mount (e.g., OPENMPI_BIN_PATH)
        version_flag: Flag to get version (e.g., "--version", "-v")

    Returns:
        Dict with success, installed, version, expected_version, version_match
    """
    results = {
        "success": False,
        "installed": False,
        "version": "",
        "expected_version": "",
        "version_match": False,
        "error": "",
    }

    nodes = get_login_compiler_nodes(host)
    if not nodes:
        results["error"] = "No login_compiler_node in PXE mapping"
        return results

    nfs_path = get_nfs_client_mount_path(host)
    if not nfs_path:
        results["error"] = "Could not get NFS client mount path from storage_config.yml"
        return results

    expected_version = get_software_version(host, software_name)
    results["expected_version"] = expected_version

    admin_ip = nodes[0].get("admin_ip", "")
    full_path = f"{nfs_path}/{bin_path}"

    cmd = run_on_remote_node(host, f"test -f {full_path} && echo EXISTS", admin_ip)
    if cmd.rc != 0 or "EXISTS" not in cmd.stdout:
        results["error"] = f"{software_name} not found at {full_path}"
        return results

    results["installed"] = True

    cmd = run_on_remote_node(host, f"{full_path} {version_flag} 2>/dev/null | head -1", admin_ip)
    if cmd.rc == 0 and cmd.stdout.strip():
        results["version"] = cmd.stdout.strip()
        if expected_version and expected_version in results["version"]:
            results["version_match"] = True
            results["success"] = True
        elif not expected_version:
            results["version_match"] = True
            results["success"] = True
        else:
            results["error"] = (
                f"Version mismatch: found '{results['version']}', "
                f"expected '{expected_version}'"
            )
    else:
        results["version"] = "unknown"
        results["error"] = f"Could not determine {software_name} version"

    return results


def verify_openmpi_installed(host) -> Dict[str, Any]:
    """Verify OpenMPI is installed and version matches software_config.json."""
    return _verify_hpc_software(host, "openmpi", OPENMPI_BIN_PATH, "--version")


def verify_ucx_installed(host) -> Dict[str, Any]:
    """Verify UCX is installed and version matches software_config.json."""
    return _verify_hpc_software(host, "ucx", UCX_BIN_PATH, "-v")


# =============================================================================
# LDMS SERVICE VERIFICATION
# =============================================================================

def is_ldms_enabled(host) -> bool:
    """Check if LDMS is enabled in software_config.json."""
    return is_software_enabled(host, "ldms")


def skip_if_ldms_not_enabled(host, log):
    """Skip test if LDMS is not enabled in software_config.json."""
    if not is_ldms_enabled(host):
        msg = SKIP_MSGS["ldms_not_enabled"]
        log.skipped(msg, SKIP_MSGS["skip_detail_not_enabled"].format(software="LDMS"))
        pytest.skip(msg)


def verify_ldms_sampler_service(host) -> Dict[str, Any]:
    """
    Verify ldmsd.sampler.service is running on all Slurm nodes.

    Checks slurm_control_node, slurm_node, login_node, login_compiler_node.

    Returns:
        Dict with success, node_results, failed_nodes
    """
    results = {
        "success": True,
        "total": 0,
        "running": 0,
        "failed": 0,
        "node_results": [],
        "failed_nodes": [],
    }

    # Get all Slurm nodes
    all_nodes = get_all_slurm_nodes(host)
    if not all_nodes:
        results["error"] = "No Slurm nodes found in PXE mapping"
        return results

    results["total"] = len(all_nodes)

    for node in all_nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")

        cmd = run_on_remote_node(
            host,
            f"systemctl is-active {LDMS_SAMPLER_SERVICE} 2>/dev/null",
            admin_ip
        )
        is_active = cmd.rc == 0 and "active" in cmd.stdout.strip()

        node_result = {
            "hostname": hostname,
            "admin_ip": admin_ip,
            "service": LDMS_SAMPLER_SERVICE,
            "active": is_active,
            "status": cmd.stdout.strip() if cmd.rc == 0 else "unknown",
        }

        results["node_results"].append(node_result)

        if is_active:
            results["running"] += 1
        else:
            results["failed"] += 1
            results["failed_nodes"].append(hostname)
            results["success"] = False

    return results


def verify_ldms_sampler_plugins(host) -> Dict[str, Any]:
    """
    Verify LDMS sampler plugins on nodes match telemetry_config.yml.

    Reads ldms_configurations.sampler_plugins from telemetry_config.yml and verifies
    /opt/ovis-ldms/etc/ldms/sampler.conf on each node has exactly those plugins.

    Returns:
        Dict with success, expected_plugins, node_results
    """
    from automation_library.core import load_input_file, TELEMETRY_CONFIG_FILE

    results = {
        "success": True,
        "expected_plugins": [],
        "node_results": [],
    }

    # Get expected plugins from telemetry_config.yml
    config = load_input_file(host, TELEMETRY_CONFIG_FILE)
    if not config:
        results["error"] = "Failed to load telemetry_config.yml"
        results["success"] = False
        return results

    ldms_cfg = config.get("ldms_configurations", {})
    sampler_configs = ldms_cfg.get("sampler_plugins", [])
    if not sampler_configs:
        results["error"] = "No ldms_configurations.sampler_plugins in telemetry_config.yml"
        results["success"] = False
        return results

    # Extract expected plugin names and their activation parameters
    expected_plugins = {}
    for plugin_config in sampler_configs:
        plugin_name = plugin_config.get("plugin_name", "")
        activation_params = plugin_config.get("activation_parameters", "")
        if plugin_name:
            expected_plugins[plugin_name] = activation_params

    results["expected_plugins"] = list(expected_plugins.keys())

    # Get all Slurm nodes
    all_nodes = get_all_slurm_nodes(host)
    if not all_nodes:
        results["error"] = "No Slurm nodes found in PXE mapping"
        return results

    for node in all_nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")

        node_result = {
            "hostname": hostname,
            "success": True,
            "configured_plugins": [],
            "missing_plugins": [],
            "extra_plugins": [],
            "param_mismatches": [],
        }

        # Read sampler.conf from node
        cmd = run_on_remote_node(
            host,
            f"cat {LDMS_SAMPLER_CONF_PATH} 2>/dev/null",
            admin_ip
        )

        if cmd.rc != 0:
            node_result["success"] = False
            node_result["error"] = "Failed to read sampler.conf"
            results["node_results"].append(node_result)
            results["success"] = False
            continue

        # Parse sampler.conf to extract configured plugins
        configured_plugins = {}
        lines = cmd.stdout.strip().split('\n')
        current_plugin = None

        for line in lines:
            line = line.strip()
            if line.startswith("load name="):
                current_plugin = line.replace("load name=", "").strip()
            elif line.startswith("start name=") and current_plugin:
                # Extract activation parameters (interval, offset, etc.)
                parts = line.split()
                params = " ".join(p for p in parts[1:] if not p.startswith("name="))
                configured_plugins[current_plugin] = params
                node_result["configured_plugins"].append(current_plugin)
                current_plugin = None

        # Compare expected vs configured
        for plugin_name, expected_params in expected_plugins.items():
            if plugin_name not in configured_plugins:
                node_result["missing_plugins"].append(plugin_name)
                node_result["success"] = False
            else:
                # Check if activation parameters match
                actual_params = configured_plugins[plugin_name]
                # Normalize parameters for comparison
                expected_set = set(expected_params.split())
                actual_set = set(actual_params.split())
                if expected_set != actual_set:
                    node_result["param_mismatches"].append(
                        f"{plugin_name}: expected '{expected_params}', got '{actual_params}'"
                    )

        # Check for extra plugins not in config
        for plugin_name in configured_plugins:
            if plugin_name not in expected_plugins:
                node_result["extra_plugins"].append(plugin_name)
                node_result["success"] = False

        results["node_results"].append(node_result)
        if not node_result["success"]:
            results["success"] = False

    return results


def verify_ldms_sampler_port(host) -> Dict[str, Any]:
    """
    Verify LDMS sampler port on Slurm nodes matches telemetry_config.yml.

    Reads ldms_sampler_port from telemetry_config.yml and checks
    /opt/ovis-ldms/etc/ldms/ldmsd.sampler.env on each node.

    Returns:
        Dict with success, expected_port, node_results
    """
    from automation_library.core import get_input_value, TELEMETRY_CONFIG_FILE

    results = {
        "success": True,
        "expected_port": None,
        "node_results": [],
        "mismatched_nodes": [],
    }

    # Get expected port from telemetry_config.yml
    expected_port = get_input_value(host, TELEMETRY_CONFIG_FILE, "ldms_sampler_port")
    if not expected_port:
        results["error"] = "ldms_sampler_port not found in telemetry_config.yml"
        results["success"] = False
        return results

    results["expected_port"] = expected_port

    # Get all Slurm nodes
    all_nodes = get_all_slurm_nodes(host)
    if not all_nodes:
        results["error"] = "No Slurm nodes found in PXE mapping"
        return results

    for node in all_nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")

        # Read LDMSD_PORT from env file
        cmd = run_on_remote_node(
            host,
            f"grep '^LDMSD_PORT=' {LDMS_SAMPLER_ENV_PATH} 2>/dev/null",
            admin_ip
        )

        actual_port = None
        if cmd.rc == 0 and cmd.stdout.strip():
            # Parse LDMSD_PORT=10001
            line = cmd.stdout.strip()
            if "=" in line:
                actual_port = line.split("=")[1].strip()

        port_match = str(actual_port) == str(expected_port)

        node_result = {
            "hostname": hostname,
            "expected_port": expected_port,
            "actual_port": actual_port,
            "match": port_match,
        }

        results["node_results"].append(node_result)

        if not port_match:
            results["mismatched_nodes"].append(hostname)
            results["success"] = False

    return results
