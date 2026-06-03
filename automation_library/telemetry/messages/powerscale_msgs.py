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
PowerScale Telemetry Automation - Messages.

This module contains all user-facing messages for PowerScale telemetry tests.
Covers 26 test cases: Functional (12), Negative/Error (8), Idempotency (1),
Performance (3), Security (2).
"""

from typing import Dict


# =============================================================================
# POWERSCALE TEST NAMES
# =============================================================================

POWERSCALE_TEST_NAMES: Dict[str, str] = {
    # Functional
    "tc_f001_deployment": "TC-F001: Omnia-Orchestrated Mode Deployment Verification",
    "tc_f002_metric_collection": "TC-F002: PowerScale Metric Collection and Label Verification",
    "tc_f003_syslog_ingestion": "TC-F003: PowerScale Syslog Ingestion and Log Verification",
    "tc_f004_feature_flags": "TC-F004: Independent Feature Flag Operation",
    "tc_f005_deployment_mode": "TC-F005: Deployment Mode - Full Pipeline Verification",
    "tc_f006_dual_destination": "TC-F006: Dual-Destination Delivery",
    "tc_f007_health_metrics": "TC-F007: Operational Health Metrics",
    "tc_f008_tls_enforcement": "TC-F008: TLS Enforcement on Metric Scraping Path",
    "tc_f009_k8s_auth": "TC-F009: Kubernetes Service-Account Authentication",
    "tc_f010_label_compliance": "TC-F010: Label Convention Compliance",
    "tc_f011_scrape_interval": "TC-F011: Scrape Interval Configurability",
    "tc_f012_csi_auth_mode": "TC-F012: CSI Driver Authorization Enabled Mode",

    # Negative / Error
    "tc_e001_csm_pod_recovery": "TC-E001: CSM Metrics Pod Failure Recovery",
    "tc_e002_otel_pod_recovery": "TC-E002: OTel Collector Pod Failure Recovery",
    "tc_e003_vmagent_scrape_retry": "TC-E003: vmagent Scrape Failure and Retry",
    "tc_e004_tls_misconfig": "TC-E004: TLS / Certificate Misconfiguration Handling",
    "tc_e005_external_failure": "TC-E005: External Endpoint Failure Isolation",
    "tc_e006_vlagent_failure": "TC-E006: VLAgent Failure Isolation",
    "tc_e007_powerscale_unreachable": "TC-E007: PowerScale Unreachable Handling",
    "tc_e008_worker_node_failure": "TC-E008: Worker Node Failure - Pod Rescheduling",
    "tc_e009_kafka_outage": "TC-E009: Kafka Broker Outage Resilience",
    "tc_e010_vminsert_outage": "TC-E010: vminsert Outage Resilience",
    "tc_e011_vlinsert_outage": "TC-E011: vlinsert Outage Resilience",

    # Idempotency
    "tc_i001_redeployment": "TC-I001: PowerScale Telemetry Redeployment Idempotency",

    # Performance
    "tc_p001_metric_latency": "TC-P001: Metric Ingestion Latency Within One Scrape Interval",
    "tc_p002_syslog_latency": "TC-P002: Syslog Event Ingestion Latency < 1 Minute",
    "tc_p003_endpoint_availability": "TC-P003: OTel Collector Endpoint Availability >= 98%",

    # Security
    "tc_s001_tls_all_comms": "TC-S001: TLS Enforcement for All Off-Cluster Communications",
    "tc_s002_no_plaintext_creds": "TC-S002: No Plaintext Credentials in Deployed Artifacts",
}


# =============================================================================
# POWERSCALE LOG MESSAGES
# =============================================================================

POWERSCALE_LOG_MSGS: Dict[str, str] = {
    # Enable checks
    "powerscale_enabled": "PowerScale telemetry is enabled",
    "powerscale_not_enabled": "PowerScale telemetry is not enabled - skipping tests",
    "metrics_enabled": "PowerScale metrics collection is enabled",
    "metrics_not_enabled": "PowerScale metrics collection is not enabled",
    "logs_enabled": "PowerScale logs collection is enabled",
    "logs_not_enabled": "PowerScale logs collection is not enabled",

    # Deployment mode
    "mode_omnia": "Deployment mode: omnia-orchestrated",
    "mode_operator": "Deployment mode: operator-provided",

    # Pod status
    "pod_running": "Pod '{pod}' is Running",
    "pod_not_running": "Pod '{pod}' is not Running (status: {status})",
    "all_pods_running": "All {component} pods are Running ({count} pods, 0 restarts)",
    "pods_not_running": "Some {component} pods are not Running",
    "pod_restart_detected": "Pod '{pod}' has {restarts} restart(s)",
    "no_restarts": "All PowerScale telemetry pods have 0 restarts",

    # CSI Driver
    "csi_driver_found": "CSI Driver '{driver}' is installed",
    "csi_driver_not_found": "CSI Driver '{driver}' not found",

    # cert-manager
    "cert_manager_running": "cert-manager pods are Running",
    "cert_manager_not_running": "cert-manager pods are not Running",
    "certificates_ready": "All certificates in telemetry namespace are Ready",
    "certificates_not_ready": "Some certificates are not Ready",

    # OTel Collector
    "otel_endpoint_ok": "OTel Collector Prometheus endpoint responding (HTTP 200)",
    "otel_endpoint_failed": "OTel Collector Prometheus endpoint not responding",

    # Metrics
    "metric_category_found": "Metric category '{category}' found ({count} series)",
    "metric_category_missing": "Metric category '{category}' not found",
    "all_categories_found": "All {count} metric categories present",
    "label_present": "Label '{label}' present on all metrics",
    "label_missing": "Label '{label}' missing on some metrics",
    "labels_compliant": "All labels follow Omnia naming conventions",

    # Syslog
    "syslog_events_found": "PowerScale syslog events found in VictoriaLogs ({count} events)",
    "syslog_events_missing": "No PowerScale syslog events found in VictoriaLogs",
    "syslog_labels_correct": "Syslog events have correct host/cluster, severity, facility labels",
    "syslog_latency_ok": "Syslog end-to-end latency < 60 seconds",

    # Feature flags
    "flag_toggle_success": "Feature flag toggle successful: metrics={metrics}, logs={logs}",
    "flag_toggle_failed": "Feature flag toggle failed",

    # TLS
    "tls_configured": "TLS is configured for metric scraping path",
    "tls_not_configured": "TLS is not configured for metric scraping path",
    "tls_traffic_encrypted": "All metric traffic is TLS-encrypted",
    "tls_plaintext_rejected": "Plaintext HTTP connection rejected",
    "tls_error_detected": "TLS error detected in scrape: {error}",
    "tls_scrape_recovered": "TLS scrape recovered after restoring valid certificates",

    # Authentication
    "sa_auth_configured": "K8s service-account authentication configured",
    "sa_auth_not_configured": "K8s service-account authentication not configured",
    "sa_auth_success": "Scrape succeeds with valid service account",
    "sa_auth_failure": "Scrape fails with invalid service account (auth error)",

    # Scrape interval
    "scrape_interval_applied": "Scrape interval {interval} correctly applied",
    "scrape_interval_mismatch": "Scrape interval mismatch: expected {expected}, actual {actual}",
    "scrape_interval_clamped": "Below/above-range scrape interval correctly clamped",

    # Deployment mode
    "deployment_pipeline_verified": "Full metrics pipeline verified: CSM + OTel + vmagent + VictoriaMetrics",
    "deployment_scrape_active": "vmagent scraping PowerScale endpoint over TLS",

    # Dual destination
    "dual_dest_both_receiving": "Both internal and external destinations receiving metrics",
    "dual_dest_internal_unaffected": "Internal VictoriaMetrics unaffected during external outage",
    "dual_dest_buffer_delivered": "Buffered metrics delivered to external endpoint on recovery",

    # Health metrics
    "health_metrics_exposed": "All operational health metrics exposed and queryable",
    "health_metric_missing": "Health metric '{metric}' not exposed",

    # Recovery
    "pod_auto_restarted": "K8s auto-restarted {component} pod",
    "pod_not_restarted": "{component} pod was not restarted by K8s",
    "metrics_resumed": "Metrics resumed in VictoriaMetrics after recovery",
    "metrics_not_resumed": "Metrics did not resume after recovery",
    "reconnection_success": "CSM Metrics reconnected to OneFS API",
    "reconnection_failed": "CSM Metrics failed to reconnect to OneFS API",

    # Idempotency
    "redeployment_success": "Redeployment completed - all pods Running, no duplicates",
    "redeployment_failed": "Redeployment failed",
    "no_duplicate_metrics": "No duplicate metrics detected after redeployment",
    "pre_restart_data_preserved": "Pre-restart data preserved in VictoriaMetrics",

    # Performance
    "latency_within_interval": "Metric latency within one scrape interval ({latency}s <= {interval}s)",
    "latency_exceeded": "Metric latency exceeded scrape interval ({latency}s > {interval}s)",
    "syslog_latency_within_limit": "Syslog latency within 1 minute ({latency}s < 60s)",
    "availability_met": "OTel Collector availability >= 98% ({availability}%)",
    "availability_not_met": "OTel Collector availability < 98% ({availability}%)",

    # Security
    "no_creds_in_logs": "No credential patterns found in pod logs",
    "creds_found_in_logs": "Credential patterns found in {component} logs",
    "no_creds_in_manifests": "No plaintext credentials in manifests or ConfigMaps",
    "creds_in_k8s_secrets": "PowerScale API credentials stored in K8s Secrets",
    "tls_keys_in_secrets": "TLS private keys stored in K8s Secrets only",

    # Other telemetry isolation
    "other_sources_unaffected": "Other telemetry sources (iDRAC, LDMS) completely unaffected",
    "other_sources_affected": "Other telemetry sources affected by PowerScale issue",

    # VLAgent isolation
    "metrics_unaffected_by_vlagent": "Metrics collection unaffected by VLAgent failure",
    "syslog_resumed_after_vlagent": "Syslog ingestion resumed after VLAgent restart",

    # Kafka / vminsert / vlinsert resilience
    "kafka_outage_metrics_unaffected": "PowerScale metrics path completely unaffected by Kafka broker outage",
    "kafka_broker_recovered": "Kafka broker recovered after outage",
    "vminsert_outage_vmagent_healthy": "vmagent continued scraping during vminsert outage",
    "vminsert_recovered_metrics_resumed": "vminsert recovered and metrics resumed",
    "vlinsert_outage_metrics_unaffected": "Metrics path completely isolated from vlinsert outage",
    "vlinsert_recovered_logs_resumed": "vlinsert recovered and syslog ingestion resumed",
}


# =============================================================================
# POWERSCALE ASSERTION MESSAGES
# =============================================================================

POWERSCALE_ASSERT_MSGS: Dict[str, str] = {
    # Enable checks
    "powerscale_not_enabled": (
        "PowerScale telemetry is not enabled in telemetry_config.yml.\n"
        "Set powerscale_telemetry_support: true to enable.\n"
        "Skipping all PowerScale telemetry tests."
    ),

    # Deployment
    "deployment_failed": (
        "PowerScale telemetry deployment verification failed.\n"
        "Missing components: {missing}\n"
        "Please verify:\n"
        "  1) telemetry_config.yml has powerscale_telemetry_support: true\n"
        "  2) Omnia telemetry playbook completed without errors\n"
        "  3) PowerScale cluster accessible with OneFS API credentials"
    ),
    "csm_metrics_not_running": (
        "CSM Metrics for PowerScale pod is not Running.\n"
        "Status: {status}\n"
        "Please check: kubectl get pods -n telemetry -l app=csm-metrics-powerscale"
    ),
    "otel_collector_not_running": (
        "OTel Collector pod is not Running.\n"
        "Status: {status}\n"
        "Please check: kubectl get pods -n telemetry -l app=otel-collector"
    ),
    "csi_driver_missing": (
        "CSI Driver for Dell PowerScale not found.\n"
        "Expected: csi-isilon.dellemc.com\n"
        "Please verify CSI Driver installation."
    ),
    "cert_manager_not_running": (
        "cert-manager pods are not Running.\n"
        "Please check: kubectl get pods -n cert-manager"
    ),
    "pod_restarts_detected": (
        "Pod restart loops detected for PowerScale telemetry pods.\n"
        "Pods with restarts: {pods}\n"
        "Please check pod logs for crash reasons."
    ),

    # Metrics
    "metric_categories_missing": (
        "PowerScale metric categories missing from VictoriaMetrics.\n"
        "Missing: {missing}\n"
        "Found: {found}\n"
        "Please verify CSM Metrics is collecting from PowerScale OneFS API."
    ),
    "labels_missing": (
        "Required labels missing on PowerScale metrics.\n"
        "Missing labels: {missing}\n"
        "All metrics must carry cluster name, node name, and protocol labels."
    ),
    "labels_non_compliant": (
        "PowerScale labels do not follow Omnia naming conventions.\n"
        "Non-compliant labels: {labels}\n"
        "Compare with other Omnia telemetry sources."
    ),

    # Syslog
    "syslog_not_ingested": (
        "PowerScale syslog events not found in VictoriaLogs.\n"
        "Please verify:\n"
        "  1) powerscale_logs_enabled: true in telemetry_config.yml\n"
        "  2) VLAgent pod is Running\n"
        "  3) PowerScale syslog forwarding is configured (RFC 5424)"
    ),
    "syslog_labels_incorrect": (
        "Syslog events have incorrect labels.\n"
        "Missing/incorrect: {labels}\n"
        "Expected: host/cluster, severity, facility labels."
    ),

    # Feature flags
    "flag_toggle_failed": (
        "Feature flag toggle failed.\n"
        "Expected: metrics={expected_metrics}, logs={expected_logs}\n"
        "Actual: metrics={actual_metrics}, logs={actual_logs}\n"
        "Disabling one flag must not affect the other."
    ),

    # TLS
    "tls_not_configured": (
        "TLS not configured for PowerScale metric scraping path.\n"
        "vmagent must use scheme: https with tls_config.\n"
        "Please check vmagent-config ConfigMap."
    ),
    "plaintext_not_rejected": (
        "Plaintext HTTP connection to OTel Collector was NOT rejected.\n"
        "All metric traffic must be TLS-encrypted.\n"
        "OTel Collector must reject plaintext connections."
    ),
    "tls_error_not_detected": (
        "TLS misconfiguration did not produce expected scrape failure.\n"
        "Certificate: {cert_issue}\n"
        "Scrape should fail with TLS error."
    ),

    # Auth
    "sa_auth_not_configured": (
        "K8s service-account authentication not configured for vmagent.\n"
        "vmagent must use service-account token for scraping."
    ),
    "unauthorized_scrape_succeeded": (
        "Scrape succeeded without valid service-account token.\n"
        "Scrape must fail with HTTP 401/403 for invalid credentials."
    ),

    # Scrape interval
    "scrape_interval_not_applied": (
        "Scrape interval not correctly applied.\n"
        "Expected: {expected}\n"
        "Actual: {actual}\n"
        "Tolerance: +/- 5 seconds"
    ),
    "scrape_interval_not_clamped": (
        "Out-of-range scrape interval was accepted without clamping.\n"
        "Attempted: {attempted}\n"
        "Effective: {effective}\n"
        "Allowed range: 30s - 60s"
    ),

    # Recovery
    "pod_not_auto_restarted": (
        "{component} pod was not auto-restarted by K8s.\n"
        "K8s Deployment controller should restart the pod."
    ),
    "metrics_not_resumed": (
        "PowerScale metrics did not resume after {component} recovery.\n"
        "Last metric timestamp: {last_ts}\n"
        "Please check pod logs for errors."
    ),

    # Deployment mode
    "deployment_pipeline_broken": (
        "Full metrics pipeline verification failed.\n"
        "CSM running: {csm_running}, OTel running: {otel_running}, "
        "Scrape up: {scrape_up}, Metrics present: {metrics_present}\n"
        "All components must be operational for PowerScale telemetry."
    ),

    # Dual destination
    "dual_dest_missing": (
        "Metrics missing from {destination} destination.\n"
        "Both internal and external destinations must receive metrics."
    ),
    "internal_affected_by_external": (
        "Internal VictoriaMetrics ingestion was interrupted by external endpoint failure.\n"
        "Internal path must be isolated from external endpoint failures."
    ),

    # Idempotency
    "duplicate_metrics_found": (
        "Duplicate metrics detected after redeployment.\n"
        "Duplicate count: {count}\n"
        "Redeployment must not create duplicate metrics."
    ),
    "config_changed_after_redeployment": (
        "Pod configuration changed after identical-config redeployment.\n"
        "Changed: {changed}\n"
        "Identical redeployment must preserve configuration."
    ),

    # Performance
    "latency_exceeded": (
        "Metric ingestion latency exceeded one scrape interval.\n"
        "Latency: {latency}s\n"
        "Scrape interval: {interval}s\n"
        "Metrics must appear within one scrape interval of emission."
    ),
    "syslog_latency_exceeded": (
        "Syslog event ingestion latency exceeded 1 minute.\n"
        "Latency: {latency}s\n"
        "Events must arrive within 60 seconds under nominal load."
    ),
    "availability_below_threshold": (
        "OTel Collector endpoint availability below 98%.\n"
        "Measured: {availability}%\n"
        "Required: >= 98% over 24 hours"
    ),

    # Security
    "credentials_in_artifacts": (
        "Plaintext credentials found in deployed artifacts.\n"
        "Location: {location}\n"
        "Pattern: {pattern}\n"
        "All credentials must be stored in K8s Secrets."
    ),
    "creds_not_in_secrets": (
        "PowerScale API credentials not stored in K8s Secrets.\n"
        "Credentials must be in K8s Secrets, not ConfigMaps or environment variables."
    ),
    "tls_keys_not_in_secrets": (
        "TLS private keys not stored in K8s Secrets.\n"
        "Private keys must be mounted from Secrets, not ConfigMaps."
    ),

    # Isolation
    "other_sources_affected": (
        "Other telemetry sources affected by PowerScale issue.\n"
        "Affected: {affected}\n"
        "PowerScale failures must not impact iDRAC, LDMS, or other sources."
    ),

    # Kafka / vminsert / vlinsert resilience
    "kafka_outage_affected_metrics": (
        "PowerScale metrics were disrupted during Kafka broker outage.\n"
        "Kafka is used for iDRAC/LDMS data only — PowerScale metric path must be isolated."
    ),
    "kafka_broker_not_recovered": (
        "Kafka broker did not recover after pod deletion.\n"
        "Strimzi operator should auto-restart the broker pod."
    ),
    "vminsert_outage_crashed_vmagent": (
        "vmagent crashed or became unhealthy during vminsert outage.\n"
        "vmagent must tolerate downstream vminsert failures gracefully."
    ),
    "vminsert_not_recovered": (
        "vminsert pod did not recover after deletion.\n"
        "VM operator should auto-restart the vminsert pod."
    ),
    "vlinsert_outage_affected_metrics": (
        "Metrics path was disrupted during vlinsert outage.\n"
        "vlinsert handles logs only — metrics path must be completely isolated."
    ),
    "vlinsert_not_recovered": (
        "vlinsert pod did not recover after deletion.\n"
        "VM operator should auto-restart the vlinsert pod."
    ),
}
