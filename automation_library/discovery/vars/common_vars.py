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
Discovery Module - Common Variables.

SSH options and common constants used across discovery tests.
"""

from automation_library.core import (
    OMNIA_CORE_CONTAINER as _CORE_CONTAINER,
    OIM_SHARED_PATH as _OIM_SHARED_PATH,
)

# =============================================================================
# SSH OPTIONS (for handling changed host keys)
# =============================================================================

SSH_OPTS = (
    "-o StrictHostKeyChecking=no "
    "-o UserKnownHostsFile=/dev/null "
    "-o BatchMode=yes "
    "-o ConnectTimeout=10"
)

# =============================================================================
# CONTAINER NAME - from core vars
# =============================================================================

CONTAINER_NAME = _CORE_CONTAINER

# =============================================================================
# REACHABILITY CHECK CONFIGURATION (for subsequent tests)
# =============================================================================

# Number of retries for unreachable nodes in subsequent tests
DISCOVERY_REACHABILITY_RETRY = 2

# Seconds between reachability retry attempts
DISCOVERY_REACHABILITY_INTERVAL = 5

# =============================================================================
# CLOUD-INIT RETRY CONFIGURATION
# =============================================================================

# Maximum number of retries per node when cloud-init is still running
CLOUDINIT_RETRY_LIMIT = 50

# Seconds to wait between retry attempts
CLOUDINIT_RETRY_INTERVAL = 10

# Statuses that indicate cloud-init completed successfully (no retry needed)
CLOUDINIT_PASSED_STATUSES = ["done"]

# Statuses that indicate cloud-init is still in progress (should retry)
CLOUDINIT_RETRY_STATUSES = ["running", "not started"]

# =============================================================================
# IMAGE CONFIG YAML DIRECTORY
# Same path used by build_image_x86_64 playbook (build_image_vars.py).
# Contains per-functional-group YAML files with 'packages' list.
# e.g. rhel-slurm_control_node_x86_64_<uuid>-image-build-10.0.yaml
# =============================================================================

IMAGE_CONFIG_YAML_DIR = f"{_OIM_SHARED_PATH}/openchami/workdir/images"
