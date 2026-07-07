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
PowerVault iSCSI storage test names, log messages, and assertion messages.
"""

# =============================================================================
# TEST NAMES (mapped to test case IDs)
# =============================================================================
TEST_NAMES = {
    # Category 1: iSCSI Infrastructure Validation
    "tc_pv_001": "TC-PV-001: iSCSI daemon (iscsid) enabled and running",
    "tc_pv_002": "TC-PV-002: iSCSI initiator name configured correctly",
    "tc_pv_003": "TC-PV-003: iSCSI target discovery succeeds from all portal IPs",
    "tc_pv_004": "TC-PV-004: iSCSI sessions are active",
    "tc_pv_005": "TC-PV-005: iSCSI node startup set to automatic",
    "tc_pv_006": "TC-PV-006: iSCSI portal port reachability",
    # Category 2: Multipath Validation
    "tc_pv_007": "TC-PV-007: multipathd service enabled and running",
    "tc_pv_008": "TC-PV-008: Multipath device exists and matches volume_id",
    "tc_pv_009": "TC-PV-009: Multipath device has multiple paths (redundancy)",
    # Category 3: Partition, Filesystem, and Mount
    "tc_pv_010": "TC-PV-010: GPT partition exists on multipath device",
    "tc_pv_011": "TC-PV-011: Filesystem formatted with correct type",
    "tc_pv_012": "TC-PV-012: Mount point directory exists",
    "tc_pv_013": "TC-PV-013: PowerVault volume is actively mounted",
    "tc_pv_014": "TC-PV-014: Mount options applied correctly",
    "tc_pv_015": "TC-PV-015: Persistent fstab entry created",
    # Category 4: Bind Mount Validation
    "tc_pv_016": "TC-PV-016: Node-specific subdirectory exists under mount point",
    "tc_pv_017": "TC-PV-017: Bind mount targets exist and are mounted",
    "tc_pv_018": "TC-PV-018: Bind mount fstab entries are persistent",
    "tc_pv_019": "TC-PV-019: Bind mount isolation (per-node data separation)",
    # Category 5: Functional Group Targeting
    "tc_pv_020": "TC-PV-020: PowerVault mounted only on correct functional groups",
    "tc_pv_021": "TC-PV-021: Multiple functional group prefixes target all matching groups",
    # Category 6: I/O and Data Integrity
    "tc_pv_022": "TC-PV-022: Write/Read test on PowerVault mount",
    "tc_pv_023": "TC-PV-023: Bind mount I/O test",
    # Category 7: Cloud-Init Integration and Logging
    "tc_pv_024": "TC-PV-024: Cloud-init runcmd script execution log exists",
    "tc_pv_025": "TC-PV-025: Cloud-init groups dict contains powervault_scripts",
    # Category 8: Error Handling and Edge Cases
    "tc_pv_026": "TC-PV-026: No duplicate fstab entries",
    # Category 9: Slurm-Specific PowerVault Validation
    "tc_pv_027": "TC-PV-027: Mandatory slurm_control_node bind mounts present and active",
    "tc_pv_028": "TC-PV-028: MySQL/MariaDB data directory on PowerVault mount",
    "tc_pv_029": "TC-PV-029: All PowerVault mounts are writable",
}

# =============================================================================
# TEST LOG MESSAGES
# =============================================================================
TEST_LOG_MSGS = {
    # Setup
    "reading_config": "Reading storage_config.yml from omnia_core container",
    "no_pv_config": "No powervault_config found in storage_config.yml — skipping",
    "found_pv_entries": "Found {count} powervault_config entries",
    "processing_pv_entry": "Processing PowerVault entry: {name}",
    # Node discovery
    "collecting_nodes": "Collecting nodes for functional group prefix: {prefix}",
    "found_target_nodes": "Found {count} target nodes for entry '{name}'",
    "connecting_node": "Connecting to node: {node_ip}",
    # iSCSI
    "checking_iscsid": "Checking iscsid service on {node_ip}",
    "checking_initiator": "Checking iSCSI initiator name on {node_ip}",
    "checking_discovery": "Running iSCSI discovery from {node_ip} to {portal_ip}:{port}",
    "checking_sessions": "Checking iSCSI sessions on {node_ip}",
    "checking_startup": "Checking iSCSI node.startup setting on {node_ip}",
    "checking_port": "Checking port {port} reachability to {portal_ip} from {node_ip}",
    # Multipath
    "checking_multipathd": "Checking multipathd service on {node_ip}",
    "checking_mpath_device": "Checking multipath device for volume_id '{volume_id}' on {node_ip}",
    "checking_mpath_paths": "Checking multipath path count on {node_ip}",
    "found_mpath_device": "Found multipath device: {device} on {node_ip}",
    # Partition/Mount
    "checking_partition": "Checking GPT partition on {device} on {node_ip}",
    "checking_fs_type": "Checking filesystem type on {node_ip}",
    "checking_mount_point": "Checking mount point {mount_point} on {node_ip}",
    "checking_mount_active": "Checking if {mount_point} is actively mounted on {node_ip}",
    "checking_mount_opts": "Checking mount options for {mount_point} on {node_ip}",
    "checking_fstab": "Checking fstab entry for {mount_point} on {node_ip}",
    # Bind mounts
    "checking_node_subdir": "Checking node subdirectory under {mount_point} on {node_ip}",
    "checking_bind_mounts": "Checking bind mounts on {node_ip}",
    "checking_bind_fstab": "Checking bind mount fstab entries on {node_ip}",
    "checking_bind_isolation": "Checking bind mount isolation between {node_a} and {node_b}",
    # Functional groups
    "checking_group_targeting": "Checking functional group targeting for entry '{name}'",
    "checking_multi_prefix": "Checking multiple prefix targeting for entry '{name}'",
    # I/O
    "running_io_test": "Running I/O write/read test on {mount_point} on {node_ip}",
    "running_bind_io_test": "Running bind mount I/O test on {node_ip}",
    # Cloud-init
    "checking_setup_log": "Checking iSCSI setup log for '{name}' on {node_ip}",
    "checking_cloud_init_dict": "Checking cloud_init_groups_dict for powervault_scripts",
    # Fstab
    "checking_fstab_duplicates": "Checking for duplicate fstab entries on {node_ip}",
    # Slurm-specific
    "checking_slurm_mandatory_binds": "Checking mandatory slurm bind mounts on {node_ip}",
    "checking_mysql_data": "Checking MySQL data on PowerVault mount on {node_ip}",
    "checking_mount_writable": "Checking writability of {mount_path} on {node_ip}",
}

# =============================================================================
# TEST ASSERTION MESSAGES
# =============================================================================
TEST_ASSERT_MSGS = {
    # iSCSI
    "iscsid_active": (
        "iscsid should be active and enabled on {node_ip}. "
        "Expected: active/enabled, Actual: {actual}"
    ),
    "iscsid_enabled": (
        "iscsid should be enabled on {node_ip}. "
        "Expected: enabled, Actual: {actual}"
    ),
    "initiator_match": (
        "InitiatorName mismatch on {node_ip}. "
        "Expected: '{expected}', Actual: '{actual}'"
    ),
    "discovery_success": (
        "iSCSI discovery should return target IQN from {portal_ip}:{port}. "
        "Expected: IQN discovered, Actual: {actual}"
    ),
    "session_active": (
        "At least one iSCSI session should be active on {node_ip}. "
        "Expected: >= 1 session, Actual: {actual}"
    ),
    "session_iqn_match": (
        "iSCSI session should target correct IQN on {node_ip}. "
        "Expected: matching IQN, Actual: {actual}"
    ),
    "startup_automatic": (
        "node.startup should be 'automatic' on {node_ip}. "
        "Expected: automatic, Actual: {actual}"
    ),
    "port_reachable": (
        "Port {port} should be reachable on {portal_ip} from {node_ip}. "
        "Expected: reachable, Actual: {actual}"
    ),
    # Multipath
    "multipathd_active": (
        "multipathd should be active and enabled on {node_ip}. "
        "Expected: active/enabled, Actual: {actual}"
    ),
    "multipathd_enabled": (
        "multipathd should be enabled on {node_ip}. "
        "Expected: enabled, Actual: {actual}"
    ),
    "mpath_device_exists": (
        "Multipath device matching volume_id should exist on {node_ip}. "
        "Expected: volume_id='{volume_id}', Actual: {actual}"
    ),
    "mpath_has_paths": (
        "Multipath device should have sufficient active paths on {node_ip}. "
        "Expected: >= {expected} path(s), Actual: {actual} path(s)"
    ),
    # Partition/Mount
    "gpt_partition_exists": (
        "GPT partition should exist on {device} on {node_ip}. "
        "Expected: GPT partition present, Actual: {actual}"
    ),
    "fs_type_match": (
        "Filesystem type mismatch on {node_ip}. "
        "Expected: '{expected}', Actual: '{actual}'"
    ),
    "mount_point_exists": (
        "Mount point directory should exist on {node_ip}. "
        "Expected: {mount_point} exists, Actual: {actual}"
    ),
    "volume_mounted": (
        "Volume should be actively mounted on {node_ip}. "
        "Expected: {mount_point} mounted, Actual: {actual}"
    ),
    "mount_opts_present": (
        "Mount option missing for {mount_point} on {node_ip}. "
        "Expected: '{option}' present, Actual: not found"
    ),
    "fstab_entry_exists": (
        "fstab entry should exist for {mount_point} on {node_ip}. "
        "Expected: entry present, Actual: {actual}"
    ),
    "fstab_fs_type_match": (
        "fstab fs_type mismatch for {mount_point} on {node_ip}. "
        "Expected: '{expected}', Actual: '{actual}'"
    ),
    # Bind mounts
    "node_subdir_exists": (
        "Node subdirectory should exist on {node_ip}. "
        "Expected: {subdir} exists, Actual: {actual}"
    ),
    "bind_source_exists": (
        "Bind mount source should exist on {node_ip}. "
        "Expected: {source} exists, Actual: {actual}"
    ),
    "bind_target_exists": (
        "Bind mount target should exist on {node_ip}. "
        "Expected: {target} exists, Actual: {actual}"
    ),
    "bind_target_mounted": (
        "Bind mount target should be a mountpoint on {node_ip}. "
        "Expected: {target} is mountpoint, Actual: {actual}"
    ),
    "bind_fstab_entry": (
        "Bind mount fstab entry should exist on {node_ip}. "
        "Expected: entry for {target}, Actual: {actual}"
    ),
    "bind_isolation": (
        "Bind mount data should be isolated between nodes. "
        "Expected: file on {node_a} NOT visible on {node_b} at {path}, Actual: {actual}"
    ),
    # Functional groups
    "mount_present_on_target": (
        "Mount should be present on target node {node_ip}. "
        "Expected: {mount_point} mounted, Actual: {actual}"
    ),
    "mount_absent_on_non_target": (
        "Mount should be ABSENT on non-target node {node_ip}. "
        "Expected: {mount_point} not mounted, Actual: {actual}"
    ),
    "all_prefix_groups_targeted": (
        "All groups matching prefixes should have the mount. "
        "Expected: mounted, Actual: {actual}"
    ),
    # I/O
    "io_write_success": (
        "Write to {mount_point} should succeed on {node_ip}. "
        "Expected: write OK, Actual: {actual}"
    ),
    "io_checksum_match": (
        "Checksum verification should pass on {node_ip}. "
        "Expected: checksum match, Actual: {actual}"
    ),
    "bind_io_write_success": (
        "Write to bind target should succeed on {node_ip}. "
        "Expected: write OK, Actual: {actual}"
    ),
    "bind_io_read_match": (
        "Data at bind source should match bind target on {node_ip}. "
        "Expected: data match, Actual: {actual}"
    ),
    # Cloud-init
    "setup_log_exists": (
        "Setup log should exist on {node_ip}. "
        "Expected: /var/log/omnia_iscsi_setup_{name}.log exists, Actual: {actual}"
    ),
    "setup_log_complete": (
        "Setup log should contain completion message on {node_ip}. "
        "Expected: completion marker present, Actual: {actual}"
    ),
    "setup_log_no_errors": (
        "Setup log should have no ERROR entries on {node_ip}. "
        "Expected: 0 errors, Actual: {actual}"
    ),
    "cloud_init_pv_scripts": (
        "cloud_init_groups_dict should contain powervault_scripts for group '{group}'. "
        "Expected: present, Actual: {actual}"
    ),
    # Fstab
    "no_duplicate_fstab": (
        "There should be exactly 1 fstab entry for {mount_point} on {node_ip}. "
        "Expected: 1, Actual: {count}"
    ),
    # Slurm-specific
    "slurm_mandatory_bind_present": (
        "Mandatory slurm bind mount {path} should be configured and active on {node_ip}. "
        "Expected: configured=True, mounted=True, Actual: configured={configured}, mounted={mounted}"
    ),
    "mysql_data_on_mount": (
        "MySQL/MariaDB data should reside on PowerVault mount on {node_ip}. "
        "Expected: mountpoint=True, service=active, data_files=present, slurm_db=present, "
        "Actual: {actual}"
    ),
    "mount_writable": (
        "Mount {mount_path} should be writable on {node_ip}. "
        "Expected: writable, Actual: {actual}"
    ),
}

# =============================================================================
# ERROR MESSAGES
# =============================================================================
ERROR_MESSAGES = {
    "config_read_failed": "Failed to read storage_config.yml: {error}",
    "no_pv_config": "No powervault_config section in storage_config.yml",
    "no_target_nodes": "No target nodes found for functional_group_prefix: {prefix}",
    "ssh_failed": "SSH connection failed to {node_ip}: {error}",
    "service_not_active": "Service {service} is not active on {node_ip}",
    "discovery_failed": "iSCSI discovery failed from {node_ip} to {portal_ip}:{port}",
    "no_sessions": "No active iSCSI sessions on {node_ip}",
    "mpath_not_found": "No multipath device matching volume_id '{volume_id}' on {node_ip}",
    "port_unreachable": "Port {port} unreachable on {portal_ip} from {node_ip}",
    "io_test_failed": "I/O test failed on {mount_point} on {node_ip}: {error}",
}

# =============================================================================
# SUCCESS MESSAGES
# =============================================================================
SUCCESS_MESSAGES = {
    "iscsid_verified": "iscsid is active and enabled on {node_ip}",
    "initiator_verified": "Initiator name matches config on {node_ip}",
    "discovery_verified": "iSCSI discovery successful on {node_ip}",
    "sessions_verified": "iSCSI sessions active on {node_ip}",
    "startup_verified": "node.startup is automatic on {node_ip}",
    "ports_verified": "All portal ports reachable from {node_ip}",
    "multipathd_verified": "multipathd is active and enabled on {node_ip}",
    "mpath_device_verified": "Multipath device '{device}' verified on {node_ip}",
    "mpath_paths_verified": "Multipath redundancy verified ({count} paths) on {node_ip}",
    "partition_verified": "GPT partition verified on {node_ip}",
    "fs_type_verified": "Filesystem type '{fs_type}' verified on {node_ip}",
    "mount_point_verified": "Mount point {mount_point} exists on {node_ip}",
    "volume_mount_verified": "Volume actively mounted at {mount_point} on {node_ip}",
    "mount_opts_verified": "Mount options verified for {mount_point} on {node_ip}",
    "fstab_verified": "Persistent fstab entry verified for {mount_point} on {node_ip}",
    "node_subdir_verified": "Node subdirectory verified on {node_ip}",
    "bind_mounts_verified": "Bind mounts verified on {node_ip}",
    "bind_fstab_verified": "Bind mount fstab entries verified on {node_ip}",
    "bind_isolation_verified": "Bind mount isolation verified between nodes",
    "group_targeting_verified": "Functional group targeting verified for entry '{name}'",
    "multi_prefix_verified": "Multiple prefix targeting verified for entry '{name}'",
    "io_test_verified": "I/O write/read test passed on {mount_point} on {node_ip}",
    "bind_io_verified": "Bind mount I/O test passed on {node_ip}",
    "setup_log_verified": "Setup log verified for '{name}' on {node_ip}",
    "cloud_init_dict_verified": "cloud_init_groups_dict verified for powervault_scripts",
    "no_duplicate_fstab_verified": "No duplicate fstab entries on {node_ip}",
    "slurm_mandatory_binds_verified": "Mandatory slurm bind mounts verified on {node_ip}",
    "mysql_data_verified": "MySQL data on PowerVault mount verified on {node_ip}",
    "mount_writable_verified": "{mount_path} is writable on {node_ip}",
}
