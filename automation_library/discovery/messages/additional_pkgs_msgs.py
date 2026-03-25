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
Discovery Module - Additional Packages & Container Images Messages.

Test names, log messages, and assertion messages for additional_packages
and additional container images verification.
"""

from typing import Dict

# =============================================================================
# TEST NAMES (displayed in reports)
# =============================================================================
ADDITIONAL_PKGS_TEST_NAMES: Dict[str, str] = {
    "additional_packages": "Verify additional RPM packages installed on nodes",
    "additional_container_images": "Verify additional container images present on K8s nodes",
}

# =============================================================================
# LOG MESSAGES (for TestLogger during test execution)
# =============================================================================
ADDITIONAL_PKGS_LOG_MSGS: Dict[str, str] = {
    # Additional Packages
    "additional_pkgs_success": (
        "All additional RPM packages installed on all nodes "
        "({checked} packages checked)"
    ),
    "additional_pkgs_failed": (
        "{missing} package(s) missing across nodes "
        "({checked} total checked)"
    ),
    "additional_pkgs_skipped": "Additional packages check skipped: {reason}",
    "additional_pkgs_json_path": "additional_packages.json path: {path}",
    "additional_pkgs_enabled": "additional_packages enabled: {enabled}",
    "additional_pkgs_subgroups": "Allowed subgroups: {subgroups}",

    # Additional Container Images
    "additional_images_success": (
        "All additional container images present on K8s nodes "
        "({checked} images checked)"
    ),
    "additional_images_failed": (
        "{missing} image(s) missing across K8s nodes "
        "({checked} total checked)"
    ),
    "additional_images_skipped": "Additional images check skipped: {reason}",
}

# =============================================================================
# ASSERTION MESSAGES (shown when tests fail)
# =============================================================================
ADDITIONAL_PKGS_ASSERT_MSGS: Dict[str, str] = {
    "additional_packages_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ ADDITIONAL PACKAGES VERIFICATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Missing packages: {missing_count}
║ Total checked: {checked_count}
║
║ Failed groups:
{failed_details}
║
║ HOW TO FIX:
║   1. Check additional_packages.json inside omnia_core container:
║      podman exec omnia_core cat {json_path}
║   2. Verify software_config.json has additional_packages enabled:
║      podman exec omnia_core cat /opt/omnia/input/project_default/software_config.json
║   3. Re-run discovery playbook to install missing packages
║   4. Check node connectivity:
║      podman exec omnia_core ssh root@<admin_ip> rpm -q <package>
╚══════════════════════════════════════════════════════════════════════════════╝
""",

    "additional_images_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ ADDITIONAL CONTAINER IMAGES VERIFICATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Missing images: {missing_count}
║ Total checked: {checked_count}
║
║ Failed groups:
{failed_details}
║
║ HOW TO FIX:
║   1. Check additional_packages.json for image entries:
║      podman exec omnia_core cat {json_path}
║   2. Verify images were pulled on K8s nodes:
║      ssh root@<admin_ip> crictl images
║   3. Re-run discovery playbook (fetch_additional_images task)
║   4. Check container runtime on nodes:
║      ssh root@<admin_ip> systemctl status crio
╚══════════════════════════════════════════════════════════════════════════════╝
""",

    "additional_json_load_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ FAILED TO LOAD additional_packages.json
╠══════════════════════════════════════════════════════════════════════════════╣
║ Path: {json_path}
║
║ HOW TO FIX:
║   1. Verify the file exists inside omnia_core:
║      podman exec omnia_core ls -la {json_path}
║   2. Check software_config.json for correct os_type/os_version:
║      podman exec omnia_core cat /opt/omnia/input/project_default/software_config.json
║   3. Ensure build_image playbook was run successfully
╚══════════════════════════════════════════════════════════════════════════════╝
""",
}
