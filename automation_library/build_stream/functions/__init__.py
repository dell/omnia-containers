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

"""Build Stream Functions Module."""

from .shared_func import (
    get_build_stream_config,
    get_build_stream_host_ip,
    get_build_stream_port,
    get_gitlab_host,
    get_gitlab_https_port,
    get_gitlab_project_name,
    get_gitlab_default_branch,
    get_postgres_user,
    ssh_to_gitlab,
    clear_cache,
    skip_if_build_stream_not_enabled,
    get_allow_pipeline_cancel,
    get_image_identifier,
    get_catalog_name,
)

from .api_func import (
    check_build_stream_health,
    get_catalog_roles,
    get_stage_log_path,
    verify_registry_images,
    verify_s3_boot_images,
)

from .db_func import (
    verify_postgres_tables,
    get_job_by_id,
    get_latest_job,
    get_job_stages,
    get_stage_state,
    verify_stage_completed,
    get_images_for_job,
    get_image_groups_for_job,
    get_all_image_groups,
)

from .gitlab_func import (
    verify_gitlab_server_running,
    verify_gitlab_runner_running,
    get_gitlab_root_token,
    list_pipelines,
    get_pipeline_status,
    get_pipeline_jobs,
    cancel_pipeline,
    get_child_pipeline_id,
    get_pipeline_jobs_by_stage,
    play_manual_job,
    trigger_pipeline_with_variables,
    upload_catalog_file,
    commit_pxe_mapping_file,
    wait_for_pipeline_triggered,
    get_gitlab_file,
    commit_gitlab_file,
)

from .generated_input_func import (
    get_omnia_branch,
    clone_omnia_repo,
    cleanup_omnia_clone,
    get_software_config,
    compare_software_json,
    verify_generated_inputs,
)

from .pipeline_func import (
    trigger_build_pipeline,
    trigger_deploy_pipeline,
    select_image_for_deploy,
    play_trigger_job,
    play_deploy_stage_job,
    play_cleanup_stage_job,
    trigger_cleanup_pipeline,
    select_image_for_cleanup,
    wait_for_cleanup_completion,
    wait_for_stage_completion,
    monitor_pipeline_stages,
    get_pipeline_stage_status,
)
