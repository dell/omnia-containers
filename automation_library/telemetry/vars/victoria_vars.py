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

IDRAC_TELEMETRY_REPORT_PATH = TELEMETRY_VARS["idrac_telemetry_report_path"]
BMC_GROUP_DATA_PATH = TELEMETRY_VARS["bmc_group_data_path"]


# =============================================================================
# VictoriaMetrics Cluster Constants
# =============================================================================

VICTORIA_CLUSTER = {
    "vmstorage": {
        "statefulset_name": "vmstorage-victoria-cluster",
        "service_name": "vmstorage-victoria-cluster",
        "replicas": 3,
        "port": 8482,
        "app_label": "vmstorage",
        "label_selector": "app.kubernetes.io/name=vmstorage,app.kubernetes.io/instance=victoria-cluster",
    },
    "vminsert": {
        "deployment_name": "vminsert-victoria-cluster",
        "service_name": "vminsert-victoria-cluster",
        "replicas": 2,
        "port": 8480,
        "app_label": "vminsert",
        "label_selector": "app.kubernetes.io/name=vminsert,app.kubernetes.io/instance=victoria-cluster",
    },
    "vmselect": {
        "deployment_name": "vmselect-victoria-cluster",
        "service_name": "vmselect-victoria-cluster",
        "replicas": 2,
        "port": 8481,
        "app_label": "vmselect",
        "label_selector": "app.kubernetes.io/name=vmselect,app.kubernetes.io/instance=victoria-cluster",
    },
}


# =============================================================================
# VMAgent Constants
# =============================================================================

VMAGENT = {
    "deployment_name": "vmagent-vmagent",
    "app_label": "vmagent",
    "label_selector": "app.kubernetes.io/name=vmagent,app.kubernetes.io/instance=vmagent",
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
    "query": "/select/0/prometheus/api/v1/query",
    "label_values": "/select/0/prometheus/api/v1/label/__name__/values",
}


# =============================================================================
# VictoriaMetrics Command Templates
# =============================================================================

VICTORIA_CMD_TEMPLATES: Dict[str, str] = {
    # Get pods by label (uses label_selector for vm-operator managed pods)
    "get_pods_by_label": (
        "kubectl get pods -n {namespace} -l {label_selector} -o json"
    ),

    # Get service external IP
    "get_service_external_ip": (
        "kubectl get svc {service_name} -n {namespace} "
        "-o jsonpath={{.status.loadBalancer.ingress[0].ip}}"
    ),

    # Get service port
    "get_service_port": (
        "kubectl get svc {service_name} -n {namespace} "
        "-o jsonpath={{.spec.ports[0].port}}"
    ),

    # Get secret
    "get_secret": (
        "kubectl get secret {secret_name} -n {namespace} -o json"
    ),

    # Get PVC storage size
    "get_pvc_storage": (
        "kubectl get pvc {pvc_name} -n {namespace} "
        "-o jsonpath={{.spec.resources.requests.storage}}"
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
