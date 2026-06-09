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
Discovery Module.

This module provides functions for verifying discovery playbook output:
1. BMC PXE mapping file generation with timestamps
2. Column validation against supported columns
3. Functional group validation against Omnia-supported groups
4. IP correlation validation (ADMIN_IP/IB_IP <-> BMC_IP) based on network_spec.yml
5. Parent service tag validation for slurm_node groups
6. OME custom group verification against PXE mapping
Organized by functionality: functions, variables, and messages.
"""

from .functions import (
    get_latest_bmc_pxe_mapping_file,
    read_bmc_pxe_mapping_raw,
    get_network_spec_subnets,
    verify_pxe_mapping_columns,
    verify_functional_groups_supported,
    verify_ip_correlation,
    verify_parent_service_tag,
    get_pxe_mapping_bmc_ips_by_group,
    clear_ome_cache,
    get_ome_session,
    get_ome_static_groups,
    get_ome_group_device_ips,
    get_ome_all_devices,
    get_ome_device_inventory,
    get_ome_device_details_by_service_tag,
    get_ome_devices_without_static_group,
)

from .vars import (
    BMC_PXE_MAPPING_PATH,
    BMC_PXE_MAPPING_PREFIX,
    SUPPORTED_COLUMNS,
    SUPPORTED_FUNCTIONAL_GROUPS,
    GROUPS_REQUIRING_PARENT_SERVICE_TAG,
    VALID_PARENT_FUNCTIONAL_GROUPS,
    OME_API_TIMEOUT,
    OME_SESSION_ENDPOINT,
    OME_GROUPS_ENDPOINT,
    OME_GROUP_DEVICES_ENDPOINT,
    OME_CUSTOM_GROUP_TYPE,
    NETWORK_SPEC_FILE,
)

from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)

__all__ = [
    # PXE mapping functions
    "get_latest_bmc_pxe_mapping_file",
    "read_bmc_pxe_mapping_raw",
    "get_network_spec_subnets",
    "verify_pxe_mapping_columns",
    "verify_functional_groups_supported",
    "verify_ip_correlation",
    "verify_parent_service_tag",
    "get_pxe_mapping_bmc_ips_by_group",
    # OME functions
    "clear_ome_cache",
    "get_ome_session",
    "get_ome_static_groups",
    "get_ome_group_device_ips",
    "get_ome_all_devices",
    "get_ome_device_inventory",
    "get_ome_device_details_by_service_tag",
    "get_ome_devices_without_static_group",
    # Variables
    "BMC_PXE_MAPPING_PATH",
    "BMC_PXE_MAPPING_PREFIX",
    "SUPPORTED_COLUMNS",
    "SUPPORTED_FUNCTIONAL_GROUPS",
    "GROUPS_REQUIRING_PARENT_SERVICE_TAG",
    "VALID_PARENT_FUNCTIONAL_GROUPS",
    "OME_API_TIMEOUT",
    "OME_SESSION_ENDPOINT",
    "OME_GROUPS_ENDPOINT",
    "OME_GROUP_DEVICES_ENDPOINT",
    "OME_CUSTOM_GROUP_TYPE",
    "NETWORK_SPEC_FILE",
    # Messages
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
    "SKIP_MSGS",
]
