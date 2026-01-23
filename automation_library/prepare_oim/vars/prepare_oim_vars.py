# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Prepare OIM - Configuration Variables.

This module loads all configuration for prepare_oim automation.
Reads from user_config.yml and input/software_config.json.

Usage:
    from automation_library.vars.prepare_oim_vars import PREPARE_OIM_VARS

"""

import json
import os
from typing import Dict, Any, List

from automation_library.checks.vars.oim_prereq_vars import OIM_PREREQ_VARS


def _get_project_root() -> str:
    """Get the project root directory."""
    # File is at automation_library/prepare_oim/vars/prepare_oim_vars.py
    # Need to go up 4 levels: vars -> prepare_oim -> automation_library -> project_root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _load_software_config() -> Dict[str, Any]:
    """Load software_config.json from project_default directory."""
    config_path = os.path.join(_get_project_root(), "project_default", "software_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _has_ldap_in_software_config() -> bool:
    """Check if openldap is present in software_config.json."""
    config = _load_software_config()
    softwares = config.get("softwares", [])
    for software in softwares:
        if isinstance(software, dict):
            name = software.get("name", "").lower()
            if "openldap" in name or "ldap" in name:
                return True
        elif isinstance(software, str):
            if "openldap" in software.lower() or "ldap" in software.lower():
                return True
    return False


# =============================================================================
# CONTAINER DEFINITIONS
# =============================================================================

# OpenChami containers (deployed by prepare_oim)
OPENCHAMI_CONTAINERS: List[str] = [
    "pulp",
    "minio-server",
    "registry",
    "step-ca",
    "postgres",
    "hydra",
    "smd",
    "opaal-idp",
    "bss",
    "opaal",
    "cloud-init-server",
    "haproxy",
    "coresmd",
]

# Core container (prerequisite - deployed by omnia.sh --install)
CORE_CONTAINERS: List[str] = [
    "omnia_core",
]

# Auth container (only required when LDAP is in software_config.json)
AUTH_CONTAINER: str = "omnia_auth"

# Pulp container (for local repo management)
PULP_CONTAINER: str = "pulp"


# =============================================================================
# PREPARE OIM VARIABLES
# =============================================================================

PREPARE_OIM_VARS: Dict[str, Any] = {

    # =========================================================================
    # CONNECTION SETTINGS (from user_config.yml)
    # =========================================================================
    "oim_server_ip": OIM_PREREQ_VARS.get("oim_server_ip", ""),
    "oim_ssh_user": OIM_PREREQ_VARS.get("oim_ssh_user", "root"),
    "oim_ssh_password": OIM_PREREQ_VARS.get("oim_ssh_password", ""),
    "oim_ssh_port": OIM_PREREQ_VARS.get("oim_ssh_port", 22),

    # =========================================================================
    # CONTAINER SETTINGS
    # =========================================================================
    "container_name": "omnia_core",
    "ssh_alias": "omnia_core",
    "ssh_port": 2222,

    # =========================================================================
    # PATHS
    # =========================================================================
    "omnia_shared_path": OIM_PREREQ_VARS.get("omnia_shared_path", "/opt/omnia"),
    "prepare_oim_playbook": "/omnia/prepare_oim/prepare_oim.yml",
    "input_dir": os.path.join(_get_project_root(), "input"),
    "container_input_dir": "/omnia/input",

    # =========================================================================
    # LDAP CONFIGURATION
    # =========================================================================
    "ldap_enabled": _has_ldap_in_software_config(),

    # =========================================================================
    # CONTAINER LISTS
    # =========================================================================
    "openchami_containers": OPENCHAMI_CONTAINERS,
    "core_containers": CORE_CONTAINERS,
    "auth_container": AUTH_CONTAINER,

    # =========================================================================
    # SERVICE SETTINGS
    # =========================================================================
    "omnia_target": "omnia.target",
    "openchami_target": "openchami.target",

    # =========================================================================
    # CERTIFICATE PATHS
    # =========================================================================
    "pulp_cert_path": "/opt/omnia/pulp/settings/certs/pulp_webserver.crt",
    "ldap_cert_path": "/opt/omnia/auth/tls_certs/ldapserver.crt",

    # =========================================================================
    # TIMEOUTS
    # =========================================================================
    "command_timeout": 30,
    "playbook_timeout": 1800,  # 30 minutes for prepare_oim playbook
    "container_check_timeout": 10,

    # =========================================================================
    # EXECUTION CONTROL
    # =========================================================================
    "skip_on_failure": OIM_PREREQ_VARS.get("skip_on_failure", False),
}


def get_all_required_containers() -> List[str]:
    """
    Get list of all containers that should be running.
    Includes auth container only if LDAP is enabled.

    Returns:
        List of container names
    """
    containers = CORE_CONTAINERS.copy() + OPENCHAMI_CONTAINERS.copy()
    if _has_ldap_in_software_config():
        containers.append(AUTH_CONTAINER)
    return containers


def get_software_config_path() -> str:
    """Get the path to software_config.json."""
    return os.path.join(_get_project_root(), "input", "software_config.json")


def is_ldap_enabled() -> bool:
    """Check if LDAP is enabled in software_config.json."""
    return _has_ldap_in_software_config()


def reload_ldap_status() -> bool:
    """Reload LDAP status from software_config.json (for runtime checks)."""
    return _has_ldap_in_software_config()
