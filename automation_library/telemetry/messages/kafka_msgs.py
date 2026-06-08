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
Kafka Automation - Messages.

This module contains all user-facing messages for Kafka and LDMS tests.
"""

from typing import Dict


# =============================================================================
# KAFKA TEST NAMES
# =============================================================================

KAFKA_TEST_NAMES: Dict[str, str] = {
    # LDMS tests
    "ldms_pods_running": "Verify LDMS pods running",
    "ldms_services_ports": "Verify LDMS services ports",
    "ldms_data_in_kafka": "Verify LDMS data flowing to Kafka topic",

    # Kafka tests
    "kafka_enabled_check": "Check if Kafka is enabled in telemetry_config.yml",
    "kafka_topics_verification": "Verify Kafka topics configuration",
    "kafka_config_match": "Verify Kafka configurations match telemetry_config.yml",
    "kafka_idrac_data": "Verify iDRAC data in Kafka topic",
    "kafka_ldms_topic_data": "Verify data flowing to ldms Kafka topic",
}


# =============================================================================
# KAFKA LOG MESSAGES
# =============================================================================

KAFKA_LOG_MSGS: Dict[str, str] = {
    # Kafka log messages
    "kafka_enabled": "Kafka sink is active (sources target kafka)",
    "kafka_not_enabled": "Kafka is not enabled - skipping Kafka tests",
    "kafka_cluster_ready": "Kafka cluster is ready",
    "kafka_cluster_not_ready": "Kafka cluster is not ready",
    "kafka_topic_exists": "Topic '{topic}' exists with {partitions} partitions",
    "kafka_topic_missing": "Topic '{topic}' is missing",
    "kafka_topic_partition_mismatch": (
        "Topic '{topic}' partition mismatch: expected {expected}, actual {actual}"
    ),
    "kafka_config_match": "Kafka configuration matches telemetry_config.yml",
    "kafka_config_mismatch": (
        "Kafka configuration mismatch: {config} expected {expected}, actual {actual}"
    ),
    "kafka_idrac_data_flowing": "Data is flowing to idrac Kafka topic",
    "kafka_ldms_data_flowing": "Data is flowing to ldms Kafka topic",
    "kafka_ldms_skipped": "LDMS topic check skipped - LDMS not enabled",

    # LDMS data verification
    "ldms_data_verifying": "Verifying LDMS data in Kafka topic",
    "ldms_data_domain": "Domain name: {domain}",
    "ldms_data_plugins": "Expected plugins: {plugins}",
    "ldms_data_hostnames": "Expected hostnames: {hostnames}",
    "ldms_data_found": "Found data from hostname '{hostname}': {plugins}",
    "ldms_data_missing": "Missing data from hostname '{hostname}'",
    "ldms_data_success": "LDMS data verified for all {count} hostnames",

    # iDRAC Kafka data verification
    "idrac_kafka_verifying": "Verifying iDRAC telemetry data in Kafka topic",
    "idrac_kafka_data_success": "iDRAC data found for all {count} service tags",
}


# =============================================================================
# KAFKA ASSERTION MESSAGES
# =============================================================================

KAFKA_ASSERT_MSGS: Dict[str, str] = {
    "kafka_not_enabled": (
        "Kafka sink is not active in telemetry_config.yml.\n"
        "No source has 'kafka' in collection_targets.\n"
        "Skipping all Kafka tests."
    ),
    "kafka_topic_missing": (
        "Required Kafka topic is missing.\n"
        "Topic: {topic}\n"
        "Required: {required}\n"
        "LDMS enabled: {ldms_enabled}\n"
        "Please check topics with: kubectl get kafkatopics -n telemetry"
    ),
    "kafka_config_mismatch": (
        "Kafka configuration does not match telemetry_config.yml.\n"
        "Mismatches:\n{mismatches}\n"
        "Please verify telemetry_sinks.kafka in telemetry_config.yml"
    ),
    "kafka_idrac_data_not_flowing": (
        "Data is not flowing to idrac Kafka topic.\n"
        "Topic ready: {topic_ready}\n"
        "Pods running: {pods_running}\n"
        "Please check idrac-telemetry pods and kafkapump container"
    ),
    "kafka_ldms_data_not_flowing": (
        "Data is not flowing to ldms Kafka topic.\n"
        "Topic ready: {topic_ready}\n"
        "Please check LDMS configuration and ldms topic"
    ),
    "kafka_bridge_not_found": (
        "Failed to get Kafka bridge LB IP.\n"
        "Check if bridge-bridge-lb service exists in telemetry namespace.\n"
        "Run: kubectl get svc bridge-bridge-lb -n telemetry"
    ),
    "kafka_rest_connection_failed": (
        "Failed to connect to Kafka REST proxy at {bridge_ip}:8080.\n"
        "This may indicate mTLS connection issues between the bridge and Kafka.\n"
        "Check:\n"
        "  1) Kafka cluster is running: kubectl get kafka -n telemetry\n"
        "  2) Bridge pod is running: kubectl get pods -n telemetry | grep bridge\n"
        "  3) mTLS certificates are valid: kafka-cluster-ca-cert, kafkapump secrets"
    ),
    "kafka_rest_parse_failed": (
        "Failed to parse topics response from REST proxy.\n"
        "Response: {response}\n"
        "This may indicate mTLS or Kafka connectivity issues."
    ),
    # Kafka cluster errors
    "kafka_cluster_config_failed": "Failed to get Kafka cluster config",
    "kafka_cluster_parse_failed": "Failed to parse Kafka cluster config",
    # Kafka config validation errors
    "kafka_config_missing": "{config} not found in telemetry_config.yml",
    "kafka_partitions_missing": (
        "partitions not defined for topic '{topic}' in telemetry_config.yml"
    ),
    # Pod/service errors
    "pods_get_failed": "Failed to get pods: {error}",
    "pods_parse_failed": "Failed to parse pods JSON",
    "services_get_failed": "Failed to get services: {error}",
    "services_parse_failed": "Failed to parse services JSON",
    # LDMS data verification errors
    "ldms_no_plugins": (
        "No LDMS sampler plugins configured in telemetry_config.yml.\n"
        "Please check ldms_configurations.sampler_plugins section."
    ),
    "ldms_no_nodes": (
        "No LDMS nodes found in PXE mapping file.\n"
        "Expected functional groups: slurm_control_node, slurm_node, "
        "login_node, login_compiler_node"
    ),
    "ldms_no_domain": (
        "Could not get domain_name from oim_metadata.yml.\n"
        "Please check /opt/omnia/.data/oim_metadata.yml in omnia_core container."
    ),
    "ldms_data_missing_hostnames": (
        "LDMS data missing from some hostnames.\n"
        "Missing: {missing}\n"
        "Found: {found}\n"
        "Please check LDMS sampler on missing nodes and verify data is being sent to Kafka."
    ),
    # iDRAC Kafka data verification errors
    "idrac_kafka_not_enabled": (
        "No source targets kafka for iDRAC telemetry"
    ),
    "idrac_kafka_no_activated_ips": (
        "No activated IPs found in telemetry report"
    ),
    "idrac_kafka_mysql_creds_failed": (
        "Failed to get MySQL credentials: {error}"
    ),
    "idrac_kafka_redfish_failed": (
        "Could not get service tags via Redfish for any activated IP"
    ),
    "idrac_kafka_consumer_failed": (
        "Failed to create Kafka consumer: {error}"
    ),
    "idrac_kafka_no_data": (
        "No iDRAC data found in Kafka topic.\n"
        "Expected service tags: {expected}\n"
        "Check if kafkapump is running and sending data to Kafka."
    ),
    "idrac_kafka_data_missing": (
        "iDRAC data missing from some service tags.\n"
        "Missing: {missing}\n"
        "Found: {found}\n"
        "Please check kafkapump on idrac-telemetry pods."
    ),
}
