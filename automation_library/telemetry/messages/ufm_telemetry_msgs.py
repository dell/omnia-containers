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
UFM InfiniBand Telemetry Automation - Messages.

This module contains all user-facing messages for UFM telemetry tests.
Covers sanity test cases mapped from TSPEC-UFM-2026-001 / TCASES-UFM-2026-001:
  Functional: TC-F001, TC-F002, TC-F003
  Performance: TC-P001
  Security: TC-S001, TC-S002
  Deployment: Deployment verification, label enrichment, scrape interval, remote-write
"""

from typing import Dict


# =============================================================================
# UFM TEST NAMES
# =============================================================================

UFM_TEST_NAMES: Dict[str, str] = {
    # Functional (from TCASES-UFM-2026-001)
    "tc_f001_scrape_active": "TC-F001: UFM HTTPS Scraping with Authentication",
    "tc_f002_dual_remotewrite": "TC-F002: Dual Remote-Write Pipeline",
    "tc_f003_syslog_ingestion": "TC-F003: Syslog Ingestion to VictoriaLogs",

    # Deployment verification (derived from test spec)
    "tc_f004_deployment": "TC-F004: UFM Telemetry Deployment Verification",
    "tc_f005_tls_basic_auth": "TC-F005: TLS and Basic Auth Verification",
    "tc_f006_label_enrichment": "TC-F006: UFM Metric Label Enrichment",
    "tc_f007_internal_remotewrite": "TC-F007: Internal Remote-Write to vminsert",
    "tc_f008_scrape_interval": "TC-F008: Scrape Interval Validation",

    # Performance (from TCASES-UFM-2026-001)
    "tc_p001_scrape_latency": "TC-P001: Scrape Latency Validation",

    # Security (from TCASES-UFM-2026-001)
    "tc_s001_tls_enforcement": "TC-S001: TLS Enforcement for UFM Communication",
    "tc_s002_credential_security": "TC-S002: No Plaintext Credentials in Artifacts",
}


# =============================================================================
# UFM LOG MESSAGES
# =============================================================================

UFM_LOG_MSGS: Dict[str, str] = {
    # Enable checks
    "ufm_enabled": "UFM telemetry is enabled",
    "ufm_not_enabled": "UFM telemetry is not enabled - skipping tests",
    "ufm_logs_enabled": "UFM syslog collection is enabled",
    "ufm_logs_not_enabled": "UFM syslog collection is not enabled - skipping test",

    # Scrape status
    "scrape_active": "UFM scrape is active (up=1)",
    "scrape_not_active": "UFM scrape is NOT active (up=0 or missing)",
    "metrics_present": "UFM metrics present in VictoriaMetrics ({count} series)",
    "metrics_not_present": "No UFM metrics found in VictoriaMetrics",

    # TLS / Auth
    "tls_configured": "TLS is configured for UFM scrape (scheme: https)",
    "tls_not_configured": "TLS is NOT configured for UFM scrape",
    "basic_auth_configured": "Basic Auth is configured for UFM scrape",
    "basic_auth_not_configured": "Basic Auth is NOT configured for UFM scrape",
    "credentials_secret_exists": "Credentials secret '{secret}' exists in namespace",
    "credentials_secret_missing": "Credentials secret '{secret}' NOT found",

    # Labels
    "labels_present": "All required labels present on UFM metrics",
    "labels_missing": "Some required labels missing from UFM metrics",
    "enrichment_labels_present": "Enrichment labels present: {labels}",
    "enrichment_labels_missing": "Enrichment labels missing: {labels}",

    # Remote write
    "remotewrite_success": "Remote-write to vminsert is successful",
    "remotewrite_failed": "Remote-write to vminsert is failing",

    # Dual remote-write
    "dual_remotewrite_success": "Metrics present in both local and remote VictoriaMetrics",
    "dual_remotewrite_failed": "Metrics NOT present in both local and remote VictoriaMetrics",
    "additional_endpoints_configured": "Additional remote-write endpoints configured: {count}",
    "no_additional_endpoints": "No additional remote-write endpoints configured",

    # Syslog
    "syslog_events_found": "UFM syslog events found in VictoriaLogs ({count} events)",
    "syslog_events_not_found": "No UFM syslog events found in VictoriaLogs",
    "vlagent_syslog_configured": "VLAgent syslog listener configured on port {port}",

    # Deployment
    "vmservicescrape_exists": "VMServiceScrape '{name}' exists",
    "vmservicescrape_missing": "VMServiceScrape '{name}' NOT found",
    "vmagent_running": "vmagent pods are Running ({count} pods, {restarts} restarts)",
    "vmagent_not_running": "vmagent pods are NOT Running",
    "service_exists": "UFM external service '{name}' exists",
    "service_missing": "UFM external service '{name}' NOT found",

    # Scrape interval
    "scrape_interval_valid": "Scrape interval is within range: {interval}",
    "scrape_interval_invalid": "Scrape interval is out of range: {interval}",

    # Scrape latency / duration
    "scrape_latency_ok": "Scrape latency P99 {latency}s < {threshold}s",
    "scrape_latency_exceeded": "Scrape latency P99 {latency}s >= {threshold}s",
    "scrape_duration_ok": "Scrape duration {duration}s is within interval {interval}s",
    "scrape_duration_exceeded": "Scrape duration {duration}s exceeds interval {interval}s",

    # Security
    "tls_enforced": "TLS enforcement verified for UFM communication",
    "no_creds_in_artifacts": "No plaintext credentials found in deployed artifacts",
    "creds_found_in_artifacts": "Plaintext credentials found in deployed artifacts",
}


# =============================================================================
# UFM ASSERT MESSAGES (include HOW TO FIX sections)
# =============================================================================

UFM_ASSERT_MSGS: Dict[str, str] = {
    # Scrape
    "scrape_not_active": (
        "UFM scrape is not active: up metric is 0 or missing.\n\n"
        "HOW TO FIX:\n"
        "  1. Verify UFM appliance is reachable: curl -k https://<UFM_IP>:9001/prometheusmetrics\n"
        "  2. Check VMServiceScrape: kubectl get vmservicescrapes -n telemetry\n"
        "  3. Check vmagent logs: kubectl logs -n telemetry -l app.kubernetes.io/name=vmagent\n"
        "  4. Verify UFM credentials secret: kubectl get secret ufm-telemetry-credentials -n telemetry\n"
        "  5. Re-run telemetry playbook: podman exec omnia_core ansible-playbook /omnia/telemetry/telemetry.yml"
    ),
    "metrics_not_present": (
        "No UFM metrics found in VictoriaMetrics.\n\n"
        "HOW TO FIX:\n"
        "  1. Verify vmagent is scraping: check up{job=~\"ufm.*\"} in VictoriaMetrics\n"
        "  2. Check vmagent remote-write to vminsert\n"
        "  3. Verify vminsert is accepting writes\n"
        "  4. Wait 2 scrape intervals and retry"
    ),

    # TLS / Auth
    "tls_not_configured": (
        "TLS is not configured for UFM scrape.\n\n"
        "HOW TO FIX:\n"
        "  1. Verify ufm_configuration.tls_mode in telemetry_config.yml\n"
        "  2. VMServiceScrape should have scheme: https\n"
        "  3. Re-run telemetry playbook to regenerate configuration"
    ),
    "basic_auth_not_configured": (
        "Basic Auth is not configured for UFM scrape.\n\n"
        "HOW TO FIX:\n"
        "  1. Verify ufm_configuration.auth_mode is 'basic' in telemetry_config.yml\n"
        "  2. Verify UFM credentials in omnia_config_credentials.yml\n"
        "  3. VMServiceScrape should reference credentials Secret"
    ),
    "credentials_secret_missing": (
        "Credentials secret '{secret}' not found in namespace {namespace}.\n\n"
        "HOW TO FIX:\n"
        "  1. Verify UFM credentials are set in omnia_config_credentials.yml\n"
        "  2. Re-run telemetry playbook to create the secret\n"
        "  3. Check: kubectl get secrets -n telemetry | grep ufm"
    ),

    # Labels
    "labels_missing": (
        "Required labels missing from UFM metrics: {missing}.\n\n"
        "HOW TO FIX:\n"
        "  1. Check VMServiceScrape relabelings configuration\n"
        "  2. Verify UFM Prometheus exporter is returning properly labeled metrics\n"
        "  3. Re-run telemetry playbook"
    ),

    # Remote write
    "remotewrite_failed": (
        "Remote-write to vminsert is not working.\n\n"
        "HOW TO FIX:\n"
        "  1. Check vmagent remote-write configuration\n"
        "  2. Verify vminsert is reachable from vmagent\n"
        "  3. Check vmagent logs for remote-write errors\n"
        "  4. kubectl logs -n telemetry -l app.kubernetes.io/name=vmagent | grep -i remote"
    ),

    # Dual remote-write
    "dual_remotewrite_failed": (
        "Metrics not present in both local and remote VictoriaMetrics.\n\n"
        "HOW TO FIX:\n"
        "  1. Check additional_metric_remote_write_endpoints in telemetry_config.yml\n"
        "  2. Verify remote endpoint is reachable from vmagent\n"
        "  3. Check vmagent logs for remote-write errors to each endpoint\n"
        "  4. Verify vmagent_remotewrite_requests_total for each URL"
    ),

    # Syslog
    "syslog_not_ingested": (
        "UFM syslog events not found in VictoriaLogs.\n\n"
        "HOW TO FIX:\n"
        "  1. Verify UFM is configured to send syslog to VLAgent IP:514 (UDP)\n"
        "  2. Check VLAgent pod is running: kubectl get pods -n telemetry -l app=vlagent\n"
        "  3. Verify VLAgent syslog listener: kubectl logs -n telemetry -l app=vlagent\n"
        "  4. Check VictoriaLogs query: search for source='ufm' in VictoriaLogs\n"
        "  5. Verify telemetry_sources.ufm.logs_enabled is true"
    ),

    # Deployment
    "vmservicescrape_missing": (
        "VMServiceScrape '{name}' not found in namespace {namespace}.\n\n"
        "HOW TO FIX:\n"
        "  1. Re-run telemetry playbook\n"
        "  2. Check Kustomize deployment: kubectl get vmservicescrapes -n telemetry"
    ),
    "vmagent_not_running": (
        "vmagent pods are not running.\n\n"
        "HOW TO FIX:\n"
        "  1. Check vmagent deployment: kubectl get pods -n telemetry -l app.kubernetes.io/name=vmagent\n"
        "  2. Check pod events: kubectl describe pod -n telemetry -l app.kubernetes.io/name=vmagent\n"
        "  3. Check vmagent logs for errors"
    ),
    "deployment_failed": (
        "UFM telemetry deployment verification failed.\n"
        "Missing components: {missing}\n\n"
        "HOW TO FIX:\n"
        "  1. Verify telemetry_sources.ufm.metrics_enabled is true in telemetry_config.yml\n"
        "  2. Re-run telemetry playbook\n"
        "  3. Check Kustomize apply output for errors"
    ),

    # Scrape interval
    "scrape_interval_invalid": (
        "Scrape interval {interval} is not within allowed range [{min}s-{max}s].\n\n"
        "HOW TO FIX:\n"
        "  1. Update ufm_configuration.scrape_interval in telemetry_config.yml\n"
        "  2. Re-run telemetry playbook"
    ),

    # Scrape latency
    "scrape_latency_exceeded": (
        "Scrape latency P99 {latency}s exceeds NFR threshold {threshold}s.\n\n"
        "HOW TO FIX:\n"
        "  1. Check UFM appliance load and responsiveness\n"
        "  2. Verify network connectivity between K8s cluster and UFM\n"
        "  3. Consider increasing scrape_timeout in telemetry_config.yml\n"
        "  4. Check UFM Prometheus exporter performance"
    ),

    # Scrape duration
    "scrape_duration_exceeded": (
        "Scrape duration {duration}s exceeds scrape interval {interval}s.\n\n"
        "HOW TO FIX:\n"
        "  1. Increase scrape_interval in ufm_configuration\n"
        "  2. Check UFM appliance performance\n"
        "  3. Verify network latency between K8s and UFM"
    ),

    # Security
    "credentials_in_artifacts": (
        "Plaintext credentials found in {location}: pattern='{pattern}'.\n\n"
        "HOW TO FIX:\n"
        "  1. Move credentials to K8s Secrets\n"
        "  2. Use basic_auth.password_file in VMServiceScrape\n"
        "  3. Verify no credentials in ConfigMaps or pod logs\n"
        "  4. Re-run telemetry playbook to regenerate configuration"
    ),
}


# =============================================================================
# UFM SKIP MESSAGES
# =============================================================================

UFM_SKIP_MSGS: Dict[str, str] = {
    "ufm_not_enabled": "UFM telemetry is not enabled (ufm.metrics_enabled=false)",
    "ufm_logs_not_enabled": "UFM syslog collection is not enabled (ufm.logs_enabled=false)",
    "no_additional_endpoints": "No additional remote-write endpoints configured - dual-write test skipped",
}
