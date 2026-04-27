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
GitLab Automation Module

Modular organization of GitLab deployment verification functions
organized by functionality: functions, variables, and messages.

This module automates the gitlab.yml playbook verification for:
- GitLab URL accessibility and services
- GitLab runner container status
- Resource requirements (CPU, memory, storage)
- Puma workers and sidekiq concurrency configuration
- Project existence and catalog sync
"""

from .functions import (
    # Config helpers
    get_gitlab_config,
    get_gitlab_host,
    get_gitlab_https_port,
    get_gitlab_project_name,
    get_provision_password,
    get_gitlab_root_password,
    clear_cache,
    skip_if_build_stream_not_enabled,
    # GitLab verification
    verify_gitlab_url_accessible,
    verify_gitlab_runner_container,
    verify_gitlab_services_running,
    verify_gitlab_resources,
    verify_puma_workers,
    verify_sidekiq_concurrency,
    verify_gitlab_project_exists,
    verify_catalog_synced,
)
from .vars import (
    GITLAB_SERVICES,
    GITLAB_RUNNER_CONTAINER,
    GITLAB_RB_PATH,
)
from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)

__all__ = [
    # Functions - Config helpers
    "get_gitlab_config",
    "get_gitlab_host",
    "get_gitlab_https_port",
    "get_gitlab_project_name",
    "get_provision_password",
    "get_gitlab_root_password",
    "clear_cache",
    "skip_if_build_stream_not_enabled",
    # Functions - GitLab verification
    "verify_gitlab_url_accessible",
    "verify_gitlab_runner_container",
    "verify_gitlab_services_running",
    "verify_gitlab_resources",
    "verify_puma_workers",
    "verify_sidekiq_concurrency",
    "verify_gitlab_project_exists",
    "verify_catalog_synced",
    # Vars
    "GITLAB_SERVICES",
    "GITLAB_RUNNER_CONTAINER",
    "GITLAB_RB_PATH",
    # Messages
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
]
