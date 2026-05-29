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
Build Stream - Build Pipeline Test Cases.

Test cases for build pipeline automation:
1. Upload catalog and trigger pipeline
2. Monitor each core stage until completion or failure
3. Dynamically detect and monitor build-image stages based on catalog architectures
4. Verify DB correctly reflects stage status
5. Verify registry images and S3 boot images after build completes
6. Final pipeline result summary

Markers:
    - sanity: Basic sanity tests
    - build_stream: Build stream module tests
    - build: Build pipeline specific tests
"""

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    trigger_build_pipeline,
    wait_for_stage_completion,
    get_stage_state,
    get_stage_log_path,
    get_images_for_job,
    get_image_groups_for_job,
    get_latest_job,
    get_catalog_roles,
    verify_registry_images,
    verify_s3_boot_images,
    BUILD_PIPELINE_CORE_STAGES,
    BUILD_IMAGE_STAGE_PREFIX,
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

_pipeline_state = {
    "job_id": None,
    "pipeline_id": None,
    "triggered": False,
    "stage_results": {},
    "catalog_roles": [],
    "catalog_architectures": [],
    "catalog_image_key": "",
}


def _get_active_stages():
    """
    Build the ordered list of stages for the current pipeline run.

    Core stages are always present. Build-image stages are added dynamically
    based on the architectures detected from the Build Stream API.
    """
    stages = list(BUILD_PIPELINE_CORE_STAGES)
    for arch in _pipeline_state.get("catalog_architectures", []):
        stages.append(f"{BUILD_IMAGE_STAGE_PREFIX}{arch}")
    if not _pipeline_state.get("catalog_architectures"):
        stages.append(f"{BUILD_IMAGE_STAGE_PREFIX}x86_64")
    return stages


def _skip_if_not_triggered(log):
    """Skip test if pipeline was not triggered."""
    if not _pipeline_state["triggered"]:
        log.skipped("Pipeline not triggered", "Previous test failed to trigger pipeline")
        pytest.skip("Pipeline not triggered")


def _should_skip_due_to_previous_failure(stage_name: str) -> bool:
    """Check if test should skip due to any prior stage failure."""
    stages = _get_active_stages()
    if stage_name not in stages:
        return False
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _pipeline_state["stage_results"]:
            prior_result = _pipeline_state["stage_results"][prior_stage]
            if prior_result.get("stage_state") == "FAILED":
                return True
    return False


def _get_failed_prior_stage(stage_name: str) -> str:
    """Get the name of the first failed prior stage, or None."""
    stages = _get_active_stages()
    if stage_name not in stages:
        return None
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _pipeline_state["stage_results"]:
            prior_result = _pipeline_state["stage_results"][prior_stage]
            if prior_result.get("stage_state") == "FAILED":
                return prior_stage
    return None


def _any_stage_failed() -> bool:
    """Return True if any monitored stage has FAILED."""
    for result in _pipeline_state["stage_results"].values():
        if result.get("stage_state") == "FAILED":
            return True
    return False


# =============================================================================
# TEST 1: UPLOAD CATALOG AND TRIGGER PIPELINE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(10)
def test_trigger_build_pipeline(host):
    """
    Test 1: Upload catalog file to GitLab and verify pipeline is auto-triggered.

    The catalog identifier is set to 'image-build-<datetime>' to ensure
    each run creates a unique image group.
    """
    import sys
    log = TestLogger(TEST_NAMES["catalog_upload"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    log.check("Uploading catalog to GitLab to trigger build pipeline")

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    result = trigger_build_pipeline(host, log_callback=_log_callback)

    if result["success"]:
        _pipeline_state["triggered"] = True
        _pipeline_state["pipeline_id"] = result["pipeline_id"]
        _pipeline_state["job_id"] = result["job_id"]

        roles_result = get_catalog_roles(host, result["job_id"])
        if roles_result["success"]:
            _pipeline_state["catalog_roles"] = roles_result["roles"]
            _pipeline_state["catalog_architectures"] = roles_result["architectures"]
            _pipeline_state["catalog_image_key"] = roles_result["image_key"]
            _log_callback(
                f"Catalog: {len(roles_result['roles'])} roles, "
                f"architectures: {roles_result['architectures']}, "
                f"image_key: {roles_result['image_key']}"
            )

        log.passed(
            TEST_LOG_MSGS["catalog_upload_ok"].format(
                pipeline_id=result["pipeline_id"],
                job_id=result["job_id"]
            ),
            result["details"]
        )
    else:
        log.failed(
            TEST_LOG_MSGS["catalog_upload_fail"].format(error=result["error"]),
            result.get("details", "")
        )
        pytest.fail(TEST_ASSERT_MSGS["catalog_upload_failed"].format(error=result["error"]))


# =============================================================================
# STAGE MONITOR AND DB VERIFY FUNCTIONS
# =============================================================================

def _run_stage_monitor_test(host, stage_name: str, order: int):
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

    job_id = _pipeline_state["job_id"]
    if not job_id:
        job_result = get_latest_job(host)
        if job_result["success"]:
            job_id = job_result["job_id"]
            _pipeline_state["job_id"] = job_id

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

    _pipeline_state["stage_results"][stage_name] = result

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


def _run_stage_db_verify_test(host, stage_name: str, order: int):
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

    job_id = _pipeline_state["job_id"]
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

    if stage_name in _pipeline_state["stage_results"]:
        monitor_result = _pipeline_state["stage_results"][stage_name]
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
    elif db_state == "PENDING" and _should_skip_due_to_previous_failure(stage_name):
        failed_stage = _get_failed_prior_stage(stage_name)
        log.passed(
            f"Stage '{stage_name}' is PENDING (prior stage '{failed_stage}' failed)",
            f"DB state: {db_state} — expected because '{failed_stage}' failed"
        )
    else:
        log.failed(
            f"Stage '{stage_name}' has unexpected state in DB: {db_state}",
            f"Expected: COMPLETED or FAILED, Got: {db_state}"
        )
        pytest.fail(f"Unexpected DB state for stage '{stage_name}': {db_state}")


# =============================================================================
# TEST 2-3: UPLOAD STAGE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(11)
def test_stage_upload_monitor(host):
    """Test 2: Monitor 'upload' stage until completion."""
    _run_stage_monitor_test(host, "upload", 11)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(12)
def test_stage_upload_db_verify(host):
    """Test 3: Verify 'upload' stage status in database."""
    _run_stage_db_verify_test(host, "upload", 12)


# =============================================================================
# TEST 4-5: PARSE-CATALOG STAGE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(13)
def test_stage_parse_catalog_monitor(host):
    """Test 4: Monitor 'parse-catalog' stage until completion."""
    _run_stage_monitor_test(host, "parse-catalog", 13)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(14)
def test_stage_parse_catalog_db_verify(host):
    """Test 5: Verify 'parse-catalog' stage status in database."""
    _run_stage_db_verify_test(host, "parse-catalog", 14)


# =============================================================================
# TEST 6-7: GENERATE-INPUT-FILES STAGE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(15)
def test_stage_generate_input_files_monitor(host):
    """Test 6: Monitor 'generate-input-files' stage until completion."""
    _run_stage_monitor_test(host, "generate-input-files", 15)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(16)
def test_stage_generate_input_files_db_verify(host):
    """Test 7: Verify 'generate-input-files' stage status in database."""
    _run_stage_db_verify_test(host, "generate-input-files", 16)


# =============================================================================
# TEST 8-9: CREATE-LOCAL-REPOSITORY STAGE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(17)
def test_stage_create_local_repository_monitor(host):
    """Test 8: Monitor 'create-local-repository' stage until completion."""
    _run_stage_monitor_test(host, "create-local-repository", 17)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(18)
def test_stage_create_local_repository_db_verify(host):
    """Test 9: Verify 'create-local-repository' stage status in database."""
    _run_stage_db_verify_test(host, "create-local-repository", 18)


# =============================================================================
# TEST 10-11: BUILD-IMAGE-X86_64 STAGE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(19)
def test_stage_build_image_x86_64_monitor(host):
    """Test 10: Monitor 'build-image-x86_64' stage until completion."""
    _run_stage_monitor_test(host, "build-image-x86_64", 19)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(20)
def test_stage_build_image_x86_64_db_verify(host):
    """Test 11: Verify 'build-image-x86_64' stage status in database."""
    _run_stage_db_verify_test(host, "build-image-x86_64", 20)


# =============================================================================
# TEST 12-13: BUILD-IMAGE-AARCH64 STAGE (dynamic — only if aarch64 in catalog)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(21)
def test_stage_build_image_aarch64_monitor(host):
    """Test 12: Monitor 'build-image-aarch64' stage until completion (skipped if not in catalog)."""
    if "aarch64" not in _pipeline_state.get("catalog_architectures", []):
        log = TestLogger(TEST_NAMES["stage_monitor"].format(stage="build-image-aarch64"))
        log.skipped(
            "aarch64 not in catalog architectures",
            f"Architectures: {_pipeline_state.get('catalog_architectures', [])}"
        )
        pytest.skip("aarch64 not in catalog architectures")
    _run_stage_monitor_test(host, "build-image-aarch64", 21)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(22)
def test_stage_build_image_aarch64_db_verify(host):
    """Test 13: Verify 'build-image-aarch64' stage in database (skipped if not in catalog)."""
    if "aarch64" not in _pipeline_state.get("catalog_architectures", []):
        log = TestLogger(TEST_NAMES["stage_db_verify"].format(stage="build-image-aarch64"))
        log.skipped(
            "aarch64 not in catalog architectures",
            f"Architectures: {_pipeline_state.get('catalog_architectures', [])}"
        )
        pytest.skip("aarch64 not in catalog architectures")
    _run_stage_db_verify_test(host, "build-image-aarch64", 22)


# =============================================================================
# TEST 14: IMAGE GROUPS CREATED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(23)
def test_image_groups_created(host):
    """Test 14: Verify image groups were created for the job."""
    log = TestLogger(TEST_NAMES["image_groups_created"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_triggered(log)

    if _any_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "Build pipeline had failures")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _pipeline_state["job_id"]
    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check(f"Checking image groups for job {job_id}")

    result = get_image_groups_for_job(host, job_id)

    if result["success"] and result["image_groups"]:
        details_lines = [f"Found {len(result['image_groups'])} image group(s):"]
        for group in result["image_groups"]:
            details_lines.append(
                f"  ✓ {group['id']} (status: {group['status']})"
            )
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


# =============================================================================
# TEST 15: IMAGES CREATED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(24)
def test_images_created(host):
    """Test 15: Verify images were created for the job."""
    log = TestLogger(TEST_NAMES["images_created"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_triggered(log)

    if _any_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "Build pipeline had failures")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _pipeline_state["job_id"]
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


# =============================================================================
# TEST 16: REGISTRY IMAGES VERIFICATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(25)
def test_registry_images(host):
    """Test 16: Verify container images exist in registry for all roles."""
    log = TestLogger(TEST_NAMES["registry_images"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_triggered(log)

    if _any_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "Build pipeline had failures")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _pipeline_state["job_id"]
    roles = _pipeline_state.get("catalog_roles", [])
    image_key = _pipeline_state.get("catalog_image_key", "")

    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    if not roles:
        roles_result = get_catalog_roles(host, job_id)
        if roles_result["success"]:
            roles = roles_result["roles"]
            image_key = roles_result["image_key"]
            _pipeline_state["catalog_roles"] = roles
            _pipeline_state["catalog_image_key"] = image_key

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


# =============================================================================
# TEST 17: S3 BOOT IMAGES VERIFICATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(26)
def test_s3_boot_images(host):
    """Test 17: Verify S3 boot images (rootfs + EFI) exist for all roles."""
    log = TestLogger(TEST_NAMES["s3_boot_images"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_triggered(log)

    if _any_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "Build pipeline had failures")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _pipeline_state["job_id"]
    roles = _pipeline_state.get("catalog_roles", [])
    image_key = _pipeline_state.get("catalog_image_key", "")

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


# =============================================================================
# TEST 18: BUILD PIPELINE FINAL RESULT
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.build
@pytest.mark.order(27)
def test_build_pipeline_result(host):
    """Test 18: Summarize pipeline result — pass if all stages passed, fail otherwise."""
    log = TestLogger(TEST_NAMES["build_pipeline_result"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_triggered(log)

    log.check("Evaluating build pipeline final result")

    stages = _get_active_stages()
    completed = []
    failed = []
    skipped = []

    for stage in stages:
        if stage in _pipeline_state["stage_results"]:
            r = _pipeline_state["stage_results"][stage]
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
        if stage in _pipeline_state["stage_results"]:
            state = _pipeline_state["stage_results"][stage].get("stage_state", "?")
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
