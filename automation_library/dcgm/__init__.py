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
DCGM Automation Module

Verification functions for NVIDIA DCGM GPU Telemetry deployment on Omnia
GPU nodes (slurm_node_x86_64 with NVIDIA GPUs). Covers:
  - CUDA validation and toolkit installation with atomic lock
  - DCGM package installation and daemon management
  - GPU discovery and enumeration (single and multi-GPU)
  - nvidia_peer_mem.ko kernel module installation
  - Idempotency, compatibility, and error-handling scenarios

Spec: TSPEC-DCGM-2026-001 v1.0.0
"""

from .functions import (
    get_gpu_nodes,
    get_login_compiler_nodes,
    verify_cuda_validation,
    verify_dcgm_metrics_dmon,
    verify_cuda_atomic_lock_installation,
    verify_multi_login_compiler_atomic_lock,
    verify_multi_gpu_nodes_no_login_compiler,
    verify_dcgm_package_installed,
    verify_dcgm_daemon_running,
    verify_gpu_discovery,
    verify_multi_gpu_discovery,
    verify_cuda_login_compiler_install,
    verify_cuda_compute_node_install,
    verify_toolkit_nfs_shared_storage,
    verify_nvidia_peer_mem_installed,
    verify_nvidia_peer_mem_all_gpu_nodes,
    verify_dcgm_role_idempotency,
    verify_rhel_compatibility,
    verify_cuda_version_compatibility,
    verify_cuda_prerequisite_blocks_deployment,
    verify_daemon_crash_recovery,
    verify_daemon_socket_error,
)
from .vars import (
    GPU_NODE_FUNCTIONAL_GROUP,
    DCGM_SERVICE_NAME,
    CUDA_INSTALL_PATH,
    CUDA_MIN_MAJOR_VERSION,
)
from .messages import TEST_NAMES, TEST_LOG_MSGS, TEST_ASSERT_MSGS

__all__ = [
    "get_gpu_nodes",
    "get_login_compiler_nodes",
    "verify_cuda_validation",
    "verify_dcgm_metrics_dmon",
    "verify_cuda_atomic_lock_installation",
    "verify_multi_login_compiler_atomic_lock",
    "verify_multi_gpu_nodes_no_login_compiler",
    "verify_dcgm_package_installed",
    "verify_dcgm_daemon_running",
    "verify_gpu_discovery",
    "verify_multi_gpu_discovery",
    "verify_cuda_login_compiler_install",
    "verify_cuda_compute_node_install",
    "verify_toolkit_nfs_shared_storage",
    "verify_nvidia_peer_mem_installed",
    "verify_nvidia_peer_mem_all_gpu_nodes",
    "verify_dcgm_role_idempotency",
    "verify_rhel_compatibility",
    "verify_cuda_version_compatibility",
    "verify_cuda_prerequisite_blocks_deployment",
    "verify_daemon_crash_recovery",
    "verify_daemon_socket_error",
    "GPU_NODE_FUNCTIONAL_GROUP",
    "DCGM_SERVICE_NAME",
    "CUDA_INSTALL_PATH",
    "CUDA_MIN_MAJOR_VERSION",
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
]
