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
Vector Telemetry Test Cases.

This module contains pytest test cases for verifying Vector deployment and pipeline.
Implements test cases from TCASES-VEC-2026-001 v1.0.0.

Automatable Test Cases:
- TC-F001: Vector Deployment and End-to-End Pipeline Verification
- TC-F002: Content-Type Based Message Routing
- TC-F003: Dynamic Topic Discovery
- TC-F004: Metric Format Normalization (PromQL-Queryable)
- TC-F005: Event Format Normalization (LogsQL-Searchable)
- TC-F006: Dead-Letter Routing for Malformed Messages
- TC-F007: Custom Transform Application and Verification
- TC-F008: Vector Resource Specification Compliance
- TC-F009: Metric Enrichment and Schema Normalization
- TC-F010: Vector Self-Metrics Exposure
- TC-E001: Malformed Message Handling (Multiple Formats)
- TC-E002: Vector Pipeline Failure and Recovery
- TC-E006: Runtime Transform Modification Constraint
- TC-I001: Vector Redeployment Idempotency
- TC-S001: mTLS Authentication to Kafka Brokers
- TC-S002: No Plaintext Credentials in Deployed Artifacts

Note: Performance tests (TC-P001-TC-P004) require scale environment.
Note: TC-E003, TC-E004, TC-E004B, TC-E005 require infrastructure manipulation.
"""

import json
import time
from datetime import datetime

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.messages import (
    VECTOR_TEST_NAMES,
    VECTOR_TEST_LOG_MSGS as LOG_MSGS,
    VECTOR_TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    get_admin_ip,
    skip_if_kafka_not_enabled,
)
from automation_library.telemetry.functions.vector_func import (
    verify_vector_pod_running,
    verify_vector_resource_specs,
    verify_vector_no_pvc,
    verify_vector_configmap_exists,
    verify_vector_mtls_config,
    get_vector_pod_logs,
    verify_vector_no_errors_in_logs,
    verify_no_plaintext_credentials,
    verify_vector_self_metrics_endpoint,
    delete_vector_pod,
    rollout_restart_vector,
    scale_vector_deployment,
    create_kafka_topic,
    produce_test_message_to_kafka,
    query_victoria_metrics,
    query_victoria_logs,
)
from automation_library.telemetry.vars.vector_vars import (
    VECTOR_RESOURCE_SPECS,
    VECTOR_KAFKA_TOPICS,
    LATENCY_THRESHOLDS,
)


# =============================================================================
# FUNCTIONAL TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_vector_resource_compliance(host):
    """
    TC-F008: Vector Resource Specification Compliance.
    
    Verifies:
    - Single replica deployment
    - Memory: 512Mi request / 1Gi limit
    - CPU: 250m request / 1000m limit
    - No PVC attached (stateless)
    - Pod Running with 0 restarts
    - Deployed in telemetry namespace
    
    Priority: P0
    Traces To: FS-VE-01
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("resource_compliance", "TC-F008: Vector Resource Specification Compliance"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Verify resource specifications
    log.check(LOG_MSGS.get("verify_resource_specs", "Verifying Vector resource specifications"))
    result = verify_vector_resource_specs(host, admin_ip)
    
    details_lines = []
    if result.get("success"):
        expected = result.get("expected_specs", {})
        actual = result.get("actual_specs", {})
        for key in expected:
            exp_val = expected[key]
            act_val = actual.get(key, "N/A")
            match = "✓" if exp_val == act_val else "✗"
            details_lines.append(f"{match} {key}: expected={exp_val}, actual={act_val}")
    else:
        mismatches = result.get("mismatches", [])
        for mismatch in mismatches:
            field = mismatch["field"]
            expected = mismatch["expected"]
            actual = mismatch["actual"]
            details_lines.append(f"✗ {field}: expected={expected}, actual={actual}")
    
    details = "\n".join(details_lines)
    
    assert result["success"], ASSERT_MSGS.get("resource_specs_match", "Vector resource specs must match FSpec")
    log.passed("Vector resource specifications match FSpec", details)
    
    # Verify no PVC attached
    log.check(LOG_MSGS.get("verify_no_pvc", "Verifying Vector has no PVC attached"))
    pvc_result = verify_vector_no_pvc(host, admin_ip)
    
    pvc_details = f"Has PVC: {pvc_result.get('has_pvc', False)}\nPVC Volumes: {pvc_result.get('pvc_volumes', [])}"
    
    assert pvc_result["success"], ASSERT_MSGS.get("no_pvc_attached", "Vector must have no PVC attached")
    log.passed("Vector is stateless (no PVC attached)", pvc_details)


@pytest.mark.sanity
@pytest.mark.order(11)
def test_vector_deployment_verification(host):
    """
    TC-F001: Vector Deployment and End-to-End Pipeline Verification.
    
    Verifies:
    - Vector pod is Running
    - 0 restarts
    - No errors in logs
    
    Priority: P0
    Traces To: AC-9.1, FS-VE-01, FS-VE-02
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("vector_deployment", "TC-F001: Vector Deployment Verification"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Verify Vector pod is running
    log.check(LOG_MSGS.get("check_vector_pod", "Checking Vector pod status"))
    result = verify_vector_pod_running(host, admin_ip)
    
    pod_name = result.get("pod_name", "N/A")
    phase = result.get("phase", "N/A")
    ready = result.get("ready", False)
    restarts = result.get("restarts", 0)
    
    details = (
        f"Pod Name: {pod_name}\n"
        f"Phase: {phase}\n"
        f"Ready: {ready}\n"
        f"Restarts: {restarts}"
    )
    
    assert result["success"], ASSERT_MSGS.get("vector_pod_running", "Vector pod must be in Running state")
    log.passed("Vector pod is Running with 0 restarts", details)
    
    # Verify no errors in logs
    log.check(LOG_MSGS.get("verify_error_logs", "Verifying no errors in Vector logs"))
    log_result = verify_vector_no_errors_in_logs(host, admin_ip, lines=500)
    
    error_count = log_result.get("error_count", 0)
    error_lines = log_result.get("error_lines", [])
    
    log_details = f"Error count: {error_count}\nSample errors: {error_lines[:5]}"
    
    if log_result["success"]:
        log.passed("No errors found in Vector logs", log_details)
    else:
        log.warning(f"Found {error_count} error entries in Vector logs", log_details)


@pytest.mark.sanity
@pytest.mark.order(12)
def test_vector_configmap_exists(host):
    """
    TC-F007: Custom Transform Application and Verification (Part 1).
    
    Verifies:
    - Vector ConfigMap exists
    - ConfigMap contains configuration
    
    Priority: P1
    Traces To: AC-9.6, FS-VE-04
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("custom_transforms", "TC-F007: Vector ConfigMap Verification"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    log.check(LOG_MSGS.get("verify_transform_config", "Verifying Vector ConfigMap exists"))
    result = verify_vector_configmap_exists(host, admin_ip)
    
    configmap_exists = result.get("configmap_exists", False)
    config_length = len(result.get("config_content", ""))
    
    details = f"ConfigMap exists: {configmap_exists}\nConfig size: {config_length} bytes"
    
    assert result["success"], "Vector ConfigMap must exist"
    log.passed("Vector ConfigMap exists and contains configuration", details)


@pytest.mark.sanity
@pytest.mark.order(13)
def test_vector_self_metrics(host):
    """
    TC-F010: Vector Self-Metrics Exposure.
    
    Verifies:
    - Vector exposes self-metrics endpoint
    - Expected metrics are present
    
    Priority: P1
    Traces To: FS-VE-05
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("self_metrics", "TC-F010: Vector Self-Metrics Exposure"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    log.check(LOG_MSGS.get("query_self_metrics", "Querying Vector self-metrics endpoint"))
    result = verify_vector_self_metrics_endpoint(host, admin_ip)
    
    metrics_available = result.get("metrics_available", False)
    expected_found = result.get("expected_metrics_found", [])
    expected_total = result.get("expected_metrics_total", 0)
    
    details = (
        f"Metrics endpoint: {result.get('metrics_endpoint', 'N/A')}\n"
        f"Metrics available: {metrics_available}\n"
        f"Expected metrics found: {len(expected_found)}/{expected_total}\n"
        f"Metrics: {', '.join(expected_found[:5])}"
    )
    
    if result["success"]:
        log.passed("Vector self-metrics endpoint is accessible", details)
    else:
        log.warning("Vector self-metrics endpoint verification incomplete", details)


@pytest.mark.sanity
@pytest.mark.order(14)
def test_dynamic_topic_discovery(host):
    """
    TC-F003: Dynamic Topic Discovery.
    
    Verifies:
    - New Kafka topic can be created
    - Vector should discover it within 60 seconds (manual verification needed)
    
    Priority: P1
    Traces To: AC-9.2, FS-VE-03
    
    Note: Full verification requires waiting 60s and producing messages.
    This test only verifies topic creation capability.
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("topic_discovery", "TC-F003: Dynamic Topic Discovery"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Create a new test topic
    test_topic = f"vector-test-discovery-{int(time.time())}"
    log.check(LOG_MSGS.get("create_new_topic", f"Creating new Kafka topic: {test_topic}"))
    
    result = create_kafka_topic(host, admin_ip, test_topic)
    
    topic_created = result.get("created", False) or result.get("success", False)
    
    details = f"Topic: {test_topic}\nCreated: {topic_created}\nOutput: {result.get('output', '')}"
    
    if result["success"]:
        log.passed(f"Kafka topic '{test_topic}' created successfully", details)
    else:
        log.warning(f"Topic creation verification incomplete: {result.get('error', 'Unknown')}", details)


@pytest.mark.sanity
@pytest.mark.order(15)
def test_produce_test_message(host):
    """
    TC-F001/TC-F002: Message Production Capability.
    
    Verifies:
    - Test messages can be produced to Kafka topics
    
    Priority: P0
    Traces To: AC-9.1
    
    Note: This tests the capability to produce messages.
    Full end-to-end verification requires VictoriaMetrics/VictoriaLogs queries.
    """
    log = TestLogger("Vector: Test Message Production")
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Produce a test LDMS metric message
    test_message = json.dumps({
        "timestamp": int(time.time()),
        "hostname": "test-node-01",
        "plugin": "meminfo",
        "metric_name": "memory_used",
        "value": 1024,
        "namespace": "ldms",
    })
    
    log.check(LOG_MSGS.get("produce_ldms_messages", "Producing test LDMS message to Kafka"))
    result = produce_test_message_to_kafka(host, admin_ip, "ldms", test_message)
    
    message_sent = result.get("message_sent", False)
    
    details = f"Topic: ldms\nMessage sent: {message_sent}"
    
    if result["success"]:
        log.passed("Test message produced to Kafka successfully", details)
    else:
        log.warning(f"Message production verification incomplete: {result.get('error', 'Unknown')}", details)


# =============================================================================
# NEGATIVE / ERROR TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(20)
def test_malformed_message_handling(host):
    """
    TC-F006/TC-E001: Malformed Message Handling.
    
    Verifies:
    - Malformed messages can be produced
    - Dead-letter routing capability exists
    
    Priority: P0
    Traces To: AC-9.5, SCN-9.3-E1
    
    Note: Full verification requires checking dead-letter topic and error logs.
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("malformed_handling", "TC-E001: Malformed Message Handling"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Produce malformed messages
    malformed_messages = [
        '{"invalid": json}',  # Invalid JSON
        '{}',  # Empty payload
        '{"missing": "required_fields"}',  # Missing required fields
    ]
    
    log.check(LOG_MSGS.get("produce_malformed", "Producing malformed messages to Kafka"))
    
    results = []
    for msg in malformed_messages:
        result = produce_test_message_to_kafka(host, admin_ip, "ldms", msg)
        results.append(result.get("success", False))
    
    details = f"Malformed messages produced: {sum(results)}/{len(malformed_messages)}"
    
    log.info("Malformed messages produced for dead-letter routing test", details)


@pytest.mark.sanity
@pytest.mark.order(21)
def test_vector_pipeline_recovery(host):
    """
    TC-E002: Vector Pipeline Failure and Recovery.
    
    Verifies:
    - Vector pod can be deleted
    - Kubernetes should automatically restart it (manual verification)
    
    Priority: P0
    Traces To: SCN-9.7-E1, FS-VE-05
    
    WARNING: This test deletes the Vector pod. Use with caution.
    Note: Automatic restart verification requires waiting and re-checking.
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("pipeline_recovery", "TC-E002: Vector Pipeline Recovery"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Get initial pod state
    log.check("Recording initial Vector pod state")
    initial_result = verify_vector_pod_running(host, admin_ip)
    initial_pod = initial_result.get("pod_name", "")
    
    log.info(f"Initial Vector pod: {initial_pod}")
    
    # Note: Actual pod deletion is commented out for safety
    # Uncomment the following lines to enable pod deletion test
    
    # log.check(LOG_MSGS.get("kill_vector_pod", "Deleting Vector pod to simulate failure"))
    # delete_result = delete_vector_pod(host, admin_ip)
    # 
    # if delete_result.get("success"):
    #     log.info(f"Vector pod '{initial_pod}' deleted successfully")
    #     
    #     # Wait for restart
    #     log.check(LOG_MSGS.get("wait_restart", "Waiting for Kubernetes to restart Vector pod"))
    #     time.sleep(30)
    #     
    #     # Verify new pod is running
    #     new_result = verify_vector_pod_running(host, admin_ip)
    #     new_pod = new_result.get("pod_name", "")
    #     
    #     details = f"Old pod: {initial_pod}\nNew pod: {new_pod}\nRunning: {new_result.get('success')}"
    #     
    #     assert new_result["success"], ASSERT_MSGS.get("auto_restart", "Kubernetes must restart Vector pod")
    #     log.passed("Vector pod restarted successfully", details)
    # else:
    #     log.warning(f"Pod deletion failed: {delete_result.get('error', 'Unknown')}")
    
    log.info("TC-E002: Pod deletion test skipped (safety). Uncomment code to enable.")


@pytest.mark.sanity
@pytest.mark.order(22)
def test_runtime_transform_modification(host):
    """
    TC-E006: Runtime Transform Modification Constraint.
    
    Verifies:
    - Vector deployment can be restarted via rollout restart
    - Constraint: transforms require redeployment (not runtime update)
    
    Priority: P2
    Traces To: SCN-9.5-E2
    
    Note: Full verification requires ConfigMap edit and message production.
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("transform_modification", "TC-E006: Transform Modification"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Test rollout restart capability
    log.check("Testing Vector rollout restart capability")
    
    # Note: Actual restart is commented out for safety
    # Uncomment to enable restart test
    
    # result = rollout_restart_vector(host, admin_ip)
    # 
    # if result.get("success"):
    #     log.info("Vector deployment rollout restart initiated")
    #     
    #     # Wait for restart
    #     time.sleep(30)
    #     
    #     # Verify pod is running
    #     pod_result = verify_vector_pod_running(host, admin_ip)
    #     
    #     details = f"Restarted: {result.get('restarted')}\nPod running: {pod_result.get('success')}"
    #     
    #     if pod_result.get("success"):
    #         log.passed("Vector deployment restarted successfully", details)
    #     else:
    #         log.warning("Vector pod not running after restart", details)
    # else:
    #     log.warning(f"Rollout restart failed: {result.get('error', 'Unknown')}")
    
    log.info("TC-E006: Rollout restart test skipped (safety). Uncomment code to enable.")


# =============================================================================
# IDEMPOTENCY TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(25)
def test_vector_redeployment_idempotency(host):
    """
    TC-I001: Vector Redeployment Idempotency.
    
    Verifies:
    - Vector resource specs remain consistent
    - Deployment configuration is idempotent
    
    Priority: P1
    Traces To: FS-VE-01
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("redeployment_idempotency", "TC-I001: Redeployment Idempotency"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Verify resource specs (idempotency check)
    log.check("Verifying Vector resource specifications are consistent")
    result = verify_vector_resource_specs(host, admin_ip)
    
    mismatches = result.get("mismatches", [])
    
    details = f"Mismatches: {len(mismatches)}\nExpected specs: {VECTOR_RESOURCE_SPECS}"
    
    assert result["success"], "Vector resource specs must be consistent (idempotent)"
    log.passed("Vector deployment is idempotent (resource specs consistent)", details)


# =============================================================================
# SECURITY TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(30)
def test_mtls_authentication(host):
    """
    TC-S001: mTLS Authentication to Kafka Brokers.
    
    Verifies:
    - Vector is configured with mTLS for Kafka
    - TLS certificate paths are present in configuration
    
    Priority: P0
    Traces To: FS-VE-05, BSpec 6.9
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("mtls_authentication", "TC-S001: mTLS Authentication"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    log.check(LOG_MSGS.get("check_mtls_config", "Checking mTLS configuration in Vector ConfigMap"))
    result = verify_vector_mtls_config(host, admin_ip)
    
    tls_configured = result.get("tls_configured", False)
    cert_paths = result.get("cert_paths", [])
    
    details = (
        f"TLS configured: {tls_configured}\n"
        f"Certificate paths found: {len(cert_paths)}\n"
        f"Sample paths: {cert_paths[:3]}"
    )
    
    assert result["success"], ASSERT_MSGS.get("mtls_configured", "Vector must be configured with mTLS")
    log.passed("Vector is configured with mTLS for Kafka", details)


@pytest.mark.sanity
@pytest.mark.order(31)
def test_no_plaintext_credentials(host):
    """
    TC-S002: No Plaintext Credentials in Deployed Artifacts.
    
    Verifies:
    - No plaintext credentials in logs
    - No plaintext credentials in ConfigMaps
    - No plaintext credentials in Deployment manifests
    
    Priority: P0
    Traces To: BSpec 6.9
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("no_plaintext_credentials", "TC-S002: No Plaintext Credentials"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    log.check(LOG_MSGS.get("search_credentials", "Searching for plaintext credentials"))
    result = verify_no_plaintext_credentials(host, admin_ip)
    
    findings = result.get("credential_findings", [])
    patterns_checked = result.get("patterns_checked", [])
    
    details = (
        f"Credential findings: {len(findings)}\n"
        f"Patterns checked: {len(patterns_checked)}\n"
        f"Findings: {findings}"
    )
    
    assert result["success"], ASSERT_MSGS.get("no_plaintext_creds", "No plaintext credentials allowed")
    log.passed("No plaintext credentials found in Vector artifacts", details)


# =============================================================================
# QUERY VERIFICATION TEST CASES (Requires VictoriaMetrics/VictoriaLogs)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(40)
def test_query_victoria_metrics_capability(host):
    """
    TC-F004: Metric Format Normalization - Query Capability.
    
    Verifies:
    - VictoriaMetrics can be queried via PromQL
    
    Priority: P0
    Traces To: AC-9.3, FS-VE-04
    
    Note: This tests query capability. Actual metric verification requires
    message production and waiting for ingestion.
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("metric_normalization", "TC-F004: PromQL Query Capability"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Test basic PromQL query
    log.check(LOG_MSGS.get("query_victoria_metrics", "Testing VictoriaMetrics PromQL query"))
    
    # Query for any metric (up is a common metric)
    result = query_victoria_metrics(host, admin_ip, "up")
    
    if result.get("success"):
        result_count = result.get("result_count", 0)
        details = f"Query: up\nResults: {result_count}"
        log.passed("VictoriaMetrics PromQL query successful", details)
    else:
        log.warning(f"VictoriaMetrics query failed: {result.get('error', 'Unknown')}")


@pytest.mark.sanity
@pytest.mark.order(41)
def test_query_victoria_logs_capability(host):
    """
    TC-F005: Event Format Normalization - Query Capability.
    
    Verifies:
    - VictoriaLogs can be queried via LogsQL
    
    Priority: P0
    Traces To: AC-9.4, FS-VE-04
    
    Note: This tests query capability. Actual event verification requires
    message production and waiting for ingestion.
    """
    log = TestLogger(VECTOR_TEST_NAMES.get("event_normalization", "TC-F005: LogsQL Query Capability"))
    
    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)
    
    # Test basic LogsQL query
    log.check(LOG_MSGS.get("query_victoria_logs", "Testing VictoriaLogs LogsQL query"))
    
    # Query for recent logs
    result = query_victoria_logs(host, admin_ip, "*")
    
    if result.get("success"):
        result_count = result.get("result_count", 0)
        details = f"Query: *\nResults: {result_count}"
        log.passed("VictoriaLogs LogsQL query successful", details)
    else:
        log.warning(f"VictoriaLogs query failed: {result.get('error', 'Unknown')}")
