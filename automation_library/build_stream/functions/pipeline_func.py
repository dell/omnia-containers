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
Build Stream Pipeline Functions (v2.1).

Functions for triggering and monitoring build_stream pipelines.
v2.1 only has build pipeline (no deploy/cleanup).
"""

import sys
import time
from typing import Dict, Any

from .gitlab_func import (
    list_pipelines,
    upload_catalog_file,
    wait_for_pipeline_triggered,
    cancel_pipeline,
)
from .db_func import (
    get_latest_job,
    get_stage_state,
)
from .api_func import get_stage_log_path
from .shared_func import (
    get_allow_pipeline_cancel,
    get_catalog_name,
)
from ..vars.build_stream_vars import (
    STAGE_POLL_INTERVAL,
    STAGE_POLL_TIMEOUT,
    STAGE_STATE_COMPLETED,
    STAGE_STATE_FAILED,
    STAGE_STATE_IN_PROGRESS,
    STAGE_STATE_PENDING,
)
from ..messages.build_stream_msgs import (
    PIPELINE_MSGS,
    STAGE_POLL_MSGS,
)


def get_catalog_content(host) -> Dict[str, Any]:
    """
    Load the catalog content with unique identifier for each run.

    Reads catalog_name from omnia_test_config.yml to select which catalog
    file to use from /omnia/examples/catalog/ inside the omnia_core container.

    The identifier is set to 'image-build-<datetime>' format to ensure
    each pipeline run creates unique artifacts.

    Args:
        host: Testinfra host object.

    Returns:
        Dict with 'success', 'content', 'catalog_file', 'error' keys.
    """
    import json
    import datetime

    from ..vars.build_stream_vars import OMNIA_CATALOG_PATH

    result = {
        "success": False,
        "content": "",
        "catalog_file": "",
        "error": "",
    }

    catalog_filename = get_catalog_name(host)
    catalog_file = f"{OMNIA_CATALOG_PATH}/{catalog_filename}"
    result["catalog_file"] = catalog_file

    check_cmd = host.run(f"podman exec omnia_core test -f {catalog_file}")
    if check_cmd.rc != 0:
        result["error"] = f"Catalog file not found: {catalog_file}"
        return result

    cmd = host.run(f"podman exec omnia_core cat {catalog_file}")
    if cmd.rc != 0:
        result["error"] = f"Failed to read catalog file: {cmd.stderr}"
        return result

    content = cmd.stdout

    try:
        catalog = json.loads(content)
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        catalog["Catalog"]["Identifier"] = f"image-build-{timestamp}"
        result["content"] = json.dumps(catalog, indent=2)
        result["success"] = True
    except (json.JSONDecodeError, KeyError) as e:
        result["error"] = f"Failed to parse catalog JSON: {e}"

    return result


def trigger_build_pipeline(host, log_callback=None) -> Dict[str, Any]:
    """
    Trigger a build pipeline by uploading the catalog file.

    Checks for running AND pending pipelines first. If allow_pipeline_cancel
    is true in omnia_test_config.yml, auto-cancels them.

    Args:
        host: Testinfra host object
        log_callback: Optional callback function for logging

    Returns:
        Dict with 'success', 'pipeline_id', 'job_id', 'details', 'error'.
    """
    result = {
        "success": False,
        "pipeline_id": 0,
        "job_id": "",
        "details": "",
        "error": "",
        "running_pipelines": [],
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    | {msg}", flush=True)
        sys.stdout.flush()

    _log(PIPELINE_MSGS["checking_pipelines"])
    pipelines_before = list_pipelines(host, per_page=10)
    if not pipelines_before["success"]:
        result["error"] = f"Failed to list pipelines: {pipelines_before['error']}"
        return result

    running_pipelines = [
        p for p in pipelines_before["pipelines"]
        if p.get("status") in ("running", "pending", "created", "waiting_for_resource")
    ]

    if running_pipelines:
        result["running_pipelines"] = running_pipelines
        allow_cancel = get_allow_pipeline_cancel(host)

        if allow_cancel:
            _log(f"Found {len(running_pipelines)} running/pending pipeline(s). Auto-canceling...")
            for p in running_pipelines:
                _log(f"  Canceling pipeline #{p['id']} (status: {p['status']})...")
                cancel_result = cancel_pipeline(host, p['id'])
                if cancel_result["success"]:
                    _log(f"  Pipeline #{p['id']} canceled")
                else:
                    _log(f"  Failed to cancel pipeline #{p['id']}: {cancel_result['error']}")
            _log("Waiting 5 seconds for pipelines to cancel...")
            time.sleep(5)
        else:
            pipeline_ids = [str(p['id']) for p in running_pipelines]
            _log(f"WARNING: Found {len(running_pipelines)} running/pending pipeline(s):")
            for p in running_pipelines:
                _log(f"  - Pipeline #{p['id']}: {p['status']} (created: {p.get('created_at', 'N/A')})")
            _log("")
            _log("Please cancel these pipelines in GitLab before triggering a new one:")
            _log("  1. Go to GitLab > CI/CD > Pipelines")
            _log(f"  2. Cancel pipeline(s): {', '.join(pipeline_ids)}")
            _log("  3. Re-run this test")
            _log("")
            _log("Or set 'allow_pipeline_cancel: true' in omnia_test_config.yml to auto-cancel.")
            result["error"] = f"Pipeline(s) {', '.join(pipeline_ids)} are running/pending. Please cancel them first."
            return result

    initial_pipeline_id = 0
    if pipelines_before["pipelines"]:
        initial_pipeline_id = pipelines_before["pipelines"][0].get("id", 0)
    _log(PIPELINE_MSGS["no_running_pipelines"].format(id=initial_pipeline_id))

    old_job_result = get_latest_job(host)
    old_job_id = old_job_result.get("job_id", "") if old_job_result["success"] else ""
    old_job_state = old_job_result.get("job_state", "") if old_job_result["success"] else ""
    if old_job_id:
        _log(f"Current latest job: {old_job_id[:8]}... (state: {old_job_state})")

    catalog_result = get_catalog_content(host)
    if not catalog_result["success"]:
        result["error"] = (
            f"Failed to load catalog: {catalog_result['error']}. "
            f"Check catalog_name in omnia_test_config.yml."
        )
        return result

    _log(f"Using catalog: {catalog_result['catalog_file']}")
    _log(PIPELINE_MSGS["uploading_catalog"])
    upload_result = upload_catalog_file(host, catalog_result["content"])
    if not upload_result["success"]:
        result["error"] = f"Failed to upload catalog: {upload_result['error']}"
        return result
    _log(PIPELINE_MSGS["catalog_uploaded"])

    _log(PIPELINE_MSGS["waiting_pipeline"])
    wait_result = wait_for_pipeline_triggered(host, initial_pipeline_id, log_callback=_log)
    if not wait_result["success"]:
        result["error"] = wait_result["error"]
        return result

    result["pipeline_id"] = wait_result["pipeline_id"]
    _log(PIPELINE_MSGS["pipeline_triggered"].format(
        id=wait_result['pipeline_id'], status=wait_result['status']
    ))

    result["details"] = (
        f"Pipeline {wait_result['pipeline_id']} triggered "
        f"(status: {wait_result['status']}, elapsed: {wait_result['elapsed']}s)"
    )

    _log(PIPELINE_MSGS["waiting_job_db"])
    job_poll_timeout = 120
    job_poll_interval = 10
    job_start_time = time.time()

    while time.time() - job_start_time < job_poll_timeout:
        elapsed = int(time.time() - job_start_time)
        job_result = get_latest_job(host)
        if job_result["success"] and job_result["job_id"]:
            new_job_id = job_result["job_id"]
            new_job_state = job_result.get("job_state", "")
            if new_job_id != old_job_id:
                result["job_id"] = new_job_id
                result["details"] += f"\nJob ID: {new_job_id} (state: {new_job_state})"
                _log(PIPELINE_MSGS["job_created"].format(
                    job_id=new_job_id, state=new_job_state
                ))
                break
            else:
                _log(
                    f"[{elapsed}s] Waiting for NEW job in DB "
                    f"(current: {old_job_id[:8]}..., state: {old_job_state})..."
                )
        else:
            _log(f"[{elapsed}s] Waiting for job in DB...")
        time.sleep(job_poll_interval)

    if not result["job_id"]:
        _log(PIPELINE_MSGS["job_not_found"])

    result["success"] = True
    return result


def wait_for_stage_completion(
    host,
    job_id: str,
    stage_name: str,
    timeout: int = None,
    poll_interval: int = None,
    log_callback=None,
) -> Dict[str, Any]:
    """
    Poll a stage until it completes or fails.

    Args:
        host: Testinfra host object
        job_id: UUID of the job
        stage_name: Name of the stage to monitor
        timeout: Max seconds to wait (default: STAGE_POLL_TIMEOUT)
        poll_interval: Seconds between polls (default: STAGE_POLL_INTERVAL)
        log_callback: Optional callback for logging

    Returns:
        Dict with 'success', 'stage_state', 'elapsed', 'error', 'log_path'.
    """
    if timeout is None:
        timeout = STAGE_POLL_TIMEOUT
    if poll_interval is None:
        poll_interval = STAGE_POLL_INTERVAL

    result = {
        "success": False,
        "stage_state": "",
        "elapsed": 0,
        "error": "",
        "log_path": "",
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)

    timeout_min = timeout // 60
    _log(STAGE_POLL_MSGS["polling_start"].format(
        stage=stage_name, interval=poll_interval, timeout=timeout_min
    ))

    start_time = time.time()
    last_state = ""

    while time.time() - start_time < timeout:
        elapsed = int(time.time() - start_time)
        elapsed_str = f"{elapsed // 60}m{elapsed % 60:02d}s"

        stage_result = get_stage_state(host, job_id, stage_name)

        if not stage_result["success"]:
            _log(STAGE_POLL_MSGS["stage_not_created"].format(
                time=elapsed_str, stage=stage_name
            ))
            time.sleep(poll_interval)
            continue

        current_state = stage_result["stage_state"]

        if current_state != last_state:
            _log(STAGE_POLL_MSGS["stage_state_change"].format(
                time=elapsed_str, stage=stage_name, state=current_state
            ))
            last_state = current_state

        if current_state == STAGE_STATE_COMPLETED:
            result["success"] = True
            result["stage_state"] = current_state
            result["elapsed"] = elapsed
            _log(STAGE_POLL_MSGS["stage_completed"].format(
                time=elapsed_str, stage=stage_name
            ))
            return result

        if current_state == STAGE_STATE_FAILED:
            result["stage_state"] = current_state
            result["elapsed"] = elapsed
            error_msg = stage_result.get("error_code", "")
            result["error"] = error_msg or f"Stage '{stage_name}' failed"
            _log(STAGE_POLL_MSGS["stage_failed"].format(
                time=elapsed_str, stage=stage_name
            ))
            if error_msg:
                _log(STAGE_POLL_MSGS["stage_error"].format(error=error_msg))

            log_path = get_stage_log_path(host, job_id, stage_name)
            if log_path:
                result["log_path"] = log_path
                _log(f"  Log file: {log_path}")

            return result

        if current_state in (STAGE_STATE_IN_PROGRESS, STAGE_STATE_PENDING):
            if elapsed % (poll_interval * 4) < poll_interval:
                _log(STAGE_POLL_MSGS["stage_still_running"].format(
                    time=elapsed_str, stage=stage_name, state=current_state
                ))

        time.sleep(poll_interval)

    elapsed = int(time.time() - start_time)
    elapsed_str = f"{elapsed // 60}m{elapsed % 60:02d}s"
    result["stage_state"] = last_state
    result["elapsed"] = elapsed
    result["error"] = f"Stage '{stage_name}' did not complete within {timeout_min} minutes"
    _log(STAGE_POLL_MSGS["stage_timeout"].format(
        time=elapsed_str, stage=stage_name
    ))
    return result
