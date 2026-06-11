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
DCGM Automation - Configuration Variables.

Constants, paths, and command templates for DCGM GPU telemetry tests.
"""

from typing import Dict, Any

from ...core.vars import (
    SLURM_NODE_FUNCTIONAL_GROUP as _SLURM_NODE_FG,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP as _LOGIN_COMPILER_FG,
    OMNIA_CORE_CONTAINER as _CONTAINER,
)


# =============================================================================
# Functional Groups
# =============================================================================

GPU_NODE_FUNCTIONAL_GROUP = _SLURM_NODE_FG          # slurm_node_x86_64
LOGIN_COMPILER_FUNCTIONAL_GROUP = _LOGIN_COMPILER_FG  # login_compiler_node_x86_64
CONTAINER_NAME = _CONTAINER                           # omnia_core

# =============================================================================
# DCGM Package & Service
# =============================================================================

DCGM_PACKAGE_NAME = "datacenter-gpu-manager"
DCGM_SERVICE_NAME = "nvidia-dcgm.service"
DCGM_SOCKET_PATH = "/var/run/dcgm/dcgm.sock"
DCGM_BINARIES = ["/usr/bin/dcgmi"]

# =============================================================================
# CUDA Paths & Config
# =============================================================================

CUDA_INSTALL_PATH = "/hpc_tools/cuda"
CUDA_PROFILE_SCRIPT = "/etc/profile.d/cuda.sh"
CUDA_ATOMIC_LOCK_FILE = "/tmp/cuda_install.lock"
CUDA_MIN_MAJOR_VERSION = 13

# =============================================================================
# RHEL Version Requirement
# =============================================================================

REQUIRED_RHEL_MAJOR = 10

# =============================================================================
# Retry / Timeout Settings
# =============================================================================

SERVICE_START_TIMEOUT = 30       # seconds to wait after service start
SERVICE_POLL_INTERVAL = 5        # seconds between service status polls
DAEMON_RESTART_WAIT = 15         # seconds after systemctl restart
MAX_GPU_DISCOVERY_RETRIES = 3
GPU_DISCOVERY_RETRY_INTERVAL = 10

# =============================================================================
# Command Templates
# =============================================================================

CMD_TEMPLATES: Dict[str, str] = {
    "ssh_opts": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",

    # nvidia-smi
    "nvidia_smi": "nvidia-smi",
    "nvidia_smi_query": "nvidia-smi --query-gpu=index,name,uuid --format=csv,noheader",
    "nvidia_smi_count": "nvidia-smi -L | wc -l",

    # CUDA toolkit
    "nvcc_version": "nvcc --version",
    "cuda_path_check": "ls -d {cuda_path}/bin {cuda_path}/lib64 {cuda_path}/include",
    "cuda_profile_check": "cat {profile_script}",
    "cuda_lock_check": "ls -la {lock_file}",
    "cuda_rpm_check": "rpm -qa | grep cuda",

    # DCGM package
    "dcgm_install": "dnf install -y datacenter-gpu-manager",
    "dcgm_rpm_check": "rpm -qi datacenter-gpu-manager",
    "dcgm_binaries_check": "ls -la /usr/bin/dcgmi",
    "dcgm_service_file_check": "ls -la /usr/lib/systemd/system/nvidia-dcgm.service",

    # Systemd service
    "service_enable": "systemctl enable {service}",
    "service_start": "systemctl start {service}",
    "service_restart": "systemctl restart {service}",
    "service_status": "systemctl status {service} --no-pager",
    "service_is_active": "systemctl is-active {service}",
    "service_logs": "journalctl -u {service} -n 50 --no-pager",

    # GPU discovery
    "dcgmi_discovery": "dcgmi discovery -l",
    "dcgmi_discovery_verbose": "dcgmi discovery -l",

    # OS version
    "os_release": "cat /etc/redhat-release",

    # NFS mount
    "hpc_tools_mount": "mount | grep /hpc_tools",
    "nvcc_from_nfs": "nvcc --version",

    # Ansible playbook (run inside container)
    "ansible_gpu_playbook": (
        "ansible-playbook -i /omnia/inventory /omnia/utils/hpc_tools/gpu.yml "
        "--limit {node} -v"
    ),
    "ansible_idempotency_check": (
        "ansible-playbook -i /omnia/inventory /omnia/utils/hpc_tools/gpu.yml "
        "--limit {node} -v 2>&1 | grep -E 'changed=|failed='"
    ),
}
