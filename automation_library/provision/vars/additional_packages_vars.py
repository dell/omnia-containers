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
Provision Module - Additional Packages & Repos Variables.

Configuration variables for additional_packages.json and additional_repos testing.
"""

from typing import Dict, List, Tuple

from ...core.vars import INPUT_BASE_PATH, SOFTWARE_CONFIG_PATH

# =============================================================================
# FUNCTIONAL GROUPS
# =============================================================================

# All 8 functional groups that can have additional packages
FUNCTIONAL_GROUPS: List[str] = [
    "service_kube_control_plane_first",
    "service_kube_control_plane",
    "service_kube_node",
    "slurm_control_node",
    "slurm_node",
    "login_node",
    "login_compiler_node",
    "os",  # Special: applies to ALL nodes
]

# Functional groups that are NOT "os" (for per-FG testing)
PER_FG_GROUPS: List[str] = [
    "service_kube_control_plane_first",
    "service_kube_control_plane",
    "service_kube_node",
    "slurm_control_node",
    "slurm_node",
    "login_node",
    "login_compiler_node",
]

# =============================================================================
# NEGATIVE TEST CASES
# =============================================================================

# Negative test cases: (test_fg, wrong_packages_from_fg)
# These define which packages should NOT be on which nodes
NEGATIVE_TEST_CASES: List[Tuple[str, str]] = [
    # Slurm nodes should NOT have K8s-specific packages (e.g. kubelet, images)
    # K8s packages are uniquely assigned, so this is a reliable negative check
    ("slurm_control_node", "service_kube_control_plane"),
    ("slurm_node", "service_kube_node"),

    # Regular login should NOT have compiler packages
    ("login_node", "login_compiler_node"),
]

# =============================================================================
# FILE PATHS (using core module vars)
# =============================================================================

# Software config path (from core)
SOFTWARE_CONFIG_JSON_PATH: str = SOFTWARE_CONFIG_PATH

# additional_packages.json location pattern
ADDITIONAL_PACKAGES_PATH_PATTERN: str = (
    f"{INPUT_BASE_PATH}/config/{{arch}}/{{os}}/{{version}}/additional_packages.json"
)

# local_repo_config.yml location
LOCAL_REPO_CONFIG_PATH: str = f"{INPUT_BASE_PATH}/local_repo_config.yml"

# =============================================================================
# ARCHITECTURES
# =============================================================================

SUPPORTED_ARCHITECTURES: List[str] = ["x86_64", "aarch64"]

# =============================================================================
# SYNC POLICIES
# =============================================================================

VALID_SYNC_POLICIES: List[str] = ["always", "partial"]

# Mapping from software_config repo_config values to Pulp Remote policy values
REPO_CONFIG_TO_PULP_POLICY: Dict[str, str] = {
    "always": "immediate",
    "partial": "on_demand",
}

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

# Maximum number of nodes to test for OS packages (to avoid long test times)
MAX_NODES_FOR_OS_TEST: int = 5

# Pulp query timeout (seconds)
PULP_QUERY_TIMEOUT: int = 30
