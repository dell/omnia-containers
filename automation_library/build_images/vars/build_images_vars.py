"""
Build Image x86_64 - Configuration Variables.

This module loads all configuration for build_image_x86_64 automation.
Reads from user_config.yml and validates S3, registry, and image settings.

Usage:
    from automation_library.build_images.vars.build_images_vars import BUILD_IMAGE_VARS

Author: Dell Technologies
"""

import os
from typing import Dict, Any, List

from automation_library.checks.vars.oim_prereq_vars import OIM_PREREQ_VARS


def _get_project_root() -> str:
    """Get the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# =============================================================================
# S3 CONTAINER DEFINITIONS
# =============================================================================

# S3 containers required for build_image_x86_64
S3_CONTAINERS: List[str] = [
    "minio-server",
]

# Registry container for regctl
REGISTRY_CONTAINER: str = "registry"


# =============================================================================
# IMAGE TYPES
# =============================================================================

# Image types that should be built for each functional group
IMAGE_TYPES: List[str] = [
    "base",
    "compute",
    "initrd",
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
    "s3_containers": S3_CONTAINERS,
    "registry_container": REGISTRY_CONTAINER,

    # =========================================================================
    # PATHS
    # =========================================================================
    "omnia_shared_path": OIM_PREREQ_VARS.get("omnia_shared_path", "/opt/omnia"),
    "build_image_playbook": "/omnia/build_image_x86_64/build_image_x86_64.yml",
    "functional_group_path": "/opt/omnia/input/project_default/functional_group.yml",
    "pxe_mapping_path": "/opt/omnia/input/project_default/pxe_mapping_file.csv",

    # =========================================================================
    # S3 SETTINGS
    # =========================================================================
    "s3_bucket": "boot-images",
    "s3_cmd": "s3cmd",

    # =========================================================================
    # REGISTRY SETTINGS
    # =========================================================================
    "regctl_cmd": "regctl",
    "registry_url": "localhost:5000",

    # =========================================================================
    # IMAGE SETTINGS
    # =========================================================================
    "image_types": IMAGE_TYPES,

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


def get_s3_containers() -> List[str]:
    """
    Get list of S3-related containers.

    Returns:
        List of container names
    """
    return S3_CONTAINERS.copy()


def get_image_types() -> List[str]:
    """
    Get list of image types to validate.

    Returns:
        List of image type names
    """
    return IMAGE_TYPES.copy()


def get_functional_group_path() -> str:
    """Get the path to functional_group.yml on OIM server."""
    return BUILD_IMAGE_VARS["functional_group_path"]


def get_pxe_mapping_path() -> str:
    """Get the path to pxe_mapping.csv on OIM server."""
    return BUILD_IMAGE_VARS["pxe_mapping_path"]
