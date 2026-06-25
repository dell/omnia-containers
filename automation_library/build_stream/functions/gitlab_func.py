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
Build Stream GitLab Functions (v2.1).

Functions for interacting with GitLab server for pipeline automation.
All runtime values are read from config files via core module functions.
"""

import json
import time
import base64
from typing import Dict, Any

from automation_library.core import run_on_oim

from .shared_func import (
    get_gitlab_host,
    get_gitlab_https_port,
    get_gitlab_project_name,
    get_gitlab_default_branch,
    ssh_to_gitlab,
)
from ..vars.build_stream_vars import (
    GITLAB_API_VERSION,
    GITLAB_ROOT_TOKEN_FILE,
    CATALOG_FILE_PATH,
    PIPELINE_POLL_INTERVAL,
    PIPELINE_POLL_TIMEOUT,
)


def verify_gitlab_server_running(host) -> Dict[str, Any]:
    """
    Verify GitLab server is running and accessible.

    Args:
        host: Testinfra host object

    Returns:
        Dict with 'success', 'url', 'http_code', 'details', 'error'.
    """
    result = {
        "success": False,
        "url": "",
        "http_code": 0,
        "details": "",
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
        f"curl -sk -o /dev/null -w '%{{http_code}}' '{url}' 2>/dev/null"
    )

    http_code = cmd.stdout.strip() if cmd.stdout else "0"
    try:
        result["http_code"] = int(http_code)
    except ValueError:
        result["http_code"] = 0

    if result["http_code"] in [200, 302]:
        result["success"] = True
        result["details"] = f"GitLab accessible at {url} (HTTP {result['http_code']})"
    else:
        result["error"] = f"GitLab not accessible at {url} (HTTP {result['http_code']})"

    return result


def verify_gitlab_runner_running(host) -> Dict[str, Any]:
    """
    Verify GitLab runner container is running on GitLab server.

    Args:
        host: Testinfra host object

    Returns:
        Dict with 'success', 'container', 'status', 'details', 'error'.
    """
    result = {
        "success": False,
        "container": "gitlab-runner",
        "status": "",
        "details": "",
        "error": "",
    }

    ssh_result = ssh_to_gitlab(host, 'podman ps --format "{{.Names}} {{.Status}}" 2>/dev/null')

    if not ssh_result["success"]:
        result["error"] = ssh_result["error"]
        return result

    if "gitlab-runner" in ssh_result["stdout"]:
        for line in ssh_result["stdout"].strip().split("\n"):
            if "gitlab-runner" in line:
                result["status"] = line.strip()
                result["success"] = True
                result["details"] = f"GitLab runner is running: {line.strip()}"
                return result

    result["error"] = "GitLab runner container not found or not running"
    return result


def get_gitlab_root_token(host) -> Dict[str, Any]:
    """
    Get GitLab root token from GitLab server.

    Args:
        host: Testinfra host object

    Returns:
        Dict with 'success', 'token', 'error'.
    """
    result = {
        "success": False,
        "token": "",
        "error": "",
    }

    ssh_result = ssh_to_gitlab(host, f"cat {GITLAB_ROOT_TOKEN_FILE} 2>/dev/null")

    if not ssh_result["success"]:
        result["error"] = f"Failed to read GitLab token: {ssh_result['error']}"
        return result

    token = ssh_result["stdout"].strip()
    if token:
        result["success"] = True
        result["token"] = token
    else:
        result["error"] = "GitLab root token file is empty"

    return result


def list_pipelines(host, per_page: int = 10) -> Dict[str, Any]:
    """
    List recent pipelines from GitLab.

    Args:
        host: Testinfra host object
        per_page: Number of pipelines to return

    Returns:
        Dict with 'success', 'pipelines' (list), 'error'.
    """
    result = {
        "success": False,
        "pipelines": [],
        "error": "",
    }

    token_result = get_gitlab_root_token(host)
    if not token_result["success"]:
        result["error"] = token_result["error"]
        return result

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    project_name = get_gitlab_project_name(host)

    if not gitlab_host or not project_name:
        result["error"] = "GitLab host or project not configured"
        return result

    url = (
        f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
        f"/projects/root%2F{project_name}/pipelines?per_page={per_page}"
    )

    cmd = run_on_oim(
        host,
        f"curl -sk '{url}' --header 'PRIVATE-TOKEN: {token_result['token']}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to list pipelines: {cmd.stderr}"
        return result

    try:
        pipelines = json.loads(cmd.stdout.strip())
        result["pipelines"] = pipelines
        result["success"] = True
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result


def cancel_pipeline(host, pipeline_id: int) -> Dict[str, Any]:
    """
    Cancel a running or pending pipeline.

    Args:
        host: Testinfra host object
        pipeline_id: Pipeline ID to cancel

    Returns:
        Dict with 'success', 'pipeline_id', 'status', 'error'.
    """
    result = {
        "success": False,
        "pipeline_id": pipeline_id,
        "status": "",
        "error": "",
    }

    token_result = get_gitlab_root_token(host)
    if not token_result["success"]:
        result["error"] = token_result["error"]
        return result

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    project_name = get_gitlab_project_name(host)

    url = (
        f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
        f"/projects/root%2F{project_name}/pipelines/{pipeline_id}/cancel"
    )

    cmd = run_on_oim(
        host,
        f"curl -sk -X POST '{url}' --header 'PRIVATE-TOKEN: {token_result['token']}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to cancel pipeline: {cmd.stderr}"
        return result

    try:
        pipeline = json.loads(cmd.stdout.strip())
        result["status"] = pipeline.get("status", "")
        result["success"] = True
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result


def upload_catalog_file(host, catalog_content: str) -> Dict[str, Any]:
    """
    Upload catalog file to GitLab repository by committing it.

    Args:
        host: Testinfra host object
        catalog_content: Catalog JSON content to commit

    Returns:
        Dict with 'success', 'commit_sha', 'error'.
    """
    return commit_gitlab_file(
        host,
        CATALOG_FILE_PATH,
        catalog_content,
        "Update catalog for pipeline trigger"
    )


def wait_for_pipeline_triggered(
    host,
    initial_pipeline_id: int = 0,
    timeout: int = None,
    poll_interval: int = None,
    log_callback=None,
) -> Dict[str, Any]:
    """
    Wait for a new pipeline to be triggered (pipeline_id > initial_pipeline_id).

    Args:
        host: Testinfra host object
        initial_pipeline_id: Pipeline ID before trigger (new must be greater)
        timeout: Max seconds to wait (default: PIPELINE_POLL_TIMEOUT)
        poll_interval: Seconds between polls (default: PIPELINE_POLL_INTERVAL)
        log_callback: Optional callback for logging

    Returns:
        Dict with 'success', 'pipeline_id', 'status', 'elapsed', 'error'.
    """
    if timeout is None:
        timeout = PIPELINE_POLL_TIMEOUT
    if poll_interval is None:
        poll_interval = PIPELINE_POLL_INTERVAL

    result = {
        "success": False,
        "pipeline_id": 0,
        "status": "",
        "elapsed": 0,
        "error": "",
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)

    start_time = time.time()
    poll_count = 0
    while time.time() - start_time < timeout:
        poll_count += 1
        elapsed = int(time.time() - start_time)
        pipelines_result = list_pipelines(host, per_page=5)
        if not pipelines_result["success"]:
            result["error"] = pipelines_result["error"]
            return result

        pipelines = pipelines_result["pipelines"]
        if pipelines:
            latest_pipeline = pipelines[0]
            latest_id = latest_pipeline.get("id", 0)

            if latest_id > initial_pipeline_id:
                result["success"] = True
                result["pipeline_id"] = latest_id
                result["status"] = latest_pipeline.get("status", "")
                result["elapsed"] = elapsed
                _log(f"[{elapsed}s] New pipeline detected: ID={result['pipeline_id']}, status={result['status']}")
                return result

        if poll_count % 3 == 0:
            _log(f"[{elapsed}s] Waiting for pipeline... (latest ID: {latest_id if pipelines else 'N/A'})")

        time.sleep(poll_interval)

    result["elapsed"] = int(time.time() - start_time)
    result["error"] = f"No new pipeline triggered within {timeout} seconds"
    return result


def get_gitlab_file(host, file_path: str) -> Dict[str, Any]:
    """
    Read a file from the GitLab repository.

    Args:
        host: Testinfra host object
        file_path: Path to file in repository

    Returns:
        Dict with 'success', 'content', 'error'.
    """
    result = {
        "success": False,
        "content": "",
        "error": "",
    }

    token_result = get_gitlab_root_token(host)
    if not token_result["success"]:
        result["error"] = f"Failed to get GitLab token: {token_result['error']}"
        return result

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    project_name = get_gitlab_project_name(host)
    branch = get_gitlab_default_branch(host)

    if not gitlab_host or not project_name:
        result["error"] = "GitLab host or project not configured"
        return result

    encoded_path = file_path.replace("/", "%2F").replace(".", "%2E")

    url = (
        f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
        f"/projects/root%2F{project_name}/repository/files/{encoded_path}"
        f"?ref={branch}"
    )

    cmd = run_on_oim(
        host,
        f"curl -sk '{url}' --header 'PRIVATE-TOKEN: {token_result['token']}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to get file: {cmd.stderr}"
        return result

    try:
        response = json.loads(cmd.stdout.strip())
        if "content" not in response:
            result["error"] = f"File not found: {response.get('message', '')}"
            return result
        content_b64 = response["content"]
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"
        return result

    try:
        result["content"] = base64.b64decode(content_b64).decode('utf-8')
        result["success"] = True
    except Exception as e:
        result["error"] = f"Failed to decode file: {e}"

    return result


def commit_gitlab_file(host, file_path: str, content: str, commit_message: str) -> Dict[str, Any]:
    """
    Commit a file to the GitLab repository.

    Args:
        host: Testinfra host object
        file_path: Path to file in repository
        content: File content to commit
        commit_message: Commit message

    Returns:
        Dict with 'success', 'commit_sha', 'error'.
    """
    result = {
        "success": False,
        "commit_sha": "",
        "error": "",
    }

    token_result = get_gitlab_root_token(host)
    if not token_result["success"]:
        result["error"] = f"Failed to get GitLab token: {token_result['error']}"
        return result

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    project_name = get_gitlab_project_name(host)
    branch = get_gitlab_default_branch(host)

    if not gitlab_host or not project_name:
        result["error"] = "GitLab host or project not configured"
        return result

    encoded_path = file_path.replace("/", "%2F").replace(".", "%2E")

    url = (
        f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
        f"/projects/root%2F{project_name}/repository/files/{encoded_path}"
    )

    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

    payload = {
        "branch": branch,
        "content": content_b64,
        "commit_message": commit_message,
        "encoding": "base64"
    }

    payload_file = "/tmp/gitlab_commit_payload.json"
    cmd = run_on_oim(
        host,
        f"cat > {payload_file} << 'EOF'\n{json.dumps(payload)}\nEOF"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to write payload file: {cmd.stderr}"
        return result

    cmd = run_on_oim(
        host,
        f"curl -sk -X PUT '{url}' "
        f"--header 'PRIVATE-TOKEN: {token_result['token']}' "
        f"--header 'Content-Type: application/json' "
        f"--data @{payload_file}"
    )

    run_on_oim(host, f"rm -f {payload_file}")

    if cmd.rc != 0:
        result["error"] = f"Failed to commit file: {cmd.stderr}"
        return result

    try:
        response = json.loads(cmd.stdout.strip())
        if "id" in response:
            result["commit_sha"] = response.get("id", "")
            result["success"] = True
        elif "file_path" in response:
            result["success"] = True
        elif "message" in response:
            result["error"] = f"GitLab API error: {response['message']}"
        else:
            result["error"] = f"Unexpected response: {cmd.stdout[:200]}"
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result
