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

Contains test names, log messages, and assertion messages for admin debug packages tests.
"""

# Test names for display
TEST_NAMES = {
    "config_check": "Admin Debug Packages Configuration Check",
    "json_check": "Admin Debug Packages JSON File Check",
    "packages_installed": "Debug Packages Installation Verification",
}

# Log messages
TEST_LOG_MSGS = {
    "config_found": "admin_debug_packages configured with {count} packages",
    "config_missing": "admin_debug_packages not found in software_config.json",
    "packages_success": "All {package_count} debug packages installed on {node_count} nodes",
    "packages_failed": "{failed_count}/{total_count} nodes have missing packages",
    "node_check_start": "Checking packages on {hostname} ({admin_ip})",
    "node_check_complete": "{hostname}: {installed}/{total} packages installed",
}

# Assertion messages
TEST_ASSERT_MSGS = {
    "config_missing": (
        "admin_debug_packages not configured in software_config.json. "
        "Error: {error}"
    ),
    "packages_missing": (
        "Debug packages missing on some nodes. "
        "Failed nodes: {failed_nodes}. "
        "Total nodes: {total_nodes}. "
        "Summary: {missing_summary}"
    ),
}

__all__ = [
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
]
