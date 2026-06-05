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
Delete Node Verification Test Cases.

This module verifies that nodes removed from the PXE mapping file
no longer have data in telemetry data stores.

Uses a local backup of the PXE mapping file (.backup/.pxe_mapping.csv)
to detect deleted nodes by comparing with the current container version.

Test cases (ordered: MySQL -> iDRAC Kafka -> LDMS Kafka -> VictoriaMetrics):
1. Verify deleted iDRAC node BMC IPs not in MySQL services table
2. Verify deleted iDRAC node data not in latest Kafka idrac topic
3. Verify deleted LDMS node data not in latest Kafka ldms topic
4. Verify deleted iDRAC node data not in VictoriaMetrics

All tests skip if:
- No backup file exists (first run - baseline is created)
- PXE mapping file is unchanged (no deleted nodes)
- The respective telemetry feature is not enabled
"""

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.messages.delete_node_msgs import (
    DELETE_NODE_TEST_NAMES,
    DELETE_NODE_LOG_MSGS,
    DELETE_NODE_ASSERT_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    get_admin_ip,
    skip_if_kafka_not_enabled,
    skip_if_ldms_not_enabled,
    skip_if_victoria_not_enabled,
    is_idrac_telemetry_enabled,
)
from automation_library.telemetry.functions.delete_node_func import (
    get_deleted_nodes_cached,
    get_deleted_ldms_hostnames,
    get_deleted_service_tags,
    get_deleted_bmc_ips,
    update_pxe_backup,
    skip_if_no_deleted_nodes,
    verify_ldms_deleted_node_in_kafka,
    verify_idrac_deleted_node_in_kafka,
    verify_idrac_deleted_node_in_mysql,
    verify_idrac_deleted_node_in_victoria,
)


# =============================================================================
# TEST CASE 1: iDRAC Deleted Node Data in MySQL (order 21)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(21)
def test_idrac_deleted_node_data_in_mysql(host):
    """
    Verify deleted node BMC IPs do NOT appear in MySQL services table
    across all idrac-telemetry pods.

    Skips if:
    - No backup exists (first run)
    - PXE mapping unchanged
    - iDRAC telemetry not enabled
    - No nodes with BMC IPs were deleted
    """
    log = TestLogger(
        DELETE_NODE_TEST_NAMES["idrac_deleted_node_mysql"]
    )

    deleted_nodes_info = get_deleted_nodes_cached(host)
    skip_if_no_deleted_nodes(deleted_nodes_info, log)

    if not is_idrac_telemetry_enabled(host):
        log.skipped(
            "iDRAC telemetry not enabled",
            "Test skipped - iDRAC source not enabled"
        )
        pytest.skip("iDRAC telemetry not enabled")

    admin_ip = get_admin_ip(host, log)
    deleted_entries = deleted_nodes_info.get("deleted_entries", [])

    # Get deleted BMC IPs
    deleted_ips = get_deleted_bmc_ips(deleted_entries)

    if not deleted_ips:
        log.skipped(
            DELETE_NODE_ASSERT_MSGS["no_deleted_idrac_nodes"],
            "No entries with BMC IPs were removed"
        )
        pytest.skip("No deleted BMC IPs found")

    log.check(DELETE_NODE_LOG_MSGS["idrac_mysql_verifying"])
    log.check(DELETE_NODE_LOG_MSGS["deleted_bmc_ips"].format(ips=deleted_ips))

    # Verify deleted BMC IPs not in MySQL
    result = verify_idrac_deleted_node_in_mysql(
        host, admin_ip, deleted_ips
    )

    if result.get("error") and not result.get("pod_results"):
        log.failed("Failed to verify deleted nodes in MySQL", result["error"])
        assert False, result["error"]

    # Build details
    details_lines = [
        f"Deleted BMC IPs: {deleted_ips}",
        "",
        "MySQL verification per pod:",
    ]

    for pr in result.get("pod_results", []):
        pod = pr["pod_name"]
        found = pr["found_deleted_ips"]
        not_found = pr["not_found_deleted_ips"]
        if found:
            details_lines.append(f"  ✗ {pod}: FOUND deleted IPs {found}")
        else:
            details_lines.append(
                f"  ✓ {pod}: No deleted IPs found (correct)"
            )

    details_lines.append("")
    details_lines.append("Overall BMC IP verification:")
    for ip in deleted_ips:
        if ip in result.get("found_in_mysql", []):
            details_lines.append(
                f"  ✗ {ip}: FOUND in MySQL (should be absent)"
            )
        else:
            details_lines.append(
                f"  ✓ {ip}: NOT found in MySQL (correctly removed)"
            )

    details = "\n".join(details_lines)

    if result["success"]:
        count = len(result.get("not_found_in_mysql", []))
        log.passed(
            DELETE_NODE_LOG_MSGS["idrac_mysql_success"].format(count=count),
            details
        )
    else:
        log.failed("Deleted BMC IPs still in MySQL", details)
        assert False, DELETE_NODE_ASSERT_MSGS["idrac_mysql_still_present"].format(
            found=result.get("found_in_mysql", []),
            not_found=result.get("not_found_in_mysql", [])
        )


# =============================================================================
# TEST CASE 2: iDRAC Deleted Node Data in Kafka (order 22)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(22)
def test_idrac_deleted_node_data_in_kafka(host):
    """
    Verify deleted iDRAC node service tags do NOT appear in the latest
    Kafka idrac topic data.

    Skips if:
    - No backup exists (first run)
    - PXE mapping unchanged
    - Kafka not enabled
    - iDRAC telemetry not enabled
    - No nodes with service tags were deleted
    """
    log = TestLogger(
        DELETE_NODE_TEST_NAMES["idrac_deleted_node_kafka"]
    )

    deleted_nodes_info = get_deleted_nodes_cached(host)
    skip_if_no_deleted_nodes(deleted_nodes_info, log)
    skip_if_kafka_not_enabled(host, log)

    if not is_idrac_telemetry_enabled(host):
        log.skipped(
            "iDRAC telemetry not enabled",
            "Test skipped - iDRAC source not enabled"
        )
        pytest.skip("iDRAC telemetry not enabled")

    admin_ip = get_admin_ip(host, log)
    deleted_entries = deleted_nodes_info.get("deleted_entries", [])

    # Get deleted service tags
    deleted_tags = get_deleted_service_tags(deleted_entries)

    if not deleted_tags:
        log.skipped(
            DELETE_NODE_ASSERT_MSGS["no_deleted_idrac_nodes"],
            "No entries with service tags were removed"
        )
        pytest.skip("No deleted service tags found")

    log.check(DELETE_NODE_LOG_MSGS["idrac_kafka_verifying"])
    log.check(DELETE_NODE_LOG_MSGS["deleted_service_tags"].format(
        tags=deleted_tags
    ))

    # Verify deleted service tags not in latest Kafka data
    result = verify_idrac_deleted_node_in_kafka(
        host, admin_ip, deleted_tags, timeout_seconds=30
    )

    if result.get("error") and not result.get("tag_results"):
        log.failed("Failed to verify iDRAC deleted nodes in Kafka", result["error"])
        assert False, result["error"]

    # Build details
    details_lines = [
        f"Kafka bridge IP: {result.get('bridge_ip', '')}",
        f"Deleted service tags: {deleted_tags}",
        "",
        "Deleted node verification:",
    ]

    for tr in result.get("tag_results", []):
        tag = tr["service_tag"]
        found = tr["found_in_latest"]
        if found:
            details_lines.append(
                f"  ✗ {tag}: FOUND in latest Kafka data (should be absent)"
            )
        else:
            details_lines.append(
                f"  ✓ {tag}: NOT found in latest data (correctly removed)"
            )

    details = "\n".join(details_lines)

    if result["success"]:
        count = len(result.get("deleted_not_in_latest", []))
        log.passed(
            DELETE_NODE_LOG_MSGS["idrac_kafka_success"].format(count=count),
            details
        )
    else:
        log.failed("Deleted iDRAC nodes still in Kafka", details)
        assert False, DELETE_NODE_ASSERT_MSGS["idrac_kafka_still_present"].format(
            found=result.get("deleted_in_latest", []),
            not_found=result.get("deleted_not_in_latest", [])
        )


# =============================================================================
# TEST CASE 3: LDMS Deleted Node Data in Kafka (order 23)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(23)
def test_ldms_deleted_node_data_in_kafka(host):
    """
    Verify deleted LDMS node hostnames do NOT appear in the latest
    Kafka ldms topic data.

    Skips if:
    - No backup exists (first run)
    - PXE mapping unchanged
    - LDMS not enabled
    - Kafka not enabled
    - No LDMS nodes were deleted
    """
    log = TestLogger(
        DELETE_NODE_TEST_NAMES["ldms_deleted_node_kafka"]
    )

    deleted_nodes_info = get_deleted_nodes_cached(host)
    skip_if_no_deleted_nodes(deleted_nodes_info, log)
    skip_if_ldms_not_enabled(host, log)
    skip_if_kafka_not_enabled(host, log)

    admin_ip = get_admin_ip(host, log)
    deleted_entries = deleted_nodes_info.get("deleted_entries", [])

    # Get deleted LDMS hostnames
    deleted_hostnames = get_deleted_ldms_hostnames(deleted_entries)

    if not deleted_hostnames:
        log.skipped(
            DELETE_NODE_ASSERT_MSGS["no_deleted_ldms_nodes"],
            "No LDMS functional group entries were removed"
        )
        pytest.skip("No deleted LDMS nodes found")

    log.check(DELETE_NODE_LOG_MSGS["ldms_kafka_verifying"])
    log.check(DELETE_NODE_LOG_MSGS["deleted_ldms_nodes"].format(
        hostnames=deleted_hostnames
    ))

    # Verify deleted hostnames not in latest Kafka data
    result = verify_ldms_deleted_node_in_kafka(
        host, admin_ip, deleted_hostnames, timeout_seconds=30
    )

    if result.get("error") and not result.get("hostname_results"):
        log.failed("Failed to verify LDMS deleted nodes", result["error"])
        assert False, result["error"]

    # Build details
    details_lines = [
        f"Kafka bridge IP: {result.get('bridge_ip', '')}",
        f"Domain: {result.get('domain_name', '')}",
        f"Deleted LDMS hostnames: {deleted_hostnames}",
        "",
        "Deleted node verification:",
    ]

    for hr in result.get("hostname_results", []):
        hostname = hr["hostname"]
        found = hr["found_in_latest"]
        if found:
            details_lines.append(
                f"  ✗ {hostname}: FOUND in latest Kafka data (should be absent)"
            )
        else:
            details_lines.append(
                f"  ✓ {hostname}: NOT found in latest data (correctly removed)"
            )

    details = "\n".join(details_lines)

    if result["success"]:
        count = len(result.get("deleted_not_in_latest", []))
        log.passed(
            DELETE_NODE_LOG_MSGS["ldms_kafka_success"].format(count=count),
            details
        )
    else:
        log.failed("Deleted LDMS nodes still in Kafka", details)
        assert False, DELETE_NODE_ASSERT_MSGS["ldms_kafka_still_present"].format(
            found=result.get("deleted_in_latest", []),
            not_found=result.get("deleted_not_in_latest", [])
        )


# =============================================================================
# TEST CASE 4: iDRAC Deleted Node Data in VictoriaMetrics (order 24)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(24)
def test_idrac_deleted_node_data_in_victoria(host):
    """
    Verify deleted iDRAC node service tags do NOT have metrics
    in VictoriaMetrics.

    Skips if:
    - No backup exists (first run)
    - PXE mapping unchanged
    - VictoriaMetrics not enabled
    - iDRAC telemetry not enabled
    - No nodes with service tags were deleted

    After verification, updates the PXE backup with current content
    so the next test run has an accurate baseline.
    """
    log = TestLogger(
        DELETE_NODE_TEST_NAMES["idrac_deleted_node_victoria"]
    )

    deleted_nodes_info = get_deleted_nodes_cached(host)
    skip_if_no_deleted_nodes(deleted_nodes_info, log)
    skip_if_victoria_not_enabled(host, log)

    if not is_idrac_telemetry_enabled(host):
        log.skipped(
            "iDRAC telemetry not enabled",
            "Test skipped - iDRAC source not enabled"
        )
        pytest.skip("iDRAC telemetry not enabled")

    admin_ip = get_admin_ip(host, log)
    deleted_entries = deleted_nodes_info.get("deleted_entries", [])

    # Get deleted service tags
    deleted_tags = get_deleted_service_tags(deleted_entries)

    if not deleted_tags:
        log.skipped(
            DELETE_NODE_ASSERT_MSGS["no_deleted_idrac_nodes"],
            "No entries with service tags were removed"
        )
        pytest.skip("No deleted service tags found")

    log.check(DELETE_NODE_LOG_MSGS["idrac_victoria_verifying"])
    log.check(DELETE_NODE_LOG_MSGS["deleted_service_tags"].format(
        tags=deleted_tags
    ))

    try:
        # Verify deleted service tags not in VictoriaMetrics
        result = verify_idrac_deleted_node_in_victoria(
            host, admin_ip, deleted_tags, timeout_seconds=30
        )

        if result.get("error") and not result.get("tag_results"):
            log.failed(
                "Failed to verify deleted nodes in VictoriaMetrics",
                result["error"]
            )
            assert False, result["error"]

        # Build details
        details_lines = [
            f"Deployment mode: {result.get('deployment_mode', '')}",
            f"External IP: {result.get('external_ip', '')}",
            f"Deleted service tags: {deleted_tags}",
            "",
            "VictoriaMetrics verification:",
        ]

        for tr in result.get("tag_results", []):
            tag = tr["service_tag"]
            found = tr["found_in_victoria"]
            count = tr.get("metric_count", 0)
            if found:
                details_lines.append(
                    f"  ✗ {tag}: FOUND in VictoriaMetrics "
                    f"({count} metrics, should be absent)"
                )
            else:
                details_lines.append(
                    f"  ✓ {tag}: NOT found in VictoriaMetrics (correctly removed)"
                )

        details = "\n".join(details_lines)

        if result["success"]:
            count = len(result.get("not_found_in_victoria", []))
            log.passed(
                DELETE_NODE_LOG_MSGS["idrac_victoria_success"].format(count=count),
                details
            )
        else:
            log.failed("Deleted service tags still in VictoriaMetrics", details)
            assert False, DELETE_NODE_ASSERT_MSGS["idrac_victoria_still_present"].format(
                found=result.get("found_in_victoria", []),
                not_found=result.get("not_found_in_victoria", [])
            )
    finally:
        # Update backup with current PXE mapping for next test run
        update_pxe_backup(host)
