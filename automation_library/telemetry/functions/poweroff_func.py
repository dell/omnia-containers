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
Telemetry Poweroff Test Functions.

Functions for verifying telemetry pod rescheduling after node poweroff.
"""

import sys
import time
from typing import Dict, Any, List

from ...core import (
    run_on_remote_node,
    is_software_enabled,
)
from ..vars import TELEMETRY_NAMESPACE
from ..vars.poweroff_vars import (
    POD_RESCHEDULE_RETRY_LIMIT,
    POD_RESCHEDULE_RETRY_INTERVAL,
    NODE_POWEROFF_WAIT_SECONDS,
    POD_RUNNING_STATUSES,
    CMD_GET_WORKER_NODES,
    CMD_GET_PODS_ON_NODE,
    CMD_GET_ALL_PODS,
    CMD_SSH_POWEROFF,
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
        List of dicts with name, status, ip keys
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
                "name": parts[0],
                "status": parts[1],
                "ip": parts[5],
            })

    return workers


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


def _print_pod_progress(
    pods_status: Dict[str, Dict],
    powered_off_node: str,
    retry_count: int,
    max_retries: int
):
    """
    Print single-line progress that updates in place.

    Args:
        pods_status: Dict of pod_name -> {status, node, rescheduled}
        powered_off_node: Name of the powered-off node
        retry_count: Current retry count
        max_retries: Maximum retries
    """
    rescheduled = sum(1 for ps in pods_status.values() if ps["rescheduled"])
    total = len(pods_status)

    # Build status summary
    status_parts = []
    for pod_name, ps in list(pods_status.items())[:5]:  # Show first 5
        short_name = pod_name[:15] + ".." if len(pod_name) > 17 else pod_name
        if ps["rescheduled"]:
            status_parts.append(f"{short_name}[\u2713]")
        else:
            status_parts.append(f"{short_name}[{ps['status']}]")

    if len(pods_status) > 5:
        status_parts.append(f"...+{len(pods_status) - 5}")

    line = (
        f"\rPod reschedule: {rescheduled}/{total} done, "
        f"retry {retry_count}/{max_retries} | " + " ".join(status_parts)
    )

    # Truncate and pad
    max_width = 120
    if len(line) > max_width:
        line = line[:max_width - 3] + "..."
    line = line.ljust(max_width)

    sys.stdout.write(line)
    sys.stdout.flush()


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

    # Print initial progress
    _print_pod_progress(pods_status, powered_off_node, 0, POD_RESCHEDULE_RETRY_LIMIT)

    # Retry loop
    for retry in range(1, POD_RESCHEDULE_RETRY_LIMIT + 1):
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

        # Update progress
        _print_pod_progress(pods_status, powered_off_node, retry, POD_RESCHEDULE_RETRY_LIMIT)

        if all_rescheduled:
            break

        # Wait before next retry
        time.sleep(POD_RESCHEDULE_RETRY_INTERVAL)

    # Print newline after progress
    sys.stdout.write("\n")
    sys.stdout.flush()

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
