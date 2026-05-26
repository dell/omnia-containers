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
PowerScale Storage Telemetry Test Cases.

This module contains pytest test cases for verifying PowerScale storage
telemetry deployment as defined in TCASES-PS-2026-001 v1.0.0.

Test cases (29 total):
  Functional (12): TC-F001 through TC-F012
  Negative/Error (11): TC-E001 through TC-E011
  Idempotency (1): TC-I001
  Performance (3): TC-P001 through TC-P003
  Security (2): TC-S001, TC-S002

Note: All tests skip if powerscale_telemetry_support is false.
      TC-E008 is marked manual and will skip in automated runs.
"""

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.messages.powerscale_msgs import (
    POWERSCALE_TEST_NAMES,
    POWERSCALE_LOG_MSGS,
    POWERSCALE_ASSERT_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    get_admin_ip,
    skip_if_powerscale_not_enabled,
    is_powerscale_metrics_enabled,
    is_powerscale_logs_enabled,
)
from automation_library.telemetry.functions.powerscale_func import (
    get_powerscale_config,
    get_powerscale_deployment_mode,
    verify_powerscale_deployment,
    verify_powerscale_metrics,
    verify_powerscale_syslog,
    verify_feature_flags,
    verify_dual_destination,
    verify_health_metrics,
    verify_tls_enforcement,
    verify_k8s_service_account_auth,
    verify_label_compliance,
    verify_scrape_interval,
    verify_csi_authorization_mode,
    verify_csm_pod_recovery,
    verify_otel_pod_recovery,
    verify_vmagent_scrape_retry,
    verify_tls_misconfiguration_handling,
    verify_external_failure_isolation,
    verify_vlagent_failure_isolation,
    verify_deployment_mode,
    verify_powerscale_unreachable_handling,
    verify_kafka_broker_outage,
    verify_vminsert_outage,
    verify_vlinsert_outage,
    verify_redeployment_idempotency,
    verify_metric_latency,
    verify_syslog_latency,
    verify_endpoint_availability,
    verify_tls_all_communications,
    verify_no_plaintext_credentials,
)


# =============================================================================
# 1. FUNCTIONAL TEST CASES (TC-F001 through TC-F012)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(30)
def test_tc_f001_deployment_verification(host):
    """
    TC-F001: Omnia-Orchestrated Mode Deployment Verification (P0).

    Verifies:
    - CSM Metrics for PowerScale pod Running with 0 restarts
    - OTel Collector pod Running with 0 restarts
    - CSI Driver for Dell PowerScale installed
    - cert-manager pods Running and certificates Ready
    - OTel Collector Prometheus endpoint responding
    - No manual intervention required
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f001_deployment"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying PowerScale telemetry deployment components")
    result = verify_powerscale_deployment(host, admin_ip)

    # Build details
    details_lines = []
    for comp in result.get("component_results", []):
        status = "✓" if comp["running"] else "✗"
        restart_info = f" (restarts: {comp['restarts']})" if comp["restarts"] > 0 else ""
        details_lines.append(
            f"{status} {comp['component']}: "
            f"{'Running' if comp['running'] else 'NOT Running'}"
            f"{restart_info}"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["all_pods_running"].format(
                component="PowerScale telemetry",
                count=len(result.get("component_results", []))
            ),
            details
        )
    else:
        if result.get("has_restarts"):
            log.failed(POWERSCALE_LOG_MSGS["pod_restart_detected"].format(
                pod="PowerScale telemetry", restarts=result["total_restarts"]
            ), details)
            assert False, POWERSCALE_ASSERT_MSGS["pod_restarts_detected"].format(
                pods=result.get("missing_components", [])
            )
        else:
            log.failed(POWERSCALE_LOG_MSGS["pods_not_running"].format(
                component="PowerScale telemetry"
            ), details)
            assert False, POWERSCALE_ASSERT_MSGS["deployment_failed"].format(
                missing=result.get("missing_components", [])
            )


@pytest.mark.sanity
@pytest.mark.order(31)
def test_tc_f002_metric_collection(host):
    """
    TC-F002: PowerScale Metric Collection and Label Verification (P0).

    Verifies all 6 metric categories:
    - IOPS, throughput, latency, capacity, health, topology
    And required labels: cluster name, node name, protocol
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f002_metric_collection"])
    skip_if_powerscale_not_enabled(host, log)

    if not is_powerscale_metrics_enabled(host):
        log.skipped(POWERSCALE_LOG_MSGS["metrics_not_enabled"],
                     "Test skipped - metrics not enabled")
        pytest.skip("PowerScale metrics not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying PowerScale metric categories and labels")
    result = verify_powerscale_metrics(host, admin_ip)

    # Build details
    details_lines = []
    for cat in result.get("category_results", []):
        status = "✓" if cat["found"] else "✗"
        details_lines.append(
            f"{status} {cat['category']}: {cat['series_count']} series"
        )
    details_lines.append("")
    for lbl in result.get("label_results", []):
        status = "✓" if lbl["present"] else "✗"
        details_lines.append(f"{status} Label '{lbl['label']}': {'present' if lbl['present'] else 'MISSING'}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["all_categories_found"].format(
                count=len(result.get("found_categories", []))
            ),
            details
        )
    else:
        log.failed("PowerScale metric verification failed", details)
        if result.get("missing_categories"):
            assert False, POWERSCALE_ASSERT_MSGS["metric_categories_missing"].format(
                missing=result["missing_categories"],
                found=result["found_categories"]
            )
        else:
            assert False, POWERSCALE_ASSERT_MSGS["labels_missing"].format(
                missing=result.get("missing_labels", [])
            )


@pytest.mark.sanity
@pytest.mark.order(32)
def test_tc_f003_syslog_ingestion(host):
    """
    TC-F003: PowerScale Syslog Ingestion and Log Verification (P0).

    Verifies:
    - VLAgent Running with syslog receiver
    - PowerScale events queryable in VictoriaLogs
    - Correct host/cluster, severity, facility labels
    - End-to-end latency < 1 minute
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f003_syslog_ingestion"])
    skip_if_powerscale_not_enabled(host, log)

    if not is_powerscale_logs_enabled(host):
        log.skipped(POWERSCALE_LOG_MSGS["logs_not_enabled"],
                     "Test skipped - logs not enabled")
        pytest.skip("PowerScale logs not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying PowerScale syslog ingestion into VictoriaLogs")
    result = verify_powerscale_syslog(host, admin_ip)

    details_lines = [
        f"VLAgent Running: {result.get('vlagent_running', False)}",
        f"Events found: {result.get('events_found', False)}",
        f"Event count: {result.get('event_count', 0)}",
    ]
    label_checks = result.get("label_checks", {})
    for label, present in label_checks.items():
        status = "✓" if present else "✗"
        details_lines.append(f"{status} {label}: {'present' if present else 'MISSING'}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["syslog_events_found"].format(
                count=result.get("event_count", 0)
            ),
            details
        )
    else:
        log.failed(POWERSCALE_LOG_MSGS["syslog_events_missing"], details)
        assert False, POWERSCALE_ASSERT_MSGS["syslog_not_ingested"]


@pytest.mark.sanity
@pytest.mark.order(33)
def test_tc_f004_feature_flags(host):
    """
    TC-F004: Independent Feature Flag Operation (P0).

    Verifies:
    - Disabling metrics flag stops metrics without affecting logs
    - Disabling logs flag stops logs without affecting metrics
    - Re-enabling restores both independently
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f004_feature_flags"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying independent feature flag operation")
    result = verify_feature_flags(host, admin_ip)

    details = (
        f"Metrics enabled: {result.get('metrics_enabled')}\n"
        f"Logs enabled: {result.get('logs_enabled')}\n"
        f"Metrics flowing: {result.get('metrics_flowing')}\n"
        f"Logs flowing: {result.get('logs_flowing')}\n"
        f"Metrics correct: {result.get('metrics_correct')}\n"
        f"Logs correct: {result.get('logs_correct')}"
    )

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["flag_toggle_success"].format(
                metrics=result.get("metrics_enabled"),
                logs=result.get("logs_enabled")
            ),
            details
        )
    else:
        log.failed(POWERSCALE_LOG_MSGS["flag_toggle_failed"], details)
        assert False, POWERSCALE_ASSERT_MSGS["flag_toggle_failed"].format(
            expected_metrics=result.get("metrics_enabled"),
            expected_logs=result.get("logs_enabled"),
            actual_metrics=result.get("metrics_flowing"),
            actual_logs=result.get("logs_flowing"),
        )


@pytest.mark.sanity
@pytest.mark.order(34)
def test_tc_f005_deployment_mode(host):
    """
    TC-F005: Deployment Mode - Full Pipeline Verification (P0).

    Verifies that in omnia-orchestrated mode (the only supported mode),
    the full metrics pipeline is operational:
    - CSM Metrics pod running
    - OTel Collector pod running
    - vmagent configured with PowerScale scrape + TLS
    - Scrape target up
    - PowerScale metrics present in VictoriaMetrics
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f005_deployment_mode"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying full metrics pipeline (omnia-orchestrated mode)")
    result = verify_deployment_mode(host, admin_ip)

    details = (
        f"CSM Metrics running: {result.get('csm_running')} "
        f"({result.get('csm_pod_count')} pods)\n"
        f"OTel Collector running: {result.get('otel_running')} "
        f"({result.get('otel_pod_count')} pods)\n"
        f"vmagent has PowerScale config: {result.get('vmagent_has_powerscale')}\n"
        f"vmagent has TLS: {result.get('vmagent_has_tls')}\n"
        f"Scrape up: {result.get('scrape_up')}\n"
        f"Metrics in VictoriaMetrics: {result.get('metrics_present')} "
        f"({result.get('metric_count')} series)"
    )

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["deployment_pipeline_verified"],
            details
        )
    else:
        log.failed("Full pipeline verification failed", details)
        assert False, POWERSCALE_ASSERT_MSGS["deployment_pipeline_broken"].format(
            csm_running=result.get('csm_running'),
            otel_running=result.get('otel_running'),
            scrape_up=result.get('scrape_up'),
            metrics_present=result.get('metrics_present'),
        )


@pytest.mark.sanity
@pytest.mark.order(35)
def test_tc_f006_dual_destination(host):
    """
    TC-F006: Dual-Destination Delivery (P1).

    Verifies:
    - Metrics flowing to internal VictoriaMetrics
    - Metrics flowing to external endpoint
    - Internal path isolated from external failures
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f006_dual_destination"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    ps_config = get_powerscale_config(host)
    external_endpoint = ps_config.get("external_omni_endpoint", "")
    if not external_endpoint:
        log.skipped(
            "external_omni_endpoint not configured in telemetry_config.yml",
            "Test skipped - dual destination not configured"
        )
        pytest.skip("external_omni_endpoint not configured")

    log.check("Verifying dual-destination delivery")
    result = verify_dual_destination(host, admin_ip)

    details = (
        f"Internal receiving: {result.get('internal_receiving')}\n"
        f"Internal metric count: {result.get('internal_metric_count')}\n"
        f"External configured: {result.get('external_configured')}\n"
        f"External endpoint: {result.get('external_endpoint')}"
    )

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["dual_dest_both_receiving"], details)
    else:
        log.failed("Dual-destination delivery verification failed", details)
        assert False, POWERSCALE_ASSERT_MSGS["dual_dest_missing"].format(
            destination="internal" if not result.get("internal_receiving") else "external"
        )


@pytest.mark.sanity
@pytest.mark.order(36)
def test_tc_f007_health_metrics(host):
    """
    TC-F007: Operational Health Metrics (P1).

    Verifies:
    - Scrape success rate metric exposed
    - Scrape error count metric exposed
    - Ingest latency metric exposed
    - Scrape errors increment on failure
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f007_health_metrics"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying operational health metrics")
    result = verify_health_metrics(host, admin_ip)

    details_lines = []
    for mr in result.get("metric_results", []):
        status = "✓" if mr["found"] else "✗"
        value_str = f" = {mr['value']}" if mr["value"] else ""
        details_lines.append(f"{status} {mr['metric']}{value_str}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["health_metrics_exposed"], details)
    else:
        log.failed("Operational health metrics incomplete", details)
        assert False, f"Missing health metrics: {result.get('missing_metrics', [])}"


@pytest.mark.sanity
@pytest.mark.order(37)
def test_tc_f008_tls_enforcement(host):
    """
    TC-F008: TLS Enforcement on Metric Scraping Path (P0).

    Verifies:
    - vmagent config has scheme: https, tls_config
    - Scrape succeeding over TLS
    - Plaintext HTTP rejected
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f008_tls_enforcement"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying TLS enforcement on metric scraping path")
    result = verify_tls_enforcement(host, admin_ip)

    details = (
        f"TLS configured: {result.get('tls_configured')}\n"
        f"Scrape up: {result.get('scrape_up')}"
    )

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["tls_configured"], details)
    else:
        log.failed(POWERSCALE_LOG_MSGS["tls_not_configured"], details)
        assert False, POWERSCALE_ASSERT_MSGS["tls_not_configured"]


@pytest.mark.sanity
@pytest.mark.order(38)
def test_tc_f009_k8s_auth(host):
    """
    TC-F009: Kubernetes Service-Account Authentication (P0).

    Verifies:
    - K8s service-account authentication configured
    - Scrape succeeds with valid service account
    - mTLS not required
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f009_k8s_auth"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying K8s service-account authentication")
    result = verify_k8s_service_account_auth(host, admin_ip)

    details = (
        f"SA configured: {result.get('sa_configured')}\n"
        f"Scrape up: {result.get('scrape_up')}\n"
        f"mTLS not required: {result.get('mtls_not_required')}"
    )

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["sa_auth_configured"], details)
    else:
        log.failed(POWERSCALE_LOG_MSGS["sa_auth_not_configured"], details)
        assert False, POWERSCALE_ASSERT_MSGS["sa_auth_not_configured"]


@pytest.mark.sanity
@pytest.mark.order(39)
def test_tc_f010_label_compliance(host):
    """
    TC-F010: Label Convention Compliance (P1).

    Verifies:
    - All PowerScale metrics carry cluster name, node name labels
    - Labels follow Omnia naming conventions
    - PowerScale metrics distinguishable from other sources
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f010_label_compliance"])
    skip_if_powerscale_not_enabled(host, log)

    if not is_powerscale_metrics_enabled(host):
        log.skipped(POWERSCALE_LOG_MSGS["metrics_not_enabled"],
                     "Test skipped - metrics not enabled")
        pytest.skip("PowerScale metrics not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying label convention compliance")
    result = verify_label_compliance(host, admin_ip)

    if result.get("error"):
        log.failed(result["error"], "")
        assert False, result["error"]

    details_lines = [f"Total series: {result.get('total_series', 0)}"]
    for label, check in result.get("label_checks", {}).items():
        status = "✓" if check["all_present"] else "✗"
        details_lines.append(
            f"{status} Label '{label}': {check['present_count']}/{check['total_count']}"
        )
    details_lines.append(f"Distinguishable: {result.get('distinguishable', False)}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["labels_compliant"], details)
    else:
        log.failed("Label compliance check failed", details)
        missing = [l for l, c in result.get("label_checks", {}).items() if not c["all_present"]]
        assert False, POWERSCALE_ASSERT_MSGS["labels_missing"].format(missing=missing)


@pytest.mark.sanity
@pytest.mark.order(40)
def test_tc_f011_scrape_interval(host):
    """
    TC-F011: Scrape Interval Configurability (P2).

    Verifies:
    - 30s and 60s intervals correctly applied
    - Below-range (15s) rejected or clamped
    - Above-range (90s) rejected or clamped
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f011_scrape_interval"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying scrape interval configurability")
    result = verify_scrape_interval(host, admin_ip)

    details = (
        f"Configured: {result.get('configured_interval')}\n"
        f"Interval (s): {result.get('interval_seconds')}\n"
        f"Effective: {result.get('effective_interval')}s\n"
        f"Within range [{result.get('min_allowed')}s-{result.get('max_allowed')}s]: "
        f"{result.get('within_range')}\n"
        f"Clamped: {result.get('clamped')}"
    )

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["scrape_interval_applied"].format(
                interval=result.get("configured_interval")
            ),
            details
        )
    else:
        log.failed("Scrape interval verification failed", details)
        assert False, POWERSCALE_ASSERT_MSGS["scrape_interval_not_applied"].format(
            expected=result.get("configured_interval"),
            actual=f"{result.get('effective_interval')}s"
        )


@pytest.mark.sanity
@pytest.mark.order(41)
def test_tc_f012_csi_auth_mode(host):
    """
    TC-F012: CSI Driver Authorization Enabled Mode (P0).

    Verifies:
    - CSI Driver authorization mode enabled
    - CSM Metrics pod Running
    - Metrics flowing with no authorization errors
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_f012_csi_auth_mode"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying CSI Driver authorization enabled mode")
    result = verify_csi_authorization_mode(host, admin_ip)

    details = (
        f"Auth enabled: {result.get('auth_enabled')}\n"
        f"CSM Running: {result.get('csm_running')}\n"
        f"Metrics flowing: {result.get('metrics_flowing')}\n"
        f"No auth errors: {result.get('no_auth_errors')}"
    )

    if result["success"]:
        log.passed("CSI Driver authorization mode operational", details)
    else:
        log.failed("CSI Driver authorization mode verification failed", details)
        if not result.get("csm_running"):
            assert False, POWERSCALE_ASSERT_MSGS["csm_metrics_not_running"].format(
                status="Not Running"
            )
        else:
            assert False, "CSI authorization mode: metrics not flowing or auth errors detected"


# =============================================================================
# 2. NEGATIVE / ERROR TEST CASES (TC-E001 through TC-E008)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(42)
def test_tc_e001_csm_pod_recovery(host):
    """
    TC-E001: CSM Metrics Pod Failure Recovery (P0).

    Steps:
    1. Confirm baseline metrics
    2. Kill CSM Metrics pod
    3. Verify K8s auto-restarts pod
    4. Verify metrics resume after restart
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e001_csm_pod_recovery"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Testing CSM Metrics pod failure recovery")
    result = verify_csm_pod_recovery(host, admin_ip)

    if result.get("error"):
        log.failed(result["error"], "")
        assert False, result["error"]

    details = (
        f"Pod restarted: {result.get('pod_restarted')}\n"
        f"New pod: {result.get('new_pod_name')}\n"
        f"Metrics resumed: {result.get('metrics_resumed')}\n"
        f"Recovery time: {result.get('recovery_time')}s"
    )

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["pod_auto_restarted"].format(
                component="CSM Metrics"
            ),
            details
        )
    else:
        log.failed("CSM Metrics pod recovery failed", details)
        if not result.get("pod_restarted"):
            assert False, POWERSCALE_ASSERT_MSGS["pod_not_auto_restarted"].format(
                component="CSM Metrics"
            )
        else:
            assert False, POWERSCALE_ASSERT_MSGS["metrics_not_resumed"].format(
                component="CSM Metrics", last_ts="N/A"
            )


@pytest.mark.sanity
@pytest.mark.order(43)
def test_tc_e002_otel_pod_recovery(host):
    """
    TC-E002: OTel Collector Pod Failure Recovery (P0).

    Steps:
    1. Kill OTel Collector pod
    2. Verify CSM Metrics continues running
    3. Verify K8s auto-restarts OTel pod
    4. Verify metrics resume
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e002_otel_pod_recovery"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Testing OTel Collector pod failure recovery")
    result = verify_otel_pod_recovery(host, admin_ip)

    if result.get("error"):
        log.failed(result["error"], "")
        assert False, result["error"]

    details = (
        f"Pod restarted: {result.get('pod_restarted')}\n"
        f"CSM unaffected: {result.get('csm_unaffected')}\n"
        f"Metrics resumed: {result.get('metrics_resumed')}\n"
        f"Recovery time: {result.get('recovery_time')}s"
    )

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["pod_auto_restarted"].format(
                component="OTel Collector"
            ),
            details
        )
    else:
        log.failed("OTel Collector pod recovery failed", details)
        assert False, POWERSCALE_ASSERT_MSGS["pod_not_auto_restarted"].format(
            component="OTel Collector"
        )


@pytest.mark.sanity
@pytest.mark.order(44)
def test_tc_e003_vmagent_scrape_retry(host):
    """
    TC-E003: vmagent Scrape Failure and Retry (P1).

    Verifies vmagent retries scraping at next interval after failure
    and recovers when endpoint becomes reachable again.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e003_vmagent_scrape_retry"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying vmagent scrape retry behavior")
    result = verify_vmagent_scrape_retry(host, admin_ip)

    details = (
        f"Scrape up: {result.get('scrape_up')}\n"
        f"Message: {result.get('message')}"
    )

    if result["success"]:
        log.passed("vmagent scrape is active and retry-capable", details)
    else:
        log.failed("vmagent scrape not active", details)
        assert False, "vmagent scrape is not active - cannot verify retry behavior"


@pytest.mark.sanity
@pytest.mark.order(45)
def test_tc_e004_tls_misconfig(host):
    """
    TC-E004: TLS / Certificate Misconfiguration Handling (P0).

    Verifies:
    - TLS scrape currently active
    - Health metrics reflect TLS status
    - System would detect invalid certificates
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e004_tls_misconfig"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying TLS misconfiguration handling readiness")
    result = verify_tls_misconfiguration_handling(host, admin_ip)

    details_lines = [
        f"TLS scrape active: {result.get('tls_scrape_active')}",
        f"Health metrics present: {result.get('health_metrics_present')}",
    ]
    for hd in result.get("health_details", []):
        status = "✓" if hd["found"] else "✗"
        details_lines.append(f"  {status} {hd['metric']}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("TLS scrape active with health metrics for error detection", details)
    else:
        log.failed("TLS misconfiguration handling verification failed", details)
        assert False, "TLS scrape not active or health metrics missing"


@pytest.mark.sanity
@pytest.mark.order(46)
def test_tc_e005_external_failure(host):
    """
    TC-E005: External Endpoint Failure Isolation (P1).

    Verifies internal VictoriaMetrics ingestion continues when
    external endpoint is down.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e005_external_failure"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    ps_config = get_powerscale_config(host)
    external_endpoint = ps_config.get("external_omni_endpoint", "")
    if not external_endpoint:
        log.skipped(
            "external_omni_endpoint not configured",
            "Test skipped - dual destination not configured"
        )
        pytest.skip("external_omni_endpoint not configured")

    log.check("Verifying external endpoint failure isolation")
    result = verify_external_failure_isolation(host, admin_ip)

    details = (
        f"Internal receiving: {result.get('internal_receiving')}\n"
        f"External configured: {result.get('external_configured')}"
    )

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["dual_dest_internal_unaffected"], details)
    else:
        log.failed("External failure isolation check failed", details)
        assert False, POWERSCALE_ASSERT_MSGS["internal_affected_by_external"]


@pytest.mark.sanity
@pytest.mark.order(47)
def test_tc_e006_vlagent_failure(host):
    """
    TC-E006: VLAgent Failure Isolation (P1).

    Verifies metrics collection path is completely unaffected
    by VLAgent failure.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e006_vlagent_failure"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VLAgent failure isolation")
    result = verify_vlagent_failure_isolation(host, admin_ip)

    details = (
        f"Metrics flowing: {result.get('metrics_flowing')}\n"
        f"VLAgent running: {result.get('vlagent_running')}"
    )

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["metrics_unaffected_by_vlagent"], details)
    else:
        log.failed("VLAgent failure isolation check failed", details)
        assert False, "Metrics path affected - should be isolated from VLAgent"


@pytest.mark.sanity
@pytest.mark.order(48)
def test_tc_e007_powerscale_unreachable(host):
    """
    TC-E007: PowerScale Unreachable Handling (P0).

    Verifies:
    - CSM Metrics pod continues running (does not crash)
    - Other telemetry sources (iDRAC, LDMS) completely unaffected
    - CSM Metrics reconnects when PowerScale becomes reachable
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e007_powerscale_unreachable"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying PowerScale unreachable handling")
    result = verify_powerscale_unreachable_handling(host, admin_ip)

    details = (
        f"CSM pod running: {result.get('csm_pod_running')}\n"
        f"Other sources OK: {result.get('other_sources_ok')}\n"
        f"iDRAC deployed: {result.get('idrac_deployed')}"
    )

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["other_sources_unaffected"], details)
    else:
        log.failed("PowerScale unreachable handling check failed", details)
        if not result.get("other_sources_ok"):
            assert False, POWERSCALE_ASSERT_MSGS["other_sources_affected"].format(
                affected="iDRAC/LDMS"
            )
        else:
            assert False, POWERSCALE_ASSERT_MSGS["csm_metrics_not_running"].format(
                status="Not Running"
            )


@pytest.mark.sanity
@pytest.mark.order(49)
def test_tc_e008_worker_node_failure(host):
    """
    TC-E008: Worker Node Failure - Pod Rescheduling (P1).

    This test is marked as MANUAL in the test spec.
    Skips in automated runs.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e008_worker_node_failure"])
    log.skipped(
        "TC-E008 is a manual test case requiring physical node failure simulation",
        "Test skipped - manual test case (requires node cordon/drain or shutdown)"
    )
    pytest.skip("TC-E008 is a manual test case")


@pytest.mark.sanity
@pytest.mark.order(60)
def test_tc_e009_kafka_broker_outage(host):
    """
    TC-E009: Kafka Broker Outage Resilience (P1).

    Verifies:
    - PowerScale metrics path is completely unaffected when a Kafka broker
      pod is deleted (Kafka is used for iDRAC/LDMS, not PowerScale)
    - Strimzi operator auto-restarts the Kafka broker
    - Kafka cluster returns to healthy state after recovery
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e009_kafka_outage"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Testing Kafka broker outage resilience")
    result = verify_kafka_broker_outage(host, admin_ip)

    if result.get("error"):
        log.failed(result["error"], "")
        assert False, result["error"]

    details = (
        f"Deleted broker: {result.get('deleted_broker')}\n"
        f"Metrics unaffected during outage: {result.get('metrics_unaffected')}\n"
        f"Broker recovered (Running): {result.get('broker_recovered')}\n"
        f"Broker phase: {result.get('broker_phase')}\n"
        f"Recovery time: {result.get('recovery_time')}s\n"
        f"Series: baseline={result.get('baseline_series')}, "
        f"during={result.get('during_outage_series')}, "
        f"after={result.get('after_recovery_series')}"
    )

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["kafka_outage_metrics_unaffected"],
            details
        )
    else:
        log.failed("Kafka broker outage resilience check failed", details)
        assert False, POWERSCALE_ASSERT_MSGS["kafka_outage_affected_metrics"]


@pytest.mark.sanity
@pytest.mark.order(61)
def test_tc_e010_vminsert_outage(host):
    """
    TC-E010: vminsert Outage Resilience (P0).

    Verifies:
    - vmagent continues scraping and does not crash when vminsert is down
    - VM operator auto-restarts the vminsert pod
    - Metrics resume flowing into VictoriaMetrics after recovery
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e010_vminsert_outage"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Testing vminsert outage resilience")
    result = verify_vminsert_outage(host, admin_ip)

    if result.get("error"):
        log.failed(result["error"], "")
        assert False, result["error"]

    details = (
        f"Deleted pod: {result.get('deleted_pod')}\n"
        f"vmagent healthy during outage: {result.get('vmagent_healthy')}\n"
        f"vminsert recovered: {result.get('vminsert_recovered')}\n"
        f"Metrics resumed: {result.get('metrics_resumed')}\n"
        f"Recovery time: {result.get('recovery_time')}s"
    )

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["vminsert_recovered_metrics_resumed"],
            details
        )
    else:
        log.failed("vminsert outage resilience check failed", details)
        if not result.get("vmagent_healthy"):
            assert False, POWERSCALE_ASSERT_MSGS["vminsert_outage_crashed_vmagent"]
        elif not result.get("vminsert_recovered"):
            assert False, POWERSCALE_ASSERT_MSGS["vminsert_not_recovered"]
        else:
            assert False, POWERSCALE_ASSERT_MSGS["metrics_not_resumed"].format(
                component="vminsert", last_ts="N/A"
            )


@pytest.mark.sanity
@pytest.mark.order(62)
def test_tc_e011_vlinsert_outage(host):
    """
    TC-E011: vlinsert Outage Resilience (P1).

    Verifies:
    - Metrics path is completely isolated from vlinsert failure
      (vlinsert handles logs only)
    - VM operator auto-restarts the vlinsert pod
    - Syslog ingestion resumes in VictoriaLogs after recovery
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_e011_vlinsert_outage"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Testing vlinsert outage resilience")
    result = verify_vlinsert_outage(host, admin_ip)

    if result.get("error"):
        log.failed(result["error"], "")
        assert False, result["error"]

    details = (
        f"Deleted pod: {result.get('deleted_pod')}\n"
        f"Metrics unaffected: {result.get('metrics_unaffected')}\n"
        f"vlinsert recovered: {result.get('vlinsert_recovered')}\n"
        f"Logs resumed: {result.get('logs_resumed')}\n"
        f"Recovery time: {result.get('recovery_time')}s"
    )

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["vlinsert_recovered_logs_resumed"],
            details
        )
    else:
        log.failed("vlinsert outage resilience check failed", details)
        if not result.get("metrics_unaffected"):
            assert False, POWERSCALE_ASSERT_MSGS["vlinsert_outage_affected_metrics"]
        elif not result.get("vlinsert_recovered"):
            assert False, POWERSCALE_ASSERT_MSGS["vlinsert_not_recovered"]
        else:
            assert False, "Syslog ingestion did not resume after vlinsert recovery"


# =============================================================================
# 3. IDEMPOTENCY TEST CASES (TC-I001)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(50)
def test_tc_i001_redeployment(host):
    """
    TC-I001: PowerScale Telemetry Redeployment Idempotency (P1).

    Verifies:
    - All pods return to Running after redeployment
    - Scrape resumes at configured interval
    - No duplicate metrics
    - Syslog ingestion resumes
    - Configuration preserved
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_i001_redeployment"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying redeployment idempotency")
    result = verify_redeployment_idempotency(host, admin_ip)

    details_lines = [
        f"Pods running: {result.get('pods_running')}",
        f"Scrape resumed: {result.get('scrape_resumed')}",
        f"Data present: {result.get('data_present')}",
    ]
    for comp in result.get("component_results", []):
        status = "✓" if comp["running"] else "✗"
        details_lines.append(f"  {status} {comp['component']}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["redeployment_success"], details)
    else:
        log.failed(POWERSCALE_LOG_MSGS["redeployment_failed"], details)
        assert False, "Redeployment idempotency check failed"


# =============================================================================
# 4. PERFORMANCE TEST CASES (TC-P001 through TC-P003)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(51)
def test_tc_p001_metric_latency(host):
    """
    TC-P001: Metric Ingestion Latency Within One Scrape Interval (P1).

    Verifies metrics appear in VictoriaMetrics within one scrape interval
    of emission.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_p001_metric_latency"])
    skip_if_powerscale_not_enabled(host, log)

    if not is_powerscale_metrics_enabled(host):
        log.skipped(POWERSCALE_LOG_MSGS["metrics_not_enabled"],
                     "Test skipped - metrics not enabled")
        pytest.skip("PowerScale metrics not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying metric ingestion latency")
    result = verify_metric_latency(host, admin_ip)

    details_lines = [f"Scrape interval: {result.get('interval_seconds')}s"]
    for m in result.get("measurements", []):
        status = "✓" if m["within_interval"] else "✗"
        details_lines.append(
            f"{status} {m['metric']}: latency={m['latency']}s"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["latency_within_interval"].format(
                latency="all",
                interval=result.get("interval_seconds")
            ),
            details
        )
    else:
        log.failed("Metric ingestion latency exceeded", details)
        assert False, "Metric latency exceeded scrape interval"


@pytest.mark.sanity
@pytest.mark.order(52)
def test_tc_p002_syslog_latency(host):
    """
    TC-P002: Syslog Event Ingestion Latency < 1 Minute (P1).

    Verifies all syslog event types arrive in VictoriaLogs within 1 minute.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_p002_syslog_latency"])
    skip_if_powerscale_not_enabled(host, log)

    if not is_powerscale_logs_enabled(host):
        log.skipped(POWERSCALE_LOG_MSGS["logs_not_enabled"],
                     "Test skipped - logs not enabled")
        pytest.skip("PowerScale logs not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying syslog event ingestion latency")
    result = verify_syslog_latency(host, admin_ip)

    details = (
        f"VLAgent running: {result.get('vlagent_running')}\n"
        f"Syslog available: {result.get('syslog_available')}\n"
        f"Event count: {result.get('event_count')}"
    )

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["syslog_latency_ok"], details)
    else:
        log.failed("Syslog latency check failed", details)
        assert False, POWERSCALE_ASSERT_MSGS["syslog_latency_exceeded"].format(
            latency="N/A"
        )


@pytest.mark.sanity
@pytest.mark.order(53)
def test_tc_p003_endpoint_availability(host):
    """
    TC-P003: OTel Collector Endpoint Availability >= 98% (P1).

    Note: Full 24-hour test requires @long-running environment.
    This test verifies current availability as a spot check.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_p003_endpoint_availability"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying OTel Collector endpoint availability (spot check)")
    result = verify_endpoint_availability(host, admin_ip)

    details = (
        f"OTel running: {result.get('otel_running')}\n"
        f"Endpoint responsive: {result.get('endpoint_responsive')}\n"
        f"Note: {result.get('note')}"
    )

    if result["success"]:
        log.passed("OTel Collector endpoint available (spot check passed)", details)
    else:
        log.failed("OTel Collector endpoint not available", details)
        assert False, POWERSCALE_ASSERT_MSGS["availability_below_threshold"].format(
            availability="N/A"
        )


# =============================================================================
# 5. SECURITY TEST CASES (TC-S001, TC-S002)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(54)
def test_tc_s001_tls_all_comms(host):
    """
    TC-S001: TLS Enforcement for All Off-Cluster Communications (P0).

    Verifies:
    - All metric paths use TLS (vmagent→OTel, vmagent→vminsert, vmagent→external)
    - No plaintext metric data in network traffic
    - Plaintext connections rejected
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_s001_tls_all_comms"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying TLS enforcement for all off-cluster communications")
    result = verify_tls_all_communications(host, admin_ip)

    details_lines = []
    for check, passed in result.get("tls_checks", {}).items():
        status = "✓" if passed else "✗"
        details_lines.append(f"{status} {check}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["tls_traffic_encrypted"], details)
    else:
        log.failed("TLS enforcement incomplete", details)
        assert False, POWERSCALE_ASSERT_MSGS["tls_not_configured"]


@pytest.mark.sanity
@pytest.mark.order(55)
def test_tc_s002_no_plaintext_creds(host):
    """
    TC-S002: No Plaintext Credentials in Deployed Artifacts (P0).

    Verifies:
    - No credential patterns in pod logs
    - No plaintext credentials in manifests or ConfigMaps
    - No credentials in environment variables
    - PowerScale API credentials stored in K8s Secrets
    - TLS private keys stored in K8s Secrets only
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_s002_no_plaintext_creds"])
    skip_if_powerscale_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Checking for plaintext credentials in deployed artifacts")
    result = verify_no_plaintext_credentials(host, admin_ip)

    details_lines = [
        f"Findings: {len(result.get('findings', []))}",
        f"Credentials in Secrets: {result.get('credentials_in_secrets')}",
    ]
    for finding in result.get("findings", []):
        details_lines.append(f"  ✗ {finding['location']}: pattern='{finding['pattern']}'")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(POWERSCALE_LOG_MSGS["no_creds_in_logs"], details)
    else:
        first_finding = result["findings"][0] if result.get("findings") else {}
        log.failed("Plaintext credentials found in artifacts", details)
        assert False, POWERSCALE_ASSERT_MSGS["credentials_in_artifacts"].format(
            location=first_finding.get("location", "unknown"),
            pattern=first_finding.get("pattern", "unknown"),
        )
