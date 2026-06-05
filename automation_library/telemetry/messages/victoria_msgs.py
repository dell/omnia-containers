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
VictoriaMetrics Automation - Messages.

This module contains all user-facing messages for VictoriaMetrics tests.
"""

from typing import Dict


# =============================================================================
# VICTORIAMETRICS TEST NAMES
# =============================================================================

VICTORIA_TEST_NAMES: Dict[str, str] = {
    "victoria_enabled": "Check if VictoriaMetrics is enabled",
    "victoria_persistence_size": "Verify VictoriaMetrics persistence size",
    "victoria_single_node_pods": "Verify VictoriaMetrics single-node pods running",
    "victoria_cluster_pods": "Verify VictoriaMetrics cluster pods running",
    "vmagent_pod_running": "Verify vmagent pod running",
    "victoria_services": "Verify VictoriaMetrics services",
    "victoria_tls_secret": "Verify VictoriaMetrics TLS secret",
    "victoria_tls_health": "Verify VictoriaMetrics TLS connection and health",
    "victoria_idrac_data": "Verify iDRAC telemetry data in VictoriaMetrics",
}


# =============================================================================
# VICTORIAMETRICS LOG MESSAGES
# =============================================================================

VICTORIA_LOG_MSGS: Dict[str, str] = {
    # Enable check
    "victoria_enabled": "VictoriaMetrics sink is active (sources target victoria_metrics)",
    "victoria_not_enabled": "VictoriaMetrics is not enabled - skipping tests",

    # Deployment mode
    "deployment_mode_single": "Deployment mode: single-node",
    "deployment_mode_cluster": "Deployment mode: cluster",

    # Persistence
    "persistence_size_match": "Persistence size matches config: {size}",
    "persistence_size_mismatch": "Persistence size mismatch",

    # Pods
    "pod_running": "Pod '{pod}' is running",
    "pod_not_running": "Pod '{pod}' is not running (status: {status})",
    "all_pods_running": "All {component} pods are running ({count} pods)",
    "pods_not_running": "Some {component} pods are not running",

    # Services
    "service_has_external_ip": "Service '{service}' has external IP: {ip}",
    "service_no_external_ip": "Service '{service}' has no external IP",
    "all_services_ready": "All VictoriaMetrics services have external IPs",

    # TLS
    "tls_secret_exists": "TLS secret '{secret}' exists with all required keys",
    "tls_secret_missing": "TLS secret '{secret}' not found",
    "tls_secret_missing_keys": "TLS secret missing keys: {keys}",
    "tls_connection_success": "TLS connection to VictoriaMetrics successful",
    "tls_connection_failed": "TLS connection to VictoriaMetrics failed",

    # Health
    "health_endpoint_success": "Health endpoint returned: {response}",
    "health_endpoint_failed": "Health endpoint check failed",

    # Data verification
    "idrac_data_found": "Found iDRAC telemetry data for service tag: {service_tag}",
    "idrac_data_not_found": "No iDRAC telemetry data for service tag: {service_tag}",
    "idrac_data_all_found": "iDRAC telemetry data found for all {count} activated service tags",
    "idrac_data_verifying": "Verifying iDRAC telemetry data in VictoriaMetrics",
}


# =============================================================================
# VICTORIAMETRICS ASSERTION MESSAGES
# =============================================================================

VICTORIA_ASSERT_MSGS: Dict[str, str] = {
    "victoria_not_enabled": (
        "VictoriaMetrics sink is not active in telemetry_config.yml.\n"
        "No source has 'victoria_metrics' in collection_targets.\n"
        "Skipping all VictoriaMetrics tests."
    ),
    "idrac_telemetry_not_enabled": (
        "iDRAC telemetry source is not enabled in telemetry_config.yml.\n"
        "telemetry_sources.idrac.metrics_enabled is false.\n"
        "Skipping all VictoriaMetrics tests."
    ),
    "persistence_size_mismatch": (
        "VictoriaMetrics persistence size mismatch.\n"
        "Expected: {expected}\n"
        "Actual: {actual}\n"
        "Please check telemetry_sinks.victoria_metrics.persistence_size in telemetry_config.yml"
    ),
    "pods_not_running": (
        "VictoriaMetrics {component} pods are not running.\n"
        "Expected: {expected} pods\n"
        "Running: {running} pods\n"
        "Not running: {not_running}\n"
        "Please check pod status with: kubectl get pods -n telemetry -l app={app_label}"
    ),
    "vmagent_not_running": (
        "vmagent pod is not running.\n"
        "vmagent is required to scrape metrics from idrac-telemetry pods.\n"
        "Please check: kubectl get pods -n telemetry -l app=vmagent"
    ),
    "service_no_external_ip": (
        "VictoriaMetrics service has no external IP.\n"
        "Service: {service}\n"
        "Expected: LoadBalancer with external IP\n"
        "Please check: kubectl get svc {service} -n telemetry"
    ),
    "tls_secret_missing": (
        "VictoriaMetrics TLS secret not found.\n"
        "Secret: {secret}\n"
        "TLS is required for VictoriaMetrics.\n"
        "Please check: kubectl get secret {secret} -n telemetry"
    ),
    "tls_secret_missing_keys": (
        "VictoriaMetrics TLS secret is missing required keys.\n"
        "Secret: {secret}\n"
        "Missing keys: {missing_keys}\n"
        "Required keys: tls.crt, tls.key, ca.crt"
    ),
    "tls_connection_failed": (
        "VictoriaMetrics TLS connection failed.\n"
        "URL: https://{host}:{port}/health\n"
        "Error: {error}\n"
        "Please verify:\n"
        "  1) VictoriaMetrics pods are running\n"
        "  2) TLS certificates are valid\n"
        "  3) Service has external IP"
    ),
    "health_check_failed": (
        "VictoriaMetrics health check failed.\n"
        "URL: https://{host}:{port}/health\n"
        "Response: {response}\n"
        "Expected: 'OK' or valid health response"
    ),
    "idrac_data_missing": (
        "iDRAC telemetry data missing from VictoriaMetrics.\n"
        "Missing service tags: {missing}\n"
        "Found service tags: {found}\n"
        "Please verify:\n"
        "  1) idrac-telemetry pods are running\n"
        "  2) victoria-pump containers are running\n"
        "  3) vmagent is scraping metrics"
    ),
}
