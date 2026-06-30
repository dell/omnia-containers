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

"""HPC Benchmarks functions package."""

from .hpc_benchmarks_func import (
    get_x86_64_cluster_nodes,
    get_aarch64_cluster_nodes,
    get_login_compiler_nodes_x86_64,
    get_login_compiler_nodes_aarch64,
    get_all_accessible_nodes,
    get_all_login_compiler_nodes,
    verify_x86_64_json_parsing,
    verify_aarch64_json_parsing,
    verify_json_parsing,
    verify_local_repo_sync_x86_64,
    verify_local_repo_sync_aarch64,
    verify_local_repo_sync,
    verify_hpc_tools_dir_creation,
    verify_x86_64_artifact_copy,
    verify_aarch64_artifact_copy,
    verify_artifact_copy,
    verify_msr_safe_x86_64_only,
    verify_container_first_guidance,
    verify_source_only_delivery,
    verify_per_tool_staging_report,
    verify_e2e_provisioning_x86_64,
    verify_e2e_provisioning_aarch64,
    verify_e2e_provisioning,
    verify_nfs_accessibility,
    verify_airgapped_staging,
    verify_post_staging_validation,
    verify_rhel_compatibility,
    verify_cuda_flow_unaffected,
    verify_nvhpc_flow_unaffected,
    verify_container_image_flow_unaffected,
    verify_openmpi_unaffected,
    verify_existing_hpc_dirs_preserved,
    verify_missing_artifact_graceful_skip,
    verify_malformed_json_failure,
    verify_msrsafe_aarch64_validation_error,
    verify_geopm_aarch64_warning,
    verify_nfs_unavailable_failure,
    verify_unsupported_package_type,
)

__all__ = [
    "get_x86_64_cluster_nodes",
    "get_aarch64_cluster_nodes",
    "get_login_compiler_nodes_x86_64",
    "get_login_compiler_nodes_aarch64",
    "get_all_accessible_nodes",
    "get_all_login_compiler_nodes",
    "verify_x86_64_json_parsing",
    "verify_aarch64_json_parsing",
    "verify_json_parsing",
    "verify_local_repo_sync_x86_64",
    "verify_local_repo_sync_aarch64",
    "verify_local_repo_sync",
    "verify_hpc_tools_dir_creation",
    "verify_x86_64_artifact_copy",
    "verify_aarch64_artifact_copy",
    "verify_artifact_copy",
    "verify_msr_safe_x86_64_only",
    "verify_container_first_guidance",
    "verify_source_only_delivery",
    "verify_per_tool_staging_report",
    "verify_e2e_provisioning_x86_64",
    "verify_e2e_provisioning_aarch64",
    "verify_e2e_provisioning",
    "verify_nfs_accessibility",
    "verify_airgapped_staging",
    "verify_post_staging_validation",
    "verify_rhel_compatibility",
    "verify_cuda_flow_unaffected",
    "verify_nvhpc_flow_unaffected",
    "verify_container_image_flow_unaffected",
    "verify_openmpi_unaffected",
    "verify_existing_hpc_dirs_preserved",
    "verify_missing_artifact_graceful_skip",
    "verify_malformed_json_failure",
    "verify_msrsafe_aarch64_validation_error",
    "verify_geopm_aarch64_warning",
    "verify_nfs_unavailable_failure",
    "verify_unsupported_package_type",
]
