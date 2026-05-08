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
VictoriaLogs Destructive Test Functions.

This module contains destructive test functions for VictoriaLogs:
- All vlstorage pods down
- All vlinsert pods down
- All vlselect pods down
- All VLAgent pods down
- Complete cluster failure and recovery
"""

import time
from typing import Dict, Any

from ...core.host import run_on_remote_node
from ..vars.shared_vars import TELEMETRY_NAMESPACE
from ..vars.victoria_logs_vars import (
    VLSTORAGE,
    VLINSERT,
    VLSELECT,
    VLAGENT_LOGS,
    VICTORIA_LOGS_TLS_SECRET,
    VICTORIA_LOGS_CMD_TEMPLATES,
)


# =============================================================================
# DESTRUCTIVE TESTS — ALL PODS DOWN
# =============================================================================

def verify_all_vlstorage_pods_down_behavior(host, admin_ip: str) -> Dict[str, Any]:
    """
    Destructive test: Kill all vlstorage pods and verify behavior.
    
    Steps:
    1. Baseline: verify cluster is healthy
    2. Kill all vlstorage pods (scale to 0)
    3. Verify vlinsert behavior (should reject writes or return error)
    4. Verify vlselect behavior (should return error, not crash)
    5. Restore vlstorage pods (scale back to 3)
    6. Wait for recovery
    7. Verify cluster is healthy again
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pods_killed": False,
        "vlinsert_behavior": "",
        "vlselect_behavior": "",
        "pods_restored": False,
        "recovery_successful": False,
        "error": "",
    }
    
    # Step 1: Baseline health check
    baseline_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlstorage "
        f"--no-headers | grep Running | wc -l",
        admin_ip,
    )
    running_count = int(baseline_cmd.stdout.strip()) if baseline_cmd.rc == 0 else 0
    result["baseline_healthy"] = running_count == 3
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {running_count}/3 vlstorage pods running"
        return result
    
    # Step 2: Kill all vlstorage pods
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        admin_ip,
    )
    result["pods_killed"] = kill_cmd.rc == 0
    
    if not result["pods_killed"]:
        result["error"] = f"Failed to scale down vlstorage: {kill_cmd.stderr}"
        return result
    
    # Wait for pods to terminate
    time.sleep(10)
    
    # Step 3: Test vlinsert behavior (should reject writes)
    vlinsert_test = _test_vlinsert_during_outage(host, admin_ip)
    result["vlinsert_behavior"] = vlinsert_test.get("behavior", "unknown")
    
    # Step 4: Test vlselect behavior (should return error, not crash)
    vlselect_test = _test_vlselect_during_outage(host, admin_ip)
    result["vlselect_behavior"] = vlselect_test.get("behavior", "unknown")
    
    # Step 5: Restore vlstorage pods
    restore_cmd = run_on_remote_node(
        host,
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=3",
        admin_ip,
    )
    result["pods_restored"] = restore_cmd.rc == 0
    
    if not result["pods_restored"]:
        result["error"] = f"Failed to scale up vlstorage: {restore_cmd.stderr}"
        return result
    
    # Step 6: Wait for recovery (up to 2 minutes)
    for i in range(24):  # 24 * 5s = 120s
        time.sleep(5)
        check_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlstorage "
            f"--no-headers | grep Running | wc -l",
            admin_ip,
        )
        running = int(check_cmd.stdout.strip()) if check_cmd.rc == 0 else 0
        if running == 3:
            result["recovery_successful"] = True
            break
    
    if not result["recovery_successful"]:
        result["error"] = "vlstorage pods did not recover within 120s"
        return result
    
    # Step 7: Verify cluster health post-recovery
    time.sleep(10)  # Allow cluster to stabilize
    health_check = _verify_cluster_health(host, admin_ip)
    result["success"] = health_check.get("healthy", False)
    
    if not result["success"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result


def verify_all_vlinsert_pods_down_behavior(host, admin_ip: str) -> Dict[str, Any]:
    """
    Destructive test: Kill all vlinsert pods and verify behavior.
    
    Expected behavior:
    - Writes should fail (no vlinsert to accept them)
    - Reads should still work (vlselect can query vlstorage directly)
    - Pods should auto-recover (Deployment will recreate them)
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pods_killed": False,
        "writes_rejected": False,
        "reads_still_work": False,
        "pods_recovered": False,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
        f"--no-headers | grep Running | wc -l",
        admin_ip,
    )
    running_count = int(baseline_cmd.stdout.strip()) if baseline_cmd.rc == 0 else 0
    result["baseline_healthy"] = running_count == 2
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {running_count}/2 vlinsert pods running"
        return result
    
    # Step 2: Kill all vlinsert pods
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        admin_ip,
    )
    result["pods_killed"] = kill_cmd.rc == 0
    
    if not result["pods_killed"]:
        result["error"] = f"Failed to scale down vlinsert: {kill_cmd.stderr}"
        return result
    
    time.sleep(10)
    
    # Step 3: Verify writes are rejected
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_rejected"] = write_test.get("behavior", "") in ["connection_refused", "timeout", "no_route"]
    
    # Step 4: Verify reads still work
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_still_work"] = read_test.get("behavior", "") == "success"
    
    # Step 5: Restore vlinsert pods
    restore_cmd = run_on_remote_node(
        host,
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        admin_ip,
    )
    
    if restore_cmd.rc != 0:
        result["error"] = f"Failed to scale up vlinsert: {restore_cmd.stderr}"
        return result
    
    # Step 6: Wait for recovery
    for i in range(24):
        time.sleep(5)
        check_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
            f"--no-headers | grep Running | wc -l",
            admin_ip,
        )
        running = int(check_cmd.stdout.strip()) if check_cmd.rc == 0 else 0
        if running == 2:
            result["pods_recovered"] = True
            break
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pods_killed"] and
        result["writes_rejected"] and
        result["reads_still_work"] and
        result["pods_recovered"]
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = "vlinsert destructive test failed - check individual steps"
    
    return result


def verify_all_vlselect_pods_down_behavior(host, admin_ip: str) -> Dict[str, Any]:
    """
    Destructive test: Kill all vlselect pods and verify behavior.
    
    Expected behavior:
    - Reads should fail (no vlselect to query)
    - Writes should still work (vlinsert writes directly to vlstorage)
    - Pods should auto-recover
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pods_killed": False,
        "reads_rejected": False,
        "writes_still_work": False,
        "pods_recovered": False,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlselect "
        f"--no-headers | grep Running | wc -l",
        admin_ip,
    )
    running_count = int(baseline_cmd.stdout.strip()) if baseline_cmd.rc == 0 else 0
    result["baseline_healthy"] = running_count == 2
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {running_count}/2 vlselect pods running"
        return result
    
    # Step 2: Kill all vlselect pods
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        admin_ip,
    )
    result["pods_killed"] = kill_cmd.rc == 0
    
    if not result["pods_killed"]:
        result["error"] = f"Failed to scale down vlselect: {kill_cmd.stderr}"
        return result
    
    time.sleep(10)
    
    # Step 3: Verify reads are rejected
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_rejected"] = read_test.get("behavior", "") in ["connection_refused", "timeout", "no_route"]
    
    # Step 4: Verify writes still work
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_still_work"] = write_test.get("behavior", "") == "success"
    
    # Step 5: Restore vlselect pods
    restore_cmd = run_on_remote_node(
        host,
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        admin_ip,
    )
    
    if restore_cmd.rc != 0:
        result["error"] = f"Failed to scale up vlselect: {restore_cmd.stderr}"
        return result
    
    # Step 6: Wait for recovery
    for i in range(24):
        time.sleep(5)
        check_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlselect "
            f"--no-headers | grep Running | wc -l",
            admin_ip,
        )
        running = int(check_cmd.stdout.strip()) if check_cmd.rc == 0 else 0
        if running == 2:
            result["pods_recovered"] = True
            break
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pods_killed"] and
        result["reads_rejected"] and
        result["writes_still_work"] and
        result["pods_recovered"]
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = "vlselect destructive test failed - check individual steps"
    
    return result


def verify_complete_cluster_failure_recovery(host, admin_ip: str) -> Dict[str, Any]:
    """
    Destructive test: Kill ALL VictoriaLogs pods and verify recovery.
    
    This is the ultimate disaster recovery test.
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "all_pods_killed": False,
        "cluster_unavailable": False,
        "all_pods_recovered": False,
        "cluster_healthy_after_recovery": False,
        "recovery_time_seconds": 0,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline = _verify_cluster_health(host, admin_ip)
    result["baseline_healthy"] = baseline.get("healthy", False)
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {baseline.get('error', '')}"
        return result
    
    # Step 2: Kill ALL pods
    start_time = time.time()
    
    kill_commands = [
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        f"kubectl scale statefulset vlagent-vlagent -n {TELEMETRY_NAMESPACE} --replicas=0",
    ]
    
    all_killed = True
    for cmd in kill_commands:
        kill_result = run_on_remote_node(host, cmd, admin_ip)
        if kill_result.rc != 0:
            all_killed = False
            result["error"] += f"Failed: {cmd}; "
    
    result["all_pods_killed"] = all_killed
    
    if not all_killed:
        # Try to restore before returning
        _restore_all_pods(host, admin_ip)
        return result
    
    time.sleep(15)
    
    # Step 3: Verify cluster is unavailable
    unavailable_test = _verify_cluster_health(host, admin_ip)
    result["cluster_unavailable"] = not unavailable_test.get("healthy", True)
    
    # Step 4: Restore ALL pods
    restore_commands = [
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=3",
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        f"kubectl scale statefulset vlagent-vlagent -n {TELEMETRY_NAMESPACE} --replicas=1",
    ]
    
    for cmd in restore_commands:
        run_on_remote_node(host, cmd, admin_ip)
    
    # Step 5: Wait for recovery (up to 3 minutes)
    for i in range(36):  # 36 * 5s = 180s
        time.sleep(5)
        
        # Check all pod counts
        vlstorage_count = _get_running_pod_count(host, admin_ip, "vlstorage")
        vlinsert_count = _get_running_pod_count(host, admin_ip, "vlinsert")
        vlselect_count = _get_running_pod_count(host, admin_ip, "vlselect")
        vlagent_count = _get_running_pod_count(host, admin_ip, "vlagent")
        
        if vlstorage_count == 3 and vlinsert_count == 2 and vlselect_count == 2 and vlagent_count == 1:
            result["all_pods_recovered"] = True
            result["recovery_time_seconds"] = int(time.time() - start_time)
            break
    
    if not result["all_pods_recovered"]:
        result["error"] = "Pods did not recover within 180s"
        return result
    
    # Step 6: Verify cluster health
    time.sleep(15)  # Allow cluster to stabilize
    health_check = _verify_cluster_health(host, admin_ip)
    result["cluster_healthy_after_recovery"] = health_check.get("healthy", False)
    
    result["success"] = (
        result["baseline_healthy"] and
        result["all_pods_killed"] and
        result["cluster_unavailable"] and
        result["all_pods_recovered"] and
        result["cluster_healthy_after_recovery"]
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _test_vlinsert_during_outage(host, admin_ip: str) -> Dict[str, Any]:
    """Test vlinsert behavior during outage."""
    # Get vlinsert external IP
    ip_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=VLINSERT["service_name"],
            namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    external_ip = ip_cmd.stdout.strip() if ip_cmd.rc == 0 else ""
    
    if not external_ip or external_ip == "null":
        return {"behavior": "no_service", "error": "vlinsert service has no external IP"}
    
    # Try to write
    test_payload = '{"_msg":"outage-test","_time":' + str(int(time.time())) + ',"job":"test"}'
    curl_cmd = (
        f"timeout 5 kubectl exec -n {TELEMETRY_NAMESPACE} "
        f"$(kubectl get pod -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
        f"-o jsonpath='{{.items[0].metadata.name}}' 2>/dev/null || echo 'none') -- "
        f"curl -k -s -w '%{{http_code}}' -o /dev/null --max-time 3 "
        f"-X POST https://localhost:{VLINSERT['port']}/insert/jsonline "
        f"--data '{test_payload}' "
        f"--cert /etc/victoria/certs/server.crt "
        f"--key /etc/victoria/certs/server.key 2>&1 || echo '000'"
    )
    
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)
    
    if cmd.rc != 0 or "000" in cmd.stdout or "none" in cmd.stdout:
        return {"behavior": "connection_refused", "http_code": "000"}
    
    http_code = cmd.stdout.strip()[-3:] if len(cmd.stdout.strip()) >= 3 else "000"
    
    if http_code in ["200", "204"]:
        return {"behavior": "success", "http_code": http_code}
    elif http_code.startswith("5"):
        return {"behavior": "server_error", "http_code": http_code}
    else:
        return {"behavior": "error", "http_code": http_code}


def _test_vlselect_during_outage(host, admin_ip: str) -> Dict[str, Any]:
    """Test vlselect behavior during outage."""
    # Get vlselect external IP
    ip_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=VLSELECT["service_name"],
            namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    external_ip = ip_cmd.stdout.strip() if ip_cmd.rc == 0 else ""
    
    if not external_ip or external_ip == "null":
        return {"behavior": "no_service", "error": "vlselect service has no external IP"}
    
    # Try to query
    curl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_query"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=VLSELECT["service_name"],
        port=VLSELECT["port"],
        external_ip=external_ip,
        query="*"
    )
    
    cmd = run_on_remote_node(host, f"timeout 5 {curl_cmd} 2>&1 || echo 'TIMEOUT'", admin_ip)
    
    if "TIMEOUT" in cmd.stdout or cmd.rc != 0:
        return {"behavior": "timeout", "error": "Query timed out"}
    
    if "Connection refused" in cmd.stdout or "No route" in cmd.stdout:
        return {"behavior": "connection_refused"}
    
    # Check if we got valid JSON response
    if "{" in cmd.stdout and "}" in cmd.stdout:
        return {"behavior": "success"}
    else:
        return {"behavior": "error", "response": cmd.stdout[:100]}


def _verify_cluster_health(host, admin_ip: str) -> Dict[str, Any]:
    """Verify overall cluster health."""
    vlstorage_count = _get_running_pod_count(host, admin_ip, "vlstorage")
    vlinsert_count = _get_running_pod_count(host, admin_ip, "vlinsert")
    vlselect_count = _get_running_pod_count(host, admin_ip, "vlselect")
    vlagent_count = _get_running_pod_count(host, admin_ip, "vlagent")
    
    healthy = (vlstorage_count == 3 and vlinsert_count == 2 and 
               vlselect_count == 2 and vlagent_count == 1)
    
    return {
        "healthy": healthy,
        "vlstorage": vlstorage_count,
        "vlinsert": vlinsert_count,
        "vlselect": vlselect_count,
        "vlagent": vlagent_count,
        "error": "" if healthy else f"Pod counts: vlstorage={vlstorage_count}, vlinsert={vlinsert_count}, vlselect={vlselect_count}, vlagent={vlagent_count}",
    }


def _get_running_pod_count(host, admin_ip: str, component: str) -> int:
    """Get count of running pods for a component."""
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name={component} "
        f"--no-headers 2>/dev/null | grep Running | wc -l",
        admin_ip,
    )
    return int(cmd.stdout.strip()) if cmd.rc == 0 and cmd.stdout.strip().isdigit() else 0


def _restore_all_pods(host, admin_ip: str):
    """Emergency restore of all pods."""
    restore_commands = [
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=3",
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        f"kubectl scale statefulset vlagent-vlagent -n {TELEMETRY_NAMESPACE} --replicas=1",
    ]
    for cmd in restore_commands:
        run_on_remote_node(host, cmd, admin_ip)


# =============================================================================
# PARTIAL FAILURE TESTS — SINGLE POD DOWN
# =============================================================================

def verify_single_vlstorage_pod_failure(host, admin_ip: str) -> Dict[str, Any]:
    """
    Partial failure test: Kill 1 of 3 vlstorage pods and verify HA.
    
    Expected behavior:
    - Writes should continue (vlinsert routes to remaining 2 nodes)
    - Reads should continue (vlselect queries remaining 2 nodes)
    - Some data may be unavailable (data on killed node)
    - Pod should auto-recover
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pod_killed": False,
        "pod_name": "",
        "writes_still_work": False,
        "reads_still_work": False,
        "pod_recovered": False,
        "recovery_time_seconds": 0,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline = _verify_cluster_health(host, admin_ip)
    result["baseline_healthy"] = baseline.get("healthy", False)
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {baseline.get('error', '')}"
        return result
    
    # Step 2: Kill one vlstorage pod (vlstorage-0)
    pod_name = "vlstorage-victoria-logs-cluster-0"
    result["pod_name"] = pod_name
    
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl delete pod {pod_name} -n {TELEMETRY_NAMESPACE} --grace-period=0 --force",
        admin_ip,
    )
    result["pod_killed"] = kill_cmd.rc == 0
    
    if not result["pod_killed"]:
        result["error"] = f"Failed to kill pod: {kill_cmd.stderr}"
        return result
    
    time.sleep(5)
    
    # Step 3: Test writes (should still work with 2/3 nodes)
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_still_work"] = write_test.get("behavior", "") == "success"
    
    # Step 4: Test reads (should still work with 2/3 nodes)
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_still_work"] = read_test.get("behavior", "") == "success"
    
    # Step 5: Wait for pod to recover (StatefulSet auto-recreates)
    start_time = time.time()
    for i in range(24):  # 24 * 5s = 120s
        time.sleep(5)
        check_cmd = run_on_remote_node(
            host,
            f"kubectl get pod {pod_name} -n {TELEMETRY_NAMESPACE} "
            f"--no-headers 2>/dev/null | grep Running",
            admin_ip,
        )
        if check_cmd.rc == 0 and "Running" in check_cmd.stdout:
            result["pod_recovered"] = True
            result["recovery_time_seconds"] = int(time.time() - start_time)
            break
    
    if not result["pod_recovered"]:
        result["error"] = f"Pod {pod_name} did not recover within 120s"
        return result
    
    # Step 6: Verify cluster health
    time.sleep(10)
    health_check = _verify_cluster_health(host, admin_ip)
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pod_killed"] and
        result["writes_still_work"] and
        result["reads_still_work"] and
        result["pod_recovered"] and
        health_check.get("healthy", False)
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result


def verify_single_vlinsert_pod_failure(host, admin_ip: str) -> Dict[str, Any]:
    """
    Partial failure test: Kill 1 of 2 vlinsert pods and verify HA.
    
    Expected behavior:
    - Writes should continue (LoadBalancer routes to remaining pod)
    - Reads should continue (vlselect independent)
    - Pod should auto-recover
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pod_killed": False,
        "pod_name": "",
        "writes_still_work": False,
        "reads_still_work": False,
        "pod_recovered": False,
        "recovery_time_seconds": 0,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline = _verify_cluster_health(host, admin_ip)
    result["baseline_healthy"] = baseline.get("healthy", False)
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {baseline.get('error', '')}"
        return result
    
    # Step 2: Get one vlinsert pod name
    get_pod_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
        f"--no-headers -o custom-columns=:metadata.name | head -1",
        admin_ip,
    )
    
    if get_pod_cmd.rc != 0 or not get_pod_cmd.stdout.strip():
        result["error"] = "Failed to get vlinsert pod name"
        return result
    
    pod_name = get_pod_cmd.stdout.strip()
    result["pod_name"] = pod_name
    
    # Step 3: Kill the pod
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl delete pod {pod_name} -n {TELEMETRY_NAMESPACE} --grace-period=0 --force",
        admin_ip,
    )
    result["pod_killed"] = kill_cmd.rc == 0
    
    if not result["pod_killed"]:
        result["error"] = f"Failed to kill pod: {kill_cmd.stderr}"
        return result
    
    time.sleep(5)
    
    # Step 4: Test writes (should still work with 1/2 pods)
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_still_work"] = write_test.get("behavior", "") == "success"
    
    # Step 5: Test reads (should still work)
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_still_work"] = read_test.get("behavior", "") == "success"
    
    # Step 6: Wait for pod to recover
    start_time = time.time()
    for i in range(24):
        time.sleep(5)
        check_count = _get_running_pod_count(host, admin_ip, "vlinsert")
        if check_count == 2:
            result["pod_recovered"] = True
            result["recovery_time_seconds"] = int(time.time() - start_time)
            break
    
    if not result["pod_recovered"]:
        result["error"] = "vlinsert pod did not recover within 120s"
        return result
    
    # Step 7: Verify cluster health
    time.sleep(10)
    health_check = _verify_cluster_health(host, admin_ip)
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pod_killed"] and
        result["writes_still_work"] and
        result["reads_still_work"] and
        result["pod_recovered"] and
        health_check.get("healthy", False)
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result


def verify_single_vlselect_pod_failure(host, admin_ip: str) -> Dict[str, Any]:
    """
    Partial failure test: Kill 1 of 2 vlselect pods and verify HA.
    
    Expected behavior:
    - Reads should continue (LoadBalancer routes to remaining pod)
    - Writes should continue (vlinsert independent)
    - Pod should auto-recover
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pod_killed": False,
        "pod_name": "",
        "writes_still_work": False,
        "reads_still_work": False,
        "pod_recovered": False,
        "recovery_time_seconds": 0,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline = _verify_cluster_health(host, admin_ip)
    result["baseline_healthy"] = baseline.get("healthy", False)
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {baseline.get('error', '')}"
        return result
    
    # Step 2: Get one vlselect pod name
    get_pod_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlselect "
        f"--no-headers -o custom-columns=:metadata.name | head -1",
        admin_ip,
    )
    
    if get_pod_cmd.rc != 0 or not get_pod_cmd.stdout.strip():
        result["error"] = "Failed to get vlselect pod name"
        return result
    
    pod_name = get_pod_cmd.stdout.strip()
    result["pod_name"] = pod_name
    
    # Step 3: Kill the pod
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl delete pod {pod_name} -n {TELEMETRY_NAMESPACE} --grace-period=0 --force",
        admin_ip,
    )
    result["pod_killed"] = kill_cmd.rc == 0
    
    if not result["pod_killed"]:
        result["error"] = f"Failed to kill pod: {kill_cmd.stderr}"
        return result
    
    time.sleep(5)
    
    # Step 4: Test reads (should still work with 1/2 pods)
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_still_work"] = read_test.get("behavior", "") == "success"
    
    # Step 5: Test writes (should still work)
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_still_work"] = write_test.get("behavior", "") == "success"
    
    # Step 6: Wait for pod to recover
    start_time = time.time()
    for i in range(24):
        time.sleep(5)
        check_count = _get_running_pod_count(host, admin_ip, "vlselect")
        if check_count == 2:
            result["pod_recovered"] = True
            result["recovery_time_seconds"] = int(time.time() - start_time)
            break
    
    if not result["pod_recovered"]:
        result["error"] = "vlselect pod did not recover within 120s"
        return result
    
    # Step 7: Verify cluster health
    time.sleep(10)
    health_check = _verify_cluster_health(host, admin_ip)
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pod_killed"] and
        result["writes_still_work"] and
        result["reads_still_work"] and
        result["pod_recovered"] and
        health_check.get("healthy", False)
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result
