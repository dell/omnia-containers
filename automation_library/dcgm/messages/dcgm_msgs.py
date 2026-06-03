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
DCGM Automation - Messages.

All user-facing test names, log messages, and assertion messages for DCGM tests.
"""

from typing import Dict


# =============================================================================
# TEST NAMES  (shown in test report header)
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    # Functional
    "cuda_validation":              "TC-F01: CUDA Validation",
    "cuda_atomic_lock":             "TC-F02: CUDA Toolkit Installation with Atomic Lock",
    "dcgm_package_install":         "TC-F03: DCGM Package Installation",
    "dcgm_daemon_startup":          "TC-F04: DCGM Daemon Startup",
    "gpu_discovery":                "TC-F05: GPU Discovery and Enumeration",
    "add_gpu_node":                 "TC-F06: Add GPU Node - DCGM Auto-Installation",
    "gpu_metrics_monitoring":       "TC-F07: GPU Job Execution with Metrics Monitoring",
    "cuda_login_compiler":          "TC-F08: CUDA Toolkit Install - Login Compiler Node Available",
    "cuda_compute_no_login":        "TC-F09: CUDA Toolkit and Driver Install - Compute Node (No Login Compiler)",
    "multi_gpu_discovery":          "TC-F10: Multi-GPU Discovery (4x GPUs)",
    "multi_login_compiler_lock":    "TC-F11: Multiple Login Compiler Nodes - Atomic Lock",
    "multi_gpu_nodes_no_login":     "TC-F12: Multiple GPU Nodes Without Login Compiler",
    "add_node_driver_only":         "TC-F13: Add GPU Node - Only Driver Installation",
    "atomic_lock_timeout":          "TC-F14: Atomic Lock Timeout - Concurrent Installation",
    "toolkit_failure_lock_release": "TC-F15: Toolkit Installation Failure - Lock Release",
    "toolkit_nfs_validation":       "TC-F16: Toolkit NFS Shared Storage Validation",
    "nvidia_peer_mem":              "TC-F18: nvidia_peer_mem.ko Module Installation",
    # Idempotency
    "dcgm_idempotency":             "TC-I01: DCGM Installation Role Idempotency",
    # Compatibility
    "rhel_compatibility":           "TC-C01: RHEL 10.x OS Compatibility",
    "cuda_compatibility":           "TC-C02: CUDA 13.x Compatibility",
    # Negative / Error
    "cuda_not_present":             "TC-E01: CUDA Not Present - Deployment Blocked",
    "daemon_crash_recovery":        "TC-E02: DCGM Daemon Crash and Auto-Recovery",
    "socket_inaccessible":          "TC-E03: DCGM Daemon Socket Inaccessible",
    "package_install_failure":      "TC-E04: DCGM Package Installation Failure",
}


# =============================================================================
# LOG MESSAGES  (shown during test execution)
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # GPU node lookup
    "no_gpu_nodes":             "No GPU nodes (slurm_node_x86_64) found in PXE mapping",
    "gpu_node_found":           "GPU node found: {admin_ip}",

    # CUDA validation
    "nvidia_smi_ok":            "nvidia-smi executed successfully on GPU node {ip}",
    "nvidia_smi_fail":          "nvidia-smi failed on GPU node {ip}",
    "nvcc_version_ok":          "CUDA toolkit {version} found at {path}",
    "nvcc_version_fail":        "CUDA toolkit not found or version < 13.x at {path}",
    "cuda_skip_non_gpu":        "CUDA installation correctly skipped on non-GPU node {ip}",
    "cuda_env_vars_ok":         "CUDA environment variables set in {script}",

    # Atomic lock
    "lock_file_created":        "Atomic lock file created at {lock_path}",
    "lock_file_released":       "Atomic lock file released after installation",
    "lock_only_one_installer":  "Only one node acquired atomic lock and installed toolkit",
    "lock_others_skipped":      "Other nodes correctly skipped toolkit installation",

    # DCGM package
    "dcgm_pkg_installed":       "datacenter-gpu-manager installed on {ip}",
    "dcgm_pkg_not_found":       "datacenter-gpu-manager not found on {ip}",
    "dcgm_binaries_ok":         "DCGM binaries present at /usr/bin/dcgmi",
    "dcgm_service_file_ok":     "nvidia-dcgm.service file present",

    # Daemon
    "daemon_running":           "nvidia-dcgm.service is active (running) on {ip}",
    "daemon_not_running":       "nvidia-dcgm.service is not running on {ip}",
    "daemon_enabled":           "nvidia-dcgm.service enabled for auto-start",
    "daemon_restarted":         "nvidia-dcgm.service restarted successfully after crash",

    # GPU discovery
    "gpus_discovered":          "dcgmi discovery found {count} GPU(s) on {ip}",
    "gpu_uuids_unique":         "All GPU UUIDs are unique",
    "gpu_metadata_complete":    "GPU metadata complete (model, UUID present)",
    "gpu_count_mismatch":       "GPU count mismatch: expected {expected}, found {actual}",

    # nvidia_peer_mem
    "peer_mem_installed":       "nvidia_peer_mem package installed on {ip}",
    "peer_mem_loaded":          "nvidia_peer_mem kernel module loaded on {ip}",
    "peer_mem_autoload_ok":     "nvidia_peer_mem configured for auto-load at boot",
    "peer_mem_not_loaded":      "nvidia_peer_mem module not loaded on {ip}",
    "peer_mem_all_nodes_ok":    "nvidia_peer_mem loaded on all {count} GPU node(s)",

    # NFS toolkit
    "nfs_mount_ok":             "/hpc_tools mounted via NFS on {ip}",
    "cuda_nfs_accessible":      "CUDA toolkit accessible from {ip} via NFS",

    # Idempotency
    "idempotency_no_changes":   "Second Ansible run produced 0 changes - idempotency confirmed",
    "idempotency_changes_found":"Second Ansible run showed changes - idempotency FAILED",

    # Compatibility
    "rhel_version_ok":          "OS is RHEL {version} - compatible",
    "rhel_version_fail":        "OS version {version} does not meet RHEL 10.x requirement",
    "cuda_version_ok":          "CUDA {version} meets minimum version requirement (13.x)",
    "cuda_version_fail":        "CUDA {version} is below minimum required version (13.x)",

    # Negative
    "cuda_prerequisite_blocked": "DCGM deployment correctly blocked - CUDA prerequisite not met",
    "crash_recovery_ok":        "nvidia-dcgm.service auto-recovered after simulated crash",
    "socket_error_handled":     "DCGM socket error handled gracefully",
    "install_failure_logged":   "DCGM package installation failure logged correctly",
}


# =============================================================================
# ASSERTION MESSAGES  (shown on test failure)
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "no_gpu_nodes": (
        "No GPU nodes found in PXE mapping under functional group slurm_node_x86_64.\n"
        "Ensure GPU nodes are provisioned and listed in pxe_mapping_file.csv."
    ),
    "nvidia_smi_failed": (
        "nvidia-smi failed on GPU node {ip} (rc={rc}).\n"
        "Expected: NVIDIA driver info and GPU details.\n"
        "Actual: {stderr}\n"
        "Fix: Ensure NVIDIA drivers are installed: dnf install -y nvidia-driver"
    ),
    "nvcc_version_failed": (
        "CUDA toolkit 13.x+ not found on {ip}.\n"
        "Expected: nvcc shows 'release 13.x' and /hpc_tools/cuda exists.\n"
        "Actual: {output}\n"
        "Fix: Verify CUDA toolkit installation in /hpc_tools/cuda"
    ),
    "dcgm_not_installed": (
        "datacenter-gpu-manager package not installed on {ip}.\n"
        "Expected: rpm -qi datacenter-gpu-manager returns package info.\n"
        "Fix: Run dnf install -y datacenter-gpu-manager"
    ),
    "daemon_not_running": (
        "nvidia-dcgm.service is not active on {ip}.\n"
        "Expected: systemctl is-active nvidia-dcgm.service returns 'active'.\n"
        "Actual: {status}\n"
        "Debug: journalctl -u nvidia-dcgm.service -n 50 --no-pager"
    ),
    "gpu_discovery_failed": (
        "dcgmi discovery returned no GPUs on {ip}.\n"
        "Expected: At least one GPU listed with UUID and device name.\n"
        "Actual: {output}\n"
        "Debug: Ensure nvidia-dcgm.service is running: systemctl status nvidia-dcgm.service"
    ),
    "gpu_count_mismatch": (
        "GPU count mismatch on {ip}.\n"
        "Expected: {expected} GPU(s).\n"
        "Actual: {actual} GPU(s).\n"
        "Debug: nvidia-smi and dcgmi discovery -l"
    ),
    "peer_mem_not_loaded": (
        "nvidia_peer_mem module not loaded on {ip}.\n"
        "Expected: lsmod | grep nvidia_peer_mem returns module entry.\n"
        "Fix: modprobe nvidia_peer_mem  or check /etc/modules-load.d/nvidia_peer_mem.conf"
    ),
    "peer_mem_no_autoload": (
        "nvidia_peer_mem not configured for auto-load on {ip}.\n"
        "Expected: /etc/modules-load.d/nvidia_peer_mem.conf contains 'nvidia_peer_mem'.\n"
        "Fix: echo 'nvidia_peer_mem' > /etc/modules-load.d/nvidia_peer_mem.conf"
    ),
    "cuda_nfs_not_accessible": (
        "CUDA toolkit not accessible from {ip} via NFS.\n"
        "Expected: nvcc --version works from NFS mount /hpc_tools/cuda.\n"
        "Fix: Verify /hpc_tools NFS mount: mount | grep /hpc_tools"
    ),
    "idempotency_failed": (
        "Ansible GPU playbook is not idempotent.\n"
        "Expected: changed=0 on second run.\n"
        "Actual: {changes}\n"
        "Fix: Review Ansible tasks for non-idempotent operations."
    ),
    "rhel_version_mismatch": (
        "RHEL version requirement not met on {ip}.\n"
        "Expected: RHEL 10.x\n"
        "Actual: {version}\n"
    ),
    "cuda_version_below_minimum": (
        "CUDA version below minimum requirement on {ip}.\n"
        "Expected: CUDA 13.x+\n"
        "Actual: {version}\n"
        "Fix: Upgrade CUDA toolkit to 13.x+"
    ),
    "cuda_prerequisite_not_blocked": (
        "DCGM deployment was NOT blocked despite missing CUDA prerequisite on {ip}.\n"
        "Expected: Ansible playbook fails with CUDA prerequisite error.\n"
        "Fix: Ensure CUDA prerequisite check (BL-001) is enforced in Ansible role."
    ),
    "daemon_not_recovered": (
        "nvidia-dcgm.service did NOT auto-recover after crash on {ip}.\n"
        "Expected: Service restarts automatically (Restart=on-failure in service file).\n"
        "Debug: systemctl cat nvidia-dcgm.service | grep Restart"
    ),
    "socket_error_not_handled": (
        "DCGM socket error not handled correctly on {ip}.\n"
        "Expected: dcgmi returns clear socket error message.\n"
        "Actual: {output}"
    ),
}
