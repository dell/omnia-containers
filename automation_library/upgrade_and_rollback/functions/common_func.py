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
Upgrade and Rollback Module - Common Functions.

Shared utility functions used by both upgrade and rollback workflows.
"""

from typing import Dict, Any, Tuple

from ...core import run_on_oim, run_in_container, OIM_METADATA_PATH


def get_oim_metadata(host, container: str = "omnia_core") -> Dict[str, Any]:
    """
    Read oim_metadata.yml from inside the omnia_core container.

    Parses the full metadata file and returns key fields including
    omnia_version, previous_omnia_version, and oim_shared_path.

    Args:
        host: Testinfra host object
        container: Container name (default: omnia_core)

    Returns:
        Dict with:
          - success (bool)
          - omnia_version (str): Current version running
          - previous_omnia_version (str): Previous version if upgrade was done
          - upgrade_backup_dir (str): Backup directory path if exists
          - oim_shared_path (str): Omnia shared path from metadata
          - error (str): Error message if failed
    """
    result = {
        "success": False,
        "omnia_version": "",
        "previous_omnia_version": "",
        "upgrade_backup_dir": "",
        "oim_shared_path": "",
        "error": "",
    }

    cmd = run_in_container(host, f"cat {OIM_METADATA_PATH}", container=container)
    if cmd.rc != 0:
        result["error"] = f"Failed to read {OIM_METADATA_PATH}: {cmd.stderr}"
        return result

    for line in cmd.stdout.strip().split("\n"):
        line = line.strip()
        if line.startswith("omnia_version:"):
            result["omnia_version"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("previous_omnia_version:"):
            result["previous_omnia_version"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("upgrade_backup_dir:"):
            result["upgrade_backup_dir"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("oim_shared_path:"):
            result["oim_shared_path"] = line.split(":", 1)[1].strip().strip('"')

    result["success"] = bool(result["omnia_version"])
    return result


def check_container_service_status(host, container: str = "omnia_core") -> Dict[str, Any]:
    """
    Check if container is running and systemctl service status.

    Provides detailed status to help user understand:
    - Container running normally
    - Container exists but stopped/failed
    - Service not found (omnia not installed)

    Args:
        host: Testinfra host object
        container: Container name (default: omnia_core)

    Returns:
        Dict with:
          - running (bool): True if container is running
          - service_exists (bool): True if systemd service exists
          - service_status (str): active/inactive/failed/not-found
          - container_status (str): Up/Exited/etc from podman
          - error (str): User-friendly error message
    """
    result = {
        "running": False,
        "service_exists": False,
        "service_status": "",
        "container_status": "",
        "error": "",
    }

    # Check podman container status
    ps_cmd = run_on_oim(
        host,
        f"podman ps -a --format '{{{{.Status}}}}' --filter name={container}",
    )
    if ps_cmd.rc == 0 and ps_cmd.stdout.strip():
        result["container_status"] = ps_cmd.stdout.strip().split("\n")[0]
        result["running"] = result["container_status"].lower().startswith("up")

    # Check systemctl service status
    svc_cmd = run_on_oim(
        host,
        f"systemctl is-active {container}.service 2>/dev/null || echo 'not-found'",
    )
    status = svc_cmd.stdout.strip()
    result["service_status"] = status
    result["service_exists"] = status != "not-found"

    # Build user-friendly error message
    if result["running"]:
        return result

    if not result["service_exists"]:
        result["error"] = (
            f"omnia_core service not found. Omnia may not be installed.\n\n"
            f"HOW TO FIX:\n"
            f"  1. Install Omnia with: ./omnia.sh --install\n"
            f"  2. Verify container is running: podman ps | grep {container}"
        )
    elif result["service_status"] == "failed":
        result["error"] = (
            f"omnia_core service is in failed state.\n\n"
            f"HOW TO FIX:\n"
            f"  1. Check service logs: journalctl -u {container}.service -n 50\n"
            f"  2. Restart service: systemctl restart {container}.service\n"
            f"  3. Verify container: podman ps | grep {container}"
        )
    elif result["service_status"] == "inactive":
        result["error"] = (
            f"omnia_core service is inactive (stopped).\n\n"
            f"HOW TO FIX:\n"
            f"  1. Start service: systemctl start {container}.service\n"
            f"  2. Verify container: podman ps | grep {container}"
        )
    else:
        result["error"] = (
            f"omnia_core container is not running "
            f"(status: {result['container_status'] or 'unknown'}).\n\n"
            f"HOW TO FIX:\n"
            f"  1. Check service: systemctl status {container}.service\n"
            f"  2. Check logs: journalctl -u {container}.service -n 50"
        )

    return result


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings (e.g., "2.1.0.0" vs "2.2.0.0").

    Args:
        v1: First version string
        v2: Second version string

    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """
    def parse(v: str) -> Tuple[int, ...]:
        try:
            return tuple(int(x) for x in v.split("."))
        except (ValueError, AttributeError):
            return (0,)

    p1, p2 = parse(v1), parse(v2)
    if p1 < p2:
        return -1
    if p1 > p2:
        return 1
    return 0
