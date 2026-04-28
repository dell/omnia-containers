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
GitLab Verification Functions.

This module provides verification functions for GitLab deployment.

For shared functions, see:
- shared_func.py - Config loading, caching, skip helpers
"""

import json
from typing import Any, Dict

from automation_library.core import (
    get_input_value,
    view_credentials_file,
    BUILD_STREAM_CONFIG_FILE,
    BUILD_STREAM_OAUTH_CREDENTIALS_PATH,
    BUILD_STREAM_OAUTH_CREDENTIALS_KEY_PATH,
)
from ...core import run_on_oim, run_in_container

from .shared_func import (
    get_gitlab_host,
    get_gitlab_https_port,
    get_gitlab_min_resources,
    get_gitlab_puma_workers,
    get_gitlab_sidekiq_concurrency,
    get_gitlab_project_name,
    get_gitlab_project_visibility,
    get_gitlab_default_branch,
    get_gitlab_root_password,
    ssh_to_gitlab,
)
from ..vars import (
    GITLAB_SERVICES,
    GITLAB_RUNNER_CONTAINER,
    GITLAB_RB_PATH,
    GITLAB_GIT_DATA_PATH,
    GITLAB_SUCCESS_HTTP_CODES,
    GITLAB_API_VERSION,
    GITLAB_VISIBILITY_LEVELS,
    GITLAB_RUNNER_QUADLET_DIR,
    GITLAB_RUNNER_QUADLET_FILE,
    GITLAB_RUNNER_SERVICES,
    GITLAB_CLEANUP_DIRECTORIES,
    GITLAB_INSTALLED_PACKAGES,
    GITLAB_CI_PIPELINE_FILE,
    GITLAB_PIPELINE_VARIABLES,
    GITLAB_ROOT_TOKEN_FILE,
    GITLAB_CI_PIPELINE_SOURCE_FILE,
    GITLAB_RAILS_CMD_PROJECT_ID,
    GITLAB_RAILS_CMD_PROJECT_VISIBILITY,
    GITLAB_RAILS_CMD_PROJECT_DEFAULT_BRANCH,
    GITLAB_RAILS_CMD_ROOT_TOKEN,
)


# =============================================================================
# GITLAB SERVER VERIFICATION FUNCTIONS
# =============================================================================

def verify_gitlab_url_accessible(host) -> Dict[str, Any]:
    """
    Verify GitLab URL is accessible from OIM server.

    Uses curl on OIM (not container) to check HTTP response.
    """
    result = {
        "success": False,
        "url": "",
        "http_code": 0,
        "error": "",
    }

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)

    if not gitlab_host:
        result["error"] = "gitlab_host not configured in gitlab_config.yml"
        return result

    url = f"https://{gitlab_host}:{gitlab_port}/"
    result["url"] = url

    # Run curl on OIM server (not in container)
    cmd = run_on_oim(
        host,
        f"curl -k -s -o /dev/null -w '%{{http_code}}' '{url}' 2>/dev/null"
    )

    if cmd.rc != 0:
        result["error"] = f"curl failed: {cmd.stderr}"
        return result

    http_code = cmd.stdout.strip() if cmd.stdout else "0"
    try:
        result["http_code"] = int(http_code)
    except ValueError:
        result["http_code"] = 0

    # GitLab returns 302 redirect to sign-in page
    if result["http_code"] in GITLAB_SUCCESS_HTTP_CODES:
        result["success"] = True
    else:
        result["error"] = f"Unexpected HTTP code: {result['http_code']}"

    return result


def verify_gitlab_runner_container(host) -> Dict[str, Any]:
    """
    Verify gitlab-runner container is running on GitLab server.

    Uses podman ps to check specific container status.
    """
    result = {
        "success": False,
        "container": GITLAB_RUNNER_CONTAINER,
        "status": "",
        "error": "",
    }

    # Check if specific container is running
    cmd = 'podman ps --format "{{.Names}} {{.Status}}" 2>/dev/null || true'
    ssh_result = ssh_to_gitlab(host, cmd)

    if GITLAB_RUNNER_CONTAINER in ssh_result["stdout"]:
        # Extract status from output
        for line in ssh_result["stdout"].strip().split("\n"):
            if GITLAB_RUNNER_CONTAINER in line:
                result["status"] = line.strip()
                result["success"] = True
                return result

    # Check if container exists but not running
    cmd = 'podman ps -a --format "{{.Names}} {{.Status}}" 2>/dev/null || true'
    ssh_result = ssh_to_gitlab(host, cmd)

    if GITLAB_RUNNER_CONTAINER in ssh_result["stdout"]:
        for line in ssh_result["stdout"].strip().split("\n"):
            if GITLAB_RUNNER_CONTAINER in line:
                result["status"] = line.strip()
                result["error"] = f"Container {GITLAB_RUNNER_CONTAINER} exists but not running"
                return result

    result["error"] = f"Container {GITLAB_RUNNER_CONTAINER} not found"
    return result


def verify_gitlab_services_running(host) -> Dict[str, Any]:
    """
    Verify that all GitLab services are running on the GitLab server.

    Uses gitlab-ctl status to check service status.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, running_services, not_running, service_status, and error keys
    """
    result = {
        "success": False,
        "running_services": [],
        "not_running": [],
        "service_status": {},
        "error": "",
    }

    ssh_result = ssh_to_gitlab(host, "gitlab-ctl status 2>/dev/null")
    if not ssh_result["success"]:
        result["error"] = ssh_result["error"]
        return result

    output = ssh_result["stdout"]
    lines = output.split('\n') if output else []

    for service in GITLAB_SERVICES:
        found = False
        for line in lines:
            if service in line:
                result["service_status"][service] = line.strip()
                if line.startswith("run:"):
                    result["running_services"].append(service)
                    found = True
                else:
                    result["not_running"].append(service)
                    found = True
                break
        if not found:
            result["not_running"].append(service)
            result["service_status"][service] = "not found"

    if not result["not_running"]:
        result["success"] = True
    else:
        result["error"] = f"Services not running: {', '.join(result['not_running'])}"

    return result


def verify_gitlab_resources(host) -> Dict[str, Any]:
    """
    Verify that GitLab server meets minimum resource requirements.

    Checks CPU cores, memory (GB), and disk space (GB).
    """
    result = {
        "success": False,
        "actual": {"cpu_cores": 0, "memory_gb": 0, "storage_gb": 0},
        "required": {},
        "checks": {"cpu": False, "memory": False, "storage": False},
        "error": "",
    }

    required = get_gitlab_min_resources(host)
    result["required"] = required

    # Get resource information
    result["actual"]["cpu_cores"] = _get_cpu_cores(host)
    result["actual"]["memory_gb"] = _get_memory_gb(host)
    result["actual"]["storage_gb"] = _get_storage_gb(host)

    # Check requirements
    result["checks"]["cpu"] = result["actual"]["cpu_cores"] >= required["min_cpu_cores"]
    result["checks"]["memory"] = result["actual"]["memory_gb"] >= required["min_memory_gb"]
    result["checks"]["storage"] = result["actual"]["storage_gb"] >= required["min_storage_gb"]

    if all(result["checks"].values()):
        result["success"] = True
    else:
        failed = [k for k, v in result["checks"].items() if not v]
        result["error"] = f"Resource requirements not met: {', '.join(failed)}"

    return result


def _get_cpu_cores(host) -> int:
    """Get CPU cores count from GitLab server."""
    ssh_result = ssh_to_gitlab(host, "nproc")
    if ssh_result["success"]:
        try:
            return int(ssh_result["stdout"].strip())
        except ValueError:
            pass
    return 0


def _get_memory_gb(host) -> int:
    """Get memory in GB from GitLab server."""
    ssh_result = ssh_to_gitlab(host, "free -g")
    if ssh_result["success"]:
        try:
            for line in ssh_result["stdout"].split('\n'):
                if 'Mem:' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        return int(parts[1])
        except (ValueError, IndexError):
            pass
    return 0


def _get_storage_gb(host) -> int:
    """Get available storage in GB from GitLab server."""
    ssh_result = ssh_to_gitlab(host, "df -BG /")
    if ssh_result["success"]:
        try:
            lines = ssh_result["stdout"].strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 4:
                    storage_str = parts[3].replace('G', '')
                    return int(storage_str)
        except (ValueError, IndexError):
            pass
    return 0


def verify_puma_workers(host) -> Dict[str, Any]:
    """
    Verify that puma workers are configured correctly in gitlab.rb.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, expected, actual, and error keys
    """
    result = {
        "success": False,
        "expected": 0,
        "actual": 0,
        "error": "",
    }

    expected = get_gitlab_puma_workers(host)
    result["expected"] = expected

    # Use simpler grep command and parse output manually
    ssh_result = ssh_to_gitlab(
        host,
        f"grep worker_processes {GITLAB_RB_PATH}"
    )

    if not ssh_result["success"]:
        result["error"] = f"Failed to read puma config: {ssh_result['error']}"
        return result

    try:
        # Parse: puma['worker_processes'] = 2
        output = ssh_result["stdout"]
        for line in output.split('\n'):
            if 'worker_processes' in line and '=' in line:
                value_part = line.split('=')[1].strip()
                result["actual"] = int(value_part)
                break
    except (ValueError, IndexError):
        result["error"] = f"Invalid puma workers value: {ssh_result['stdout']}"
        return result

    if result["actual"] == expected:
        result["success"] = True
    else:
        result["error"] = f"Puma workers mismatch: expected {expected}, actual {result['actual']}"

    return result


def verify_sidekiq_concurrency(host) -> Dict[str, Any]:
    """
    Verify that sidekiq concurrency is configured correctly in gitlab.rb.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, expected, actual, and error keys
    """
    result = {
        "success": False,
        "expected": 0,
        "actual": 0,
        "error": "",
    }

    expected = get_gitlab_sidekiq_concurrency(host)
    result["expected"] = expected

    # Use simpler grep command and parse output manually
    ssh_result = ssh_to_gitlab(
        host,
        f"grep max_concurrency {GITLAB_RB_PATH}"
    )

    if not ssh_result["success"]:
        result["error"] = f"Failed to read sidekiq config: {ssh_result['error']}"
        return result

    try:
        # Parse: sidekiq['max_concurrency'] = 10
        output = ssh_result["stdout"]
        for line in output.split('\n'):
            if 'max_concurrency' in line and '=' in line:
                value_part = line.split('=')[1].strip()
                result["actual"] = int(value_part)
                break
    except (ValueError, IndexError):
        result["error"] = f"Invalid sidekiq concurrency value: {ssh_result['stdout']}"
        return result

    if result["actual"] == expected:
        result["success"] = True
    else:
        result["error"] = (
            f"Sidekiq concurrency mismatch: expected {expected}, "
            f"actual {result['actual']}"
        )

    return result


def verify_gitlab_project_exists(host) -> Dict[str, Any]:
    """
    Verify that the GitLab project exists.

    Uses gitlab-rails runner to check if project exists.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, project_name, project_id, and error keys
    """
    result = {
        "success": False,
        "project_name": "",
        "project_id": None,
        "error": "",
    }

    project_name = get_gitlab_project_name(host)
    result["project_name"] = project_name

    rails_cmd = GITLAB_RAILS_CMD_PROJECT_ID.format(project_name=project_name)
    ssh_result = ssh_to_gitlab(host, rails_cmd)

    if not ssh_result["success"]:
        result["error"] = f"Failed to query GitLab: {ssh_result['error']}"
        return result

    project_id = ssh_result["stdout"].strip()
    if project_id and project_id.isdigit():
        result["project_id"] = int(project_id)
        result["success"] = True
    else:
        result["error"] = f"Project '{project_name}' not found"

    return result


def verify_gitlab_project_visibility(host) -> Dict[str, Any]:
    """
    Verify that GitLab project visibility is configured correctly.

    Uses gitlab-rails runner to check project visibility.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, project_name, expected, actual, and error keys
    """
    result = {
        "success": False,
        "project_name": "",
        "expected": "",
        "actual": "",
        "error": "",
    }

    project_name = get_gitlab_project_name(host)
    expected_visibility = get_gitlab_project_visibility(host)
    result["project_name"] = project_name
    result["expected"] = expected_visibility

    # First verify project exists
    project_result = verify_gitlab_project_exists(host)
    if not project_result["success"]:
        result["error"] = project_result["error"]
        return result

    rails_cmd = GITLAB_RAILS_CMD_PROJECT_VISIBILITY.format(project_name=project_name)
    ssh_result = ssh_to_gitlab(host, rails_cmd)

    if not ssh_result["success"]:
        result["error"] = f"Failed to query GitLab: {ssh_result['error']}"
        return result

    actual_level = ssh_result["stdout"].strip()

    # Convert numeric level to human-readable name
    level_to_name = {v: k for k, v in GITLAB_VISIBILITY_LEVELS.items()}
    actual_visibility = level_to_name.get(actual_level, f"unknown({actual_level})")
    result["actual"] = actual_visibility

    expected_level = GITLAB_VISIBILITY_LEVELS.get(expected_visibility, "0")

    if actual_level == expected_level:
        result["success"] = True
    else:
        result["error"] = (
            f"Visibility mismatch: expected {expected_visibility}, "
            f"actual {actual_visibility}"
        )

    return result


def verify_gitlab_default_branch(host) -> Dict[str, Any]:
    """
    Verify that GitLab project default branch is configured correctly.

    Uses gitlab-rails runner to check default branch.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, project_name, expected, actual, and error keys
    """
    result = {
        "success": False,
        "project_name": "",
        "expected": "",
        "actual": "",
        "error": "",
    }

    project_name = get_gitlab_project_name(host)
    expected_branch = get_gitlab_default_branch(host)
    result["project_name"] = project_name
    result["expected"] = expected_branch

    # First verify project exists
    project_result = verify_gitlab_project_exists(host)
    if not project_result["success"]:
        result["error"] = project_result["error"]
        return result

    rails_cmd = GITLAB_RAILS_CMD_PROJECT_DEFAULT_BRANCH.format(project_name=project_name)
    ssh_result = ssh_to_gitlab(host, rails_cmd)

    if not ssh_result["success"]:
        result["error"] = f"Failed to query GitLab: {ssh_result['error']}"
        return result

    actual_branch = ssh_result["stdout"].strip()
    result["actual"] = actual_branch

    if actual_branch == expected_branch:
        result["success"] = True
    else:
        result["error"] = (
            f"Default branch mismatch: expected {expected_branch}, actual {actual_branch}"
        )

    return result


# =============================================================================
# GITLAB INSTALL VERIFICATION FUNCTIONS
# =============================================================================

def verify_gitlab_runner_quadlet_exists(host) -> Dict[str, Any]:
    """
    Verify gitlab-runner quadlet file exists on GitLab server.

    Checks if quadlet file exists at configured path.
    """
    result = {
        "success": False,
        "quadlet_path": f"{GITLAB_RUNNER_QUADLET_DIR}/{GITLAB_RUNNER_QUADLET_FILE}",
        "exists": False,
        "error": "",
    }

    quadlet_path = f"{GITLAB_RUNNER_QUADLET_DIR}/{GITLAB_RUNNER_QUADLET_FILE}"
    ssh_result = ssh_to_gitlab(
        host,
        f"test -f {quadlet_path} && echo EXISTS || echo NOT_FOUND"
    )

    if not ssh_result["success"]:
        result["error"] = ssh_result["error"]
        return result

    if "EXISTS" in ssh_result["stdout"]:
        result["exists"] = True
        result["success"] = True
    else:
        result["error"] = f"Quadlet file not found: {result['quadlet_path']}"

    return result


def verify_gitlab_runner_services_status(host) -> Dict[str, Any]:
    """
    Verify all GitLab runner services are running on GitLab server.

    Checks gitlab-runner.service and gitlab-runsvdir.service.
    Returns consolidated status like prepare_oim service check.
    """
    result = {
        "success": False,
        "results": [],
        "passed": 0,
        "failed": 0,
        "total": 0,
        "details": "",
        "error": "",
    }

    passed = 0
    failed = 0
    results = []

    for svc in GITLAB_RUNNER_SERVICES:
        svc_name = svc["name"]
        ssh_result = ssh_to_gitlab(
            host,
            f"systemctl is-active {svc_name} 2>/dev/null"
        )

        if not ssh_result["success"]:
            result["error"] = ssh_result["error"]
            return result

        status = ssh_result["stdout"].strip()
        is_active = status == "active"

        if is_active:
            verdict = "pass"
            message = f"{svc_name}: active"
            passed += 1
        else:
            verdict = "fail"
            message = f"{svc_name}: {status} (expected active)"
            failed += 1

        results.append({
            "name": svc_name,
            "description": svc["description"],
            "status": status,
            "is_active": is_active,
            "verdict": verdict,
            "message": message,
        })

    total = passed + failed
    details = f"Services: {passed}/{total} running\n"
    for svc in results:
        mark = "✓" if svc["verdict"] == "pass" else "✘"
        details += f"  {mark} {svc['message']}\n"

    result["success"] = failed == 0
    result["results"] = results
    result["passed"] = passed
    result["failed"] = failed
    result["total"] = total
    result["details"] = details

    return result


def verify_gitlab_server_reachable(host) -> Dict[str, Any]:
    """
    Verify GitLab server is reachable from omnia_core container via SSH.

    Uses ssh to check if GitLab server responds.
    """
    result = {
        "success": False,
        "gitlab_host": "",
        "error": "",
    }

    gitlab_host = get_gitlab_host(host)
    result["gitlab_host"] = gitlab_host

    if not gitlab_host:
        result["error"] = "gitlab_host not configured in gitlab_config.yml"
        return result

    ssh_result = ssh_to_gitlab(host, "echo REACHABLE")

    if ssh_result["success"] and "REACHABLE" in ssh_result["stdout"]:
        result["success"] = True
    else:
        result["error"] = f"GitLab server {gitlab_host} not reachable: {ssh_result['error']}"

    return result


# =============================================================================
# GITLAB CLEANUP VERIFICATION FUNCTIONS
# =============================================================================

def verify_gitlab_runner_container_removed(host) -> Dict[str, Any]:
    """
    Verify gitlab-runner container is removed after cleanup.

    Checks that specific container does not exist using podman ps filter.
    """
    result = {
        "success": False,
        "container": GITLAB_RUNNER_CONTAINER,
        "exists": True,
        "error": "",
    }

    # Use podman ps -a to check if container exists
    cmd = 'podman ps -a --format "{{.Names}}" 2>/dev/null || true'
    ssh_result = ssh_to_gitlab(host, cmd)

    # Check stdout for container name
    if GITLAB_RUNNER_CONTAINER in ssh_result["stdout"]:
        result["error"] = f"Container {GITLAB_RUNNER_CONTAINER} still exists"
    else:
        result["exists"] = False
        result["success"] = True

    return result


def verify_gitlab_runner_quadlet_removed(host) -> Dict[str, Any]:
    """
    Verify gitlab-runner quadlet file is removed after cleanup.

    Checks that quadlet file does not exist at configured path.
    """
    result = {
        "success": False,
        "quadlet_path": f"{GITLAB_RUNNER_QUADLET_DIR}/{GITLAB_RUNNER_QUADLET_FILE}",
        "exists": True,
        "error": "",
    }

    quadlet_path = f"{GITLAB_RUNNER_QUADLET_DIR}/{GITLAB_RUNNER_QUADLET_FILE}"
    ssh_result = ssh_to_gitlab(
        host,
        f"test -f {quadlet_path} && echo EXISTS || echo NOT_FOUND"
    )

    if not ssh_result["success"]:
        result["error"] = ssh_result["error"]
        return result

    if "NOT_FOUND" in ssh_result["stdout"]:
        result["exists"] = False
        result["success"] = True
    else:
        result["error"] = f"Quadlet file still exists: {result['quadlet_path']}"

    return result


def verify_gitlab_runner_services_stopped(host) -> Dict[str, Any]:
    """
    Verify all GitLab runner services are stopped after cleanup.

    Checks gitlab-runner.service and gitlab-runsvdir.service are not active.
    Returns consolidated status like prepare_oim service check.
    """
    result = {
        "success": False,
        "results": [],
        "passed": 0,
        "failed": 0,
        "total": 0,
        "details": "",
        "error": "",
    }

    passed = 0
    failed = 0
    results = []

    for svc in GITLAB_RUNNER_SERVICES:
        svc_name = svc["name"]
        ssh_result = ssh_to_gitlab(
            host,
            f"systemctl is-active {svc_name} 2>/dev/null"
        )

        status = ssh_result["stdout"].strip() if ssh_result["stdout"] else "inactive"
        is_stopped = status in ["inactive", "failed", ""]

        if is_stopped:
            verdict = "pass"
            message = f"{svc_name}: stopped"
            passed += 1
        else:
            verdict = "fail"
            message = f"{svc_name}: {status} (expected stopped)"
            failed += 1

        results.append({
            "name": svc_name,
            "description": svc["description"],
            "status": status,
            "is_stopped": is_stopped,
            "verdict": verdict,
            "message": message,
        })

    total = passed + failed
    details = f"Services: {passed}/{total} stopped\n"
    for svc in results:
        mark = "✓" if svc["verdict"] == "pass" else "✘"
        details += f"  {mark} {svc['message']}\n"

    result["success"] = failed == 0
    result["results"] = results
    result["passed"] = passed
    result["failed"] = failed
    result["total"] = total
    result["details"] = details

    return result


def verify_gitlab_url_not_accessible(host) -> Dict[str, Any]:
    """
    Verify GitLab URL is NOT accessible after cleanup.

    Uses curl to check that GitLab does not respond.
    """
    result = {
        "success": False,
        "url": "",
        "http_code": 0,
        "error": "",
    }

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)

    if not gitlab_host:
        result["error"] = "gitlab_host not configured in gitlab_config.yml"
        return result

    url = f"https://{gitlab_host}:{gitlab_port}/"
    result["url"] = url

    cmd = run_on_oim(
        host,
        f"curl -k -s -o /dev/null -w '%{{http_code}}' --connect-timeout 5 '{url}' 2>/dev/null"
    )

    http_code = cmd.stdout.strip() if cmd.stdout else "0"
    try:
        result["http_code"] = int(http_code)
    except ValueError:
        result["http_code"] = 0

    # Success means GitLab is NOT accessible
    if result["http_code"] == 0 or result["http_code"] >= 500:
        result["success"] = True
    else:
        result["error"] = f"GitLab still accessible at {url} (HTTP {result['http_code']})"

    return result


def verify_gitlab_directories_removed(host) -> Dict[str, Any]:
    """
    Verify GitLab directories are removed after cleanup.

    Checks /etc/gitlab, /var/opt/gitlab, /var/log/gitlab, /opt/gitlab.
    """
    result = {
        "success": False,
        "directories": GITLAB_CLEANUP_DIRECTORIES,
        "existing": [],
        "removed": [],
        "error": "",
    }

    for directory in GITLAB_CLEANUP_DIRECTORIES:
        ssh_result = ssh_to_gitlab(
            host,
            f"test -d {directory} && echo EXISTS || echo NOT_FOUND"
        )

        if ssh_result["success"]:
            if "EXISTS" in ssh_result["stdout"]:
                result["existing"].append(directory)
            else:
                result["removed"].append(directory)

    if not result["existing"]:
        result["success"] = True
    else:
        result["error"] = f"Directories still exist: {', '.join(result['existing'])}"

    return result


def verify_gitlab_services_stopped(host) -> Dict[str, Any]:
    """
    Verify all GitLab services are stopped after cleanup.

    Checks that gitlab-ctl status returns error or no services running.
    """
    result = {
        "success": False,
        "services": GITLAB_SERVICES,
        "running": [],
        "error": "",
    }

    ssh_result = ssh_to_gitlab(host, "gitlab-ctl status 2>/dev/null")

    # If gitlab-ctl doesn't exist or returns error, cleanup was successful
    if not ssh_result["success"] or "command not found" in ssh_result["stderr"].lower():
        result["success"] = True
        return result

    output = ssh_result["stdout"]
    for service in GITLAB_SERVICES:
        for line in output.split('\n'):
            if service in line and line.startswith("run:"):
                result["running"].append(service)

    if not result["running"]:
        result["success"] = True
    else:
        result["error"] = f"Services still running: {', '.join(result['running'])}"

    return result


def verify_catalog_synced(host) -> Dict[str, Any]:
    """
    Verify that the omnia-catalog is synced to GitLab.

    Checks if .gitlab-ci.yml exists in the repository.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, project_name, ci_file_exists, and error keys
    """
    result = {
        "success": False,
        "project_name": "",
        "ci_file_exists": False,
        "files_found": [],
        "error": "",
    }

    project_name = get_gitlab_project_name(host)
    result["project_name"] = project_name

    # First verify project exists
    project_result = verify_gitlab_project_exists(host)
    if not project_result["success"]:
        result["error"] = project_result["error"]
        return result

    # Check if .gitlab-ci.yml exists using API
    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    gitlab_password = get_gitlab_root_password(host)

    if not gitlab_password:
        result["error"] = "gitlab_root_password not found in credentials"
        return result

    token_cmd = GITLAB_RAILS_CMD_ROOT_TOKEN
    ssh_result = ssh_to_gitlab(host, token_cmd)

    if ssh_result["success"] and ssh_result["stdout"]:
        token = ssh_result["stdout"].strip()
        # Use API to check repository files
        api_url = (
            f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}/"
            f"projects/{project_result['project_id']}/repository/tree"
        )
        api_cmd = (
            f"curl -k -s --header 'PRIVATE-TOKEN: {token}' '{api_url}' "
            f"2>/dev/null | grep -o '\"name\":\"[^\"]*\"' | head -10"
        )
        cmd = run_in_container(host, api_cmd)
        if cmd.rc == 0 and cmd.stdout:
            files = [f.split('"')[3] for f in cmd.stdout.strip().split('\n') if '"name":' in f]
            result["files_found"] = files
            if ".gitlab-ci.yml" in files:
                result["ci_file_exists"] = True
                result["success"] = True
            else:
                result["error"] = ".gitlab-ci.yml not found in repository"
        else:
            result["error"] = "Failed to list repository files"
    else:
        # Fallback: check via git
        ssh_result = ssh_to_gitlab(
            host,
            f"ls {GITLAB_GIT_DATA_PATH} 2>/dev/null | head -1"
        )
        if ssh_result["success"] and ssh_result["stdout"]:
            result["success"] = True
            result["ci_file_exists"] = True  # Assume synced if repo exists
        else:
            result["error"] = "Could not verify catalog sync"

    return result


# =============================================================================
# GITLAB PACKAGE VERIFICATION FUNCTIONS
# =============================================================================

def verify_gitlab_packages_installed(host) -> Dict[str, Any]:
    """
    Verify GitLab packages are installed on GitLab server.

    Checks each package from GITLAB_INSTALLED_PACKAGES using rpm -q.
    """
    result = {
        "success": False,
        "installed": [],
        "not_installed": [],
        "expected": GITLAB_INSTALLED_PACKAGES,
        "error": "",
    }

    for pkg in GITLAB_INSTALLED_PACKAGES:
        ssh_result = ssh_to_gitlab(host, f"rpm -q {pkg}")

        # rpm -q returns non-zero when package not found
        # Only fail if SSH connection itself failed
        err = ssh_result.get("error", "").lower()
        if "ssh" in err and "connection" in err:
            result["error"] = ssh_result["error"]
            return result

        if ssh_result["rc"] == 0:
            result["installed"].append(pkg)
        else:
            result["not_installed"].append(pkg)

    if not result["not_installed"]:
        result["success"] = True
    else:
        result["error"] = f"Missing packages: {result['not_installed']}"

    return result


def verify_gitlab_packages_removed(host) -> Dict[str, Any]:
    """
    Verify GitLab packages are removed after cleanup.

    Checks each package from GITLAB_INSTALLED_PACKAGES using rpm -q.
    Only checks the same packages that were installed.
    """
    result = {
        "success": False,
        "removed": [],
        "still_installed": [],
        "expected_removed": GITLAB_INSTALLED_PACKAGES,
        "error": "",
    }

    for pkg in GITLAB_INSTALLED_PACKAGES:
        ssh_result = ssh_to_gitlab(host, f"rpm -q {pkg}")

        # rpm -q returns non-zero when package not found, which is expected
        # Only fail if SSH connection itself failed
        err = ssh_result.get("error", "").lower()
        if "ssh" in err and "connection" in err:
            result["error"] = ssh_result["error"]
            return result

        if ssh_result["rc"] == 0:
            result["still_installed"].append(pkg)
        else:
            result["removed"].append(pkg)

    if not result["still_installed"]:
        result["success"] = True
    else:
        result["error"] = f"Packages still installed: {result['still_installed']}"

    return result


def verify_gitlab_port_free(host) -> Dict[str, Any]:
    """
    Verify GitLab HTTPS port is free after cleanup.

    Checks that the configured gitlab_https_port is not in use.
    """
    result = {
        "success": False,
        "port": 0,
        "in_use": True,
        "error": "",
    }

    gitlab_port = get_gitlab_https_port(host)
    result["port"] = gitlab_port

    # Check if port is listening on GitLab server
    cmd = f"ss -tlnp | grep -w {gitlab_port} || true"
    ssh_result = ssh_to_gitlab(host, cmd)

    if not ssh_result["stdout"].strip():
        # Port is not in use - good for cleanup
        result["in_use"] = False
        result["success"] = True
    else:
        result["error"] = f"Port {gitlab_port} is still in use"

    return result


# =============================================================================
# GITLAB CI/CD PIPELINE VERIFICATION FUNCTIONS
# =============================================================================

def verify_gitlab_pipeline_file_exists(host) -> Dict[str, Any]:
    """
    Verify .gitlab-ci.yml pipeline file exists in GitLab project repository.

    Compares expected content from source file in omnia_core container
    with actual content in GitLab repository via API.
    """
    result = {
        "success": False,
        "file": GITLAB_CI_PIPELINE_FILE,
        "exists": False,
        "content_matches": False,
        "project_name": "",
        "branch": "",
        "error": "",
    }

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    project_name = get_gitlab_project_name(host)
    default_branch = get_gitlab_default_branch(host)

    result["project_name"] = project_name
    result["branch"] = default_branch

    if not gitlab_host or not project_name:
        result["error"] = "gitlab_host or gitlab_project_name not configured"
        return result

    expected_cmd = f"cat {GITLAB_CI_PIPELINE_SOURCE_FILE} | md5sum | cut -d' ' -f1"
    expected_result = run_in_container(host, expected_cmd)

    if expected_result.rc != 0:
        result["error"] = "Failed to read pipeline source file"
        return result

    expected_hash = expected_result.stdout.strip()

    # Get actual content from GitLab repository via API
    # Single SSH call: get token and fetch file content
    full_project_path = f"root/{project_name}" if "/" not in project_name else project_name
    encoded_project = full_project_path.replace("/", "%2F")
    api_url = f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
    file_url = f"{api_url}/projects/{encoded_project}/repository/files"
    file_url = f"{file_url}/{GITLAB_CI_PIPELINE_FILE}?ref={default_branch}"

    # Combined command: read token, fetch file, decode base64, compute hash
    # Uses jq for proper JSON parsing
    combined_cmd = (
        f'TOKEN=$(cat {GITLAB_ROOT_TOKEN_FILE}); '
        f'curl -sk -H "PRIVATE-TOKEN: $TOKEN" "{file_url}" | '
        f'jq -r ".content // empty" | base64 -d 2>/dev/null | '
        f'md5sum | cut -d" " -f1 || echo "FILE_NOT_FOUND"'
    )

    ssh_result = ssh_to_gitlab(host, combined_cmd)

    if not ssh_result["success"]:
        result["error"] = f"Failed to fetch file from GitLab: {ssh_result['error']}"
        return result

    actual_hash = ssh_result["stdout"].strip()

    if actual_hash == "FILE_NOT_FOUND" or not actual_hash:
        result["error"] = "Pipeline file not found in repository"
        return result

    # Compare hashes
    result["exists"] = True
    if expected_hash == actual_hash:
        result["content_matches"] = True
        result["success"] = True
    else:
        result["error"] = f"Content mismatch: expected hash {expected_hash}, got {actual_hash}"

    return result


def verify_gitlab_pipeline_variables(host) -> Dict[str, Any]:
    """
    Verify GitLab pipeline variables are configured with correct values.

    Checks that GITLAB_API_TOKEN, BSM_API_URL, BSM_API_USERNAME, BSM_API_PASSWORD,
    BSM_API_CERT variables are set with expected values from config files.

    Expected values come from:
    - GITLAB_API_TOKEN: /root/.gitlab_root_token on GitLab server
    - BSM_API_URL: https://{build_stream_host_ip}:{build_stream_port}
    - BSM_API_USERNAME: auth_registration.username from oauth credentials
    - BSM_API_PASSWORD: auth_registration.password from oauth credentials
    - BSM_API_CERT: certificate content (just check exists)
    """
    result = {
        "success": False,
        "expected": GITLAB_PIPELINE_VARIABLES,
        "configured_correctly": [],
        "missing": [],
        "value_mismatch": [],
        "project_name": "",
        "error": "",
    }

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    project_name = get_gitlab_project_name(host)

    result["project_name"] = project_name

    if not gitlab_host or not project_name:
        result["error"] = "gitlab_host or gitlab_project_name not configured"
        return result

    # Check if build_stream is enabled
    build_stream_enabled = get_input_value(
        host, BUILD_STREAM_CONFIG_FILE, "enable_build_stream", default=False
    )
    if not build_stream_enabled:
        result["error"] = "build_stream is not enabled - pipeline variables not expected"
        return result

    # Build expected values dictionary from config files
    # 1. BSM_API_URL from build_stream_config.yml
    build_stream_host = get_input_value(
        host, BUILD_STREAM_CONFIG_FILE, "build_stream_host_ip", default=""
    )
    build_stream_port = get_input_value(
        host, BUILD_STREAM_CONFIG_FILE, "build_stream_port", default=8010
    )

    # 2. BSM_API_USERNAME and BSM_API_PASSWORD from oauth credentials
    oauth_creds = view_credentials_file(
        host,
        BUILD_STREAM_OAUTH_CREDENTIALS_PATH,
        BUILD_STREAM_OAUTH_CREDENTIALS_KEY_PATH
    )

    expected_username = ""
    expected_password = ""
    if oauth_creds["success"]:
        auth_reg = oauth_creds["content"].get("auth_registration", {})
        expected_username = auth_reg.get("username", "")
        expected_password = auth_reg.get("password", "")

    # 3. BSM_API_CERT from /opt/omnia/build_stream_ssl/ssl/bs_cert.pem in omnia_core
    cert_path = "/opt/omnia/build_stream_ssl/ssl/bs_cert.pem"
    cert_result = run_in_container(host, f"cat {cert_path} 2>/dev/null")
    expected_cert = cert_result.stdout.strip() if cert_result.rc == 0 else ""

    # 4. GITLAB_API_TOKEN from /root/.gitlab_root_token on GitLab server
    # Will be fetched along with variables in single SSH call

    # Store all expected values in dictionary for comparison
    expected_values = {
        "BSM_API_URL": f"https://{build_stream_host}:{build_stream_port}",
        "BSM_API_USERNAME": expected_username,
        "BSM_API_PASSWORD": expected_password,
        "BSM_API_CERT": expected_cert,
        # GITLAB_API_TOKEN - compare with token from GitLab server
    }

    # Single SSH call to GitLab: get token AND fetch all variables
    # Output format: TOKEN_VALUE|||JSON_RESPONSE (separated by |||)
    full_project_path = f"root/{project_name}" if "/" not in project_name else project_name
    encoded_project = full_project_path.replace("/", "%2F")
    api_url = f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
    vars_url = f"{api_url}/projects/{encoded_project}/variables"

    # Combined command: read token, output it, then fetch variables
    # Output: TOKEN|||JSON_RESPONSE
    combined_cmd = (
        f'TOKEN=$(cat {GITLAB_ROOT_TOKEN_FILE}); '
        f'echo "$TOKEN|||$(curl -sk -H "PRIVATE-TOKEN: $TOKEN" "{vars_url}")"'
    )

    ssh_result = ssh_to_gitlab(host, combined_cmd)
    if not ssh_result["success"]:
        result["error"] = f"Failed to fetch variables: {ssh_result['error']}"
        return result

    # Parse the response: TOKEN|||JSON_RESPONSE
    try:
        output = ssh_result["stdout"].strip()
        if "|||" not in output:
            result["error"] = f"Invalid response format: {output[:100]}"
            return result

        expected_token, json_content = output.split("|||", 1)
        expected_token = expected_token.strip()

        # Add expected token to expected_values for comparison
        expected_values["GITLAB_API_TOKEN"] = expected_token

        if not json_content:
            result["error"] = "Empty response from variables API"
            return result

        variables_data = json.loads(json_content)
        if not isinstance(variables_data, list):
            # API returned error (e.g., 401 Unauthorized)
            if isinstance(variables_data, dict) and "message" in variables_data:
                result["error"] = f"API error: {variables_data['message']}"
            else:
                result["error"] = f"Unexpected response: {json_content[:100]}"
            return result

        # Build actual variables dictionary from API response
        actual_variables = {var["key"]: var["value"] for var in variables_data}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        result["error"] = f"Failed to parse response: {str(e)[:100]}"
        return result

    # Compare expected vs actual for each pipeline variable
    for var_name in GITLAB_PIPELINE_VARIABLES:
        if var_name not in actual_variables:
            result["missing"].append(var_name)
        else:
            actual_value = actual_variables[var_name].strip()

            if var_name in expected_values:
                # Compare with expected value (strip whitespace for comparison)
                expected_val = expected_values[var_name].strip()
                if actual_value == expected_val:
                    result["configured_correctly"].append(var_name)
                else:
                    # Truncate long values for display
                    max_len = 50
                    if len(expected_val) > max_len:
                        exp_display = expected_val[:max_len] + "..."
                    else:
                        exp_display = expected_val
                    if len(actual_value) > max_len:
                        act_display = actual_value[:max_len] + "..."
                    else:
                        act_display = actual_value
                    result["value_mismatch"].append({
                        "variable": var_name,
                        "expected": exp_display,
                        "actual": act_display
                    })
            else:
                # Unknown variable - just verify non-empty
                if actual_value:
                    result["configured_correctly"].append(var_name)
                else:
                    result["missing"].append(var_name)

    # Set success if no missing and no mismatches
    if not result["missing"] and not result["value_mismatch"]:
        result["success"] = True
    else:
        errors = []
        if result["missing"]:
            errors.append(f"Missing: {result['missing']}")
        if result["value_mismatch"]:
            mismatches = [v['variable'] for v in result["value_mismatch"]]
            errors.append(f"Value mismatch: {mismatches}")
        result["error"] = "; ".join(errors)

    return result
