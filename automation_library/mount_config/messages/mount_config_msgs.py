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
Message strings for mount_config test automation.
"""

TEST_NAMES = {
    "tc_mount_001": "TC-MOUNT-001: Verify mount point exists",
    "tc_mount_002": "TC-MOUNT-002: Verify mount is active",
    "tc_mount_003": "TC-MOUNT-003: Verify filesystem type",
    "tc_mount_004": "TC-MOUNT-004: Verify mount options",
    "tc_mount_005": "TC-MOUNT-005: Verify fstab persistence",
    "tc_mount_006": "TC-MOUNT-006: Verify mount_params resolution",
    "tc_mount_007": "TC-MOUNT-007: Verify functional group prefix targeting",
    "tc_mount_008": "TC-MOUNT-008: Verify exact groups targeting",
    "tc_mount_009": "TC-MOUNT-009: Verify mount_on_oim",
    "tc_mount_010": "TC-MOUNT-010: Verify node subdirectory exists",
    "tc_mount_011": "TC-MOUNT-011: Verify node_key bind mounts active",
    "tc_mount_012": "TC-MOUNT-012: Verify bind mount fstab entries",
    "tc_mount_013": "TC-MOUNT-013: Verify bind mount isolation",
    "tc_mount_014": "TC-MOUNT-014: Verify mount permissions",
}

TEST_LOG_MSGS = {
    "checking_mount_point": "Checking mount point {mount_point} on {node_ip}",
    "checking_fstab": "Checking fstab entry for {mount_point} on {node_ip}",
    "checking_mount_options": "Checking mount options for {mount_point} on {node_ip}",
    "checking_node_subdir": "Checking node subdirectory {subdir} on {node_ip}",
    "checking_bind_mounts": "Checking bind mounts on {node_ip}",
    "checking_bind_isolation": "Checking bind mount isolation for {bind_target} on {node_ip}",
    "checking_permissions": "Checking permissions for {path} on {node_ip}",
    "mount_ok": "Mount {mount_point} verified on {node_ip}",
    "mount_failed": "Mount {mount_point} verification failed on {node_ip}: {error}",
    "no_mounts": "No mounts configured in storage_config.yml",
    "no_target_nodes": "No target nodes found for mount {name}",
}

TEST_ASSERT_MSGS = {
    "mount_point_missing": "Mount point {mount_point} does not exist on {node_ip}",
    "mount_not_active": "Mount {mount_point} is not active on {node_ip}",
    "fstab_missing": "No fstab entry for {mount_point} on {node_ip}",
    "options_mismatch": "Mount options mismatch for {mount_point}: expected {expected}, actual {actual}",
    "node_subdir_missing": "Node subdirectory {subdir} does not exist on {node_ip}",
    "bind_mount_missing": "Bind mount {bind_target} is not active on {node_ip}",
    "bind_isolation_failed": "Bind mount {bind_target} is not isolated on {node_ip}",
    "permission_mismatch": "Permission mismatch for {path}: expected {expected}, actual {actual}",
}

SUCCESS_MESSAGES = {
    "mount_verified": "Mount {mount_point} verified on {node_ip}",
    "fstab_verified": "Fstab entry verified for {mount_point} on {node_ip}",
    "bind_mount_verified": "Bind mount {bind_target} verified on {node_ip}",
    "isolation_verified": "Bind isolation verified for {bind_target} on {node_ip}",
}
