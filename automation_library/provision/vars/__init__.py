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

"""Provision Variables Module."""

from .common_vars import (
    SSH_OPTS,
    CONTAINER_NAME,
    IMAGE_CONFIG_YAML_DIR,
    PROVISION_REACHABILITY_RETRY,
    PROVISION_REACHABILITY_INTERVAL,
    CLOUDINIT_RETRY_LIMIT,
    CLOUDINIT_RETRY_INTERVAL,
    CLOUDINIT_PASSED_STATUSES,
    CLOUDINIT_RETRY_STATUSES,
    OPENCHAMI_WORKDIR,
    BSS_BOOT_DIR,
    CLOUDINIT_TEMPLATE_DIR,
)

from .slurm_vars import (
    SLURM_CONTROL_SERVICES,
    SLURM_NODE_SERVICES,
    LOGIN_NODE_SERVICES,
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

from .minimal_os_vars import (
    FUNCTIONAL_GROUPS,
    BASE_PACKAGES,
    LDMS_PACKAGES,
    EXCLUDED_PACKAGE_PATTERNS,
    EXCLUDED_SERVICES,
    REQUIRED_SERVICES,
    LDMS_SERVICE_CHECK_CMD,
    MINIMAL_OS_VARS,
)
