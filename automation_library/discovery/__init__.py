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
Discovery Module

This module provides functions for discovery automation and verification.
Verifies node discovery, OpenCHAMI registration, passwordless SSH, and configuration files.

Organized by functionality: functions, variables, and messages.
"""

# Import specific items to avoid circular imports
# Note: Import functions first, then vars and messages to avoid circular dependency
from .functions import (
    # Helper
    get_nodes_by_functional_group,
    # Original verification functions
    verify_nodes_ssh_reachable,
    verify_ochami_nodes_discovered,
    verify_nodes_yaml_file,
    verify_passwordless_ssh,
    verify_node_hostnames,
    # New validation functions
    validate_node_boot,
    validate_packages_by_group,
    validate_bmc_group_csv,
    # Consolidated validation (all nodes, grouped by functional group)
    validate_all_services,
    validate_all_sinfo,
    validate_all_ldap,
    validate_kubernetes_nodes,
)
from .vars import (
    OPENCHAMI_NODES_PATH,
    OPENCHAMI_HOSTNAME_PATH,
    BMC_GROUP_DATA_PATH,
    OIM_METADATA_PATH,
    CONTAINER_NAME,
    SSH_TIMEOUT,
    CMD_TEMPLATES,
    LOGIN_SERVICES,
    SLURM_CONTROL_SERVICES,
    FUNCTIONAL_GROUP_LOGIN,
    FUNCTIONAL_GROUP_LOGIN_COMPILER,
    FUNCTIONAL_GROUP_SLURM_CONTROL,
    FUNCTIONAL_GROUP_KUBE_CONTROL,
)
from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)

from . import functions as _functions
from . import vars as _vars
from . import messages as _messages

__all__ = list(_functions.__all__) + list(_vars.__all__) + list(_messages.__all__)
