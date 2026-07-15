# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Kubernetes automation module for OMNIA test automation.

Modules:
- functions: OIMOperations class and k8s verification helpers
- vars: Constants, timeouts, paths, and command templates
- messages: Status and error message constants
"""

from .functions.k8s_func import OIMOperations, get_oim_operations

from .vars.k8s_vars import (
    DEFAULT_STORAGE_CLASS,
    EXPECTED_CONTAINER_RUNTIME,
    CONTROL_PLANE_GROUP,
    WORKER_NODE_GROUP,
    KUBELET_SERVICE,
    CRIO_SERVICE,
    CRI_O_SERVICE,
    CHRONYD_SERVICE,
    READY_STATE_MAX_RETRIES,
    READY_STATE_RETRY_DELAY_SECONDS,
)

from .messages.k8s_msgs import (
    TEST_PASSED,
    TEST_FAILED,
    TEST_SKIPPED,
    ERROR_NO_NODES_FOUND,
    ERROR_NO_CONTROL_PLANE_NODES,
)

__all__ = [
    # Main class and factory
    "OIMOperations",
    "get_oim_operations",
    # Key vars
    "DEFAULT_STORAGE_CLASS",
    "EXPECTED_CONTAINER_RUNTIME",
    "CONTROL_PLANE_GROUP",
    "WORKER_NODE_GROUP",
    "KUBELET_SERVICE",
    "CRIO_SERVICE",
    "CRI_O_SERVICE",
    "CHRONYD_SERVICE",
    "READY_STATE_MAX_RETRIES",
    "READY_STATE_RETRY_DELAY_SECONDS",
    # Key messages
    "TEST_PASSED",
    "TEST_FAILED",
    "TEST_SKIPPED",
    "ERROR_NO_NODES_FOUND",
    "ERROR_NO_CONTROL_PLANE_NODES",
]
