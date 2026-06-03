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

"""DCGM vars package."""

from .dcgm_vars import (
    GPU_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_FUNCTIONAL_GROUP,
    CONTAINER_NAME,
    DCGM_PACKAGE_NAME,
    DCGM_SERVICE_NAME,
    DCGM_SOCKET_PATH,
    DCGM_BINARIES,
    CUDA_INSTALL_PATH,
    CUDA_PROFILE_SCRIPT,
    CUDA_ATOMIC_LOCK_FILE,
    CUDA_MIN_MAJOR_VERSION,
    NVIDIA_PEER_MEM_MODULE,
    NVIDIA_PEER_MEM_AUTOLOAD_CONF,
    REQUIRED_RHEL_MAJOR,
    SERVICE_START_TIMEOUT,
    DAEMON_RESTART_WAIT,
    CMD_TEMPLATES,
)

__all__ = [
    "GPU_NODE_FUNCTIONAL_GROUP",
    "LOGIN_COMPILER_FUNCTIONAL_GROUP",
    "CONTAINER_NAME",
    "DCGM_PACKAGE_NAME",
    "DCGM_SERVICE_NAME",
    "DCGM_SOCKET_PATH",
    "DCGM_BINARIES",
    "CUDA_INSTALL_PATH",
    "CUDA_PROFILE_SCRIPT",
    "CUDA_ATOMIC_LOCK_FILE",
    "CUDA_MIN_MAJOR_VERSION",
    "NVIDIA_PEER_MEM_MODULE",
    "NVIDIA_PEER_MEM_AUTOLOAD_CONF",
    "REQUIRED_RHEL_MAJOR",
    "SERVICE_START_TIMEOUT",
    "DAEMON_RESTART_WAIT",
    "CMD_TEMPLATES",
]
