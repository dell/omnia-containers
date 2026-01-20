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
Build Image - Configuration Variables.

This module loads all configuration for build_image automation.
Reads from user_config.yml and project_default/pxe_mapping_file.csv.

Usage:
    from automation_library.build_image.vars.build_image_vars import BUILD_IMAGE_VARS

Author: Dell Technologies
"""

import csv
import os
from typing import Dict, Any, List, Set

from automation_library.checks.vars.oim_prereq_vars import OIM_PREREQ_VARS


def _get_project_root() -> str:
    """Get the project root directory."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def _load_pxe_mapping() -> List[Dict[str, str]]:
    """Load pxe_mapping_file.csv from project_default directory."""
    config_path = os.path.join(_get_project_root(), "project_default", "pxe_mapping_file.csv")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except (IOError, csv.Error):
            pass
    return []


def _get_functional_groups() -> Set[str]:
    """Extract unique functional group names from pxe_mapping_file.csv."""
    rows = _load_pxe_mapping()
    groups = set()
    for row in rows:
        fg_name = row.get("FUNCTIONAL_GROUP_NAME", "").strip()
        if fg_name:
            groups.add(fg_name)
    return groups


def _get_group_names() -> Set[str]:
    """Extract unique group names from pxe_mapping_file.csv."""
    rows = _load_pxe_mapping()
    groups = set()
    for row in rows:
        grp_name = row.get("GROUP_NAME", "").strip()
        if grp_name:
            groups.add(grp_name)
    return groups


# =============================================================================
# S3 CONTAINER DEFINITIONS
# =============================================================================

S3_CONTAINERS: List[str] = [
    "minio-server",
]


# =============================================================================
# BUILD IMAGE VARIABLES
# =============================================================================

BUILD_IMAGE_VARS: Dict[str, Any] = {

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
    "build_image_playbook": "/omnia/build_image_x86_64/build_image_x86_64.yml",
    "functional_group_file_path": "/opt/omnia/.data/functional_groups_config.yml",
    "pxe_mapping_file": "pxe_mapping_file.csv",

    # =========================================================================
    # S3 COMMANDS
    # =========================================================================
    "s3_list_images_cmd": "s3cmd ls -Hr s3://boot-images",
    "s3_bucket_name": "boot-images",

    # =========================================================================
    # IMAGE TYPES (3 images per functional group)
    # Actual S3 naming: initramfs-*.img, vmlinuz-*, rhel10.0-* (rootfs)
    # =========================================================================
    "image_types": ["initramfs", "vmlinuz", "rhel"],

    # =========================================================================
    # CONTAINER LISTS
    # =========================================================================
    "s3_containers": S3_CONTAINERS,

    # =========================================================================
    # TIMEOUTS
    # =========================================================================
    "command_timeout": 60,
    "playbook_timeout": 3600,  # 60 minutes for build_image playbook
    "container_check_timeout": 10,

    # =========================================================================
    # EXECUTION CONTROL
    # =========================================================================
    "skip_on_failure": OIM_PREREQ_VARS.get("skip_on_failure", False),
}


def get_functional_groups_from_pxe_mapping() -> Set[str]:
    """
    Get unique functional group names from pxe_mapping_file.csv.

    Returns:
        Set of functional group names
    """
    return _get_functional_groups()


def get_group_names_from_pxe_mapping() -> Set[str]:
    """
    Get unique group names from pxe_mapping_file.csv.

    Returns:
        Set of group names
    """
    return _get_group_names()


def get_pxe_mapping_path() -> str:
    """Get the path to pxe_mapping_file.csv."""
    return os.path.join(_get_project_root(), "project_default", "pxe_mapping_file.csv")


def get_pxe_mapping_data() -> List[Dict[str, str]]:
    """
    Get all rows from pxe_mapping_file.csv.

    Returns:
        List of dictionaries representing CSV rows
    """
    return _load_pxe_mapping()
