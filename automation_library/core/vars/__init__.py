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

"""Core Variables Module."""

from .common_vars import (
    SSH_OPTS,
    OMNIA_CORE_CONTAINER,
    PODMAN_EXEC_PREFIX,
)

from .connectivity_vars import (
    PING_RETRY_LIMIT,
    PING_RETRY_INTERVAL,
    SSH_RETRY_LIMIT,
    SSH_RETRY_INTERVAL,
    MAX_PARALLEL_WORKERS,
    CONNECTIVITY_PROGRESS_INTERVAL,
    CMD_PING_NODE,
    CMD_SSH_CHECK,
)

from .cloudinit_vars import (
    CLOUDINIT_RETRY_LIMIT,
    CLOUDINIT_RETRY_INTERVAL,
    CLOUDINIT_PASSED_STATUSES,
    CLOUDINIT_RETRY_STATUSES,
    CMD_CLOUDINIT_STATUS,
)

from .build_stream_vars import (
    POSTGRES_CONTAINER,
    POSTGRES_DB,
    POSTGRES_USER_KEY,
    COMPLETED_STATE,
    STAGE_BUILD_IMAGE_X86_64,
    STAGE_BUILD_IMAGE_AARCH64,
    STAGE_CREATE_LOCAL_REPO,
    STAGE_VALIDATE_IMAGE,
    STAGE_PARSE_CATALOG,
    STAGE_GENERATE_INPUT,
)

from .paths_vars import (
    # Base paths
    OIM_SHARED_PATH,
    OMNIA_DATA_PATH,
    OMNIA_AUTH_PATH,
    OMNIA_TELEMETRY_PATH,
    OMNIA_LOG_PATH,
    OMNIA_PULP_PATH,
    INPUT_BASE_PATH,
    # Input file names
    SOFTWARE_CONFIG_FILE,
    BUILD_STREAM_CONFIG_FILE,
    GITLAB_CONFIG_FILE,
    NETWORK_SPEC_FILE,
    PROVISION_CONFIG_FILE,
    DISCOVERY_CONFIG_FILE,
    TELEMETRY_CONFIG_FILE,
    STORAGE_CONFIG_FILE,
    OMNIA_CONFIG_FILE,
    OMNIA_CREDENTIALS_FILE,
    HA_CONFIG_FILE,
    PXE_MAPPING_FILE,
    BMC_PXE_MAPPING_FILE_PREFIX,
    # Full input file paths
    SOFTWARE_CONFIG_PATH,
    TELEMETRY_CONFIG_PATH,
    OMNIA_CONFIG_PATH,
    NETWORK_SPEC_PATH,
    PROVISION_CONFIG_PATH,
    DISCOVERY_CONFIG_PATH,
    STORAGE_CONFIG_PATH,
    HA_CONFIG_PATH,
    PXE_MAPPING_FILE_PATH,
    OMNIA_CREDENTIALS_PATH,
    OMNIA_CREDENTIALS_KEY_PATH,
    GITLAB_CONFIG_PATH,
    BUILD_STREAM_OAUTH_CREDENTIALS_PATH,
    BUILD_STREAM_OAUTH_CREDENTIALS_KEY_PATH,
    # Data paths
    SERVICE_CLUSTER_METADATA_PATH,
    OIM_METADATA_PATH,
    FUNCTIONAL_GROUPS_CONFIG_PATH,
    # Auth paths
    SLAPD_CONF_PATH,
    LDAP_CERT_PATH,
    # Telemetry paths
    BMC_GROUP_DATA_PATH,
    IDRAC_TELEMETRY_REPORT_PATH,
    # Pulp paths
    PULP_CERT_PATH,
    # Log paths
    LOCAL_REPO_LOG_PATH,
    # K8s functional groups
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
    K8S_WORKER_NODE_FUNCTIONAL_GROUP,
    # Slurm functional groups
    SLURM_CONTROL_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_AARCH64_FUNCTIONAL_GROUP,
    LOGIN_NODE_FUNCTIONAL_GROUP,
    LOGIN_NODE_AARCH64_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_AARCH64_FUNCTIONAL_GROUP,
    # Supported functional groups list
    OMNIA_SUPPORTED_FUNCTIONAL_GROUPS,
    # PXE mapping columns
    PXE_MAPPING_REQUIRED_COLUMNS,
)
