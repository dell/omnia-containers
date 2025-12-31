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
Telemetry Automation - Core Functions.

This module provides functions for verifying telemetry pods in K8s cluster.
"""

import re
from typing import Dict, Any

from ..vars.telemetry_vars import (
    TELEMETRY_VARS,
    PROVISION_CONFIG_PATH,
    TELEMETRY_NAMESPACE,
    IDRAC_TELEMETRY_POD_PREFIX,
)


# =============================================================================
# TELEMETRY POD VERIFICATION FUNCTIONS
# =============================================================================

def get_service_kube_node_count(host) -> int:
    """
    Get count of service_kube_node entries from PXE mapping file.

    Args:
        host: Testinfra host object

    Returns:
        Count of service_kube_node entries
    """
    container = TELEMETRY_VARS["container_name"]
    provision_config_path = PROVISION_CONFIG_PATH

    # Read provision_config.yml to get pxe_mapping_file_path
    cmd = host.run(f"podman exec {container} cat {provision_config_path}")
    if cmd.rc != 0:
        return 0

    # Extract pxe_mapping_file_path
    match = re.search(
        r'pxe_mapping_file_path:\s*["\']?([^"\'#\n]+)["\']?',
        cmd.stdout
    )
    if not match:
        return 0
    pxe_mapping_path = match.group(1).strip()

    # Read PXE mapping file and count service_kube_node entries
    cmd = host.run(f"podman exec {container} cat {pxe_mapping_path}")
    if cmd.rc != 0:
        return 0

    count = 0
    for line in cmd.stdout.strip().split('\n'):
        if 'service_kube_node' in line.lower():
            count += 1

    return count


def verify_idrac_telemetry_pod_count(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify idrac-telemetry pods count matches expected count.

    SSH to remote node and check kubectl get pods for idrac-telemetry.
    Expected count = service_kube_node count + 1 (for management layer pod).

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of node to SSH to (from PXE mapping file)

    Returns:
        Dict with success, expected_count, actual_count, pods, error
    """
    from ...core.host import run_on_remote_node

    # Get expected count (service_kube_node count + 1 for mgmt)
    service_kube_node_count = get_service_kube_node_count(host)
    expected_count = service_kube_node_count + 1

    # Get idrac-telemetry pods from remote node
    namespace = TELEMETRY_NAMESPACE
    pod_prefix = IDRAC_TELEMETRY_POD_PREFIX
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} -o name 2>/dev/null | grep {pod_prefix}",
        admin_ip
    )

    pods = []
    if cmd.rc == 0 and cmd.stdout.strip():
        pods = [p.strip() for p in cmd.stdout.strip().split('\n') if p.strip()]

    actual_count = len(pods)
    success = actual_count == expected_count

    return {
        "success": success,
        "expected_count": expected_count,
        "actual_count": actual_count,
        "service_kube_node_count": service_kube_node_count,
        "pods": pods,
        "error": "" if success else (
            f"Expected {expected_count} idrac-telemetry pods, found {actual_count}"
        ),
    }


def verify_all_telemetry_pods_running(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify all pods in telemetry namespace are running.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of node to SSH to (from PXE mapping file)

    Returns:
        Dict with success, total_pods, running_pods, not_running_pods, output, error
    """
    from ...core.host import run_on_remote_node

    namespace = TELEMETRY_NAMESPACE

    # Get all pods with status
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} --no-headers 2>/dev/null",
        admin_ip
    )

    if cmd.rc != 0:
        return {
            "success": False,
            "total_pods": 0,
            "running_pods": [],
            "not_running_pods": [],
            "output": "",
            "error": f"Failed to get pods: {cmd.stderr}",
        }

    running_pods = []
    not_running_pods = []

    # Valid statuses: Running for regular pods, Completed for job/cronjob pods
    valid_statuses = ["Running", "Completed"]

    for line in cmd.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 3:
            pod_name = parts[0]
            status = parts[2]
            if status in valid_statuses:
                running_pods.append({
                    "name": pod_name,
                    "status": status,
                    "line": line
                })
            else:
                not_running_pods.append({
                    "name": pod_name,
                    "status": status,
                    "line": line
                })

    total_pods = len(running_pods) + len(not_running_pods)
    success = len(not_running_pods) == 0 and total_pods > 0

    # Get full output with headers for display
    cmd_full = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} -o wide 2>/dev/null",
        admin_ip
    )

    return {
        "success": success,
        "total_pods": total_pods,
        "running_pods": running_pods,
        "not_running_pods": not_running_pods,
        "running_count": len(running_pods),
        "not_running_count": len(not_running_pods),
        "output": cmd_full.stdout if cmd_full.rc == 0 else cmd.stdout,
        "error": "" if success else (
            f"{len(not_running_pods)} pods not in Running state"
        ),
    }
