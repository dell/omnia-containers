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

"""Discovery Functions Module."""

# Common functions
from .common_func import (
    # SSH error parsing
    parse_ssh_error,
    # SSH key cleanup
    cleanup_ssh_known_hosts,
    # Node retrieval
    get_slurm_control_nodes,
    get_slurm_compute_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
    get_all_slurm_nodes,
    get_k8s_nodes,
    # Skip functions
    skip_if_no_slurm_nodes,
    skip_if_no_k8s_nodes,
    # SSH verification
    verify_ssh_from_core,
    verify_ssh_from_oim,
    # Cloud-init verification
    verify_cloudinit_status,
    # K8s verification
    verify_k8s_nodes_ready,
    verify_k8s_telemetry_pods,
)

# Slurm functions
from .slurm_func import (
    # Enable check functions
    is_openmpi_enabled,
    is_ucx_enabled,
    is_ldms_enabled,
    # Skip functions
    skip_if_openmpi_not_enabled,
    skip_if_ucx_not_enabled,
    skip_if_ldms_not_enabled,
    # Service output formatting helpers
    format_service_status,
    build_service_details,
    # Service verification
    verify_services_on_nodes,
    # Cross-node SSH
    verify_cross_node_ssh,
    # sinfo
    verify_sinfo_nodes,
    # OpenMPI/UCX
    verify_openmpi_installed,
    verify_ucx_installed,
    # LDMS
    verify_ldms_sampler_service,
    verify_ldms_sampler_port,
    verify_ldms_sampler_plugins,
)

# LDAP functions
from .ldap_func import (
    is_openldap_enabled,
    skip_if_openldap_not_enabled,
    apply_slapd_conf_and_verify,
    verify_ldap_user_login_from_oim,
    verify_ldap_user_login_from_core,
    verify_pam_slurm_adopt,
)

# Additional packages functions
from .additional_pkgs_func import (
    verify_additional_packages,
    verify_additional_container_images,
    is_additional_packages_enabled,
    get_allowed_additional_subgroups,
    get_additional_packages_json_path,
    extract_rpm_packages_for_role,
    extract_images_for_role,
    clear_additional_pkgs_cache,
)
