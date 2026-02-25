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
Kafka Automation - Configuration Variables.

Contains all Kafka and LDMS related constants and command templates.
"""

from typing import Dict


# =============================================================================
# Config File Paths (inside container)
# =============================================================================

TELEMETRY_CONFIG_PATH = "/opt/omnia/input/project_default/telemetry_config.yml"
SOFTWARE_CONFIG_PATH = "/opt/omnia/input/project_default/software_config.json"


# =============================================================================
# LDMS Constants
# =============================================================================

LDMS_AGGR_POD_PREFIX = "nersc-ldms-aggr"
LDMS_STORE_POD_PREFIX = "nersc-ldms-store"


# =============================================================================
# Kafka REST Proxy (Bridge) Constants
# =============================================================================

KAFKA_BRIDGE_SERVICE = "bridge-bridge-lb"
KAFKA_BRIDGE_PORT = "8080"


# =============================================================================
# LDMS Data Verification Constants
# =============================================================================

# LDMS functional groups that send data to Kafka
LDMS_FUNCTIONAL_GROUPS = [
    "slurm_control_node_x86_64",
    "slurm_node_x86_64",
    "slurm_node_aarch64",
    "login_node_x86_64",
    "login_node_aarch64",
    "login_compiler_node_x86_64",
    "login_compiler_node_aarch64",
]

# OIM metadata path (for domain name)
OIM_METADATA_PATH = "/opt/omnia/.data/oim_metadata.yml"


# =============================================================================
# Kafka Command Templates
# =============================================================================

KAFKA_CMD_TEMPLATES: Dict[str, str] = {
    # Get Kafka bridge (REST proxy) external IP
    "get_bridge_lb_ip": (
        "kubectl get svc {service} -n {namespace} "
        "-o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'"
    ),

    # REST proxy - list topics
    "rest_list_topics": "curl -s http://{bridge_ip}:{port}/topics",

    # REST proxy - create consumer group
    "rest_create_consumer": (
        'curl -s -X POST http://{bridge_ip}:{port}/consumers/{consumer_group} '
        '-H "content-type: application/vnd.kafka.v2+json" '
        '-d \'{{"name": "{consumer_name}", "format": "json", '
        '"auto.offset.reset": "earliest", "enable.auto.commit": true}}\''
    ),

    # REST proxy - subscribe to topic
    "rest_subscribe_topic": (
        'curl -s -X POST http://{bridge_ip}:{port}/consumers/{consumer_group}'
        '/instances/{consumer_name}/subscription '
        '-H "content-type: application/vnd.kafka.v2+json" '
        '-d \'{{"topics": ["{topic}"]}}\''
    ),

    # REST proxy - consume records
    "rest_consume_records": (
        'curl -s -X GET http://{bridge_ip}:{port}/consumers/{consumer_group}'
        '/instances/{consumer_name}/records '
        '-H "accept: application/vnd.kafka.json.v2+json"'
    ),

    # REST proxy - delete consumer
    "rest_delete_consumer": (
        'curl -s -X DELETE http://{bridge_ip}:{port}/consumers/{consumer_group}'
        '/instances/{consumer_name}'
    ),

    # Kubectl commands for Kafka verification
    "get_kafka_cluster": "kubectl get kafka kafka -n {namespace} -o json",
    "get_kafka_topics": "kubectl get kafkatopics -n {namespace} -o json",
    "get_pods": "kubectl get pods -n {namespace} -o json",
    "get_services": "kubectl get svc -n {namespace} -o json",
}
