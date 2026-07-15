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

"""Upgrade and Rollback Variables Module."""

from .upgrade_core_vars import (
    UPGRADE_VARS,
    SUPPORTED_VERSIONS,
    VERSION_PROPERTIES,
    get_core_tag_for_version,
)
from .prepare_upgrade_vars import PREPARE_UPGRADE_VARS
from .backup_verify_vars import BACKUP_VERIFY_VARS
from .rollback_core_vars import ROLLBACK_VARS

# K8s & Telemetry upgrade
from .k8s_telemetry_upgrade_vars import (
    K8S_UPGRADE_VARS,
    SNAPSHOT_PATH,
    TELEMETRY_NAMESPACE,
    KUBE_SYSTEM_NAMESPACE,
    CALICO_NAMESPACE,
    METALLB_NAMESPACE,
    KUBECTL_CMD,
)

__all__ = [
    "UPGRADE_VARS",
    "SUPPORTED_VERSIONS",
    "VERSION_PROPERTIES",
    "get_core_tag_for_version",
    "PREPARE_UPGRADE_VARS",
    "BACKUP_VERIFY_VARS",
    "ROLLBACK_VARS",
    # K8s & Telemetry upgrade
    "K8S_UPGRADE_VARS",
    "SNAPSHOT_PATH",
    "TELEMETRY_NAMESPACE",
    "KUBE_SYSTEM_NAMESPACE",
    "CALICO_NAMESPACE",
    "METALLB_NAMESPACE",
    "KUBECTL_CMD",
]
