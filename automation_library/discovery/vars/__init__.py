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
Discovery Variables Module.

Exports all discovery-related constants and configuration variables.
"""

from .discovery_vars import (
    OPENCHAMI_NODES_PATH,
    BMC_GROUP_DATA_PATH,
    OPEN_NETWORK_SPEC_PATH,
    CONTAINER_NAME,
    SSH_TIMEOUT,
    CMD_TEMPLATES,
    LOGIN_SERVICES,
    SLURM_CONTROL_SERVICES,
    FUNCTIONAL_GROUP_SLURM_CONTROL,
    FUNCTIONAL_GROUP_KUBE_CONTROL,
)
from .admin_debug_packages_vars import (
    SOFTWARE_CONFIG_PATH,
    ADMIN_DEBUG_PACKAGES_JSON,
)

__all__ = [
    "OPENCHAMI_NODES_PATH",
    "BMC_GROUP_DATA_PATH",
    "OPEN_NETWORK_SPEC_PATH",
    "CONTAINER_NAME",
    "SSH_TIMEOUT",
    "CMD_TEMPLATES",
    "LOGIN_SERVICES",
    "SLURM_CONTROL_SERVICES",
    "FUNCTIONAL_GROUP_SLURM_CONTROL",
    "FUNCTIONAL_GROUP_KUBE_CONTROL",
    # Admin debug packages
    "SOFTWARE_CONFIG_PATH",
    "ADMIN_DEBUG_PACKAGES_JSON",
]
