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
PowerScale Telemetry Automation - Configuration Variables.

Contains all PowerScale telemetry related constants, pod labels, metric names,
and command templates used for verifying PowerScale storage telemetry deployment.
"""

from typing import Dict, List


# =============================================================================
# PowerScale Deployment Modes
# =============================================================================

DEPLOYMENT_MODE_OMNIA = "omnia-orchestrated"
DEPLOYMENT_MODE_OPERATOR = "operator-provided"


# =============================================================================
# PowerScale Pod Constants
# =============================================================================

CSM_METRICS_POWERSCALE = {
    "k8s_app_name": "karavi-metrics-powerscale",
    "app_label": "karavi-metrics-powerscale",
    "component": "CSM Metrics for PowerScale",
    "label_selector": "app.kubernetes.io/name=karavi-metrics-powerscale",
}

OTEL_COLLECTOR = {
    "k8s_app_name": "otel-collector",
    "app_label": "otel-collector",
    "component": "OpenTelemetry Collector",
    "label_selector": "app.kubernetes.io/name=otel-collector",
    "prometheus_port": 8889,
    "grpc_port": 55680,
}

CERT_MANAGER = {
    "namespace": "telemetry",
    "app_label": "cert-manager",
    "component": "cert-manager",
    "label_selector": "app=cert-manager",
}

CSI_DRIVER_POWERSCALE = {
    "driver_name": "csi-isilon.dellemc.com",
    "component": "CSI Driver for Dell PowerScale",
}

VLAGENT = {
    "k8s_app_name": "vlagent",
    "app_label": "vlagent",
    "component": "VLAgent",
    "label_selector": "app.kubernetes.io/name=vlagent",
}


# =============================================================================
# PowerScale Scrape Interval Limits
# =============================================================================

SCRAPE_INTERVAL_MIN_SECONDS = 30
SCRAPE_INTERVAL_MAX_SECONDS = 60
SCRAPE_INTERVAL_DEFAULT = "30s"
SCRAPE_INTERVAL_TOLERANCE_SECONDS = 5


# =============================================================================
# PowerScale Metric Categories
# =============================================================================

POWERSCALE_METRIC_CATEGORIES: Dict[str, str] = {
    "performance": "powerscale_cluster_(cpu_use_rate|disk_read_operation_rate|disk_write_operation_rate|disk_throughput_read_rate_megabytes_per_second|disk_throughput_write_rate_megabytes_per_second)",
    "capacity": "powerscale_cluster_(remaining_capacity_terabytes|total_capacity_terabytes|used_capacity_percentage)",
    "quota": "powerscale_(directory_total_hard_quota.*|volume_hard_quota.*|volume_quota_subscribed.*)",
    "topology": "karavi_topology_metrics",
}

POWERSCALE_REQUIRED_LABELS: List[str] = [
    "otel_scope_name",
    "StorageSystem",
]

POWERSCALE_PROTOCOL_LABELS: List[str] = [
    "NFS",
    "SMB",
    "S3",
]


# =============================================================================
# PowerScale Health Metrics
# =============================================================================

POWERSCALE_HEALTH_METRICS: List[str] = [
    "up",
    "scrape_samples_scraped",
    "scrape_duration_seconds",
    "scrape_series_added",
]


# =============================================================================
# Credential Patterns for Security Test (TC-S002)
# =============================================================================

CREDENTIAL_PATTERNS: List[str] = [
    "-----BEGIN",
    "password=",
    "token=",
    "secret=",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN PRIVATE KEY",
    "BEGIN CERTIFICATE",
]


# =============================================================================
# PowerScale Command Templates
# =============================================================================

POWERSCALE_CMD_TEMPLATES: Dict[str, str] = {
    # Get pods by label in namespace (supports both label styles)
    "get_pods_by_label": (
        "kubectl get pods -n {namespace} -l {label_selector} -o json"
    ),

    # Get pods by app.kubernetes.io/name label
    "get_pods_by_k8s_name": (
        "kubectl get pods -n {namespace} -l app.kubernetes.io/name={k8s_app_name} -o json"
    ),

    # Get pods by app= label
    "get_pods_by_app": (
        "kubectl get pods -n {namespace} -l app={app_label} -o json"
    ),

    # Get all pods in namespace
    "get_all_pods": (
        "kubectl get pods -n {namespace} -o json"
    ),

    # Get pods in a specific namespace
    "get_pods_namespace": (
        "kubectl get pods -n {namespace} -o json"
    ),

    # Get CSI drivers
    "get_csi_drivers": (
        "kubectl get csidrivers -o json"
    ),

    # Get certificates in namespace
    "get_certificates": (
        "kubectl get certificates -n {namespace} -o json"
    ),

    # Get pod logs
    "get_pod_logs": (
        "kubectl logs -n {namespace} {pod_name} --tail={tail_lines}"
    ),

    # Get pod restart count
    "get_pod_restart_count": (
        "kubectl get pods -n {namespace} -l {label_selector} "
        "-o jsonpath='{{range .items[*]}}{{.status.containerStatuses[0].restartCount}}{{\"\\n\"}}{{end}}'"
    ),

    # Delete a pod (for failure recovery tests)
    "delete_pod": (
        "kubectl delete pod {pod_name} -n {namespace}"
    ),

    # Get configmap
    "get_configmap": (
        "kubectl get configmap {configmap_name} -n {namespace} -o yaml"
    ),

    # Get services
    "get_services": (
        "kubectl get svc -n {namespace} -o json"
    ),

    # Get secrets in namespace
    "get_secrets": (
        "kubectl get secrets -n {namespace} -o json"
    ),

    # Get deployment manifest
    "get_deployment": (
        "kubectl get deployment {deployment_name} -n {namespace} -o yaml"
    ),

    # Get configmaps in namespace
    "get_configmaps": (
        "kubectl get configmaps -n {namespace} -o yaml"
    ),

    # Get pod environment variables
    "get_pod_env": (
        "kubectl get pods -n {namespace} -l {label_selector} "
        "-o jsonpath='{{range .items[*].spec.containers[*].env[*]}}{{.name}}={{.value}}{{\"\\n\"}}{{end}}'"
    ),

    # Curl OTel Collector metrics endpoint (HTTP on ClusterIP)
    "curl_otel_metrics": (
        "curl -s --max-time 30 http://{host}:{port}/metrics"
    ),

    # Curl OTel Collector metrics endpoint (HTTPS fallback)
    "curl_otel_metrics_https": (
        "curl -sk --max-time 30 https://{host}:{port}/metrics"
    ),

    # Get service external IP (single quotes prevent shell brace expansion)
    "get_service_external_ip": (
        "kubectl get svc {service_name} -n {namespace} "
        "-o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'"
    ),

    # Get vmagent scrape config
    "get_vmagent_config": (
        "kubectl get configmap vmagent-config -n {namespace} -o yaml"
    ),

    # Apply network policy (for negative tests)
    "apply_network_policy": (
        "kubectl apply -f - <<EOF\n"
        "apiVersion: networking.k8s.io/v1\n"
        "kind: NetworkPolicy\n"
        "metadata:\n"
        "  name: {policy_name}\n"
        "  namespace: {namespace}\n"
        "spec:\n"
        "  podSelector:\n"
        "    matchLabels:\n"
        "      app: {app_label}\n"
        "  policyTypes:\n"
        "  - Ingress\n"
        "  ingress: []\n"
        "EOF"
    ),

    # Delete network policy
    "delete_network_policy": (
        "kubectl delete networkpolicy {policy_name} -n {namespace} --ignore-not-found"
    ),

    # Get pods on a specific node
    "get_pods_on_node": (
        "kubectl get pods -n {namespace} -o wide --field-selector spec.nodeName={node_name}"
    ),

    # Get worker nodes
    "get_worker_nodes": (
        "kubectl get nodes -l node-role.kubernetes.io/worker= -o json"
    ),
}


# =============================================================================
# VictoriaMetrics Query Templates (reuse from victoria_vars)
# =============================================================================

POWERSCALE_VM_QUERY_TEMPLATES: Dict[str, str] = {
    # Query for metric category
    "query_metric_category": '{{__name__=~"{pattern}"}}',

    # Query for scrape up status (OTel Collector job)
    "query_scrape_up": 'up{job="otel-collector"}',

    # Query for scrape metrics
    "query_scrape_metrics": 'scrape_samples_scraped{job="otel-collector"}',

    # Query for all powerscale metrics
    "query_all_powerscale": '{__name__=~"powerscale_.*"}',

    # Query for all karavi metrics
    "query_all_karavi": '{__name__=~"karavi_.*"}',

    # Query for specific metric
    "query_metric": '{metric_name}',
}


# =============================================================================
# VictoriaLogs Query Templates
# =============================================================================

POWERSCALE_VL_QUERY_TEMPLATES: Dict[str, str] = {
    # Query for powerscale syslog events
    "query_syslog_events": '_stream:{{host=~".*powerscale.*"}}',
}


# =============================================================================
# Retry Constants
# =============================================================================

POD_RESTART_WAIT_SECONDS = 30
POD_RESTART_MAX_RETRIES = 10
SCRAPE_WAIT_MULTIPLIER = 2  # Wait N * scrape_interval for data
SYSLOG_MAX_WAIT_SECONDS = 60
