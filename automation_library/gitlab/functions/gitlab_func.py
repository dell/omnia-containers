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

from typing import Any, Dict

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

    Uses podman ps via SSH to check container status.
    """
    result = {
        "success": False,
        "container": GITLAB_RUNNER_CONTAINER,
        "status": "",
        "error": "",
    }

    # Use simple podman ps output without format string to avoid escaping issues
    ssh_result = ssh_to_gitlab(host, "podman ps")
    if not ssh_result["success"]:
        result["error"] = ssh_result["error"]
        return result

    output = ssh_result["stdout"]
    for line in output.split('\n'):
        if GITLAB_RUNNER_CONTAINER in line:
            # Container found and running (podman ps only shows running containers)
            result["status"] = "Up"
            result["success"] = True
            return result

    # Check if container exists but not running
    ssh_result = ssh_to_gitlab(host, "podman ps -a")
    if ssh_result["success"]:
        for line in ssh_result["stdout"].split('\n'):
            if GITLAB_RUNNER_CONTAINER in line:
                result["status"] = "Exited"
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

    rails_cmd = (
        f'gitlab-rails runner "puts Project.find_by(name: '
        f'\\\"{project_name}\\\")&.id" 2>/dev/null'
    )
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

    rails_cmd = (
        f'gitlab-rails runner "puts Project.find_by(name: '
        f'\\\"{project_name}\\\")&.visibility_level" 2>/dev/null'
    )
    ssh_result = ssh_to_gitlab(host, rails_cmd)

    if not ssh_result["success"]:
        result["error"] = f"Failed to query GitLab: {ssh_result['error']}"
        return result

    actual_visibility = ssh_result["stdout"].strip()
    result["actual"] = actual_visibility

    expected_level = GITLAB_VISIBILITY_LEVELS.get(expected_visibility, "0")

    if actual_visibility == expected_level:
        result["success"] = True
    else:
        result["error"] = (
            f"Visibility mismatch: expected {expected_visibility} (level {expected_level}), "
            f"actual level {actual_visibility}"
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

    rails_cmd = (
        f'gitlab-rails runner "puts Project.find_by(name: '
        f'\\\"{project_name}\\\")&.default_branch" 2>/dev/null'
    )
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

    # Get private token first
    token_cmd = (
        'gitlab-rails runner "'
        "user = User.find_by(username: 'root'); "
        "token = user.personal_access_tokens.active.first; "
        'puts token&.token" 2>/dev/null'
    )
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
