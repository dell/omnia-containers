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
Apptainer Module

Provides test automation functions for Apptainer container workloads on
Omnia-managed Slurm clusters (MD-928).

Covers 31 test cases across three categories:
  - Installation and SIF image management (TC1-TC9)
  - Slurm job execution with containers (TC10-TC28)
  - Reboot resilience / negative scenarios (TC29-TC31)

Organised by functionality: functions, vars, messages.
"""

from .functions import (
    get_slurm_control_nodes,
    get_slurm_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
    verify_apptainer_installed_on_all_slurm_nodes,
    verify_download_script_reads_image_list,
    verify_download_images_only_from_pulp,
    verify_sif_download_does_not_increase_ram,
    verify_sif_files_in_container_images_dir,
    verify_sif_file_format_validation,
    verify_sif_file_permissions,
    verify_script_skips_already_downloaded_sif,
    verify_script_handles_missing_images_gracefully,
    verify_submit_single_node_apptainer_job,
    verify_submit_multi_node_apptainer_job,
    verify_no_root_required_for_apptainer,
    verify_sif_readable_by_ldap_user,
    verify_submit_apptainer_job_as_ldap_user,
    verify_sif_reuse_without_redownload,
    verify_sif_image_integrity,
    verify_execute_multiple_apptainer_jobs_concurrently,
    verify_job_with_invalid_sif_file,
    verify_sif_permission_600_fails_job,
    verify_gpu_accessible_in_apptainer_container,
    verify_gpu_count_correct_in_container,
    verify_execute_cuda_workload_in_container,
    verify_gpu_memory_allocation_in_container,
    verify_infiniband_accessible_in_container,
    verify_nfs_mount_visibility_in_container,
    verify_job_array_execution_in_containers,
    verify_container_cleanup_after_job_failure,
    verify_nfs_and_sif_accessible_after_reboot,
    verify_container_execution_post_reboot,
    verify_download_script_works_after_reboot,
)
from .vars import (
    COMPUTE_NODE_HPC_TOOLS_DIR,
    COMPUTE_NODE_CONTAINER_IMAGES_DIR,
    COMPUTE_NODE_DOWNLOAD_SCRIPT,
    COMPUTE_NODE_CONTAINER_IMAGE_LIST,
    APPTAINER_BINARY,
    SIF_EXTENSION,
    APPTAINER_JOB_TIMEOUT,
    APPTAINER_SACCT_TIMEOUT,
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
    # TC1-TC9 – Installation & SIF management
    "verify_apptainer_installed_on_all_slurm_nodes",
    "verify_download_script_reads_image_list",
    "verify_download_images_only_from_pulp",
    "verify_sif_download_does_not_increase_ram",
    "verify_sif_files_in_container_images_dir",
    "verify_sif_file_format_validation",
    "verify_sif_file_permissions",
    "verify_script_skips_already_downloaded_sif",
    "verify_script_handles_missing_images_gracefully",
    # TC10-TC19 – Slurm job execution
    "verify_submit_single_node_apptainer_job",
    "verify_submit_multi_node_apptainer_job",
    "verify_no_root_required_for_apptainer",
    "verify_sif_readable_by_ldap_user",
    "verify_submit_apptainer_job_as_ldap_user",
    "verify_sif_reuse_without_redownload",
    "verify_sif_image_integrity",
    "verify_execute_multiple_apptainer_jobs_concurrently",
    "verify_job_with_invalid_sif_file",
    "verify_sif_permission_600_fails_job",
    # TC20-TC28 – Advanced / hardware
    "verify_gpu_accessible_in_apptainer_container",
    "verify_gpu_count_correct_in_container",
    "verify_execute_cuda_workload_in_container",
    "verify_gpu_memory_allocation_in_container",
    "verify_infiniband_accessible_in_container",
    "verify_nfs_mount_visibility_in_container",
    "verify_job_array_execution_in_containers",
    "verify_container_cleanup_after_job_failure",
    # TC29-TC31 – Negative / reboot
    "verify_nfs_and_sif_accessible_after_reboot",
    "verify_container_execution_post_reboot",
    "verify_download_script_works_after_reboot",
    # Vars
    "COMPUTE_NODE_HPC_TOOLS_DIR",
    "COMPUTE_NODE_CONTAINER_IMAGES_DIR",
    "COMPUTE_NODE_DOWNLOAD_SCRIPT",
    "COMPUTE_NODE_CONTAINER_IMAGE_LIST",
    "APPTAINER_BINARY",
    "SIF_EXTENSION",
    "APPTAINER_JOB_TIMEOUT",
    "APPTAINER_SACCT_TIMEOUT",
    # Messages
    "TEST_PASSED",
    "TEST_FAILED",
    "TEST_SKIPPED",
]
