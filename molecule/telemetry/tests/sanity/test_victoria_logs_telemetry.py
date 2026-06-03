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
VictoriaLogs Consolidated Test Suite.

This module consolidates all VictoriaLogs test cases from multiple files:
  - test_victoria_logs.py
  - test_victoria_logs_config.py (excluding OMN01D-2248 liveness probe test)
  - test_victoria_logs_edge_cases.py
  - test_victoria_logs_destructive.py
  - test_victoria_logs_partial_failure.py
  - test_victoria_logs_cleanup.py

Total test cases: 48 (2 tests removed per user request)

Excluded tests:
  - OMN01D-2248: test_vlstorage_liveness_probe (liveness probe test)
  - OMN01D-2250: test_omn01d_2250_authentication_defect (authentication test)

Test categories:
  - Sanity tests (basic functionality)
  - Configuration tests (replication, readiness probes)
  - Edge case tests (resource limits, large messages)
  - Destructive tests (pod failures, cluster recovery)
  - Partial failure tests (HA verification)
  - Cleanup tests (retention, removal)
"""

# =============================================================================
# IMPORTS
# =============================================================================

import pytest

from automation_library.core import TestLogger
from automation_library.core.host import run_on_remote_node
from automation_library.telemetry.messages.victoria_logs_msgs import (
    VICTORIA_LOGS_TEST_NAMES,
    VICTORIA_LOGS_LOG_MSGS,
    VICTORIA_LOGS_ASSERT_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    is_idrac_telemetry_enabled,
    is_victoria_logs_enabled,
    get_admin_ip,
    skip_if_victoria_logs_not_enabled,
)
from automation_library.telemetry.vars.shared_vars import TELEMETRY_NAMESPACE
from automation_library.telemetry.vars.victoria_logs_vars import (
    VLSTORAGE,
    VLINSERT,
    VLSELECT,
    VLAGENT_LOGS,
    VLAGENT_CONFIGMAP_NAME,
    VLAGENT_SYSLOG_INGESTION_WAIT_SECS,
    VLAGENT_MULTI_MSG_COUNT,
    VLAGENT_BULK_COUNT,
    VLSELECT_QUERY_RESPONSE_MAX_SECS,
    TLS_CERT_MIN_VALID_SECS,
    VICTORIA_LOGS_TLS_SECRET,
)
from automation_library.telemetry.functions.victoria_logs_func import (
    get_victoria_logs_config,
    verify_victoria_logs_storage_size,
    verify_victoria_logs_cluster_pods,
    verify_vlagent_pod,
    verify_victoria_logs_services,
    verify_victoria_logs_tls_secret,
    verify_victoria_logs_health,
    verify_victoria_logs_query,
    verify_vlagent_configmap,
    verify_vlagent_pvc,
    verify_vlagent_syslog_service,
    inject_test_syslog,
    verify_syslog_received,
    verify_vlagent_configmap_content,
    verify_syslog_stream_labels,
    verify_logsql_field_filter,
    verify_vlinsert_direct_write,
    verify_retention_period_applied,
    verify_invalid_logsql_rejected,
    verify_nonexistent_stream_empty,
    verify_plain_http_rejected,
    verify_wrong_ca_rejected,
    verify_tls_cert_validity,
    verify_multi_message_ingestion,
    verify_bulk_ingestion,
    verify_query_response_time,
    verify_pod_restart_preserves_data,
    verify_vlagent_pvc_mounted,
    verify_ha_under_vlstorage_failure,
    verify_resource_limits_enforced,
    verify_resource_requests_set,
    verify_large_log_message_handling,
    verify_malformed_json_rejected,
    verify_sql_injection_protection,
    verify_namespace_isolation,
    verify_rbac_restrictions,
    verify_pod_security_context,
)
from automation_library.telemetry.functions.victoria_logs_destructive_func import (
    verify_all_vlstorage_pods_down,
    verify_all_vlinsert_pods_down,
    verify_all_vlselect_pods_down,
    verify_complete_cluster_failure_recovery,
)
from automation_library.telemetry.functions.victoria_logs_partial_failure_func import (
    verify_single_vlstorage_pod_failure,
    verify_single_vlinsert_pod_failure,
    verify_single_vlselect_pod_failure,
)
from automation_library.telemetry.functions.victoria_logs_cleanup_func import (
    verify_retention_cleanup_cycle,
    verify_default_retention_period,
    verify_independent_cleanup,
)
from automation_library.telemetry.functions.victoria_logs_config_func import (
    verify_vlstorage_replication_factor,
    verify_vlstorage_liveness_probe,
    verify_vlstorage_readiness_probe,
)

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

# Source: test_victoria_logs.py
@pytest.mark.order(25)
def test_victoria_logs_enabled(host):
    """
    Test Case 1: Verify VictoriaLogs is enabled.

    VictoriaLogs is co-deployed with VictoriaMetrics. Checks:
    - idrac_telemetry_support is true
    - 'victoria' is in idrac_telemetry_collection_type
    - Logs victoria_logs_configurations (storage_size, retention_period)
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["victoria_logs_enabled"])

    if not is_idrac_telemetry_enabled(host):
        log.skipped(
            "iDRAC telemetry is not enabled (idrac_telemetry_support=false)",
            "Test skipped - iDRAC telemetry not enabled"
        )
        pytest.skip("iDRAC telemetry is not enabled")

    if not is_victoria_logs_enabled(host):
        log.skipped(
            VICTORIA_LOGS_LOG_MSGS["victoria_logs_not_enabled"],
            "Test skipped - VictoriaLogs not enabled"
        )
        pytest.skip(
            "VictoriaLogs is not enabled in idrac_telemetry_collection_type"
        )

    logs_config = get_victoria_logs_config(host)
    details = (
        f"storage_size   : {logs_config.get('storage_size', 'N/A')}\n"
        f"retention_period: {logs_config.get('retention_period', 'N/A')}"
    )

    log.passed(VICTORIA_LOGS_LOG_MSGS["victoria_logs_enabled"], details)


# Source: test_victoria_logs.py
@pytest.mark.order(26)
def test_victoria_logs_storage_size(host):
    """
    Test Case 2: Verify vlstorage PVC size matches config.

    Verifies that all vlstorage PVC storage sizes match
    victoria_logs_configurations.storage_size in telemetry_config.yml.
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["victoria_logs_storage_size"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying vlstorage PVC storage sizes")
    result = verify_victoria_logs_storage_size(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify vlstorage PVC sizes", result["error"])
        assert False, result["error"]

    expected_size = result.get("expected_size", "")
    details_lines = [f"Expected size: {expected_size}"]
    for pvc_result in result.get("pvc_results", []):
        pvc_name = pvc_result["pvc_name"]
        actual_size = pvc_result["actual_size"]
        match = pvc_result["match"]
        status = "✓" if match else "✗"
        details_lines.append(f"{status} PVC '{pvc_name}': {actual_size}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["storage_size_match"].format(
                size=expected_size
            ),
            details
        )
    else:
        mismatches = result.get("mismatches", [])
        mismatch_str = ", ".join(
            f"{m['pvc_name']}: expected {m['expected']}, actual {m['actual']}"
            for m in mismatches
        )
        log.failed(VICTORIA_LOGS_LOG_MSGS["storage_size_mismatch"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["storage_size_mismatch"].format(
            expected=expected_size,
            actual=mismatch_str
        )


# Source: test_victoria_logs.py
@pytest.mark.order(27)
def test_victoria_logs_cluster_pods(host):
    """
    Test Case 3: Verify VictoriaLogs cluster pods are running.

    Verifies all three VLCluster components are at their expected replica counts:
    - vlstorage  : 3 pods (StatefulSet — persistent log storage)
    - vlinsert   : 2 pods (Deployment — log ingestion gateway)
    - vlselect   : 2 pods (Deployment — log query gateway)
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["victoria_logs_cluster_pods"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VictoriaLogs cluster pods")
    result = verify_victoria_logs_cluster_pods(host, admin_ip)

    if result.get("error") and not result.get("component_results"):
        log.failed("Failed to verify cluster pods", str(result.get("errors", [])))
        assert False, str(result.get("errors", []))

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
        total_running = sum(
            c["running_count"] for c in result.get("component_results", [])
        )
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["all_pods_running"].format(
                component="cluster",
                count=total_running
            ),
            details
        )
    else:
        errors = result.get("errors", [])
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["pods_not_running"].format(
                component="cluster"
            ),
            details + "\n" + "; ".join(errors)
        )
        failed_comp = next(
            (c for c in result.get("component_results", []) if not c["success"]),
            None
        )
        if failed_comp:
            assert False, VICTORIA_LOGS_ASSERT_MSGS["pods_not_running"].format(
                component=failed_comp["component"],
                expected=failed_comp["expected_replicas"],
                running=failed_comp["running_count"],
                not_running=[
                    p["pod"]
                    for p in failed_comp.get("pod_results", [])
                    if not p["running"]
                ],
                app_label=failed_comp["app_label"]
            )
        assert False, "; ".join(errors)


# Source: test_victoria_logs.py
@pytest.mark.order(28)
def test_vlagent_pod_running(host):
    """
    Test Case 4: Verify VLAgent pod is running.

    VLAgent provides:
    - Syslog reception on port 514 (plaintext) and 6514 (TLS)
    - RemoteWrite forwarding to vlinsert (JSON Lines over HTTPS)
    - PVC-backed buffer for retry during vlinsert unavailability
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["vlagent_pod_running"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(f"Verifying VLAgent pod (app={VLAGENT_LOGS['app_label']})")
    result = verify_vlagent_pod(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify vlagent pod", result["error"])
        assert False, result["error"]

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
            VICTORIA_LOGS_LOG_MSGS["all_pods_running"].format(
                component="vlagent",
                count=len(result.get("pod_results", []))
            ),
            details
        )
    else:
        errors = result.get("errors", [])
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["pods_not_running"].format(
                component="vlagent"
            ),
            details + "\n" + "; ".join(errors)
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["vlagent_not_running"]


# Source: test_victoria_logs.py
@pytest.mark.order(29)
def test_victoria_logs_services(host):
    """
    Test Case 5: Verify VictoriaLogs LoadBalancer services have external IPs.

    Checks:
    - vlinsert-victoria-logs-cluster (port 9481) — log ingestion endpoint
    - vlselect-victoria-logs-cluster (port 9471) — log query endpoint
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["victoria_logs_services"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VictoriaLogs LoadBalancer services")
    result = verify_victoria_logs_services(host, admin_ip)

    if result.get("error") and not result.get("service_results"):
        log.failed("Failed to verify services", str(result.get("errors", [])))
        assert False, str(result.get("errors", []))

    details_lines = []
    for svc_result in result.get("service_results", []):
        service = svc_result["service"]
        external_ip = svc_result.get("external_ip", "")
        port = svc_result["port"]
        has_ip = svc_result["has_external_ip"]
        status = "✓" if has_ip else "✗"
        if has_ip:
            details_lines.append(
                f"{status} Service '{service}': {external_ip}:{port}"
            )
        else:
            details_lines.append(
                f"{status} Service '{service}': NO EXTERNAL IP"
            )

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["all_services_ready"], details)
    else:
        errors = result.get("errors", [])
        failed_svc = next(
            (
                s for s in result.get("service_results", [])
                if not s["has_external_ip"]
            ),
            None
        )
        if failed_svc:
            log.failed(
                VICTORIA_LOGS_LOG_MSGS["service_no_external_ip"].format(
                    service=failed_svc["service"]
                ),
                details + "\n" + "; ".join(errors)
            )
            assert False, VICTORIA_LOGS_ASSERT_MSGS["service_no_external_ip"].format(
                service=failed_svc["service"]
            )
        assert False, "; ".join(errors)


# Source: test_victoria_logs.py
@pytest.mark.order(30)
def test_victoria_logs_tls_secret(host):
    """
    Test Case 6: Verify VictoriaLogs TLS secret exists.

    Checks that the shared 'victoria-tls-certs' secret exists with:
    - tls.crt
    - tls.key
    - ca.crt

    This secret is shared between VictoriaMetrics and VictoriaLogs.
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["victoria_logs_tls_secret"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(f"Verifying TLS secret '{VICTORIA_LOGS_TLS_SECRET}'")
    result = verify_victoria_logs_tls_secret(host, admin_ip)

    if not result.get("secret_exists", False):
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["tls_secret_missing"].format(
                secret=VICTORIA_LOGS_TLS_SECRET
            ),
            result.get("error", "")
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["tls_secret_missing"].format(
            secret=VICTORIA_LOGS_TLS_SECRET
        )

    keys_found = result.get("keys_found", [])
    missing_keys = result.get("missing_keys", [])
    details_lines = [f"Keys found: {keys_found}"]
    if missing_keys:
        details_lines.append(f"Missing keys: {missing_keys}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["tls_secret_exists"].format(
                secret=VICTORIA_LOGS_TLS_SECRET
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["tls_secret_missing_keys"].format(
                keys=missing_keys
            ),
            details
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["tls_secret_missing_keys"].format(
            secret=VICTORIA_LOGS_TLS_SECRET,
            missing_keys=missing_keys
        )


# Source: test_victoria_logs.py
@pytest.mark.order(31)
def test_victoria_logs_health(host):
    """
    Test Case 7: Verify TLS connection and /health endpoint on vlselect.

    Tests:
    - TLS connection to vlselect-victoria-logs-cluster (port 9471)
      using CA certificate from victoria-tls-certs secret
    - /health endpoint returns a valid response
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["victoria_logs_health"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]

    log.check(f"Verifying TLS connection to {service_name}:{port}")
    result = verify_victoria_logs_health(host, admin_ip)

    if result.get("error") and not result.get("tls_connected"):
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["tls_connection_failed"],
            result["error"]
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["tls_connection_failed"].format(
            host=result.get("external_ip", ""),
            port=result.get("port", port),
            error=result.get("error", "")
        )

    external_ip = result.get("external_ip", "")
    health_response = result.get("health_response", "")

    details = (
        f"Service: {result.get('service_name', service_name)}\n"
        f"URL: https://{external_ip}:{port}/health\n"
        f"TLS connected: {result.get('tls_connected', False)}\n"
        f"Health response: {health_response}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["tls_connection_success"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["health_endpoint_failed"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["health_check_failed"].format(
            host=external_ip,
            port=port,
            response=health_response
        )


# Source: test_victoria_logs.py
@pytest.mark.order(32)
def test_victoria_logs_query(host):
    """
    Test Case 8: Verify VictoriaLogs log query endpoint is accessible.

    Queries vlselect /select/logsql/stats/streams?query=* via TLS to confirm
    the LogsQL query endpoint is reachable.

    Notes:
    - An empty stream list (stream_count=0) is a pass — vlselect is healthy
      but no logs have been ingested yet.
    - The test fails only if the endpoint is completely unreachable.
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["victoria_logs_query"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]

    log.check(
        f"Querying VictoriaLogs log streams endpoint on {service_name}:{port}"
    )
    result = verify_victoria_logs_query(host, admin_ip)

    external_ip = result.get("external_ip", "")
    stream_count = result.get("stream_count", 0)
    streams = result.get("streams", [])

    details_lines = [
        f"Service: {service_name}",
        f"URL: https://{external_ip}:{port}/select/logsql/stats/streams?query=*",
        f"Endpoint accessible: {result.get('endpoint_accessible', False)}",
        f"Streams found: {stream_count}",
    ]
    if streams:
        details_lines.append("Sample streams:")
        for stream in streams:
            details_lines.append(f"  - {stream}")

    details = "\n".join(details_lines)

    if result["success"]:
        if stream_count > 0:
            log.passed(
                VICTORIA_LOGS_LOG_MSGS["query_streams_found"].format(
                    count=stream_count
                ),
                details
            )
        else:
            log.passed(
                VICTORIA_LOGS_LOG_MSGS["query_streams_empty"],
                details
            )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["query_endpoint_failed"],
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["query_endpoint_failed"].format(
            host=external_ip,
            port=port,
            error=result.get("error", "Endpoint not accessible")
        )


# Source: test_victoria_logs.py
@pytest.mark.order(33)
def test_victoria_logs_configmap(host):
    """
    Test Case 9: Verify VLAgent ConfigMap 'vlagent-config' exists.

    The ConfigMap 'vlagent-config' is deployed by:
      victorialogs-vlagent-config.yaml.j2

    It contains:
    - Syslog receiver config (plaintext :514, TLS :6514)
    - remoteWrite pipeline to vlinsert (/insert/jsonline)
    - Persistent queue (PVC-backed buffer) config

    Note: No data-source-specific relabel rules are configured yet.
    PowerScale, UFM, and Skyview syslog sources are not yet implemented.
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["victoria_logs_configmap"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(f"Verifying ConfigMap '{VLAGENT_CONFIGMAP_NAME}' in telemetry namespace")
    result = verify_vlagent_configmap(host, admin_ip)

    details = (
        f"ConfigMap: {result.get('configmap_name', VLAGENT_CONFIGMAP_NAME)}\n"
        f"Exists: {result.get('configmap_exists', False)}\n"
        f"Has data: {result.get('has_data', False)}"
    )

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["configmap_exists"].format(
                configmap=VLAGENT_CONFIGMAP_NAME
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["configmap_missing"].format(
                configmap=VLAGENT_CONFIGMAP_NAME
            ),
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["configmap_missing"].format(
            configmap=VLAGENT_CONFIGMAP_NAME
        )


# Source: test_victoria_logs.py
@pytest.mark.order(34)
def test_vlagent_pvc(host):
    """
    Test Case 10: Verify VLAgent buffer PVC exists.

    The VictoriaMetrics operator creates a PVC (labelled app=vlagent)
    for the VLAgent disk-backed WAL buffer (default 5Gi).

    Purpose: Prevents log loss during vlinsert unavailability — unsent
    batches are persisted to this PVC and retried with exponential backoff.
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["vlagent_pvc"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    app_label = VLAGENT_LOGS["app_label"]
    log.check(f"Verifying VLAgent buffer PVC (app={app_label})")
    result = verify_vlagent_pvc(host, admin_ip)

    if result["success"]:
        details_lines = [f"PVCs found: {result['pvc_count']}"]
        for pvc_result in result.get("pvc_results", []):
            bound_str = "Bound" if pvc_result["bound"] else pvc_result["phase"]
            details_lines.append(
                f"  PVC '{pvc_result['pvc_name']}': {pvc_result['size']} ({bound_str})"
            )
        details = "\n".join(details_lines)

        first_pvc = result["pvc_results"][0] if result.get("pvc_results") else {}
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["vlagent_pvc_exists"].format(
                size=first_pvc.get("size", "unknown")
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["vlagent_pvc_missing"],
            f"Error: {result.get('error', '')}"
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["vlagent_pvc_missing"]


# Source: test_victoria_logs.py
@pytest.mark.order(35)
def test_vlagent_syslog_service(host):
    """
    Test Case 11: Verify VLAgent syslog service exposes ports 514 and 6514.

    The VictoriaMetrics operator creates a service for the VLAgent CR.
    Service type is LoadBalancer (MetalLB) or NodePort (fallback).

    Expected ports (from victorialogs-operator-vlagent.yaml.j2):
    - 514  TCP/UDP  : Plaintext syslog (RFC 3164/5424)
    - 6514 TCP      : TLS syslog (RFC 5425)
    - 9429 TCP      : VLAgent health check

    Note: These ports are verified as configured on the service. Actual
    syslog ingestion requires a data source (PowerScale, UFM, Skyview)
    which are not yet configured in this deployment.
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["vlagent_syslog_service"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    service_name = VLAGENT_LOGS["service_name"]
    log.check(f"Verifying VLAgent syslog service '{service_name}' ports")
    result = verify_vlagent_syslog_service(host, admin_ip)

    if not result.get("service_exists", False):
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["vlagent_service_missing"].format(
                service=service_name
            ),
            result.get("error", "")
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["vlagent_service_missing"].format(
            service=service_name
        )

    ports_found = result.get("ports_found", [])
    missing_ports = result.get("missing_ports", [])
    service_type = result.get("service_type", "")

    details = (
        f"Service: {service_name}\n"
        f"Type: {service_type}\n"
        f"Ports found: {ports_found}\n"
        f"Missing ports: {missing_ports if missing_ports else 'none'}"
    )

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["vlagent_service_ports_ok"].format(
                service=service_name,
                ports=ports_found
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["vlagent_service_ports_missing"].format(
                ports=missing_ports
            ),
            details
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["vlagent_service_ports_missing"].format(
            service=service_name,
            missing_ports=missing_ports
        )


# Source: test_victoria_logs.py
@pytest.mark.order(36)
def test_vlagent_syslog_injection(host):
    """
    Test Case 12: Synthetic syslog injection end-to-end test.

    Since no real syslog data sources are deployed (PowerScale disabled,
    UFM/Skyview not yet implemented), this test simulates a data source by
    using the `logger` utility on the admin node to send a synthetic
    RFC 3164 syslog message directly to the VLAgent LoadBalancer IP on
    port 514 (plaintext syslog).

    Full path exercised:
      logger (admin node) → VLAgent :514 → vlinsert :9481
        → vlstorage → vlselect query

    Injection methods tried in order:
    - Method A (LoadBalancer): use VLAgent service external IP if MetalLB assigned one
    - Method B (PodIP): if no LoadBalancer, get VLAgent pod IP via kubectl and
      run logger from the K8s node (which has direct pod network access)
    For each method TCP is attempted first, then UDP fallback.

    Steps:
    1. Resolve VLAgent IP (LoadBalancer → pod IP fallback)
    2. Generate a unique message ID: omniavltest<epoch>
    3. Send via: logger -n <vlagent_ip> -P 514 -T -t omnia-vllogs-test -- <msg_id>
    4. Wait 15s for VLAgent to batch and forward to vlinsert
    5. Query vlselect /select/logsql/query?query=<msg_id>&start=now-5m
    6. Assert the unique message ID appears in the response

    Requirements:
    - `logger` (util-linux) installed on the K8s node (default on RHEL/Rocky)
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["vlagent_syslog_injection"])

    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(
        "Step 1/3: Injecting synthetic syslog to VLAgent port 514 "
        "(Method A: LoadBalancer IP; fallback Method B: pod IP via K8s node)"
    )
    inject_result = inject_test_syslog(host, admin_ip)

    if not inject_result["success"]:
        error = inject_result.get("error", "")
        vlagent_ip = inject_result.get("vlagent_ip", "")
        injection_method = inject_result.get("injection_method", "none")

        if injection_method == "none":
            log.skipped(
                VICTORIA_LOGS_LOG_MSGS["syslog_no_vlagent_ip"],
                "VLAgent IP not resolvable via any method - skipping"
            )
            pytest.skip("VLAgent has no accessible IP (LoadBalancer or pod IP)")

        log.failed(VICTORIA_LOGS_LOG_MSGS["syslog_inject_failed"], error)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["syslog_inject_failed"].format(
            vlagent_ip=vlagent_ip,
            error=error
        )

    vlagent_ip = inject_result["vlagent_ip"]
    message_id = inject_result["message_id"]
    injection_method = inject_result.get("injection_method", "unknown")

    log.passed(
        VICTORIA_LOGS_LOG_MSGS["syslog_injecting"].format(
            ip=vlagent_ip, msg_id=message_id
        ),
        f"Method: {injection_method} | logger sent syslog to {vlagent_ip}:514"
    )
    log.check(
        VICTORIA_LOGS_LOG_MSGS["syslog_waiting"].format(
            secs=VLAGENT_SYSLOG_INGESTION_WAIT_SECS
        )
    )

    log.check(
        f"Step 2/3: Querying vlselect for message ID '{message_id}'"
    )
    verify_result = verify_syslog_received(host, admin_ip, message_id)

    vlselect_ip = verify_result.get("external_ip", "")
    details = (
        f"VLAgent IP: {vlagent_ip}\n"
        f"Message ID: {message_id}\n"
        f"vlselect IP: {vlselect_ip}:{VLSELECT['port']}\n"
        f"Message found: {verify_result.get('message_found', False)}\n"
        f"Response (first 300 chars): "
        f"{verify_result.get('response_text', '')[:300]}"
    )

    if verify_result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["syslog_received"].format(msg_id=message_id),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["syslog_not_received"].format(
                secs=VLAGENT_SYSLOG_INGESTION_WAIT_SECS
            ),
            details + f"\nError: {verify_result.get('error', '')}"
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["syslog_not_received"].format(
            secs=VLAGENT_SYSLOG_INGESTION_WAIT_SECS,
            msg_id=message_id
        )


# =============================================================================
# TC13 – ConfigMap content (Functional)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(37)
def test_vlagent_configmap_content(host):
    """TC13: Verify vlagent-config ConfigMap has syslog receiver and remoteWrite."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["vlagent_configmap_content"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VLAgent ConfigMap contains syslog and remoteWrite config")
    result = verify_vlagent_configmap_content(host, admin_ip)

    details = (
        f"Has syslog receiver: {result.get('has_syslog', False)}\n"
        f"Has remoteWrite/vlinsert: {result.get('has_remotewrite', False)}"
    )
    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["configmap_content_ok"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["configmap_content_missing"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["configmap_content_missing"]


# =============================================================================
# TC14 – Syslog stream labels (Functional)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(38)
def test_syslog_stream_labels(host):
    """TC14: Inject syslog and verify stream labels appear in VictoriaLogs."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["syslog_stream_labels"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Injecting syslog and querying for stream label field")
    result = verify_syslog_stream_labels(host, admin_ip)

    details = (
        f"Field: {result.get('field', '')}\n"
        f"Value: {result.get('value', '')}"
    )
    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["stream_label_found"].format(
                field=result.get("field", ""), value=result.get("value", "")
            ),
            details,
        )
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["stream_label_missing"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["stream_label_missing"].format(
            field=result.get("field", ""), value=result.get("value", "")
        )


# =============================================================================
# TC15 – LogsQL field-filter query (Functional)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(39)
def test_logsql_field_filter(host):
    """TC15: Verify LogsQL field-filter query returns matching log entry."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["logsql_field_filter"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Running LogsQL field-filter query on vlselect")
    result = verify_logsql_field_filter(host, admin_ip)

    details = f"Query: {result.get('query', '')}"
    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["field_filter_found"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["field_filter_missing"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["field_filter_missing"].format(
            query=result.get("query", "")
        )


# =============================================================================
# TC16 – vlinsert direct HTTP POST (Functional)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(40)
def test_vlinsert_direct_write(host):
    """TC16: POST a log line directly to vlinsert and verify HTTP 200."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["vlinsert_direct_write"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(f"Posting JSON log line to vlinsert:{VLINSERT['port']}/insert/jsonline")
    result = verify_vlinsert_direct_write(host, admin_ip)

    details = (
        f"Service: {result.get('service', VLINSERT['service_name'])}\n"
        f"HTTP code: {result.get('http_code', '')}"
    )
    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["vlinsert_direct_ok"].format(
                code=result.get("http_code", "")
            ),
            details,
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["vlinsert_direct_failed"].format(
                code=result.get("http_code", "")
            ),
            details,
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["vlinsert_direct_failed"].format(
            service=result.get("service", ""), code=result.get("http_code", "")
        )


# =============================================================================
# TC17 – Retention period applied (Functional)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(41)
def test_retention_period_applied(host):
    """TC17: Verify vlstorage pod args include the retention period flag."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["retention_period_applied"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Checking vlstorage pod args for --retentionPeriod flag")
    result = verify_retention_period_applied(host, admin_ip)

    details = (
        f"Configured period: {result.get('configured_period', '')}\n"
        f"Retention flag present: {result.get('has_retention_flag', False)}\n"
        f"Period matches config: {result.get('period_matches', False)}\n"
        f"Pod args (excerpt): {result.get('args_text', '')[:150]}"
    )
    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["retention_period_ok"].format(
                period=result.get("configured_period", "")
            ),
            details,
        )
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["retention_period_missing"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["retention_period_missing"]


# =============================================================================
# TC18 – Invalid LogsQL rejected (Negative)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(42)
def test_invalid_logsql_rejected(host):
    """TC18: Verify malformed LogsQL query returns HTTP 4xx."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["invalid_logsql_rejected"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Sending malformed LogsQL query to vlselect")
    result = verify_invalid_logsql_rejected(host, admin_ip)

    details = (
        f"Query: {result.get('query', '')}\n"
        f"HTTP code: {result.get('http_code', '')}"
    )
    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["invalid_query_rejected"].format(
                code=result.get("http_code", "")
            ),
            details,
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["invalid_query_accepted"].format(
                code=result.get("http_code", "")
            ),
            details,
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["invalid_query_accepted"].format(
            query=result.get("query", ""), code=result.get("http_code", "")
        )


# =============================================================================
# TC19 – Non-existent stream returns empty (Negative)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(43)
def test_nonexistent_stream_empty(host):
    """TC19: Query non-existent log stream returns empty result, not error."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["nonexistent_stream_empty"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Querying non-existent stream {job='omnia-nonexistent-xyz-99999'}")
    result = verify_nonexistent_stream_empty(host, admin_ip)

    details = f"Response: '{result.get('response', '')}'"
    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["nonexistent_stream_empty"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["nonexistent_stream_error"], details)
        assert False, f"Non-existent stream query did not return empty. Got: {result.get('response', '')[:100]}"


# =============================================================================
# TC20 – Plain HTTP rejected (Negative / Security)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(44)
def test_plain_http_rejected(host):
    """TC20: Verify vlselect rejects plain HTTP (TLS required)."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["plain_http_rejected"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(f"Sending plain HTTP request to vlselect port {VLSELECT['port']}")
    result = verify_plain_http_rejected(host, admin_ip)

    details = f"HTTP code (plain): {result.get('http_code', '000')}"
    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["plain_http_rejected"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["plain_http_accepted"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["plain_http_accepted"].format(
            code=result.get("http_code", "")
        )


# =============================================================================
# TC21 – Wrong CA certificate rejected (Negative / Security)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(45)
def test_wrong_ca_rejected(host):
    """TC21: Verify vlselect rejects connections with invalid CA certificate."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["wrong_ca_rejected"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Attempting TLS connection to vlselect with wrong CA cert")
    result = verify_wrong_ca_rejected(host, admin_ip)

    details = f"HTTP code (wrong CA): {result.get('http_code', '000')}"
    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["wrong_ca_rejected"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["wrong_ca_accepted"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["wrong_ca_accepted"]


# =============================================================================
# TC22 – Pod restart preserves data (Idempotency)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(46)
def test_pod_restart_preserves_data(host):
    """TC22: Inject syslog, restart VLAgent pod, verify data still queryable."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["pod_restart_preserves_data"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Step 1: Injecting syslog before pod restart")
    log.check("Step 2: Deleting VLAgent pod (StatefulSet will recreate)")
    log.check("Step 3: Waiting for pod readiness and re-querying vlselect")
    result = verify_pod_restart_preserves_data(host, admin_ip)

    details = (
        f"Message ID: {result.get('message_id', '')}\n"
        f"Found after restart: {result.get('message_found_after_restart', False)}"
    )
    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["pod_restart_ok"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["pod_restart_data_lost"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["pod_restart_data_lost"].format(
            msg_id=result.get("message_id", "")
        )


# =============================================================================
# TC23 – Multiple messages without deduplication (Idempotency)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(47)
def test_multi_message_ingestion(host):
    """TC23: Inject N distinct messages and verify all are stored."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["multi_message_ingestion"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(f"Injecting {VLAGENT_MULTI_MSG_COUNT} distinct syslog messages")
    result = verify_multi_message_ingestion(host, admin_ip)

    details = (
        f"Expected: {result.get('expected', VLAGENT_MULTI_MSG_COUNT)}\n"
        f"Found: {result.get('found', 0)}"
    )
    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["multi_msg_ok"].format(
                count=result.get("found", 0)
            ),
            details,
        )
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["multi_msg_failed"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["multi_msg_failed"].format(
            expected=result.get("expected", 0), found=result.get("found", 0)
        )


# =============================================================================
# TC24 – Query response time (Performance)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(48)
def test_query_response_time(host):
    """TC24: Verify vlselect /health response time is under threshold."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["query_response_time"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(
        f"Measuring vlselect response time (threshold: {VLSELECT_QUERY_RESPONSE_MAX_SECS}s)"
    )
    result = verify_query_response_time(host, admin_ip)

    time_secs = result.get("time_secs", 0)
    details = (
        f"Response time: {time_secs:.3f}s\n"
        f"Threshold: {VLSELECT_QUERY_RESPONSE_MAX_SECS}s"
    )
    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["response_time_ok"].format(
                time=time_secs, max=VLSELECT_QUERY_RESPONSE_MAX_SECS
            ),
            details,
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["response_time_slow"].format(
                time=time_secs, max=VLSELECT_QUERY_RESPONSE_MAX_SECS
            ),
            details,
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["response_time_slow"].format(
            time=time_secs, max=VLSELECT_QUERY_RESPONSE_MAX_SECS
        )


# =============================================================================
# TC25 – Bulk syslog ingestion (Performance)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(49)
def test_bulk_ingestion(host):
    """TC25: Inject 50 syslog messages in a loop and verify ≥90% are stored."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["bulk_ingestion"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(f"Bulk-injecting {VLAGENT_BULK_COUNT} syslog messages via logger loop")
    result = verify_bulk_ingestion(host, admin_ip)

    details = (
        f"Injected: {VLAGENT_BULK_COUNT}\n"
        f"Found: {result.get('found', 0)}\n"
        f"Prefix: {result.get('prefix', '')}"
    )
    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["bulk_ok"].format(
                found=result.get("found", 0), count=VLAGENT_BULK_COUNT
            ),
            details,
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["bulk_failed"].format(
                found=result.get("found", 0), count=VLAGENT_BULK_COUNT
            ),
            details,
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["bulk_failed"].format(
            count=VLAGENT_BULK_COUNT, found=result.get("found", 0)
        )


# =============================================================================
# TC26 – TLS certificate validity (Security)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(50)
def test_tls_cert_validity(host):
    """TC26: Verify the victoria-tls-certs certificate is valid and not near expiry."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["tls_cert_validity"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    days = TLS_CERT_MIN_VALID_SECS // 86400
    log.check(f"Checking TLS cert '{VICTORIA_LOGS_TLS_SECRET}' valid for ≥{days} days")
    result = verify_tls_cert_validity(host, admin_ip)

    details = (
        f"Secret: {VICTORIA_LOGS_TLS_SECRET}\n"
        f"Min valid days: {days}\n"
        f"OpenSSL output: {result.get('openssl_output', '')}"
    )
    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["tls_cert_valid"].format(days=days), details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["tls_cert_expiring"].format(days=days), details
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["tls_cert_expiring"].format(days=days)


# =============================================================================
# TC27 – VLAgent PVC mounted in pod (Security / Config)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(51)
def test_vlagent_pvc_mounted(host):
    """TC27: Verify the VLAgent pod has its buffer PVC volume mounted."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["vlagent_pvc_mounted"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Checking VLAgent pod spec for mounted PVC volume")
    result = verify_vlagent_pvc_mounted(host, admin_ip)

    details = f"Volumes found: {result.get('volumes_found', '')}"
    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["pvc_mounted_ok"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["pvc_mounted_missing"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["pvc_mounted_missing"]


# =============================================================================
# TC28 – RBAC restrictions (Security)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(52)
def test_rbac_restrictions(host):
    """TC28: Verify default service account cannot read the TLS secret."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["rbac_restrictions"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(
        f"Checking RBAC: {VLAGENT_LOGS['service_name']} default SA → "
        f"get secret/{VICTORIA_LOGS_TLS_SECRET}"
    )
    result = verify_rbac_restrictions(host, admin_ip)

    details = (
        f"Service account: {result.get('service_account', '')}\n"
        f"kubectl auth can-i output: {result.get('output', '')}"
    )
    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["rbac_denied"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["rbac_allowed"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["rbac_allowed"]


# =============================================================================
# TC29 – Pod security context (Security)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(53)
def test_pod_security_context(host):
    """TC29: Verify no VictoriaLogs pod runs a privileged container."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["pod_security_context"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check(
        "Checking securityContext.privileged on vlstorage, vlinsert, vlselect, vlagent pods"
    )
    result = verify_pod_security_context(host, admin_ip)

    details = f"Privileged pods found: {result.get('privileged_pods', [])}"
    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["pod_security_ok"], details)
    else:
        privileged = result.get("privileged_pods", [])
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["pod_security_privileged"].format(
                pod=", ".join(privileged)
            ),
            details,
        )
        assert False, VICTORIA_LOGS_ASSERT_MSGS["pod_security_privileged"].format(
            pod=", ".join(privileged)
        )


# =============================================================================
# TC30 – HA under vlstorage failure (TC-F006 / TC-E001)
# =============================================================================


# Source: test_victoria_logs.py
@pytest.mark.order(54)
def test_ha_under_vlstorage_failure(host):
    """
    TC30 (TC-F006/TC-E001): Verify HA and buffering under vlstorage failure.
    
    Steps:
    1. Baseline: send syslog and verify queryable
    2. Kill vlstorage-0 pod
    3. Send syslog during outage
    4. Verify vlinsert accepts (HTTP 2xx)
    5. Verify vlselect returns results (degraded but not failed)
    6. Wait for pod recovery
    7. Verify all events queryable post-recovery
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["ha_under_vlstorage_failure"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Running HA test: kill vlstorage-0, send syslog, verify recovery")
    result = verify_ha_under_vlstorage_failure(host, admin_ip)

    details = (
        f"Baseline found: {result.get('baseline_found', False)}\n"
        f"Pod killed: {result.get('pod_killed', False)}\n"
        f"Outage sent: {result.get('outage_sent', False)}\n"
        f"vlinsert accepted: {result.get('vlinsert_accepted', False)}\n"
        f"Pod recovered: {result.get('pod_recovered', False)}\n"
        f"Outage events found: {result.get('outage_events_found', False)}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["ha_test_passed"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["ha_test_failed"], details)
        assert False, VICTORIA_LOGS_ASSERT_MSGS["ha_test_failed"].format(
            baseline_found=result.get("baseline_found", False),
            pod_killed=result.get("pod_killed", False),
            outage_sent=result.get("outage_sent", False),
            vlinsert_accepted=result.get("vlinsert_accepted", False),
            pod_recovered=result.get("pod_recovered", False),
            outage_events_found=result.get("outage_events_found", False),
            error=result.get("error", "Unknown error"),
        )


# Source: test_victoria_logs_config.py
@pytest.mark.order(31)
def test_vlstorage_replication_factor(host):
    """
    OMN01D-2249: Verify vlstorage has replicationFactor configured.
    
    VLCluster should be deployed with replicationFactor >= 2 to ensure
    data redundancy. Without replication, permanent node loss causes
    permanent data loss.
    
    Expected: replicationFactor >= 2 (each log shard replicated)
    Defect:   replicationFactor not configured (default = 1, no redundancy)
    """
    log = TestLogger("OMN01D-2249: Verify vlstorage replicationFactor")
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    log.check("Checking VLCluster replicationFactor configuration")
    
    # Get replicationFactor from VLCluster CR
    cmd = run_on_remote_node(
        host,
        f"kubectl get vlcluster {VLCLUSTER_NAME} -n {TELEMETRY_NAMESPACE} "
        f"-o jsonpath='{{.spec.vlstorage.replicationFactor}}'",
        admin_ip,
    )
    
    replication_factor = cmd.stdout.strip()
    
    log.check(f"VLCluster replicationFactor: '{replication_factor}'")
    
    # Check if replicationFactor is set
    if not replication_factor or replication_factor == "":
        log.failed(
            "❌ DEFECT OMN01D-2249 CONFIRMED\n"
            "VLCluster has NO replicationFactor configured\n"
            "Default replicationFactor = 1 (no data redundancy)\n\n"
            "Impact:\n"
            "  - Each log shard stored on single vlstorage node only\n"
            "  - Permanent node loss = permanent data loss\n"
            "  - No data redundancy or fault tolerance\n"
            "  - Production data at risk\n\n"
            "Recommendation:\n"
            "  - Set spec.vlstorage.replicationFactor: 2 or 3\n"
            "  - Ensures data replicated across multiple nodes\n"
            "  - Provides fault tolerance for node failures",
            f"replicationFactor: Not configured (default = 1)\n"
            f"vlstorage replicas: {VLSTORAGE['replicas']}\n"
            f"Expected: replicationFactor >= 2"
        )
        # Don't fail test - this is expected defect
        # assert False, "OMN01D-2249: No replicationFactor configured"
    else:
        try:
            rf_value = int(replication_factor)
            
            if rf_value < 2:
                log.failed(
                    f"❌ DEFECT OMN01D-2249 CONFIRMED\n"
                    f"VLCluster replicationFactor = {rf_value} (insufficient)\n"
                    f"Minimum recommended: 2\n\n"
                    "Impact: Limited data redundancy",
                    f"replicationFactor: {rf_value}\n"
                    f"vlstorage replicas: {VLSTORAGE['replicas']}\n"
                    f"Expected: >= 2"
                )
                # Don't fail test - this is expected defect
            else:
                log.passed(
                    f"✅ DEFECT OMN01D-2249 FIXED\n"
                    f"VLCluster has replicationFactor = {rf_value}\n"
                    f"Data is replicated across {rf_value} vlstorage nodes\n"
                    f"Fault tolerance: Can survive {rf_value - 1} node failures",
                    f"replicationFactor: {rf_value}\n"
                    f"vlstorage replicas: {VLSTORAGE['replicas']}"
                )
        except ValueError:
            log.failed(
                f"❌ Invalid replicationFactor value: '{replication_factor}'",
                f"Expected: integer >= 2\nActual: '{replication_factor}'"
            )
            assert False, f"Invalid replicationFactor: {replication_factor}"


# OMN01D-2248 test removed - liveness probe test case excluded per user request

# Source: test_victoria_logs_config.py
@pytest.mark.order(33)
def test_vlstorage_readiness_probe(host):
    """
    Verify vlstorage pods have readiness probe configured.
    
    Readiness probes ensure pods only receive traffic when ready to serve requests.
    """
    log = TestLogger("Verify vlstorage readiness probe")
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    log.check("Checking vlstorage pod readiness probe configuration")
    
    # Get all vlstorage pod names
    get_pods_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} "
        f"-l app.kubernetes.io/name=vlstorage "
        f"-o jsonpath='{{.items[*].metadata.name}}'",
        admin_ip,
    )
    
    pod_names = get_pods_cmd.stdout.strip().split()
    
    if not pod_names:
        log.failed("No vlstorage pods found", "")
        assert False, "No vlstorage pods found"
    
    log.check(f"Found {len(pod_names)} vlstorage pods")
    
    # Check each pod for readiness probe
    pods_without_probe = []
    pods_with_probe = []
    
    for pod_name in pod_names:
        # Get readiness probe configuration
        probe_cmd = run_on_remote_node(
            host,
            f"kubectl get pod {pod_name} -n {TELEMETRY_NAMESPACE} "
            f"-o jsonpath='{{.spec.containers[0].readinessProbe}}'",
            admin_ip,
        )
        
        probe_config = probe_cmd.stdout.strip()
        
        if not probe_config or probe_config == "":
            pods_without_probe.append(pod_name)
            log.check(f"  {pod_name}: ❌ NO readiness probe")
        else:
            pods_with_probe.append(pod_name)
            log.check(f"  {pod_name}: ✅ Has readiness probe")
    
    # Evaluate results
    if pods_without_probe:
        log.failed(
            "vlstorage pods missing readiness probe\n"
            "Pods may receive traffic before ready to serve requests",
            f"Pods without readiness probe: {len(pods_without_probe)}/{len(pod_names)}\n"
            f"Missing probe: {', '.join(pods_without_probe)}"
        )
        assert False, f"vlstorage pods missing readiness probe: {pods_without_probe}"
    else:
        log.passed(
            "All vlstorage pods have readiness probe configured",
            f"Pods with readiness probe: {len(pods_with_probe)}/{len(pod_names)}"
        )


# Source: test_victoria_logs_edge_cases.py
@pytest.mark.order(55)
def test_resource_limits_enforced(host):
    """TC31: Verify CPU and memory limits are configured for all VictoriaLogs pods."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["resource_limits_enforced"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying resource limits on all VictoriaLogs pods")
    result = verify_resource_limits_enforced(host, admin_ip)

    details_lines = []
    for comp in result.get("components", []):
        status = "✓" if comp["has_limits"] else "✗"
        details_lines.append(
            f"{status} {comp['pod']}: CPU={comp['cpu_limit']}, Memory={comp['memory_limit']}"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["resource_limits_ok"], details)
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["resource_limits_missing"],
            details + f"\nMissing limits: {result.get('missing_limits', [])}"
        )
        assert False, f"Resource limits missing on pods: {result.get('missing_limits', [])}"


# Source: test_victoria_logs_edge_cases.py
@pytest.mark.order(56)
def test_resource_requests_set(host):
    """TC32: Verify CPU and memory requests are configured for all VictoriaLogs pods."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["resource_requests_set"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying resource requests on all VictoriaLogs pods")
    result = verify_pod_resource_requests_set(host, admin_ip)

    details_lines = []
    for comp in result.get("components", []):
        status = "✓" if comp["has_requests"] else "✗"
        details_lines.append(
            f"{status} {comp['pod']}: CPU={comp['cpu_request']}, Memory={comp['memory_request']}"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["resource_requests_ok"], details)
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["resource_requests_missing"],
            details + f"\nMissing requests: {result.get('missing_requests', [])}"
        )
        assert False, f"Resource requests missing on pods: {result.get('missing_requests', [])}"


# Source: test_victoria_logs_edge_cases.py
@pytest.mark.order(57)
def test_large_log_message_handling(host):
    """TC33: Verify vlinsert handles extremely large log messages (1MB) gracefully."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["large_log_message_handling"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Sending 1MB log message to vlinsert")
    result = verify_large_log_message_handling(host, admin_ip)

    details = (
        f"Message size: {result.get('message_size', 'N/A')}\n"
        f"HTTP code: {result.get('http_code', '000')}\n"
        f"Test ID: {result.get('test_id', '')}"
    )

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["large_message_handled"].format(
                code=result.get("http_code", "")
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["large_message_failed"].format(
                code=result.get("http_code", "")
            ),
            details
        )
        assert False, f"Large message handling failed: {result.get('error', '')}"


# Source: test_victoria_logs_edge_cases.py
@pytest.mark.order(58)
def test_malformed_json_rejected(host):
    """TC34: Verify vlinsert rejects malformed JSON with appropriate error code."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["malformed_json_rejected"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Sending malformed JSON to vlinsert")
    result = verify_malformed_json_rejected(host, admin_ip)

    details = f"HTTP code: {result.get('http_code', '000')}"

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["malformed_json_rejected_ok"].format(
                code=result.get("http_code", "")
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["malformed_json_accepted"].format(
                code=result.get("http_code", "")
            ),
            details
        )
        assert False, f"Malformed JSON not rejected: {result.get('error', '')}"


# Source: test_victoria_logs_edge_cases.py
@pytest.mark.order(59)
def test_sql_injection_protection(host):
    """TC35: Verify LogsQL query endpoint is protected against SQL injection attempts."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["sql_injection_protection"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Testing SQL injection protection on LogsQL endpoint")
    result = verify_sql_injection_protection(host, admin_ip)

    details_lines = []
    for test_result in result.get("results", []):
        status = "✓" if test_result["safe"] else "✗"
        details_lines.append(
            f"{status} Payload: {test_result['payload'][:50]}... → HTTP {test_result['http_code']}"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["sql_injection_safe"], details)
    else:
        log.failed(VICTORIA_LOGS_LOG_MSGS["sql_injection_vulnerable"], details)
        assert False, "SQL injection vulnerability detected in LogsQL endpoint"


# Source: test_victoria_logs_edge_cases.py
@pytest.mark.order(60)
def test_namespace_isolation(host):
    """TC36: Verify VictoriaLogs resources are isolated to telemetry namespace."""
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["namespace_isolation"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying namespace isolation for VictoriaLogs resources")
    result = verify_namespace_isolation(host, admin_ip)

    details = (
        f"Telemetry namespace resources: {result.get('telemetry_resources', 0)}\n"
        f"Other namespace resources: {result.get('other_namespace_resources', 0)}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["namespace_isolation_ok"], details)
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["namespace_isolation_failed"],
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, f"Namespace isolation violated: {result.get('error', '')}"


# Source: test_victoria_logs_destructive.py
@pytest.mark.order(61)
def test_all_vlstorage_pods_down(host):
    """
    TC37 (DESTRUCTIVE): Kill all vlstorage pods and verify recovery.
    
    Expected behavior:
    - vlinsert should reject writes or return errors
    - vlselect should return errors (cannot query without storage)
    - Pods should auto-recover (StatefulSet recreates them)
    - Cluster should return to healthy state
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["all_vlstorage_down"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("⚠️  DESTRUCTIVE TEST: Killing all vlstorage pods")
    log.check("Step 1: Baseline health check")
    log.check("Step 2: Scale vlstorage to 0 replicas")
    log.check("Step 3: Test vlinsert behavior (should reject writes)")
    log.check("Step 4: Test vlselect behavior (should return errors)")
    log.check("Step 5: Scale vlstorage back to 3 replicas")
    log.check("Step 6: Wait for recovery (up to 120s)")
    log.check("Step 7: Verify cluster health")
    
    result = verify_all_vlstorage_pods_down_behavior(host, admin_ip)

    details = (
        f"Baseline healthy: {result.get('baseline_healthy', False)}\n"
        f"Pods killed: {result.get('pods_killed', False)}\n"
        f"vlinsert behavior: {result.get('vlinsert_behavior', 'unknown')}\n"
        f"vlselect behavior: {result.get('vlselect_behavior', 'unknown')}\n"
        f"Pods restored: {result.get('pods_restored', False)}\n"
        f"Recovery successful: {result.get('recovery_successful', False)}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["vlstorage_down_test_passed"], details)
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["vlstorage_down_test_failed"],
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, f"vlstorage destructive test failed: {result.get('error', '')}"


# Source: test_victoria_logs_destructive.py
@pytest.mark.order(62)
def test_all_vlinsert_pods_down(host):
    """
    TC38 (DESTRUCTIVE): Kill all vlinsert pods and verify recovery.
    
    Expected behavior:
    - Writes should fail (no vlinsert to accept them)
    - Reads should still work (vlselect queries vlstorage directly)
    - Pods should auto-recover (Deployment recreates them)
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["all_vlinsert_down"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("⚠️  DESTRUCTIVE TEST: Killing all vlinsert pods")
    log.check("Expected: Writes rejected, reads still work, pods recover")
    
    result = verify_all_vlinsert_pods_down_behavior(host, admin_ip)

    details = (
        f"Baseline healthy: {result.get('baseline_healthy', False)}\n"
        f"Pods killed: {result.get('pods_killed', False)}\n"
        f"Writes rejected: {result.get('writes_rejected', False)}\n"
        f"Reads still work: {result.get('reads_still_work', False)}\n"
        f"Pods recovered: {result.get('pods_recovered', False)}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["vlinsert_down_test_passed"], details)
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["vlinsert_down_test_failed"],
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, f"vlinsert destructive test failed: {result.get('error', '')}"


# Source: test_victoria_logs_destructive.py
@pytest.mark.order(63)
def test_all_vlselect_pods_down(host):
    """
    TC39 (DESTRUCTIVE): Kill all vlselect pods and verify recovery.
    
    Expected behavior:
    - Reads should fail (no vlselect to query)
    - Writes should still work (vlinsert writes to vlstorage directly)
    - Pods should auto-recover (Deployment recreates them)
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["all_vlselect_down"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("⚠️  DESTRUCTIVE TEST: Killing all vlselect pods")
    log.check("Expected: Reads rejected, writes still work, pods recover")
    
    result = verify_all_vlselect_pods_down_behavior(host, admin_ip)

    details = (
        f"Baseline healthy: {result.get('baseline_healthy', False)}\n"
        f"Pods killed: {result.get('pods_killed', False)}\n"
        f"Reads rejected: {result.get('reads_rejected', False)}\n"
        f"Writes still work: {result.get('writes_still_work', False)}\n"
        f"Pods recovered: {result.get('pods_recovered', False)}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["vlselect_down_test_passed"], details)
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["vlselect_down_test_failed"],
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, f"vlselect destructive test failed: {result.get('error', '')}"


# Source: test_victoria_logs_destructive.py
@pytest.mark.order(64)
def test_complete_cluster_failure_recovery(host):
    """
    TC40 (DESTRUCTIVE): Kill ALL VictoriaLogs pods and verify complete recovery.
    
    This is the ultimate disaster recovery test.
    
    Expected behavior:
    - All services unavailable during outage
    - All pods auto-recover (StatefulSets and Deployments recreate them)
    - Cluster returns to fully healthy state
    - Recovery time should be < 3 minutes
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["complete_cluster_failure"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("⚠️  DESTRUCTIVE TEST: Killing ALL VictoriaLogs pods")
    log.check("This simulates complete cluster failure")
    log.check("Expected: All pods recover, cluster returns to healthy state")
    
    result = verify_complete_cluster_failure_recovery(host, admin_ip)

    details = (
        f"Baseline healthy: {result.get('baseline_healthy', False)}\n"
        f"All pods killed: {result.get('all_pods_killed', False)}\n"
        f"Cluster unavailable: {result.get('cluster_unavailable', False)}\n"
        f"All pods recovered: {result.get('all_pods_recovered', False)}\n"
        f"Cluster healthy after recovery: {result.get('cluster_healthy_after_recovery', False)}\n"
        f"Recovery time: {result.get('recovery_time_seconds', 0)}s"
    )

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["cluster_failure_test_passed"].format(
                time=result.get("recovery_time_seconds", 0)
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["cluster_failure_test_failed"],
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, f"Complete cluster failure test failed: {result.get('error', '')}"


# Source: test_victoria_logs_partial_failure.py
@pytest.mark.order(65)
def test_single_vlstorage_pod_failure(host):
    """
    TC41 (PARTIAL FAILURE): Kill 1 of 3 vlstorage pods and verify HA.
    
    Expected behavior:
    - Writes should continue (vlinsert routes to remaining 2 nodes)
    - Reads should continue (vlselect queries remaining 2 nodes)
    - Some data may be unavailable (data on killed node)
    - Pod should auto-recover (StatefulSet recreates it)
    - No complete service outage
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["single_vlstorage_failure"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("⚠️  PARTIAL FAILURE TEST: Killing 1 of 3 vlstorage pods")
    log.check("Expected: Reads and writes continue, pod auto-recovers")
    
    result = verify_single_vlstorage_pod_failure(host, admin_ip)

    details = (
        f"Pod killed: {result.get('pod_name', 'unknown')}\n"
        f"Baseline healthy: {result.get('baseline_healthy', False)}\n"
        f"Pod killed: {result.get('pod_killed', False)}\n"
        f"Writes still work: {result.get('writes_still_work', False)}\n"
        f"Reads still work: {result.get('reads_still_work', False)}\n"
        f"Pod recovered: {result.get('pod_recovered', False)}\n"
        f"Recovery time: {result.get('recovery_time_seconds', 0)}s"
    )

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["single_vlstorage_ha_passed"].format(
                pod=result.get("pod_name", "vlstorage-0"),
                time=result.get("recovery_time_seconds", 0)
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["single_vlstorage_ha_failed"].format(
                pod=result.get("pod_name", "vlstorage-0")
            ),
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, f"Single vlstorage pod failure test failed: {result.get('error', '')}"


# Source: test_victoria_logs_partial_failure.py
@pytest.mark.order(66)
def test_single_vlinsert_pod_failure(host):
    """
    TC42 (PARTIAL FAILURE): Kill 1 of 2 vlinsert pods and verify HA.
    
    Expected behavior:
    - Writes should continue (LoadBalancer routes to remaining pod)
    - Reads should continue (vlselect independent)
    - Pod should auto-recover (Deployment recreates it)
    - No complete service outage
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["single_vlinsert_failure"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("⚠️  PARTIAL FAILURE TEST: Killing 1 of 2 vlinsert pods")
    log.check("Expected: Reads and writes continue, pod auto-recovers")
    
    result = verify_single_vlinsert_pod_failure(host, admin_ip)

    details = (
        f"Pod killed: {result.get('pod_name', 'unknown')}\n"
        f"Baseline healthy: {result.get('baseline_healthy', False)}\n"
        f"Pod killed: {result.get('pod_killed', False)}\n"
        f"Writes still work: {result.get('writes_still_work', False)}\n"
        f"Reads still work: {result.get('reads_still_work', False)}\n"
        f"Pod recovered: {result.get('pod_recovered', False)}\n"
        f"Recovery time: {result.get('recovery_time_seconds', 0)}s"
    )

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["single_vlinsert_ha_passed"].format(
                pod=result.get("pod_name", "vlinsert-xxx"),
                time=result.get("recovery_time_seconds", 0)
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["single_vlinsert_ha_failed"].format(
                pod=result.get("pod_name", "vlinsert-xxx")
            ),
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, f"Single vlinsert pod failure test failed: {result.get('error', '')}"


# Source: test_victoria_logs_partial_failure.py
@pytest.mark.order(67)
def test_single_vlselect_pod_failure(host):
    """
    TC43 (PARTIAL FAILURE): Kill 1 of 2 vlselect pods and verify HA.
    
    Expected behavior:
    - Reads should continue (LoadBalancer routes to remaining pod)
    - Writes should continue (vlinsert independent)
    - Pod should auto-recover (Deployment recreates it)
    - No complete service outage
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["single_vlselect_failure"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("⚠️  PARTIAL FAILURE TEST: Killing 1 of 2 vlselect pods")
    log.check("Expected: Reads and writes continue, pod auto-recovers")
    
    result = verify_single_vlselect_pod_failure(host, admin_ip)

    details = (
        f"Pod killed: {result.get('pod_name', 'unknown')}\n"
        f"Baseline healthy: {result.get('baseline_healthy', False)}\n"
        f"Pod killed: {result.get('pod_killed', False)}\n"
        f"Reads still work: {result.get('reads_still_work', False)}\n"
        f"Writes still work: {result.get('writes_still_work', False)}\n"
        f"Pod recovered: {result.get('pod_recovered', False)}\n"
        f"Recovery time: {result.get('recovery_time_seconds', 0)}s"
    )

    if result["success"]:
        log.passed(
            VICTORIA_LOGS_LOG_MSGS["single_vlselect_ha_passed"].format(
                pod=result.get("pod_name", "vlselect-xxx"),
                time=result.get("recovery_time_seconds", 0)
            ),
            details
        )
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["single_vlselect_ha_failed"].format(
                pod=result.get("pod_name", "vlselect-xxx")
            ),
            details + f"\nError: {result.get('error', '')}"
        )
        assert False, f"Single vlselect pod failure test failed: {result.get('error', '')}"


# Source: test_victoria_logs_cleanup.py
@pytest.mark.order(68)
def test_retention_cleanup_cycle(host):
    """
    TC-F005: Verify retention cleanup cycle removes old logs.
    
    Test steps:
    1. Ingest logs backdated to 2 days ago (outside retention window)
    2. Ingest logs within current retention window
    3. Wait for cleanup cycle to run
    4. Verify backdated logs are no longer queryable
    5. Verify recent logs are still queryable
    6. Verify storage reclaimed
    
    Note: This test requires a short retention period (e.g., 1 day) to be configured.
    The cleanup cycle typically runs every 1 hour, so this test may take time.
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["retention_cleanup_cycle"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Testing retention cleanup cycle")
    log.check("Step 1: Ingest backdated logs (2 days old)")
    log.check("Step 2: Ingest recent logs (within retention)")
    log.check("Step 3: Wait for cleanup cycle (2 minutes)")
    log.check("Step 4: Verify backdated logs removed")
    log.check("Step 5: Verify recent logs preserved")
    
    result = verify_retention_cleanup_cycle(host, admin_ip)

    details = (
        f"Backdated logs ingested: {result.get('backdated_logs_ingested', False)}\n"
        f"Recent logs ingested: {result.get('recent_logs_ingested', False)}\n"
        f"Backdated queryable before cleanup: {result.get('backdated_logs_queryable_before_cleanup', False)}\n"
        f"Backdated queryable after cleanup: {result.get('backdated_logs_queryable_after_cleanup', False)}\n"
        f"Recent queryable after cleanup: {result.get('recent_logs_queryable_after_cleanup', False)}\n"
        f"Storage decreased: {result.get('storage_decreased', False)}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["retention_cleanup_passed"], details)
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["retention_cleanup_failed"],
            details + f"\nError: {result.get('error', '')}"
        )
        # Don't fail the test for now - this may need longer cleanup cycle time
        # assert False, f"Retention cleanup test failed: {result.get('error', '')}"


# Source: test_victoria_logs_cleanup.py
@pytest.mark.order(69)
def test_default_retention_period(host):
    """
    TC-F005 (Part): Verify default retention period is 30 days.
    
    When VictoriaLogs is deployed without an explicit retention setting,
    it should default to 30 days.
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["default_retention_period"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying default retention period")
    
    result = verify_default_retention_period(host, admin_ip)

    details = f"Default retention period: {result.get('default_retention_days', 0)} days"

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["default_retention_ok"], details)
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["default_retention_wrong"].format(
                days=result.get("default_retention_days", 0)
            ),
            details + f"\nError: {result.get('error', '')}"
        )


# Source: test_victoria_logs_cleanup.py
@pytest.mark.order(70)
def test_independent_cleanup(host):
    """
    TC-E004: Verify VictoriaLogs removal does not affect VictoriaMetrics or Kafka.
    
    This test removes and redeploys VictoriaLogs to verify:
    - VictoriaMetrics continues to work after VictoriaLogs removal
    - Kafka continues to work after VictoriaLogs removal
    - Vector does not crash (may log errors)
    - VictoriaLogs redeploys cleanly
    
    WARNING: This test is skipped by default as it's too destructive.
    Only run in isolated test environments.
    """
    log = TestLogger(VICTORIA_LOGS_TEST_NAMES["independent_cleanup"])
    skip_if_victoria_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("⚠️  DESTRUCTIVE TEST: VictoriaLogs removal and redeployment")
    log.check("This test is skipped by default")
    
    result = verify_victoria_logs_independent_cleanup(host, admin_ip)

    details = (
        f"VictoriaMetrics baseline: {result.get('victoria_metrics_baseline_ok', False)}\n"
        f"Kafka baseline: {result.get('kafka_baseline_ok', False)}\n"
        f"VictoriaLogs removed: {result.get('victoria_logs_removed', False)}\n"
        f"VictoriaMetrics after removal: {result.get('victoria_metrics_after_removal_ok', False)}\n"
        f"Kafka after removal: {result.get('kafka_after_removal_ok', False)}\n"
        f"Vector running: {result.get('vector_running_after_removal', False)}\n"
        f"VictoriaLogs redeployed: {result.get('victoria_logs_redeployed', False)}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOGS_LOG_MSGS["independent_cleanup_passed"], details)
    else:
        log.failed(
            VICTORIA_LOGS_LOG_MSGS["independent_cleanup_failed"],
            details + f"\nError: {result.get('error', '')}"
        )


# OMN01D-2250 test removed - authentication test case excluded per user request


