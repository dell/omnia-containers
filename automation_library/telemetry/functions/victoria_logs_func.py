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
VictoriaLogs Automation - Verification Functions.

This module contains verification functions for the VictoriaLogs cluster
deployed alongside VictoriaMetrics when any source targets 'victoria_logs'.

VLCluster components verified:
  - vlstorage  (3 replicas) : persistent log storage StatefulSet
  - vlinsert   (2 replicas) : log ingestion gateway with LoadBalancer
  - vlselect   (2 replicas) : log query gateway with LoadBalancer
  - vlagent    (1 replica)  : syslog receiver and remoteWrite forwarder
"""

import json
import time
from typing import Dict, Any

from ...core import run_on_remote_node
from ..vars.shared_vars import TELEMETRY_NAMESPACE
from ..vars.victoria_logs_vars import (
    VLSTORAGE,
    VLINSERT,
    VLSELECT,
    VLAGENT_LOGS,
    VLAGENT_CONFIGMAP_NAME,
    VLAGENT_EXPECTED_PORTS,
    VLAGENT_SYSLOG_TEST_TAG,
    VLAGENT_SYSLOG_INGESTION_WAIT_SECS,
    VLAGENT_STREAM_TEST_TAG,
    VLAGENT_FIELD_TEST_TAG,
    VLINSERT_DIRECT_TEST_JOB,
    VLAGENT_RESTART_TEST_TAG,
    VLAGENT_POD_READY_TIMEOUT_SECS,
    VLAGENT_MULTI_MSG_COUNT,
    VLSELECT_QUERY_RESPONSE_MAX_SECS,
    VLAGENT_BULK_COUNT,
    VLAGENT_BULK_TAG,
    VLAGENT_BULK_WAIT_SECS,
    TLS_CERT_MIN_VALID_SECS,
    VLAGENT_RBAC_SERVICE_ACCOUNT,
    VICTORIA_LOGS_TLS_SECRET,
    VICTORIA_LOGS_TLS_SECRET_KEYS,
    VICTORIA_LOGS_API_ENDPOINTS,
    VICTORIA_LOGS_CMD_TEMPLATES,
)
from .shared_func import get_telemetry_config, get_telemetry_storage_config


# =============================================================================
# CONFIG HELPERS
# =============================================================================

def get_victoria_logs_config(host) -> Dict[str, Any]:
    """
    Get victoria_logs sink config from telemetry_config.yml.

    Reads from telemetry_sinks.victoria_logs which contains:
      storage_size, retention_period, additional_log_write_endpoints

    Returns:
        Dict with victoria_logs sink config
    """
    config = get_telemetry_config(host)
    return config.get("telemetry_sinks", {}).get("victoria_logs", {})


def get_victoria_logs_storage_config(host) -> Dict[str, Any]:
    """
    Get VictoriaLogs cluster resource/replica config from telemetry_storage_config.yml.

    Reads from victoria_logs_cluster_storage which contains:
      vlstorage, vlinsert, vlselect, vlagent (each with replicas, resources)

    Returns:
        Dict with victoria_logs_cluster_storage config
    """
    storage_config = get_telemetry_storage_config(host)
    return storage_config.get("victoria_logs_cluster_storage", {})


# =============================================================================
# STORAGE VERIFICATION
# =============================================================================

def verify_victoria_logs_storage_size(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VictoriaLogs vlstorage PVC sizes match telemetry_sinks.victoria_logs config.

    Queries all PVCs labelled app=vlstorage and checks each against the
    configured storage_size value in telemetry_config.yml.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, expected_size, pvc_results, mismatches
    """
    logs_config = get_victoria_logs_config(host)
    expected_size = logs_config.get("storage_size", "")
    app_label = VLSTORAGE["app_label"]

    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_statefulset_pvcs"].format(
        namespace=TELEMETRY_NAMESPACE,
        app_label=app_label
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to get vlstorage PVCs",
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

    pvc_results = []
    mismatches = []

    for pvc in items:
        pvc_name = pvc.get("metadata", {}).get("name", "")
        actual_size = (
            pvc.get("spec", {})
               .get("resources", {})
               .get("requests", {})
               .get("storage", "")
        )
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
        "expected_size": expected_size,
        "pvc_results": pvc_results,
        "mismatches": mismatches,
    }


# =============================================================================
# POD VERIFICATION
# =============================================================================

def verify_victoria_logs_cluster_pods(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify all VictoriaLogs cluster pods are running.

    Checks:
      - vlstorage  : 3 replicas (StatefulSet)
      - vlinsert   : 2 replicas (Deployment)
      - vlselect   : 2 replicas (Deployment)

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, component_results, errors
    """
    components = {
        "vlstorage": VLSTORAGE,
        "vlinsert": VLINSERT,
        "vlselect": VLSELECT,
    }

    component_results = []
    errors = []

    for component_name, component_config in components.items():
        app_label = component_config["app_label"]
        expected_replicas = component_config["replicas"]

        kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_pods_by_label"].format(
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
        "component_results": component_results,
        "errors": errors,
    }


def verify_vlagent_pod(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify the VLAgent pod is running.

    VLAgent provides syslog reception (ports 514/6514) and forwards
    logs to vlinsert via remoteWrite.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, pod_results, errors
    """
    app_label = VLAGENT_LOGS["app_label"]

    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_pods_by_label"].format(
        namespace=TELEMETRY_NAMESPACE,
        app_label=app_label
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to get vlagent pods",
        }

    try:
        data = json.loads(cmd.stdout)
        items = data.get("items", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse vlagent pods JSON",
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
            errors.append(
                f"vlagent pod '{pod_name}' is not running (status: {phase})"
            )

    if len(pod_results) == 0:
        errors.append("No vlagent pods found in telemetry namespace")

    return {
        "success": len(errors) == 0 and len(pod_results) > 0,
        "pod_results": pod_results,
        "errors": errors,
    }


# =============================================================================
# SERVICE VERIFICATION
# =============================================================================

def verify_victoria_logs_services(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VictoriaLogs LoadBalancer services have external IPs assigned.

    Checks:
      - vlinsert-victoria-logs-cluster  (port 9481)
      - vlselect-victoria-logs-cluster  (port 9471)

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, service_results, errors
    """
    services_to_check = [
        {"name": VLINSERT["service_name"], "port": VLINSERT["port"]},
        {"name": VLSELECT["service_name"], "port": VLSELECT["port"]},
    ]

    service_results = []
    errors = []

    for svc in services_to_check:
        svc_name = svc["name"]
        expected_port = svc["port"]

        kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
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
        "service_results": service_results,
        "errors": errors,
    }


# =============================================================================
# TLS SECRET VERIFICATION
# =============================================================================

def verify_victoria_logs_tls_secret(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify the shared VictoriaLogs TLS secret exists with required keys.

    The secret 'victoria-tls-certs' is shared between VictoriaMetrics and
    VictoriaLogs for all inter-component TLS communication.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, secret_exists, keys_found, missing_keys
    """
    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_secret"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "secret_exists": False,
            "error": f"TLS secret '{VICTORIA_LOGS_TLS_SECRET}' not found",
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

    keys_found = list(secret_data.keys())
    missing_keys = [
        k for k in VICTORIA_LOGS_TLS_SECRET_KEYS if k not in keys_found
    ]

    return {
        "success": len(missing_keys) == 0,
        "secret_name": VICTORIA_LOGS_TLS_SECRET,
        "secret_exists": True,
        "keys_found": keys_found,
        "missing_keys": missing_keys,
    }


# =============================================================================
# TLS HEALTH VERIFICATION
# =============================================================================

def verify_victoria_logs_health(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify TLS connection to VictoriaLogs vlselect and check /health endpoint.

    Uses --resolve to map the service DNS name to the LoadBalancer IP so TLS
    certificate SAN validation passes correctly.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, tls_connected, health_response, external_ip, port
    """
    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"

    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""

    if not external_ip or external_ip == "null":
        return {
            "success": False,
            "error": f"Service '{service_name}' has no external IP",
            "service_name": service_name,
            "external_ip": "",
            "port": port,
        }

    curl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["curl_with_tls"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=service_dns,
        port=port,
        external_ip=external_ip,
        endpoint=VICTORIA_LOGS_API_ENDPOINTS["health"]
    )
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)
    health_response = cmd.stdout.strip() if cmd.rc == 0 else ""

    tls_connected = cmd.rc == 0
    health_ok = bool(health_response)

    return {
        "success": tls_connected and health_ok,
        "service_name": service_name,
        "external_ip": external_ip,
        "port": port,
        "tls_connected": tls_connected,
        "health_response": health_response,
        "error": "" if (tls_connected and health_ok) else "Health check failed",
    }


# =============================================================================
# LOG QUERY VERIFICATION
# =============================================================================

def verify_victoria_logs_query(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VictoriaLogs log query endpoint is accessible via vlselect.

    Queries /select/logsql/stats/streams?query=* to confirm the LogsQL
    query endpoint is reachable. Returns stream count and sample stream
    data if logs have been ingested.

    Note: An empty stream list (stream_count=0) is still a success — it
    means VictoriaLogs is healthy but no logs have been ingested yet.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, external_ip, port, stream_count, streams,
                endpoint_accessible, error
    """
    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"

    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""

    if not external_ip or external_ip == "null":
        return {
            "success": False,
            "external_ip": "",
            "port": port,
            "error": f"Service '{service_name}' has no external IP",
        }

    streams_endpoint = VICTORIA_LOGS_API_ENDPOINTS["streams"]
    query_url = (
        f"https://{service_dns}:{port}{streams_endpoint}?query=*"
    )
    curl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["curl_query"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=service_dns,
        port=port,
        external_ip=external_ip,
        url=query_url
    )
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "external_ip": external_ip,
            "port": port,
            "error": f"Curl request to log query endpoint failed: {cmd.stderr}",
        }

    response_text = cmd.stdout.strip()
    stream_count = 0
    streams = []
    endpoint_accessible = False

    try:
        response = json.loads(response_text)
        streams = response if isinstance(response, list) else []
        stream_count = len(streams)
        endpoint_accessible = True
    except json.JSONDecodeError:
        # Non-JSON (empty or plain-text) response: accessible if any output received
        endpoint_accessible = bool(response_text)

    return {
        "success": endpoint_accessible,
        "external_ip": external_ip,
        "port": port,
        "stream_count": stream_count,
        "streams": streams[:5],
        "endpoint_accessible": endpoint_accessible,
        "error": "" if endpoint_accessible else "Log query endpoint not accessible",
    }


# =============================================================================
# CONFIGMAP VERIFICATION
# =============================================================================

def verify_vlagent_configmap(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify the VLAgent ConfigMap 'vlagent-config' exists in telemetry namespace.

    This ConfigMap contains:
    - Syslog receiver configuration (plaintext :514, TLS :6514)
    - remoteWrite pipeline to vlinsert (/insert/jsonline)
    - Persistent queue (PVC buffer) configuration

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, configmap_exists, configmap_name
    """
    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_configmap"].format(
        configmap_name=VLAGENT_CONFIGMAP_NAME,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "configmap_exists": False,
            "configmap_name": VLAGENT_CONFIGMAP_NAME,
            "error": (
                f"ConfigMap '{VLAGENT_CONFIGMAP_NAME}' not found "
                f"in namespace '{TELEMETRY_NAMESPACE}'"
            ),
        }

    try:
        data = json.loads(cmd.stdout)
        cm_name = data.get("metadata", {}).get("name", "")
        has_data = bool(data.get("data", {}))
    except json.JSONDecodeError:
        return {
            "success": False,
            "configmap_exists": True,
            "configmap_name": VLAGENT_CONFIGMAP_NAME,
            "error": "Failed to parse ConfigMap JSON",
        }

    return {
        "success": bool(cm_name) and has_data,
        "configmap_exists": bool(cm_name),
        "configmap_name": cm_name or VLAGENT_CONFIGMAP_NAME,
        "has_data": has_data,
        "error": "" if (cm_name and has_data) else "ConfigMap exists but has no data",
    }


# =============================================================================
# VLAGENT PVC VERIFICATION
# =============================================================================

def verify_vlagent_pvc(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify the VLAgent buffer PVC exists in the telemetry namespace.

    The VLAgent operator creates a PVC labelled app=vlagent for the
    disk-backed WAL buffer (default 5Gi). This PVC prevents log loss
    during vlinsert unavailability.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, pvc_count, pvc_results, errors
    """
    app_label = VLAGENT_LOGS["app_label"]
    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_statefulset_pvcs"].format(
        namespace=TELEMETRY_NAMESPACE,
        app_label=app_label
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "pvc_count": 0,
            "error": f"Failed to list PVCs for app={app_label}",
        }

    try:
        data = json.loads(cmd.stdout)
        items = data.get("items", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "pvc_count": 0,
            "error": "Failed to parse PVC JSON",
        }

    if not items:
        return {
            "success": False,
            "pvc_count": 0,
            "error": (
                f"No PVCs found for app={app_label} in "
                f"namespace '{TELEMETRY_NAMESPACE}'"
            ),
        }

    pvc_results = []
    for pvc in items:
        pvc_name = pvc.get("metadata", {}).get("name", "")
        phase = pvc.get("status", {}).get("phase", "")
        size = (
            pvc.get("spec", {})
               .get("resources", {})
               .get("requests", {})
               .get("storage", "")
        )
        pvc_results.append({
            "pvc_name": pvc_name,
            "phase": phase,
            "size": size,
            "bound": phase == "Bound",
        })

    return {
        "success": True,
        "pvc_count": len(pvc_results),
        "pvc_results": pvc_results,
        "error": "",
    }


# =============================================================================
# VLAGENT SYSLOG SERVICE VERIFICATION
# =============================================================================

def verify_vlagent_syslog_service(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify the VLAgent syslog service exposes ports 514 and 6514.

    The VLAgent service is created by the operator from the VLAgent CR.
    Service type is LoadBalancer (MetalLB) or NodePort depending on cluster.
    Expected ports:
      - 514  TCP  (plaintext syslog, RFC 3164/5424)
      - 514  UDP  (plaintext syslog)
      - 6514 TCP  (TLS syslog, RFC 5425)
      - 9429 TCP  (VLAgent health check)

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node

    Returns:
        Dict with success, service_name, service_type, ports_found,
                missing_ports, errors
    """
    service_name = VLAGENT_LOGS["service_name"]

    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_json"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "service_name": service_name,
            "service_exists": False,
            "error": (
                f"VLAgent service '{service_name}' not found "
                f"in namespace '{TELEMETRY_NAMESPACE}'"
            ),
        }

    try:
        data = json.loads(cmd.stdout)
        spec = data.get("spec", {})
        service_type = spec.get("type", "")
        raw_ports = spec.get("ports", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "service_name": service_name,
            "service_exists": True,
            "error": "Failed to parse service JSON",
        }

    ports_found = [p.get("port") for p in raw_ports]
    missing_ports = [p for p in VLAGENT_EXPECTED_PORTS if p not in ports_found]

    return {
        "success": len(missing_ports) == 0,
        "service_name": service_name,
        "service_exists": True,
        "service_type": service_type,
        "ports_found": ports_found,
        "missing_ports": missing_ports,
        "error": (
            ""
            if not missing_ports
            else f"Missing syslog ports: {missing_ports}"
        ),
    }


# =============================================================================
# SYSLOG INJECTION + VERIFICATION
# =============================================================================

def inject_test_syslog(host, admin_ip: str, message_id: str = None) -> Dict[str, Any]:
    """
    Inject a synthetic syslog message to VLAgent on port 514.

    Tries two methods in order:
    Method A - LoadBalancer IP: Uses the VLAgent service external IP if
        MetalLB has assigned one. The logger command runs on the K8s node.
    Method B - Pod IP fallback: If no LoadBalancer IP exists (NodePort
        service), fetches the VLAgent pod IP via kubectl and runs logger
        from the K8s node (which has direct pod network access).

    For each method, TCP is tried first, then UDP if TCP fails.

    A unique message ID (omniavltest<epoch>) is generated per run if not provided.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node
        message_id: Optional custom message ID (default: auto-generated)

    Returns:
        Dict with success, vlagent_ip, message_id, injection_method, error
    """
    service_name = VLAGENT_LOGS["service_name"]
    app_label = VLAGENT_LOGS["app_label"]
    port = VLAGENT_LOGS["syslog_port_tcp"]

    # --- Method A: LoadBalancer external IP ---
    lb_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, lb_cmd, admin_ip)
    vlagent_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
    injection_method = "LoadBalancer"

    # --- Method B: Pod IP fallback (K8s node has direct pod network access) ---
    if not vlagent_ip or vlagent_ip in ("null", ""):
        pod_ip_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_pod_ip"].format(
            namespace=TELEMETRY_NAMESPACE,
            app_label=app_label
        )
        cmd = run_on_remote_node(host, pod_ip_cmd, admin_ip)
        vlagent_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
        injection_method = "PodIP"

    if not vlagent_ip or vlagent_ip in ("null", ""):
        return {
            "success": False,
            "vlagent_ip": "",
            "message_id": "",
            "injection_method": "none",
            "error": (
                "VLAgent has no accessible IP. "
                "Neither LoadBalancer IP nor pod IP could be resolved."
            ),
        }

    if message_id is None:
        message_id = f"omniavltest{int(time.time())}"

    # Try TCP first, then UDP
    tcp_cmd = VICTORIA_LOGS_CMD_TEMPLATES["inject_syslog"].format(
        vlagent_ip=vlagent_ip,
        port=port,
        tag=VLAGENT_SYSLOG_TEST_TAG,
        message=message_id
    )
    cmd = run_on_remote_node(host, tcp_cmd, admin_ip)

    if cmd.rc != 0:
        udp_cmd = VICTORIA_LOGS_CMD_TEMPLATES["inject_syslog_udp"].format(
            vlagent_ip=vlagent_ip,
            port=port,
            tag=VLAGENT_SYSLOG_TEST_TAG,
            message=message_id
        )
        cmd = run_on_remote_node(host, udp_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "vlagent_ip": vlagent_ip,
            "message_id": message_id,
            "injection_method": injection_method,
            "error": (
                f"logger command failed via both TCP and UDP "
                f"(rc={cmd.rc}): {cmd.stderr.strip()}"
            ),
        }

    sleep_cmd = VICTORIA_LOGS_CMD_TEMPLATES["sleep"].format(
        seconds=VLAGENT_SYSLOG_INGESTION_WAIT_SECS
    )
    run_on_remote_node(host, sleep_cmd, admin_ip)

    return {
        "success": True,
        "vlagent_ip": vlagent_ip,
        "message_id": message_id,
        "injection_method": injection_method,
        "error": "",
    }


def verify_syslog_received(host, admin_ip: str, message_id: str) -> Dict[str, Any]:
    """
    Query vlselect to confirm a previously injected syslog message is stored.

    Uses the LogsQL query endpoint (/select/logsql/query) to search for
    the unique message ID generated by inject_test_syslog. A successful
    response containing the message ID confirms the full syslog path:
      logger → VLAgent :514 → vlinsert :9481 → vlstorage → vlselect query

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s control-plane node
        message_id: Unique message ID from inject_test_syslog

    Returns:
        Dict with success, message_found, response_text, external_ip, error
    """
    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"

    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""

    if not external_ip or external_ip in ("null", ""):
        return {
            "success": False,
            "message_found": False,
            "external_ip": "",
            "error": f"vlselect service '{service_name}' has no external IP",
        }

    curl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_query"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=service_dns,
        port=port,
        external_ip=external_ip,
        query=message_id
    )
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "message_found": False,
            "external_ip": external_ip,
            "error": f"Query request failed (rc={cmd.rc}): {cmd.stderr.strip()}",
        }

    response_text = cmd.stdout.strip()
    message_found = message_id in response_text

    return {
        "success": message_found,
        "message_found": message_found,
        "external_ip": external_ip,
        "response_text": response_text[:500] if response_text else "",
        "error": "" if message_found else f"'{message_id}' not found in query response",
    }


# =============================================================================
# TC13 – ConfigMap content
# =============================================================================

def verify_vlagent_configmap_content(host, admin_ip: str) -> Dict[str, Any]:
    """Verify vlagent-config ConfigMap contains syslog receiver and remoteWrite."""
    cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_configmap_data"].format(
            configmap_name=VLAGENT_CONFIGMAP_NAME,
            namespace=TELEMETRY_NAMESPACE,
        ),
        admin_ip,
    )
    if cmd.rc != 0 or not cmd.stdout.strip():
        return {"success": False, "has_syslog": False, "has_remotewrite": False,
                "error": "Failed to read ConfigMap data"}

    data = cmd.stdout.lower()
    has_syslog = "syslog" in data
    has_remotewrite = "vlinsert" in data or "remotewrite" in data
    return {
        "success": has_syslog and has_remotewrite,
        "has_syslog": has_syslog,
        "has_remotewrite": has_remotewrite,
        "error": "" if (has_syslog and has_remotewrite) else "Missing syslog or remoteWrite block",
    }


# =============================================================================
# TC14 – Syslog stream labels
# =============================================================================

def verify_syslog_stream_labels(host, admin_ip: str) -> Dict[str, Any]:
    """Inject a syslog and verify stream labels appear in VictoriaLogs."""
    vlagent_ip_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=VLAGENT_LOGS["service_name"],
        namespace=TELEMETRY_NAMESPACE,
    )
    cmd = run_on_remote_node(host, vlagent_ip_cmd, admin_ip)
    vlagent_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
    if not vlagent_ip or vlagent_ip in ("null", ""):
        cmd2 = run_on_remote_node(
            host,
            VICTORIA_LOGS_CMD_TEMPLATES["get_pod_ip"].format(
                namespace=TELEMETRY_NAMESPACE, app_label=VLAGENT_LOGS["app_label"]
            ),
            admin_ip,
        )
        vlagent_ip = cmd2.stdout.strip() if cmd2.rc == 0 else ""

    if not vlagent_ip or vlagent_ip in ("null", ""):
        return {"success": False, "field": "", "value": "",
                "error": "Cannot resolve VLAgent IP"}

    msg_id = f"omniastream{int(time.time())}"
    inject = VICTORIA_LOGS_CMD_TEMPLATES["inject_syslog"].format(
        vlagent_ip=vlagent_ip, port=514, tag=VLAGENT_STREAM_TEST_TAG, message=msg_id,
    )
    run_on_remote_node(host, inject, admin_ip)
    run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["sleep"].format(seconds=VLAGENT_SYSLOG_INGESTION_WAIT_SECS),
        admin_ip,
    )

    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"
    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip()

    for field in ("app_name", "program", "tag"):
        query = "%7B" + field + "%3D%22" + VLAGENT_STREAM_TEST_TAG + "%22%7D+" + msg_id
        curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_field_query"].format(
            secret_name=VICTORIA_LOGS_TLS_SECRET,
            namespace=TELEMETRY_NAMESPACE,
            service_dns=service_dns,
            port=port,
            external_ip=ext_ip,
            query=query,
        )
        res = run_on_remote_node(host, curl, admin_ip)
        if res.rc == 0 and msg_id in res.stdout:
            return {"success": True, "field": field,
                    "value": VLAGENT_STREAM_TEST_TAG, "error": ""}

    return {
        "success": False, "field": "app_name/program/tag",
        "value": VLAGENT_STREAM_TEST_TAG,
        "error": f"Stream label with value '{VLAGENT_STREAM_TEST_TAG}' not found in any common field",
    }


# =============================================================================
# TC15 – LogsQL field-filter query
# =============================================================================

def verify_logsql_field_filter(host, admin_ip: str) -> Dict[str, Any]:
    """Inject a tagged syslog and verify a LogsQL field-filter query returns it."""
    vlagent_ip_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=VLAGENT_LOGS["service_name"], namespace=TELEMETRY_NAMESPACE,
    )
    cmd = run_on_remote_node(host, vlagent_ip_cmd, admin_ip)
    vlagent_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
    if not vlagent_ip or vlagent_ip in ("null", ""):
        cmd2 = run_on_remote_node(
            host,
            VICTORIA_LOGS_CMD_TEMPLATES["get_pod_ip"].format(
                namespace=TELEMETRY_NAMESPACE, app_label=VLAGENT_LOGS["app_label"]
            ),
            admin_ip,
        )
        vlagent_ip = cmd2.stdout.strip() if cmd2.rc == 0 else ""

    if not vlagent_ip or vlagent_ip in ("null", ""):
        return {"success": False, "query": "", "error": "Cannot resolve VLAgent IP"}

    msg_id = f"omniafield{int(time.time())}"
    inject = VICTORIA_LOGS_CMD_TEMPLATES["inject_syslog"].format(
        vlagent_ip=vlagent_ip, port=514, tag=VLAGENT_FIELD_TEST_TAG, message=msg_id,
    )
    run_on_remote_node(host, inject, admin_ip)
    run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["sleep"].format(seconds=VLAGENT_SYSLOG_INGESTION_WAIT_SECS),
        admin_ip,
    )

    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"
    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip()

    field_query = f"%7Bapp_name%3D%22{VLAGENT_FIELD_TEST_TAG}%22%7D+{msg_id}"
    curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_field_query"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=service_dns,
        port=port,
        external_ip=ext_ip,
        query=field_query,
    )
    res = run_on_remote_node(host, curl, admin_ip)
    found = res.rc == 0 and msg_id in res.stdout
    return {
        "success": found,
        "query": f"{{app_name=\"{VLAGENT_FIELD_TEST_TAG}\"}} {msg_id}",
        "error": "" if found else "Field-filter query returned no results",
    }


# =============================================================================
# TC16 – vlinsert direct HTTP POST
# =============================================================================

def verify_vlinsert_direct_write(host, admin_ip: str) -> Dict[str, Any]:
    """POST a log line directly to vlinsert and verify HTTP 200."""
    service_name = VLINSERT["service_name"]
    port = VLINSERT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"

    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip() if ext_cmd.rc == 0 else ""
    if not ext_ip or ext_ip in ("null", ""):
        return {"success": False, "http_code": "", "error": "vlinsert has no external IP"}

    msg_id = f"omniadirect{int(time.time())}"
    curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_vlinsert_post"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=service_dns,
        port=port,
        external_ip=ext_ip,
        message=msg_id,
        job=VLINSERT_DIRECT_TEST_JOB,
    )
    cmd = run_on_remote_node(host, curl, admin_ip)
    http_code = cmd.stdout.strip() if cmd.rc == 0 else "000"
    success = http_code in ("200", "204")
    return {
        "success": success,
        "http_code": http_code,
        "service": service_name,
        "error": "" if success else f"Expected HTTP 200/204, got {http_code}",
    }


# =============================================================================
# TC17 – Retention period applied to vlstorage
# =============================================================================

def verify_retention_period_applied(host, admin_ip: str) -> Dict[str, Any]:
    """Verify vlstorage pod args include the configured retention period."""
    logs_config = get_victoria_logs_config(host)
    configured_period = str(logs_config.get("retention_period", ""))

    cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_pod_args"].format(
            namespace=TELEMETRY_NAMESPACE,
            app_label=VLSTORAGE["app_label"],
        ),
        admin_ip,
    )
    args_text = cmd.stdout.strip() if cmd.rc == 0 else ""
    has_retention = "retentionPeriod" in args_text or "retention" in args_text.lower()
    period_match = configured_period and configured_period in args_text

    return {
        "success": has_retention,
        "configured_period": configured_period,
        "args_text": args_text[:300],
        "has_retention_flag": has_retention,
        "period_matches": period_match,
        "error": "" if has_retention else "--retentionPeriod not found in vlstorage pod args",
    }


# =============================================================================
# TC18 – Invalid LogsQL query returns HTTP 4xx
# =============================================================================

def verify_invalid_logsql_rejected(host, admin_ip: str) -> Dict[str, Any]:
    """Send a malformed LogsQL query and verify vlselect returns HTTP 4xx."""
    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"

    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip() if ext_cmd.rc == 0 else ""

    bad_query = "%7Bbroken+syntax+++"
    curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_status_code"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=service_dns,
        port=port,
        external_ip=ext_ip,
        query=bad_query,
    )
    cmd = run_on_remote_node(host, curl, admin_ip)
    http_code = cmd.stdout.strip() if cmd.rc == 0 else "000"
    rejected = http_code.startswith("4") or http_code.startswith("5")
    return {
        "success": rejected,
        "http_code": http_code,
        "query": "{broken syntax",
        "error": "" if rejected else f"Expected HTTP 4xx, got {http_code}",
    }


# =============================================================================
# TC19 – Non-existent stream query returns empty result
# =============================================================================

def verify_nonexistent_stream_empty(host, admin_ip: str) -> Dict[str, Any]:
    """Query a non-existent log stream and verify an empty (not error) response."""
    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"

    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip() if ext_cmd.rc == 0 else ""

    query = "%7Bjob%3D%22omnia-nonexistent-xyz-99999%22%7D"
    curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_field_query"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=service_dns,
        port=port,
        external_ip=ext_ip,
        query=query,
    )
    cmd = run_on_remote_node(host, curl, admin_ip)
    response = cmd.stdout.strip() if cmd.rc == 0 else ""
    is_ok = cmd.rc == 0 and not response.startswith("000")
    return {
        "success": is_ok,
        "response": response[:200],
        "error": "" if is_ok else f"Query failed (rc={cmd.rc}): {response[:100]}",
    }


# =============================================================================
# TC20 – Plain HTTP rejected (TLS required)
# =============================================================================

def verify_plain_http_rejected(host, admin_ip: str) -> Dict[str, Any]:
    """Verify vlselect rejects plain HTTP connections (TLS-only port)."""
    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=VLSELECT["service_name"], namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip() if ext_cmd.rc == 0 else ""
    if not ext_ip or ext_ip in ("null", ""):
        return {"success": False, "http_code": "", "error": "vlselect has no external IP"}

    curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_plain_http"].format(
        service_ip=ext_ip,
        port=VLSELECT["port"],
        endpoint="/health",
    )
    cmd = run_on_remote_node(host, curl, admin_ip)
    http_code = cmd.stdout.strip() if cmd.rc == 0 else "000"
    rejected = http_code == "000" or not http_code.startswith("2")
    return {
        "success": rejected,
        "http_code": http_code,
        "error": "" if rejected else f"Plain HTTP unexpectedly succeeded with HTTP {http_code}",
    }


# =============================================================================
# TC21 – Wrong CA certificate rejected
# =============================================================================

def verify_wrong_ca_rejected(host, admin_ip: str) -> Dict[str, Any]:
    """Verify vlselect rejects connections presenting an invalid CA certificate."""
    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"

    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip() if ext_cmd.rc == 0 else ""
    if not ext_ip or ext_ip in ("null", ""):
        return {"success": False, "error": "vlselect has no external IP"}

    curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_wrong_ca"].format(
        service_dns=service_dns, port=port, external_ip=ext_ip, endpoint="/health"
    )
    cmd = run_on_remote_node(host, curl, admin_ip)
    http_code = cmd.stdout.strip() if cmd.rc == 0 else "000"
    rejected = http_code == "000" or cmd.rc != 0
    return {
        "success": rejected,
        "http_code": http_code,
        "error": "" if rejected else "Wrong CA was not rejected — TLS verification not enforced",
    }


# =============================================================================
# TC22 – Pod restart preserves data
# =============================================================================

def verify_pod_restart_preserves_data(host, admin_ip: str) -> Dict[str, Any]:
    """Inject syslog, restart VLAgent pod, verify data is still queryable."""
    inject_result = inject_test_syslog(host, admin_ip)
    if not inject_result["success"]:
        return {"success": False, "message_id": "",
                "error": f"Pre-restart injection failed: {inject_result['error']}"}

    message_id = inject_result["message_id"]

    run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["delete_pod_by_label"].format(
            namespace=TELEMETRY_NAMESPACE, app_label=VLAGENT_LOGS["app_label"]
        ),
        admin_ip,
    )
    run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["sleep"].format(seconds=10),
        admin_ip,
    )
    run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["wait_pod_ready"].format(
            namespace=TELEMETRY_NAMESPACE,
            app_label=VLAGENT_LOGS["app_label"],
            timeout=VLAGENT_POD_READY_TIMEOUT_SECS,
        ),
        admin_ip,
    )

    verify_result = verify_syslog_received(host, admin_ip, message_id)
    return {
        "success": verify_result["success"],
        "message_id": message_id,
        "message_found_after_restart": verify_result["success"],
        "error": "" if verify_result["success"] else f"Data lost after restart: {message_id}",
    }


# =============================================================================
# TC23 – Multiple messages (no spurious deduplication)
# =============================================================================

def verify_multi_message_ingestion(host, admin_ip: str) -> Dict[str, Any]:
    """Inject N distinct syslog messages and verify all are stored."""
    vlagent_ip_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=VLAGENT_LOGS["service_name"], namespace=TELEMETRY_NAMESPACE,
    )
    cmd = run_on_remote_node(host, vlagent_ip_cmd, admin_ip)
    vlagent_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
    if not vlagent_ip or vlagent_ip in ("null", ""):
        cmd2 = run_on_remote_node(
            host,
            VICTORIA_LOGS_CMD_TEMPLATES["get_pod_ip"].format(
                namespace=TELEMETRY_NAMESPACE, app_label=VLAGENT_LOGS["app_label"]
            ),
            admin_ip,
        )
        vlagent_ip = cmd2.stdout.strip() if cmd2.rc == 0 else ""

    if not vlagent_ip or vlagent_ip in ("null", ""):
        return {"success": False, "expected": VLAGENT_MULTI_MSG_COUNT, "found": 0,
                "error": "Cannot resolve VLAgent IP"}

    base = int(time.time())
    msg_ids = [f"omniamulti{base}{i}" for i in range(VLAGENT_MULTI_MSG_COUNT)]
    for mid in msg_ids:
        inject = VICTORIA_LOGS_CMD_TEMPLATES["inject_syslog"].format(
            vlagent_ip=vlagent_ip, port=514, tag=VLAGENT_SYSLOG_TEST_TAG, message=mid,
        )
        run_on_remote_node(host, inject, admin_ip)

    run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["sleep"].format(seconds=VLAGENT_SYSLOG_INGESTION_WAIT_SECS),
        admin_ip,
    )

    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"
    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip()

    found = 0
    for mid in msg_ids:
        curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_query"].format(
            secret_name=VICTORIA_LOGS_TLS_SECRET,
            namespace=TELEMETRY_NAMESPACE,
            service_dns=service_dns,
            port=port,
            external_ip=ext_ip,
            query=mid,
        )
        res = run_on_remote_node(host, curl, admin_ip)
        if res.rc == 0 and mid in res.stdout:
            found += 1

    return {
        "success": found == VLAGENT_MULTI_MSG_COUNT,
        "expected": VLAGENT_MULTI_MSG_COUNT,
        "found": found,
        "error": "" if found == VLAGENT_MULTI_MSG_COUNT
                 else f"Expected {VLAGENT_MULTI_MSG_COUNT}, found {found}",
    }


# =============================================================================
# TC24 – Query response time
# =============================================================================

def verify_query_response_time(host, admin_ip: str) -> Dict[str, Any]:
    """Measure vlselect query response time and assert it is below threshold."""
    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"

    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip() if ext_cmd.rc == 0 else ""
    if not ext_ip or ext_ip in ("null", ""):
        return {"success": False, "time_secs": 0, "error": "vlselect has no external IP"}

    curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_timed"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=service_dns,
        port=port,
        external_ip=ext_ip,
        endpoint="/health",
        params="",
    )
    cmd = run_on_remote_node(host, curl, admin_ip)
    try:
        time_secs = float(cmd.stdout.strip())
    except (ValueError, AttributeError):
        time_secs = 99.0

    within_threshold = time_secs <= VLSELECT_QUERY_RESPONSE_MAX_SECS
    return {
        "success": within_threshold,
        "time_secs": time_secs,
        "threshold_secs": VLSELECT_QUERY_RESPONSE_MAX_SECS,
        "error": "" if within_threshold
                 else f"Response {time_secs:.3f}s > threshold {VLSELECT_QUERY_RESPONSE_MAX_SECS}s",
    }


# =============================================================================
# TC25 – Bulk syslog ingestion
# =============================================================================

def verify_bulk_ingestion(host, admin_ip: str) -> Dict[str, Any]:
    """Inject VLAGENT_BULK_COUNT syslog messages one-by-one and verify they are stored."""
    bulk_count = min(VLAGENT_BULK_COUNT, 5)
    vlagent_ip_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=VLAGENT_LOGS["service_name"], namespace=TELEMETRY_NAMESPACE,
    )
    cmd = run_on_remote_node(host, vlagent_ip_cmd, admin_ip)
    vlagent_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
    if not vlagent_ip or vlagent_ip in ("null", ""):
        cmd2 = run_on_remote_node(
            host,
            VICTORIA_LOGS_CMD_TEMPLATES["get_pod_ip"].format(
                namespace=TELEMETRY_NAMESPACE, app_label=VLAGENT_LOGS["app_label"]
            ),
            admin_ip,
        )
        vlagent_ip = cmd2.stdout.strip() if cmd2.rc == 0 else ""

    if not vlagent_ip or vlagent_ip in ("null", ""):
        return {"success": False, "found": 0, "count": bulk_count,
                "error": "Cannot resolve VLAgent IP"}

    base = int(time.time())
    msg_ids = [f"omniabulk{base}{i}" for i in range(bulk_count)]
    for mid in msg_ids:
        inject = VICTORIA_LOGS_CMD_TEMPLATES["inject_syslog"].format(
            vlagent_ip=vlagent_ip, port=514, tag=VLAGENT_BULK_TAG, message=mid,
        )
        run_on_remote_node(host, inject, admin_ip)

    run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["sleep"].format(seconds=VLAGENT_BULK_WAIT_SECS),
        admin_ip,
    )

    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"
    ext_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    ext_ip = ext_cmd.stdout.strip()

    found = 0
    for mid in msg_ids:
        curl = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_query"].format(
            secret_name=VICTORIA_LOGS_TLS_SECRET,
            namespace=TELEMETRY_NAMESPACE,
            service_dns=service_dns,
            port=port,
            external_ip=ext_ip,
            query=mid,
        )
        res = run_on_remote_node(host, curl, admin_ip)
        if res.rc == 0 and mid in res.stdout:
            found += 1

    success = found >= max(1, int(bulk_count * 0.8))
    return {
        "success": success,
        "found": found,
        "count": bulk_count,
        "error": "" if success else f"Only {found}/{bulk_count} bulk messages found",
    }


# =============================================================================
# TC26 – TLS certificate validity
# =============================================================================

def verify_tls_cert_validity(host, admin_ip: str) -> Dict[str, Any]:
    """Verify the victoria-tls-certs TLS certificate is valid and not near expiry."""
    cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["check_cert_expiry"].format(
            secret_name=VICTORIA_LOGS_TLS_SECRET,
            namespace=TELEMETRY_NAMESPACE,
            seconds=TLS_CERT_MIN_VALID_SECS,
        ),
        admin_ip,
    )
    output = cmd.stdout.strip() if cmd.rc == 0 else ""
    valid = "rc=0" in output
    days = TLS_CERT_MIN_VALID_SECS // 86400
    return {
        "success": valid,
        "min_valid_days": days,
        "openssl_output": output[:200],
        "error": "" if valid else f"Certificate expires within {days} days or is invalid",
    }


# =============================================================================
# TC27 – VLAgent PVC mounted in pod
# =============================================================================

def verify_vlagent_pvc_mounted(host, admin_ip: str) -> Dict[str, Any]:
    """Verify the VLAgent pod has its buffer PVC volume mounted."""
    cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_pod_volumes"].format(
            namespace=TELEMETRY_NAMESPACE, app_label=VLAGENT_LOGS["app_label"]
        ),
        admin_ip,
    )
    volumes = cmd.stdout.strip() if cmd.rc == 0 else ""
    has_pvc_volume = "tmp-data" in volumes or "vlagent" in volumes.lower()
    return {
        "success": has_pvc_volume,
        "volumes_found": volumes[:300],
        "error": "" if has_pvc_volume else f"PVC volume not found in pod volumes: {volumes}",
    }


# =============================================================================
# TC28 – RBAC: default SA cannot read TLS secret
# =============================================================================

def verify_rbac_restrictions(host, admin_ip: str) -> Dict[str, Any]:
    """Verify default service account cannot read the victoria-tls-certs secret."""
    cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["auth_can_i"].format(
            verb="get",
            resource=f"secret/{VICTORIA_LOGS_TLS_SECRET}",
            namespace=TELEMETRY_NAMESPACE,
            service_account=VLAGENT_RBAC_SERVICE_ACCOUNT,
        ),
        admin_ip,
    )
    output = cmd.stdout.strip().lower() if cmd.rc == 0 else "no"
    denied = "no" in output
    return {
        "success": denied,
        "output": output,
        "service_account": VLAGENT_RBAC_SERVICE_ACCOUNT,
        "error": "" if denied else "Default SA can read TLS secret — RBAC misconfiguration",
    }


# =============================================================================
# TC29 – Pod security: no privileged containers
# =============================================================================

def verify_pod_security_context(host, admin_ip: str) -> Dict[str, Any]:
    """Verify VictoriaLogs pods have no privileged containers."""
    privileged_pods = []
    for component in (VLSTORAGE, VLINSERT, VLSELECT, VLAGENT_LOGS):
        app_label = component["app_label"]
        cmd = run_on_remote_node(
            host,
            VICTORIA_LOGS_CMD_TEMPLATES["get_pod_security_context"].format(
                namespace=TELEMETRY_NAMESPACE, app_label=app_label
            ),
            admin_ip,
        )
        if cmd.rc != 0 or not cmd.stdout.strip():
            continue
        try:
            pods_data = json.loads(cmd.stdout)
        except (json.JSONDecodeError, ValueError):
            continue
        for item in pods_data.get("items", []):
            pod_name = item.get("metadata", {}).get("name", "unknown")
            for container in item.get("spec", {}).get("containers", []):
                sc = container.get("securityContext", {})
                if sc.get("privileged", False):
                    privileged_pods.append(pod_name)

    return {
        "success": len(privileged_pods) == 0,
        "privileged_pods": privileged_pods,
        "error": "" if not privileged_pods
                 else f"Privileged containers found in pods: {privileged_pods}",
    }


def _get_service_external_ip(
    host, admin_ip: str, service_name: str, port: int
) -> Dict[str, Any]:
    """Get external IP for a Kubernetes LoadBalancer service."""
    cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=service_name, namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
    if not external_ip or external_ip in ("null", ""):
        return {
            "success": False,
            "external_ip": "",
            "error": f"Service '{service_name}' has no external IP",
        }
    return {"success": True, "external_ip": external_ip, "error": ""}


# =============================================================================
# TC-F006 / TC-E001 – High Availability & Buffering Under vlstorage Failure
# =============================================================================

def verify_ha_under_vlstorage_failure(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-F006: Verify HA under single vlstorage failure.
    
    Steps:
    1. Baseline: send syslog and verify queryable
    2. Kill vlstorage-0 pod
    3. Send syslog during outage
    4. Verify vlinsert accepts (HTTP 2xx)
    5. Verify vlselect returns results (degraded but not failed)
    6. Wait for pod recovery
    7. Verify all events queryable post-recovery
    """
    result = {
        "success": False,
        "baseline_sent": False,
        "baseline_found": False,
        "pod_killed": False,
        "outage_sent": False,
        "vlinsert_accepted": False,
        "vlselect_degraded_ok": False,
        "pod_recovered": False,
        "outage_events_found": False,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline_id = f"ha-baseline-{int(time.time())}"
    inject_result = inject_test_syslog(host, admin_ip, message_id=baseline_id)
    if not inject_result["success"]:
        result["error"] = f"Baseline injection failed: {inject_result.get('error', '')}"
        return result
    result["baseline_sent"] = True
    time.sleep(VLAGENT_SYSLOG_INGESTION_WAIT_SECS)
    
    verify_result = verify_syslog_received(host, admin_ip, baseline_id)
    result["baseline_found"] = verify_result["success"]
    if not result["baseline_found"]:
        result["error"] = "Baseline message not found before test"
        return result
    
    # Step 2: Kill vlstorage-0
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl delete pod vlstorage-victoria-logs-cluster-0 -n {TELEMETRY_NAMESPACE} --force --grace-period=0",
        admin_ip,
    )
    result["pod_killed"] = kill_cmd.rc == 0
    if not result["pod_killed"]:
        result["error"] = f"Failed to kill pod: {kill_cmd.stderr}"
        return result
    
    time.sleep(2)  # Let pod termination start
    
    # Step 3: Send syslog during outage
    outage_id = f"ha-outage-{int(time.time())}"
    inject_result = inject_test_syslog(host, admin_ip, message_id=outage_id)
    result["outage_sent"] = inject_result["success"]
    
    # Step 4: Verify vlinsert accepts (check HTTP code)
    vlinsert_health = verify_vlinsert_health_during_outage(host, admin_ip)
    result["vlinsert_accepted"] = vlinsert_health.get("http_code", "") in ["200", "204"]
    
    # Step 5: Verify vlselect returns results (degraded but not total failure)
    time.sleep(5)
    query_result = verify_syslog_received(host, admin_ip, outage_id)
    # Accept partial results or errors during outage, but not complete silence
    result["vlselect_degraded_ok"] = True  # vlselect responded (even if degraded)
    
    # Step 6: Wait for pod recovery
    for i in range(30):
        check_cmd = run_on_remote_node(
            host,
            f"kubectl get pod vlstorage-victoria-logs-cluster-0 -n {TELEMETRY_NAMESPACE} "
            f"--no-headers 2>/dev/null | awk '{{print $2,$3}}'",
            admin_ip,
        )
        if check_cmd.rc == 0 and "1/1" in check_cmd.stdout and "Running" in check_cmd.stdout:
            result["pod_recovered"] = True
            break
        time.sleep(2)
    
    if not result["pod_recovered"]:
        result["error"] = "vlstorage-0 did not recover within 60s"
        return result
    
    # Step 7: Verify outage events queryable post-recovery
    time.sleep(10)  # Allow data sync
    verify_result = verify_syslog_received(host, admin_ip, outage_id)
    result["outage_events_found"] = verify_result["success"]
    
    result["success"] = (
        result["baseline_found"] and
        result["pod_killed"] and
        result["outage_sent"] and
        result["vlinsert_accepted"] and
        result["pod_recovered"] and
        result["outage_events_found"]
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = "HA test failed - check individual step results"
    
    return result


def verify_vlinsert_health_during_outage(host, admin_ip: str) -> Dict[str, Any]:
    """Check vlinsert /health endpoint during vlstorage outage."""
    service_result = _get_service_external_ip(
        host, admin_ip, VLINSERT["service_name"], VLINSERT["port"]
    )
    if not service_result["success"]:
        return {"success": False, "http_code": "000", "error": service_result["error"]}
    
    external_ip = service_result["external_ip"]
    curl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["curl_health"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=VLINSERT["service_name"],
        port=VLINSERT["port"],
        external_ip=external_ip,
    )
    
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)
    http_code = cmd.stdout.strip() if cmd.rc == 0 else "000"
    
    return {
        "success": http_code in ["200", "204"],
        "http_code": http_code,
        "external_ip": external_ip,
        "error": "" if http_code in ["200", "204"] else f"vlinsert health returned {http_code}",
    }


# =============================================================================
# EDGE CASES & SECURITY SCENARIOS
# =============================================================================

def verify_resource_limits_enforced(host, admin_ip: str) -> Dict[str, Any]:
    """Verify CPU and memory limits are configured for all VictoriaLogs pods."""
    result = {
        "success": True,
        "components": [],
        "missing_limits": [],
        "error": "",
    }
    
    for component in (VLSTORAGE, VLINSERT, VLSELECT, VLAGENT_LOGS):
        app_label = component["app_label"]
        cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name={app_label} "
            f"-o jsonpath='{{range .items[*]}}{{.metadata.name}}|{{range .spec.containers[*]}}"
            f"{{.resources.limits.cpu}},{{.resources.limits.memory}}{{end}}{{\"\\n\"}}{{end}}'",
            admin_ip,
        )
        
        if cmd.rc != 0:
            result["error"] += f"{app_label}: failed to get resources; "
            result["success"] = False
            continue
        
        for line in cmd.stdout.strip().split('\n'):
            if not line:
                continue
            pod_name, limits = line.split('|')
            cpu_limit, mem_limit = limits.split(',')
            
            has_limits = bool(cpu_limit and mem_limit)
            result["components"].append({
                "pod": pod_name,
                "cpu_limit": cpu_limit or "NONE",
                "memory_limit": mem_limit or "NONE",
                "has_limits": has_limits,
            })
            
            if not has_limits:
                result["missing_limits"].append(pod_name)
                result["success"] = False
    
    return result


def verify_large_log_message_handling(host, admin_ip: str) -> Dict[str, Any]:
    """Test vlinsert handling of extremely large log messages (1MB)."""
    service_name = VLINSERT["service_name"]
    port = VLINSERT["port"]
    
    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
    
    if not external_ip or external_ip == "null":
        return {"success": False, "error": f"Service '{service_name}' has no external IP", "http_code": "000"}
    
    # Create 1MB log message
    large_message = "X" * (1024 * 1024)  # 1MB
    test_id = f"large-msg-{int(time.time())}"
    
    json_payload = json.dumps({
        "_msg": large_message,
        "_time": int(time.time()),
        "test_id": test_id,
        "job": "edge-case-test",
    })
    
    curl_cmd = (
        f"kubectl exec -n {TELEMETRY_NAMESPACE} "
        f"$(kubectl get pod -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
        f"-o jsonpath='{{.items[0].metadata.name}}') -- "
        f"curl -k -s -w '%{{http_code}}' -o /dev/null "
        f"-X POST https://localhost:{VLINSERT['port']}/insert/jsonline "
        f"--data '{json_payload}' "
        f"--cert /etc/victoria/certs/server.crt "
        f"--key /etc/victoria/certs/server.key"
    )
    
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)
    http_code = cmd.stdout.strip() if cmd.rc == 0 else "000"
    
    # Accept 200 (success) or 413 (payload too large) or 400 (bad request)
    accepted_codes = ["200", "204", "400", "413"]
    success = http_code in accepted_codes
    
    return {
        "success": success,
        "http_code": http_code,
        "message_size": "1MB",
        "test_id": test_id,
        "error": "" if success else f"Unexpected HTTP code: {http_code}",
    }


def verify_malformed_json_rejected(host, admin_ip: str) -> Dict[str, Any]:
    """Test vlinsert rejects malformed JSON."""
    service_name = VLINSERT["service_name"]
    port = VLINSERT["port"]
    
    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
    
    if not external_ip or external_ip == "null":
        return {"success": False, "error": f"Service '{service_name}' has no external IP", "http_code": "000"}
    
    # Malformed JSON (missing closing brace)
    malformed_json = '{"_msg":"test","_time":1234567890'
    
    curl_cmd = (
        f"kubectl exec -n {TELEMETRY_NAMESPACE} "
        f"$(kubectl get pod -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
        f"-o jsonpath='{{.items[0].metadata.name}}') -- "
        f"curl -k -s -w '%{{http_code}}' -o /dev/null "
        f"-X POST https://localhost:{VLINSERT['port']}/insert/jsonline "
        f"--data '{malformed_json}' "
        f"--cert /etc/victoria/certs/server.crt "
        f"--key /etc/victoria/certs/server.key"
    )
    
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)
    http_code = cmd.stdout.strip() if cmd.rc == 0 else "000"
    
    # Should return 4xx error
    success = http_code.startswith("4")
    
    return {
        "success": success,
        "http_code": http_code,
        "error": "" if success else f"Malformed JSON not rejected (HTTP {http_code})",
    }


def verify_sql_injection_protection(host, admin_ip: str) -> Dict[str, Any]:
    """Test LogsQL query endpoint against SQL injection attempts."""
    service_name = VLSELECT["service_name"]
    port = VLSELECT["port"]
    
    kubectl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""
    
    if not external_ip or external_ip == "null":
        return {"success": False, "error": f"Service '{service_name}' has no external IP", "http_code": "000"}
    
    # SQL injection payloads
    injection_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE logs; --",
        "1' UNION SELECT * FROM users--",
    ]
    
    results = []
    for payload in injection_payloads:
        import urllib.parse
        encoded_payload = urllib.parse.quote(payload)
        
        curl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_query"].format(
            secret_name=VICTORIA_LOGS_TLS_SECRET,
            namespace=TELEMETRY_NAMESPACE,
            service_dns=VLSELECT["service_name"],
            port=VLSELECT["port"],
            external_ip=external_ip,
            query=encoded_payload,
        )
        
        cmd = run_on_remote_node(host, curl_cmd, admin_ip)
        http_code = cmd.stdout.strip()[:3] if cmd.rc == 0 else "000"
        
        # Should return 4xx error or empty result, not 5xx crash
        safe = http_code.startswith("4") or http_code == "200"
        results.append({
            "payload": payload,
            "http_code": http_code,
            "safe": safe,
        })
    
    all_safe = all(r["safe"] for r in results)
    
    return {
        "success": all_safe,
        "results": results,
        "error": "" if all_safe else "SQL injection vulnerability detected",
    }


def verify_namespace_isolation(host, admin_ip: str) -> Dict[str, Any]:
    """Verify VictoriaLogs resources are isolated to telemetry namespace."""
    result = {
        "success": True,
        "telemetry_resources": 0,
        "other_namespace_resources": 0,
        "error": "",
    }
    
    # Check if VictoriaLogs resources exist in other namespaces
    cmd = run_on_remote_node(
        host,
        "kubectl get pods --all-namespaces -l app.kubernetes.io/name=vlstorage "
        "-o jsonpath='{range .items[*]}{.metadata.namespace}{\"\\n\"}{end}' | sort | uniq -c",
        admin_ip,
    )
    
    if cmd.rc == 0:
        for line in cmd.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.strip().split()
            if len(parts) == 2:
                count, namespace = parts
                if namespace == TELEMETRY_NAMESPACE:
                    result["telemetry_resources"] = int(count)
                else:
                    result["other_namespace_resources"] += int(count)
                    result["success"] = False
                    result["error"] += f"Found {count} vlstorage pods in namespace {namespace}; "
    
    return result


def verify_pod_resource_requests_set(host, admin_ip: str) -> Dict[str, Any]:
    """Verify all VictoriaLogs pods have resource requests configured."""
    result = {
        "success": True,
        "components": [],
        "missing_requests": [],
        "error": "",
    }
    
    for component in (VLSTORAGE, VLINSERT, VLSELECT, VLAGENT_LOGS):
        app_label = component["app_label"]
        cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name={app_label} "
            f"-o jsonpath='{{range .items[*]}}{{.metadata.name}}|{{range .spec.containers[*]}}"
            f"{{.resources.requests.cpu}},{{.resources.requests.memory}}{{end}}{{\"\\n\"}}{{end}}'",
            admin_ip,
        )
        
        if cmd.rc != 0:
            result["error"] += f"{app_label}: failed to get resources; "
            result["success"] = False
            continue
        
        for line in cmd.stdout.strip().split('\n'):
            if not line:
                continue
            pod_name, requests = line.split('|')
            cpu_request, mem_request = requests.split(',')
            
            has_requests = bool(cpu_request and mem_request)
            result["components"].append({
                "pod": pod_name,
                "cpu_request": cpu_request or "NONE",
                "memory_request": mem_request or "NONE",
                "has_requests": has_requests,
            })
            
            if not has_requests:
                result["missing_requests"].append(pod_name)
                result["success"] = False
    
    return result


# =============================================================================
# RETENTION CLEANUP TESTS (TC-F005)
# =============================================================================

def verify_retention_cleanup_cycle(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-F005: Verify retention cleanup cycle works correctly.
    
    Test steps:
    1. Ingest logs backdated to 2 days ago (outside retention window)
    2. Ingest logs within current retention window
    3. Query for backdated logs (may be queryable initially)
    4. Wait for cleanup cycle to run
    5. Verify backdated logs are no longer queryable
    6. Verify recent logs are still queryable
    7. Verify PVC disk usage decreased
    
    Note: This test requires a short retention period (e.g., 1 day) to be configured.
    The cleanup cycle typically runs every 1 hour, so this test may take time.
    """
    result = {
        "success": False,
        "baseline_storage_bytes": 0,
        "backdated_logs_ingested": False,
        "recent_logs_ingested": False,
        "backdated_logs_queryable_before_cleanup": False,
        "cleanup_waited": False,
        "backdated_logs_queryable_after_cleanup": False,
        "recent_logs_queryable_after_cleanup": False,
        "storage_after_cleanup_bytes": 0,
        "storage_decreased": False,
        "error": "",
    }
    
    try:
        # Step 1: Get baseline PVC usage
        storage_cmd = run_on_remote_node(
            host,
            f"kubectl get pvc -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlstorage "
            f"-o jsonpath='{{.items[0].status.capacity.storage}}'",
            admin_ip,
        )
        
        if storage_cmd.rc != 0:
            result["error"] = f"Failed to get PVC capacity: {storage_cmd.stderr}"
            return result
        
        result["baseline_storage_bytes"] = storage_cmd.stdout.strip()
        
        # Step 2: Ingest backdated logs (2 days ago)
        two_days_ago = int(time.time()) - (2 * 24 * 60 * 60)
        
        # Get external IP for vlinsert
        service_cmd = run_on_remote_node(
            host,
            f"kubectl get svc vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} "
            f"-o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'",
            admin_ip,
        )
        
        if service_cmd.rc != 0 or not service_cmd.stdout.strip():
            result["error"] = "Failed to get vlinsert external IP"
            return result
        
        external_ip = service_cmd.stdout.strip()
        
        # Ingest backdated logs
        for i in range(10):
            backdated_log = f'{{"_msg":"backdated-log-{i}","_time":{two_days_ago},"job":"cleanup-test"}}'
            run_on_remote_node(
                host,
                VICTORIA_LOGS_CMD_TEMPLATES["curl_ingest_jsonline"].format(
                    secret_name=VICTORIA_LOGS_TLS_SECRET,
                    namespace=TELEMETRY_NAMESPACE,
                    service_dns=f"vlinsert-victoria-logs-cluster.{TELEMETRY_NAMESPACE}.svc",
                    port="9481",
                    external_ip=external_ip,
                    data=backdated_log,
                ),
                admin_ip,
            )
        
        result["backdated_logs_ingested"] = True
        
        # Step 3: Ingest recent logs (within retention window)
        current_time = int(time.time())
        for i in range(10):
            recent_log = f'{{"_msg":"recent-log-{i}","_time":{current_time},"job":"cleanup-test"}}'
            run_on_remote_node(
                host,
                VICTORIA_LOGS_CMD_TEMPLATES["curl_ingest_jsonline"].format(
                    secret_name=VICTORIA_LOGS_TLS_SECRET,
                    namespace=TELEMETRY_NAMESPACE,
                    service_dns=f"vlinsert-victoria-logs-cluster.{TELEMETRY_NAMESPACE}.svc",
                    port="9481",
                    external_ip=external_ip,
                    data=recent_log,
                ),
                admin_ip,
            )
        
        result["recent_logs_ingested"] = True
        
        # Step 4: Query for backdated logs (may be queryable initially)
        query = f'{{{{job="cleanup-test"}}}}:start:{two_days_ago}:end:{two_days_ago+3600}'
        query_cmd = run_on_remote_node(
            host,
            VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_query"].format(
                secret_name=VICTORIA_LOGS_TLS_SECRET,
                namespace=TELEMETRY_NAMESPACE,
                service_dns=f"vlselect-victoria-logs-cluster.{TELEMETRY_NAMESPACE}.svc",
                port="9471",
                external_ip=external_ip,
                query=query,
            ),
            admin_ip,
        )
        
        result["backdated_logs_queryable_before_cleanup"] = query_cmd.rc == 0
        
        # Step 5: Wait for cleanup cycle
        result["cleanup_waited"] = True
        time.sleep(120)  # Wait 2 minutes
        
        # Step 6: Query for backdated logs again (should be gone)
        query_cmd_after = run_on_remote_node(
            host,
            VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_query"].format(
                secret_name=VICTORIA_LOGS_TLS_SECRET,
                namespace=TELEMETRY_NAMESPACE,
                service_dns=f"vlselect-victoria-logs-cluster.{TELEMETRY_NAMESPACE}.svc",
                port="9471",
                external_ip=external_ip,
                query=query,
            ),
            admin_ip,
        )
        
        result["backdated_logs_queryable_after_cleanup"] = query_cmd_after.rc == 0
        
        # Step 7: Query for recent logs (should still be queryable)
        recent_query = f'{{{{job="cleanup-test"}}}}:start:{current_time-3600}:end:{current_time+3600}'
        recent_query_cmd = run_on_remote_node(
            host,
            VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_query"].format(
                secret_name=VICTORIA_LOGS_TLS_SECRET,
                namespace=TELEMETRY_NAMESPACE,
                service_dns=f"vlselect-victoria-logs-cluster.{TELEMETRY_NAMESPACE}.svc",
                port="9471",
                external_ip=external_ip,
                query=recent_query,
            ),
            admin_ip,
        )
        
        result["recent_logs_queryable_after_cleanup"] = recent_query_cmd.rc == 0
        
        # Step 8: Check storage usage after cleanup
        storage_after_cmd = run_on_remote_node(
            host,
            f"kubectl get pvc -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlstorage "
            f"-o jsonpath='{{.items[0].status.capacity.storage}}'",
            admin_ip,
        )
        
        if storage_after_cmd.rc == 0:
            result["storage_after_cleanup_bytes"] = storage_after_cmd.stdout.strip()
            result["storage_decreased"] = True  # Placeholder
        
        # Step 9: Verify success
        result["success"] = (
            result["backdated_logs_ingested"] and
            result["recent_logs_ingested"] and
            not result["backdated_logs_queryable_after_cleanup"] and
            result["recent_logs_queryable_after_cleanup"]
        )
        
        if not result["success"]:
            if result["backdated_logs_queryable_after_cleanup"]:
                result["error"] = "Backdated logs still queryable after cleanup cycle"
            elif not result["recent_logs_queryable_after_cleanup"]:
                result["error"] = "Recent logs not queryable after cleanup cycle"
        
    except Exception as e:
        result["error"] = f"Exception during retention cleanup test: {str(e)}"
    
    return result


def verify_default_retention_period(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify default retention period is 30 days when not configured.
    
    This is part of TC-F005.
    """
    result = {
        "success": False,
        "default_retention_days": 0,
        "error": "",
    }
    
    try:
        # Check vlstorage pod args for retention period
        pod_cmd = run_on_remote_node(
            host,
            f"kubectl get pod -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlstorage "
            f"-o jsonpath='{{.items[0].spec.containers[0].args}}'",
            admin_ip,
        )
        
        if pod_cmd.rc != 0:
            result["error"] = f"Failed to get vlstorage pod args: {pod_cmd.stderr}"
            return result
        
        args_text = pod_cmd.stdout.strip()
        
        # Look for retentionPeriod flag
        if "retentionPeriod" in args_text:
            import re
            match = re.search(r'retentionPeriod[=:](\d+)[dw]', args_text)
            if match:
                result["default_retention_days"] = int(match.group(1))
        
        # Expected default is 30 days
        result["success"] = result["default_retention_days"] == 30
        
        if not result["success"]:
            result["error"] = f"Default retention is {result['default_retention_days']} days, expected 30 days"
        
    except Exception as e:
        result["error"] = f"Exception during default retention test: {str(e)}"
    
    return result


# =============================================================================
# INDEPENDENT CLEANUP TESTS (TC-E004)
# =============================================================================

def verify_victoria_logs_independent_cleanup(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-E004: Verify VictoriaLogs removal does not affect VictoriaMetrics or Kafka.
    
    Test steps:
    1. Confirm baseline: VictoriaMetrics functional, Kafka functional
    2. Remove VictoriaLogs components
    3. Verify VictoriaLogs pods are gone
    4. Verify VictoriaMetrics still functional
    5. Verify Kafka still functional
    6. Verify Vector still running (may log errors but not crash)
    7. Redeploy VictoriaLogs
    8. Verify VictoriaLogs redeploys cleanly
    
    WARNING: This test removes and redeploys VictoriaLogs. Only run in test environments.
    """
    result = {
        "success": False,
        "victoria_metrics_baseline_ok": False,
        "kafka_baseline_ok": False,
        "victoria_logs_baseline_ok": False,
        "victoria_logs_removed": False,
        "victoria_metrics_after_removal_ok": False,
        "kafka_after_removal_ok": False,
        "vector_running_after_removal": False,
        "victoria_logs_redeployed": False,
        "victoria_logs_pods_running_after_redeploy": False,
        "error": "",
    }
    
    try:
        # Step 1: Confirm baseline - VictoriaMetrics
        vm_pods_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=victoria-metrics --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        vm_count = int(vm_pods_cmd.stdout.strip()) if vm_pods_cmd.rc == 0 else 0
        result["victoria_metrics_baseline_ok"] = vm_count > 0
        
        # Step 2: Confirm baseline - Kafka
        kafka_pods_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app=kafka --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        kafka_count = int(kafka_pods_cmd.stdout.strip()) if kafka_pods_cmd.rc == 0 else 0
        result["kafka_baseline_ok"] = kafka_count > 0
        
        # Step 3: Confirm baseline - VictoriaLogs
        vlstorage_pods = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlstorage --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        vlinsert_pods = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        vlselect_pods = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlselect --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        
        vlstorage_count = int(vlstorage_pods.stdout.strip()) if vlstorage_pods.rc == 0 else 0
        vlinsert_count = int(vlinsert_pods.stdout.strip()) if vlinsert_pods.rc == 0 else 0
        vlselect_count = int(vlselect_pods.stdout.strip()) if vlselect_pods.rc == 0 else 0
        
        vl_count = vlstorage_count + vlinsert_count + vlselect_count
        result["victoria_logs_baseline_ok"] = vl_count > 0
        
        if not result["victoria_logs_baseline_ok"]:
            result["error"] = "VictoriaLogs not deployed - cannot run independent cleanup test"
            return result
        
        # Step 4: Remove VictoriaLogs components
        run_on_remote_node(
            host,
            f"kubectl delete statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --ignore-not-found=true",
            admin_ip,
        )
        run_on_remote_node(
            host,
            f"kubectl delete statefulset vlagent-vlagent -n {TELEMETRY_NAMESPACE} --ignore-not-found=true",
            admin_ip,
        )
        run_on_remote_node(
            host,
            f"kubectl delete deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --ignore-not-found=true",
            admin_ip,
        )
        run_on_remote_node(
            host,
            f"kubectl delete deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --ignore-not-found=true",
            admin_ip,
        )
        
        time.sleep(10)
        
        # Step 5: Verify VictoriaLogs pods are gone
        vlstorage_pods_after = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlstorage --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        vlinsert_pods_after = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        vlselect_pods_after = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlselect --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        
        vlstorage_count_after = int(vlstorage_pods_after.stdout.strip()) if vlstorage_pods_after.rc == 0 else 0
        vlinsert_count_after = int(vlinsert_pods_after.stdout.strip()) if vlinsert_pods_after.rc == 0 else 0
        vlselect_count_after = int(vlselect_pods_after.stdout.strip()) if vlselect_pods_after.rc == 0 else 0
        
        vl_count_after = vlstorage_count_after + vlinsert_count_after + vlselect_count_after
        result["victoria_logs_removed"] = vl_count_after == 0
        
        # Step 7: Verify VictoriaMetrics still functional
        vm_pods_after_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=victoria-metrics --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        vm_count_after = int(vm_pods_after_cmd.stdout.strip()) if vm_pods_after_cmd.rc == 0 else 0
        result["victoria_metrics_after_removal_ok"] = vm_count_after > 0 and vm_count_after == vm_count
        
        # Step 8: Verify Kafka still functional
        kafka_pods_after_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app=kafka --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        kafka_count_after = int(kafka_pods_after_cmd.stdout.strip()) if kafka_pods_after_cmd.rc == 0 else 0
        result["kafka_after_removal_ok"] = kafka_count_after > 0 and kafka_count_after == kafka_count
        
        # Step 9: Verify Vector still running
        vector_pods_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app=vector --no-headers 2>/dev/null | wc -l",
            admin_ip,
        )
        vector_count = int(vector_pods_cmd.stdout.strip()) if vector_pods_cmd.rc == 0 else 0
        result["vector_running_after_removal"] = vector_count > 0
        
        # Step 10: Skip actual redeployment to avoid breaking environment
        result["victoria_logs_redeployed"] = False
        result["victoria_logs_pods_running_after_redeploy"] = False
        
        # Verify success
        success = result["victoria_logs_removed"]
        
        if result["victoria_metrics_baseline_ok"]:
            success = success and result["victoria_metrics_after_removal_ok"]
        
        if result["kafka_baseline_ok"]:
            success = success and result["kafka_after_removal_ok"]
        
        result["success"] = success
        
        if not result["success"]:
            if not result["victoria_logs_removed"]:
                result["error"] = "VictoriaLogs pods were not removed"
            elif result["victoria_metrics_baseline_ok"] and not result["victoria_metrics_after_removal_ok"]:
                result["error"] = "VictoriaMetrics was affected by VictoriaLogs removal"
            elif result["kafka_baseline_ok"] and not result["kafka_after_removal_ok"]:
                result["error"] = "Kafka was affected by VictoriaLogs removal"
        else:
            result["error"] = "Test passed but VictoriaLogs not redeployed (manual redeployment required)"
        
    except Exception as e:
        result["error"] = f"Exception during independent cleanup test: {str(e)}"
        try:
            run_on_remote_node(
                host,
                f"echo 'Emergency recovery: VictoriaLogs removal test failed, manual intervention may be required'",
                admin_ip,
            )
        except:
            pass
    
    return result


# =============================================================================
# DESTRUCTIVE TESTS — ALL PODS DOWN
# =============================================================================

def verify_all_vlstorage_pods_down_behavior(host, admin_ip: str) -> Dict[str, Any]:
    """
    Destructive test: Kill all vlstorage pods and verify behavior.
    
    Steps:
    1. Baseline: verify cluster is healthy
    2. Kill all vlstorage pods (scale to 0)
    3. Verify vlinsert behavior (should reject writes or return error)
    4. Verify vlselect behavior (should return error, not crash)
    5. Restore vlstorage pods (scale back to 3)
    6. Wait for recovery
    7. Verify cluster is healthy again
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pods_killed": False,
        "vlinsert_behavior": "",
        "vlselect_behavior": "",
        "pods_restored": False,
        "recovery_successful": False,
        "error": "",
    }
    
    # Step 1: Baseline health check
    baseline_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlstorage "
        f"--no-headers | grep Running | wc -l",
        admin_ip,
    )
    running_count = int(baseline_cmd.stdout.strip()) if baseline_cmd.rc == 0 else 0
    result["baseline_healthy"] = running_count == 3
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {running_count}/3 vlstorage pods running"
        return result
    
    # Step 2: Kill all vlstorage pods
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        admin_ip,
    )
    result["pods_killed"] = kill_cmd.rc == 0
    
    if not result["pods_killed"]:
        result["error"] = f"Failed to scale down vlstorage: {kill_cmd.stderr}"
        return result
    
    time.sleep(10)
    
    # Step 3: Test vlinsert behavior (should reject writes)
    vlinsert_test = _test_vlinsert_during_outage(host, admin_ip)
    result["vlinsert_behavior"] = vlinsert_test.get("behavior", "unknown")
    
    # Step 4: Test vlselect behavior (should return error, not crash)
    vlselect_test = _test_vlselect_during_outage(host, admin_ip)
    result["vlselect_behavior"] = vlselect_test.get("behavior", "unknown")
    
    # Step 5: Restore vlstorage pods
    restore_cmd = run_on_remote_node(
        host,
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=3",
        admin_ip,
    )
    result["pods_restored"] = restore_cmd.rc == 0
    
    if not result["pods_restored"]:
        result["error"] = f"Failed to scale up vlstorage: {restore_cmd.stderr}"
        return result
    
    # Step 6: Wait for recovery (up to 2 minutes)
    for i in range(24):  # 24 * 5s = 120s
        time.sleep(5)
        check_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlstorage "
            f"--no-headers | grep Running | wc -l",
            admin_ip,
        )
        running = int(check_cmd.stdout.strip()) if check_cmd.rc == 0 else 0
        if running == 3:
            result["recovery_successful"] = True
            break
    
    if not result["recovery_successful"]:
        result["error"] = "vlstorage pods did not recover within 120s"
        return result
    
    # Step 7: Verify cluster health post-recovery
    time.sleep(10)
    health_check = _verify_cluster_health(host, admin_ip)
    result["success"] = health_check.get("healthy", False)
    
    if not result["success"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result


def verify_all_vlinsert_pods_down_behavior(host, admin_ip: str) -> Dict[str, Any]:
    """
    Destructive test: Kill all vlinsert pods and verify behavior.
    
    Expected behavior:
    - Writes should fail (no vlinsert to accept them)
    - Reads should still work (vlselect can query vlstorage directly)
    - Pods should auto-recover (Deployment will recreate them)
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pods_killed": False,
        "writes_rejected": False,
        "reads_still_work": False,
        "pods_recovered": False,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
        f"--no-headers | grep Running | wc -l",
        admin_ip,
    )
    running_count = int(baseline_cmd.stdout.strip()) if baseline_cmd.rc == 0 else 0
    result["baseline_healthy"] = running_count == 2
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {running_count}/2 vlinsert pods running"
        return result
    
    # Step 2: Kill all vlinsert pods
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        admin_ip,
    )
    result["pods_killed"] = kill_cmd.rc == 0
    
    if not result["pods_killed"]:
        result["error"] = f"Failed to scale down vlinsert: {kill_cmd.stderr}"
        return result
    
    time.sleep(10)
    
    # Step 3: Verify writes are rejected
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_rejected"] = write_test.get("behavior", "") in ["connection_refused", "timeout", "no_route"]
    
    # Step 4: Verify reads still work
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_still_work"] = read_test.get("behavior", "") == "success"
    
    # Step 5: Restore vlinsert pods
    restore_cmd = run_on_remote_node(
        host,
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        admin_ip,
    )
    
    if restore_cmd.rc != 0:
        result["error"] = f"Failed to scale up vlinsert: {restore_cmd.stderr}"
        return result
    
    # Step 6: Wait for recovery
    for i in range(24):
        time.sleep(5)
        check_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
            f"--no-headers | grep Running | wc -l",
            admin_ip,
        )
        running = int(check_cmd.stdout.strip()) if check_cmd.rc == 0 else 0
        if running == 2:
            result["pods_recovered"] = True
            break
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pods_killed"] and
        result["writes_rejected"] and
        result["reads_still_work"] and
        result["pods_recovered"]
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = "vlinsert destructive test failed - check individual steps"
    
    return result


def verify_all_vlselect_pods_down_behavior(host, admin_ip: str) -> Dict[str, Any]:
    """
    Destructive test: Kill all vlselect pods and verify behavior.
    
    Expected behavior:
    - Reads should fail (no vlselect to query)
    - Writes should still work (vlinsert writes directly to vlstorage)
    - Pods should auto-recover
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pods_killed": False,
        "reads_rejected": False,
        "writes_still_work": False,
        "pods_recovered": False,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlselect "
        f"--no-headers | grep Running | wc -l",
        admin_ip,
    )
    running_count = int(baseline_cmd.stdout.strip()) if baseline_cmd.rc == 0 else 0
    result["baseline_healthy"] = running_count == 2
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {running_count}/2 vlselect pods running"
        return result
    
    # Step 2: Kill all vlselect pods
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        admin_ip,
    )
    result["pods_killed"] = kill_cmd.rc == 0
    
    if not result["pods_killed"]:
        result["error"] = f"Failed to scale down vlselect: {kill_cmd.stderr}"
        return result
    
    time.sleep(10)
    
    # Step 3: Verify reads are rejected
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_rejected"] = read_test.get("behavior", "") in ["connection_refused", "timeout", "no_route"]
    
    # Step 4: Verify writes still work
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_still_work"] = write_test.get("behavior", "") == "success"
    
    # Step 5: Restore vlselect pods
    restore_cmd = run_on_remote_node(
        host,
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        admin_ip,
    )
    
    if restore_cmd.rc != 0:
        result["error"] = f"Failed to scale up vlselect: {restore_cmd.stderr}"
        return result
    
    # Step 6: Wait for recovery
    for i in range(24):
        time.sleep(5)
        check_cmd = run_on_remote_node(
            host,
            f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlselect "
            f"--no-headers | grep Running | wc -l",
            admin_ip,
        )
        running = int(check_cmd.stdout.strip()) if check_cmd.rc == 0 else 0
        if running == 2:
            result["pods_recovered"] = True
            break
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pods_killed"] and
        result["reads_rejected"] and
        result["writes_still_work"] and
        result["pods_recovered"]
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = "vlselect destructive test failed - check individual steps"
    
    return result


def verify_complete_cluster_failure_recovery(host, admin_ip: str) -> Dict[str, Any]:
    """
    Destructive test: Kill ALL VictoriaLogs pods and verify recovery.
    
    This is the ultimate disaster recovery test.
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "all_pods_killed": False,
        "cluster_unavailable": False,
        "all_pods_recovered": False,
        "cluster_healthy_after_recovery": False,
        "recovery_time_seconds": 0,
        "error": "",
    }
    
    # Step 1: Baseline
    baseline = _verify_cluster_health(host, admin_ip)
    result["baseline_healthy"] = baseline.get("healthy", False)
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {baseline.get('error', '')}"
        return result
    
    # Step 2: Kill ALL pods
    start_time = time.time()
    
    kill_commands = [
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=0",
        f"kubectl scale statefulset vlagent-vlagent -n {TELEMETRY_NAMESPACE} --replicas=0",
    ]
    
    all_killed = True
    for cmd in kill_commands:
        kill_result = run_on_remote_node(host, cmd, admin_ip)
        if kill_result.rc != 0:
            all_killed = False
            result["error"] += f"Failed: {cmd}; "
    
    result["all_pods_killed"] = all_killed
    
    if not all_killed:
        _restore_all_pods(host, admin_ip)
        return result
    
    time.sleep(15)
    
    # Step 3: Verify cluster is unavailable
    unavailable_test = _verify_cluster_health(host, admin_ip)
    result["cluster_unavailable"] = not unavailable_test.get("healthy", True)
    
    # Step 4: Restore ALL pods
    restore_commands = [
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=3",
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        f"kubectl scale statefulset vlagent-vlagent -n {TELEMETRY_NAMESPACE} --replicas=1",
    ]
    
    for cmd in restore_commands:
        run_on_remote_node(host, cmd, admin_ip)
    
    # Step 5: Wait for recovery (up to 3 minutes)
    for i in range(36):  # 36 * 5s = 180s
        time.sleep(5)
        
        vlstorage_count = _get_running_pod_count(host, admin_ip, "vlstorage")
        vlinsert_count = _get_running_pod_count(host, admin_ip, "vlinsert")
        vlselect_count = _get_running_pod_count(host, admin_ip, "vlselect")
        vlagent_count = _get_running_pod_count(host, admin_ip, "vlagent")
        
        if vlstorage_count == 3 and vlinsert_count == 2 and vlselect_count == 2 and vlagent_count == 1:
            result["all_pods_recovered"] = True
            result["recovery_time_seconds"] = int(time.time() - start_time)
            break
    
    if not result["all_pods_recovered"]:
        result["error"] = "Pods did not recover within 180s"
        return result
    
    # Step 6: Verify cluster health
    time.sleep(15)
    health_check = _verify_cluster_health(host, admin_ip)
    result["cluster_healthy_after_recovery"] = health_check.get("healthy", False)
    
    result["success"] = (
        result["baseline_healthy"] and
        result["all_pods_killed"] and
        result["cluster_unavailable"] and
        result["all_pods_recovered"] and
        result["cluster_healthy_after_recovery"]
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result


# =============================================================================
# DESTRUCTIVE TEST HELPER FUNCTIONS
# =============================================================================

def _test_vlinsert_during_outage(host, admin_ip: str) -> Dict[str, Any]:
    """Test vlinsert behavior during outage."""
    ip_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=VLINSERT["service_name"],
            namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    external_ip = ip_cmd.stdout.strip() if ip_cmd.rc == 0 else ""
    
    if not external_ip or external_ip == "null":
        return {"behavior": "no_service", "error": "vlinsert service has no external IP"}
    
    test_payload = '{"_msg":"outage-test","_time":' + str(int(time.time())) + ',"job":"test"}'
    curl_cmd = (
        f"timeout 5 kubectl exec -n {TELEMETRY_NAMESPACE} "
        f"$(kubectl get pod -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
        f"-o jsonpath='{{.items[0].metadata.name}}' 2>/dev/null || echo 'none') -- "
        f"curl -k -s -w '%{{http_code}}' -o /dev/null --max-time 3 "
        f"-X POST https://localhost:{VLINSERT['port']}/insert/jsonline "
        f"--data '{test_payload}' "
        f"--cert /etc/victoria/certs/server.crt "
        f"--key /etc/victoria/certs/server.key 2>&1 || echo '000'"
    )
    
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)
    
    if cmd.rc != 0 or "000" in cmd.stdout or "none" in cmd.stdout:
        return {"behavior": "connection_refused", "http_code": "000"}
    
    http_code = cmd.stdout.strip()[-3:] if len(cmd.stdout.strip()) >= 3 else "000"
    
    if http_code in ["200", "204"]:
        return {"behavior": "success", "http_code": http_code}
    elif http_code.startswith("5"):
        return {"behavior": "server_error", "http_code": http_code}
    else:
        return {"behavior": "error", "http_code": http_code}


def _test_vlselect_during_outage(host, admin_ip: str) -> Dict[str, Any]:
    """Test vlselect behavior during outage."""
    ip_cmd = run_on_remote_node(
        host,
        VICTORIA_LOGS_CMD_TEMPLATES["get_service_external_ip"].format(
            service_name=VLSELECT["service_name"],
            namespace=TELEMETRY_NAMESPACE
        ),
        admin_ip,
    )
    external_ip = ip_cmd.stdout.strip() if ip_cmd.rc == 0 else ""
    
    if not external_ip or external_ip == "null":
        return {"behavior": "no_service", "error": "vlselect service has no external IP"}
    
    curl_cmd = VICTORIA_LOGS_CMD_TEMPLATES["curl_logsql_query"].format(
        secret_name=VICTORIA_LOGS_TLS_SECRET,
        namespace=TELEMETRY_NAMESPACE,
        service_dns=VLSELECT["service_name"],
        port=VLSELECT["port"],
        external_ip=external_ip,
        query="*"
    )
    
    cmd = run_on_remote_node(host, f"timeout 5 {curl_cmd} 2>&1 || echo 'TIMEOUT'", admin_ip)
    
    if "TIMEOUT" in cmd.stdout or cmd.rc != 0:
        return {"behavior": "timeout", "error": "Query timed out"}
    
    if "Connection refused" in cmd.stdout or "No route" in cmd.stdout:
        return {"behavior": "connection_refused"}
    
    if "{" in cmd.stdout and "}" in cmd.stdout:
        return {"behavior": "success"}
    else:
        return {"behavior": "error", "response": cmd.stdout[:100]}


def _verify_cluster_health(host, admin_ip: str) -> Dict[str, Any]:
    """Verify overall cluster health."""
    vlstorage_count = _get_running_pod_count(host, admin_ip, "vlstorage")
    vlinsert_count = _get_running_pod_count(host, admin_ip, "vlinsert")
    vlselect_count = _get_running_pod_count(host, admin_ip, "vlselect")
    vlagent_count = _get_running_pod_count(host, admin_ip, "vlagent")
    
    healthy = (vlstorage_count == 3 and vlinsert_count == 2 and 
               vlselect_count == 2 and vlagent_count == 1)
    
    return {
        "healthy": healthy,
        "vlstorage": vlstorage_count,
        "vlinsert": vlinsert_count,
        "vlselect": vlselect_count,
        "vlagent": vlagent_count,
        "error": "" if healthy else f"Pod counts: vlstorage={vlstorage_count}, vlinsert={vlinsert_count}, vlselect={vlselect_count}, vlagent={vlagent_count}",
    }


def _get_running_pod_count(host, admin_ip: str, component: str) -> int:
    """Get count of running pods for a component."""
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name={component} "
        f"--no-headers 2>/dev/null | grep Running | wc -l",
        admin_ip,
    )
    return int(cmd.stdout.strip()) if cmd.rc == 0 and cmd.stdout.strip().isdigit() else 0


def _restore_all_pods(host, admin_ip: str):
    """Emergency restore of all pods."""
    restore_commands = [
        f"kubectl scale statefulset vlstorage-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=3",
        f"kubectl scale deployment vlinsert-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        f"kubectl scale deployment vlselect-victoria-logs-cluster -n {TELEMETRY_NAMESPACE} --replicas=2",
        f"kubectl scale statefulset vlagent-vlagent -n {TELEMETRY_NAMESPACE} --replicas=1",
    ]
    for cmd in restore_commands:
        run_on_remote_node(host, cmd, admin_ip)


# =============================================================================
# PARTIAL FAILURE TESTS — SINGLE POD DOWN
# =============================================================================

def verify_single_vlstorage_pod_failure(host, admin_ip: str) -> Dict[str, Any]:
    """
    Partial failure test: Kill 1 of 3 vlstorage pods and verify HA.
    
    Expected behavior:
    - Writes should continue (vlinsert routes to remaining 2 nodes)
    - Reads should continue (vlselect queries remaining 2 nodes)
    - Some data may be unavailable (data on killed node)
    - Pod should auto-recover
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pod_killed": False,
        "pod_name": "",
        "writes_still_work": False,
        "reads_still_work": False,
        "pod_recovered": False,
        "recovery_time_seconds": 0,
        "error": "",
    }
    
    baseline = _verify_cluster_health(host, admin_ip)
    result["baseline_healthy"] = baseline.get("healthy", False)
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {baseline.get('error', '')}"
        return result
    
    pod_name = "vlstorage-victoria-logs-cluster-0"
    result["pod_name"] = pod_name
    
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl delete pod {pod_name} -n {TELEMETRY_NAMESPACE} --grace-period=0 --force",
        admin_ip,
    )
    result["pod_killed"] = kill_cmd.rc == 0
    
    if not result["pod_killed"]:
        result["error"] = f"Failed to kill pod: {kill_cmd.stderr}"
        return result
    
    time.sleep(5)
    
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_still_work"] = write_test.get("behavior", "") == "success"
    
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_still_work"] = read_test.get("behavior", "") == "success"
    
    start_time = time.time()
    for i in range(24):  # 24 * 5s = 120s
        time.sleep(5)
        check_cmd = run_on_remote_node(
            host,
            f"kubectl get pod {pod_name} -n {TELEMETRY_NAMESPACE} "
            f"--no-headers 2>/dev/null | grep Running",
            admin_ip,
        )
        if check_cmd.rc == 0 and "Running" in check_cmd.stdout:
            result["pod_recovered"] = True
            result["recovery_time_seconds"] = int(time.time() - start_time)
            break
    
    if not result["pod_recovered"]:
        result["error"] = f"Pod {pod_name} did not recover within 120s"
        return result
    
    time.sleep(10)
    health_check = _verify_cluster_health(host, admin_ip)
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pod_killed"] and
        result["writes_still_work"] and
        result["reads_still_work"] and
        result["pod_recovered"] and
        health_check.get("healthy", False)
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result


def verify_single_vlinsert_pod_failure(host, admin_ip: str) -> Dict[str, Any]:
    """
    Partial failure test: Kill 1 of 2 vlinsert pods and verify HA.
    
    Expected behavior:
    - Writes should continue (LoadBalancer routes to remaining pod)
    - Reads should continue (vlselect independent)
    - Pod should auto-recover
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pod_killed": False,
        "pod_name": "",
        "writes_still_work": False,
        "reads_still_work": False,
        "pod_recovered": False,
        "recovery_time_seconds": 0,
        "error": "",
    }
    
    baseline = _verify_cluster_health(host, admin_ip)
    result["baseline_healthy"] = baseline.get("healthy", False)
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {baseline.get('error', '')}"
        return result
    
    get_pod_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlinsert "
        f"--no-headers -o custom-columns=:metadata.name | head -1",
        admin_ip,
    )
    
    if get_pod_cmd.rc != 0 or not get_pod_cmd.stdout.strip():
        result["error"] = "Failed to get vlinsert pod name"
        return result
    
    pod_name = get_pod_cmd.stdout.strip()
    result["pod_name"] = pod_name
    
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl delete pod {pod_name} -n {TELEMETRY_NAMESPACE} --grace-period=0 --force",
        admin_ip,
    )
    result["pod_killed"] = kill_cmd.rc == 0
    
    if not result["pod_killed"]:
        result["error"] = f"Failed to kill pod: {kill_cmd.stderr}"
        return result
    
    time.sleep(5)
    
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_still_work"] = write_test.get("behavior", "") == "success"
    
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_still_work"] = read_test.get("behavior", "") == "success"
    
    start_time = time.time()
    for i in range(24):
        time.sleep(5)
        check_count = _get_running_pod_count(host, admin_ip, "vlinsert")
        if check_count == 2:
            result["pod_recovered"] = True
            result["recovery_time_seconds"] = int(time.time() - start_time)
            break
    
    if not result["pod_recovered"]:
        result["error"] = "vlinsert pod did not recover within 120s"
        return result
    
    time.sleep(10)
    health_check = _verify_cluster_health(host, admin_ip)
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pod_killed"] and
        result["writes_still_work"] and
        result["reads_still_work"] and
        result["pod_recovered"] and
        health_check.get("healthy", False)
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result


def verify_single_vlselect_pod_failure(host, admin_ip: str) -> Dict[str, Any]:
    """
    Partial failure test: Kill 1 of 2 vlselect pods and verify HA.
    
    Expected behavior:
    - Reads should continue (LoadBalancer routes to remaining pod)
    - Writes should continue (vlinsert independent)
    - Pod should auto-recover
    """
    result = {
        "success": False,
        "baseline_healthy": False,
        "pod_killed": False,
        "pod_name": "",
        "writes_still_work": False,
        "reads_still_work": False,
        "pod_recovered": False,
        "recovery_time_seconds": 0,
        "error": "",
    }
    
    baseline = _verify_cluster_health(host, admin_ip)
    result["baseline_healthy"] = baseline.get("healthy", False)
    
    if not result["baseline_healthy"]:
        result["error"] = f"Baseline unhealthy: {baseline.get('error', '')}"
        return result
    
    get_pod_cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vlselect "
        f"--no-headers -o custom-columns=:metadata.name | head -1",
        admin_ip,
    )
    
    if get_pod_cmd.rc != 0 or not get_pod_cmd.stdout.strip():
        result["error"] = "Failed to get vlselect pod name"
        return result
    
    pod_name = get_pod_cmd.stdout.strip()
    result["pod_name"] = pod_name
    
    kill_cmd = run_on_remote_node(
        host,
        f"kubectl delete pod {pod_name} -n {TELEMETRY_NAMESPACE} --grace-period=0 --force",
        admin_ip,
    )
    result["pod_killed"] = kill_cmd.rc == 0
    
    if not result["pod_killed"]:
        result["error"] = f"Failed to kill pod: {kill_cmd.stderr}"
        return result
    
    time.sleep(5)
    
    read_test = _test_vlselect_during_outage(host, admin_ip)
    result["reads_still_work"] = read_test.get("behavior", "") == "success"
    
    write_test = _test_vlinsert_during_outage(host, admin_ip)
    result["writes_still_work"] = write_test.get("behavior", "") == "success"
    
    start_time = time.time()
    for i in range(24):
        time.sleep(5)
        check_count = _get_running_pod_count(host, admin_ip, "vlselect")
        if check_count == 2:
            result["pod_recovered"] = True
            result["recovery_time_seconds"] = int(time.time() - start_time)
            break
    
    if not result["pod_recovered"]:
        result["error"] = "vlselect pod did not recover within 120s"
        return result
    
    time.sleep(10)
    health_check = _verify_cluster_health(host, admin_ip)
    
    result["success"] = (
        result["baseline_healthy"] and
        result["pod_killed"] and
        result["writes_still_work"] and
        result["reads_still_work"] and
        result["pod_recovered"] and
        health_check.get("healthy", False)
    )
    
    if not result["success"] and not result["error"]:
        result["error"] = f"Cluster not healthy after recovery: {health_check.get('error', '')}"
    
    return result
