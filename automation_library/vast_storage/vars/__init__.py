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
VAST Storage automation variables module.
"""

from .vast_storage_vars import *

__all__ = [
    # Node functional groups
    "COMPUTE_NODE_FUNCTIONAL_GROUP",
    "CONTROLLER_NODE_FUNCTIONAL_GROUP",
    "LOGIN_NODE_FUNCTIONAL_GROUP",
    "LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP",
    # Configuration paths
    "STORAGE_CONFIG_PATH",
    "PXE_MAPPING_PATH",
    "ANSIBLE_INVENTORY_PATH",
    "FSTAB_PATH",
    "CLOUD_INIT_LOG_PATH",
    # VAST specific paths
    "VAST_CLIENT_RPM_PATH",
    "VAST_KERNEL_MODULE",
    "VAST_CTL_COMMAND",
    "VAST_MOUNT_UNIT_PREFIX",
    # Storage backend paths
    "POWERSCALE_NFS_EXPORT",
    "POWERVAULT_ISCSI_TARGET",
    # Mount points
    "VAST_MOUNT_POINTS",
    "POWERSCALE_MOUNT_POINTS",
    "POWERVAULT_MOUNT_POINTS",
    "SHARED_NAMESPACE_DIRS",
    "NODE_SPECIFIC_SCRATCH_PATH",
    "TMP_BIND_MOUNT_PATH",
    # Network configuration
    "IB_INTERFACE",
    "IB_MTU",
    "IB_SUBNET",
    "VAST_RDMA_PORT",
    "NFS_TCP_PORT",
    "ISCSI_PORT",
    # DNS configuration
    "VAST_FQDN",
    "IB_DNS_SERVER",
    # Mount options
    "VAST_MOUNT_OPTIONS",
    "POWERSCALE_MOUNT_OPTIONS",
    "POWERVAULT_MOUNT_OPTIONS",
    # Performance targets
    "RDMA_LATENCY_TARGET_US",
    "RDMA_LATENCY_P99_US",
    "THROUGHPUT_TARGET_GB",
    "IOPS_TARGET",
    "BOOT_TIME_TOLERANCE_PERCENT",
    # Retry configuration
    "MOUNT_RETRY_COUNT",
    "MOUNT_RETRY_DELAYS",
    # Test data paths
    "TEST_DATASET_PATH",
    "CHECKPOINT_DATA_SIZE_GB",
    "RANDOM_IO_SIZE_GB",
    "SEQUENTIAL_STREAM_SIZE_GB",
    "METADATA_OPS_FILE_COUNT",
]
