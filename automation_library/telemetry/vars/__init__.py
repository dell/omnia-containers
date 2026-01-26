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

from .idrac_telemetry_vars import (
    TELEMETRY_VARS,
    validate_telemetry_config,
    PROVISION_CONFIG_PATH,
    BMC_GROUP_DATA_PATH,
    SERVICE_CLUSTER_METADATA_PATH,
    TELEMETRY_NAMESPACE,
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
    IDRAC_TELEMETRY_POD_PREFIX,
    STABILITY_WAIT_TIME,
    CMD_TEMPLATES,
)

from .kafka_vars import (
    TELEMETRY_CONFIG_PATH,
    SOFTWARE_CONFIG_PATH,
    KAFKA_CMD_TEMPLATES,
    LDMS_AGGR_POD_PREFIX,
    LDMS_STORE_POD_PREFIX,
    KAFKA_BRIDGE_SERVICE,
    KAFKA_BRIDGE_PORT,
)

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
