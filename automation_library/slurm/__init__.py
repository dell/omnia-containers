# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Slurm Module

This module provides functions for Slurm cluster test automation.
Verifies Slurm services, node states, and job execution.

Organized by functionality: functions, variables, and messages.
"""

from .functions import (
    # Node discovery
    get_slurm_control_nodes,
    get_slurm_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
    get_all_munge_nodes,
    get_slurm_node_count,
    # Service checks
    verify_slurmctld_active,
    verify_slurmd_active,
    verify_slurmd_active_on_login_nodes,
    verify_slurmd_on_login_nodes_only,
    verify_slurmd_on_login_compiler_nodes_only,
    verify_munge_active,
    verify_munge_on_control_nodes,
    verify_munge_on_slurm_nodes,
    verify_munge_on_login_nodes,
    verify_munge_on_login_compiler_nodes,
    # Cluster state
    verify_slurm_nodes_idle,
    verify_login_nodes_idle,
    verify_srun_job,
    verify_sbatch_job,
    # Root job submission
    verify_root_sbatch_from_login_node,
    verify_root_multi_sbatch_from_login_node,
    verify_root_sbatch_from_multiple_login_nodes,
    # Advanced scenarios
    verify_drain_undrain_queuing,
    verify_insufficient_resources,
    verify_passwordless_ssh,
    # LDAP user tests
    verify_ldapuser_login,
    verify_ldapuser_blocked_on_slurm_nodes,
    verify_pam_from_login_node,
    verify_pam_from_login_compiler_node,
    verify_pam_from_control_node,
    verify_openmpi_job,
    verify_job_queuing,
    verify_ldap_sbatch_from_login_nodes,
    verify_ldap_multi_sbatch_from_login_node,
    verify_ldapuser_login_on_control_nodes,
    verify_ldapuser_login_on_login_nodes,
    verify_ldapuser_login_on_login_compiler_nodes,
    verify_invalid_ldap_username,
    verify_invalid_ldap_password,
    set_ldapuser_home_permissions,
)
from .vars import (
    SLURM_CONTROL_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_FUNCTIONAL_GROUP,
    LOGIN_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
    SLURMCTLD_SERVICE,
    SLURMD_SERVICE,
    MUNGE_SERVICE,
    MUNGE_REQUIRED_GROUPS,
    PXE_MAPPING_FILE_PATH,
)
from .messages import (
    TEST_PASSED,
    TEST_FAILED,
    TEST_SKIPPED,
)

__all__ = [
    # Node discovery
    "get_slurm_control_nodes",
    "get_slurm_nodes",
    "get_login_nodes",
    "get_login_compiler_nodes",
    "get_all_munge_nodes",
    "get_slurm_node_count",
    # Service checks
    "verify_slurmctld_active",
    "verify_slurmd_active",
    "verify_slurmd_active_on_login_nodes",
    "verify_slurmd_on_login_nodes_only",
    "verify_slurmd_on_login_compiler_nodes_only",
    "verify_munge_active",
    "verify_munge_on_control_nodes",
    "verify_munge_on_slurm_nodes",
    "verify_munge_on_login_nodes",
    "verify_munge_on_login_compiler_nodes",
    # Cluster state
    "verify_slurm_nodes_idle",
    "verify_login_nodes_idle",
    "verify_srun_job",
    "verify_sbatch_job",
    # Root job submission
    "verify_root_sbatch_from_login_node",
    "verify_root_multi_sbatch_from_login_node",
    "verify_root_sbatch_from_multiple_login_nodes",
    # Advanced scenarios
    "verify_drain_undrain_queuing",
    "verify_insufficient_resources",
    "verify_passwordless_ssh",
    # LDAP user tests
    "verify_ldapuser_login",
    "verify_ldapuser_blocked_on_slurm_nodes",
    "verify_pam_from_login_node",
    "verify_pam_from_login_compiler_node",
    "verify_pam_from_control_node",
    "verify_openmpi_job",
    "verify_job_queuing",
    "verify_ldap_sbatch_from_login_nodes",
    "verify_ldap_multi_sbatch_from_login_node",
    "verify_ldapuser_login_on_control_nodes",
    "verify_ldapuser_login_on_login_nodes",
    "verify_ldapuser_login_on_login_compiler_nodes",
    "verify_invalid_ldap_username",
    "verify_invalid_ldap_password",
    "set_ldapuser_home_permissions",
    # Vars
    "SLURM_CONTROL_NODE_FUNCTIONAL_GROUP",
    "SLURM_NODE_FUNCTIONAL_GROUP",
    "LOGIN_NODE_FUNCTIONAL_GROUP",
    "LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP",
    "SLURMCTLD_SERVICE",
    "SLURMD_SERVICE",
    "MUNGE_SERVICE",
    "MUNGE_REQUIRED_GROUPS",
    "PXE_MAPPING_FILE_PATH",
    # Messages
    "TEST_PASSED",
    "TEST_FAILED",
    "TEST_SKIPPED",
]
