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
VictoriaMetrics Automation - Configuration Variables.

Contains all VictoriaMetrics related constants, ports, and command templates.
"""

from typing import Dict

from .idrac_telemetry_vars import TELEMETRY_VARS

# =============================================================================
# Config File Paths (from TELEMETRY_VARS - no duplication)
# =============================================================================

TELEMETRY_CONFIG_PATH = TELEMETRY_VARS["telemetry_config_path"]
IDRAC_TELEMETRY_REPORT_PATH = TELEMETRY_VARS["idrac_telemetry_report_path"]
BMC_GROUP_DATA_PATH = TELEMETRY_VARS["bmc_group_data_path"]


# =============================================================================
# VictoriaMetrics Deployment Modes
# =============================================================================

DEPLOYMENT_MODE_SINGLE = "single-node"
DEPLOYMENT_MODE_CLUSTER = "cluster"


# =============================================================================
# VictoriaMetrics Single-Node Constants
# =============================================================================

VICTORIA_SINGLE_NODE = {
    "statefulset_name": "victoria-metric",
    "service_name": "victoria-loadbalancer",
    "port": 8443,
    "app_label": "victoriametrics",
}


# =============================================================================
# VictoriaMetrics Cluster Constants
# =============================================================================

VICTORIA_CLUSTER = {
    "vmstorage": {
        "statefulset_name": "vmstorage",
        "service_name": "vmstorage",
        "replicas": 3,
        "port": 8482,
        "app_label": "vmstorage",
    },
    "vminsert": {
        "deployment_name": "vminsert",
        "service_name": "vminsert",
        "replicas": 2,
        "port": 8480,
        "app_label": "vminsert",
    },
    "vmselect": {
        "deployment_name": "vmselect",
        "service_name": "vmselect",
        "replicas": 2,
        "port": 8481,
        "app_label": "vmselect",
    },
}


# =============================================================================
# VMAgent Constants
# =============================================================================

VMAGENT = {
    "deployment_name": "vmagent",
    "app_label": "vmagent",
}


# =============================================================================
# TLS Secret
# =============================================================================

VICTORIA_TLS_SECRET = "victoria-tls-certs"
VICTORIA_TLS_SECRET_KEYS = ["tls.crt", "tls.key", "ca.crt"]


# =============================================================================
# VictoriaMetrics API Endpoints
# =============================================================================

VICTORIA_API_ENDPOINTS = {
    "health": "/health",
    "metrics": "/metrics",
    # Single-node API paths
    "single_query": "/api/v1/query",
    "single_label_values": "/api/v1/label/__name__/values",
    # Cluster API paths (vmselect)
    "cluster_query": "/select/0/prometheus/api/v1/query",
    "cluster_label_values": "/select/0/prometheus/api/v1/label/__name__/values",
}


# =============================================================================
# VictoriaMetrics Command Templates
# =============================================================================

VICTORIA_CMD_TEMPLATES: Dict[str, str] = {
    # Get pods by label
    "get_pods_by_label": (
        "kubectl get pods -n {namespace} -l app={app_label} -o json"
    ),

    # Get service external IP
    "get_service_external_ip": (
        "kubectl get svc {service_name} -n {namespace} "
        "-o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'"
    ),

    # Get service port
    "get_service_port": (
        "kubectl get svc {service_name} -n {namespace} "
        "-o jsonpath='{{.spec.ports[0].port}}'"
    ),

    # Get secret
    "get_secret": (
        "kubectl get secret {secret_name} -n {namespace} -o json"
    ),

    # Get PVC storage size
    "get_pvc_storage": (
        "kubectl get pvc {pvc_name} -n {namespace} "
        "-o jsonpath='{{.spec.resources.requests.storage}}'"
    ),

    # Get all PVCs for a statefulset
    "get_statefulset_pvcs": (
        "kubectl get pvc -n {namespace} -l app={app_label} -o json"
    ),

    # Curl with TLS (using CA cert from secret)
    "curl_with_tls": (
        "curl -s --max-time 30 --cacert /tmp/ca.crt "
        "https://{host}:{port}{endpoint}"
    ),

    # Get CA cert from secret and save to file
    "extract_ca_cert": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d"
    ),

    # Query VictoriaMetrics API
    "query_metrics": (
        "curl -s --max-time 30 --cacert /tmp/ca.crt "
        "'https://{host}:{port}{endpoint}?query={query}'"
    ),
}
