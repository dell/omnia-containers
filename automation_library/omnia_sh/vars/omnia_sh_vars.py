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
Omnia.sh Test - Configuration Variables.

This module loads configuration variables for omnia.sh verification tests.
- Non-sensitive settings come from omnia_test_config.yml
- Sensitive credentials (omnia_core_password) come from omnia_test_credentials.yml

Usage:
    from automation_library.omnia_sh.vars.omnia_sh_vars import OMNIA_SH_VARS, TEST_VARS

"""

from typing import Dict, Any

from ...checks.vars.oim_prereq_vars import _omnia_test_config, _omnia_test_credentials
from ...core import (
    OIM_METADATA_PATH as _CORE_OIM_METADATA_PATH,
    OMNIA_CORE_CONTAINER as _CORE_CONTAINER,
    OMNIA_GIT_RAW_BASE_URL as _GIT_RAW_BASE,
)


# =============================================================================
# OMNIA.SH VARIABLES
# - Config values from omnia_test_config.yml
# - Credentials from omnia_test_credentials.yml
# =============================================================================

# OIM server config
_oim_server_ip = _omnia_test_config.get("oim_server_ip", "")

# NFS configuration (from config)
_share_option = _omnia_test_config.get("share_option", "")
_nfs_type = _omnia_test_config.get("nfs_type", "")
_nfs_server_ip = _omnia_test_config.get("nfs_server_ip", "")
_nfs_share_path = _omnia_test_config.get("nfs_share_path", "")
_omnia_shared_path = _omnia_test_config.get("omnia_shared_path", "")
_omnia_clone_path = _omnia_test_config.get("omnia_clone_path", "")

# Credentials (from credentials file)
_omnia_core_password = _omnia_test_credentials.get("omnia_core_password", "")

# Repository URLs for omnia.sh download
# omnia_branch is for omnia repo (where omnia.sh lives)
# core_tag is for versioned downloads
_omnia_branch = _omnia_test_config.get("omnia_branch", "")
_core_tag = _omnia_test_config.get("core_tag", "")

OMNIA_SH_VARS: Dict[str, Any] = {
    # Container config (hardcoded - same as omnia.sh)
    "container_name": _CORE_CONTAINER,
    "ssh_port": 2222,
    # OIM server
    "oim_server_ip": _oim_server_ip,
    # NFS config from omnia_test_config.yml
    "share_option": _share_option,
    "nfs_type": _nfs_type,
    "nfs_server_ip": _nfs_server_ip,
    "nfs_share_path": _nfs_share_path,
    "omnia_shared_path": _omnia_shared_path,
    "omnia_core_password": _omnia_core_password,
    "omnia_clone_path": _omnia_clone_path,
    # Download URLs for omnia.sh (omnia repo, not omnia-artifactory)
    "omnia_sh_branch_url": f"{_GIT_RAW_BASE}/refs/heads/{_omnia_branch}/omnia.sh" if _omnia_branch else "",
    "omnia_sh_tag_url": f"{_GIT_RAW_BASE}/refs/tags/{_core_tag}/omnia.sh" if _core_tag else "",
    "omnia_sh_path": f"{_omnia_clone_path}/omnia.sh" if _omnia_clone_path else "",
    # Timeout and polling intervals for install/uninstall operations
    "install_timeout": 600,       # 10 minutes for install
    "uninstall_timeout": 300,     # 5 minutes for uninstall
    "poll_interval": 10,          # 10 seconds progress poll interval
}


# =============================================================================
# TEST VARIABLES (for molecule/pytest tests)
# =============================================================================

TEST_VARS: Dict[str, Any] = {
    # Container verification
    "container_name": _CORE_CONTAINER,
    "container_file": f"/etc/containers/systemd/{_CORE_CONTAINER}.container",
    "service_name": f"{_CORE_CONTAINER}.service",
    "metadata_file": _CORE_OIM_METADATA_PATH,
    "ssh_alias": _CORE_CONTAINER,
    "ssh_timeout": 5,
    # From omnia_test_config.yml
    "oim_server_ip": _oim_server_ip,
    "share_option": _share_option,
    "nfs_type": _nfs_type,
    "nfs_server_ip": _nfs_server_ip,
    "nfs_share_path": _nfs_share_path,
    "omnia_shared_path": _omnia_shared_path,
    "omnia_core_password": _omnia_core_password,
}
