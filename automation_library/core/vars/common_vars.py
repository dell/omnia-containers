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
Core Common Variables.

Shared constants used across all core functions.
"""

# =============================================================================
# CONTAINER CONFIGURATION
# =============================================================================

OMNIA_CORE_CONTAINER = "omnia_core"
PODMAN_EXEC_PREFIX = f"podman exec {OMNIA_CORE_CONTAINER} bash -lc"

# =============================================================================
# GIT URL BASE  (shared across upgrade, rollback, prereq, etc.)
# =============================================================================

OMNIA_GIT_RAW_BASE_URL = "https://raw.githubusercontent.com/dell/omnia"
OMNIA_ARTIFACTORY_GIT_RAW_BASE_URL = (
    "https://raw.githubusercontent.com/dell/omnia-artifactory"
)

# =============================================================================
# SSH OPTIONS
# =============================================================================

SSH_OPTS = "-o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes"

# =============================================================================
# CONFIGURATION FILES
# =============================================================================

# Main config file (non-sensitive settings - always plain text)
OMNIA_TEST_CONFIG_FILE = "omnia_test_config.yml"

# Credentials file (sensitive passwords - vault encrypted)
OMNIA_TEST_CREDENTIALS_FILE = "omnia_test_credentials.yml"
OMNIA_TEST_CREDENTIALS_KEY = ".omnia_test_credentials.key"
