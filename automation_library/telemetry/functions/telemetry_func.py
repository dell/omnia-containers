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

This module provides functions for:
- Running telemetry.yml playbook
- Checking prerequisite files (provision_config.yml, pxe_mapping_file, etc.)
- Verifying telemetry pods (VictoriaMetrics, Kafka, iDRAC telemetry)
"""

import re
from typing import Dict, Any, List, Optional

from ..vars.telemetry_vars import (
    TELEMETRY_VARS,
    PROVISION_CONFIG_PATH,
    BMC_GROUP_DATA_PATH,
    SERVICE_CLUSTER_METADATA_PATH,
    TELEMETRY_NAMESPACE,
    IDRAC_TELEMETRY_POD_PREFIX,
)


# =============================================================================
# PREREQUISITE CHECK FUNCTIONS
# =============================================================================

def check_file_exists(host, file_path: str) -> Dict[str, Any]:
    """
    Check if a file exists inside the omnia_core container.

    Args:
        host: Testinfra host object
        file_path: Path to file inside container

    Returns:
        Dict with success, exists, path, error keys
    """
    container = TELEMETRY_VARS["container_name"]
    check_cmd = f"test -f {file_path} && echo 'EXISTS' || echo 'NOT_FOUND'"
    cmd = host.run(f"podman exec {container} {check_cmd}")

    exists = "EXISTS" in cmd.stdout
    return {
        "success": exists,
        "exists": exists,
        "path": file_path,
        "error": "" if exists else f"File not found: {file_path}",
    }


def check_provision_config(host) -> Dict[str, Any]:
    """
    Check if provision_config.yml exists inside omnia_core container.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, path, pxe_mapping_file_path, error keys
    """
    container = TELEMETRY_VARS["container_name"]
    config_path = PROVISION_CONFIG_PATH

    # Check if file exists
    result = check_file_exists(host, config_path)
    if not result["success"]:
        return {
            "success": False,
            "path": config_path,
            "pxe_mapping_file_path": None,
            "error": f"provision_config.yml not found at {config_path}",
        }

    # Read the file and extract pxe_mapping_file_path
    cmd = host.run(f"podman exec {container} cat {config_path}")
    if cmd.rc != 0:
        return {
            "success": False,
            "path": config_path,
            "pxe_mapping_file_path": None,
            "error": f"Failed to read provision_config.yml: {cmd.stderr}",
        }

    # Parse YAML to get pxe_mapping_file_path
    pxe_mapping_path = None
    for line in cmd.stdout.splitlines():
        if "pxe_mapping_file_path:" in line:
            # Extract the path value
            match = re.search(r'pxe_mapping_file_path:\s*["\']?([^"\'#\n]+)["\']?', line)
            if match:
                pxe_mapping_path = match.group(1).strip()
                break

    if not pxe_mapping_path:
        return {
            "success": True,
            "path": config_path,
            "pxe_mapping_file_path": None,
            "error": "pxe_mapping_file_path not found in provision_config.yml",
        }

    return {
        "success": True,
        "path": config_path,
        "pxe_mapping_file_path": pxe_mapping_path,
        "error": "",
    }


def check_pxe_mapping_file(host, pxe_mapping_path: str) -> Dict[str, Any]:
    """
    Check if PXE mapping file exists and count service_kube_node entries.

    Args:
        host: Testinfra host object
        pxe_mapping_path: Path to PXE mapping file inside container

    Returns:
        Dict with success, path, service_kube_node_count, error keys
    """
    container = TELEMETRY_VARS["container_name"]

    # Check if file exists
    result = check_file_exists(host, pxe_mapping_path)
    if not result["success"]:
        return {
            "success": False,
            "path": pxe_mapping_path,
            "service_kube_node_count": 0,
            "error": f"PXE mapping file not found at {pxe_mapping_path}",
        }

    # Read file and count service_kube_node entries
    cmd = host.run(f"podman exec {container} cat {pxe_mapping_path}")
    if cmd.rc != 0:
        return {
            "success": False,
            "path": pxe_mapping_path,
            "service_kube_node_count": 0,
            "error": f"Failed to read PXE mapping file: {cmd.stderr}",
        }

    # Count service_kube_node entries (CSV format)
    service_kube_node_count = 0
    for line in cmd.stdout.splitlines():
        if "service_kube_node" in line.lower():
            service_kube_node_count += 1

    return {
        "success": True,
        "path": pxe_mapping_path,
        "service_kube_node_count": service_kube_node_count,
        "content": cmd.stdout,
        "error": "",
    }


def check_bmc_group_data(host) -> Dict[str, Any]:
    """
    Check if bmc_group_data.csv exists inside omnia_core container.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, path, error keys
    """
    return check_file_exists(host, BMC_GROUP_DATA_PATH)


def check_service_cluster_metadata(host) -> Dict[str, Any]:
    """
    Check if service_cluster_metadata.yml exists inside omnia_core container.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, path, content, error keys
    """
    container = TELEMETRY_VARS["container_name"]
    metadata_path = SERVICE_CLUSTER_METADATA_PATH

    result = check_file_exists(host, metadata_path)
    if not result["success"]:
        return {
            "success": False,
            "path": metadata_path,
            "content": None,
            "error": f"service_cluster_metadata.yml not found at {metadata_path}",
        }

    # Read the content
    cmd = host.run(f"podman exec {container} cat {metadata_path}")
    return {
        "success": True,
        "path": metadata_path,
        "content": cmd.stdout if cmd.rc == 0 else None,
        "error": "" if cmd.rc == 0 else cmd.stderr,
    }


def check_telemetry_prerequisites(host) -> Dict[str, Any]:
    """
    Run all telemetry prerequisite checks.

    Args:
        host: Testinfra host object

    Returns:
        Dict with overall success and individual check results
    """
    results = {
        "success": True,
        "checks": {},
        "errors": [],
    }

    # Check provision_config.yml
    provision_result = check_provision_config(host)
    results["checks"]["provision_config"] = provision_result
    if not provision_result["success"]:
        results["success"] = False
        results["errors"].append(provision_result["error"])

    # Check PXE mapping file if provision_config exists
    if provision_result.get("pxe_mapping_file_path"):
        pxe_result = check_pxe_mapping_file(host, provision_result["pxe_mapping_file_path"])
        results["checks"]["pxe_mapping_file"] = pxe_result
        if not pxe_result["success"]:
            results["success"] = False
            results["errors"].append(pxe_result["error"])

    # Check bmc_group_data.csv
    bmc_result = check_bmc_group_data(host)
    results["checks"]["bmc_group_data"] = bmc_result
    if not bmc_result["success"]:
        results["success"] = False
        results["errors"].append(bmc_result["error"])

    # Check service_cluster_metadata.yml
    metadata_result = check_service_cluster_metadata(host)
    results["checks"]["service_cluster_metadata"] = metadata_result
    if not metadata_result["success"]:
        results["success"] = False
        results["errors"].append(metadata_result["error"])

    return results


# =============================================================================
# CONTAINER CHECK FUNCTIONS
# =============================================================================

def check_container_running(host, container_name: str = None) -> Dict[str, Any]:
    """
    Check if a container is running on the OIM server.

    Args:
        host: Testinfra host object
        container_name: Name of container (default: omnia_core)

    Returns:
        Dict with success, status, error keys
    """
    if container_name is None:
        container_name = TELEMETRY_VARS["container_name"]

    ps_format = "'{{.Names}} {{.Status}}'"
    cmd = host.run(f"podman ps --format {ps_format} | grep -w {container_name}")

    if cmd.rc == 0 and container_name in cmd.stdout:
        status = cmd.stdout.strip()
        return {
            "success": True,
            "status": status,
            "error": "",
        }

    # Check if container exists but not running
    cmd_all = host.run(
        f"podman ps -a --format {ps_format} | grep -w {container_name}"
    )
    if cmd_all.rc == 0:
        status = cmd_all.stdout.strip()
        return {
            "success": False,
            "status": status,
            "error": f"Container {container_name} exists but is not running",
        }

    return {
        "success": False,
        "status": "not found",
        "error": f"Container {container_name} not found",
    }


# =============================================================================
# TELEMETRY POD CHECK FUNCTIONS
# =============================================================================

def check_telemetry_namespace(host) -> Dict[str, Any]:
    """
    Check if telemetry namespace exists in K8s cluster.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, namespace, error keys
    """
    container = TELEMETRY_VARS["container_name"]
    namespace = TELEMETRY_NAMESPACE

    cmd = host.run(f"podman exec {container} kubectl get namespace {namespace} -o name 2>/dev/null")

    if cmd.rc == 0 and namespace in cmd.stdout:
        return {
            "success": True,
            "namespace": namespace,
            "error": "",
        }

    return {
        "success": False,
        "namespace": namespace,
        "error": f"Namespace '{namespace}' not found",
    }


def check_pods_running(host, pod_prefix: str, namespace: str = None) -> Dict[str, Any]:
    """
    Check if pods with given prefix are running in namespace.

    Args:
        host: Testinfra host object
        pod_prefix: Prefix of pod names to check
        namespace: K8s namespace (default: telemetry)

    Returns:
        Dict with success, running_pods, total_pods, error keys
    """
    container = TELEMETRY_VARS["container_name"]
    if namespace is None:
        namespace = TELEMETRY_NAMESPACE

    cmd = host.run(
        f"podman exec {container} kubectl get pods -n {namespace} "
        f"--field-selector=status.phase=Running -o name 2>/dev/null | grep {pod_prefix}"
    )

    running_pods = []
    if cmd.rc == 0 and cmd.stdout.strip():
        running_pods = [p.strip() for p in cmd.stdout.strip().splitlines() if p.strip()]

    # Get total pods with this prefix
    cmd_all = host.run(
        f"podman exec {container} kubectl get pods -n {namespace} "
        f"-o name 2>/dev/null | grep {pod_prefix}"
    )

    total_pods = []
    if cmd_all.rc == 0 and cmd_all.stdout.strip():
        total_pods = [p.strip() for p in cmd_all.stdout.strip().splitlines() if p.strip()]

    success = len(running_pods) > 0 and len(running_pods) == len(total_pods)

    return {
        "success": success,
        "running_pods": running_pods,
        "total_pods": total_pods,
        "running_count": len(running_pods),
        "total_count": len(total_pods),
        "error": "" if success else f"Not all {pod_prefix} pods are running",
    }


def check_victoria_pods_running(host) -> Dict[str, Any]:
    """
    Check if VictoriaMetrics pods are running.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success and pod status details
    """
    results = {
        "success": True,
        "pods": {},
        "errors": [],
    }

    for pod_prefix in TELEMETRY_VARS["victoria_pods"]:
        result = check_pods_running(host, pod_prefix)
        results["pods"][pod_prefix] = result
        if not result["success"]:
            results["success"] = False
            results["errors"].append(f"{pod_prefix}: {result['error']}")

    return results


def check_kafka_pods_running(host) -> Dict[str, Any]:
    """
    Check if Kafka pods are running.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success and pod status details
    """
    results = {
        "success": True,
        "pods": {},
        "errors": [],
    }

    for pod_prefix in TELEMETRY_VARS["kafka_pods"]:
        result = check_pods_running(host, pod_prefix)
        results["pods"][pod_prefix] = result
        if not result["success"]:
            results["success"] = False
            results["errors"].append(f"{pod_prefix}: {result['error']}")

    return results


def check_idrac_telemetry_pods_running(host) -> Dict[str, Any]:
    """
    Check if iDRAC telemetry pods are running.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success and pod status details
    """
    results = {
        "success": True,
        "pods": {},
        "errors": [],
    }

    for pod_prefix in TELEMETRY_VARS["idrac_telemetry_pods"]:
        result = check_pods_running(host, pod_prefix)
        results["pods"][pod_prefix] = result
        if not result["success"]:
            results["success"] = False
            results["errors"].append(f"{pod_prefix}: {result['error']}")

    return results


# =============================================================================
# PLAYBOOK EXECUTION FUNCTIONS
# =============================================================================

def run_telemetry_playbook(host, timeout: int = 1800) -> Dict[str, Any]:
    """
    Execute telemetry.yml playbook inside omnia_core container.

    Args:
        host: Testinfra host object
        timeout: Timeout in seconds (default: 30 minutes)

    Returns:
        Dict with success, stdout, stderr, exit_code keys
    """
    container = TELEMETRY_VARS["container_name"]
    playbook = TELEMETRY_VARS["telemetry_playbook"]

    cmd = host.run(
        f"podman exec -w /omnia {container} ansible-playbook {playbook} -v",
    )

    return {
        "success": cmd.rc == 0,
        "stdout": cmd.stdout,
        "stderr": cmd.stderr,
        "exit_code": cmd.rc,
        "error": cmd.stderr if cmd.rc != 0 else "",
    }


# =============================================================================
# VERIFICATION FUNCTIONS
# =============================================================================

def verify_telemetry_pods(host) -> Dict[str, Any]:
    """
    Verify all telemetry pods are running.

    Args:
        host: Testinfra host object

    Returns:
        Dict with overall success and component results
    """
    results = {
        "success": True,
        "components": {},
        "errors": [],
    }

    # Check namespace first
    ns_result = check_telemetry_namespace(host)
    results["components"]["namespace"] = ns_result
    if not ns_result["success"]:
        results["success"] = False
        results["errors"].append(ns_result["error"])
        return results  # Can't check pods if namespace doesn't exist

    # Check VictoriaMetrics
    victoria_result = check_victoria_pods_running(host)
    results["components"]["victoria_metrics"] = victoria_result
    if not victoria_result["success"]:
        results["success"] = False
        results["errors"].extend(victoria_result["errors"])

    # Check Kafka
    kafka_result = check_kafka_pods_running(host)
    results["components"]["kafka"] = kafka_result
    if not kafka_result["success"]:
        results["success"] = False
        results["errors"].extend(kafka_result["errors"])

    # Check iDRAC telemetry
    idrac_result = check_idrac_telemetry_pods_running(host)
    results["components"]["idrac_telemetry"] = idrac_result
    if not idrac_result["success"]:
        results["success"] = False
        results["errors"].extend(idrac_result["errors"])

    return results


def verify_victoria_metrics(host) -> Dict[str, Any]:
    """Verify VictoriaMetrics deployment."""
    return check_victoria_pods_running(host)


def verify_kafka(host) -> Dict[str, Any]:
    """Verify Kafka deployment."""
    return check_kafka_pods_running(host)


def verify_idrac_telemetry(host) -> Dict[str, Any]:
    """Verify iDRAC telemetry deployment."""
    return check_idrac_telemetry_pods_running(host)


def check_service_cluster_ready(host) -> Dict[str, Any]:
    """
    Check if service cluster is ready for telemetry deployment.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success and details
    """
    container = TELEMETRY_VARS["container_name"]

    # Check if kubectl can access cluster
    cmd = host.run(f"podman exec {container} kubectl cluster-info 2>/dev/null")

    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Cannot access K8s cluster. Service cluster may not be deployed.",
            "details": cmd.stderr,
        }

    return {
        "success": True,
        "error": "",
        "details": cmd.stdout,
    }


def check_telemetry_config(host) -> Dict[str, Any]:
    """
    Check telemetry configuration inside container.

    Args:
        host: Testinfra host object

    Returns:
        Dict with config details
    """
    container = TELEMETRY_VARS["container_name"]
    config_path = "/opt/omnia/input/project_default/telemetry_config.yml"

    result = check_file_exists(host, config_path)
    if not result["success"]:
        return {
            "success": False,
            "path": config_path,
            "config": None,
            "error": f"telemetry_config.yml not found at {config_path}",
        }

    # Read config
    cmd = host.run(f"podman exec {container} cat {config_path}")

    return {
        "success": True,
        "path": config_path,
        "config": cmd.stdout if cmd.rc == 0 else None,
        "error": "" if cmd.rc == 0 else cmd.stderr,
    }


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
    match = re.search(r'pxe_mapping_file_path:\s*["\']?([^"\'#\n]+)["\']?', cmd.stdout)
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


def get_idrac_telemetry_pods_on_k8s(host, admin_ip: str) -> Dict[str, Any]:
    """
    Get idrac-telemetry pods status from remote node.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of node to SSH to (from PXE mapping file)

    Returns:
        Dict with success, pods list, error
    """
    from ...core.host import run_on_remote_node

    namespace = TELEMETRY_NAMESPACE
    pod_prefix = IDRAC_TELEMETRY_POD_PREFIX
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} -o wide 2>/dev/null | grep {pod_prefix}",
        admin_ip
    )

    if cmd.rc != 0:
        return {
            "success": False,
            "pods": [],
            "output": "",
            "error": f"Failed to get pods: {cmd.stderr}",
        }

    return {
        "success": True,
        "pods": cmd.stdout.strip().split('\n') if cmd.stdout.strip() else [],
        "output": cmd.stdout,
        "error": "",
    }


def get_all_telemetry_pods(host, admin_ip: str) -> Dict[str, Any]:
    """
    Get all pods in telemetry namespace with their status.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of node to SSH to (from PXE mapping file)

    Returns:
        Dict with success, pods list, output, error
    """
    from ...core.host import run_on_remote_node

    namespace = TELEMETRY_NAMESPACE
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} -o wide 2>/dev/null",
        admin_ip
    )

    if cmd.rc != 0:
        return {
            "success": False,
            "pods": [],
            "output": "",
            "error": f"Failed to get pods: {cmd.stderr}",
        }

    return {
        "success": True,
        "pods": cmd.stdout.strip().split('\n') if cmd.stdout.strip() else [],
        "output": cmd.stdout,
        "error": "",
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
                running_pods.append({"name": pod_name, "status": status, "line": line})
            else:
                not_running_pods.append({"name": pod_name, "status": status, "line": line})

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
        "error": "" if success else f"{len(not_running_pods)} pods not in Running state",
    }
