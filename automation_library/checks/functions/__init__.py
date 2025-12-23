# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Prerequisite Check Functions

Modular organization of OIM prerequisite validation functions
organized by functionality: system, hardware, network, services, repository, and validation.
"""

# Import all functions to maintain compatibility
from .main import run_all_prereq_checks
from .system import configure_hostname
from .hardware import check_ipmi_tool, install_ipmi_tool, get_hardware_inventory, validate_hardware
from .network import validate_network_interfaces, configure_pxe_nic, check_internet
from .services import check_nfs_reachable
from .repository import ensure_git_installed, clone_omnia_repo, build_container_images, download_omnia_sh
from .validation import validate_os, check_podman

__all__ = [
    "run_all_prereq_checks",
    "configure_hostname", 
    "check_ipmi_tool",
    "install_ipmi_tool",
    "get_hardware_inventory",
    "validate_hardware",
    "validate_network_interfaces",
    "configure_pxe_nic", 
    "check_internet",
    "check_nfs_reachable",
    "ensure_git_installed",
    "clone_omnia_repo",
    "build_container_images",
    "download_omnia_sh",
    "validate_os",
    "check_podman"
]
