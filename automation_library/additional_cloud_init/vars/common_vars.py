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
Additional Cloud-Init Module - Common Variables.

Constants and configuration values for additional cloud-init functionality.
"""

from automation_library.core import (
    INPUT_BASE_PATH as _INPUT_BASE_PATH,
)

# =============================================================================
# Path Constants (inside container)
# =============================================================================

ADDITIONAL_CLOUD_INIT_CONFIG_PATH = f"{_INPUT_BASE_PATH}/additional_cloud_init.yml"

# =============================================================================
# Retry Configuration
# =============================================================================

ADDITIONAL_CLOUD_INIT_RETRY_COUNT = 3
ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL = 30

# =============================================================================
# Cloud-Init Validation Constants
# =============================================================================

# Keys that are prohibited in additional cloud-init configuration
# These are platform-managed and must not be overridden by users
PROHIBITED_CLOUD_INIT_KEYS = frozenset({
    "bootcmd",          # Boot-time commands (platform managed)
    "network",          # Network configuration (platform managed)
    "network-config",   # Network configuration (platform managed)
    "packages",         # Package installation (platform managed)
})

# Keys that are allowed in additional cloud-init configuration
ALLOWED_CLOUD_INIT_KEYS = frozenset({
    "write_files",      # Write files to filesystem
    "runcmd",          # Run commands at final stage
})

# =============================================================================
# SMD Group Constants
# =============================================================================

SMD_GROUP_PREFIX = "additional_cloud_init"
COMMON_SMD_GROUP_NAME = "additional_cloud_init"

# =============================================================================
# BSS Cloud-Init Group Constants
# =============================================================================

BSS_CLOUD_INIT_TIMEOUT = 300  # 5 minutes timeout for BSS operations
BSS_CLOUD_INIT_RETRY_COUNT = 3

# =============================================================================
# Template Rendering Constants
# =============================================================================

CLOUD_INIT_TEMPLATE_NAME = "additional_cloud_init"
MERGE_HOW_STRATEGY = "no_replace"  # Platform defaults win, lists append

# =============================================================================
# Node Verification Constants
# =============================================================================

# Default file permissions if not specified
DEFAULT_FILE_PERMISSIONS = "0644"

# Common log file locations for runcmd verification
COMMON_LOG_LOCATIONS = (
    "/var/log/custom_setup.log",
    "/var/log/cloud-init-output.log",
    "/var/log/cloud-init.log",
)

# Cloud-init status check commands
CLOUD_INIT_STATUS_CMD = "cloud-init status"
CLOUD_INIT_STATUS_SUCCESS = "done"
