# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Testinfra utilities for molecule tests.
"""

import os
import re
import subprocess
import tempfile
from typing import Dict, Any, List, Union

import yaml
import testinfra

from .vars import PROVISION_CONFIG_PATH


def _get_project_root() -> str:
    """Get the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_user_config() -> Dict[str, Any]:
    """Load user_config.yml."""
    config_path = os.path.join(_get_project_root(), "user_config.yml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _is_local_ip(ip: str) -> bool:
    """Check if IP belongs to this machine."""
    if ip in ["localhost", "127.0.0.1", ""]:
        return True
    try:
        result = subprocess.run(
            ["hostname", "-I"], capture_output=True, text=True, timeout=5, check=False
        )
        return ip in result.stdout.strip().split()
    except (OSError, subprocess.SubprocessError):
        return False


def get_testinfra_host() -> testinfra.host.Host:
    """
    Get testinfra host connected to OIM server.

    Always reads IP directly from user_config.yml to avoid hostname resolution issues.
    """
    config = load_user_config()
    oim_ip = config.get("oim_server_ip", "localhost")

    # Local execution
    if _is_local_ip(oim_ip):
        return testinfra.get_host("local://")

    # Remote - always use direct SSH with IP from user_config.yml
    ssh_user = config.get("oim_ssh_user", "root")
    ssh_port = config.get("oim_ssh_port", 22)
    ssh_password = config.get("oim_ssh_password", "")

    # Create a temporary inventory with resolved IP
    inventory_dir = os.path.join(tempfile.gettempdir(), "omnia_testinfra")
    os.makedirs(inventory_dir, exist_ok=True)
    inventory_path = os.path.join(inventory_dir, "inventory.ini")

    with open(inventory_path, "w", encoding="utf-8") as f:
        f.write("[all]\n")
        f.write(f"oim_server ansible_host={oim_ip} ansible_user={ssh_user} ")
        f.write(f"ansible_port={ssh_port} ansible_ssh_pass={ssh_password} ")
        f.write("ansible_connection=ssh ")
        ssh_args = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        f.write(f"ansible_ssh_common_args='{ssh_args}'\n")

    return testinfra.get_host("ansible://oim_server", ansible_inventory=inventory_path)


def run_on_oim(host: testinfra.host.Host, cmd: str) -> subprocess.CompletedProcess:
    """
    Run command on OIM server.

    Args:
        host: Testinfra host connected to OIM server
        cmd: Command to execute

    Returns:
        Result with stdout, stderr, rc attributes
    """
    result = host.run(cmd)
    return result


def run_in_container(
    host: testinfra.host.Host,
    cmd: str,
    container: str = "omnia_core"
) -> subprocess.CompletedProcess:
    """
    Run command inside a container on OIM server.

    Args:
        host: Testinfra host connected to OIM server
        cmd: Command to execute inside container
        container: Container name (default: omnia_core)

    Returns:
        Result with stdout, stderr, rc attributes
    """
    container_cmd = f"podman exec {container} {cmd}"
    return host.run(container_cmd)


def run_on_remote_node(
    host: testinfra.host.Host,
    cmd: str,
    admin_ip: str
) -> subprocess.CompletedProcess:
    """
    Run command on remote node via SSH from omnia_core container.

    SSH from omnia_core to remote node uses passwordless SSH.

    Args:
        host: Testinfra host connected to OIM server
        cmd: Command to execute on remote node
        admin_ip: Admin IP of remote node (from PXE mapping file)

    Returns:
        Result with stdout, stderr, rc attributes
    """
    ssh_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    ssh_cmd = f"ssh {ssh_opts} root@{admin_ip} '{cmd}'"
    return run_in_container(host, ssh_cmd)


# Column name mapping (CSV header -> internal field name)
_PXE_COLUMN_MAP = {
    "FUNCTIONAL_GROUP_NAME": "functional_group",
    "GROUP_NAME": "group_name",
    "SERVICE_TAG": "service_tag",
    "PARENT_SERVICE_TAG": "parent_service_tag",
    "HOSTNAME": "hostname",
    "ADMIN_MAC": "admin_mac",
    "ADMIN_IP": "admin_ip",
    "BMC_MAC": "bmc_mac",
    "BMC_IP": "bmc_ip",
}


def _read_pxe_mapping(host: testinfra.host.Host) -> tuple:
    """
    Read and parse the PXE mapping file from omnia_core container.

    Handles dynamic column order by parsing the header row.

    Args:
        host: Testinfra host connected to OIM server

    Returns:
        Tuple of (column_indices, rows):
        - column_indices: Dict mapping field name to column index
        - rows: List of rows, where each row is a list of column values

        Returns ({}, []) if file cannot be read.
    """
    # Read provision_config.yml to get pxe_mapping_file_path
    result = run_in_container(host, f"cat {PROVISION_CONFIG_PATH}")
    if result.rc != 0:
        return {}, []

    # Extract pxe_mapping_file_path
    pattern = r'pxe_mapping_file_path:\s*["\']?([^"\'#\n]+)["\']?'
    match = re.search(pattern, result.stdout)
    if not match:
        return {}, []
    pxe_mapping_path = match.group(1).strip()

    # Read PXE mapping file
    result = run_in_container(host, f"cat {pxe_mapping_path}")
    if result.rc != 0:
        return {}, []

    lines = result.stdout.strip().split('\n')
    if not lines:
        return {}, []

    # Parse header row to get column indices
    header = [col.strip().upper() for col in lines[0].split(',')]
    column_indices = {}
    for i, col_name in enumerate(header):
        if col_name in _PXE_COLUMN_MAP:
            field_name = _PXE_COLUMN_MAP[col_name]
            column_indices[field_name] = i

    # Parse data rows (skip header)
    rows = []
    for line in lines[1:]:
        if line.strip():
            parts = line.split(',')
            rows.append(parts)

    return column_indices, rows


def get_node_info(
    host: testinfra.host.Host,
    search_by: str = None,
    search_value: str = None
) -> Dict[str, str]:
    """
    Get FIRST matching node's info from PXE mapping file.

    Search by any field and return all fields for the matching node.
    For getting all matching nodes, use get_nodes_info() instead.

    Args:
        host: Testinfra host connected to OIM server
        search_by: Field name to search by (all use exact match). Options:
            - "functional_group"
            - "hostname"
            - "admin_ip"
            - "service_tag"
            - "bmc_ip"
            - "group_name"
            - "admin_mac"
            - "bmc_mac"
            - "parent_service_tag"
        search_value: Value to search for (exact match)

    Returns:
        Dict with all node fields, or empty dict if not found:
        {
            "functional_group": "...",
            "group_name": "...",
            "service_tag": "...",
            "parent_service_tag": "...",
            "hostname": "...",
            "admin_mac": "...",
            "admin_ip": "...",
            "bmc_mac": "...",
            "bmc_ip": "..."
        }

    Example:
        # Search by functional_group (exact match)
        node = get_node_info(host, search_by="functional_group",
                              search_value="service_kube_control_plane_x86_64")
        print(f"IP: {node['admin_ip']}, Hostname: {node['hostname']}")

        # Search by admin_ip
        node = get_node_admin_ip(host, search_by="admin_ip", search_value="172.16.107.21")
        print(f"Hostname: {node['hostname']}, BMC IP: {node['bmc_ip']}")

        # Search by hostname
        node = get_node_admin_ip(host, search_by="hostname", search_value="k8scp1")
        print(f"IP: {node['admin_ip']}, Service Tag: {node['service_tag']}")
    """
    if not search_by or not search_value:
        return {}

    column_indices, rows = _read_pxe_mapping(host)

    if search_by not in column_indices:
        return {}

    search_idx = column_indices[search_by]

    for parts in rows:
        if len(parts) <= search_idx:
            continue

        line_value = parts[search_idx].strip()

        # Exact match for all fields
        if line_value == search_value:
            result = {}
            for field_name, idx in column_indices.items():
                result[field_name] = parts[idx].strip() if len(parts) > idx else ""
            return result

    return {}


def get_nodes_info(
    host: testinfra.host.Host,
    search_by: str = None,
    search_value: str = None
) -> List[Dict[str, str]]:
    """
    Get ALL matching nodes' info from PXE mapping file.

    Search by any field and return all fields for all matching nodes.
    For getting just the first match, use get_node_info() instead.

    Args:
        host: Testinfra host connected to OIM server
        search_by: Field name to search by (all use exact match). Options:
            - "functional_group"
            - "hostname"
            - "admin_ip"
            - "service_tag"
            - "bmc_ip"
            - "group_name"
            - "admin_mac"
            - "bmc_mac"
            - "parent_service_tag"
        search_value: Value to search for (exact match)

    Returns:
        List of dicts, each with all node fields:
        [
            {
                "functional_group": "...",
                "group_name": "...",
                "service_tag": "...",
                "parent_service_tag": "...",
                "hostname": "...",
                "admin_mac": "...",
                "admin_ip": "...",
                "bmc_mac": "...",
                "bmc_ip": "..."
            },
            ...
        ]

    Example:
        # Get all nodes in functional_group (exact match)
        nodes = get_nodes_info(host, search_by="functional_group",
                                search_value="service_kube_control_plane_x86_64")
        for node in nodes:
            print(f"IP: {node['admin_ip']}, Hostname: {node['hostname']}")

        # Get all nodes by group_name
        nodes = get_node_admin_ips(host, search_by="group_name", search_value="grp0")
        for node in nodes:
            print(f"{node['hostname']} - {node['admin_ip']} - {node['bmc_ip']}")
    """
    if not search_by or not search_value:
        return []

    column_indices, rows = _read_pxe_mapping(host)

    if search_by not in column_indices:
        return []

    search_idx = column_indices[search_by]
    results = []

    for parts in rows:
        if len(parts) <= search_idx:
            continue

        line_value = parts[search_idx].strip()

        # Exact match for all fields
        if line_value == search_value:
            result = {}
            for field_name, idx in column_indices.items():
                result[field_name] = parts[idx].strip() if len(parts) > idx else ""
            results.append(result)

    return results


# =============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# These functions provide backward compatibility with the merged git version.
# They use _read_pxe_mapping() internally to avoid code duplication.
# =============================================================================

def get_node_admin_ip(
    host: testinfra.host.Host,
    functional_group: str = None,
    hostname: str = None
) -> str:
    """
    Get the admin IP of a node from PXE mapping file.

    This is a backward-compatible wrapper around get_node_info().

    Args:
        host: Testinfra host connected to OIM server
        functional_group: Functional group name to match (contains match)
        hostname: Hostname to match (exact match)

    Returns:
        Admin IP of matching node, or empty string if not found
    """
    if hostname:
        node = get_node_info(host, search_by="hostname", search_value=hostname)
        return node.get("admin_ip", "")

    if functional_group:
        # For functional_group, use contains match (backward compat)
        column_indices, rows = _read_pxe_mapping(host)
        fg_idx = column_indices.get("functional_group")
        ip_idx = column_indices.get("admin_ip")
        if fg_idx is not None and ip_idx is not None:
            for parts in rows:
                if len(parts) > max(fg_idx, ip_idx):
                    if functional_group in parts[fg_idx]:
                        return parts[ip_idx].strip()

    return ""


def get_functional_groups_from_pxe_mapping(host: testinfra.host.Host) -> set:
    """
    Extract all unique functional group names from PXE mapping file.

    Args:
        host: Testinfra host object

    Returns:
        Set of functional group names
    """
    column_indices, rows = _read_pxe_mapping(host)
    fg_idx = column_indices.get("functional_group")
    if fg_idx is None:
        return set()

    groups = set()
    for parts in rows:
        if len(parts) > fg_idx and parts[fg_idx].strip():
            groups.add(parts[fg_idx].strip())
    return groups


def get_group_names_from_pxe_mapping(host: testinfra.host.Host) -> set:
    """
    Extract all unique group names from PXE mapping file.

    Args:
        host: Testinfra host object

    Returns:
        Set of group names
    """
    column_indices, rows = _read_pxe_mapping(host)
    grp_idx = column_indices.get("group_name")
    if grp_idx is None:
        return set()

    groups = set()
    for parts in rows:
        if len(parts) > grp_idx and parts[grp_idx].strip():
            groups.add(parts[grp_idx].strip())
    return groups
