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
VictoriaLogs Automation - Configuration Variables.

Contains all VictoriaLogs cluster constants, ports, service names,
and kubectl command templates.

VictoriaLogs cluster is always deployed in cluster mode (VLCluster CR)
alongside VictoriaMetrics when any source targets 'victoria_logs'.

Components (operator-managed via VLCluster CR named 'victoria-logs-cluster'):
  - vlstorage  : StatefulSet, 3 replicas, port 9491 (internal)
  - vlinsert   : Deployment, 2 replicas, port 9481 (LoadBalancer)
  - vlselect   : Deployment, 2 replicas, port 9471 (LoadBalancer)
  - vlagent    : Deployment, 1 replica  (VLAgent CR, syslog receiver + forwarder)
"""

from typing import Dict


# =============================================================================
# VLCluster CR Name
# =============================================================================

VLCLUSTER_NAME = "victoria-logs-cluster"


# =============================================================================
# vlstorage - Persistent log storage (StatefulSet, internal only)
# =============================================================================

VLSTORAGE = {
    "statefulset_name": f"vlstorage-{VLCLUSTER_NAME}",
    "service_name": f"vlstorage-{VLCLUSTER_NAME}",
    "replicas": 3,
    "port": 9491,
    "app_label": "vlstorage",
    "pvc_prefix": "vlstorage-data",
}


# =============================================================================
# vlinsert - Log ingestion gateway (Deployment, LoadBalancer)
# =============================================================================

VLINSERT = {
    "deployment_name": f"vlinsert-{VLCLUSTER_NAME}",
    "service_name": f"vlinsert-{VLCLUSTER_NAME}",
    "replicas": 2,
    "port": 9481,
    "app_label": "vlinsert",
}


# =============================================================================
# vlselect - Log query gateway (Deployment, LoadBalancer)
# =============================================================================

VLSELECT = {
    "deployment_name": f"vlselect-{VLCLUSTER_NAME}",
    "service_name": f"vlselect-{VLCLUSTER_NAME}",
    "replicas": 2,
    "port": 9471,
    "app_label": "vlselect",
}


# =============================================================================
# VLAgent - Platform-managed log forwarding agent (VLAgent CR)
# Provides syslog reception and remoteWrite forwarding to vlinsert
# =============================================================================

VLAGENT_LOGS = {
    "deployment_name": "vlagent",
    "service_name": "vlagent-vlagent",  # operator prefixes CR name: <cr>-<cr>
    "app_label": "vlagent",             # used as app.kubernetes.io/name=vlagent
    "component_label": "victorialogs",
    "syslog_port_tcp": 514,
    "syslog_port_udp": 514,
    "syslog_tls_port": 6514,
    "health_port": 9429,
}


# VLAgent configuration ConfigMap name
# Contains syslog receiver + remoteWrite pipeline config (victorialogs-vlagent-config.yaml.j2)
VLAGENT_CONFIGMAP_NAME = "vlagent-config"

# Ports exposed on the VLAgent K8s Service (LoadBalancer via MetalLB).
# serviceSpec patched to LoadBalancer type with syslog ports added.
# 514  - syslog plaintext (TCP + UDP)
# 9429 - health/metrics endpoint
VLAGENT_EXPECTED_PORTS = [514, 9429]

# Syslog injection test constants
# Used when there are no real data sources (PowerScale / UFM / Skyview)
# to exercise the VLAgent syslog → VictoriaLogs end-to-end path
VLAGENT_SYSLOG_TEST_TAG = "omnia-vllogs-test"
VLAGENT_SYSLOG_INGESTION_WAIT_SECS = 15  # seconds to wait for VLAgent to batch and forward

# TC14/TC15 - stream label and field-filter tests
VLAGENT_STREAM_TEST_TAG = "omnia-vllogs-stream"
VLAGENT_FIELD_TEST_TAG = "omnia-vllogs-field"

# TC16 - direct vlinsert write
VLINSERT_DIRECT_TEST_JOB = "omnia-direct-test"

# TC22 - pod restart test
VLAGENT_RESTART_TEST_TAG = "omnia-vllogs-restart"
VLAGENT_POD_READY_TIMEOUT_SECS = 120

# TC23 - multi-message ingestion
VLAGENT_MULTI_MSG_COUNT = 3

# TC24 - query response time threshold (seconds)
VLSELECT_QUERY_RESPONSE_MAX_SECS = 5.0

# TC25 - bulk ingestion
VLAGENT_BULK_COUNT = 50
VLAGENT_BULK_TAG = "omnia-vllogs-bulk"
VLAGENT_BULK_WAIT_SECS = 25

# TC26 - TLS cert minimum validity (7 days)
TLS_CERT_MIN_VALID_SECS = 604800

# TC28 - RBAC: default service account should NOT read the TLS secret
VLAGENT_RBAC_SERVICE_ACCOUNT = "system:serviceaccount:telemetry:default"


# =============================================================================
# TLS Secret (shared with VictoriaMetrics)
# =============================================================================

VICTORIA_LOGS_TLS_SECRET = "victoria-tls-certs"
VICTORIA_LOGS_TLS_SECRET_KEYS = ["tls.crt", "tls.key", "ca.crt"]


# =============================================================================
# VictoriaLogs API Endpoints (vlselect query gateway)
# =============================================================================

VICTORIA_LOGS_API_ENDPOINTS: Dict[str, str] = {
    "health": "/health",
    "streams": "/select/logsql/stats/streams",
    "query": "/select/logsql/query",
}


# =============================================================================
# VictoriaLogs Command Templates
# =============================================================================

VICTORIA_LOGS_CMD_TEMPLATES: Dict[str, str] = {
    # Get pods by app label (VictoriaMetrics operator uses app.kubernetes.io/name=)
    "get_pods_by_label": (
        "kubectl get pods -n {namespace} "
        "-l 'app.kubernetes.io/name={app_label}' -o json"
    ),

    # Get service external IP (LoadBalancer ingress)
    "get_service_external_ip": (
        "kubectl get svc {service_name} -n {namespace} "
        "-o jsonpath={{.status.loadBalancer.ingress[0].ip}}"
    ),

    # Get service port
    "get_service_port": (
        "kubectl get svc {service_name} -n {namespace} "
        "-o jsonpath={{.spec.ports[0].port}}"
    ),

    # Get secret as JSON
    "get_secret": (
        "kubectl get secret {secret_name} -n {namespace} -o json"
    ),

    # Get all PVCs for a given app label
    # VictoriaMetrics operator sets app.kubernetes.io/name on PVCs
    "get_statefulset_pvcs": (
        "kubectl get pvc -n {namespace} "
        "-l 'app.kubernetes.io/name={app_label}' -o json"
    ),

    # Get ConfigMap as JSON
    "get_configmap": (
        "kubectl get configmap {configmap_name} -n {namespace} -o json"
    ),

    # Get Service as JSON (for port and type inspection)
    "get_service_json": (
        "kubectl get svc {service_name} -n {namespace} -o json"
    ),

    # Get the first pod IP for a given app label
    # Used as fallback when no LoadBalancer IP is available (NodePort service)
    "get_pod_ip": (
        "kubectl get pods -n {namespace} "
        "-l 'app.kubernetes.io/name={app_label}' "
        "-o jsonpath='{{.items[0].status.podIP}}'"
    ),

    # Inject a synthetic RFC 3164 syslog message to VLAgent via TCP (port 514)
    # Uses logger (util-linux), available by default on RHEL/CentOS/Rocky
    # -T forces TCP (default is UDP; TCP is more reliable for remote hosts)
    "inject_syslog": (
        "logger -n {vlagent_ip} -P {port} -T -t {tag} -- {message}"
    ),

    # UDP syslog injection (fallback if TCP fails)
    "inject_syslog_udp": (
        "logger -n {vlagent_ip} -P {port} -d -t {tag} -- {message}"
    ),

    # Sleep N seconds (used between syslog injection and verification)
    "sleep": "sleep {seconds}",

    # Query VictoriaLogs via vlselect LogsQL endpoint with TLS
    "curl_logsql_query": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s --max-time 30 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "'https://{service_dns}:{port}/select/logsql/query"
        "?query={query}&start=now-5m&limit=10'; echo"
    ),

    # Extract CA cert from TLS secret to /tmp/ca.crt and curl endpoint
    # Uses --resolve to map service DNS name to LoadBalancer IP for TLS verification
    "curl_with_tls": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s --max-time 30 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "https://{service_dns}:{port}{endpoint}; echo"
    ),

    # Extract CA cert and curl a full URL (for query endpoints with params)
    "curl_query": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s --max-time 30 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "'{url}'; echo"
    ),

    # --- TC13: ConfigMap content ---
    # Get raw ConfigMap data keys and values
    "get_configmap_data": (
        "kubectl get configmap {configmap_name} -n {namespace} "
        "-o jsonpath='{{.data}}'"
    ),

    # --- TC14/TC15: stream labels + field-filter query ---
    # LogsQL query with field filter (e.g., app_name="omnia-vllogs-test")
    "curl_logsql_field_query": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s --max-time 30 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "'https://{service_dns}:{port}/select/logsql/query"
        "?query={query}&start=now-10m&limit=20'; echo"
    ),

    # --- TC16: vlinsert direct HTTP POST ---
    "curl_vlinsert_post": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s -o /tmp/vlinsert_resp.txt -w '%{{http_code}}' "
        "--max-time 15 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "-X POST -H 'Content-Type: application/stream+json' "
        "-d '{{\"_msg\":\"{message}\",\"job\":\"{job}\"}}' "
        "'https://{service_dns}:{port}/insert/jsonline'; echo"
    ),

    # --- TC17: retention period in pod args ---
    "get_pod_args": (
        "kubectl get pods -n {namespace} "
        "-l 'app.kubernetes.io/name={app_label}' "
        "-o jsonpath='{{.items[0].spec.containers[0].args}}'"
    ),

    # --- TC18: invalid LogsQL query → 4xx ---
    "curl_logsql_status_code": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s -o /dev/null -w '%{{http_code}}' "
        "--max-time 15 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "'https://{service_dns}:{port}/select/logsql/query"
        "?query={query}&start=now-5m'; echo"
    ),

    # --- TC20: plain HTTP to TLS-only port → rejected ---
    "curl_plain_http": (
        "curl -s -o /dev/null -w '%{{http_code}}' "
        "--max-time 10 "
        "'http://{service_ip}:{port}{endpoint}'; echo"
    ),

    # --- TC21: wrong CA cert → TLS failure ---
    "curl_wrong_ca": (
        "echo 'invalid-ca' > /tmp/wrong_ca.crt && "
        "curl -s -o /dev/null -w '%{{http_code}}' "
        "--max-time 10 --cacert /tmp/wrong_ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "'https://{service_dns}:{port}{endpoint}'; echo"
    ),

    # --- TC22: pod restart (delete pod, StatefulSet recreates it) ---
    "delete_pod_by_label": (
        "kubectl delete pod -n {namespace} "
        "-l 'app.kubernetes.io/name={app_label}' --wait=false"
    ),
    "wait_pod_ready": (
        "kubectl wait pod -n {namespace} "
        "-l 'app.kubernetes.io/name={app_label}' "
        "--for=condition=Ready --timeout={timeout}s"
    ),

    # --- TC24: query response time ---
    "curl_timed": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s -o /dev/null -w '%{{time_total}}' "
        "--max-time 30 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "'https://{service_dns}:{port}{endpoint}?{params}'; echo"
    ),

    # --- TC25: bulk syslog injection via shell loop (TCP) ---
    "inject_syslog_bulk": (
        "for i in $(seq 1 {count}); do "
        "logger -n {vlagent_ip} -P {port} -T -t {tag} -- {prefix}$i; "
        "done"
    ),

    # --- TC25: bulk syslog injection via shell loop (UDP, faster) ---
    "inject_syslog_bulk_udp": (
        "for i in $(seq 1 {count}); do "
        "logger -n {vlagent_ip} -P {port} -d -t {tag} -- {prefix}$i; "
        "done"
    ),

    # LogsQL query returning raw response (for bulk count)
    "curl_logsql_count_query": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s --max-time 30 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "'https://{service_dns}:{port}/select/logsql/query"
        "?query={query}&start=now-10m&limit={limit}'; echo"
    ),

    # --- TC26: TLS certificate expiry check ---
    "check_cert_expiry": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.tls\\.crt}}' | base64 -d | "
        "openssl x509 -noout -checkend {seconds} 2>&1; echo rc=$?"
    ),

    # --- TC27: VLAgent PVC mounted in pod ---
    "get_pod_volumes": (
        "kubectl get pods -n {namespace} "
        "-l 'app.kubernetes.io/name={app_label}' "
        "-o jsonpath='{{.items[0].spec.volumes[*].name}}'"
    ),

    # --- TC28: RBAC check ---
    "auth_can_i": (
        "kubectl auth can-i {verb} {resource} "
        "-n {namespace} --as={service_account}"
    ),

    # --- TC29: pod security context ---
    "get_pod_security_context": (
        "kubectl get pods -n {namespace} "
        "-l 'app.kubernetes.io/name={app_label}' "
        "-o json"
    ),

    # --- Cleanup/Retention: ingest JSON line directly ---
    "curl_ingest_jsonline": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s -o /dev/null -w '%{{http_code}}' "
        "--max-time 15 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "-X POST -H 'Content-Type: application/stream+json' "
        "-d '{data}' "
        "'https://{service_dns}:{port}/insert/jsonline'; echo"
    ),

    # --- TC-F006: health check during outage ---
    "curl_health": (
        "kubectl get secret {secret_name} -n {namespace} "
        "-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
        "curl -s -o /dev/null -w '%{{http_code}}' "
        "--max-time 15 --cacert /tmp/ca.crt "
        "--resolve {service_dns}:{port}:{external_ip} "
        "'https://{service_dns}:{port}/health'; echo"
    ),
}
