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

"""Telemetry variables module."""

# Shared telemetry constants (used across all telemetry modules)
from .shared_vars import (
    TELEMETRY_NAMESPACE,
    CONTAINER_NAME,
)

# iDRAC telemetry specific
from .idrac_telemetry_vars import (
    TELEMETRY_VARS,
    IDRAC_TELEMETRY_POD_PREFIX,
    STABILITY_WAIT_TIME,
    CMD_TEMPLATES,
)

# Kafka specific
from .kafka_vars import (
    KAFKA_CMD_TEMPLATES,
    LDMS_AGGR_POD_PREFIX,
    LDMS_STORE_POD_PREFIX,
    KAFKA_BRIDGE_SERVICE,
    KAFKA_BRIDGE_PORT,
    LDMS_FUNCTIONAL_GROUPS,
)

# VictoriaMetrics specific
from .victoria_vars import (
    DEPLOYMENT_MODE_SINGLE,
    DEPLOYMENT_MODE_CLUSTER,
    VICTORIA_SINGLE_NODE,
    VICTORIA_CLUSTER,
    VMAGENT,
    VICTORIA_TLS_SECRET,
    VICTORIA_TLS_SECRET_KEYS,
    VICTORIA_API_ENDPOINTS,
    VICTORIA_CMD_TEMPLATES,
)

# Vector specific
from .vector_vars import (
    VECTOR_DEPLOYMENT_NAME,
    VECTOR_CONFIGMAP_NAME,
    VECTOR_APP_LABEL,
    VECTOR_RESOURCE_SPECS,
    VECTOR_KAFKA_TOPICS,
    VICTORIA_METRICS_ENDPOINTS,
    VICTORIA_LOGS_ENDPOINTS,
    VECTOR_METRICS_PORT,
    VECTOR_METRICS_PATH,
    VECTOR_SELF_METRICS,
    VECTOR_CMD_TEMPLATES,
    LDMS_METRIC_TEMPLATE,
    IDRAC_EVENT_TEMPLATE,
    LATENCY_THRESHOLDS,
    PERFORMANCE_THRESHOLDS,
    TOPIC_DISCOVERY_TIMEOUT_SECONDS,
    ERROR_LOG_PATTERNS,
    CREDENTIAL_PATTERNS,
)
