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
Discovery Module Variables.

Contains constants for discovery verification.
"""

from automation_library.core import (
    INPUT_BASE_PATH,
    BMC_PXE_MAPPING_FILE_PREFIX,
    NETWORK_SPEC_FILE,
    OMNIA_SUPPORTED_FUNCTIONAL_GROUPS,
    PXE_MAPPING_REQUIRED_COLUMNS,
    SLURM_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_AARCH64_FUNCTIONAL_GROUP,
    K8S_WORKER_NODE_FUNCTIONAL_GROUP,
)

# =============================================================================
# BMC PXE MAPPING FILE SETTINGS
# =============================================================================

BMC_PXE_MAPPING_PATH = INPUT_BASE_PATH
BMC_PXE_MAPPING_PREFIX = BMC_PXE_MAPPING_FILE_PREFIX

# =============================================================================
# SUPPORTED COLUMNS AND FUNCTIONAL GROUPS (re-exported from core)
# =============================================================================

SUPPORTED_COLUMNS = PXE_MAPPING_REQUIRED_COLUMNS
SUPPORTED_FUNCTIONAL_GROUPS = OMNIA_SUPPORTED_FUNCTIONAL_GROUPS

# =============================================================================
# FUNCTIONAL GROUPS THAT REQUIRE PARENT_SERVICE_TAG
# Only slurm_node groups should have parent_service_tag populated
# =============================================================================

GROUPS_REQUIRING_PARENT_SERVICE_TAG = [
    SLURM_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_AARCH64_FUNCTIONAL_GROUP,
]

# =============================================================================
# FUNCTIONAL GROUPS THAT CAN BE PARENTS (service_kube_node)
# Parent service tags should reference service_kube_node service tags
# =============================================================================

VALID_PARENT_FUNCTIONAL_GROUPS = [
    K8S_WORKER_NODE_FUNCTIONAL_GROUP,
]

# =============================================================================
# OME API SETTINGS
# =============================================================================

OME_API_TIMEOUT = 30
OME_SESSION_ENDPOINT = "/api/SessionService/Sessions"
OME_GROUPS_ENDPOINT = "/api/GroupService/Groups"
OME_GROUP_DEVICES_ENDPOINT = "/api/GroupService/Groups({group_id})/Devices"

# OME group types - TypeId 3000 = Custom/Static groups (user-created)
OME_CUSTOM_GROUP_TYPE = 3000
