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
Build Stream - Manual Pipeline Trigger Tests.

Tests for manually triggering pipelines using PIPELINE_TYPE variable:
  - Build: PIPELINE_TYPE=build
  - Deploy: PIPELINE_TYPE=deploy

These tests verify that pipelines can be triggered via API with variables,
then monitor stages, select images manually, and verify database updates.

Markers:
    - sanity: Basic sanity tests
    - build_stream: Build stream module tests
    - manual: Manual pipeline trigger tests
"""

import sys
import time

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    trigger_pipeline_with_variables,
    wait_for_stage_completion,
    get_stage_log_path,
    get_catalog_roles,
    get_image_groups_for_job,
    get_images_for_job,
    get_all_image_groups,
    verify_registry_images,
    verify_s3_boot_images,
    list_pipelines,
    get_pipeline_status,
    cancel_pipeline,
    select_image_for_deploy,
    get_allow_pipeline_cancel,
    get_latest_job,
    BUILD_PIPELINE_CORE_STAGES,
    BUILD_IMAGE_STAGE_PREFIX,
    STAGE_POLL_INTERVAL,
    STAGE_POLL_TIMEOUT,
    SKIP_MSGS,
)


# =============================================================================
# MODULE-LEVEL STATE
# =============================================================================

_manual_state = {
    "build_job_id": None,
    "build_pipeline_id": None,
    "build_triggered": False,
    "build_completed": False,
    "deploy_pipeline_id": None,
    "deploy_triggered": False,
    "deploy_completed": False,
    "catalog_roles": [],
    "catalog_architectures": [],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _handle_running_pipelines(host, log_callback=None):
    """Check for running pipelines and handle based on config."""
    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)

    result = list_pipelines(host, per_page=10)
    if not result["success"]:
        return False, f"Failed to list pipelines: {result['error']}"

    running = [
        p for p in result["pipelines"]
        if p.get("status") in ("running", "pending", "created", "waiting_for_resource")
    ]

    if not running:
        return True, ""

    allow_cancel = get_allow_pipeline_cancel(host)
    if allow_cancel:
        _log(f"Found {len(running)} running pipeline(s). Auto-canceling...")
        for p in running:
            cancel_result = cancel_pipeline(host, p["id"])
            if cancel_result["success"]:
                _log(f"  ✓ Canceled pipeline #{p['id']}")
            else:
                _log(f"  ✗ Failed to cancel #{p['id']}: {cancel_result['error']}")
        time.sleep(5)
        return True, ""
    else:
        pipeline_ids = [str(p["id"]) for p in running]
        return False, (
            f"Pipeline(s) {', '.join(pipeline_ids)} are running. "
            "Set allow_pipeline_cancel=true or cancel manually."
        )


def _wait_for_pipeline_completion(host, pipeline_id, log_callback=None, timeout=7200):
    """Wait for a pipeline to complete."""
    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)

    start_time = time.time()
    poll_interval = 30
    completed_statuses = ("success", "failed", "canceled", "skipped")

    while time.time() - start_time < timeout:
        result = get_pipeline_status(host, pipeline_id)
        if not result["success"]:
            _log(f"Warning: Failed to get status: {result['error']}")
            time.sleep(poll_interval)
            continue

        status = result.get("status", "unknown")
        if status in completed_statuses:
            _log(f"Pipeline #{pipeline_id} completed: {status}")
            return status == "success"

        elapsed = int(time.time() - start_time)
        _log(f"[{elapsed}s] Pipeline #{pipeline_id}: {status}")
        time.sleep(poll_interval)

    return False


# =============================================================================
# TEST 1: MANUAL BUILD PIPELINE TRIGGER
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.manual
@pytest.mark.order(30)
def test_manual_build_trigger(host):
    """
    Test 1: Trigger build pipeline using PIPELINE_TYPE=build variable.

    This tests manual pipeline triggering via GitLab API.
    """
    log = TestLogger("Manual Build Trigger")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    log.check("Triggering build pipeline with PIPELINE_TYPE=build")

    # Handle running pipelines
    ok, error = _handle_running_pipelines(host, log_callback=_log_callback)
    if not ok:
        log.failed("Cannot trigger pipeline", error)
        pytest.fail(error)

    # Get current latest job for comparison
    old_job = get_latest_job(host)
    old_job_id = old_job.get("job_id", "") if old_job["success"] else ""

    # Trigger pipeline with PIPELINE_TYPE=build
    _log_callback("Triggering pipeline with PIPELINE_TYPE=build...")
    result = trigger_pipeline_with_variables(host, {"PIPELINE_TYPE": "build"})

    if not result["success"]:
        log.failed(
            f"Failed to trigger build pipeline: {result['error']}",
            "Check GitLab API access"
        )
        pytest.fail(f"Trigger failed: {result['error']}")

    _manual_state["build_pipeline_id"] = result["pipeline_id"]
    _manual_state["build_triggered"] = True

    _log_callback(f"Pipeline #{result['pipeline_id']} triggered (status: {result['status']})")

    # Wait for new job to appear in database
    _log_callback("Waiting for new job in database...")
    max_wait = 120
    start_time = time.time()
    new_job_id = None

    while time.time() - start_time < max_wait:
        job_result = get_latest_job(host)
        if job_result["success"]:
            current_job_id = job_result.get("job_id", "")
            if current_job_id and current_job_id != old_job_id:
                new_job_id = current_job_id
                _log_callback(f"New job detected: {new_job_id[:8]}...")
                break
        time.sleep(5)

    if not new_job_id:
        log.failed(
            "No new job appeared in database",
            f"Pipeline #{result['pipeline_id']} may have failed to start"
        )
        pytest.fail("No new job in database")

    _manual_state["build_job_id"] = new_job_id

    log.passed(
        f"Build pipeline #{result['pipeline_id']} triggered successfully",
        f"Job ID: {new_job_id}"
    )


# =============================================================================
# TEST 2: MONITOR BUILD STAGES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.manual
@pytest.mark.order(31)
def test_manual_build_stages(host):
    """
    Test 2: Monitor build pipeline stages until completion.
    """
    log = TestLogger("Manual Build Stages")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    if not _manual_state["build_triggered"]:
        log.skipped("Build not triggered", "Run test_manual_build_trigger first")
        pytest.skip("Build not triggered")

    job_id = _manual_state["build_job_id"]
    if not job_id:
        log.skipped("No job ID", "Build trigger may have failed")
        pytest.skip("No job ID")

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    log.check(f"Monitoring stages for job {job_id[:8]}...")

    # Monitor core stages
    core_stages = list(BUILD_PIPELINE_CORE_STAGES)
    _log_callback(f"Core stages: {core_stages}")

    for stage_name in core_stages:
        _log_callback(f"Monitoring stage: {stage_name}...")
        stage_result = wait_for_stage_completion(
            host, job_id, stage_name,
            timeout=STAGE_POLL_TIMEOUT,
            poll_interval=STAGE_POLL_INTERVAL,
            log_callback=lambda msg: print(f"      │ {msg}", flush=True),
        )
        if not stage_result["success"]:
            log_path = get_stage_log_path(host, job_id, stage_name)
            log.failed(
                f"Stage '{stage_name}' failed",
                f"Error: {stage_result.get('error', 'Unknown')}\nLog: {log_path or 'N/A'}"
            )
            pytest.fail(f"Stage '{stage_name}' failed")
        _log_callback(f"✓ Stage '{stage_name}' COMPLETED")

    # Get catalog info for build-image stages
    _log_callback("Getting catalog information...")
    roles_result = get_catalog_roles(host, job_id)
    if roles_result["success"]:
        _manual_state["catalog_roles"] = roles_result.get("roles", [])
        _manual_state["catalog_architectures"] = roles_result.get("architectures", ["x86_64"])
        _log_callback(f"Roles: {_manual_state['catalog_roles']}")
        _log_callback(f"Architectures: {_manual_state['catalog_architectures']}")

    # Monitor build-image stages
    archs = _manual_state.get("catalog_architectures", ["x86_64"])
    build_stages = [f"{BUILD_IMAGE_STAGE_PREFIX}{arch}" for arch in archs]
    _log_callback(f"Build stages: {build_stages}")

    for stage_name in build_stages:
        _log_callback(f"Monitoring stage: {stage_name}...")
        stage_result = wait_for_stage_completion(
            host, job_id, stage_name,
            timeout=STAGE_POLL_TIMEOUT,
            poll_interval=STAGE_POLL_INTERVAL,
            log_callback=lambda msg: print(f"      │ {msg}", flush=True),
        )
        if not stage_result["success"]:
            log_path = get_stage_log_path(host, job_id, stage_name)
            log.failed(
                f"Stage '{stage_name}' failed",
                f"Error: {stage_result.get('error', 'Unknown')}\nLog: {log_path or 'N/A'}"
            )
            pytest.fail(f"Stage '{stage_name}' failed")
        _log_callback(f"✓ Stage '{stage_name}' COMPLETED")

    _manual_state["build_completed"] = True

    log.passed(
        "All build stages completed successfully",
        f"Core: {len(core_stages)}, Build: {len(build_stages)}"
    )


# =============================================================================
# TEST 3: VERIFY BUILD DATABASE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.manual
@pytest.mark.order(32)
def test_manual_build_verify_db(host):
    """
    Test 3: Verify database has image_groups with BUILT status.
    """
    log = TestLogger("Manual Build Verify DB")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    if not _manual_state["build_completed"]:
        log.skipped("Build not completed", "Run previous tests first")
        pytest.skip("Build not completed")

    job_id = _manual_state["build_job_id"]

    log.check(f"Verifying database for job {job_id[:8]}...")

    # Check image_groups
    ig_result = get_image_groups_for_job(host, job_id)
    if not ig_result["success"]:
        log.failed(
            "Failed to query image_groups",
            ig_result.get("error", "Database error")
        )
        pytest.fail("Database query failed")

    built_groups = [g for g in ig_result["image_groups"] if g["status"] == "BUILT"]
    if not built_groups:
        log.failed(
            "No BUILT image groups found",
            f"Found: {[g['status'] for g in ig_result['image_groups']]}"
        )
        pytest.fail("No BUILT image groups")

    # Check images table
    images_result = get_images_for_job(host, job_id)
    if images_result["success"] and images_result["images"]:
        roles = list(set([img.get("role") for img in images_result["images"] if img.get("role")]))
        _manual_state["catalog_roles"] = roles

    log.passed(
        f"Found {len(built_groups)} BUILT image group(s)",
        f"Roles: {_manual_state.get('catalog_roles', [])}"
    )


# =============================================================================
# TEST 4: VERIFY BUILD REGISTRY AND S3
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.manual
@pytest.mark.order(33)
def test_manual_build_verify_artifacts(host):
    """
    Test 4: Verify registry images and S3 boot images exist.
    """
    log = TestLogger("Manual Build Verify Artifacts")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    if not _manual_state["build_completed"]:
        log.skipped("Build not completed", "Run previous tests first")
        pytest.skip("Build not completed")

    job_id = _manual_state["build_job_id"]
    roles = _manual_state.get("catalog_roles", [])

    if not roles:
        log.skipped("No roles available", "Cannot verify artifacts")
        pytest.skip("No roles")

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    log.check(f"Verifying artifacts for {len(roles)} role(s)")

    # Verify registry
    _log_callback("Checking registry images...")
    reg_result = verify_registry_images(host, job_id, roles, "")
    if reg_result["success"]:
        _log_callback(f"✓ Registry: {len(reg_result.get('found', []))}/{len(roles)} roles found")
        for item in reg_result.get("found", []):
            _log_callback(f"    ✓ {item['role']}: {item.get('repo', 'N/A')}")
    else:
        _log_callback(f"✗ Registry: {len(reg_result.get('found', []))}/{len(roles)} roles found")

    # Verify S3
    _log_callback("Checking S3 boot images...")
    s3_result = verify_s3_boot_images(host, job_id, roles, "")
    if s3_result["success"]:
        _log_callback(f"✓ S3: {len(s3_result.get('found_roles', []))}/{len(roles)} roles complete")
    else:
        _log_callback(f"✗ S3: {len(s3_result.get('found_roles', []))}/{len(roles)} roles complete")

    if reg_result["success"] and s3_result["success"]:
        log.passed(
            "All artifacts verified successfully",
            f"Registry: {len(reg_result.get('found', []))}, S3: {len(s3_result.get('found_roles', []))}"
        )
    else:
        log.failed(
            "Some artifacts missing",
            f"Registry OK: {reg_result['success']}, S3 OK: {s3_result['success']}"
        )
        pytest.fail("Artifact verification failed")


# =============================================================================
# TEST 5: MANUAL DEPLOY PIPELINE TRIGGER
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.manual
@pytest.mark.order(34)
def test_manual_deploy_trigger(host):
    """
    Test 5: Trigger deploy pipeline using PIPELINE_TYPE=deploy variable.
    """
    log = TestLogger("Manual Deploy Trigger")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    # Check if we have BUILT images
    built_groups = []
    ig_result = get_all_image_groups(host)
    if ig_result["success"]:
        built_groups = [g for g in ig_result["image_groups"] if g["status"] == "BUILT"]

    if not built_groups:
        log.skipped(
            "No BUILT images available",
            "Run build pipeline first"
        )
        pytest.skip("No BUILT images")

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    log.check("Triggering deploy pipeline with PIPELINE_TYPE=deploy")

    # Handle running pipelines
    ok, error = _handle_running_pipelines(host, log_callback=_log_callback)
    if not ok:
        log.failed("Cannot trigger pipeline", error)
        pytest.fail(error)

    # Trigger pipeline with PIPELINE_TYPE=deploy
    _log_callback("Triggering pipeline with PIPELINE_TYPE=deploy...")
    result = trigger_pipeline_with_variables(host, {"PIPELINE_TYPE": "deploy"})

    if not result["success"]:
        log.failed(
            f"Failed to trigger deploy pipeline: {result['error']}",
            "Check GitLab API access"
        )
        pytest.fail(f"Trigger failed: {result['error']}")

    _manual_state["deploy_pipeline_id"] = result["pipeline_id"]
    _manual_state["deploy_triggered"] = True

    _log_callback(f"Pipeline #{result['pipeline_id']} triggered (status: {result['status']})")

    log.passed(
        f"Deploy pipeline #{result['pipeline_id']} triggered successfully",
        f"Status: {result['status']}"
    )


# =============================================================================
# TEST 6: SELECT IMAGE FOR DEPLOY
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.manual
@pytest.mark.order(35)
def test_manual_deploy_select_image(host):
    """
    Test 6: Select image group for deployment (manual job selection).
    """
    log = TestLogger("Manual Deploy Select Image")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    if not _manual_state["deploy_triggered"]:
        log.skipped("Deploy not triggered", "Run test_manual_deploy_trigger first")
        pytest.skip("Deploy not triggered")

    pipeline_id = _manual_state["deploy_pipeline_id"]

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    log.check(f"Selecting image for deploy pipeline #{pipeline_id}")

    result = select_image_for_deploy(host, pipeline_id, log_callback=_log_callback)

    if not result["success"]:
        log.failed(
            f"Failed to select image: {result['error']}",
            "Check pipeline structure"
        )
        pytest.fail(f"Image selection failed: {result['error']}")

    _log_callback(f"Selected image group: {result['image_group_id']}")

    log.passed(
        f"Image group selected: {result['image_group_id']}",
        f"GitLab job ID: {result.get('gitlab_job_id', 'N/A')}"
    )


# =============================================================================
# TEST 7: WAIT FOR DEPLOY COMPLETION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.manual
@pytest.mark.order(36)
def test_manual_deploy_completion(host):
    """
    Test 7: Wait for deploy pipeline to complete.
    """
    log = TestLogger("Manual Deploy Completion")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    if not _manual_state["deploy_triggered"]:
        log.skipped("Deploy not triggered", "Run previous tests first")
        pytest.skip("Deploy not triggered")

    pipeline_id = _manual_state["deploy_pipeline_id"]

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    log.check(f"Waiting for deploy pipeline #{pipeline_id} to complete")

    success = _wait_for_pipeline_completion(host, pipeline_id, log_callback=_log_callback, timeout=1800)

    if success:
        _manual_state["deploy_completed"] = True
        log.passed(
            f"Deploy pipeline #{pipeline_id} completed successfully",
            "All stages passed"
        )
    else:
        log.failed(
            f"Deploy pipeline #{pipeline_id} failed or timed out",
            "Check GitLab for details"
        )
        pytest.fail("Deploy pipeline failed")
