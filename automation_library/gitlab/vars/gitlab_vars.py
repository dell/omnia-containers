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
