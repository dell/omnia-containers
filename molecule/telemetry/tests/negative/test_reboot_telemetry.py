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
Telemetry Reboot Negative Test Cases.

Tests telemetry pod resilience when a K8s worker node is rebooted.
Verifies that the node comes back online, cloud-init completes, node rejoins
the cluster, and all telemetry pods are running.

Skip Logic:
- If service_k8s is not enabled -> ALL tests skip
- If less than 1 worker node -> ALL tests skip
- If reboot test (test case 1) skips or fails -> ALL subsequent tests skip

Test cases (mirrors sanity tests after reboot):
1. Verify telemetry pods after worker node reboot
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
    reboot_node,
    wait_for_node_down,
    wait_for_node_online,
    wait_for_cloudinit_done,
    wait_for_node_rejoin_cluster,
    get_telemetry_pods_on_node,
    get_all_telemetry_pods,
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
from automation_library.telemetry.vars import (
    NODE_REBOOT_WAIT_SECONDS,
    NODE_ONLINE_TIMEOUT_SECONDS,
)
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

_reboot_state = {
    "node_name": None,
    "node_ip": None,
    "reboot_done": False,
    "reboot_skipped": False,
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
    Check prerequisites for all reboot tests.
    Returns (can_proceed, admin_ip, skip_reason).
    
    For reboot test, we only need at least 1 Ready worker node.
    """
    # Check if service_k8s is enabled in softwares list
    if not _is_service_k8s_enabled(host):
        return False, None, "service_k8s is not enabled in software_config.json"

    admin_ip = get_admin_ip(host, log)

    # Check worker nodes - need at least 1 Ready worker for reboot test
    workers = get_k8s_worker_nodes(host, admin_ip)
    if len(workers) < 1:
        return False, admin_ip, f"Need at least 1 worker node, found {len(workers)}"

    # Check if at least 1 worker is Ready (not all workers need to be Ready)
    ready_workers = [w for w in workers if w["status"] == "Ready"]
    if len(ready_workers) < 1:
        not_ready = [w for w in workers if w["status"] != "Ready"]
        return False, admin_ip, f"No Ready worker nodes found. Not Ready: {[w['hostname'] for w in not_ready]}"

    _reboot_state["workers_ready"] = True
    return True, admin_ip, None


def _skip_if_reboot_not_done(log):
    """Skip test if reboot was not performed or was skipped."""
    if _reboot_state["reboot_skipped"]:
        reason = _reboot_state["skip_reason"] or "Reboot test was skipped"
        log.skipped(reason, "Skipping dependent test")
        pytest.skip(reason)

    if not _reboot_state["reboot_done"]:
        log.skipped(
            "Reboot test was not run",
            "Run test_telemetry_after_node_reboot first"
        )
        pytest.skip("Reboot test was not run")


def _skip_if_service_k8s_not_enabled(host, log):
    """Skip test if service_k8s is not enabled."""
    if not _is_service_k8s_enabled(host):
        log.skipped(
            "service_k8s is not enabled in software_config.json",
            "Test requires K8s cluster"
        )
        pytest.skip("service_k8s is not enabled in software_config.json")


# =============================================================================
# TEST CASE 1: NODE REBOOT AND RECOVERY
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(20)
def test_telemetry_after_node_reboot(host):
    """
    Test Case 1: Verify telemetry pods after worker node reboot.

    This test verifies telemetry resilience by:
    1. Check if service_k8s is enabled in software_config
    2. Get K8s worker nodes from kubectl
    3. Skip if no worker nodes available
    4. Select node with most telemetry pods for reboot
    5. Reboot the selected worker node
    6. Wait for node to go down (NotReady status)
    7. Wait for node to come back online (ping + SSH)
    8. Wait for cloud-init to complete
    9. Wait for node to rejoin K8s cluster
    10. Verify all telemetry pods are running
    """
    log = TestLogger("Verify telemetry pods after node reboot")

    # Check prerequisites
    can_proceed, admin_ip, skip_reason = _check_prerequisites(host, log)

    if not can_proceed:
        _reboot_state["reboot_skipped"] = True
        _reboot_state["skip_reason"] = skip_reason
        log.skipped(skip_reason, "Prerequisites not met")
        pytest.skip(skip_reason)

    # Get worker nodes
    log.check("Getting K8s worker nodes")
    workers = get_k8s_worker_nodes(host, admin_ip)
    
    # Display worker nodes with hostname and IP
    log.check(f"Found {len(workers)} worker nodes:")
    for w in workers:
        log.check(f"  {w['hostname']} ({w['ip']}) - {w['status']}")

    # Filter to only Ready workers for reboot target selection
    ready_workers = [w for w in workers if w["status"] == "Ready"]
    log.check(f"Ready workers available for reboot: {len(ready_workers)}")

    # Select target node from Ready workers only (node with most pods)
    log.check("Selecting target node for reboot (Ready node with most telemetry pods)")
    selection = select_target_node_for_poweroff(host, admin_ip, ready_workers)
    
    target_worker = selection["selected"]
    target_hostname = target_worker["hostname"]
    target_ip = target_worker["ip"]
    
    # Display pod distribution across nodes
    log.check("Pod distribution across worker nodes:")
    for hostname, info in selection["pod_counts"].items():
        log.check(f"  {hostname}: {info['count']} pods")
    
    log.check(f"Selected: {target_hostname} ({target_ip}) - {selection['reason']}")

    _reboot_state["node_name"] = target_hostname
    _reboot_state["node_ip"] = target_ip

    # Get ALL pods in telemetry namespace before reboot
    log.check("Listing all pods in telemetry namespace before reboot:")
    all_pods_before = get_all_telemetry_pods(host, admin_ip)
    log.check(f"Total pods: {len(all_pods_before)}")
    for pod in all_pods_before:
        log.check(f"  {pod['name']:<45} {pod['status']:<12} {pod['node']}")

    # Reboot the node
    log.check(f"Rebooting node: {target_hostname} ({target_ip})")
    reboot_result = reboot_node(host, admin_ip, target_ip)

    if not reboot_result["success"]:
        _reboot_state["reboot_skipped"] = True
        _reboot_state["skip_reason"] = f"Failed to reboot: {reboot_result.get('error')}"
        log.failed(f"Failed to reboot {target_hostname}", reboot_result.get("error", ""))
        assert False, f"Failed to reboot node: {reboot_result.get('error')}"

    # Wait for node to go down
    log.check(f"Waiting for node {target_hostname} to go down")
    time.sleep(NODE_REBOOT_WAIT_SECONDS)
    
    node_down = wait_for_node_down(host, admin_ip, target_hostname, timeout_seconds=60)
    if node_down["success"]:
        log.check(f"Node {target_hostname} is now {node_down['status']} (took {node_down['elapsed_seconds']}s)")
    else:
        log.check(f"Note: Node may have rebooted quickly, continuing with online check")

    # Wait for node to come back online
    log.check(f"Waiting for node {target_hostname} to come back online (max {NODE_ONLINE_TIMEOUT_SECONDS}s)")
    online_result = wait_for_node_online(host, admin_ip, target_ip, NODE_ONLINE_TIMEOUT_SECONDS)
    
    if not online_result["success"]:
        _reboot_state["reboot_skipped"] = True
        _reboot_state["skip_reason"] = f"Node did not come online: {online_result.get('error')}"
        log.failed(f"Node {target_hostname} did not come back online", online_result.get("error", ""))
        assert False, f"Node did not come online: {online_result.get('error')}"
    
    log.check(f"Node {target_hostname} is online (ping: {online_result['ping_ok']}, ssh: {online_result['ssh_ok']}, took {online_result['elapsed_seconds']}s)")

    # Wait for cloud-init to complete
    log.check(f"Waiting for cloud-init to complete on {target_hostname}")
    cloudinit_result = wait_for_cloudinit_done(host, admin_ip, target_ip, target_hostname)
    
    if cloudinit_result["success"]:
        log.check(f"Cloud-init completed: {cloudinit_result['status']} (took {cloudinit_result['elapsed_seconds']}s)")
    else:
        log.check(f"Warning: Cloud-init status: {cloudinit_result['status']} - continuing anyway")

    # Wait for node to rejoin K8s cluster
    log.check(f"Waiting for node {target_hostname} to rejoin K8s cluster")
    rejoin_result = wait_for_node_rejoin_cluster(host, admin_ip, target_hostname, timeout_seconds=120)
    
    if not rejoin_result["success"]:
        _reboot_state["reboot_skipped"] = True
        _reboot_state["skip_reason"] = f"Node did not rejoin cluster: {rejoin_result.get('error')}"
        log.failed(f"Node {target_hostname} did not rejoin cluster", rejoin_result.get("error", ""))
        assert False, f"Node did not rejoin cluster: {rejoin_result.get('error')}"
    
    log.check(f"Node {target_hostname} rejoined cluster with status: {rejoin_result['status']} (took {rejoin_result['elapsed_seconds']}s)")

    _reboot_state["reboot_done"] = True

    # Verify ALL pods in telemetry namespace are running
    log.check("Verifying all pods in telemetry namespace are running")
    running_result = verify_all_telemetry_pods_running(host, admin_ip)

    # List all pods after reboot with their locations
    log.check("All telemetry pods after reboot:")
    if running_result.get("output"):
        for line in running_result["output"].strip().split('\n'):
            log.check(f"  {line}")

    # Build details for final report
    details_lines = [
        f"Rebooted node: {target_hostname} ({target_ip})",
        f"Total pods in namespace: {running_result['total_pods']}",
        f"Node online after: {online_result['elapsed_seconds']}s",
        f"Cloud-init status: {cloudinit_result['status']}",
        f"Node rejoin after: {rejoin_result['elapsed_seconds']}s",
        "",
        f"Final: {running_result['running_count']} running, {running_result['not_running_count']} not running",
    ]

    if running_result["not_running_pods"]:
        details_lines.append("Not running pods:")
        for pod in running_result["not_running_pods"]:
            details_lines.append(f"  {pod['name']}: {pod['status']}")

    details = "\n".join(details_lines)
    success = running_result["success"]

    if success:
        log.passed(f"All telemetry pods running after reboot of {target_hostname}", details)
    else:
        error_msg = running_result.get("error")
        log.failed(f"Some pods not running after reboot: {error_msg}", details)

    assert success, (
        f"Telemetry pods not running after rebooting {target_hostname}: "
        f"{running_result.get('error')}"
    )


# =============================================================================
# IDRAC TELEMETRY TEST CASES (after reboot)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(21)
def test_idrac_telemetry_pod_count_after_reboot(host):
    """
    Test Case 2: Verify idrac-telemetry pods count matches expected after reboot.
    """
    log = TestLogger(TEST_NAMES["idrac_telemetry_pod_count"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    admin_ip = get_admin_ip(host, log)

    log.check(f"Checking idrac-telemetry pods on {admin_ip}")
    result = verify_idrac_telemetry_pod_count(host, admin_ip)

    details = (
        f"service_kube_node count: {result.get('service_kube_node_count', 'N/A')}\n"
        f"service_kube_nodes with children: {result.get('service_kube_nodes_with_children', 'N/A')}\n"
        f"Expected pods: {result.get('expected_pods', 'N/A')}\n"
        f"Actual pods: {result.get('actual_pods', 'N/A')}"
    )

    if result.get("error"):
        log.failed(f"Failed to verify pod count: {result['error']}", details)
        assert False, result["error"]

    if result["success"]:
        log.passed(f"idrac-telemetry pod count matches: {result.get('actual_pods', 'N/A')}", details)
    else:
        log.failed(f"Pod count mismatch: expected {result.get('expected_pods', 'N/A')}, got {result.get('actual_pods', 'N/A')}", details)

    assert result["success"], f"Pod count mismatch: {details}"


@pytest.mark.negative
@pytest.mark.order(22)
def test_mysql_data_in_idrac_telemetry_pods_after_reboot(host):
    """
    Test Case 3: Verify MySQL data in idrac-telemetry pods after reboot.
    """
    log = TestLogger(TEST_NAMES["mysql_data_in_pods"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    admin_ip = get_admin_ip(host, log)

    if not has_activated_ips(host):
        log.skipped("No activated IPs found in telemetry report", "Test skipped")
        pytest.skip("No activated IPs found in telemetry report")

    log.check("Decrypting MySQL credentials and verifying data in pods")
    result = verify_mysql_data_in_pods(host, admin_ip)

    if result.get("error") and not result.get("pod_results"):
        log.failed("Failed to verify MySQL data", result["error"])
        assert False, result["error"]

    pod_results = result.get("pod_results", [])
    passed = sum(1 for pr in pod_results if pr["success"])
    failed = len(pod_results) - passed

    details_lines = []
    for pr in pod_results:
        status = "✓" if pr["success"] else "✗"
        details_lines.append(f"  {status} {pr['pod_name']}: {pr.get('row_count', 0)} rows")
        if pr.get("error"):
            details_lines.append(f"      Error: {pr['error']}")

    details = "\n".join(details_lines)

    if failed == 0:
        log.passed(f"MySQL data verified in {passed} pods", details)
    else:
        log.failed(f"MySQL data verification failed in {failed}/{len(pod_results)} pods", details)

    assert failed == 0, f"MySQL data verification failed in {failed} pods"


@pytest.mark.negative
@pytest.mark.order(23)
def test_receiver_collecting_metrics_after_reboot(host):
    """
    Test Case 4: Verify idrac-telemetry-receiver is collecting metrics after reboot.
    """
    log = TestLogger(TEST_NAMES["receiver_collecting_metrics"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    admin_ip = get_admin_ip(host, log)

    if not has_activated_ips(host):
        log.skipped("No activated IPs found in telemetry report", "Test skipped")
        pytest.skip("No activated IPs found in telemetry report")

    log.check("Checking idrac-telemetry-receiver logs for metrics collection")
    result = verify_receiver_collecting_metrics(host, admin_ip)

    if result.get("error") and not result.get("pod_results"):
        log.failed("Failed to verify receiver metrics", result["error"])
        assert False, result["error"]

    pod_results = result.get("pod_results", [])
    passed = sum(1 for pr in pod_results if pr["success"])
    failed = len(pod_results) - passed

    details_lines = []
    for pr in pod_results:
        status = "✓" if pr["success"] else "✗"
        details_lines.append(f"  {status} {pr['pod_name']}: {pr.get('metrics_count', 0)} metrics")

    details = "\n".join(details_lines)

    if failed == 0:
        log.passed(f"Receiver collecting metrics in {passed} pods", details)
    else:
        log.failed(f"Receiver not collecting in {failed}/{len(pod_results)} pods", details)

    assert failed == 0, f"Receiver not collecting metrics in {failed} pods"


# =============================================================================
# KAFKA TEST CASES (after reboot)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(24)
def test_ldms_pods_running_after_reboot(host):
    """
    Test Case 5: Verify LDMS pods are running after reboot.
    """
    log = TestLogger(TEST_NAMES.get("ldms_pods_running", "Verify LDMS pods running") + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_ldms_enabled(host):
        log.skipped("LDMS is not enabled", "Test skipped")
        pytest.skip("LDMS is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying LDMS pods are running in telemetry namespace")
    result = verify_ldms_pods_running(host, admin_ip)

    if result.get("skipped"):
        pytest.skip(result.get("reason", "LDMS not enabled"))

    details_lines = []
    for pod in result.get("pods", []):
        status = "✓" if pod["status"] == "Running" else "✗"
        details_lines.append(f"  {status} {pod['name']}: {pod['status']}")

    details = "\n".join(details_lines) if details_lines else "No LDMS pods found"

    if result["success"]:
        log.passed(f"All {len(result.get('pods', []))} LDMS pods running", details)
    else:
        log.failed(result.get("error", "LDMS pods not running"), details)

    assert result["success"], result.get("error", "LDMS pods not running")


@pytest.mark.negative
@pytest.mark.order(25)
def test_ldms_services_ports_after_reboot(host):
    """
    Test Case 6: Verify LDMS services ports match telemetry_config.yml after reboot.
    """
    log = TestLogger(TEST_NAMES.get("ldms_services_ports", "Verify LDMS services ports") + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

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

    details_lines = []
    for svc in result.get("services", []):
        status = "✓" if svc["match"] else "✗"
        details_lines.append(f"  {status} {svc['name']}: expected {svc['expected']}, actual {svc['actual']}")

    details = "\n".join(details_lines) if details_lines else "No services found"

    if result["success"]:
        log.passed("All LDMS service ports match config", details)
    else:
        log.failed("LDMS service port mismatch", details)

    assert result["success"], "LDMS service port mismatch"


@pytest.mark.negative
@pytest.mark.order(26)
def test_kafka_topics_after_reboot(host):
    """
    Test Case 7: Verify Kafka topics via REST proxy after reboot.
    """
    log = TestLogger(TEST_NAMES["kafka_topics_verification"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    admin_ip = get_admin_ip(host, log)

    log.check("Getting Kafka topics via REST proxy")
    result = verify_kafka_topics_via_rest(host, admin_ip)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", "Kafka not enabled"), "Test skipped")
        pytest.skip(result.get("skip_reason", "Kafka not enabled"))

    if result.get("error") and not result.get("topics"):
        log.failed("Failed to get Kafka topics", result["error"])
        assert False, result["error"]

    details = f"Topics found: {', '.join(result.get('topics', []))}"

    if result["success"]:
        log.passed("Kafka topics verified", details)
    else:
        log.failed(result.get("error", "Topic verification failed"), details)

    assert result["success"], result.get("error", "Kafka topic verification failed")


@pytest.mark.negative
@pytest.mark.order(27)
def test_kafka_config_match_after_reboot(host):
    """
    Test Case 8: Verify Kafka configurations match telemetry_config.yml after reboot.
    """
    log = TestLogger(TEST_NAMES["kafka_config_match"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_kafka_enabled(host):
        log.skipped("Kafka is not enabled", "Test skipped")
        pytest.skip("Kafka is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Checking Kafka config inside broker pod vs telemetry_config.yml")
    result = verify_kafka_config_match(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify Kafka config", result["error"])
        assert False, result["error"]

    details_lines = []
    for key, match_info in result.get("config_matches", {}).items():
        status = "✓" if match_info["match"] else "✗"
        details_lines.append(f"  {status} {key}: expected={match_info['expected']}, actual={match_info['actual']}")

    details = "\n".join(details_lines) if details_lines else "No config to verify"

    if result["success"]:
        log.passed("Kafka config matches telemetry_config.yml", details)
    else:
        log.failed("Kafka config mismatch", details)

    assert result["success"], "Kafka config mismatch"


@pytest.mark.negative
@pytest.mark.order(28)
def test_idrac_data_in_kafka_topic_after_reboot(host):
    """
    Test Case 9: Verify iDRAC telemetry data in Kafka topic after reboot.
    """
    log = TestLogger(TEST_NAMES.get("kafka_idrac_data", "Verify iDRAC data in Kafka") + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_kafka_enabled(host):
        log.skipped("Kafka is not enabled", "Test skipped")
        pytest.skip("Kafka is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying iDRAC telemetry data in Kafka topic")
    result = verify_idrac_data_in_kafka(host, admin_ip, timeout_seconds=30)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", ""), "Test skipped")
        pytest.skip(result.get("skip_reason", ""))

    if result.get("error"):
        log.failed("Failed to verify iDRAC data in Kafka", result["error"])
        assert False, result["error"]

    details = f"Found {result.get('message_count', 0)} messages with iDRAC data"

    if result["success"]:
        log.passed("iDRAC data found in Kafka topic", details)
    else:
        log.failed("No iDRAC data in Kafka topic", details)

    assert result["success"], "No iDRAC data found in Kafka topic"


@pytest.mark.negative
@pytest.mark.order(29)
def test_ldms_latest_data_in_kafka_after_reboot(host):
    """
    Test Case 10: Verify LDMS latest data in Kafka topic after reboot.
    """
    log = TestLogger(TEST_NAMES.get("ldms_latest_data", "Verify LDMS data in Kafka") + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_ldms_enabled(host):
        log.skipped("LDMS is not enabled", "Test skipped")
        pytest.skip("LDMS is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying latest LDMS data in Kafka topic")
    result = verify_ldms_data_in_kafka(host, admin_ip, timeout_seconds=30)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", ""), "Test skipped")
        pytest.skip(result.get("skip_reason", ""))

    if result.get("error"):
        log.failed("Failed to verify LDMS data in Kafka", result["error"])
        assert False, result["error"]

    details = f"Found {result.get('message_count', 0)} LDMS messages"

    if result["success"]:
        log.passed("LDMS data found in Kafka topic", details)
    else:
        log.failed("No LDMS data in Kafka topic", details)

    assert result["success"], "No LDMS data found in Kafka topic"


# =============================================================================
# VICTORIAMETRICS TEST CASES (after reboot)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(30)
def test_victoria_enabled_after_reboot(host):
    """
    Test Case 11: Verify VictoriaMetrics is enabled after reboot.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_enabled"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_idrac_telemetry_enabled(host):
        log.skipped("iDRAC telemetry is not enabled", "Test skipped")
        pytest.skip("iDRAC telemetry is not enabled")

    if not is_victoria_enabled(host):
        log.skipped(VICTORIA_LOG_MSGS["victoria_not_enabled"], "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    deployment_mode = get_deployment_mode(host)
    log.passed(
        f"VictoriaMetrics is enabled (mode: {deployment_mode})",
        f"Deployment mode: {deployment_mode}"
    )


@pytest.mark.negative
@pytest.mark.order(31)
def test_victoria_persistence_size_after_reboot(host):
    """
    Test Case 12: Verify VictoriaMetrics persistence size matches config after reboot.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_persistence_size"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying VictoriaMetrics PVC storage size")
    result = verify_victoria_persistence_size(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify persistence size", result["error"])
        assert False, result["error"]

    details = (
        f"Expected: {result.get('expected_size', 'N/A')}\n"
        f"Actual: {result.get('actual_size', 'N/A')}"
    )

    if result["success"]:
        log.passed("VictoriaMetrics persistence size matches config", details)
    else:
        log.failed("Persistence size mismatch", details)

    assert result["success"], "VictoriaMetrics persistence size mismatch"


@pytest.mark.negative
@pytest.mark.order(32)
def test_victoria_pods_after_reboot(host):
    """
    Test Case 13: Verify VictoriaMetrics pods are running after reboot.
    """
    log = TestLogger("Verify VictoriaMetrics pods (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)
    deployment_mode = get_deployment_mode(host)

    log.check(f"Verifying VictoriaMetrics pods (mode: {deployment_mode})")

    if deployment_mode == DEPLOYMENT_MODE_SINGLE:
        result = verify_victoria_single_node_pods(host, admin_ip)
    else:
        result = verify_victoria_cluster_pods(host, admin_ip)

    if result.get("skip"):
        log.skipped(result.get("skip_reason", ""), "Test skipped")
        pytest.skip(result.get("skip_reason", ""))

    if result.get("error"):
        log.failed("Failed to verify VictoriaMetrics pods", result["error"])
        assert False, result["error"]

    details_lines = []
    for pod in result.get("pods", []):
        status = "✓" if pod.get("running", False) else "✗"
        details_lines.append(f"  {status} {pod['name']}: {pod.get('status', 'Unknown')}")

    details = "\n".join(details_lines) if details_lines else "No pods found"

    if result["success"]:
        log.passed(f"All VictoriaMetrics pods running ({deployment_mode} mode)", details)
    else:
        log.failed("VictoriaMetrics pods not running", details)

    assert result["success"], "VictoriaMetrics pods not running"


@pytest.mark.negative
@pytest.mark.order(33)
def test_vmagent_pod_running_after_reboot(host):
    """
    Test Case 14: Verify vmagent pod is running after reboot.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["vmagent_pod_running"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check("Verifying vmagent pod")
    result = verify_vmagent_pod(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify vmagent pod", result["error"])
        assert False, result["error"]

    details = f"vmagent pod: {result.get('pod_name', 'N/A')} - {result.get('status', 'Unknown')}"

    if result["success"]:
        log.passed("vmagent pod is running", details)
    else:
        log.failed("vmagent pod not running", details)

    assert result["success"], "vmagent pod not running"


@pytest.mark.negative
@pytest.mark.order(34)
def test_victoria_services_after_reboot(host):
    """
    Test Case 15: Verify VictoriaMetrics services have external IPs after reboot.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_services"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)
    deployment_mode = get_deployment_mode(host)

    log.check(f"Verifying VictoriaMetrics services (mode: {deployment_mode})")
    result = verify_victoria_services(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify VictoriaMetrics services", result["error"])
        assert False, result["error"]

    details_lines = []
    for svc in result.get("services", []):
        status = "✓" if svc.get("has_external_ip", False) else "✗"
        details_lines.append(f"  {status} {svc['name']}: {svc.get('external_ip', 'None')}")

    details = "\n".join(details_lines) if details_lines else "No services found"

    if result["success"]:
        log.passed("VictoriaMetrics services have external IPs", details)
    else:
        log.failed("VictoriaMetrics services missing external IPs", details)

    assert result["success"], "VictoriaMetrics services missing external IPs"


@pytest.mark.negative
@pytest.mark.order(35)
def test_victoria_tls_secret_after_reboot(host):
    """
    Test Case 16: Verify VictoriaMetrics TLS secret exists after reboot.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_tls_secret"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)

    log.check(f"Verifying TLS secret '{VICTORIA_TLS_SECRET}'")
    result = verify_victoria_tls_secret(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify TLS secret", result["error"])
        assert False, result["error"]

    details_lines = [f"Secret: {VICTORIA_TLS_SECRET}"]
    for key in result.get("keys", []):
        status = "✓" if key.get("exists", False) else "✗"
        details_lines.append(f"  {status} {key['name']}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("TLS secret exists with required keys", details)
    else:
        log.failed("TLS secret missing or incomplete", details)

    assert result["success"], "TLS secret missing or incomplete"


@pytest.mark.negative
@pytest.mark.order(36)
def test_victoria_tls_health_after_reboot(host):
    """
    Test Case 17: Verify TLS connection and health endpoint after reboot.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_tls_health"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)
    deployment_mode = get_deployment_mode(host)

    log.check(f"Verifying TLS connection (mode: {deployment_mode})")
    result = verify_victoria_tls_health(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to verify TLS health", result["error"])
        assert False, result["error"]

    details = (
        f"Endpoint: {result.get('endpoint', 'N/A')}\n"
        f"Status: {result.get('status', 'Unknown')}\n"
        f"Response: {result.get('response', 'N/A')[:100]}"
    )

    if result["success"]:
        log.passed("TLS connection healthy", details)
    else:
        log.failed("TLS connection unhealthy", details)

    assert result["success"], "TLS connection unhealthy"


@pytest.mark.negative
@pytest.mark.order(37)
def test_victoria_idrac_data_after_reboot(host):
    """
    Test Case 18: Verify iDRAC telemetry data in VictoriaMetrics after reboot.
    """
    log = TestLogger(VICTORIA_TEST_NAMES["victoria_idrac_data"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

    if not is_victoria_enabled(host):
        log.skipped("VictoriaMetrics is not enabled", "Test skipped")
        pytest.skip("VictoriaMetrics is not enabled")

    admin_ip = get_admin_ip(host, log)

    activated_tags = get_activated_service_tags(host, admin_ip)
    if not activated_tags:
        log.skipped("No activated service tags found", "Test skipped")
        pytest.skip("No activated service tags found")

    log.check(f"Verifying iDRAC data for {len(activated_tags)} service tags")
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
        log.passed("iDRAC data found in VictoriaMetrics", details)
    else:
        log.failed("iDRAC data missing in VictoriaMetrics", details)

    assert result["success"], "iDRAC data missing in VictoriaMetrics"


# =============================================================================
# DELETE NODE TEST CASES (after reboot)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(38)
def test_idrac_deleted_node_data_in_mysql_after_reboot(host):
    """
    Test Case 19: Verify deleted node BMC IPs not in MySQL after reboot.
    """
    log = TestLogger(DELETE_NODE_TEST_NAMES["idrac_deleted_node_mysql"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

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
@pytest.mark.order(39)
def test_idrac_deleted_node_data_in_kafka_after_reboot(host):
    """
    Test Case 20: Verify deleted iDRAC node data not in Kafka after reboot.
    """
    log = TestLogger(DELETE_NODE_TEST_NAMES["idrac_deleted_node_kafka"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

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
@pytest.mark.order(40)
def test_ldms_deleted_node_data_in_kafka_after_reboot(host):
    """
    Test Case 21: Verify deleted LDMS node data not in Kafka after reboot.
    """
    log = TestLogger(DELETE_NODE_TEST_NAMES["ldms_deleted_node_kafka"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

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
@pytest.mark.order(41)
def test_idrac_deleted_node_data_in_victoria_after_reboot(host):
    """
    Test Case 22: Verify deleted iDRAC node data not in VictoriaMetrics after reboot.
    """
    log = TestLogger(DELETE_NODE_TEST_NAMES["idrac_deleted_node_victoria"] + " (after reboot)")

    _skip_if_service_k8s_not_enabled(host, log)
    _skip_if_reboot_not_done(log)

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
