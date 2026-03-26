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
Admin Debug Packages Module.

This module provides functions for verifying admin debug packages installation
on cluster nodes. It checks that all packages defined in admin_debug_packages.json
are installed on all nodes.

Organized by functionality: functions, variables, and messages.
"""

from .functions import (
    verify_admin_debug_packages_config,
    verify_debug_packages_installed,
    get_packages_from_json,
)
from .vars import (
    ADMIN_DEBUG_PACKAGES_JSON,
    SOFTWARE_CONFIG_PATH,
    CONTAINER_NAME,
)
from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)

__all__ = [
    # Functions
    "verify_admin_debug_packages_config",
    "verify_debug_packages_installed",
    "get_packages_from_json",
    # Variables
    "ADMIN_DEBUG_PACKAGES_JSON",
    "SOFTWARE_CONFIG_PATH",
    "CONTAINER_NAME",
    # Messages
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
]
