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

This module provides functions for discovery playbook verification,
including Minimal OS functional group validation.

Uses core module utilities for SSH, PXE mapping, and config reading.

Test Categories:
- Common: Node boot, passwordless SSH, hostname sync
- Slurm: Services, cross-node SSH, sinfo, OpenMPI/UCX
- K8s: Node ready status
- Minimal OS: Functional groups, packages, LDMS, security
"""

from .functions import (
    # Common functions
    cleanup_ssh_known_hosts,
    get_slurm_control_nodes,
    get_slurm_compute_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
    get_all_slurm_nodes,
    get_k8s_nodes,
    skip_if_no_slurm_nodes,
    skip_if_no_k8s_nodes,
    verify_ssh_from_core,
    verify_ssh_from_oim,
    # Slurm functions
    is_openmpi_enabled,
    is_ucx_enabled,
    is_openldap_enabled,
    skip_if_openmpi_not_enabled,
    skip_if_ucx_not_enabled,
    verify_services_on_nodes,
    verify_cross_node_ssh,
    verify_sinfo_nodes,
    verify_openmpi_installed,
    verify_ucx_installed,
    # LDAP functions
    skip_if_openldap_not_enabled,
    apply_slapd_conf_and_verify,
)
from .vars import (
    SSH_OPTS,
    CONTAINER_NAME,
    SLURM_CONTROL_SERVICES,
    SLURM_NODE_SERVICES,
    LOGIN_NODE_SERVICES,
    OPENMPI_BIN_PATH,
    UCX_BIN_PATH,
    LDAP_CONTAINER_NAME,
    SLAPD_CONF_TEMPLATE,
)
from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)
