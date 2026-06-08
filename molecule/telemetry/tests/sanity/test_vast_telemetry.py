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
VAST Storage Telemetry - Sanity Test Cases.

This module contains functional, performance, and security test cases
for verifying VAST storage telemetry deployment as defined in the
VAST telemetry test specification.

Test cases (10 total):
  Functional (6): TC-F001, TC-F002, TC-F003, TC-F004, TC-F008, TC-F012
  Performance (2): TC-P001, TC-P002
  Security (2): TC-S001, TC-S002

Note: All tests skip if telemetry_sources.vast.metrics_enabled is false.
"""

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.messages.vast_telemetry_msgs import (
    VAST_TEST_NAMES,
    VAST_LOG_MSGS,
    VAST_ASSERT_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    get_admin_ip,
    skip_if_vast_not_enabled,
)
from automation_library.telemetry.vars.vast_telemetry_vars import (
    VAST_CREDENTIALS_SECRET,
    VAST_VMSERVICESCRAPE_NAME,
)
from automation_library.telemetry.vars.shared_vars import TELEMETRY_NAMESPACE
from automation_library.telemetry.functions.vast_telemetry_func import (
    verify_vast_scrape_active,
    verify_vast_tls_basic_auth,
    verify_vast_label_enrichment,
    verify_vast_internal_remotewrite,
    verify_vast_scrape_interval,
    verify_vast_deployment,
    verify_vast_scrape_duration,
    verify_vast_metric_coverage,
    verify_vast_tls_enforcement,
    verify_vast_no_plaintext_credentials,
)


# =============================================================================
# 1. FUNCTIONAL TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(60)
def test_tc_f001_vast_scrape_active(host):
    """
    TC-F001: VAST Scrape Active and Metrics Present (P0).

    Verifies:
    - up{job=~"vast.*"} == 1
    - VAST metrics present in VictoriaMetrics (count > 0)
    - Scrape samples being collected
    """
    log = TestLogger(VAST_TEST_NAMES["tc_f001_scrape_active"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VAST scrape is active and metrics are present")
    result = verify_vast_scrape_active(host, admin_ip)

    details = (
        f"Scrape up: {result.get('scrape_up')} (value={result.get('up_value')})\n"
        f"Series count: {result.get('series_count')}\n"
        f"Samples scraped: {result.get('samples_scraped')}"
    )

    if result["success"]:
        log.passed(
            VAST_LOG_MSGS["scrape_active"],
            details
        )
    else:
        log.failed(VAST_LOG_MSGS["scrape_not_active"], details)
        if not result.get("scrape_up"):
            assert False, VAST_ASSERT_MSGS["scrape_not_active"]
        else:
            assert False, VAST_ASSERT_MSGS["metrics_not_present"]


@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(61)
def test_tc_f002_vast_tls_basic_auth(host):
    """
    TC-F002: TLS and Basic Auth Verification (P0).

    Verifies:
    - VMServiceScrape has scheme: https
    - Basic Auth configured with credentials from K8s Secret
    - TLS config present (insecureSkipVerify or CA cert)
    - Scrape is active (TLS handshake succeeds)
    """
    log = TestLogger(VAST_TEST_NAMES["tc_f002_tls_basic_auth"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying TLS and Basic Auth configuration for VAST scrape")
    result = verify_vast_tls_basic_auth(host, admin_ip)

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
            VAST_LOG_MSGS["tls_configured"] + " | " +
            VAST_LOG_MSGS["basic_auth_configured"],
            details
        )
    else:
        log.failed("TLS/Basic Auth verification failed", details)
        if not result.get("tls_configured"):
            assert False, VAST_ASSERT_MSGS["tls_not_configured"]
        elif not result.get("basic_auth_configured"):
            assert False, VAST_ASSERT_MSGS["basic_auth_not_configured"]
        elif not result.get("secret_exists"):
            assert False, VAST_ASSERT_MSGS["credentials_secret_missing"].format(
                secret=result.get("secret_name", VAST_CREDENTIALS_SECRET),
                namespace=TELEMETRY_NAMESPACE
            )
        else:
            assert False, VAST_ASSERT_MSGS["scrape_not_active"]


@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(62)
def test_tc_f003_vast_label_enrichment(host):
    """
    TC-F003: VAST Metric Label Enrichment (P0).

    Verifies:
    - All VAST metrics have required labels (job, instance)
    - Enrichment labels (source, subsystem) are present
    """
    log = TestLogger(VAST_TEST_NAMES["tc_f003_label_enrichment"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VAST metric label enrichment")
    result = verify_vast_label_enrichment(host, admin_ip)

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
        log.passed(VAST_LOG_MSGS["labels_present"], details)
    else:
        log.failed(VAST_LOG_MSGS["labels_missing"], details)
        assert False, VAST_ASSERT_MSGS["labels_missing"].format(
            missing=result.get("missing_required", [])
        )


@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(63)
def test_tc_f004_vast_internal_remotewrite(host):
    """
    TC-F004: Internal Remote-Write to vminsert (P0).

    Verifies:
    - vmagent_remotewrite_requests_total with status_code=2XX is incrementing
    - VAST metrics present in VictoriaMetrics (via vmselect)
    - No pending data buildup
    """
    log = TestLogger(VAST_TEST_NAMES["tc_f004_internal_remotewrite"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying internal remote-write to vminsert")
    result = verify_vast_internal_remotewrite(host, admin_ip)

    details = (
        f"Remote-write success: {result.get('remotewrite_success')}\n"
        f"Remote-write count: {result.get('remotewrite_count')}\n"
        f"Series in VictoriaMetrics: {result.get('series_in_vm')}\n"
        f"Pending data bytes: {result.get('pending_data_bytes')}"
    )

    if result["success"]:
        log.passed(VAST_LOG_MSGS["remotewrite_success"], details)
    else:
        log.failed(VAST_LOG_MSGS["remotewrite_failed"], details)
        assert False, VAST_ASSERT_MSGS["remotewrite_failed"]


@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(64)
def test_tc_f008_vast_scrape_interval(host):
    """
    TC-F008: Scrape Interval Validation (P1).

    Verifies:
    - VMServiceScrape interval is within [30s, 60s]
    - Scrape timeout is less than interval
    """
    log = TestLogger(VAST_TEST_NAMES["tc_f008_scrape_interval"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VAST scrape interval configuration")
    result = verify_vast_scrape_interval(host, admin_ip)

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
            VAST_LOG_MSGS["scrape_interval_valid"].format(
                interval=result.get("configured_interval")
            ),
            details
        )
    else:
        log.failed(
            VAST_LOG_MSGS["scrape_interval_invalid"].format(
                interval=result.get("configured_interval")
            ),
            details
        )
        assert False, VAST_ASSERT_MSGS["scrape_interval_invalid"].format(
            interval=result.get("configured_interval"),
            min=result.get("min_allowed"),
            max=result.get("max_allowed"),
        )


@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(65)
def test_tc_f012_vast_deployment(host):
    """
    TC-F012: VAST Telemetry Deployment Verification (P0).

    Verifies:
    - VMServiceScrape resource exists and is operational
    - VAST external service exists with endpoints
    - Credentials Secret exists with username/password keys
    - vmagent pods Running with 0 restarts
    - Scrape is active (up=1)
    """
    log = TestLogger(VAST_TEST_NAMES["tc_f012_deployment"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VAST telemetry deployment components")
    result = verify_vast_deployment(host, admin_ip)

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
            VAST_LOG_MSGS["vmservicescrape_exists"].format(
                name=VAST_VMSERVICESCRAPE_NAME
            ),
            details
        )
    else:
        if result.get("has_restarts"):
            log.failed(
                VAST_LOG_MSGS["vmagent_not_running"],
                details
            )
            assert False, VAST_ASSERT_MSGS["vmagent_not_running"]
        else:
            log.failed("VAST deployment verification failed", details)
            assert False, VAST_ASSERT_MSGS["deployment_failed"].format(
                missing=result.get("missing_components", [])
            )


# =============================================================================
# 2. PERFORMANCE TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(66)
def test_tc_p001_vast_scrape_duration(host):
    """
    TC-P001: Scrape Duration Within Interval (P0).

    Verifies scrape_duration_seconds{job=~"vast.*"} < scrape_interval.
    """
    log = TestLogger(VAST_TEST_NAMES["tc_p001_scrape_duration"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VAST scrape duration is within scrape interval")
    result = verify_vast_scrape_duration(host, admin_ip)

    details = (
        f"Scrape duration: {result.get('scrape_duration')}s\n"
        f"Scrape interval: {result.get('scrape_interval')}s\n"
        f"Within interval: {result.get('within_interval')}"
    )

    if result["success"]:
        log.passed(
            VAST_LOG_MSGS["scrape_duration_ok"].format(
                duration=result.get("scrape_duration"),
                interval=result.get("scrape_interval")
            ),
            details
        )
    else:
        log.failed(
            VAST_LOG_MSGS["scrape_duration_exceeded"].format(
                duration=result.get("scrape_duration"),
                interval=result.get("scrape_interval")
            ),
            details
        )
        assert False, VAST_ASSERT_MSGS["scrape_duration_exceeded"].format(
            duration=result.get("scrape_duration"),
            interval=result.get("scrape_interval")
        )


@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(67)
def test_tc_p002_vast_metric_coverage(host):
    """
    TC-P002: VAST Metric Family Coverage >= 90% (P0).

    Verifies >= 500 unique VAST metric families are present
    in VictoriaMetrics.
    """
    log = TestLogger(VAST_TEST_NAMES["tc_p002_metric_coverage"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VAST metric family coverage")
    result = verify_vast_metric_coverage(host, admin_ip)

    details_lines = [
        f"Metric families found: {result.get('family_count')}",
        f"Minimum expected: {result.get('min_expected')}",
        f"Meets minimum: {result.get('meets_minimum')}",
    ]
    sample = result.get("sample_families", [])
    if sample:
        details_lines.append(f"\nSample families (first {len(sample)}):")
        for f in sample:
            details_lines.append(f"  - {f}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            VAST_LOG_MSGS["coverage_met"].format(
                percent="100",
                threshold=result.get("threshold_percent"),
                count=result.get("family_count")
            ),
            details
        )
    else:
        log.failed(
            VAST_LOG_MSGS["coverage_not_met"].format(
                percent="N/A",
                threshold=result.get("threshold_percent"),
                count=result.get("family_count")
            ),
            details
        )
        assert False, VAST_ASSERT_MSGS["coverage_not_met"].format(
            percent="N/A",
            threshold=result.get("threshold_percent"),
            count=result.get("family_count"),
            expected=result.get("min_expected"),
        )


# =============================================================================
# 3. SECURITY TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(68)
def test_tc_s001_vast_tls_enforcement(host):
    """
    TC-S001: TLS Enforcement for VAST Communication (P0).

    Verifies:
    - VMServiceScrape scheme is https
    - tlsConfig is present
    - Scrape is active (TLS handshake succeeds)
    """
    log = TestLogger(VAST_TEST_NAMES["tc_s001_tls_enforcement"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying TLS enforcement for VAST communication")
    result = verify_vast_tls_enforcement(host, admin_ip)

    details_lines = []
    for check, passed in result.get("tls_checks", {}).items():
        status = "\u2713" if passed else "\u2717"
        details_lines.append(f"{status} {check}: {passed}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VAST_LOG_MSGS["tls_enforced"], details)
    else:
        log.failed("TLS enforcement verification failed", details)
        assert False, VAST_ASSERT_MSGS["tls_not_configured"]


@pytest.mark.sanity
@pytest.mark.vast_telemetry
@pytest.mark.order(69)
def test_tc_s002_vast_no_plaintext_creds(host):
    """
    TC-S002: No Plaintext Credentials in Deployed Artifacts (P0).

    Verifies:
    - No credential patterns in vmagent pod logs
    - No plaintext credentials in ConfigMaps
    - Credentials stored in K8s Secrets only
    """
    log = TestLogger(VAST_TEST_NAMES["tc_s002_no_plaintext_creds"])
    skip_if_vast_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Checking for plaintext credentials in deployed artifacts")
    result = verify_vast_no_plaintext_credentials(host, admin_ip)

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
        log.passed(VAST_LOG_MSGS["no_creds_in_artifacts"], details)
    else:
        first_finding = result["findings"][0] if result.get("findings") else {}
        log.failed(VAST_LOG_MSGS["creds_found_in_artifacts"], details)
        assert False, VAST_ASSERT_MSGS["credentials_in_artifacts"].format(
            location=first_finding.get("location", "unknown"),
            pattern=first_finding.get("pattern", "unknown"),
        )
