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
External Kafka & Victoria Endpoints - Sanity Test Cases.

Tests for verifying external endpoint connectivity and configuration:

  1. External Kafka Endpoints
     - Kafka bootstrap services accessible externally
     - Kafka topics accessible via REST bridge for enabled sources
     Skips if Kafka sink is not enabled (no source targets kafka).

  2. External Victoria Metric Remote-Write Endpoints
     (additional_metric_remote_write_endpoints in telemetry_config.yml)
     Skips if no endpoints are configured.

  3. External Victoria Log Write Endpoints
     (additional_log_write_endpoints in telemetry_config.yml)
     Skips if no endpoints are configured.

  4. External Endpoint Configuration Parsing
     Validates the schema of both metric and log endpoints.
     Always runs.

Test cases (6 total):
  Kafka External (2):
    TC-KEXT001  Kafka bootstrap/bridge external access
    TC-KEXT002  Kafka topics accessible via REST bridge

  Victoria External (3):
    TC-EXT001   External metric remote-write endpoint in vmagent
    TC-EXT002   External log write endpoint in vlagent
    TC-EXT003   External endpoint config parsing & validation

References:
  - telemetry_config.yml: telemetry_sinks.victoria_metrics.additional_metric_remote_write_endpoints
  - telemetry_config.yml: telemetry_sinks.victoria_logs.additional_log_write_endpoints
  - Kafka: Strimzi-managed cluster with REST bridge (bridge-bridge-lb service)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.messages.kafka_msgs import (
    KAFKA_TEST_NAMES,
    KAFKA_LOG_MSGS,
    KAFKA_ASSERT_MSGS,
)
from automation_library.telemetry.messages.powerscale_msgs import (
    POWERSCALE_TEST_NAMES,
    POWERSCALE_LOG_MSGS,
    POWERSCALE_ASSERT_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    get_admin_ip,
    skip_if_kafka_not_enabled,
)
from automation_library.telemetry.functions.kafka_func import (
    verify_kafka_external_access,
    verify_kafka_topic_accessibility,
    get_kafka_bridge_ip,
)
from automation_library.telemetry.functions.powerscale_func import (
    get_additional_metric_endpoints,
    get_additional_log_endpoints,
    verify_external_metric_endpoints,
    verify_external_log_endpoints,
)
from automation_library.telemetry.vars.kafka_vars import KAFKA_BRIDGE_PORT


# =============================================================================
# 1. EXTERNAL KAFKA ENDPOINT TESTS (TC-KEXT001, TC-KEXT002)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(70)
def test_tc_kext001_kafka_external_access(host):
    """
    TC-KEXT001: External Kafka Endpoint Access Verification (P1).

    Verifies:
    - Kafka bootstrap services exist in the telemetry namespace
    - Bootstrap services have external IPs (LoadBalancer) or
      REST bridge is accessible
    - Kafka REST bridge health endpoint responds

    Skips if no source targets kafka.
    """
    log = TestLogger(KAFKA_TEST_NAMES["kafka_ext_access"])
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying Kafka external endpoint access")
    result = verify_kafka_external_access(host, admin_ip)

    details_lines = [
        f"Bootstrap services found: {result.get('has_bootstrap')}",
    ]
    for svc in result.get("bootstrap_services", []):
        ext_ip = svc.get("external_ip", "none")
        details_lines.append(
            f"  - {svc['name']}: type={svc['type']}, "
            f"external_ip={ext_ip}, ports={svc['ports']}"
        )
    details_lines.append(
        f"Has external IP: {result.get('has_external_ip')}"
    )
    details_lines.append(
        f"REST bridge IP: {result.get('bridge_ip') or 'N/A'}"
    )
    details_lines.append(
        f"REST bridge accessible: {result.get('bridge_accessible')}"
    )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            KAFKA_LOG_MSGS["kafka_ext_bootstrap_found"].format(
                count=len(result.get("bootstrap_services", []))
            ),
            details
        )
    else:
        if not result.get("has_bootstrap"):
            log.failed(
                KAFKA_LOG_MSGS["kafka_ext_bootstrap_not_found"], details
            )
            assert False, KAFKA_ASSERT_MSGS["kafka_ext_no_bootstrap"]
        else:
            log.failed(
                KAFKA_LOG_MSGS["kafka_ext_bridge_not_accessible"], details
            )
            assert False, KAFKA_ASSERT_MSGS["kafka_ext_no_access"]


@pytest.mark.sanity
@pytest.mark.order(71)
def test_tc_kext002_kafka_topic_accessibility(host):
    """
    TC-KEXT002: Kafka Topic Accessibility via REST Bridge (P1).

    Verifies:
    - Kafka REST bridge responds to topic listing
    - All expected topics (for enabled sources targeting kafka) exist
    - Topics match sources with kafka in collection_targets
      (e.g., idrac, ldms)

    Skips if no source targets kafka.
    """
    log = TestLogger(KAFKA_TEST_NAMES["kafka_ext_topic_access"])
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying Kafka topics accessible via REST bridge")
    result = verify_kafka_topic_accessibility(host, admin_ip)

    details_lines = [
        f"REST bridge IP: {result.get('bridge_ip') or 'N/A'}",
        f"Topics found: {len(result.get('topics_found', []))}",
        f"Expected topics: {result.get('expected_topics', [])}",
    ]
    for tr in result.get("topic_results", []):
        status = "\u2713" if tr["found"] else "\u2717"
        details_lines.append(f"  {status} {tr['topic']}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            KAFKA_LOG_MSGS["kafka_ext_topics_accessible"].format(
                count=len(result.get("expected_topics", []))
            ),
            details
        )
    else:
        if not result.get("bridge_ip"):
            log.failed(
                KAFKA_LOG_MSGS["kafka_ext_bridge_not_accessible"], details
            )
            assert False, KAFKA_ASSERT_MSGS["kafka_bridge_not_found"]
        else:
            log.failed(
                KAFKA_LOG_MSGS["kafka_ext_topics_missing"], details
            )
            missing = [
                t["topic"] for t in result.get("topic_results", [])
                if not t["found"]
            ]
            assert False, KAFKA_ASSERT_MSGS["kafka_ext_topics_missing"].format(
                missing=missing,
                available=result.get("topics_found", []),
            )


# =============================================================================
# 2. EXTERNAL VICTORIA METRIC ENDPOINT TESTS (TC-EXT001 through TC-EXT003)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(72)
def test_tc_ext001_external_metric_endpoints(host):
    """
    TC-EXT001: External Victoria Metric Remote-Write Endpoints (P1).

    Verifies:
    - additional_metric_remote_write_endpoints parsed from telemetry_config.yml
    - Each configured endpoint URL is present in vmagent remoteWrite config
    - TLS skip-verify flag honoured when set

    Skips if no additional_metric_remote_write_endpoints are configured.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_ext001_metric_endpoints"])
    admin_ip = get_admin_ip(host, log)

    endpoints = get_additional_metric_endpoints(host)
    if not endpoints:
        log.skipped(
            POWERSCALE_LOG_MSGS["ext_metric_endpoints_not_configured"],
            "No additional_metric_remote_write_endpoints in telemetry_config.yml"
        )
        pytest.skip("No external metric endpoints configured")

    log.check(
        POWERSCALE_LOG_MSGS["ext_metric_endpoints_configured"].format(
            count=len(endpoints)
        )
    )
    result = verify_external_metric_endpoints(host, admin_ip)

    details_lines = [f"Endpoints configured: {len(endpoints)}"]
    for ep_result in result.get("endpoint_results", []):
        status = "\u2713" if ep_result["found_in_vmagent"] else "\u2717"
        tls_info = (
            " (tls_insecure_skip_verify=true)"
            if ep_result.get("tls_insecure_skip_verify") else ""
        )
        details_lines.append(
            f"{status} {ep_result['url']}{tls_info}"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["ext_metric_endpoints_verified"], details
        )
    else:
        log.failed("External metric endpoint verification failed", details)
        missing = [
            ep["url"] for ep in result["endpoint_results"]
            if not ep["found_in_vmagent"]
        ]
        assert False, POWERSCALE_ASSERT_MSGS["ext_metric_endpoint_missing"].format(
            url=", ".join(missing)
        )


@pytest.mark.sanity
@pytest.mark.order(73)
def test_tc_ext002_external_log_endpoints(host):
    """
    TC-EXT002: External Victoria Log Write Endpoints (P1).

    Verifies:
    - additional_log_write_endpoints parsed from telemetry_config.yml
    - Each configured endpoint URL is present in vlagent/vector config
    - TLS skip-verify flag honoured when set

    Skips if no additional_log_write_endpoints are configured.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_ext002_log_endpoints"])
    admin_ip = get_admin_ip(host, log)

    endpoints = get_additional_log_endpoints(host)
    if not endpoints:
        log.skipped(
            POWERSCALE_LOG_MSGS["ext_log_endpoints_not_configured"],
            "No additional_log_write_endpoints in telemetry_config.yml"
        )
        pytest.skip("No external log endpoints configured")

    log.check(
        POWERSCALE_LOG_MSGS["ext_log_endpoints_configured"].format(
            count=len(endpoints)
        )
    )
    result = verify_external_log_endpoints(host, admin_ip)

    details_lines = [f"Endpoints configured: {len(endpoints)}"]
    for ep_result in result.get("endpoint_results", []):
        status = "\u2713" if ep_result["found_in_vlagent"] else "\u2717"
        tls_info = (
            " (tls_insecure_skip_verify=true)"
            if ep_result.get("tls_insecure_skip_verify") else ""
        )
        details_lines.append(
            f"{status} {ep_result['url']}{tls_info}"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            POWERSCALE_LOG_MSGS["ext_log_endpoints_verified"], details
        )
    else:
        log.failed("External log endpoint verification failed", details)
        missing = [
            ep["url"] for ep in result["endpoint_results"]
            if not ep["found_in_vlagent"]
        ]
        assert False, POWERSCALE_ASSERT_MSGS["ext_log_endpoint_missing"].format(
            url=", ".join(missing)
        )


@pytest.mark.sanity
@pytest.mark.order(74)
def test_tc_ext003_config_parsing(host):
    """
    TC-EXT003: External Endpoint Configuration Parsing (P1).

    Verifies:
    - telemetry_config.yml can be read and parsed
    - additional_metric_remote_write_endpoints is a list (even if empty)
    - additional_log_write_endpoints is a list (even if empty)
    - Each entry has a 'url' field starting with http:// or https://
    - Optional tls_insecure_skip_verify is a boolean

    This test always runs (does not skip on empty endpoints) to validate
    the configuration schema.
    """
    log = TestLogger(POWERSCALE_TEST_NAMES["tc_ext003_config_parsing"])

    log.check("Parsing external endpoint configuration from telemetry_config.yml")

    metric_endpoints = get_additional_metric_endpoints(host)
    log_endpoints = get_additional_log_endpoints(host)

    details_lines = [
        f"additional_metric_remote_write_endpoints: {len(metric_endpoints)} entries",
        f"additional_log_write_endpoints: {len(log_endpoints)} entries",
    ]

    errors = []

    # Validate metric endpoints
    if not isinstance(metric_endpoints, list):
        errors.append("additional_metric_remote_write_endpoints is not a list")
    for i, ep in enumerate(metric_endpoints):
        if not isinstance(ep, dict):
            errors.append(f"metric endpoint [{i}] is not a dict")
            continue
        url = ep.get("url", "")
        if not url:
            errors.append(f"metric endpoint [{i}] missing 'url' field")
        elif not (url.startswith("http://") or url.startswith("https://")):
            errors.append(
                f"metric endpoint [{i}] url does not start with http(s)://: {url}"
            )
        tls_skip = ep.get("tls_insecure_skip_verify")
        if tls_skip is not None and not isinstance(tls_skip, bool):
            errors.append(
                f"metric endpoint [{i}] tls_insecure_skip_verify is not a boolean"
            )
        details_lines.append(f"  metric [{i}]: url={url}")

    # Validate log endpoints
    if not isinstance(log_endpoints, list):
        errors.append("additional_log_write_endpoints is not a list")
    for i, ep in enumerate(log_endpoints):
        if not isinstance(ep, dict):
            errors.append(f"log endpoint [{i}] is not a dict")
            continue
        url = ep.get("url", "")
        if not url:
            errors.append(f"log endpoint [{i}] missing 'url' field")
        elif not (url.startswith("http://") or url.startswith("https://")):
            errors.append(
                f"log endpoint [{i}] url does not start with http(s)://: {url}"
            )
        tls_skip = ep.get("tls_insecure_skip_verify")
        if tls_skip is not None and not isinstance(tls_skip, bool):
            errors.append(
                f"log endpoint [{i}] tls_insecure_skip_verify is not a boolean"
            )
        details_lines.append(f"  log [{i}]: url={url}")

    if errors:
        for err in errors:
            details_lines.append(f"\u2717 {err}")

    details = "\n".join(details_lines)

    if not errors:
        log.passed(POWERSCALE_LOG_MSGS["ext_config_valid"], details)
    else:
        log.failed("External endpoint configuration validation failed", details)
        assert False, (
            f"Configuration errors found: {'; '.join(errors)}"
        )
