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

from .apptainer_func import (
    # Node discovery
    get_slurm_control_nodes,
    get_slurm_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
    # TC1
    verify_apptainer_installed_on_all_slurm_nodes,
    # TC2
    verify_download_script_reads_image_list,
    # TC3
    verify_download_images_only_from_pulp,
    # TC_DL
    verify_run_download_script,
    # TC4
    verify_sif_download_does_not_increase_ram,
    # TC5
    verify_sif_files_in_container_images_dir,
    # TC6
    verify_sif_file_format_validation,
    # TC7
    verify_sif_file_permissions,
    # TC8
    verify_script_skips_already_downloaded_sif,
    # TC9
    verify_script_handles_missing_images_gracefully,
    # TC10
    verify_submit_single_node_apptainer_job,
    # TC11
    verify_submit_multi_node_apptainer_job,
    # TC12
    verify_no_root_required_for_apptainer,
    # TC13
    verify_sif_readable_by_ldap_user,
    # TC14
    verify_submit_apptainer_job_as_ldap_user,
    # TC15
    verify_sif_reuse_without_redownload,
    # TC16
    verify_sif_image_integrity,
    # TC17
    verify_execute_multiple_apptainer_jobs_concurrently,
    # TC18
    verify_job_with_invalid_sif_file,
    # TC19
    verify_sif_permission_600_fails_job,
    # TC20
    verify_gpu_accessible_in_apptainer_container,
    # TC21
    verify_gpu_count_correct_in_container,
    # TC22
    verify_execute_cuda_workload_in_container,
    # TC23
    verify_gpu_memory_allocation_in_container,
    # TC24
    verify_infiniband_accessible_in_container,
    # TC25
    verify_nfs_mount_visibility_in_container,
    # TC26
    verify_slurm_env_vars_in_container,
    # TC27
    verify_job_array_execution_in_containers,
    # TC28
    verify_container_cleanup_after_job_failure,
    # TC29
    verify_nfs_and_sif_accessible_after_reboot,
    # TC30
    verify_container_execution_post_reboot,
    # TC31
    verify_download_script_works_after_reboot,
)
