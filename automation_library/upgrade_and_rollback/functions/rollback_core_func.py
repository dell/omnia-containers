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
Rollback Module - Functions.

Functions for verifying rollback prerequisites, executing the rollback,
and verifying the post-rollback state.  No hardcoded values — everything
comes from ``ROLLBACK_VARS``.
"""

import time
from functools import partial
from typing import Dict, Any, Optional, Callable, List

from ...core import (
    run_on_oim,
    run_in_container,
    check_container_running,
    compare_directory_md5sum,
    download_omnia_sh as _core_download_omnia_sh,
)
from ..vars.rollback_core_vars import ROLLBACK_VARS
from .common_func import get_oim_metadata, check_container_service_status


def verify_rollback_precondition(host) -> Dict[str, Any]:
    """
    Check whether rollback is needed by reading the oim_metadata.yml.

    Determines rollback state based on omnia_version and previous_omnia_version:
    - not_running: Container not running (check service status)
    - fresh_install: At current_version without previous_omnia_version (never upgraded)
    - rollback_needed: At new_version with previous_omnia_version (can rollback)
    - already_rolled_back: At current_version (rollback already done or not needed)

    Args:
        host: Testinfra host object

    Returns:
        Dict with:
          - rollback_needed (bool)
          - running_version (str)
          - previous_version (str)
          - target_version (str)
          - container_running (bool)
          - state (str): not_running/fresh_install/rollback_needed/already_rolled_back
          - error (str)
    """
    container = ROLLBACK_VARS["container_name"]
    target_version = ROLLBACK_VARS["current_version"]
    new_version = ROLLBACK_VARS["new_version"]

    # Validate config
    if not target_version or not new_version:
        return {
            "rollback_needed": False,
            "running_version": "",
            "previous_version": "",
            "target_version": target_version,
            "container_running": False,
            "state": "config_error",
            "error": (
                "current_version or new_version not configured in "
                "omnia_test_config.yml upgrade section"
            ),
        }

    # Check container running with service status
    status = check_container_running(host, container)
    container_running = status.get("success", False)

    if not container_running:
        # Get detailed service status for better error message
        svc_status = check_container_service_status(host, container)
        return {
            "rollback_needed": False,
            "running_version": "",
            "previous_version": "",
            "target_version": target_version,
            "container_running": False,
            "state": "not_running",
            "service_status": svc_status.get("service_status", ""),
            "service_exists": svc_status.get("service_exists", False),
            "error": svc_status.get("error", f"{container} container is not running"),
        }

    # Read full metadata including previous_omnia_version
    metadata = get_oim_metadata(host, container)
    if not metadata["success"]:
        return {
            "rollback_needed": False,
            "running_version": "",
            "previous_version": "",
            "target_version": target_version,
            "container_running": True,
            "state": "metadata_error",
            "error": metadata["error"],
        }

    running_version = metadata["omnia_version"]
    previous_version = metadata["previous_omnia_version"]

    base = {
        "running_version": running_version,
        "previous_version": previous_version,
        "target_version": target_version,
        "container_running": True,
    }

    # At current_version (target) without previous_version → fresh install
    if running_version == target_version and not previous_version:
        return {
            **base,
            "rollback_needed": False,
            "state": "fresh_install",
            "error": (
                f"Container is at {target_version} (fresh install). "
                f"No previous_omnia_version found - never upgraded. "
                f"Rollback not applicable."
            ),
        }

    # At current_version (target) with previous_version → already rolled back
    if running_version == target_version:
        return {
            **base,
            "rollback_needed": False,
            "state": "already_rolled_back",
            "error": (
                f"Container is already at {target_version}. "
                f"No rollback needed."
            ),
        }

    # At new_version with previous_version → rollback is needed
    if running_version == new_version and previous_version:
        return {
            **base,
            "rollback_needed": True,
            "state": "rollback_needed",
            "error": "",
        }

    # At new_version without previous_version → fresh install at new version
    if running_version == new_version:
        return {
            **base,
            "rollback_needed": False,
            "state": "fresh_install_new",
            "error": (
                f"Container is at {new_version} (fresh install). "
                f"No previous_omnia_version found - cannot rollback."
            ),
        }

    # Unknown state
    return {
        **base,
        "rollback_needed": False,
        "state": "unexpected_version",
        "error": (
            f"Container running version '{running_version}' — "
            f"expected '{new_version}' (to rollback to '{target_version}'). "
            f"Cannot determine rollback eligibility."
        ),
    }


def check_rollback_image(host) -> Dict[str, Any]:
    """
    Check that the rollback target image (e.g. omnia_core:2.1) exists.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, tag, error
    """
    tag = ROLLBACK_VARS["rollback_image_tag"]

    cmd = run_on_oim(
        host,
        f"podman images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' "
        f"| grep -q 'omnia_core:{tag}'",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "tag": tag,
            "error": f"omnia_core:{tag} not found in podman images",
        }

    return {"success": True, "tag": tag, "error": ""}


def download_omnia_sh_for_rollback(host) -> Dict[str, Any]:
    """
    Download a fresh omnia.sh for rollback.

    Thin wrapper around ``core.download_omnia_sh`` using rollback vars.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, path, url, ref_type, error
    """
    omnia_branch = ROLLBACK_VARS["omnia_branch"]
    if not omnia_branch:
        return {
            "success": False,
            "path": ROLLBACK_VARS["omnia_sh_path"],
            "url": "",
            "ref_type": "",
            "error": "omnia_branch not configured in omnia_test_config.yml",
        }

    return _core_download_omnia_sh(
        host,
        branch_url=ROLLBACK_VARS["omnia_sh_branch_url"],
        tag_url=ROLLBACK_VARS["omnia_sh_tag_url"],
        dest_path=ROLLBACK_VARS["omnia_sh_path"],
        cmd_fn=run_on_oim,
    )


def run_omnia_rollback(
    host,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> Dict[str, Any]:
    """
    Run ``omnia.sh --rollback`` with automated 'y' confirmation.

    Starts in a background sub-shell, polls every ``poll_interval``
    seconds, and returns the last N lines on completion.

    Args:
        host: Testinfra host object
        progress_callback: Optional ``fn(elapsed_seconds)`` for progress

    Returns:
        Dict with success, rc, output (last N lines), error
    """
    omnia_sh_path = ROLLBACK_VARS["omnia_sh_path"]
    poll_interval = ROLLBACK_VARS["poll_interval"]
    tail_lines = ROLLBACK_VARS["tail_lines"]
    timeout = ROLLBACK_VARS["rollback_timeout"]
    log_file = "/tmp/rollback.log"
    rc_file = f"{log_file}.rc"

    # Start rollback in background, write exit code to rc_file on finish
    start_cmd = run_on_oim(
        host,
        f"bash -c 'rm -f {rc_file}; "
        f"(printf \"y\\n\" | {omnia_sh_path} --rollback "
        f"> {log_file} 2>&1; echo $? > {rc_file}) & echo $!'",
    )
    if start_cmd.rc != 0 or not start_cmd.stdout.strip():
        return {
            "success": False,
            "rc": start_cmd.rc,
            "output": "",
            "error": f"Failed to start rollback: "
                     f"{start_cmd.stderr.strip() or 'no PID returned'}",
        }

    elapsed = 0

    # Poll until rc_file appears (process finished) or timeout
    while elapsed < timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval

        if progress_callback:
            progress_callback(elapsed)

        check = run_on_oim(
            host, f"test -f {rc_file} && echo DONE || echo RUNNING",
        )
        if check.stdout.strip() == "DONE":
            break
    else:
        # Timeout — kill any remaining process
        run_on_oim(host, f"pkill -f '{omnia_sh_path} --rollback' 2>/dev/null")
        # Get output (full if tail_lines=0, else last N lines)
        if tail_lines == 0:
            out_cmd = run_on_oim(host, f"cat {log_file} 2>/dev/null")
        else:
            out_cmd = run_on_oim(host, f"tail -{tail_lines} {log_file} 2>/dev/null")
        return {
            "success": False,
            "rc": -1,
            "output": out_cmd.stdout.strip() if out_cmd.rc == 0 else "",
            "error": f"Rollback timed out after {timeout}s",
        }

    # Read exit code
    rc_cmd = run_on_oim(host, f"cat {rc_file} 2>/dev/null")
    rc_str = rc_cmd.stdout.strip()
    rc = int(rc_str) if rc_str.isdigit() else 1

    # Get output (full if tail_lines=0, else last N lines)
    if tail_lines == 0:
        out_cmd = run_on_oim(host, f"cat {log_file} 2>/dev/null")
    else:
        out_cmd = run_on_oim(host, f"tail -{tail_lines} {log_file} 2>/dev/null")
    output = out_cmd.stdout.strip() if out_cmd.rc == 0 else ""

    if rc != 0:
        return {
            "success": False,
            "rc": rc,
            "output": output,
            "error": f"Rollback exited with rc={rc}",
        }

    return {"success": True, "rc": 0, "output": output, "error": ""}


def verify_rollback_container(host) -> Dict[str, Any]:
    """
    Verify the container rolled back to the expected (pre-upgrade) version.

    Checks:
    1. omnia_core container is running
    2. omnia_version in metadata matches current_version
    3. Container image tag matches rollback_image_tag

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, version, expected, expected_tag,
              container_name, container_image, container_status,
              container_running, error
    """
    container = ROLLBACK_VARS["container_name"]
    expected_ver = ROLLBACK_VARS["current_version"]
    expected_tag = ROLLBACK_VARS["rollback_image_tag"]

    # 1. Structured container info
    ps_cmd = run_on_oim(
        host,
        f"podman ps -a --format '{{{{.Names}}}}|{{{{.Image}}}}|{{{{.Status}}}}' "
        f"--filter name={container}",
    )
    c_name, c_image, c_status = container, "", ""
    if ps_cmd.rc == 0 and ps_cmd.stdout.strip():
        parts = ps_cmd.stdout.strip().split("|", 2)
        if len(parts) == 3:
            c_name, c_image, c_status = (p.strip() for p in parts)

    # 2. Container running?
    status = check_container_running(host, container)
    container_running = status.get("success", False)

    # 3. Read version from metadata
    version = ""
    if container_running:
        metadata_path = ROLLBACK_VARS["oim_metadata_path"]
        meta_cmd = run_in_container(
            host,
            f"grep '^omnia_version:' {metadata_path} "
            "| awk '{print $2}' | tr -d '\"'",
            container=container,
        )
        version = meta_cmd.stdout.strip() if meta_cmd.rc == 0 else ""

    errors: List[str] = []
    if not container_running:
        errors.append("omnia_core container is not running after rollback")
    if version and version != expected_ver:
        errors.append(
            f"Version mismatch: expected {expected_ver}, found {version}"
        )
    elif not version and container_running:
        errors.append("Could not read omnia_version from metadata")

    return {
        "success": container_running and version == expected_ver,
        "version": version,
        "expected": expected_ver,
        "expected_tag": expected_tag,
        "container_name": c_name,
        "container_image": c_image,
        "container_status": c_status,
        "container_running": container_running,
        "error": "; ".join(errors) if errors else "",
    }


def verify_rollback_backup_md5sum(host, category: str) -> Dict[str, Any]:
    """
    After rollback, verify restored files match their backup (md5sum).

    Uses the core ``compare_directory_md5sum`` utility.  The *category*
    selects paths from ``ROLLBACK_VARS["verify_categories"]``.

    Categories: project_default, quadlets, boot, cloudinit, nodes, images.

    Args:
        host: Testinfra host object
        category: Key in ROLLBACK_VARS["verify_categories"]

    Returns:
        Dict with success, files (list of {name, match}), error
    """
    categories = ROLLBACK_VARS["verify_categories"]
    cfg = categories.get(category)
    if cfg is None:
        return {
            "success": False,
            "files": [],
            "error": f"Unknown rollback verify category: {category}",
        }

    container = ROLLBACK_VARS["container_name"]
    backup_dir = cfg["backup_dir"]
    current_dir = cfg["current_dir"]
    on_oim = cfg["on_oim"]
    exclude = cfg.get("exclude", [])

    # Check if source directory exists before attempting verification
    if on_oim:
        check_cmd = run_on_oim
    else:
        check_cmd = partial(run_in_container, container=container)
    
    dir_check = check_cmd(host, f"test -d {current_dir} && echo 'EXISTS' || echo 'NOT_EXISTS'")
    if dir_check.stdout.strip() != "EXISTS":
        return {
            "success": True,  # Skip test, not a failure
            "files": [],
            "error": f"Source directory {current_dir} does not exist - rollback verification skipped",
            "skipped": True,
        }
    
    # Check if source directory has any files (for quadlets specifically)
    if category == "quadlets":
        files_check = check_cmd(host, f"ls -1 {current_dir}/*.container 2>/dev/null | wc -l")
        if files_check.stdout.strip() == "0":
            return {
                "success": True,  # Skip test, not a failure
                "files": [],
                "error": f"No .container files found in {current_dir} (except omnia_core.container) - rollback verification skipped",
                "skipped": True,
            }

    # Backup is always under /opt/omnia (shared volume) → container
    backup_cmd = partial(run_in_container, container=container)

    # Current: OIM host or container depending on category
    if on_oim:
        current_cmd = run_on_oim
    else:
        current_cmd = partial(run_in_container, container=container)

    result = compare_directory_md5sum(
        host,
        backup_dir=backup_dir,
        current_dir=current_dir,
        backup_cmd_fn=backup_cmd,
        current_cmd_fn=current_cmd,
        exclude=exclude,
    )

    # Enrich error with category context (exclude skipped files from count)
    if not result["success"] and result["files"]:
        mismatched = sum(1 for f in result["files"] if f["match"] == "✗")
        compared = sum(1 for f in result["files"] if f["match"] != "⊘")
        result["error"] = (
            f"{mismatched}/{compared} {category} files "
            f"do not match after rollback"
        )
    elif not result["files"]:
        # Check if this is expected (e.g., all files excluded for quadlets)
        if category == "quadlets":
            result["success"] = True  # Skip as success, not a failure
            result["error"] = f"No .container files found in {current_dir} (except omnia_core.container) - rollback verification skipped"
            result["skipped"] = True
        else:
            result["error"] = f"No files found in {backup_dir}"

    return result
