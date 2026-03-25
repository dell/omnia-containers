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

"""Discovery Variables Module."""

from .common_vars import (
    SSH_OPTS,
    CONTAINER_NAME,
)

from .slurm_vars import (
    SLURM_CONTROL_SERVICES,
    SLURM_NODE_SERVICES,
    LOGIN_NODE_SERVICES,
    OPENMPI_BIN_PATH,
    UCX_BIN_PATH,
    LDMS_SAMPLER_SERVICE,
    LDMS_SAMPLER_CONF_PATH,
    LDMS_SAMPLER_ENV_PATH,
)

from .ldap_vars import (
    LDAP_CONTAINER_NAME,
    SLAPD_CONF_TEMPLATE,
    CONTAINER_STABLE_WAIT_SECONDS,
    CONTAINER_CHECK_INTERVAL,
)
