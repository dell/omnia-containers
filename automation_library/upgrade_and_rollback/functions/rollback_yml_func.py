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
Rollback Module - rollback.yml Execution Functions.

Functions for running and verifying the per-component ``rollback.yml``
playbook inside the omnia_core container.

Rollback order (reverse of upgrade):
  slurm -> k8s -> build_stream -> oim

Key behaviours:
- Always passes ``-e skip_approval=true`` to bypass operator prompt.
- Runs the playbook in the background; polls for completion.
- Returns structured results with output, rc, and error messages.
- Reads ``rollback_manifest.yml`` to verify per-component status.
- Checks for upgrade lock before starting rollback.
"""

import time
from typing import Dict, Any, List, Optional, Callable

from ...core import (
    run_in_container,
    load_container_file,
    is_software_enabled,
)
from ..vars.rollback_yml_vars import ROLLBACK_YML_VARS


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _get_log_output(
    host, container: str, log_file: str, tail_lines: int,
) -> str:
    """Read last N lines (or all) from a log file."""
    if tail_lines == 0:
        cmd = run_in_container(
            host,
            f"cat {log_file} 2>/dev/null",
            container=container,
        )
    else:
        cmd = run_in_container(
            host,
            f"tail -{tail_lines} {log_file} 2>/dev/null",
            container=container,
        )
    return cmd.stdout.strip() if cmd.rc == 0 else ""


def _check_playbook_running(host, container: str) -> Dict[str, Any]:
    """Check if rollback.yml is already running."""
    check_cmd = run_in_container(
        host,
        r"ps aux | grep -E 'ansible-playbook.*rollback\.yml'"
        r" | grep -v grep || echo 'NO_PROCESS'",
        container=container,
    )

    if check_cmd.rc != 0:
        return {
            "running": False,
            "process_info": "",
            "error": (
                "Failed to check processes: "
                f"{check_cmd.stderr.strip()}"
            ),
        }

    output = check_cmd.stdout.strip()
    if output == "NO_PROCESS" or not output:
        return {
            "running": False,
            "process_info": "",
            "error": "",
        }

    return {
        "running": True,
        "process_info": output,
        "error": "",
    }


def _read_manifest_component_status(
    host, manifest_path: str,
) -> Dict[str, str]:
    """
    Read component_status from rollback_manifest.yml.

    Uses core module ``load_container_file`` for YAML loading.

    Returns:
        Dict mapping component name to status string.
        Empty dict on error.
    """
    manifest = load_container_file(host, manifest_path)
    if not manifest:
        return {}
    component_status = manifest.get("component_status", {})
    return {
        str(k): str(v) for k, v in component_status.items()
    }


# =============================================================================
# LOCK CHECK
# =============================================================================

def check_upgrade_lock(host) -> Dict[str, Any]:
    """
    Check if an upgrade is currently in progress.

    Returns:
        Dict with lock_exists (bool), lock_path, error
    """
    container = ROLLBACK_YML_VARS["container_name"]
    lock_path = ROLLBACK_YML_VARS["upgrade_lock_path"]

    cmd = run_in_container(
        host,
        f"test -f {lock_path} "
        f"&& echo LOCKED || echo UNLOCKED",
        container=container,
    )

    locked = cmd.stdout.strip() == "LOCKED"
    return {
        "lock_exists": locked,
        "lock_path": lock_path,
        "error": "",
    }


# =============================================================================
# MANIFEST VERIFICATION
# =============================================================================

def verify_rollback_manifest(host) -> Dict[str, Any]:
    """
    Verify rollback_manifest.yml exists and is readable.

    Uses core module ``load_container_file`` for YAML loading.

    Returns:
        Dict with success, manifest_path, exists,
        rollback_status, component_status (dict), error
    """
    container = ROLLBACK_YML_VARS["container_name"]
    manifest_path = ROLLBACK_YML_VARS["manifest_path"]

    exist_cmd = run_in_container(
        host,
        f"test -f {manifest_path} "
        f"&& echo EXISTS || echo MISSING",
        container=container,
    )
    if exist_cmd.stdout.strip() != "EXISTS":
        return {
            "success": False,
            "manifest_path": manifest_path,
            "exists": False,
            "rollback_status": "",
            "component_status": {},
            "error": (
                "rollback_manifest.yml not found "
                f"at {manifest_path}"
            ),
        }

    manifest = load_container_file(host, manifest_path)
    if not manifest:
        return {
            "success": False,
            "manifest_path": manifest_path,
            "exists": True,
            "rollback_status": "",
            "component_status": {},
            "error": (
                "Failed to parse rollback_manifest.yml "
                f"at {manifest_path}"
            ),
        }

    return {
        "success": True,
        "manifest_path": manifest_path,
        "exists": True,
        "rollback_status": manifest.get(
            "rollback_status", ""
        ),
        "component_status": manifest.get(
            "component_status", {}
        ),
        "error": "",
    }


def verify_rollback_manifest_component_status(
    host, component: str,
) -> Dict[str, Any]:
    """
    Verify a single component's status in rollback_manifest.yml.

    A component is considered successful if its status is
    ``completed`` or ``skipped``.

    Args:
        host: Testinfra host object
        component: Component name (slurm, k8s, build_stream, oim)

    Returns:
        Dict with success, component, status, manifest_path, error
    """
    manifest_path = ROLLBACK_YML_VARS["manifest_path"]

    component_status = _read_manifest_component_status(
        host, manifest_path,
    )
    if not component_status:
        return {
            "success": False,
            "component": component,
            "status": "",
            "manifest_path": manifest_path,
            "error": (
                "Could not read component_status from "
                f"{manifest_path}. Ensure rollback.yml ran "
                "and manifest was written."
            ),
        }

    status = component_status.get(component, "not_found")
    success = status in ("completed", "skipped")

    return {
        "success": success,
        "component": component,
        "status": status,
        "manifest_path": manifest_path,
        "error": (
            ""
            if success
            else (
                f"Component '{component}' status is "
                f"'{status}' "
                "(expected 'completed' or 'skipped')"
            )
        ),
    }


# =============================================================================
# SOFTWARE CONFIG CHECK
# =============================================================================

def check_rollback_software_component_enabled(
    host, software_name: str,
) -> Dict[str, Any]:
    """
    Check if a software component is enabled in software_config.json.

    Uses core module ``is_software_enabled`` for JSON loading.

    Args:
        host: Testinfra host object
        software_name: Name to look for in softwares[] list

    Returns:
        Dict with success, enabled (bool), software_name, error
    """
    enabled = is_software_enabled(host, software_name)
    return {
        "success": True,
        "enabled": enabled,
        "software_name": software_name,
        "error": "",
    }


# =============================================================================
# PREREQUISITE CHECK
# =============================================================================

def verify_rollback_component_prerequisites(
    host, component: str,
) -> Dict[str, Any]:
    """
    Verify that prerequisite components are completed/skipped
    before rolling back this component.

    Args:
        host: Testinfra host object
        component: Component to check prerequisites for

    Returns:
        Dict with success, component, prerequisites,
        unmet (list), error
    """
    cfg = ROLLBACK_YML_VARS
    manifest_path = cfg["manifest_path"]
    prereqs = cfg["component_prerequisites"].get(
        component, [],
    )

    if not prereqs:
        return {
            "success": True,
            "component": component,
            "prerequisites": prereqs,
            "unmet": [],
            "error": "",
        }

    component_status = _read_manifest_component_status(
        host, manifest_path,
    )

    unmet = []
    for prereq in prereqs:
        status = component_status.get(prereq, "not_found")
        if status not in ("completed", "skipped"):
            unmet.append(f"{prereq}={status}")

    return {
        "success": len(unmet) == 0,
        "component": component,
        "prerequisites": prereqs,
        "unmet": unmet,
        "error": (
            ""
            if not unmet
            else (
                f"Unmet prerequisites for '{component}': "
                f"{', '.join(unmet)}"
            )
        ),
    }


# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

def check_rollback_yml_exists(host) -> Dict[str, Any]:
    """
    Check that omnia_core container is running and rollback.yml
    is present. Also checks if rollback.yml is already running.

    Returns:
        Dict with success, container_running, playbook_exists,
        playbook_running, process_info, error
    """
    container = ROLLBACK_YML_VARS["container_name"]
    playbook_path = ROLLBACK_YML_VARS["playbook_path"]

    # Check container running
    ps_cmd = run_in_container(
        host, "echo CONTAINER_OK", container=container,
    )
    container_running = (
        ps_cmd.rc == 0 and "CONTAINER_OK" in ps_cmd.stdout
    )

    if not container_running:
        return {
            "success": False,
            "container_running": False,
            "playbook_exists": False,
            "playbook_running": False,
            "process_info": "",
            "error": (
                "omnia_core container is not running "
                "or not reachable.\n\n"
                "HOW TO FIX:\n"
                "  1. Check container: "
                f"podman ps | grep {container}\n"
                "  2. Start if stopped: "
                f"systemctl start {container}.service"
            ),
        }

    # Check rollback.yml exists inside container
    exist_cmd = run_in_container(
        host,
        f"test -f {playbook_path} "
        f"&& echo EXISTS || echo MISSING",
        container=container,
    )
    playbook_exists = exist_cmd.stdout.strip() == "EXISTS"

    if not playbook_exists:
        return {
            "success": False,
            "container_running": True,
            "playbook_exists": False,
            "playbook_running": False,
            "process_info": "",
            "error": (
                "rollback.yml not found at "
                f"{playbook_path} inside {container}.\n\n"
                "HOW TO FIX:\n"
                "  1. Verify the Omnia upgrade repo "
                "was cloned into the container\n"
                "  2. Check: podman exec "
                f"{container} ls -la /omnia/upgrade/"
            ),
        }

    # Check if playbook is currently running
    running_check = _check_playbook_running(host, container)

    if running_check["running"]:
        log_file = ROLLBACK_YML_VARS["log_file"]
        process_info = running_check["process_info"]
        return {
            "success": False,
            "container_running": True,
            "playbook_exists": True,
            "playbook_running": True,
            "process_info": process_info,
            "error": (
                "rollback.yml playbook is currently "
                f"running inside {container}.\n\n"
                f"Running process:\n{process_info}\n\n"
                "HOW TO FIX:\n"
                "  1. Wait for current playbook "
                "to complete\n"
                "  2. Check logs: podman exec "
                f"{container} cat {log_file}\n"
                "  3. Or kill process if needed: "
                f"podman exec {container} "
                "pkill -f "
                "'ansible-playbook.*rollback.yml'"
            ),
        }

    return {
        "success": True,
        "container_running": True,
        "playbook_exists": True,
        "playbook_running": False,
        "process_info": "",
        "error": "",
    }


# =============================================================================
# ROLLBACK.YML EXECUTION HELPERS
# =============================================================================

def _build_playbook_cmd(
    playbook_path: str,
    tags: Optional[List[str]] = None,
    extra_vars: Optional[Dict[str, str]] = None,
) -> str:
    """Build the ansible-playbook command string."""
    cmd_parts = [
        f"ansible-playbook {playbook_path}",
        "-e skip_approval=true",
    ]
    if tags:
        cmd_parts.append(f"--tags {','.join(tags)}")
    if extra_vars:
        for key, val in extra_vars.items():
            cmd_parts.append(f"-e {key}={val}")
    return " ".join(cmd_parts)


def _poll_playbook_completion(
    host, container: str, rc_file: str,
    timeout: int,
    progress_callback: Optional[Callable[[int], None]],
) -> int:
    """Poll until rc_file appears or timeout."""
    interval = ROLLBACK_YML_VARS["poll_interval"]
    elapsed = 0
    while elapsed < timeout:
        time.sleep(interval)
        elapsed += interval
        if progress_callback:
            progress_callback(elapsed)
        check = run_in_container(
            host,
            f"test -f {rc_file} && echo DONE || echo RUNNING",
            container=container,
        )
        if check.stdout.strip() == "DONE":
            break
    return elapsed


# =============================================================================
# ROLLBACK.YML EXECUTION
# =============================================================================

def run_rollback_yml(
    host,
    tags: Optional[List[str]] = None,
    extra_vars: Optional[Dict[str, str]] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> Dict[str, Any]:
    """
    Run ``rollback.yml`` inside the omnia_core container.

    Always passes ``-e skip_approval=true`` for non-interactive
    execution.

    The playbook is started in the background and polled every
    ``poll_interval`` seconds until completion or timeout.

    Args:
        host: Testinfra host object
        tags: Optional list of component tags to pass via --tags
        extra_vars: Optional dict of extra -e key=value vars
        progress_callback: Optional callable(elapsed_seconds)

    Returns:
        Dict with success, rc, output (last N lines), tags, error
    """
    cfg = ROLLBACK_YML_VARS
    container = cfg["container_name"]
    tags_label = ",".join(tags) if tags else "all"

    # Check if playbook is currently running
    running_check = _check_playbook_running(host, container)
    if running_check["running"]:
        process_info = running_check["process_info"]
        return {
            "success": False,
            "rc": -2,
            "output": "",
            "tags": tags_label,
            "error": (
                "rollback.yml playbook is currently running "
                f"inside {container}.\n\n"
                f"Running process:\n{process_info}\n\n"
                "Wait for current playbook to complete or "
                "kill the process:\n"
                f"  podman exec {container} pkill -f "
                "'ansible-playbook.*rollback.yml'"
            ),
        }

    # Use single timeout — playbooks manage their own
    timeout = cfg["timeout"]

    rc_file = f"{cfg['log_file']}.rc"
    playbook_cmd = _build_playbook_cmd(
        cfg["playbook_path"], tags, extra_vars,
    )

    # Start playbook in background; write rc to rc_file on exit
    start_cmd = run_in_container(
        host,
        (
            f"bash -c 'rm -f {rc_file}; "
            f"({playbook_cmd} > {cfg['log_file']} 2>&1; "
            f"echo $? > {rc_file}) & echo $!'"
        ),
        container=container,
    )

    if start_cmd.rc != 0 or not start_cmd.stdout.strip():
        return {
            "success": False,
            "rc": start_cmd.rc,
            "output": "",
            "tags": tags_label,
            "error": (
                f"Failed to start rollback.yml [{tags_label}]"
                f": {start_cmd.stderr.strip() or 'unknown'}"
            ),
        }

    elapsed = _poll_playbook_completion(
        host, container, rc_file, timeout, progress_callback,
    )

    # Timeout branch
    if elapsed >= timeout:
        return {
            "success": False,
            "rc": -1,
            "output": _get_log_output(
                host, container,
                cfg["log_file"], cfg["tail_lines"],
            ),
            "tags": tags_label,
            "error": (
                f"rollback.yml [{tags_label}] "
                f"timed out after {timeout}s"
            ),
        }

    # Read exit code from rc_file
    rc_cmd = run_in_container(
        host,
        f"cat {rc_file} 2>/dev/null",
        container=container,
    )
    rc_str = rc_cmd.stdout.strip()
    rc = int(rc_str) if rc_str.isdigit() else 1

    return {
        "success": rc == 0,
        "rc": rc,
        "output": _get_log_output(
            host, container,
            cfg["log_file"], cfg["tail_lines"],
        ),
        "tags": tags_label,
        "error": (
            ""
            if rc == 0
            else (
                f"rollback.yml [{tags_label}] "
                f"exited with rc={rc}"
            )
        ),
    }
