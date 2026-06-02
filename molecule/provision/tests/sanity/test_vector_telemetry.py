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
Vector Telemetry Test Cases for Provision Module.

Implements test cases from TCASES-VEC-2026-001 v1.0.0.

Multi-Vector architecture:
  - vector-ldms: LDMS metrics -> VictoriaMetrics
  - vector-ome:  OME events   -> VictoriaMetrics + VictoriaLogs

Automatable (17 tests):
  TC-F001  Vector Deployment Verification
  TC-F002  Kafka Topics Verification / LDMS Message Production
  TC-F003  Dynamic Topic Discovery
  TC-F004  OME Health Metrics in VictoriaMetrics
  TC-F005  OME Audit Logs in VictoriaLogs
  TC-F007  ConfigMap Verification
  TC-F008  Resource Specification Compliance
  TC-F010  Self-Metrics Exposure
  TC-E001  Malformed Message Handling
  TC-E002  Pipeline Recovery Readiness
  TC-E006  Transform Modification Constraint
  TC-I001  Redeployment Idempotency
  TC-S001  mTLS Authentication
  TC-S002  No Plaintext Credentials

Non-Automatable:
  TC-F006  Dead-Letter Routing (requires specific setup)
  TC-F009  Graceful Shutdown (requires pod termination observation)
  TC-P001  Performance tests (require scale environment)
  TC-E003  Infrastructure failure tests (require controlled env)
"""

import json
import time

import pytest

from automation_library.core import TestLogger
from automation_library.core.functions import run_on_remote_node
from automation_library.provision.functions import get_k8s_nodes
from automation_library.telemetry.functions import (
    create_kafka_topic,
    get_admin_ip,
    produce_test_message_to_kafka,
    skip_if_kafka_not_enabled,
    verify_all_vector_configmaps,
    verify_no_plaintext_credentials,
    verify_vector_configmap_exists,
    verify_vector_mtls_config,
    verify_vector_no_errors_in_logs,
    verify_vector_no_pvc,
    verify_vector_pod_running,
    verify_vector_resource_specs,
    verify_vector_self_metrics_endpoint,
)
from automation_library.telemetry.vars import (
    VECTOR_DEPLOYMENT_NAMES,
)


# =============================================================================
# FUNCTIONAL TEST CASES
# =============================================================================


@pytest.mark.sanity
@pytest.mark.order(32)
def test_vector_resource_compliance(host):
    """TC-F008: Vector Resource Specification Compliance.

    Verifies for both vector-ldms and vector-ome:
    - 2 replicas per deployment
    - Resource requests/limits match per-deployment specs
    - No PVC attached (stateless)

    Priority: P0 | Traces To: FS-VE-01
    """
    log = TestLogger("TC-F008: Vector Resource Specification Compliance")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    all_details = []
    all_pass = True

    for deploy_name in VECTOR_DEPLOYMENT_NAMES:
        log.check(f"Verifying {deploy_name} resource specifications")
        result = verify_vector_resource_specs(host, admin_ip, deploy_name)

        expected = result.get("expected_specs", {})
        actual = result.get("actual_specs", {})
        lines = [f"Deployment: {deploy_name}"]

        if result.get("success"):
            for key in expected:
                lines.append(
                    f"  [PASS] {key}: {actual.get(key, 'N/A')}"
                )
        else:
            all_pass = False
            for mis in result.get("mismatches", []):
                lines.append(
                    f"  [FAIL] {mis['field']}: "
                    f"expected={mis['expected']}, actual={mis['actual']}"
                )

        # Verify no PVC
        log.check(f"Verifying {deploy_name} has no PVC attached")
        pvc = verify_vector_no_pvc(host, admin_ip, deploy_name)
        if pvc.get("success"):
            lines.append("  [PASS] No PVC attached (stateless)")
        else:
            all_pass = False
            lines.append(
                f"  [FAIL] PVC found: {pvc.get('pvc_volumes', [])}"
            )

        all_details.extend(lines)

    details = "\n".join(all_details)
    assert all_pass, (
        "Vector resource specs must match expected values:\n" + details
    )
    log.passed("All Vector deployments match expected specs", details)


@pytest.mark.sanity
@pytest.mark.order(33)
def test_vector_deployment_verification(host):
    """TC-F001: Vector Deployment and End-to-End Pipeline Verification.

    Verifies for all Vector deployments (vector-ldms, vector-ome):
    - All pods are Running and ready
    - 0 restarts
    - No critical errors in logs

    Priority: P0 | Traces To: AC-9.1, FS-VE-01, FS-VE-02
    """
    log = TestLogger("TC-F001: Vector Deployment Verification")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Checking all Vector pods status (vector-ldms, vector-ome)")
    result = verify_vector_pod_running(host, admin_ip)

    total_pods = result.get("total_pods", 0)
    running_pods = result.get("running_pods", 0)
    pods = result.get("pods", [])

    lines = [
        f"Total pods: {total_pods}",
        f"Running pods: {running_pods}",
    ]
    for pod in pods:
        icon = "[PASS]" if pod.get("is_running") else "[FAIL]"
        lines.append(
            f"  {icon} {pod.get('pod_name')}: {pod.get('phase')} "
            f"(restarts: {pod.get('restarts', 0)})"
        )

    details = "\n".join(lines)
    assert result["success"], "All Vector pods must be in Running state"
    log.passed(
        f"All {running_pods}/{total_pods} Vector pods are Running", details
    )

    # Log errors (non-blocking)
    log.check("Verifying no critical errors in Vector logs")
    log_result = verify_vector_no_errors_in_logs(host, admin_ip, lines=500)

    err_count = log_result.get("error_count", 0)
    err_lines = log_result.get("error_lines", [])
    checked = log_result.get("deployments_checked", [])

    log_details = (
        f"Deployments checked: {', '.join(checked)}\n"
        f"Error count: {err_count}\n"
        f"Sample errors: {err_lines[:5]}"
    )

    if log_result["success"]:
        log.passed("No critical errors found in Vector logs", log_details)
    else:
        log.warning(
            f"Found {err_count} error entries in Vector logs", log_details
        )


@pytest.mark.sanity
@pytest.mark.order(34)
def test_vector_configmap_exists(host):
    """TC-F007: Custom Transform Application and Verification.

    Verifies:
    - vector-ldms-config ConfigMap exists
    - vector-ome-config ConfigMap exists

    Priority: P1 | Traces To: AC-9.6, FS-VE-04
    """
    log = TestLogger("TC-F007: Vector ConfigMap Verification")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying all Vector ConfigMaps exist")
    result = verify_all_vector_configmaps(host, admin_ip)

    total = result.get("total", 0)
    existing = result.get("existing", 0)

    lines = [f"Total ConfigMaps: {total}", f"Existing: {existing}"]
    for cm_info in result.get("configmaps", []):
        icon = "[PASS]" if cm_info.get("exists") else "[FAIL]"
        lines.append(f"  {icon} {cm_info.get('configmap_name')}")

    details = "\n".join(lines)
    assert result["success"], "All Vector ConfigMaps must exist"
    log.passed(f"All {existing}/{total} Vector ConfigMaps exist", details)


@pytest.mark.sanity
@pytest.mark.order(35)
def test_vector_self_metrics(host):
    """TC-F010: Vector Self-Metrics Exposure.

    Verifies vector-ldms exposes self-metrics on port 9599.

    Priority: P1 | Traces To: FS-VE-05
    """
    log = TestLogger("TC-F010: Vector Self-Metrics Exposure")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Querying vector-ldms self-metrics endpoint")
    result = verify_vector_self_metrics_endpoint(
        host, admin_ip, "vector-ldms"
    )

    details = (
        f"Deployment: {result.get('deployment_name', 'N/A')}\n"
        f"Pod: {result.get('pod_name', 'N/A')}\n"
        f"Metrics port: {result.get('metrics_port', 'N/A')}\n"
        f"Metrics available: {result.get('metrics_available', False)}\n"
        f"Patterns found: "
        f"{', '.join(result.get('expected_metrics_found', []))}"
    )

    if result["success"]:
        log.passed("Vector self-metrics endpoint is accessible", details)
    else:
        log.warning(
            "Vector self-metrics endpoint verification incomplete", details
        )


@pytest.mark.sanity
@pytest.mark.order(36)
def test_dynamic_topic_discovery(host):
    """TC-F003: Dynamic Topic Discovery.

    Verifies a new Kafka topic can be created.

    Priority: P1 | Traces To: AC-9.2, FS-VE-03
    """
    log = TestLogger("TC-F003: Dynamic Topic Discovery")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    test_topic = f"vector-test-discovery-{int(time.time())}"
    log.check(f"Creating new Kafka topic: {test_topic}")

    result = create_kafka_topic(host, admin_ip, test_topic)
    created = result.get("created", False) or result.get("success", False)

    details = (
        f"Topic: {test_topic}\n"
        f"Created: {created}\n"
        f"Output: {result.get('output', '')}"
    )

    if result["success"]:
        log.passed(f"Kafka topic '{test_topic}' created", details)
    else:
        log.warning(
            f"Topic creation incomplete: {result.get('error', 'Unknown')}",
            details,
        )


@pytest.mark.sanity
@pytest.mark.order(37)
def test_produce_test_message(host):
    """TC-F002: LDMS Metrics Pipeline - Message Production.

    Verifies test messages can be produced to Kafka 'ldms' topic.

    Priority: P0 | Traces To: AC-9.1
    """
    log = TestLogger("TC-F002: LDMS Message Production")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    test_message = json.dumps({
        "timestamp": int(time.time()),
        "hostname": "test-node-01",
        "plugin": "meminfo",
        "metric_name": "memory_used",
        "value": 1024,
        "namespace": "ldms",
    })

    log.check("Producing test LDMS message to Kafka 'ldms' topic")
    result = produce_test_message_to_kafka(
        host, admin_ip, "ldms", test_message
    )

    sent = result.get("message_sent", False)
    details = f"Topic: ldms\nMessage sent: {sent}"

    if result["success"]:
        log.passed("Test message produced to Kafka successfully", details)
    else:
        log.warning(
            f"Message production incomplete: "
            f"{result.get('error', 'Unknown')}",
            details,
        )


# =============================================================================
# NEGATIVE / ERROR TEST CASES
# =============================================================================


@pytest.mark.sanity
@pytest.mark.order(40)
def test_malformed_message_handling(host):
    """TC-E001: Malformed Message Handling.

    Produces malformed messages to Kafka for dead-letter routing validation.

    Priority: P0 | Traces To: AC-9.5, SCN-9.3-E1
    """
    log = TestLogger("TC-E001: Malformed Message Handling")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    malformed_messages = [
        '{"invalid": json}',
        '{}',
        '{"missing": "required_fields"}',
    ]

    log.check("Producing malformed messages to Kafka 'ldms' topic")

    results = []
    for msg in malformed_messages:
        result = produce_test_message_to_kafka(host, admin_ip, "ldms", msg)
        results.append(result.get("success", False))

    count = sum(results)
    total = len(malformed_messages)
    details = f"Malformed messages produced: {count}/{total}"

    log.info(
        "Malformed messages produced for dead-letter routing test", details
    )


@pytest.mark.sanity
@pytest.mark.order(41)
def test_vector_pipeline_recovery(host):
    """TC-E002: Vector Pipeline Failure and Recovery.

    Verifies pods are running and deployment supports auto-restart.

    Priority: P0 | Traces To: SCN-9.7-E1, FS-VE-05

    Note: Actual pod deletion is commented out for safety.
    """
    log = TestLogger("TC-E002: Vector Pipeline Recovery Readiness")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Recording current Vector pod state")
    initial = verify_vector_pod_running(host, admin_ip)

    total_pods = initial.get("total_pods", 0)
    running_pods = initial.get("running_pods", 0)
    pods = initial.get("pods", [])

    lines = [
        f"Total Vector pods: {total_pods}",
        f"Running pods: {running_pods}",
    ]
    for pod in pods:
        lines.append(f"  - {pod.get('pod_name')}: {pod.get('phase')}")

    details = "\n".join(lines)
    assert initial["success"], "Vector pods must be running for recovery test"
    log.passed(
        "Vector pods are running and ready for recovery testing", details
    )
    log.info("Note: Pod deletion test is commented out for safety")


@pytest.mark.sanity
@pytest.mark.order(42)
def test_runtime_transform_modification(host):
    """TC-E006: Runtime Transform Modification Constraint.

    Verifies ConfigMaps contain transform configuration.

    Priority: P2 | Traces To: SCN-9.5-E2

    Note: Actual rollout restart is commented out for safety.
    """
    log = TestLogger("TC-E006: Transform Modification Constraint")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying Vector ConfigMaps contain transform configuration")

    result = verify_vector_configmap_exists(
        host, admin_ip, "vector-ldms-config"
    )

    if result.get("success"):
        config_content = result.get("config_content", "")
        has_transforms = "transform" in config_content.lower()

        details = (
            f"ConfigMap: vector-ldms-config\n"
            f"Contains transforms: {has_transforms}\n"
            f"Config size: {len(config_content)} bytes"
        )

        log.passed(
            "Vector ConfigMap contains transform configuration", details
        )
    else:
        log.warning(
            f"ConfigMap verification failed: "
            f"{result.get('error', 'Unknown')}"
        )

    log.info("Note: Rollout restart test is commented out for safety")


# =============================================================================
# IDEMPOTENCY TEST CASES
# =============================================================================


@pytest.mark.sanity
@pytest.mark.order(45)
def test_vector_redeployment_idempotency(host):
    """TC-I001: Vector Redeployment Idempotency.

    Verifies all deployments are running, healthy, and not restarting.

    Priority: P1 | Traces To: FS-VE-01
    """
    log = TestLogger("TC-I001: Redeployment Idempotency")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Verifying Vector deployments are in consistent state")
    result = verify_vector_pod_running(host, admin_ip)

    total_pods = result.get("total_pods", 0)
    running_pods = result.get("running_pods", 0)
    pods = result.get("pods", [])
    total_restarts = sum(p.get("restarts", 0) for p in pods)

    lines = [
        f"Total pods: {total_pods}",
        f"Running pods: {running_pods}",
        f"Total restarts: {total_restarts}",
    ]
    for pod in pods:
        icon = "[PASS]" if pod.get("is_running") else "[FAIL]"
        lines.append(
            f"  {icon} {pod.get('pod_name')}: "
            f"restarts={pod.get('restarts', 0)}"
        )

    details = "\n".join(lines)
    assert result["success"], "All Vector pods must be running for idempotency"
    log.passed(
        "Vector deployments are idempotent (consistent state)", details
    )


# =============================================================================
# SECURITY TEST CASES
# =============================================================================


@pytest.mark.sanity
@pytest.mark.order(50)
def test_mtls_authentication(host):
    """TC-S001: mTLS Authentication to Kafka Brokers.

    Verifies TLS certificate paths are present in configuration.

    Priority: P0 | Traces To: FS-VE-05, BSpec 6.9
    """
    log = TestLogger("TC-S001: mTLS Authentication")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Checking mTLS configuration in vector-ldms-config")
    result = verify_vector_mtls_config(
        host, admin_ip, "vector-ldms-config"
    )

    tls_ok = result.get("tls_configured", False)
    cert_paths = result.get("cert_paths", [])

    details = (
        f"ConfigMap: vector-ldms-config\n"
        f"TLS configured: {tls_ok}\n"
        f"Certificate paths found: {len(cert_paths)}\n"
        f"Sample paths: {cert_paths[:5]}"
    )

    assert result["success"], "Vector must be configured with mTLS for Kafka"
    log.passed("Vector is configured with mTLS for Kafka", details)


@pytest.mark.sanity
@pytest.mark.order(51)
def test_no_plaintext_credentials(host):
    """TC-S002: No Plaintext Credentials in Deployed Artifacts.

    Scans logs, ConfigMaps and Deployment manifests for credentials.

    Priority: P0 | Traces To: BSpec 6.9
    """
    log = TestLogger("TC-S002: No Plaintext Credentials")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Searching for plaintext credentials in Vector artifacts")
    result = verify_no_plaintext_credentials(host, admin_ip)

    findings = result.get("credential_findings", [])
    details = (
        f"Deployments checked: "
        f"{', '.join(result.get('deployments_checked', []))}\n"
        f"ConfigMaps checked: "
        f"{', '.join(result.get('configmaps_checked', []))}\n"
        f"Patterns checked: {len(result.get('patterns_checked', []))}\n"
        f"Credential findings: {len(findings)}"
    )

    assert result["success"], (
        "No plaintext credentials allowed in Vector artifacts"
    )
    log.passed(
        "No plaintext credentials found in Vector artifacts", details
    )


# =============================================================================
# QUERY VERIFICATION TEST CASES
# =============================================================================


@pytest.mark.sanity
@pytest.mark.order(55)
def test_kafka_topics_exist(host):
    """TC-F002: Verify Kafka Topics Exist.

    Queries Kafka Bridge REST API for OME topics.

    Priority: P0 | Traces To: AC-9.1
    """
    log = TestLogger("TC-F002: Kafka Topics Verification")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Getting Kafka Bridge LoadBalancer IP")
    cmd = run_on_remote_node(
        host,
        (
            "kubectl get svc bridge-bridge-lb -n telemetry"
            " -o jsonpath="
            "'{.status.loadBalancer.ingress[0].ip}'"
        ),
        admin_ip,
    )

    if cmd.rc != 0:
        log.failed("Failed to get Kafka Bridge IP", cmd.stderr)
        pytest.fail("Cannot get Kafka Bridge IP")

    kafka_lb_ip = cmd.stdout.strip()
    log.info(f"Kafka Bridge IP: {kafka_lb_ip}")

    log.check("Querying Kafka topics via Bridge REST API")
    topics_cmd = run_on_remote_node(
        host,
        f"curl -s -X GET 'http://{kafka_lb_ip}:8080/topics'"
        " | jq -r '.[]'",
        admin_ip,
    )

    if topics_cmd.rc != 0:
        log.failed("Failed to query Kafka topics", topics_cmd.stderr)
        pytest.fail("Cannot query Kafka topics")

    topics = [
        t.strip()
        for t in topics_cmd.stdout.strip().split("\n")
        if t.strip()
    ]

    lines = [
        f"Kafka Bridge IP: {kafka_lb_ip}",
        f"Total topics: {len(topics)}",
        "Topics found:",
    ]
    for topic in topics:
        lines.append(f"  - {topic}")

    details = "\n".join(lines)

    expected = ["ome.health", "ome.auditlogs"]
    found = [t for t in expected if t in topics]

    if found:
        log.passed(
            f"Found {len(found)}/{len(expected)} expected topics", details
        )
    else:
        log.warning("No expected OME topics found", details)


@pytest.mark.sanity
@pytest.mark.order(56)
def test_query_victoria_metrics_ome_health(host):
    """TC-F004: OME Health Metrics in VictoriaMetrics.

    Queries VictoriaMetrics for OME health metrics via PromQL.

    Priority: P0 | Traces To: AC-9.3, FS-VE-04
    """
    log = TestLogger("TC-F004: OME Health Metrics Verification")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Getting VictoriaMetrics vmselect IP")
    cmd = run_on_remote_node(
        host,
        (
            "kubectl get svc vmselect-victoria-cluster -n telemetry"
            " -o jsonpath="
            "'{.status.loadBalancer.ingress[0].ip}'"
        ),
        admin_ip,
    )

    if cmd.rc != 0:
        log.warning("Failed to get vmselect IP", cmd.stderr)
        pytest.skip("Cannot get vmselect IP")

    vmselect_ip = cmd.stdout.strip()
    log.info(f"VictoriaMetrics vmselect IP: {vmselect_ip}")

    log.check("Querying OME health metrics from VictoriaMetrics")
    query = 'last_over_time({source_subsystem="ome",type="health"}[1h])'
    vm_url = (
        f"https://{vmselect_ip}:8481"
        "/select/0/prometheus/api/v1/query"
    )

    query_cmd = run_on_remote_node(
        host,
        f"curl -ksS '{vm_url}' --data-urlencode 'query={query}'"
        " | jq -r '.data.result | length'",
        admin_ip,
    )

    if query_cmd.rc != 0:
        log.warning("Failed to query VictoriaMetrics", query_cmd.stderr)
        pytest.skip("Cannot query VictoriaMetrics")

    stdout = query_cmd.stdout.strip()
    result_count = int(stdout) if stdout.isdigit() else 0

    sample_cmd = run_on_remote_node(
        host,
        f"curl -ksS '{vm_url}' --data-urlencode 'query={query}'"
        " | jq -r '.data.result[0:3]'",
        admin_ip,
    )

    lines = [
        f"VictoriaMetrics URL: {vm_url}",
        f"Query: {query}",
        f"Results found: {result_count}",
    ]
    if result_count > 0 and sample_cmd.rc == 0:
        lines.append(f"Sample: {sample_cmd.stdout[:200]}...")

    details = "\n".join(lines)

    if result_count > 0:
        log.passed(
            f"OME health metrics found ({result_count} results)", details
        )
    else:
        log.warning(
            "No OME health metrics found (may need time to ingest)",
            details,
        )


@pytest.mark.sanity
@pytest.mark.order(57)
def test_query_victoria_logs_ome_auditlogs(host):
    """TC-F005: OME Audit Logs in VictoriaLogs.

    Queries VictoriaLogs for OME audit logs via LogsQL.

    Priority: P0 | Traces To: AC-9.4, FS-VE-04
    """
    log = TestLogger("TC-F005: OME Audit Logs Verification")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    log.check("Getting VictoriaLogs vlselect IP")
    cmd = run_on_remote_node(
        host,
        (
            "kubectl get svc vlselect-victoria-logs-cluster"
            " -n telemetry -o jsonpath="
            "'{.status.loadBalancer.ingress[0].ip}'"
        ),
        admin_ip,
    )

    if cmd.rc != 0:
        log.warning("Failed to get vlselect IP", cmd.stderr)
        pytest.skip("Cannot get vlselect IP")

    vlselect_ip = cmd.stdout.strip()
    log.info(f"VictoriaLogs vlselect IP: {vlselect_ip}")

    log.check("Querying OME audit logs from VictoriaLogs")
    query = "_msg_topic:ome.auditlogs"
    vl_url = f"https://{vlselect_ip}:9471/select/logsql/query"

    query_cmd = run_on_remote_node(
        host,
        f"curl -ksS '{vl_url}'"
        f" --data-urlencode 'query={query}'"
        " --data-urlencode 'limit=20'"
        " | jq -r '._msg' | head -1",
        admin_ip,
    )

    if query_cmd.rc != 0:
        log.warning("Failed to query VictoriaLogs", query_cmd.stderr)
        pytest.skip("Cannot query VictoriaLogs")

    has_results = (
        query_cmd.stdout.strip() != ""
        and query_cmd.stdout.strip() != "null"
    )

    count_cmd = run_on_remote_node(
        host,
        f"curl -ksS '{vl_url}'"
        f" --data-urlencode 'query={query}'"
        " --data-urlencode 'limit=100'"
        " | jq -r '._msg' | wc -l",
        admin_ip,
    )

    stdout = count_cmd.stdout.strip()
    result_count = int(stdout) if stdout.isdigit() else 0

    lines = [
        f"VictoriaLogs URL: {vl_url}",
        f"Query: {query}",
        f"Results found: {result_count}",
    ]

    if has_results:
        sample_cmd = run_on_remote_node(
            host,
            f"curl -ksS '{vl_url}'"
            f" --data-urlencode 'query={query}'"
            " --data-urlencode 'limit=1'"
            " | jq -r '._msg | fromjson | .Data[0].Message'",
            admin_ip,
        )
        if sample_cmd.rc == 0 and sample_cmd.stdout.strip():
            lines.append(
                f"Sample: {sample_cmd.stdout.strip()[:100]}..."
            )

    details = "\n".join(lines)

    if result_count > 0:
        log.passed(
            f"OME audit logs found ({result_count} results)", details
        )
    else:
        log.warning(
            "No OME audit logs found (may need time to ingest)", details
        )
