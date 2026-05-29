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
Build Stream - Deploy Pipeline Test Cases.

Test cases for deploy pipeline automation:
1. Trigger deploy pipeline by committing PXE mapping file
2. Monitor deploy stages (upload, deploy, pxe_boot, restart)
3. Verify each stage in database (pass if DB correctly reflects status)

Markers:
    - sanity: Basic sanity tests
    - build_stream: Build stream module tests
    - deploy: Deploy pipeline specific tests
"""

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    trigger_deploy_pipeline,
    select_image_for_deploy,
    wait_for_stage_completion,
    get_stage_state,
    get_stage_log_path,
    get_latest_job,
    get_all_image_groups,
    DEPLOY_PIPELINE_STAGES,
    STAGE_POLL_INTERVAL,
    STAGE_POLL_TIMEOUT,
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# MODULE-LEVEL STATE
# =============================================================================

_deploy_state = {
    "job_id": None,
    "pipeline_id": None,
    "triggered": False,
    "stage_results": {},
    "build_succeeded": False,
}


def _check_build_succeeded(host) -> bool:
    """Check if build pipeline succeeded by looking for BUILT image groups."""
    result = get_all_image_groups(host)
    if result["success"] and result["image_groups"]:
        built_groups = [g for g in result["image_groups"] if g["status"] == "BUILT"]
        return len(built_groups) > 0
    return False


def _skip_if_not_triggered(log):
    """Skip test if deploy pipeline was not triggered."""
    if not _deploy_state["triggered"]:
        log.skipped("Deploy not triggered", "Previous test failed to trigger deploy pipeline")
        pytest.skip("Deploy pipeline not triggered")


def _get_previous_stage(stage_name: str) -> str:
    """Get the previous stage name in the pipeline."""
    stages = DEPLOY_PIPELINE_STAGES
    idx = stages.index(stage_name) if stage_name in stages else -1
    return stages[idx - 1] if idx > 0 else None


def _should_skip_due_to_previous_failure(stage_name: str) -> bool:
    """Check if test should skip due to any prior stage failure."""
    stages = DEPLOY_PIPELINE_STAGES
    if stage_name not in stages:
        return False
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _deploy_state["stage_results"]:
            prior_result = _deploy_state["stage_results"][prior_stage]
            if prior_result.get("stage_state") == "FAILED":
                return True
    return False


def _get_failed_prior_stage(stage_name: str) -> str:
    """Get the name of the first failed prior stage, or None."""
    stages = DEPLOY_PIPELINE_STAGES
    if stage_name not in stages:
        return None
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _deploy_state["stage_results"]:
            prior_result = _deploy_state["stage_results"][prior_stage]
            if prior_result.get("stage_state") == "FAILED":
                return prior_stage
    return None


# =============================================================================
# TEST 1: TRIGGER DEPLOY PIPELINE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.deploy
@pytest.mark.order(30)
def test_trigger_deploy_pipeline(host):
    """
    Test 1: Commit PXE mapping file to GitLab and trigger deploy pipeline.

    This auto-triggers the deploy pipeline by committing the PXE mapping file.
    Skips if build pipeline has not succeeded (no BUILT image groups).
    """
    import sys
    log = TestLogger("Trigger Deploy Pipeline")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    if not _check_build_succeeded(host):
        log.skipped(
            SKIP_MSGS["build_failed"],
            "No BUILT image groups found. Build pipeline must complete successfully first."
        )
        pytest.skip(SKIP_MSGS["build_failed"])

    _deploy_state["build_succeeded"] = True
    log.check("Committing PXE mapping file to trigger deploy pipeline")

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    result = trigger_deploy_pipeline(host, log_callback=_log_callback)

    if result["success"]:
        _deploy_state["triggered"] = True
        _deploy_state["pipeline_id"] = result["pipeline_id"]
        _deploy_state["job_id"] = result["job_id"]

        _log_callback("Auto-selecting image group for deployment...")
        select_result = select_image_for_deploy(host, result["pipeline_id"], log_callback=_log_callback)
        if select_result["success"]:
            _log_callback(f"Image group selected: {select_result['image_group_id']}")
        else:
            _log_callback(f"⚠ Image selection failed: {select_result['error']}")
            _log_callback("Deploy stages may require manual image selection in GitLab")

        log.passed(
            f"Deploy pipeline {result['pipeline_id']} triggered",
            result["details"]
        )
    else:
        log.failed(
            f"Failed to trigger deploy pipeline: {result['error']}",
            result.get("details", "")
        )
        pytest.fail(f"Failed to trigger deploy pipeline: {result['error']}")


# =============================================================================
# STAGE MONITOR AND DB VERIFY FUNCTIONS
# =============================================================================

def _run_stage_monitor_test(host, stage_name: str):
    """Run stage monitor test for a given stage."""
    log = TestLogger(TEST_NAMES["stage_monitor"].format(stage=stage_name))

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_triggered(log)

    failed_stage = _get_failed_prior_stage(stage_name)
    if failed_stage:
        log.skipped(
            SKIP_MSGS["previous_stage_failed"].format(stage=failed_stage),
            f"Stage '{failed_stage}' failed"
        )
        pytest.skip(f"Prior stage '{failed_stage}' failed")

    job_id = _deploy_state["job_id"]
    if not job_id:
        job_result = get_latest_job(host)
        if job_result["success"]:
            job_id = job_result["job_id"]
            _deploy_state["job_id"] = job_id

    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    import sys
    log.check(f"Monitoring stage '{stage_name}' for job {job_id}")

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    result = wait_for_stage_completion(
        host, job_id, stage_name,
        timeout=STAGE_POLL_TIMEOUT,
        poll_interval=STAGE_POLL_INTERVAL,
        log_callback=_log_callback
    )

    _deploy_state["stage_results"][stage_name] = result

    if result["success"]:
        log.passed(
            TEST_LOG_MSGS["stage_completed"].format(stage=stage_name, elapsed=result["elapsed"]),
            f"State: {result['stage_state']}"
        )
    else:
        fail_details = f"State: {result.get('stage_state', 'N/A')}\nElapsed: {result.get('elapsed', 0)}s"
        log_path = get_stage_log_path(host, job_id, stage_name)
        if log_path:
            fail_details += f"\nLog file: {log_path}"
            _log_callback(f"Log file path: {log_path}")
        log.failed(
            TEST_LOG_MSGS["stage_failed"].format(stage=stage_name, error=result["error"]),
            fail_details
        )
        pytest.fail(TEST_ASSERT_MSGS["stage_failed"].format(stage=stage_name, error=result["error"]))


def _run_stage_db_verify_test(host, stage_name: str):
    """
    Run stage DB verification test.

    IMPORTANT: This test PASSES if the DB correctly reflects the stage status,
    even if the stage failed. The purpose is to verify DB accuracy, not stage success.
    """
    log = TestLogger(TEST_NAMES["stage_db_verify"].format(stage=stage_name))

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_triggered(log)

    job_id = _deploy_state["job_id"]
    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check(f"Verifying stage '{stage_name}' in database")

    db_result = get_stage_state(host, job_id, stage_name)

    if not db_result["success"]:
        if _should_skip_due_to_previous_failure(stage_name):
            log.skipped(
                f"Stage '{stage_name}' not in DB (previous stage failed)",
                "Expected behavior when previous stage fails"
            )
            return
        log.failed(
            TEST_LOG_MSGS["stage_db_fail"].format(stage=stage_name, error=db_result["error"]),
            f"DB query failed: {db_result['error']}"
        )
        pytest.fail(f"DB query failed for stage '{stage_name}'")

    db_state = db_result["stage_state"]
    expected_state = None

    if stage_name in _deploy_state["stage_results"]:
        monitor_result = _deploy_state["stage_results"][stage_name]
        expected_state = monitor_result.get("stage_state")

    if expected_state and db_state == expected_state:
        log.passed(
            f"DB correctly shows stage '{stage_name}' as {db_state}",
            f"Stage state: {db_state}\nDB matches monitored state"
        )
    elif db_state in ("COMPLETED", "FAILED"):
        log.passed(
            f"Stage '{stage_name}' verified in DB (state: {db_state})",
            f"DB state: {db_state}"
        )
    else:
        log.failed(
            f"Stage '{stage_name}' has unexpected state in DB: {db_state}",
            f"Expected: COMPLETED or FAILED, Got: {db_state}"
        )
        pytest.fail(f"Unexpected DB state for stage '{stage_name}': {db_state}")


# =============================================================================
# TEST 2-3: DEPLOY STAGE (DB stage)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.deploy
@pytest.mark.order(31)
def test_stage_deploy_monitor(host):
    """Test 2: Monitor 'deploy' stage until completion."""
    _run_stage_monitor_test(host, "deploy")


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.deploy
@pytest.mark.order(32)
def test_stage_deploy_db_verify(host):
    """Test 3: Verify 'deploy' stage status in database."""
    _run_stage_db_verify_test(host, "deploy")


# =============================================================================
# TEST 4-5: RESTART STAGE (DB stage)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.deploy
@pytest.mark.order(33)
def test_stage_restart_monitor(host):
    """Test 4: Monitor 'restart' stage until completion."""
    _run_stage_monitor_test(host, "restart")


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.deploy
@pytest.mark.order(34)
def test_stage_restart_db_verify(host):
    """Test 5: Verify 'restart' stage status in database."""
    _run_stage_db_verify_test(host, "restart")
