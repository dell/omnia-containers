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
# Kafka Constants
# =============================================================================

KAFKA_BOOTSTRAP_SERVER = "kafka-kafka-bootstrap:9093"
KAFKA_CLUSTER_CA_SECRET = "kafka-cluster-ca-cert"
KAFKA_USER_SECRET = "kafkapump"
KAFKA_STRIMZI_IMAGE = "quay.io/strimzi/kafka:0.48.0-kafka-4.1.0"
KAFKA_MTLS_TEST_JOB_PREFIX = "kafka-mtls-test-automation"


# =============================================================================
# LDMS Constants
# =============================================================================

LDMS_AGGR_POD_PREFIX = "nersc-ldms-aggr"
LDMS_STORE_POD_PREFIX = "nersc-ldms-store"


# =============================================================================
# Kafka Command Templates
# =============================================================================

KAFKA_CMD_TEMPLATES: Dict[str, str] = {
    # Create truststore from cluster CA certificate
    "create_truststore": (
        "keytool -import -trustcacerts -alias kafka-cluster-ca "
        "-file /etc/kafka/cluster-ca/ca.crt "
        "-keystore /tmp/truststore.jks "
        "-storepass changeit -noprompt"
    ),

    # Create keystore from kafkapump client certificate
    "create_keystore": (
        "openssl pkcs12 -export "
        "-in /etc/kafka/kafkapump-certs/user.crt "
        "-inkey /etc/kafka/kafkapump-certs/user.key "
        "-out /tmp/kafkapump-keystore.p12 "
        "-password pass:changeit "
        "-name kafkapump"
    ),

    # Create Kafka client properties for mTLS
    "create_client_properties": (
        "echo 'security.protocol=SSL' > /tmp/client.properties && "
        "echo 'ssl.truststore.location=/tmp/truststore.jks' >> /tmp/client.properties && "
        "echo 'ssl.truststore.password=changeit' >> /tmp/client.properties && "
        "echo 'ssl.keystore.location=/tmp/kafkapump-keystore.p12' >> /tmp/client.properties && "
        "echo 'ssl.keystore.password=changeit' >> /tmp/client.properties && "
        "echo 'ssl.keystore.type=PKCS12' >> /tmp/client.properties"
    ),

    # List Kafka topics via mTLS
    "list_topics": (
        "/opt/kafka/bin/kafka-topics.sh --bootstrap-server {bootstrap_server} "
        "--command-config /tmp/client.properties --list"
    ),

    # Kubectl commands for Kafka verification
    "get_kafka_cluster": "kubectl get kafka kafka -n {namespace} -o json",
    "get_kafka_topics": "kubectl get kafkatopics -n {namespace} -o json",
    "get_pods": "kubectl get pods -n {namespace} -o json",
    "get_services": "kubectl get svc -n {namespace} -o json",
    "delete_job": "kubectl delete job {job_name} -n {namespace} --ignore-not-found",
    "force_delete_pods": (
        "kubectl delete pods -n {namespace} "
        "-l job-name={job_name} --force --grace-period=0 --ignore-not-found"
    ),
    "get_pod_by_job": (
        "kubectl get pods -n {namespace} -l job-name={job_name} "
        "-o jsonpath='{{.items[0].metadata.name}}'"
    ),
    "get_pod_status": "kubectl get pod {pod_name} -n {namespace} -o jsonpath='{{.status.phase}}'",
    "exec_in_pod": 'kubectl exec -n {namespace} {pod_name} -- /bin/bash -c "{command}"',
}
