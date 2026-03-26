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
Discovery Messages Module.

Exports all discovery-related test names, log messages, and assertion messages.
"""

from .discovery_msgs import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)
from .admin_debug_packages_msgs import (
    ADMIN_DEBUG_TEST_NAMES,
    ADMIN_DEBUG_LOG_MSGS,
    ADMIN_DEBUG_ASSERT_MSGS,
)

__all__ = [
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
    # Admin debug packages
    "ADMIN_DEBUG_TEST_NAMES",
    "ADMIN_DEBUG_LOG_MSGS",
    "ADMIN_DEBUG_ASSERT_MSGS",
]
