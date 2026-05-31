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
Build Stream - Stress Test for Build Pipeline.

Runs the FULL build pipeline N times (default 50), with ALL validations:
  1. Wait for any running pipeline to complete (intelligent waiting)
  2. Trigger new pipeline (upload catalog to GitLab)
  3. Wait for new job_id in database
  4. Monitor ALL stages until completion
  5. Verify image_groups created in DB with status BUILT
  6. Verify images table has entries for each role
  7. Verify registry images exist (regctl)
  8. Verify S3 boot images exist (3 per role)

IMPORTANT: This test does NOT auto-cancel pipelines.
  - First iteration: If pipeline running, prompts user to cancel and re-run
  - Subsequent iterations: Waits for GitLab pipeline to complete before next

Configuration:
  - Default count: STRESS_BUILD_PIPELINE_COUNT (50) from build_stream_vars.py
  - Override via environment variable: BUILD_STRESS_COUNT=10

Usage:
  pytest molecule/build_stream/tests/stress/ -m stress -v
  BUILD_STRESS_COUNT=5 pytest molecule/build_stream/tests/stress/ -m stress -v
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    trigger_build_pipeline,
    wait_for_stage_completion,
    get_stage_log_path,
    get_catalog_roles,
    get_image_groups_for_job,
    get_images_for_job,
    verify_registry_images,
    verify_s3_boot_images,
    list_pipelines,
    get_pipeline_status,
    BUILD_IMAGE_STAGE_PREFIX,
    BUILD_PIPELINE_CORE_STAGES,
    STAGE_POLL_INTERVAL,
    STAGE_POLL_TIMEOUT,
    STRESS_BUILD_PIPELINE_COUNT,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

def _get_stress_count() -> int:
    """Get the number of stress iterations from env or default."""
    return int(os.environ.get("BUILD_STRESS_COUNT", STRESS_BUILD_PIPELINE_COUNT))


# =============================================================================
# HELPER: WAIT FOR GITLAB PIPELINE COMPLETION
# =============================================================================

def _wait_for_gitlab_pipeline_completion(
    host,
    pipeline_id: int,
    log_callback=None,
    timeout: int = 7200
) -> bool:
    """
    Wait for a specific GitLab pipeline to complete.

    Args:
        host: Testinfra host object
        pipeline_id: GitLab pipeline ID to wait for
        log_callback: Optional logging callback
        timeout: Max wait time in seconds (default 2 hours)

    Returns:
        True if pipeline completed (success or failed), False if timeout
    """
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
            return True

        elapsed = int(time.time() - start_time)
        _log(f"[{elapsed}s] Pipeline #{pipeline_id} status: {status}, waiting...")
        time.sleep(poll_interval)

    return False


def _wait_for_all_pipelines_complete(host, log_callback=None, timeout: int = 7200) -> bool:
    """
    Wait for all running/pending pipelines to complete.

    Args:
        host: Testinfra host object
        log_callback: Optional logging callback
        timeout: Max wait time in seconds (default 2 hours)

    Returns:
        True if no running pipelines, False if timeout
    """
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


# =============================================================================
# ITERATION RESULT STRUCTURE
# =============================================================================

def _create_iteration_result(iteration: int) -> Dict[str, Any]:
    """Create a fresh result dict for one iteration."""
    return {
        "iteration": iteration,
        "success": False,
        "job_id": None,
        "pipeline_id": None,
        "start_time": None,
        "end_time": None,
        "elapsed_seconds": 0,
        "stages": {},
        "stage_errors": [],
        "catalog_roles": [],
        "catalog_architectures": [],
        "catalog_image_key": "",
        "db_image_group_ok": False,
        "db_images_ok": False,
        "db_images_count": 0,
        "registry_ok": False,
        "registry_found": 0,
        "registry_missing": 0,
        "s3_ok": False,
        "s3_found_roles": 0,
        "s3_missing_roles": 0,
        "s3_total_files": 0,
        "error": "",
    }


# =============================================================================
# SINGLE ITERATION - FULL PIPELINE WITH ALL VALIDATIONS
# =============================================================================

def _run_single_iteration(
    host,
    iteration: int,
    total: int,
    is_first: bool = False
) -> Dict[str, Any]:
    """
    Run a single complete build pipeline iteration with ALL validations.

    Args:
        host: Testinfra host object
        iteration: Current iteration number (1-based)
        total: Total number of iterations
        is_first: True if this is the first iteration

    Returns:
        Dict with all validation results for this iteration
    """
    result = _create_iteration_result(iteration)
    result["start_time"] = datetime.now().isoformat()

    def _log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"    │ [{timestamp}] [Iter {iteration}/{total}] {msg}", flush=True)
        sys.stdout.flush()

    _log("=" * 50)
    _log(f"STARTING ITERATION {iteration}/{total}")
    _log("=" * 50)

    # =========================================================================
    # STEP 1: WAIT FOR ANY RUNNING PIPELINES TO COMPLETE
    # =========================================================================
    if is_first:
        _log("Step 1/8: First iteration - checking for running pipelines...")
    else:
        _log("Step 1/8: Waiting for previous pipeline to complete...")
        if not _wait_for_all_pipelines_complete(host, log_callback=_log, timeout=7200):
            result["error"] = "Timeout waiting for previous pipeline to complete"
            result["end_time"] = datetime.now().isoformat()
            result["elapsed_seconds"] = int(
                (datetime.fromisoformat(result["end_time"])
                 - datetime.fromisoformat(result["start_time"])).total_seconds()
            )
            _log(f"FAILED: {result['error']}")
            return result
        _log("All pipelines completed, proceeding...")

    # =========================================================================
    # STEP 2: TRIGGER BUILD PIPELINE
    # =========================================================================
    _log("Step 2/8: Triggering build pipeline...")

    # Note: allow_pipeline_cancel is read from omnia_test_config.yml internally
    trigger_result = trigger_build_pipeline(
        host,
        log_callback=_log,
    )

    if not trigger_result["success"]:
        result["error"] = f"Trigger failed: {trigger_result['error']}"
        result["end_time"] = datetime.now().isoformat()
        result["elapsed_seconds"] = int(
            (datetime.fromisoformat(result["end_time"])
             - datetime.fromisoformat(result["start_time"])).total_seconds()
        )
        _log(f"FAILED: {result['error']}")
        return result

    job_id = trigger_result["job_id"]
    pipeline_id = trigger_result["pipeline_id"]
    result["job_id"] = job_id
    result["pipeline_id"] = pipeline_id

    _log(f"Pipeline #{pipeline_id} triggered, Job ID: {job_id}")

    # =========================================================================
    # STEP 3: MONITOR CORE STAGES
    # =========================================================================
    _log("Step 3/8: Monitoring core pipeline stages...")

    core_stages = list(BUILD_PIPELINE_CORE_STAGES)
    _log(f"Core stages: {core_stages}")

    all_stages_passed = True
    for stage_name in core_stages:
        _log(f"  Monitoring stage: {stage_name}...")

        stage_result = wait_for_stage_completion(
            host, job_id, stage_name,
            timeout=STAGE_POLL_TIMEOUT,
            poll_interval=STAGE_POLL_INTERVAL,
            log_callback=lambda msg: print(f"      │ {msg}", flush=True),
        )

        stage_state = stage_result.get("stage_state", "UNKNOWN")
        result["stages"][stage_name] = {
            "state": stage_state,
            "elapsed": stage_result.get("elapsed", 0),
            "success": stage_result["success"],
        }

        if stage_result["success"]:
            _log(f"  ✓ Stage '{stage_name}' COMPLETED in {stage_result['elapsed']}s")
        else:
            all_stages_passed = False
            error_msg = stage_result.get("error", "Unknown error")
            result["stage_errors"].append(f"{stage_name}: {error_msg}")
            _log(f"  ✗ Stage '{stage_name}' FAILED: {error_msg}")

            log_path = get_stage_log_path(host, job_id, stage_name)
            if log_path:
                _log(f"    Log file: {log_path}")
            break

    if not all_stages_passed:
        result["error"] = f"Stage failures: {'; '.join(result['stage_errors'])}"
        result["end_time"] = datetime.now().isoformat()
        result["elapsed_seconds"] = int(
            (datetime.fromisoformat(result["end_time"])
             - datetime.fromisoformat(result["start_time"])).total_seconds()
        )
        return result

    # =========================================================================
    # STEP 4: GET CATALOG INFO (after parse-catalog completes)
    # =========================================================================
    _log("Step 4/8: Getting catalog information...")

    roles_result = get_catalog_roles(host, job_id)
    if roles_result["success"]:
        result["catalog_roles"] = roles_result["roles"]
        result["catalog_architectures"] = roles_result.get("architectures", ["x86_64"])
        result["catalog_image_key"] = roles_result.get("image_key", "")
        _log(
            f"Catalog: {len(result['catalog_roles'])} roles, "
            f"architectures: {result['catalog_architectures']}"
        )
    else:
        _log(f"Warning: Could not get catalog info: {roles_result.get('error', 'Unknown')}")
        result["catalog_roles"] = []
        result["catalog_architectures"] = ["x86_64"]
        result["catalog_image_key"] = ""

    # =========================================================================
    # STEP 5: MONITOR BUILD-IMAGE STAGES
    # =========================================================================
    _log("Step 5/8: Monitoring build-image stages...")

    build_stages = [
        f"{BUILD_IMAGE_STAGE_PREFIX}{arch}"
        for arch in result["catalog_architectures"]
    ]
    _log(f"Build stages: {build_stages}")

    for stage_name in build_stages:
        _log(f"  Monitoring stage: {stage_name}...")

        stage_result = wait_for_stage_completion(
            host, job_id, stage_name,
            timeout=STAGE_POLL_TIMEOUT,
            poll_interval=STAGE_POLL_INTERVAL,
            log_callback=lambda msg: print(f"      │ {msg}", flush=True),
        )

        stage_state = stage_result.get("stage_state", "UNKNOWN")
        result["stages"][stage_name] = {
            "state": stage_state,
            "elapsed": stage_result.get("elapsed", 0),
            "success": stage_result["success"],
        }

        if stage_result["success"]:
            _log(f"  ✓ Stage '{stage_name}' COMPLETED in {stage_result['elapsed']}s")
        else:
            all_stages_passed = False
            error_msg = stage_result.get("error", "Unknown error")
            result["stage_errors"].append(f"{stage_name}: {error_msg}")
            _log(f"  ✗ Stage '{stage_name}' FAILED: {error_msg}")

            log_path = get_stage_log_path(host, job_id, stage_name)
            if log_path:
                _log(f"    Log file: {log_path}")
            break

    if not all_stages_passed:
        result["error"] = f"Stage failures: {'; '.join(result['stage_errors'])}"
        result["end_time"] = datetime.now().isoformat()
        result["elapsed_seconds"] = int(
            (datetime.fromisoformat(result["end_time"])
             - datetime.fromisoformat(result["start_time"])).total_seconds()
        )
        return result

    _log("All stages completed successfully")

    # =========================================================================
    # STEP 6: VERIFY DATABASE (image_groups and images)
    # =========================================================================
    _log("Step 6/8: Verifying database records...")

    # Verify image_groups
    ig_result = get_image_groups_for_job(host, job_id)
    if ig_result["success"] and ig_result["image_groups"]:
        built_groups = [g for g in ig_result["image_groups"] if g["status"] == "BUILT"]
        if built_groups:
            result["db_image_group_ok"] = True
            _log(f"  ✓ Found {len(built_groups)} image group(s) with BUILT status")
        else:
            _log("  ✗ No image groups with BUILT status")
    else:
        _log(f"  ✗ Failed to get image groups: {ig_result.get('error', 'No groups')}")

    # Verify images and extract roles if catalog API failed
    images_result = get_images_for_job(host, job_id)
    if images_result["success"] and images_result["images"]:
        result["db_images_count"] = len(images_result["images"])

        # CRITICAL: Extract roles from DB if catalog_roles is empty
        if not result["catalog_roles"]:
            db_roles = [
                img.get("role") for img in images_result["images"]
                if img.get("role")
            ]
            if db_roles:
                result["catalog_roles"] = list(set(db_roles))
                _log(f"  Extracted {len(result['catalog_roles'])} roles from DB: {result['catalog_roles']}")

        expected = len(result["catalog_roles"]) if result["catalog_roles"] else 1
        if result["db_images_count"] >= expected:
            result["db_images_ok"] = True
            _log(f"  ✓ Found {result['db_images_count']} images in DB")
        else:
            _log(f"  ✗ Only {result['db_images_count']} images (expected >= {expected})")
    else:
        _log(f"  ✗ Failed to get images: {images_result.get('error', 'No images')}")

    # =========================================================================
    # STEP 7: VERIFY REGISTRY AND S3 IMAGES
    # =========================================================================
    _log("Step 7/8: Verifying registry and S3 images...")

    if result["catalog_roles"]:
        _log(f"  Verifying for roles: {result['catalog_roles']}")
        _log(f"  Using full job_id: {job_id}")

        # Registry verification
        _log("  Checking registry images...")
        reg_result = verify_registry_images(
            host, job_id, result["catalog_roles"], result["catalog_image_key"]
        )
        result["registry_found"] = len(reg_result.get("found", []))
        result["registry_missing"] = len(reg_result.get("missing", []))

        if reg_result["success"]:
            result["registry_ok"] = True
            _log(f"  ✓ Registry: {result['registry_found']}/{len(result['catalog_roles'])} roles found")
            for item in reg_result.get("found", []):
                _log(f"      ✓ {item['role']}: {item.get('repo', 'N/A')}")
        else:
            _log(f"  ✗ Registry: {result['registry_found']}/{len(result['catalog_roles'])} roles found")
            for item in reg_result.get("found", []):
                _log(f"      ✓ {item['role']}: {item.get('repo', 'N/A')}")
            for m in reg_result.get("missing", []):
                _log(f"      ✗ Missing: {m}")

        # S3 verification
        _log("  Checking S3 boot images...")
        s3_result = verify_s3_boot_images(
            host, job_id, result["catalog_roles"], result["catalog_image_key"]
        )
        result["s3_found_roles"] = len(s3_result.get("found_roles", []))
        result["s3_missing_roles"] = len(s3_result.get("missing_roles", []))
        result["s3_total_files"] = s3_result.get("total_files", 0)

        if s3_result["success"]:
            result["s3_ok"] = True
            _log(f"  ✓ S3: {result['s3_found_roles']}/{len(result['catalog_roles'])} roles complete")
            for item in s3_result.get("found_roles", []):
                _log(f"      ✓ {item['role']}: rootfs={item['rootfs']}, efi={item['efi_files']}")
                for rf in item.get("rootfs_files", []):
                    _log(f"          {rf}")
                for ef in item.get("efi_file_paths", []):
                    _log(f"          {ef}")
        else:
            _log(f"  ✗ S3: {result['s3_found_roles']}/{len(result['catalog_roles'])} roles complete")
            for item in s3_result.get("found_roles", []):
                _log(f"      ✓ {item['role']}: rootfs={item['rootfs']}, efi={item['efi_files']}")
            for m in s3_result.get("missing_roles", []):
                _log(f"      ✗ {m['role']}: rootfs={m['rootfs']}, efi={m['efi_files']}")
    else:
        _log("  ⚠ No roles available - cannot verify registry/S3")
        result["registry_ok"] = False
        result["s3_ok"] = False

    # =========================================================================
    # STEP 8: WAIT FOR GITLAB PIPELINE TO FULLY COMPLETE
    # =========================================================================
    _log("Step 8/8: Waiting for GitLab pipeline to fully complete...")

    if not _wait_for_gitlab_pipeline_completion(host, pipeline_id, log_callback=_log, timeout=300):
        _log("Warning: Timeout waiting for GitLab pipeline, but DB stages completed")

    # =========================================================================
    # FINAL RESULT
    # =========================================================================
    result["end_time"] = datetime.now().isoformat()
    result["elapsed_seconds"] = int(
        (datetime.fromisoformat(result["end_time"])
         - datetime.fromisoformat(result["start_time"])).total_seconds()
    )

    result["success"] = (
        all_stages_passed
        and result["db_image_group_ok"]
        and result["db_images_ok"]
        and result["registry_ok"]
        and result["s3_ok"]
    )

    if result["success"]:
        _log("=" * 50)
        _log(f"ITERATION {iteration}/{total} PASSED in {result['elapsed_seconds']}s")
        _log("=" * 50)
    else:
        failures = []
        if not all_stages_passed:
            failures.append("stages")
        if not result["db_image_group_ok"]:
            failures.append("db_image_groups")
        if not result["db_images_ok"]:
            failures.append("db_images")
        if not result["registry_ok"]:
            failures.append("registry")
        if not result["s3_ok"]:
            failures.append("s3")
        result["error"] = f"Failed checks: {', '.join(failures)}"
        _log("=" * 50)
        _log(f"ITERATION {iteration}/{total} FAILED: {result['error']}")
        _log("=" * 50)

    return result


# =============================================================================
# MAIN STRESS TEST
# =============================================================================

@pytest.mark.stress
@pytest.mark.order(100)
def test_stress_build_pipeline(host):
    """
    Stress test: Run build pipeline N times with FULL validation each time.

    Each iteration:
      1. Wait for any running pipelines to complete
      2. Trigger new pipeline
      3. Monitor all stages
      4. Get catalog info (roles, architectures)
      5. Monitor build-image stages
      6. Verify DB (image_groups, images) and extract roles from DB
      7. Verify registry and S3 images using full job_id
      8. Wait for GitLab pipeline to fully complete

    IMPORTANT: Does NOT auto-cancel pipelines.
      - First iteration prompts user if pipeline running
      - Subsequent iterations wait for completion
    """
    log = TestLogger("Stress Build Pipeline")

    if not is_build_stream_enabled(host):
        log.skipped("Build stream not enabled", "Test skipped")
        pytest.skip("Build stream not enabled")

    count = _get_stress_count()
    log.check(f"Running {count} full build pipeline iteration(s) with ALL validations")

    print("\n" + "#" * 70, flush=True)
    print(f"# BUILD STREAM STRESS TEST - {count} ITERATIONS", flush=True)
    print("# Each iteration: trigger -> stages -> DB -> registry -> S3", flush=True)
    print(f"# Started at: {datetime.now().isoformat()}", flush=True)
    print("#" * 70 + "\n", flush=True)

    results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0
    total_elapsed = 0

    for i in range(1, count + 1):
        iteration_result = _run_single_iteration(
            host, i, count,
            is_first=(i == 1)
        )
        results.append(iteration_result)
        total_elapsed += iteration_result["elapsed_seconds"]

        if iteration_result["success"]:
            passed += 1
        else:
            failed += 1

        print(
            f"\n    Progress: {i}/{count} complete, "
            f"{passed} passed, {failed} failed\n",
            flush=True
        )

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "#" * 70, flush=True)
    print("# STRESS TEST COMPLETE", flush=True)
    print(f"# Total: {count}, Passed: {passed}, Failed: {failed}", flush=True)
    print(
        f"# Total time: {total_elapsed}s "
        f"({total_elapsed // 60}m {total_elapsed % 60}s)",
        flush=True
    )
    print(f"# Finished at: {datetime.now().isoformat()}", flush=True)
    print("#" * 70 + "\n", flush=True)

    summary_lines = [
        f"Total iterations: {count}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        f"Total time: {total_elapsed}s",
        "",
        "Per-iteration results:",
    ]

    for r in results:
        status = "PASS" if r["success"] else "FAIL"
        job_str = r["job_id"][:8] if r["job_id"] else "N/A"
        summary_lines.append(
            f"  [{status}] Iter {r['iteration']}: "
            f"job={job_str}... "
            f"time={r['elapsed_seconds']}s "
            f"stages={len(r['stages'])} "
            f"reg={r['registry_found']}/{r['registry_found'] + r['registry_missing']} "
            f"s3={r['s3_found_roles']}/{r['s3_found_roles'] + r['s3_missing_roles']}"
        )
        if r["error"]:
            summary_lines.append(f"       Error: {r['error']}")

    if failed == 0:
        log.passed(
            f"All {count} iterations passed with full validation",
            "\n".join(summary_lines),
        )
    else:
        log.failed(
            f"{failed}/{count} iterations failed",
            "\n".join(summary_lines),
        )
        pytest.fail(f"Stress test: {failed}/{count} iterations failed")
