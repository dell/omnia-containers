# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Telemetry Kafka Test Cases.

This module contains pytest test cases for verifying Kafka configuration
and connectivity in the telemetry namespace.

Test cases:
1. Verify LDMS pods running (if ldms enabled)
2. Verify LDMS services ports match telemetry_config.yml (if ldms enabled)
3. Verify Kafka mTLS connection
4. Verify Kafka topics configuration
5. Verify Kafka configurations match telemetry_config.yml (inside pod)
6. Verify data flowing to idrac topic
7. Verify data flowing to ldms topic (if ldms enabled)

Note: Kafka tests skip if kafka is not in idrac_telemetry_collection_type.
      LDMS tests skip if ldms is not in software_config.json.
"""

import pytest

from automation_library.core import (
    TestLogger,
    get_node_admin_ip,
)
from automation_library.telemetry.vars import (
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
)
from automation_library.telemetry.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.telemetry.functions.kafka_func import (
    is_kafka_enabled,
    is_ldms_enabled,
    verify_ldms_pods_running,
    verify_ldms_services_ports,
    verify_kafka_mtls_connection,
    verify_kafka_topics,
    verify_kafka_config_match,
    verify_idrac_topic_data,
    verify_ldms_topic_data,
)


# =============================================================================
# LDMS TEST CASES (run first, before Kafka tests)
# =============================================================================

def test_ldms_pods_running(host):
    """
    Test Case 1: Verify LDMS pods are running.

    If LDMS is enabled in software_config.json, verifies:
    - nersc-ldms-aggr pod is running
    - nersc-ldms-store pod is running
    """
    log = TestLogger(TEST_NAMES.get("ldms_pods_running", "Verify LDMS pods running"))

    # Skip if LDMS not enabled
    if not is_ldms_enabled(host):
        pytest.skip("LDMS is not enabled in software_config.json")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify LDMS pods
    log.check("Verifying LDMS pods are running in telemetry namespace")
    result = verify_ldms_pods_running(host, admin_ip)

    if result.get("skipped"):
        pytest.skip(result.get("reason", "LDMS not enabled"))

    # Show pod results
    for pod_result in result.get("pod_results", []):
        pod = pod_result["pod"]
        phase = pod_result["phase"]
        running = pod_result["running"]
        status = "✓" if running else "✗"
        log.check(f"  {status} Pod '{pod}': {phase}")

    if result["success"]:
        log.passed("All LDMS pods are running", "nersc-ldms-aggr and nersc-ldms-store")
    else:
        errors = result.get("errors", [])
        log.failed("LDMS pods verification failed", "; ".join(errors))
        assert False, f"LDMS pods not running: {'; '.join(errors)}"


def test_ldms_services_ports(host):
    """
    Test Case 2: Verify LDMS services ports match telemetry_config.yml.

    If LDMS is enabled, verifies:
    - ldms-aggr service port matches ldms_agg_port in telemetry_config.yml
    - ldms-store service port matches ldms_store_port in telemetry_config.yml
    """
    log = TestLogger(TEST_NAMES.get("ldms_services_ports", "Verify LDMS services ports"))

    # Skip if LDMS not enabled
    if not is_ldms_enabled(host):
        pytest.skip("LDMS is not enabled in software_config.json")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify LDMS services ports
    log.check("Verifying LDMS services ports match telemetry_config.yml")
    result = verify_ldms_services_ports(host, admin_ip)

    if result.get("skipped"):
        pytest.skip(result.get("reason", "LDMS not enabled"))

    if result.get("error"):
        log.failed("Failed to get LDMS services", result["error"])
        assert False, result["error"]

    # Show expected config
    expected = result.get("expected_config", {})
    log.check(f"  Expected ldms_agg_port: {expected.get('ldms_agg_port')}")
    log.check(f"  Expected ldms_store_port: {expected.get('ldms_store_port')}")

    # Show service results
    for svc_result in result.get("service_results", []):
        svc = svc_result["service"]
        expected_port = svc_result["expected_port"]
        actual_port = svc_result["actual_port"]
        match = svc_result["match"]
        status = "✓" if match else "✗"
        log.check(f"  {status} Service '{svc}': expected={expected_port}, actual={actual_port}")

    if result["success"]:
        log.passed("All LDMS services ports match", "Ports configured correctly")
    else:
        errors = result.get("errors", [])
        log.failed("LDMS services port mismatch", "; ".join(errors))
        assert False, f"LDMS services port mismatch: {'; '.join(errors)}"


# =============================================================================
# KAFKA TEST CASES
# =============================================================================

def test_kafka_mtls_connection(host):
    """
    Test Case 3: Verify Kafka mTLS connection.

    Runs mTLS test inside a temporary pod with mounted certificates:
    1. Create truststore from cluster CA certificate
    2. Create keystore from kafkapump client certificate
    3. Create Kafka client properties for mTLS
    4. Verify mTLS connection by listing topics
    """
    log = TestLogger(TEST_NAMES["kafka_mtls_connection"])

    # Skip if Kafka not enabled
    if not is_kafka_enabled(host):
        pytest.skip("Kafka is not enabled in idrac_telemetry_collection_type")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify mTLS connection
    log.check("Running Kafka mTLS connection test inside pod")
    result = verify_kafka_mtls_connection(host, admin_ip)

    # Show step results (only mTLS steps, not topics)
    log.check(f"  Step 1 - Truststore created: {'✓' if result.get('truststore_created') else '✗'}")
    log.check(f"  Step 2 - Keystore created: {'✓' if result.get('keystore_created') else '✗'}")
    log.check(f"  Step 3 - Client properties created: {'✓' if result.get('client_properties_created') else '✗'}")
    log.check(f"  Step 4 - mTLS connection success: {'✓' if result.get('mtls_connection_success') else '✗'}")

    if result["success"]:
        log.passed(LOG_MSGS["kafka_mtls_success"], "mTLS connection established successfully")
    else:
        log.failed(LOG_MSGS["kafka_mtls_failed"], result.get("error", ""))
        assert False, ASSERT_MSGS["kafka_mtls_failed"].format(
            cluster_ready=result.get("mtls_connection_success", False),
            kafkapump_secret=result.get("keystore_created", False),
            cluster_ca=result.get("truststore_created", False),
            topics=result.get("topics_listed", [])
        )


def test_kafka_topics(host):
    """
    Test Case 2: Verify Kafka topics configuration.

    Verifies:
    - idrac topic exists (required when kafka enabled)
    - ldms topic exists ONLY if ldms is in software_config.json
    - Fails if ldms topic exists but ldms not enabled
    - Fails if ldms topic missing but ldms is enabled
    """
    log = TestLogger(TEST_NAMES["kafka_topics_verification"])

    # Skip if Kafka not enabled
    if not is_kafka_enabled(host):
        pytest.skip("Kafka is not enabled in idrac_telemetry_collection_type")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify topics
    log.check("Verifying Kafka topics configuration")
    result = verify_kafka_topics(host, admin_ip)

    ldms_enabled = result.get("ldms_enabled", False)
    log.check(f"  LDMS enabled in software_config.json: {ldms_enabled}")

    # List all topics found
    all_topics = result.get("all_topics", [])
    log.check(f"  Topics found: {all_topics}")

    # Show topic verification results
    for topic_result in result.get("topic_results", []):
        topic = topic_result["topic"]
        exists = topic_result["exists"]

        if topic == "idrac":
            if exists:
                log.check("  ✓ Topic 'idrac': exists (required)")
            else:
                log.check("  ✗ Topic 'idrac': MISSING (required)")
        elif topic == "ldms":
            if ldms_enabled and exists:
                log.check("  ✓ Topic 'ldms': exists (ldms enabled in software_config.json)")
            elif ldms_enabled and not exists:
                log.check("  ✗ Topic 'ldms': MISSING (ldms enabled but topic not found)")
            elif not ldms_enabled and exists:
                log.check("  ✗ Topic 'ldms': EXISTS but ldms NOT enabled in software_config.json")
            else:
                log.check("  ✓ Topic 'ldms': correctly not created (ldms not enabled)")

    if result["success"]:
        log.passed("All Kafka topics verified", f"Topics: {all_topics}")
    else:
        errors = result.get("errors", [])
        log.failed("Kafka topic verification failed", "; ".join(errors))
        first_error = errors[0] if errors else "Unknown error"
        assert False, first_error


def test_kafka_config_match(host):
    """
    Test Case 3: Verify Kafka configurations match telemetry_config.yml.

    Checks inside the Kafka broker pod to verify actual config matches expected.
    Verifies:
    - log_retention_hours matches
    - log_retention_bytes matches
    - log_segment_bytes matches
    """
    log = TestLogger(TEST_NAMES["kafka_config_match"])

    # Skip if Kafka not enabled
    if not is_kafka_enabled(host):
        pytest.skip("Kafka is not enabled in idrac_telemetry_collection_type")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify config match (checks inside Kafka pod)
    log.check("Checking Kafka config inside broker pod vs telemetry_config.yml")
    result = verify_kafka_config_match(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to get Kafka config", result["error"])
        assert False, result["error"]

    # Show config comparison (values read from telemetry_config.yml and Kafka CRD)
    expected = result.get("expected_config", {})
    actual = result.get("actual_config", {})

    log.check(f"  log_retention_hours: expected={expected.get('log_retention_hours')}, "
              f"actual={actual.get('log.retention.hours')}")
    log.check(f"  log_retention_bytes: expected={expected.get('log_retention_bytes')}, "
              f"actual={actual.get('log.retention.bytes')}")
    log.check(f"  log_segment_bytes: expected={expected.get('log_segment_bytes')}, "
              f"actual={actual.get('log.segment.bytes')}")

    mismatches = result.get("mismatches", [])
    if result["success"]:
        log.passed(LOG_MSGS["kafka_config_match"], "All configurations match")
    else:
        mismatch_str = "\n".join([
            f"  - {m['config']}: expected {m['expected']}, actual {m['actual']}"
            for m in mismatches
        ])
        log.failed("Kafka configuration mismatch", mismatch_str)
        assert False, ASSERT_MSGS["kafka_config_mismatch"].format(mismatches=mismatch_str)


def test_kafka_idrac_topic_data(host):
    """
    Test Case 4: Verify data is flowing to idrac Kafka topic.

    Verifies:
    - idrac topic is ready
    - idrac-telemetry pods are running (kafkapump sends data)
    """
    log = TestLogger(TEST_NAMES["kafka_idrac_topic_data"])

    # Skip if Kafka not enabled
    if not is_kafka_enabled(host):
        pytest.skip("Kafka is not enabled in idrac_telemetry_collection_type")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify idrac topic data
    log.check("Verifying data flow to idrac Kafka topic")
    result = verify_idrac_topic_data(host, admin_ip)

    log.check(f"  Topic ready: {result.get('topic_ready', False)}")
    log.check(f"  Pods running: {result.get('pods_running', False)}")

    if result["success"]:
        log.passed(LOG_MSGS["kafka_idrac_data_flowing"], "idrac topic is receiving data")
    else:
        log.failed("idrac topic data flow verification failed", result.get("error", ""))
        assert False, ASSERT_MSGS["kafka_idrac_data_not_flowing"].format(
            topic_ready=result.get("topic_ready", False),
            pods_running=result.get("pods_running", False)
        )


def test_kafka_ldms_topic_data(host):
    """
    Test Case 6: Verify data is flowing to ldms Kafka topic.

    Only runs if LDMS is enabled in software_config.json.
    """
    log = TestLogger(TEST_NAMES["kafka_ldms_topic_data"])

    # Skip if Kafka not enabled
    if not is_kafka_enabled(host):
        pytest.skip("Kafka is not enabled")

    # Skip if LDMS not enabled
    if not is_ldms_enabled(host):
        log.check(LOG_MSGS["kafka_ldms_skipped"])
        pytest.skip("LDMS is not enabled in software_config.json")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify ldms topic data
    log.check("Verifying ldms Kafka topic")
    result = verify_ldms_topic_data(host, admin_ip)

    if result.get("skipped"):
        log.check(f"  Skipped: {result.get('reason', '')}")
        pytest.skip(result.get("reason", "LDMS not enabled"))

    log.check(f"  Topic ready: {result.get('topic_ready', False)}")

    if result["success"]:
        log.passed(LOG_MSGS["kafka_ldms_data_flowing"], "ldms topic is ready")
    else:
        log.failed("ldms topic verification failed", result.get("error", ""))
        assert False, ASSERT_MSGS["kafka_ldms_data_not_flowing"].format(
            topic_ready=result.get("topic_ready", False)
        )
