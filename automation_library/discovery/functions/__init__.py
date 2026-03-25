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
Discovery Functions Module.

Exports all discovery verification functions.
"""

from .discovery_func import (
    # Helper functions
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
    # Certificate renewal
    renew_openchami_cert,
    # Consolidated validation (all nodes, grouped by functional group)
    validate_all_services,
    validate_all_sinfo,
    validate_kubernetes_nodes,
)
from .bmc_func import validate_bmc_group_csv
from .ldap_func import (
    ensure_ldap_test_user,
    validate_ldap_login_non_slurm,
    validate_ldap_login_slurm_nodes,
)
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

__all__ = [
    # Helper functions
    "get_nodes_by_functional_group",
    # Original verification functions
    "verify_nodes_ssh_reachable",
    "verify_ochami_nodes_discovered",
    "verify_nodes_yaml_file",
    "verify_passwordless_ssh",
    "verify_node_hostnames",
    # New validation functions
    "validate_node_boot",
    "validate_packages_by_group",
    "validate_bmc_group_csv",
    # Certificate renewal
    "renew_openchami_cert",
    # Consolidated validation (all nodes, grouped by functional group)
    "validate_all_services",
    "validate_all_sinfo",
    "ensure_ldap_test_user",
    "validate_ldap_login_non_slurm",
    "validate_ldap_login_slurm_nodes",
    "validate_kubernetes_nodes",
    # Additional packages & container images
    "verify_additional_packages",
    "verify_additional_container_images",
    "is_additional_packages_enabled",
    "get_allowed_additional_subgroups",
    "get_additional_packages_json_path",
    "extract_rpm_packages_for_role",
    "extract_images_for_role",
    "clear_additional_pkgs_cache",
]
