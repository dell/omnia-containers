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
UFM InfiniBand Telemetry - Sanity Test Cases.

This module contains functional, performance, and security test cases
for verifying UFM InfiniBand telemetry deployment as defined in
TSPEC-UFM-2026-001 and TCASES-UFM-2026-001.

Test cases (11 total):
  Functional (6): TC-F001, TC-F002, TC-F003, TC-F004, TC-F005, TC-F006, TC-F007, TC-F008
  Performance (1): TC-P001
  Security (2): TC-S001, TC-S002

Note: All tests skip if telemetry_sources.ufm.metrics_enabled is false.
      TC-F003 additionally skips if telemetry_sources.ufm.logs_enabled is false.
"""

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.messages.ufm_telemetry_msgs import (
    UFM_TEST_NAMES,
    UFM_LOG_MSGS,
    UFM_ASSERT_MSGS,
    UFM_SKIP_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    get_admin_ip,
    skip_if_ufm_not_enabled,
    skip_if_ufm_logs_not_enabled,
)
from automation_library.telemetry.vars.ufm_telemetry_vars import (
    UFM_CREDENTIALS_SECRET,
    UFM_VMSERVICESCRAPE_NAME,
)
from automation_library.telemetry.vars.shared_vars import TELEMETRY_NAMESPACE
from automation_library.telemetry.functions.ufm_telemetry_func import (
    verify_ufm_scrape_active,
    verify_ufm_dual_remotewrite,
    verify_ufm_syslog_ingestion,
    verify_ufm_deployment,
    verify_ufm_tls_basic_auth,
    verify_ufm_label_enrichment,
    verify_ufm_internal_remotewrite,
    verify_ufm_scrape_interval,
    verify_ufm_scrape_latency,
    verify_ufm_tls_enforcement,
    verify_ufm_no_plaintext_credentials,
    get_additional_remote_write_endpoints,
)


# =============================================================================
# 1. FUNCTIONAL TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(70)
def test_tc_f001_ufm_scrape_active(host):
    """
    TC-F001: UFM HTTPS Scraping with Authentication (P0).

    Verifies:
    - up{job=~"ufm.*"} == 1
    - UFM metrics present in VictoriaMetrics (count > 0)
    - Scrape samples being collected
    """
    log = TestLogger(UFM_TEST_NAMES["tc_f001_scrape_active"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying UFM scrape is active and metrics are present")
    result = verify_ufm_scrape_active(host, admin_ip)

    details = (
        f"Scrape up: {result.get('scrape_up')} (value={result.get('up_value')})\n"
        f"Series count: {result.get('series_count')}\n"
        f"Samples scraped: {result.get('samples_scraped')}"
    )

    if result["success"]:
        log.passed(
            UFM_LOG_MSGS["scrape_active"],
            details
        )
    else:
        log.failed(UFM_LOG_MSGS["scrape_not_active"], details)
        if not result.get("scrape_up"):
            assert False, UFM_ASSERT_MSGS["scrape_not_active"]
        else:
            assert False, UFM_ASSERT_MSGS["metrics_not_present"]


@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(71)
def test_tc_f002_ufm_dual_remotewrite(host):
    """
    TC-F002: Dual Remote-Write Pipeline (P0).

    Verifies:
    - Metrics written to local VictoriaMetrics (vminsert)
    - If additional_metric_remote_write_endpoints configured,
      metrics also written to remote endpoints
    - No excessive pending data buildup
    """
    log = TestLogger(UFM_TEST_NAMES["tc_f002_dual_remotewrite"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Check if additional endpoints are configured
    additional_endpoints = get_additional_remote_write_endpoints(host)
    if not additional_endpoints:
        log.skipped(
            UFM_SKIP_MSGS["no_additional_endpoints"],
            "No additional_metric_remote_write_endpoints in telemetry_config.yml"
        )
        pytest.skip(UFM_SKIP_MSGS["no_additional_endpoints"])

    log.check("Verifying dual remote-write pipeline")
    result = verify_ufm_dual_remotewrite(host, admin_ip)

    details = (
        f"Local write success: {result.get('local_write_success')}\n"
        f"Remote write success: {result.get('remote_write_success')}\n"
        f"Additional endpoints: {result.get('additional_endpoints_count')}\n"
        f"Series in VictoriaMetrics: {result.get('series_in_vm')}\n"
        f"Pending data bytes: {result.get('pending_data_bytes')}\n"
        f"Remote-write details: {result.get('remotewrite_details')}"
    )

    if result["success"]:
        log.passed(
            UFM_LOG_MSGS["dual_remotewrite_success"],
            details
        )
    else:
        log.failed(UFM_LOG_MSGS["dual_remotewrite_failed"], details)
        assert False, UFM_ASSERT_MSGS["dual_remotewrite_failed"]


@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(72)
def test_tc_f003_ufm_syslog_ingestion(host):
    """
    TC-F003: Syslog Ingestion to VictoriaLogs (P0).

    Verifies:
    - VLAgent pod is running
    - VLAgent syslog listener is configured on port 514
    - UFM syslog events present in VictoriaLogs
    """
    log = TestLogger(UFM_TEST_NAMES["tc_f003_syslog_ingestion"])
    skip_if_ufm_not_enabled(host, log)
    skip_if_ufm_logs_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying UFM syslog ingestion to VictoriaLogs")
    result = verify_ufm_syslog_ingestion(host, admin_ip)

    details = (
        f"VLAgent running: {result.get('vlagent_running')}\n"
        f"Syslog configured: {result.get('syslog_configured')} "
        f"(port={result.get('syslog_port')})\n"
        f"Events found: {result.get('events_found')} "
        f"(count={result.get('event_count')})\n"
        f"vlselect IP: {result.get('vlselect_ip')}"
    )

    if result["success"]:
        log.passed(
            UFM_LOG_MSGS["syslog_events_found"].format(
                count=result.get("event_count")
            ),
            details
        )
    else:
        log.failed(UFM_LOG_MSGS["syslog_events_not_found"], details)
        assert False, UFM_ASSERT_MSGS["syslog_not_ingested"]


@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(73)
def test_tc_f004_ufm_deployment(host):
    """
    TC-F004: UFM Telemetry Deployment Verification (P0).

    Verifies:
    - VMServiceScrape resource exists and is operational
    - UFM external service exists with endpoints
    - Credentials Secret exists with username/password keys
    - vmagent pods Running with 0 restarts
    - Scrape is active (up=1)
    """
    log = TestLogger(UFM_TEST_NAMES["tc_f004_deployment"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying UFM telemetry deployment components")
    result = verify_ufm_deployment(host, admin_ip)

    # Build details
    details_lines = []
    for comp in result.get("component_results", []):
        status = "\u2713" if comp["running"] else "\u2717"
        restart_info = (
            f" (restarts: {comp['restarts']})" if comp["restarts"] > 0 else ""
        )
        extra = f" [{comp['details']}]" if comp.get("details") else ""
        details_lines.append(
            f"{status} {comp['component']}: "
            f"{'OK' if comp['running'] else 'MISSING'}"
            f"{restart_info}{extra}"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            UFM_LOG_MSGS["vmservicescrape_exists"].format(
                name=UFM_VMSERVICESCRAPE_NAME
            ),
            details
        )
    else:
        if result.get("has_restarts"):
            log.failed(
                UFM_LOG_MSGS["vmagent_not_running"],
                details
            )
            assert False, UFM_ASSERT_MSGS["vmagent_not_running"]
        else:
            log.failed("UFM deployment verification failed", details)
            assert False, UFM_ASSERT_MSGS["deployment_failed"].format(
                missing=result.get("missing_components", [])
            )


@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(74)
def test_tc_f005_ufm_tls_basic_auth(host):
    """
    TC-F005: TLS and Basic Auth Verification (P0).

    Verifies:
    - VMServiceScrape has scheme: https
    - Basic Auth configured with credentials from K8s Secret
    - TLS config present (insecureSkipVerify or CA cert)
    - Scrape is active (TLS handshake succeeds)
    """
    log = TestLogger(UFM_TEST_NAMES["tc_f005_tls_basic_auth"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying TLS and Basic Auth configuration for UFM scrape")
    result = verify_ufm_tls_basic_auth(host, admin_ip)

    details = (
        f"TLS configured: {result.get('tls_configured')} "
        f"(scheme={result.get('scheme')})\n"
        f"Basic Auth configured: {result.get('basic_auth_configured')}\n"
        f"insecureSkipVerify: {result.get('insecure_skip_verify')}\n"
        f"Secret exists: {result.get('secret_exists')} "
        f"(keys={result.get('secret_keys')})\n"
        f"Scrape up: {result.get('scrape_up')}"
    )

    if result["success"]:
        log.passed(
            UFM_LOG_MSGS["tls_configured"] + " | " +
            UFM_LOG_MSGS["basic_auth_configured"],
            details
        )
    else:
        log.failed("TLS/Basic Auth verification failed", details)
        if not result.get("tls_configured"):
            assert False, UFM_ASSERT_MSGS["tls_not_configured"]
        elif not result.get("basic_auth_configured"):
            assert False, UFM_ASSERT_MSGS["basic_auth_not_configured"]
        elif not result.get("secret_exists"):
            assert False, UFM_ASSERT_MSGS["credentials_secret_missing"].format(
                secret=result.get("secret_name", UFM_CREDENTIALS_SECRET),
                namespace=TELEMETRY_NAMESPACE
            )
        else:
            assert False, UFM_ASSERT_MSGS["scrape_not_active"]


@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(75)
def test_tc_f006_ufm_label_enrichment(host):
    """
    TC-F006: UFM Metric Label Enrichment (P0).

    Verifies:
    - All UFM metrics have required labels (job, instance)
    - Enrichment labels (source, cluster) are present
    """
    log = TestLogger(UFM_TEST_NAMES["tc_f006_label_enrichment"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying UFM metric label enrichment")
    result = verify_ufm_label_enrichment(host, admin_ip)

    if result.get("error"):
        log.failed(result["error"], "")
        assert False, result["error"]

    # Build details
    details_lines = [f"Total series checked: {result.get('total_series', 0)}"]

    details_lines.append("\nRequired labels:")
    for lbl in result.get("required_label_results", []):
        status = "\u2713" if lbl["present"] else "\u2717"
        details_lines.append(
            f"  {status} {lbl['label']}: {lbl['count']}/{lbl['total']}"
        )

    details_lines.append("\nEnrichment labels:")
    for lbl in result.get("enrichment_label_results", []):
        status = "\u2713" if lbl["present"] else "\u2717"
        details_lines.append(
            f"  {status} {lbl['label']}: {lbl['count']}/{lbl['total']}"
        )

    # Show sample labels
    sample = result.get("sample_labels", {})
    if sample:
        details_lines.append(f"\nSample metric labels: {sample}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(UFM_LOG_MSGS["labels_present"], details)
    else:
        log.failed(UFM_LOG_MSGS["labels_missing"], details)
        assert False, UFM_ASSERT_MSGS["labels_missing"].format(
            missing=result.get("missing_required", [])
        )


@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(76)
def test_tc_f007_ufm_internal_remotewrite(host):
    """
    TC-F007: Internal Remote-Write to vminsert (P0).

    Verifies:
    - vmagent_remotewrite_requests_total with status_code=2XX is incrementing
    - UFM metrics present in VictoriaMetrics (via vmselect)
    - No pending data buildup
    """
    log = TestLogger(UFM_TEST_NAMES["tc_f007_internal_remotewrite"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying internal remote-write to vminsert")
    result = verify_ufm_internal_remotewrite(host, admin_ip)

    details = (
        f"Remote-write success: {result.get('remotewrite_success')}\n"
        f"Remote-write count: {result.get('remotewrite_count')}\n"
        f"Series in VictoriaMetrics: {result.get('series_in_vm')}\n"
        f"Pending data bytes: {result.get('pending_data_bytes')}"
    )

    if result["success"]:
        log.passed(UFM_LOG_MSGS["remotewrite_success"], details)
    else:
        log.failed(UFM_LOG_MSGS["remotewrite_failed"], details)
        assert False, UFM_ASSERT_MSGS["remotewrite_failed"]


@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(77)
def test_tc_f008_ufm_scrape_interval(host):
    """
    TC-F008: Scrape Interval Validation (P1).

    Verifies:
    - VMServiceScrape interval is within [15s, 60s]
    - Scrape timeout is less than interval
    """
    log = TestLogger(UFM_TEST_NAMES["tc_f008_scrape_interval"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying UFM scrape interval configuration")
    result = verify_ufm_scrape_interval(host, admin_ip)

    details = (
        f"Configured: {result.get('configured_interval')}\n"
        f"Interval (s): {result.get('interval_seconds')}\n"
        f"Within range [{result.get('min_allowed')}s-{result.get('max_allowed')}s]: "
        f"{result.get('within_range')}\n"
        f"Timeout: {result.get('timeout')} ({result.get('timeout_seconds')}s)\n"
        f"Timeout valid (< interval): {result.get('timeout_valid')}"
    )

    if result["success"]:
        log.passed(
            UFM_LOG_MSGS["scrape_interval_valid"].format(
                interval=result.get("configured_interval")
            ),
            details
        )
    else:
        log.failed(
            UFM_LOG_MSGS["scrape_interval_invalid"].format(
                interval=result.get("configured_interval")
            ),
            details
        )
        assert False, UFM_ASSERT_MSGS["scrape_interval_invalid"].format(
            interval=result.get("configured_interval"),
            min=result.get("min_allowed"),
            max=result.get("max_allowed"),
        )


# =============================================================================
# 2. PERFORMANCE TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(78)
def test_tc_p001_ufm_scrape_latency(host):
    """
    TC-P001: Scrape Latency Validation (P1).

    Verifies:
    - scrape_duration_seconds{job=~"ufm.*"} P99 < 5s (NFR threshold)
    - Scrape duration is within scrape interval
    """
    log = TestLogger(UFM_TEST_NAMES["tc_p001_scrape_latency"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying UFM scrape latency is within NFR threshold")
    result = verify_ufm_scrape_latency(host, admin_ip)

    details = (
        f"Scrape duration: {result.get('scrape_duration')}s\n"
        f"P99 threshold: {result.get('p99_threshold')}s\n"
        f"Within threshold: {result.get('within_threshold')}\n"
        f"Scrape interval: {result.get('scrape_interval')}s\n"
        f"Within interval: {result.get('within_interval')}"
    )

    if result["success"]:
        log.passed(
            UFM_LOG_MSGS["scrape_latency_ok"].format(
                latency=result.get("scrape_duration"),
                threshold=result.get("p99_threshold")
            ),
            details
        )
    else:
        log.failed(
            UFM_LOG_MSGS["scrape_latency_exceeded"].format(
                latency=result.get("scrape_duration"),
                threshold=result.get("p99_threshold")
            ),
            details
        )
        assert False, UFM_ASSERT_MSGS["scrape_latency_exceeded"].format(
            latency=result.get("scrape_duration"),
            threshold=result.get("p99_threshold")
        )


# =============================================================================
# 3. SECURITY TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(79)
def test_tc_s001_ufm_tls_enforcement(host):
    """
    TC-S001: TLS Enforcement for UFM Communication (P0).

    Verifies:
    - VMServiceScrape scheme is https
    - tlsConfig is present
    - Scrape is active (TLS handshake succeeds)
    """
    log = TestLogger(UFM_TEST_NAMES["tc_s001_tls_enforcement"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying TLS enforcement for UFM communication")
    result = verify_ufm_tls_enforcement(host, admin_ip)

    details_lines = []
    for check, passed in result.get("tls_checks", {}).items():
        status = "\u2713" if passed else "\u2717"
        details_lines.append(f"{status} {check}: {passed}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(UFM_LOG_MSGS["tls_enforced"], details)
    else:
        log.failed("TLS enforcement verification failed", details)
        assert False, UFM_ASSERT_MSGS["tls_not_configured"]


@pytest.mark.sanity
@pytest.mark.ufm_telemetry
@pytest.mark.order(80)
def test_tc_s002_ufm_no_plaintext_creds(host):
    """
    TC-S002: No Plaintext Credentials in Deployed Artifacts (P0).

    Verifies:
    - No credential patterns in vmagent pod logs
    - No plaintext credentials in ConfigMaps
    - Credentials stored in K8s Secrets only
    """
    log = TestLogger(UFM_TEST_NAMES["tc_s002_credential_security"])
    skip_if_ufm_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Checking for plaintext credentials in deployed artifacts")
    result = verify_ufm_no_plaintext_credentials(host, admin_ip)

    details_lines = [
        f"Findings: {len(result.get('findings', []))}",
        f"Credentials in Secrets: {result.get('credentials_in_secrets')}",
    ]
    for finding in result.get("findings", []):
        details_lines.append(
            f"  \u2717 {finding['location']}: pattern='{finding['pattern']}'"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(UFM_LOG_MSGS["no_creds_in_artifacts"], details)
    else:
        first_finding = result["findings"][0] if result.get("findings") else {}
        log.failed(UFM_LOG_MSGS["creds_found_in_artifacts"], details)
        assert False, UFM_ASSERT_MSGS["credentials_in_artifacts"].format(
            location=first_finding.get("location", "unknown"),
            pattern=first_finding.get("pattern", "unknown"),
        )
