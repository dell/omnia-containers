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
Testinfra tests for telemetry verification.

This file contains test functions that verify telemetry deployment was successful.

Usage:
    ./run_molecule.sh telemetry test      # Run playbook + verify
    ./run_molecule.sh telemetry verify    # Verify only
"""

import time

from automation_library.core import (
    TestLogger,
    get_node_admin_ip,
)
from automation_library.telemetry.vars import (
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
)
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
)


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_idrac_telemetry_pod_count(host):
    """
    Test Case 1: Verify idrac-telemetry pods count matches expected.

    SSH to K8s control plane via omnia_core container and verify:
    - idrac-telemetry pods count = service_kube_node count + 1 (for mgmt layer)

    Uses get_node_admin_ip() with functional_group or hostname to get admin IP.
    """
    log = TestLogger(TEST_NAMES["idrac_telemetry_pod_count"])

    # Get admin IP by functional_group_name
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify pod count
    log.check(f"Checking idrac-telemetry pods on {admin_ip}")
    result = verify_idrac_telemetry_pod_count(host, admin_ip)

    details = (
        f"service_kube_node count: {result['service_kube_node_count']}\n"
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

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    max_retries = 3
    retry_interval = 60  # seconds

    for attempt in range(1, max_retries + 1):
        log.check(f"Checking all pods in telemetry namespace (attempt {attempt}/{max_retries})")
        result = verify_all_telemetry_pods_running(host, admin_ip)

        # Show output
        log.check(f"Pod status (attempt {attempt}):")
        if result["output"]:
            for line in result["output"].strip().split('\n'):
                print(f"    {line}")

        if result["success"]:
            log.passed(
                LOG_MSGS["all_pods_running"].format(total=result["total_pods"]),
                f"All pods running on attempt {attempt}"
            )
            return  # Test passed

        # Not all pods running
        not_running_names = [p["name"] for p in result["not_running_pods"]]
        log.check(
            f"  Not running ({result['not_running_count']}/{result['total_pods']}): "
            f"{not_running_names}"
        )

        if attempt < max_retries:
            log.check(f"Waiting {retry_interval}s before retry...")
            time.sleep(retry_interval)

    # All retries exhausted
    log.failed(
        LOG_MSGS["some_pods_not_running"].format(
            not_running=result["not_running_count"],
            total=result["total_pods"]
        ),
        f"Failed after {max_retries} retries"
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

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify MySQL data in all pods
    log.check("Decrypting MySQL credentials from ansible vault")
    result = verify_mysql_data_in_pods(host, admin_ip)

    if result.get("error") and not result.get("pod_results"):
        log.failed(LOG_MSGS["mysql_creds_failed"], result["error"])
        assert False, result["error"]

    log.check(LOG_MSGS["mysql_creds_decrypted"])

    # Show activated IPs
    log.check(f"Activated IPs from telemetry report: {result.get('activated_ips', [])}")

    # Show results for each pod
    all_success = True
    for pod_result in result.get("pod_results", []):
        pod_name = pod_result["pod_name"]
        expected = pod_result["expected_ips"]
        actual = pod_result["actual_ips"]
        missing = pod_result["missing_ips"]

        log.check(f"\n  Pod: {pod_name}")
        log.check(f"    Expected IPs: {expected}")
        log.check(f"    Actual IPs in MySQL: {actual}")

        if pod_result["success"]:
            log.check(f"    ✓ {LOG_MSGS['mysql_pod_verified'].format(pod_name=pod_name)}")
        else:
            log.check(
                f"    ✗ {LOG_MSGS['mysql_pod_missing_ips'].format(pod_name=pod_name, missing=missing)}"
            )
            all_success = False

    if all_success:
        log.passed(
            LOG_MSGS["mysql_all_pods_verified"],
            f"Verified {len(result.get('pod_results', []))} pods"
        )
    else:
        # Find first failed pod for assertion message
        failed_pod = next(
            (p for p in result.get("pod_results", []) if not p["success"]),
            None
        )
        if failed_pod:
            log.failed(
                result["error"],
                f"Pod {failed_pod['pod_name']} missing IPs: {failed_pod['missing_ips']}"
            )
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

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify receiver logs
    log.check("Checking idrac-telemetry-receiver logs for metrics collection")
    result = verify_receiver_collecting_metrics(host, admin_ip)

    if result.get("error") and not result.get("pod_results"):
        log.failed("Failed to verify receiver logs", result["error"])
        assert False, result["error"]

    # Show results for each pod
    all_success = True
    for pod_result in result.get("pod_results", []):
        pod_name = pod_result["pod_name"]
        mysql_ips = pod_result["mysql_ips"]
        ip_results = pod_result.get("ip_results", [])

        log.check(f"\n  Pod: {pod_name}")
        log.check(f"    MySQL IPs: {mysql_ips}")

        # Show each IP with its service_tag and sample reports
        for ip_result in ip_results:
            ip = ip_result.get("ip", "")
            service_tag = ip_result.get("service_tag", "")
            sample_reports = ip_result.get("sample_reports", [])

            if service_tag and sample_reports:
                log.check(f"    IP: {ip} → Service Tag: {service_tag} - ✓ Collecting metrics")
                log.check("      Sample metric reports:")
                for report in sample_reports:
                    # Extract just the metric report path
                    if '/redfish/v1/TelemetryService/MetricReports/' in report:
                        metric_name = report.split('/MetricReports/')[-1]
                        log.check(f"        - {service_tag}: Got new report for .../{metric_name}")
            elif service_tag:
                log.check(
                    f"    IP: {ip} → Service Tag: {service_tag} - SSE connected (no recent reports)"
                )
            else:
                log.check(f"    IP: {ip} → Service Tag: NOT FOUND - ✗ Not collecting")

        if not pod_result["success"]:
            all_success = False

    if all_success:
        log.passed(
            LOG_MSGS["receiver_all_collecting"],
            f"Verified {len(result.get('pod_results', []))} pods"
        )
    else:
        # Find first failed pod for assertion message
        failed_pod = next(
            (p for p in result.get("pod_results", []) if not p["success"]),
            None
        )
        if failed_pod:
            log.failed(
                result["error"],
                f"Pod {failed_pod['pod_name']} not collecting metrics"
            )
            assert False, ASSERT_MSGS["receiver_not_collecting"].format(
                pod_name=failed_pod["pod_name"],
                mysql_ips=failed_pod["mysql_ips"],
                service_tags=[r.get("service_tag", "") for r in failed_pod.get("ip_results", [])]
            )
