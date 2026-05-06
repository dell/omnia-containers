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
Core Node Checks Functions.

Functions for checking node connectivity (ping/SSH) and cloud-init status.
Results are cached to avoid repeated checks across tests.
"""

import time
import threading
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .host_func import run_in_container, run_on_remote_node
from ..vars.connectivity_vars import (
    PING_RETRY_LIMIT,
    PING_RETRY_INTERVAL,
    SSH_RETRY_LIMIT,
    SSH_RETRY_INTERVAL,
    MAX_PARALLEL_WORKERS,
)
from ..vars.cloudinit_vars import (
    CLOUDINIT_RETRY_LIMIT,
    CLOUDINIT_RETRY_INTERVAL,
    CLOUDINIT_PASSED_STATUSES,
    CLOUDINIT_RETRY_STATUSES,
    CMD_CLOUDINIT_STATUS,
)


# =============================================================================
# CONNECTIVITY CACHE
# =============================================================================

_connectivity_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.Lock()


def clear_connectivity_cache():
    """Clear the global connectivity cache."""
    global _connectivity_cache
    with _cache_lock:
        _connectivity_cache.clear()


def get_connectivity_cache() -> Dict[str, Dict[str, Any]]:
    """Get a copy of the current connectivity cache."""
    with _cache_lock:
        return _connectivity_cache.copy()


def get_reachable_nodes(nodes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Get nodes that are reachable from cache."""
    with _cache_lock:
        return [
            n for n in nodes
            if _connectivity_cache.get(n.get("admin_ip", ""), {}).get("reachable", False)
        ]


def get_unreachable_nodes(nodes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Get nodes that are unreachable from cache."""
    with _cache_lock:
        return [
            n for n in nodes
            if not _connectivity_cache.get(n.get("admin_ip", ""), {}).get("reachable", False)
        ]


def is_node_reachable(admin_ip: str) -> bool:
    """Check if a node is reachable from cache."""
    with _cache_lock:
        return _connectivity_cache.get(admin_ip, {}).get("reachable", False)


def get_node_error(admin_ip: str) -> str:
    """Get error message for a node from cache."""
    with _cache_lock:
        return _connectivity_cache.get(admin_ip, {}).get("error", "Node not in cache")


# =============================================================================
# SINGLE NODE CONNECTIVITY CHECK
# =============================================================================

def check_node_connectivity_once(host, admin_ip: str, hostname: str = None) -> Dict[str, Any]:
    """
    Check connectivity for a single node once (no retry).

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the node
        hostname: Hostname for display (defaults to admin_ip)

    Returns:
        Dict with connectivity status
    """
    if hostname is None:
        hostname = admin_ip

    result = {
        "hostname": hostname,
        "admin_ip": admin_ip,
        "ping_ok": False,
        "ssh_ok": False,
        "reachable": False,
        "error": "",
    }

    start_time = time.time()

    # Check ping once
    cmd = run_in_container(host, f"ping -c 1 -W 2 {admin_ip} 2>&1")
    if cmd.rc == 0:
        result["ping_ok"] = True
    else:
        result["error"] = f"Node {hostname} ({admin_ip}) not pingable"
        result["elapsed_seconds"] = int(time.time() - start_time)
        return result

    # Check SSH once
    cmd = run_on_remote_node(host, "echo ok 2>&1", admin_ip)
    if cmd.rc == 0 and "ok" in (cmd.stdout or ""):
        result["ssh_ok"] = True
        result["reachable"] = True
    else:
        result["error"] = f"SSH to {hostname} ({admin_ip}) failed"

    result["elapsed_seconds"] = int(time.time() - start_time)
    return result


def check_node_connectivity_with_retry(
    host, admin_ip: str, hostname: str = None,
    ping_retry_limit: int = None, ping_retry_interval: int = None,
    ssh_retry_limit: int = None, ssh_retry_interval: int = None
) -> Dict[str, Any]:
    """
    Check connectivity for a single node with retry logic.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the node
        hostname: Hostname for display
        ping_retry_limit: Max ping retries
        ping_retry_interval: Seconds between ping retries
        ssh_retry_limit: Max SSH retries
        ssh_retry_interval: Seconds between SSH retries

    Returns:
        Dict with connectivity status
    """
    if hostname is None:
        hostname = admin_ip
    if ping_retry_limit is None:
        ping_retry_limit = PING_RETRY_LIMIT
    if ping_retry_interval is None:
        ping_retry_interval = PING_RETRY_INTERVAL
    if ssh_retry_limit is None:
        ssh_retry_limit = SSH_RETRY_LIMIT
    if ssh_retry_interval is None:
        ssh_retry_interval = SSH_RETRY_INTERVAL

    result = {
        "hostname": hostname,
        "admin_ip": admin_ip,
        "ping_ok": False,
        "ssh_ok": False,
        "reachable": False,
        "ping_retries": 0,
        "ssh_retries": 0,
        "error": "",
    }

    start_time = time.time()

    # Check ping with retry
    for retry in range(1, ping_retry_limit + 1):
        result["ping_retries"] = retry
        cmd = run_in_container(host, f"ping -c 1 -W 2 {admin_ip} 2>&1")
        if cmd.rc == 0:
            result["ping_ok"] = True
            break

        # Print progress every 12 retries (1 minute)
        if retry % 12 == 0:
            elapsed = int(time.time() - start_time)
            remaining = (ping_retry_limit - retry) * ping_retry_interval
            print(
                f"    {hostname}: ping retry {retry}/{ping_retry_limit} "
                f"({elapsed}s elapsed, ~{remaining}s remaining)", flush=True
            )

        time.sleep(ping_retry_interval)

    if not result["ping_ok"]:
        result["error"] = (
            f"Node {hostname} ({admin_ip}) not pingable after {ping_retry_limit} attempts"
        )
        result["elapsed_seconds"] = int(time.time() - start_time)
        return result

    # Check SSH with retry
    for retry in range(1, ssh_retry_limit + 1):
        result["ssh_retries"] = retry
        cmd = run_on_remote_node(host, "echo ok 2>&1", admin_ip)
        if cmd.rc == 0 and "ok" in (cmd.stdout or ""):
            result["ssh_ok"] = True
            result["reachable"] = True
            break

        # Print progress every 12 retries (1 minute)
        if retry % 12 == 0:
            elapsed = int(time.time() - start_time)
            remaining = (ssh_retry_limit - retry) * ssh_retry_interval
            print(
                f"    {hostname}: SSH retry {retry}/{ssh_retry_limit} "
                f"({elapsed}s elapsed, ~{remaining}s remaining)", flush=True
            )

        time.sleep(ssh_retry_interval)

    if not result["ssh_ok"]:
        result["error"] = f"SSH to {hostname} ({admin_ip}) failed after {ssh_retry_limit} attempts"

    result["elapsed_seconds"] = int(time.time() - start_time)
    return result


# =============================================================================
# MULTI-NODE CONNECTIVITY CHECK (TWO-PHASE)
# =============================================================================

def verify_nodes_connectivity(
    host, nodes: List[Dict[str, str]],
    ping_retry_limit: int = None, ping_retry_interval: int = None,
    ssh_retry_limit: int = None, ssh_retry_interval: int = None,
    max_workers: int = None, use_cache: bool = True
) -> Dict[str, Any]:
    """
    Verify connectivity to multiple nodes with two-phase approach:
    1. Check all nodes once (parallel, no retry)
    2. Retry only failed nodes with retry logic

    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip, hostname
        ping_retry_limit: Max ping retries per node
        ping_retry_interval: Seconds between ping retries
        ssh_retry_limit: Max SSH retries per node
        ssh_retry_interval: Seconds between SSH retries
        max_workers: Maximum parallel threads
        use_cache: Whether to use cached results

    Returns:
        Dict with success, total, reachable_count, unreachable_count, results
    """
    if max_workers is None:
        max_workers = MAX_PARALLEL_WORKERS

    results = {
        "success": True,
        "total": len(nodes),
        "reachable_count": 0,
        "unreachable_count": 0,
        "results": [],
    }

    if not nodes:
        return results

    print("\n  ═══════════════════════════════════════════════════════════════", flush=True)
    print(f"  Connectivity Check: {len(nodes)} nodes", flush=True)
    print("  ═══════════════════════════════════════════════════════════════\n", flush=True)

    # Check for cached nodes
    nodes_to_check = []
    cached_results = []

    with _cache_lock:
        for node in nodes:
            admin_ip = node.get("admin_ip", "")
            hostname = node.get("hostname", admin_ip)

            if use_cache and admin_ip in _connectivity_cache:
                cached_result = _connectivity_cache[admin_ip].copy()
                cached_results.append(cached_result)
                status = "✓ reachable" if cached_result["reachable"] else "✗ unreachable"
                print(f"  → {hostname}: {status} (cached)", flush=True)
            else:
                nodes_to_check.append(node)

    if not nodes_to_check:
        all_results = cached_results
    else:
        # PHASE 1: Check all nodes once (parallel)
        print(f"\n  → Phase 1: Quick check ({len(nodes_to_check)} nodes)...", flush=True)

        phase1_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_node = {}
            for node in nodes_to_check:
                admin_ip = node.get("admin_ip", "")
                hostname = node.get("hostname", admin_ip)
                future = executor.submit(check_node_connectivity_once, host, admin_ip, hostname)
                future_to_node[future] = node

            for future in as_completed(future_to_node):
                try:
                    result = future.result()
                    phase1_results.append(result)
                    status = "✓ reachable" if result["reachable"] else "✗ unreachable"
                    print(f"  → {result['hostname']}: {status}", flush=True)
                except Exception as e:
                    node = future_to_node[future]
                    admin_ip = node.get("admin_ip", "")
                    hostname = node.get("hostname", admin_ip)
                    error_result = {
                        "hostname": hostname,
                        "admin_ip": admin_ip,
                        "ping_ok": False,
                        "ssh_ok": False,
                        "reachable": False,
                        "error": f"Exception: {e}",
                        "elapsed_seconds": 0,
                    }
                    phase1_results.append(error_result)
                    print(f"  → {hostname}: ✗ exception - {e}", flush=True)

        # Separate passed and failed
        passed_nodes = [r for r in phase1_results if r["reachable"]]
        failed_nodes = [r for r in phase1_results if not r["reachable"]]

        # Cache passed nodes
        with _cache_lock:
            for result in passed_nodes:
                _connectivity_cache[result["admin_ip"]] = result

        print(
            f"\n  → Phase 1 Results: {len(passed_nodes)} passed, {len(failed_nodes)} failed",
            flush=True
        )

        # PHASE 2: Retry failed nodes
        final_results = passed_nodes.copy()

        if failed_nodes:
            print(f"\n  → Phase 2: Retrying {len(failed_nodes)} failed nodes...", flush=True)

            for failed_result in failed_nodes:
                admin_ip = failed_result["admin_ip"]
                hostname = failed_result["hostname"]

                print(f"    Retrying {hostname}...", flush=True)
                retry_result = check_node_connectivity_with_retry(
                    host, admin_ip, hostname,
                    ping_retry_limit, ping_retry_interval,
                    ssh_retry_limit, ssh_retry_interval
                )
                final_results.append(retry_result)

                status = "✓ reachable" if retry_result["reachable"] else "✗ unreachable"
                print(f"    {hostname}: {status}", flush=True)

                # Cache result
                with _cache_lock:
                    _connectivity_cache[retry_result["admin_ip"]] = retry_result

        all_results = cached_results + final_results

    # Process results
    for result in all_results:
        if result["reachable"]:
            results["reachable_count"] += 1
        else:
            results["unreachable_count"] += 1
            results["success"] = False
        results["results"].append(result)

    print("\n  ═══════════════════════════════════════════════════════════════", flush=True)
    print(f"  Summary: {results['reachable_count']}/{results['total']} nodes reachable", flush=True)
    print("  ═══════════════════════════════════════════════════════════════\n", flush=True)

    return results


def check_nodes_reachability(
    host, nodes: List[Dict[str, str]], retry_limit: int = 2, retry_interval: int = 5
) -> Dict[str, Any]:
    """
    Quick reachability check for subsequent tests (uses cache, minimal retry).

    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip, hostname
        retry_limit: Max retries for unreachable nodes (default: 2)
        retry_interval: Seconds between retries (default: 5)

    Returns:
        Dict with reachable and unreachable node lists
    """
    reachable = []
    unreachable = []

    with _cache_lock:
        for node in nodes:
            admin_ip = node.get("admin_ip", "")
            hostname = node.get("hostname", admin_ip)

            if admin_ip in _connectivity_cache:
                if _connectivity_cache[admin_ip]["reachable"]:
                    reachable.append(node)
                else:
                    # Try quick retry for cached unreachable
                    for _ in range(retry_limit):
                        result = check_node_connectivity_once(host, admin_ip, hostname)
                        if result["reachable"]:
                            _connectivity_cache[admin_ip] = result
                            reachable.append(node)
                            break
                        time.sleep(retry_interval)
                    else:
                        err = _connectivity_cache[admin_ip].get("error", "Unreachable")
                        unreachable.append({**node, "error": err})
            else:
                # Not in cache, do quick check
                result = check_node_connectivity_once(host, admin_ip, hostname)
                _connectivity_cache[admin_ip] = result
                if result["reachable"]:
                    reachable.append(node)
                else:
                    unreachable.append({**node, "error": result.get("error", "Unreachable")})

    return {"reachable": reachable, "unreachable": unreachable}


def print_unreachable_nodes(unreachable: List[Dict[str, str]]):
    """Print unreachable nodes with error messages."""
    if unreachable:
        print(f"  → Skipping {len(unreachable)} unreachable nodes:", flush=True)
        for node in unreachable:
            hostname = node.get("hostname", node.get("admin_ip", ""))
            admin_ip = node.get("admin_ip", "")
            error = node.get("error", "Unreachable")
            print(f"    ✗ {hostname} ({admin_ip}): {error}", flush=True)


# =============================================================================
# CLOUD-INIT FUNCTIONS
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
    if "status: running" in output:
        return "running"
    if "status: not started" in output or "not started" in output.lower():
        return "not started"
    if "status: error" in output:
        return "error"
    if cmd.rc != 0 and not output:
        return "command_failed"
    return "unknown"


def wait_for_cloudinit(
    host, target_ip: str, hostname: str = None,
    retry_limit: int = None, retry_interval: int = None,
    passed_statuses: List[str] = None, retry_statuses: List[str] = None,
    show_progress: bool = True,
) -> Dict[str, Any]:
    """
    Wait for cloud-init to complete on a single node.
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

        if show_progress and retry % 6 == 0:
            print(
                f"  → Cloud-init [{hostname}]: {status} "
                f"(retry {retry}/{retry_limit}, {elapsed}s)", flush=True
            )

        if status in passed_statuses:
            return {
                "success": True, "status": status,
                "retries": retry, "elapsed_seconds": elapsed
            }

        if status not in retry_statuses:
            return {
                "success": False, "status": status,
                "retries": retry, "elapsed_seconds": elapsed,
                "error": f"Cloud-init failed with status: {status}"
            }

        time.sleep(retry_interval)

    return {
        "success": False, "status": status, "retries": retry_limit,
        "elapsed_seconds": int(time.time() - start_time),
        "error": f"Cloud-init retry limit ({retry_limit}) reached, status: {status}"
    }


def verify_cloudinit_status(
    host, nodes: List[Dict[str, str]],
    retry_limit: int = None, retry_interval: int = None,
    reachability_retry: int = 2, reachability_interval: int = 5,
) -> Dict[str, Any]:
    """
    Verify cloud-init completed on multiple nodes.
    Uses cached connectivity to skip unreachable nodes.
    """
    if retry_limit is None:
        retry_limit = CLOUDINIT_RETRY_LIMIT
    if retry_interval is None:
        retry_interval = CLOUDINIT_RETRY_INTERVAL

    # Check reachability first
    reach_check = check_nodes_reachability(host, nodes, reachability_retry, reachability_interval)
    reachable = reach_check["reachable"]
    unreachable = reach_check["unreachable"]

    results = {"success": True, "total": len(nodes), "results": []}

    # Print unreachable nodes
    print_unreachable_nodes(unreachable)
    for node in unreachable:
        results["results"].append({
            "hostname": node.get("hostname", ""),
            "admin_ip": node.get("admin_ip", ""),
            "success": False,
            "status": "unreachable",
            "error": node.get("error", "Node unreachable"),
        })
        results["success"] = False

    # Check cloud-init on reachable nodes
    for node in reachable:
        admin_ip = node.get("admin_ip", "")
        hostname = node.get("hostname", admin_ip)

        result = wait_for_cloudinit(host, admin_ip, hostname, retry_limit, retry_interval)

        if result["success"]:
            print(f"  → ✓ {hostname}: cloud-init done", flush=True)
        else:
            print(f"  → ✗ {hostname}: {result.get('error', 'failed')}", flush=True)
            results["success"] = False

        results["results"].append({
            "hostname": hostname,
            "admin_ip": admin_ip,
            "success": result["success"],
            "status": result["status"],
            "error": result.get("error", ""),
        })

    return results
