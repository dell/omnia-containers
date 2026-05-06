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

"""GitLab Functions Module - exports all verification functions."""

from .shared_func import (
    get_gitlab_config,
    get_gitlab_host,
    get_gitlab_https_port,
    get_gitlab_project_name,
    get_gitlab_project_visibility,
    get_gitlab_default_branch,
    get_gitlab_puma_workers,
    get_gitlab_sidekiq_concurrency,
    get_gitlab_min_resources,
    get_provision_password,
    get_gitlab_root_password,
    clear_cache,
    ssh_to_gitlab,
    skip_if_build_stream_not_enabled,
    skip_if_gitlab_host_not_configured,
)
from .gitlab_func import (
    verify_gitlab_url_accessible,
    verify_gitlab_runner_container,
    verify_gitlab_services_running,
    verify_gitlab_resources,
    verify_puma_workers,
    verify_sidekiq_concurrency,
    verify_gitlab_project_exists,
    verify_gitlab_project_visibility,
    verify_gitlab_default_branch,
    # Install verification
    verify_gitlab_runner_quadlet_exists,
    verify_gitlab_runner_services_status,
    verify_gitlab_server_reachable,
    verify_gitlab_packages_installed,
    # Cleanup verification
    verify_gitlab_runner_container_removed,
    verify_gitlab_runner_quadlet_removed,
    verify_gitlab_runner_services_stopped,
    verify_gitlab_url_not_accessible,
    verify_gitlab_directories_removed,
    verify_gitlab_services_stopped,
    verify_gitlab_packages_removed,
    verify_gitlab_port_free,
    verify_gitlab_pipeline_file_exists,
    verify_gitlab_pipeline_variables,
)

__all__ = [
    # Shared/Config
    "get_gitlab_config",
    "get_gitlab_host",
    "get_gitlab_https_port",
    "get_gitlab_project_name",
    "get_gitlab_project_visibility",
    "get_gitlab_default_branch",
    "get_gitlab_puma_workers",
    "get_gitlab_sidekiq_concurrency",
    "get_gitlab_min_resources",
    "get_provision_password",
    "get_gitlab_root_password",
    "clear_cache",
    "ssh_to_gitlab",
    "skip_if_build_stream_not_enabled",
    "skip_if_gitlab_host_not_configured",
    # GitLab verification
    "verify_gitlab_url_accessible",
    "verify_gitlab_runner_container",
    "verify_gitlab_services_running",
    "verify_gitlab_resources",
    "verify_puma_workers",
    "verify_sidekiq_concurrency",
    "verify_gitlab_project_exists",
    "verify_gitlab_project_visibility",
    "verify_gitlab_default_branch",
    # Install verification
    "verify_gitlab_runner_quadlet_exists",
    "verify_gitlab_runner_services_status",
    "verify_gitlab_server_reachable",
    "verify_gitlab_packages_installed",
    # Cleanup verification
    "verify_gitlab_runner_container_removed",
    "verify_gitlab_runner_quadlet_removed",
    "verify_gitlab_runner_services_stopped",
    "verify_gitlab_url_not_accessible",
    "verify_gitlab_directories_removed",
    "verify_gitlab_services_stopped",
    "verify_gitlab_packages_removed",
    "verify_gitlab_port_free",
    "verify_gitlab_pipeline_file_exists",
    "verify_gitlab_pipeline_variables",
]
