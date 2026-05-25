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
Discovery Module Messages.

User-facing messages for discovery verification tests.
"""

# =============================================================================
# TEST NAMES
# =============================================================================

TEST_NAMES = {
    "bmc_pxe_mapping_created": "Verify BMC PXE mapping file created with timestamp",
    "pxe_mapping_columns": "Verify PXE mapping file has required columns",
    "functional_groups_supported": "Verify all functional groups are Omnia-supported",
    "ip_correlation": "Verify IP correlation (ADMIN_IP/IB_IP <-> BMC_IP)",
    "parent_service_tag": "Verify PARENT_SERVICE_TAG rules",
    "ome_functional_groups": "Verify OME custom groups match PXE mapping",
    "ome_unassigned_devices": "Verify OME devices assigned to static groups",
    "admin_mac_validation": "Verify ADMIN_MAC matches OME first active non-iDRAC NIC",
    "ib_nic_name_validation": "Verify IB_NIC_NAME matches OME first active InfiniBand NIC",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS = {
    # BMC PXE mapping
    "bmc_pxe_mapping_found": "Found BMC PXE mapping file: {filename} (timestamp: {timestamp})",
    "bmc_pxe_mapping_not_found": "No BMC PXE mapping file found with timestamp",
    "bmc_pxe_mapping_rows": "BMC PXE mapping contains {count} rows",

    # Column validation
    "columns_valid": "All {count} required columns present",
    "columns_missing": "Missing columns: {columns}",
    "columns_extra": "Extra columns found: {columns}",

    # Functional groups
    "groups_valid": "All {count} functional groups are Omnia-supported",
    "groups_unsupported": "Unsupported functional groups: {groups}",
    "groups_found": "Found functional groups: {groups}",

    # IP correlation
    "ip_correlation_valid": "All {count} rows have valid IP correlation",
    "ip_correlation_invalid": "{count} rows have IP correlation issues",

    # Parent service tag
    "parent_tag_valid": "All {count} rows have valid PARENT_SERVICE_TAG",
    "parent_tag_invalid": "{count} rows have PARENT_SERVICE_TAG issues",

    # OME connection
    "ome_connecting": "Connecting to OME at {ip}",
    "ome_connected": "Successfully connected to OME",
    "ome_connection_failed": "Failed to connect to OME: {error}",

    # OME groups
    "ome_groups_found": "Found {count} custom groups in OME",
    "ome_group_checking": "Checking OME group: {name}",
    "ome_group_not_found": "Functional group '{name}' not found in OME custom groups",
    "ome_group_match": "Group '{name}' matches: {matched}/{total} IPs",
    "ome_group_mismatch": "Group '{name}' IP mismatch - PXE: {pxe_count}, OME: {ome_count}",

    # Verification results
    "all_groups_verified": "All {count} functional groups verified successfully",
    "groups_verification_failed": "{failed}/{total} functional groups failed verification",

    # OME unassigned devices
    "ome_all_devices_count": "Total devices in OME: {count}",
    "ome_assigned_devices_count": "Devices assigned to static groups: {count}",
    "ome_unassigned_devices_count": "Devices NOT assigned to any static group: {count}",
    "ome_unassigned_default_group": "These devices will get default functional group: slurm_node_aarch64",
}

# =============================================================================
# ASSERTION MESSAGES
# =============================================================================

TEST_ASSERT_MSGS = {
    "bmc_pxe_mapping_not_created": (
        "BMC PXE mapping file with timestamp not found.\n"
        "Expected: bmc_pxe_mapping_file_<timestamp>.csv in {path}\n"
        "Discovery playbook may not have run successfully."
    ),
    "columns_missing": (
        "PXE mapping file missing required columns.\n"
        "Missing: {missing}\n"
        "Present: {present}\n"
        "Discovery playbook may have generated incomplete output."
    ),
    "unsupported_functional_groups": (
        "PXE mapping contains unsupported functional groups.\n"
        "Unsupported: {unsupported}\n"
        "Supported groups: {supported}\n"
        "Check discovery configuration or OME group names."
    ),
    "ip_correlation_failed": (
        "IP correlation validation failed.\n"
        "Invalid rows: {count}\n"
        "Example: {example}\n"
        "ADMIN_IP should be admin_subnet[0:2] + bmc_ip[2:4]"
    ),
    "parent_service_tag_failed": (
        "PARENT_SERVICE_TAG validation failed.\n"
        "Invalid rows: {count}\n"
        "Example: {example}\n"
        "Only slurm_node groups should have PARENT_SERVICE_TAG referencing service_kube_node."
    ),
    "ome_connection_failed": (
        "Failed to connect to OME at {ip}.\n"
        "Error: {error}\n"
        "Check OME IP and credentials in discovery_config.yml and omnia_config_credentials.yml"
    ),
    "ome_group_not_found": (
        "Functional group '{name}' not found in OME custom groups.\n"
        "Available OME groups: {available}\n"
        "Ensure the group exists in OME under Custom Groups."
    ),
    "ome_group_ip_mismatch": (
        "IP mismatch for functional group '{name}'.\n"
        "PXE mapping BMC IPs: {pxe_ips}\n"
        "OME group device IPs: {ome_ips}\n"
        "Missing in OME: {missing}\n"
        "Extra in OME: {extra}"
    ),
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================

SKIP_MSGS = {
    "bmc_discovery_disabled": "BMC discovery not enabled (enable_bmc_discovery: false)",
    "no_bmc_pxe_mapping": "No BMC PXE mapping file found",
    "no_rows_in_mapping": "PXE mapping file has no data rows",
    "ome_credentials_missing": "OME credentials not found in omnia_config_credentials.yml",
}
