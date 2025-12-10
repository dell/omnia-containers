"""
Omnia.sh Test - Configuration Variables.

This module loads USER INPUTS from:
  - omnia_sh_config.yml: User inputs for omnia.sh (share_option, password, etc.)
  - user_config.yml: NFS server IP and share path only

All other values use omnia.sh script defaults - no overrides.

Usage:
    from automation_library.vars.omnia_sh_vars import OMNIA_SH_VARS

Author: Dell Technologies
"""

import os
from typing import Dict, Any

import yaml

from .oim_prereq_vars import OIM_PREREQ_VARS, USER_CONFIG_PATH


# =============================================================================
# Configuration File Paths
# =============================================================================

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_OMNIA_SH_CONFIG_FILE = os.path.join(_PROJECT_ROOT, "omnia_sh_config.yml")

OMNIA_SH_CONFIG_PATH = _OMNIA_SH_CONFIG_FILE


# =============================================================================
# Configuration Loader
# =============================================================================

def _load_omnia_sh_config() -> Dict[str, Any]:
    """Load user inputs from omnia_sh_config.yml."""
    if os.path.exists(_OMNIA_SH_CONFIG_FILE):
        try:
            with open(_OMNIA_SH_CONFIG_FILE, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    return {}


_omnia_sh_config = _load_omnia_sh_config()


# =============================================================================
# OMNIA.SH VARIABLES
# =============================================================================
#
# USER INPUTS (from config files):
#   - nfs_server_ip, nfs_share_path: from user_config.yml
#   - share_option, nfs_type, omnia_shared_path, omnia_core_password: from omnia_sh_config.yml
#
# SCRIPT DEFAULTS (hardcoded - same as omnia.sh uses):
#   - container_name, ssh_port, container_image_tag
#
# =============================================================================

OMNIA_SH_VARS: Dict[str, Any] = {
    
    # =========================================================================
    # USER INPUTS - from user_config.yml
    # =========================================================================
    
    "nfs_server_ip": OIM_PREREQ_VARS.get("nfs_server", ""),
    "nfs_share_path": OIM_PREREQ_VARS.get("nfs_share_path", ""),
    "omnia_clone_path": OIM_PREREQ_VARS.get("omnia_clone_path", "/opt/omnia-artifactory"),
    
    # =========================================================================
    # USER INPUTS - from omnia_sh_config.yml
    # =========================================================================
    
    "share_option": _omnia_sh_config.get("share_option", ""),
    "nfs_type": _omnia_sh_config.get("nfs_type", ""),
    "omnia_shared_path": _omnia_sh_config.get("omnia_shared_path", ""),
    "omnia_core_password": _omnia_sh_config.get("omnia_core_password", ""),
    
    # =========================================================================
    # SCRIPT DEFAULTS - same as omnia.sh (DO NOT OVERRIDE)
    # =========================================================================
    
    "container_name": "omnia_core",      # Hardcoded in omnia.sh
    "ssh_port": 2222,                     # Hardcoded in omnia.sh
    "container_image_tag": "1.0",         # Hardcoded in omnia.sh
    
    # =========================================================================
    # TEST TIMEOUTS (internal use only)
    # =========================================================================
    
    "command_timeout": 30,
    "install_timeout": 600,
    "container_start_timeout": 60,
}


def get_omnia_sh_path() -> str:
    """
    Get the path to omnia.sh script.
    
    Returns:
        Absolute path to omnia.sh
    """
    return os.path.join(OMNIA_SH_VARS["omnia_clone_path"], "omnia.sh")


def validate_config() -> Dict[str, Any]:
    """
    Validate user inputs for omnia.sh execution.
    
    Returns:
        Dict with 'valid' (bool) and 'errors' (list of error messages)
    """
    errors = []
    
    # Check omnia_sh_config.yml exists
    if not os.path.exists(_OMNIA_SH_CONFIG_FILE):
        errors.append(f"omnia_sh_config.yml not found at {_OMNIA_SH_CONFIG_FILE}")
        return {"valid": False, "errors": errors}
    
    # Check required user inputs from omnia_sh_config.yml
    if not OMNIA_SH_VARS["share_option"]:
        errors.append(f"share_option not set in {OMNIA_SH_CONFIG_PATH}")
    
    if not OMNIA_SH_VARS["omnia_shared_path"]:
        errors.append(f"omnia_shared_path not set in {OMNIA_SH_CONFIG_PATH}")
    
    if not OMNIA_SH_VARS["omnia_core_password"]:
        errors.append(f"omnia_core_password not set in {OMNIA_SH_CONFIG_PATH}")
    
    # Check NFS inputs from user_config.yml (only if NFS selected)
    if OMNIA_SH_VARS["share_option"] == "NFS":
        if not OMNIA_SH_VARS["nfs_type"]:
            errors.append(f"nfs_type not set in {OMNIA_SH_CONFIG_PATH}")
        if not OMNIA_SH_VARS["nfs_server_ip"]:
            errors.append(f"nfs_server_ip not set in {USER_CONFIG_PATH}")
        if not OMNIA_SH_VARS["nfs_share_path"]:
            errors.append(f"nfs_share_path not set in {USER_CONFIG_PATH}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
