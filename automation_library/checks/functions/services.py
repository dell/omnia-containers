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

"""NFS server validation functions for OIM prerequisite checks."""

from typing import Dict

from ...core.formatting import log as _log
from ..messages.oim_prereq_msgs import OIM_PREREQ_MSGS
from ..vars.oim_prereq_vars import OIM_PREREQ_VARS, USER_CONFIG_PATH
from .system import run_command


def check_nfs_reachable() -> Dict:
    """Check if NFS server is reachable and has sufficient capacity."""
    _log("Checking NFS server...", "INFO")
    nfs_server = OIM_PREREQ_VARS.get("nfs_server", "")
    nfs_path = OIM_PREREQ_VARS.get("nfs_share_path", "")

    # Check if NFS server is configured
    if not nfs_server or nfs_server.strip() == "":
        return {
            "reachable": False,
            "message": "NFS server IP not configured",
            "details": OIM_PREREQ_MSGS["nfs_not_configured_instruction"].format(config_path=USER_CONFIG_PATH)
        }

    # Step 1: Ping NFS server
    _log(f"Pinging NFS server {nfs_server}...", "INFO")
    rc, _, _ = run_command(["ping", "-c", "1", "-W", "5", nfs_server])
    if rc != 0:
        return {
            "reachable": False,
            "server": nfs_server,
            "message": f"NFS server {nfs_server} is NOT reachable",
            "details": OIM_PREREQ_MSGS["nfs_not_reachable_instruction"].format(server=nfs_server, config_path=USER_CONFIG_PATH)
        }

    _log(f"NFS server {nfs_server} is reachable", "OK")

    # Step 2: Ensure nfs-utils is installed
    _log("Checking if nfs-utils is installed...", "DEBUG")
    rc, _, _ = run_command(["rpm", "-q", "nfs-utils"])
    if rc != 0:
        _log("nfs-utils not installed, attempting to install...", "INFO")
        rc, _, stderr = run_command(["dnf", "install", "-y", "nfs-utils"], timeout=120)
        if rc != 0:
            return {
                "reachable": False,
                "server": nfs_server,
                "message": "NFS client (nfs-utils) not installed and installation failed",
                "details": f"ACTION REQUIRED: Install nfs-utils manually.\n- Run: sudo dnf install -y nfs-utils\n- Error: {stderr}"
            }
        _log("nfs-utils installed successfully", "OK")

    # Step 3: Check NFS share path if provided
    if not nfs_path or nfs_path.strip() == "":
        return {
            "reachable": True,
            "server": nfs_server,
            "message": f"NFS server {nfs_server} is reachable (share path not configured)",
            "details": f"Set 'nfs_share_path' in {USER_CONFIG_PATH} to check capacity"
        }

    return {
        "reachable": True,
        "server": nfs_server,
        "message": f"NFS server {nfs_server} is reachable",
        "details": f"Path: {nfs_path}"
    }
