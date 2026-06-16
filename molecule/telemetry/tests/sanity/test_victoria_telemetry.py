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
VictoriaMetrics Telemetry Test Cases.

This module contains pytest test cases for verifying VictoriaMetrics deployment.

Test cases:
1. Verify VictoriaMetrics is enabled
2. Verify persistence size matches config
3. Verify cluster pods running (vmstorage, vminsert, vmselect)
4. Verify vmagent pod running
5. Verify VictoriaMetrics services have external IPs
6. Verify TLS secret exists
7. Verify TLS connection and health endpoint
8. Verify iDRAC telemetry data in VictoriaMetrics

Note: All tests skip if no source targets victoria_metrics.
"""

from datetime import datetime

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.vars.victoria_vars import (
    VICTORIA_TLS_SECRET,
)
from automation_library.telemetry.messages.victoria_msgs import (
    VICTORIA_TEST_NAMES,
    VICTORIA_LOG_MSGS,
    VICTORIA_ASSERT_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    is_victoria_enabled,
    get_activated_service_tags,
    get_admin_ip,
    skip_if_victoria_not_enabled,
)
from automation_library.telemetry.functions.victoria_func import (
    get_victoria_config,
    verify_victoria_persistence_size,
    verify_victoria_cluster_pods,
    verify_vmagent_pod,
    verify_victoria_services,
    verify_victoria_tls_secret,
    verify_victoria_tls_health,
    verify_victoria_idrac_data,
)


# =============================================================================
# TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(12)
def test_victoria_enabled(host):
    """
    Test Case 1: Verify VictoriaMetrics is enabled.

    Checks:
    - At least one source targets victoria_metrics
    - Logs deployment mode for information
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_enabled"])

    # Check if VictoriaMetrics sink is active
    if not is_victoria_enabled(host):
        log.skipped(
            VICTORIA_LOG_MSGS["victoria_not_enabled"],
            "Test skipped - VictoriaMetrics not enabled"
        )
        pytest.skip("VictoriaMetrics sink is not active")

    victoria_config = get_victoria_config(host)

    details = (
        f"Deployment mode: cluster\n"
        f"persistence_size: {victoria_config.get('persistence_size', 'N/A')}\n"
        f"retention_period: {victoria_config.get('retention_period', 'N/A')}"
    )

    log.passed(VICTORIA_LOG_MSGS["victoria_enabled"], details)


@pytest.mark.sanity
@pytest.mark.order(13)
def test_victoria_persistence_size(host):
    """
    Test Case 2: Verify VictoriaMetrics persistence size matches config.

    Verifies that PVC storage size matches telemetry_sinks.victoria_metrics.persistence_size
    in telemetry_config.yml.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_persistence_size"])

    skip_if_victoria_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify persistence size
    log.check("Verifying VictoriaMetrics PVC storage size")
    result = verify_victoria_persistence_size(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify persistence size", result["error"])
        assert False, result["error"]

    # Build details
    expected_size = result.get("expected_size", "")
    details_lines = [
        f"Expected size: {expected_size}",
    ]
    for pvc_result in result.get("pvc_results", []):
        pvc_name = pvc_result["pvc_name"]
        actual_size = pvc_result["actual_size"]
        match = pvc_result["match"]
        status = "✓" if match else "✗"
        details_lines.append(f"{status} PVC '{pvc_name}': {actual_size}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["persistence_size_match"].format(size=expected_size),
            details
        )
    else:
        mismatches = result.get("mismatches", [])
        mismatch_str = ", ".join(
            f"{m['pvc_name']}: expected {m['expected']}, actual {m['actual']}"
            for m in mismatches
        )
        log.failed(VICTORIA_LOG_MSGS["persistence_size_mismatch"], details)
        assert False, VICTORIA_ASSERT_MSGS["persistence_size_mismatch"].format(
            expected=expected_size,
            actual=mismatch_str
        )


@pytest.mark.sanity
@pytest.mark.order(14)
def test_victoria_cluster_pods(host):
    """
    Test Case 3: Verify VictoriaMetrics cluster pods are running.

    Verifies vmstorage (3), vminsert (2), vmselect (2) pods are running.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_cluster_pods"])

    skip_if_victoria_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify cluster pods
    log.check("Verifying VictoriaMetrics cluster pods")
    result = verify_victoria_cluster_pods(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify pods", result["error"])
        assert False, result["error"]

    # Build details
    details_lines = []
    all_success = True
    for comp_result in result.get("component_results", []):
        comp_ok = comp_result["success"]
        status = "✓" if comp_ok else "✗"
        details_lines.append(
            f"{status} {comp_result['component']}: "
            f"{comp_result['running_count']}/{comp_result['expected_replicas']} running"
        )

        for pod_result in comp_result.get("pod_results", []):
            pod_status = "✓" if pod_result["running"] else "✗"
            details_lines.append(
                f"    {pod_status} {pod_result['pod']}: {pod_result['phase']}"
            )

        if not comp_ok:
            all_success = False

    details = "\n".join(details_lines)

    if all_success:
        log.passed(
            VICTORIA_LOG_MSGS["all_pods_running"].format(
                component="cluster",
                count=sum(
                    c["running_count"]
                    for c in result.get("component_results", [])
                )
            ),
            details
        )
    else:
        errors = result.get("errors", [])
        log.failed(
            VICTORIA_LOG_MSGS["pods_not_running"].format(component="cluster"),
            details + "\n" + "; ".join(errors)
        )
        assert False, "; ".join(errors)


@pytest.mark.sanity
@pytest.mark.order(15)
def test_vmagent_pod_running(host):
    """
    Test Case 5: Verify vmagent pod is running.

    vmagent scrapes metrics from idrac-telemetry pods and writes to VictoriaMetrics.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["vmagent_pod_running"])

    skip_if_victoria_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify vmagent pod
    log.check("Verifying vmagent pod")
    result = verify_vmagent_pod(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify vmagent pod", result["error"])
        assert False, result["error"]

    # Build details
    details_lines = []
    for pod_result in result.get("pod_results", []):
        pod = pod_result["pod"]
        phase = pod_result["phase"]
        running = pod_result["running"]
        status = "✓" if running else "✗"
        details_lines.append(f"{status} Pod '{pod}': {phase}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["all_pods_running"].format(
                component="vmagent",
                count=len(result.get("pod_results", []))
            ),
            details
        )
    else:
        errors = result.get("errors", [])
        log.failed(
            VICTORIA_LOG_MSGS["pods_not_running"].format(component="vmagent"),
            details + "\n" + "; ".join(errors)
        )
        assert False, VICTORIA_ASSERT_MSGS["vmagent_not_running"]


@pytest.mark.sanity
@pytest.mark.order(16)
def test_victoria_services(host):
    """
    Test Case 5: Verify VictoriaMetrics services have external IPs.

    Checks vminsert (port 8480) and vmselect (port 8481) services.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_services"])

    skip_if_victoria_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify services
    log.check("Verifying VictoriaMetrics services")
    result = verify_victoria_services(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify services", result["error"])
        assert False, result["error"]

    # Build details
    details_lines = []
    for svc_result in result.get("service_results", []):
        service = svc_result["service"]
        external_ip = svc_result.get("external_ip", "")
        port = svc_result["port"]
        has_ip = svc_result["has_external_ip"]
        status = "✓" if has_ip else "✗"

        if has_ip:
            details_lines.append(f"{status} Service '{service}': {external_ip}:{port}")
        else:
            details_lines.append(f"{status} Service '{service}': NO EXTERNAL IP")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOG_MSGS["all_services_ready"], details)
    else:
        errors = result.get("errors", [])
        failed_svc = next(
            (s for s in result.get("service_results", []) if not s["has_external_ip"]),
            None
        )
        if failed_svc:
            log.failed(
                VICTORIA_LOG_MSGS["service_no_external_ip"].format(
                    service=failed_svc["service"]
                ),
                details + "\n" + "; ".join(errors)
            )
            assert False, VICTORIA_ASSERT_MSGS["service_no_external_ip"].format(
                service=failed_svc["service"]
            )


@pytest.mark.sanity
@pytest.mark.order(17)
def test_victoria_tls_secret(host):
    """
    Test Case 7: Verify VictoriaMetrics TLS secret exists.

    Checks that victoria-tls-certs secret exists with:
    - tls.crt
    - tls.key
    - ca.crt
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_tls_secret"])

    skip_if_victoria_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify TLS secret
    log.check(f"Verifying TLS secret '{VICTORIA_TLS_SECRET}'")
    result = verify_victoria_tls_secret(host, admin_ip)

    if not result.get("secret_exists", False):
        log.failed(
            VICTORIA_LOG_MSGS["tls_secret_missing"].format(secret=VICTORIA_TLS_SECRET),
            result.get("error", "")
        )
        assert False, VICTORIA_ASSERT_MSGS["tls_secret_missing"].format(
            secret=VICTORIA_TLS_SECRET
        )

    # Build details
    keys_found = result.get("keys_found", [])
    missing_keys = result.get("missing_keys", [])
    details_lines = [f"Keys found: {keys_found}"]
    if missing_keys:
        details_lines.append(f"Missing keys: {missing_keys}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["tls_secret_exists"].format(secret=VICTORIA_TLS_SECRET),
            details
        )
    else:
        log.failed(
            VICTORIA_LOG_MSGS["tls_secret_missing_keys"].format(keys=missing_keys),
            details
        )
        assert False, VICTORIA_ASSERT_MSGS["tls_secret_missing_keys"].format(
            secret=VICTORIA_TLS_SECRET,
            missing_keys=missing_keys
        )


@pytest.mark.sanity
@pytest.mark.order(18)
def test_victoria_tls_health(host):
    """
    Test Case 8: Verify TLS connection and health endpoint.

    Tests:
    - TLS connection using CA certificate
    - /health endpoint returns valid response
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_tls_health"])

    skip_if_victoria_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify TLS connection and health
    log.check("Verifying TLS connection")
    result = verify_victoria_tls_health(host, admin_ip)

    if result.get("error"):
        log.failed(
            VICTORIA_LOG_MSGS["tls_connection_failed"],
            result["error"]
        )
        assert False, VICTORIA_ASSERT_MSGS["tls_connection_failed"].format(
            host=result.get("external_ip", ""),
            port=result.get("port", ""),
            error=result.get("error", "")
        )

    # Build details
    external_ip = result.get("external_ip", "")
    port = result.get("port", "")
    health_response = result.get("health_response", "")

    details = (
        f"Service: {result.get('service_name', '')}\n"
        f"URL: https://{external_ip}:{port}/health\n"
        f"TLS connected: {result.get('tls_connected', False)}\n"
        f"Health response: {health_response}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOG_MSGS["tls_connection_success"], details)
    else:
        log.failed(VICTORIA_LOG_MSGS["health_endpoint_failed"], details)
        assert False, VICTORIA_ASSERT_MSGS["health_check_failed"].format(
            host=external_ip,
            port=port,
            response=health_response
        )


def _build_victoria_tag_lines(tag_result):
    """Build detail lines for a single VictoriaMetrics service tag result."""
    lines = []
    stag = tag_result["service_tag"]
    if tag_result["found"]:
        lines.append(f"  ✓ {stag}")
        lines.append(
            f"      Metrics     : {tag_result['metric_count']} found"
        )
        latest_ts = tag_result.get("latest_timestamp", 0)
        if latest_ts:
            try:
                human_ts = datetime.fromtimestamp(
                    int(latest_ts)
                ).strftime("%Y-%m-%d %H:%M:%S")
                lines.append(
                    f"      VM Time     : {latest_ts} ({human_ts})"
                )
            except (ValueError, OSError):
                lines.append(f"      VM Time     : {latest_ts}")
        for sample in tag_result.get("sample_metrics", []):
            lines.append(
                f"        - {sample['metric_name']}: {sample['value']}"
            )
    else:
        lines.append(f"  ✗ {stag}: NO DATA FOUND")
    return lines


@pytest.mark.sanity
@pytest.mark.order(19)
def test_victoria_idrac_data(host):
    """
    Test Case 9: Verify iDRAC telemetry data in VictoriaMetrics.

    For each activated service tag in idrac_telemetry_report.yml:
    - Query VictoriaMetrics for PowerEdge_* metrics
    - Verify data exists
    - Display sample metrics
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_idrac_data"])

    skip_if_victoria_not_enabled(host, log)

    admin_ip = get_admin_ip(host, log)

    # Check for activated service tags (needs admin_ip for Redfish lookup)
    activated_tags = get_activated_service_tags(host, admin_ip)
    if not activated_tags:
        log.skipped(
            "No activated service tags found in telemetry report",
            "Test skipped - no telemetry activation to verify"
        )
        pytest.skip("No activated service tags found in telemetry report")

    # Verify iDRAC data
    log.check(VICTORIA_LOG_MSGS["idrac_data_verifying"])
    result = verify_victoria_idrac_data(host, admin_ip)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", ""), "Test skipped")
        pytest.skip(result.get("skip_reason", ""))

    if result.get("error"):
        log.failed("Failed to verify iDRAC data", result["error"])
        assert False, result["error"]

    # Build details with | line mechanism like other tests
    details_lines = [
        f"Activated service tags: {activated_tags}",
        f"VictoriaMetrics URL: https://{result.get('external_ip')}:{result.get('port')}",
        "",
        "Service tag verification:",
    ]

    for tag_result in result.get("service_tag_results", []):
        details_lines.extend(_build_victoria_tag_lines(tag_result))

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["idrac_data_all_found"].format(
                count=len(result.get("found_tags", []))
            ),
            details
        )
    else:
        log.failed(
            f"iDRAC data missing for "
            f"{len(result.get('missing_tags', []))} service tags",
            details
        )
        assert False, VICTORIA_ASSERT_MSGS["idrac_data_missing"].format(
            missing=result.get("missing_tags", []),
            found=result.get("found_tags", [])
        )
