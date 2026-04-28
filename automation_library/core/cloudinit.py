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
Core Cloud-Init Verification Functions.

Functions for checking cloud-init status on nodes with retry logic
and progress bar display. Used by discovery and telemetry modules.
"""

import sys
import time
from typing import Dict, Any, List

from .host import run_on_remote_node


# =============================================================================
# DEFAULT CONFIGURATION
# =============================================================================

DEFAULT_CLOUDINIT_RETRY_LIMIT = 60
DEFAULT_CLOUDINIT_RETRY_INTERVAL = 10
DEFAULT_CLOUDINIT_PASSED_STATUSES = ["done"]
DEFAULT_CLOUDINIT_RETRY_STATUSES = ["running", "not started"]


# =============================================================================
# CLOUD-INIT STATUS FUNCTIONS
# =============================================================================

def get_cloudinit_status(host, target_ip: str) -> str:
    """
    Get cloud-init status from a node.

    Args:
        host: Testinfra host object
        target_ip: Target node IP address

    Returns:
        Status string: 'done', 'running', 'not started', 'error', or 'unknown'
    """
    cmd = run_on_remote_node(host, "cloud-init status 2>&1", target_ip)
    output = cmd.stdout.strip() if cmd.stdout else ""

    if "status: done" in output:
        return "done"
    elif "status: running" in output:
        return "running"
    elif "status: not started" in output or "not started" in output.lower():
        return "not started"
    elif "status: error" in output:
        return "error"
    elif cmd.rc != 0 and not output:
        return "command_failed"
    else:
        return "unknown"


def wait_for_cloudinit(
    host,
    target_ip: str,
    hostname: str = None,
    retry_limit: int = None,
    retry_interval: int = None,
    passed_statuses: List[str] = None,
    retry_statuses: List[str] = None,
    show_progress: bool = True,
) -> Dict[str, Any]:
    """
    Wait for cloud-init to complete on a single node with progress bar.
    
    Args:
        host: Testinfra host object
        target_ip: IP of node to check
        hostname: Hostname for display (defaults to target_ip)
        retry_limit: Max retries (default: 30)
        retry_interval: Seconds between retries (default: 10)
        passed_statuses: Statuses that indicate success (default: ['done'])
        retry_statuses: Statuses that should retry (default: ['running', 'not started'])
        show_progress: Whether to show progress bar
    
    Returns:
        Dict with success, status, retries, elapsed_seconds, error
    """
    # Apply defaults
    if retry_limit is None:
        retry_limit = DEFAULT_CLOUDINIT_RETRY_LIMIT
    if retry_interval is None:
        retry_interval = DEFAULT_CLOUDINIT_RETRY_INTERVAL
    if passed_statuses is None:
        passed_statuses = DEFAULT_CLOUDINIT_PASSED_STATUSES
    if retry_statuses is None:
        retry_statuses = DEFAULT_CLOUDINIT_RETRY_STATUSES
    if hostname is None:
        hostname = target_ip
    
    start_time = time.time()
    status = "checking"
    
    for retry in range(1, retry_limit + 1):
        status = get_cloudinit_status(host, target_ip)
        elapsed = int(time.time() - start_time)
        
        if show_progress:
            print(f"  → Cloud-init [{hostname}]: status={status} (retry {retry}/{retry_limit}, {elapsed}s)")
        
        if status in passed_statuses:
            return {
                "success": True,
                "status": status,
                "retries": retry,
                "elapsed_seconds": elapsed,
            }
        
        if status not in retry_statuses:
            # Error or unknown status - don't retry
            return {
                "success": False,
                "status": status,
                "retries": retry,
                "elapsed_seconds": elapsed,
                "error": f"Cloud-init failed with status: {status}",
            }
        
        time.sleep(retry_interval)
    
    return {
        "success": False,
        "status": status,
        "retries": retry_limit,
        "elapsed_seconds": int(time.time() - start_time),
        "error": f"Cloud-init retry limit ({retry_limit}) reached, status: {status}",
    }


def verify_cloudinit_status_multi(
    host,
    nodes: List[Dict[str, str]],
    retry_limit: int = None,
    retry_interval: int = None,
    passed_statuses: List[str] = None,
    retry_statuses: List[str] = None,
) -> Dict[str, Any]:
    """
    Verify cloud-init completed on multiple nodes with retry logic.

    Progress is printed on a single line that updates in place.

    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip, hostname
        retry_limit: Max retries per node
        retry_interval: Seconds between retries
        passed_statuses: Statuses that indicate success
        retry_statuses: Statuses that should retry

    Returns:
        Dict with success, total, results (per-node details)
    """
    # Apply defaults
    if retry_limit is None:
        retry_limit = DEFAULT_CLOUDINIT_RETRY_LIMIT
    if retry_interval is None:
        retry_interval = DEFAULT_CLOUDINIT_RETRY_INTERVAL
    if passed_statuses is None:
        passed_statuses = DEFAULT_CLOUDINIT_PASSED_STATUSES
    if retry_statuses is None:
        retry_statuses = DEFAULT_CLOUDINIT_RETRY_STATUSES
    
    results = {
        "success": True,
        "total": len(nodes),
        "results": [],
    }

    # Track status for each node
    node_statuses: Dict[str, Dict] = {}
    for node in nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")
        node_statuses[hostname] = {
            "status": "checking",
            "retries": 0,
            "done": False,
            "admin_ip": admin_ip,
        }

    # Retry loop
    all_done = False
    retry_count = 0
    while not all_done:
        all_done = True
        retry_count += 1

        # Print status summary
        done_count = sum(1 for ns in node_statuses.values() if ns["done"])
        status_counts = {}
        for ns in node_statuses.values():
            s = ns["status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        status_str = ", ".join(f"{s}:{c}" for s, c in status_counts.items())
        print(f"  → Cloud-init: {done_count}/{len(nodes)} done | {status_str}")

        for hostname, ns in node_statuses.items():
            if ns["done"]:
                continue

            admin_ip = ns["admin_ip"]
            status = get_cloudinit_status(host, admin_ip)
            ns["status"] = status

            # Check if passed
            if status in passed_statuses:
                ns["done"] = True
                continue

            # Check if should retry
            if status in retry_statuses:
                ns["retries"] += 1
                if ns["retries"] >= retry_limit:
                    ns["done"] = True
                    ns["status"] = f"{status} (retry limit reached)"
                else:
                    all_done = False
            else:
                # Error/unknown - mark as done (failed)
                ns["done"] = True

        # Wait before next retry
        if not all_done:
            time.sleep(retry_interval)

    # Build final results
    for node in nodes:
        hostname = node.get("hostname", "")
        admin_ip = node.get("admin_ip", "")
        ns = node_statuses[hostname]

        node_result = {
            "hostname": hostname,
            "admin_ip": admin_ip,
            "success": ns["status"] in passed_statuses,
            "status": ns["status"],
            "retries": ns["retries"],
            "errors": "",
        }

        if not node_result["success"]:
            if "retry limit" in ns["status"]:
                node_result["errors"] = f"cloud-init {ns['status']}"
            elif ns["status"] == "error":
                node_result["errors"] = "cloud-init completed with errors"
            elif ns["status"] == "command_failed":
                node_result["errors"] = "cloud-init command failed"
            else:
                node_result["errors"] = f"cloud-init status: {ns['status']}"
            results["success"] = False

        results["results"].append(node_result)

    return results
