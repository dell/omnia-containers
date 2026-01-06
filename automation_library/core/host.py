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
from typing import Dict, Any

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

    # Read provision_config.yml to get pxe_mapping_file_path
    result = run_in_container(host, f"cat {PROVISION_CONFIG_PATH}")
    if result.rc != 0:
        return admin_ip

    # Extract pxe_mapping_file_path
    pattern = r'pxe_mapping_file_path:\s*["\']?([^"\'#\n]+)["\']?'
    match = re.search(pattern, result.stdout)
    if not match:
        return admin_ip
    pxe_mapping_path = match.group(1).strip()

    # Read PXE mapping file
    result = run_in_container(host, f"cat {pxe_mapping_path}")
    if result.rc != 0:
        return admin_ip

    # CSV: FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,
    #      HOSTNAME,ADMIN_MAC,ADMIN_IP,...
    # Index: 0, 1, 2, 3, 4, 5, 6
    for line in result.stdout.strip().split('\n'):
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
