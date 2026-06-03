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

"""Discovery Module Functions."""

from .pxe_mapping_func import (
    get_latest_bmc_pxe_mapping_file,
    read_bmc_pxe_mapping_raw,
    get_network_spec_subnets,
    verify_pxe_mapping_columns,
    verify_functional_groups_supported,
    verify_ip_correlation,
    verify_parent_service_tag,
    get_pxe_mapping_bmc_ips_by_group,
)

from .ome_func import (
    clear_ome_cache,
    get_ome_session,
    get_ome_static_groups,
    get_ome_group_device_ips,
    get_ome_all_devices,
    get_ome_device_inventory,
    get_ome_device_details_by_service_tag,
    get_ome_devices_without_static_group,
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
]
