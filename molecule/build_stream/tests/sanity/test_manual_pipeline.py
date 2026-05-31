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
Build Stream - Manual Pipeline Trigger Tests (Build + Deploy).

Tests for manually triggering pipelines via PIPELINE_TYPE variable:
  - Build: PIPELINE_TYPE=build
  - Deploy: PIPELINE_TYPE=deploy

Same test structure as auto-trigger tests but uses API variable trigger.

Test Order (after test_cleanup_pipeline.py):
  - Order 60-77: Build pipeline (manual trigger via PIPELINE_TYPE=build)
  - Order 80-84: Deploy pipeline (manual trigger via PIPELINE_TYPE=deploy)

Markers:
    - sanity: Basic sanity tests
    - build_manual: Build pipeline manual trigger tests
    - deploy_manual: Deploy pipeline manual trigger tests
"""

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    trigger_pipeline_with_variables,
    trigger_deploy_pipeline,
    select_image_for_deploy,
    play_deploy_stage_job,
    wait_for_stage_completion,
    get_stage_state,
    get_stage_log_path,
    get_images_for_job,
    get_image_groups_for_job,
    get_latest_job,
    get_catalog_roles,
    get_all_image_groups,
    verify_registry_images,
    verify_s3_boot_images,
    BUILD_PIPELINE_CORE_STAGES,
    BUILD_IMAGE_STAGE_PREFIX,
    DEPLOY_PIPELINE_STAGES,
    STAGE_POLL_INTERVAL,
    STAGE_POLL_TIMEOUT,
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# BUILD PIPELINE STATE
# =============================================================================

_build_state = {
    "job_id": None,
    "pipeline_id": None,
    "triggered": False,
    "stage_results": {},
    "catalog_roles": [],
    "catalog_architectures": [],
    "catalog_image_key": "",
}


def _get_build_stages():
    """Build the ordered list of stages for the current pipeline run."""
    stages = list(BUILD_PIPELINE_CORE_STAGES)
    for arch in _build_state.get("catalog_architectures", []):
        stages.append(f"{BUILD_IMAGE_STAGE_PREFIX}{arch}")
    if not _build_state.get("catalog_architectures"):
        stages.append(f"{BUILD_IMAGE_STAGE_PREFIX}x86_64")
    return stages


def _skip_if_build_not_triggered(log):
    """Skip test if build pipeline was not triggered."""
    if not _build_state["triggered"]:
        log.skipped("Build not triggered", "Previous test failed to trigger pipeline")
        pytest.skip("Build pipeline not triggered")


def _build_should_skip_due_to_failure(stage_name: str) -> bool:
    """Check if test should skip due to any prior stage failure."""
    stages = _get_build_stages()
    if stage_name not in stages:
        return False
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _build_state["stage_results"]:
            if _build_state["stage_results"][prior_stage].get("stage_state") == "FAILED":
                return True
    return False


def _get_build_failed_prior_stage(stage_name: str) -> str:
    """Get the name of the first failed prior stage, or None."""
    stages = _get_build_stages()
    if stage_name not in stages:
        return None
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _build_state["stage_results"]:
            if _build_state["stage_results"][prior_stage].get("stage_state") == "FAILED":
                return prior_stage
    return None


def _any_build_stage_failed() -> bool:
    """Return True if any monitored stage has FAILED."""
    for result in _build_state["stage_results"].values():
        if result.get("stage_state") == "FAILED":
            return True
    return False


# =============================================================================
# DEPLOY PIPELINE STATE
# =============================================================================

_deploy_state = {
    "job_id": None,
    "pipeline_id": None,
    "triggered": False,
    "stage_results": {},
}


def _skip_if_deploy_not_triggered(log):
    """Skip test if deploy pipeline was not triggered."""
    if not _deploy_state["triggered"]:
        log.skipped("Deploy not triggered", "Previous test failed to trigger pipeline")
        pytest.skip("Deploy pipeline not triggered")


def _deploy_should_skip_due_to_failure(stage_name: str) -> bool:
    """Check if test should skip due to any prior stage failure."""
    stages = DEPLOY_PIPELINE_STAGES
    if stage_name not in stages:
        return False
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _deploy_state["stage_results"]:
            if _deploy_state["stage_results"][prior_stage].get("stage_state") == "FAILED":
                return True
    return False


def _get_deploy_failed_prior_stage(stage_name: str) -> str:
    """Get the name of the first failed prior stage, or None."""
    stages = DEPLOY_PIPELINE_STAGES
    if stage_name not in stages:
        return None
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _deploy_state["stage_results"]:
            if _deploy_state["stage_results"][prior_stage].get("stage_state") == "FAILED":
                return prior_stage
    return None


# =============================================================================
# BUILD STAGE HELPER FUNCTIONS
# =============================================================================

def _run_build_stage_monitor(host, stage_name: str):
    """Run stage monitor test for build pipeline."""
    log = TestLogger(TEST_NAMES["stage_monitor"].format(stage=stage_name))

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_build_not_triggered(log)

    failed_stage = _get_build_failed_prior_stage(stage_name)
    if failed_stage:
        log.skipped(
            SKIP_MSGS["previous_stage_failed"].format(stage=failed_stage),
            f"Stage '{failed_stage}' failed"
        )
        pytest.skip(f"Prior stage '{failed_stage}' failed")

    job_id = _build_state["job_id"]
    if not job_id:
        job_result = get_latest_job(host)
        if job_result["success"]:
            job_id = job_result["job_id"]
            _build_state["job_id"] = job_id

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

    _build_state["stage_results"][stage_name] = result

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


def _run_build_stage_db_verify(host, stage_name: str):
    """Run stage DB verification test for build pipeline."""
    log = TestLogger(TEST_NAMES["stage_db_verify"].format(stage=stage_name))

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_build_not_triggered(log)

    job_id = _build_state["job_id"]
    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check(f"Verifying stage '{stage_name}' in database")

    db_result = get_stage_state(host, job_id, stage_name)

    if not db_result["success"]:
        if _build_should_skip_due_to_failure(stage_name):
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

    if stage_name in _build_state["stage_results"]:
        expected_state = _build_state["stage_results"][stage_name].get("stage_state")

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
    elif db_state == "PENDING" and _build_should_skip_due_to_failure(stage_name):
        failed_stage = _get_build_failed_prior_stage(stage_name)
        log.passed(
            f"Stage '{stage_name}' is PENDING (prior stage '{failed_stage}' failed)",
            f"DB state: {db_state}"
        )
    else:
        log.failed(
            f"Stage '{stage_name}' has unexpected state in DB: {db_state}",
            f"Expected: COMPLETED or FAILED, Got: {db_state}"
        )
        pytest.fail(f"Unexpected DB state for stage '{stage_name}': {db_state}")


# =============================================================================
# DEPLOY STAGE HELPER FUNCTIONS
# =============================================================================

def _run_deploy_stage_monitor(host, stage_name: str):
    """Run stage monitor test for deploy pipeline."""
    log = TestLogger(TEST_NAMES["stage_monitor"].format(stage=stage_name))

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_deploy_not_triggered(log)

    failed_stage = _get_deploy_failed_prior_stage(stage_name)
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


def _run_deploy_stage_db_verify(host, stage_name: str):
    """Run stage DB verification test for deploy pipeline."""
    log = TestLogger(TEST_NAMES["stage_db_verify"].format(stage=stage_name))

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_deploy_not_triggered(log)

    job_id = _deploy_state["job_id"]
    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check(f"Verifying stage '{stage_name}' in database")

    db_result = get_stage_state(host, job_id, stage_name)

    if not db_result["success"]:
        if _deploy_should_skip_due_to_failure(stage_name):
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
        expected_state = _deploy_state["stage_results"][stage_name].get("stage_state")

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
# BUILD PIPELINE TESTS (Order 60-77) - MANUAL TRIGGER
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(60)
def test_manual_trigger_build_pipeline(host):
    """Test: Trigger build pipeline using PIPELINE_TYPE=build variable."""
    import sys
    import time
    log = TestLogger("Manual Trigger Build Pipeline")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    log.check("Triggering build pipeline with PIPELINE_TYPE=build")

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    old_job = get_latest_job(host)
    old_job_id = old_job.get("job_id", "") if old_job["success"] else ""

    _log_callback("Triggering pipeline with PIPELINE_TYPE=build...")
    result = trigger_pipeline_with_variables(host, {"PIPELINE_TYPE": "build"})

    if not result["success"]:
        log.failed(
            f"Failed to trigger build pipeline: {result['error']}",
            "Check GitLab API access"
        )
        pytest.fail(f"Trigger failed: {result['error']}")

    _build_state["pipeline_id"] = result["pipeline_id"]
    _log_callback(f"Pipeline #{result['pipeline_id']} triggered (status: {result['status']})")

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

    _build_state["triggered"] = True
    _build_state["job_id"] = new_job_id

    roles_result = get_catalog_roles(host, new_job_id)
    if roles_result["success"]:
        _build_state["catalog_roles"] = roles_result["roles"]
        _build_state["catalog_architectures"] = roles_result["architectures"]
        _build_state["catalog_image_key"] = roles_result["image_key"]
        _log_callback(
            f"Catalog: {len(roles_result['roles'])} roles, "
            f"architectures: {roles_result['architectures']}"
        )

    log.passed(
        f"Build pipeline #{result['pipeline_id']} triggered successfully",
        f"Job ID: {new_job_id}"
    )


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(61)
def test_manual_build_stage_upload_monitor(host):
    """Monitor 'upload' stage until completion."""
    _run_build_stage_monitor(host, "upload")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(62)
def test_manual_build_stage_upload_db_verify(host):
    """Verify 'upload' stage status in database."""
    _run_build_stage_db_verify(host, "upload")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(63)
def test_manual_build_stage_parse_catalog_monitor(host):
    """Monitor 'parse-catalog' stage until completion."""
    _run_build_stage_monitor(host, "parse-catalog")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(64)
def test_manual_build_stage_parse_catalog_db_verify(host):
    """Verify 'parse-catalog' stage status in database."""
    _run_build_stage_db_verify(host, "parse-catalog")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(65)
def test_manual_build_stage_generate_input_files_monitor(host):
    """Monitor 'generate-input-files' stage until completion."""
    _run_build_stage_monitor(host, "generate-input-files")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(66)
def test_manual_build_stage_generate_input_files_db_verify(host):
    """Verify 'generate-input-files' stage status in database."""
    _run_build_stage_db_verify(host, "generate-input-files")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(67)
def test_manual_build_stage_create_local_repository_monitor(host):
    """Monitor 'create-local-repository' stage until completion."""
    _run_build_stage_monitor(host, "create-local-repository")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(68)
def test_manual_build_stage_create_local_repository_db_verify(host):
    """Verify 'create-local-repository' stage status in database."""
    _run_build_stage_db_verify(host, "create-local-repository")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(69)
def test_manual_build_stage_build_image_x86_64_monitor(host):
    """Monitor 'build-image-x86_64' stage until completion."""
    _run_build_stage_monitor(host, "build-image-x86_64")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(70)
def test_manual_build_stage_build_image_x86_64_db_verify(host):
    """Verify 'build-image-x86_64' stage status in database."""
    _run_build_stage_db_verify(host, "build-image-x86_64")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(71)
def test_manual_build_stage_build_image_aarch64_monitor(host):
    """Monitor 'build-image-aarch64' stage (skipped if not in catalog)."""
    if "aarch64" not in _build_state.get("catalog_architectures", []):
        log = TestLogger(TEST_NAMES["stage_monitor"].format(stage="build-image-aarch64"))
        log.skipped(
            "aarch64 not in catalog architectures",
            f"Architectures: {_build_state.get('catalog_architectures', [])}"
        )
        pytest.skip("aarch64 not in catalog architectures")
    _run_build_stage_monitor(host, "build-image-aarch64")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(72)
def test_manual_build_stage_build_image_aarch64_db_verify(host):
    """Verify 'build-image-aarch64' stage in database (skipped if not in catalog)."""
    if "aarch64" not in _build_state.get("catalog_architectures", []):
        log = TestLogger(TEST_NAMES["stage_db_verify"].format(stage="build-image-aarch64"))
        log.skipped(
            "aarch64 not in catalog architectures",
            f"Architectures: {_build_state.get('catalog_architectures', [])}"
        )
        pytest.skip("aarch64 not in catalog architectures")
    _run_build_stage_db_verify(host, "build-image-aarch64")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(73)
def test_manual_build_image_groups_created(host):
    """Verify image groups were created for the job."""
    log = TestLogger(TEST_NAMES["image_groups_created"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_build_not_triggered(log)

    if _any_build_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "Build pipeline had failures")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _build_state["job_id"]
    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check(f"Checking image groups for job {job_id}")

    result = get_image_groups_for_job(host, job_id)

    if result["success"] and result["image_groups"]:
        details_lines = [f"Found {len(result['image_groups'])} image group(s):"]
        for group in result["image_groups"]:
            details_lines.append(f"  ✓ {group['id']} (status: {group['status']})")
        log.passed(
            TEST_LOG_MSGS["image_groups_ok"].format(count=len(result["image_groups"]), job_id=job_id),
            "\n".join(details_lines)
        )
    else:
        log.failed(
            TEST_LOG_MSGS["image_groups_fail"].format(job_id=job_id),
            result.get("error", "No image groups found")
        )
        pytest.fail(f"No image groups found for job {job_id}")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(74)
def test_manual_build_images_created(host):
    """Verify images were created for the job."""
    log = TestLogger(TEST_NAMES["images_created"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_build_not_triggered(log)

    if _any_build_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "Build pipeline had failures")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _build_state["job_id"]
    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check(f"Checking images for job {job_id}")

    result = get_images_for_job(host, job_id)

    if result["success"] and result["images"]:
        details_lines = [f"Found {len(result['images'])} image(s):"]
        for img in result["images"]:
            details_lines.append(
                f"  ✓ {img['role']} → {img['image_name']} (group: {img['group_id']})"
            )
        log.passed(
            TEST_LOG_MSGS["images_ok"].format(count=len(result["images"]), job_id=job_id),
            "\n".join(details_lines)
        )
    else:
        log.failed(
            TEST_LOG_MSGS["images_fail"].format(job_id=job_id),
            result.get("error", "No images found")
        )
        pytest.fail(f"No images found for job {job_id}")


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(75)
def test_manual_build_registry_images(host):
    """Verify container images exist in registry for all roles."""
    log = TestLogger(TEST_NAMES["registry_images"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_build_not_triggered(log)

    if _any_build_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "Build pipeline had failures")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _build_state["job_id"]
    roles = _build_state.get("catalog_roles", [])
    image_key = _build_state.get("catalog_image_key", "")

    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    if not roles:
        roles_result = get_catalog_roles(host, job_id)
        if roles_result["success"]:
            roles = roles_result["roles"]
            image_key = roles_result["image_key"]
            _build_state["catalog_roles"] = roles
            _build_state["catalog_image_key"] = image_key

    log.check(f"Verifying registry images for {len(roles)} roles (job {job_id[:8]}...)")

    result = verify_registry_images(host, job_id, roles, image_key)

    if result["success"]:
        details_lines = [result["details"]]
        for item in result["found"]:
            details_lines.append(f"  ✓ {item['role']} → {item['repo']}")
        log.passed(
            TEST_LOG_MSGS["registry_ok"].format(count=len(roles)),
            "\n".join(details_lines)
        )
    else:
        error_msg = result.get("error", "")
        missing = result.get("missing", [])
        if missing:
            error_msg = f"Missing roles: {', '.join(missing)}"
        log.failed(
            TEST_LOG_MSGS["registry_fail"].format(count=len(missing), missing=missing),
            error_msg
        )
        pytest.fail(TEST_ASSERT_MSGS["registry_images_failed"].format(error=error_msg))


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(76)
def test_manual_build_s3_boot_images(host):
    """Verify S3 boot images (rootfs + EFI) exist for all roles."""
    log = TestLogger(TEST_NAMES["s3_boot_images"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_build_not_triggered(log)

    if _any_build_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "Build pipeline had failures")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _build_state["job_id"]
    roles = _build_state.get("catalog_roles", [])
    image_key = _build_state.get("catalog_image_key", "")

    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    if not roles:
        roles_result = get_catalog_roles(host, job_id)
        if roles_result["success"]:
            roles = roles_result["roles"]
            image_key = roles_result["image_key"]

    log.check(f"Verifying S3 boot images for {len(roles)} roles (job {job_id[:8]}...)")

    result = verify_s3_boot_images(host, job_id, roles, image_key)

    if result["success"]:
        details_lines = [result["details"]]
        for item in result["found_roles"]:
            details_lines.append(
                f"  ✓ {item['role']} (rootfs: {item['rootfs']}, "
                f"efi: {item['efi_files']}, total: {item['total']})"
            )
        log.passed(
            TEST_LOG_MSGS["s3_ok"].format(count=len(roles)),
            "\n".join(details_lines)
        )
    else:
        error_msg = result.get("error", "")
        missing = result.get("missing_roles", [])
        if missing:
            error_msg = (
                "Missing roles: "
                + ", ".join(
                    f"{m['role']} (rootfs: {m['rootfs']}, efi: {m['efi_files']})"
                    for m in missing
                )
            )
        log.failed(
            TEST_LOG_MSGS["s3_fail"].format(count=len(missing), missing=missing),
            error_msg
        )
        pytest.fail(TEST_ASSERT_MSGS["s3_images_failed"].format(error=error_msg))


@pytest.mark.sanity
@pytest.mark.build_manual
@pytest.mark.order(77)
def test_manual_build_pipeline_result(host):
    """Summarize build pipeline result."""
    log = TestLogger(TEST_NAMES["build_pipeline_result"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_build_not_triggered(log)

    log.check("Evaluating build pipeline final result")

    stages = _get_build_stages()
    completed = []
    failed = []
    skipped = []

    for stage in stages:
        if stage in _build_state["stage_results"]:
            r = _build_state["stage_results"][stage]
            if r.get("stage_state") == "COMPLETED":
                completed.append(stage)
            elif r.get("stage_state") == "FAILED":
                failed.append(stage)
            else:
                skipped.append(stage)
        else:
            skipped.append(stage)

    details_lines = [
        f"Stages: {len(stages)} total, {len(completed)} completed, "
        f"{len(failed)} failed, {len(skipped)} skipped"
    ]
    for stage in stages:
        if stage in _build_state["stage_results"]:
            state = _build_state["stage_results"][stage].get("stage_state", "?")
            symbol = "✓" if state == "COMPLETED" else "✗" if state == "FAILED" else "○"
            details_lines.append(f"  {symbol} {stage}: {state}")
        else:
            details_lines.append(f"  ○ {stage}: NOT MONITORED")

    if not failed:
        log.passed(
            TEST_LOG_MSGS["pipeline_result_ok"],
            "\n".join(details_lines)
        )
    else:
        log.failed(
            TEST_LOG_MSGS["pipeline_result_fail"],
            "\n".join(details_lines)
        )
        pytest.fail(f"Pipeline failed: {', '.join(failed)}")


# =============================================================================
# DEPLOY PIPELINE TESTS (Order 80-84) - MANUAL TRIGGER
# =============================================================================

def _check_build_succeeded(host) -> bool:
    """Check if deployable image groups exist (any status except CLEANED)."""
    result = get_all_image_groups(host)
    if result["success"] and result["image_groups"]:
        deployable = [g for g in result["image_groups"] if g["status"] != "CLEANED"]
        return len(deployable) > 0
    return False


@pytest.mark.sanity
@pytest.mark.deploy_manual
@pytest.mark.order(80)
def test_manual_trigger_deploy_pipeline(host):
    """Trigger deploy pipeline using PIPELINE_TYPE=deploy variable."""
    import sys
    log = TestLogger("Manual Trigger Deploy Pipeline")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    if not _check_build_succeeded(host):
        log.skipped(
            SKIP_MSGS["build_failed"],
            "No BUILT image groups found. Build pipeline must complete successfully first."
        )
        pytest.skip(SKIP_MSGS["build_failed"])

    log.check("Triggering deploy pipeline with PIPELINE_TYPE=deploy")

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    # Use trigger_deploy_pipeline with use_pxe_commit=False for manual trigger
    result = trigger_deploy_pipeline(host, log_callback=_log_callback, use_pxe_commit=False)

    if result["success"]:
        _deploy_state["triggered"] = True
        _deploy_state["pipeline_id"] = result["pipeline_id"]
        _deploy_state["job_id"] = result["job_id"]

        _log_callback("Auto-selecting image group for deployment...")
        select_result = select_image_for_deploy(host, result["pipeline_id"], log_callback=_log_callback)
        if select_result["success"]:
            _log_callback(f"Image group selected: {select_result['image_group_id']}")

            # Update job_id from the selected image group (tied to build)
            if select_result.get("job_id"):
                _deploy_state["job_id"] = select_result["job_id"]
                _log_callback(f"Using job ID from image group: {select_result['job_id'][:8]}...")

            # After selecting image, play the deploy stage job (it's manual)
            _log_callback("Playing deploy stage job...")
            deploy_result = play_deploy_stage_job(host, result["pipeline_id"], log_callback=_log_callback)
            if deploy_result["success"]:
                _log_callback("Deploy stage started successfully")
            else:
                _log_callback(f"⚠ Failed to start deploy stage: {deploy_result['error']}")
                _log_callback("You may need to manually play 'deploy' job in GitLab")
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


@pytest.mark.sanity
@pytest.mark.deploy_manual
@pytest.mark.order(81)
def test_manual_deploy_stage_deploy_monitor(host):
    """Monitor 'deploy' stage until completion."""
    _run_deploy_stage_monitor(host, "deploy")


@pytest.mark.sanity
@pytest.mark.deploy_manual
@pytest.mark.order(82)
def test_manual_deploy_stage_deploy_db_verify(host):
    """Verify 'deploy' stage status in database."""
    _run_deploy_stage_db_verify(host, "deploy")


@pytest.mark.sanity
@pytest.mark.deploy_manual
@pytest.mark.order(83)
def test_manual_deploy_stage_restart_monitor(host):
    """Monitor 'restart' stage until completion."""
    _run_deploy_stage_monitor(host, "restart")


@pytest.mark.sanity
@pytest.mark.deploy_manual
@pytest.mark.order(84)
def test_manual_deploy_stage_restart_db_verify(host):
    """Verify 'restart' stage status in database."""
    _run_deploy_stage_db_verify(host, "restart")


@pytest.mark.sanity
@pytest.mark.deploy_manual
@pytest.mark.order(85)
def test_manual_deploy_stage_validate_monitor(host):
    """Monitor 'validate' stage until completion."""
    _run_deploy_stage_monitor(host, "validate")


@pytest.mark.sanity
@pytest.mark.deploy_manual
@pytest.mark.order(86)
def test_manual_deploy_stage_validate_db_verify(host):
    """Verify 'validate' stage status in database."""
    _run_deploy_stage_db_verify(host, "validate")
