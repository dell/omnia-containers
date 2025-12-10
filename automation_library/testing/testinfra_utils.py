"""
Testinfra utilities for molecule tests.

This module provides shared utilities for connecting to the OIM server
via testinfra. It auto-detects whether tests are running locally on
the OIM server or remotely.

Usage:
    from automation_library.testing import get_testinfra_host
    
    @pytest.fixture(scope="module")
    def host():
        return get_testinfra_host()

Author: Dell Technologies
"""

import os
import subprocess
from typing import Dict, Any, Optional

import yaml
import testinfra


# =============================================================================
# Configuration Loading
# =============================================================================

def get_project_root() -> str:
    """Get the project root directory."""
    # Go up from automation_library/testing/ to project root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_user_config() -> Dict[str, Any]:
    """
    Load user_config.yml to get OIM server details.
    
    Returns:
        Dict containing user configuration
    """
    config_path = os.path.join(get_project_root(), "user_config.yml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def load_omnia_sh_config() -> Dict[str, Any]:
    """
    Load omnia_sh_config.yml for omnia.sh specific settings.
    
    Returns:
        Dict containing omnia_sh configuration
    """
    config_path = os.path.join(get_project_root(), "omnia_sh_config.yml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


# =============================================================================
# Network Utilities
# =============================================================================

def is_local_ip(ip: str) -> bool:
    """
    Check if the given IP belongs to this machine.
    
    Args:
        ip: IP address to check
        
    Returns:
        True if IP is local, False otherwise
    """
    if ip in ["localhost", "127.0.0.1", ""]:
        return True
    
    try:
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True,
            text=True,
            timeout=5
        )
        local_ips = result.stdout.strip().split()
        return ip in local_ips
    except Exception:
        return False


# =============================================================================
# Testinfra Host Factory
# =============================================================================

def get_testinfra_host(
    use_ansible_inventory: bool = True,
    ansible_host_name: str = "oim_server"
) -> testinfra.host.Host:
    """
    Get a testinfra host connected to the OIM server.
    
    This function auto-detects whether tests are running on the OIM server
    itself (uses local connection) or remotely (uses Ansible inventory).
    
    Args:
        use_ansible_inventory: If True, use molecule's Ansible inventory for remote
        ansible_host_name: Name of the host in Ansible inventory
        
    Returns:
        testinfra Host object connected to OIM server
        
    Usage:
        @pytest.fixture(scope="module")
        def host():
            return get_testinfra_host()
    """
    config = load_user_config()
    oim_ip = config.get("oim_server_ip", "localhost")
    
    # Check if we're running on the OIM server itself
    if is_local_ip(oim_ip):
        # Running locally on OIM server - use local connection
        return testinfra.get_host("local://")
    
    # Running remotely - try to use Ansible inventory from molecule
    if use_ansible_inventory:
        molecule_inventory = os.environ.get("MOLECULE_INVENTORY_FILE")
        if molecule_inventory and os.path.exists(molecule_inventory):
            return testinfra.get_host(
                f"ansible://{ansible_host_name}",
                ansible_inventory=molecule_inventory
            )
    
    # Fallback to local if no inventory available
    return testinfra.get_host("local://")


def get_oim_server_ip() -> str:
    """
    Get the OIM server IP from user_config.yml.
    
    Returns:
        OIM server IP address
    """
    config = load_user_config()
    return config.get("oim_server_ip", "localhost")


def get_oim_ssh_credentials() -> Dict[str, Any]:
    """
    Get SSH credentials for OIM server from user_config.yml.
    
    Returns:
        Dict with 'user', 'password', 'port' keys
    """
    config = load_user_config()
    return {
        "user": config.get("oim_ssh_user", "root"),
        "password": config.get("oim_ssh_password", ""),
        "port": config.get("oim_ssh_port", 22),
    }
