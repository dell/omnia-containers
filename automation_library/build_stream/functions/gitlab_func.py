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
Build Stream GitLab Functions.

Functions for interacting with GitLab server for pipeline automation.
All runtime values are read from config files via core module functions.
"""

import json
import time
import base64
from typing import Dict, Any, List, Optional

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


def get_pipeline_status(host, pipeline_id: int) -> Dict[str, Any]:
    """
    Get status of a specific pipeline.

    Args:
        host: Testinfra host object
        pipeline_id: Pipeline ID

    Returns:
        Dict with 'success', 'pipeline_id', 'status', 'source', 'error'.
    """
    result = {
        "success": False,
        "pipeline_id": pipeline_id,
        "status": "",
        "source": "",
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
        f"/projects/root%2F{project_name}/pipelines/{pipeline_id}"
    )

    cmd = run_on_oim(
        host,
        f"curl -sk '{url}' --header 'PRIVATE-TOKEN: {token_result['token']}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to get pipeline status: {cmd.stderr}"
        return result

    try:
        pipeline = json.loads(cmd.stdout.strip())
        result["status"] = pipeline.get("status", "")
        result["source"] = pipeline.get("source", "")
        result["success"] = True
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result


def get_pipeline_jobs(host, pipeline_id: int) -> Dict[str, Any]:
    """
    Get jobs for a specific pipeline.

    Args:
        host: Testinfra host object
        pipeline_id: Pipeline ID

    Returns:
        Dict with 'success', 'jobs' (list), 'error'.
    """
    result = {
        "success": False,
        "jobs": [],
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
        f"/projects/root%2F{project_name}/pipelines/{pipeline_id}/jobs"
    )

    cmd = run_on_oim(
        host,
        f"curl -sk '{url}' --header 'PRIVATE-TOKEN: {token_result['token']}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to get pipeline jobs: {cmd.stderr}"
        return result

    try:
        jobs = json.loads(cmd.stdout.strip())
        result["jobs"] = jobs
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


def get_child_pipeline_id(host, parent_pipeline_id: int) -> Dict[str, Any]:
    """
    Get the child pipeline ID from a parent pipeline (bridge job).

    Args:
        host: Testinfra host object
        parent_pipeline_id: Parent pipeline ID

    Returns:
        Dict with 'success', 'child_pipeline_id', 'error'.
    """
    result = {
        "success": False,
        "child_pipeline_id": 0,
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
        f"/projects/root%2F{project_name}/pipelines/{parent_pipeline_id}/bridges"
    )

    cmd = run_on_oim(
        host,
        f"curl -sk '{url}' --header 'PRIVATE-TOKEN: {token_result['token']}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to get bridges: {cmd.stderr}"
        return result

    try:
        bridges = json.loads(cmd.stdout.strip())
        for bridge in bridges:
            downstream = bridge.get("downstream_pipeline", {})
            if downstream and downstream.get("id"):
                result["child_pipeline_id"] = downstream["id"]
                result["success"] = True
                return result
        result["error"] = "No child pipeline found"
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result


def get_pipeline_jobs_by_stage(host, pipeline_id: int, stage: str = None) -> Dict[str, Any]:
    """
    Get jobs for a pipeline, optionally filtered by stage.

    Args:
        host: Testinfra host object
        pipeline_id: Pipeline ID
        stage: Optional stage name to filter

    Returns:
        Dict with 'success', 'jobs' (list), 'error'.
    """
    result = {
        "success": False,
        "jobs": [],
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
        f"/projects/root%2F{project_name}/pipelines/{pipeline_id}/jobs"
    )

    cmd = run_on_oim(
        host,
        f"curl -sk '{url}' --header 'PRIVATE-TOKEN: {token_result['token']}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to get jobs: {cmd.stderr}"
        return result

    try:
        jobs = json.loads(cmd.stdout.strip())
        if stage:
            jobs = [j for j in jobs if j.get("stage") == stage]
        result["jobs"] = jobs
        result["success"] = True
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result


def play_manual_job(host, job_id: int) -> Dict[str, Any]:
    """
    Play (trigger) a manual job in GitLab.

    Args:
        host: Testinfra host object
        job_id: Job ID to play

    Returns:
        Dict with 'success', 'job_id', 'status', 'error'.
    """
    result = {
        "success": False,
        "job_id": job_id,
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
        f"/projects/root%2F{project_name}/jobs/{job_id}/play"
    )

    cmd = run_on_oim(
        host,
        f"curl -sk -X POST '{url}' --header 'PRIVATE-TOKEN: {token_result['token']}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to play job: {cmd.stderr}"
        return result

    try:
        job = json.loads(cmd.stdout.strip())
        result["status"] = job.get("status", "")
        result["success"] = True
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result


def trigger_pipeline_with_variables(host, variables: Dict[str, str]) -> Dict[str, Any]:
    """
    Trigger a new pipeline with specified variables.

    Args:
        host: Testinfra host object
        variables: Dict of variable names to values (e.g., {"PIPELINE_TYPE": "cleanup"})

    Returns:
        Dict with 'success', 'pipeline_id', 'status', 'error'.
    """
    result = {
        "success": False,
        "pipeline_id": 0,
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
    branch = get_gitlab_default_branch(host)

    url = (
        f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
        f"/projects/root%2F{project_name}/pipeline"
    )

    var_list = [{"key": k, "value": v} for k, v in variables.items()]
    data = {
        "ref": branch,
        "variables": var_list
    }

    json_data = json.dumps(data)

    cmd = run_on_oim(
        host,
        f"curl -sk -X POST '{url}' "
        f"--header 'PRIVATE-TOKEN: {token_result['token']}' "
        f"--header 'Content-Type: application/json' "
        f"-d '{json_data}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to trigger pipeline: {cmd.stderr}"
        return result

    try:
        response = json.loads(cmd.stdout.strip())
        if "id" in response:
            result["pipeline_id"] = response["id"]
            result["status"] = response.get("status", "")
            result["success"] = True
        else:
            result["error"] = f"Pipeline trigger failed: {response.get('message', cmd.stdout[:200])}"
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result


def upload_catalog_file(host, catalog_content: str) -> Dict[str, Any]:
    """
    Upload catalog file to GitLab to trigger build pipeline.

    Args:
        host: Testinfra host object
        catalog_content: JSON content of the catalog file

    Returns:
        Dict with 'success', 'commit_id', 'file_path', 'error'.
    """
    result = {
        "success": False,
        "commit_id": "",
        "file_path": CATALOG_FILE_PATH,
        "error": "",
    }

    token_result = get_gitlab_root_token(host)
    if not token_result["success"]:
        result["error"] = token_result["error"]
        return result

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    project_name = get_gitlab_project_name(host)
    branch = get_gitlab_default_branch(host)

    if not gitlab_host or not project_name:
        result["error"] = "GitLab host or project not configured"
        return result

    encoded_content = base64.b64encode(catalog_content.encode()).decode()

    url = (
        f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
        f"/projects/root%2F{project_name}/repository/files/{CATALOG_FILE_PATH}"
    )

    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "branch": branch,
        "content": encoded_content,
        "commit_message": f"Automation: Update catalog to trigger build pipeline ({timestamp})",
        "encoding": "base64"
    }

    json_data = json.dumps(data)

    cmd = run_on_oim(
        host,
        f"curl -sk -X PUT '{url}' "
        f"--header 'PRIVATE-TOKEN: {token_result['token']}' "
        f"--header 'Content-Type: application/json' "
        f"-d '{json_data}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to upload catalog: {cmd.stderr}"
        return result

    try:
        response = json.loads(cmd.stdout.strip())
        if "file_path" in response:
            result["success"] = True
            result["commit_id"] = response.get("id", "")
        else:
            result["error"] = f"Upload failed: {response.get('message', cmd.stdout[:200])}"
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result


def commit_pxe_mapping_file(host) -> Dict[str, Any]:
    """
    Commit the PXE mapping file to trigger deploy pipeline.

    This function reads the current PXE mapping file from GitLab and
    re-commits it with a new commit message to trigger the deploy pipeline.

    Args:
        host: Testinfra host object

    Returns:
        Dict with 'success', 'commit_id', 'file_path', 'error'.
    """
    result = {
        "success": False,
        "commit_id": "",
        "file_path": "input/pxe_mapping_file.csv",
        "error": "",
    }

    token_result = get_gitlab_root_token(host)
    if not token_result["success"]:
        result["error"] = token_result["error"]
        return result

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    project_name = get_gitlab_project_name(host)
    branch = get_gitlab_default_branch(host)

    if not gitlab_host or not project_name:
        result["error"] = "GitLab host or project not configured"
        return result

    get_url = (
        f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
        f"/projects/root%2F{project_name}/repository/files/input%2Fpxe_mapping_file.csv"
        f"?ref={branch}"
    )

    cmd = run_on_oim(
        host,
        f"curl -sk '{get_url}' --header 'PRIVATE-TOKEN: {token_result['token']}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to get PXE mapping file: {cmd.stderr}"
        return result

    try:
        response = json.loads(cmd.stdout.strip())
        if "content" not in response:
            result["error"] = f"PXE mapping file not found: {response.get('message', '')}"
            return result
        current_content_b64 = response["content"]
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"
        return result

    import base64
    import datetime

    try:
        current_content = base64.b64decode(current_content_b64).decode('utf-8')
    except Exception as e:
        result["error"] = f"Failed to decode PXE mapping file: {e}"
        return result

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Swap the last two columns of each row to trigger a file change
    # This avoids adding comments which are not supported in CSV
    lines = current_content.strip().split('\n')
    modified_lines = []
    for line in lines:
        if line.strip() and not line.strip().startswith('#'):
            cols = line.split(',')
            if len(cols) >= 2:
                # Swap last two columns
                cols[-1], cols[-2] = cols[-2], cols[-1]
                modified_lines.append(','.join(cols))
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)
    modified_content = '\n'.join(modified_lines) + '\n'

    modified_content_b64 = base64.b64encode(modified_content.encode('utf-8')).decode('utf-8')

    put_url = (
        f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
        f"/projects/root%2F{project_name}/repository/files/input%2Fpxe_mapping_file.csv"
    )

    data = {
        "branch": branch,
        "content": modified_content_b64,
        "commit_message": f"Automation: Trigger deploy pipeline ({timestamp})",
        "encoding": "base64"
    }

    json_data = json.dumps(data)

    cmd = run_on_oim(
        host,
        f"curl -sk -X PUT '{put_url}' "
        f"--header 'PRIVATE-TOKEN: {token_result['token']}' "
        f"--header 'Content-Type: application/json' "
        f"-d '{json_data}'"
    )

    if cmd.rc != 0:
        result["error"] = f"Failed to commit PXE mapping file: {cmd.stderr}"
        return result

    try:
        response = json.loads(cmd.stdout.strip())
        if "file_path" in response:
            result["success"] = True
            result["commit_id"] = response.get("id", "")
        else:
            result["error"] = f"Commit failed: {response.get('message', cmd.stdout[:200])}"
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"

    return result


def wait_for_pipeline_triggered(
    host,
    initial_pipeline_id: int,
    timeout: int = PIPELINE_POLL_TIMEOUT,
    poll_interval: int = PIPELINE_POLL_INTERVAL,
    log_callback=None,
) -> Dict[str, Any]:
    """
    Wait for a new pipeline to be triggered after catalog upload.

    Args:
        host: Testinfra host object
        initial_pipeline_id: ID of the latest pipeline before upload
        timeout: Maximum time to wait in seconds
        poll_interval: Time between checks in seconds
        log_callback: Optional callback function for logging

    Returns:
        Dict with 'success', 'pipeline_id', 'status', 'elapsed', 'error'.
    """
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

        if poll_count % 3 == 0:  # Log every 3rd poll
            _log(f"[{elapsed}s] Waiting for pipeline... (latest ID: {latest_id if pipelines else 'N/A'})")

        time.sleep(poll_interval)

    result["elapsed"] = int(time.time() - start_time)
    result["error"] = f"No new pipeline triggered within {timeout} seconds"
    return result
