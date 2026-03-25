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
iDRAC Telemetry Test Cases.

This module contains pytest test cases for verifying iDRAC telemetry deployment.

Test cases:
1. Verify idrac-telemetry pod count matches expected
2. Verify all telemetry pods are running
3. Verify MySQL data in idrac-telemetry pods
4. Verify idrac-telemetry-receiver is collecting metrics
"""

import time
import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.functions.shared_func import get_admin_ip
from automation_library.telemetry.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.telemetry.functions import (
    verify_idrac_telemetry_pod_count,
    verify_all_telemetry_pods_running,
    verify_mysql_data_in_pods,
    verify_receiver_collecting_metrics,
    has_activated_ips,
)


# =============================================================================
# IDRAC TELEMETRY TEST CASES
# =============================================================================

def test_idrac_telemetry_pod_count(host):
    """
    Test Case 1: Verify idrac-telemetry pods count matches expected.

    SSH to K8s control plane via omnia_core container and verify:
    - idrac-telemetry pods count = service_kube_node count + 1 (for mgmt layer)

    Uses get_node_info() with search_by and search_value to get admin IP.
    """
    log = TestLogger(TEST_NAMES["idrac_telemetry_pod_count"])

    admin_ip = get_admin_ip(host, log)

    # Verify pod count
    log.check(f"Checking idrac-telemetry pods on {admin_ip}")
    result = verify_idrac_telemetry_pod_count(host, admin_ip)

    details = (
        f"service_kube_node count: {result['service_kube_node_count']}\n"
        f"service_kube_nodes with children: {result['service_kube_nodes_with_children']}\n"
        f"Expected pods: {result['expected_count']}\n"
        f"Actual pods: {result['actual_count']}\n"
        f"Pods: {result['pods']}"
    )

    if result["success"]:
        log.passed(
            LOG_MSGS["idrac_pod_count_match"].format(expected=result['expected_count']),
            details
        )
    else:
        log.failed(LOG_MSGS["idrac_pod_count_mismatch"], details)

    assert result["success"], ASSERT_MSGS["idrac_pod_count_mismatch"].format(
        expected=result['expected_count'],
        actual=result['actual_count'],
        svc_count=result['service_kube_node_count']
    )


def test_all_telemetry_pods_running(host):
    """
    Test Case 2: Verify all pods in telemetry namespace are running.

    Retries up to 3 times with 60 second intervals.
    All pods must be in Running state for the test to pass.
    """
    log = TestLogger(TEST_NAMES["all_telemetry_pods_running"])

    admin_ip = get_admin_ip(host, log)

    max_retries = 3
    retry_interval = 60  # seconds

    for attempt in range(1, max_retries + 1):
        log.check(f"Checking all pods in telemetry namespace (attempt {attempt}/{max_retries})")
        result = verify_all_telemetry_pods_running(host, admin_ip)

        if result["success"]:
            details_lines = [f"All pods running on attempt {attempt}"]
            if result["output"]:
                for line in result["output"].strip().split('\n'):
                    details_lines.append(f"  {line}")
            log.passed(
                LOG_MSGS["all_pods_running"].format(total=result["total_pods"]),
                "\n".join(details_lines)
            )
            return  # Test passed

        # Not all pods running
        if attempt < max_retries:
            not_running_names = [p["name"] for p in result["not_running_pods"]]
            log.check(
                f"Not running ({result['not_running_count']}/{result['total_pods']}): "
                f"{not_running_names} - retrying in {retry_interval}s"
            )
            time.sleep(retry_interval)

    # All retries exhausted
    fail_details_lines = [f"Failed after {max_retries} retries"]
    if result["output"]:
        for line in result["output"].strip().split('\n'):
            fail_details_lines.append(f"  {line}")
    not_running_names = [p["name"] for p in result["not_running_pods"]]
    fail_details_lines.append(f"Not running: {not_running_names}")
    log.failed(
        LOG_MSGS["some_pods_not_running"].format(
            not_running=result["not_running_count"],
            total=result["total_pods"]
        ),
        "\n".join(fail_details_lines)
    )
    assert False, ASSERT_MSGS["telemetry_pods_not_running"].format(
        total=result["total_pods"],
        running=result["running_count"],
        not_running=result["not_running_count"]
    )


def test_mysql_data_in_idrac_telemetry_pods(host):
    """
    Test Case 3: Verify MySQL data in idrac-telemetry pods.

    For each idrac-telemetry pod, verify that expected IPs are present in MySQL:
    - idrac-telemetry-0 (MGMT): IPs with no PARENT in bmc_group_data.csv AND activated
    - idrac-telemetry-N: IPs with PARENT=service_tag AND activated

    Steps:
    1. Decrypt ansible vault to get MySQL credentials
    2. Get activated IPs from idrac_telemetry_report.yml
    3. Get BMC group data and service cluster metadata
    4. For each pod, verify expected IPs exist in MySQL services table
    """
    log = TestLogger(TEST_NAMES["mysql_data_in_pods"])

    admin_ip = get_admin_ip(host, log)

    # Skip if no activated IPs
    if not has_activated_ips(host):
        log.skipped(
            "No activated IPs found in telemetry report",
            "Test skipped - no telemetry activation to verify"
        )
        pytest.skip("No activated IPs found in telemetry report")

    # Verify MySQL data in all pods
    log.check("Decrypting MySQL credentials and verifying data in pods")
    result = verify_mysql_data_in_pods(host, admin_ip)

    # Fail on actual errors (MySQL connection, etc.)
    if result.get("error") and not result.get("pod_results"):
        log.failed(LOG_MSGS["mysql_creds_failed"], result["error"])
        assert False, result["error"]

    # Build details for all pods
    details_lines = [
        LOG_MSGS["mysql_creds_decrypted"],
        f"Activated IPs: {result.get('activated_ips', [])}",
    ]

    all_success = True
    for pod_result in result.get("pod_results", []):
        pod_name = pod_result["pod_name"]
        expected = pod_result["expected_ips"]
        actual = pod_result["actual_ips"]
        missing = pod_result["missing_ips"]

        details_lines.append(f"")
        details_lines.append(f"Pod: {pod_name}")
        details_lines.append(f"  Expected IPs: {expected}")
        details_lines.append(f"  Actual IPs  : {actual}")

        if pod_result["success"]:
            details_lines.append(
                f"  ✓ {LOG_MSGS['mysql_pod_verified'].format(pod_name=pod_name)}"
            )
        else:
            details_lines.append(
                f"  ✗ {LOG_MSGS['mysql_pod_missing_ips'].format(pod_name=pod_name, missing=missing)}"
            )
            all_success = False

    details = "\n".join(details_lines)

    if all_success:
        log.passed(
            LOG_MSGS["mysql_all_pods_verified"],
            details
        )
    else:
        failed_pod = next(
            (p for p in result.get("pod_results", []) if not p["success"]),
            None
        )
        log.failed(result.get("error", "MySQL data missing"), details)
        if failed_pod:
            assert False, ASSERT_MSGS["mysql_data_missing"].format(
                pod_name=failed_pod["pod_name"],
                expected=failed_pod["expected_ips"],
                actual=failed_pod["actual_ips"],
                missing=failed_pod["missing_ips"]
            )


def test_receiver_collecting_metrics(host):
    """
    Test Case 4: Verify idrac-telemetry-receiver is collecting metrics.

    For each idrac-telemetry pod:
    - Get MySQL IPs and map to service tags from receiver logs
    - Verify "Got new report for /redfish/v1/TelemetryService/MetricReports" entries
    - Show 2-3 sample metric report entries per service tag
    """
    log = TestLogger(TEST_NAMES["receiver_collecting_metrics"])

    admin_ip = get_admin_ip(host, log)

    # Skip if no activated IPs
    if not has_activated_ips(host):
        log.skipped(
            "No activated IPs found in telemetry report",
            "Test skipped - no telemetry activation to verify"
        )
        pytest.skip("No activated IPs found in telemetry report")

    # Verify receiver logs
    log.check("Checking idrac-telemetry-receiver logs for metrics collection")
    result = verify_receiver_collecting_metrics(host, admin_ip)

    # Fail on actual errors (log access, etc.)
    if result.get("error") and not result.get("pod_results"):
        log.failed("Failed to verify receiver logs", result["error"])
        assert False, result["error"]

    # Build details for all pods
    details_lines = []
    all_success = True
    for pod_result in result.get("pod_results", []):
        pod_name = pod_result["pod_name"]
        mysql_ips = pod_result["mysql_ips"]
        ip_results = pod_result.get("ip_results", [])

        details_lines.append(f"Pod: {pod_name}")
        details_lines.append(f"  MySQL IPs: {mysql_ips}")

        for ip_result in ip_results:
            ip = ip_result.get("ip", "")
            service_tag = ip_result.get("service_tag", "")
            sample_reports = ip_result.get("sample_reports", [])

            if service_tag and sample_reports:
                details_lines.append(
                    f"  ✓ {ip} → {service_tag} - Collecting metrics"
                )
                for report in sample_reports:
                    if '/redfish/v1/TelemetryService/MetricReports/' in report:
                        metric_name = report.split('/MetricReports/')[-1]
                        details_lines.append(
                            f"      - {service_tag}: .../{metric_name}"
                        )
            elif service_tag:
                details_lines.append(
                    f"  ⚠ {ip} → {service_tag} - SSE connected (no recent reports)"
                )
            else:
                details_lines.append(
                    f"  ✗ {ip} → NOT FOUND - Not collecting"
                )

        if not pod_result["success"]:
            all_success = False
        details_lines.append("")

    details = "\n".join(details_lines)

    if all_success:
        log.passed(
            LOG_MSGS["receiver_all_collecting"],
            details
        )
    else:
        failed_pod = next(
            (p for p in result.get("pod_results", []) if not p["success"]),
            None
        )
        log.failed(result.get("error", "Receiver not collecting"), details)
        if failed_pod:
            assert False, ASSERT_MSGS["receiver_not_collecting"].format(
                pod_name=failed_pod["pod_name"],
                mysql_ips=failed_pod["mysql_ips"],
                service_tags=[r.get("service_tag", "") for r in failed_pod.get("ip_results", [])]
            )
