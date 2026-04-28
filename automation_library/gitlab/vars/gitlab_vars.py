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
GitLab Variables - Constants for GitLab automation.

For module-specific functions, see:
- shared_func.py - Config loading, caching, skip helpers
- gitlab_func.py - GitLab verification functions
"""

# =============================================================================
# GITLAB SERVICES (on GitLab server, checked via gitlab-ctl status)
# =============================================================================

GITLAB_SERVICES = [
    "puma",
    "sidekiq",
    "nginx",
    "postgresql",
    "redis",
    "gitaly",
    "gitlab-workhorse",
    "logrotate",
]

# =============================================================================
# GITLAB CONTAINER (on GitLab server)
# =============================================================================

GITLAB_RUNNER_CONTAINER = "gitlab-runner"

# =============================================================================
# FILE PATHS (on GitLab server)
# =============================================================================

GITLAB_RB_PATH = "/etc/gitlab/gitlab.rb"
GITLAB_GIT_DATA_PATH = "/var/opt/gitlab/git-data/repositories/@hashed/"

# =============================================================================
# HTTP STATUS CODES
# =============================================================================

GITLAB_SUCCESS_HTTP_CODES = [200, 302]

# =============================================================================
# API CONFIGURATION
# =============================================================================

GITLAB_API_VERSION = "v4"

# =============================================================================
# GITLAB VISIBILITY LEVELS
# =============================================================================
# GitLab visibility level mapping (numeric values used by GitLab Rails)
# private: 0, internal: 10, public: 20

GITLAB_VISIBILITY_LEVELS = {
    "private": "0",
    "internal": "10",
    "public": "20",
}

# =============================================================================
# GITLAB RUNNER PATHS (on GitLab server)
# =============================================================================

GITLAB_RUNNER_QUADLET_DIR = "/etc/containers/systemd"
GITLAB_RUNNER_QUADLET_FILE = "gitlab-runner.container"
GITLAB_RUNNER_SERVICE_NAME = "gitlab-runner"
GITLAB_RUNNER_CONFIG_PATH = "/srv/gitlab-runner/config"

# =============================================================================
# GITLAB SERVICES (on GitLab server)
# =============================================================================

GITLAB_RUNNER_SERVICES = [
    {"name": "gitlab-runner.service", "description": "GitLab Runner Container"},
    {"name": "gitlab-runsvdir.service", "description": "GitLab Runit supervision process"},
]

# =============================================================================
# GITLAB CLEANUP DIRECTORIES (verified after cleanup)
# =============================================================================

GITLAB_CLEANUP_DIRECTORIES = [
    "/etc/gitlab",
    "/var/opt/gitlab",
    "/var/log/gitlab",
    "/opt/gitlab",
]

# =============================================================================
# GITLAB PACKAGES (installed during deployment)
# =============================================================================

GITLAB_INSTALLED_PACKAGES = [
    "gitlab-ce",
]

# =============================================================================
# GITLAB CI/CD PIPELINE CONFIGURATION
# =============================================================================

GITLAB_CI_PIPELINE_FILE = ".gitlab-ci.yml"

# Pipeline variables set by gitlab.yml playbook (from build_stream_oauth_credentials)
GITLAB_PIPELINE_VARIABLES = [
    "GITLAB_API_TOKEN",
    "BSM_API_URL",
    "BSM_API_USERNAME",
    "BSM_API_PASSWORD",
    "BSM_API_CERT",
]

# =============================================================================
# GITLAB FILE PATHS (on GitLab server)
# =============================================================================
GITLAB_ROOT_TOKEN_FILE = "/root/.gitlab_root_token"
GITLAB_INITIAL_ROOT_PASSWORD_FILE = "/etc/gitlab/initial_root_password"

# =============================================================================
# GITLAB CI/CD PIPELINE SOURCE FILE (in omnia_core container)
# =============================================================================
GITLAB_CI_PIPELINE_SOURCE_FILE = "/omnia/gitlab/roles/hosted_gitlab/files/.gitlab-ci.yml"

# =============================================================================
# GITLAB RAILS COMMAND TEMPLATES
# =============================================================================
GITLAB_RAILS_CMD_PROJECT_ID = (
    'gitlab-rails runner "puts Project.find_by(name: '
    '\\\"{project_name}\\\")&.id" 2>/dev/null'
)
GITLAB_RAILS_CMD_PROJECT_VISIBILITY = (
    'gitlab-rails runner "puts Project.find_by(name: '
    '\\\"{project_name}\\\")&.visibility_level" 2>/dev/null'
)
GITLAB_RAILS_CMD_PROJECT_DEFAULT_BRANCH = (
    'gitlab-rails runner "puts Project.find_by(name: '
    '\\\"{project_name}\\\")&.default_branch" 2>/dev/null'
)
GITLAB_RAILS_CMD_ROOT_TOKEN = (
    'gitlab-rails runner "'
    "user = User.find_by(username: 'root'); "
    "token = user.personal_access_tokens.active.first; "
    'puts token&.token" 2>/dev/null'
)
