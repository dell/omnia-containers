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
Build Stream Pipeline Functions.

Functions for triggering and monitoring build_stream pipelines.
"""

import os
import sys
import time
from typing import Dict, Any, List

from .gitlab_func import (
    list_pipelines,
    upload_catalog_file,
    wait_for_pipeline_triggered,
    cancel_pipeline,
    get_child_pipeline_id,
    get_pipeline_jobs_by_stage,
    play_manual_job,
    trigger_pipeline_with_variables,
)
from .db_func import (
    get_latest_job,
    get_stage_state,
    get_all_image_groups,
)
from .shared_func import get_allow_pipeline_cancel, get_cleanup_image_identifier
from ..vars.build_stream_vars import (
    STAGE_POLL_INTERVAL,
    STAGE_POLL_TIMEOUT,
    STAGE_STATE_COMPLETED,
    STAGE_STATE_FAILED,
    STAGE_STATE_RUNNING,
    STAGE_STATE_PENDING,
)
from ..messages.build_stream_msgs import (
    PIPELINE_MSGS,
    STAGE_POLL_MSGS,
)


def get_catalog_content() -> str:
    """
    Load the catalog content with unique identifier for each run.

    The identifier is set to 'image-build-<datetime>' format to ensure
    each pipeline run creates a unique image group and avoids
    DuplicateImageGroupError.

    Returns:
        Catalog JSON content as string with unique identifier.
    """
    import json
    import datetime

    catalog_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "catalogs"
    )
    catalog_file = os.path.join(catalog_dir, "slurm_only_x86_64_catalog.json")

    if not os.path.exists(catalog_file):
        return ""

    with open(catalog_file, "r") as f:
        content = f.read()

    try:
        catalog = json.loads(content)
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        catalog["Catalog"]["Identifier"] = f"image-build-{timestamp}"
        return json.dumps(catalog, indent=2)
    except (json.JSONDecodeError, KeyError):
        return content


def trigger_build_pipeline(host, log_callback=None) -> Dict[str, Any]:
    """
    Trigger a build pipeline by uploading the catalog file.

    Checks for running AND pending pipelines first. If allow_pipeline_cancel
    is true in omnia_test_config.yml, auto-cancels them. Otherwise asks user
    to cancel manually.

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
            print(f"    │ {msg}", flush=True)
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
                    _log(f"  ✓ Pipeline #{p['id']} canceled")
                else:
                    _log(f"  ✗ Failed to cancel pipeline #{p['id']}: {cancel_result['error']}")
            _log("Waiting 5 seconds for pipelines to cancel...")
            time.sleep(5)
        else:
            pipeline_ids = [str(p['id']) for p in running_pipelines]
            _log(f"⚠ WARNING: Found {len(running_pipelines)} running/pending pipeline(s):")
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

    catalog_content = get_catalog_content()
    if not catalog_content:
        result["error"] = "Failed to load catalog file from automation library"
        return result

    _log(PIPELINE_MSGS["uploading_catalog"])
    upload_result = upload_catalog_file(host, catalog_content)
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


def trigger_deploy_pipeline(host, log_callback=None) -> Dict[str, Any]:
    """
    Trigger a deploy pipeline by committing the PXE mapping file.

    Checks for running AND pending pipelines first. If allow_pipeline_cancel
    is true in omnia_test_config.yml, auto-cancels them. Otherwise asks user
    to cancel manually.

    Args:
        host: Testinfra host object
        log_callback: Optional callback function for logging

    Returns:
        Dict with 'success', 'pipeline_id', 'job_id', 'details', 'error'.
    """
    from .gitlab_func import commit_pxe_mapping_file

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
            print(f"    │ {msg}", flush=True)
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
                    _log(f"  ✓ Pipeline #{p['id']} canceled")
                else:
                    _log(f"  ✗ Failed to cancel pipeline #{p['id']}: {cancel_result['error']}")
            _log("Waiting 5 seconds for pipelines to cancel...")
            time.sleep(5)
        else:
            pipeline_ids = [str(p['id']) for p in running_pipelines]
            _log(f"⚠ WARNING: Found {len(running_pipelines)} running/pending pipeline(s):")
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

    _log("Committing PXE mapping file to GitLab...")
    commit_result = commit_pxe_mapping_file(host)
    if not commit_result["success"]:
        result["error"] = f"Failed to commit PXE mapping: {commit_result['error']}"
        return result
    _log("PXE mapping file committed successfully")

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
        f"Deploy pipeline {wait_result['pipeline_id']} triggered "
        f"(status: {wait_result['status']}, elapsed: {wait_result['elapsed']}s)"
    )

    result["job_id"] = old_job_id if old_job_id else ""
    result["success"] = True
    return result


def select_image_for_deploy(host, pipeline_id: int, log_callback=None) -> Dict[str, Any]:
    """
    Auto-select the latest BUILT image group for deployment.

    The deploy pipeline creates manual selection jobs for each image group.
    This function finds the latest BUILT image group and plays its selection job.

    Args:
        host: Testinfra host object
        pipeline_id: Parent deploy pipeline ID
        log_callback: Optional callback function for logging

    Returns:
        Dict with 'success', 'image_group_id', 'job_id', 'error'.
    """
    result = {
        "success": False,
        "image_group_id": "",
        "gitlab_job_id": 0,
        "error": "",
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    _log("Getting latest BUILT image group from database...")
    ig_result = get_all_image_groups(host)
    if not ig_result["success"]:
        result["error"] = f"Failed to get image groups: {ig_result['error']}"
        return result

    built_groups = [g for g in ig_result["image_groups"] if g["status"] == "BUILT"]
    if not built_groups:
        result["error"] = "No BUILT image groups found. Run build pipeline first."
        return result

    latest_group = sorted(built_groups, key=lambda x: x.get("created_at", ""), reverse=True)[0]
    image_group_id = latest_group.get("id", "")
    _log(f"Latest BUILT image group: {image_group_id}")
    result["image_group_id"] = image_group_id

    _log(f"Getting child pipeline from parent pipeline #{pipeline_id}...")
    child_result = get_child_pipeline_id(host, pipeline_id)
    if not child_result["success"]:
        result["error"] = f"Failed to get child pipeline: {child_result['error']}"
        return result

    child_pipeline_id = child_result["child_pipeline_id"]
    _log(f"Child pipeline ID: {child_pipeline_id}")

    _log("Waiting for grandchild pipeline with selection jobs...")
    max_wait = 300  # 5 minutes - child pipeline needs time to run list_images and trigger grandchild
    poll_interval = 10
    start_time = time.time()
    target_pipeline_id = child_pipeline_id

    while time.time() - start_time < max_wait:
        jobs_result = get_pipeline_jobs_by_stage(host, target_pipeline_id, stage="select_image")
        if jobs_result["success"] and jobs_result["jobs"]:
            _log(f"Found {len(jobs_result['jobs'])} selection job(s) in pipeline #{target_pipeline_id}")
            break

        grandchild_result = get_child_pipeline_id(host, target_pipeline_id)
        if grandchild_result["success"] and grandchild_result["child_pipeline_id"]:
            grandchild_id = grandchild_result["child_pipeline_id"]
            if grandchild_id != target_pipeline_id:
                _log(f"Found grandchild pipeline: {grandchild_id}")
                target_pipeline_id = grandchild_id
                continue

        elapsed = int(time.time() - start_time)
        _log(f"[{elapsed}s] Waiting for selection jobs...")
        time.sleep(poll_interval)
    else:
        result["error"] = "Timeout waiting for selection jobs (5 min)"
        return result

    target_job = None
    _log(f"Looking for job matching image group: {image_group_id}")
    for job in jobs_result["jobs"]:
        job_name = job.get("name", "")
        if job_name == image_group_id:
            target_job = job
            _log(f"Found exact match: {job_name}")
            break

    if not target_job:
        _log(f"Available selection jobs: {[j.get('name') for j in jobs_result['jobs']]}")
        for job in jobs_result["jobs"]:
            if job.get("status") == "manual":
                target_job = job
                _log(f"Using first manual job: {job.get('name')}")
                break
        if not target_job:
            target_job = jobs_result["jobs"][0]
            _log(f"Using first available job: {target_job.get('name')}")

    gitlab_job_id = target_job.get("id")
    job_name = target_job.get("name", "")
    job_status = target_job.get("status", "")

    _log(f"Playing selection job: {job_name} (ID: {gitlab_job_id}, status: {job_status})")

    if job_status == "manual":
        play_result = play_manual_job(host, gitlab_job_id)
        if not play_result["success"]:
            result["error"] = f"Failed to play job: {play_result['error']}"
            return result
        _log(f"Selection job triggered: {play_result['status']}")
    else:
        _log(f"Job already in status: {job_status}")

    result["gitlab_job_id"] = gitlab_job_id
    result["success"] = True
    return result


def trigger_cleanup_pipeline(host, log_callback=None) -> Dict[str, Any]:
    """
    Trigger a cleanup pipeline using PIPELINE_TYPE=cleanup variable.

    Checks for running AND pending pipelines first. If allow_pipeline_cancel
    is true in omnia_test_config.yml, auto-cancels them.

    Args:
        host: Testinfra host object
        log_callback: Optional callback function for logging

    Returns:
        Dict with 'success', 'pipeline_id', 'details', 'error'.
    """
    result = {
        "success": False,
        "pipeline_id": 0,
        "details": "",
        "error": "",
        "running_pipelines": [],
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)
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
                    _log(f"  ✓ Pipeline #{p['id']} canceled")
                else:
                    _log(f"  ✗ Failed to cancel pipeline #{p['id']}: {cancel_result['error']}")
            _log("Waiting 5 seconds for pipelines to cancel...")
            time.sleep(5)
        else:
            pipeline_ids = [str(p['id']) for p in running_pipelines]
            _log(f"⚠ WARNING: Found {len(running_pipelines)} running/pending pipeline(s):")
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

    initial_id = pipelines_before["pipelines"][0].get("id", 0) if pipelines_before["pipelines"] else 0
    _log(PIPELINE_MSGS["no_running_pipelines"].format(id=initial_id))

    _log("Checking for BUILT image groups to clean...")
    ig_result = get_all_image_groups(host)
    if not ig_result["success"]:
        result["error"] = f"Failed to get image groups: {ig_result['error']}"
        return result

    built_groups = [g for g in ig_result["image_groups"] if g["status"] == "BUILT"]
    if not built_groups:
        result["error"] = "No BUILT image groups found. Nothing to clean."
        return result

    _log(f"Found {len(built_groups)} BUILT image group(s) to clean")

    _log("Triggering cleanup pipeline with PIPELINE_TYPE=cleanup...")
    trigger_result = trigger_pipeline_with_variables(host, {"PIPELINE_TYPE": "cleanup"})
    if not trigger_result["success"]:
        result["error"] = f"Failed to trigger cleanup pipeline: {trigger_result['error']}"
        return result

    result["pipeline_id"] = trigger_result["pipeline_id"]
    _log(f"Cleanup pipeline #{trigger_result['pipeline_id']} triggered (status: {trigger_result['status']})")

    result["details"] = (
        f"Cleanup pipeline {trigger_result['pipeline_id']} triggered "
        f"(status: {trigger_result['status']})"
    )

    result["success"] = True
    return result


def select_image_for_cleanup(host, pipeline_id: int, log_callback=None) -> Dict[str, Any]:
    """
    Select an image group for cleanup.

    If cleanup_image_identifier is set in omnia_test_config.yml, uses that.
    Otherwise, auto-selects the latest BUILT image group.

    The cleanup pipeline creates manual selection jobs for each image group.
    This function finds the target image group and plays its selection job.

    Args:
        host: Testinfra host object
        pipeline_id: Parent cleanup pipeline ID
        log_callback: Optional callback function for logging

    Returns:
        Dict with 'success', 'image_group_id', 'gitlab_job_id', 'error'.
    """
    result = {
        "success": False,
        "image_group_id": "",
        "gitlab_job_id": 0,
        "error": "",
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    # Check if specific image identifier is configured
    configured_id = get_cleanup_image_identifier(host)
    if configured_id:
        _log(f"Using configured cleanup_image_identifier: {configured_id}")
        image_group_id = configured_id
    else:
        _log("Getting latest BUILT image group from database...")
        ig_result = get_all_image_groups(host)
        if not ig_result["success"]:
            result["error"] = f"Failed to get image groups: {ig_result['error']}"
            return result

        built_groups = [g for g in ig_result["image_groups"] if g["status"] == "BUILT"]
        if not built_groups:
            result["error"] = "No BUILT image groups found. Nothing to clean."
            return result

        latest_group = sorted(
            built_groups, key=lambda x: x.get("created_at", ""), reverse=True
        )[0]
        image_group_id = latest_group.get("id", "")
        _log(f"Auto-selected latest BUILT image group: {image_group_id}")

    result["image_group_id"] = image_group_id

    _log(f"Getting child pipeline from parent pipeline #{pipeline_id}...")
    child_result = get_child_pipeline_id(host, pipeline_id)
    if not child_result["success"]:
        result["error"] = f"Failed to get child pipeline: {child_result['error']}"
        return result

    child_pipeline_id = child_result["child_pipeline_id"]
    _log(f"Child pipeline ID: {child_pipeline_id}")

    _log("Waiting for grandchild pipeline with selection jobs...")
    max_wait = 300  # 5 minutes - child pipeline needs time to run list_images and trigger grandchild
    poll_interval = 10
    start_time = time.time()
    target_pipeline_id = child_pipeline_id

    while time.time() - start_time < max_wait:
        jobs_result = get_pipeline_jobs_by_stage(host, target_pipeline_id, stage="select_image")
        if jobs_result["success"] and jobs_result["jobs"]:
            _log(f"Found {len(jobs_result['jobs'])} selection job(s) in pipeline #{target_pipeline_id}")
            break

        grandchild_result = get_child_pipeline_id(host, target_pipeline_id)
        if grandchild_result["success"] and grandchild_result["child_pipeline_id"]:
            grandchild_id = grandchild_result["child_pipeline_id"]
            if grandchild_id != target_pipeline_id:
                _log(f"Found grandchild pipeline: {grandchild_id}")
                target_pipeline_id = grandchild_id
                continue

        elapsed = int(time.time() - start_time)
        _log(f"[{elapsed}s] Waiting for selection jobs...")
        time.sleep(poll_interval)
    else:
        result["error"] = "Timeout waiting for selection jobs (5 min)"
        return result

    target_job = None
    _log(f"Looking for job matching image group: {image_group_id}")
    for job in jobs_result["jobs"]:
        job_name = job.get("name", "")
        if job_name == image_group_id:
            target_job = job
            _log(f"Found exact match: {job_name}")
            break

    if not target_job:
        _log(f"Available selection jobs: {[j.get('name') for j in jobs_result['jobs']]}")
        for job in jobs_result["jobs"]:
            if job.get("status") == "manual":
                target_job = job
                _log(f"Using first manual job: {job.get('name')}")
                break
        if not target_job:
            target_job = jobs_result["jobs"][0]
            _log(f"Using first available job: {target_job.get('name')}")

    gitlab_job_id = target_job.get("id")
    job_name = target_job.get("name", "")
    job_status = target_job.get("status", "")

    _log(f"Playing selection job: {job_name} (ID: {gitlab_job_id}, status: {job_status})")

    if job_status == "manual":
        play_result = play_manual_job(host, gitlab_job_id)
        if not play_result["success"]:
            result["error"] = f"Failed to play job: {play_result['error']}"
            return result
        _log(f"Selection job triggered: {play_result['status']}")
    else:
        _log(f"Job already in status: {job_status}")

    result["gitlab_job_id"] = gitlab_job_id
    result["success"] = True
    return result


def wait_for_cleanup_completion(host, image_group_id: str, timeout: int = 300, log_callback=None) -> Dict[str, Any]:
    """
    Wait for cleanup to complete and verify image group status changed to CLEANED.

    Args:
        host: Testinfra host object
        image_group_id: Image group ID being cleaned
        timeout: Maximum time to wait in seconds
        log_callback: Optional callback function for logging

    Returns:
        Dict with 'success', 'image_group_id', 'status', 'error'.
    """
    result = {
        "success": False,
        "image_group_id": image_group_id,
        "status": "",
        "error": "",
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    _log(f"Waiting for image group {image_group_id} to be CLEANED...")
    poll_interval = 10
    start_time = time.time()

    while time.time() - start_time < timeout:
        elapsed = int(time.time() - start_time)
        ig_result = get_all_image_groups(host)
        if ig_result["success"]:
            for ig in ig_result["image_groups"]:
                if ig.get("id") == image_group_id:
                    status = ig.get("status", "")
                    result["status"] = status
                    if status == "CLEANED":
                        _log(f"[{elapsed}s] Image group {image_group_id} is now CLEANED ✓")
                        result["success"] = True
                        return result
                    else:
                        _log(f"[{elapsed}s] Image group status: {status}")
                    break
        time.sleep(poll_interval)

    result["error"] = f"Timeout waiting for image group to be CLEANED (last status: {result['status']})"
    return result


def wait_for_stage_completion(
    host,
    job_id: str,
    stage_name: str,
    timeout: int = STAGE_POLL_TIMEOUT,
    poll_interval: int = STAGE_POLL_INTERVAL,
    log_callback=None,
) -> Dict[str, Any]:
    """
    Wait for a specific stage to complete (COMPLETED or FAILED).

    Prints real-time status updates during polling.

    Args:
        host: Testinfra host object
        job_id: UUID of the job
        stage_name: Name of the stage to monitor
        timeout: Maximum time to wait in seconds (default 2 hours)
        poll_interval: Time between checks in seconds (default 30s)
        log_callback: Optional callback function for logging (receives message string)

    Returns:
        Dict with 'success', 'stage_name', 'stage_state', 'elapsed', 'error'.
    """
    result = {
        "success": False,
        "stage_name": stage_name,
        "stage_state": "",
        "elapsed": 0,
        "error": "",
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    def _format_time(seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}m {secs}s"

    start_time = time.time()
    last_state = ""
    poll_count = 0
    last_pipeline_status = ""

    _log(STAGE_POLL_MSGS["polling_start"].format(
        stage=stage_name, interval=poll_interval, timeout=timeout // 60
    ))

    while time.time() - start_time < timeout:
        poll_count += 1
        elapsed = int(time.time() - start_time)
        time_str = _format_time(elapsed)

        stage_result = get_stage_state(host, job_id, stage_name)

        if not stage_result["success"]:
            if "not found" in stage_result["error"].lower():
                _log(STAGE_POLL_MSGS["stage_not_created"].format(
                    time=time_str, stage=stage_name
                ))
                pipelines_result = list_pipelines(host, per_page=1)
                if pipelines_result["success"] and pipelines_result["pipelines"]:
                    pipeline = pipelines_result["pipelines"][0]
                    pipeline_status = pipeline.get("status", "unknown")
                    if pipeline_status == "failed":
                        result["error"] = f"Pipeline #{pipeline['id']} failed. Stage '{stage_name}' was never created."
                        _log(STAGE_POLL_MSGS["pipeline_failed"])
                        return result
                    if pipeline_status == "canceled":
                        result["error"] = f"Pipeline #{pipeline['id']} was canceled."
                        _log(STAGE_POLL_MSGS["pipeline_canceled"])
                        return result
                time.sleep(poll_interval)
                continue
            result["error"] = stage_result["error"]
            return result

        current_state = stage_result["stage_state"]
        result["stage_state"] = current_state

        if current_state != last_state:
            _log(STAGE_POLL_MSGS["stage_state_change"].format(
                time=time_str, stage=stage_name, state=current_state
            ))
            last_state = current_state

        if current_state == STAGE_STATE_COMPLETED:
            result["success"] = True
            result["elapsed"] = elapsed
            _log(STAGE_POLL_MSGS["stage_completed"].format(time=time_str, stage=stage_name))
            return result

        if current_state == STAGE_STATE_FAILED:
            result["elapsed"] = elapsed
            error_code = stage_result.get("error_code", "")
            result["error"] = (
                f"Stage '{stage_name}' failed"
                + (f": {error_code}" if error_code else "")
            )
            _log(STAGE_POLL_MSGS["stage_failed"].format(time=time_str, stage=stage_name))
            if error_code:
                _log(STAGE_POLL_MSGS["stage_error"].format(error=error_code))
            return result

        if current_state in (STAGE_STATE_RUNNING, "IN_PROGRESS", STAGE_STATE_PENDING):
            pipelines_result = list_pipelines(host, per_page=1)
            if pipelines_result["success"] and pipelines_result["pipelines"]:
                pipeline = pipelines_result["pipelines"][0]
                pipeline_status = pipeline.get("status", "unknown")
                if pipeline_status != last_pipeline_status:
                    _log(STAGE_POLL_MSGS["pipeline_status"].format(
                        time=time_str, id=pipeline['id'], status=pipeline_status
                    ))
                    last_pipeline_status = pipeline_status
                if pipeline_status == "failed":
                    result["error"] = f"Pipeline #{pipeline['id']} failed. Check GitLab for details."
                    _log(STAGE_POLL_MSGS["pipeline_failed"])
                    return result
                if pipeline_status == "canceled":
                    result["error"] = f"Pipeline #{pipeline['id']} was canceled."
                    _log(STAGE_POLL_MSGS["pipeline_canceled"])
                    return result

            if poll_count % 2 == 0:
                _log(STAGE_POLL_MSGS["stage_still_running"].format(
                    time=time_str, stage=stage_name, state=current_state.lower()
                ))

        time.sleep(poll_interval)

    result["elapsed"] = int(time.time() - start_time)
    result["error"] = (
        f"Stage '{stage_name}' did not complete within {timeout // 60} minutes "
        f"(last state: {last_state})"
    )
    _log(STAGE_POLL_MSGS["stage_timeout"].format(
        time=_format_time(result['elapsed']), stage=stage_name
    ))
    return result


def get_pipeline_stage_status(host, job_id: str, stage_name: str) -> Dict[str, Any]:
    """
    Get the current status of a pipeline stage.

    Args:
        host: Testinfra host object
        job_id: UUID of the job
        stage_name: Name of the stage

    Returns:
        Dict with 'success', 'stage_name', 'stage_state', 'is_running',
        'is_completed', 'is_failed', 'error'.
    """
    result = {
        "success": False,
        "stage_name": stage_name,
        "stage_state": "",
        "is_running": False,
        "is_completed": False,
        "is_failed": False,
        "is_pending": False,
        "error": "",
    }

    stage_result = get_stage_state(host, job_id, stage_name)
    if not stage_result["success"]:
        result["error"] = stage_result["error"]
        return result

    state = stage_result["stage_state"]
    result["stage_state"] = state
    result["success"] = True
    result["is_running"] = state == STAGE_STATE_RUNNING
    result["is_completed"] = state == STAGE_STATE_COMPLETED
    result["is_failed"] = state == STAGE_STATE_FAILED
    result["is_pending"] = state == STAGE_STATE_PENDING

    return result


def monitor_pipeline_stages(
    host,
    job_id: str,
    stages: List[str],
    timeout_per_stage: int = STAGE_POLL_TIMEOUT,
    poll_interval: int = STAGE_POLL_INTERVAL,
) -> Dict[str, Any]:
    """
    Monitor multiple pipeline stages sequentially.

    Args:
        host: Testinfra host object
        job_id: UUID of the job
        stages: List of stage names to monitor
        timeout_per_stage: Maximum time to wait per stage
        poll_interval: Time between checks

    Returns:
        Dict with 'success', 'completed_stages', 'failed_stage', 'results', 'error'.
    """
    result = {
        "success": False,
        "completed_stages": [],
        "failed_stage": "",
        "results": [],
        "error": "",
    }

    for stage_name in stages:
        stage_result = wait_for_stage_completion(
            host, job_id, stage_name, timeout_per_stage, poll_interval
        )

        result["results"].append({
            "stage_name": stage_name,
            "stage_state": stage_result["stage_state"],
            "elapsed": stage_result["elapsed"],
            "success": stage_result["success"],
            "error": stage_result.get("error", ""),
        })

        if stage_result["success"]:
            result["completed_stages"].append(stage_name)
        else:
            result["failed_stage"] = stage_name
            result["error"] = stage_result["error"]
            return result

    result["success"] = True
    return result
