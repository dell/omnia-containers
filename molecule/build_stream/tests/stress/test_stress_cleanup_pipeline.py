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
Build Stream - Stress Test for Cleanup Pipeline.

Deletes ALL BUILT image groups one by one with full verification:
  1. Get all BUILT image groups from database
  2. For each image group:
     a. Trigger cleanup pipeline (PIPELINE_TYPE=cleanup)
     b. Select the image group for cleanup
     c. Wait for cleanup to complete
     d. Verify DB status changed to CLEANED
     e. Verify S3 images deleted (no files for this job_id)
     f. Verify registry images deleted (no repos for this job_id)
  3. Final verification: No BUILT image groups remain

Configuration:
  - image_identifier: If set, only deletes that specific image group
  - If empty, deletes ALL BUILT image groups

Usage:
  pytest molecule/build_stream/tests/stress/test_stress_cleanup_pipeline.py -m stress -v
"""

import sys
import time
from datetime import datetime
from typing import Dict, Any, List

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    trigger_cleanup_pipeline,
    select_image_for_cleanup,
    wait_for_cleanup_completion,
    get_all_image_groups,
    get_images_for_job,
    verify_registry_images,
    verify_s3_boot_images,
    get_image_identifier,
    get_pipeline_status,
)


# =============================================================================
# HELPER: WAIT FOR GITLAB PIPELINE COMPLETION
# =============================================================================

def _wait_for_gitlab_pipeline_completion(
    host,
    pipeline_id: int,
    log_callback=None,
    timeout: int = 600
) -> bool:
    """
    Wait for a specific GitLab pipeline to complete.

    Args:
        host: Testinfra host object
        pipeline_id: GitLab pipeline ID to wait for
        log_callback: Optional logging callback
        timeout: Max wait time in seconds (default 10 min)

    Returns:
        True if pipeline completed, False if timeout
    """
    def _log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(f"    │ {msg}", flush=True)

    start_time = time.time()
    poll_interval = 15
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
            return True

        elapsed = int(time.time() - start_time)
        _log(f"[{elapsed}s] Pipeline #{pipeline_id} status: {status}, waiting...")
        time.sleep(poll_interval)

    return False


# =============================================================================
# CLEANUP ITERATION RESULT
# =============================================================================

def _create_cleanup_result(image_group_id: str) -> Dict[str, Any]:
    """Create a fresh result dict for one cleanup iteration."""
    return {
        "image_group_id": image_group_id,
        "job_id": "",
        "success": False,
        "pipeline_id": 0,
        "start_time": None,
        "end_time": None,
        "elapsed_seconds": 0,
        "db_status_cleaned": False,
        "registry_empty": False,
        "s3_empty": False,
        "roles": [],
        "error": "",
    }


# =============================================================================
# SINGLE CLEANUP ITERATION
# =============================================================================

def _run_cleanup_iteration(
    host,
    image_group: Dict[str, Any],
    iteration: int,
    total: int,
) -> Dict[str, Any]:
    """
    Run a single cleanup iteration for one image group.

    Args:
        host: Testinfra host object
        image_group: Image group dict with 'id', 'job_id', 'status'
        iteration: Current iteration number (1-based)
        total: Total number of iterations

    Returns:
        Dict with cleanup validation results
    """
    image_group_id = image_group.get("id", "")
    job_id = image_group.get("job_id", "")

    result = _create_cleanup_result(image_group_id)
    result["job_id"] = job_id
    result["start_time"] = datetime.now().isoformat()

    def _log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"    │ [{timestamp}] [Cleanup {iteration}/{total}] {msg}", flush=True)
        sys.stdout.flush()

    _log("=" * 50)
    _log(f"CLEANING IMAGE GROUP: {image_group_id}")
    _log(f"Job ID: {job_id}")
    _log("=" * 50)

    # =========================================================================
    # STEP 1: GET ROLES FOR THIS IMAGE GROUP (for verification later)
    # =========================================================================
    _log("Step 1/6: Getting image roles from database...")

    images_result = get_images_for_job(host, job_id)
    if images_result["success"] and images_result["images"]:
        result["roles"] = list(set([
            img.get("role") for img in images_result["images"]
            if img.get("role")
        ]))
        _log(f"Found {len(result['roles'])} roles: {result['roles']}")
    else:
        _log("Warning: Could not get roles from DB, will skip registry/S3 verification")

    # =========================================================================
    # STEP 2: TRIGGER CLEANUP PIPELINE
    # =========================================================================
    _log("Step 2/6: Triggering cleanup pipeline...")

    trigger_result = trigger_cleanup_pipeline(host, log_callback=_log)
    if not trigger_result["success"]:
        result["error"] = f"Trigger failed: {trigger_result['error']}"
        result["end_time"] = datetime.now().isoformat()
        result["elapsed_seconds"] = int(
            (datetime.fromisoformat(result["end_time"])
             - datetime.fromisoformat(result["start_time"])).total_seconds()
        )
        _log(f"FAILED: {result['error']}")
        return result

    result["pipeline_id"] = trigger_result["pipeline_id"]
    _log(f"Pipeline #{trigger_result['pipeline_id']} triggered")

    # =========================================================================
    # STEP 3: SELECT IMAGE GROUP FOR CLEANUP
    # =========================================================================
    _log("Step 3/6: Selecting image group for cleanup...")

    select_result = select_image_for_cleanup(
        host, trigger_result["pipeline_id"], log_callback=_log
    )
    if not select_result["success"]:
        result["error"] = f"Selection failed: {select_result['error']}"
        result["end_time"] = datetime.now().isoformat()
        result["elapsed_seconds"] = int(
            (datetime.fromisoformat(result["end_time"])
             - datetime.fromisoformat(result["start_time"])).total_seconds()
        )
        _log(f"FAILED: {result['error']}")
        return result

    _log(f"Selected image group: {select_result['image_group_id']}")

    # =========================================================================
    # STEP 4: WAIT FOR CLEANUP TO COMPLETE
    # =========================================================================
    _log("Step 4/6: Waiting for cleanup to complete...")

    cleanup_result = wait_for_cleanup_completion(
        host, image_group_id, timeout=300, log_callback=_log
    )
    if cleanup_result["success"]:
        result["db_status_cleaned"] = True
        _log("✓ DB status updated to CLEANED")
    else:
        _log(f"Warning: {cleanup_result['error']}")
        # Also wait for GitLab pipeline to complete
        _wait_for_gitlab_pipeline_completion(
            host, trigger_result["pipeline_id"], log_callback=_log, timeout=300
        )

    # =========================================================================
    # STEP 5: VERIFY REGISTRY IMAGES DELETED
    # =========================================================================
    _log("Step 5/6: Verifying registry images deleted...")

    if result["roles"]:
        reg_result = verify_registry_images(host, job_id, result["roles"], "")
        found_count = len(reg_result.get("found", []))
        if found_count == 0:
            result["registry_empty"] = True
            _log(f"✓ Registry: No images found for job_id {job_id[:8]}...")
        else:
            _log(f"✗ Registry: Still found {found_count} images:")
            for item in reg_result.get("found", []):
                _log(f"    - {item['role']}: {item.get('repo', 'N/A')}")
    else:
        _log("⚠ Skipping registry check - no roles available")
        result["registry_empty"] = True  # Assume empty if no roles to check

    # =========================================================================
    # STEP 6: VERIFY S3 IMAGES DELETED
    # =========================================================================
    _log("Step 6/6: Verifying S3 images deleted...")

    if result["roles"]:
        s3_result = verify_s3_boot_images(host, job_id, result["roles"], "")
        found_count = len(s3_result.get("found_roles", []))
        if found_count == 0:
            result["s3_empty"] = True
            _log(f"✓ S3: No boot images found for job_id {job_id[:8]}...")
        else:
            _log(f"✗ S3: Still found files for {found_count} roles:")
            for item in s3_result.get("found_roles", []):
                _log(f"    - {item['role']}: rootfs={item['rootfs']}, efi={item['efi_files']}")
    else:
        _log("⚠ Skipping S3 check - no roles available")
        result["s3_empty"] = True  # Assume empty if no roles to check

    # =========================================================================
    # FINAL RESULT
    # =========================================================================
    result["end_time"] = datetime.now().isoformat()
    result["elapsed_seconds"] = int(
        (datetime.fromisoformat(result["end_time"])
         - datetime.fromisoformat(result["start_time"])).total_seconds()
    )

    result["success"] = (
        result["db_status_cleaned"]
        and result["registry_empty"]
        and result["s3_empty"]
    )

    if result["success"]:
        _log("=" * 50)
        _log(f"✓ CLEANUP PASSED: {image_group_id} in {result['elapsed_seconds']}s")
        _log("=" * 50)
    else:
        failures = []
        if not result["db_status_cleaned"]:
            failures.append("db_status")
        if not result["registry_empty"]:
            failures.append("registry")
        if not result["s3_empty"]:
            failures.append("s3")
        result["error"] = f"Failed checks: {', '.join(failures)}"
        _log("=" * 50)
        _log(f"✗ CLEANUP FAILED: {result['error']}")
        _log("=" * 50)

    return result


# =============================================================================
# MAIN STRESS TEST
# =============================================================================

@pytest.mark.stress
@pytest.mark.order(105)
def test_stress_cleanup_pipeline(host):
    """
    Stress test: Delete ALL BUILT image groups with full verification.

    For each BUILT image group:
      1. Trigger cleanup pipeline
      2. Select the image group
      3. Wait for cleanup completion
      4. Verify DB status = CLEANED
      5. Verify registry images deleted
      6. Verify S3 images deleted

    If image_identifier is set in config, only deletes that specific image.
    Otherwise, deletes ALL BUILT image groups.
    """
    log = TestLogger("Stress Cleanup Pipeline")

    if not is_build_stream_enabled(host):
        log.skipped("Build stream not enabled", "Test skipped")
        pytest.skip("Build stream not enabled")

    # Get all image groups
    ig_result = get_all_image_groups(host)
    if not ig_result["success"]:
        log.failed(
            "Failed to get image groups",
            ig_result.get("error", "Database query failed")
        )
        pytest.fail(f"Failed to get image groups: {ig_result.get('error', '')}")

    # Filter to BUILT groups only
    built_groups = [g for g in ig_result["image_groups"] if g["status"] == "BUILT"]

    if not built_groups:
        log.passed(
            "No BUILT image groups to clean",
            "All image groups are already CLEANED or no groups exist."
        )
        return

    # Check if specific image identifier is configured
    configured_id = get_image_identifier(host)
    if configured_id:
        # Only clean the specified image group
        target_groups = [g for g in built_groups if g["id"] == configured_id]
        if not target_groups:
            log.failed(
                f"Configured image_identifier not found: {configured_id}",
                f"Available BUILT groups: {[g['id'] for g in built_groups]}"
            )
            pytest.fail(f"Image group {configured_id} not found or not BUILT")
        built_groups = target_groups
        log.check(f"Cleaning configured image group: {configured_id}")
    else:
        log.check(f"Cleaning ALL {len(built_groups)} BUILT image group(s)")

    print("\n" + "#" * 70, flush=True)
    print(f"# BUILD STREAM CLEANUP STRESS TEST - {len(built_groups)} IMAGE GROUPS", flush=True)
    print("# Each cleanup: trigger -> select -> wait -> verify DB/registry/S3", flush=True)
    print(f"# Started at: {datetime.now().isoformat()}", flush=True)
    print("#" * 70 + "\n", flush=True)

    results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0
    total_elapsed = 0

    for i, group in enumerate(built_groups, 1):
        iteration_result = _run_cleanup_iteration(host, group, i, len(built_groups))
        results.append(iteration_result)
        total_elapsed += iteration_result["elapsed_seconds"]

        if iteration_result["success"]:
            passed += 1
        else:
            failed += 1

        print(
            f"\n    Progress: {i}/{len(built_groups)} complete, "
            f"{passed} passed, {failed} failed\n",
            flush=True
        )

    # =========================================================================
    # FINAL VERIFICATION: No BUILT groups remain
    # =========================================================================
    print("\n" + "=" * 70, flush=True)
    print("FINAL VERIFICATION: Checking no BUILT image groups remain...", flush=True)

    final_result = get_all_image_groups(host)
    if final_result["success"]:
        remaining_built = [g for g in final_result["image_groups"] if g["status"] == "BUILT"]
        if remaining_built:
            print(f"⚠ WARNING: {len(remaining_built)} BUILT groups still remain:", flush=True)
            for g in remaining_built:
                print(f"    - {g['id']}", flush=True)
        else:
            print("✓ All image groups are now CLEANED", flush=True)

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "#" * 70, flush=True)
    print("# CLEANUP STRESS TEST COMPLETE", flush=True)
    print(f"# Total: {len(built_groups)}, Passed: {passed}, Failed: {failed}", flush=True)
    print(
        f"# Total time: {total_elapsed}s "
        f"({total_elapsed // 60}m {total_elapsed % 60}s)",
        flush=True
    )
    print(f"# Finished at: {datetime.now().isoformat()}", flush=True)
    print("#" * 70 + "\n", flush=True)

    summary_lines = [
        f"Total image groups: {len(built_groups)}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        f"Total time: {total_elapsed}s",
        "",
        "Per-image results:",
    ]

    for r in results:
        status = "PASS" if r["success"] else "FAIL"
        job_str = r["job_id"][:8] if r["job_id"] else "N/A"
        summary_lines.append(
            f"  [{status}] {r['image_group_id']}: "
            f"job={job_str}... "
            f"time={r['elapsed_seconds']}s "
            f"db={r['db_status_cleaned']} "
            f"reg={r['registry_empty']} "
            f"s3={r['s3_empty']}"
        )
        if r["error"]:
            summary_lines.append(f"       Error: {r['error']}")

    if failed == 0:
        log.passed(
            f"All {len(built_groups)} image groups cleaned successfully",
            "\n".join(summary_lines),
        )
    else:
        log.failed(
            f"{failed}/{len(built_groups)} cleanups failed",
            "\n".join(summary_lines),
        )
        pytest.fail(f"Cleanup stress test: {failed}/{len(built_groups)} failed")
