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
User Registry - Configuration Constants.

Constants used by user_registry verification functions.
All dynamic configuration is read at runtime from local_repo_config.yml
inside the omnia_core container.

Author: Dell Technologies
"""

from automation_library.core import (
    INPUT_BASE_PATH as _INPUT_BASE_PATH,
)

# =============================================================================
# INPUT FILES
# =============================================================================

LOCAL_REPO_CONFIG_FILE = "local_repo_config.yml"
LOCAL_REPO_CONFIG_PATH = f"{_INPUT_BASE_PATH}/{LOCAL_REPO_CONFIG_FILE}"
USER_REGISTRY_CREDENTIAL_FILE = "user_registry_credential.yml"
USER_REGISTRY_CREDENTIAL_PATH = f"{_INPUT_BASE_PATH}/{USER_REGISTRY_CREDENTIAL_FILE}"

# =============================================================================
# PULP CONTAINER REMOTE NAMING
# =============================================================================

# User registry repos in Pulp are prefixed with this string
USER_REGISTRY_REPO_PREFIX = "container_repo_"
USER_REGISTRY_REMOTE_PREFIX = "user_remote_"

# =============================================================================
# REGISTRY PROTOCOL DETECTION
# =============================================================================

HTTPS_SCHEME = "https"
HTTP_SCHEME = "http"
