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
Core Connectivity Functions.

Functions for checking ping and SSH connectivity to nodes with retry logic.
Results are cached to avoid repeated checks across tests.
"""

import time
from typing import Dict, Any, List

from .host_func_full import run_in_container, run_on_remote_node
from ..vars.connectivity_vars import (
    PING_RETRY_LIMIT,
    PING_RETRY_INTERVAL,
    SSH_RETRY_LIMIT,
    SSH_RETRY_INTERVAL,
    CMD_PING_NODE,
    CMD_SSH_CHECK,
)


# =============================================================================
# CONNECTIVITY CACHE
# =============================================================================

_connectivity_cache: Dict[str, Dict[str, Any]] = {}


def get_connectivity_cache() -> Dict[str, Dict[str, Any]]:
    """Get the current connectivity cache."""
    return _connectivity_cache.copy()


def clear_connectivity_cache():
    """Clear the connectivity cache."""
    global _connectivity_cache
    _connectivity_cache = {}


def get_reachable_nodes(nodes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Get nodes that are reachable (ping + SSH) from cache.
    
    Args:
        nodes: List of node dicts with admin_ip
    
    Returns:
        List of reachable nodes
    """
    reachable = []
    for node in nodes:
        admin_ip = node.get("admin_ip", "")
        if admin_ip in _connectivity_cache:
            if _connectivity_cache[admin_ip].get("reachable", False):
                reachable.append(node)
    return reachable


def get_unreachable_nodes(nodes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Get nodes that are unreachable from cache.
    
    Args:
        nodes: List of node dicts with admin_ip
    
    Returns:
        List of unreachable nodes with error info
    """
    unreachable = []
    for node in nodes:
        admin_ip = node.get("admin_ip", "")
        if admin_ip in _connectivity_cache:
            cache_entry = _connectivity_cache[admin_ip]
            if not cache_entry.get("reachable", False):
                unreachable.append({
                    **node,
                    "ping_ok": cache_entry.get("ping_ok", False),
                    "ssh_ok": cache_entry.get("ssh_ok", False),
                    "error": cache_entry.get("error", ""),
                })
    return unreachable


# =============================================================================
# PING CHECK FUNCTIONS
# =============================================================================

def check_node_ping(
    host,
    admin_ip: str,
    hostname: str = None,
    retry_limit: int = None,
    retry_interval: int = None,
) -> Dict[str, Any]:
    """
    Check if a node is pingable with retry logic.
    
    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the node
        hostname: Hostname for display (defaults to admin_ip)
        retry_limit: Max retries (default: 240 = 20 minutes)
        retry_interval: Seconds between retries (default: 5)
    
    Returns:
        Dict with success, ping_ok, retries, elapsed_seconds, error
    """
    if hostname is None:
        hostname = admin_ip
    if retry_limit is None:
        retry_limit = PING_RETRY_LIMIT
    if retry_interval is None:
        retry_interval = PING_RETRY_INTERVAL
    
    start_time = time.time()
    
    for retry in range(1, retry_limit + 1):
        elapsed = int(time.time() - start_time)
        
        cmd = run_in_container(host, CMD_PING_NODE.format(target_ip=admin_ip))
        if cmd.rc == 0:
            return {
                "success": True,
                "ping_ok": True,
                "hostname": hostname,
                "admin_ip": admin_ip,
                "retries": retry,
                "elapsed_seconds": elapsed,
            }
        
        # Print status every 12 retries (1 minute)
        if retry % 12 == 0:
            print(f"  → Waiting for {hostname} to respond to ping ({elapsed}s)")
        
        time.sleep(retry_interval)
    
    elapsed = int(time.time() - start_time)
    return {
        "success": False,
        "ping_ok": False,
        "hostname": hostname,
        "admin_ip": admin_ip,
        "retries": retry_limit,
        "elapsed_seconds": elapsed,
        "error": f"Node {hostname} ({admin_ip}) is not pingable after {elapsed}s",
    }


# =============================================================================
# SSH CHECK FUNCTIONS
# =============================================================================

def check_node_ssh(
    host,
    admin_ip: str,
    hostname: str = None,
    retry_limit: int = None,
    retry_interval: int = None,
) -> Dict[str, Any]:
    """
    Check if SSH to a node is working with retry logic.
    
    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the node
        hostname: Hostname for display (defaults to admin_ip)
        retry_limit: Max retries (default: 60 = 5 minutes)
        retry_interval: Seconds between retries (default: 5)
    
    Returns:
        Dict with success, ssh_ok, retries, elapsed_seconds, error
    """
    if hostname is None:
        hostname = admin_ip
    if retry_limit is None:
        retry_limit = SSH_RETRY_LIMIT
    if retry_interval is None:
        retry_interval = SSH_RETRY_INTERVAL
    
    start_time = time.time()
    
    for retry in range(1, retry_limit + 1):
        elapsed = int(time.time() - start_time)
        
        cmd = run_on_remote_node(host, "echo ok 2>&1", admin_ip)
        if cmd.rc == 0 and "ok" in (cmd.stdout or ""):
            return {
                "success": True,
                "ssh_ok": True,
                "hostname": hostname,
                "admin_ip": admin_ip,
                "retries": retry,
                "elapsed_seconds": elapsed,
            }
        
        # Print status every 12 retries (1 minute)
        if retry % 12 == 0:
            print(f"  → Waiting for SSH on {hostname} ({elapsed}s)")
        
        time.sleep(retry_interval)
    
    elapsed = int(time.time() - start_time)
    return {
        "success": False,
        "ssh_ok": False,
        "hostname": hostname,
        "admin_ip": admin_ip,
        "retries": retry_limit,
        "elapsed_seconds": elapsed,
        "error": f"SSH to {hostname} ({admin_ip}) failed after {elapsed}s",
    }


# =============================================================================
# COMBINED CONNECTIVITY CHECK
# =============================================================================

def check_node_connectivity(
    host,
    admin_ip: str,
    hostname: str = None,
    ping_retry_limit: int = None,
    ping_retry_interval: int = None,
    ssh_retry_limit: int = None,
    ssh_retry_interval: int = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Check if a node is reachable (ping + SSH) with retry logic.
    
    First checks ping with retry, then checks SSH with retry.
    Results are cached to avoid repeated checks.
    
    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the node
        hostname: Hostname for display (defaults to admin_ip)
        ping_retry_limit: Max ping retries (default: 240 = 20 minutes)
        ping_retry_interval: Seconds between ping retries (default: 5)
        ssh_retry_limit: Max SSH retries (default: 60 = 5 minutes)
        ssh_retry_interval: Seconds between SSH retries (default: 5)
        use_cache: Whether to use/update cache (default: True)
    
    Returns:
        Dict with ping_ok, ssh_ok, reachable, retries, elapsed_seconds, error
    """
    global _connectivity_cache
    
    if hostname is None:
        hostname = admin_ip
    
    # Check cache first
    if use_cache and admin_ip in _connectivity_cache:
        return _connectivity_cache[admin_ip]
    
    result = {
        "ping_ok": False,
        "ssh_ok": False,
        "reachable": False,
        "hostname": hostname,
        "admin_ip": admin_ip,
        "ping_retries": 0,
        "ssh_retries": 0,
        "elapsed_seconds": 0,
        "error": "",
    }
    
    start_time = time.time()
    
    # Check ping first
    ping_result = check_node_ping(
        host, admin_ip, hostname,
        retry_limit=ping_retry_limit,
        retry_interval=ping_retry_interval,
    )
    
    result["ping_ok"] = ping_result["ping_ok"]
    result["ping_retries"] = ping_result["retries"]
    
    if not ping_result["success"]:
        result["error"] = ping_result["error"]
        result["elapsed_seconds"] = int(time.time() - start_time)
        if use_cache:
            _connectivity_cache[admin_ip] = result
        return result
    
    # Ping OK, now check SSH
    ssh_result = check_node_ssh(
        host, admin_ip, hostname,
        retry_limit=ssh_retry_limit,
        retry_interval=ssh_retry_interval,
    )
    
    result["ssh_ok"] = ssh_result["ssh_ok"]
    result["ssh_retries"] = ssh_result["retries"]
    result["elapsed_seconds"] = int(time.time() - start_time)
    
    if ssh_result["success"]:
        result["reachable"] = True
    else:
        result["error"] = ssh_result["error"]
    
    if use_cache:
        _connectivity_cache[admin_ip] = result
    
    return result


def verify_nodes_connectivity(
    host,
    nodes: List[Dict[str, str]],
    ping_retry_limit: int = None,
    ping_retry_interval: int = None,
    ssh_retry_limit: int = None,
    ssh_retry_interval: int = None,
) -> Dict[str, Any]:
    """
    Verify connectivity for multiple nodes with retry logic.
    
    Only retries for nodes that are not yet reachable.
    
    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip, hostname
        ping_retry_limit: Max ping retries per node
        ping_retry_interval: Seconds between ping retries
        ssh_retry_limit: Max SSH retries per node
        ssh_retry_interval: Seconds between SSH retries
    
    Returns:
        Dict with success, total, reachable_count, unreachable_count, results
    """
    results = {
        "success": True,
        "total": len(nodes),
        "reachable_count": 0,
        "unreachable_count": 0,
        "results": [],
    }
    
    for node in nodes:
        admin_ip = node.get("admin_ip", "")
        hostname = node.get("hostname", admin_ip)
        
        print(f"  → Checking connectivity to {hostname} ({admin_ip})")
        
        node_result = check_node_connectivity(
            host, admin_ip, hostname,
            ping_retry_limit=ping_retry_limit,
            ping_retry_interval=ping_retry_interval,
            ssh_retry_limit=ssh_retry_limit,
            ssh_retry_interval=ssh_retry_interval,
        )
        
        if node_result["reachable"]:
            results["reachable_count"] += 1
            print(f"  → ✓ {hostname}: reachable (ping: {node_result['ping_retries']} retries, ssh: {node_result['ssh_retries']} retries)")
        else:
            results["unreachable_count"] += 1
            results["success"] = False
            if not node_result["ping_ok"]:
                print(f"  → ✗ {hostname}: not pingable")
            else:
                print(f"  → ✗ {hostname}: ping OK but SSH failed")
        
        results["results"].append(node_result)
    
    return results
