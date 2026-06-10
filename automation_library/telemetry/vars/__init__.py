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
    VICTORIA_CLUSTER,
    VMAGENT,
    VICTORIA_TLS_SECRET,
    VICTORIA_TLS_SECRET_KEYS,
    VICTORIA_API_ENDPOINTS,
    VICTORIA_CMD_TEMPLATES,
)

# VictoriaLogs specific
from .victoria_logs_vars import (
    VLCLUSTER_NAME,
    VLSTORAGE,
    VLINSERT,
    VLSELECT,
    VLAGENT_LOGS,
    VICTORIA_LOGS_TLS_SECRET,
    VICTORIA_LOGS_CMD_TEMPLATES,
)

# PowerScale specific
from .powerscale_vars import (
    DEPLOYMENT_MODE_OMNIA,
    DEPLOYMENT_MODE_OPERATOR,
    CSM_METRICS_POWERSCALE,
)

# Failover test specific (poweroff/reboot)
from .failover_vars import (
    POD_RESCHEDULE_RETRY_LIMIT,
    POD_RESCHEDULE_RETRY_INTERVAL,
    NODE_POWEROFF_WAIT_SECONDS,
    NODE_REBOOT_WAIT_SECONDS,
    NODE_ONLINE_TIMEOUT_SECONDS,
    POD_RUNNING_STATUSES,
    POD_TROUBLE_STATUSES,
    CMD_GET_WORKER_NODES,
    CMD_GET_PODS_ON_NODE,
    CMD_GET_ALL_PODS,
    CMD_SSH_POWEROFF,
    CMD_SSH_REBOOT,
    CMD_PING_NODE,
    CMD_SSH_CHECK,
    CMD_CLOUDINIT_STATUS,
    CLOUDINIT_RETRY_LIMIT,
    CLOUDINIT_RETRY_INTERVAL,
    CLOUDINIT_PASSED_STATUSES,
    CLOUDINIT_RETRY_STATUSES,
)

# Vector specific
from .vector_vars import (
    VECTOR_DEPLOYMENTS,
    VECTOR_DEPLOYMENT_NAMES,
    VECTOR_CONFIGMAP_NAMES,
    VECTOR_DEPLOYMENT_NAME,
    VECTOR_CONFIGMAP_NAME,
    VECTOR_APP_LABEL,
    VECTOR_RESOURCE_SPECS,
    VECTOR_KAFKA_TOPICS,
    VICTORIA_METRICS_ENDPOINTS,
    VICTORIA_LOGS_ENDPOINTS,
    VECTOR_METRICS_PORTS,
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
