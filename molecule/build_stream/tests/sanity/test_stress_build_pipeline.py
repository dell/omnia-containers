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

Runs the full build pipeline (trigger → monitor all stages → verify images)
repeatedly for a configurable number of iterations (default 50).

The iteration count is controlled by:
  - STRESS_BUILD_PIPELINE_COUNT in build_stream_vars.py (default 50)
  - Or override via env var BUILD_STRESS_COUNT

Markers:
    - stress: Stress / load tests (separate from sanity)
    - build_stream: Build stream module tests
"""

import os
import sys
import time

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    trigger_build_pipeline,
    wait_for_stage_completion,
    get_stage_state,
    get_stage_log_path,
    get_catalog_roles,
    get_image_groups_for_job,
    verify_registry_images,
    verify_s3_boot_images,
    BUILD_PIPELINE_CORE_STAGES,
    BUILD_IMAGE_STAGE_PREFIX,
    STAGE_POLL_INTERVAL,
    STAGE_POLL_TIMEOUT,
    STRESS_BUILD_PIPELINE_COUNT,
)


def _get_stress_count() -> int:
    """Get the number of stress iterations from env or default."""
    return int(os.environ.get("BUILD_STRESS_COUNT", STRESS_BUILD_PIPELINE_COUNT))


def _run_single_build_pipeline(host, iteration: int, total: int) -> dict:
    """
    Run a single build pipeline end-to-end and return a summary dict.

    Returns:
        Dict with 'success', 'job_id', 'pipeline_id', 'stages', 'elapsed',
        'registry_ok', 's3_ok', 'error'.
    """
    summary = {
        "success": False,
        "iteration": iteration,
        "job_id": None,
        "pipeline_id": None,
        "stages": {},
        "elapsed": 0,
        "registry_ok": False,
        "s3_ok": False,
        "error": "",
    }

    start = time.time()

    def _log(msg):
        print(f"    │ [iter {iteration}/{total}] {msg}", flush=True)
        sys.stdout.flush()

    # 1. Trigger pipeline
    _log("Triggering build pipeline...")
    result = trigger_build_pipeline(host, log_callback=_log)

    if not result["success"]:
        summary["error"] = f"Trigger failed: {result['error']}"
        summary["elapsed"] = int(time.time() - start)
        return summary

    job_id = result["job_id"]
    pipeline_id = result["pipeline_id"]
    summary["job_id"] = job_id
    summary["pipeline_id"] = pipeline_id

    # 2. Get catalog info for dynamic stages
    roles_result = get_catalog_roles(host, job_id)
    architectures = roles_result.get("architectures", ["x86_64"]) if roles_result["success"] else ["x86_64"]
    roles = roles_result.get("roles", []) if roles_result["success"] else []
    image_key = roles_result.get("image_key", "") if roles_result["success"] else ""

    # 3. Build stage list
    stages = list(BUILD_PIPELINE_CORE_STAGES)
    for arch in architectures:
        stages.append(f"{BUILD_IMAGE_STAGE_PREFIX}{arch}")

    # 4. Monitor each stage
    all_passed = True
    for stage_name in stages:
        stage_result = wait_for_stage_completion(
            host, job_id, stage_name,
            timeout=STAGE_POLL_TIMEOUT,
            poll_interval=STAGE_POLL_INTERVAL,
            log_callback=_log,
        )
        summary["stages"][stage_name] = stage_result.get("stage_state", "UNKNOWN")

        if not stage_result["success"]:
            all_passed = False
            log_path = get_stage_log_path(host, job_id, stage_name)
            if log_path:
                _log(f"Log file: {log_path}")
            summary["error"] = f"Stage '{stage_name}' failed"
            break

    # 5. Post-build verification (only if all stages passed)
    if all_passed and roles:
        reg = verify_registry_images(host, job_id, roles, image_key)
        summary["registry_ok"] = reg["success"]
        if not reg["success"]:
            _log(f"Registry check failed: missing={reg.get('missing', [])}")

        s3 = verify_s3_boot_images(host, job_id, roles, image_key)
        summary["s3_ok"] = s3["success"]
        if not s3["success"]:
            _log(f"S3 check failed: missing={[m['role'] for m in s3.get('missing_roles', [])]}")

        summary["success"] = reg["success"] and s3["success"]
    elif all_passed:
        summary["success"] = True

    summary["elapsed"] = int(time.time() - start)
    status = "PASS" if summary["success"] else "FAIL"
    _log(f"Iteration {iteration} {status} in {summary['elapsed']}s")
    return summary


@pytest.mark.stress
@pytest.mark.build_stream
@pytest.mark.order(100)
def test_stress_build_pipeline(host):
    """
    Stress test: Run build pipeline N times and report results.

    The iteration count defaults to STRESS_BUILD_PIPELINE_COUNT (50)
    and can be overridden by setting BUILD_STRESS_COUNT env var.
    """
    log = TestLogger("Stress Build Pipeline")

    if not is_build_stream_enabled(host):
        log.skipped("Build stream not enabled", "Test skipped")
        pytest.skip("Build stream not enabled")

    count = _get_stress_count()
    log.check(f"Running build pipeline {count} time(s)")

    results = []
    passed = 0
    failed = 0

    for i in range(1, count + 1):
        print(f"\n{'=' * 60}", flush=True)
        print(f"  STRESS ITERATION {i}/{count}", flush=True)
        print(f"{'=' * 60}", flush=True)

        summary = _run_single_build_pipeline(host, i, count)
        results.append(summary)

        if summary["success"]:
            passed += 1
        else:
            failed += 1

    # Final summary
    details_lines = [
        f"Total: {count}, Passed: {passed}, Failed: {failed}",
        "",
    ]
    for r in results:
        status = "PASS" if r["success"] else "FAIL"
        job_str = r["job_id"][:8] if r["job_id"] else "N/A"
        details_lines.append(
            f"  [{status}] Iter {r['iteration']}: "
            f"job={job_str}... elapsed={r['elapsed']}s"
            + (f" error={r['error']}" if r["error"] else "")
        )

    if failed == 0:
        log.passed(
            f"All {count} iterations passed",
            "\n".join(details_lines),
        )
    else:
        log.failed(
            f"{failed}/{count} iterations failed",
            "\n".join(details_lines),
        )
        pytest.fail(f"Stress test: {failed}/{count} iterations failed")
