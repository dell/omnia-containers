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
Delete Node Verification - Messages.

This module contains all user-facing messages for delete node verification tests.
"""

from typing import Dict


# =============================================================================
# DELETE NODE TEST NAMES
# =============================================================================

DELETE_NODE_TEST_NAMES: Dict[str, str] = {
    "idrac_deleted_node_mysql": "Verify deleted iDRAC node data not in MySQL",
    "idrac_deleted_node_kafka": "Verify deleted iDRAC node data not in Kafka",
    "ldms_deleted_node_kafka": "Verify deleted LDMS node data not in Kafka",
    "idrac_deleted_node_victoria": "Verify deleted iDRAC node data not in VictoriaMetrics",
}


# =============================================================================
# DELETE NODE LOG MESSAGES
# =============================================================================

DELETE_NODE_LOG_MSGS: Dict[str, str] = {
    # Backup management
    "backup_not_found": "No PXE mapping backup found - creating baseline",
    "backup_created": "PXE mapping backup created at .backup/.pxe_mapping.csv",
    "backup_updated": "PXE mapping backup updated",
    "files_identical": "PXE mapping unchanged - no deleted nodes",

    # Delete detection
    "deleted_nodes_found": "Found {count} deleted node(s) in PXE mapping",
    "no_deleted_nodes": "No deleted nodes detected",
    "deleted_ldms_nodes": "Deleted LDMS hostnames: {hostnames}",
    "deleted_service_tags": "Deleted service tags: {tags}",
    "deleted_bmc_ips": "Deleted BMC IPs: {ips}",

    # iDRAC MySQL verification (order 1)
    "idrac_mysql_verifying": "Verifying deleted BMC IPs not in MySQL services table",
    "idrac_mysql_not_found": (
        "Deleted BMC IP '{ip}' correctly absent from MySQL"
    ),
    "idrac_mysql_found": (
        "Deleted BMC IP '{ip}' still found in MySQL services table"
    ),
    "idrac_mysql_success": (
        "All {count} deleted BMC IPs verified absent from MySQL"
    ),

    # iDRAC Kafka verification (order 2)
    "idrac_kafka_verifying": "Verifying deleted iDRAC service tags not in latest Kafka data",
    "idrac_kafka_not_found": (
        "Deleted service tag '{tag}' correctly absent from latest Kafka data"
    ),
    "idrac_kafka_found": (
        "Deleted service tag '{tag}' still found in latest Kafka data"
    ),
    "idrac_kafka_success": (
        "All {count} deleted service tags verified absent from latest Kafka data"
    ),

    # LDMS Kafka verification (order 3)
    "ldms_kafka_verifying": "Verifying deleted LDMS hostnames not in latest Kafka data",
    "ldms_kafka_not_found": (
        "Deleted LDMS hostname '{hostname}' correctly absent from latest Kafka data"
    ),
    "ldms_kafka_found": (
        "Deleted LDMS hostname '{hostname}' still found in latest Kafka data"
    ),
    "ldms_kafka_success": (
        "All {count} deleted LDMS hostnames verified absent from latest Kafka data"
    ),

    # iDRAC VictoriaMetrics verification (order 4)
    "idrac_victoria_verifying": (
        "Verifying deleted service tags not in VictoriaMetrics"
    ),
    "idrac_victoria_not_found": (
        "Deleted service tag '{tag}' correctly absent from VictoriaMetrics"
    ),
    "idrac_victoria_found": (
        "Deleted service tag '{tag}' still has metrics in VictoriaMetrics"
    ),
    "idrac_victoria_success": (
        "All {count} deleted service tags verified absent from VictoriaMetrics"
    ),
}


# =============================================================================
# DELETE NODE ASSERTION MESSAGES
# =============================================================================

DELETE_NODE_ASSERT_MSGS: Dict[str, str] = {
    "idrac_mysql_still_present": (
        "Deleted BMC IPs still found in MySQL services table.\n"
        "Still present: {found}\n"
        "Verified absent: {not_found}\n"
        "These BMC IPs were removed from PXE mapping but remain in MySQL."
    ),
    "idrac_kafka_still_present": (
        "Deleted iDRAC service tags still have data in latest Kafka topic.\n"
        "Still present: {found}\n"
        "Verified absent: {not_found}\n"
        "These service tags were removed from PXE mapping but data persists in Kafka."
    ),
    "ldms_kafka_still_present": (
        "Deleted LDMS hostnames still have data in latest Kafka topic.\n"
        "Still present: {found}\n"
        "Verified absent: {not_found}\n"
        "These hostnames were removed from PXE mapping but data persists in Kafka."
    ),
    "idrac_victoria_still_present": (
        "Deleted service tags still have metrics in VictoriaMetrics.\n"
        "Still present: {found}\n"
        "Verified absent: {not_found}\n"
        "These service tags were removed from PXE mapping but metrics persist."
    ),
    "no_deleted_ldms_nodes": (
        "No deleted LDMS nodes found.\n"
        "PXE mapping has changed but no LDMS functional group entries were removed."
    ),
    "no_deleted_idrac_nodes": (
        "No deleted nodes with BMC IPs or service tags found.\n"
        "PXE mapping has changed but no entries with BMC data were removed."
    ),
}
