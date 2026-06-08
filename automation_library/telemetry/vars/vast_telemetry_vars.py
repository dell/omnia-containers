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
VAST Storage Telemetry Automation - Configuration Variables.

Contains all VAST telemetry related constants, pod labels, metric names,
and command templates used for verifying VAST storage telemetry deployment.
"""

from typing import Dict, List


# =============================================================================
# VAST Scrape Job Constants
# =============================================================================

VAST_JOB_PATTERN = "vast.*"
VAST_SCRAPE_JOB = "vast-external"
VAST_CREDENTIALS_SECRET = "vast-telemetry-credentials"
VAST_SERVICE_NAME = "vast-external"
VAST_APP_LABEL = "vast-external"
VAST_VMSERVICESCRAPE_NAME = "vast-storage-metrics"


# =============================================================================
# VAST Scrape Interval Limits
# =============================================================================

SCRAPE_INTERVAL_MIN_SECONDS = 30
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
# VAST Metric Endpoint
# =============================================================================

VAST_METRICS_PATH = "/api/prometheusmetrics/all"
VAST_METRICS_PORT = 443
VAST_METRICS_SCHEME = "https"


# =============================================================================
# VAST Required Labels (on scraped metrics)
# =============================================================================

VAST_REQUIRED_LABELS: List[str] = [
    "job",
    "instance",
]

VAST_ENRICHMENT_LABELS: List[str] = [
    "source",
    "subsystem",
]


# =============================================================================
# VAST Health Metrics (exposed by vmagent for VAST scrape)
# =============================================================================

VAST_HEALTH_METRICS: List[str] = [
    "up",
    "scrape_samples_scraped",
    "scrape_duration_seconds",
    "scrape_series_added",
]


# =============================================================================
# VAST Metric Family Coverage
# =============================================================================

VAST_MIN_METRIC_FAMILIES = 500
VAST_COVERAGE_THRESHOLD_PERCENT = 90


# =============================================================================
# VAST Credential Patterns (for security tests)
# =============================================================================

CREDENTIAL_PATTERNS: List[str] = [
    "password=",
    "token=",
    "secret=",
    "Authorization:",
    "Basic ",
]


# =============================================================================
# VAST Command Templates
# =============================================================================

VAST_CMD_TEMPLATES: Dict[str, str] = {
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

    # Get vmagent pods (label_selector should be VMAGENT_LABEL_SELECTOR)
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

    # Get service external IP (single quotes prevent shell brace expansion)
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
# VictoriaMetrics Query Templates for VAST
# =============================================================================

VAST_VM_QUERY_TEMPLATES: Dict[str, str] = {
    # Scrape up status
    "query_scrape_up": 'up{job=~"vast.*"}',

    # Count all VAST metric series
    "query_count_series": 'count({job=~"vast.*"})',

    # Count unique metric families
    "query_count_families": 'count by (__name__) ({job=~"vast.*"})',

    # Scrape duration
    "query_scrape_duration": 'scrape_duration_seconds{job=~"vast.*"}',

    # Scrape samples scraped
    "query_scrape_samples": 'scrape_samples_scraped{job=~"vast.*"}',

    # Remote write success
    "query_remotewrite_success": (
        'vmagent_remotewrite_requests_total{status_code="2XX"}'
    ),

    # Remote write pending
    "query_remotewrite_pending": 'vmagent_remotewrite_pending_data_bytes',

    # All VAST metrics (for label checks)
    "query_all_vast": '{job=~"vast.*"}',
}


# =============================================================================
# Retry Constants
# =============================================================================

POD_RESTART_WAIT_SECONDS = 30
POD_RESTART_MAX_RETRIES = 10
SCRAPE_WAIT_MULTIPLIER = 2
