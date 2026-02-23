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

import csv
import io
import os
import re
import subprocess
import tempfile
from typing import Dict, Any, List, Optional

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


def _get_pxe_mapping_content(host) -> str:
    """
    Read pxe_mapping file content from inside omnia_core container.
    Uses pxe_mapping_file_path from provision_config.yml.

    Args:
        host: testinfra host object

    Returns:
        Content of pxe_mapping file as string, or empty string if not found
    """
    # Read provision_config.yml to get pxe_mapping_file_path
    result = run_in_container(host, f"cat {PROVISION_CONFIG_PATH}")
    if result.rc != 0:
        return ""

    # Extract pxe_mapping_file_path
    pattern = r'pxe_mapping_file_path:\s*["\']?([^"\'#\n]+)["\']?'
    match = re.search(pattern, result.stdout)
    if not match:
        return ""
    pxe_path = match.group(1).strip()

    # Read pxe_mapping file from inside container
    result = run_in_container(host, f"cat {pxe_path}")
    if result.rc != 0:
        return ""

    return result.stdout.strip()


def get_node_admin_ip(
    host: testinfra.host.Host,
    functional_group: str = None,
    hostname: str = None
) -> str:
    """
    Get the admin IP of a node from PXE mapping file.

    Reads provision_config.yml to get pxe_mapping_file_path, then extracts
    the admin IP based on functional_group_name or hostname.

    Args:
        host: Testinfra host connected to OIM server
        functional_group: Functional group name to match
        hostname: Hostname to match (e.g., 'k8scp1')

    Returns:
        Admin IP of matching node, or empty string if not found
    """
    admin_ip = ""

    if not functional_group and not hostname:
        return admin_ip

    pxe_content = _get_pxe_mapping_content(host)
    if not pxe_content:
        return admin_ip

    # CSV: FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,
    #      HOSTNAME,ADMIN_MAC,ADMIN_IP,...
    # Index: 0, 1, 2, 3, 4, 5, 6
    for line in pxe_content.split('\n'):
        parts = line.split(',')
        if len(parts) >= 7:
            line_func_group = parts[0]
            line_hostname = parts[4]

            # Match by functional_group or hostname
            if functional_group and functional_group in line_func_group:
                admin_ip = parts[6]
                break
            if hostname and hostname == line_hostname:
                admin_ip = parts[6]
                break

    return admin_ip


def get_nodes_info(
    host: testinfra.host.Host,
    search_by: Optional[str] = None,
    search_value: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Get nodes information from PXE mapping CSV.

    Reads provision_config.yml to get pxe_mapping_file_path, then parses the
    PXE mapping CSV inside omnia_core container.

    Args:
        host: Testinfra host connected to OIM server
        search_by: Column/key to filter on. Supported: functional_group, hostname,
            group_name, service_tag, parent_service_tag, admin_ip
        search_value: Value to match. For functional_group, match is substring
            (to support patterns like 'login_node' matching 'login_node_x86_64').

    Returns:
        List of node dicts. Keys are normalized to: functional_group, group_name,
        service_tag, parent_service_tag, hostname, admin_mac, admin_ip.
    """
    pxe_content = _get_pxe_mapping_content(host)
    if not pxe_content:
        return []

    try:
        reader = csv.DictReader(io.StringIO(pxe_content))
    except (csv.Error, TypeError):
        return []

    nodes: List[Dict[str, str]] = []
    for row in reader:
        node = {
            "functional_group": (row.get("FUNCTIONAL_GROUP_NAME") or "").strip(),
            "group_name": (row.get("GROUP_NAME") or "").strip(),
            "service_tag": (row.get("SERVICE_TAG") or "").strip(),
            "parent_service_tag": (row.get("PARENT_SERVICE_TAG") or "").strip(),
            "hostname": (row.get("HOSTNAME") or "").strip(),
            "admin_mac": (row.get("ADMIN_MAC") or "").strip(),
            "admin_ip": (row.get("ADMIN_IP") or "").strip(),
        }
        if any(node.values()):
            nodes.append(node)

    if not search_by or not search_value:
        return nodes

    search_by_norm = search_by.strip().lower()
    search_value_norm = str(search_value).strip()

    supported_keys = {
        "functional_group": "functional_group",
        "hostname": "hostname",
        "group_name": "group_name",
        "service_tag": "service_tag",
        "parent_service_tag": "parent_service_tag",
        "admin_ip": "admin_ip",
    }
    key = supported_keys.get(search_by_norm)
    if not key:
        return []

    if key == "functional_group":
        return [n for n in nodes if search_value_norm in (n.get(key) or "")]
    return [n for n in nodes if (n.get(key) or "") == search_value_norm]


def get_functional_groups_from_pxe_mapping(host) -> set:
    """
    Read pxe_mapping file from inside omnia_core container and extract functional groups.
    Uses pxe_mapping_file_path from provision_config.yml.

    Args:
        host: testinfra host object

    Returns:
        Set of functional group names (FUNCTIONAL_GROUP_NAME column)
    """
    pxe_content = _get_pxe_mapping_content(host)
    if not pxe_content:
        return set()

    # Parse CSV content
    lines = pxe_content.split('\n')
    if len(lines) < 2:  # Need header + at least one data row
        return set()

    # Get header and find FUNCTIONAL_GROUP_NAME column
    header = lines[0].split(',')
    try:
        fg_index = header.index('FUNCTIONAL_GROUP_NAME')
    except ValueError:
        return set()

    # Extract functional groups
    groups = set()
    for line in lines[1:]:
        if line.strip():
            cols = line.split(',')
            if len(cols) > fg_index and cols[fg_index].strip():
                groups.add(cols[fg_index].strip())

    return groups


def get_group_names_from_pxe_mapping(host) -> set:
    """
    Read pxe_mapping file from inside omnia_core container and extract group names.
    Uses pxe_mapping_file_path from provision_config.yml.

    Args:
        host: testinfra host object

    Returns:
        Set of group names (GROUP_NAME column)
    """
    pxe_content = _get_pxe_mapping_content(host)
    if not pxe_content:
        return set()

    # Parse CSV content
    lines = pxe_content.split('\n')
    if len(lines) < 2:
        return set()

    # Get header and find GROUP_NAME column
    header = lines[0].split(',')
    try:
        grp_index = header.index('GROUP_NAME')
    except ValueError:
        return set()

    # Extract group names
    groups = set()
    for line in lines[1:]:
        if line.strip():
            cols = line.split(',')
            if len(cols) > grp_index and cols[grp_index].strip():
                groups.add(cols[grp_index].strip())

    return groups
