"""
Testinfra utilities for molecule tests.
"""

import os
import subprocess
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


def load_omnia_sh_config() -> Dict[str, Any]:
    """Load omnia_sh_config.yml."""
    config_path = os.path.join(_get_project_root(), "omnia_sh_config.yml")
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
    
    Auto-detects local vs remote execution.
    """
    config = load_user_config()
    oim_ip = config.get("oim_server_ip", "localhost")
    
    # Local execution
    if _is_local_ip(oim_ip):
        return testinfra.get_host("local://")
    
    # Remote - use molecule inventory if available
    molecule_inventory = os.environ.get("MOLECULE_INVENTORY_FILE")
    if molecule_inventory and os.path.exists(molecule_inventory):
        return testinfra.get_host("ansible://oim_server", ansible_inventory=molecule_inventory)
    
    # Fallback - create inventory from user_config.yml
    ssh_user = config.get("oim_ssh_user", "root")
    ssh_port = config.get("oim_ssh_port", 22)
    ssh_password = config.get("oim_ssh_password", "")
    
    inventory_path = os.path.join(_get_project_root(), "molecule", "omnia_sh", "inventory.yml")
    os.makedirs(os.path.dirname(inventory_path), exist_ok=True)
    
    with open(inventory_path, "w") as f:
        f.write(f"[all]\noim_server ansible_host={oim_ip} ansible_user={ssh_user} "
                f"ansible_port={ssh_port} ansible_ssh_pass={ssh_password} "
                f"ansible_connection=ssh ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n")
    
    return testinfra.get_host("ansible://oim_server", ansible_inventory=inventory_path)
