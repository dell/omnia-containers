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
VictoriaMetrics Automation - Functions.

This module contains verification functions for VictoriaMetrics telemetry.
"""

import json
import urllib.parse
from typing import Dict, Any

from ...core.host import run_on_remote_node
from ..vars.shared_vars import TELEMETRY_NAMESPACE
from ..vars.victoria_vars import (
    DEPLOYMENT_MODE_SINGLE,
    DEPLOYMENT_MODE_CLUSTER,
    VICTORIA_SINGLE_NODE,
    VICTORIA_CLUSTER,
    VMAGENT,
    VICTORIA_TLS_SECRET,
    VICTORIA_TLS_SECRET_KEYS,
    VICTORIA_API_ENDPOINTS,
    VICTORIA_CMD_TEMPLATES,
)
from .shared_func import (
    get_telemetry_config,
    get_activated_service_tags,
)


def get_deployment_mode(host) -> str:
    """
    Get VictoriaMetrics deployment mode from telemetry_config.yml.

    Returns:
        'single-node' or 'cluster'
    """
    config = get_telemetry_config(host)
    victoria_config = config.get("victoria_configurations", {})
    return victoria_config.get("deployment_mode", "")


def get_victoria_config(host) -> Dict[str, Any]:
    """
    Get victoria_configurations from telemetry_config.yml.

    Returns:
        Dict with victoria config (deployment_mode, persistence_size, retention_period)
    """
    config = get_telemetry_config(host)
    return config.get("victoria_configurations", {})


def verify_victoria_persistence_size(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VictoriaMetrics PVC storage matches config.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, expected_size, actual_sizes, mismatches
    """
    victoria_config = get_victoria_config(host)
    expected_size = victoria_config.get("persistence_size", "")
    deployment_mode = get_deployment_mode(host)

    # Get PVCs based on deployment mode
    if deployment_mode == DEPLOYMENT_MODE_SINGLE:
        pvc_prefix = "victoria-metrics-pvc"
    else:
        pvc_prefix = "vmstorage-data"

    # Get all PVCs
    kubectl_cmd = f"kubectl get pvc -n {TELEMETRY_NAMESPACE} -o json"
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to get PVCs",
            "expected_size": expected_size,
        }

    try:
        data = json.loads(cmd.stdout)
        items = data.get("items", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse PVC JSON",
            "expected_size": expected_size,
        }

    # Filter PVCs by prefix
    pvc_results = []
    mismatches = []

    for pvc in items:
        pvc_name = pvc.get("metadata", {}).get("name", "")
        if pvc_prefix in pvc_name:
            actual_size = pvc.get("spec", {}).get("resources", {}).get(
                "requests", {}
            ).get("storage", "")
            match = actual_size == expected_size
            pvc_results.append({
                "pvc_name": pvc_name,
                "expected_size": expected_size,
                "actual_size": actual_size,
                "match": match,
            })
            if not match:
                mismatches.append({
                    "pvc_name": pvc_name,
                    "expected": expected_size,
                    "actual": actual_size,
                })

    return {
        "success": len(mismatches) == 0 and len(pvc_results) > 0,
        "deployment_mode": deployment_mode,
        "expected_size": expected_size,
        "pvc_results": pvc_results,
        "mismatches": mismatches,
    }


def verify_victoria_single_node_pods(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VictoriaMetrics single-node pods are running.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, pod_results, errors
    """
    deployment_mode = get_deployment_mode(host)
    if deployment_mode != DEPLOYMENT_MODE_SINGLE:
        return {
            "skip": True,
            "skip_reason": f"Deployment mode is '{deployment_mode}', not single-node",
        }

    app_label = VICTORIA_SINGLE_NODE["app_label"]

    kubectl_cmd = VICTORIA_CMD_TEMPLATES["get_pods_by_label"].format(
        namespace=TELEMETRY_NAMESPACE,
        app_label=app_label
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to get pods",
        }

    try:
        data = json.loads(cmd.stdout)
        items = data.get("items", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse pods JSON",
        }

    pod_results = []
    errors = []

    for pod in items:
        pod_name = pod.get("metadata", {}).get("name", "")
        phase = pod.get("status", {}).get("phase", "")
        running = phase == "Running"
        pod_results.append({
            "pod": pod_name,
            "phase": phase,
            "running": running,
        })
        if not running:
            errors.append(f"Pod '{pod_name}' is not running (status: {phase})")

    # Expect at least 1 pod
    if len(pod_results) == 0:
        errors.append("No victoria-metric pods found")

    return {
        "success": len(errors) == 0,
        "deployment_mode": deployment_mode,
        "expected_count": 1,
        "actual_count": len(pod_results),
        "pod_results": pod_results,
        "errors": errors,
    }


def verify_victoria_cluster_pods(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VictoriaMetrics cluster pods are running.

    Checks: vmstorage (3), vminsert (2), vmselect (2)

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, component_results, errors
    """
    deployment_mode = get_deployment_mode(host)
    if deployment_mode != DEPLOYMENT_MODE_CLUSTER:
        return {
            "skip": True,
            "skip_reason": f"Deployment mode is '{deployment_mode}', not cluster",
        }

    component_results = []
    errors = []

    for component_name, component_config in VICTORIA_CLUSTER.items():
        app_label = component_config["app_label"]
        expected_replicas = component_config["replicas"]

        kubectl_cmd = VICTORIA_CMD_TEMPLATES["get_pods_by_label"].format(
            namespace=TELEMETRY_NAMESPACE,
            app_label=app_label
        )
        cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
        if cmd.rc != 0:
            errors.append(f"Failed to get {component_name} pods")
            continue

        try:
            data = json.loads(cmd.stdout)
            items = data.get("items", [])
        except json.JSONDecodeError:
            errors.append(f"Failed to parse {component_name} pods JSON")
            continue

        pod_results = []
        running_count = 0

        for pod in items:
            pod_name = pod.get("metadata", {}).get("name", "")
            phase = pod.get("status", {}).get("phase", "")
            running = phase == "Running"
            pod_results.append({
                "pod": pod_name,
                "phase": phase,
                "running": running,
            })
            if running:
                running_count += 1
            else:
                errors.append(
                    f"Pod '{pod_name}' ({component_name}) is not running "
                    f"(status: {phase})"
                )

        component_results.append({
            "component": component_name,
            "app_label": app_label,
            "expected_replicas": expected_replicas,
            "running_count": running_count,
            "pod_results": pod_results,
            "success": running_count >= expected_replicas,
        })

    return {
        "success": len(errors) == 0,
        "deployment_mode": deployment_mode,
        "component_results": component_results,
        "errors": errors,
    }


def verify_vmagent_pod(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify vmagent pod is running.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, pod_results, errors
    """
    app_label = VMAGENT["app_label"]

    kubectl_cmd = VICTORIA_CMD_TEMPLATES["get_pods_by_label"].format(
        namespace=TELEMETRY_NAMESPACE,
        app_label=app_label
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to get vmagent pods",
        }

    try:
        data = json.loads(cmd.stdout)
        items = data.get("items", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse vmagent pods JSON",
        }

    pod_results = []
    errors = []

    for pod in items:
        pod_name = pod.get("metadata", {}).get("name", "")
        phase = pod.get("status", {}).get("phase", "")
        running = phase == "Running"
        pod_results.append({
            "pod": pod_name,
            "phase": phase,
            "running": running,
        })
        if not running:
            errors.append(f"vmagent pod '{pod_name}' is not running (status: {phase})")

    if len(pod_results) == 0:
        errors.append("No vmagent pods found")

    return {
        "success": len(errors) == 0 and len(pod_results) > 0,
        "pod_results": pod_results,
        "errors": errors,
    }


def verify_victoria_services(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VictoriaMetrics services have external IPs.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, service_results, errors
    """
    deployment_mode = get_deployment_mode(host)

    # Determine which services to check based on deployment mode
    if deployment_mode == DEPLOYMENT_MODE_SINGLE:
        services_to_check = [
            {
                "name": VICTORIA_SINGLE_NODE["service_name"],
                "port": VICTORIA_SINGLE_NODE["port"],
            }
        ]
    else:
        services_to_check = [
            {
                "name": VICTORIA_CLUSTER["vminsert"]["service_name"],
                "port": VICTORIA_CLUSTER["vminsert"]["port"],
            },
            {
                "name": VICTORIA_CLUSTER["vmselect"]["service_name"],
                "port": VICTORIA_CLUSTER["vmselect"]["port"],
            },
        ]

    service_results = []
    errors = []

    for svc in services_to_check:
        svc_name = svc["name"]
        expected_port = svc["port"]

        # Get external IP
        kubectl_cmd = VICTORIA_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=svc_name,
            namespace=TELEMETRY_NAMESPACE
        )
        cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
        external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""

        has_ip = bool(external_ip) and external_ip != "null"

        service_results.append({
            "service": svc_name,
            "external_ip": external_ip if has_ip else None,
            "port": expected_port,
            "has_external_ip": has_ip,
        })

        if not has_ip:
            errors.append(f"Service '{svc_name}' has no external IP")

    return {
        "success": len(errors) == 0,
        "deployment_mode": deployment_mode,
        "service_results": service_results,
        "errors": errors,
    }


def verify_victoria_tls_secret(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VictoriaMetrics TLS secret exists with required keys.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, secret_exists, keys_found, missing_keys
    """
    kubectl_cmd = VICTORIA_CMD_TEMPLATES["get_secret"].format(
        secret_name=VICTORIA_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "secret_exists": False,
            "error": f"TLS secret '{VICTORIA_TLS_SECRET}' not found",
        }

    try:
        data = json.loads(cmd.stdout)
        secret_data = data.get("data", {})
    except json.JSONDecodeError:
        return {
            "success": False,
            "secret_exists": True,
            "error": "Failed to parse secret JSON",
        }

    # Check for required keys
    keys_found = list(secret_data.keys())
    missing_keys = [k for k in VICTORIA_TLS_SECRET_KEYS if k not in keys_found]

    return {
        "success": len(missing_keys) == 0,
        "secret_name": VICTORIA_TLS_SECRET,
        "secret_exists": True,
        "keys_found": keys_found,
        "missing_keys": missing_keys,
    }


def verify_victoria_tls_health(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify TLS connection to VictoriaMetrics and check health endpoint.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, tls_connected, health_response, errors
    """
    deployment_mode = get_deployment_mode(host)

    # Get service info based on deployment mode
    if deployment_mode == DEPLOYMENT_MODE_SINGLE:
        service_name = VICTORIA_SINGLE_NODE["service_name"]
        port = VICTORIA_SINGLE_NODE["port"]
    else:
        service_name = VICTORIA_CLUSTER["vmselect"]["service_name"]
        port = VICTORIA_CLUSTER["vmselect"]["port"]

    # Get external IP
    kubectl_cmd = VICTORIA_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""

    if not external_ip or external_ip == "null":
        return {
            "success": False,
            "error": f"Service '{service_name}' has no external IP",
        }

    # Extract CA cert from secret
    extract_cmd = VICTORIA_CMD_TEMPLATES["extract_ca_cert"].format(
        secret_name=VICTORIA_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, extract_cmd, admin_ip)
    if cmd.rc != 0 or not cmd.stdout.strip():
        return {
            "success": False,
            "error": "Failed to extract CA certificate from secret",
        }

    # Save CA cert to temp file and curl health endpoint
    # Use --resolve to map service DNS name to IP for TLS verification
    # since the cert SAN contains DNS names, not the LoadBalancer IP
    # Write cert directly via kubectl to preserve newlines, add trailing echo
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"
    curl_cmd = (
        f"kubectl get secret {VICTORIA_TLS_SECRET} -n {TELEMETRY_NAMESPACE} "
        f"-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        f"curl -s --max-time 30 --cacert /tmp/ca.crt "
        f"--resolve {service_dns}:{port}:{external_ip} "
        f"https://{service_dns}:{port}/health; echo"
    )
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)
    health_response = cmd.stdout.strip() if cmd.rc == 0 else ""

    # Check if health response is valid
    tls_connected = cmd.rc == 0
    health_ok = bool(health_response)

    return {
        "success": tls_connected and health_ok,
        "deployment_mode": deployment_mode,
        "service_name": service_name,
        "external_ip": external_ip,
        "port": port,
        "tls_connected": tls_connected,
        "health_response": health_response,
        "error": "" if (tls_connected and health_ok) else "Health check failed",
    }


def verify_victoria_idrac_data(
    host, admin_ip: str, timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Verify iDRAC telemetry data exists in VictoriaMetrics for activated service tags.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        timeout_seconds: Timeout for API queries

    Returns:
        Dict with success, service_tag_results, found_tags, missing_tags
    """
    deployment_mode = get_deployment_mode(host)

    # Get activated service tags
    activated_tags = get_activated_service_tags(host)
    if not activated_tags:
        return {
            "skip": True,
            "skip_reason": "No activated service tags found in telemetry report",
        }

    # Get service info based on deployment mode
    if deployment_mode == DEPLOYMENT_MODE_SINGLE:
        service_name = VICTORIA_SINGLE_NODE["service_name"]
        port = VICTORIA_SINGLE_NODE["port"]
        query_endpoint = VICTORIA_API_ENDPOINTS["single_query"]
    else:
        service_name = VICTORIA_CLUSTER["vmselect"]["service_name"]
        port = VICTORIA_CLUSTER["vmselect"]["port"]
        query_endpoint = VICTORIA_API_ENDPOINTS["cluster_query"]

    # Get external IP
    kubectl_cmd = VICTORIA_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""

    if not external_ip or external_ip == "null":
        return {
            "success": False,
            "error": f"Service '{service_name}' has no external IP",
        }

    # Extract CA cert
    extract_cmd = VICTORIA_CMD_TEMPLATES["extract_ca_cert"].format(
        secret_name=VICTORIA_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, extract_cmd, admin_ip)
    if cmd.rc != 0 or not cmd.stdout.strip():
        return {
            "success": False,
            "error": "Failed to extract CA certificate",
        }

    # Query for each service tag
    service_tag_results = []
    found_tags = []
    missing_tags = []

    for service_tag in activated_tags:
        # Query for PowerEdge metrics with this service tag
        query = urllib.parse.quote(
            f'{{__name__=~"PowerEdge_.*",ServiceTag="{service_tag}"}}'
        )

        # Use --resolve to map service DNS name to IP for TLS verification
        # Write cert directly via kubectl to preserve newlines, add trailing echo
        service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"
        curl_cmd = (
            f"kubectl get secret {VICTORIA_TLS_SECRET} -n {TELEMETRY_NAMESPACE} "
            f"-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
            f"curl -s --max-time {timeout_seconds} --cacert /tmp/ca.crt "
            f"--resolve {service_dns}:{port}:{external_ip} "
            f"'https://{service_dns}:{port}{query_endpoint}?query={query}'; echo"
        )
        cmd = run_on_remote_node(host, curl_cmd, admin_ip)

        try:
            response = json.loads(cmd.stdout) if cmd.rc == 0 else {}
            result_data = response.get("data", {}).get("result", [])
        except json.JSONDecodeError:
            result_data = []

        has_data = len(result_data) > 0

        # Get sample metrics if data found
        sample_metrics = []
        latest_timestamp = 0

        if has_data:
            for item in result_data[:3]:  # Get up to 3 sample metrics
                metric = item.get("metric", {})
                value = item.get("value", [])
                metric_name = metric.get("__name__", "")
                # value[0] is timestamp (unix epoch), value[1] is the metric value
                metric_timestamp = int(float(value[0])) if len(value) > 0 else 0
                metric_value = value[1] if len(value) > 1 else ""
                if metric_timestamp > latest_timestamp:
                    latest_timestamp = metric_timestamp
                sample_metrics.append({
                    "metric_name": metric_name,
                    "value": metric_value,
                    "timestamp": metric_timestamp,
                    "labels": {
                        k: v for k, v in metric.items()
                        if k not in ["__name__", "ServiceTag"]
                    },
                })

        service_tag_results.append({
            "service_tag": service_tag,
            "found": has_data,
            "latest_timestamp": latest_timestamp,
            "metric_count": len(result_data),
            "sample_metrics": sample_metrics,
        })

        if has_data:
            found_tags.append(service_tag)
        else:
            missing_tags.append(service_tag)

    return {
        "success": len(missing_tags) == 0,
        "deployment_mode": deployment_mode,
        "external_ip": external_ip,
        "port": port,
        "activated_tags": activated_tags,
        "service_tag_results": service_tag_results,
        "found_tags": found_tags,
        "missing_tags": missing_tags,
    }
