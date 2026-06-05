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
PowerScale Storage Telemetry - Negative / Error Test Cases.

Moved from test_powerscale_telemetry.py.

Test cases (11):
  Negative/Error: TC-E001 through TC-E011
    - TC-E001: CSM Metrics Pod Failure Recovery
    - TC-E002: OTel Collector Pod Failure Recovery
    - TC-E003: vmagent Scrape Failure and Retry
    - TC-E004: TLS / Certificate Misconfiguration Handling
    - TC-E005: External Endpoint Failure Isolation
    - TC-E006: VLAgent Failure Isolation
    - TC-E007: PowerScale Unreachable Handling
    - TC-E008: Worker Node Failure (manual, skipped)
    - TC-E009: Kafka Broker Outage Resilience
    - TC-E010: vminsert Outage Resilience
    - TC-E011: vlinsert Outage Resilience

Note: All tests skip if telemetry_sources.powerscale.metrics_enabled is false.
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
)
from automation_library.telemetry.functions.powerscale_func import (
    get_powerscale_config,
    verify_csm_pod_recovery,
    verify_otel_pod_recovery,
    verify_vmagent_scrape_retry,
    verify_tls_misconfiguration_handling,
    verify_external_failure_isolation,
    verify_vlagent_failure_isolation,
    verify_powerscale_unreachable_handling,
    verify_kafka_broker_outage,
    verify_vminsert_outage,
    verify_vlinsert_outage,
)


# =============================================================================
# NEGATIVE / ERROR TEST CASES (TC-E001 through TC-E011)
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
