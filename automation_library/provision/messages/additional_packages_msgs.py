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
Provision Module - Additional Packages & Repos Messages.

Test names, log messages, and assertion messages for additional_packages.json
and additional_repos testing.
"""

from typing import Dict

# =============================================================================
# TEST NAMES
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    # Per-FG package scoping tests
    "per_fg_packages_positive": "Per-FG Packages - Positive Tests",
    "per_fg_packages_negative": "Per-FG Packages - Negative Tests",
    "os_packages_all_nodes": "OS Packages on All Nodes",

    # additional_repos tests
    "additional_repos_ssl": "additional_repos SSL Configuration",
    "additional_repos_policy": "additional_repos Sync Policy",

    # aarch64 tests
    "aarch64_packages": "aarch64 Additional Packages",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # Per-FG package scoping
    "per_fg_positive_ok": "All FG-specific packages installed correctly",
    "per_fg_positive_fail": "Some FG-specific packages missing on nodes",
    "per_fg_negative_ok": "All negative tests passed - no wrong packages found",
    "per_fg_negative_fail": "Wrong packages found on nodes - FG scoping violated",
    "os_packages_ok": "All OS packages installed on all nodes",
    "os_packages_fail": "OS packages missing on some nodes",

    # additional_repos SSL
    "repos_ssl_ok": "All SSL configurations correct",
    "repos_ssl_fail": "Some repositories have incorrect SSL configuration",
    "repos_ssl_skip": "No SSL-enabled repos configured",

    # additional_repos sync policy
    "repos_policy_ok": "All sync policies correct",
    "repos_policy_fail": "Some repositories have incorrect sync policy",
    "repos_policy_skip": "No repos with explicit policy configured",

    # aarch64
    "aarch64_ok": "aarch64 packages configured ({total} total)",
    "aarch64_fail": "No packages configured for aarch64",
    "aarch64_skip": "No aarch64 additional_packages.json configured",

    # Common
    "no_config": "No additional_packages.json configured",
    "no_repos": "No additional_repos configured",
    "no_nodes": "No nodes found for functional groups",
}

# =============================================================================
# ASSERTION MESSAGES
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    # Per-FG package scoping
    "per_fg_positive_failed": (
        "FG-specific packages not installed correctly.\n"
        "Failed functional groups: {failed_fgs}\n"
        "Details:\n{details}"
    ),
    "per_fg_negative_failed": (
        "FG scoping violated - wrong packages found on wrong nodes.\n"
        "Violations: {violations}\n"
        "Details:\n{details}"
    ),
    "os_packages_failed": (
        "OS packages not installed on all nodes.\n"
        "Failed nodes: {failed_nodes}\n"
        "Details:\n{details}"
    ),

    # additional_repos SSL
    "repos_ssl_failed": (
        "Some repositories have incorrect SSL configuration.\n"
        "Failed repos: {failed_repos}\n"
        "Details:\n{details}"
    ),

    # additional_repos sync policy
    "repos_policy_failed": (
        "Some repositories have incorrect sync policy.\n"
        "Failed repos: {failed_repos}\n"
        "Details:\n{details}"
    ),

    # aarch64
    "aarch64_empty": (
        "aarch64 additional_packages.json is empty.\n"
        "No packages configured for ARM architecture."
    ),
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================

SKIP_MSGS: Dict[str, str] = {
    "no_additional_packages": "No additional_packages.json configured",
    "no_additional_repos": "No additional_repos configured",
    "no_nodes_for_fg": "No nodes found for functional groups",
    "no_ssl_repos": "No SSL-enabled repos configured",
    "no_policy_repos": "No repos with explicit policy configured",
    "no_aarch64_config": "No aarch64 additional_packages.json configured",
}
