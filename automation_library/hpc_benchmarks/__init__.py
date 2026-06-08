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
HPC Benchmarks automation module.

Modules:
- functions: Verification functions for all HPC benchmark staging test cases
- vars: Constants, paths, and command templates
- messages: Test names, log messages, and assertion messages

Spec: TSPEC-HPCBENCH-2026-001 v1.0.0
"""

from .functions import (
    get_x86_64_cluster_nodes,
    get_aarch64_cluster_nodes,
    get_login_compiler_nodes_x86_64,
    get_login_compiler_nodes_aarch64,
    get_all_accessible_nodes,
    verify_x86_64_json_parsing,
    verify_local_repo_sync_x86_64,
    verify_hpc_tools_dir_creation,
    verify_x86_64_artifact_copy,
    verify_msr_safe_x86_64_only,
    verify_container_first_guidance,
    verify_source_only_delivery,
    verify_per_tool_staging_report,
    verify_e2e_provisioning_x86_64,
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
from .vars import (
    X86_64_NODE_FUNCTIONAL_GROUP,
    AARCH64_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_X86_64_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_AARCH64_FUNCTIONAL_GROUP,
    SLURM_CUSTOM_JSON_X86_64,
    SLURM_CUSTOM_JSON_AARCH64,
    OFFLINE_REPO_X86_64_TARBALL,
    OFFLINE_REPO_AARCH64_TARBALL,
    HPC_TOOLS_BASE,
    X86_64_BENCHMARK_DIRS,
    AARCH64_BENCHMARK_DIRS,
    X86_64_ONLY_DIRS,
    X86_64_BENCHMARK_PACKAGES,
    AARCH64_BENCHMARK_PACKAGES,
    CONTAINER_FIRST_PACKAGE,
    TOOL_TO_DIR,
)
from .messages import TEST_NAMES, TEST_LOG_MSGS, TEST_ASSERT_MSGS

__all__ = [
    # Node lookup
    "get_x86_64_cluster_nodes",
    "get_aarch64_cluster_nodes",
    "get_login_compiler_nodes_x86_64",
    "get_login_compiler_nodes_aarch64",
    "get_all_accessible_nodes",
    # Functional verification
    "verify_x86_64_json_parsing",
    "verify_local_repo_sync_x86_64",
    "verify_hpc_tools_dir_creation",
    "verify_x86_64_artifact_copy",
    "verify_msr_safe_x86_64_only",
    "verify_container_first_guidance",
    "verify_source_only_delivery",
    "verify_per_tool_staging_report",
    "verify_e2e_provisioning_x86_64",
    "verify_nfs_accessibility",
    "verify_airgapped_staging",
    "verify_post_staging_validation",
    "verify_rhel_compatibility",
    "verify_cuda_flow_unaffected",
    "verify_nvhpc_flow_unaffected",
    "verify_container_image_flow_unaffected",
    "verify_openmpi_unaffected",
    "verify_existing_hpc_dirs_preserved",
    # Regression
    # Performance
    # Negative / Error
    "verify_missing_artifact_graceful_skip",
    "verify_malformed_json_failure",
    "verify_msrsafe_aarch64_validation_error",
    "verify_geopm_aarch64_warning",
    "verify_nfs_unavailable_failure",
    "verify_unsupported_package_type",
    # Vars
    "X86_64_NODE_FUNCTIONAL_GROUP",
    "AARCH64_NODE_FUNCTIONAL_GROUP",
    "LOGIN_COMPILER_X86_64_FUNCTIONAL_GROUP",
    "LOGIN_COMPILER_AARCH64_FUNCTIONAL_GROUP",
    "SLURM_CUSTOM_JSON_X86_64",
    "SLURM_CUSTOM_JSON_AARCH64",
    "OFFLINE_REPO_X86_64_TARBALL",
    "OFFLINE_REPO_AARCH64_TARBALL",
    "HPC_TOOLS_BASE",
    "X86_64_BENCHMARK_DIRS",
    "AARCH64_BENCHMARK_DIRS",
    "X86_64_ONLY_DIRS",
    "X86_64_BENCHMARK_PACKAGES",
    "AARCH64_BENCHMARK_PACKAGES",
    "CONTAINER_FIRST_PACKAGE",
    "TOOL_TO_DIR",
    # Messages
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
]
