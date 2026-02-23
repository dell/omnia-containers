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
Discovery Module - Verification Functions.

This module contains all verification functions for discovery automation.
Functions follow the return dictionary pattern with success, error keys.

Author: Dell Technologies
"""

import json
from typing import Dict, Any, List

import yaml

from automation_library.core import (
    get_functional_groups_from_pxe_mapping,
    get_nodes_info,
)
from ..vars.discovery_vars import (
    CONTAINER_NAME,
    SSH_TIMEOUT,
    CMD_TEMPLATES,
    OPENCHAMI_NODES_PATH,
    LOGIN_SERVICES,
    SLURM_CONTROL_SERVICES,
    FUNCTIONAL_GROUP_SLURM_CONTROL,
    FUNCTIONAL_GROUP_KUBE_CONTROL,
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


def _get_all_nodes(host) -> List[Dict[str, str]]:
    """Get all nodes from PXE mapping."""
    nodes_by_group = get_nodes_by_functional_group(host)
    all_nodes = []
    for nodes in nodes_by_group.values():
        all_nodes.extend(nodes)
    return all_nodes


# =============================================================================
# VERIFICATION FUNCTIONS
# =============================================================================

def verify_nodes_ssh_reachable(host) -> Dict[str, Any]:
    """Verify SSH connectivity to all nodes. Results grouped by functional_group."""
    nodes_by_group = get_nodes_by_functional_group(host)

    if not nodes_by_group:
        return {
            "success": False, "error": "No nodes found in PXE mapping",
            "total_count": 0, "success_count": 0, "failed_count": 0,
            "results_by_group": {}, "failed_nodes": [],
        }

    results_by_group = {}
    all_failed = []
    total = 0
    success_count = 0

    for func_group, nodes in nodes_by_group.items():
        group_results = []
        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")
            total += 1

            if not admin_ip:
                group_results.append({
                    "hostname": hostname, "admin_ip": "",
                    "ssh_via_ip": False, "output": "No IP",
                })
                all_failed.append(f"{hostname} (no IP)")
                continue

            result = _run_command_on_node(host, admin_ip, "hostname")
            ssh_ok = result["success"]

            if ssh_ok:
                success_count += 1
            else:
                all_failed.append(f"{hostname} ({admin_ip})")

            group_results.append({
                "hostname": hostname, "admin_ip": admin_ip,
                "ssh_via_ip": ssh_ok,
                "output": result["output"] if ssh_ok else result["error"],
            })
        results_by_group[func_group] = group_results

    return {
        "success": not all_failed,
        "total_count": total, "success_count": success_count,
        "failed_count": len(all_failed),
        "results_by_group": results_by_group,
        "failed_nodes": all_failed,
        "error": "" if not all_failed else f"{len(all_failed)} nodes unreachable",
    }


def verify_ochami_nodes_discovered(host) -> Dict[str, Any]:
    """Verify nodes are discovered in OpenCHAMI SMD. Returns detailed SMD info."""
    nodes_by_group = get_nodes_by_functional_group(host)
    all_nodes = _get_all_nodes(host)

    if not all_nodes:
        return {
            "success": False, "error": "No nodes found in PXE mapping",
            "total_count": 0, "discovered_count": 0, "bmc_count": 0,
            "smd_components": [], "nodes_by_group": {},
        }

    ochami_cmd = CMD_TEMPLATES["ochami_smd_get_all"]
    cmd = host.run(ochami_cmd)

    if cmd.rc != 0:
        return {
            "success": False, "error": f"Failed to query SMD: {cmd.stderr}",
            "total_count": len(all_nodes), "discovered_count": 0, "bmc_count": 0,
            "smd_components": [], "nodes_by_group": nodes_by_group,
        }

    try:
        smd_data = json.loads(cmd.stdout)
        components = smd_data.get("Components", [])
    except json.JSONDecodeError:
        return {
            "success": False, "error": "Failed to parse SMD response",
            "total_count": len(all_nodes), "discovered_count": 0, "bmc_count": 0,
            "smd_components": [], "nodes_by_group": nodes_by_group,
        }

    smd_nodes = [c for c in components if c.get("Type") == "Node"]
    smd_bmcs = [c for c in components if c.get("Type") == "NodeBMC"]

    smd_details = []
    for comp in smd_nodes:
        smd_details.append({
            "xname": comp.get("ID", ""), "type": comp.get("Type", ""),
            "role": comp.get("Role", ""), "nid": comp.get("NID", ""),
        })

    expected = len(all_nodes)
    discovered = len(smd_nodes)
    success = discovered >= expected

    return {
        "success": success, "total_count": expected, "discovered_count": discovered,
        "bmc_count": len(smd_bmcs), "smd_components": smd_details,
        "nodes_by_group": nodes_by_group,
        "error": "" if success else f"Expected {expected}, found {discovered}"
    }


def _make_yaml_fail(nodes_by_group, error_msg):
    """Return a failure dict for verify_nodes_yaml_file."""
    return {
        "success": False, "path": OPENCHAMI_NODES_PATH,
        "nodes_count": 0, "nodes_yaml_content": [],
        "nodes_by_group": nodes_by_group,
        "missing_nodes": [], "error": error_msg,
    }


def verify_nodes_yaml_file(host) -> Dict[str, Any]:
    """Verify nodes.yaml file exists. Returns detailed content."""
    nodes_by_group = get_nodes_by_functional_group(host)

    check_cmd = CMD_TEMPLATES["file_exists_container"].format(
        container=CONTAINER_NAME, file_path=OPENCHAMI_NODES_PATH,
    )
    cmd = host.run(check_cmd)
    if cmd.rc != 0:
        return _make_yaml_fail(
            nodes_by_group,
            f"File not found: {OPENCHAMI_NODES_PATH}",
        )

    read_cmd = CMD_TEMPLATES["read_file_container"].format(
        container=CONTAINER_NAME, file_path=OPENCHAMI_NODES_PATH,
    )
    cmd = host.run(read_cmd)
    if cmd.rc != 0:
        return _make_yaml_fail(
            nodes_by_group, f"Failed to read: {cmd.stderr}",
        )

    try:
        yaml_content = yaml.safe_load(cmd.stdout)
    except yaml.YAMLError as exc:
        return _make_yaml_fail(
            nodes_by_group, f"Invalid YAML: {exc}",
        )

    if isinstance(yaml_content, dict) and "nodes" in yaml_content:
        nodes_yaml = yaml_content["nodes"]
    elif isinstance(yaml_content, list):
        nodes_yaml = yaml_content
    else:
        return _make_yaml_fail(
            nodes_by_group, "nodes.yaml format not recognized",
        )

    nodes_detail = []
    yaml_hostnames = set()
    for entry in nodes_yaml:
        if isinstance(entry, dict):
            name = entry.get("name", entry.get("hostname", ""))
            if name:
                yaml_hostnames.add(name)
            nodes_detail.append({
                "name": name,
                "xname": entry.get("xname", ""),
                "group": entry.get("group", ""),
                "nid": entry.get("nid", ""),
                "bmc_ip": entry.get("bmc_ip", ""),
                "interfaces": entry.get("interfaces", []),
            })

    pxe_nodes = _get_all_nodes(host)
    pxe_hostnames = {n.get("hostname", "") for n in pxe_nodes}
    missing = list(pxe_hostnames - yaml_hostnames)

    return {
        "success": not missing,
        "path": OPENCHAMI_NODES_PATH,
        "nodes_count": len(nodes_yaml),
        "nodes_yaml_content": nodes_detail,
        "nodes_by_group": nodes_by_group,
        "missing_nodes": missing,
        "error": (
            "" if not missing
            else f"{len(missing)} nodes missing"
        ),
    }


def _check_passwordless_ssh(host, hostname, admin_ip):
    """Check passwordless SSH via IP and hostname for a single node."""
    result_ip = _run_batch_ssh(host, admin_ip, "echo OK")
    ssh_via_ip = result_ip["success"] and "OK" in result_ip["output"]

    result_host = _run_batch_ssh(host, hostname, "echo OK")
    ssh_via_hostname = (
        result_host["success"] and "OK" in result_host["output"]
    )
    return {
        "hostname": hostname, "admin_ip": admin_ip,
        "ssh_via_ip": ssh_via_ip,
        "ssh_via_hostname": ssh_via_hostname,
        "error": "" if ssh_via_ip else "SSH via IP failed",
    }


def verify_passwordless_ssh(host) -> Dict[str, Any]:
    """Verify passwordless SSH via IP and hostname. Grouped by role."""
    nodes_by_group = get_nodes_by_functional_group(host)

    if not nodes_by_group:
        return {
            "success": False, "error": "No nodes found",
            "total_count": 0, "success_count": 0,
            "failed_count": 0, "results_by_group": {},
            "failed_nodes": [],
        }

    results_by_group = {}
    all_failed = []
    total = 0
    success_count = 0

    for func_group, nodes in nodes_by_group.items():
        group_results = []
        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")
            total += 1

            if not admin_ip:
                group_results.append({
                    "hostname": hostname, "admin_ip": "",
                    "ssh_via_ip": False, "ssh_via_hostname": False,
                    "error": "No IP",
                })
                all_failed.append(f"{hostname} (no IP)")
                continue

            entry = _check_passwordless_ssh(
                host, hostname, admin_ip,
            )
            if entry["ssh_via_ip"]:
                success_count += 1
            else:
                all_failed.append(f"{hostname} ({admin_ip})")

            group_results.append(entry)
        results_by_group[func_group] = group_results

    return {
        "success": not all_failed,
        "total_count": total, "success_count": success_count,
        "failed_count": len(all_failed),
        "results_by_group": results_by_group,
        "failed_nodes": all_failed,
        "error": (
            "" if not all_failed
            else f"{len(all_failed)} nodes failed"
        ),
    }


def verify_node_hostnames(host) -> Dict[str, Any]:
    """Verify node hostnames match PXE mapping. Grouped by functional_group."""
    nodes_by_group = get_nodes_by_functional_group(host)

    if not nodes_by_group:
        return {
            "success": False, "error": "No nodes found",
            "total_count": 0, "match_count": 0,
            "mismatch_count": 0, "results_by_group": {},
        }

    results_by_group = {}
    total = 0
    match_count = 0
    mismatches = []

    for func_group, nodes in nodes_by_group.items():
        group_results = []
        for node in nodes:
            expected = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")
            total += 1

            if not admin_ip:
                group_results.append({
                    "expected": expected, "actual": "",
                    "admin_ip": "", "match": False,
                    "error": "No IP",
                })
                mismatches.append(expected)
                continue

            result = _run_command_on_node(
                host, admin_ip, "hostname",
            )
            if not result["success"]:
                group_results.append({
                    "expected": expected, "actual": "",
                    "admin_ip": admin_ip, "match": False,
                    "error": "SSH failed",
                })
                mismatches.append(expected)
                continue

            actual = result["output"]
            match = (
                expected.split('.')[0] == actual.split('.')[0]
            )

            if match:
                match_count += 1
            else:
                mismatches.append(expected)

            group_results.append({
                "expected": expected, "actual": actual,
                "admin_ip": admin_ip, "match": match,
                "error": "" if match else f"Got: {actual}",
            })
        results_by_group[func_group] = group_results

    return {
        "success": not mismatches,
        "total_count": total, "match_count": match_count,
        "mismatch_count": len(mismatches),
        "results_by_group": results_by_group,
        "error": (
            "" if not mismatches
            else f"{len(mismatches)} mismatches"
        ),
    }


# =============================================================================
# SERVICE VALIDATION HELPER
# =============================================================================

def _run_batch_ssh(host, target: str, command: str) -> Dict[str, Any]:
    """Run SSH command in batch mode (no password prompt)."""
    ssh_opts = CMD_TEMPLATES["ssh_opts_batch"].format(timeout=SSH_TIMEOUT)
    ssh_cmd = CMD_TEMPLATES["ssh_to_node"].format(
        container=CONTAINER_NAME, ssh_opts=ssh_opts,
        admin_ip=target, command=command,
    )
    cmd = host.run(ssh_cmd)
    return {
        "success": cmd.rc == 0,
        "output": cmd.stdout.strip(),
        "error": cmd.stderr.strip(),
    }


def _validate_service_on_node(host, admin_ip: str, service: str) -> Dict[str, Any]:
    """Check if a service is active on a node via SSH. Returns detailed status."""
    ssh_opts = CMD_TEMPLATES["ssh_opts"].format(timeout=SSH_TIMEOUT)
    # Get detailed status: Active state + enabled state + brief info
    cmd_str = (
        f"systemctl is-active {service} && systemctl is-enabled {service} && "
        f"systemctl show {service} --property=ActiveState,SubState,MainPID --no-pager"
    )
    ssh_cmd = CMD_TEMPLATES["ssh_to_node"].format(
        container=CONTAINER_NAME, ssh_opts=ssh_opts, admin_ip=admin_ip, command=cmd_str
    )
    cmd = host.run(ssh_cmd)
    output_lines = cmd.stdout.strip().split('\n')
    # Parse output: first line = is-active, second = is-enabled, rest = properties
    is_active = len(output_lines) > 0 and output_lines[0] == "active"
    is_enabled = len(output_lines) > 1 and output_lines[1] == "enabled"
    status_info = f"active={output_lines[0] if output_lines else 'unknown'}"
    if len(output_lines) > 1:
        status_info += f", enabled={output_lines[1]}"
    return {
        "service": service, "active": is_active, "enabled": is_enabled,
        "output": status_info, "raw": cmd.stdout.strip()
    }


def _run_command_on_node(host, admin_ip: str, command: str) -> Dict[str, Any]:
    """Run a command on a node via SSH and return result."""
    ssh_opts = CMD_TEMPLATES["ssh_opts"].format(timeout=SSH_TIMEOUT)
    ssh_cmd = CMD_TEMPLATES["ssh_to_node"].format(
        container=CONTAINER_NAME, ssh_opts=ssh_opts, admin_ip=admin_ip, command=command
    )
    cmd = host.run(ssh_cmd)
    return {"success": cmd.rc == 0, "output": cmd.stdout.strip(), "error": cmd.stderr.strip()}


# =============================================================================
# NODE BOOT VALIDATION
# =============================================================================

def validate_node_boot(host) -> Dict[str, Any]:
    """Validate all nodes have booted and are reachable. Results grouped by functional_group."""
    nodes_by_group = get_nodes_by_functional_group(host)

    if not nodes_by_group:
        return {
            "success": False, "error": "No nodes found in PXE mapping",
            "total_count": 0, "booted_count": 0, "results_by_group": {},
        }

    results_by_group = {}
    total = 0
    booted = 0
    failed_nodes = []

    for func_group, nodes in nodes_by_group.items():
        group_results = []
        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")
            total += 1

            if not admin_ip:
                group_results.append({
                    "hostname": hostname, "booted": False,
                    "uptime": "", "error": "No IP",
                })
                failed_nodes.append(hostname)
                continue

            result = _run_command_on_node(host, admin_ip, "uptime")
            is_booted = result["success"]

            if is_booted:
                booted += 1
            else:
                failed_nodes.append(hostname)

            group_results.append({
                "hostname": hostname, "admin_ip": admin_ip,
                "booted": is_booted,
                "uptime": result["output"] if is_booted else "",
                "error": "" if is_booted else "Unreachable",
            })
        results_by_group[func_group] = group_results

    return {
        "success": not failed_nodes,
        "total_count": total, "booted_count": booted,
        "failed_nodes": failed_nodes,
        "results_by_group": results_by_group,
        "error": (
            "" if not failed_nodes
            else f"{len(failed_nodes)} nodes not booted"
        ),
    }


# =============================================================================
# PACKAGE VALIDATION
# =============================================================================

def _check_packages_on_node(
    host, admin_ip: str, packages: List[str],
) -> Dict[str, Any]:
    """Check which packages are installed on a single node."""
    pkg_results = {}
    missing = []
    for pkg in packages:
        cmd_str = CMD_TEMPLATES["rpm_query"].format(package=pkg)
        result = _run_command_on_node(host, admin_ip, cmd_str)
        installed = (
            result["success"]
            and "not installed" not in result["output"].lower()
        )
        pkg_results[pkg] = installed
        if not installed:
            missing.append(pkg)
    return {"packages": pkg_results, "missing": missing}


def validate_packages_by_group(
    host, packages: List[str], functional_group: str = None,
) -> Dict[str, Any]:
    """Validate packages installed on nodes. Optionally filter by group."""
    if functional_group:
        nodes = get_nodes_info(
            host, search_by="functional_group",
            search_value=functional_group,
        )
        nodes_by_group = (
            {functional_group: nodes} if nodes else {}
        )
    else:
        nodes_by_group = get_nodes_by_functional_group(host)

    if not nodes_by_group:
        return {
            "success": False, "error": "No nodes found",
            "total_nodes": 0, "results_by_group": {},
        }

    results_by_group = {}
    all_missing = []

    for func_group, nodes in nodes_by_group.items():
        group_results = []
        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")

            if not admin_ip:
                group_results.append({
                    "hostname": hostname,
                    "packages": {}, "error": "No IP",
                })
                continue

            check = _check_packages_on_node(
                host, admin_ip, packages,
            )
            if check["missing"]:
                all_missing.append(
                    f"{hostname}: {check['missing']}",
                )

            group_results.append({
                "hostname": hostname, "admin_ip": admin_ip,
                "packages": check["packages"],
                "missing": check["missing"],
                "error": (
                    "" if not check["missing"]
                    else f"Missing: {check['missing']}"
                ),
            })
        results_by_group[func_group] = group_results

    total_nodes = sum(
        len(n) for n in nodes_by_group.values()
    )
    return {
        "success": not all_missing,
        "total_nodes": total_nodes,
        "packages_checked": packages,
        "results_by_group": results_by_group,
        "error": (
            "" if not all_missing
            else f"Missing packages on {len(all_missing)} nodes"
        ),
    }


# =============================================================================
# CONSOLIDATED VALIDATION FUNCTIONS
# =============================================================================

def _get_services_for_group(func_group: str) -> List[str]:
    """Return the correct service list based on functional group.

    slurm_control_node runs slurmctld; all other nodes run slurmd.
    """
    if FUNCTIONAL_GROUP_SLURM_CONTROL in func_group:
        return list(SLURM_CONTROL_SERVICES)
    return list(LOGIN_SERVICES)


def validate_all_services(host) -> Dict[str, Any]:
    """
    Validate services on ALL nodes, grouped by functional group.

    - slurm_control_node: sssd, munge, slurmctld
    - All other nodes: sssd, munge, slurmd

    Returns:
        Dict with success, group_results (per functional group), and error.
    """
    all_grouped = get_nodes_by_functional_group(host)
    if not all_grouped:
        return {
            "success": False, "skipped": True,
            "error": "No nodes found", "group_results": {},
        }

    group_results = {}
    all_success = True

    for func_group, nodes in all_grouped.items():
        services = _get_services_for_group(func_group)
        group_results[func_group] = []

        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")
            node_result = {
                "hostname": hostname, "admin_ip": admin_ip,
                "services": {},
            }

            if not admin_ip:
                for svc in services:
                    node_result["services"][svc] = {
                        "active": False, "output": "No IP",
                        "error": "No IP",
                    }
                all_success = False
                group_results[func_group].append(node_result)
                continue

            for svc in services:
                svc_result = _validate_service_on_node(
                    host, admin_ip, svc,
                )
                node_result["services"][svc] = {
                    "active": svc_result["active"],
                    "output": svc_result["output"],
                    "error": (
                        "" if svc_result["active"]
                        else f"{svc} not active"
                    ),
                }
                if not svc_result["active"]:
                    all_success = False

            group_results[func_group].append(node_result)

    return {
        "success": all_success, "skipped": False,
        "group_results": group_results,
        "error": (
            "" if all_success
            else "Some services not active on some nodes"
        ),
    }


def validate_all_sinfo(host) -> Dict[str, Any]:
    """
    Validate sinfo command on ALL nodes, grouped by functional group.

    Runs 'sinfo' on every node to verify Slurm cluster visibility.

    Returns:
        Dict with success, group_results (per functional group), and error.
    """
    all_grouped = get_nodes_by_functional_group(host)
    if not all_grouped:
        return {"success": False, "skipped": True, "error": "No nodes found", "group_results": {}}

    group_results = {}
    all_success = True

    for func_group, nodes in all_grouped.items():
        group_results[func_group] = []
        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")

            if not admin_ip:
                group_results[func_group].append({
                    "hostname": hostname, "success": False, "output": "", "error": "No IP",
                })
                all_success = False
                continue

            result = _run_command_on_node(host, admin_ip, "sinfo")
            group_results[func_group].append({
                "hostname": hostname, "admin_ip": admin_ip,
                "success": result["success"], "output": result["output"][:500],
                "error": "" if result["success"] else result["error"],
            })
            if not result["success"]:
                all_success = False

    return {
        "success": all_success, "skipped": False,
        "group_results": group_results,
        "error": "" if all_success else "sinfo failed on some nodes",
    }


def validate_all_ldap(host) -> Dict[str, Any]:
    """
    Validate LDAP on ALL nodes, grouped by functional group.

    Runs 'getent passwd' (UID >= 1000) on every node to check LDAP users.

    Returns:
        Dict with success, group_results (per functional group), and error.
    """
    all_grouped = get_nodes_by_functional_group(host)
    if not all_grouped:
        return {"success": False, "skipped": True, "error": "No nodes found", "group_results": {}}

    group_results = {}
    all_success = True

    for func_group, nodes in all_grouped.items():
        group_results[func_group] = []
        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")

            if not admin_ip:
                group_results[func_group].append({
                    "hostname": hostname, "success": False,
                    "users": [], "user_count": 0,
                    "error": "No IP",
                })
                all_success = False
                continue

            result = _run_command_on_node(
                host, admin_ip, CMD_TEMPLATES["ldap_check"],
            )
            users = []
            if result["success"] and result["output"].strip():
                for line in result["output"].strip().split("\n"):
                    parts = line.split(":")
                    if parts and parts[0]:
                        users.append(parts[0])
            ldap_ok = len(users) > 0
            group_results[func_group].append({
                "hostname": hostname, "admin_ip": admin_ip,
                "success": ldap_ok,
                "users": users,
                "user_count": len(users),
                "error": (
                    "" if ldap_ok
                    else "No LDAP users found"
                ),
            })
            if not ldap_ok:
                all_success = False

    return {
        "success": all_success, "skipped": False,
        "group_results": group_results,
        "error": "" if all_success else "LDAP not working on some nodes",
    }


# =============================================================================
# KUBERNETES VALIDATION
# =============================================================================

def _parse_kubectl_nodes_output(raw_output: str) -> Dict[str, Any]:
    """Parse 'kubectl get nodes' table output into structured data."""
    lines = raw_output.strip().split('\n')
    k8s_nodes = []
    not_ready = []

    for line in lines[1:]:  # Skip header line
        parts = line.split()
        if len(parts) >= 5:
            is_ready = parts[1].lower() == "ready"
            if not is_ready:
                not_ready.append(parts[0])
            k8s_nodes.append({
                "name": parts[0], "status": parts[1],
                "roles": parts[2], "age": parts[3],
                "version": parts[4],
            })

    success = not not_ready and len(k8s_nodes) > 0
    if not_ready:
        error_msg = f"{len(not_ready)} nodes not ready"
    elif not k8s_nodes:
        error_msg = "No k8s nodes found"
    else:
        error_msg = ""

    return {
        "k8s_nodes": k8s_nodes, "not_ready": not_ready,
        "total_nodes": len(k8s_nodes),
        "ready_count": len(k8s_nodes) - len(not_ready),
        "success": success, "error": error_msg,
    }


def _get_nodes_by_group_pattern(
    all_grouped: Dict[str, List[Dict[str, str]]],
    pattern: str,
) -> List[Dict[str, str]]:
    """Filter nodes from grouped dict where group name contains pattern."""
    matched = []
    for func_group, nodes in all_grouped.items():
        if pattern in func_group:
            matched.extend(nodes)
    return matched


def validate_kubernetes_nodes(host) -> Dict[str, Any]:
    """
    Validate Kubernetes via 'kubectl get nodes -A' on kube control planes.

    Finds kube_control_plane nodes from PXE mapping, SSHs into each,
    runs kubectl get nodes -A, and parses the table output.

    Returns:
        Dict with success, control_plane_results, and error.
    """
    all_grouped = get_nodes_by_functional_group(host)
    if not all_grouped:
        return {
            "success": False, "skipped": True,
            "error": "No nodes found in PXE mapping",
            "control_plane_results": [],
        }

    kube_cp_nodes = _get_nodes_by_group_pattern(
        all_grouped, FUNCTIONAL_GROUP_KUBE_CONTROL,
    )
    if not kube_cp_nodes:
        return {
            "success": False, "skipped": True,
            "error": "No kube_control_plane nodes found",
            "control_plane_results": [],
        }

    cp_results = []
    all_success = True
    fail_entry = {
        "success": False, "output": "", "k8s_nodes": [],
    }

    for node in kube_cp_nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")

        if not admin_ip:
            cp_results.append({
                **fail_entry,
                "hostname": hostname, "admin_ip": "",
                "error": "No admin_ip",
            })
            all_success = False
            continue

        cmd_key = CMD_TEMPLATES["kubectl_get_nodes_all"]
        result = _run_command_on_node(host, admin_ip, cmd_key)

        if not result["success"]:
            cp_results.append({
                **fail_entry,
                "hostname": hostname, "admin_ip": admin_ip,
                "error": result["error"],
            })
            all_success = False
            continue

        parsed = _parse_kubectl_nodes_output(result["output"])
        if not parsed["success"]:
            all_success = False

        cp_results.append({
            "hostname": hostname, "admin_ip": admin_ip,
            "output": result["output"].strip(),
            **parsed,
        })

    return {
        "success": all_success, "skipped": False,
        "control_plane_results": cp_results,
        "error": (
            "" if all_success
            else "Kubernetes validation failed on some nodes"
        ),
    }
