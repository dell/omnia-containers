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
Admin Debug Packages Messages.

Test names, log messages, and assertion messages for admin debug packages.
"""

from typing import Dict

# Test names for display
ADMIN_DEBUG_TEST_NAMES: Dict[str, str] = {
    "config_check": "Admin Debug Packages Configuration Check",
    "json_check": "Admin Debug Packages JSON File Check",
    "packages_installed": "Debug Packages Installation Verification",
}

# Log messages
ADMIN_DEBUG_LOG_MSGS: Dict[str, str] = {
    "config_found": (
        "admin_debug_packages configured with {count} packages"
    ),
    "config_missing": (
        "admin_debug_packages not found in software_config.json"
    ),
    "packages_success": (
        "All {package_count} debug packages installed on "
        "{node_count} nodes"
    ),
    "packages_failed": (
        "{failed_count}/{total_count} nodes have missing packages"
    ),
}

# Assertion messages
ADMIN_DEBUG_ASSERT_MSGS: Dict[str, str] = {
    "config_missing": (
        "admin_debug_packages not configured in "
        "software_config.json. Error: {error}"
    ),
    "packages_missing": (
        "Debug packages missing on some nodes. "
        "Failed nodes: {failed_nodes}. "
        "Total nodes: {total_nodes}. "
        "Summary: {missing_summary}"
    ),
}

__all__ = [
    "ADMIN_DEBUG_TEST_NAMES",
    "ADMIN_DEBUG_LOG_MSGS",
    "ADMIN_DEBUG_ASSERT_MSGS",
]
