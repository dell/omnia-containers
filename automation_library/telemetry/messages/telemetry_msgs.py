# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Telemetry Automation - Messages.

This module contains all user-facing messages, test names, and assertion messages
for the telemetry automation module.

Variables are imported from telemetry_vars.py to avoid duplication.
"""

from typing import Dict, Any


# =============================================================================
# TEST NAMES
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    # Prerequisite checks
    "provision_config_exists": "Verify provision_config.yml exists",
    "pxe_mapping_file_exists": "Verify PXE mapping file exists",
    "service_kube_nodes_count": "Verify service_kube_node count in PXE mapping",
    "bmc_group_data_exists": "Verify bmc_group_data.csv exists",
    "service_cluster_metadata_exists": "Verify service_cluster_metadata.yml exists",

    # Telemetry pod checks
    "telemetry_namespace_exists": "Verify telemetry namespace exists",
    "victoria_pods_running": "Verify VictoriaMetrics pods are running",
    "kafka_pods_running": "Verify Kafka pods are running",
    "idrac_telemetry_pods_running": "Verify iDRAC telemetry pods are running",
    "idrac_telemetry_pod_count": "Verify idrac-telemetry pod count matches expected",
    "all_telemetry_pods_running": "Verify all telemetry namespace pods are running",

    # Container checks
    "container_running": "Verify {container} container is running",

    # Playbook execution
    "telemetry_playbook_execution": "Execute telemetry.yml playbook",
}


# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # Success messages
    "file_exists": "File exists: {path}",
    "file_not_found": "File not found: {path}",
    "namespace_exists": "Namespace '{namespace}' exists in K8s cluster",
    "namespace_not_found": "Namespace '{namespace}' not found in K8s cluster",
    "pods_running": "All {component} pods are running",
    "pods_not_running": "Some {component} pods are not running",
    "container_running": "Container {container} is running",
    "container_not_running": "Container {container} is not running",

    # idrac-telemetry pod count
    "idrac_pod_count_match": "idrac-telemetry pod count matches expected ({expected} pods)",
    "idrac_pod_count_mismatch": "idrac-telemetry pod count mismatch",

    # all telemetry pods running
    "all_pods_running": "All {total} pods in telemetry namespace are running",
    "some_pods_not_running": "{not_running} of {total} pods not in Running state",
    "stability_check_pass": "Stability check passed after {wait_time}s wait",
    "stability_check_fail": "Stability check failed after {wait_time}s wait",

    # Prerequisite messages
    "provision_config_found": "provision_config.yml found at {path}",
    "pxe_mapping_found": "PXE mapping file found at {path}",
    "pxe_mapping_path_extracted": "PXE mapping file path extracted: {path}",
    "service_kube_nodes_found": "Found {count} service_kube_node entries in PXE mapping",
    "bmc_group_data_found": "bmc_group_data.csv found at {path}",
    "service_cluster_metadata_found": "service_cluster_metadata.yml found at {path}",

    # Error messages
    "provision_config_not_found": "provision_config.yml not found at {path}",
    "pxe_mapping_not_found": "PXE mapping file not found at {path}",
    "no_service_kube_nodes": "No service_kube_node entries found in PXE mapping",
    "bmc_group_data_not_found": "bmc_group_data.csv not found at {path}",
    "service_cluster_metadata_not_found": "service_cluster_metadata.yml not found at {path}",

    # Playbook messages
    "playbook_started": "Starting telemetry.yml playbook execution",
    "playbook_success": "telemetry.yml playbook executed successfully",
    "playbook_failed": "telemetry.yml playbook execution failed",
}


# =============================================================================
# ASSERTION MESSAGES
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "file_not_found": (
        "Required file not found: {path}\n"
        "This file is required for telemetry deployment.\n"
        "Please ensure the file exists before running telemetry playbook."
    ),
    "provision_config_not_found": (
        "provision_config.yml not found at {path}\n"
        "This file is required to determine the PXE mapping file path.\n"
        "Please run discovery/provision playbooks first."
    ),
    "pxe_mapping_not_found": (
        "PXE mapping file not found at {path}\n"
        "This file contains node inventory required for telemetry.\n"
        "Please ensure provision has been completed."
    ),
    "no_service_kube_nodes": (
        "No service_kube_node entries found in PXE mapping file.\n"
        "Telemetry requires at least one service_kube_node.\n"
        "Please check your PXE mapping file configuration."
    ),
    "bmc_group_data_not_found": (
        "bmc_group_data.csv not found at {path}\n"
        "This file contains BMC/iDRAC IP addresses for telemetry collection.\n"
        "Please ensure discovery has been completed."
    ),
    "service_cluster_metadata_not_found": (
        "service_cluster_metadata.yml not found at {path}\n"
        "This file contains service cluster configuration.\n"
        "Please ensure service K8s cluster has been deployed."
    ),
    "namespace_not_found": (
        "Telemetry namespace '{namespace}' not found in K8s cluster.\n"
        "Please ensure telemetry.yml playbook has been executed."
    ),
    "pods_not_running": (
        "{component} pods are not running.\n"
        "Expected pods: {expected}\n"
        "Running pods: {running}\n"
        "Please check pod status with: kubectl get pods -n telemetry"
    ),
    "container_not_running": (
        "Container {container} is not running.\n"
        "Status: {status}\n"
        "Please check container status with: podman ps -a"
    ),
    "playbook_failed": (
        "telemetry.yml playbook execution failed.\n"
        "Exit code: {exit_code}\n"
        "Error: {error}\n"
        "Please check logs for more details."
    ),
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
}


# =============================================================================
# GENERAL MESSAGES
# =============================================================================

TELEMETRY_MSGS: Dict[str, str] = {
    "prereq_check_start": "Starting telemetry prerequisite checks...",
    "prereq_check_complete": "Telemetry prerequisite checks complete",
    "prereq_check_failed": "Telemetry prerequisite checks failed",

    "playbook_start": "Starting telemetry.yml playbook execution...",
    "playbook_complete": "Telemetry playbook execution complete",

    "verification_start": "Starting telemetry verification...",
    "verification_complete": "Telemetry verification complete",
    "verification_failed": "Telemetry verification failed",
}
