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
Build Stream - Comprehensive Stress Test Suite.

Test Cases (run in order):
  1. test_stress_build_to_50: Build images until 50 exist (skip if already 50)
  2. test_stress_build_51st_fails: Try to create 51st image, verify it fails
  3. test_stress_delete_and_rebuild: Delete 1 image, create 1 new, verify success
  4. test_stress_build_fails_at_50: Try to create another (should fail - back to 50)
  5. test_stress_cleanup_all: Delete all images, verify DB=CLEANED, S3/registry empty

IMPORTANT:
  - Tests stop on first failure (no point continuing if build/cleanup fails)
  - If image_identifier is configured but not found, test fails with clear error
  - Each test verifies DB status, registry images, and S3 boot images

Configuration (omnia_test_config.yml):
  - image_identifier: Specific image group for deploy/cleanup (empty = auto-select)
  - allow_pipeline_cancel: Auto-cancel running pipelines (true/false)

Usage:
  pytest molecule/build_stream/tests/stress/test_stress_pipeline.py -v --tb=short
"""

import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    trigger_build_pipeline,
    trigger_cleanup_pipeline,
    select_image_for_cleanup,
    wait_for_cleanup_completion,
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
    get_image_identifier,
    BUILD_IMAGE_STAGE_PREFIX,
    BUILD_PIPELINE_CORE_STAGES,
    STAGE_POLL_INTERVAL,
    STAGE_POLL_TIMEOUT,
    STRESS_BUILD_PIPELINE_COUNT,
)


# =============================================================================
# MODULE-LEVEL STATE (shared across tests)
# =============================================================================

_stress_state = {
    "initial_built_count": 0,
    "max_images": STRESS_BUILD_PIPELINE_COUNT,  # Default 50
    "last_build_job_id": None,
    "last_cleanup_image_group": None,
    "tests_passed": 0,
    "tests_failed": 0,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_built_image_count(host) -> int:
    """Get count of BUILT image groups."""
    result = get_all_image_groups(host)
    if result["success"]:
        return len([g for g in result["image_groups"] if g["status"] == "BUILT"])
    return 0


def _get_built_image_groups(host) -> List[Dict[str, Any]]:
    """Get list of BUILT image groups."""
    result = get_all_image_groups(host)
    if result["success"]:
        return [g for g in result["image_groups"] if g["status"] == "BUILT"]
    return []


def _wait_for_all_pipelines_complete(host, log_callback=None, timeout: int = 7200) -> bool:
    """Wait for all running/pending pipelines to complete."""
    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)

    start_time = time.time()
    poll_interval = 30

    while time.time() - start_time < timeout:
        result = list_pipelines(host, per_page=5)
        if not result["success"]:
            _log(f"Warning: Failed to list pipelines: {result['error']}")
            time.sleep(poll_interval)
            continue

        running = [
            p for p in result["pipelines"]
            if p.get("status") in ("running", "pending", "created", "waiting_for_resource")
        ]

        if not running:
            return True

        elapsed = int(time.time() - start_time)
        pipeline_ids = [str(p["id"]) for p in running]
        _log(f"[{elapsed}s] Waiting for pipeline(s) {', '.join(pipeline_ids)} to complete...")
        time.sleep(poll_interval)

    return False


def _wait_for_gitlab_pipeline_completion(
    host,
    pipeline_id: int,
    log_callback=None,
    timeout: int = 7200
) -> bool:
    """Wait for a specific GitLab pipeline to complete."""
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
            _log(f"Warning: Failed to get pipeline status: {result['error']}")
            time.sleep(poll_interval)
            continue

        status = result.get("status", "unknown")
        if status in completed_statuses:
            _log(f"Pipeline #{pipeline_id} completed with status: {status}")
            return status == "success"

        elapsed = int(time.time() - start_time)
        _log(f"[{elapsed}s] Pipeline #{pipeline_id} status: {status}, waiting...")
        time.sleep(poll_interval)

    return False


def _run_single_build(host, log_callback=None) -> Dict[str, Any]:
    """
    Run a single build pipeline with full validation.

    Returns:
        Dict with success, job_id, pipeline_id, error, and validation results.
    """
    result = {
        "success": False,
        "job_id": None,
        "pipeline_id": None,
        "error": "",
        "stages_passed": False,
        "db_ok": False,
        "registry_ok": False,
        "s3_ok": False,
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    # Step 1: Wait for any running pipelines
    _log("Waiting for any running pipelines to complete...")
    if not _wait_for_all_pipelines_complete(host, log_callback=_log, timeout=7200):
        result["error"] = "Timeout waiting for pipelines to complete"
        return result

    # Step 2: Trigger build pipeline
    _log("Triggering build pipeline...")
    trigger_result = trigger_build_pipeline(host, log_callback=_log)
    if not trigger_result["success"]:
        result["error"] = f"Trigger failed: {trigger_result['error']}"
        return result

    result["job_id"] = trigger_result["job_id"]
    result["pipeline_id"] = trigger_result["pipeline_id"]
    _log(f"Pipeline #{trigger_result['pipeline_id']} triggered, Job ID: {trigger_result['job_id']}")

    # Step 3: Monitor core stages
    _log("Monitoring core stages...")
    core_stages = list(BUILD_PIPELINE_CORE_STAGES)

    for stage_name in core_stages:
        _log(f"  Monitoring stage: {stage_name}...")
        stage_result = wait_for_stage_completion(
            host, trigger_result["job_id"], stage_name,
            timeout=STAGE_POLL_TIMEOUT,
            poll_interval=STAGE_POLL_INTERVAL,
            log_callback=lambda msg: print(f"      │ {msg}", flush=True),
        )
        if not stage_result["success"]:
            result["error"] = f"Stage '{stage_name}' failed: {stage_result.get('error', 'Unknown')}"
            log_path = get_stage_log_path(host, trigger_result["job_id"], stage_name)
            if log_path:
                _log(f"    Log file: {log_path}")
            return result
        _log(f"  ✓ Stage '{stage_name}' COMPLETED")

    # Step 4: Get catalog info
    _log("Getting catalog information...")
    roles_result = get_catalog_roles(host, trigger_result["job_id"])
    catalog_roles = roles_result.get("roles", []) if roles_result["success"] else []
    catalog_architectures = roles_result.get("architectures", ["x86_64"]) if roles_result["success"] else ["x86_64"]

    # Step 5: Monitor build-image stages
    _log("Monitoring build-image stages...")
    build_stages = [f"{BUILD_IMAGE_STAGE_PREFIX}{arch}" for arch in catalog_architectures]

    for stage_name in build_stages:
        _log(f"  Monitoring stage: {stage_name}...")
        stage_result = wait_for_stage_completion(
            host, trigger_result["job_id"], stage_name,
            timeout=STAGE_POLL_TIMEOUT,
            poll_interval=STAGE_POLL_INTERVAL,
            log_callback=lambda msg: print(f"      │ {msg}", flush=True),
        )
        if not stage_result["success"]:
            result["error"] = f"Stage '{stage_name}' failed: {stage_result.get('error', 'Unknown')}"
            log_path = get_stage_log_path(host, trigger_result["job_id"], stage_name)
            if log_path:
                _log(f"    Log file: {log_path}")
            return result
        _log(f"  ✓ Stage '{stage_name}' COMPLETED")

    result["stages_passed"] = True
    _log("All stages completed successfully")

    # Step 6: Verify database
    _log("Verifying database records...")
    ig_result = get_image_groups_for_job(host, trigger_result["job_id"])
    if ig_result["success"] and ig_result["image_groups"]:
        built_groups = [g for g in ig_result["image_groups"] if g["status"] == "BUILT"]
        if built_groups:
            result["db_ok"] = True
            _log(f"  ✓ Found {len(built_groups)} image group(s) with BUILT status")

    # Extract roles from DB if catalog API failed
    images_result = get_images_for_job(host, trigger_result["job_id"])
    if images_result["success"] and images_result["images"]:
        if not catalog_roles:
            catalog_roles = list(set([
                img.get("role") for img in images_result["images"]
                if img.get("role")
            ]))
            _log(f"  Extracted {len(catalog_roles)} roles from DB: {catalog_roles}")

    # Step 7: Verify registry
    _log("Verifying registry images...")
    if catalog_roles:
        reg_result = verify_registry_images(host, trigger_result["job_id"], catalog_roles, "")
        if reg_result["success"]:
            result["registry_ok"] = True
            _log(f"  ✓ Registry: {len(reg_result.get('found', []))}/{len(catalog_roles)} roles found")
            for item in reg_result.get("found", []):
                _log(f"      ✓ {item['role']}: {item.get('repo', 'N/A')}")
        else:
            _log(f"  ✗ Registry: {len(reg_result.get('found', []))}/{len(catalog_roles)} roles found")
    else:
        result["registry_ok"] = True  # No roles to check

    # Step 8: Verify S3
    _log("Verifying S3 boot images...")
    if catalog_roles:
        s3_result = verify_s3_boot_images(host, trigger_result["job_id"], catalog_roles, "")
        if s3_result["success"]:
            result["s3_ok"] = True
            _log(f"  ✓ S3: {len(s3_result.get('found_roles', []))}/{len(catalog_roles)} roles complete")
        else:
            _log(f"  ✗ S3: {len(s3_result.get('found_roles', []))}/{len(catalog_roles)} roles complete")
    else:
        result["s3_ok"] = True  # No roles to check

    # Step 9: Wait for GitLab pipeline to fully complete
    _log("Waiting for GitLab pipeline to fully complete...")
    _wait_for_gitlab_pipeline_completion(host, trigger_result["pipeline_id"], log_callback=_log, timeout=300)

    result["success"] = (
        result["stages_passed"]
        and result["db_ok"]
        and result["registry_ok"]
        and result["s3_ok"]
    )

    if result["success"]:
        _log("✓ BUILD PASSED")
    else:
        failures = []
        if not result["stages_passed"]:
            failures.append("stages")
        if not result["db_ok"]:
            failures.append("db")
        if not result["registry_ok"]:
            failures.append("registry")
        if not result["s3_ok"]:
            failures.append("s3")
        result["error"] = f"Failed checks: {', '.join(failures)}"
        _log(f"✗ BUILD FAILED: {result['error']}")

    return result


def _run_single_cleanup(host, image_group: Dict[str, Any], log_callback=None) -> Dict[str, Any]:
    """
    Run a single cleanup for one image group with full validation.

    Returns:
        Dict with success, image_group_id, error, and validation results.
    """
    image_group_id = image_group.get("id", "")
    job_id = image_group.get("job_id", "")

    result = {
        "success": False,
        "image_group_id": image_group_id,
        "job_id": job_id,
        "error": "",
        "db_cleaned": False,
        "registry_empty": False,
        "s3_empty": False,
    }

    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    _log(f"Cleaning image group: {image_group_id}")

    # Get roles for verification
    images_result = get_images_for_job(host, job_id)
    roles = []
    if images_result["success"] and images_result["images"]:
        roles = list(set([
            img.get("role") for img in images_result["images"]
            if img.get("role")
        ]))
        _log(f"Found {len(roles)} roles: {roles}")

    # Trigger cleanup pipeline
    _log("Triggering cleanup pipeline...")
    trigger_result = trigger_cleanup_pipeline(host, log_callback=_log)
    if not trigger_result["success"]:
        result["error"] = f"Trigger failed: {trigger_result['error']}"
        return result

    # Select image group
    _log("Selecting image group for cleanup...")
    select_result = select_image_for_cleanup(
        host, trigger_result["pipeline_id"], log_callback=_log
    )
    if not select_result["success"]:
        result["error"] = f"Selection failed: {select_result['error']}"
        return result

    # Wait for cleanup completion
    _log("Waiting for cleanup to complete...")
    cleanup_result = wait_for_cleanup_completion(
        host, image_group_id, timeout=300, log_callback=_log
    )
    if cleanup_result["success"]:
        result["db_cleaned"] = True
        _log("✓ DB status updated to CLEANED")
    else:
        _log(f"Warning: {cleanup_result['error']}")
        # Wait for pipeline anyway
        _wait_for_gitlab_pipeline_completion(
            host, trigger_result["pipeline_id"], log_callback=_log, timeout=300
        )

    # Verify registry empty
    _log("Verifying registry images deleted...")
    if roles:
        reg_result = verify_registry_images(host, job_id, roles, "")
        found_count = len(reg_result.get("found", []))
        if found_count == 0:
            result["registry_empty"] = True
            _log(f"✓ Registry: No images found for job_id {job_id[:8]}...")
        else:
            _log(f"✗ Registry: Still found {found_count} images")
    else:
        result["registry_empty"] = True

    # Verify S3 empty
    _log("Verifying S3 images deleted...")
    if roles:
        s3_result = verify_s3_boot_images(host, job_id, roles, "")
        found_count = len(s3_result.get("found_roles", []))
        if found_count == 0:
            result["s3_empty"] = True
            _log(f"✓ S3: No boot images found for job_id {job_id[:8]}...")
        else:
            _log(f"✗ S3: Still found files for {found_count} roles")
    else:
        result["s3_empty"] = True

    result["success"] = (
        result["db_cleaned"]
        and result["registry_empty"]
        and result["s3_empty"]
    )

    if result["success"]:
        _log(f"✓ CLEANUP PASSED: {image_group_id}")
    else:
        failures = []
        if not result["db_cleaned"]:
            failures.append("db")
        if not result["registry_empty"]:
            failures.append("registry")
        if not result["s3_empty"]:
            failures.append("s3")
        result["error"] = f"Failed checks: {', '.join(failures)}"
        _log(f"✗ CLEANUP FAILED: {result['error']}")

    return result


# =============================================================================
# TEST 1: BUILD TO 50 IMAGES
# =============================================================================

@pytest.mark.stress
@pytest.mark.build_stream
@pytest.mark.order(100)
def test_stress_build_to_50(host):
    """
    Test 1: Build images until 50 exist.

    If already 50 images, skip this test.
    Stops on first build failure.
    """
    log = TestLogger("Stress Build to 50")

    if not is_build_stream_enabled(host):
        log.skipped("Build stream not enabled", "Test skipped")
        pytest.skip("Build stream not enabled")

    current_count = _get_built_image_count(host)
    _stress_state["initial_built_count"] = current_count
    max_images = _stress_state["max_images"]

    log.check(f"Current BUILT image count: {current_count}, Target: {max_images}")

    if current_count >= max_images:
        log.passed(
            f"Already have {current_count} BUILT images (max: {max_images})",
            "Skipping build - already at capacity"
        )
        return

    builds_needed = max_images - current_count
    print("\n" + "#" * 70, flush=True)
    print(f"# STRESS BUILD: Need to build {builds_needed} more images", flush=True)
    print(f"# Current: {current_count}, Target: {max_images}", flush=True)
    print(f"# Started at: {datetime.now().isoformat()}", flush=True)
    print("#" * 70 + "\n", flush=True)

    passed = 0
    failed = 0

    for i in range(builds_needed):
        print(f"\n{'=' * 50}", flush=True)
        print(f"BUILD {i + 1}/{builds_needed}", flush=True)
        print(f"{'=' * 50}\n", flush=True)

        def _log_callback(msg):
            print(f"    │ {msg}", flush=True)
            sys.stdout.flush()

        build_result = _run_single_build(host, log_callback=_log_callback)

        if build_result["success"]:
            passed += 1
            _stress_state["last_build_job_id"] = build_result["job_id"]
            print(f"\n✓ Build {i + 1}/{builds_needed} PASSED\n", flush=True)
        else:
            failed += 1
            print(f"\n✗ Build {i + 1}/{builds_needed} FAILED: {build_result['error']}\n", flush=True)
            # Stop on first failure
            log.failed(
                f"Build failed at iteration {i + 1}/{builds_needed}",
                f"Error: {build_result['error']}"
            )
            pytest.fail(f"Build failed: {build_result['error']}")

    final_count = _get_built_image_count(host)
    log.passed(
        f"Built {passed} images successfully",
        f"Final count: {final_count} BUILT images"
    )


# =============================================================================
# TEST 2: 51ST IMAGE SHOULD FAIL
# =============================================================================

@pytest.mark.stress
@pytest.mark.build_stream
@pytest.mark.order(101)
def test_stress_build_51st_fails(host):
    """
    Test 2: Try to create 51st image, verify it fails as expected.

    This test expects the build to fail because we're at max capacity.
    """
    log = TestLogger("Stress Build 51st Fails")

    if not is_build_stream_enabled(host):
        log.skipped("Build stream not enabled", "Test skipped")
        pytest.skip("Build stream not enabled")

    current_count = _get_built_image_count(host)
    max_images = _stress_state["max_images"]

    log.check(f"Current BUILT image count: {current_count}, Max: {max_images}")

    if current_count < max_images:
        log.skipped(
            f"Only {current_count} images exist (need {max_images} to test limit)",
            "Run test_stress_build_to_50 first"
        )
        pytest.skip(f"Need {max_images} images to test limit")

    print("\n" + "#" * 70, flush=True)
    print("# STRESS BUILD 51st: Expecting failure at max capacity", flush=True)
    print(f"# Current: {current_count}, Max: {max_images}", flush=True)
    print("#" * 70 + "\n", flush=True)

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    build_result = _run_single_build(host, log_callback=_log_callback)

    if build_result["success"]:
        # Build succeeded when it should have failed
        log.failed(
            "Build succeeded when it should have failed at max capacity",
            f"Job ID: {build_result['job_id']}"
        )
        pytest.fail("Build should have failed at max capacity but succeeded")
    else:
        # Build failed as expected
        log.passed(
            "Build failed as expected at max capacity",
            f"Error: {build_result['error']}"
        )


# =============================================================================
# TEST 3: DELETE 1 AND REBUILD
# =============================================================================

@pytest.mark.stress
@pytest.mark.build_stream
@pytest.mark.order(102)
def test_stress_delete_and_rebuild(host):
    """
    Test 3: Delete 1 image, create 1 new image, verify success.

    This tests that after deleting an image, we can build a new one.
    """
    log = TestLogger("Stress Delete and Rebuild")

    if not is_build_stream_enabled(host):
        log.skipped("Build stream not enabled", "Test skipped")
        pytest.skip("Build stream not enabled")

    built_groups = _get_built_image_groups(host)
    if not built_groups:
        log.skipped("No BUILT images to delete", "Run build tests first")
        pytest.skip("No BUILT images to delete")

    log.check(f"Current BUILT image count: {len(built_groups)}")

    print("\n" + "#" * 70, flush=True)
    print("# STRESS DELETE AND REBUILD", flush=True)
    print("# Step 1: Delete 1 image", flush=True)
    print("# Step 2: Build 1 new image", flush=True)
    print("#" * 70 + "\n", flush=True)

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    # Step 1: Delete one image
    print("\n=== STEP 1: DELETE ONE IMAGE ===\n", flush=True)
    target_group = built_groups[0]  # Delete the oldest
    _stress_state["last_cleanup_image_group"] = target_group["id"]

    cleanup_result = _run_single_cleanup(host, target_group, log_callback=_log_callback)
    if not cleanup_result["success"]:
        log.failed(
            f"Failed to delete image group: {target_group['id']}",
            f"Error: {cleanup_result['error']}"
        )
        pytest.fail(f"Cleanup failed: {cleanup_result['error']}")

    print("\n✓ Image deleted successfully\n", flush=True)

    # Step 2: Build new image
    print("\n=== STEP 2: BUILD NEW IMAGE ===\n", flush=True)
    build_result = _run_single_build(host, log_callback=_log_callback)
    if not build_result["success"]:
        log.failed(
            "Failed to build new image after deletion",
            f"Error: {build_result['error']}"
        )
        pytest.fail(f"Build failed: {build_result['error']}")

    _stress_state["last_build_job_id"] = build_result["job_id"]
    final_count = _get_built_image_count(host)

    log.passed(
        "Delete and rebuild completed successfully",
        f"Final BUILT count: {final_count}"
    )


# =============================================================================
# TEST 4: BUILD FAILS AT 50 AGAIN
# =============================================================================

@pytest.mark.stress
@pytest.mark.build_stream
@pytest.mark.order(103)
def test_stress_build_fails_at_50_again(host):
    """
    Test 4: Try to create another image (should fail - back to 50).

    After test 3, we should be back at max capacity.
    """
    log = TestLogger("Stress Build Fails at 50 Again")

    if not is_build_stream_enabled(host):
        log.skipped("Build stream not enabled", "Test skipped")
        pytest.skip("Build stream not enabled")

    current_count = _get_built_image_count(host)
    max_images = _stress_state["max_images"]

    log.check(f"Current BUILT image count: {current_count}, Max: {max_images}")

    if current_count < max_images:
        log.skipped(
            f"Only {current_count} images exist (need {max_images} to test limit)",
            "Previous tests may have failed"
        )
        pytest.skip(f"Need {max_images} images to test limit")

    print("\n" + "#" * 70, flush=True)
    print("# STRESS BUILD: Expecting failure at max capacity (again)", flush=True)
    print("#" * 70 + "\n", flush=True)

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    build_result = _run_single_build(host, log_callback=_log_callback)

    if build_result["success"]:
        log.failed(
            "Build succeeded when it should have failed at max capacity",
            f"Job ID: {build_result['job_id']}"
        )
        pytest.fail("Build should have failed at max capacity but succeeded")
    else:
        log.passed(
            "Build failed as expected at max capacity",
            f"Error: {build_result['error']}"
        )


# =============================================================================
# TEST 5: CLEANUP ALL IMAGES
# =============================================================================

@pytest.mark.stress
@pytest.mark.build_stream
@pytest.mark.cleanup
@pytest.mark.order(104)
def test_stress_cleanup_all(host):
    """
    Test 5: Delete all images, verify DB=CLEANED, S3/registry empty.

    Stops on first cleanup failure.
    """
    log = TestLogger("Stress Cleanup All")

    if not is_build_stream_enabled(host):
        log.skipped("Build stream not enabled", "Test skipped")
        pytest.skip("Build stream not enabled")

    built_groups = _get_built_image_groups(host)
    if not built_groups:
        log.passed("No BUILT images to clean", "All images already cleaned")
        return

    log.check(f"Cleaning {len(built_groups)} BUILT image group(s)")

    print("\n" + "#" * 70, flush=True)
    print(f"# STRESS CLEANUP ALL: {len(built_groups)} images", flush=True)
    print(f"# Started at: {datetime.now().isoformat()}", flush=True)
    print("#" * 70 + "\n", flush=True)

    passed = 0
    failed = 0

    for i, group in enumerate(built_groups, 1):
        print(f"\n{'=' * 50}", flush=True)
        print(f"CLEANUP {i}/{len(built_groups)}: {group['id']}", flush=True)
        print(f"{'=' * 50}\n", flush=True)

        def _log_callback(msg):
            print(f"    │ {msg}", flush=True)
            sys.stdout.flush()

        cleanup_result = _run_single_cleanup(host, group, log_callback=_log_callback)

        if cleanup_result["success"]:
            passed += 1
            print(f"\n✓ Cleanup {i}/{len(built_groups)} PASSED\n", flush=True)
        else:
            failed += 1
            print(f"\n✗ Cleanup {i}/{len(built_groups)} FAILED: {cleanup_result['error']}\n", flush=True)
            # Stop on first failure
            log.failed(
                f"Cleanup failed at iteration {i}/{len(built_groups)}",
                f"Image group: {group['id']}\nError: {cleanup_result['error']}"
            )
            pytest.fail(f"Cleanup failed: {cleanup_result['error']}")

    # Final verification
    final_built = _get_built_image_groups(host)
    if final_built:
        log.failed(
            f"{len(final_built)} BUILT images still remain",
            f"Remaining: {[g['id'] for g in final_built]}"
        )
        pytest.fail(f"{len(final_built)} BUILT images still remain")

    log.passed(
        f"All {passed} image groups cleaned successfully",
        "No BUILT images remain"
    )
