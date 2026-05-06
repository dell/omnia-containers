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
Vector Automation - Variables.

This module contains constants and configuration for Vector telemetry verification.
"""

# =============================================================================
# Vector Deployment Constants
# =============================================================================

VECTOR_DEPLOYMENT_NAME = "vector"
VECTOR_CONFIGMAP_NAME = "vector-config"
VECTOR_APP_LABEL = "app=vector"

# =============================================================================
# Vector Resource Specifications (from FS-VE-01)
# =============================================================================

VECTOR_RESOURCE_SPECS = {
    "replicas": 1,
    "memory_request": "512Mi",
    "memory_limit": "1Gi",
    "cpu_request": "250m",
    "cpu_limit": "1000m",
}

# =============================================================================
# Vector Kafka Topics
# =============================================================================

VECTOR_KAFKA_TOPICS = {
    "ldms": "ldms",
    "idrac": "idrac",
    "ome": "ome-telemetry",
    "mixed": "mixed-content",
    "dead_letter": "vector-dead-letter",
}

# =============================================================================
# VictoriaMetrics Endpoints
# =============================================================================

VICTORIA_METRICS_ENDPOINTS = {
    "vminsert": "vminsert:8480",
    "vmselect": "vmselect:8481",
}

# =============================================================================
# VictoriaLogs Endpoints
# =============================================================================

VICTORIA_LOGS_ENDPOINTS = {
    "vlinsert": "vlinsert:9481",
    "vlselect": "vlselect:9471",
}

# =============================================================================
# Vector Metrics Endpoint
# =============================================================================

VECTOR_METRICS_PORT = 9090
VECTOR_METRICS_PATH = "/metrics"

# =============================================================================
# Vector Self-Metrics (FS-VE-05)
# =============================================================================

VECTOR_SELF_METRICS = [
    "vector_processed_messages_total",
    "vector_failed_messages_total",
    "vector_bytes_processed",
    "vector_consumer_lag",
    "vector_error_count",
]

# =============================================================================
# Command Templates
# =============================================================================

VECTOR_CMD_TEMPLATES = {
    "get_pods": "kubectl get pods -n {namespace} -l {label} -o json",
    "get_deployment": "kubectl get deployment {name} -n {namespace} -o json",
    "get_configmap": "kubectl get configmap {name} -n {namespace} -o yaml",
    "get_pod_logs": "kubectl logs -n {namespace} {pod_name} --tail={lines}",
    "delete_pod": "kubectl delete pod {pod_name} -n {namespace}",
    "rollout_restart": "kubectl rollout restart deployment {name} -n {namespace}",
    "scale_deployment": "kubectl scale deployment {name} -n {namespace} --replicas={replicas}",
    "exec_in_pod": "kubectl exec {pod_name} -n {namespace} -- {command}",
}

# =============================================================================
# Test Message Templates
# =============================================================================

LDMS_METRIC_TEMPLATE = {
    "timestamp": None,
    "hostname": None,
    "plugin": "meminfo",
    "metric_name": "memory_used",
    "value": None,
    "namespace": "ldms",
}

IDRAC_EVENT_TEMPLATE = {
    "timestamp": None,
    "hostname": None,
    "event_type": "thermal_alert",
    "message": None,
    "source": "idrac",
}

# =============================================================================
# Latency Thresholds (from AC-9.1, NFR-9.2)
# =============================================================================

LATENCY_THRESHOLDS = {
    "ingestion_max_seconds": 120,  # 2 minutes (AC-9.1)
    "p99_max_seconds": 5,          # p99 < 5s (NFR-9.2)
    "p95_max_seconds": 3,          # p95 < 3s
    "p50_max_seconds": 1,          # p50 < 1s
}

# =============================================================================
# Performance Thresholds (from NFR-9.1, NFR-9.3)
# =============================================================================

PERFORMANCE_THRESHOLDS = {
    "min_throughput_msgs_per_sec": 100000,  # 100K msgs/s (NFR-9.1)
    "max_cpu_millicores": 1000,             # 1 core (NFR-9.3)
    "max_memory_gi": 1,                      # 1 Gi (NFR-9.3)
}

# =============================================================================
# Topic Discovery Timeout (from FS-VE-03)
# =============================================================================

TOPIC_DISCOVERY_TIMEOUT_SECONDS = 60  # 1 polling cycle

# =============================================================================
# Error Patterns for Log Analysis
# =============================================================================

ERROR_LOG_PATTERNS = [
    "error",
    "failed",
    "exception",
    "panic",
    "fatal",
]

CREDENTIAL_PATTERNS = [
    "-----BEGIN",
    "password=",
    "token=",
    "secret=",
    "key=",
]
