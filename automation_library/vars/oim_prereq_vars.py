"""
Variables for OIM prerequisite checks.

This file loads user configuration from user_config.yml and provides defaults.
Users should edit user_config.yml - not this file.
"""

import os
import yaml

# Path to user config file (in project root, next to requirements.txt)
# automation_library/vars/oim_prereq_vars.py -> go up 3 levels to project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_USER_CONFIG_FILE = os.path.join(_PROJECT_ROOT, "user_config.yml")


def _load_user_config() -> dict:
    """Load user configuration from YAML file."""
    if os.path.exists(_USER_CONFIG_FILE):
        try:
            with open(_USER_CONFIG_FILE, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    return {}


# Load user config
_user_config = _load_user_config()

# =============================================================================
# OIM PREREQUISITE VARIABLES
# =============================================================================
# Values are loaded from user_config.yml, with defaults as fallback.
# =============================================================================

OIM_PREREQ_VARS = {
    # -------------------------------------------------------------------------
    # Execution Control
    # -------------------------------------------------------------------------
    "skip_on_failure": _user_config.get("skip_on_failure", True),
    
    # -------------------------------------------------------------------------
    # Target OIM Server (Remote Execution)
    # -------------------------------------------------------------------------
    "oim_server_ip": _user_config.get("oim_server_ip", ""),
    "oim_ssh_user": _user_config.get("oim_ssh_user", "root"),
    "oim_ssh_password": _user_config.get("oim_ssh_password", ""),
    "oim_ssh_port": _user_config.get("oim_ssh_port", 22),
    
    # -------------------------------------------------------------------------
    # OS Validation (from user_config.yml)
    # -------------------------------------------------------------------------
    "required_os": _user_config.get("required_os", "rhel"),
    "required_os_version": _user_config.get("required_os_version", "10"),
    "required_kernel_version": _user_config.get("required_kernel_version", ""),
    
    # -------------------------------------------------------------------------
    # Network Interfaces (from user_config.yml)
    # -------------------------------------------------------------------------
    "pxe_interface": _user_config.get("pxe_interface", ""),
    "pxe_ip": _user_config.get("pxe_ip", "") or "172.16.107.254/24",  # Default if not set
    "force_configure_pxe": _user_config.get("force_configure_pxe", False),
    "public_interface": _user_config.get("public_interface", ""),
    
    # -------------------------------------------------------------------------
    # NFS Configuration (from user_config.yml)
    # -------------------------------------------------------------------------
    "nfs_server": _user_config.get("nfs_server_ip", ""),
    "nfs_share_path": _user_config.get("nfs_share_path", ""),
    "nfs_min_capacity_gb": _user_config.get("nfs_min_capacity_gb", 100),
    
    # -------------------------------------------------------------------------
    # Podman Configuration (from user_config.yml)
    # -------------------------------------------------------------------------
    "podman_min_version": _user_config.get("podman_min_version", "4.0.0"),
    
    # -------------------------------------------------------------------------
    # Omnia Artifactory Repository (from user_config.yml, with defaults in source code)
    # -------------------------------------------------------------------------
    "omnia_repo_url": _user_config.get("omnia_repo_url", "") or "https://github.com/dell/omnia-artifactory.git",
    "artifactory_branch": _user_config.get("artifactory_branch", "") or "omnia-container",
    "omnia_clone_path": _user_config.get("omnia_clone_path", "") or "/opt/omnia-artifactory",
    
    # -------------------------------------------------------------------------
    # Container Build Configuration (from user_config.yml)
    # -------------------------------------------------------------------------
    "reconfigure_images": _user_config.get("reconfigure_images", False),
    "container_images": _user_config.get("container_images", "") or "core",
    "omnia_branch": _user_config.get("omnia_branch", ""),  # Required if reconfigure_images is true
    
    # -------------------------------------------------------------------------
    # Hardware Requirements (from user_config.yml)
    # -------------------------------------------------------------------------
    "min_cores": _user_config.get("min_cores", 4),
    "min_memory_gb": _user_config.get("min_memory_gb", 16),
    "min_disk_gb": _user_config.get("min_disk_gb", 100),
    
    # -------------------------------------------------------------------------
    # Internet Check (fixed defaults)
    # -------------------------------------------------------------------------
    "internet_check_host": "8.8.8.8",
    "internet_timeout": 10,
    
    # -------------------------------------------------------------------------
    # IPMI (fixed defaults)
    # -------------------------------------------------------------------------
    "ipmi_tool": "ipmitool",
    "ipmi_package": "ipmitool",
    
    # -------------------------------------------------------------------------
    # Git (fixed defaults)
    # -------------------------------------------------------------------------
    "git_package": "git",
    
    # -------------------------------------------------------------------------
    # Timeouts (fixed defaults)
    # -------------------------------------------------------------------------
    "command_timeout": 30,
}
