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
from .functions.vast_telemetry_func import (
    is_vast_telemetry_enabled,
    verify_vast_scrape_active,
    verify_vast_deployment,
    verify_vast_metric_coverage,
)
from .vars.idrac_telemetry_vars import TELEMETRY_VARS
from .vars.kafka_vars import KAFKA_CMD_TEMPLATES
from .messages.shared_msgs import TELEMETRY_MSGS, TEST_NAMES
