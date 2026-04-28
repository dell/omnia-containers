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
GitLab Messages - Test names, log messages, and assertion messages.

For module-specific functions, see:
- shared_func.py - Config loading, caching, skip helpers
- gitlab_func.py - GitLab verification functions
"""

# =============================================================================
# TEST NAMES
# =============================================================================

TEST_NAMES = {
    # GitLab Install - Server
    "gitlab_packages_installed": "Verify GitLab packages are installed",
    "gitlab_server_reachable": "Verify GitLab server is reachable",
    "gitlab_runner_container": "Verify gitlab-runner container running",
    "gitlab_runner_quadlet_exists": "Verify gitlab-runner quadlet file exists",
    "gitlab_runner_service_running": "Verify gitlab-runner service is running",
    "gitlab_runner_services_status": "Verify GitLab runner services status",
    "gitlab_url_accessible": "Verify GitLab URL is accessible",
    "gitlab_services_running": "Verify GitLab services are running",
    "gitlab_resources": "Verify GitLab server meets resource requirements",
    "puma_workers": "Verify puma workers configuration",
    "sidekiq_concurrency": "Verify sidekiq concurrency configuration",
    # GitLab Install - Project
    "gitlab_project_exists": "Verify GitLab project exists",
    "gitlab_project_visibility": "Verify GitLab project visibility",
    "gitlab_default_branch": "Verify GitLab default branch",
    "gitlab_pipeline_file_exists": "Verify GitLab pipeline file exists",
    "gitlab_pipeline_variables": "Verify GitLab pipeline variables configured",
    # GitLab Cleanup
    "gitlab_packages_removed": "Verify GitLab packages are removed",
    "gitlab_runner_container_removed": "Verify gitlab-runner container removed",
    "gitlab_runner_quadlet_removed": "Verify gitlab-runner quadlet file removed",
    "gitlab_runner_service_stopped": "Verify gitlab-runner service stopped",
    "gitlab_runner_services_stopped": "Verify GitLab runner services stopped",
    "gitlab_url_not_accessible": "Verify GitLab URL is not accessible",
    "gitlab_directories_removed": "Verify GitLab directories removed",
    "gitlab_services_stopped": "Verify GitLab services stopped",
    "gitlab_port_free": "Verify GitLab port is free",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS = {
    # GitLab Install - Server - Success
    "packages_installed": "GitLab packages installed: {packages}",
    "server_reachable": "GitLab server {host} is reachable",
    "container_running": "gitlab-runner container is running: {status}",
    "quadlet_exists": "gitlab-runner quadlet file exists: {path}",
    "service_running": "gitlab-runner service is running: {status}",
    "runner_services_ok": "All GitLab runner services are running",
    "gitlab_accessible": "GitLab is accessible at {url} (HTTP {code})",
    "gitlab_services_ok": "All GitLab services are running ({count} services)",
    "resources_ok": "GitLab server meets resource requirements",
    "puma_workers_ok": "Puma workers configured correctly: {workers}",
    "sidekiq_ok": "Sidekiq concurrency configured correctly: {concurrency}",
    # GitLab Install - Server - Failure
    "packages_not_installed": "GitLab packages not installed: {packages}",
    "server_not_reachable": "GitLab server {host} is not reachable",
    "container_not_running": "gitlab-runner container not running",
    "quadlet_not_found": "gitlab-runner quadlet file not found: {path}",
    "service_not_running": "gitlab-runner service is not running: {status}",
    "runner_services_failed": "Some GitLab runner services are not running",
    "gitlab_not_accessible": "GitLab is not accessible at {url}",
    "gitlab_services_failed": "Some GitLab services are not running: {services}",
    "resources_insufficient": "GitLab server does not meet resource requirements",
    "puma_workers_mismatch": "Puma workers mismatch: expected {expected}, actual {actual}",
    "sidekiq_mismatch": "Sidekiq concurrency mismatch: expected {expected}, actual {actual}",
    # GitLab Install - Project - Success
    "project_exists": "GitLab project '{name}' exists (ID: {id})",
    "visibility_ok": "Project visibility configured correctly: {visibility}",
    "default_branch_ok": "Default branch configured correctly: {branch}",
    "pipeline_file_exists": "GitLab pipeline file exists: {file}",
    "pipeline_variables_ok": "GitLab pipeline variables configured",
    # GitLab Install - Project - Failure
    "project_not_found": "GitLab project '{name}' not found",
    "visibility_mismatch": "Project visibility mismatch: expected {expected}, actual {actual}",
    "default_branch_mismatch": "Default branch mismatch: expected {expected}, actual {actual}",
    "pipeline_file_not_found": "GitLab pipeline file not found: {file}",
    "pipeline_variables_missing": "GitLab pipeline variables missing: {vars}",
    # GitLab Cleanup - Success
    "packages_removed": "GitLab packages removed: {packages}",
    "container_removed": "gitlab-runner container removed",
    "quadlet_removed": "gitlab-runner quadlet file removed",
    "service_stopped": "gitlab-runner service stopped",
    "runner_services_stopped": "All GitLab runner services stopped",
    "gitlab_not_accessible_cleanup": "GitLab URL is not accessible (cleanup successful)",
    "directories_removed": "GitLab directories removed",
    "services_stopped": "All GitLab services stopped",
    "port_free": "GitLab port {port} is free",
    # GitLab Cleanup - Failure
    "packages_still_installed": "GitLab packages still installed: {packages}",
    "container_still_exists": "gitlab-runner container still exists",
    "quadlet_still_exists": "gitlab-runner quadlet file still exists: {path}",
    "service_still_running": "gitlab-runner service still running: {status}",
    "runner_services_still_running": "Some GitLab runner services still running",
    "gitlab_still_accessible": "GitLab URL still accessible at {url}",
    "directories_still_exist": "GitLab directories still exist: {dirs}",
    "services_still_running": "GitLab services still running: {services}",
    "port_still_in_use": "GitLab port {port} is still in use",
}

# =============================================================================
# ASSERTION MESSAGES
# =============================================================================

TEST_ASSERT_MSGS = {
    # GitLab Install - Server
    "packages_not_installed": (
        "GitLab packages not installed: {packages}. "
        "Run gitlab.yml playbook to deploy GitLab"
    ),
    "server_not_reachable": (
        "GitLab server {host} is not reachable. Check network connectivity"
    ),
    "container_not_running": (
        "gitlab-runner container not running on GitLab server. "
        "Run gitlab.yml playbook to deploy GitLab"
    ),
    "quadlet_not_found": (
        "gitlab-runner quadlet file not found at {path}. "
        "Run gitlab.yml playbook to deploy GitLab"
    ),
    "service_not_running": (
        "gitlab-runner service is not running. "
        "Run 'systemctl start gitlab-runner' on GitLab server"
    ),
    "gitlab_not_accessible": (
        "GitLab is not accessible at {url} (HTTP {code}). "
        "Check network connectivity and GitLab server status"
    ),
    "gitlab_services_not_running": (
        "GitLab services not running: {services}. "
        "Run 'gitlab-ctl start' on GitLab server"
    ),
    "cpu_insufficient": (
        "Insufficient CPU cores. Required: {required}, Available: {actual}"
    ),
    "memory_insufficient": (
        "Insufficient memory. Required: {required}GB, Available: {actual}GB"
    ),
    "storage_insufficient": (
        "Insufficient storage. Required: {required}GB, Available: {actual}GB"
    ),
    "puma_workers_mismatch": (
        "Puma workers mismatch. Expected: {expected}, Actual: {actual}"
    ),
    "sidekiq_mismatch": (
        "Sidekiq concurrency mismatch. Expected: {expected}, Actual: {actual}"
    ),
    # GitLab Install - Project
    "project_not_found": (
        "GitLab project '{name}' not found"
    ),
    "visibility_mismatch": (
        "Project visibility mismatch. Expected: {expected}, Actual: {actual}"
    ),
    "default_branch_mismatch": (
        "Default branch mismatch. Expected: {expected}, Actual: {actual}"
    ),
    "pipeline_file_not_found": (
        "GitLab pipeline file {file} not found in project. "
        "Run gitlab.yml playbook to deploy GitLab"
    ),
    "pipeline_variables_missing": (
        "GitLab pipeline variables missing: {vars}. "
        "Run gitlab.yml playbook to deploy GitLab"
    ),
    # GitLab Cleanup
    "packages_still_installed": (
        "GitLab packages still installed: {packages}. Cleanup failed"
    ),
    "container_still_exists": (
        "gitlab-runner container still exists. Cleanup failed"
    ),
    "quadlet_still_exists": (
        "gitlab-runner quadlet file still exists at {path}. Cleanup failed"
    ),
    "service_still_running": (
        "gitlab-runner service still running. Cleanup failed"
    ),
    "gitlab_still_accessible": (
        "GitLab URL still accessible at {url}. Cleanup failed"
    ),
    "directories_still_exist": (
        "GitLab directories still exist: {dirs}. Cleanup failed"
    ),
    "services_still_running": (
        "GitLab services still running: {services}. Cleanup failed"
    ),
    "port_still_in_use": (
        "GitLab port {port} is still in use. Cleanup failed"
    ),
}
