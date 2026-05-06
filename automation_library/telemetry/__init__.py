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
Telemetry Automation Module

Modular organization of Omnia telemetry deployment and verification functions
organized by functionality: functions, variables, and messages.

This module automates the telemetry.yml playbook execution and verification
for iDRAC telemetry, VictoriaMetrics, Kafka, and LDMS components.
"""

from .functions.idrac_telemetry_func import (
    get_service_kube_node_count,
    verify_idrac_telemetry_pod_count,
    verify_all_telemetry_pods_running,
)
from .functions.shared_func import (
    is_kafka_enabled,
    is_ldms_enabled,
)
from .functions.kafka_func import (
    verify_kafka_topics_via_rest,
    verify_kafka_config_match,
    verify_ldms_pods_running,
    verify_ldms_services_ports,
)
from .functions.vector_func import (
    verify_vector_pod_running,
    verify_vector_resource_specs,
    verify_vector_no_pvc,
    verify_vector_configmap_exists,
    verify_vector_mtls_config,
    get_vector_pod_logs,
    verify_vector_no_errors_in_logs,
    verify_no_plaintext_credentials,
    verify_vector_self_metrics_endpoint,
    delete_vector_pod,
    rollout_restart_vector,
    scale_vector_deployment,
    create_kafka_topic,
    produce_test_message_to_kafka,
    query_victoria_metrics,
    query_victoria_logs,
)
from .vars.idrac_telemetry_vars import TELEMETRY_VARS
from .vars.kafka_vars import KAFKA_CMD_TEMPLATES
from .vars.vector_vars import (
    VECTOR_DEPLOYMENT_NAME,
    VECTOR_RESOURCE_SPECS,
    VECTOR_KAFKA_TOPICS,
    VECTOR_SELF_METRICS,
)
from .messages.shared_msgs import TELEMETRY_MSGS, TEST_NAMES
from .messages.vector_msgs import (
    VECTOR_TEST_NAMES,
    VECTOR_TEST_LOG_MSGS,
    VECTOR_TEST_ASSERT_MSGS,
)
