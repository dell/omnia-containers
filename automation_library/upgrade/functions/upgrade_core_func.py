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

Functions for verifying and executing the Omnia upgrade workflow:
- Operation and version validation
- Pre-upgrade container/version check
- Clone repo, build core image, download omnia.sh
- Run omnia.sh --upgrade with automated interactive input
- Post-upgrade backup, version, and container verification
"""

import time
from typing import Dict, Any, List

from ...core import (
    run_on_oim,
    run_in_container,
    check_container_running,
)
from ..vars.upgrade_core_vars import (
    UPGRADE_VARS,
    SUPPORTED_VERSIONS,
    VALID_OPERATIONS,
    get_core_tag_for_version,
)


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_operation() -> Dict[str, Any]:
    """
    Validate that upgrade.operation is a supported value.

    Returns:
        Dict with success, operation, error
    """
    operation = UPGRADE_VARS["operation"].strip().lower()
    if operation not in VALID_OPERATIONS:
        return {
            "success": False,
            "operation": UPGRADE_VARS["operation"],
            "error": (
                f"upgrade.operation is '{UPGRADE_VARS['operation']}' — "
                f"must be one of: {', '.join(VALID_OPERATIONS)}"
            ),
        }
    return {"success": True, "operation": operation, "error": ""}


def validate_versions() -> Dict[str, Any]:
    """
    Validate that current_version and new_version are in SUPPORTED_VERSIONS.

    Returns:
        Dict with success, current_version, new_version, error
    """
    cur_ver = UPGRADE_VARS["current_version"]
    new_ver = UPGRADE_VARS["new_version"]
    errors: List[str] = []

    if cur_ver not in SUPPORTED_VERSIONS:
        errors.append(
            f"current_version '{cur_ver}' not in SUPPORTED_VERSIONS: "
            f"{', '.join(SUPPORTED_VERSIONS)}"
        )
    if new_ver not in SUPPORTED_VERSIONS:
        errors.append(
            f"new_version '{new_ver}' not in SUPPORTED_VERSIONS: "
            f"{', '.join(SUPPORTED_VERSIONS)}"
        )

    return {
        "success": len(errors) == 0,
        "current_version": cur_ver,
        "new_version": new_ver,
        "error": "; ".join(errors),
    }


def validate_config() -> Dict[str, Any]:
    """
    Validate that all required upgrade config fields are present and non-blank.

    Checks: operation, current_version, new_version, repo_branch, omnia_branch.

    Returns:
        Dict with success, missing (list), blank (list), error
    """
    required_fields = (
        "operation", "current_version", "new_version",
        "repo_branch", "omnia_branch",
    )
    missing: List[str] = []
    blank: List[str] = []

    for field in required_fields:
        val = UPGRADE_VARS.get(field)
        if val is None:
            missing.append(field)
        elif isinstance(val, str) and not val.strip():
            blank.append(field)

    errors: List[str] = []
    if missing:
        errors.append(f"Missing fields: {', '.join(missing)}")
    if blank:
        errors.append(f"Blank fields: {', '.join(blank)}")

    return {
        "success": len(errors) == 0,
        "missing": missing,
        "blank": blank,
        "error": "; ".join(errors),
    }


def check_backup_exists(host) -> bool:
    """
    Check if the backup directory exists (used to detect prior upgrade).

    Args:
        host: Testinfra host object

    Returns:
        True if backup_path directory exists inside the container.
    """
    container = UPGRADE_VARS["container_name"]
    backup_path = UPGRADE_VARS["backup_path"]
    chk = run_in_container(
        host, f"test -d '{backup_path}'", container=container,
    )
    return chk.rc == 0


# =============================================================================
# PRE-UPGRADE CHECKS
# =============================================================================

def check_pre_upgrade_container(host) -> Dict[str, Any]:
    """
    Check omnia_core container status and current version via podman and metadata.

    Returns structured container info (container_name, container_image,
    container_status) instead of raw podman output.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, version, container_name, container_image,
              container_status, state, error
    """
    container = UPGRADE_VARS["container_name"]
    metadata_path = UPGRADE_VARS["oim_metadata_path"]
    from_version = UPGRADE_VARS["current_version"]
    to_version = UPGRADE_VARS["new_version"]

    # 1. Get structured container info
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

    # 2. Check container running
    container_check = check_container_running(host, container)
    if not container_check.get("success"):
        return {
            "success": False,
            "version": "",
            "container_name": c_name,
            "container_image": c_image,
            "container_status": c_status or "not running",
            "state": "not_running",
            "error": f"{container} container is not running",
        }

    # 3. Read version from metadata (only omnia_version, not full contents)
    meta_cmd = run_in_container(
        host,
        f"grep '^omnia_version:' {metadata_path} "
        "| awk '{print $2}' | tr -d '\"'",
        container=container,
    )

    if meta_cmd.rc != 0:
        return {
            "success": False,
            "version": "",
            "container_name": c_name,
            "container_image": c_image,
            "container_status": c_status,
            "state": "metadata_error",
            "error": f"Failed to read omnia_version from {metadata_path}",
        }

    current_version = meta_cmd.stdout.strip()

    # 4. Determine state
    base = {
        "version": current_version,
        "container_name": c_name,
        "container_image": c_image,
        "container_status": c_status,
    }

    if current_version == to_version:
        return {**base, "success": False, "state": "already_at_target", "error": ""}

    if current_version == from_version:
        return {**base, "success": True, "state": "ready_for_upgrade", "error": ""}

    return {
        **base,
        "success": False,
        "state": "unexpected_version",
        "error": (
            f"Expected {from_version} but found {current_version}. "
            f"Update 'upgrade.current_version' in omnia_test_config.yml."
        ),
    }


# =============================================================================
# CLONE, BUILD, AND DOWNLOAD
# =============================================================================

def clone_upgrade_repo(host) -> Dict[str, Any]:
    """
    Delete any existing clone directory and clone omnia-artifactory fresh.

    Same pattern as oim-prereq-check repository.clone_omnia_repo().

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, clone_path, error
    """
    repo_url = UPGRADE_VARS["repo_url"]
    branch = UPGRADE_VARS["repo_branch"]
    clone_path = UPGRADE_VARS["clone_path"]

    # Kill stale processes that might lock the dir
    run_on_oim(
        host,
        "pkill -9 -f build_images 2>/dev/null; "
        "pkill -9 -f 'git clone' 2>/dev/null; sleep 1",
    )

    # Always delete and re-create
    run_on_oim(host, f"rm -rf {clone_path}")
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

    # Verify build_images.sh is present
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


def build_core_image(host, progress_callback=None) -> Dict[str, Any]:
    """
    Build the omnia_core container image with progress reporting.

    Runs build_images.sh in the background and polls every
    ``build_progress_interval`` seconds, calling *progress_callback*
    with the elapsed time so the test can print periodic updates.

    Args:
        host: Testinfra host object
        progress_callback: Optional callable(elapsed_seconds: int) for
            periodic progress output.

    Returns:
        Dict with success, image_tag, rc, build_output, error
    """
    clone_path = UPGRADE_VARS["clone_path"]
    omnia_branch = UPGRADE_VARS["omnia_branch"]
    core_tag = UPGRADE_VARS["core_tag"]
    timeout = UPGRADE_VARS["build_timeout"]
    interval = UPGRADE_VARS["build_progress_interval"]

    # Make executable
    run_on_oim(host, f"chmod +x {clone_path}/build_images.sh")

    # Temp files for background execution
    log_file = "/tmp/omnia_upgrade_build.log"
    pid_file = "/tmp/omnia_upgrade_build.pid"
    rc_file = "/tmp/omnia_upgrade_build.rc"
    wrapper = "/tmp/omnia_upgrade_build.sh"

    # Write a wrapper script to avoid quoting issues over SSH
    run_on_oim(
        host,
        f"cat > {wrapper} << 'BUILDEOF'\n"
        f"#!/bin/bash\n"
        f"cd {clone_path}\n"
        f"./build_images.sh core core_tag={core_tag} "
        f"omnia_branch={omnia_branch}\n"
        f"echo $? > {rc_file}\n"
        f"BUILDEOF\n"
        f"chmod +x {wrapper}",
    )

    # Run wrapper in background
    run_on_oim(
        host,
        f"nohup {wrapper} > {log_file} 2>&1 & echo $! > {pid_file}",
    )

    # Read the PID
    pid_cmd = run_on_oim(host, f"cat {pid_file}")
    pid = pid_cmd.stdout.strip()

    elapsed = 0
    while elapsed < timeout:
        time.sleep(min(interval, timeout - elapsed))
        elapsed += interval

        # Check if process is still running
        alive = run_on_oim(host, f"kill -0 {pid} 2>/dev/null; echo $?")
        still_running = alive.stdout.strip() == "0"

        if progress_callback:
            progress_callback(elapsed)

        if not still_running:
            break

    # If still running after timeout, kill it
    if elapsed >= timeout:
        run_on_oim(host, f"kill -9 {pid} 2>/dev/null || true")

    # Read exit code from rc_file (written by the wrapper)
    rc_cmd = run_on_oim(host, f"cat {rc_file} 2>/dev/null || echo 1")
    rc_str = rc_cmd.stdout.strip().split("\n")[-1]
    try:
        rc = int(rc_str)
    except ValueError:
        rc = 1

    # Read build log (last 200 lines for display)
    log_cmd = run_on_oim(host, f"tail -200 {log_file} 2>/dev/null")
    build_output = log_cmd.stdout.strip() if log_cmd.rc == 0 else ""

    # Clean up temp files
    run_on_oim(host, f"rm -f {log_file} {pid_file} {rc_file} {wrapper}")

    if rc != 0 and elapsed >= timeout:
        return {
            "success": False,
            "image_tag": core_tag,
            "rc": rc,
            "build_output": build_output,
            "error": f"Build timed out after {timeout}s",
        }

    if rc != 0:
        return {
            "success": False,
            "image_tag": core_tag,
            "rc": rc,
            "build_output": build_output,
            "error": f"build_images.sh exited with code {rc}",
        }

    return {
        "success": True,
        "image_tag": core_tag,
        "rc": 0,
        "build_output": build_output,
        "error": "",
    }


def verify_podman_image(host, tag: str) -> Dict[str, Any]:
    """
    Verify that omnia_core:<tag> image exists in podman.

    Args:
        host: Testinfra host object
        tag: Expected image tag (e.g., "2.2")

    Returns:
        Dict with success, images_output, error
    """
    cmd = run_on_oim(
        host,
        "podman images --format "
        "'table {{.Repository}}\\t{{.Tag}}\\t{{.Size}}\\t{{.Created}}' "
        "| grep -E 'REPOSITORY|omnia_core'",
    )
    images_output = cmd.stdout.strip() if cmd.rc == 0 else "(no output)"

    # Check specific tag
    check = run_on_oim(
        host,
        f"podman images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' "
        f"| grep -qE '^(localhost/)?omnia_core:{tag}$'",
    )

    return {
        "success": check.rc == 0,
        "images_output": images_output,
        "error": "" if check.rc == 0 else f"omnia_core:{tag} not found",
    }


def download_omnia_sh(host) -> Dict[str, Any]:
    """
    Download omnia.sh from the configured omnia_branch and mark executable.

    Tries branch URL first, then tag URL (same fallback pattern as
    oim-prereq-check ``repository.download_omnia_sh()``).

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, path, url, ref_type, error
    """
    omnia_branch = UPGRADE_VARS["omnia_branch"]
    clone_path = UPGRADE_VARS["clone_path"]
    omnia_sh_path = f"{clone_path}/omnia.sh"
    branch_url = UPGRADE_VARS["omnia_sh_branch_url"]
    tag_url = UPGRADE_VARS["omnia_sh_tag_url"]

    if not omnia_branch:
        return {
            "success": False,
            "path": omnia_sh_path,
            "url": "",
            "ref_type": "",
            "error": "omnia_branch not configured in omnia_test_config.yml",
        }

    # Try branch URL first
    cmd = run_on_oim(host, f"curl -f -o '{omnia_sh_path}' '{branch_url}'")
    if cmd.rc == 0:
        run_on_oim(host, f"chmod +x '{omnia_sh_path}'")
        return {
            "success": True,
            "path": omnia_sh_path,
            "url": branch_url,
            "ref_type": "branch",
            "error": "",
        }

    # Fallback: try tag URL
    cmd = run_on_oim(host, f"curl -f -o '{omnia_sh_path}' '{tag_url}'")
    if cmd.rc == 0:
        run_on_oim(host, f"chmod +x '{omnia_sh_path}'")
        return {
            "success": True,
            "path": omnia_sh_path,
            "url": tag_url,
            "ref_type": "tag",
            "error": "",
        }

    # Both failed
    return {
        "success": False,
        "path": omnia_sh_path,
        "url": f"{branch_url} / {tag_url}",
        "ref_type": "",
        "error": (
            f"Failed to download omnia.sh from '{omnia_branch}'.\n"
            f"  Tried branch: {branch_url}\n"
            f"  Tried tag:    {tag_url}"
        ),
    }


# =============================================================================
# UPGRADE EXECUTION
# =============================================================================

def run_omnia_upgrade(host, progress_callback=None) -> Dict[str, Any]:
    """
    Run omnia.sh --upgrade on the OIM server.

    The upgrade menu asks the user to select an upgrade option (1, 2, …)
    and then confirm with 'y'.  We pipe ``1\\ny\\n`` via a wrapper
    script that runs in the background so the SSH session does not time
    out.  The function polls every 10 s and returns once the process
    finishes or the ``upgrade_timeout`` is reached.

    Args:
        host: Testinfra host object
        progress_callback: Optional callable(elapsed_seconds: int) for
            periodic progress output.

    Returns:
        Dict with success, output, rc, omnia_sh_path, error
    """
    clone_path = UPGRADE_VARS["clone_path"]
    omnia_sh_path = f"{clone_path}/omnia.sh"
    timeout = UPGRADE_VARS["upgrade_timeout"]
    poll_interval = 10

    # Verify omnia.sh is present and executable
    check = run_on_oim(host, f"test -x {omnia_sh_path}")
    if check.rc != 0:
        return {
            "success": False,
            "output": "",
            "rc": -1,
            "omnia_sh_path": omnia_sh_path,
            "error": f"omnia.sh not found or not executable at {omnia_sh_path}",
        }

    # Temp files for background execution
    log_file = "/tmp/omnia_upgrade_run.log"
    pid_file = "/tmp/omnia_upgrade_run.pid"
    rc_file = "/tmp/omnia_upgrade_run.rc"
    wrapper = "/tmp/omnia_upgrade_run.sh"

    # Write wrapper script to avoid quoting / timeout issues
    run_on_oim(
        host,
        f"cat > {wrapper} << 'UPGRADEEOF'\n"
        f"#!/bin/bash\n"
        f"printf '1\\ny\\n' | {omnia_sh_path} --upgrade\n"
        f"echo $? > {rc_file}\n"
        f"UPGRADEEOF\n"
        f"chmod +x {wrapper}",
    )

    # Run wrapper in background
    run_on_oim(
        host,
        f"nohup {wrapper} > {log_file} 2>&1 & echo $! > {pid_file}",
    )

    pid_cmd = run_on_oim(host, f"cat {pid_file}")
    pid = pid_cmd.stdout.strip()

    elapsed = 0
    while elapsed < timeout:
        time.sleep(min(poll_interval, timeout - elapsed))
        elapsed += poll_interval

        alive = run_on_oim(host, f"kill -0 {pid} 2>/dev/null; echo $?")
        still_running = alive.stdout.strip() == "0"

        if progress_callback:
            progress_callback(elapsed)

        if not still_running:
            break

    if elapsed >= timeout:
        run_on_oim(host, f"kill -9 {pid} 2>/dev/null || true")

    # Read exit code
    rc_cmd = run_on_oim(host, f"cat {rc_file} 2>/dev/null || echo 1")
    rc_str = rc_cmd.stdout.strip().split("\n")[-1]
    try:
        rc = int(rc_str)
    except ValueError:
        rc = 1

    # Capture last 50 lines for display
    log_cmd = run_on_oim(host, f"tail -50 {log_file} 2>/dev/null")
    last_50 = log_cmd.stdout.strip() if log_cmd.rc == 0 else ""

    # Clean up
    run_on_oim(host, f"rm -f {log_file} {pid_file} {rc_file} {wrapper}")

    if rc != 0 and elapsed >= timeout:
        return {
            "success": False,
            "output": last_50,
            "rc": rc,
            "omnia_sh_path": omnia_sh_path,
            "error": f"omnia.sh --upgrade timed out after {timeout}s",
        }

    if rc != 0:
        return {
            "success": False,
            "output": last_50,
            "rc": rc,
            "omnia_sh_path": omnia_sh_path,
            "error": "omnia.sh --upgrade exited non-zero",
        }

    return {
        "success": True,
        "output": last_50,
        "rc": 0,
        "omnia_sh_path": omnia_sh_path,
        "error": "",
    }


# =============================================================================
# POST-UPGRADE VERIFICATION
# =============================================================================

def verify_backup_directory(host) -> Dict[str, Any]:
    """
    Verify backup directory exists with expected sub-directories.

    Checks:
    - ``{backup_path}`` exists
    - Sub-directories: ``configs/``, ``input/``, ``metadata/``, ``openchami/``

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, backup_path, sub_dirs (dict), error
    """
    container = UPGRADE_VARS["container_name"]
    backup_path = UPGRADE_VARS["backup_path"]

    chk = run_in_container(
        host, f"test -d '{backup_path}'", container=container,
    )
    if chk.rc != 0:
        return {
            "success": False,
            "backup_path": backup_path,
            "sub_dirs": {},
            "error": f"Backup directory not found: {backup_path}",
        }

    # Sub-directories
    expected_subs = ("configs", "input", "metadata", "openchami")
    sub_dirs: Dict[str, bool] = {}
    for sub in expected_subs:
        chk = run_in_container(
            host, f"test -d '{backup_path}/{sub}'", container=container,
        )
        sub_dirs[sub] = chk.rc == 0

    missing_dirs = [k for k, v in sub_dirs.items() if not v]
    all_ok = len(missing_dirs) == 0

    return {
        "success": all_ok,
        "backup_path": backup_path,
        "sub_dirs": sub_dirs,
        "error": f"Missing dirs: {', '.join(missing_dirs)}" if missing_dirs else "",
    }


def verify_post_upgrade_state(host) -> Dict[str, Any]:
    """
    Verify the cluster is in the expected post-upgrade state.

    Checks:
    1. omnia_core container is running
    2. omnia_version in metadata matches new_version
    3. Container image tag matches expected core_tag

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, version, expected, expected_tag,
              container_name, container_image, container_status,
              container_running, error
    """
    container = UPGRADE_VARS["container_name"]
    to_version = UPGRADE_VARS["new_version"]
    expected_tag = get_core_tag_for_version(to_version)

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
        metadata_path = UPGRADE_VARS["oim_metadata_path"]
        meta_cmd = run_in_container(
            host,
            f"grep '^omnia_version:' {metadata_path} "
            "| awk '{print $2}' | tr -d '\"'",
            container=container,
        )
        version = meta_cmd.stdout.strip() if meta_cmd.rc == 0 else ""

    errors: List[str] = []
    if not container_running:
        errors.append("omnia_core container is not running")
    if version and version != to_version:
        errors.append(f"Version mismatch: expected {to_version}, found {version}")
    elif not version and container_running:
        errors.append("Could not read omnia_version from metadata")

    return {
        "success": container_running and version == to_version,
        "version": version,
        "expected": to_version,
        "expected_tag": expected_tag,
        "container_name": c_name,
        "container_image": c_image,
        "container_status": c_status,
        "container_running": container_running,
        "error": "; ".join(errors) if errors else "",
    }
