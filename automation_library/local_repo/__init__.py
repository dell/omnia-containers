# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Local Repo Functions

Modular organization of Local Repo deployment and management functions
organized by functionality: functions, variables, and messages.
"""

# Import specific items to avoid circular imports
# Note: Import functions first, then vars and messages to avoid circular dependency
from .functions.local_repo_func import (
    check_container_running,
    run_in_omnia_core,
    read_file_in_omnia_core,
    check_pulp_cli_repository_list,
    check_pulp_api_status,
    check_software_download_status,
    check_per_software_package_status,
    check_pulp_repositories_synced,
    check_pulp_distributions_published,
    check_container_repos_synced,
    check_file_repos_synced,
    check_pulp_content_accessible,
    check_software_packages_in_pulp,
    load_software_config,
    check_rhel10_base_repos_in_pulp,
    check_aarch64_repos_in_pulp,
    check_epel_repos_in_pulp,
    check_crb_repos_in_pulp,
    check_slurm_repo_in_pulp,
    check_cuda_packages_in_pulp,
    check_openmpi_ucx_packages_in_pulp,
    check_openldap_packages_in_pulp,
    check_multiarch_repo_segregation,
    check_subscription_status,
    check_software_config_json_valid,
    check_pulp_repo_metadata_present,
)
from .vars.local_repo_vars import (
    OMNIA_CORE_CONTAINER,
    PULP_CONTAINER,
    LOG_BASE_PATH,
    ARCH_LIST,
    PULP_CONTENT_PORT,
    PULP_CONTENT_SCHEME,
    PULP_API_TIMEOUT_SECONDS,
)
from .messages.local_repo_msgs import (
    TEST_VARS, TEST_NAMES, TEST_LOG_MSGS, TEST_ASSERT_MSGS,
)
