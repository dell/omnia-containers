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
OIM Prerequisite Check - Configuration Variables.

This module loads user configuration from omnia_test_config.yml and provides
sensible defaults for all prerequisite check parameters.

Usage:
    from automation_library.vars.oim_prereq_vars import OIM_PREREQ_VARS, OMNIA_TEST_CONFIG_PATH

    # Access a variable
    server_ip = OIM_PREREQ_VARS["oim_server_ip"]

Note:
    - Users should edit omnia_test_config.yml, NOT this file
    - All values can be overridden via omnia_test_config.yml
    - Default values are used when omnia_test_config.yml doesn't specify a value

Author: Dell Technologies
"""

import os
from typing import Dict, Any

import yaml

from automation_library.core.vars import OIM_SHARED_PATH as _CORE_OIM_SHARED_PATH


# =============================================================================
# Configuration File Path
# =============================================================================

# Path to user config file (in project root, next to requirements.txt)
# automation_library/checks/vars/oim_prereq_vars.py -> go up 4 levels to project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
_OMNIA_TEST_CONFIG_FILE = os.path.join(_PROJECT_ROOT, "omnia_test_config.yml")

# Export config path for use in error messages
OMNIA_TEST_CONFIG_PATH = _OMNIA_TEST_CONFIG_FILE


# =============================================================================
# Configuration Loader
# =============================================================================

def _load_omnia_test_config() -> Dict[str, Any]:
    """
    Load user configuration from YAML file with error handling and validation.

    Returns:
        Dict containing user configuration, or empty dict if file not found/invalid.

    Note:
        Silently returns empty dict on errors to allow defaults to be used.
    """
    if os.path.exists(_OMNIA_TEST_CONFIG_FILE):
        try:
            with open(_OMNIA_TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (IOError, yaml.YAMLError):
            return {}
    return {}


# Load user config once at module import
_omnia_test_config = _load_omnia_test_config()


# =============================================================================
# OIM PREREQUISITE VARIABLES
# =============================================================================
#
# This dictionary contains all configuration variables for prerequisite checks.
# Values are loaded from omnia_test_config.yml with defaults as fallback.
#
# Variable Naming Convention:
#   - Keys match the YAML keys in omnia_test_config.yml where applicable
#   - Defaults are provided for optional values
#   - Empty string ("") indicates required user input
#
# =============================================================================

OIM_PREREQ_VARS: Dict[str, Any] = {

    # =========================================================================
    # EXECUTION CONTROL
    # =========================================================================
    # Controls how the tool behaves when a check fails

    # skip_on_failure: If True, continue running checks even if one fails
    #                  If False, stop immediately on first failure
    "skip_on_failure": _omnia_test_config.get("skip_on_failure", True),

    # =========================================================================
    # TARGET OIM SERVER (Remote Execution)
    # =========================================================================
    # SSH connection details for the remote OIM server where checks are run

    # oim_server_ip: IP address of the target OIM server (REQUIRED)
    "oim_server_ip": _omnia_test_config.get("oim_server_ip", ""),

    # oim_ssh_user: SSH username for remote connection
    "oim_ssh_user": _omnia_test_config.get("oim_ssh_user", "root"),

    # oim_ssh_password: SSH password for remote connection (REQUIRED)
    "oim_ssh_password": _omnia_test_config.get("oim_ssh_password", ""),

    # oim_ssh_port: SSH port number
    "oim_ssh_port": _omnia_test_config.get("oim_ssh_port", 22),

    # =========================================================================
    # HOSTNAME CONFIGURATION (FIRST TASK)
    # =========================================================================
    # Hostname to set on the OIM server (must include domain)

    # oim_hostname: FQDN to set (e.g., "oim.omnia.test")
    "oim_hostname": _omnia_test_config.get("oim_hostname", ""),

    # =========================================================================
    # OS VALIDATION
    # =========================================================================
    # Requirements for the operating system on the target server

    # required_os: Expected OS name (e.g., "rhel", "centos", "rocky")
    "required_os": _omnia_test_config.get("required_os", "rhel"),

    # required_os_version: Expected OS version (e.g., "10", "9.3")
    "required_os_version": _omnia_test_config.get("required_os_version", "10"),

    # required_kernel_version: Expected kernel version (empty = skip check)
    "required_kernel_version": _omnia_test_config.get("required_kernel_version", ""),

    # =========================================================================
    # NETWORK INTERFACES
    # =========================================================================
    # Network interface configuration for PXE and public networks

    # network_type: Network configuration type ("dedicated" or "lom")
    "network_type": _omnia_test_config.get("network_type", "dedicated"),

    # pxe_interface: Name of the PXE/provisioning network interface (e.g., "eno1")
    "pxe_interface": _omnia_test_config.get("pxe_interface", ""),

    # pxe_ip: IP address to assign to PXE interface (CIDR notation)
    "pxe_ip": _omnia_test_config.get("pxe_ip", "") or "172.16.107.254/24",

    # idrac_ip: IP address for iDRAC (only used when network_type is "lom")
    "idrac_ip": _omnia_test_config.get("idrac_ip", "") or "172.16.107.253/24",

    # force_configure_pxe: If True, reconfigure PXE IP even if already set
    "force_configure_pxe": _omnia_test_config.get("force_configure_pxe", False),

    # public_interface: Name of the public/internet-facing interface (e.g., "eno2")
    "public_interface": _omnia_test_config.get("public_interface", ""),

    # =========================================================================
    # NFS CONFIGURATION
    # =========================================================================
    # NFS server details for shared storage

    # nfs_server: IP address of the NFS server
    "nfs_server": _omnia_test_config.get("nfs_server_ip", ""),

    # nfs_share_path: NFS export path (e.g., "/mnt/share")
    "nfs_share_path": _omnia_test_config.get("nfs_share_path", ""),

    # nfs_min_capacity_gb: Minimum required NFS capacity in GB
    "nfs_min_capacity_gb": _omnia_test_config.get("nfs_min_capacity_gb", 100),

    # =========================================================================
    # OMNIA.SH INSTALLATION
    # =========================================================================
    # Settings for omnia.sh --install command

    # share_option: Storage option ("NFS" or "Local")
    "share_option": _omnia_test_config.get("share_option", "NFS"),

    # nfs_type: NFS type ("external" or "internal")
    "nfs_type": _omnia_test_config.get("nfs_type", "external"),

    # omnia_shared_path: Local path for omnia data storage
    "omnia_shared_path": _omnia_test_config.get("omnia_shared_path", _CORE_OIM_SHARED_PATH),

    # omnia_core_password: Root password for omnia_core container SSH
    "omnia_core_password": _omnia_test_config.get("omnia_core_password", ""),

    # =========================================================================
    # PODMAN CONFIGURATION
    # =========================================================================
    # Container runtime requirements

    # podman_min_version: Minimum required Podman version (e.g., "4.0.0")
    "podman_min_version": _omnia_test_config.get("podman_min_version", "4.0.0"),

    # =========================================================================
    # OMNIA ARTIFACTORY REPOSITORY
    # =========================================================================
    # Git repository settings for cloning Omnia Artifactory

    # omnia_repo_url: Git URL for Omnia Artifactory repository
    "omnia_repo_url": (
        _omnia_test_config.get("omnia_repo_url", "") or
        "https://github.com/dell/omnia-artifactory.git"
    ),

    # artifactory_branch: Branch to clone from Omnia Artifactory repo
    "artifactory_branch": _omnia_test_config.get("artifactory_branch", "") or "omnia-container",

    # omnia_clone_path: Local path where repository will be cloned
    "omnia_clone_path": _omnia_test_config.get("omnia_clone_path", "") or "/opt/omnia-artifactory",

    # =========================================================================
    # CONTAINER BUILD CONFIGURATION
    # =========================================================================
    # Settings for building container images

    # reconfigure_images: If True, clone repo and build container images
    #                     If False, skip git clone and container build
    "reconfigure_images": _omnia_test_config.get("reconfigure_images", False),

    # core_tag: Core image version tag
    # Usage: ./build_images.sh core core_tag=1.1 omnia_branch=pub/q1_dev
    "core_tag": _omnia_test_config.get("core_tag", ""),

    # omnia_branch: Omnia branch/tag for core image build
    # Will build the core container with the below omnia branch/tag code
    # Can be a branch (e.g., "main", "pub/q1_dev") or a tag (e.g., "v1.6.0")
    "omnia_branch": _omnia_test_config.get("omnia_branch", ""),

    # =========================================================================
    # HARDWARE REQUIREMENTS
    # =========================================================================
    # Minimum hardware specifications for the target server

    # min_cores: Minimum number of CPU cores required
    "min_cores": _omnia_test_config.get("min_cores", 4),

    # min_memory_gb: Minimum RAM required in GB
    "min_memory_gb": _omnia_test_config.get("min_memory_gb", 16),

    # min_disk_gb: Minimum disk space required in GB
    "min_disk_gb": _omnia_test_config.get("min_disk_gb", 100),

    # =========================================================================
    # INTERNET CONNECTIVITY (Fixed Defaults)
    # =========================================================================
    # Settings for internet connectivity check - not user configurable

    # internet_check_host: Host to ping for internet connectivity test
    "internet_check_host": "8.8.8.8",

    # internet_timeout: Timeout in seconds for ping test
    "internet_timeout": 10,

    # =========================================================================
    # IPMI TOOL (Fixed Defaults)
    # =========================================================================
    # IPMI tool settings - not user configurable

    # ipmi_tool: Command name for IPMI tool
    "ipmi_tool": "ipmitool",

    # ipmi_package: Package name to install if IPMI tool is missing
    "ipmi_package": "ipmitool",

    # =========================================================================
    # GIT (Fixed Defaults)
    # =========================================================================
    # Git settings - not user configurable

    # git_package: Package name to install if Git is missing
    "git_package": "git",

    # =========================================================================
    # TIMEOUTS (Fixed Defaults)
    # =========================================================================
    # Command execution timeouts - not user configurable

    # command_timeout: Default timeout in seconds for shell commands
    "command_timeout": 30,

    # =========================================================================
    # BUILD STREAM JOB OVERRIDE
    # =========================================================================
    # Optional: pin a specific build_stream job UUID to verify.
    # When empty (""), the automation uses the latest COMPLETED job from postgres.
    "build_stream_job_id": _omnia_test_config.get("build_stream_job_id", ""),
}
