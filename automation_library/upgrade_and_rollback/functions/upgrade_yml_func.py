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
Upgrade Module - upgrade.yml Execution Functions.

Functions for running and verifying the per-component ``upgrade.yml``
playbook inside the omnia_core container.

Supported components (in upgrade order):
  oim → k8s → slurm → openchami

Key behaviours:
- Always passes ``-e skip_approval=true`` to bypass operator prompt in automation.
- Runs the playbook in the background inside the container; polls for completion.
- Returns structured results with output, rc, and human-readable error messages.
- Reads ``upgrade_manifest.yml`` to verify per-component completion status.
"""

import time
from typing import Dict, Any, List, Optional, Callable

from ...core import run_in_container, load_container_file, is_software_enabled
from ..vars.upgrade_yml_vars import UPGRADE_YML_VARS


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _get_log_output(host, container: str, log_file: str, tail_lines: int) -> str:
    """Read last N lines (or all) from a log file inside the container."""
    if tail_lines == 0:
        cmd = run_in_container(host, f"cat {log_file} 2>/dev/null", container=container)
    else:
        cmd = run_in_container(
            host, f"tail -{tail_lines} {log_file} 2>/dev/null", container=container,
        )
    return cmd.stdout.strip() if cmd.rc == 0 else ""


def _check_playbook_running(host, container: str) -> Dict[str, Any]:
    """Check if upgrade.yml playbook is already running inside the container."""
    check_cmd = run_in_container(
        host,
        r"ps aux | grep -E 'ansible-playbook.*upgrade\.yml' | grep -v grep || echo 'NO_PROCESS'",
        container=container,
    )

    if check_cmd.rc != 0:
        return {
            "running": False,
            "process_info": "",
            "error": f"Failed to check processes: {check_cmd.stderr.strip()}"
        }

    output = check_cmd.stdout.strip()
    if output == "NO_PROCESS" or not output:
        return {
            "running": False,
            "process_info": "",
            "error": ""
        }

    return {
        "running": True,
        "process_info": output,
        "error": ""
    }


def _check_upgrade_status(host, container: str, manifest_path: str) -> Dict[str, Any]:
    """Check upgrade status from upgrade_manifest.yml."""
    manifest = load_container_file(host, manifest_path)

    if not manifest:
        return {
            "manifest_exists": False,
            "upgrade_status": "",
            "already_completed": False,
            "error": ""
        }

    upgrade_status = manifest.get("upgrade_status", "unknown")
    already_completed = upgrade_status == "completed"

    return {
        "manifest_exists": True,
        "upgrade_status": upgrade_status,
        "already_completed": already_completed,
        "error": ""
    }


def _read_manifest_component_status(host, container: str, manifest_path: str) -> Dict[str, str]:
    """
    Read component_status dict from upgrade_manifest.yml inside the container.

    Returns:
        Dict mapping component name → status string.
        Empty dict on error.
    """
    manifest = load_container_file(host, manifest_path)
    if not manifest:
        return {}

    component_status = manifest.get("component_status", {})
    return {str(k): str(v) for k, v in component_status.items()}


# =============================================================================
# MANIFEST VERIFICATION
# =============================================================================

def verify_upgrade_manifest(host) -> Dict[str, Any]:
    """
    Verify upgrade_manifest.yml exists and is readable inside the container.

    Returns:
        Dict with success, manifest_path, exists, upgrade_status,
              component_status (dict), error
    """
    container = UPGRADE_YML_VARS["container_name"]
    manifest_path = UPGRADE_YML_VARS["manifest_path"]

    exist_cmd = run_in_container(
        host, f"test -f {manifest_path} && echo EXISTS || echo MISSING",
        container=container,
    )
    if exist_cmd.stdout.strip() != "EXISTS":
        return {
            "success": False,
            "manifest_path": manifest_path,
            "exists": False,
            "upgrade_status": "",
            "component_status": {},
            "error": f"upgrade_manifest.yml not found at {manifest_path}",
        }

    manifest = load_container_file(host, manifest_path)
    if not manifest:
        return {
            "success": False,
            "manifest_path": manifest_path,
            "exists": True,
            "upgrade_status": "",
            "component_status": {},
            "error": f"Failed to parse upgrade_manifest.yml at {manifest_path}",
        }

    return {
        "success": True,
        "manifest_path": manifest_path,
        "exists": True,
        "upgrade_status": manifest.get("upgrade_status", ""),
        "component_status": manifest.get("component_status", {}),
        "error": "",
    }


def verify_manifest_component_status(host, component: str) -> Dict[str, Any]:
    """
    Verify a single component's status in upgrade_manifest.yml.

    A component is considered successful if its status is ``completed``
    or ``skipped``.

    Args:
        host: Testinfra host object
        component: Component name (oim, k8s, slurm, openchami)

    Returns:
        Dict with success, component, status, manifest_path, error
    """
    container = UPGRADE_YML_VARS["container_name"]
    manifest_path = UPGRADE_YML_VARS["manifest_path"]

    component_status = _read_manifest_component_status(host, container, manifest_path)
    if not component_status:
        return {
            "success": False,
            "component": component,
            "status": "",
            "manifest_path": manifest_path,
            "error": (
                f"Could not read component_status from {manifest_path}. "
                f"Ensure upgrade.yml ran and manifest was written."
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
                f"Component '{component}' status is '{status}' "
                f"(expected 'completed' or 'skipped')"
            )
        ),
    }


# =============================================================================
# SOFTWARE CONFIG CHECK
# =============================================================================

def check_software_component_enabled(host, software_name: str) -> Dict[str, Any]:
    """
    Check if a software component is enabled in software_config.json.

    Args:
        host: Testinfra host object
        software_name: Name to look for in softwares[] list
                       (e.g. "service_k8s", "slurm_custom", "openchami")

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
# PRE-FLIGHT CHECKS
# =============================================================================

def check_upgrade_yml_exists(host) -> Dict[str, Any]:
    """
    Check that the omnia_core container is running and upgrade.yml is present.
    Also checks if upgrade.yml playbook is already running.

    Returns:
        Dict with success, container_running, playbook_exists, playbook_running,
        process_info, error
    """
    container = UPGRADE_YML_VARS["container_name"]
    playbook_path = UPGRADE_YML_VARS["playbook_path"]

    # Check container running
    ps_cmd = run_in_container(
        host, "echo CONTAINER_OK", container=container,
    )
    container_running = ps_cmd.rc == 0 and "CONTAINER_OK" in ps_cmd.stdout

    if not container_running:
        return {
            "success": False,
            "container_running": False,
            "playbook_exists": False,
            "playbook_running": False,
            "process_info": "",
            "error": (
                f"omnia_core container is not running or not reachable.\n\n"
                f"HOW TO FIX:\n"
                f"  1. Check container: podman ps | grep {container}\n"
                f"  2. Start if stopped: systemctl start {container}.service"
            ),
        }

    # Check upgrade.yml exists inside container
    exist_cmd = run_in_container(
        host,
        f"test -f {playbook_path} && echo EXISTS || echo MISSING",
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
                f"upgrade.yml not found at {playbook_path} inside {container}.\n\n"
                f"HOW TO FIX:\n"
                f"  1. Verify the Omnia upgrade repo was cloned into the container\n"
                f"  2. Check: podman exec {container} ls -la /omnia/upgrade/"
            ),
        }

    # Check if playbook is currently running
    running_check = _check_playbook_running(host, container)

    if running_check["running"]:
        return {
            "success": False,
            "container_running": True,
            "playbook_exists": True,
            "playbook_running": True,
            "process_info": running_check["process_info"],
            "error": (
                f"upgrade.yml playbook is currently running inside {container}.\n\n"
                f"Running process:\n{running_check['process_info']}\n\n"
                f"HOW TO FIX:\n"
                f"  1. Wait for current playbook to complete\n"
                f"  2. Check logs: podman exec {container} cat {UPGRADE_YML_VARS['log_file']}\n"
                f"  3. Or kill process if needed: podman exec {container} "
                f"pkill -f 'ansible-playbook.*upgrade.yml'"
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
# UPGRADE.YML EXECUTION HELPERS
# =============================================================================

def _build_playbook_cmd(
    playbook_path: str,
    tags: Optional[List[str]] = None,
    extra_vars: Optional[Dict[str, str]] = None,
) -> str:
    """Build the ansible-playbook command string."""
    cmd_parts = [f"ansible-playbook {playbook_path}", "-e skip_approval=true"]
    if tags:
        cmd_parts.append(f"--tags {','.join(tags)}")
    if extra_vars:
        for key, val in extra_vars.items():
            cmd_parts.append(f"-e {key}={val}")
    return " ".join(cmd_parts)


def _poll_playbook_completion(
    host, container: str, rc_file: str,
    timeout: int, progress_callback: Optional[Callable[[int], None]],
) -> int:
    """Poll until rc_file appears or timeout. Returns elapsed seconds."""
    interval = UPGRADE_YML_VARS["poll_interval"]
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
# UPGRADE.YML EXECUTION
# =============================================================================

def run_upgrade_yml(
    host,
    tags: Optional[List[str]] = None,
    extra_vars: Optional[Dict[str, str]] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> Dict[str, Any]:
    """
    Run ``upgrade.yml`` inside the omnia_core container.

    Always passes ``-e skip_approval=true`` for non-interactive / automation
    execution.

    The playbook is started in the background and polled every
    ``poll_interval`` seconds until completion or timeout.

    Args:
        host: Testinfra host object
        tags: Optional list of component tags to pass via ``--tags``
              (e.g. ["oim"], ["k8s"], ["slurm"]).  None = run all tags.
        extra_vars: Optional dict of extra ``-e key=value`` vars to append.
        progress_callback: Optional callable(elapsed_seconds) invoked each poll.

    Returns:
        Dict with success, rc, output (last N lines), tags, error
    """
    cfg = UPGRADE_YML_VARS
    container = cfg["container_name"]
    tags_label = ",".join(tags) if tags else "all"

    # Check if playbook is currently running
    running_check = _check_playbook_running(host, container)
    if running_check["running"]:
        return {
            "success": False,
            "rc": -2,
            "output": "",
            "tags": tags_label,
            "error": (
                f"upgrade.yml playbook is currently running inside {container}.\n\n"
                f"Running process:\n{running_check['process_info']}\n\n"
                f"Wait for current playbook to complete or kill the process:\n"
                f"  podman exec {container} pkill -f 'ansible-playbook.*upgrade.yml'"
            ),
        }

    # Resolve timeout
    if tags and len(tags) == 1 and tags[0] in cfg["component_timeouts"]:
        timeout = cfg["component_timeouts"][tags[0]]
    else:
        timeout = cfg["default_timeout"]

    rc_file = f"{cfg['log_file']}.rc"
    playbook_cmd = _build_playbook_cmd(cfg["playbook_path"], tags, extra_vars)

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
                f"Failed to start upgrade.yml [{tags_label}]: "
                f"{start_cmd.stderr.strip() or 'unknown error'}"
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
            "output": _get_log_output(host, container, cfg["log_file"], cfg["tail_lines"]),
            "tags": tags_label,
            "error": f"upgrade.yml [{tags_label}] timed out after {timeout}s",
        }

    # Read exit code from rc_file
    rc_cmd = run_in_container(
        host, f"cat {rc_file} 2>/dev/null", container=container,
    )
    rc = int(rc_cmd.stdout.strip()) if rc_cmd.stdout.strip().isdigit() else 1

    return {
        "success": rc == 0,
        "rc": rc,
        "output": _get_log_output(host, container, cfg["log_file"], cfg["tail_lines"]),
        "tags": tags_label,
        "error": (
            ""
            if rc == 0
            else f"upgrade.yml [{tags_label}] exited with rc={rc}"
        ),
    }
