# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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

"""etcd local disk message constants used by the OMNIA automation library."""

# =============================================================================
# GENERAL
# =============================================================================

ETCD_LOCAL_DISK_DISABLED = (
    "etcd_on_local_disk is not enabled in omnia_config.yml - skipping local disk tests"
)
NO_CONTROL_PLANE_NODES = "No control plane nodes found in PXE mapping"
NODE_UNREACHABLE = "Node {node} is unreachable via {target}"

# =============================================================================
# TC-F01: BOSS CARD DETECTION
# =============================================================================

BOSS_CARD_DETECTED = "Dell BOSS card detected on node {node}: {details}"
BOSS_CARD_NOT_DETECTED = "Dell BOSS card not detected on node {node}"
BOSS_CARD_CHECK_PASSED = "BOSS card detection passed on all control plane nodes"
BOSS_CARD_CHECK_FAILED = "BOSS card detection failed: {message}"
BOSS_CARD_CHECK_SKIPPED = "BOSS card detection skipped: {message}"

# =============================================================================
# TC-F02: RAID CONFIGURATION VALIDATION
# =============================================================================

RAID_CONFIG_VALID = "RAID configuration is valid on node {node}: {details}"
RAID_CONFIG_INVALID = "RAID configuration is invalid on node {node}: {details}"
RAID_CHECK_PASSED = "RAID configuration validation passed on all control plane nodes"
RAID_CHECK_FAILED = "RAID configuration validation failed: {message}"

# =============================================================================
# TC-F03: DISK PARTITIONING
# =============================================================================

PARTITION_EXISTS = "GPT partition exists for etcd on node {node}: {partition}"
PARTITION_NOT_FOUND = "No GPT partition found for etcd on node {node}"
PARTITION_IS_ROOT = "Partition on node {node} is the root disk - not allowed"
PARTITION_CHECK_PASSED = "Disk partitioning verification passed on all control plane nodes"
PARTITION_CHECK_FAILED = "Disk partitioning verification failed: {message}"

# =============================================================================
# TC-F04: FILESYSTEM CREATION
# =============================================================================

FILESYSTEM_VALID = "Filesystem on node {node} is {fstype} on {partition}"
FILESYSTEM_INVALID = "Filesystem on node {node} is not ext4/xfs: {fstype}"
FILESYSTEM_NOT_FOUND = "No filesystem found on etcd partition on node {node}"
FILESYSTEM_CHECK_PASSED = "Filesystem creation verification passed on all control plane nodes"
FILESYSTEM_CHECK_FAILED = "Filesystem creation verification failed: {message}"

# =============================================================================
# TC-F05: FSTAB UPDATE AND MOUNT
# =============================================================================

FSTAB_ENTRY_EXISTS = "UUID-based fstab entry exists for {mount} on node {node}"
FSTAB_ENTRY_MISSING = "No fstab entry found for {mount} on node {node}"
MOUNT_ACTIVE = "{mount} is mounted on node {node}"
MOUNT_NOT_ACTIVE = "{mount} is not mounted on node {node}"
FSTAB_CHECK_PASSED = "fstab update and mount verification passed on all control plane nodes"
FSTAB_CHECK_FAILED = "fstab update and mount verification failed: {message}"

# =============================================================================
# TC-F06: ETCD CONFIGURATION TO LOCAL DISK
# =============================================================================

ETCD_USING_LOCAL_DISK = "etcd is using local disk at {mount} on node {node}"
ETCD_NOT_USING_LOCAL_DISK = "etcd is not using local disk on node {node}: {details}"
ETCD_CONFIG_CHECK_PASSED = "etcd configuration to local disk passed on all control plane nodes"
ETCD_CONFIG_CHECK_FAILED = "etcd configuration to local disk failed: {message}"

# =============================================================================
# TC-F07: FALLBACK DISK DETECTION
# =============================================================================

FALLBACK_DISK_DETECTED = "Fallback disk detected on node {node}: {disk}"
FALLBACK_DISK_NOT_DETECTED = "No fallback disk detected on node {node}"
FALLBACK_CHECK_PASSED = "Fallback disk detection passed on node {node}"
FALLBACK_CHECK_FAILED = "Fallback disk detection failed: {message}"

# =============================================================================
# TC-F08: FIRST BOOT DISK SETUP
# =============================================================================

FIRST_BOOT_SCRIPT_EXISTS = "etcd-disk-setup.sh exists on node {node}"
FIRST_BOOT_SCRIPT_MISSING = "etcd-disk-setup.sh not found on node {node}"
FIRST_BOOT_LOG_EXISTS = "etcd-disk-setup.log exists on node {node}"
FIRST_BOOT_LOG_MISSING = "etcd-disk-setup.log not found on node {node}"
FIRST_BOOT_LOG_SUCCESS = "etcd-disk-setup.sh completed successfully on node {node}"
FIRST_BOOT_LOG_FAILED = "etcd-disk-setup.sh did not complete successfully on node {node}"
FIRST_BOOT_CHECK_PASSED = "First boot disk setup verification passed on all control plane nodes"
FIRST_BOOT_CHECK_FAILED = "First boot disk setup verification failed: {message}"

# =============================================================================
# TC-F09: SUBSEQUENT BOOT FSTAB UPDATE
# =============================================================================

FSTAB_UPDATE_SCRIPT_EXISTS = "etcd-fstab-update.sh exists on node {node}"
FSTAB_UPDATE_SCRIPT_MISSING = "etcd-fstab-update.sh not found on node {node}"
FSTAB_UPDATE_LOG_EXISTS = "diskless-etcd-mount.log exists on node {node}"
FSTAB_UPDATE_LOG_MISSING = "diskless-etcd-mount.log not found on node {node}"
FSTAB_UPDATE_LOG_SUCCESS = "etcd-fstab-update.sh completed successfully on node {node}"
FSTAB_UPDATE_LOG_FAILED = "etcd-fstab-update.sh did not complete successfully on node {node}"
SUBSEQUENT_BOOT_CHECK_PASSED = (
    "Subsequent boot fstab update verification passed on all control plane nodes"
)
SUBSEQUENT_BOOT_CHECK_FAILED = "Subsequent boot fstab update verification failed: {message}"

# =============================================================================
# TC-F10, TC-F11, TC-F12: DISK TYPE SUPPORT
# =============================================================================

DISK_TYPE_DETECTED = "{disk_type} disk detected on node {node}: {disk}"
DISK_TYPE_NOT_DETECTED = "{disk_type} disk not detected on node {node}"
DISK_TYPE_CHECK_PASSED = "{disk_type} disk support verification passed on node {node}"
DISK_TYPE_CHECK_FAILED = "{disk_type} disk support verification failed: {message}"

# =============================================================================
# ETCD PERMISSIONS
# =============================================================================

ETCD_PERMISSIONS_VALID = "etcd user/group and permissions are correct on node {node}"
ETCD_PERMISSIONS_INVALID = "etcd permissions are incorrect on node {node}: {details}"

# =============================================================================
# POST-REBOOT: CONTROL PLANE REBOOT
# =============================================================================

REBOOT_NODE_INITIATED = "Reboot initiated on control plane node {node} ({ip})"
REBOOT_NODE_NOT_FOUND = "No control plane node found for reboot"
REBOOT_NO_REMAINING_NODES = "No remaining control plane nodes after reboot"
NODE_ONLINE_PASSED = "Node {node} ({ip}) is online after reboot (took {elapsed}s)"
NODE_ONLINE_FAILED = "Node {node} ({ip}) did not come online within {timeout}s"
CLOUD_INIT_PASSED = "Cloud-init completed successfully on node {node} after reboot"
CLOUD_INIT_FAILED = "Cloud-init did not complete on node {node} within {timeout}s"

# =============================================================================
# POST-REBOOT: TC-F09 (TIMESTAMP-AWARE)
# =============================================================================

FSTAB_UPDATE_LOG_TIMESTAMP_VALID = (
    "etcd-fstab-update.sh log updated after reboot on node {node}"
    " (log time: {log_time}, reboot time: {reboot_time})"
)
FSTAB_UPDATE_LOG_TIMESTAMP_STALE = (
    "etcd-fstab-update.sh log was NOT updated after reboot on node {node}"
    " (log time: {log_time}, reboot time: {reboot_time})"
)
SUBSEQUENT_BOOT_POST_REBOOT_PASSED = (
    "Subsequent boot fstab update verified after reboot on all control plane nodes"
)
SUBSEQUENT_BOOT_POST_REBOOT_FAILED = (
    "Subsequent boot fstab update verification failed after reboot: {message}"
)

# =============================================================================
# POST-REBOOT: FSTAB + MOUNT PERSISTENCE
# =============================================================================

FSTAB_MOUNT_POST_REBOOT_PASSED = (
    "fstab entry and mount persisted after reboot on all control plane nodes"
)
FSTAB_MOUNT_POST_REBOOT_FAILED = (
    "fstab/mount persistence failed after reboot: {message}"
)

# =============================================================================
# POST-REBOOT: ETCD LOCAL DISK PERSISTENCE
# =============================================================================

ETCD_LOCAL_DISK_POST_REBOOT_PASSED = (
    "etcd is still using local disk after reboot on all control plane nodes"
)
ETCD_LOCAL_DISK_POST_REBOOT_FAILED = (
    "etcd local disk configuration failed after reboot: {message}"
)

# =============================================================================
# POST-REBOOT: ETCD CLUSTER HEALTH
# =============================================================================

ETCD_CLUSTER_HEALTHY = "etcd cluster is healthy after reboot: {details}"
ETCD_CLUSTER_UNHEALTHY = "etcd cluster is unhealthy after reboot: {details}"
ETCD_HEALTH_CHECK_PASSED = (
    "etcd cluster health verified after reboot on all control plane nodes"
)
ETCD_HEALTH_CHECK_FAILED = "etcd cluster health check failed after reboot: {message}"
