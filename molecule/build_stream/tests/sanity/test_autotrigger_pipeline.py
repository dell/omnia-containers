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
Build Stream Auto-Trigger Pipeline Tests (v2.1).

Sanity tests for triggering and monitoring the build pipeline:
  - Trigger pipeline via catalog upload
  - Monitor each stage (parse-catalog, generate-input-files,
    create-local-repository, build-image-x86_64, build-image-aarch64,
    validate-image-on-test)
  - Verify each stage in database
  - Verify catalog roles and architectures
  - Verify registry images
  - Verify S3 boot images
  - Final pipeline result summary

v2.1 has a SINGLE pipeline (unlike v2.2 which has separate build + deploy).
The "deploy-and-validate" CI/CD stage runs the validate-image-on-test job
which deploys and validates the built images on test nodes.
"""

import sys

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled

from automation_library.build_stream.functions import (
    skip_if_build_stream_not_enabled,
    trigger_build_pipeline,
    wait_for_stage_completion,
    get_catalog_roles,
    verify_stage_completed,
    get_latest_job,
    verify_registry_images,
    verify_s3_boot_images,
)
from automation_library.build_stream.vars.build_stream_vars import (
    BUILD_PIPELINE_CORE_STAGES,
    BUILD_IMAGE_STAGE_PREFIX,
    STAGE_STATE_COMPLETED,
    STAGE_STATE_FAILED,
    STAGE_POLL_TIMEOUT,
    STAGE_POLL_INTERVAL,
    STAGE_VALIDATE_IMAGE,
)
from automation_library.build_stream.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# MODULE-LEVEL STATE
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


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _log_callback(msg):
    """Log callback for pipeline functions."""
    print(f"    | {msg}", flush=True)
    sys.stdout.flush()


def _get_build_stages():
    """Get the list of build stages based on catalog architectures."""
    stages = list(BUILD_PIPELINE_CORE_STAGES)
    for arch in _build_state.get("catalog_architectures", []):
        stages.append(f"{BUILD_IMAGE_STAGE_PREFIX}{arch}")
    if not _build_state.get("catalog_architectures"):
        stages.append(f"{BUILD_IMAGE_STAGE_PREFIX}x86_64")
    stages.append(STAGE_VALIDATE_IMAGE)
    return stages


def _skip_if_build_not_triggered(log):
    """Skip test if build pipeline was not triggered."""
    if not _build_state["triggered"]:
        log.skipped(
            SKIP_MSGS["pipeline_not_triggered"],
            "Build pipeline was not triggered"
        )
        pytest.skip(SKIP_MSGS["pipeline_not_triggered"])


def _build_should_skip_due_to_failure(stage_name: str) -> bool:
    """Check if test should skip due to any prior stage failure."""
    stages = _get_build_stages()
    if stage_name not in stages:
        return False
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _build_state["stage_results"]:
            if _build_state["stage_results"][prior_stage].get("stage_state") == STAGE_STATE_FAILED:
                return True
    return False


def _get_build_failed_prior_stage(stage_name: str) -> str:
    """Get the name of the first failed prior stage, or empty string."""
    stages = _get_build_stages()
    if stage_name not in stages:
        return ""
    current_idx = stages.index(stage_name)
    for prior_stage in stages[:current_idx]:
        if prior_stage in _build_state["stage_results"]:
            if _build_state["stage_results"][prior_stage].get("stage_state") == STAGE_STATE_FAILED:
                return prior_stage
    return ""


def _any_build_stage_failed() -> bool:
    """Check if any build stage failed."""
    for result in _build_state["stage_results"].values():
        if result.get("stage_state") == STAGE_STATE_FAILED:
            return True
    return False


# =============================================================================
# SHARED STAGE MONITOR + DB VERIFY FUNCTIONS
# =============================================================================

def _run_build_stage_monitor(host, stage_name: str):
    """Monitor a build stage until completion."""
    log = TestLogger(TEST_NAMES["stage_monitor"].format(stage=stage_name))
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_not_triggered(log)

    failed_stage = _get_build_failed_prior_stage(stage_name)
    if failed_stage:
        log.skipped(
            SKIP_MSGS["previous_stage_failed"].format(stage=failed_stage),
            f"Prior stage '{failed_stage}' failed"
        )
        pytest.skip(SKIP_MSGS["previous_stage_failed"].format(stage=failed_stage))

    job_id = _build_state["job_id"]
    if not job_id:
        job_result = get_latest_job(host)
        if job_result["success"]:
            job_id = job_result["job_id"]
            _build_state["job_id"] = job_id

    if not job_id:
        log.failed("No job_id available for stage monitoring")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check(TEST_LOG_MSGS["stage_running"].format(stage=stage_name))

    if stage_name in ["parse-catalog", "generate-input-files"]:
        stage_timeout = 300
    else:
        stage_timeout = STAGE_POLL_TIMEOUT

    result = wait_for_stage_completion(
        host, job_id, stage_name,
        timeout=stage_timeout,
        poll_interval=STAGE_POLL_INTERVAL,
        log_callback=_log_callback,
    )

    _build_state["stage_results"][stage_name] = result

    elapsed = result.get("elapsed", 0)
    details = (
        f"Stage: {stage_name}\n"
        f"State: {result['stage_state']}\n"
        f"Elapsed: {elapsed}s ({elapsed // 60}m{elapsed % 60:02d}s)"
    )
    if result.get("log_path"):
        details += f"\nLog: {result['log_path']}"

    if result["success"]:
        log.passed(
            TEST_LOG_MSGS["stage_completed"].format(stage=stage_name, elapsed=elapsed),
            details
        )
    else:
        log.failed(
            TEST_LOG_MSGS["stage_failed"].format(stage=stage_name, error=result["error"]),
            details
        )
        pytest.fail(
            TEST_ASSERT_MSGS["stage_failed"].format(stage=stage_name, error=result["error"])
        )


def _run_build_stage_db_verify(host, stage_name: str):
    """Verify a build stage state in the database."""
    log = TestLogger(TEST_NAMES["stage_db_verify"].format(stage=stage_name))
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_not_triggered(log)

    if _build_should_skip_due_to_failure(stage_name):
        failed = _get_build_failed_prior_stage(stage_name)
        log.skipped(
            SKIP_MSGS["previous_stage_failed"].format(stage=failed),
            f"Prior stage '{failed}' failed"
        )
        pytest.skip(SKIP_MSGS["previous_stage_failed"].format(stage=failed))

    job_id = _build_state["job_id"]
    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check(f"Verifying stage '{stage_name}' in database...")
    db_result = verify_stage_completed(host, job_id, stage_name)

    if not db_result["success"]:
        log.failed(
            TEST_LOG_MSGS["stage_db_fail"].format(stage=stage_name, error=db_result["error"]),
        )
        pytest.fail(
            TEST_ASSERT_MSGS["stage_db_failed"].format(stage=stage_name, error=db_result["error"])
        )

    db_state = db_result["stage_state"]
    details = f"Stage: {stage_name}\nDB State: {db_state}\n{db_result.get('details', '')}"

    if stage_name in _build_state["stage_results"]:
        monitored_state = _build_state["stage_results"][stage_name].get("stage_state", "")
        details += f"\nMonitored State: {monitored_state}"
        if db_state == monitored_state:
            details += "\nDB matches monitored state"

    log.passed(
        TEST_LOG_MSGS["stage_db_ok"].format(stage=stage_name, state=db_state),
        details
    )


# =============================================================================
# TEST 10: Trigger Build Pipeline
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(10)
def test_trigger_build_pipeline(host):
    """Trigger a build pipeline by uploading the catalog file."""
    log = TestLogger(TEST_NAMES["catalog_upload"])
    skip_if_build_stream_not_enabled(host, log)

    log.check("Triggering build pipeline via catalog upload...")

    result = trigger_build_pipeline(host, log_callback=_log_callback)

    if result["success"]:
        _build_state["triggered"] = True
        _build_state["pipeline_id"] = result["pipeline_id"]
        _build_state["job_id"] = result["job_id"]

        if result["job_id"]:
            roles_result = get_catalog_roles(host, result["job_id"])
            if roles_result["success"]:
                _build_state["catalog_roles"] = roles_result["roles"]
                _build_state["catalog_architectures"] = roles_result["architectures"]
                _build_state["catalog_image_key"] = roles_result["image_key"]

        details = result.get("details", "")
        if _build_state["catalog_roles"]:
            details += f"\nRoles: {_build_state['catalog_roles']}"
            details += f"\nArchitectures: {_build_state['catalog_architectures']}"
            details += f"\nImage key: {_build_state['catalog_image_key']}"

        log.passed(
            TEST_LOG_MSGS["pipeline_triggered_ok"].format(pipeline_id=result["pipeline_id"]),
            details
        )
    else:
        log.failed(
            TEST_LOG_MSGS["pipeline_triggered_fail"].format(error=result["error"]),
            result.get("details", "")
        )
        pytest.fail(TEST_ASSERT_MSGS["pipeline_not_triggered"])


# =============================================================================
# TESTS 11-12: parse-catalog
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(11)
def test_build_stage_parse_catalog_monitor(host):
    """Monitor parse-catalog stage until completion."""
    _run_build_stage_monitor(host, "parse-catalog")


@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(12)
def test_build_stage_parse_catalog_db_verify(host):
    """Verify parse-catalog stage state in database."""
    _run_build_stage_db_verify(host, "parse-catalog")


# =============================================================================
# TESTS 13-14: generate-input-files
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(13)
def test_build_stage_generate_input_monitor(host):
    """Monitor generate-input-files stage until completion."""
    _run_build_stage_monitor(host, "generate-input-files")


@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(14)
def test_build_stage_generate_input_db_verify(host):
    """Verify generate-input-files stage state in database."""
    _run_build_stage_db_verify(host, "generate-input-files")


# =============================================================================
# TESTS 15-16: create-local-repository
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(15)
def test_build_stage_local_repo_monitor(host):
    """Monitor create-local-repository stage until completion."""
    _run_build_stage_monitor(host, "create-local-repository")


@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(16)
def test_build_stage_local_repo_db_verify(host):
    """Verify create-local-repository stage state in database."""
    _run_build_stage_db_verify(host, "create-local-repository")


# =============================================================================
# TESTS 17-18: build-image-x86_64
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(17)
def test_build_stage_build_image_x86_64_monitor(host):
    """Monitor build-image-x86_64 stage until completion."""
    _run_build_stage_monitor(host, "build-image-x86_64")


@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(18)
def test_build_stage_build_image_x86_64_db_verify(host):
    """Verify build-image-x86_64 stage state in database."""
    _run_build_stage_db_verify(host, "build-image-x86_64")


# =============================================================================
# TESTS 19-20: build-image-aarch64 (conditional)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(19)
def test_build_stage_build_image_aarch64_monitor(host):
    """Monitor build-image-aarch64 stage until completion (if applicable)."""
    log = TestLogger(TEST_NAMES["stage_monitor"].format(stage="build-image-aarch64"))
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_not_triggered(log)

    if "aarch64" not in _build_state.get("catalog_architectures", []):
        log.skipped(
            "aarch64 not in catalog architectures",
            f"Architectures: {_build_state.get('catalog_architectures', [])}"
        )
        pytest.skip("aarch64 not in catalog architectures")

    _run_build_stage_monitor(host, "build-image-aarch64")


@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(20)
def test_build_stage_build_image_aarch64_db_verify(host):
    """Verify build-image-aarch64 stage state in database (if applicable)."""
    log = TestLogger(TEST_NAMES["stage_db_verify"].format(stage="build-image-aarch64"))
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_not_triggered(log)

    if "aarch64" not in _build_state.get("catalog_architectures", []):
        log.skipped(
            "aarch64 not in catalog architectures",
            f"Architectures: {_build_state.get('catalog_architectures', [])}"
        )
        pytest.skip("aarch64 not in catalog architectures")

    _run_build_stage_db_verify(host, "build-image-aarch64")


# =============================================================================
# TESTS 21-22: validate-image-on-test (deploy-and-validate CI/CD stage)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(21)
def test_build_stage_validate_image_monitor(host):
    """Monitor validate-image-on-test stage until completion."""
    _run_build_stage_monitor(host, STAGE_VALIDATE_IMAGE)


@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(22)
def test_build_stage_validate_image_db_verify(host):
    """Verify validate-image-on-test stage state in database."""
    _run_build_stage_db_verify(host, STAGE_VALIDATE_IMAGE)


# =============================================================================
# TEST 23: Catalog Roles Verification
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(23)
def test_build_catalog_roles(host):
    """Verify catalog roles and architectures from Build Stream API."""
    log = TestLogger(TEST_NAMES["catalog_roles"])
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_not_triggered(log)

    if _any_build_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "One or more build stages failed")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _build_state["job_id"]
    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check("Retrieving catalog roles from Build Stream API...")
    result = get_catalog_roles(host, job_id)

    if result["success"]:
        _build_state["catalog_roles"] = result["roles"]
        _build_state["catalog_architectures"] = result["architectures"]
        _build_state["catalog_image_key"] = result["image_key"]

        details = (
            f"Roles: {result['roles']}\n"
            f"Architectures: {result['architectures']}\n"
            f"Image Key: {result['image_key']}"
        )
        log.passed(
            TEST_LOG_MSGS["catalog_roles_ok"].format(
                roles=result["roles"], archs=result["architectures"]
            ),
            details
        )
    else:
        log.failed(
            TEST_LOG_MSGS["catalog_roles_fail"].format(error=result["error"])
        )
        pytest.fail(
            TEST_ASSERT_MSGS["catalog_roles_failed"].format(error=result["error"])
        )


# =============================================================================
# TEST 24: Registry Images Verification
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(24)
def test_build_registry_images(host):
    """Verify container images exist in the local registry for each role."""
    log = TestLogger(TEST_NAMES["registry_images"])
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_not_triggered(log)

    if _any_build_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "One or more build stages failed")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _build_state["job_id"]
    roles = _build_state.get("catalog_roles", [])
    image_key = _build_state.get("catalog_image_key", "")

    if not job_id or not roles:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id or roles available")
        pytest.skip("No job_id or catalog roles available")

    log.check(f"Verifying registry images for {len(roles)} roles...")
    result = verify_registry_images(host, job_id, roles, image_key)

    details = (
        f"Registry: {result.get('registry_url', '')}\n"
        f"Found: {len(result.get('found', []))}/{len(roles)} roles\n"
        f"{result.get('details', '')}"
    )

    if result.get("missing"):
        details += f"\nMissing roles: {result['missing']}"

    if result["success"]:
        log.passed(
            TEST_LOG_MSGS["registry_ok"].format(count=len(result["found"])),
            details
        )
    else:
        log.failed(
            TEST_LOG_MSGS["registry_fail"].format(
                count=len(result.get("missing", [])),
                missing=result.get("missing", [])
            ),
            details
        )
        pytest.fail(
            TEST_ASSERT_MSGS["registry_images_failed"].format(error=result.get("error", ""))
        )


# =============================================================================
# TEST 25: S3 Boot Images Verification
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(25)
def test_build_s3_boot_images(host):
    """Verify S3 boot images exist for each role."""
    log = TestLogger(TEST_NAMES["s3_boot_images"])
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_not_triggered(log)

    if _any_build_stage_failed():
        log.skipped(SKIP_MSGS["build_failed"], "One or more build stages failed")
        pytest.skip(SKIP_MSGS["build_failed"])

    job_id = _build_state["job_id"]
    roles = _build_state.get("catalog_roles", [])
    image_key = _build_state.get("catalog_image_key", "")

    if not job_id or not roles:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id or roles available")
        pytest.skip("No job_id or catalog roles available")

    log.check(f"Verifying S3 boot images for {len(roles)} roles...")
    result = verify_s3_boot_images(host, job_id, roles, image_key)

    details = result.get("details", "")
    if result.get("missing_roles"):
        missing_info = []
        for mr in result["missing_roles"]:
            missing_info.append(
                f"  {mr['role']}: rootfs={mr['rootfs']}, efi={mr['efi_files']}, total={mr['total']}"
            )
        details += "\nMissing:\n" + "\n".join(missing_info)

    if result["success"]:
        log.passed(
            TEST_LOG_MSGS["s3_ok"].format(count=len(result["found_roles"])),
            details
        )
    else:
        missing_names = [r["role"] for r in result.get("missing_roles", [])]
        log.failed(
            TEST_LOG_MSGS["s3_fail"].format(
                count=len(missing_names), missing=missing_names
            ),
            details
        )
        pytest.fail(
            TEST_ASSERT_MSGS["s3_images_failed"].format(error=result.get("error", ""))
        )


# =============================================================================
# TEST 26: Build Pipeline Final Result
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_auto
@pytest.mark.order(26)
def test_build_pipeline_result(host):
    """Final summary of build pipeline results."""
    log = TestLogger(TEST_NAMES["build_pipeline_result"])
    skip_if_build_stream_not_enabled(host, log)
    _skip_if_build_not_triggered(log)

    stages = _get_build_stages()
    details_lines = [
        f"Pipeline ID: {_build_state.get('pipeline_id', 'N/A')}",
        f"Job ID: {_build_state.get('job_id', 'N/A')}",
        f"Stages monitored: {len(_build_state['stage_results'])}/{len(stages)}",
        "",
    ]

    all_passed = True
    for stage in stages:
        if stage in _build_state["stage_results"]:
            result = _build_state["stage_results"][stage]
            state = result.get("stage_state", "UNKNOWN")
            elapsed = result.get("elapsed", 0)
            elapsed_str = f"{elapsed // 60}m{elapsed % 60:02d}s"
            if state == STAGE_STATE_COMPLETED:
                details_lines.append(f"  PASS {stage} ({elapsed_str})")
            else:
                details_lines.append(f"  FAIL {stage} ({elapsed_str}): {result.get('error', '')}")
                all_passed = False
        elif stage not in _build_state.get("catalog_architectures", []) and stage.startswith("build-image-"):
            arch = stage.replace("build-image-", "")
            if arch not in _build_state.get("catalog_architectures", []):
                details_lines.append(f"  SKIP {stage} (not in catalog)")
            else:
                details_lines.append(f"  N/A  {stage}")
                all_passed = False
        else:
            details_lines.append(f"  N/A  {stage}")
            all_passed = False

    details = "\n".join(details_lines)

    if all_passed:
        log.passed(TEST_LOG_MSGS["pipeline_result_ok"], details)
    else:
        log.failed(TEST_LOG_MSGS["pipeline_result_fail"], details)
        pytest.fail("Build pipeline did not complete successfully")
