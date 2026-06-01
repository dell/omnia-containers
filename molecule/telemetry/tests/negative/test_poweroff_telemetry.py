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
Telemetry Poweroff Negative Test Cases.

Tests telemetry pod resilience when a K8s worker node is powered off.
Verifies that pods reschedule to available nodes and all sanity tests pass.

Skip Logic:
- If service_kube is not enabled -> ALL tests skip
- If less than 2 worker nodes -> ALL tests skip
- If poweroff test (test case 1) skips or fails -> ALL subsequent tests skip

Test cases (mirrors sanity tests after poweroff):
1. Verify telemetry pods reschedule after worker node poweroff
2. Verify idrac-telemetry pod count
3. Verify MySQL data in idrac-telemetry pods
4. Verify idrac-telemetry-receiver is collecting metrics
5. Verify LDMS pods running
6. Verify LDMS services ports
7. Verify Kafka topics
8. Verify Kafka config match
9. Verify iDRAC data in Kafka
10. Verify LDMS data in Kafka
11. Verify VictoriaMetrics enabled
12. Verify VictoriaMetrics persistence size
13. Verify VictoriaMetrics pods (single-node or cluster)
14. Verify vmagent pod
15. Verify VictoriaMetrics services
16. Verify VictoriaMetrics TLS secret
17. Verify VictoriaMetrics TLS health
18. Verify iDRAC data in VictoriaMetrics
"""

import time
import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.functions import (
    get_k8s_worker_nodes,
    select_target_node_for_poweroff,
    poweroff_node,
    wait_for_node_down,
    get_telemetry_pods_on_node,
    get_all_telemetry_pods,
    wait_for_pods_reschedule,
    verify_all_telemetry_pods_running,
    verify_idrac_telemetry_pod_count,
    verify_mysql_data_in_pods,
    verify_receiver_collecting_metrics,
    has_activated_ips,
    verify_kafka_config_match,
    verify_kafka_topics_via_rest,
    verify_ldms_pods_running,
    verify_ldms_services_ports,
    verify_idrac_data_in_kafka,
    verify_ldms_data_in_kafka,
    get_deployment_mode,
    get_victoria_config,
    verify_victoria_persistence_size,
    verify_victoria_single_node_pods,
    verify_victoria_cluster_pods,
    verify_vmagent_pod,
    verify_victoria_services,
    verify_victoria_tls_secret,
    verify_victoria_tls_health,
    verify_victoria_idrac_data,
    get_activated_service_tags,
)
from automation_library.telemetry.functions.shared_func import (
    get_admin_ip,
    is_kafka_enabled,
    is_ldms_enabled,
    is_victoria_enabled,
    is_idrac_telemetry_enabled,
    skip_if_kafka_not_enabled,
    skip_if_ldms_not_enabled,
    skip_if_victoria_not_enabled,
)
from automation_library.telemetry.vars import NODE_POWEROFF_WAIT_SECONDS
from automation_library.telemetry.vars.victoria_vars import (
    DEPLOYMENT_MODE_SINGLE,
    DEPLOYMENT_MODE_CLUSTER,
    VICTORIA_TLS_SECRET,
)
from automation_library.telemetry.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.telemetry.messages.victoria_msgs import (
    VICTORIA_TEST_NAMES,
    VICTORIA_LOG_MSGS,
    VICTORIA_ASSERT_MSGS,
)
from automation_library.telemetry.messages.delete_node_msgs import (
    DELETE_NODE_TEST_NAMES,
    DELETE_NODE_LOG_MSGS,
    DELETE_NODE_ASSERT_MSGS,
)
from automation_library.telemetry.functions.delete_node_func import (
    get_deleted_nodes_cached,
    get_deleted_ldms_hostnames,
    get_deleted_service_tags,
    get_deleted_bmc_ips,
    skip_if_no_deleted_nodes,
    verify_ldms_deleted_node_in_kafka,
    verify_idrac_deleted_node_in_kafka,
    verify_idrac_deleted_node_in_mysql,
    verify_idrac_deleted_node_in_victoria,
)


# =============================================================================
# MODULE-LEVEL STATE (shared between tests)
# =============================================================================

_poweroff_state = {
    "node_name": None,
    "node_ip": None,
    "poweroff_done": False,
    "poweroff_skipped": False,
    "skip_reason": None,
    "workers_ready": False,
}


def _is_service_k8s_enabled(host) -> bool:
    """
    Check if service_k8s is enabled in software_config.json.

    Checks the softwares list for service_k8s entry.
    """
    from automation_library.core import get_input_value, SOFTWARE_CONFIG_FILE
    softwares = get_input_value(host, SOFTWARE_CONFIG_FILE, "softwares")
    if not softwares:
        return False
    for software in softwares:
        if isinstance(software, dict) and software.get("name", "").lower() == "service_k8s":
            return True
    return False


def _check_prerequisites(host, log):
    """
    Check prerequisites for all poweroff tests.
    Returns (can_proceed, admin_ip, skip_reason).
    """
    # Check if service_k8s is enabled in softwares list
    if not _is_service_k8s_enabled(host):
        return False, None, "service_k8s is not enabled in software_config.json"

    admin_ip = get_admin_ip(host, log)

    # Check worker nodes
    workers = get_k8s_worker_nodes(host, admin_ip)
    if len(workers) < 2:
        return False, admin_ip, f"Need at least 2 worker nodes, found {len(workers)}"

    # Check if workers are Ready
    not_ready = [w for w in workers if w["status"] != "Ready"]
    if not_ready:
        return False, admin_ip, f"Worker nodes not Ready: {[w['hostname'] for w in not_ready]}"

    _poweroff_state["workers_ready"] = True
    return True, admin_ip, None


def _skip_if_poweroff_not_done(log):
    """Skip test if poweroff was not performed or was skipped."""
    if _poweroff_state["poweroff_skipped"]:
        reason = _poweroff_state["skip_reason"] or "Poweroff test was skipped"
        log.skipped(reason, "Skipping dependent test")
        pytest.skip(reason)

    if not _poweroff_state["poweroff_done"]:
        log.skipped(
            "Poweroff test was not run",
            "Run test_pods_reschedule_after_node_poweroff first"
        )
        pytest.skip("Poweroff test was not run")


def _skip_if_service_k8s_not_enabled(host, log):
    """Skip test if service_k8s is not enabled."""
    if not _is_service_k8s_enabled(host):
        log.skipped(
            "service_k8s is not enabled in software_config.json",
            "Test requires K8s cluster"
        )
        pytest.skip("service_k8s is not enabled in software_config.json")


# =============================================================================
# TEST CASE 1: POD RESCHEDULE AFTER POWEROFF
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(1)
def test_pods_reschedule_after_node_poweroff(host):
    """
    Test Case 1: Verify telemetry pods reschedule after worker node poweroff.

    This test verifies telemetry resilience by:
    1. Check if service_k8s is enabled in software_config
    2. Get K8s worker nodes from kubectl
    3. Skip if less than 2 worker nodes (need spare capacity)
    4. Select node with most telemetry pods for poweroff
    5. Power off the selected worker node
    6. Wait for node to go down (NotReady status)
    7. Wait for pods to reschedule to other nodes (with progress bar)
    8. Verify all pods are running on remaining nodes

    Note: Manual power-on of the node is required after test.
    """
    log = TestLogger("Verify telemetry pods reschedule after node poweroff")

    # Check prerequisites
    can_proceed, admin_ip, skip_reason = _check_prerequisites(host, log)

    if not can_proceed:
        _poweroff_state["poweroff_skipped"] = True
        _poweroff_state["skip_reason"] = skip_reason
        log.skipped(skip_reason, "Prerequisites not met")
        pytest.skip(skip_reason)

    # Get worker nodes
    log.check("Getting K8s worker nodes")
    workers = get_k8s_worker_nodes(host, admin_ip)

    # Display worker nodes with hostname and IP
    log.check(f"Found {len(workers)} worker nodes:")
    for w in workers:
        log.check(f"  {w['hostname']} ({w['ip']}) - {w['status']}")

    # Select target node (node with most pods)
    log.check("Selecting target node for poweroff (node with most telemetry pods)")
    selection = select_target_node_for_poweroff(host, admin_ip, workers)

    target_worker = selection["selected"]
    target_hostname = target_worker["hostname"]
    target_ip = target_worker["ip"]

    # Display pod distribution across nodes
    log.check("Pod distribution across worker nodes:")
    for hostname, info in selection["pod_counts"].items():
        log.check(f"  {hostname}: {info['count']} pods")

    log.check(f"Selected: {target_hostname} ({target_ip}) - {selection['reason']}")

    _poweroff_state["node_name"] = target_hostname
    _poweroff_state["node_ip"] = target_ip

    # Get ALL pods in telemetry namespace before poweroff
    log.check("Listing all pods in telemetry namespace before poweroff:")
    all_pods_before = get_all_telemetry_pods(host, admin_ip)
    log.check(f"Total pods: {len(all_pods_before)}")
    for pod in all_pods_before:
        log.check(f"  {pod['name']:<45} {pod['status']:<12} {pod['node']}")

    # Get pods on target node
    original_pods = get_telemetry_pods_on_node(host, admin_ip, target_hostname)

    if not original_pods:
        _poweroff_state["poweroff_skipped"] = True
        _poweroff_state["skip_reason"] = f"No telemetry pods on {target_hostname}"
        log.skipped(f"No telemetry pods on {target_hostname}", "Nothing to reschedule")
        pytest.skip(f"No telemetry pods on {target_hostname}")

    log.check(f"Pods on target node {target_hostname} ({len(original_pods)} pods):")
    for pod in original_pods:
        log.check(f"  {pod['name']:<45} {pod['status']}")

    # Power off the node
    log.check(f"Powering off node: {target_hostname} ({target_ip})")
    poweroff_result = poweroff_node(host, admin_ip, target_ip)

    if not poweroff_result["success"]:
        _poweroff_state["poweroff_skipped"] = True
        _poweroff_state["skip_reason"] = f"Failed to power off: {poweroff_result.get('error')}"
        log.failed(f"Failed to power off {target_hostname}", poweroff_result.get("error", ""))
        assert False, f"Failed to power off node: {poweroff_result.get('error')}"

    _poweroff_state["poweroff_done"] = True

    # Wait for node to go down
    log.check(f"Waiting for node {target_hostname} to go down (max {NODE_POWEROFF_WAIT_SECONDS}s)")
    node_down = wait_for_node_down(host, admin_ip, target_hostname, NODE_POWEROFF_WAIT_SECONDS)

    if node_down["success"]:
        log.check(f"Node {target_hostname} is now {node_down['status']} (took {node_down['elapsed_seconds']}s)")
    else:
        log.check(f"Warning: Node {target_hostname} may still be Ready, continuing with pod reschedule check")

    # Wait for pods to reschedule with progress bar
    log.check("Waiting for pods to reschedule to other nodes:")
    reschedule_result = wait_for_pods_reschedule(host, admin_ip, target_hostname, original_pods)

    # Verify ALL pods in telemetry namespace are running
    log.check("Verifying all pods in telemetry namespace are running")
    running_result = verify_all_telemetry_pods_running(host, admin_ip)

    # List all pods after poweroff with their new locations
    log.check("All telemetry pods after poweroff:")
    if running_result.get("output"):
        for line in running_result["output"].strip().split('\n'):
            log.check(f"  {line}")

    # Build details for final report
    details_lines = [
        f"Target node: {target_hostname} ({target_ip})",
        f"Original pods on target: {len(original_pods)}",
        f"Total pods in namespace: {running_result['total_pods']}",
        "",
        "Reschedule Results:",
        reschedule_result["details"],
        "",
        f"Final: {running_result['running_count']} running, {running_result['not_running_count']} not running",
    ]

    if running_result["not_running_pods"]:
        details_lines.append("Not running pods:")
        for pod in running_result["not_running_pods"]:
            details_lines.append(f"  {pod['name']}: {pod['status']}")

    details = "\n".join(details_lines)
    success = reschedule_result["success"] and running_result["success"]

    if success:
        log.passed(f"All {len(original_pods)} pods rescheduled successfully", details)
    else:
        error_msg = reschedule_result.get("error") or running_result.get("error")
        log.failed(f"Pod rescheduling failed: {error_msg}", details)

    # Reminder to power on the node
    log.check("")
    log.check("=" * 60)
    log.check(f"IMPORTANT: Node {target_hostname} ({target_ip}) is powered off.")
    log.check("Please power on the node manually before running this test again.")
    log.check("=" * 60)

    assert success, (
        f"Pod rescheduling failed after powering off {target_hostname}: "
        f"{reschedule_result.get('error') or running_result.get('error')}"
    )


# =============================================================================
# IDRAC TELEMETRY TEST CASES (after poweroff)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(2)
def test_idrac_telemetry_pod_count(host):
    """
    Test Case 2: Verify idrac-telemetry pods count matches expected after poweroff.
    """
    log = TestLogger(TEST_NAMES["idrac_telemetry_pod_count"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    admin_ip = get_admin_ip(host, log)

    log.check(f"Checking idrac-telemetry pods on {admin_ip}")
    result = verify_idrac_telemetry_pod_count(host, admin_ip)

    details = (
        f"service_kube_node count: {result['service_kube_node_count']}\n"
        f"service_kube_nodes with children: {result['service_kube_nodes_with_children']}\n"
        f"Expected pods: {result['expected_count']}\n"
        f"Actual pods: {result['actual_count']}\n"
        f"Pods: {result['pods']}"
    )

    if result["success"]:
        log.passed(LOG_MSGS["idrac_pod_count_match"].format(expected=result['expected_count']), details)
    else:
        log.failed(LOG_MSGS["idrac_pod_count_mismatch"], details)

    assert result["success"], ASSERT_MSGS["idrac_pod_count_mismatch"].format(
        expected=result['expected_count'],
        actual=result['actual_count'],
        svc_count=result['service_kube_node_count']
    )


@pytest.mark.negative
@pytest.mark.order(3)
def test_mysql_data_in_idrac_telemetry_pods(host):
    """
    Test Case 3: Verify MySQL data in idrac-telemetry pods after poweroff.
    """
    log = TestLogger(TEST_NAMES["mysql_data_in_pods"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    admin_ip = get_admin_ip(host, log)

    if not has_activated_ips(host):
        log.skipped("No activated IPs found in telemetry report", "Test skipped")
        pytest.skip("No activated IPs found in telemetry report")

    log.check("Decrypting MySQL credentials and verifying data in pods")
    result = verify_mysql_data_in_pods(host, admin_ip)

    if result.get("error") and not result.get("pod_results"):
        log.failed(LOG_MSGS["mysql_creds_failed"], result["error"])
        assert False, result["error"]

    details_lines = [
        LOG_MSGS["mysql_creds_decrypted"],
        f"Activated IPs: {result.get('activated_ips', [])}",
    ]

    all_success = True
    for pod_result in result.get("pod_results", []):
        pod_name = pod_result["pod_name"]
        expected = pod_result["expected_ips"]
        actual = pod_result["actual_ips"]
        missing = pod_result["missing_ips"]

        details_lines.append("")
        details_lines.append(f"Pod: {pod_name}")
        details_lines.append(f"  Expected IPs: {expected}")
        details_lines.append(f"  Actual IPs  : {actual}")

        if pod_result["success"]:
            details_lines.append(f"  \u2713 {LOG_MSGS['mysql_pod_verified'].format(pod_name=pod_name)}")
        else:
            details_lines.append(f"  \u2717 {LOG_MSGS['mysql_pod_missing_ips'].format(pod_name=pod_name, missing=missing)}")
            all_success = False

    details = "\n".join(details_lines)

    if all_success:
        log.passed(LOG_MSGS["mysql_all_pods_verified"], details)
    else:
        failed_pod = next((p for p in result.get("pod_results", []) if not p["success"]), None)
        log.failed(result.get("error", "MySQL data missing"), details)
        if failed_pod:
            assert False, ASSERT_MSGS["mysql_data_missing"].format(
                pod_name=failed_pod["pod_name"],
                expected=failed_pod["expected_ips"],
                actual=failed_pod["actual_ips"],
                missing=failed_pod["missing_ips"]
            )


@pytest.mark.negative
@pytest.mark.order(4)
def test_receiver_collecting_metrics(host):
    """
    Test Case 4: Verify idrac-telemetry-receiver is collecting metrics after poweroff.
    """
    log = TestLogger(TEST_NAMES["receiver_collecting_metrics"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    admin_ip = get_admin_ip(host, log)

    if not has_activated_ips(host):
        log.skipped("No activated IPs found in telemetry report", "Test skipped")
        pytest.skip("No activated IPs found in telemetry report")

    log.check("Checking idrac-telemetry-receiver logs for metrics collection")
    result = verify_receiver_collecting_metrics(host, admin_ip)

    if result.get("error") and not result.get("pod_results"):
        log.failed("Failed to verify receiver logs", result["error"])
        assert False, result["error"]

    details_lines = []
    all_success = True
    for pod_result in result.get("pod_results", []):
        details_lines.append(f"Pod: {pod_result['pod_name']}")
        details_lines.append(f"  MySQL IPs: {pod_result['mysql_ips']}")
        if not pod_result["success"]:
            all_success = False
        details_lines.append("")

    details = "\n".join(details_lines)

    if all_success:
        log.passed(LOG_MSGS["receiver_all_collecting"], details)
    else:
        failed_pod = next((p for p in result.get("pod_results", []) if not p["success"]), None)
        log.failed(result.get("error", "Receiver not collecting"), details)
        if failed_pod:
            assert False, ASSERT_MSGS["receiver_not_collecting"].format(
                pod_name=failed_pod["pod_name"],
                mysql_ips=failed_pod["mysql_ips"],
                service_tags=[r.get("service_tag", "") for r in failed_pod.get("ip_results", [])]
            )


# =============================================================================
# KAFKA TEST CASES (after poweroff)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(5)
def test_ldms_pods_running(host):
    """
    Test Case 5: Verify LDMS pods are running after poweroff.
    """
    log = TestLogger(TEST_NAMES.get("ldms_pods_running", "Verify LDMS pods running") + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_ldms_enabled(host):
        log.skipped("LDMS is not enabled", "Test skipped")
        pytest.skip("LDMS is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying LDMS pods are running in telemetry namespace")
    result = verify_ldms_pods_running(host, admin_ip)

    if result.get("skipped"):
        pytest.skip(result.get("reason", "LDMS not enabled"))

    details_lines = []
    for pod_result in result.get("pod_results", []):
        status = "\u2713" if pod_result["running"] else "\u2717"
        details_lines.append(f"{status} Pod '{pod_result['pod']}': {pod_result['phase']}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("All LDMS pods are running", details)
    else:
        errors = result.get("errors", [])
        log.failed("LDMS pods verification failed", details + "\n" + "; ".join(errors))
        assert False, f"LDMS pods not running: {'; '.join(errors)}"


@pytest.mark.negative
@pytest.mark.order(6)
def test_ldms_services_ports(host):
    """
    Test Case 6: Verify LDMS services ports match telemetry_config.yml after poweroff.
    """
    log = TestLogger(TEST_NAMES.get("ldms_services_ports", "Verify LDMS services ports") + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_ldms_enabled(host):
        log.skipped("LDMS is not enabled", "Test skipped")
        pytest.skip("LDMS is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying LDMS services ports match telemetry_config.yml")
    result = verify_ldms_services_ports(host, admin_ip)

    if result.get("skipped"):
        pytest.skip(result.get("reason", "LDMS not enabled"))

    if result.get("error"):
        log.failed("Failed to get LDMS services", result["error"])
        assert False, result["error"]

    expected = result.get("expected_config", {})
    details_lines = [
        f"Expected ldms_agg_port: {expected.get('ldms_agg_port')}",
        f"Expected ldms_store_port: {expected.get('ldms_store_port')}",
    ]

    for svc_result in result.get("service_results", []):
        status = "\u2713" if svc_result["match"] else "\u2717"
        details_lines.append(
            f"{status} Service '{svc_result['service']}': "
            f"expected={svc_result['expected_port']}, actual={svc_result['actual_port']}"
        )

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("All LDMS services ports match", details)
    else:
        errors = result.get("errors", [])
        log.failed("LDMS services port mismatch", details + "\n" + "; ".join(errors))
        assert False, f"LDMS services port mismatch: {'; '.join(errors)}"


@pytest.mark.negative
@pytest.mark.order(7)
def test_kafka_topics(host):
    """
    Test Case 7: Verify Kafka topics via REST proxy after poweroff.
    """
    log = TestLogger(TEST_NAMES["kafka_topics_verification"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    admin_ip = get_admin_ip(host, log)

    log.check("Getting Kafka topics via REST proxy")
    result = verify_kafka_topics_via_rest(host, admin_ip)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", "Kafka not enabled"), "Test skipped")
        pytest.skip(result.get("skip_reason", "Kafka not enabled"))

    if result.get("error") and not result.get("topics"):
        log.failed("Failed to get topics via REST proxy", result["error"])
        assert False, result["error"]

    details_lines = [
        f"Kafka bridge IP: {result.get('bridge_ip', '')}",
        f"Topics found: {result.get('topics', [])}",
    ]
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("All Kafka topic checks passed", details)
    else:
        errors = result.get("errors", [])
        log.failed("Kafka topic verification failed", details + "\n" + "; ".join(errors))
        assert False, "; ".join(errors)


@pytest.mark.negative
@pytest.mark.order(8)
def test_kafka_config_match(host):
    """
    Test Case 8: Verify Kafka configurations match telemetry_config.yml after poweroff.
    """
    log = TestLogger(TEST_NAMES["kafka_config_match"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_kafka_enabled(host):
        log.skipped("Kafka is not enabled", "Test skipped")
        pytest.skip("Kafka is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Checking Kafka config inside broker pod vs telemetry_config.yml")
    result = verify_kafka_config_match(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to get Kafka config", result["error"])
        assert False, result["error"]

    expected = result.get("expected_config", {})
    actual = result.get("actual_config", {})

    details_lines = [
        f"log_retention_hours: expected={expected.get('log_retention_hours')}, actual={actual.get('log.retention.hours')}",
        f"log_retention_bytes: expected={expected.get('log_retention_bytes')}, actual={actual.get('log.retention.bytes')}",
        f"log_segment_bytes: expected={expected.get('log_segment_bytes')}, actual={actual.get('log.segment.bytes')}",
    ]
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(LOG_MSGS["kafka_config_match"], details)
    else:
        mismatches = result.get("mismatches", [])
        mismatch_str = "\n".join([f"  \u2717 {m['config']}: expected {m['expected']}, actual {m['actual']}" for m in mismatches])
        log.failed("Kafka configuration mismatch", details + "\n\nMismatches:\n" + mismatch_str)
        assert False, ASSERT_MSGS["kafka_config_mismatch"].format(mismatches=mismatch_str)


@pytest.mark.negative
@pytest.mark.order(9)
def test_idrac_data_in_kafka_topic(host):
    """
    Test Case 9: Verify iDRAC telemetry data in Kafka topic after poweroff.
    """
    log = TestLogger(TEST_NAMES.get("kafka_idrac_data", "Verify iDRAC data in Kafka") + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_kafka_enabled(host):
        log.skipped("Kafka is not enabled", "Test skipped")
        pytest.skip("Kafka is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying iDRAC telemetry data in Kafka topic")
    result = verify_idrac_data_in_kafka(host, admin_ip, timeout_seconds=30)

    if result.get("skipped"):
        log.skipped(result.get("reason", ""), "Test skipped")
        pytest.skip(result.get("reason", ""))

    if result.get("error") and not result.get("service_tag_results"):
        log.failed("Failed to verify iDRAC data in Kafka", result["error"])
        assert False, result["error"]

    details_lines = [f"Kafka bridge IP: {result.get('bridge_ip', '')}"]
    details = "\n".join(details_lines)

    if result["success"]:
        found_count = len(result.get("found_tags", []))
        log.passed(f"iDRAC data found for all {found_count} service tags", details)
    else:
        missing = result.get("missing_tags", [])
        log.failed(f"iDRAC data missing for {len(missing)} service tags", details)
        assert False, result.get("error", "iDRAC data missing")


@pytest.mark.negative
@pytest.mark.order(10)
def test_ldms_latest_data_in_kafka(host):
    """
    Test Case 10: Verify LDMS latest data in Kafka topic after poweroff.
    """
    log = TestLogger(TEST_NAMES.get("ldms_latest_data", "Verify LDMS data in Kafka") + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_ldms_enabled(host):
        log.skipped("LDMS is not enabled", "Test skipped")
        pytest.skip("LDMS is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying latest LDMS data in Kafka topic")
    result = verify_ldms_data_in_kafka(host, admin_ip, timeout_seconds=30)

    if result.get("skipped"):
        log.skipped(result.get("reason", "LDMS not enabled"), "Test skipped")
        pytest.skip(result.get("reason", "LDMS not enabled"))

    expected_count = result.get("expected_instance_count", 0)
    found_count = result.get("found_instance_count", 0)
    details = f"Expected instances: {expected_count}, Found: {found_count}"

    if result["success"]:
        log.passed(f"LDMS latest data verified for all {len(result.get('found_hostnames', []))} hostnames", details)
    else:
        missing_hosts = result.get("missing_hostnames", [])
        log.failed(f"LDMS data missing from {len(missing_hosts)} hostnames", details)
        assert False, f"LDMS data missing: {missing_hosts}"


# =============================================================================
# VICTORIAMETRICS TEST CASES (after poweroff)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(11)
def test_victoria_enabled(host):
    """
    Test Case 11: Verify VictoriaMetrics is enabled after poweroff.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_enabled"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_idrac_telemetry_enabled(host):
        log.skipped("iDRAC telemetry is not enabled", "Test skipped")
        pytest.skip("iDRAC telemetry is not enabled")

    if not is_victoria_enabled(host):
        log.skipped(VICTORIA_LOG_MSGS["victoria_not_enabled"], "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    deployment_mode = get_deployment_mode(host)
    victoria_config = get_victoria_config(host)

    mode_msg = (
        VICTORIA_LOG_MSGS["deployment_mode_single"]
        if deployment_mode == DEPLOYMENT_MODE_SINGLE
        else VICTORIA_LOG_MSGS["deployment_mode_cluster"]
    )
    details = (
        f"{mode_msg}\n"
        f"persistence_size: {victoria_config.get('persistence_size', 'N/A')}\n"
        f"retention_period: {victoria_config.get('retention_period', 'N/A')}"
    )

    log.passed(VICTORIA_LOG_MSGS["victoria_enabled"], details)


@pytest.mark.negative
@pytest.mark.order(12)
def test_victoria_persistence_size(host):
    """
    Test Case 12: Verify VictoriaMetrics persistence size matches config after poweroff.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_persistence_size"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VictoriaMetrics PVC storage size")
    result = verify_victoria_persistence_size(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify persistence size", result["error"])
        assert False, result["error"]

    deployment_mode = result.get("deployment_mode", "")
    expected_size = result.get("expected_size", "")
    details_lines = [f"Deployment mode: {deployment_mode}", f"Expected size: {expected_size}"]

    for pvc_result in result.get("pvc_results", []):
        status = "\u2713" if pvc_result["match"] else "\u2717"
        details_lines.append(f"{status} PVC '{pvc_result['pvc_name']}': {pvc_result['actual_size']}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOG_MSGS["persistence_size_match"].format(size=expected_size), details)
    else:
        log.failed(VICTORIA_LOG_MSGS["persistence_size_mismatch"], details)
        assert False, "Persistence size mismatch"


@pytest.mark.negative
@pytest.mark.order(13)
def test_victoria_pods(host):
    """
    Test Case 13: Verify VictoriaMetrics pods are running after poweroff.
    """
    log = TestLogger("Verify VictoriaMetrics pods (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)
    deployment_mode = get_deployment_mode(host)

    log.check(f"Verifying VictoriaMetrics pods (mode: {deployment_mode})")

    if deployment_mode == DEPLOYMENT_MODE_SINGLE:
        result = verify_victoria_single_node_pods(host, admin_ip)
    elif deployment_mode == DEPLOYMENT_MODE_CLUSTER:
        result = verify_victoria_cluster_pods(host, admin_ip)
    else:
        log.skipped(f"Unknown deployment mode: {deployment_mode}", "Test skipped")
        pytest.skip(f"Unknown deployment mode: {deployment_mode}")

    if result.get("skip"):
        log.skipped(result.get("skip_reason", ""), "Test skipped")
        pytest.skip(result.get("skip_reason", ""))

    if result.get("error"):
        log.failed("Failed to verify pods", result["error"])
        assert False, result["error"]

    details_lines = []
    for pod_result in result.get("pod_results", []):
        status = "\u2713" if pod_result["running"] else "\u2717"
        details_lines.append(f"{status} Pod '{pod_result['pod']}': {pod_result['phase']}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOG_MSGS["all_pods_running"].format(component=deployment_mode, count=len(result.get("pod_results", []))), details)
    else:
        errors = result.get("errors", [])
        log.failed(VICTORIA_LOG_MSGS["pods_not_running"].format(component=deployment_mode), details + "\n" + "; ".join(errors))
        assert False, "; ".join(errors)


@pytest.mark.negative
@pytest.mark.order(14)
def test_vmagent_pod_running(host):
    """
    Test Case 14: Verify vmagent pod is running after poweroff.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["vmagent_pod_running"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying vmagent pod")
    result = verify_vmagent_pod(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify vmagent pod", result["error"])
        assert False, result["error"]

    details_lines = []
    for pod_result in result.get("pod_results", []):
        status = "\u2713" if pod_result["running"] else "\u2717"
        details_lines.append(f"{status} Pod '{pod_result['pod']}': {pod_result['phase']}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOG_MSGS["all_pods_running"].format(component="vmagent", count=len(result.get("pod_results", []))), details)
    else:
        errors = result.get("errors", [])
        log.failed(VICTORIA_LOG_MSGS["pods_not_running"].format(component="vmagent"), details + "\n" + "; ".join(errors))
        assert False, VICTORIA_ASSERT_MSGS["vmagent_not_running"]


@pytest.mark.negative
@pytest.mark.order(15)
def test_victoria_services(host):
    """
    Test Case 15: Verify VictoriaMetrics services have external IPs after poweroff.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_services"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)
    deployment_mode = get_deployment_mode(host)

    log.check(f"Verifying VictoriaMetrics services (mode: {deployment_mode})")
    result = verify_victoria_services(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify services", result["error"])
        assert False, result["error"]

    details_lines = []
    for svc_result in result.get("service_results", []):
        service = svc_result["service"]
        external_ip = svc_result.get("external_ip", "")
        port = svc_result["port"]
        has_ip = svc_result["has_external_ip"]
        status = "\u2713" if has_ip else "\u2717"

        if has_ip:
            details_lines.append(f"{status} Service '{service}': {external_ip}:{port}")
        else:
            details_lines.append(f"{status} Service '{service}': NO EXTERNAL IP")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOG_MSGS["all_services_ready"], details)
    else:
        errors = result.get("errors", [])
        log.failed("VictoriaMetrics services not ready", details + "\n" + "; ".join(errors))
        assert False, "; ".join(errors)


@pytest.mark.negative
@pytest.mark.order(16)
def test_victoria_tls_secret(host):
    """
    Test Case 16: Verify VictoriaMetrics TLS secret exists after poweroff.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_tls_secret"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check(f"Verifying TLS secret '{VICTORIA_TLS_SECRET}'")
    result = verify_victoria_tls_secret(host, admin_ip)

    if not result.get("secret_exists", False):
        log.failed(
            VICTORIA_LOG_MSGS["tls_secret_missing"].format(secret=VICTORIA_TLS_SECRET),
            result.get("error", "")
        )
        assert False, VICTORIA_ASSERT_MSGS["tls_secret_missing"].format(secret=VICTORIA_TLS_SECRET)

    keys_found = result.get("keys_found", [])
    missing_keys = result.get("missing_keys", [])
    details_lines = [f"Keys found: {keys_found}"]
    if missing_keys:
        details_lines.append(f"Missing keys: {missing_keys}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(VICTORIA_LOG_MSGS["tls_secret_exists"].format(secret=VICTORIA_TLS_SECRET), details)
    else:
        log.failed(VICTORIA_LOG_MSGS["tls_secret_missing_keys"].format(keys=missing_keys), details)
        assert False, VICTORIA_ASSERT_MSGS["tls_secret_missing_keys"].format(
            secret=VICTORIA_TLS_SECRET,
            missing_keys=missing_keys
        )


@pytest.mark.negative
@pytest.mark.order(17)
def test_victoria_tls_health(host):
    """
    Test Case 17: Verify TLS connection and health endpoint after poweroff.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_tls_health"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)
    deployment_mode = get_deployment_mode(host)

    log.check(f"Verifying TLS connection (mode: {deployment_mode})")
    result = verify_victoria_tls_health(host, admin_ip)

    if result.get("error"):
        log.failed(VICTORIA_LOG_MSGS["tls_connection_failed"], result["error"])
        assert False, VICTORIA_ASSERT_MSGS["tls_connection_failed"].format(
            host=result.get("external_ip", ""),
            port=result.get("port", ""),
            error=result.get("error", "")
        )

    external_ip = result.get("external_ip", "")
    port = result.get("port", "")
    health_response = result.get("health_response", "")

    details = (
        f"Service: {result.get('service_name', '')}\n"
        f"URL: https://{external_ip}:{port}/health\n"
        f"TLS connected: {result.get('tls_connected', False)}\n"
        f"Health response: {health_response}"
    )

    if result["success"]:
        log.passed(VICTORIA_LOG_MSGS["tls_connection_success"], details)
    else:
        log.failed(VICTORIA_LOG_MSGS["health_endpoint_failed"], details)
        assert False, VICTORIA_ASSERT_MSGS["health_check_failed"].format(
            host=external_ip,
            port=port,
            response=health_response
        )


@pytest.mark.negative
@pytest.mark.order(18)
def test_victoria_idrac_data(host):
    """
    Test Case 18: Verify iDRAC telemetry data in VictoriaMetrics after poweroff.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_idrac_data"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)

    activated_tags = get_activated_service_tags(host, admin_ip)
    if not activated_tags:
        log.skipped("No activated service tags found in telemetry report", "Test skipped")
        pytest.skip("No activated service tags found in telemetry report")

    log.check(VICTORIA_LOG_MSGS["idrac_data_verifying"])
    result = verify_victoria_idrac_data(host, admin_ip)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", ""), "Test skipped")
        pytest.skip(result.get("skip_reason", ""))

    if result.get("error"):
        log.failed("Failed to verify iDRAC data", result["error"])
        assert False, result["error"]

    # Build detailed output like sanity tests
    details_lines = [
        f"Activated service tags: {activated_tags}",
        f"VictoriaMetrics URL: https://{result.get('external_ip')}:{result.get('port')}",
        "",
        "Service tag verification:",
    ]

    for tag_result in result.get("service_tag_results", []):
        stag = tag_result["service_tag"]
        if tag_result["found"]:
            details_lines.append(f"  ✓ {stag}")
            details_lines.append(f"      Metrics     : {tag_result['metric_count']} found")
            latest_ts = tag_result.get("latest_timestamp", 0)
            if latest_ts:
                from datetime import datetime
                try:
                    human_ts = datetime.fromtimestamp(int(latest_ts)).strftime("%Y-%m-%d %H:%M:%S")
                    details_lines.append(f"      VM Time     : {latest_ts} ({human_ts})")
                except (ValueError, OSError):
                    details_lines.append(f"      VM Time     : {latest_ts}")
            for sample in tag_result.get("sample_metrics", []):
                details_lines.append(f"        - {sample['metric_name']}: {sample['value']}")
        else:
            details_lines.append(f"  ✗ {stag}: NO DATA FOUND")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            VICTORIA_LOG_MSGS["idrac_data_all_found"].format(count=len(result.get("found_tags", []))),
            details
        )
    else:
        log.failed(
            f"iDRAC data missing for {len(result.get('missing_tags', []))} service tags",
            details
        )
        assert False, VICTORIA_ASSERT_MSGS["idrac_data_missing"].format(
            missing=result.get("missing_tags", []),
            found=result.get("found_tags", [])
        )


# =============================================================================
# DELETE NODE TEST CASES (after poweroff)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(19)
def test_idrac_deleted_node_data_in_mysql_after_poweroff(host):
    """
    Test Case 19: Verify deleted node BMC IPs not in MySQL after poweroff.
    """
    log = TestLogger(DELETE_NODE_TEST_NAMES["idrac_deleted_node_mysql"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    deleted_nodes_info = get_deleted_nodes_cached(host)
    skip_if_no_deleted_nodes(deleted_nodes_info, log)

    if not is_idrac_telemetry_enabled(host):
        log.skipped("iDRAC telemetry not enabled", "Test skipped")
        pytest.skip("iDRAC telemetry not enabled")

    admin_ip = get_admin_ip(host, log)
    deleted_entries = deleted_nodes_info.get("deleted_entries", [])
    deleted_ips = get_deleted_bmc_ips(deleted_entries)

    if not deleted_ips:
        log.skipped("No deleted nodes with BMC IPs", "Test skipped")
        pytest.skip("No deleted nodes with BMC IPs")

    log.check(f"Verifying {len(deleted_ips)} deleted BMC IPs not in MySQL")
    result = verify_idrac_deleted_node_in_mysql(host, admin_ip, deleted_ips)

    if result.get("error"):
        log.failed("Failed to verify deleted nodes in MySQL", result["error"])
        assert False, result["error"]

    details_lines = [f"Deleted BMC IPs: {deleted_ips}"]
    for ip_result in result.get("ip_results", []):
        status = "✓" if not ip_result["found"] else "✗"
        details_lines.append(f"  {status} {ip_result['bmc_ip']}: {'not found' if not ip_result['found'] else 'FOUND'}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("Deleted node BMC IPs not found in MySQL", details)
    else:
        log.failed("Deleted node BMC IPs still in MySQL", details)

    assert result["success"], "Deleted node BMC IPs still found in MySQL"


@pytest.mark.negative
@pytest.mark.order(20)
def test_idrac_deleted_node_data_in_kafka_after_poweroff(host):
    """
    Test Case 20: Verify deleted iDRAC node data not in Kafka after poweroff.
    """
    log = TestLogger(DELETE_NODE_TEST_NAMES["idrac_deleted_node_kafka"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_kafka_enabled(host):
        log.skipped("Kafka is not enabled", "Test skipped")
        pytest.skip("Kafka is not enabled")

    deleted_nodes_info = get_deleted_nodes_cached(host)
    skip_if_no_deleted_nodes(deleted_nodes_info, log)

    admin_ip = get_admin_ip(host, log)
    deleted_entries = deleted_nodes_info.get("deleted_entries", [])
    deleted_tags = get_deleted_service_tags(deleted_entries)

    if not deleted_tags:
        log.skipped("No deleted nodes with service tags", "Test skipped")
        pytest.skip("No deleted nodes with service tags")

    log.check(f"Verifying {len(deleted_tags)} deleted service tags not in Kafka")
    result = verify_idrac_deleted_node_in_kafka(host, admin_ip, deleted_tags, timeout_seconds=30)

    if result.get("error"):
        log.failed("Failed to verify deleted nodes in Kafka", result["error"])
        assert False, result["error"]

    details_lines = [f"Deleted service tags: {deleted_tags}"]
    for tr in result.get("tag_results", []):
        status = "✓" if not tr["found_in_latest"] else "✗"
        details_lines.append(f"  {status} {tr['service_tag']}: {'not found' if not tr['found_in_latest'] else 'FOUND'}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("Deleted node service tags not found in Kafka", details)
    else:
        log.failed("Deleted node service tags still in Kafka", details)

    assert result["success"], "Deleted node service tags still found in Kafka"


@pytest.mark.negative
@pytest.mark.order(21)
def test_ldms_deleted_node_data_in_kafka_after_poweroff(host):
    """
    Test Case 21: Verify deleted LDMS node data not in Kafka after poweroff.
    """
    log = TestLogger(DELETE_NODE_TEST_NAMES["ldms_deleted_node_kafka"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_ldms_enabled(host):
        log.skipped("LDMS is not enabled", "Test skipped")
        pytest.skip("LDMS is not enabled")

    deleted_nodes_info = get_deleted_nodes_cached(host)
    skip_if_no_deleted_nodes(deleted_nodes_info, log)

    admin_ip = get_admin_ip(host, log)
    deleted_entries = deleted_nodes_info.get("deleted_entries", [])
    deleted_hostnames = get_deleted_ldms_hostnames(deleted_entries)

    if not deleted_hostnames:
        log.skipped("No deleted LDMS nodes", "Test skipped")
        pytest.skip("No deleted LDMS nodes")

    log.check(f"Verifying {len(deleted_hostnames)} deleted hostnames not in Kafka")
    result = verify_ldms_deleted_node_in_kafka(host, admin_ip, deleted_hostnames, timeout_seconds=30)

    if result.get("error"):
        log.failed("Failed to verify deleted LDMS nodes in Kafka", result["error"])
        assert False, result["error"]

    details_lines = [f"Deleted hostnames: {deleted_hostnames}"]
    for hr in result.get("hostname_results", []):
        status = "✓" if not hr["found_in_latest"] else "✗"
        details_lines.append(f"  {status} {hr['hostname']}: {'not found' if not hr['found_in_latest'] else 'FOUND'}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("Deleted LDMS hostnames not found in Kafka", details)
    else:
        log.failed("Deleted LDMS hostnames still in Kafka", details)

    assert result["success"], "Deleted LDMS hostnames still found in Kafka"


@pytest.mark.negative
@pytest.mark.order(22)
def test_idrac_deleted_node_data_in_victoria_after_poweroff(host):
    """
    Test Case 22: Verify deleted iDRAC node data not in VictoriaMetrics after poweroff.
    """
    log = TestLogger(DELETE_NODE_TEST_NAMES["idrac_deleted_node_victoria"] + " (after poweroff)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_poweroff_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    deleted_nodes_info = get_deleted_nodes_cached(host)
    skip_if_no_deleted_nodes(deleted_nodes_info, log)

    admin_ip = get_admin_ip(host, log)
    deleted_entries = deleted_nodes_info.get("deleted_entries", [])
    deleted_tags = get_deleted_service_tags(deleted_entries)

    if not deleted_tags:
        log.skipped("No deleted nodes with service tags", "Test skipped")
        pytest.skip("No deleted nodes with service tags")

    log.check(f"Verifying {len(deleted_tags)} deleted service tags not in VictoriaMetrics")
    result = verify_idrac_deleted_node_in_victoria(host, admin_ip, deleted_tags)

    if result.get("error"):
        log.failed("Failed to verify deleted nodes in VictoriaMetrics", result["error"])
        assert False, result["error"]

    details_lines = [f"Deleted service tags: {deleted_tags}"]
    for tr in result.get("tag_results", []):
        status = "✓" if not tr["found"] else "✗"
        details_lines.append(f"  {status} {tr['service_tag']}: {'not found' if not tr['found'] else 'FOUND'}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("Deleted node service tags not found in VictoriaMetrics", details)
    else:
        log.failed("Deleted node service tags still in VictoriaMetrics", details)

    assert result["success"], "Deleted node service tags still found in VictoriaMetrics"
