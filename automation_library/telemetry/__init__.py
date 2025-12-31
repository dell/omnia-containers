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
Telemetry Automation Module

Modular organization of Omnia telemetry deployment and verification functions
organized by functionality: functions, variables, and messages.

This module automates the telemetry.yml playbook execution and verification
for iDRAC telemetry, VictoriaMetrics, Kafka, and LDMS components.
"""

from .functions.telemetry_func import (
    run_telemetry_playbook,
    verify_telemetry_pods,
    verify_victoria_metrics,
    verify_kafka,
    verify_idrac_telemetry,
    check_telemetry_prerequisites,
    check_service_cluster_ready,
    check_telemetry_config,
)
from .vars.telemetry_vars import TELEMETRY_VARS, validate_telemetry_config
from .messages.telemetry_msgs import TELEMETRY_MSGS, TEST_NAMES
