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
Install OS - Variables and Constants.

This module contains all constants, paths, timeouts, and configuration
defaults for the install_os automation.
"""

from typing import Dict, Any, List

# =============================================================================
# INSTALL OS VARIABLES
# =============================================================================

INSTALL_OS_VARS: Dict[str, Any] = {
    # Default paths
    "default_iso_source_path": "/opt/omnia/rhel_10.0_aarch64.iso",
    "default_iso_target_directory": "/opt/omnia/iso_output",
    "default_kickstart_template": "admin_aarch64",
    "manifest_filename": "install_manifest.yml",
    # Container
    "container_name": "omnia_core",
    "install_os_workdir": "/omnia/utils/install_os",
    "install_os_arm_node_workdir": "/omnia/utils/install_os_arm_node",
    # Timeouts
    "ssh_timeout": 10,
    "idrac_timeout": 30,
    "post_install_ssh_timeout": 600,
    "post_install_ssh_retry_interval": 30,
    # Retry configuration
    "idrac_retry_count": 3,
    "idrac_retry_delay": 10,
    # Expected values
    "expected_os_version": "10",
    "expected_arch": "aarch64",
}

# Required ISO tooling
REQUIRED_TOOLS: List[str] = [
    "xorrisofs",
    "isomd5sum",
]

# Add to INSTALL_OS_VARS for backward compat
INSTALL_OS_VARS["required_tools"] = REQUIRED_TOOLS
