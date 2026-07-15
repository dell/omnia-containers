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
Upgrade and Rollback Module.

Combined module for Omnia upgrade and rollback workflows.
"""

from .functions import (
    # Common
    compare_versions,
    # Upgrade
    validate_upgrade_versions,
    validate_versions,
    validate_config,
    check_backup_exists,
    check_pre_upgrade_container,
    clone_upgrade_repo,
    build_core_image,
    verify_podman_image,
    download_omnia_sh,
    run_omnia_upgrade,
    verify_backup_directory,
    verify_post_upgrade_state,
    run_prepare_upgrade,
    verify_backup_md5sum,
    # Rollback
    verify_rollback_precondition,
    check_rollback_image,
    download_omnia_sh_for_rollback,
    run_omnia_rollback,
    verify_rollback_container,
    verify_rollback_backup_md5sum,
)
from .functions import (
    check_upgrade_yml_exists,
    run_upgrade_yml,
    verify_upgrade_manifest,
    verify_manifest_component_status,
    check_software_component_enabled,
)
from .vars import (
    UPGRADE_VARS,
    SUPPORTED_VERSIONS,
    VERSION_PROPERTIES,
    get_core_tag_for_version,
    PREPARE_UPGRADE_VARS,
    BACKUP_VERIFY_VARS,
    ROLLBACK_VARS,
    UPGRADE_YML_VARS,
)
from .messages import (
    # Upgrade messages
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
    BACKUP_TEST_NAMES,
    BACKUP_LOG_MSGS,
    BACKUP_ASSERT_MSGS,
    BACKUP_SKIP_MSGS,
    PREPARE_TEST_NAMES,
    PREPARE_LOG_MSGS,
    PREPARE_ASSERT_MSGS,
    PREPARE_SKIP_MSGS,
    # Rollback messages
    ROLLBACK_TEST_NAMES,
    ROLLBACK_LOG_MSGS,
    ROLLBACK_ASSERT_MSGS,
    ROLLBACK_SKIP_MSGS,
    UPGRADE_YML_TEST_NAMES,
    UPGRADE_YML_LOG_MSGS,
    UPGRADE_YML_ASSERT_MSGS,
    UPGRADE_YML_SKIP_MSGS,
)

__all__ = [
    # Common functions
    "compare_versions",
    # Upgrade functions
    "validate_upgrade_versions",
    "validate_versions",
    "validate_config",
    "check_backup_exists",
    "check_pre_upgrade_container",
    "clone_upgrade_repo",
    "build_core_image",
    "verify_podman_image",
    "download_omnia_sh",
    "run_omnia_upgrade",
    "verify_backup_directory",
    "verify_post_upgrade_state",
    "run_prepare_upgrade",
    "verify_backup_md5sum",
    # Rollback functions
    "verify_rollback_precondition",
    "check_rollback_image",
    "download_omnia_sh_for_rollback",
    "run_omnia_rollback",
    "verify_rollback_container",
    "verify_rollback_backup_md5sum",
    # upgrade_yml functions
    "check_upgrade_yml_exists",
    "run_upgrade_yml",
    "verify_upgrade_manifest",
    "verify_manifest_component_status",
    "check_software_component_enabled",
    # Vars
    "UPGRADE_VARS",
    "SUPPORTED_VERSIONS",
    "VERSION_PROPERTIES",
    "get_core_tag_for_version",
    "PREPARE_UPGRADE_VARS",
    "BACKUP_VERIFY_VARS",
    "ROLLBACK_VARS",
    "UPGRADE_YML_VARS",
    # Messages
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
    "SKIP_MSGS",
    "BACKUP_TEST_NAMES",
    "BACKUP_LOG_MSGS",
    "BACKUP_ASSERT_MSGS",
    "BACKUP_SKIP_MSGS",
    "PREPARE_TEST_NAMES",
    "PREPARE_LOG_MSGS",
    "PREPARE_ASSERT_MSGS",
    "PREPARE_SKIP_MSGS",
    "ROLLBACK_TEST_NAMES",
    "ROLLBACK_LOG_MSGS",
    "ROLLBACK_ASSERT_MSGS",
    "ROLLBACK_SKIP_MSGS",
    "UPGRADE_YML_TEST_NAMES",
    "UPGRADE_YML_LOG_MSGS",
    "UPGRADE_YML_ASSERT_MSGS",
    "UPGRADE_YML_SKIP_MSGS",
]
