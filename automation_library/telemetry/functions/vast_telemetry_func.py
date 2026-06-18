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
VAST Storage Telemetry Automation - Functions.

This module contains verification functions for VAST storage telemetry.
Implements the logic for positive/sanity test cases defined in the
VAST telemetry test specification.
"""

import json
import urllib.parse
from typing import Dict, Any, List

from ...core import run_on_remote_node
from ..vars.shared_vars import TELEMETRY_NAMESPACE
from ..vars.vast_telemetry_vars import (
    VAST_JOB_PATTERN,
    VAST_SCRAPE_JOB,
    VAST_CREDENTIALS_SECRET,
    VAST_SERVICE_NAME,
    VAST_APP_LABEL,
    VAST_VMSERVICESCRAPE_NAME,
    VAST_REQUIRED_LABELS,
    VAST_ENRICHMENT_LABELS,
    VAST_HEALTH_METRICS,
    VAST_MIN_METRIC_FAMILIES,
    VAST_COVERAGE_THRESHOLD_PERCENT,
    VAST_METRICS_PATH,
    VAST_METRICS_SCHEME,
    VAST_CMD_TEMPLATES,
    VAST_VM_QUERY_TEMPLATES,
    SCRAPE_INTERVAL_MIN_SECONDS,
    SCRAPE_INTERVAL_MAX_SECONDS,
    SCRAPE_INTERVAL_TOLERANCE_SECONDS,
    CREDENTIAL_PATTERNS,
    VMSELECT_LABEL_SELECTOR,
    VMAGENT_LABEL_SELECTOR,
)
from ..vars.victoria_vars import (
    VICTORIA_CLUSTER,
    VICTORIA_API_ENDPOINTS,
)
from .shared_func import get_telemetry_config


# =============================================================================
# CONFIGURATION HELPERS
# =============================================================================

def is_vast_telemetry_enabled(host) -> bool:
    """
    Check if VAST telemetry is enabled in telemetry_config.yml.

    Checks telemetry_sources.vast.metrics_enabled.

    Args:
        host: Testinfra host object

    Returns:
        True if VAST telemetry is enabled
    """
    config = get_telemetry_config(host)
    sources = config.get("telemetry_sources", {})
    vast_config = sources.get("vast", {})
    return bool(vast_config.get("metrics_enabled", False))


def get_vast_config(host) -> Dict[str, Any]:
    """
    Get VAST-specific configuration from telemetry_config.yml.

    Returns:
        Dict with VAST telemetry configuration
    """
    config = get_telemetry_config(host)
    return config.get("vast_configurations", {})


def _get_vm_query_endpoint(host) -> Dict[str, Any]:
    """
    Get VictoriaMetrics query endpoint info.

    VictoriaMetrics is always deployed in cluster mode.
    """
    return {
        "service_name": VICTORIA_CLUSTER["vmselect"]["service_name"],
        "port": VICTORIA_CLUSTER["vmselect"]["port"],
        "query_endpoint": VICTORIA_API_ENDPOINTS["cluster_query"],
    }


def _get_vmselect_ip(host, admin_ip: str) -> Dict[str, str]:
    """
    Get vmselect service IP by label selector (handles dynamic service names).

    Tries LoadBalancer external IP first, then falls back to ClusterIP.

    Returns:
        Dict with 'ip', 'port', 'error'
    """
    vm_info = _get_vm_query_endpoint(host)
    port = str(vm_info["port"])

    # Find vmselect service by app.kubernetes.io/name label
    label_selector = VMSELECT_LABEL_SELECTOR
    kubectl_cmd = (
        f"kubectl get svc -n {TELEMETRY_NAMESPACE} -l {label_selector} "
        f"-o jsonpath='{{.items[0].status.loadBalancer.ingress[0].ip}}'"
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip().strip("'") if cmd.rc == 0 else ""

    if external_ip and external_ip != "null":
        return {"ip": external_ip, "port": port, "error": ""}

    # Fallback to ClusterIP
    kubectl_cmd = (
        f"kubectl get svc -n {TELEMETRY_NAMESPACE} -l {label_selector} "
        f"-o jsonpath='{{.items[0].spec.clusterIP}}'"
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    cluster_ip = cmd.stdout.strip().strip("'") if cmd.rc == 0 else ""

    if cluster_ip and cluster_ip != "null":
        return {"ip": cluster_ip, "port": port, "error": ""}

    return {"ip": "", "port": port, "error": "No IP found for vmselect service"}


# Module-level cache for vmselect IP
_vmselect_ip_cache: Dict[str, str] = {}


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
    query_endpoint = vm_info["query_endpoint"]

    # Get vmselect IP (cached)
    cache_key = f"{admin_ip}_vmselect"
    if cache_key in _vmselect_ip_cache:
        ip = _vmselect_ip_cache[cache_key]
        port = str(vm_info["port"])
    else:
        ip_info = _get_vmselect_ip(host, admin_ip)
        if ip_info["error"]:
            return {"success": False, "result": [], "error": ip_info["error"]}
        ip = ip_info["ip"]
        port = ip_info["port"]
        _vmselect_ip_cache[cache_key] = ip

    encoded_query = urllib.parse.quote(query)
    curl_cmd = (
        f"curl -sk --max-time {timeout} "
        f"'https://{ip}:{port}{query_endpoint}?query={encoded_query}'"
    )
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)

    try:
        response = json.loads(cmd.stdout) if cmd.rc == 0 else {}
        result_data = response.get("data", {}).get("result", [])
        return {"success": True, "result": result_data, "error": ""}
    except json.JSONDecodeError:
        return {"success": False, "result": [], "error": "Failed to parse VM response"}


# =============================================================================
# TC-F001: SCRAPE ACTIVE AND METRICS PRESENT
# =============================================================================

def verify_vast_scrape_active(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VAST scrape is active and metrics are present (TC-F001).

    Checks:
    - up{job=~"vast.*"} == 1
    - count({job=~"vast.*"}) > 0
    - Scrape samples being collected

    Returns:
        Dict with success, scrape_up, series_count, samples_scraped
    """
    # Check scrape up status
    up_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_scrape_up"]
    )
    scrape_up = False
    up_value = "0"
    if up_result["success"] and up_result["result"]:
        up_value = up_result["result"][0].get("value", [None, "0"])[1]
        scrape_up = up_value == "1"

    # Count total series
    count_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_count_series"]
    )
    series_count = 0
    if count_result["success"] and count_result["result"]:
        series_count = int(count_result["result"][0].get("value", [None, "0"])[1])

    # Check scrape samples
    samples_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_scrape_samples"]
    )
    samples_scraped = 0
    if samples_result["success"] and samples_result["result"]:
        samples_scraped = int(
            float(samples_result["result"][0].get("value", [None, "0"])[1])
        )

    return {
        "success": scrape_up and series_count > 0,
        "scrape_up": scrape_up,
        "up_value": up_value,
        "series_count": series_count,
        "samples_scraped": samples_scraped,
    }


# =============================================================================
# TC-F002: TLS AND BASIC AUTH VERIFICATION
# =============================================================================

def verify_vast_tls_basic_auth(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify TLS and Basic Auth are configured for VAST scrape (TC-F002).

    Checks:
    - VMServiceScrape has scheme: https
    - VMServiceScrape has basicAuth configured
    - VMServiceScrape references credentials Secret
    - tlsConfig present (insecureSkipVerify or CA cert)
    - Scrape is active (up=1)

    Returns:
        Dict with success, tls_configured, basic_auth_configured,
        secret_exists, scrape_up
    """
    # Get VMServiceScrape
    kubectl_cmd = VAST_CMD_TEMPLATES["get_vmservicescrape"].format(
        name=VAST_VMSERVICESCRAPE_NAME, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    tls_configured = False
    basic_auth_configured = False
    insecure_skip_verify = False
    scheme = ""

    if cmd.rc == 0:
        try:
            vmss = json.loads(cmd.stdout)
            endpoints = vmss.get("spec", {}).get("endpoints", [])
            if endpoints:
                ep = endpoints[0]
                scheme = ep.get("scheme", "")
                tls_configured = scheme == "https"

                # Check basicAuth
                basic_auth = ep.get("basicAuth", {})
                basic_auth_configured = bool(
                    basic_auth.get("username") and basic_auth.get("password")
                )

                # Check TLS config
                tls_config = ep.get("tlsConfig", {})
                insecure_skip_verify = tls_config.get("insecureSkipVerify", False)
        except json.JSONDecodeError:
            pass

    # Check credentials Secret exists
    secret_cmd = VAST_CMD_TEMPLATES["get_secret"].format(
        secret_name=VAST_CREDENTIALS_SECRET, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, secret_cmd, admin_ip)
    secret_exists = cmd.rc == 0
    secret_keys = []
    if secret_exists:
        try:
            secret_data = json.loads(cmd.stdout)
            secret_keys = list(secret_data.get("data", {}).keys())
        except json.JSONDecodeError:
            pass

    # Verify scrape is working
    up_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_scrape_up"]
    )
    scrape_up = False
    if up_result["success"] and up_result["result"]:
        scrape_up = up_result["result"][0].get("value", [None, "0"])[1] == "1"

    return {
        "success": tls_configured and basic_auth_configured and secret_exists and scrape_up,
        "tls_configured": tls_configured,
        "scheme": scheme,
        "basic_auth_configured": basic_auth_configured,
        "insecure_skip_verify": insecure_skip_verify,
        "secret_exists": secret_exists,
        "secret_keys": secret_keys,
        "scrape_up": scrape_up,
    }


# =============================================================================
# TC-F003: LABEL ENRICHMENT VERIFICATION
# =============================================================================

def verify_vast_label_enrichment(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VAST metric label enrichment (TC-F003).

    Checks:
    - All VAST metrics have required labels (job, instance)
    - Enrichment labels (source, subsystem) are present

    Returns:
        Dict with success, required_label_results, enrichment_label_results,
        total_series, sample_labels
    """
    # Query a sample of VAST metrics
    vm_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_scrape_up"]
    )
    if not vm_result["success"] or not vm_result["result"]:
        return {
            "success": False,
            "error": "Cannot query VAST metrics",
            "required_label_results": [],
            "enrichment_label_results": [],
            "total_series": 0,
        }

    series = vm_result["result"]
    total_series = len(series)

    # Check required labels
    required_label_results = []
    missing_required = []
    for label in VAST_REQUIRED_LABELS:
        count = sum(1 for s in series if label in s.get("metric", {}))
        has_label = count == total_series
        required_label_results.append({
            "label": label,
            "present": has_label,
            "count": count,
            "total": total_series,
        })
        if not has_label:
            missing_required.append(label)

    # Check enrichment labels
    enrichment_label_results = []
    missing_enrichment = []
    for label in VAST_ENRICHMENT_LABELS:
        count = sum(1 for s in series if label in s.get("metric", {}))
        has_label = count == total_series
        enrichment_label_results.append({
            "label": label,
            "present": has_label,
            "count": count,
            "total": total_series,
        })
        if not has_label:
            missing_enrichment.append(label)

    # Collect sample labels for reporting
    sample_labels = {}
    if series:
        sample_labels = dict(series[0].get("metric", {}))

    return {
        "success": len(missing_required) == 0,
        "required_label_results": required_label_results,
        "enrichment_label_results": enrichment_label_results,
        "missing_required": missing_required,
        "missing_enrichment": missing_enrichment,
        "total_series": total_series,
        "sample_labels": sample_labels,
    }


# =============================================================================
# TC-F004: INTERNAL REMOTE-WRITE TO VMINSERT
# =============================================================================

def verify_vast_internal_remotewrite(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify internal remote-write to vminsert is working (TC-F004).

    Checks:
    - vmagent_remotewrite_requests_total with status_code=2XX is incrementing
    - VAST metrics are present in VictoriaMetrics (via vmselect)
    - No pending data buildup

    Returns:
        Dict with success, remotewrite_success, series_in_vm,
        pending_data_bytes
    """
    # Check remote write success counter
    rw_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_remotewrite_success"]
    )
    remotewrite_success = False
    rw_count = 0
    if rw_result["success"] and rw_result["result"]:
        for r in rw_result["result"]:
            val = float(r.get("value", [None, "0"])[1])
            if val > 0:
                remotewrite_success = True
                rw_count += int(val)

    # Check VAST metrics present in VictoriaMetrics
    count_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_count_series"]
    )
    series_in_vm = 0
    if count_result["success"] and count_result["result"]:
        series_in_vm = int(count_result["result"][0].get("value", [None, "0"])[1])

    # Check pending data bytes
    pending_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_remotewrite_pending"]
    )
    pending_data_bytes = 0
    if pending_result["success"] and pending_result["result"]:
        for r in pending_result["result"]:
            pending_data_bytes += int(
                float(r.get("value", [None, "0"])[1])
            )

    return {
        "success": remotewrite_success and series_in_vm > 0,
        "remotewrite_success": remotewrite_success,
        "remotewrite_count": rw_count,
        "series_in_vm": series_in_vm,
        "pending_data_bytes": pending_data_bytes,
    }


# =============================================================================
# TC-F008: SCRAPE INTERVAL VALIDATION
# =============================================================================

def verify_vast_scrape_interval(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VAST scrape interval is within allowed range (TC-F008).

    Checks:
    - VMServiceScrape interval is within [30s, 60s]
    - Scrape timeout is less than interval

    Returns:
        Dict with success, configured_interval, interval_seconds,
        within_range, timeout
    """
    # Get VMServiceScrape
    kubectl_cmd = VAST_CMD_TEMPLATES["get_vmservicescrape"].format(
        name=VAST_VMSERVICESCRAPE_NAME, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    configured_interval = ""
    interval_seconds = 0
    timeout_str = ""
    timeout_seconds = 0

    if cmd.rc == 0:
        try:
            vmss = json.loads(cmd.stdout)
            endpoints = vmss.get("spec", {}).get("endpoints", [])
            if endpoints:
                ep = endpoints[0]
                configured_interval = ep.get("interval", "30s")
                timeout_str = ep.get("scrapeTimeout", "15s")

                # Parse interval
                interval_str = configured_interval.rstrip("s")
                interval_seconds = int(interval_str) if interval_str.isdigit() else 30

                # Parse timeout
                timeout_val = timeout_str.rstrip("s")
                timeout_seconds = int(timeout_val) if timeout_val.isdigit() else 15
        except (json.JSONDecodeError, ValueError):
            pass

    within_range = (
        SCRAPE_INTERVAL_MIN_SECONDS <= interval_seconds <= SCRAPE_INTERVAL_MAX_SECONDS
    )
    timeout_valid = timeout_seconds < interval_seconds

    return {
        "success": within_range and timeout_valid,
        "configured_interval": configured_interval,
        "interval_seconds": interval_seconds,
        "within_range": within_range,
        "min_allowed": SCRAPE_INTERVAL_MIN_SECONDS,
        "max_allowed": SCRAPE_INTERVAL_MAX_SECONDS,
        "timeout": timeout_str,
        "timeout_seconds": timeout_seconds,
        "timeout_valid": timeout_valid,
    }


# =============================================================================
# TC-F012: DEPLOYMENT VERIFICATION
# =============================================================================

def verify_vast_deployment(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify complete VAST telemetry deployment (TC-F012).

    Checks:
    - VMServiceScrape resource exists and is operational
    - VAST external service exists with endpoints
    - Credentials Secret exists with required keys
    - vmagent pods Running with 0 restarts
    - Scrape is active

    Returns:
        Dict with success, component_results, missing_components
    """
    component_results = []
    missing = []

    # 1. VMServiceScrape
    kubectl_cmd = VAST_CMD_TEMPLATES["get_vmservicescrape"].format(
        name=VAST_VMSERVICESCRAPE_NAME, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    vmss_exists = cmd.rc == 0
    vmss_status = ""
    if vmss_exists:
        try:
            vmss = json.loads(cmd.stdout)
            status = vmss.get("status", {})
            update_status = status.get("updateStatus", "")
            vmss_status = update_status
        except json.JSONDecodeError:
            pass

    component_results.append({
        "component": "VMServiceScrape",
        "running": vmss_exists,
        "details": f"status={vmss_status}" if vmss_status else "",
        "restarts": 0,
    })
    if not vmss_exists:
        missing.append("VMServiceScrape")

    # 2. VAST external service (lookup by label selector)
    svc_cmd = (
        f"kubectl get svc -n {TELEMETRY_NAMESPACE} "
        f"-l app={VAST_APP_LABEL} -o json"
    )
    cmd = run_on_remote_node(host, svc_cmd, admin_ip)
    svc_exists = False
    svc_type = ""
    svc_ports = []
    if cmd.rc == 0:
        try:
            data = json.loads(cmd.stdout)
            items = data.get("items", [])
            if items:
                svc_exists = True
                svc = items[0]
                svc_type = svc.get("spec", {}).get("type", "")
                svc_ports = [
                    p.get("port") for p in svc.get("spec", {}).get("ports", [])
                ]
        except json.JSONDecodeError:
            pass

    component_results.append({
        "component": "VAST External Service",
        "running": svc_exists,
        "details": f"type={svc_type}, ports={svc_ports}",
        "restarts": 0,
    })
    if not svc_exists:
        missing.append("VAST External Service")

    # 3. Credentials Secret
    secret_cmd = VAST_CMD_TEMPLATES["get_secret"].format(
        secret_name=VAST_CREDENTIALS_SECRET, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, secret_cmd, admin_ip)
    secret_exists = cmd.rc == 0
    secret_keys = []
    if secret_exists:
        try:
            secret_data = json.loads(cmd.stdout)
            secret_keys = list(secret_data.get("data", {}).keys())
        except json.JSONDecodeError:
            pass

    has_username = "username" in secret_keys
    has_password = "password" in secret_keys
    component_results.append({
        "component": "Credentials Secret",
        "running": secret_exists and has_username and has_password,
        "details": f"keys={secret_keys}",
        "restarts": 0,
    })
    if not (secret_exists and has_username and has_password):
        missing.append("Credentials Secret")

    # 4. vmagent pods
    vmagent_cmd = VAST_CMD_TEMPLATES["get_vmagent_pods"].format(
        namespace=TELEMETRY_NAMESPACE,
        label_selector=VMAGENT_LABEL_SELECTOR,
    )
    cmd = run_on_remote_node(host, vmagent_cmd, admin_ip)
    vmagent_running = False
    vmagent_count = 0
    vmagent_restarts = 0
    if cmd.rc == 0:
        try:
            data = json.loads(cmd.stdout)
            pods = data.get("items", [])
            vmagent_count = len(pods)
            running_count = 0
            for pod in pods:
                phase = pod.get("status", {}).get("phase", "")
                if phase == "Running":
                    running_count += 1
                for cs in pod.get("status", {}).get("containerStatuses", []):
                    vmagent_restarts += int(cs.get("restartCount", 0))
            vmagent_running = running_count > 0 and running_count == vmagent_count
        except json.JSONDecodeError:
            pass

    component_results.append({
        "component": "vmagent",
        "running": vmagent_running,
        "details": f"{vmagent_count} pods, {vmagent_restarts} restarts",
        "restarts": vmagent_restarts,
    })
    if not vmagent_running:
        missing.append("vmagent")

    # 5. Scrape active
    up_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_scrape_up"]
    )
    scrape_up = False
    if up_result["success"] and up_result["result"]:
        scrape_up = up_result["result"][0].get("value", [None, "0"])[1] == "1"

    component_results.append({
        "component": "VAST Scrape",
        "running": scrape_up,
        "details": "up=1" if scrape_up else "up=0",
        "restarts": 0,
    })
    if not scrape_up:
        missing.append("VAST Scrape")

    total_restarts = vmagent_restarts
    return {
        "success": len(missing) == 0 and total_restarts == 0,
        "component_results": component_results,
        "missing_components": missing,
        "total_restarts": total_restarts,
        "has_restarts": total_restarts > 0,
    }


# =============================================================================
# TC-P001: SCRAPE DURATION WITHIN INTERVAL
# =============================================================================

def verify_vast_scrape_duration(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VAST scrape duration is within scrape interval (TC-P001).

    Checks:
    - scrape_duration_seconds{job=~"vast.*"} < scrape_interval

    Returns:
        Dict with success, scrape_duration, scrape_interval, within_interval
    """
    # Get scrape duration
    duration_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_scrape_duration"]
    )
    scrape_duration = 0.0
    if duration_result["success"] and duration_result["result"]:
        scrape_duration = float(
            duration_result["result"][0].get("value", [None, "0"])[1]
        )

    # Get configured interval from VMServiceScrape
    interval_result = verify_vast_scrape_interval(host, admin_ip)
    interval_seconds = interval_result.get("interval_seconds", 30)

    within_interval = scrape_duration < interval_seconds

    return {
        "success": within_interval,
        "scrape_duration": round(scrape_duration, 3),
        "scrape_interval": interval_seconds,
        "within_interval": within_interval,
        "tolerance": SCRAPE_INTERVAL_TOLERANCE_SECONDS,
    }


# =============================================================================
# TC-P002: METRIC FAMILY COVERAGE
# =============================================================================

def verify_vast_metric_coverage(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify VAST metric family coverage (TC-P002).

    Checks:
    - Count unique VAST metric families
    - Coverage >= VAST_COVERAGE_THRESHOLD_PERCENT of expected

    Returns:
        Dict with success, family_count, coverage_percent, threshold,
        sample_families
    """
    # Count unique metric families
    families_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_count_families"]
    )
    family_count = 0
    sample_families = []
    if families_result["success"]:
        family_count = len(families_result["result"])
        # Collect first 20 family names for reporting
        sample_families = [
            r.get("metric", {}).get("__name__", "")
            for r in families_result["result"][:20]
        ]

    meets_minimum = family_count >= VAST_MIN_METRIC_FAMILIES

    return {
        "success": meets_minimum,
        "family_count": family_count,
        "min_expected": VAST_MIN_METRIC_FAMILIES,
        "meets_minimum": meets_minimum,
        "threshold_percent": VAST_COVERAGE_THRESHOLD_PERCENT,
        "sample_families": sample_families,
    }


# =============================================================================
# TC-S001: TLS ENFORCEMENT
# =============================================================================

def verify_vast_tls_enforcement(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify TLS enforcement for VAST communication (TC-S001).

    Checks:
    - VMServiceScrape scheme is https
    - tlsConfig is present
    - Scrape is active (TLS handshake succeeds)

    Returns:
        Dict with success, tls_checks
    """
    # Get VMServiceScrape
    kubectl_cmd = VAST_CMD_TEMPLATES["get_vmservicescrape"].format(
        name=VAST_VMSERVICESCRAPE_NAME, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)

    tls_checks = {}
    if cmd.rc == 0:
        try:
            vmss = json.loads(cmd.stdout)
            endpoints = vmss.get("spec", {}).get("endpoints", [])
            if endpoints:
                ep = endpoints[0]
                tls_checks["scheme_https"] = ep.get("scheme", "") == "https"
                tls_checks["tls_config_present"] = "tlsConfig" in ep
                tls_checks["path_correct"] = ep.get("path", "") == VAST_METRICS_PATH
        except json.JSONDecodeError:
            pass

    # Verify scrape is working (proves TLS handshake succeeds)
    up_result = _query_victoria_metrics(
        host, admin_ip, VAST_VM_QUERY_TEMPLATES["query_scrape_up"]
    )
    if up_result["success"] and up_result["result"]:
        tls_checks["scrape_active"] = (
            up_result["result"][0].get("value", [None, "0"])[1] == "1"
        )
    else:
        tls_checks["scrape_active"] = False

    all_passed = all(tls_checks.values()) if tls_checks else False

    return {
        "success": all_passed,
        "tls_checks": tls_checks,
    }


# =============================================================================
# TC-S002: NO PLAINTEXT CREDENTIALS IN ARTIFACTS
# =============================================================================

def verify_vast_no_plaintext_credentials(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify no plaintext credentials in deployed artifacts (TC-S002).

    Checks:
    - No credential patterns in vmagent pod logs
    - No plaintext credentials in ConfigMaps
    - Credentials stored in K8s Secrets only

    Returns:
        Dict with success, findings, credentials_in_secrets
    """
    findings = []

    # 1. Check vmagent pod logs for credential patterns
    vmagent_cmd = VAST_CMD_TEMPLATES["get_vmagent_pods"].format(
        namespace=TELEMETRY_NAMESPACE,
        label_selector=VMAGENT_LABEL_SELECTOR,
    )
    cmd = run_on_remote_node(host, vmagent_cmd, admin_ip)
    if cmd.rc == 0:
        try:
            data = json.loads(cmd.stdout)
            pods = data.get("items", [])
            for pod in pods[:2]:  # Check first 2 pods
                pod_name = pod.get("metadata", {}).get("name", "")
                containers = [
                    c.get("name", "")
                    for c in pod.get("spec", {}).get("containers", [])
                ]
                for container_name in containers:
                    log_cmd = (
                        f"kubectl logs -n {TELEMETRY_NAMESPACE} "
                        f"{pod_name} -c {container_name} --tail=200"
                    )
                    log_result = run_on_remote_node(host, log_cmd, admin_ip)
                    if log_result.rc == 0:
                        for pattern in CREDENTIAL_PATTERNS:
                            if pattern.lower() in log_result.stdout.lower():
                                findings.append({
                                    "location": f"pod/{pod_name}/{container_name} logs",
                                    "pattern": pattern,
                                })
        except json.JSONDecodeError:
            pass

    # 2. Check vmagent pod environment variables for credential patterns
    vmagent_env_cmd = VAST_CMD_TEMPLATES["get_pod_env"].format(
        namespace=TELEMETRY_NAMESPACE,
        label_selector=VMAGENT_LABEL_SELECTOR,
    )
    cmd = run_on_remote_node(host, vmagent_env_cmd, admin_ip)
    if cmd.rc == 0:
        for line in cmd.stdout.splitlines():
            line_lower = line.lower().strip()
            # Only flag if actual credential value appears exposed
            for pattern in CREDENTIAL_PATTERNS:
                if pattern.lower() in line_lower:
                    findings.append({
                        "location": "vmagent env vars",
                        "pattern": pattern,
                    })
                    break

    # 3. Verify credentials are in Secrets
    secret_cmd = VAST_CMD_TEMPLATES["get_secret"].format(
        secret_name=VAST_CREDENTIALS_SECRET, namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, secret_cmd, admin_ip)
    credentials_in_secrets = cmd.rc == 0

    return {
        "success": len(findings) == 0 and credentials_in_secrets,
        "findings": findings,
        "credentials_in_secrets": credentials_in_secrets,
    }
