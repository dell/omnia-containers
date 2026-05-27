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
VAST Storage automation module.

Modules:
- functions: Verification functions for all VAST storage test cases
- vars: Constants, paths, and command templates
- messages: Test names, log messages, and assertion messages

Spec: TSPEC-STOR-2026-001 v1.0.0
"""

from .functions import (
    # Node collection
    get_compute_nodes,
    get_controller_nodes,
    get_login_nodes,
    get_all_accessible_nodes,
    # Configuration verification
    verify_storage_config_parsing,
    verify_single_backend_active,
    verify_backend_role_assignment,
    verify_mount_options,
    verify_fstab_generation,
    # Network verification
    verify_ib_interface_config,
    verify_ib_mtu,
    verify_ib_ip_assignment,
    verify_ib_link_status,
    verify_rdma_connectivity,
    verify_dns_resolution,
    verify_port_reachability,
    # VAST specific
    verify_vastnfs_client_install,
    verify_vastnfs_kernel_module,
    verify_vast_rdma_mount,
    verify_vastnfs_ctl_status,
    verify_vast_compute_only,
    # Mount verification
    verify_mount_point_exists,
    verify_mount_active,
    verify_mount_protocol,
    verify_systemd_mount_units,
    verify_mount_permissions,
    verify_mount_accessibility,
    # Storage isolation
    verify_scratch_isolation,
    verify_tmp_bind_mount,
    verify_hostname_scratch_dir,
    # PowerScale/PowerVault
    verify_powerscale_mounts,
    verify_powervault_iscsi,
    verify_powerscale_fallback,
    # Slurm integration
    verify_slurm_state_persistence,
    verify_slurm_storage_paths,
    verify_job_logs_persistence,
    verify_mpi_checkpoint,
    # Performance
    measure_rdma_latency,
    measure_throughput,
    measure_iops,
    measure_boot_time,
    # Error handling
    verify_stale_handle_recovery,
    verify_mount_retry_logic,
    verify_error_logging,
    # Idempotency
    verify_provisioning_idempotency,
    verify_mount_state_consistency,
    # Node operations
    verify_add_compute_node,
    verify_remove_compute_node,
    # Compatibility
    verify_rhel_compatibility,
    verify_job_output_consistency,
)

from .vars import (
    # Node groups
    COMPUTE_NODE_FUNCTIONAL_GROUP,
    CONTROLLER_NODE_FUNCTIONAL_GROUP,
    LOGIN_NODE_FUNCTIONAL_GROUP,
    # Paths
    STORAGE_CONFIG_PATH,
    PXE_MAPPING_PATH,
    FSTAB_PATH,
    VAST_KERNEL_MODULE,
    VAST_CTL_COMMAND,
    # Mount points
    VAST_MOUNT_POINTS,
    POWERSCALE_MOUNT_POINTS,
    POWERVAULT_MOUNT_POINTS,
    # Network
    IB_INTERFACE,
    IB_MTU,
    IB_SUBNET,
    VAST_RDMA_PORT,
    VAST_FQDN,
    # Performance targets
    RDMA_LATENCY_TARGET_US,
    RDMA_LATENCY_P99_US,
    THROUGHPUT_TARGET_GB,
    IOPS_TARGET,
    # Mount options
    VAST_MOUNT_OPTIONS,
    POWERSCALE_MOUNT_OPTIONS,
)

from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
)

__all__ = [
    # Node functions
    "get_compute_nodes",
    "get_controller_nodes", 
    "get_login_nodes",
    "get_all_accessible_nodes",
    # Configuration
    "verify_storage_config_parsing",
    "verify_single_backend_active",
    "verify_backend_role_assignment",
    "verify_mount_options",
    "verify_fstab_generation",
    # Network
    "verify_ib_interface_config",
    "verify_ib_mtu",
    "verify_ib_ip_assignment",
    "verify_ib_link_status",
    "verify_rdma_connectivity",
    "verify_dns_resolution",
    "verify_port_reachability",
    # VAST
    "verify_vastnfs_client_install",
    "verify_vastnfs_kernel_module",
    "verify_vast_rdma_mount",
    "verify_vastnfs_ctl_status",
    "verify_vast_compute_only",
    # Mounts
    "verify_mount_point_exists",
    "verify_mount_active",
    "verify_mount_protocol",
    "verify_systemd_mount_units",
    "verify_mount_permissions",
    "verify_mount_accessibility",
    # Isolation
    "verify_scratch_isolation",
    "verify_tmp_bind_mount",
    "verify_hostname_scratch_dir",
    # Other backends
    "verify_powerscale_mounts",
    "verify_powervault_iscsi",
    "verify_powerscale_fallback",
    # Slurm
    "verify_slurm_state_persistence",
    "verify_slurm_storage_paths",
    "verify_job_logs_persistence",
    "verify_mpi_checkpoint",
    # Performance
    "measure_rdma_latency",
    "measure_throughput",
    "measure_iops",
    "measure_boot_time",
    # Error handling
    "verify_stale_handle_recovery",
    "verify_mount_retry_logic",
    "verify_error_logging",
    # Idempotency
    "verify_provisioning_idempotency",
    "verify_mount_state_consistency",
    # Node ops
    "verify_add_compute_node",
    "verify_remove_compute_node",
    # Compatibility
    "verify_rhel_compatibility",
    "verify_job_output_consistency",
    # Constants
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
    "ERROR_MESSAGES",
    "SUCCESS_MESSAGES",
    "COMPUTE_NODE_FUNCTIONAL_GROUP",
    "CONTROLLER_NODE_FUNCTIONAL_GROUP",
    "LOGIN_NODE_FUNCTIONAL_GROUP",
    "STORAGE_CONFIG_PATH",
    "VAST_MOUNT_POINTS",
    "POWERSCALE_MOUNT_POINTS",
    "IB_INTERFACE",
    "IB_MTU",
    "VAST_RDMA_PORT",
    "RDMA_LATENCY_TARGET_US",
    "THROUGHPUT_TARGET_GB",
    "IOPS_TARGET",
]
