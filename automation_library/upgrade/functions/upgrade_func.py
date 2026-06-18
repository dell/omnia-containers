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
Upgrade Module - Functions.

Functions for verifying the Omnia upgrade workflow:
- Pre-upgrade version check
- Clone new artifactory and build core image
- Run omnia.sh --upgrade
- Post-upgrade verification (backup, version, container cleanup)
"""

from typing import Dict, Any

import yaml

from ...core import (
    run_on_oim,
    run_in_container,
    check_container_running,
    OMNIA_CORE_CONTAINER,
)
from ..vars.upgrade_vars import UPGRADE_VARS


# =============================================================================
# PRE-UPGRADE CHECKS
# =============================================================================

def get_current_omnia_version(host) -> Dict[str, Any]:
    """
    Read the current omnia_version from oim_metadata.yml inside omnia_core.

    Args:
        host: Testinfra host object

    Returns:
        Dict with:
            - success (bool)
            - version (str): Current omnia_version
            - metadata (dict): Full metadata contents
            - error (str): Error message if failed
    """
    container = UPGRADE_VARS["container_name"]
    metadata_path = UPGRADE_VARS["oim_metadata_path"]

    # Check container is running
    container_status = check_container_running(host, container)
    if not container_status.get("running"):
        return {
            "success": False,
            "version": "",
            "metadata": {},
            "error": f"{container} container is not running",
        }

    # Read metadata
    cmd = run_in_container(host, f"cat {metadata_path}", container=container)
    if cmd.rc != 0:
        return {
            "success": False,
            "version": "",
            "metadata": {},
            "error": f"Failed to read {metadata_path}: {cmd.stderr}",
        }

    try:
        metadata = yaml.safe_load(cmd.stdout)
        version = metadata.get("omnia_version", "")
        return {
            "success": True,
            "version": str(version),
            "metadata": metadata,
            "error": "",
        }
    except yaml.YAMLError as e:
        return {
            "success": False,
            "version": "",
            "metadata": {},
            "error": f"Failed to parse metadata YAML: {str(e)}",
        }


def verify_pre_upgrade_state(host) -> Dict[str, Any]:
    """
    Verify the cluster is in the expected pre-upgrade state.

    Checks:
    1. omnia_core container is running
    2. Current version matches upgrade_from_version
    3. If version already matches upgrade_to_version, determine if backup exists

    Args:
        host: Testinfra host object

    Returns:
        Dict with:
            - success (bool): True if ready for upgrade
            - version (str): Current version
            - state (str): 'ready_for_upgrade', 'already_upgraded', 'already_at_target'
            - has_backup (bool): Whether backup folder exists
            - error (str)
    """
    from_version = UPGRADE_VARS["upgrade_from_version"]
    to_version = UPGRADE_VARS["upgrade_to_version"]
    backup_base = UPGRADE_VARS["backup_base_path"]

    # Get current version
    version_result = get_current_omnia_version(host)
    if not version_result["success"]:
        return {
            "success": False,
            "version": "",
            "state": "error",
            "has_backup": False,
            "error": version_result["error"],
        }

    current_version = version_result["version"]

    # Check for backup folder
    backup_check = run_on_oim(host, f"ls -d {backup_base}/backup* 2>/dev/null")
    has_backup = backup_check.rc == 0 and backup_check.stdout.strip() != ""

    # Already at target version
    if current_version == to_version:
        state = "already_upgraded" if has_backup else "already_at_target"
        return {
            "success": False,
            "version": current_version,
            "state": state,
            "has_backup": has_backup,
            "error": "",
        }

    # At expected from_version
    if current_version == from_version:
        return {
            "success": True,
            "version": current_version,
            "state": "ready_for_upgrade",
            "has_backup": has_backup,
            "error": "",
        }

    # At some other version
    return {
        "success": False,
        "version": current_version,
        "state": "unexpected_version",
        "has_backup": has_backup,
        "error": (
            f"Expected version {from_version} but found {current_version}. "
            f"Update 'upgrade.from_version' in omnia_test_config.yml."
        ),
    }


# =============================================================================
# CLONE AND BUILD
# =============================================================================

def clone_upgrade_artifactory(host) -> Dict[str, Any]:
    """
    Clone omnia-artifactory to the upgrade clone path on the OIM server.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, clone_path, error
    """
    repo_url = UPGRADE_VARS["upgrade_repo_url"]
    branch = UPGRADE_VARS["upgrade_repo_branch"]
    clone_path = UPGRADE_VARS["upgrade_clone_path"]
    timeout = UPGRADE_VARS["clone_timeout"]

    # Remove existing directory if present
    run_on_oim(host, f"rm -rf {clone_path}")

    # Create parent directory
    parent_dir = "/".join(clone_path.rsplit("/", 1)[:-1]) or "/"
    run_on_oim(host, f"mkdir -p {parent_dir}")

    # Clone
    cmd = run_on_oim(
        host,
        f"git clone -b {branch} {repo_url} {clone_path}",
    )

    if cmd.rc != 0:
        return {
            "success": False,
            "clone_path": clone_path,
            "error": cmd.stderr or cmd.stdout or "git clone failed",
        }

    # Verify clone
    verify = run_on_oim(host, f"test -f {clone_path}/build_images.sh")
    if verify.rc != 0:
        return {
            "success": False,
            "clone_path": clone_path,
            "error": "build_images.sh not found in cloned repo",
        }

    return {
        "success": True,
        "clone_path": clone_path,
        "branch": branch,
        "error": "",
    }


def build_upgrade_core_image(host) -> Dict[str, Any]:
    """
    Build the new omnia_core container image for upgrade.

    Runs: ./build_images.sh core omnia_branch=<branch> core_tag=<tag>

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, image_tag, error
    """
    clone_path = UPGRADE_VARS["upgrade_clone_path"]
    omnia_branch = UPGRADE_VARS["omnia_branch"]
    core_tag = UPGRADE_VARS["core_tag"]

    # Make script executable
    run_on_oim(host, f"chmod +x {clone_path}/build_images.sh")

    # Build core image
    build_cmd = (
        f"cd {clone_path} && "
        f"./build_images.sh core omnia_branch={omnia_branch} core_tag={core_tag}"
    )
    cmd = run_on_oim(host, build_cmd)

    if cmd.rc != 0:
        return {
            "success": False,
            "image_tag": core_tag,
            "error": cmd.stderr or cmd.stdout or "build_images.sh failed",
        }

    # Verify image exists in podman
    verify = run_on_oim(
        host,
        f"podman images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' "
        f"| grep -E 'omnia_core:{core_tag}'"
    )

    if verify.rc != 0:
        return {
            "success": False,
            "image_tag": core_tag,
            "error": f"Image omnia_core:{core_tag} not found after build",
        }

    return {
        "success": True,
        "image_tag": core_tag,
        "image_name": verify.stdout.strip(),
        "error": "",
    }


# =============================================================================
# UPGRADE EXECUTION
# =============================================================================

def run_omnia_upgrade(host) -> Dict[str, Any]:
    """
    Run omnia.sh --upgrade on the OIM server.

    Automatically provides inputs for any interactive prompts.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, output, error
    """
    clone_path = UPGRADE_VARS["upgrade_clone_path"]
    omnia_sh_path = f"{clone_path}/omnia.sh"

    # Check omnia.sh exists
    check = run_on_oim(host, f"test -f {omnia_sh_path}")
    if check.rc != 0:
        return {
            "success": False,
            "output": "",
            "error": f"omnia.sh not found at {omnia_sh_path}",
        }

    # Make executable
    run_on_oim(host, f"chmod +x {omnia_sh_path}")

    # Run upgrade — pipe 'y' for any confirmation prompts
    upgrade_cmd = f"echo 'y' | {omnia_sh_path} --upgrade"
    cmd = run_on_oim(host, upgrade_cmd)

    if cmd.rc != 0:
        return {
            "success": False,
            "output": cmd.stdout,
            "error": cmd.stderr or cmd.stdout or "omnia.sh --upgrade failed",
        }

    return {
        "success": True,
        "output": cmd.stdout,
        "error": "",
    }


# =============================================================================
# POST-UPGRADE VERIFICATION
# =============================================================================

def verify_backup_folder(host) -> Dict[str, Any]:
    """
    Verify that a backup folder was created during the upgrade.

    The backup folder is typically created under the omnia shared path
    (e.g., /opt/omnia/backup_<timestamp> or /opt/omnia/.backup).

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, backup_path, contents, error
    """
    backup_base = UPGRADE_VARS["backup_base_path"]

    # Look for backup directories (various naming patterns)
    cmd = run_on_oim(
        host,
        f"find {backup_base} -maxdepth 2 -type d "
        f"-name '*backup*' -o -name '.backup' 2>/dev/null | head -5"
    )

    if cmd.rc != 0 or not cmd.stdout.strip():
        return {
            "success": False,
            "backup_path": "",
            "contents": [],
            "error": f"No backup folder found under {backup_base}",
        }

    backup_paths = [p for p in cmd.stdout.strip().split("\n") if p]
    if not backup_paths:
        return {
            "success": False,
            "backup_path": "",
            "contents": [],
            "error": f"No backup folder found under {backup_base}",
        }

    # Use the first found backup path
    backup_path = backup_paths[0]

    # List contents
    ls_cmd = run_on_oim(host, f"ls -la {backup_path}")
    contents = ls_cmd.stdout.strip().split("\n") if ls_cmd.rc == 0 else []

    return {
        "success": True,
        "backup_path": backup_path,
        "all_backup_paths": backup_paths,
        "contents": contents,
        "error": "",
    }


def verify_post_upgrade_version(host) -> Dict[str, Any]:
    """
    Verify that the omnia_core container is now running the target version.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, expected, actual, metadata, error
    """
    to_version = UPGRADE_VARS["upgrade_to_version"]

    version_result = get_current_omnia_version(host)
    if not version_result["success"]:
        return {
            "success": False,
            "expected": to_version,
            "actual": "",
            "metadata": {},
            "error": version_result["error"],
        }

    actual = version_result["version"]
    success = actual == to_version

    return {
        "success": success,
        "expected": to_version,
        "actual": actual,
        "metadata": version_result["metadata"],
        "error": "" if success else (
            f"Expected version {to_version} but found {actual}"
        ),
    }


def verify_no_old_container(host) -> Dict[str, Any]:
    """
    Verify that no old omnia_core container (from pre-upgrade) is still running.

    Checks:
    1. Only one omnia_core container is running
    2. The running container has the correct (new) version

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, running_containers, error
    """
    # List all containers with omnia_core in the name
    cmd = run_on_oim(
        host,
        "podman ps -a --format '{{.ID}} {{.Names}} {{.Status}} {{.Image}}' "
        "| grep -i omnia_core"
    )

    containers = []
    if cmd.rc == 0 and cmd.stdout.strip():
        for line in cmd.stdout.strip().split("\n"):
            parts = line.split(None, 3)
            if len(parts) >= 3:
                containers.append({
                    "id": parts[0],
                    "name": parts[1],
                    "status": parts[2],
                    "image": parts[3] if len(parts) > 3 else "",
                })

    # Count running containers
    running = [c for c in containers if "Up" in c.get("status", "")]

    if len(running) > 1:
        details = "; ".join(
            f"{c['name']}({c['id'][:12]}) image={c['image']}"
            for c in running
        )
        return {
            "success": False,
            "running_containers": running,
            "all_containers": containers,
            "error": f"Multiple omnia_core containers running: {details}",
        }

    if len(running) == 0:
        return {
            "success": False,
            "running_containers": [],
            "all_containers": containers,
            "error": "No omnia_core container is running after upgrade",
        }

    # Exactly one running — verify it has the new version
    version_result = get_current_omnia_version(host)
    to_version = UPGRADE_VARS["upgrade_to_version"]

    if version_result["success"] and version_result["version"] == to_version:
        return {
            "success": True,
            "running_containers": running,
            "all_containers": containers,
            "error": "",
        }

    return {
        "success": False,
        "running_containers": running,
        "all_containers": containers,
        "error": (
            f"Running container version is {version_result.get('version', 'unknown')}, "
            f"expected {to_version}"
        ),
    }
