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

from automation_library.core.vars import OMNIA_CORE_CONTAINER as _CORE_CONTAINER

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
