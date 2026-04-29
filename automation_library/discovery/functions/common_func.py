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
Discovery Module - Common Functions.

Functions for SSH verification and node retrieval used across all tests.
"""

from typing import Dict, Any, List

import sys
import time

import pytest

from automation_library.core import (
    run_on_remote_node,
    run_in_container,
    get_nodes_info,
    SLURM_CONTROL_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_AARCH64_FUNCTIONAL_GROUP,
    LOGIN_NODE_FUNCTIONAL_GROUP,
    LOGIN_NODE_AARCH64_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_AARCH64_FUNCTIONAL_GROUP,
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
    K8S_WORKER_NODE_FUNCTIONAL_GROUP,
)
from ..vars import (
    SSH_OPTS,
    CLOUDINIT_RETRY_LIMIT,
    CLOUDINIT_RETRY_INTERVAL,
    CLOUDINIT_PASSED_STATUSES,
    CLOUDINIT_RETRY_STATUSES,
)
from ..messages import SKIP_MSGS
from .package_collector import (
    get_base_image_packages,
    get_packages_for_functional_group,
    build_package_map,
)


# =============================================================================
# SSH ERROR PARSING
# =============================================================================

def parse_ssh_error(output: str) -> str:
    """
    Extract the first meaningful error line from SSH output.

    SSH outputs errors like:
        ssh: connect to host lcnode port 22: No route to host
        ssh: connect to host 100.33.22.11 port 22: Connection timed out
        Permission denied (publickey,gssapi-keyex,gssapi-with-mic,password).

    This function extracts the first 'ssh:' line or the first meaningful
    error line so the user sees the full error message.

    Args:
        output: Raw SSH stdout+stderr output

    Returns:
        Full first error line from SSH output
    """
    if not output:
        return "No output from SSH command"

    # Look for the first line starting with "ssh:" (the actual error)
    for line in output.strip().split('\n'):
        line = line.strip()
        if line.startswith("ssh:"):
            return line
        if "Permission denied" in line:
            return line
        if "Connection refused" in line:
            return line
        if "Connection timed out" in line or "timed out" in line.lower():
            return line
        if "No route to host" in line:
            return line
        if "Host key verification failed" in line:
            return line
        if "Network is unreachable" in line:
            return line
        if "Name or service not known" in line:
            return line

    # No recognized pattern - return first non-empty line
    for line in output.strip().split('\n'):
        line = line.strip()
        if line:
            return line

    return output.strip()


# =============================================================================
# SSH KEY CLEANUP (handle changed host keys)
# =============================================================================

def cleanup_ssh_known_hosts(host, target: str):
    """
    Remove old SSH host key for target (IP or hostname).

    This handles the case where host keys have changed.
    """
    run_in_container(host, f"ssh-keygen -R {target} 2>/dev/null || true")


# =============================================================================
# NODE CONNECTIVITY CHECK (ping + SSH)
# =============================================================================

# Cache for node connectivity status
_node_connectivity_cache: Dict[str, Dict[str, Any]] = {}


def check_node_connectivity(host, admin_ip: str, hostname: str = None) -> Dict[str, Any]:
    """
    Check if a node is reachable via ping and SSH.
    
    Results are cached to avoid repeated checks.
    
    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the node
        hostname: Hostname for display (defaults to admin_ip)
    
    Returns:
        Dict with ping_ok, ssh_ok, reachable, error
    """
    if hostname is None:
        hostname = admin_ip
    
    # Check cache first
    if admin_ip in _node_connectivity_cache:
        return _node_connectivity_cache[admin_ip]
    
    result = {
        "ping_ok": False,
        "ssh_ok": False,
        "reachable": False,
        "hostname": hostname,
        "admin_ip": admin_ip,
        "error": "",
    }
    
    # Check ping first
    cmd = run_in_container(host, f"ping -c 1 -W 2 {admin_ip} 2>&1")
    if cmd.rc == 0:
        result["ping_ok"] = True
    else:
        result["error"] = f"Node {hostname} ({admin_ip}) is not pingable"
        _node_connectivity_cache[admin_ip] = result
        return result
    
    # Check SSH
    cmd = run_on_remote_node(host, "echo ok 2>&1", admin_ip)
    if cmd.rc == 0 and "ok" in (cmd.stdout or ""):
        result["ssh_ok"] = True
        result["reachable"] = True
    else:
        result["error"] = f"Node {hostname} ({admin_ip}) SSH not working"
    
    _node_connectivity_cache[admin_ip] = result
    return result


def check_nodes_connectivity(host, nodes: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Check connectivity for multiple nodes.
    
    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip, hostname
    
    Returns:
        Dict with success, reachable_nodes, unreachable_nodes
    """
    reachable = []
    unreachable = []
    
    for node in nodes:
        admin_ip = node.get("admin_ip", "")
        hostname = node.get("hostname", admin_ip)
        
        result = check_node_connectivity(host, admin_ip, hostname)
        
        if result["reachable"]:
            reachable.append(node)
        else:
            unreachable.append({
                **node,
                "error": result["error"],
            })
    
    return {
        "success": len(unreachable) == 0,
        "total": len(nodes),
        "reachable_nodes": reachable,
        "unreachable_nodes": unreachable,
    }


def filter_reachable_nodes(host, nodes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter nodes to only those that are reachable (ping + SSH).
    
    Args:
        host: Testinfra host object
        nodes: List of node dicts
    
    Returns:
        List of reachable nodes
    """
    result = check_nodes_connectivity(host, nodes)
    return result["reachable_nodes"]


# =============================================================================
# NODE RETRIEVAL FUNCTIONS
# =============================================================================

def get_slurm_control_nodes(host) -> List[Dict[str, str]]:
    """Get slurm_control_node nodes from PXE mapping."""
    return get_nodes_info(
        host, search_by="functional_group",
        search_value=SLURM_CONTROL_NODE_FUNCTIONAL_GROUP
    )


def get_slurm_compute_nodes(host) -> List[Dict[str, str]]:
    """Get slurm_node (compute) nodes from PXE mapping - both x86_64 and aarch64."""
    nodes = get_nodes_info(
        host, search_by="functional_group",
        search_value=SLURM_NODE_FUNCTIONAL_GROUP
    )
    nodes.extend(get_nodes_info(
        host, search_by="functional_group",
        search_value=SLURM_NODE_AARCH64_FUNCTIONAL_GROUP
    ))
    return nodes


def get_login_nodes(host) -> List[Dict[str, str]]:
    """Get login_node nodes from PXE mapping - both x86_64 and aarch64."""
    nodes = get_nodes_info(
        host, search_by="functional_group",
        search_value=LOGIN_NODE_FUNCTIONAL_GROUP
    )
    nodes.extend(get_nodes_info(
        host, search_by="functional_group",
        search_value=LOGIN_NODE_AARCH64_FUNCTIONAL_GROUP
    ))
    return nodes


def get_login_compiler_nodes(host) -> List[Dict[str, str]]:
    """Get login_compiler_node nodes from PXE mapping - both x86_64 and aarch64."""
    nodes = get_nodes_info(
        host, search_by="functional_group",
        search_value=LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP
    )
    nodes.extend(get_nodes_info(
        host, search_by="functional_group",
        search_value=LOGIN_COMPILER_NODE_AARCH64_FUNCTIONAL_GROUP
    ))
    return nodes


def get_all_slurm_nodes(host) -> List[Dict[str, str]]:
    """Get all Slurm cluster nodes (control, compute, login, login_compiler)."""
    nodes = []
    nodes.extend(get_slurm_control_nodes(host))
    nodes.extend(get_slurm_compute_nodes(host))
    nodes.extend(get_login_nodes(host))
    nodes.extend(get_login_compiler_nodes(host))
    return nodes


def get_k8s_nodes(host) -> List[Dict[str, str]]:
    """Get all K8s cluster nodes (control_plane and worker)."""
    nodes = get_nodes_info(
        host, search_by="functional_group",
        search_value=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP
    )
    nodes.extend(get_nodes_info(
        host, search_by="functional_group",
        search_value=K8S_WORKER_NODE_FUNCTIONAL_GROUP
    ))
    return nodes


# =============================================================================
# SKIP FUNCTIONS
# =============================================================================

def skip_if_no_slurm_nodes(host, log):
    """Skip test if no Slurm nodes in PXE mapping."""
    nodes = get_all_slurm_nodes(host)
    if not nodes:
        msg = SKIP_MSGS["no_slurm_nodes"]
        log.skipped(msg, SKIP_MSGS["skip_detail_no_nodes"].format(node_type="Slurm"))
        pytest.skip(msg)


def skip_if_no_k8s_nodes(host, log):
    """Skip test if no K8s nodes in PXE mapping."""
    nodes = get_k8s_nodes(host)
    if not nodes:
        msg = SKIP_MSGS["no_k8s_nodes"]
        log.skipped(msg, SKIP_MSGS["skip_detail_no_nodes"].format(node_type="K8s"))
        pytest.skip(msg)


# =============================================================================
# SSH VERIFICATION FUNCTIONS
# =============================================================================

def verify_ssh_from_core(
    host, nodes: List[Dict[str, str]], use_hostname: bool = True
) -> Dict[str, Any]:
    """
    Verify SSH from omnia_core to nodes.

    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip, hostname, functional_group
        use_hostname: If True, use hostname; else use admin_ip

    Returns:
        Dict with success, details string, failed_nodes
    """
    results = {
        "success": True,
        "total": len(nodes),
        "failed": 0,
        "failed_nodes": [],
        "details": "",
    }

    # Group nodes by functional_group
    groups: Dict[str, List[Dict]] = {}
    for node in nodes:
        fg = node["functional_group"]
        if fg not in groups:
            groups[fg] = []
        groups[fg].append(node)

    details_lines = []
    for group, group_nodes in groups.items():
        # Show full functional group name
        details_lines.append(f"  [{group}]")
        for node in group_nodes:
            hostname = node["hostname"]
            admin_ip = node["admin_ip"]
            target = hostname if use_hostname else admin_ip

            # First check ping (single attempt, no retry)
            ping_cmd = run_in_container(host, f"ping -c 1 -W 2 {admin_ip} 2>&1")
            if ping_cmd.rc != 0:
                details_lines.append(f"    ✗ {hostname}: Node not reachable (ping failed to {admin_ip})")
                results["failed"] += 1
                results["failed_nodes"].append(hostname)
                results["success"] = False
                continue

            # Cleanup old SSH key first
            cleanup_ssh_known_hosts(host, target)

            # Test SSH - capture output for error details (single attempt)
            cmd = run_on_remote_node(host, "whoami 2>&1", target)
            output = (cmd.stdout or "") + (cmd.stderr or "")
            ok = cmd.rc == 0 and "root" in output

            if ok:
                details_lines.append(f"    ✓ {hostname}")
            else:
                error_msg = parse_ssh_error(output)
                details_lines.append(f"    ✗ {hostname}: SSH failed - {error_msg}")
                results["failed"] += 1
                results["failed_nodes"].append(hostname)
                results["success"] = False

    results["details"] = "\n".join(details_lines)
    return results


def verify_ssh_from_oim(
    host, nodes: List[Dict[str, str]], use_hostname: bool = True
) -> Dict[str, Any]:
    """
    Verify SSH from OIM (inside omnia_core container) to nodes.

    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip, hostname, functional_group
        use_hostname: If True, use hostname; else use admin_ip

    Returns:
        Dict with success, details string, failed_nodes
    """
    results = {
        "success": True,
        "total": len(nodes),
        "failed": 0,
        "failed_nodes": [],
        "details": "",
    }

    # Group nodes by functional_group
    groups: Dict[str, List[Dict]] = {}
    for node in nodes:
        fg = node["functional_group"]
        if fg not in groups:
            groups[fg] = []
        groups[fg].append(node)

    details_lines = []
    for group, group_nodes in groups.items():
        # Show full functional group name
        details_lines.append(f"  [{group}]")
        for node in group_nodes:
            hostname = node["hostname"]
            admin_ip = node["admin_ip"]
            target = hostname if use_hostname else admin_ip

            # First check ping (single attempt, no retry)
            ping_cmd = run_in_container(host, f"ping -c 1 -W 2 {admin_ip} 2>&1")
            if ping_cmd.rc != 0:
                details_lines.append(f"    ✗ {hostname}: Node not reachable (ping failed to {admin_ip})")
                results["failed"] += 1
                results["failed_nodes"].append(hostname)
                results["success"] = False
                continue

            # Cleanup old SSH key first
            cleanup_ssh_known_hosts(host, target)

            # Test SSH from inside container - capture stderr for error details (single attempt)
            ssh_cmd = f"ssh {SSH_OPTS} root@{target} whoami 2>&1"
            cmd = run_in_container(host, ssh_cmd)
            output = cmd.stdout.strip() if cmd.stdout else ""
            ok = cmd.rc == 0 and "root" in output

            if ok:
                details_lines.append(f"    ✓ {hostname}")
            else:
                error_msg = parse_ssh_error(output)
                details_lines.append(f"    ✗ {hostname}: SSH failed - {error_msg}")
                results["failed"] += 1
                results["failed_nodes"].append(hostname)
                results["success"] = False

    results["details"] = "\n".join(details_lines)
    return results


# =============================================================================
# CLOUD-INIT VERIFICATION (uses core module)
# =============================================================================

def verify_cloudinit_status(host, nodes: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Verify cloud-init completed successfully on all nodes with retry logic.

    For diskless OS deployments, cloud-init handles provisioning.
    Uses core.cloudinit module for the actual verification.

    Args:
        host: Testinfra host object
        nodes: List of node dicts with admin_ip, hostname

    Returns:
        Dict with success, total, results (per-node details)
    """
    from automation_library.core import verify_cloudinit_status_multi
    
    return verify_cloudinit_status_multi(
        host,
        nodes,
        retry_limit=CLOUDINIT_RETRY_LIMIT,
        retry_interval=CLOUDINIT_RETRY_INTERVAL,
        passed_statuses=CLOUDINIT_PASSED_STATUSES,
        retry_statuses=CLOUDINIT_RETRY_STATUSES,
    )


# =============================================================================
# K8S NODE VERIFICATION
# =============================================================================

def verify_k8s_nodes_ready(host, expected_nodes: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Verify K8s nodes from PXE mapping are Ready and no extra nodes exist.

    Args:
        host: Testinfra host object
        expected_nodes: List of K8s node dicts from PXE mapping

    Returns:
        Dict with success, expected, actual, missing, extra, not_ready, node_results
    """
    results = {
        "success": True,
        "expected": [n.get("hostname", "") for n in expected_nodes],
        "actual": [],
        "missing": [],
        "extra": [],
        "not_ready": [],
        "node_results": [],
    }

    if not expected_nodes:
        return results

    # Get first control plane node to run kubectl
    control_plane = None
    for node in expected_nodes:
        fg = node.get("functional_group", "")
        if "control_plane" in fg.lower():
            control_plane = node
            break

    if not control_plane:
        results["success"] = False
        results["error"] = "No control plane node found in expected nodes"
        return results

    admin_ip = control_plane.get("admin_ip", "")

    # Get actual nodes from cluster
    cmd = run_on_remote_node(host, "kubectl get nodes --no-headers", admin_ip)
    if cmd.rc != 0:
        results["success"] = False
        results["error"] = f"kubectl get nodes failed: {cmd.stderr}"
        return results

    # Parse kubectl output: NAME STATUS ROLES AGE VERSION
    cluster_nodes = {}
    for line in cmd.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            node_name = parts[0]
            node_status = parts[1]
            cluster_nodes[node_name] = node_status
            results["actual"].append(node_name)

    # Check each expected node
    for node in expected_nodes:
        hostname = node.get("hostname", "")
        admin_ip_node = node.get("admin_ip", "")

        node_result = {
            "hostname": hostname,
            "admin_ip": admin_ip_node,
            "found": False,
            "ready": False,
            "status": "NotFound",
        }

        # Check if node exists in cluster (by hostname or IP)
        found_name = None
        for cluster_name in cluster_nodes:
            if hostname == cluster_name or admin_ip_node == cluster_name:
                found_name = cluster_name
                break

        if found_name:
            node_result["found"] = True
            node_result["status"] = cluster_nodes[found_name]
            node_result["ready"] = cluster_nodes[found_name] == "Ready"

            if not node_result["ready"]:
                results["not_ready"].append(hostname)
                results["success"] = False
        else:
            results["missing"].append(hostname)
            results["success"] = False

        results["node_results"].append(node_result)

    # Check for extra nodes (in cluster but not in PXE mapping)
    expected_identifiers = set()
    for node in expected_nodes:
        expected_identifiers.add(node.get("hostname", ""))
        expected_identifiers.add(node.get("admin_ip", ""))

    for cluster_name in cluster_nodes:
        if cluster_name not in expected_identifiers:
            results["extra"].append(cluster_name)
            results["success"] = False

    return results


# =============================================================================
# K8S TELEMETRY PODS VERIFICATION
# =============================================================================

def verify_k8s_telemetry_pods(host, k8s_nodes: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Verify telemetry pods are running in K8s cluster based on telemetry_config.

    Checks pods in telemetry namespace based on configuration:
    - LDMS pods (nersc-ldms-aggr, nersc-ldms-store) if ldms enabled in software_config
    - iDRAC telemetry pods if idrac_telemetry_support is true
    - VictoriaMetrics pods based on deployment_mode (single-node vs cluster)
    - Kafka pods (always expected for telemetry)

    Args:
        host: Testinfra host object
        k8s_nodes: List of K8s node dicts from PXE mapping

    Returns:
        Dict with success, expected_pods, running_pods, missing_pods, deployment_mode
    """
    from automation_library.core import is_software_enabled, load_input_file, TELEMETRY_CONFIG_FILE

    results = {
        "success": True,
        "expected_pods": [],
        "running_pods": [],
        "missing_pods": [],
        "pod_details": [],
        "deployment_mode": "",
        "ldms_enabled": False,
        "idrac_enabled": False,
    }

    if not k8s_nodes:
        results["error"] = "No K8s nodes provided"
        return results

    # Get control plane node
    control_plane = None
    for node in k8s_nodes:
        fg = node.get("functional_group", "")
        if "control_plane" in fg.lower():
            control_plane = node
            break

    if not control_plane:
        results["error"] = "No control plane node found"
        results["success"] = False
        return results

    admin_ip = control_plane.get("admin_ip", "")

    # Check telemetry config for enabled features
    telemetry_config = load_input_file(host, TELEMETRY_CONFIG_FILE)

    # Build expected pods based on configuration
    expected_prefixes = []

    # LDMS pods - only if ldms enabled in software_config
    ldms_enabled = is_software_enabled(host, "ldms")
    results["ldms_enabled"] = ldms_enabled
    if ldms_enabled:
        expected_prefixes.extend(["nersc-ldms-aggr", "nersc-ldms-store"])

    # iDRAC telemetry pods - only if idrac_telemetry_support is true
    idrac_enabled = telemetry_config.get("idrac_telemetry_support", False) if telemetry_config else False
    results["idrac_enabled"] = idrac_enabled
    if idrac_enabled:
        expected_prefixes.append("idrac-telemetry")

    # VictoriaMetrics pods based on deployment_mode
    victoria_config = telemetry_config.get("victoria_configurations", {}) if telemetry_config else {}
    deployment_mode = victoria_config.get("deployment_mode", "cluster")
    results["deployment_mode"] = deployment_mode

    if deployment_mode == "single-node":
        # Single-node mode: victoria-metric statefulset + vmagent
        expected_prefixes.extend(["victoria-metric", "vmagent"])
    else:
        # Cluster mode: vminsert, vmselect, vmstorage, vmagent
        expected_prefixes.extend(["vmagent", "vminsert", "vmselect", "vmstorage"])

    # Kafka pods (always expected for telemetry)
    expected_prefixes.extend(["kafka-broker", "kafka-controller", "strimzi-cluster-operator"])

    results["expected_pods"] = expected_prefixes

    # Get running pods in telemetry namespace
    cmd = run_on_remote_node(
        host,
        "kubectl get pods -n telemetry --no-headers"
        " -o custom-columns=NAME:.metadata.name,STATUS:.status.phase 2>/dev/null",
        admin_ip
    )

    if cmd.rc != 0:
        results["error"] = f"Failed to get pods: {cmd.stderr}"
        results["success"] = False
        return results

    # Parse pod output
    running_pods = {}
    for line in cmd.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            pod_name = parts[0]
            pod_status = parts[1]
            running_pods[pod_name] = pod_status
            results["running_pods"].append(pod_name)

    # Check each expected prefix has at least one running pod
    for prefix in expected_prefixes:
        found = False
        for pod_name, status in running_pods.items():
            if pod_name.startswith(prefix):
                found = True
                is_running = status in ["Running", "Completed"]
                results["pod_details"].append({
                    "prefix": prefix,
                    "pod_name": pod_name,
                    "status": status,
                    "running": is_running,
                })
                if not is_running:
                    results["success"] = False
                break

        if not found:
            results["missing_pods"].append(prefix)
            results["success"] = False

    return results


# =============================================================================
# NODE PACKAGE VERIFICATION
# =============================================================================


def _verify_packages_on_node(
    host,
    node: Dict[str, str],
    packages: List[str],
) -> Dict[str, Any]:
    """
    Verify expected packages are installed on a single node via rpm -qa.

    Uses same matching strategies as build_image_func.py _verify_single_image_packages():
    - Strategy 1: installed name starts with base package name
    - Strategy 2: base package name contained and is prefix of installed name
    - Strategy 3: python3.X -> python3-X.Y RHEL naming convention

    Returns package_details matching build_image test format:
        [{"expected": pkg, "found": found_version_or_None, "status": "installed"|"missing"}]

    Args:
        host: Testinfra host object
        node: Node dict with hostname, admin_ip, functional_group
        packages: List of expected package names

    Returns:
        Dict with success, hostname, found_packages, missing_packages,
        package_details, details, error
    """
    hostname = node.get("hostname", "")
    admin_ip = node.get("admin_ip", "")

    if not packages:
        return {
            "hostname": hostname,
            "success": True,
            "found_packages": [],
            "missing_packages": [],
            "package_details": [],
            "details": "No packages defined in image YAML for this functional group",
            "error": None,
        }

    cmd = run_on_remote_node(host, "rpm -qa 2>/dev/null", admin_ip)
    if cmd.rc != 0:
        return {
            "hostname": hostname,
            "success": False,
            "found_packages": [],
            "missing_packages": packages,
            "package_details": [],
            "details": None,
            "error": f"rpm -qa failed on {hostname}: {cmd.stderr or cmd.stdout}",
        }

    installed_packages = [
        line.strip()
        for line in cmd.stdout.strip().split("\n")
        if line.strip()
    ]

    found_packages: List[str] = []
    missing_packages: List[str] = []
    package_details: List[Dict[str, Any]] = []

    for pkg in packages:
        base_pkg = (
            pkg.split("-")[0]
            if "-" in pkg and pkg.split("-")[-1][0].isdigit()
            else pkg
        )

        found = False
        found_version = None

        for installed in installed_packages:
            inst_lower = installed.lower()
            base_lower = base_pkg.lower()
            if inst_lower.startswith(base_lower):
                found = True
                found_version = installed
                break
            if base_lower in inst_lower and inst_lower.split("-")[0] == base_lower:
                found = True
                found_version = installed
                break
            if base_lower.startswith("python") and "." in base_lower:
                py_version = base_lower.replace("python", "")
                if inst_lower.startswith(f"python3-{py_version}"):
                    found = True
                    found_version = installed
                    break

        if found:
            found_packages.append(pkg)
            package_details.append({"expected": pkg, "found": found_version, "status": "installed"})
        else:
            missing_packages.append(pkg)
            package_details.append({"expected": pkg, "found": None, "status": "missing"})

    success = len(missing_packages) == 0
    details_lines = [f"  {len(found_packages)}/{len(packages)} packages installed"]
    if missing_packages:
        details_lines.append(f"  Missing: {', '.join(missing_packages)}")

    return {
        "hostname": hostname,
        "success": success,
        "found_packages": found_packages,
        "missing_packages": missing_packages,
        "package_details": package_details,
        "details": "\n".join(details_lines),
        "error": f"Missing: {', '.join(missing_packages)}" if missing_packages else None,
    }


def verify_node_packages(host, nodes: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Verify all expected packages are installed on each provisioned node.

    Delegates package collection to package_collector.py which replicates
    the exact same logic as build_image_x86_64 playbook:
    1. Reads all functional groups dynamically from PXE mapping (no hardcoding)
    2. For each FG finds its image YAML in IMAGE_CONFIG_YAML_DIR via glob
    3. Combines base image packages + compute packages (deduplicated)
    4. SSHs to each node and verifies via rpm -qa

    Args:
        host: Testinfra host object
        nodes: List of node dicts with hostname, admin_ip, functional_group

    Returns:
        Dict with success, total, passed, failed, results (per-node with
        package_details), nodes_missing_packages, error
    """
    result: Dict[str, Any] = {
        "success": True,
        "total": len(nodes),
        "passed": 0,
        "failed": 0,
        "results": [],
        "nodes_missing_packages": [],
        "error": None,
    }

    # Build complete package map for all FGs present in PXE mapping
    # package_collector reads FGs dynamically - no hardcoding
    package_map = build_package_map(host)

    # Also build per-arch base packages cache for any FGs not in package_map
    x86_base: List[str] = []
    aarch64_base: List[str] = []

    _fg_pkg_cache: Dict[str, List[str]] = {}

    for node in nodes:
        functional_group = node.get("functional_group", "")

        if functional_group not in _fg_pkg_cache:
            if functional_group in package_map:
                _fg_pkg_cache[functional_group] = package_map[functional_group]
            else:
                # FG not in PXE mapping but present in nodes: collect on-demand
                arch = "aarch64" if "aarch64" in functional_group else "x86_64"
                if arch == "x86_64":
                    if not x86_base:
                        x86_base = get_base_image_packages(host, "x86_64")
                    base = x86_base
                else:
                    if not aarch64_base:
                        aarch64_base = get_base_image_packages(host, "aarch64")
                    base = aarch64_base
                _fg_pkg_cache[functional_group] = get_packages_for_functional_group(
                    host, functional_group, base
                )

        packages = _fg_pkg_cache[functional_group]
        node_result = _verify_packages_on_node(host, node, packages)
        result["results"].append(node_result)

        if node_result["success"]:
            result["passed"] += 1
        else:
            result["failed"] += 1
            result["success"] = False
            result["nodes_missing_packages"].append(node_result["hostname"])

    return result
