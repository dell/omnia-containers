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
    # GitLab server
    "gitlab_runner_container": "Verify gitlab-runner container running",
    "gitlab_url_accessible": "Verify GitLab URL is accessible",
    "gitlab_services_running": "Verify GitLab services are running",
    "gitlab_resources": "Verify GitLab server meets resource requirements",
    "puma_workers": "Verify puma workers configuration",
    "sidekiq_concurrency": "Verify sidekiq concurrency configuration",
    # Project
    "gitlab_project_exists": "Verify GitLab project exists",
    "gitlab_project_visibility": "Verify GitLab project visibility",
    "gitlab_default_branch": "Verify GitLab default branch",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS = {
    # GitLab server - Success
    "container_running": "gitlab-runner container is running: {status}",
    "gitlab_accessible": "GitLab is accessible at {url} (HTTP {code})",
    "gitlab_services_ok": "All GitLab services are running ({count} services)",
    "resources_ok": "GitLab server meets resource requirements",
    "puma_workers_ok": "Puma workers configured correctly: {workers}",
    "sidekiq_ok": "Sidekiq concurrency configured correctly: {concurrency}",
    # GitLab server - Failure
    "container_not_running": "gitlab-runner container not running",
    "gitlab_not_accessible": "GitLab is not accessible at {url}",
    "gitlab_services_failed": "Some GitLab services are not running: {services}",
    "resources_insufficient": "GitLab server does not meet resource requirements",
    "puma_workers_mismatch": "Puma workers mismatch: expected {expected}, actual {actual}",
    "sidekiq_mismatch": "Sidekiq concurrency mismatch: expected {expected}, actual {actual}",
    # Project - Success
    "project_exists": "GitLab project '{name}' exists (ID: {id})",
    "visibility_ok": "Project visibility configured correctly: {visibility}",
    "default_branch_ok": "Default branch configured correctly: {branch}",
    # Project - Failure
    "project_not_found": "GitLab project '{name}' not found",
    "visibility_mismatch": "Project visibility mismatch: expected {expected}, actual {actual}",
    "default_branch_mismatch": "Default branch mismatch: expected {expected}, actual {actual}",
}

# =============================================================================
# ASSERTION MESSAGES
# =============================================================================

TEST_ASSERT_MSGS = {
    # GitLab server
    "container_not_running": (
        "gitlab-runner container not running on GitLab server. "
        "Run gitlab.yml playbook to deploy GitLab"
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
    # Project
    "project_not_found": (
        "GitLab project '{name}' not found"
    ),
    "visibility_mismatch": (
        "Project visibility mismatch. Expected: {expected}, Actual: {actual}"
    ),
    "default_branch_mismatch": (
        "Default branch mismatch. Expected: {expected}, Actual: {actual}"
    ),
    "project_not_exist_for_visibility": (
        "Cannot check visibility - project '{name}' does not exist"
    ),
    "project_not_exist_for_branch": (
        "Cannot check default branch - project '{name}' does not exist"
    ),
}
