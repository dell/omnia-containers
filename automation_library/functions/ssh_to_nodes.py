"""
SSH to Nodes from omnia_core - Functions.

This module provides functions to:
- Parse PXE mapping file to extract hostname and admin IP
- SSH from omnia_core container to compute nodes
- Verify SSH connectivity to all nodes in the mapping file

Author: Dell Technologies
"""

import csv
from typing import Dict, Any, List, Optional


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_PXE_MAPPING_FILE = "/opt/omnia/input/project_default/pxe_mapping_file.csv"
SSH_TIMEOUT = 10
OMNIA_CORE_ALIAS = "omnia_core"


# =============================================================================
# PXE MAPPING FILE PARSER
# =============================================================================

def parse_pxe_mapping_file(host, file_path: str = None) -> Dict[str, Any]:
    """
    Parse the PXE mapping file and extract node information.

    Args:
        host: testinfra host object
        file_path: path to the PXE mapping CSV file

    Returns:
        Dict with 'success', 'nodes', 'error'
    """
    file_path = file_path or DEFAULT_PXE_MAPPING_FILE

    cmd = host.run(f"cat {file_path}")

    if cmd.rc != 0:
        return {
            "success": False,
            "nodes": [],
            "error": f"Failed to read file: {cmd.stderr.strip() or 'File not found'}"
        }

    nodes = []
    lines = cmd.stdout.strip().split('\n')

    if len(lines) < 2:
        return {
            "success": False,
            "nodes": [],
            "error": "File is empty or has no data rows"
        }

    header = lines[0].split(',')

    try:
        hostname_idx = header.index('HOSTNAME')
        admin_ip_idx = header.index('ADMIN_IP')
    except ValueError as e:
        return {
            "success": False,
            "nodes": [],
            "error": f"Required column not found: {str(e)}"
        }

    functional_group_idx = header.index('FUNCTIONAL_GROUP_NAME') if 'FUNCTIONAL_GROUP_NAME' in header else None
    group_name_idx = header.index('GROUP_NAME') if 'GROUP_NAME' in header else None
    service_tag_idx = header.index('SERVICE_TAG') if 'SERVICE_TAG' in header else None
    bmc_ip_idx = header.index('BMC_IP') if 'BMC_IP' in header else None

    for line in lines[1:]:
        if not line.strip():
            continue

        fields = line.split(',')

        node = {
            "hostname": fields[hostname_idx] if len(fields) > hostname_idx else "",
            "admin_ip": fields[admin_ip_idx] if len(fields) > admin_ip_idx else "",
            "functional_group": fields[functional_group_idx] if functional_group_idx and len(fields) > functional_group_idx else "",
            "group_name": fields[group_name_idx] if group_name_idx and len(fields) > group_name_idx else "",
            "service_tag": fields[service_tag_idx] if service_tag_idx and len(fields) > service_tag_idx else "",
            "bmc_ip": fields[bmc_ip_idx] if bmc_ip_idx and len(fields) > bmc_ip_idx else "",
        }

        if node["hostname"] or node["admin_ip"]:
            nodes.append(node)

    return {
        "success": True,
        "nodes": nodes,
        "count": len(nodes),
        "error": None
    }


# =============================================================================
# SSH FUNCTIONS
# =============================================================================

def ssh_from_omnia_core_to_node(host, target: str, command: str = "hostname", 
                                 timeout: int = None, use_ip: bool = True) -> Dict[str, Any]:
    """
    SSH from omnia_core container to a target node.

    Args:
        host: testinfra host object
        target: hostname or IP address of the target node
        command: command to execute on the target node
        timeout: SSH connection timeout
        use_ip: if True, use IP address; if False, use hostname

    Returns:
        Dict with 'success', 'output', 'target', 'error'
    """
    timeout = timeout or SSH_TIMEOUT

    ssh_cmd = (
        f"ssh -o BatchMode=yes -o StrictHostKeyChecking=no "
        f"-o ConnectTimeout={timeout} {OMNIA_CORE_ALIAS} "
        f"'ssh -o BatchMode=yes -o StrictHostKeyChecking=no "
        f"-o ConnectTimeout={timeout} {target} \"{command}\"'"
    )

    cmd = host.run(ssh_cmd)

    if cmd.rc == 0:
        return {
            "success": True,
            "output": cmd.stdout.strip(),
            "target": target,
            "error": None
        }

    return {
        "success": False,
        "output": cmd.stdout.strip(),
        "target": target,
        "error": cmd.stderr.strip() or "SSH connection failed"
    }


def ssh_to_node_by_hostname(host, hostname: str, command: str = "hostname", 
                            timeout: int = None) -> Dict[str, Any]:
    """
    SSH from omnia_core to a node using its hostname.

    Args:
        host: testinfra host object
        hostname: hostname of the target node
        command: command to execute
        timeout: SSH timeout

    Returns:
        Dict with 'success', 'output', 'target', 'error'
    """
    return ssh_from_omnia_core_to_node(host, hostname, command, timeout, use_ip=False)


def ssh_to_node_by_ip(host, admin_ip: str, command: str = "hostname", 
                      timeout: int = None) -> Dict[str, Any]:
    """
    SSH from omnia_core to a node using its admin IP.

    Args:
        host: testinfra host object
        admin_ip: admin IP address of the target node
        command: command to execute
        timeout: SSH timeout

    Returns:
        Dict with 'success', 'output', 'target', 'error'
    """
    return ssh_from_omnia_core_to_node(host, admin_ip, command, timeout, use_ip=True)


def ssh_to_all_nodes(host, file_path: str = None, command: str = "hostname",
                     use_ip: bool = True, timeout: int = None) -> Dict[str, Any]:
    """
    SSH from omnia_core to all nodes in the PXE mapping file.

    Args:
        host: testinfra host object
        file_path: path to PXE mapping file
        command: command to execute on each node
        use_ip: if True, use admin IP; if False, use hostname
        timeout: SSH timeout

    Returns:
        Dict with 'success', 'results', 'summary', 'error'
    """
    mapping = parse_pxe_mapping_file(host, file_path)

    if not mapping["success"]:
        return {
            "success": False,
            "results": [],
            "summary": {},
            "error": mapping["error"]
        }

    results = []
    success_count = 0
    failed_count = 0

    for node in mapping["nodes"]:
        target = node["admin_ip"] if use_ip else node["hostname"]

        if not target:
            results.append({
                "hostname": node["hostname"],
                "admin_ip": node["admin_ip"],
                "target_used": target,
                "success": False,
                "output": "",
                "error": "No valid target (IP or hostname)"
            })
            failed_count += 1
            continue

        ssh_result = ssh_from_omnia_core_to_node(host, target, command, timeout)

        results.append({
            "hostname": node["hostname"],
            "admin_ip": node["admin_ip"],
            "functional_group": node["functional_group"],
            "target_used": target,
            "success": ssh_result["success"],
            "output": ssh_result["output"],
            "error": ssh_result["error"]
        })

        if ssh_result["success"]:
            success_count += 1
        else:
            failed_count += 1

    return {
        "success": failed_count == 0,
        "results": results,
        "summary": {
            "total": len(results),
            "success": success_count,
            "failed": failed_count
        },
        "error": None
    }


def verify_ssh_connectivity_to_nodes(host, file_path: str = None, 
                                     timeout: int = None) -> Dict[str, Any]:
    """
    Verify SSH connectivity from omnia_core to all nodes in the mapping file.

    Args:
        host: testinfra host object
        file_path: path to PXE mapping file
        timeout: SSH timeout

    Returns:
        Dict with 'success', 'nodes', 'summary', 'error'
    """
    result = ssh_to_all_nodes(host, file_path, command="echo SSH_OK && hostname", 
                              use_ip=True, timeout=timeout)

    if not result["success"] and result["error"]:
        return result

    verified_nodes = []
    for node_result in result["results"]:
        verified = node_result["success"] and "SSH_OK" in node_result.get("output", "")
        verified_nodes.append({
            **node_result,
            "verified": verified
        })

    return {
        "success": all(n["verified"] for n in verified_nodes),
        "nodes": verified_nodes,
        "summary": result["summary"],
        "error": None
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_node_by_hostname(host, hostname: str, file_path: str = None) -> Dict[str, Any]:
    """
    Get node information by hostname from the mapping file.

    Args:
        host: testinfra host object
        hostname: hostname to search for
        file_path: path to PXE mapping file

    Returns:
        Dict with 'success', 'node', 'error'
    """
    mapping = parse_pxe_mapping_file(host, file_path)

    if not mapping["success"]:
        return {
            "success": False,
            "node": None,
            "error": mapping["error"]
        }

    for node in mapping["nodes"]:
        if node["hostname"] == hostname:
            return {
                "success": True,
                "node": node,
                "error": None
            }

    return {
        "success": False,
        "node": None,
        "error": f"Node with hostname '{hostname}' not found"
    }


def get_node_by_ip(host, admin_ip: str, file_path: str = None) -> Dict[str, Any]:
    """
    Get node information by admin IP from the mapping file.

    Args:
        host: testinfra host object
        admin_ip: admin IP to search for
        file_path: path to PXE mapping file

    Returns:
        Dict with 'success', 'node', 'error'
    """
    mapping = parse_pxe_mapping_file(host, file_path)

    if not mapping["success"]:
        return {
            "success": False,
            "node": None,
            "error": mapping["error"]
        }

    for node in mapping["nodes"]:
        if node["admin_ip"] == admin_ip:
            return {
                "success": True,
                "node": node,
                "error": None
            }

    return {
        "success": False,
        "node": None,
        "error": f"Node with admin IP '{admin_ip}' not found"
    }


def get_nodes_by_functional_group(host, functional_group: str, 
                                   file_path: str = None) -> Dict[str, Any]:
    """
    Get all nodes belonging to a functional group.

    Args:
        host: testinfra host object
        functional_group: functional group name (e.g., 'slurm_node_x86_64')
        file_path: path to PXE mapping file

    Returns:
        Dict with 'success', 'nodes', 'error'
    """
    mapping = parse_pxe_mapping_file(host, file_path)

    if not mapping["success"]:
        return {
            "success": False,
            "nodes": [],
            "error": mapping["error"]
        }

    matching_nodes = [
        node for node in mapping["nodes"]
        if node["functional_group"] == functional_group
    ]

    return {
        "success": True,
        "nodes": matching_nodes,
        "count": len(matching_nodes),
        "error": None
    }


def list_all_nodes(host, file_path: str = None) -> Dict[str, Any]:
    """
    List all nodes from the PXE mapping file.

    Args:
        host: testinfra host object
        file_path: path to PXE mapping file

    Returns:
        Dict with 'success', 'nodes', 'error'
    """
    return parse_pxe_mapping_file(host, file_path)
