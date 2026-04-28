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
Telemetry Failover Test Functions.

Functions for verifying telemetry pod rescheduling after node poweroff/reboot.
"""

import sys
import time
from typing import Dict, Any, List

from ...core import (
    run_on_remote_node,
    run_in_container,
    is_software_enabled,
)
from ..vars import TELEMETRY_NAMESPACE
from ..vars.failover_vars import (
    POD_RESCHEDULE_RETRY_LIMIT,
    POD_RESCHEDULE_RETRY_INTERVAL,
    NODE_POWEROFF_WAIT_SECONDS,
    NODE_REBOOT_WAIT_SECONDS,
    NODE_ONLINE_TIMEOUT_SECONDS,
    POD_RUNNING_STATUSES,
    CMD_GET_WORKER_NODES,
    CMD_GET_PODS_ON_NODE,
    CMD_GET_ALL_PODS,
    CMD_SSH_POWEROFF,
    CMD_SSH_REBOOT,
    CMD_PING_NODE,
    CMD_SSH_CHECK,
    CMD_CLOUDINIT_STATUS,
    CLOUDINIT_RETRY_LIMIT,
    CLOUDINIT_RETRY_INTERVAL,
    CLOUDINIT_PASSED_STATUSES,
    CLOUDINIT_RETRY_STATUSES,
)


# =============================================================================
# K8S WORKER NODE FUNCTIONS
# =============================================================================

def get_k8s_worker_nodes(host, admin_ip: str) -> List[Dict[str, str]]:
    """
    Get list of K8s worker nodes from kubectl.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane

    Returns:
        List of dicts with hostname, status, ip keys
    """
    cmd = run_on_remote_node(
        host,
        CMD_GET_WORKER_NODES,
        admin_ip
    )

    if cmd.rc != 0:
        return []

    workers = []
    for line in cmd.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 6:
            workers.append({
                "hostname": parts[0],
                "status": parts[1],
                "ip": parts[5],
            })

    return workers


def select_target_node_for_poweroff(
    host, admin_ip: str, workers: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Select the best worker node to power off for testing.
    
    Selects the node with the most telemetry pods running on it.
    If pods are evenly distributed, selects randomly.
    
    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane
        workers: List of worker node dicts with hostname, status, ip
    
    Returns:
        Dict with selected node info and pod counts per node
    """
    import random
    
    # Get all pods and count per node
    all_pods = get_all_telemetry_pods(host, admin_ip)
    
    # Count pods per worker node
    pod_counts = {}
    for worker in workers:
        hostname = worker["hostname"]
        pod_counts[hostname] = {
            "count": 0,
            "pods": [],
            "worker": worker,
        }
    
    for pod in all_pods:
        node = pod.get("node", "")
        if node in pod_counts:
            pod_counts[node]["count"] += 1
            pod_counts[node]["pods"].append(pod["name"])
    
    # Find node(s) with most pods
    max_count = max(pc["count"] for pc in pod_counts.values()) if pod_counts else 0
    
    if max_count == 0:
        # No pods on any worker, select first
        return {
            "selected": workers[0] if workers else None,
            "pod_counts": pod_counts,
            "reason": "No telemetry pods found on workers",
        }
    
    # Get nodes with max pods
    max_nodes = [h for h, pc in pod_counts.items() if pc["count"] == max_count]
    
    if len(max_nodes) == 1:
        selected_hostname = max_nodes[0]
        reason = f"Node has most pods ({max_count})"
    else:
        # Multiple nodes with same count, select randomly
        selected_hostname = random.choice(max_nodes)
        reason = f"Random selection from {len(max_nodes)} nodes with {max_count} pods each"
    
    return {
        "selected": pod_counts[selected_hostname]["worker"],
        "pod_counts": pod_counts,
        "reason": reason,
    }


def poweroff_node(host, admin_ip: str, target_ip: str) -> Dict[str, Any]:
    """
    Power off a K8s worker node via SSH.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane (for SSH hop)
        target_ip: IP of node to power off

    Returns:
        Dict with success, error keys
    """
    # SSH to target node and run poweroff command
    # Use nohup and background to avoid SSH hang
    cmd = run_on_remote_node(
        host,
        CMD_SSH_POWEROFF.format(target_ip=target_ip),
        admin_ip
    )

    # Command may return error since connection drops, that's expected
    return {
        "success": True,
        "node_ip": target_ip,
        "error": "",
    }


def wait_for_node_down(
    host, admin_ip: str, target_hostname: str, timeout_seconds: int = 60
) -> Dict[str, Any]:
    """
    Wait for a K8s node to show NotReady status.
    
    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane
        target_hostname: Hostname of node to check
        timeout_seconds: Max seconds to wait
    
    Returns:
        Dict with success, status, elapsed_seconds
    """
    start_time = time.time()
    check_interval = 5
    
    while (time.time() - start_time) < timeout_seconds:
        workers = get_k8s_worker_nodes(host, admin_ip)
        
        for w in workers:
            if w["hostname"] == target_hostname:
                if w["status"] != "Ready":
                    return {
                        "success": True,
                        "status": w["status"],
                        "elapsed_seconds": int(time.time() - start_time),
                    }
                break
        
        time.sleep(check_interval)
    
    return {
        "success": False,
        "status": "Ready",
        "elapsed_seconds": timeout_seconds,
        "error": f"Node {target_hostname} still Ready after {timeout_seconds}s",
    }


# =============================================================================
# POD STATUS FUNCTIONS
# =============================================================================

def get_telemetry_pods_on_node(
    host, admin_ip: str, node_name: str
) -> List[Dict[str, str]]:
    """
    Get telemetry pods running on a specific node.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane
        node_name: Name of the K8s node

    Returns:
        List of dicts with name, status, node keys
    """
    cmd = run_on_remote_node(
        host,
        CMD_GET_PODS_ON_NODE.format(namespace=TELEMETRY_NAMESPACE, node_name=node_name),
        admin_ip
    )

    if cmd.rc != 0:
        return []

    pods = []
    for line in cmd.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 7:
            pods.append({
                "name": parts[0],
                "ready": parts[1],
                "status": parts[2],
                "node": parts[6] if len(parts) > 6 else node_name,
            })

    return pods


def get_all_telemetry_pods(host, admin_ip: str) -> List[Dict[str, str]]:
    """
    Get all telemetry pods with their node assignments.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane

    Returns:
        List of dicts with name, status, node keys
    """
    cmd = run_on_remote_node(
        host,
        CMD_GET_ALL_PODS.format(namespace=TELEMETRY_NAMESPACE),
        admin_ip
    )

    if cmd.rc != 0:
        return []

    pods = []
    for line in cmd.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 7:
            pods.append({
                "name": parts[0],
                "ready": parts[1],
                "status": parts[2],
                "node": parts[6],
            })

    return pods


def wait_for_pods_reschedule(
    host,
    admin_ip: str,
    powered_off_node: str,
    original_pods: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Wait for pods from powered-off node to reschedule to other nodes.

    Uses configurable retry logic with single-line progress output.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane
        powered_off_node: Name of the node that was powered off
        original_pods: List of pods that were on the powered-off node

    Returns:
        Dict with success, rescheduled_pods, failed_pods, details
    """
    if not original_pods:
        return {
            "success": True,
            "rescheduled_pods": [],
            "failed_pods": [],
            "details": "No pods were on the powered-off node",
        }

    # Track pod status: {pod_name: {status, node, rescheduled}}
    pods_status: Dict[str, Dict] = {}
    for pod in original_pods:
        pods_status[pod["name"]] = {
            "original_node": powered_off_node,
            "status": "waiting",
            "node": "",
            "rescheduled": False,
        }

    # Retry loop
    for retry in range(1, POD_RESCHEDULE_RETRY_LIMIT + 1):
        # Print retry status
        rescheduled_count = sum(1 for ps in pods_status.values() if ps["rescheduled"])
        print(f"  → Waiting for pods to reschedule: {rescheduled_count}/{len(pods_status)} (retry {retry}/{POD_RESCHEDULE_RETRY_LIMIT})")
        # Get current pod status
        current_pods = get_all_telemetry_pods(host, admin_ip)

        # Check each original pod
        all_rescheduled = True
        for pod_name, ps in pods_status.items():
            if ps["rescheduled"]:
                continue

            # Find this pod in current pods
            found = False
            for cp in current_pods:
                if cp["name"] == pod_name:
                    found = True
                    ps["status"] = cp["status"]
                    ps["node"] = cp["node"]

                    # Check if rescheduled (running on different node)
                    if (cp["node"] != powered_off_node and
                            cp["status"] in POD_RUNNING_STATUSES):
                        ps["rescheduled"] = True
                    else:
                        all_rescheduled = False
                    break

            if not found:
                # Pod might be recreated with different name (StatefulSet)
                # Check for pods with similar prefix
                pod_prefix = pod_name.rsplit('-', 1)[0]
                for cp in current_pods:
                    if (cp["name"].startswith(pod_prefix) and
                            cp["node"] != powered_off_node and
                            cp["status"] in POD_RUNNING_STATUSES):
                        ps["rescheduled"] = True
                        ps["node"] = cp["node"]
                        ps["status"] = cp["status"]
                        break
                else:
                    all_rescheduled = False
                    ps["status"] = "not_found"

        if all_rescheduled:
            print(f"  → All pods rescheduled successfully")
            break

        # Wait before next retry
        time.sleep(POD_RESCHEDULE_RETRY_INTERVAL)

    # Build results
    rescheduled_pods = []
    failed_pods = []

    for pod_name, ps in pods_status.items():
        if ps["rescheduled"]:
            rescheduled_pods.append({
                "name": pod_name,
                "original_node": powered_off_node,
                "new_node": ps["node"],
                "status": ps["status"],
            })
        else:
            failed_pods.append({
                "name": pod_name,
                "original_node": powered_off_node,
                "current_status": ps["status"],
            })

    success = len(failed_pods) == 0

    # Build details
    details_lines = [
        f"Powered-off node: {powered_off_node}",
        f"Original pods: {len(original_pods)}",
        f"Rescheduled: {len(rescheduled_pods)}",
        f"Failed: {len(failed_pods)}",
    ]

    for rp in rescheduled_pods:
        details_lines.append(
            f"  \u2713 {rp['name']}: {rp['original_node']} -> {rp['new_node']}"
        )

    for fp in failed_pods:
        details_lines.append(
            f"  \u2717 {fp['name']}: stuck on {fp['original_node']} ({fp['current_status']})"
        )

    return {
        "success": success,
        "rescheduled_pods": rescheduled_pods,
        "failed_pods": failed_pods,
        "details": "\n".join(details_lines),
        "error": "" if success else f"{len(failed_pods)} pods failed to reschedule",
    }


def verify_pods_not_on_node(
    host, admin_ip: str, node_name: str
) -> Dict[str, Any]:
    """
    Verify no telemetry pods are running on a specific node.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane
        node_name: Name of the node to check

    Returns:
        Dict with success, pods_on_node, error
    """
    pods = get_telemetry_pods_on_node(host, admin_ip, node_name)

    # Filter to only running pods (ignore terminated/evicted)
    running_pods = [p for p in pods if p["status"] in POD_RUNNING_STATUSES]

    return {
        "success": len(running_pods) == 0,
        "pods_on_node": running_pods,
        "error": "" if not running_pods else (
            f"{len(running_pods)} pods still on {node_name}"
        ),
    }


def verify_all_pods_running(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify all telemetry pods are in Running state.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane

    Returns:
        Dict with success, running_pods, not_running_pods, error
    """
    pods = get_all_telemetry_pods(host, admin_ip)

    running_pods = []
    not_running_pods = []

    for pod in pods:
        if pod["status"] in POD_RUNNING_STATUSES:
            running_pods.append(pod)
        else:
            not_running_pods.append(pod)

    return {
        "success": len(not_running_pods) == 0 and len(running_pods) > 0,
        "total": len(pods),
        "running_pods": running_pods,
        "not_running_pods": not_running_pods,
        "error": "" if not not_running_pods else (
            f"{len(not_running_pods)} pods not running"
        ),
    }


# =============================================================================
# REBOOT FUNCTIONS
# =============================================================================

def reboot_node(host, admin_ip: str, target_ip: str) -> Dict[str, Any]:
    """
    Reboot a K8s worker node via SSH.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane (for SSH hop)
        target_ip: IP of node to reboot

    Returns:
        Dict with success, error keys
    """
    cmd = run_on_remote_node(
        host,
        CMD_SSH_REBOOT.format(target_ip=target_ip),
        admin_ip
    )

    # Command may return error since connection drops, that's expected
    return {
        "success": True,
        "node_ip": target_ip,
        "error": "",
    }


def wait_for_node_online(
    host, admin_ip: str, target_ip: str, timeout_seconds: int = None
) -> Dict[str, Any]:
    """
    Wait for a node to come back online after reboot.
    
    Checks ping first, then SSH connectivity.
    
    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane
        target_ip: IP of node to check
        timeout_seconds: Max seconds to wait (default from config)
    
    Returns:
        Dict with success, ping_ok, ssh_ok, elapsed_seconds
    """
    if timeout_seconds is None:
        timeout_seconds = NODE_ONLINE_TIMEOUT_SECONDS
    
    start_time = time.time()
    check_interval = 10
    ping_ok = False
    ssh_ok = False
    
    while (time.time() - start_time) < timeout_seconds:
        elapsed = int(time.time() - start_time)
        
        # Check ping first
        if not ping_ok:
            cmd = run_in_container(host, CMD_PING_NODE.format(target_ip=target_ip))
            if cmd.rc == 0:
                ping_ok = True
                print(f"  → Node {target_ip} is pingable (took {elapsed}s)")
        
        # If ping ok, check SSH
        if ping_ok and not ssh_ok:
            cmd = run_on_remote_node(host, "echo ok 2>&1", target_ip)
            if cmd.rc == 0 and "ok" in (cmd.stdout or ""):
                ssh_ok = True
                print(f"  → Node {target_ip} SSH is ready (took {elapsed}s)")
                return {
                    "success": True,
                    "ping_ok": True,
                    "ssh_ok": True,
                    "elapsed_seconds": elapsed,
                }
        
        time.sleep(check_interval)
    
    return {
        "success": False,
        "ping_ok": ping_ok,
        "ssh_ok": ssh_ok,
        "elapsed_seconds": timeout_seconds,
        "error": f"Node {target_ip} not online after {timeout_seconds}s",
    }


def wait_for_cloudinit_done(
    host, admin_ip: str, target_ip: str, target_hostname: str
) -> Dict[str, Any]:
    """
    Wait for cloud-init to complete on a rebooted node.
    
    Uses core.cloudinit module for the actual verification.
    
    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane
        target_ip: IP of rebooted node
        target_hostname: Hostname of rebooted node
    
    Returns:
        Dict with success, status, retries, elapsed_seconds
    """
    from ...core import wait_for_cloudinit
    
    return wait_for_cloudinit(
        host,
        target_ip,
        hostname=target_hostname,
        retry_limit=CLOUDINIT_RETRY_LIMIT,
        retry_interval=CLOUDINIT_RETRY_INTERVAL,
        passed_statuses=CLOUDINIT_PASSED_STATUSES,
        retry_statuses=CLOUDINIT_RETRY_STATUSES,
        show_progress=True,
    )


def wait_for_node_rejoin_cluster(
    host, admin_ip: str, target_hostname: str, timeout_seconds: int = 120
) -> Dict[str, Any]:
    """
    Wait for a node to rejoin the K8s cluster with Ready status.
    
    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane
        target_hostname: Hostname of node to check
        timeout_seconds: Max seconds to wait
    
    Returns:
        Dict with success, status, elapsed_seconds
    """
    start_time = time.time()
    check_interval = 10
    
    while (time.time() - start_time) < timeout_seconds:
        elapsed = int(time.time() - start_time)
        
        workers = get_k8s_worker_nodes(host, admin_ip)
        
        for w in workers:
            if w["hostname"] == target_hostname:
                if w["status"] == "Ready":
                    print(f"  → Node {target_hostname} rejoined cluster (took {elapsed}s)")
                    return {
                        "success": True,
                        "status": "Ready",
                        "elapsed_seconds": elapsed,
                    }
                else:
                    # Node found but not ready yet
                    break
        
        print(f"  → Waiting for node {target_hostname} to rejoin cluster ({elapsed}s/{timeout_seconds}s)")
        time.sleep(check_interval)
    
    return {
        "success": False,
        "status": "NotReady",
        "elapsed_seconds": timeout_seconds,
        "error": f"Node {target_hostname} did not rejoin cluster after {timeout_seconds}s",
    }
