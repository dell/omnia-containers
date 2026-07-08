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
PowerVault iSCSI storage automation functions module.
"""

from .powervault_func import *

__all__ = [
    # Safe remote execution
    "safe_run_on_remote_node",
    # Configuration readers
    "read_storage_config",
    "get_powervault_entries",
    "get_mount_params",
    "skip_if_no_powervault",
    "resolve_pv_fs_type",
    "resolve_pv_mount_opts",
    # Node discovery
    "get_target_nodes",
    "get_non_target_nodes",
    "resolve_node_key_value",
    # iSCSI verification
    "verify_iscsi_service",
    "verify_initiator_name",
    "verify_iscsi_discovery",
    "verify_iscsi_sessions",
    "verify_iscsi_startup_automatic",
    "verify_portal_reachability",
    # Multipath verification
    "verify_multipath_service",
    "verify_multipath_device",
    "verify_multipath_paths",
    # Partition/Mount verification
    "verify_gpt_partition",
    "verify_filesystem_type",
    "verify_mount_point_exists",
    "verify_volume_mounted",
    "verify_mount_options",
    "verify_fstab_entry",
    # Bind mount verification
    "verify_node_subdirectory",
    "verify_bind_mounts",
    "verify_bind_fstab_entries",
    "verify_bind_isolation",
    # Functional group targeting
    "verify_functional_group_targeting",
    "verify_multiple_prefix_targeting",
    # I/O verification
    "verify_io_test",
    "verify_bind_io_test",
    # Cloud-init and logging
    "verify_setup_log",
    "verify_cloud_init_groups_dict",
    # Fstab duplicate check
    "verify_no_duplicate_fstab",
    # Slurm-specific and writability checks
    "verify_mount_writable",
    "verify_slurm_mandatory_bind_mounts",
    "verify_mysql_data_on_mount",
    "SLURM_MANDATORY_BIND_MOUNTS",
]
