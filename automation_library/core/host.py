"""
Testinfra utilities for molecule tests.
"""

import os
import subprocess
import tempfile
from typing import Dict, Any

import yaml
import testinfra


def _get_project_root() -> str:
    """Get the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_user_config() -> Dict[str, Any]:
    """Load user_config.yml."""
    config_path = os.path.join(_get_project_root(), "user_config.yml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def _is_local_ip(ip: str) -> bool:
    """Check if IP belongs to this machine."""
    if ip in ["localhost", "127.0.0.1", ""]:
        return True
    try:
        result = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5)
        return ip in result.stdout.strip().split()
    except Exception:
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

    with open(inventory_path, "w") as f:
        f.write(f"[all]\n")
        f.write(f"oim_server ansible_host={oim_ip} ansible_user={ssh_user} ")
        f.write(f"ansible_port={ssh_port} ansible_ssh_pass={ssh_password} ")
        f.write(f"ansible_connection=ssh ")
        f.write(f"ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'\n")

    return testinfra.get_host("ansible://oim_server", ansible_inventory=inventory_path)
