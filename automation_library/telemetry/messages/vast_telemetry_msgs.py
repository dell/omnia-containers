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
VAST Storage Telemetry Automation - Messages.

This module contains all user-facing messages for VAST telemetry tests.
Covers positive/sanity test cases: Functional, Performance, Security.
"""

from typing import Dict


# =============================================================================
# VAST TEST NAMES
# =============================================================================

VAST_TEST_NAMES: Dict[str, str] = {
    # Functional
    "tc_f001_scrape_active": "TC-F001: VAST Scrape Active and Metrics Present",
    "tc_f002_tls_basic_auth": "TC-F002: TLS and Basic Auth Verification",
    "tc_f003_label_enrichment": "TC-F003: VAST Metric Label Enrichment",
    "tc_f004_internal_remotewrite": "TC-F004: Internal Remote-Write to vminsert",
    "tc_f008_scrape_interval": "TC-F008: Scrape Interval Validation",
    "tc_f012_deployment": "TC-F012: VAST Telemetry Deployment Verification",

    # Performance
    "tc_p001_scrape_duration": "TC-P001: Scrape Duration Within Interval",
    "tc_p002_metric_coverage": "TC-P002: VAST Metric Family Coverage >= 90%",

    # Security
    "tc_s001_tls_enforcement": "TC-S001: TLS Enforcement for VAST Communication",
    "tc_s002_no_plaintext_creds": "TC-S002: No Plaintext Credentials in Artifacts",

    # Negative / Error
    "tc_e001_pod_delete_recovery": "TC-E001: Pod Deletion and Recovery — Full Telemetry Stack",
}


# =============================================================================
# VAST LOG MESSAGES
# =============================================================================

VAST_LOG_MSGS: Dict[str, str] = {
    # Enable checks
    "vast_enabled": "VAST telemetry is enabled",
    "vast_not_enabled": "VAST telemetry is not enabled - skipping tests",

    # Scrape status
    "scrape_active": "VAST scrape is active (up=1)",
    "scrape_not_active": "VAST scrape is NOT active (up=0 or missing)",
    "metrics_present": "VAST metrics present in VictoriaMetrics ({count} series)",
    "metrics_not_present": "No VAST metrics found in VictoriaMetrics",

    # TLS / Auth
    "tls_configured": "TLS is configured for VAST scrape (scheme: https)",
    "tls_not_configured": "TLS is NOT configured for VAST scrape",
    "basic_auth_configured": "Basic Auth is configured for VAST scrape",
    "basic_auth_not_configured": "Basic Auth is NOT configured for VAST scrape",
    "credentials_secret_exists": "Credentials secret '{secret}' exists in namespace",
    "credentials_secret_missing": "Credentials secret '{secret}' NOT found",

    # Labels
    "labels_present": "All required labels present on VAST metrics",
    "labels_missing": "Some required labels missing from VAST metrics",
    "enrichment_labels_present": "Enrichment labels present: {labels}",
    "enrichment_labels_missing": "Enrichment labels missing: {labels}",

    # Remote write
    "remotewrite_success": "Remote-write to vminsert is successful",
    "remotewrite_failed": "Remote-write to vminsert is failing",

    # Deployment
    "vmservicescrape_exists": "VMServiceScrape '{name}' exists",
    "vmservicescrape_missing": "VMServiceScrape '{name}' NOT found",
    "vmagent_running": "vmagent pods are Running ({count} pods, {restarts} restarts)",
    "vmagent_not_running": "vmagent pods are NOT Running",
    "service_exists": "VAST external service '{name}' exists",
    "service_missing": "VAST external service '{name}' NOT found",

    # Scrape interval
    "scrape_interval_valid": "Scrape interval is within range: {interval}",
    "scrape_interval_invalid": "Scrape interval is out of range: {interval}",

    # Scrape duration
    "scrape_duration_ok": "Scrape duration {duration}s is within interval {interval}s",
    "scrape_duration_exceeded": "Scrape duration {duration}s exceeds interval {interval}s",

    # Coverage
    "coverage_met": "Metric family coverage {percent}% >= {threshold}% ({count} families)",
    "coverage_not_met": "Metric family coverage {percent}% < {threshold}% ({count} families)",

    # Security
    "tls_enforced": "TLS enforcement verified for VAST communication",
    "no_creds_in_artifacts": "No plaintext credentials found in deployed artifacts",
    "creds_found_in_artifacts": "Plaintext credentials found in deployed artifacts",

    # Negative / Error (TC-E001)
    "pods_recorded": "Recorded {count} telemetry pods before deletion",
    "pods_deleted": "All telemetry pods deleted from namespace",
    "pods_recovered": "All {count} telemetry pods recovered to Running state",
    "pods_not_recovered": "{not_running} of {total} pods not recovered after {timeout}s",
    "scrape_recovered": "VAST scrape recovered — metrics readable after pod recovery",
    "scrape_not_recovered": "VAST scrape NOT recovered after pod recovery",
}


# =============================================================================
# VAST ASSERT MESSAGES
# =============================================================================

VAST_ASSERT_MSGS: Dict[str, str] = {
    # Scrape
    "scrape_not_active": (
        "VAST scrape is not active: up metric is 0 or missing. "
        "Check VMServiceScrape configuration and VAST connectivity."
    ),
    "metrics_not_present": (
        "No VAST metrics found in VictoriaMetrics. "
        "Verify vmagent is scraping and remote-writing to vminsert."
    ),

    # TLS / Auth
    "tls_not_configured": (
        "TLS is not configured for VAST scrape. "
        "VMServiceScrape should have scheme: https."
    ),
    "basic_auth_not_configured": (
        "Basic Auth is not configured for VAST scrape. "
        "VMServiceScrape should reference credentials Secret."
    ),
    "credentials_secret_missing": (
        "Credentials secret '{secret}' not found in namespace {namespace}."
    ),

    # Labels
    "labels_missing": (
        "Required labels missing from VAST metrics: {missing}. "
        "Check VMServiceScrape relabelings configuration."
    ),
    "enrichment_labels_missing": (
        "Enrichment labels missing from VAST metrics: {missing}. "
        "Check VMServiceScrape metricRelabelings configuration."
    ),

    # Remote write
    "remotewrite_failed": (
        "Remote-write to vminsert is not working. "
        "Check vmagent remote-write configuration and vminsert availability."
    ),

    # Deployment
    "vmservicescrape_missing": (
        "VMServiceScrape '{name}' not found in namespace {namespace}."
    ),
    "vmagent_not_running": (
        "vmagent pods are not running. "
        "Check vmagent deployment status."
    ),
    "service_missing": (
        "VAST external service '{name}' not found in namespace {namespace}."
    ),
    "deployment_failed": (
        "VAST telemetry deployment verification failed. "
        "Missing components: {missing}"
    ),

    # Scrape interval
    "scrape_interval_invalid": (
        "Scrape interval {interval} is not within allowed range "
        "[{min}s-{max}s]."
    ),

    # Scrape duration
    "scrape_duration_exceeded": (
        "Scrape duration {duration}s exceeds scrape interval {interval}s."
    ),

    # Coverage
    "coverage_not_met": (
        "VAST metric family coverage {percent}% is below threshold {threshold}%. "
        "Found {count} families, expected >= {expected}."
    ),

    # Security
    "credentials_in_artifacts": (
        "Plaintext credentials found in {location}: pattern='{pattern}'."
    ),

    # Negative / Error (TC-E001)
    "pod_recovery_failed": (
        "Telemetry pods did not recover after force-deletion.\n"
        "Expected: All pods return to Running within timeout.\n"
        "Not running: {not_running_pods}\n"
        "Fix: Check K8s scheduler, node resources, and pod events."
    ),
    "scrape_recovery_failed": (
        "VAST scrape did not resume after pod recovery.\n"
        "Expected: up{{job=~\"vast.*\"}} == 1 and metrics queryable.\n"
        "Series count: {series_count}\n"
        "Fix: Check vmagent logs and VMServiceScrape configuration."
    ),
}
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
VAST Storage Telemetry Automation - Messages.

This module contains all user-facing messages for VAST telemetry tests.
Covers positive/sanity test cases: Functional, Performance, Security.
"""

from typing import Dict


# =============================================================================
# VAST TEST NAMES
# =============================================================================

VAST_TEST_NAMES: Dict[str, str] = {
    # Functional
    "tc_f001_scrape_active": "TC-F001: VAST Scrape Active and Metrics Present",
    "tc_f002_tls_basic_auth": "TC-F002: TLS and Basic Auth Verification",
    "tc_f003_label_enrichment": "TC-F003: VAST Metric Label Enrichment",
    "tc_f004_internal_remotewrite": "TC-F004: Internal Remote-Write to vminsert",
    "tc_f008_scrape_interval": "TC-F008: Scrape Interval Validation",
    "tc_f012_deployment": "TC-F012: VAST Telemetry Deployment Verification",

    # Performance
    "tc_p001_scrape_duration": "TC-P001: Scrape Duration Within Interval",
    "tc_p002_metric_coverage": "TC-P002: VAST Metric Family Coverage >= 90%",

    # Security
    "tc_s001_tls_enforcement": "TC-S001: TLS Enforcement for VAST Communication",
    "tc_s002_no_plaintext_creds": "TC-S002: No Plaintext Credentials in Artifacts",

    # Negative / Error
    "tc_e001_pod_delete_recovery": "TC-E001: Pod Deletion and Recovery — Full Telemetry Stack",
}


# =============================================================================
# VAST LOG MESSAGES
# =============================================================================

VAST_LOG_MSGS: Dict[str, str] = {
    # Enable checks
    "vast_enabled": "VAST telemetry is enabled",
    "vast_not_enabled": "VAST telemetry is not enabled - skipping tests",

    # Scrape status
    "scrape_active": "VAST scrape is active (up=1)",
    "scrape_not_active": "VAST scrape is NOT active (up=0 or missing)",
    "metrics_present": "VAST metrics present in VictoriaMetrics ({count} series)",
    "metrics_not_present": "No VAST metrics found in VictoriaMetrics",

    # TLS / Auth
    "tls_configured": "TLS is configured for VAST scrape (scheme: https)",
    "tls_not_configured": "TLS is NOT configured for VAST scrape",
    "basic_auth_configured": "Basic Auth is configured for VAST scrape",
    "basic_auth_not_configured": "Basic Auth is NOT configured for VAST scrape",
    "credentials_secret_exists": "Credentials secret '{secret}' exists in namespace",
    "credentials_secret_missing": "Credentials secret '{secret}' NOT found",

    # Labels
    "labels_present": "All required labels present on VAST metrics",
    "labels_missing": "Some required labels missing from VAST metrics",
    "enrichment_labels_present": "Enrichment labels present: {labels}",
    "enrichment_labels_missing": "Enrichment labels missing: {labels}",

    # Remote write
    "remotewrite_success": "Remote-write to vminsert is successful",
    "remotewrite_failed": "Remote-write to vminsert is failing",

    # Deployment
    "vmservicescrape_exists": "VMServiceScrape '{name}' exists",
    "vmservicescrape_missing": "VMServiceScrape '{name}' NOT found",
    "vmagent_running": "vmagent pods are Running ({count} pods, {restarts} restarts)",
    "vmagent_not_running": "vmagent pods are NOT Running",
    "service_exists": "VAST external service '{name}' exists",
    "service_missing": "VAST external service '{name}' NOT found",

    # Scrape interval
    "scrape_interval_valid": "Scrape interval is within range: {interval}",
    "scrape_interval_invalid": "Scrape interval is out of range: {interval}",

    # Scrape duration
    "scrape_duration_ok": "Scrape duration {duration}s is within interval {interval}s",
    "scrape_duration_exceeded": "Scrape duration {duration}s exceeds interval {interval}s",

    # Coverage
    "coverage_met": "Metric family coverage {percent}% >= {threshold}% ({count} families)",
    "coverage_not_met": "Metric family coverage {percent}% < {threshold}% ({count} families)",

    # Security
    "tls_enforced": "TLS enforcement verified for VAST communication",
    "no_creds_in_artifacts": "No plaintext credentials found in deployed artifacts",
    "creds_found_in_artifacts": "Plaintext credentials found in deployed artifacts",

    # Negative / Error (TC-E001)
    "pods_recorded": "Recorded {count} telemetry pods before deletion",
    "pods_deleted": "All telemetry pods deleted from namespace",
    "pods_recovered": "All {count} telemetry pods recovered to Running state",
    "pods_not_recovered": "{not_running} of {total} pods not recovered after {timeout}s",
    "scrape_recovered": "VAST scrape recovered — metrics readable after pod recovery",
    "scrape_not_recovered": "VAST scrape NOT recovered after pod recovery",
}


# =============================================================================
# VAST ASSERT MESSAGES
# =============================================================================

VAST_ASSERT_MSGS: Dict[str, str] = {
    # Scrape
    "scrape_not_active": (
        "VAST scrape is not active: up metric is 0 or missing. "
        "Check VMServiceScrape configuration and VAST connectivity."
    ),
    "metrics_not_present": (
        "No VAST metrics found in VictoriaMetrics. "
        "Verify vmagent is scraping and remote-writing to vminsert."
    ),

    # TLS / Auth
    "tls_not_configured": (
        "TLS is not configured for VAST scrape. "
        "VMServiceScrape should have scheme: https."
    ),
    "basic_auth_not_configured": (
        "Basic Auth is not configured for VAST scrape. "
        "VMServiceScrape should reference credentials Secret."
    ),
    "credentials_secret_missing": (
        "Credentials secret '{secret}' not found in namespace {namespace}."
    ),

    # Labels
    "labels_missing": (
        "Required labels missing from VAST metrics: {missing}. "
        "Check VMServiceScrape relabelings configuration."
    ),
    "enrichment_labels_missing": (
        "Enrichment labels missing from VAST metrics: {missing}. "
        "Check VMServiceScrape metricRelabelings configuration."
    ),

    # Remote write
    "remotewrite_failed": (
        "Remote-write to vminsert is not working. "
        "Check vmagent remote-write configuration and vminsert availability."
    ),

    # Deployment
    "vmservicescrape_missing": (
        "VMServiceScrape '{name}' not found in namespace {namespace}."
    ),
    "vmagent_not_running": (
        "vmagent pods are not running. "
        "Check vmagent deployment status."
    ),
    "service_missing": (
        "VAST external service '{name}' not found in namespace {namespace}."
    ),
    "deployment_failed": (
        "VAST telemetry deployment verification failed. "
        "Missing components: {missing}"
    ),

    # Scrape interval
    "scrape_interval_invalid": (
        "Scrape interval {interval} is not within allowed range "
        "[{min}s-{max}s]."
    ),

    # Scrape duration
    "scrape_duration_exceeded": (
        "Scrape duration {duration}s exceeds scrape interval {interval}s."
    ),

    # Coverage
    "coverage_not_met": (
        "VAST metric family coverage {percent}% is below threshold {threshold}%. "
        "Found {count} families, expected >= {expected}."
    ),

    # Security
    "credentials_in_artifacts": (
        "Plaintext credentials found in {location}: pattern='{pattern}'."
    ),

    # Negative / Error (TC-E001)
    "pod_recovery_failed": (
        "Telemetry pods did not recover after force-deletion.\n"
        "Expected: All pods return to Running within timeout.\n"
        "Not running: {not_running_pods}\n"
        "Fix: Check K8s scheduler, node resources, and pod events."
    ),
    "scrape_recovery_failed": (
        "VAST scrape did not resume after pod recovery.\n"
        "Expected: up{{job=~\"vast.*\"}} == 1 and metrics queryable.\n"
        "Series count: {series_count}\n"
        "Fix: Check vmagent logs and VMServiceScrape configuration."
    ),
}
