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
VictoriaLogs Automation - Messages.

This module contains all user-facing messages for VictoriaLogs tests.
"""

from typing import Dict


# =============================================================================
# VICTORIALOGS TEST NAMES
# =============================================================================

VICTORIA_LOGS_TEST_NAMES: Dict[str, str] = {
    "victoria_logs_enabled": "Check if VictoriaLogs is enabled",
    "victoria_logs_storage_size": "Verify VictoriaLogs vlstorage PVC size",
    "victoria_logs_cluster_pods": "Verify VictoriaLogs cluster pods running",
    "vlagent_pod_running": "Verify VLAgent pod running",
    "victoria_logs_services": "Verify VictoriaLogs services have external IPs",
    "victoria_logs_tls_secret": "Verify VictoriaLogs TLS secret",
    "victoria_logs_health": "Verify VictoriaLogs TLS connection and health",
    "victoria_logs_query": "Verify VictoriaLogs log query endpoint",
    "victoria_logs_configmap": "Verify VLAgent ConfigMap exists",
    "vlagent_pvc": "Verify VLAgent buffer PVC exists",
    "vlagent_syslog_service": "Verify VLAgent syslog service ports",
    "vlagent_syslog_injection": (
        "Verify VLAgent syslog ingestion (synthetic log injection)"
    ),
    # Functional
    "vlagent_configmap_content": "Verify VLAgent ConfigMap has syslog receiver and remoteWrite",
    "syslog_stream_labels": "Verify syslog stream labels in VictoriaLogs",
    "logsql_field_filter": "Verify LogsQL field-filter query",
    "vlinsert_direct_write": "Verify vlinsert direct HTTP POST write",
    "retention_period_applied": "Verify retention period applied to vlstorage",
    # Negative
    "invalid_logsql_rejected": "Verify invalid LogsQL query returns HTTP 4xx",
    "nonexistent_stream_empty": "Verify non-existent stream query returns empty result",
    "plain_http_rejected": "Verify plain HTTP access is rejected (TLS required)",
    "wrong_ca_rejected": "Verify wrong CA certificate is rejected",
    # Idempotency
    "pod_restart_preserves_data": "Verify VLAgent pod restart preserves ingested data",
    "multi_message_ingestion": "Verify multiple messages ingested without deduplication",
    # Performance
    "query_response_time": "Verify vlselect query response time within threshold",
    "bulk_ingestion": "Verify bulk syslog ingestion (50 messages)",
    # Security
    "tls_cert_validity": "Verify TLS certificate is valid and not near expiry",
    "vlagent_pvc_mounted": "Verify VLAgent buffer PVC is mounted in pod",
    "rbac_restrictions": "Verify RBAC: default SA cannot read TLS secret",
    "pod_security_context": "Verify VictoriaLogs pods have no privileged containers",
    # TC-F006 / TC-E001
    "ha_under_vlstorage_failure": "Verify HA and buffering under vlstorage failure (TC-F006/TC-E001)",
    # Edge Cases & Security
    "resource_limits_enforced": "Verify CPU and memory limits are enforced for all pods",
    "resource_requests_set": "Verify CPU and memory requests are configured for all pods",
    "large_log_message_handling": "Verify handling of extremely large log messages (1MB)",
    "malformed_json_rejected": "Verify malformed JSON is rejected by vlinsert",
    "sql_injection_protection": "Verify LogsQL is protected against SQL injection",
    "namespace_isolation": "Verify VictoriaLogs resources are isolated to telemetry namespace",
    # Destructive Tests - All Pods Down
    "all_vlstorage_down": "Verify behavior when all vlstorage pods are down",
    "all_vlinsert_down": "Verify behavior when all vlinsert pods are down",
    "all_vlselect_down": "Verify behavior when all vlselect pods are down",
    "complete_cluster_failure": "Verify complete cluster failure and recovery",
    # Partial Failure Tests - Single Pod Down
    "single_vlstorage_failure": "Verify HA when 1 of 3 vlstorage pods fails",
    "single_vlinsert_failure": "Verify HA when 1 of 2 vlinsert pods fails",
    "single_vlselect_failure": "Verify HA when 1 of 2 vlselect pods fails",
    # Cleanup Tests
    "retention_cleanup_cycle": "Verify retention cleanup cycle removes old logs",
    "default_retention_period": "Verify default retention period is 30 days",
    "independent_cleanup": "Verify VictoriaLogs removal does not affect VictoriaMetrics or Kafka",
}


# =============================================================================
# VICTORIALOGS LOG MESSAGES
# =============================================================================

VICTORIA_LOGS_LOG_MSGS: Dict[str, str] = {
    # Enable check
    "victoria_logs_enabled": (
        "VictoriaLogs is enabled (co-deployed with VictoriaMetrics)"
    ),
    "victoria_logs_not_enabled": "VictoriaLogs is not enabled - skipping tests",

    # Storage size
    "storage_size_match": "vlstorage PVC size matches config: {size}",
    "storage_size_mismatch": "vlstorage PVC size mismatch",

    # Pods
    "pod_running": "Pod '{pod}' is running",
    "pod_not_running": "Pod '{pod}' is not running (status: {status})",
    "all_pods_running": "All {component} pods are running ({count} pods)",
    "pods_not_running": "Some {component} pods are not running",

    # Services
    "service_has_external_ip": "Service '{service}' has external IP: {ip}",
    "service_no_external_ip": "Service '{service}' has no external IP",
    "all_services_ready": "All VictoriaLogs services have external IPs",

    # TLS
    "tls_secret_exists": "TLS secret '{secret}' exists with all required keys",
    "tls_secret_missing": "TLS secret '{secret}' not found",
    "tls_secret_missing_keys": "TLS secret missing keys: {keys}",
    "tls_connection_success": "TLS connection to VictoriaLogs vlselect successful",
    "tls_connection_failed": "TLS connection to VictoriaLogs failed",

    # Health
    "health_endpoint_success": "Health endpoint returned: {response}",
    "health_endpoint_failed": "Health endpoint check failed",

    # Log query
    "query_streams_found": (
        "VictoriaLogs stream query returned {count} stream(s)"
    ),
    "query_streams_empty": (
        "VictoriaLogs stream query returned no results (no logs ingested yet — "
        "no syslog data sources configured)"
    ),
    "query_endpoint_ok": "VictoriaLogs log query endpoint is accessible",
    "query_endpoint_failed": "VictoriaLogs log query endpoint is not accessible",

    # ConfigMap
    "configmap_exists": "VLAgent ConfigMap '{configmap}' exists",
    "configmap_missing": "VLAgent ConfigMap '{configmap}' not found",

    # VLAgent buffer PVC
    "vlagent_pvc_exists": "VLAgent buffer PVC exists (size: {size})",
    "vlagent_pvc_missing": "VLAgent buffer PVC not found in telemetry namespace",

    # VLAgent syslog service ports
    "vlagent_service_ports_ok": (
        "VLAgent syslog service '{service}' has expected ports: {ports}"
    ),
    "vlagent_service_missing": "VLAgent service '{service}' not found",
    "vlagent_service_ports_missing": (
        "VLAgent syslog service missing expected ports: {ports}"
    ),

    # Syslog injection
    "syslog_injecting": (
        "Injecting synthetic syslog to VLAgent {ip}:514 (message ID: {msg_id})"
    ),
    "syslog_waiting": (
        "Waiting {secs}s for VLAgent to batch and forward to vlinsert..."
    ),
    "syslog_received": (
        "Synthetic syslog received in VictoriaLogs (message ID: {msg_id})"
    ),
    "syslog_not_received": (
        "Synthetic syslog NOT found in VictoriaLogs after {secs}s wait"
    ),
    "syslog_inject_failed": (
        "Failed to inject syslog to VLAgent service"
    ),
    "syslog_no_vlagent_ip": (
        "VLAgent service has no external IP — cannot inject syslog "
        "(MetalLB/LoadBalancer required)"
    ),
    # TC13
    "configmap_content_ok": "VLAgent ConfigMap has syslog receiver and remoteWrite config",
    "configmap_content_missing": "VLAgent ConfigMap missing required syslog/remoteWrite config",
    # TC14/TC15
    "stream_label_found": "Syslog stream label '{field}={value}' found in VictoriaLogs",
    "stream_label_missing": "Syslog stream label not found in VictoriaLogs",
    "field_filter_found": "LogsQL field-filter query returned matching log entry",
    "field_filter_missing": "LogsQL field-filter query returned no results",
    # TC16
    "vlinsert_direct_ok": "vlinsert direct POST accepted (HTTP {code})",
    "vlinsert_direct_failed": "vlinsert direct POST failed (HTTP {code})",
    # TC17
    "retention_period_ok": "vlstorage retention period matches config: {period}",
    "retention_period_missing": "vlstorage retention period not found in pod args",
    # TC18
    "invalid_query_rejected": "Invalid LogsQL query correctly rejected (HTTP {code})",
    "invalid_query_accepted": "Invalid LogsQL query was NOT rejected (HTTP {code})",
    # TC19
    "nonexistent_stream_empty": "Non-existent stream query returned empty result (correct)",
    "nonexistent_stream_error": "Non-existent stream query returned error (should be empty)",
    # TC20
    "plain_http_rejected": "Plain HTTP access correctly rejected (TLS required)",
    "plain_http_accepted": "Plain HTTP access was NOT rejected",
    # TC21
    "wrong_ca_rejected": "Wrong CA certificate correctly rejected by vlselect",
    "wrong_ca_accepted": "Wrong CA certificate was NOT rejected (TLS misconfigured)",
    # TC22
    "pod_restart_ok": "VLAgent pod restarted and data preserved in VictoriaLogs",
    "pod_restart_data_lost": "Data not found after VLAgent pod restart",
    # TC23
    "multi_msg_ok": "All {count} messages ingested without deduplication",
    "multi_msg_failed": "Not all messages found — expected {expected}, found {found}",
    # TC24
    "response_time_ok": "vlselect query responded in {time:.3f}s (threshold: {max}s)",
    "response_time_slow": "vlselect query too slow: {time:.3f}s (threshold: {max}s)",
    # TC25
    "bulk_ok": "Bulk ingestion complete — {found}/{count} messages verified",
    "bulk_failed": "Bulk ingestion incomplete — {found}/{count} messages found",
    # TC26
    "tls_cert_valid": "TLS certificate is valid (not expiring within {days} days)",
    "tls_cert_expiring": "TLS certificate expires within {days} days — renewal needed",
    # TC27
    "pvc_mounted_ok": "VLAgent PVC buffer volume is mounted in pod",
    "pvc_mounted_missing": "VLAgent PVC buffer volume not found in pod spec",
    # TC28
    "rbac_denied": "RBAC: default SA correctly denied access to TLS secret",
    "rbac_allowed": "RBAC: default SA has unexpected access to TLS secret",
    # TC29
    "pod_security_ok": "All VictoriaLogs pods have non-privileged security context",
    "pod_security_privileged": "Pod '{pod}' has privileged container — security risk",
    # TC-F006 / TC-E001
    "ha_test_baseline_ok": "HA test baseline: syslog ingested and queryable",
    "ha_test_pod_killed": "vlstorage-0 pod killed successfully",
    "ha_test_outage_sent": "Syslog sent during vlstorage outage",
    "ha_test_vlinsert_ok": "vlinsert accepted writes during outage (HTTP 2xx)",
    "ha_test_pod_recovered": "vlstorage-0 pod recovered and running",
    "ha_test_data_recovered": "All outage events queryable post-recovery",
    "ha_test_passed": "HA test passed: ingestion continued, data preserved",
    "ha_test_failed": "HA test failed — check individual step results",
    # Edge Cases & Security
    "resource_limits_ok": "All VictoriaLogs pods have CPU and memory limits configured",
    "resource_limits_missing": "Some pods missing resource limits",
    "resource_requests_ok": "All VictoriaLogs pods have CPU and memory requests configured",
    "resource_requests_missing": "Some pods missing resource requests",
    "large_message_handled": "Large log message (1MB) handled correctly (HTTP {code})",
    "large_message_failed": "Large log message handling failed (HTTP {code})",
    "malformed_json_rejected_ok": "Malformed JSON correctly rejected (HTTP {code})",
    "malformed_json_accepted": "Malformed JSON was NOT rejected (HTTP {code})",
    "sql_injection_safe": "LogsQL protected against SQL injection attempts",
    "sql_injection_vulnerable": "SQL injection vulnerability detected",
    "namespace_isolation_ok": "VictoriaLogs resources isolated to telemetry namespace",
    "namespace_isolation_failed": "VictoriaLogs resources found in other namespaces",
    # Destructive Tests - All Pods Down
    "vlstorage_down_test_passed": "All vlstorage pods down test passed: cluster recovered successfully",
    "vlstorage_down_test_failed": "All vlstorage pods down test failed",
    "vlinsert_down_test_passed": "All vlinsert pods down test passed: reads work, writes rejected, recovery successful",
    "vlinsert_down_test_failed": "All vlinsert pods down test failed",
    "vlselect_down_test_passed": "All vlselect pods down test passed: writes work, reads rejected, recovery successful",
    "vlselect_down_test_failed": "All vlselect pods down test failed",
    "cluster_failure_test_passed": "Complete cluster failure test passed: all pods recovered in {time}s",
    "cluster_failure_test_failed": "Complete cluster failure test failed",
    # Partial Failure Tests - Single Pod Down
    "single_vlstorage_ha_passed": "HA test passed: {pod} killed, reads/writes continued, recovered in {time}s",
    "single_vlstorage_ha_failed": "HA test failed: {pod} killed but service degraded",
    "single_vlinsert_ha_passed": "HA test passed: {pod} killed, reads/writes continued, recovered in {time}s",
    "single_vlinsert_ha_failed": "HA test failed: {pod} killed but service degraded",
    "single_vlselect_ha_passed": "HA test passed: {pod} killed, reads/writes continued, recovered in {time}s",
    "single_vlselect_ha_failed": "HA test failed: {pod} killed but service degraded",
    # Cleanup Tests
    "retention_cleanup_passed": "Retention cleanup cycle works: old logs removed, recent logs preserved",
    "retention_cleanup_failed": "Retention cleanup cycle failed",
    "default_retention_ok": "Default retention period is 30 days",
    "default_retention_wrong": "Default retention period is {days} days, expected 30 days",
    "independent_cleanup_passed": "Independent cleanup passed: VictoriaLogs removal does not affect other components",
    "independent_cleanup_failed": "Independent cleanup failed",
}


# =============================================================================
# VICTORIALOGS ASSERTION MESSAGES
# =============================================================================

VICTORIA_LOGS_ASSERT_MSGS: Dict[str, str] = {
    "victoria_logs_not_enabled": (
        "VictoriaLogs is not enabled in telemetry_config.yml.\n"
        "'victoria' is not in idrac_telemetry_collection_type.\n"
        "Skipping all VictoriaLogs tests."
    ),
    "idrac_telemetry_not_enabled": (
        "iDRAC telemetry is not enabled in telemetry_config.yml.\n"
        "idrac_telemetry_support is set to false.\n"
        "Skipping all VictoriaLogs tests."
    ),
    "storage_size_mismatch": (
        "VictoriaLogs vlstorage PVC size mismatch.\n"
        "Expected: {expected}\n"
        "Actual: {actual}\n"
        "Please check victoria_logs_configurations.storage_size "
        "in telemetry_config.yml"
    ),
    "pods_not_running": (
        "VictoriaLogs {component} pods are not running.\n"
        "Expected: {expected} pods\n"
        "Running: {running} pods\n"
        "Not running: {not_running}\n"
        "Please check: kubectl get pods -n telemetry -l app={app_label}"
    ),
    "vlagent_not_running": (
        "VLAgent pod is not running.\n"
        "vlagent is required for syslog reception and log forwarding "
        "to VictoriaLogs.\n"
        "Please check: kubectl get pods -n telemetry -l app=vlagent"
    ),
    "service_no_external_ip": (
        "VictoriaLogs service has no external IP.\n"
        "Service: {service}\n"
        "Expected: LoadBalancer with external IP\n"
        "Please check: kubectl get svc {service} -n telemetry"
    ),
    "tls_secret_missing": (
        "VictoriaLogs TLS secret not found.\n"
        "Secret: {secret}\n"
        "TLS is required for VictoriaLogs cluster inter-component communication.\n"
        "Please check: kubectl get secret {secret} -n telemetry"
    ),
    "tls_secret_missing_keys": (
        "VictoriaLogs TLS secret is missing required keys.\n"
        "Secret: {secret}\n"
        "Missing keys: {missing_keys}\n"
        "Required keys: tls.crt, tls.key, ca.crt"
    ),
    "tls_connection_failed": (
        "VictoriaLogs TLS connection failed.\n"
        "URL: https://{host}:{port}/health\n"
        "Error: {error}\n"
        "Please verify:\n"
        "  1) VictoriaLogs pods are running\n"
        "  2) TLS certificates are valid\n"
        "  3) vlselect service has external IP"
    ),
    "health_check_failed": (
        "VictoriaLogs health check failed.\n"
        "URL: https://{host}:{port}/health\n"
        "Response: {response}\n"
        "Expected: 'OK' or valid health response"
    ),
    "query_endpoint_failed": (
        "VictoriaLogs log query endpoint is not accessible.\n"
        "URL: https://{host}:{port}/select/logsql/stats/streams\n"
        "Error: {error}\n"
        "Please verify vlselect pods are running and TLS is configured correctly."
    ),
    "configmap_missing": (
        "VLAgent ConfigMap not found.\n"
        "ConfigMap: {configmap}\n"
        "This ConfigMap contains the syslog receiver and remoteWrite pipeline config.\n"
        "Please check: kubectl get configmap {configmap} -n telemetry"
    ),
    "vlagent_pvc_missing": (
        "VLAgent buffer PVC not found.\n"
        "Expected a PVC labelled app=vlagent in the telemetry namespace.\n"
        "Please check: kubectl get pvc -n telemetry -l app=vlagent"
    ),
    "vlagent_service_missing": (
        "VLAgent service not found.\n"
        "Service: {service}\n"
        "Please check: kubectl get svc {service} -n telemetry"
    ),
    "vlagent_service_ports_missing": (
        "VLAgent syslog service is missing expected ports.\n"
        "Service: {service}\n"
        "Missing ports: {missing_ports}\n"
        "Expected syslog ports: 514 (TCP/UDP plaintext), 6514 (TCP TLS)\n"
        "Please check: kubectl get svc {service} -n telemetry -o json"
    ),
    "syslog_no_vlagent_ip": (
        "VLAgent service has no external IP.\n"
        "Syslog injection requires a LoadBalancer (MetalLB) external IP on port 514.\n"
        "Please check: kubectl get svc vlagent -n telemetry"
    ),
    "syslog_inject_failed": (
        "Failed to inject synthetic syslog to VLAgent.\n"
        "VLAgent IP: {vlagent_ip}\n"
        "Error: {error}\n"
        "Please verify logger is installed: which logger"
    ),
    "syslog_not_received": (
        "Synthetic syslog was not found in VictoriaLogs after {secs}s.\n"
        "Message ID: {msg_id}\n"
        "Possible causes:\n"
        "  1) VLAgent not forwarding to vlinsert (check vlagent pod logs)\n"
        "  2) vlinsert not accepting writes\n"
        "  3) Ingestion delay > {secs}s (increase VLAGENT_SYSLOG_INGESTION_WAIT_SECS)\n"
        "Diagnose: kubectl logs -n telemetry -l app=vlagent --tail=50"
    ),
    "configmap_content_missing": (
        "VLAgent ConfigMap 'vlagent-config' is missing required configuration.\n"
        "Expected: syslog receiver block AND remoteWrite URL pointing to vlinsert.\n"
        "Check: kubectl get configmap vlagent-config -n telemetry -o yaml"
    ),
    "stream_label_missing": (
        "Syslog stream label not found in VictoriaLogs.\n"
        "Field: {field}, Value: {value}\n"
        "Ensure VLAgent syslog parser preserves the syslog program/tag field."
    ),
    "field_filter_missing": (
        "LogsQL field-filter query '{query}' returned no results.\n"
        "Ensure syslog messages are being stored with the expected stream labels."
    ),
    "vlinsert_direct_failed": (
        "vlinsert direct HTTP POST failed.\n"
        "Service: {service}, HTTP code: {code}\n"
        "Expected HTTP 200. Check vlinsert logs: kubectl logs -n telemetry -l app.kubernetes.io/name=vlinsert"
    ),
    "retention_period_missing": (
        "vlstorage retention period not found in pod args.\n"
        "Expected to find '--retentionPeriod' in container args.\n"
        "Check vlstorage CR or VLCluster spec."
    ),
    "invalid_query_accepted": (
        "Invalid LogsQL query '{query}' was NOT rejected.\n"
        "Expected HTTP 4xx, got HTTP {code}.\n"
        "vlselect should reject malformed queries."
    ),
    "plain_http_accepted": (
        "Plain HTTP request to vlselect was not rejected.\n"
        "vlselect should only accept HTTPS (TLS) connections.\n"
        "HTTP code: {code}"
    ),
    "wrong_ca_accepted": (
        "vlselect accepted connection with an invalid CA certificate.\n"
        "TLS verification is not enforced — security risk."
    ),
    "pod_restart_data_lost": (
        "Data not found in VictoriaLogs after VLAgent pod restart.\n"
        "Message ID: {msg_id}\n"
        "VLAgent data is stored in vlstorage (StatefulSet PVC) — should persist across VLAgent restarts."
    ),
    "multi_msg_failed": (
        "Not all messages found in VictoriaLogs.\n"
        "Expected: {expected} messages, Found: {found}\n"
        "VictoriaLogs should not deduplicate distinct messages."
    ),
    "response_time_slow": (
        "vlselect query response time {time:.3f}s exceeds threshold {max}s.\n"
        "Check vlselect resources and vlstorage health."
    ),
    "bulk_failed": (
        "Bulk ingestion incomplete.\n"
        "Expected: {count} messages, Found: {found}\n"
        "Check VLAgent and vlinsert logs for dropped messages."
    ),
    "tls_cert_expiring": (
        "TLS certificate expires within {days} days.\n"
        "Secret: victoria-tls-certs\n"
        "Renew the certificate before it expires to avoid service interruption."
    ),
    "pvc_mounted_missing": (
        "VLAgent PVC buffer volume not found in pod spec.\n"
        "VLAgent requires a PVC mount for WAL buffering.\n"
        "Check pod spec: kubectl get pod vlagent-vlagent-0 -n telemetry -o yaml"
    ),
    "rbac_allowed": (
        "RBAC misconfiguration: default service account can read TLS secret.\n"
        "The 'victoria-tls-certs' secret should not be readable by default SA.\n"
        "Review RBAC roles in the telemetry namespace."
    ),
    "pod_security_privileged": (
        "Security risk: privileged container detected.\n"
        "Pod: {pod}\n"
        "VictoriaLogs pods should run as non-privileged, non-root containers."
    ),
    "ha_test_failed": (
        "HA test failed.\n"
        "Baseline found: {baseline_found}\n"
        "Pod killed: {pod_killed}\n"
        "Outage sent: {outage_sent}\n"
        "vlinsert accepted: {vlinsert_accepted}\n"
        "Pod recovered: {pod_recovered}\n"
        "Outage events found: {outage_events_found}\n"
        "Error: {error}"
    ),
}
