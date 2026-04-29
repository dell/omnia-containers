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
Core Cloud-Init Functions.

Functions for checking cloud-init status on nodes with retry logic.
Uses connectivity cache to skip unreachable nodes.
"""

import time
from typing import Dict, Any, List

from .host_func_full import run_on_remote_node
from .connectivity_func import get_connectivity_cache
from ..vars.cloudinit_vars import (
    CLOUDINIT_RETRY_LIMIT,
    CLOUDINIT_RETRY_INTERVAL,
    CLOUDINIT_PASSED_STATUSES,
    CLOUDINIT_RETRY_STATUSES,
    CMD_CLOUDINIT_STATUS,
)


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
    cmd = run_on_remote_node(host, CMD_CLOUDINIT_STATUS, target_ip)
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
    Wait for cloud-init to complete on a single node.
    
    Args:
        host: Testinfra host object
        target_ip: IP of node to check
        hostname: Hostname for display (defaults to target_ip)
        retry_limit: Max retries (default: 60)
        retry_interval: Seconds between retries (default: 10)
        passed_statuses: Statuses that indicate success (default: ['done'])
        retry_statuses: Statuses that should retry (default: ['running', 'not started'])
        show_progress: Whether to show progress output
    
    Returns:
        Dict with success, status, retries, elapsed_seconds, error
    """
    if retry_limit is None:
        retry_limit = CLOUDINIT_RETRY_LIMIT
    if retry_interval is None:
        retry_interval = CLOUDINIT_RETRY_INTERVAL
    if passed_statuses is None:
        passed_statuses = CLOUDINIT_PASSED_STATUSES
    if retry_statuses is None:
        retry_statuses = CLOUDINIT_RETRY_STATUSES
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
    skip_unreachable: bool = True,
) -> Dict[str, Any]:
    """
    Verify cloud-init completed on multiple nodes with retry logic.

    Uses connectivity cache to skip unreachable nodes.

    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip, hostname
        retry_limit: Max retries per node
        retry_interval: Seconds between retries
        passed_statuses: Statuses that indicate success
        retry_statuses: Statuses that should retry
        skip_unreachable: Skip nodes that are not reachable (from cache)

    Returns:
        Dict with success, total, results (per-node details)
    """
    if retry_limit is None:
        retry_limit = CLOUDINIT_RETRY_LIMIT
    if retry_interval is None:
        retry_interval = CLOUDINIT_RETRY_INTERVAL
    if passed_statuses is None:
        passed_statuses = CLOUDINIT_PASSED_STATUSES
    if retry_statuses is None:
        retry_statuses = CLOUDINIT_RETRY_STATUSES
    
    connectivity_cache = get_connectivity_cache()
    
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
        
        # Check if node is reachable from cache
        if skip_unreachable and admin_ip in connectivity_cache:
            cache_entry = connectivity_cache[admin_ip]
            if not cache_entry.get("reachable", False):
                # Node is unreachable, skip with appropriate error
                if not cache_entry.get("ping_ok", False):
                    error = f"Node {hostname} is not pingable"
                else:
                    error = f"SSH to {hostname} is not working"
                
                results["results"].append({
                    "hostname": hostname,
                    "admin_ip": admin_ip,
                    "success": False,
                    "status": "skipped",
                    "retries": 0,
                    "errors": error,
                })
                results["success"] = False
                print(f"  → ✗ {hostname}: {error} (skipped)")
                continue
        
        node_statuses[hostname] = {
            "status": "checking",
            "retries": 0,
            "done": False,
            "admin_ip": admin_ip,
        }

    # Retry loop for reachable nodes
    all_done = False
    while not all_done:
        all_done = True

        for hostname, ns in node_statuses.items():
            if ns["done"]:
                continue

            admin_ip = ns["admin_ip"]
            status = get_cloudinit_status(host, admin_ip)
            ns["status"] = status

            if status in passed_statuses:
                ns["done"] = True
                print(f"  → ✓ {hostname}: cloud-init done")
                continue

            if status in retry_statuses:
                ns["retries"] += 1
                if ns["retries"] >= retry_limit:
                    ns["done"] = True
                    ns["status"] = f"{status} (retry limit reached)"
                    print(f"  → ✗ {hostname}: cloud-init {status} (retry limit reached)")
                else:
                    all_done = False
                    if ns["retries"] % 6 == 0:  # Print every minute
                        print(f"  → {hostname}: cloud-init {status} (retry {ns['retries']}/{retry_limit})")
            else:
                ns["done"] = True
                print(f"  → ✗ {hostname}: cloud-init {status}")

        if not all_done:
            time.sleep(retry_interval)

    # Build final results
    for hostname, ns in node_statuses.items():
        admin_ip = ns["admin_ip"]

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
