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
VAST Storage test names, log messages, and assertion messages.

Spec: TSPEC-STOR-2026-001 v1.0.0
"""

# =============================================================================
# TEST NAMES (mapped to test case IDs from test spec)
# =============================================================================
TEST_NAMES = {
    # Functional Tests
    "tc_001_single_backend_active": "TC-001: Single Storage Backend Active",
    "tc_002_unified_namespace": "TC-002: Unified /shared Namespace",
    "tc_003_node_scratch_isolation": "TC-003: Per-Node Scratch Isolation",
    "tc_004_ib_mtu_configuration": "TC-004: InfiniBand MTU Configuration",
    "tc_005_single_ib_interface": "TC-005: Single IB Interface Configuration",
    "tc_006_mount_options_applied": "TC-006: Mount Options Applied Correctly",
    "tc_007_boot_mount_consistency": "TC-007: Boot Mount Consistency",
    "tc_008_slurm_state_persistence": "TC-008: Slurm State Persistence",
    "tc_011_parse_storage_config": "TC-011: Parse storage_config.yaml",
    "tc_012_backend_role_assignment": "TC-012: Backend Role Assignment",
    "tc_013_ib_network_config": "TC-013: IB Network Configuration",
    "tc_014_vastnfs_client_install": "TC-014: VAST NFS Client Installation",
    "tc_015_fstab_generation": "TC-015: /etc/fstab Generation",
    "tc_016_vast_rdma_mount": "TC-016: VAST RDMA Mount",
    "tc_018_powervault_iscsi": "TC-018: PowerVault iSCSI Mount",
    "tc_019_e2e_provisioning": "TC-019: End-to-End Provisioning",
    "tc_021_vast_compute_only": "TC-021: VAST on Compute Only",
    "tc_022_powerscale_all_roles": "TC-022: PowerScale on All Roles",
    "tc_023_mount_permissions": "TC-023: Mount Permissions Applied",
    "tc_025_mount_accessibility": "TC-025: Mount Point Accessibility",
    "tc_028_concurrent_backends": "TC-028: Concurrent Backend Mounts",
    "tc_029_mpi_checkpoint": "TC-029: MPI Checkpoint to VAST",
    "tc_031_add_compute_node": "TC-031: Add Compute Node",
    "tc_032_remove_compute_node": "TC-032: Remove Compute Node",
    "tc_034_backend_job_consistency": "TC-034: Job Output Consistency",
    "tc_035_mysql_persistence": "TC-035: MySQL Database Persistence",
    "tc_036_ldap_user_jobs": "TC-036: LDAP User Job Execution",
    "tc_037_job_logs_persistence": "TC-037: Job Logs Persistence",
    "tc_038_hpc_compilation": "TC-038: HPC Application Compilation",
    "tc_042_rdma_drivers": "TC-042: RDMA Drivers Loaded",
    "tc_043_vastnfs_kernel_module": "TC-043: VAST NFS Kernel Module",
    "tc_044_slurm_storage_paths": "TC-044: Slurm Storage Paths",
    "tc_046_tmp_bind_mount": "TC-046: /tmp Bind Mount",
    "tc_047_hostname_scratch": "TC-047: Hostname-Scoped Scratch",
    "tc_048_ib_link_validation": "TC-048: IB Link Validation",
    "tc_049_vast_dns_resolution": "TC-049: VAST DNS Resolution",
    "tc_050_vastnfs_ctl_status": "TC-050: vastnfs-ctl Status",
    "tc_051_nfsstat_verification": "TC-051: NFS Mount Protocol Verification",
    "tc_052_controller_no_vast": "TC-052: Controller No VAST",
    "tc_053_login_node_mounts": "TC-053: Login Node Mount Table",
    "tc_054_login_compiler_mounts": "TC-054: Login+Compiler Mount Table",
    "tc_056_powerscale_fallback": "TC-056: PowerScale Fallback",
    "tc_057_permission_profiles": "TC-057: Permission Profiles Applied",
    "tc_058_ib_ip_empty_skip": "TC-058: IB_IP Empty Skip Configuration",
    "tc_059_ib_ip_validation": "TC-059: IB_IP Subnet Validation",
    "tc_060_systemd_mount_units": "TC-060: Systemd Mount Units",
    "tc_063_port_reachability": "TC-063: Port Reachability Checks",
    "tc_085_swap_configuration": "TC-085: Swap Space Configuration",
    "tc_086_vast_enabled_flag": "TC-086: VAST Enabled Flag",
    "tc_087_duplicate_mount_validation": "TC-087: Duplicate Mount Path Validation",
    
    # Negative/Error Tests
    "tc_010_scratch_isolation_failure": "TC-010: Scratch Isolation Failure Handling",
    "tc_024_invalid_yaml": "TC-024: Invalid YAML Handling",
    "tc_033_vast_mount_failure": "TC-033: VAST Mount Failure Logging",
    "tc_066_stale_handle_recovery": "TC-066: STALE Handle Recovery",
    "tc_069_ib_mac_no_ip": "TC-069: IB_MAC Present No IP",
    "tc_070_missing_config_section": "TC-070: Missing Config Section",
    "tc_071_misconfigured_client": "TC-071: Misconfigured Client Boot Failure",
    "tc_072_powerscale_timeout": "TC-072: PowerScale Mount Timeout",
    "tc_073_ib_ip_correlation": "TC-073: IB_IP Correlation Validation",
    
    # Performance Tests
    "tc_027_rdma_latency": "TC-027: RDMA Latency Performance",
    "tc_076_aggregate_throughput": "TC-076: Aggregate Throughput",
    "tc_077_iops_performance": "TC-077: IOPS Performance",
    
    # Idempotency Tests
    "tc_074_provisioning_idempotency": "TC-074: Provisioning Idempotency",
    "tc_075_mount_state_idempotency": "TC-075: Mount State Idempotency",
    
    # Compatibility Tests
    "tc_084_rhel_compatibility": "TC-084: RHEL Kernel Compatibility",
}

# =============================================================================
# TEST LOG MESSAGES
# =============================================================================
TEST_LOG_MSGS = {
    # Setup messages
    "setup_start": "Starting test setup for {test_name}",
    "setup_complete": "Test setup completed successfully",
    "teardown_start": "Starting test teardown",
    "teardown_complete": "Test teardown completed",
    
    # Verification messages
    "verifying_config": "Verifying storage configuration: {config_file}",
    "checking_mount": "Checking mount point: {mount_point}",
    "validating_network": "Validating network configuration for {interface}",
    "testing_rdma": "Testing RDMA connectivity to {host}:{port}",
    "checking_module": "Checking kernel module: {module}",
    "validating_dns": "Validating DNS resolution for {fqdn}",
    "checking_service": "Checking service status: {service}",
    "measuring_performance": "Measuring {metric} performance",
    
    # Node operations
    "collecting_nodes": "Collecting nodes with functional group: {group}",
    "connecting_node": "Connecting to node: {node_ip}",
    "executing_command": "Executing command on {node}: {command}",
    "node_accessible": "Node {node_ip} is accessible",
    "node_inaccessible": "Node {node_ip} is not accessible: {error}",
    
    # Mount operations
    "mount_attempt": "Attempting to mount {backend} at {mount_point}",
    "mount_success": "Successfully mounted {mount_point}",
    "mount_failed": "Failed to mount {mount_point}: {error}",
    "unmount_attempt": "Attempting to unmount {mount_point}",
    "unmount_success": "Successfully unmounted {mount_point}",
    
    # Performance measurements
    "latency_measured": "Measured latency: {avg_us} µs (avg), {p99_us} µs (p99)",
    "throughput_measured": "Measured throughput: {throughput_gb} GB/s",
    "iops_measured": "Measured IOPS: {iops}",
    
    # Error handling
    "error_detected": "Error detected: {error}",
    "retry_attempt": "Retry attempt {attempt}/{max_attempts}",
    "recovery_initiated": "Recovery initiated for {issue}",
    "fallback_triggered": "Fallback to {backend} triggered",
}

# =============================================================================
# TEST ASSERTION MESSAGES
# =============================================================================
TEST_ASSERT_MSGS = {
    # Configuration assertions
    "single_backend": "Only one storage backend should be active",
    "backend_enabled": "{backend} should be enabled for {role}",
    "backend_disabled": "{backend} should be disabled for {role}",
    "config_valid": "Storage configuration should be valid YAML",
    "config_section_present": "Configuration section '{section}' should be present",
    
    # Network assertions
    "ib_interface_configured": "IB interface {interface} should be configured",
    "ib_mtu_correct": "IB MTU should be {expected_mtu}, got {actual_mtu}",
    "ib_ip_assigned": "IB interface should have IP in subnet {subnet}",
    "ib_link_active": "IB link should be active",
    "port_reachable": "Port {port} should be reachable on {host}",
    
    # Mount assertions
    "mount_exists": "Mount point {mount_point} should exist",
    "mount_active": "Mount {mount_point} should be active",
    "mount_options": "Mount should have options: {options}",
    "mount_protocol": "Mount should use protocol: {protocol}",
    "fstab_entry": "fstab should contain entry for {mount_point}",
    "systemd_unit_active": "Systemd mount unit {unit} should be active",
    
    # Module/Service assertions
    "module_loaded": "Kernel module {module} should be loaded",
    "rpm_installed": "RPM package {package} should be installed",
    "service_running": "Service {service} should be running",
    "command_available": "Command {command} should be available",
    
    # Permission assertions
    "file_ownership": "File {path} should be owned by {user}:{group}",
    "file_permissions": "File {path} should have permissions {mode}",
    "write_access": "User {user} should have write access to {path}",
    "no_write_access": "User {user} should not have write access to {path}",
    
    # Isolation assertions
    "scratch_isolated": "Scratch directory should be isolated per node",
    "tmp_isolated": "/tmp should be isolated per node",
    "no_data_leakage": "No data leakage between nodes",
    
    # Performance assertions
    "latency_within_target": "Latency {actual} µs should be <= {target} µs",
    "throughput_meets_target": "Throughput {actual} GB/s should be >= {target} GB/s",
    "iops_meets_target": "IOPS {actual} should be >= {target}",
    "boot_time_acceptable": "Boot time increase {percent}% should be <= {tolerance}%",
    
    # DNS assertions
    "dns_resolves": "FQDN {fqdn} should resolve to IB subnet",
    "dns_ip_range": "Resolved IP {ip} should be in range {subnet}",
    
    # Idempotency assertions
    "state_unchanged": "System state should be unchanged after re-run",
    "mounts_consistent": "Mount state should be consistent across reboots",
    
    # Error handling assertions
    "error_logged": "Error should be logged in {log_file}",
    "recovery_successful": "Recovery from {error} should be successful",
    "fallback_activated": "Fallback to {backend} should be activated",
    "graceful_degradation": "System should degrade gracefully",
}

# =============================================================================
# ERROR MESSAGES
# =============================================================================
ERROR_MESSAGES = {
    "yaml_parse_error": "Failed to parse YAML configuration: {error}",
    "mount_timeout": "Mount operation timed out after {timeout} seconds",
    "rdma_connection_failed": "RDMA connection failed: {error}",
    "ib_link_down": "InfiniBand link is down on interface {interface}",
    "dns_resolution_failed": "DNS resolution failed for {fqdn}: {error}",
    "module_not_loaded": "Required kernel module {module} is not loaded",
    "rpm_not_installed": "Required RPM package {package} is not installed",
    "permission_denied": "Permission denied accessing {path}",
    "stale_handle": "Stale NFS file handle detected on {mount_point}",
    "duplicate_mount": "Duplicate mount path detected: {path}",
    "missing_config": "Missing required configuration: {config}",
    "invalid_subnet": "IP {ip} is not in required subnet {subnet}",
    "port_unreachable": "Port {port} is not reachable on {host}",
    "service_not_running": "Required service {service} is not running",
    "test_timeout": "Test timed out after {timeout} seconds",
}

# =============================================================================
# SUCCESS MESSAGES
# =============================================================================
SUCCESS_MESSAGES = {
    "config_valid": "Storage configuration is valid",
    "mount_successful": "Successfully mounted {mount_point}",
    "rdma_connected": "RDMA connection established successfully",
    "performance_target_met": "Performance target met: {metric}",
    "recovery_complete": "Recovery completed successfully",
    "provisioning_complete": "Node provisioning completed successfully",
    "test_passed": "Test {test_name} passed successfully",
    "all_nodes_accessible": "All {count} nodes are accessible",
    "idempotency_verified": "Idempotency verified - no changes detected",
    "isolation_verified": "Node isolation verified successfully",
}
