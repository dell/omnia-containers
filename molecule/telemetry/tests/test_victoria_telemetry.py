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

This module contains pytest test cases for verifying VictoriaMetrics configuration
and data collection in the telemetry namespace.

Test cases:
1. Verify VictoriaMetrics is enabled
2. Verify persistence size matches config
3. Verify single-node pods running (if deployment_mode=single-node)
4. Verify cluster pods running (if deployment_mode=cluster)
5. Verify vmagent pod running
6. Verify VictoriaMetrics services have external IPs
7. Verify TLS secret exists
8. Verify TLS connection and health endpoint
9. Verify iDRAC telemetry data in VictoriaMetrics

Note: All tests skip if:
  - idrac_telemetry_support is false
  - 'victoria' is not in idrac_telemetry_collection_type
"""

from datetime import datetime

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.vars.victoria_vars import (
    DEPLOYMENT_MODE_SINGLE,
    DEPLOYMENT_MODE_CLUSTER,
    VICTORIA_SINGLE_NODE,
    VICTORIA_TLS_SECRET,
)
from automation_library.telemetry.messages.victoria_msgs import (
    VICTORIA_TEST_NAMES,
    VICTORIA_LOG_MSGS,
    VICTORIA_ASSERT_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    is_victoria_enabled,
    is_idrac_telemetry_enabled,
    get_activated_service_tags,
    get_admin_ip,
    skip_if_victoria_not_enabled,
)
from automation_library.telemetry.functions.victoria_func import (
    get_deployment_mode,
    get_victoria_config,
    verify_victoria_persistence_size,
    verify_victoria_single_node_pods,
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

def test_victoria_enabled(host):
    """
    Test Case 1: Verify VictoriaMetrics is enabled.

    Checks:
    - idrac_telemetry_support is true
    - 'victoria' is in idrac_telemetry_collection_type
    - Logs deployment mode for information
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_enabled"])

    # Check if iDRAC telemetry is enabled
    if not is_idrac_telemetry_enabled(host):
        log.skipped(
            "iDRAC telemetry is not enabled (idrac_telemetry_support=false)",
            "Test skipped - iDRAC telemetry not enabled"
        )
        pytest.skip("iDRAC telemetry is not enabled")

    # Check if VictoriaMetrics is enabled
    if not is_victoria_enabled(host):
        log.skipped(
            VICTORIA_LOG_MSGS["victoria_not_enabled"],
            "Test skipped - VictoriaMetrics not enabled"
        )
        pytest.skip("VictoriaMetrics is not enabled in idrac_telemetry_collection_type")

    # Log deployment mode
    deployment_mode = get_deployment_mode(host)
    victoria_config = get_victoria_config(host)

    log.check(VICTORIA_LOG_MSGS["victoria_enabled"])
    if deployment_mode == DEPLOYMENT_MODE_SINGLE:
        log.check(VICTORIA_LOG_MSGS["deployment_mode_single"])
    else:
        log.check(VICTORIA_LOG_MSGS["deployment_mode_cluster"])

    log.check(f"  persistence_size: {victoria_config.get('persistence_size', 'N/A')}")
    log.check(f"  retention_period: {victoria_config.get('retention_period', 'N/A')}")

    log.passed(
        VICTORIA_LOG_MSGS["victoria_enabled"],
        f"Deployment mode: {deployment_mode}"
    )


def test_victoria_persistence_size(host):
    """
    Test Case 2: Verify VictoriaMetrics persistence size matches config.

    Verifies that PVC storage size matches victoria_configurations.persistence_size
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

    # Show results
    deployment_mode = result.get("deployment_mode", "")
    expected_size = result.get("expected_size", "")
    log.check(f"  Deployment mode: {deployment_mode}")
    log.check(f"  Expected size: {expected_size}")

    for pvc_result in result.get("pvc_results", []):
        pvc_name = pvc_result["pvc_name"]
        actual_size = pvc_result["actual_size"]
        match = pvc_result["match"]
        status = "✓" if match else "✗"
        log.check(f"  {status} PVC '{pvc_name}': {actual_size}")

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["persistence_size_match"].format(size=expected_size),
            f"{len(result.get('pvc_results', []))} PVCs verified"
        )
    else:
        mismatches = result.get("mismatches", [])
        mismatch_str = ", ".join(
            f"{m['pvc_name']}: expected {m['expected']}, actual {m['actual']}"
            for m in mismatches
        )
        log.failed(VICTORIA_LOG_MSGS["persistence_size_mismatch"], mismatch_str)
        assert False, VICTORIA_ASSERT_MSGS["persistence_size_mismatch"].format(
            expected=expected_size,
            actual=mismatch_str
        )


def test_victoria_single_node_pods(host):
    """
    Test Case 3: Verify VictoriaMetrics single-node pods are running.

    Only runs if deployment_mode is 'single-node'.
    Verifies victoria-metric StatefulSet pod is running.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_single_node_pods"])

    skip_if_victoria_not_enabled(host, log)

    # Check deployment mode
    deployment_mode = get_deployment_mode(host)
    if deployment_mode != DEPLOYMENT_MODE_SINGLE:
        log.skipped(
            f"Deployment mode is '{deployment_mode}', not single-node",
            "Test skipped - not single-node mode"
        )
        pytest.skip(f"Deployment mode is '{deployment_mode}', not single-node")

    admin_ip = get_admin_ip(host, log)

    # Verify single-node pods
    log.check("Verifying VictoriaMetrics single-node pods")
    result = verify_victoria_single_node_pods(host, admin_ip)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", ""), "Test skipped")
        pytest.skip(result.get("skip_reason", ""))

    if result.get("error"):
        log.failed("Failed to verify pods", result["error"])
        assert False, result["error"]

    # Show pod results
    for pod_result in result.get("pod_results", []):
        pod = pod_result["pod"]
        phase = pod_result["phase"]
        running = pod_result["running"]
        status = "✓" if running else "✗"
        log.check(f"  {status} Pod '{pod}': {phase}")

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["all_pods_running"].format(
                component="victoria-metric",
                count=result.get("actual_count", 0)
            ),
            "Single-node VictoriaMetrics is running"
        )
    else:
        errors = result.get("errors", [])
        log.failed(
            VICTORIA_LOG_MSGS["pods_not_running"].format(component="victoria-metric"),
            "; ".join(errors)
        )
        assert False, VICTORIA_ASSERT_MSGS["pods_not_running"].format(
            component="victoria-metric",
            expected=1,
            running=result.get("actual_count", 0),
            not_running=errors,
            app_label=VICTORIA_SINGLE_NODE["app_label"]
        )


def test_victoria_cluster_pods(host):
    """
    Test Case 4: Verify VictoriaMetrics cluster pods are running.

    Only runs if deployment_mode is 'cluster'.
    Verifies vmstorage (3), vminsert (2), vmselect (2) pods are running.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_cluster_pods"])

    skip_if_victoria_not_enabled(host, log)

    # Check deployment mode
    deployment_mode = get_deployment_mode(host)
    if deployment_mode != DEPLOYMENT_MODE_CLUSTER:
        log.skipped(
            f"Deployment mode is '{deployment_mode}', not cluster",
            "Test skipped - not cluster mode"
        )
        pytest.skip(f"Deployment mode is '{deployment_mode}', not cluster")

    admin_ip = get_admin_ip(host, log)

    # Verify cluster pods
    log.check("Verifying VictoriaMetrics cluster pods")
    result = verify_victoria_cluster_pods(host, admin_ip)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", ""), "Test skipped")
        pytest.skip(result.get("skip_reason", ""))

    if result.get("error"):
        log.failed("Failed to verify pods", result["error"])
        assert False, result["error"]

    # Show component results
    all_success = True
    for comp_result in result.get("component_results", []):
        component = comp_result["component"]
        expected = comp_result["expected_replicas"]
        running = comp_result["running_count"]
        success = comp_result["success"]
        status = "✓" if success else "✗"

        log.check(f"  {status} {component}: {running}/{expected} running")

        for pod_result in comp_result.get("pod_results", []):
            pod = pod_result["pod"]
            phase = pod_result["phase"]
            pod_running = pod_result["running"]
            pod_status = "✓" if pod_running else "✗"
            log.check(f"      {pod_status} {pod}: {phase}")

        if not success:
            all_success = False

    if all_success:
        log.passed(
            VICTORIA_LOG_MSGS["all_pods_running"].format(
                component="cluster",
                count=sum(
                    c["running_count"]
                    for c in result.get("component_results", [])
                )
            ),
            "All VictoriaMetrics cluster pods are running"
        )
    else:
        errors = result.get("errors", [])
        log.failed(
            VICTORIA_LOG_MSGS["pods_not_running"].format(component="cluster"),
            "; ".join(errors)
        )
        assert False, "; ".join(errors)


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

    # Show pod results
    for pod_result in result.get("pod_results", []):
        pod = pod_result["pod"]
        phase = pod_result["phase"]
        running = pod_result["running"]
        status = "✓" if running else "✗"
        log.check(f"  {status} Pod '{pod}': {phase}")

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["all_pods_running"].format(
                component="vmagent",
                count=len(result.get("pod_results", []))
            ),
            "vmagent is running"
        )
    else:
        errors = result.get("errors", [])
        log.failed(
            VICTORIA_LOG_MSGS["pods_not_running"].format(component="vmagent"),
            "; ".join(errors)
        )
        assert False, VICTORIA_ASSERT_MSGS["vmagent_not_running"]


def test_victoria_services(host):
    """
    Test Case 6: Verify VictoriaMetrics services have external IPs.

    Single-node: victoria-loadbalancer (port 8443)
    Cluster: vminsert (port 8480), vmselect (port 8481)
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_services"])

    skip_if_victoria_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify services
    deployment_mode = get_deployment_mode(host)
    log.check(f"Verifying VictoriaMetrics services (mode: {deployment_mode})")
    result = verify_victoria_services(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify services", result["error"])
        assert False, result["error"]

    # Show service results
    for svc_result in result.get("service_results", []):
        service = svc_result["service"]
        external_ip = svc_result.get("external_ip", "")
        port = svc_result["port"]
        has_ip = svc_result["has_external_ip"]
        status = "✓" if has_ip else "✗"

        if has_ip:
            log.check(f"  {status} Service '{service}': {external_ip}:{port}")
        else:
            log.check(f"  {status} Service '{service}': NO EXTERNAL IP")

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["all_services_ready"],
            f"{len(result.get('service_results', []))} services verified"
        )
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
                "; ".join(errors)
            )
            assert False, VICTORIA_ASSERT_MSGS["service_no_external_ip"].format(
                service=failed_svc["service"]
            )


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

    # Show keys found
    keys_found = result.get("keys_found", [])
    missing_keys = result.get("missing_keys", [])

    log.check(f"  Keys found: {keys_found}")
    if missing_keys:
        log.check(f"  Missing keys: {missing_keys}")

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["tls_secret_exists"].format(secret=VICTORIA_TLS_SECRET),
            f"Keys: {keys_found}"
        )
    else:
        log.failed(
            VICTORIA_LOG_MSGS["tls_secret_missing_keys"].format(keys=missing_keys),
            f"Missing: {missing_keys}"
        )
        assert False, VICTORIA_ASSERT_MSGS["tls_secret_missing_keys"].format(
            secret=VICTORIA_TLS_SECRET,
            missing_keys=missing_keys
        )


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
    deployment_mode = get_deployment_mode(host)
    log.check(f"Verifying TLS connection (mode: {deployment_mode})")
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

    # Show results
    external_ip = result.get("external_ip", "")
    port = result.get("port", "")
    health_response = result.get("health_response", "")

    log.check(f"  Service: {result.get('service_name', '')}")
    log.check(f"  URL: https://{external_ip}:{port}/health")
    log.check(f"  TLS connected: {result.get('tls_connected', False)}")
    log.check(f"  Health response: {health_response}")

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["tls_connection_success"],
            f"Health: {health_response}"
        )
    else:
        log.failed(
            VICTORIA_LOG_MSGS["health_endpoint_failed"],
            f"Response: {health_response}"
        )
        assert False, VICTORIA_ASSERT_MSGS["health_check_failed"].format(
            host=external_ip,
            port=port,
            response=health_response
        )


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
    log.check(f"  Activated service tags: {activated_tags}")
    result = verify_victoria_idrac_data(host, admin_ip)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", ""), "Test skipped")
        pytest.skip(result.get("skip_reason", ""))

    if result.get("error"):
        log.failed("Failed to verify iDRAC data", result["error"])
        assert False, result["error"]

    # Show results for each service tag
    log.check(f"  VictoriaMetrics URL: https://{result.get('external_ip')}:{result.get('port')}")
    log.check("Service tag verification results:")

    for tag_result in result.get("service_tag_results", []):
        service_tag = tag_result["service_tag"]
        found = tag_result["found"]
        latest_ts = tag_result.get("latest_timestamp", 0)
        metric_count = tag_result["metric_count"]
        status = "✓" if found else "✗"

        if found:
            log.check(f"  {status} {service_tag}")
            log.check(f"      Service Tag : {service_tag}")
            log.check(f"      Metrics     : {metric_count} found")
            if latest_ts:
                try:
                    human_ts = datetime.fromtimestamp(int(latest_ts)).strftime("%Y-%m-%d %H:%M:%S")
                    log.check(f"      VM Time     : {latest_ts} ({human_ts})")
                except (ValueError, OSError):
                    log.check(f"      VM Time     : {latest_ts}")
            for sample in tag_result.get("sample_metrics", []):
                metric_name = sample["metric_name"]
                value = sample["value"]
                log.check(f"        - {metric_name}: {value}")
        else:
            log.check(f"  {status} {service_tag}: NO DATA FOUND")

    if result["success"]:
        found_count = len(result.get("found_tags", []))
        log.passed(
            VICTORIA_LOG_MSGS["idrac_data_all_found"].format(count=found_count),
            f"Data found for all {found_count} service tags"
        )
    else:
        missing = result.get("missing_tags", [])
        found = result.get("found_tags", [])
        log.failed(
            f"iDRAC data missing for {len(missing)} service tags",
            f"Missing: {missing}"
        )
        assert False, VICTORIA_ASSERT_MSGS["idrac_data_missing"].format(
            missing=missing,
            found=found
        )
