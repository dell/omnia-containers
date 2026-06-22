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
UFM InfiniBand Telemetry Automation - Configuration Variables.

Contains all UFM telemetry related constants, pod labels, metric names,
and command templates used for verifying UFM InfiniBand telemetry deployment.

UFM DATA PIPELINE:
  Metrics: UFM Prometheus Exporter (HTTPS) → vmagent(shared) → victoria_metrics
  Logs:    UFM Syslog (UDP 514) → VLAgent → VictoriaLogs
"""

from typing import Dict, List


# =============================================================================
# UFM Scrape Job Constants
# =============================================================================

UFM_JOB_PATTERN = "ufm.*"
UFM_SCRAPE_JOB = "ufm-external"
UFM_CREDENTIALS_SECRET = "ufm-telemetry-credentials"
UFM_SERVICE_NAME = "ufm-external"
UFM_APP_LABEL = "ufm-external"
UFM_VMSERVICESCRAPE_NAME = "ufm-infiniband-metrics"


# =============================================================================
# UFM Scrape Interval Limits
# =============================================================================

SCRAPE_INTERVAL_MIN_SECONDS = 15
SCRAPE_INTERVAL_MAX_SECONDS = 60
SCRAPE_INTERVAL_DEFAULT = "30s"
SCRAPE_TIMEOUT_DEFAULT = "15s"
SCRAPE_INTERVAL_TOLERANCE_SECONDS = 5


# =============================================================================
# Kubernetes Label Selectors (for service/pod discovery)
# =============================================================================

VMSELECT_LABEL_SELECTOR = "app.kubernetes.io/name=vmselect"
VMAGENT_LABEL_SELECTOR = "app.kubernetes.io/name=vmagent"


# =============================================================================
# UFM Metric Endpoint
# =============================================================================

UFM_METRICS_PATH = "/prometheusmetrics"
UFM_METRICS_PORT = 9001
UFM_METRICS_SCHEME = "https"


# =============================================================================
# UFM Required Labels (on scraped metrics)
# =============================================================================

UFM_REQUIRED_LABELS: List[str] = [
    "job",
    "instance",
]

UFM_ENRICHMENT_LABELS: List[str] = [
    "source",
    "cluster",
]


# =============================================================================
# UFM Health Metrics (exposed by vmagent for UFM scrape)
# =============================================================================

UFM_HEALTH_METRICS: List[str] = [
    "up",
    "scrape_samples_scraped",
    "scrape_duration_seconds",
    "scrape_series_added",
]


# =============================================================================
# UFM Metric Family Coverage
# =============================================================================

UFM_MIN_METRIC_FAMILIES = 50
UFM_COVERAGE_THRESHOLD_PERCENT = 90


# =============================================================================
# UFM Syslog Constants
# =============================================================================

UFM_SYSLOG_PORT = 514
UFM_SYSLOG_PROTOCOL = "udp"
UFM_SYSLOG_SOURCE_LABEL = "ufm"


# =============================================================================
# UFM Credential Patterns (for security tests)
# =============================================================================

CREDENTIAL_PATTERNS: List[str] = [
    "password=",
    "token=",
    "secret=",
    "Authorization:",
    "Basic ",
]


# =============================================================================
# UFM Scrape Latency Thresholds (NFR)
# =============================================================================

SCRAPE_LATENCY_P99_MAX_SECONDS = 5.0
SCRAPE_DURATION_SAMPLE_COUNT = 10


# =============================================================================
# UFM Command Templates
# =============================================================================

UFM_CMD_TEMPLATES: Dict[str, str] = {
    # Get VMServiceScrape resource
    "get_vmservicescrape": (
        "kubectl get vmservicescrapes.operator.victoriametrics.com "
        "{name} -n {namespace} -o json"
    ),

    # Get pods by label in namespace
    "get_pods_by_label": (
        "kubectl get pods -n {namespace} -l {label_selector} -o json"
    ),

    # Get service by name
    "get_service": (
        "kubectl get svc {service_name} -n {namespace} -o json"
    ),

    # Get endpoints for a service
    "get_endpoints": (
        "kubectl get endpoints {service_name} -n {namespace} -o json"
    ),

    # Get secret
    "get_secret": (
        "kubectl get secret {secret_name} -n {namespace} -o json"
    ),

    # Get vmagent pods
    "get_vmagent_pods": (
        "kubectl get pods -n {namespace} -l {label_selector} -o json"
    ),

    # Get pod logs
    "get_pod_logs": (
        "kubectl logs -n {namespace} {pod_name} --tail={tail_lines}"
    ),

    # Get configmap
    "get_configmap": (
        "kubectl get configmap {configmap_name} -n {namespace} -o yaml"
    ),

    # Get service external IP
    "get_service_external_ip": (
        "kubectl get svc {service_name} -n {namespace} "
        "-o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'"
    ),

    # Get all configmaps in namespace (for credential search)
    "get_configmaps": (
        "kubectl get configmaps -n {namespace} -o yaml"
    ),

    # Get all secrets in namespace
    "get_secrets": (
        "kubectl get secrets -n {namespace} -o json"
    ),

    # Get pod environment variables
    "get_pod_env": (
        "kubectl get pods -n {namespace} -l {label_selector} "
        "-o jsonpath='{{range .items[*].spec.containers[*].env[*]}}{{.name}}={{.value}}{{\"\\n\"}}{{end}}'"
    ),
}


# =============================================================================
# VictoriaMetrics Query Templates for UFM
# =============================================================================

UFM_VM_QUERY_TEMPLATES: Dict[str, str] = {
    # Scrape up status
    "query_scrape_up": 'up{job=~"ufm.*"}',

    # Count all UFM metric series
    "query_count_series": 'count({job=~"ufm.*"})',

    # Count unique metric families
    "query_count_families": 'count by (__name__) ({job=~"ufm.*"})',

    # Scrape duration
    "query_scrape_duration": 'scrape_duration_seconds{job=~"ufm.*"}',

    # Scrape samples scraped
    "query_scrape_samples": 'scrape_samples_scraped{job=~"ufm.*"}',

    # Remote write success
    "query_remotewrite_success": (
        'vmagent_remotewrite_requests_total{status_code="2XX"}'
    ),

    # Remote write pending
    "query_remotewrite_pending": 'vmagent_remotewrite_pending_data_bytes',

    # All UFM metrics (for label checks)
    "query_all_ufm": '{job=~"ufm.*"}',

    # Scrape series added (for dual-write verification)
    "query_scrape_series_added": 'scrape_series_added{job=~"ufm.*"}',
}


# =============================================================================
# VictoriaLogs Query Templates for UFM Syslog
# =============================================================================

UFM_VL_QUERY_TEMPLATES: Dict[str, str] = {
    # Query syslog events from UFM
    "query_ufm_syslog": '_stream_id:*source="ufm"*',

    # Count UFM syslog entries
    "query_ufm_syslog_count": '_stream_id:*source="ufm"* | stats count()',
}


# =============================================================================
# Retry Constants
# =============================================================================

POD_RESTART_WAIT_SECONDS = 30
POD_RESTART_MAX_RETRIES = 10
SCRAPE_WAIT_MULTIPLIER = 2
