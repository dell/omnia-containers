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
Local Repo - Configuration Constants.

Pure constants used by local_repo verification functions.
All dynamic configuration is read at runtime via core/load_inputs.py.

Author: Dell Technologies
"""

from automation_library.core.vars import (
    OMNIA_CORE_CONTAINER as _CORE_CONTAINER,
    LOCAL_REPO_LOG_PATH as _CORE_LOG_PATH,
)

# =============================================================================
# CONTAINER NAMES
# =============================================================================

OMNIA_CORE_CONTAINER = _CORE_CONTAINER
PULP_CONTAINER = "pulp"

# =============================================================================
# PATHS (inside omnia_core container) - from core vars
# =============================================================================

LOG_BASE_PATH = _CORE_LOG_PATH
SOFTWARE_CSV_FILENAME = "software.csv"
STATUS_CSV_FILENAME = "status.csv"

# Supported architectures
ARCH_LIST = ["x86_64", "aarch64"]

# =============================================================================
# PULP SETTINGS
# =============================================================================

PULP_CONTENT_PORT = 2225
PULP_CONTENT_SCHEME = "https"
PULP_API_STATUS_URI = "/pulp/api/v3/status/"
PULP_CONTENT_PATH_PREFIX = "/pulp/content/"

# =============================================================================
# TIMEOUTS
# =============================================================================

PULP_API_TIMEOUT_SECONDS = 300
CURL_CONNECT_TIMEOUT = 10
