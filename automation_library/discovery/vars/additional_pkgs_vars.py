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
Discovery Module - Additional Packages & Container Images Variables.

Constants and configuration for verifying additional_packages (RPMs)
and additional container images on discovered nodes.
"""

from typing import Dict, List

from automation_library.core.vars import INPUT_BASE_PATH, SOFTWARE_CONFIG_FILE

# =============================================================================
# Config File Paths (inside omnia_core container)
# =============================================================================
SOFTWARE_CONFIG_PATH = f"{INPUT_BASE_PATH}/{SOFTWARE_CONFIG_FILE}"

# Template for additional_packages.json path inside omnia_core container
# Requires: arch, os_type, os_version
ADDITIONAL_PACKAGES_JSON_TEMPLATE = (
    f"{INPUT_BASE_PATH}/config/{{arch}}/{{os_type}}/{{os_version}}/additional_packages.json"
)

# =============================================================================
# Role-Specific Keys (from build_image config.py)
# Roles that can have role-specific entries in additional_packages.json
# =============================================================================
ROLE_SPECIFIC_KEYS: List[str] = [
    "slurm_control_node",
    "slurm_node",
    "login_node",
    "login_compiler_node",
    "service_kube_control_plane_first",
    "service_kube_control_plane",
    "service_kube_node",
]

# Roles that receive container images (Kubernetes roles only)
IMAGE_ROLE_KEYS: List[str] = [
    "service_kube_control_plane",
    "service_kube_control_plane_first",
    "service_kube_node",
]

# =============================================================================
# Architecture Suffix Mapping
# =============================================================================
ARCH_SUFFIXES: Dict[str, str] = {
    "x86_64": "_x86_64",
    "aarch64": "_aarch64",
}

# =============================================================================
# Container Runtime Commands
# =============================================================================
CMD_TEMPLATES: Dict[str, str] = {
    # Check RPM package installed on node
    "rpm_query": "rpm -q {package}",
    # Check container image present via crictl (for K8s nodes)
    "crictl_image_check": "crictl images --output json",
    # Check container image present via podman (fallback)
    "podman_image_check": "podman images --format '{{{{.Repository}}}}:{{{{.Tag}}}}'",
}
