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
Omnia.sh Test - Configuration Variables.

This module loads all configuration from user_config.yml.
All omnia.sh related settings are now in user_config.yml (section 13).

Usage:
    from automation_library.omnia_sh.vars.omnia_sh_vars import OMNIA_SH_VARS

Author: Dell Technologies
"""

import os
from typing import Dict, Any

from ...checks.vars.oim_prereq_vars import OIM_PREREQ_VARS, USER_CONFIG_PATH


# =============================================================================
# OMNIA.SH VARIABLES
# =============================================================================
# All configuration now comes from user_config.yml
# =============================================================================

OMNIA_SH_VARS: Dict[str, Any] = {

    # =========================================================================
    # USER INPUTS - all from user_config.yml
    # =========================================================================

    # NFS settings (section 6)
    "nfs_server_ip": OIM_PREREQ_VARS.get("nfs_server_ip", ""),
    "nfs_share_path": OIM_PREREQ_VARS.get("nfs_share_path", ""),

    # Clone path (section 11)
    "omnia_clone_path": OIM_PREREQ_VARS.get("omnia_clone_path", "/opt/omnia-artifactory"),

    # Omnia.sh install settings (section 13)
    "share_option": OIM_PREREQ_VARS.get("share_option", "NFS"),
    "nfs_type": OIM_PREREQ_VARS.get("nfs_type", "external"),
    "omnia_shared_path": OIM_PREREQ_VARS.get("omnia_shared_path", "/opt/omnia"),
    "omnia_core_password": OIM_PREREQ_VARS.get("omnia_core_password", ""),

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

    # Check user_config.yml exists
    if not os.path.exists(USER_CONFIG_PATH):
        errors.append(f"user_config.yml not found at {USER_CONFIG_PATH}")
        return {"valid": False, "errors": errors}

    # Check required user inputs
    if not OMNIA_SH_VARS["share_option"]:
        errors.append(f"share_option not set in {USER_CONFIG_PATH}")

    if not OMNIA_SH_VARS["omnia_shared_path"]:
        errors.append(f"omnia_shared_path not set in {USER_CONFIG_PATH}")

    if not OMNIA_SH_VARS["omnia_core_password"]:
        errors.append(f"omnia_core_password not set in {USER_CONFIG_PATH}")

    # Check NFS inputs (only if NFS selected)
    if OMNIA_SH_VARS["share_option"] == "NFS":
        if not OMNIA_SH_VARS["nfs_type"]:
            errors.append(f"nfs_type not set in {USER_CONFIG_PATH}")
        if not OMNIA_SH_VARS["nfs_server_ip"]:
            errors.append(f"nfs_server_ip not set in {USER_CONFIG_PATH}")
        if not OMNIA_SH_VARS["nfs_share_path"]:
            errors.append(f"nfs_share_path not set in {USER_CONFIG_PATH}")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
