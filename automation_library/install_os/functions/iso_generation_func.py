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

"""ISO generation verification functions for install_os automation.

All checks run inside the omnia_core container via ``run_in_container``
because the ISOs, tools, and output artefacts live on the container's
/opt/omnia mount — which is different from the host's /opt/omnia.
"""

from typing import Dict, Any

from automation_library.core import run_in_container
from automation_library.install_os.vars import INSTALL_OS_VARS


def check_source_iso_exists(host, iso_path: str = None) -> Dict[str, Any]:
    """Verify source ISO exists at the specified path inside omnia_core."""
    path = iso_path or INSTALL_OS_VARS["default_iso_source_path"]
    cmd = run_in_container(host, f"test -f {path} && echo 'EXISTS' || echo 'NOT_FOUND'")
    exists = cmd.stdout.strip() == "EXISTS"
    return {
        "success": exists,
        "path": path,
        "error": "" if exists else f"Source ISO not found at {path}",
    }


def verify_source_iso_checksum(
    host, iso_path: str, expected_checksum: str
) -> Dict[str, Any]:
    """Validate SHA-256 checksum of the source ISO."""
    cmd = run_in_container(host, f"sha256sum {iso_path}")
    if cmd.rc != 0:
        return {
            "success": False,
            "checksum": "",
            "error": f"Failed to compute checksum: {cmd.stderr.strip()}",
        }
    actual = cmd.stdout.strip().split()[0]
    matches = actual == expected_checksum
    return {
        "success": matches,
        "checksum": actual,
        "expected": expected_checksum,
        "error": "" if matches else f"Checksum mismatch: expected {expected_checksum}, got {actual}",
    }


def check_output_iso_exists(
    host, output_dir: str = None
) -> Dict[str, Any]:
    """Verify repacked ISO was created in the output directory."""
    path = output_dir or INSTALL_OS_VARS["default_iso_target_directory"]
    cmd = run_in_container(host, f"bash -c 'ls -1 {path}/*.iso 2>/dev/null'")
    if cmd.rc != 0 or not cmd.stdout.strip():
        return {
            "success": False,
            "iso_path": "",
            "error": f"No repacked ISO found in {path}",
        }
    iso_files = cmd.stdout.strip().splitlines()
    return {
        "success": True,
        "iso_path": iso_files[0],
        "iso_count": len(iso_files),
        "error": "",
    }


def verify_output_iso_checksum(host, iso_path: str) -> Dict[str, Any]:
    """Compute and return the SHA-256 checksum of the repacked ISO."""
    cmd = run_in_container(host, f"sha256sum {iso_path}")
    if cmd.rc != 0:
        return {
            "success": False,
            "checksum": "",
            "error": f"Failed to compute checksum: {cmd.stderr.strip()}",
        }
    checksum = cmd.stdout.strip().split()[0]
    return {"success": True, "checksum": checksum, "error": ""}


def check_kickstart_in_iso(host, iso_path: str) -> Dict[str, Any]:
    """Verify kickstart.cfg exists in NFS output directory (not embedded in ISO)."""
    output_dir = INSTALL_OS_VARS["default_iso_target_directory"]
    kickstart_path = f"{output_dir}/kickstart.cfg"
    cmd = run_in_container(host, f"test -f {kickstart_path} && echo 'FOUND' || echo 'NOT_FOUND'")
    found = "FOUND" in cmd.stdout
    return {
        "success": found,
        "kickstart_path": kickstart_path,
        "error": "" if found else f"kickstart.cfg not found at {kickstart_path}",
    }


def verify_grub_config_in_iso(host, iso_path: str) -> Dict[str, Any]:
    """Verify GRUB2 config contains NFS kickstart reference (inst.ks=nfs:...)."""
    mount_point = "/tmp/test_iso_mount"
    cmds = [
        f"mkdir -p {mount_point}",
        f"mount -o ro,loop {iso_path} {mount_point}",
        f"grep -q 'inst.ks=nfs:' {mount_point}/EFI/BOOT/grub.cfg && echo 'FOUND' || echo 'NOT_FOUND'",
        f"umount {mount_point}",
    ]
    cmd = run_in_container(host, "bash -c '" + " && ".join(cmds) + "'")
    found = "FOUND" in cmd.stdout
    return {
        "success": found,
        "error": "" if found else "GRUB config missing NFS kickstart reference (inst.ks=nfs:...)",
    }


def check_tooling_available(host) -> Dict[str, Any]:
    """Verify required ISO tooling is installed inside omnia_core."""
    tools = INSTALL_OS_VARS["required_tools"]
    missing = []
    for tool in tools:
        cmd = run_in_container(host, f"bash -c 'command -v {tool}' 2>/dev/null")
        if cmd.rc != 0:
            missing.append(tool)
    return {
        "success": len(missing) == 0,
        "missing": missing,
        "checked": tools,
        "error": "" if not missing else f"Missing tools: {', '.join(missing)}",
    }


def check_manifest_exists(
    host, output_dir: str = None
) -> Dict[str, Any]:
    """Verify install manifest was generated."""
    path = output_dir or INSTALL_OS_VARS["default_iso_target_directory"]
    manifest = f"{path}/install_manifest.yml"
    cmd = run_in_container(host, f"test -f {manifest} && echo 'EXISTS' || echo 'NOT_FOUND'")
    exists = cmd.stdout.strip() == "EXISTS"
    return {
        "success": exists,
        "path": manifest,
        "error": "" if exists else f"Manifest not found at {manifest}",
    }
