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
Telemetry Automation - Shared Variables.

This module contains shared constants used across all telemetry modules
(iDRAC, Kafka, VictoriaMetrics).

For module-specific constants, see:
- idrac_telemetry_vars.py - iDRAC telemetry specific
- kafka_vars.py - Kafka and LDMS specific
- victoria_vars.py - VictoriaMetrics specific
"""

# Import from core (single source of truth for K8s constants)
from ...core.vars import (
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
    K8S_WORKER_NODE_FUNCTIONAL_GROUP,
)


# =============================================================================
# Telemetry Namespace
# =============================================================================

TELEMETRY_NAMESPACE = "telemetry"


# =============================================================================
# Config File Paths (inside container) - used by shared_func.py
# =============================================================================

TELEMETRY_CONFIG_PATH = "/opt/omnia/input/project_default/telemetry_config.yml"
SOFTWARE_CONFIG_PATH = "/opt/omnia/input/project_default/software_config.json"


# =============================================================================
# Container
# =============================================================================

CONTAINER_NAME = "omnia_core"
