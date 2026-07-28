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
Mount configuration test automation module.
"""

from .functions import (
    read_storage_config,
    get_mounts_entries,
    get_swap_entries,
    get_mount_params,
    skip_if_no_mounts,
    resolve_mount_fs_type,
    resolve_mount_opts,
    resolve_mount_dump_freq,
    resolve_mount_fsck_pass,
    get_target_nodes_for_mount,
    get_non_target_nodes_for_mount,
    resolve_node_key_value,
    verify_mount_point_exists,
    verify_volume_mounted,
    verify_mount_options,
    verify_fstab_entry,
    verify_node_subdirectory,
    verify_bind_mounts,
    verify_bind_fstab_entries,
    verify_bind_isolation,
    verify_mount_permissions,
    verify_mount_on_oim,
)

from .vars import (
    DEFAULT_FS_TYPE,
    DEFAULT_MOUNT_OPTS,
    DEFAULT_NODE_KEY,
    NODE_KEY_COMMANDS,
    FSTAB_BIND_FS_TYPE,
    FSTAB_BIND_OPTIONS,
)

from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SUCCESS_MESSAGES,
)

__all__ = [
    # Functions
    "read_storage_config",
    "get_mounts_entries",
    "get_swap_entries",
    "get_mount_params",
    "skip_if_no_mounts",
    "resolve_mount_fs_type",
    "resolve_mount_opts",
    "resolve_mount_dump_freq",
    "resolve_mount_fsck_pass",
    "get_target_nodes_for_mount",
    "get_non_target_nodes_for_mount",
    "resolve_node_key_value",
    "verify_mount_point_exists",
    "verify_volume_mounted",
    "verify_mount_options",
    "verify_fstab_entry",
    "verify_node_subdirectory",
    "verify_bind_mounts",
    "verify_bind_fstab_entries",
    "verify_bind_isolation",
    "verify_mount_permissions",
    "verify_mount_on_oim",
    # Vars
    "DEFAULT_FS_TYPE",
    "DEFAULT_MOUNT_OPTS",
    "DEFAULT_NODE_KEY",
    "NODE_KEY_COMMANDS",
    "FSTAB_BIND_FS_TYPE",
    "FSTAB_BIND_OPTIONS",
    "IO_TEST_FILE",
    "IO_TEST_CONTENT",
    "IO_TEST_CHECKSUM_FILE",
    # Messages
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
    "SUCCESS_MESSAGES",
]
