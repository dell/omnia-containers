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
Vector Automation - Functions.

This module contains verification functions for Vector telemetry pipeline.
Implements test cases from TCASES-VEC-2026-001 v1.0.0.

Supports multi-Vector architecture:
- vector-ldms: LDMS metrics → VictoriaMetrics
- vector-ome: iDRAC/OME events → VictoriaLogs
"""

import json
import urllib.parse
from typing import Dict, Any, Optional

from ...core.functions import run_on_remote_node
from ..vars.shared_vars import TELEMETRY_NAMESPACE
from ..vars.vector_vars import (
    VECTOR_DEPLOYMENT_NAMES,
    VECTOR_CONFIGMAP_NAMES,
    VECTOR_DEPLOYMENT_NAME,
    VECTOR_RESOURCE_SPECS,
    VECTOR_CMD_TEMPLATES,
    VECTOR_METRICS_PORTS,
    ERROR_LOG_PATTERNS,
    CREDENTIAL_PATTERNS,
)


# =============================================================================
# Vector Deployment Verification Functions
# =============================================================================

def verify_vector_pod_running(
    host, admin_ip: str, deployment_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify Vector pod(s) are running in telemetry namespace.

    Implements: TC-F001, TC-F008

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        deployment_name: Specific deployment to check (e.g., 'vector-ldms')
                        If None, checks all Vector deployments

    Returns:
        Dict with success, pods (list of pod info), total_pods, running_pods
    """
    deployments_to_check = (
        [deployment_name] if deployment_name else VECTOR_DEPLOYMENT_NAMES
    )

    all_pods = []
    running_count = 0
    total_count = 0

    for deploy_name in deployments_to_check:
        # Use 'app' label which is the actual label used in the cluster
        kubectl_cmd = (
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} "
            f"-l app={deploy_name} -o json"
        )

        cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
        if cmd.rc != 0:
            continue

        try:
            data = json.loads(cmd.stdout)
            items = data.get("items", [])
        except json.JSONDecodeError:
            continue

        for pod in items:
            total_count += 1
            pod_name = pod.get("metadata", {}).get("name", "")
            phase = pod.get("status", {}).get("phase", "")

            container_statuses = pod.get("status", {}).get("containerStatuses", [])
            ready = False
            restarts = 0

            if container_statuses:
                ready = container_statuses[0].get("ready", False)
                restarts = container_statuses[0].get("restartCount", 0)

            is_running = phase == "Running" and ready
            if is_running:
                running_count += 1

            all_pods.append({
                "pod_name": pod_name,
                "deployment": deploy_name,
                "phase": phase,
                "ready": ready,
                "restarts": restarts,
                "is_running": is_running,
            })

    return {
        "success": total_count > 0 and running_count == total_count,
        "pods": all_pods,
        "total_pods": total_count,
        "running_pods": running_count,
        "pod_name": all_pods[0]["pod_name"] if all_pods else "",
        "phase": all_pods[0]["phase"] if all_pods else "",
        "ready": all_pods[0]["ready"] if all_pods else False,
        "restarts": all_pods[0]["restarts"] if all_pods else 0,
    }


def verify_vector_resource_specs(
    host, admin_ip: str, deployment_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify Vector deployment resource specifications.

    Implements: TC-F008 (FS-VE-01)

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        deployment_name: Specific deployment to check (default: vector-ldms)

    Returns:
        Dict with success, expected_specs, actual_specs, deployments
    """
    deploy_name = deployment_name or VECTOR_DEPLOYMENT_NAMES[0]
    
    kubectl_cmd = VECTOR_CMD_TEMPLATES["get_deployment"].format(
        name=deploy_name,
        namespace=TELEMETRY_NAMESPACE
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": f"Failed to get Vector deployment {deploy_name}",
            "stderr": cmd.stderr,
        }

    try:
        data = json.loads(cmd.stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse deployment JSON",
        }

    spec = data.get("spec", {})
    replicas = spec.get("replicas", 0)

    containers = spec.get("template", {}).get("spec", {}).get("containers", [])
    if not containers:
        return {
            "success": False,
            "error": "No containers found in deployment spec",
        }

    container = containers[0]
    resources = container.get("resources", {})
    requests = resources.get("requests", {})
    limits = resources.get("limits", {})

    actual_specs = {
        "replicas": replicas,
        "memory_request": requests.get("memory", ""),
        "memory_limit": limits.get("memory", ""),
        "cpu_request": requests.get("cpu", ""),
        "cpu_limit": limits.get("cpu", ""),
    }

    expected_specs = VECTOR_RESOURCE_SPECS.get(deploy_name, {})
    if not expected_specs:
        return {
            "success": False,
            "error": f"No expected specs defined for {deploy_name}",
            "deployment_name": deploy_name,
        }

    mismatches = []
    for key, expected_value in expected_specs.items():
        actual_value = actual_specs.get(key)
        if actual_value != expected_value:
            mismatches.append({
                "field": key,
                "expected": expected_value,
                "actual": actual_value,
            })

    return {
        "success": len(mismatches) == 0,
        "deployment_name": deploy_name,
        "expected_specs": expected_specs,
        "actual_specs": actual_specs,
        "mismatches": mismatches,
    }


def verify_vector_no_pvc(
    host, admin_ip: str, deployment_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify Vector has no PVC attached (stateless deployment).

    Implements: TC-F001, TC-F008

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        deployment_name: Specific deployment to check (default: vector-ldms)

    Returns:
        Dict with success, has_pvc, volume_info
    """
    deploy_name = deployment_name or VECTOR_DEPLOYMENT_NAMES[0]
    
    kubectl_cmd = VECTOR_CMD_TEMPLATES["get_deployment"].format(
        name=deploy_name,
        namespace=TELEMETRY_NAMESPACE
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": f"Failed to get Vector deployment {deploy_name}",
        }

    try:
        data = json.loads(cmd.stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse deployment JSON",
        }

    volumes = data.get("spec", {}).get("template", {}).get("spec", {}).get("volumes", [])

    pvc_volumes = []
    for volume in volumes:
        if "persistentVolumeClaim" in volume:
            pvc_volumes.append(volume.get("name", ""))

    return {
        "success": len(pvc_volumes) == 0,
        "deployment_name": deploy_name,
        "has_pvc": len(pvc_volumes) > 0,
        "pvc_volumes": pvc_volumes,
        "total_volumes": len(volumes),
    }


# =============================================================================
# Vector ConfigMap and Transform Verification
# =============================================================================

def verify_vector_configmap_exists(
    host, admin_ip: str, configmap_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify Vector ConfigMap exists and contains configuration.

    Implements: TC-F007

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        configmap_name: Specific ConfigMap to check (default: vector-ldms-config)

    Returns:
        Dict with success, configmap_exists, config_content
    """
    cm_name = configmap_name or VECTOR_CONFIGMAP_NAMES[0]
    
    kubectl_cmd = VECTOR_CMD_TEMPLATES["get_configmap"].format(
        name=cm_name,
        namespace=TELEMETRY_NAMESPACE
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": f"Failed to get Vector ConfigMap {cm_name}",
            "configmap_exists": False,
        }

    return {
        "success": True,
        "configmap_name": cm_name,
        "configmap_exists": True,
        "config_content": cmd.stdout,
    }


def verify_all_vector_configmaps(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify all Vector ConfigMaps exist.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node

    Returns:
        Dict with success, configmaps (list of results)
    """
    results = []
    all_exist = True

    for cm_name in VECTOR_CONFIGMAP_NAMES:
        result = verify_vector_configmap_exists(host, admin_ip, cm_name)
        results.append({
            "configmap_name": cm_name,
            "exists": result.get("configmap_exists", False),
        })
        if not result.get("success"):
            all_exist = False

    return {
        "success": all_exist,
        "configmaps": results,
        "total": len(VECTOR_CONFIGMAP_NAMES),
        "existing": sum(1 for r in results if r["exists"]),
    }


def verify_vector_mtls_config(
    host, admin_ip: str, configmap_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify Vector is configured with mTLS for Kafka connections.

    Implements: TC-S001

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        configmap_name: Specific ConfigMap to check (default: vector-ldms-config)

    Returns:
        Dict with success, tls_configured, cert_paths
    """
    result = verify_vector_configmap_exists(host, admin_ip, configmap_name)
    if not result.get("success"):
        return result

    config_content = result.get("config_content", "")

    tls_indicators = [
        "tls",
        "ssl",
        "certificate",
        "ca_file",
        "crt_file",
        "key_file",
    ]

    tls_configured = any(indicator in config_content.lower() for indicator in tls_indicators)

    cert_paths = []
    for line in config_content.split("\n"):
        if any(indicator in line.lower() for indicator in ["cert", "key", "ca"]):
            if "=" in line or ":" in line:
                cert_paths.append(line.strip())

    return {
        "success": tls_configured,
        "tls_configured": tls_configured,
        "cert_paths": cert_paths,
    }


# =============================================================================
# Vector Logs and Error Verification
# =============================================================================

def get_vector_pod_logs(
    host, admin_ip: str, lines: int = 100, deployment_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get Vector pod logs.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        lines: Number of log lines to retrieve
        deployment_name: Specific deployment to get logs from (default: vector-ldms)

    Returns:
        Dict with success, pod_name, logs
    """
    deploy_name = deployment_name or VECTOR_DEPLOYMENT_NAMES[0]
    pod_result = verify_vector_pod_running(host, admin_ip, deploy_name)
    
    if not pod_result.get("pods"):
        return {
            "success": False,
            "error": f"No {deploy_name} pods found",
        }

    pod_name = pod_result["pods"][0]["pod_name"]

    kubectl_cmd = VECTOR_CMD_TEMPLATES["get_pod_logs"].format(
        namespace=TELEMETRY_NAMESPACE,
        pod_name=pod_name,
        lines=lines
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": f"Failed to get {deploy_name} pod logs",
            "pod_name": pod_name,
        }

    return {
        "success": True,
        "deployment_name": deploy_name,
        "pod_name": pod_name,
        "logs": cmd.stdout,
    }


def verify_vector_no_errors_in_logs(
    host, admin_ip: str, lines: int = 500, deployment_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify Vector logs show no errors.

    Implements: TC-F001

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        lines: Number of log lines to check
        deployment_name: Specific deployment to check (default: all deployments)

    Returns:
        Dict with success, error_count, error_lines
    """
    deployments_to_check = (
        [deployment_name] if deployment_name else VECTOR_DEPLOYMENT_NAMES
    )
    
    all_error_lines = []
    total_lines = 0
    
    for deploy_name in deployments_to_check:
        log_result = get_vector_pod_logs(host, admin_ip, lines, deploy_name)
        if not log_result.get("success"):
            continue

        logs = log_result.get("logs", "")
        total_lines += len(logs.split("\n"))

        for line in logs.split("\n"):
            line_lower = line.lower()
            if any(pattern in line_lower for pattern in ERROR_LOG_PATTERNS):
                all_error_lines.append(f"[{deploy_name}] {line.strip()}")

    return {
        "success": len(all_error_lines) == 0,
        "error_count": len(all_error_lines),
        "error_lines": all_error_lines[:10],
        "total_lines_checked": total_lines,
        "deployments_checked": deployments_to_check,
    }


def verify_no_plaintext_credentials(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify no plaintext credentials in Vector artifacts.

    Implements: TC-S002

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node

    Returns:
        Dict with success, credential_findings
    """
    findings = []

    # Check all ConfigMaps
    for cm_name in VECTOR_CONFIGMAP_NAMES:
        configmap_result = verify_vector_configmap_exists(host, admin_ip, cm_name)
        if configmap_result.get("success"):
            config_content = configmap_result.get("config_content", "")
            for pattern in CREDENTIAL_PATTERNS:
                if pattern in config_content:
                    findings.append(f"Pattern '{pattern}' found in ConfigMap {cm_name}")

    # Check pod logs for all deployments
    for deploy_name in VECTOR_DEPLOYMENT_NAMES:
        log_result = get_vector_pod_logs(host, admin_ip, 1000, deploy_name)
        if log_result.get("success"):
            logs = log_result.get("logs", "")
            for pattern in CREDENTIAL_PATTERNS:
                if pattern in logs:
                    findings.append(f"Pattern '{pattern}' found in {deploy_name} pod logs")

    # Check deployment manifests
    for deploy_name in VECTOR_DEPLOYMENT_NAMES:
        kubectl_cmd = VECTOR_CMD_TEMPLATES["get_deployment"].format(
            name=deploy_name,
            namespace=TELEMETRY_NAMESPACE
        )
        cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
        if cmd.rc == 0:
            for pattern in CREDENTIAL_PATTERNS:
                if pattern in cmd.stdout:
                    findings.append(f"Pattern '{pattern}' found in {deploy_name} Deployment manifest")

    return {
        "success": len(findings) == 0,
        "credential_findings": findings,
        "patterns_checked": CREDENTIAL_PATTERNS,
        "deployments_checked": VECTOR_DEPLOYMENT_NAMES,
        "configmaps_checked": VECTOR_CONFIGMAP_NAMES,
    }


# =============================================================================
# Vector Self-Metrics Verification
# =============================================================================

def verify_vector_self_metrics_endpoint(
    host, admin_ip: str, deployment_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify Vector exposes self-metrics endpoint.

    Implements: TC-F010

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        deployment_name: Specific deployment to check (default: vector-ldms)

    Returns:
        Dict with success, metrics_endpoint, metrics_available
    """
    deploy_name = deployment_name or VECTOR_DEPLOYMENT_NAMES[0]
    pod_result = verify_vector_pod_running(host, admin_ip, deploy_name)
    
    if not pod_result.get("pods"):
        return {
            "success": False,
            "error": f"No {deploy_name} pods found",
        }

    pod_name = pod_result["pods"][0]["pod_name"]
    metrics_port = VECTOR_METRICS_PORTS.get(deploy_name, 9599)

    kubectl_cmd = (
        f"kubectl exec -n {TELEMETRY_NAMESPACE} {pod_name} -- "
        f"wget -q -O- http://localhost:{metrics_port}/metrics 2>/dev/null || "
        f"curl -s http://localhost:{metrics_port}/metrics 2>/dev/null"
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    metrics_available = cmd.rc == 0 and len(cmd.stdout) > 0

    # Check for Vector component metrics (actual Vector metric names)
    vector_metric_patterns = [
        "vector_component",
        "vector_buffer",
        "vector_events",
        "vector_bytes",
    ]
    
    expected_metrics_found = []
    if metrics_available:
        for pattern in vector_metric_patterns:
            if pattern in cmd.stdout:
                expected_metrics_found.append(pattern)

    return {
        "success": metrics_available,
        "deployment_name": deploy_name,
        "pod_name": pod_name,
        "metrics_port": metrics_port,
        "metrics_endpoint": f"http://localhost:{metrics_port}/metrics",
        "metrics_available": metrics_available,
        "expected_metrics_found": expected_metrics_found,
        "metrics_sample": cmd.stdout[:500] if metrics_available else "",
    }


# =============================================================================
# Vector Pod Management Functions
# =============================================================================

def delete_vector_pod(host, admin_ip: str) -> Dict[str, Any]:
    """
    Delete Vector pod to simulate failure.

    Implements: TC-E002

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node

    Returns:
        Dict with success, pod_name, deleted
    """
    pod_result = verify_vector_pod_running(host, admin_ip)
    if not pod_result.get("pod_name"):
        return {
            "success": False,
            "error": "Vector pod not found",
        }

    pod_name = pod_result["pod_name"]

    kubectl_cmd = VECTOR_CMD_TEMPLATES["delete_pod"].format(
        namespace=TELEMETRY_NAMESPACE,
        pod_name=pod_name
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    return {
        "success": cmd.rc == 0,
        "pod_name": pod_name,
        "deleted": cmd.rc == 0,
        "output": cmd.stdout,
    }


def rollout_restart_vector(host, admin_ip: str) -> Dict[str, Any]:
    """
    Rollout restart Vector deployment.

    Implements: TC-E006, TC-I001

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node

    Returns:
        Dict with success, restarted
    """
    kubectl_cmd = VECTOR_CMD_TEMPLATES["rollout_restart"].format(
        name=VECTOR_DEPLOYMENT_NAME,
        namespace=TELEMETRY_NAMESPACE
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    return {
        "success": cmd.rc == 0,
        "restarted": cmd.rc == 0,
        "output": cmd.stdout,
    }


def scale_vector_deployment(host, admin_ip: str, replicas: int) -> Dict[str, Any]:
    """
    Scale Vector deployment to specified replicas.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        replicas: Number of replicas

    Returns:
        Dict with success, scaled, replicas
    """
    kubectl_cmd = VECTOR_CMD_TEMPLATES["scale_deployment"].format(
        name=VECTOR_DEPLOYMENT_NAME,
        namespace=TELEMETRY_NAMESPACE,
        replicas=replicas
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    return {
        "success": cmd.rc == 0,
        "scaled": cmd.rc == 0,
        "replicas": replicas,
        "output": cmd.stdout,
    }


# =============================================================================
# Kafka Topic Management for Vector Tests
# =============================================================================

def create_kafka_topic(host, admin_ip: str, topic_name: str) -> Dict[str, Any]:
    """
    Create a new Kafka topic for Vector testing.

    Implements: TC-F003 (Dynamic Topic Discovery)

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        topic_name: Name of the topic to create

    Returns:
        Dict with success, topic_name, created
    """
    # Find Kafka pod
    kubectl_cmd = (
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} "
        "-l app.kubernetes.io/name=kafka -o json"
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to find Kafka pod",
        }

    try:
        data = json.loads(cmd.stdout)
        items = data.get("items", [])
        if not items:
            return {
                "success": False,
                "error": "No Kafka pods found",
            }
        kafka_pod = items[0].get("metadata", {}).get("name", "")
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse Kafka pod JSON",
        }

    # Create topic using kafka-topics.sh
    create_cmd = (
        f"kubectl exec {kafka_pod} -n {TELEMETRY_NAMESPACE} -- "
        f"bin/kafka-topics.sh --create --topic {topic_name} "
        "--bootstrap-server localhost:9092 --partitions 3 "
        "--replication-factor 1"
    )

    cmd = run_on_remote_node(host, create_cmd, admin_ip)

    return {
        "success": cmd.rc == 0 or "already exists" in cmd.stdout.lower(),
        "topic_name": topic_name,
        "created": cmd.rc == 0,
        "output": cmd.stdout,
    }


def produce_test_message_to_kafka(
    host, admin_ip: str, topic: str, message: str
) -> Dict[str, Any]:
    """
    Produce a test message to Kafka topic.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        topic: Kafka topic name
        message: Message content (JSON string)

    Returns:
        Dict with success, topic, message_sent
    """
    # Find Kafka pod
    kubectl_cmd = (
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} "
        "-l app.kubernetes.io/name=kafka -o json"
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to find Kafka pod",
        }

    try:
        data = json.loads(cmd.stdout)
        items = data.get("items", [])
        if not items:
            return {
                "success": False,
                "error": "No Kafka pods found",
            }
        kafka_pod = items[0].get("metadata", {}).get("name", "")
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse Kafka pod JSON",
        }

    # Escape message for shell
    escaped_message = message.replace('"', '\\"').replace("'", "\\'")

    # Produce message using kafka-console-producer.sh
    produce_cmd = (
        f"kubectl exec {kafka_pod} -n {TELEMETRY_NAMESPACE} -- "
        f"bash -c \"echo '{escaped_message}' | bin/kafka-console-producer.sh "
        f"--topic {topic} --bootstrap-server localhost:9092\""
    )

    cmd = run_on_remote_node(host, produce_cmd, admin_ip)

    return {
        "success": cmd.rc == 0,
        "topic": topic,
        "message_sent": cmd.rc == 0,
        "output": cmd.stdout if cmd.rc != 0 else "",
    }


# =============================================================================
# VictoriaMetrics Query Functions for Vector Verification
# =============================================================================

def query_victoria_metrics(host, admin_ip: str, query: str) -> Dict[str, Any]:
    """
    Query VictoriaMetrics using PromQL.

    Implements: TC-F001, TC-F002, TC-F004

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        query: PromQL query string

    Returns:
        Dict with success, query, result_count, results
    """
    # URL encode the query
    encoded_query = urllib.parse.quote(query)

    # Find vmselect pod
    kubectl_cmd = (
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} "
        "-l app.kubernetes.io/name=vmselect -o json"
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to find vmselect pod",
        }

    try:
        data = json.loads(cmd.stdout)
        items = data.get("items", [])
        if not items:
            return {
                "success": False,
                "error": "No vmselect pods found",
            }
        vmselect_pod = items[0].get("metadata", {}).get("name", "")
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse vmselect pod JSON",
        }

    # Query VictoriaMetrics
    curl_cmd = (
        f"curl -s 'http://localhost:8481/select/0/prometheus/api/v1/"
        f"query?query={encoded_query}'"
    )
    kubectl_cmd = VECTOR_CMD_TEMPLATES["exec_in_pod"].format(
        namespace=TELEMETRY_NAMESPACE,
        pod_name=vmselect_pod,
        command=curl_cmd
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to query VictoriaMetrics",
            "query": query,
        }

    try:
        result = json.loads(cmd.stdout)
        result_data = result.get("data", {}).get("result", [])
        result_count = len(result_data)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse query result",
            "query": query,
        }

    return {
        "success": True,
        "query": query,
        "result_count": result_count,
        "results": result_data,
    }


# =============================================================================
# VictoriaLogs Query Functions for Vector Verification
# =============================================================================

def query_victoria_logs(host, admin_ip: str, query: str) -> Dict[str, Any]:
    """
    Query VictoriaLogs using LogsQL.

    Implements: TC-F001, TC-F002, TC-F005

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control plane node
        query: LogsQL query string

    Returns:
        Dict with success, query, result_count, results
    """
    # URL encode the query
    encoded_query = urllib.parse.quote(query)

    # Find vlselect pod
    kubectl_cmd = (
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} "
        "-l app.kubernetes.io/name=vlselect -o json"
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to find vlselect pod",
        }

    try:
        data = json.loads(cmd.stdout)
        items = data.get("items", [])
        if not items:
            return {
                "success": False,
                "error": "No vlselect pods found",
            }
        vlselect_pod = items[0].get("metadata", {}).get("name", "")
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse vlselect pod JSON",
        }

    # Query VictoriaLogs
    curl_cmd = (
        f"curl -s 'http://localhost:9471/select/logsql/"
        f"query?query={encoded_query}'"
    )
    kubectl_cmd = VECTOR_CMD_TEMPLATES["exec_in_pod"].format(
        namespace=TELEMETRY_NAMESPACE,
        pod_name=vlselect_pod,
        command=curl_cmd
    )

    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to query VictoriaLogs",
            "query": query,
        }

    try:
        result = json.loads(cmd.stdout)
        # VictoriaLogs response format may vary
        result_count = len(result) if isinstance(result, list) else 0
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse query result",
            "query": query,
        }

    return {
        "success": True,
        "query": query,
        "result_count": result_count,
        "results": result if isinstance(result, list) else [],
    }
