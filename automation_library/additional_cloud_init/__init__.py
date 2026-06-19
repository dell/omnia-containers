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
Additional Cloud-Init Module

This module provides functions for additional cloud-init configuration verification.
Uses core module utilities for SSH, PXE mapping, and config reading.

Test Categories:
- Configuration: File validation, YAML parsing, prohibited key checks
- SMD Groups: Common and per-FG group creation, idempotency
- Templates: Cloud-init rendering with merge_how behavior
- BSS Integration: Group registration and boot management
- End-to-End: Full provisioning with write_files and runcmd
"""

from .functions import (
    # Common functions
    get_functional_groups_from_config,
    load_additional_cloud_init_config,
    skip_if_additional_cloud_init_disabled,
    # Validation functions
    validate_cloud_init_config,
    validate_functional_groups,
    check_prohibited_keys,
    validate_write_files,
    validate_runcmd,
    # SMD functions
    verify_smd_group_creation,
    verify_smd_group_deletion,
    verify_bss_group_registration,
    # Node verification functions
    verify_cloud_init_files_on_nodes,
    verify_runcmd_execution_on_nodes,
    verify_additional_cloud_init_integration,
)
from .vars import (
    ADDITIONAL_CLOUD_INIT_CONFIG_PATH,
    ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
    ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL,
    PROHIBITED_CLOUD_INIT_KEYS,
    ALLOWED_CLOUD_INIT_KEYS,
    SMD_GROUP_PREFIX,
    COMMON_SMD_GROUP_NAME,
)
from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)
