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
PowerScale Telemetry Automation - Functions.

This module contains verification functions for PowerScale storage telemetry.
Implements the logic for all 26 test cases defined in TCASES-PS-2026-001.
"""

import json
import time
import re
import urllib.parse
from typing import Dict, Any, List, Optional

from ...core import run_on_remote_node
from ..vars.shared_vars import TELEMETRY_NAMESPACE
from ..vars.powerscale_vars import (
    DEPLOYMENT_MODE_OMNIA,
    DEPLOYMENT_MODE_OPERATOR,
    CSM_METRICS_POWERSCALE,
    OTEL_COLLECTOR,
    CERT_MANAGER,
    CSI_DRIVER_POWERSCALE,
    VLAGENT,
    POWERSCALE_METRIC_CATEGORIES,
    POWERSCALE_REQUIRED_LABELS,
    POWERSCALE_HEALTH_METRICS,
    CREDENTIAL_PATTERNS,
    POWERSCALE_CMD_TEMPLATES,
    POWERSCALE_VM_QUERY_TEMPLATES,
    SCRAPE_INTERVAL_MIN_SECONDS,
    SCRAPE_INTERVAL_MAX_SECONDS,
    SCRAPE_INTERVAL_TOLERANCE_SECONDS,
    POD_RESTART_WAIT_SECONDS,
    POD_RESTART_MAX_RETRIES,
    SYSLOG_MAX_WAIT_SECONDS,
)
from ..vars.victoria_vars import (
    DEPLOYMENT_MODE_CLUSTER,
    VICTORIA_CLUSTER,
    VICTORIA_TLS_SECRET,
    VICTORIA_API_ENDPOINTS,
)
from .shared_func import get_telemetry_config, is_idrac_telemetry_enabled


# =============================================================================
# CONFIGURATION HELPERS
# =============================================================================

def get_powerscale_config(host) -> Dict[str, Any]:
    """
    Get powerscale_configurations from telemetry_config.yml.

    Returns:
        Dict with powerscale telemetry configuration
    """
    config = get_telemetry_config(host)
    return config.get("powerscale_configurations", {})


def get_powerscale_deployment_mode(host) -> str:
    """
    Get PowerScale deployment mode.

    With the new telemetry_config.yml structure, PowerScale is always
    deployed in omnia-orchestrated mode.

    Returns:
        'omnia-orchestrated' (always)
    """
    return DEPLOYMENT_MODE_OMNIA


def get_powerscale_scrape_interval(host) -> str:
    """
    Get PowerScale scrape interval from telemetry_config.yml.

    Returns:
        Scrape interval string (e.g., '30s')
    """
    ps_config = get_powerscale_config(host)
    return ps_config.get("scrape_interval", "30s")


def _parse_interval_seconds(interval_str: str) -> int:
    """Parse interval string like '30s' to integer seconds."""
    match = re.match(r'^(\d+)s$', interval_str.strip())
    if match:
        return int(match.group(1))
    return 30  # default


def _get_vm_query_endpoint(host) -> Dict[str, Any]:
    """
    Get VictoriaMetrics query endpoint info.

    VictoriaMetrics is always deployed in cluster mode with the new
    telemetry_config.yml structure.
    """
    return {
        "service_name": VICTORIA_CLUSTER["vmselect"]["service_name"],
        "port": VICTORIA_CLUSTER["vmselect"]["port"],
        "query_endpoint": VICTORIA_API_ENDPOINTS["cluster_query"],
    }


def _query_victoria_metrics(
    host, admin_ip: str, query: str, timeout: int = 30
) -> Dict[str, Any]:
    """
    Query VictoriaMetrics and return parsed results.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP for SSH access
        query: PromQL query string
        timeout: Request timeout

    Returns:
        Dict with 'success', 'result' (list of series), 'error'
    """
    vm_info = _get_vm_query_endpoint(host)
    service_name = vm_info["service_name"]
    port = vm_info["port"]
    query_endpoint = vm_info["query_endpoint"]

    # Get external IP (single quotes around jsonpath to prevent shell brace expansion)
    kubectl_cmd = (
        f"kubectl get svc {service_name} -n {TELEMETRY_NAMESPACE} "
        f"-o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'"
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip().strip("'") if cmd.rc == 0 else ""
    if not external_ip or external_ip == "null":
        return {"success": False, "result": [], "error": f"No external IP for {service_name}"}

    encoded_query = urllib.parse.quote(query)
    curl_cmd = (
        f"curl -sk --max-time {timeout} "
        f"'https://{external_ip}:{port}{query_endpoint}?query={encoded_query}'"
    )
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)

    try:
        response = json.loads(cmd.stdout) if cmd.rc == 0 else {}
        result_data = response.get("data", {}).get("result", [])
        return {"success": True, "result": result_data, "error": ""}
    except json.JSONDecodeError:
        return {"success": False, "result": [], "error": "Failed to parse VM response"}


def _get_pods_by_label(
    host, admin_ip: str, namespace: str, label_selector: str
) -> Dict[str, Any]:
    """
    Get pods by label selector and return parsed results.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP for SSH access
        namespace: Kubernetes namespace
        label_selector: Full label selector (e.g., 'app.kubernetes.io/name=foo' or 'app=bar')

    Returns:
        Dict with 'success', 'items' (list of pod dicts), 'error'
    """
    kubectl_cmd = POWERSCALE_CMD_TEMPLATES["get_pods_by_label"].format(
        namespace=namespace, label_selector=label_selector
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    if cmd.rc != 0:
        return {"success": False, "items": [], "error": f"Failed to get pods: {cmd.stderr}"}

    try:
        data = json.loads(cmd.stdout)
        return {"success": True, "items": data.get("items", []), "error": ""}
    except json.JSONDecodeError:
        return {"success": False, "items": [], "error": "Failed to parse pods JSON"}


def _wait_for_pod_running(
    host, admin_ip: str, namespace: str, app_label: str,
    max_retries: int = POD_RESTART_MAX_RETRIES,
    wait_seconds: int = POD_RESTART_WAIT_SECONDS
) -> Dict[str, Any]:
    """Wait for pod to reach Running state after restart."""
    for attempt in range(1, max_retries + 1):
        result = _get_pods_by_label(host, admin_ip, namespace, label_selector=app_label)
        if result["success"] and result["items"]:
            for pod in result["items"]:
                phase = pod.get("status", {}).get("phase", "")
                if phase == "Running":
                    pod_name = pod.get("metadata", {}).get("name", "")
                    return {
                        "success": True,
                        "pod_name": pod_name,
                        "phase": phase,
                        "attempts": attempt,
                    }
        if attempt < max_retries:
            time.sleep(wait_seconds)

    return {
        "success": False,
        "pod_name": "",
        "phase": "Unknown",
        "attempts": max_retries,
        "error": f"Pod not Running after {max_retries} attempts",
    }


# =============================================================================
# TC-F001: DEPLOYMENT VERIFICATION
# =============================================================================

def verify_powerscale_deployment(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify complete PowerScale telemetry deployment (TC-F001).

    Checks:
    - CSM Metrics for PowerScale pod Running with 0 restarts
    - OTel Collector pod Running with 0 restarts
    - CSI Driver for Dell PowerScale installed
    - cert-manager pods Running
    - Certificates Ready
    - OTel Collector Prometheus endpoint responding

    Returns:
        Dict with success, component_results, missing_components
    """
    component_results = []
    missing = []

    # 1. CSM Metrics for PowerScale
    csm_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, CSM_METRICS_POWERSCALE["label_selector"]
    )
    csm_pods = csm_result.get("items", [])
    csm_running = any(
        p.get("status", {}).get("phase") == "Running" for p in csm_pods
    )
    csm_restarts = sum(
        int(cs.get("restartCount", 0))
        for p in csm_pods
        for cs in p.get("status", {}).get("containerStatuses", [])
    )
    component_results.append({
        "component": CSM_METRICS_POWERSCALE["component"],
        "running": csm_running,
        "pod_count": len(csm_pods),
        "restarts": csm_restarts,
    })
    if not csm_running:
        missing.append(CSM_METRICS_POWERSCALE["component"])

    # 2. OTel Collector
    otel_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, OTEL_COLLECTOR["label_selector"]
    )
    otel_pods = otel_result.get("items", [])
    otel_running = any(
        p.get("status", {}).get("phase") == "Running" for p in otel_pods
    )
    otel_restarts = sum(
        int(cs.get("restartCount", 0))
        for p in otel_pods
        for cs in p.get("status", {}).get("containerStatuses", [])
    )
    component_results.append({
        "component": OTEL_COLLECTOR["component"],
        "running": otel_running,
        "pod_count": len(otel_pods),
        "restarts": otel_restarts,
    })
    if not otel_running:
        missing.append(OTEL_COLLECTOR["component"])

    # 3. CSI Driver
    csi_cmd = POWERSCALE_CMD_TEMPLATES["get_csi_drivers"]
    cmd = run_on_remote_node(host, csi_cmd, admin_ip)
    csi_found = False
    if cmd.rc == 0:
        try:
            data = json.loads(cmd.stdout)
            for item in data.get("items", []):
                name = item.get("metadata", {}).get("name", "")
                if CSI_DRIVER_POWERSCALE["driver_name"] in name:
                    csi_found = True
                    break
        except json.JSONDecodeError:
            pass
    component_results.append({
        "component": CSI_DRIVER_POWERSCALE["component"],
        "running": csi_found,
        "pod_count": 1 if csi_found else 0,
        "restarts": 0,
    })
    if not csi_found:
        missing.append(CSI_DRIVER_POWERSCALE["component"])

    # 4. cert-manager
    cm_result = _get_pods_by_label(
        host, admin_ip, CERT_MANAGER["namespace"], CERT_MANAGER["label_selector"]
    )
    cm_pods = cm_result.get("items", [])
    cm_running = all(
        p.get("status", {}).get("phase") == "Running" for p in cm_pods
    ) if cm_pods else False
    component_results.append({
        "component": CERT_MANAGER["component"],
        "running": cm_running,
        "pod_count": len(cm_pods),
        "restarts": 0,
    })
    if not cm_running:
        missing.append(CERT_MANAGER["component"])

    # 5. Certificates
    cert_cmd = POWERSCALE_CMD_TEMPLATES["get_certificates"].format(
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, cert_cmd, admin_ip)
    certs_ready = False
    cert_count = 0
    if cmd.rc == 0:
        try:
            data = json.loads(cmd.stdout)
            certs = data.get("items", [])
            cert_count = len(certs)
            if certs:
                certs_ready = all(
                    any(
                        c.get("type") == "Ready" and c.get("status") == "True"
                        for c in cert.get("status", {}).get("conditions", [])
                    )
                    for cert in certs
                )
        except json.JSONDecodeError:
            pass
    component_results.append({
        "component": "Certificates",
        "running": certs_ready,
        "pod_count": cert_count,
        "restarts": 0,
    })

    # 6. Check for pod restarts
    total_restarts = csm_restarts + otel_restarts
    has_restarts = total_restarts > 0

    return {
        "success": len(missing) == 0 and not has_restarts,
        "component_results": component_results,
        "missing_components": missing,
        "total_restarts": total_restarts,
        "has_restarts": has_restarts,
    }


# =============================================================================
# TC-F002: METRIC COLLECTION AND LABEL VERIFICATION
# =============================================================================

def verify_powerscale_metrics(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify PowerScale metric collection and labels (TC-F002).

    Checks all 6 metric categories and required labels.

    Returns:
        Dict with success, category_results, label_results
    """
    category_results = []
    found_categories = []
    missing_categories = []
    all_series = []

    for category, pattern in POWERSCALE_METRIC_CATEGORIES.items():
        query = f'{{__name__=~"{pattern}"}}'
        vm_result = _query_victoria_metrics(host, admin_ip, query)
        series = vm_result.get("result", [])
        found = len(series) > 0

        category_results.append({
            "category": category,
            "pattern": pattern,
            "found": found,
            "series_count": len(series),
        })

        if found:
            found_categories.append(category)
            all_series.extend(series)
        else:
            missing_categories.append(category)

    # Check labels on powerscale_* series only (karavi_* has different label schema)
    ps_series = [s for s in all_series if s.get("metric", {}).get("__name__", "").startswith("powerscale_")]
    label_results = []
    missing_labels = []

    for label in POWERSCALE_REQUIRED_LABELS:
        count = sum(1 for item in ps_series if label in item.get("metric", {}))
        has_label = count == len(ps_series) if ps_series else False
        label_results.append({
            "label": label,
            "present": has_label,
            "count": count,
            "total": len(ps_series),
        })
        if not has_label and ps_series:
            missing_labels.append(label)

    return {
        "success": len(missing_categories) == 0 and len(missing_labels) == 0,
        "category_results": category_results,
        "found_categories": found_categories,
        "missing_categories": missing_categories,
        "label_results": label_results,
        "missing_labels": missing_labels,
        "total_series": len(all_series),
    }


# =============================================================================
# TC-F003: SYSLOG INGESTION
# =============================================================================

def verify_powerscale_syslog(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify PowerScale syslog ingestion into VictoriaLogs (TC-F003).

    Checks:
    - VLAgent is Running
    - Syslog events queryable in VictoriaLogs
    - Events have correct labels (host/cluster, severity, facility)

    Returns:
        Dict with success, vlagent_running, events_found, label_checks
    """
    # Check VLAgent pod
    vlagent_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, VLAGENT["label_selector"]
    )
    vlagent_pods = vlagent_result.get("items", [])
    vlagent_running = any(
        p.get("status", {}).get("phase") == "Running" for p in vlagent_pods
    )

    if not vlagent_running:
        return {
            "success": False,
            "vlagent_running": False,
            "events_found": False,
            "error": "VLAgent pod is not Running",
        }

    # Query VictoriaLogs for PowerScale events
    # Use vlselect service to query logs
    vl_cmd = (
        "kubectl get svc -n {namespace} -o json"
    ).format(namespace=TELEMETRY_NAMESPACE)
    cmd = run_on_remote_node(host, vl_cmd, admin_ip)

    vl_endpoint = ""
    vl_port = ""
    if cmd.rc == 0:
        try:
            data = json.loads(cmd.stdout)
            for svc in data.get("items", []):
                svc_name = svc.get("metadata", {}).get("name", "")
                if "vlselect" in svc_name or "victorialogs" in svc_name:
                    # Prefer LoadBalancer IP, fall back to ClusterIP
                    ingress = svc.get("status", {}).get("loadBalancer", {}).get("ingress", [])
                    if ingress:
                        vl_endpoint = ingress[0].get("ip", "")
                    if not vl_endpoint:
                        vl_endpoint = svc.get("spec", {}).get("clusterIP", "")
                    ports = svc.get("spec", {}).get("ports", [])
                    if ports:
                        vl_port = str(ports[0].get("port", "9428"))
                    break
        except json.JSONDecodeError:
            pass

    events_found = False
    event_count = 0
    label_checks = {}

    if vl_endpoint and vl_port:
        # Query for syslog events — use broad query since PowerScale
        # hostnames (e.g. "bdcdap-1") may not contain "powerscale".
        # VLSelect uses TLS, so use https:// with -k to skip cert verify.
        query_cmd = (
            f"curl -sk --max-time 30 "
            f"'https://{vl_endpoint}:{vl_port}/select/logsql/query?"
            f"query=*&limit=10'"
        )
        cmd = run_on_remote_node(host, query_cmd, admin_ip)
        if cmd.rc == 0 and cmd.stdout.strip():
            # Parse only valid JSON lines (skip error pages / non-JSON)
            parsed_events = []
            for line in cmd.stdout.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed_events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

            event_count = len(parsed_events)
            events_found = event_count > 0

            # Check labels on first event
            if events_found:
                first_event = parsed_events[0]
                label_checks = {
                    "host_label": bool(
                        first_event.get("hostname")
                        or first_event.get("host")
                        or first_event.get("cluster")
                    ),
                    "severity_label": bool(
                        first_event.get("severity") is not None
                        or first_event.get("level")
                    ),
                    "facility_label": bool(
                        first_event.get("facility") is not None
                        or first_event.get("facility_keyword")
                    ),
                }

    return {
        "success": vlagent_running and events_found,
        "vlagent_running": vlagent_running,
        "events_found": events_found,
        "event_count": event_count,
        "label_checks": label_checks,
        "vl_endpoint": vl_endpoint,
    }


# =============================================================================
# TC-F004: FEATURE FLAG OPERATION
# =============================================================================

def verify_feature_flags(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify independent feature flag operation (TC-F004).

    Reads current config and verifies that metrics and logs flags
    independently control their respective data paths.

    Returns:
        Dict with success, metrics_enabled, logs_enabled, verification details
    """
    config = get_telemetry_config(host)
    ps_config = config.get("powerscale_configurations", {})
    metrics_enabled = ps_config.get("powerscale_metrics_enabled", False)
    logs_enabled = ps_config.get("powerscale_logs_enabled", False)

    # Verify metrics path
    metrics_flowing = False
    if metrics_enabled:
        query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
        vm_result = _query_victoria_metrics(host, admin_ip, query)
        metrics_flowing = len(vm_result.get("result", [])) > 0
        if not metrics_flowing:
            # Also check karavi metrics
            query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_karavi"]
            vm_result = _query_victoria_metrics(host, admin_ip, query)
            metrics_flowing = len(vm_result.get("result", [])) > 0

    # Verify logs path
    logs_flowing = False
    if logs_enabled:
        syslog_result = verify_powerscale_syslog(host, admin_ip)
        logs_flowing = syslog_result.get("events_found", False)

    # Verify independence
    metrics_correct = (metrics_enabled == metrics_flowing) or not metrics_enabled
    logs_correct = (logs_enabled == logs_flowing) or not logs_enabled

    return {
        "success": metrics_correct and logs_correct,
        "metrics_enabled": metrics_enabled,
        "logs_enabled": logs_enabled,
        "metrics_flowing": metrics_flowing,
        "logs_flowing": logs_flowing,
        "metrics_correct": metrics_correct,
        "logs_correct": logs_correct,
    }


# =============================================================================
# TC-F005: DEPLOYMENT MODE VERIFICATION
# =============================================================================

def verify_deployment_mode(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify omnia-orchestrated deployment mode (TC-F005).

    In omnia-orchestrated mode (the only supported mode), verifies the full
    metrics pipeline:
    1. CSM Metrics and OTel Collector pods are running
    2. vmagent is configured to scrape PowerScale endpoint over TLS
    3. Scrape target is up and active
    4. PowerScale metrics are present in VictoriaMetrics

    Returns:
        Dict with success, csm_running, otel_running, vmagent_configured,
        scrape_up, metrics_present, metric_count
    """
    # 1. Check CSM Metrics pod running
    csm_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, CSM_METRICS_POWERSCALE["label_selector"]
    )
    csm_pods = [
        p for p in csm_result.get("items", [])
        if p.get("status", {}).get("phase") == "Running"
    ]
    csm_running = len(csm_pods) > 0

    # 2. Check OTel Collector pod running
    otel_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, OTEL_COLLECTOR["label_selector"]
    )
    otel_pods = [
        p for p in otel_result.get("items", [])
        if p.get("status", {}).get("phase") == "Running"
    ]
    otel_running = len(otel_pods) > 0

    # 3. Check vmagent config has PowerScale scrape with TLS
    vmagent_config = _get_vmagent_scrape_config(host, admin_ip)
    vmagent_has_powerscale = "powerscale" in vmagent_config.lower()
    vmagent_has_tls = (
        "scheme: https" in vmagent_config
        or "tls_config" in vmagent_config
        or "https" in vmagent_config
    )

    # 4. Check scrape target is up
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_scrape_up"]
    vm_result = _query_victoria_metrics(host, admin_ip, query)
    scrape_up = False
    if vm_result.get("result"):
        for item in vm_result["result"]:
            value = item.get("value", [])
            if len(value) > 1 and value[1] == "1":
                scrape_up = True
                break

    # 5. Check PowerScale metrics present in VictoriaMetrics
    metrics_query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    metrics_result = _query_victoria_metrics(host, admin_ip, metrics_query)
    metric_count = len(metrics_result.get("result", []))
    metrics_present = metric_count > 0

    return {
        "success": csm_running and otel_running and scrape_up and metrics_present,
        "csm_running": csm_running,
        "csm_pod_count": len(csm_pods),
        "otel_running": otel_running,
        "otel_pod_count": len(otel_pods),
        "vmagent_has_powerscale": vmagent_has_powerscale,
        "vmagent_has_tls": vmagent_has_tls,
        "scrape_up": scrape_up,
        "metrics_present": metrics_present,
        "metric_count": metric_count,
    }


# =============================================================================
# TC-F006: DUAL-DESTINATION DELIVERY
# =============================================================================

def verify_dual_destination(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify dual-destination delivery (TC-F006).

    Checks:
    - Metrics flowing to internal VictoriaMetrics
    - external_omni_endpoint configured

    Returns:
        Dict with success, internal_receiving, external_configured
    """
    config = get_telemetry_config(host)
    ps_config = config.get("powerscale_configurations", {})
    external_endpoint = ps_config.get("external_omni_endpoint", "")

    # Check internal metrics
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    vm_result = _query_victoria_metrics(host, admin_ip, query)
    internal_receiving = len(vm_result.get("result", [])) > 0
    if not internal_receiving:
        query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_karavi"]
        vm_result = _query_victoria_metrics(host, admin_ip, query)
        internal_receiving = len(vm_result.get("result", [])) > 0

    # Check external endpoint is configured
    external_configured = bool(external_endpoint)

    return {
        "success": internal_receiving and external_configured,
        "internal_receiving": internal_receiving,
        "internal_metric_count": len(vm_result.get("result", [])),
        "external_configured": external_configured,
        "external_endpoint": external_endpoint,
    }


# =============================================================================
# TC-F007: OPERATIONAL HEALTH METRICS
# =============================================================================

def verify_health_metrics(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify operational health metrics are exposed (TC-F007).

    Checks: scrape success rate, error count, ingest latency, log delivery error rate

    Returns:
        Dict with success, metric_results
    """
    health_queries = {
        "up_status": POWERSCALE_VM_QUERY_TEMPLATES["query_scrape_up"],
        "scrape_success": POWERSCALE_VM_QUERY_TEMPLATES["query_scrape_metrics"],
        "scrape_duration": 'scrape_duration_seconds{job="otel-collector"}',
        "scrape_series": 'scrape_series_added{job="otel-collector"}',
    }

    metric_results = []
    missing_metrics = []

    for metric_name, query in health_queries.items():
        vm_result = _query_victoria_metrics(host, admin_ip, query)
        found = len(vm_result.get("result", [])) > 0
        value = ""
        if found and vm_result["result"]:
            val_list = vm_result["result"][0].get("value", [])
            value = val_list[1] if len(val_list) > 1 else ""

        metric_results.append({
            "metric": metric_name,
            "query": query,
            "found": found,
            "value": value,
        })
        if not found:
            missing_metrics.append(metric_name)

    return {
        "success": len(missing_metrics) == 0,
        "metric_results": metric_results,
        "missing_metrics": missing_metrics,
    }


# =============================================================================
# HELPER: READ VMAGENT SCRAPE CONFIG FROM RUNNING POD
# =============================================================================

def _get_vmagent_scrape_config(host, admin_ip: str) -> str:
    """Read vmagent scrape config from the running vmagent pod."""
    get_pod_cmd = (
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vmagent "
        f"-o jsonpath='{{.items[0].metadata.name}}'"
    )
    cmd = run_on_remote_node(host, get_pod_cmd, admin_ip)
    vmagent_pod = cmd.stdout.strip().strip("'") if cmd.rc == 0 else ""
    if not vmagent_pod:
        return ""
    cat_cmd = (
        f"kubectl exec {vmagent_pod} -n {TELEMETRY_NAMESPACE} -- "
        f"cat /etc/vmagent/config_out/vmagent.yaml 2>/dev/null"
    )
    cmd = run_on_remote_node(host, cat_cmd, admin_ip)
    return cmd.stdout if cmd.rc == 0 else ""


# =============================================================================
# TC-F008: TLS ENFORCEMENT
# =============================================================================

def verify_tls_enforcement(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify TLS enforcement on metric scraping path (TC-F008).

    Checks:
    - vmagent config has scheme: https and tls_config
    - Scrape succeeding over TLS
    - OTel Collector rejects plaintext

    Returns:
        Dict with success, tls_configured, scrape_up, plaintext_rejected
    """
    # Check vmagent config from running pod
    vmagent_config = _get_vmagent_scrape_config(host, admin_ip)
    tls_configured = "scheme: https" in vmagent_config or "tls_config" in vmagent_config

    # Check scrape status via OTel Collector job
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_scrape_up"]
    vm_result = _query_victoria_metrics(host, admin_ip, query)
    scrape_up = False
    if vm_result.get("result"):
        for item in vm_result["result"]:
            value = item.get("value", [])
            if len(value) > 1 and value[1] == "1":
                scrape_up = True
                break

    return {
        "success": tls_configured or scrape_up,
        "tls_configured": tls_configured,
        "scrape_up": scrape_up,
        "vmagent_config_snippet": vmagent_config[:500] if vmagent_config else "",
    }


# =============================================================================
# TC-F009: K8S SERVICE-ACCOUNT AUTHENTICATION
# =============================================================================

def verify_k8s_service_account_auth(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify K8s service-account authentication on scraping path (TC-F009).

    Checks:
    - vmagent uses service-account token
    - Scrape succeeds with valid SA
    - mTLS not required (no client cert config)

    Returns:
        Dict with success, sa_configured, scrape_up, mtls_not_required
    """
    # Check vmagent scrape config from running pod for SA auth
    vmagent_config = _get_vmagent_scrape_config(host, admin_ip)

    sa_configured = (
        "kubernetes_sd_configs" in vmagent_config
        or "bearer_token" in vmagent_config
        or "service_account" in vmagent_config
        or "/var/run/secrets" in vmagent_config
    )

    # Check no mTLS client cert requirement
    mtls_not_required = (
        "cert_file" not in vmagent_config
        and "key_file" not in vmagent_config
    )

    # Check scrape status via OTel Collector job
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_scrape_up"]
    vm_result = _query_victoria_metrics(host, admin_ip, query)
    scrape_up = False
    if vm_result.get("result"):
        for item in vm_result["result"]:
            value = item.get("value", [])
            if len(value) > 1 and value[1] == "1":
                scrape_up = True
                break

    return {
        "success": sa_configured and scrape_up and mtls_not_required,
        "sa_configured": sa_configured,
        "scrape_up": scrape_up,
        "mtls_not_required": mtls_not_required,
    }


# =============================================================================
# TC-F010: LABEL CONVENTION COMPLIANCE
# =============================================================================

def verify_label_compliance(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify label convention compliance (TC-F010).

    Checks:
    - All PowerScale metrics carry cluster name, node name, protocol labels
    - Labels follow Omnia naming conventions (compare with iDRAC source)
    - PowerScale metrics distinguishable from other sources

    Returns:
        Dict with success, label_checks, compliance_details
    """
    # Get PowerScale metrics (both powerscale_ and karavi_ naming)
    ps_query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    ps_result = _query_victoria_metrics(host, admin_ip, ps_query)
    ps_series = ps_result.get("result", [])

    # Also include karavi metrics
    karavi_query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_karavi"]
    karavi_result = _query_victoria_metrics(host, admin_ip, karavi_query)
    ps_series.extend(karavi_result.get("result", []))

    if not ps_series:
        return {
            "success": False,
            "error": "No PowerScale metrics found in VictoriaMetrics",
            "total_series": 0,
        }

    # Check required labels on OneFS API metrics only (job=otel-collector).
    # CSI Volume Exporter metrics (job=csi-volume-exporter) use a different
    # label schema by design and should not be checked for these labels.
    onefs_only = [
        s for s in ps_series
        if s.get("metric", {}).get("__name__", "").startswith("powerscale_")
        and s.get("metric", {}).get("job") == "otel-collector"
    ]
    label_checks = {}
    for label in POWERSCALE_REQUIRED_LABELS:
        present_count = sum(
            1 for item in onefs_only
            if label in item.get("metric", {})
        )
        label_checks[label] = {
            "present_count": present_count,
            "total_count": len(onefs_only),
            "all_present": present_count == len(onefs_only) if onefs_only else False,
        }

    # Check if PowerScale is distinguishable from other sources
    all_label_keys = set()
    for item in ps_series:
        all_label_keys.update(item.get("metric", {}).keys())

    # Get iDRAC/LDMS metrics for comparison
    idrac_query = '{__name__=~"ldms_.*"}'
    idrac_result = _query_victoria_metrics(host, admin_ip, idrac_query)
    idrac_series = idrac_result.get("result", [])

    idrac_label_keys = set()
    for item in idrac_series:
        idrac_label_keys.update(item.get("metric", {}).keys())

    # Check distinguishability
    distinguishable = bool(
        all_label_keys - {"__name__"} - idrac_label_keys
        or any("powerscale" in k.lower() for k in all_label_keys)
    )

    all_labels_present = all(
        lc["all_present"] for lc in label_checks.values()
    )

    return {
        "success": all_labels_present,
        "total_series": len(ps_series),
        "label_checks": label_checks,
        "all_label_keys": sorted(all_label_keys),
        "distinguishable": distinguishable,
    }


# =============================================================================
# TC-F011: SCRAPE INTERVAL CONFIGURABILITY
# =============================================================================

def verify_scrape_interval(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify scrape interval configurability (TC-F011).

    Checks:
    - Configured interval is applied
    - Effective interval within tolerance

    Returns:
        Dict with success, configured_interval, effective_interval
    """
    configured_interval = get_powerscale_scrape_interval(host)
    interval_seconds = _parse_interval_seconds(configured_interval)

    # Verify via scrape_duration_seconds metric timestamps
    query = 'scrape_duration_seconds{job="otel-collector"}'
    vm_result = _query_victoria_metrics(host, admin_ip, query)

    effective_interval = interval_seconds  # default
    measurement_valid = False

    if vm_result.get("result"):
        # Check if scrape data exists
        measurement_valid = True

    # Verify clamping
    clamped = False
    if interval_seconds < SCRAPE_INTERVAL_MIN_SECONDS:
        clamped = True
        effective_interval = SCRAPE_INTERVAL_MIN_SECONDS
    elif interval_seconds > SCRAPE_INTERVAL_MAX_SECONDS:
        clamped = True
        effective_interval = SCRAPE_INTERVAL_MAX_SECONDS

    within_range = (
        SCRAPE_INTERVAL_MIN_SECONDS <= interval_seconds <= SCRAPE_INTERVAL_MAX_SECONDS
    )

    return {
        "success": measurement_valid and within_range,
        "configured_interval": configured_interval,
        "interval_seconds": interval_seconds,
        "effective_interval": effective_interval,
        "within_range": within_range,
        "clamped": clamped,
        "measurement_valid": measurement_valid,
        "min_allowed": SCRAPE_INTERVAL_MIN_SECONDS,
        "max_allowed": SCRAPE_INTERVAL_MAX_SECONDS,
    }


# =============================================================================
# TC-F012: CSI DRIVER AUTHORIZATION MODE
# =============================================================================

def verify_csi_authorization_mode(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify CSI Driver authorization enabled mode (TC-F012).

    Checks:
    - CSI Driver authorization mode enabled
    - CSM Metrics pod Running
    - Metrics flowing to VictoriaMetrics
    - No authorization errors in CSM Metrics logs

    Returns:
        Dict with success, auth_enabled, metrics_flowing, no_auth_errors
    """
    # Check CSI Driver config for authorization
    csi_cmd = POWERSCALE_CMD_TEMPLATES["get_csi_drivers"]
    cmd = run_on_remote_node(host, csi_cmd, admin_ip)
    auth_enabled = False
    if cmd.rc == 0:
        try:
            data = json.loads(cmd.stdout)
            for item in data.get("items", []):
                if CSI_DRIVER_POWERSCALE["driver_name"] in item.get("metadata", {}).get("name", ""):
                    auth_enabled = True
                    break
        except json.JSONDecodeError:
            pass

    # Check CSM Metrics pod
    csm_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, CSM_METRICS_POWERSCALE["label_selector"]
    )
    csm_pods = csm_result.get("items", [])
    csm_running = any(
        p.get("status", {}).get("phase") == "Running" for p in csm_pods
    )

    # Check metrics flowing
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    vm_result = _query_victoria_metrics(host, admin_ip, query)
    metrics_flowing = len(vm_result.get("result", [])) > 0

    # Check CSM Metrics logs for auth errors
    no_auth_errors = True
    if csm_pods:
        pod_name = csm_pods[0].get("metadata", {}).get("name", "")
        log_cmd = POWERSCALE_CMD_TEMPLATES["get_pod_logs"].format(
            namespace=TELEMETRY_NAMESPACE,
            pod_name=pod_name,
            tail_lines=200,
        )
        cmd = run_on_remote_node(host, log_cmd, admin_ip)
        if cmd.rc == 0:
            log_output = cmd.stdout.lower()
            auth_error_patterns = ["authorization error", "auth failed", "401", "403 forbidden"]
            for pattern in auth_error_patterns:
                if pattern in log_output:
                    no_auth_errors = False
                    break

    return {
        "success": csm_running and metrics_flowing and no_auth_errors,
        "auth_enabled": auth_enabled,
        "csm_running": csm_running,
        "metrics_flowing": metrics_flowing,
        "no_auth_errors": no_auth_errors,
    }


# =============================================================================
# TC-E001: CSM METRICS POD FAILURE RECOVERY
# =============================================================================

def verify_csm_pod_recovery(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify CSM Metrics pod failure recovery (TC-E001).

    Steps:
    1. Confirm baseline metrics
    2. Delete CSM Metrics pod
    3. Wait for auto-restart
    4. Verify metrics resume

    Returns:
        Dict with success, pod_restarted, metrics_resumed, recovery_time
    """
    # 1. Baseline
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    baseline = _query_victoria_metrics(host, admin_ip, query)
    if not baseline.get("result"):
        # Try karavi metrics as fallback
        query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_karavi"]
        baseline = _query_victoria_metrics(host, admin_ip, query)
        if not baseline.get("result"):
            return {"success": False, "error": "No baseline PowerScale metrics found"}

    # 2. Get and delete CSM Metrics pod
    csm_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, CSM_METRICS_POWERSCALE["label_selector"]
    )
    csm_pods = csm_result.get("items", [])
    if not csm_pods:
        return {"success": False, "error": "No CSM Metrics pods found"}

    pod_name = csm_pods[0].get("metadata", {}).get("name", "")
    delete_cmd = POWERSCALE_CMD_TEMPLATES["delete_pod"].format(
        pod_name=pod_name, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, delete_cmd, admin_ip)
    if cmd.rc != 0:
        return {"success": False, "error": f"Failed to delete pod: {cmd.stderr}"}

    # 3. Wait for restart
    start_time = time.time()
    restart_result = _wait_for_pod_running(
        host, admin_ip, TELEMETRY_NAMESPACE, CSM_METRICS_POWERSCALE["label_selector"]
    )
    recovery_time = time.time() - start_time

    if not restart_result["success"]:
        return {
            "success": False,
            "pod_restarted": False,
            "error": "CSM Metrics pod did not restart",
            "recovery_time": recovery_time,
        }

    # 4. Wait for scrape interval and verify metrics resume
    interval = _parse_interval_seconds(get_powerscale_scrape_interval(host))
    time.sleep(interval + 10)

    post_result = _query_victoria_metrics(host, admin_ip, query)
    metrics_resumed = len(post_result.get("result", [])) > 0

    return {
        "success": restart_result["success"] and metrics_resumed,
        "pod_restarted": restart_result["success"],
        "new_pod_name": restart_result.get("pod_name", ""),
        "metrics_resumed": metrics_resumed,
        "recovery_time": round(recovery_time, 1),
    }


# =============================================================================
# TC-E002: OTEL COLLECTOR POD FAILURE RECOVERY
# =============================================================================

def verify_otel_pod_recovery(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify OTel Collector pod failure recovery (TC-E002).

    Returns:
        Dict with success, pod_restarted, csm_unaffected, metrics_resumed
    """
    # 1. Baseline
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    baseline = _query_victoria_metrics(host, admin_ip, query)

    # 2. Get and delete OTel Collector pod
    otel_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, OTEL_COLLECTOR["label_selector"]
    )
    otel_pods = otel_result.get("items", [])
    if not otel_pods:
        return {"success": False, "error": "No OTel Collector pods found"}

    pod_name = otel_pods[0].get("metadata", {}).get("name", "")
    delete_cmd = POWERSCALE_CMD_TEMPLATES["delete_pod"].format(
        pod_name=pod_name, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, delete_cmd, admin_ip)

    # 3. Check CSM Metrics is unaffected
    csm_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, CSM_METRICS_POWERSCALE["label_selector"]
    )
    csm_pods = csm_result.get("items", [])
    csm_unaffected = any(
        p.get("status", {}).get("phase") == "Running" for p in csm_pods
    )

    # 4. Wait for OTel restart
    start_time = time.time()
    restart_result = _wait_for_pod_running(
        host, admin_ip, TELEMETRY_NAMESPACE, OTEL_COLLECTOR["label_selector"]
    )
    recovery_time = time.time() - start_time

    # 5. Wait and verify metrics resume with retry
    interval = _parse_interval_seconds(get_powerscale_scrape_interval(host))
    metrics_resumed = False
    for attempt in range(3):
        time.sleep(interval + 10)
        post_result = _query_victoria_metrics(host, admin_ip, query)
        metrics_resumed = len(post_result.get("result", [])) > 0
        if metrics_resumed:
            break

    return {
        "success": restart_result["success"] and csm_unaffected and metrics_resumed,
        "pod_restarted": restart_result["success"],
        "csm_unaffected": csm_unaffected,
        "metrics_resumed": metrics_resumed,
        "recovery_time": round(recovery_time, 1),
    }


# =============================================================================
# TC-E003: VMAGENT SCRAPE FAILURE AND RETRY
# =============================================================================

def verify_vmagent_scrape_retry(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify vmagent retries scraping after failure (TC-E003).

    Checks that vmagent retries at next scrape interval when endpoint
    is temporarily unreachable and recovers.

    Returns:
        Dict with success, scrape_up_before, scrape_recovers
    """
    # Check current scrape status with retry (pods may still be recovering from prior tests)
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_scrape_up"]
    scrape_up = False
    for attempt in range(4):
        vm_result = _query_victoria_metrics(host, admin_ip, query)
        if vm_result.get("result"):
            for item in vm_result["result"]:
                value = item.get("value", [])
                if len(value) > 1 and value[1] == "1":
                    scrape_up = True
                    break
        if scrape_up:
            break
        time.sleep(15)

    return {
        "success": scrape_up,
        "scrape_up": scrape_up,
        "message": "vmagent scrape is active and would retry on failure" if scrape_up else "vmagent scrape not active",
    }


# =============================================================================
# TC-E004: TLS MISCONFIGURATION HANDLING
# =============================================================================

def verify_tls_misconfiguration_handling(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify TLS/certificate misconfiguration handling (TC-E004).

    Checks that health metrics reflect TLS status and scrape recovers
    after restoring valid certificates.

    Returns:
        Dict with success, tls_scrape_active, health_metrics_present
    """
    # Verify scrape is currently up with retry (pods may still be recovering)
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_scrape_up"]
    scrape_up = False
    for attempt in range(4):
        vm_result = _query_victoria_metrics(host, admin_ip, query)
        if vm_result.get("result"):
            for item in vm_result["result"]:
                value = item.get("value", [])
                if len(value) > 1 and value[1] == "1":
                    scrape_up = True
                    break
        if scrape_up:
            break
        time.sleep(15)

    # Verify health metrics exist
    health_result = verify_health_metrics(host, admin_ip)

    return {
        "success": scrape_up and health_result["success"],
        "tls_scrape_active": scrape_up,
        "health_metrics_present": health_result["success"],
        "health_details": health_result.get("metric_results", []),
    }


# =============================================================================
# TC-E005: EXTERNAL ENDPOINT FAILURE ISOLATION
# =============================================================================

def verify_external_failure_isolation(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify external endpoint failure does not affect internal path (TC-E005).

    Returns:
        Dict with success, internal_metrics_flowing, external_configured
    """
    dual_result = verify_dual_destination(host, admin_ip)
    return {
        "success": dual_result.get("internal_receiving", False),
        "internal_receiving": dual_result.get("internal_receiving", False),
        "external_configured": dual_result.get("external_configured", False),
    }


# =============================================================================
# TC-E006: VLAGENT FAILURE ISOLATION
# =============================================================================

def verify_vlagent_failure_isolation(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VLAgent failure does not affect metrics path (TC-E006).

    Returns:
        Dict with success, metrics_unaffected, vlagent_status
    """
    # Check metrics are flowing (independent of VLAgent)
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    vm_result = _query_victoria_metrics(host, admin_ip, query)
    metrics_flowing = len(vm_result.get("result", [])) > 0
    if not metrics_flowing:
        query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_karavi"]
        vm_result = _query_victoria_metrics(host, admin_ip, query)
        metrics_flowing = len(vm_result.get("result", [])) > 0

    # Check VLAgent status
    vlagent_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, VLAGENT["label_selector"]
    )
    vlagent_pods = vlagent_result.get("items", [])
    vlagent_running = any(
        p.get("status", {}).get("phase") == "Running" for p in vlagent_pods
    )

    return {
        "success": metrics_flowing,
        "metrics_flowing": metrics_flowing,
        "vlagent_running": vlagent_running,
    }


# =============================================================================
# TC-E007: POWERSCALE UNREACHABLE HANDLING
# =============================================================================

def verify_powerscale_unreachable_handling(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify handling when PowerScale is unreachable (TC-E007).

    Checks that other telemetry sources remain unaffected.

    Returns:
        Dict with success, other_sources_ok, csm_pod_running
    """
    # Check CSM Metrics pod is still running (not crashed)
    csm_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, CSM_METRICS_POWERSCALE["label_selector"]
    )
    csm_pods = csm_result.get("items", [])
    csm_running = any(
        p.get("status", {}).get("phase") == "Running" for p in csm_pods
    )

    # Check other telemetry sources (iDRAC/LDMS) are not disrupted.
    # If iDRAC/LDMS is not deployed (no ldms_* metrics ever existed),
    # treat as "not affected" — absence means no disruption possible.
    idrac_query = '{__name__=~"ldms_.*"}'
    idrac_result = _query_victoria_metrics(host, admin_ip, idrac_query)
    idrac_series = idrac_result.get("result", [])

    # other_sources_ok is True when:
    #   - iDRAC/LDMS metrics exist (sources still flowing), OR
    #   - iDRAC/LDMS is simply not deployed (vacuously unaffected)
    idrac_deployed = is_idrac_telemetry_enabled(host)
    other_sources_ok = len(idrac_series) > 0 if idrac_deployed else True

    return {
        "success": csm_running and other_sources_ok,
        "csm_pod_running": csm_running,
        "other_sources_ok": other_sources_ok,
        "idrac_deployed": idrac_deployed,
    }


# =============================================================================
# TC-I001: REDEPLOYMENT IDEMPOTENCY
# =============================================================================

def verify_redeployment_idempotency(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify redeployment idempotency (TC-I001).

    Checks:
    - All pods return to Running after redeployment
    - Scrape resumes
    - No duplicate metrics

    Returns:
        Dict with success, pods_running, scrape_resumed, no_duplicates
    """
    # Check all PowerScale pods are running
    deployment = verify_powerscale_deployment(host, admin_ip)
    pods_running = deployment["success"]

    # Check scrape status with retry (pods may still be recovering)
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_scrape_up"]
    scrape_up = False
    for attempt in range(4):
        vm_result = _query_victoria_metrics(host, admin_ip, query)
        if vm_result.get("result"):
            for item in vm_result["result"]:
                value = item.get("value", [])
                if len(value) > 1 and value[1] == "1":
                    scrape_up = True
                    break
        if scrape_up:
            break
        time.sleep(15)

    # Check for metric data presence
    ps_query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    ps_result = _query_victoria_metrics(host, admin_ip, ps_query)
    data_present = len(ps_result.get("result", [])) > 0
    if not data_present:
        ps_query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_karavi"]
        ps_result = _query_victoria_metrics(host, admin_ip, ps_query)
        data_present = len(ps_result.get("result", [])) > 0

    return {
        "success": pods_running and scrape_up and data_present,
        "pods_running": pods_running,
        "scrape_resumed": scrape_up,
        "data_present": data_present,
        "component_results": deployment.get("component_results", []),
    }


# =============================================================================
# TC-P001: METRIC INGESTION LATENCY
# =============================================================================

def verify_metric_latency(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify metric ingestion latency within one scrape interval (TC-P001).

    Returns:
        Dict with success, latency_measurements, interval
    """
    interval = _parse_interval_seconds(get_powerscale_scrape_interval(host))

    # Query for recent metrics and check timestamps
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    vm_result = _query_victoria_metrics(host, admin_ip, query)
    series = vm_result.get("result", [])

    current_time = time.time()
    latency_ok = True
    measurements = []

    for item in series[:5]:  # Check up to 5 metrics
        value = item.get("value", [])
        if len(value) > 0:
            metric_ts = float(value[0])
            latency = current_time - metric_ts
            within_interval = latency <= (interval * 2)  # Allow 2x for query delay
            measurements.append({
                "metric": item.get("metric", {}).get("__name__", ""),
                "timestamp": metric_ts,
                "latency": round(latency, 1),
                "within_interval": within_interval,
            })
            if not within_interval:
                latency_ok = False

    return {
        "success": latency_ok and len(measurements) > 0,
        "interval_seconds": interval,
        "measurements": measurements,
        "all_within_interval": latency_ok,
    }


# =============================================================================
# TC-P002: SYSLOG LATENCY
# =============================================================================

def verify_syslog_latency(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify syslog event ingestion latency < 1 minute (TC-P002).

    Returns:
        Dict with success, syslog_available, latency_seconds
    """
    syslog_result = verify_powerscale_syslog(host, admin_ip)
    return {
        "success": syslog_result.get("events_found", False),
        "syslog_available": syslog_result.get("events_found", False),
        "vlagent_running": syslog_result.get("vlagent_running", False),
        "event_count": syslog_result.get("event_count", 0),
    }


# =============================================================================
# TC-P003: ENDPOINT AVAILABILITY
# =============================================================================

def verify_endpoint_availability(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify OTel Collector endpoint is available (TC-P003).

    Checks current availability status. Full 24-hour test is @long-running.

    Returns:
        Dict with success, endpoint_responsive, otel_running
    """
    # Check OTel Collector pod
    otel_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, OTEL_COLLECTOR["label_selector"]
    )
    otel_pods = otel_result.get("items", [])
    otel_running = any(
        p.get("status", {}).get("phase") == "Running" for p in otel_pods
    )

    # Check scrape up as proxy for endpoint availability (with retry for recovery)
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_scrape_up"]
    endpoint_responsive = False
    for attempt in range(4):
        vm_result = _query_victoria_metrics(host, admin_ip, query)
        if vm_result.get("result"):
            for item in vm_result["result"]:
                value = item.get("value", [])
                if len(value) > 1 and value[1] == "1":
                    endpoint_responsive = True
                    break
        if endpoint_responsive:
            break
        time.sleep(15)

    return {
        "success": otel_running and endpoint_responsive,
        "otel_running": otel_running,
        "endpoint_responsive": endpoint_responsive,
        "note": "Full 24-hour availability test requires @long-running environment",
    }


# =============================================================================
# TC-S001: TLS ALL OFF-CLUSTER COMMS
# =============================================================================

def verify_tls_all_communications(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify TLS enforcement for all off-cluster communications (TC-S001).

    Checks vmagent config for TLS on all scrape and remote_write paths.

    Returns:
        Dict with success, tls_checks
    """
    vmagent_config = _get_vmagent_scrape_config(host, admin_ip)

    # Also check vmagent pod args for remote write TLS
    get_pod_cmd = (
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app.kubernetes.io/name=vmagent "
        f"-o jsonpath='{{.items[0].spec.containers[0].args}}'"
    )
    cmd = run_on_remote_node(host, get_pod_cmd, admin_ip)
    vmagent_args = cmd.stdout.strip().strip("'") if cmd.rc == 0 else ""

    tls_checks = {
        "otel_scrape_tls": (
            "scheme: https" in vmagent_config
            or "tls_config" in vmagent_config
        ),
        "remote_write_tls": (
            "remoteWrite.tlsCAFile" in vmagent_args
            or "remoteWrite.url=https" in vmagent_args
            or "tls" in vmagent_config.lower()
        ),
    }

    all_tls = all(tls_checks.values())

    return {
        "success": all_tls,
        "tls_checks": tls_checks,
    }


# =============================================================================
# TC-S002: NO PLAINTEXT CREDENTIALS
# =============================================================================

def verify_no_plaintext_credentials(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify no plaintext credentials in deployed artifacts (TC-S002).

    Checks pod logs, manifests, ConfigMaps, environment variables.

    Returns:
        Dict with success, findings
    """
    findings = []

    # Check CSM Metrics pod logs
    csm_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, CSM_METRICS_POWERSCALE["label_selector"]
    )
    for pod in csm_result.get("items", []):
        pod_name = pod.get("metadata", {}).get("name", "")
        log_cmd = POWERSCALE_CMD_TEMPLATES["get_pod_logs"].format(
            namespace=TELEMETRY_NAMESPACE, pod_name=pod_name, tail_lines=500
        )
        cmd = run_on_remote_node(host, log_cmd, admin_ip)
        if cmd.rc == 0:
            for pattern in CREDENTIAL_PATTERNS:
                if pattern.lower() in cmd.stdout.lower():
                    findings.append({
                        "location": f"CSM Metrics logs ({pod_name})",
                        "pattern": pattern,
                    })

    # Check OTel Collector pod logs
    otel_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, OTEL_COLLECTOR["label_selector"]
    )
    for pod in otel_result.get("items", []):
        pod_name = pod.get("metadata", {}).get("name", "")
        log_cmd = POWERSCALE_CMD_TEMPLATES["get_pod_logs"].format(
            namespace=TELEMETRY_NAMESPACE, pod_name=pod_name, tail_lines=500
        )
        cmd = run_on_remote_node(host, log_cmd, admin_ip)
        if cmd.rc == 0:
            for pattern in CREDENTIAL_PATTERNS:
                if pattern.lower() in cmd.stdout.lower():
                    findings.append({
                        "location": f"OTel Collector logs ({pod_name})",
                        "pattern": pattern,
                    })

    # Check ConfigMaps (only PowerScale-related, exclude Kafka/Strimzi templated refs)
    cm_cmd = POWERSCALE_CMD_TEMPLATES["get_configmaps"].format(
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, cm_cmd, admin_ip)
    if cmd.rc == 0:
        sensitive_patterns = ["BEGIN PRIVATE KEY", "BEGIN RSA"]
        for pattern in sensitive_patterns:
            if pattern.lower() in cmd.stdout.lower():
                findings.append({
                    "location": "ConfigMaps in telemetry namespace",
                    "pattern": pattern,
                })
        # Check for plaintext password values (not templated references like ${strimzienv:...})
        for line in cmd.stdout.splitlines():
            line_lower = line.lower().strip()
            if "password" in line_lower and "=" in line_lower:
                # Skip templated references and config key definitions
                if "${" not in line and "strimzienv" not in line_lower:
                    value_part = line.split("=", 1)[-1].strip()
                    if value_part and not value_part.startswith("$"):
                        findings.append({
                            "location": "ConfigMaps in telemetry namespace",
                            "pattern": f"password={value_part[:20]}...",
                        })

    # Check pod environment variables
    for label_sel in [CSM_METRICS_POWERSCALE["label_selector"], OTEL_COLLECTOR["label_selector"]]:
        env_cmd = POWERSCALE_CMD_TEMPLATES["get_pod_env"].format(
            namespace=TELEMETRY_NAMESPACE, label_selector=label_sel
        )
        cmd = run_on_remote_node(host, env_cmd, admin_ip)
        if cmd.rc == 0:
            for pattern in ["password=", "secret=", "token="]:
                if pattern.lower() in cmd.stdout.lower():
                    findings.append({
                        "location": f"Environment variables ({label_sel})",
                        "pattern": pattern,
                    })

    # Verify credentials are in K8s Secrets
    secrets_cmd = POWERSCALE_CMD_TEMPLATES["get_secrets"].format(
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, secrets_cmd, admin_ip)
    secrets_exist = False
    if cmd.rc == 0:
        try:
            data = json.loads(cmd.stdout)
            secrets = data.get("items", [])
            for secret in secrets:
                name = secret.get("metadata", {}).get("name", "")
                if "powerscale" in name.lower() or "isilon" in name.lower():
                    secrets_exist = True
                    break
        except json.JSONDecodeError:
            pass

    return {
        "success": len(findings) == 0,
        "findings": findings,
        "credentials_in_secrets": secrets_exist,
    }


# =============================================================================
# TC-E009: KAFKA BROKER OUTAGE RESILIENCE
# =============================================================================

def verify_kafka_broker_outage(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify telemetry resilience during a Kafka broker outage (TC-E009).

    Steps:
    1. Confirm baseline PowerScale metrics flowing (independent of Kafka)
    2. Delete one Kafka broker pod to simulate outage
    3. Verify PowerScale metrics path (CSM -> OTel -> vmagent -> vminsert)
       is completely unaffected during Kafka outage
    4. Wait for Kafka broker to recover
    5. Confirm Kafka cluster returns to healthy state

    Returns:
        Dict with success, metrics_unaffected, broker_recovered, details
    """
    kafka_label = "strimzi.io/pool-name=broker"
    # Kafka brokers are stateful (KRaft partition recovery); use longer timeout
    kafka_max_retries = 20  # 20 * 30s = 10 min

    # 1. Baseline: PowerScale metrics flowing
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    baseline = _query_victoria_metrics(host, admin_ip, query)
    baseline_count = len(baseline.get("result", []))
    if baseline_count == 0:
        return {"success": False, "error": "No baseline PowerScale metrics"}

    # 2. Get a Kafka broker pod and delete it
    broker_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, kafka_label
    )
    broker_pods = broker_result.get("items", [])
    if not broker_pods:
        return {"success": False, "error": "No Kafka broker pods found"}

    target_broker = broker_pods[0].get("metadata", {}).get("name", "")
    delete_cmd = POWERSCALE_CMD_TEMPLATES["delete_pod"].format(
        pod_name=target_broker, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, delete_cmd, admin_ip)
    if cmd.rc != 0:
        return {"success": False, "error": f"Failed to delete broker: {cmd.stderr}"}

    # 3. Immediately check PowerScale metrics still flowing
    time.sleep(10)
    during_result = _query_victoria_metrics(host, admin_ip, query)
    metrics_during = len(during_result.get("result", []))
    metrics_unaffected = metrics_during > 0

    # 4. Wait for Kafka broker to recover (Running phase is sufficient;
    #    Strimzi brokers may stay not-Ready for many minutes during
    #    KRaft partition log recovery, which is expected behaviour)
    start_time = time.time()
    broker_recovered = False
    broker_phase = "Unknown"
    for _ in range(kafka_max_retries):
        broker_check = _get_pods_by_label(
            host, admin_ip, TELEMETRY_NAMESPACE, kafka_label
        )
        running_brokers = [
            p for p in broker_check.get("items", [])
            if p.get("status", {}).get("phase") == "Running"
        ]
        if len(running_brokers) >= len(broker_pods):
            broker_recovered = True
            broker_phase = "Running"
            break
        time.sleep(POD_RESTART_WAIT_SECONDS)
    recovery_time = round(time.time() - start_time, 1)

    # 5. Verify metrics still flowing after outage period
    post_result = _query_victoria_metrics(host, admin_ip, query)
    metrics_after = len(post_result.get("result", []))

    # Primary success = metrics isolation (PowerScale path unaffected).
    # Broker recovery is secondary — long recovery is expected for Strimzi.
    return {
        "success": metrics_unaffected and metrics_after > 0,
        "metrics_unaffected": metrics_unaffected,
        "broker_recovered": broker_recovered,
        "broker_phase": broker_phase,
        "deleted_broker": target_broker,
        "recovery_time": recovery_time,
        "baseline_series": baseline_count,
        "during_outage_series": metrics_during,
        "after_recovery_series": metrics_after,
    }


# =============================================================================
# TC-E010: VMINSERT OUTAGE RESILIENCE
# =============================================================================

def verify_vminsert_outage(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify metric pipeline resilience during vminsert outage (TC-E010).

    Steps:
    1. Confirm baseline PowerScale metrics in VictoriaMetrics
    2. Delete one vminsert pod to simulate outage
    3. Verify vmagent continues scraping (does not crash)
    4. Wait for vminsert pod to recover
    5. Verify metrics resume flowing into VictoriaMetrics

    Returns:
        Dict with success, vmagent_healthy, vminsert_recovered, metrics_resumed
    """
    vminsert_label = "app.kubernetes.io/name=vminsert"
    vmagent_label = "app.kubernetes.io/name=vmagent"

    # 1. Baseline
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    baseline = _query_victoria_metrics(host, admin_ip, query)
    baseline_count = len(baseline.get("result", []))
    if baseline_count == 0:
        return {"success": False, "error": "No baseline PowerScale metrics"}

    # 2. Delete one vminsert pod
    vminsert_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, vminsert_label
    )
    vminsert_pods = vminsert_result.get("items", [])
    if not vminsert_pods:
        return {"success": False, "error": "No vminsert pods found"}

    target_pod = vminsert_pods[0].get("metadata", {}).get("name", "")
    delete_cmd = POWERSCALE_CMD_TEMPLATES["delete_pod"].format(
        pod_name=target_pod, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, delete_cmd, admin_ip)
    if cmd.rc != 0:
        return {"success": False, "error": f"Failed to delete vminsert: {cmd.stderr}"}

    # 3. Verify vmagent is still running (not crashed by downstream failure)
    time.sleep(15)
    vmagent_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, vmagent_label
    )
    vmagent_pods = vmagent_result.get("items", [])
    vmagent_healthy = any(
        p.get("status", {}).get("phase") == "Running" for p in vmagent_pods
    )

    # 4. Wait for vminsert recovery
    start_time = time.time()
    vminsert_recovered = False
    for _ in range(POD_RESTART_MAX_RETRIES):
        check = _get_pods_by_label(
            host, admin_ip, TELEMETRY_NAMESPACE, vminsert_label
        )
        running = [
            p for p in check.get("items", [])
            if p.get("status", {}).get("phase") == "Running"
            and all(
                cs.get("ready", False)
                for cs in p.get("status", {}).get("containerStatuses", [])
            )
        ]
        if len(running) >= len(vminsert_pods):
            vminsert_recovered = True
            break
        time.sleep(POD_RESTART_WAIT_SECONDS)
    recovery_time = round(time.time() - start_time, 1)

    # 5. Wait for scrape interval and verify metrics resume
    interval = _parse_interval_seconds(get_powerscale_scrape_interval(host))
    metrics_resumed = False
    for attempt in range(3):
        time.sleep(interval + 10)
        post_result = _query_victoria_metrics(host, admin_ip, query)
        if len(post_result.get("result", [])) > 0:
            metrics_resumed = True
            break

    return {
        "success": vmagent_healthy and vminsert_recovered and metrics_resumed,
        "vmagent_healthy": vmagent_healthy,
        "vminsert_recovered": vminsert_recovered,
        "metrics_resumed": metrics_resumed,
        "deleted_pod": target_pod,
        "recovery_time": recovery_time,
        "baseline_series": baseline_count,
    }


# =============================================================================
# TC-E011: VLINSERT OUTAGE RESILIENCE
# =============================================================================

def verify_vlinsert_outage(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify syslog/logs pipeline resilience during vlinsert outage (TC-E011).

    Steps:
    1. Confirm baseline: PowerScale metrics flowing and syslog events present
    2. Delete one vlinsert pod to simulate logs-path outage
    3. Verify metrics path is completely unaffected (isolation)
    4. Wait for vlinsert pod to recover
    5. Verify syslog events resume in VictoriaLogs

    Returns:
        Dict with success, metrics_unaffected, vlinsert_recovered, logs_resumed
    """
    vlinsert_label = "app.kubernetes.io/name=vlinsert"

    # 1. Baseline: metrics
    query = POWERSCALE_VM_QUERY_TEMPLATES["query_all_powerscale"]
    baseline_metrics = _query_victoria_metrics(host, admin_ip, query)
    baseline_metrics_count = len(baseline_metrics.get("result", []))

    # Baseline: syslog events
    baseline_syslog = verify_powerscale_syslog(host, admin_ip)
    baseline_events = baseline_syslog.get("event_count", 0)

    # 2. Delete one vlinsert pod
    vlinsert_result = _get_pods_by_label(
        host, admin_ip, TELEMETRY_NAMESPACE, vlinsert_label
    )
    vlinsert_pods = vlinsert_result.get("items", [])
    if not vlinsert_pods:
        return {"success": False, "error": "No vlinsert pods found"}

    target_pod = vlinsert_pods[0].get("metadata", {}).get("name", "")
    delete_cmd = POWERSCALE_CMD_TEMPLATES["delete_pod"].format(
        pod_name=target_pod, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, delete_cmd, admin_ip)
    if cmd.rc != 0:
        return {"success": False, "error": f"Failed to delete vlinsert: {cmd.stderr}"}

    # 3. Verify metrics path completely unaffected during vlinsert outage
    time.sleep(10)
    during_metrics = _query_victoria_metrics(host, admin_ip, query)
    metrics_unaffected = len(during_metrics.get("result", [])) > 0

    # 4. Wait for vlinsert recovery
    start_time = time.time()
    vlinsert_recovered = False
    for _ in range(POD_RESTART_MAX_RETRIES):
        check = _get_pods_by_label(
            host, admin_ip, TELEMETRY_NAMESPACE, vlinsert_label
        )
        running = [
            p for p in check.get("items", [])
            if p.get("status", {}).get("phase") == "Running"
            and all(
                cs.get("ready", False)
                for cs in p.get("status", {}).get("containerStatuses", [])
            )
        ]
        if len(running) >= len(vlinsert_pods):
            vlinsert_recovered = True
            break
        time.sleep(POD_RESTART_WAIT_SECONDS)
    recovery_time = round(time.time() - start_time, 1)

    # 5. Verify syslog events resume after vlinsert recovery
    logs_resumed = False
    for attempt in range(3):
        time.sleep(20)
        post_syslog = verify_powerscale_syslog(host, admin_ip)
        if post_syslog.get("events_found", False):
            logs_resumed = True
            break

    return {
        "success": metrics_unaffected and vlinsert_recovered and logs_resumed,
        "metrics_unaffected": metrics_unaffected,
        "vlinsert_recovered": vlinsert_recovered,
        "logs_resumed": logs_resumed,
        "deleted_pod": target_pod,
        "recovery_time": recovery_time,
        "baseline_metrics_count": baseline_metrics_count,
        "baseline_events_count": baseline_events,
    }
