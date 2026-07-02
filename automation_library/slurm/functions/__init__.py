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

from .slurm_func import (
    get_slurm_control_nodes,
    get_slurm_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
    get_all_munge_nodes,
    get_slurm_node_count,
    verify_all_pxe_nodes_in_slurm_cluster,
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
    verify_slurm_nodes_idle,
    verify_login_nodes_idle,
    verify_srun_job,
    verify_sbatch_job,
    verify_root_sbatch_from_login_node,
    verify_root_multi_sbatch_from_login_node,
    verify_root_sbatch_from_multiple_login_nodes,
    verify_drain_undrain_queuing,
    verify_insufficient_resources,
    verify_passwordless_ssh,
    submit_upgrade_sbatch_job,
)
from .slurm_reboot_func import (
    reboot_and_verify_control_nodes,
    reboot_and_verify_slurm_nodes,
    reboot_and_verify_login_nodes,
    reboot_and_verify_login_compiler_nodes,
    reboot_all_slurm_nodes_parallel,
    verify_cloud_init_after_reboot,
    verify_control_node_services_after_reboot,
    verify_compute_node_services_after_reboot,
    verify_login_node_services_after_reboot,
    verify_slurmdbd_active,
    verify_slurmdbd_data_preserved,
    wait_for_nodes_idle_after_reboot,
    verify_sbatch_after_reboot,
    verify_ldap_login_after_reboot,
    verify_ldap_sbatch_after_reboot,
)
from .slurm_ldap_func import (
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

__all__ = [
    # Node discovery
    "get_slurm_control_nodes",
    "get_slurm_nodes",
    "get_login_nodes",
    "get_login_compiler_nodes",
    "get_all_munge_nodes",
    "get_slurm_node_count",
    "verify_all_pxe_nodes_in_slurm_cluster",
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
    "submit_upgrade_sbatch_job",
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
    # Reboot scenarios
    "reboot_and_verify_control_nodes",
    "reboot_and_verify_slurm_nodes",
    "reboot_and_verify_login_nodes",
    "reboot_and_verify_login_compiler_nodes",
    "reboot_all_slurm_nodes_parallel",
    "verify_cloud_init_after_reboot",
    "verify_control_node_services_after_reboot",
    "verify_compute_node_services_after_reboot",
    "verify_login_node_services_after_reboot",
    "verify_slurmdbd_active",
    "verify_slurmdbd_data_preserved",
    "wait_for_nodes_idle_after_reboot",
    "verify_sbatch_after_reboot",
    "verify_ldap_login_after_reboot",
    "verify_ldap_sbatch_after_reboot",
]
