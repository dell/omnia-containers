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

"""OS and Podman validation functions for OIM prerequisite checks."""

from typing import Dict

from ...core.formatting import log as _log
from ..messages.oim_prereq_msgs import OIM_PREREQ_MSGS
from ..vars.oim_prereq_vars import OIM_PREREQ_VARS, USER_CONFIG_PATH
from .system import run_command, run_shell


def get_os_info() -> Dict:
    """Get OS name, version, and kernel info from remote server."""
    os_info = {"name": "", "version": "", "full": "", "kernel": "", "build": ""}

    # Read /etc/os-release via SSH on remote server
    rc, stdout, _ = run_shell("cat /etc/os-release 2>/dev/null")
    if rc == 0 and stdout:
        for line in stdout.split("\n"):
            if line.startswith("ID="):
                os_info["name"] = line.split("=")[1].strip().strip('"').lower()
            elif line.startswith("VERSION_ID="):
                os_info["version"] = line.split("=")[1].strip().strip('"')
            elif line.startswith("PRETTY_NAME="):
                os_info["full"] = line.split("=", 1)[1].strip().strip('"')

    # Get kernel version via uname -r
    rc, stdout, _ = run_shell("uname -r 2>/dev/null")
    if rc == 0 and stdout:
        os_info["kernel"] = stdout.strip()

    # Get full build info via uname -a
    rc, stdout, _ = run_shell("uname -a 2>/dev/null")
    if rc == 0 and stdout:
        os_info["build"] = stdout.strip()

    return os_info


def validate_os() -> Dict:
    """Validate OS against required OS, version, and kernel."""
    _log("Validating OS...", "INFO")
    os_info = get_os_info()
    required_os = OIM_PREREQ_VARS.get("required_os", "rhel").lower()
    required_version = OIM_PREREQ_VARS.get("required_os_version", "10")
    required_kernel = OIM_PREREQ_VARS.get("required_kernel_version", "")

    if not os_info["name"]:
        return {"passed": False, "os_info": os_info, "message": OIM_PREREQ_MSGS["os_not_detected"]}

    # Check OS name
    actual_os = os_info["name"].lower()
    if not actual_os.startswith(required_os):
        return {
            "passed": False,
            "os_info": os_info,
            "message": f"OS mismatch: {actual_os} != {required_os}",
            "details": f"ACTION REQUIRED: OS does not match.\n- Required: {required_os}\n- Actual: {actual_os}\n- Update 'required_os' in {USER_CONFIG_PATH} if this OS is acceptable."
        }

    # Check OS version
    actual_version = os_info["version"]
    if not actual_version.startswith(required_version):
        return {
            "passed": False,
            "os_info": os_info,
            "message": f"OS version mismatch: {actual_version} != {required_version}",
            "details": f"ACTION REQUIRED: OS version does not match.\n- Required: {required_version}\n- Actual: {actual_version}\n- Update 'required_os_version' in {USER_CONFIG_PATH} or upgrade OS."
        }

    # Check kernel version if required
    if required_kernel and required_kernel.strip():
        actual_kernel = os_info.get("kernel", "")
        if actual_kernel != required_kernel:
            return {
                "passed": False,
                "os_info": os_info,
                "message": f"Kernel version mismatch: {actual_kernel} != {required_kernel}",
                "details": f"ACTION REQUIRED: Kernel version does not match.\n- Required: {required_kernel}\n- Actual: {actual_kernel}\n- Update 'required_kernel_version' in {USER_CONFIG_PATH} or upgrade kernel."
            }

    return {"passed": True, "os_info": os_info, "message": OIM_PREREQ_MSGS["os_check_pass"].format(os_name=os_info["name"], os_version=os_info["version"])}


def check_podman() -> Dict:
    """Check Podman installation and version."""
    _log("Checking Podman installation...", "INFO")
    min_version = OIM_PREREQ_VARS["podman_min_version"]

    rc, stdout, stderr = run_command(["podman", "--version"])
    if rc != 0:
        return {
            "passed": False,
            "message": OIM_PREREQ_MSGS["podman_not_found"],
            "details": f"ACTION REQUIRED: Install Podman.\n- Run: dnf install -y podman\n- Error: {stderr}"
        }

    # Extract version
    import re
    version_match = re.search(r"podman version (\d+\.\d+\.\d+)", stdout)
    if not version_match:
        return {
            "passed": False,
            "message": "Could not parse Podman version",
            "details": f"Output: {stdout}"
        }

    version = version_match.group(1)

    # Simple version comparison (assumes semantic versioning)
    def version_tuple(v):
        return tuple(map(int, v.split('.')))

    if version_tuple(version) >= version_tuple(min_version):
        return {
            "passed": True,
            "message": OIM_PREREQ_MSGS["podman_version_ok"].format(
                version=version, min_version=min_version
            ),
            "details": f"Version: {version}"
        }
    return {
        "passed": False,
        "message": OIM_PREREQ_MSGS["podman_version_low"].format(
            version=version, min_version=min_version
        ),
        "details": f"ACTION REQUIRED: Upgrade Podman.\n- Current: {version}\n- Required: {min_version}+"
    }
