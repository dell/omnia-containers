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
iDRAC Telemetry Automation - Messages.

This module contains all user-facing messages for iDRAC telemetry tests.
"""

from typing import Dict


# =============================================================================
# IDRAC TELEMETRY TEST NAMES
# =============================================================================

IDRAC_TEST_NAMES: Dict[str, str] = {
    # Telemetry pod checks
    "telemetry_namespace_exists": "Verify telemetry namespace exists",
    "victoria_pods_running": "Verify VictoriaMetrics pods are running",
    "idrac_telemetry_pods_running": "Verify iDRAC telemetry pods are running",
    "idrac_telemetry_pod_count": "Verify idrac-telemetry pod count matches expected",
    "all_telemetry_pods_running": "Verify all telemetry namespace pods are running",
    "mysql_data_in_pods": "Verify MySQL data in idrac-telemetry pods",
    "receiver_collecting_metrics": "Verify idrac-telemetry-receiver collecting metrics",
}


# =============================================================================
# IDRAC TELEMETRY LOG MESSAGES
# =============================================================================

IDRAC_LOG_MSGS: Dict[str, str] = {
    # idrac-telemetry pod count
    "idrac_pod_count_match": "idrac-telemetry pod count matches expected ({expected} pods)",
    "idrac_pod_count_mismatch": "idrac-telemetry pod count mismatch",

    # all telemetry pods running
    "all_pods_running": "All {total} pods in telemetry namespace are running",
    "some_pods_not_running": "{not_running} of {total} pods not in Running state",
    "stability_check_pass": "Stability check passed after {wait_time}s wait",
    "stability_check_fail": "Stability check failed after {wait_time}s wait",

    # MySQL data verification
    "mysql_creds_decrypted": "MySQL credentials decrypted from ansible vault",
    "mysql_creds_failed": "Failed to decrypt MySQL credentials",
    "mysql_pod_verified": "Pod {pod_name}: All expected IPs found in MySQL",
    "mysql_pod_missing_ips": "Pod {pod_name}: Missing IPs in MySQL: {missing}",
    "mysql_all_pods_verified": "All idrac-telemetry pods have correct MySQL data",

    # Receiver metrics verification
    "receiver_collecting": "Pod {pod_name}: Receiver collecting metrics",
    "receiver_connected": "Pod {pod_name}: Receiver SSE connected (Status 200)",
    "receiver_not_collecting": "Pod {pod_name}: Receiver not collecting metrics",
    "receiver_all_collecting": "All idrac-telemetry-receiver containers collecting metrics",
}


# =============================================================================
# IDRAC TELEMETRY ASSERTION MESSAGES
# =============================================================================

IDRAC_ASSERT_MSGS: Dict[str, str] = {
    "idrac_pod_count_mismatch": (
        "idrac-telemetry pod count mismatch.\n"
        "Expected: {expected} pods (service_kube_node count {svc_count} + 1 for mgmt)\n"
        "Actual: {actual} pods\n"
        "Please check telemetry deployment with: kubectl get pods -n telemetry"
    ),
    "telemetry_pods_not_running": (
        "Some pods in telemetry namespace are not running.\n"
        "Total pods: {total}\n"
        "Running: {running}\n"
        "Not running: {not_running}\n"
        "Please check pod status with: kubectl get pods -n telemetry"
    ),
    "mysql_data_missing": (
        "MySQL data verification failed for some pods.\n"
        "Pod: {pod_name}\n"
        "Expected IPs: {expected}\n"
        "Actual IPs: {actual}\n"
        "Missing IPs: {missing}\n"
        "Please check MySQL data in pod with: kubectl exec -n telemetry {pod_name} "
        "-c mysqldb -- mysql -u <user> -p<pass> -e 'USE idrac_telemetrydb; SELECT * FROM services;'"
    ),
    "receiver_not_collecting": (
        "idrac-telemetry-receiver not collecting metrics.\n"
        "Pod: {pod_name}\n"
        "MySQL IPs: {mysql_ips}\n"
        "Service tags found: {service_tags}\n"
        "Please check receiver logs with: kubectl logs -n telemetry {pod_name} "
        "-c idrac-telemetry-receiver --tail=100"
    ),
}
