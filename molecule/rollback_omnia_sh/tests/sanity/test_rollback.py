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
Omnia Core Rollback Test Cases.

Verifies the omnia.sh --rollback workflow after an upgrade has been
performed.  Restores the omnia_core container to the original version
and checks that all configuration files are correctly restored.

PREREQUISITES:
  - omnia_core is running at the upgraded version (e.g. 2.2.0.0)
  - A backup from the upgrade exists
  - The original image (e.g. omnia_core:2.1) is available locally

Test cases (executed in order):
 1. Verify rollback precondition (not already at target version)
 2. Verify rollback image (omnia_core:2.1) is available
 3. Download omnia.sh and run omnia.sh --rollback
 4. Verify omnia_core rolled back to original version (2.1.0.0)
 5. Verify project_default files restored (md5sum)
 6. Verify quadlet files restored (md5sum)
 7. Verify boot files restored (md5sum)
 8. Verify cloud-init files restored (md5sum)
 9. Verify nodes files restored (md5sum)
10. Verify image definition files restored (md5sum)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.upgrade_and_rollback.functions import (
    verify_rollback_precondition,
    check_rollback_image,
    download_omnia_sh_for_rollback,
    run_omnia_rollback,
    verify_rollback_container,
    verify_rollback_backup_md5sum,
)
from automation_library.upgrade_and_rollback.vars import ROLLBACK_VARS
from automation_library.upgrade_and_rollback.messages import (
    ROLLBACK_TEST_NAMES as TEST_NAMES,
    ROLLBACK_LOG_MSGS as LOG,
    ROLLBACK_ASSERT_MSGS as ASSERT,
    ROLLBACK_SKIP_MSGS as SKIP,
)


# =============================================================================
# MODULE-LEVEL GATES
# =============================================================================

_rollback_needed: bool = False
_rollback_image_ok: bool = False
_rollback_passed: bool = False


# =============================================================================
# TC-1: VERIFY ROLLBACK PRECONDITION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_rollback_precondition(host):
    """
    Test Case 1: Verify rollback is actually needed.

    States:
    - not_running: Container not running → skip all tests
    - fresh_install: At current_version without previous_omnia_version → skip all
    - rollback_needed: At new_version with previous_version → proceed
    - already_rolled_back: At current_version → skip all tests
    """
    global _rollback_needed

    target = ROLLBACK_VARS["current_version"]
    new_ver = ROLLBACK_VARS["new_version"]

    log = TestLogger(
        TEST_NAMES["precondition"].format(
            new_version=new_ver, target_version=target,
        )
    )
    log.check(
        LOG["checking_precondition"].format(
            new_version=new_ver, target_version=target,
        )
    )

    result = verify_rollback_precondition(host)
    state = result.get("state", "unknown")

    # Config error
    if state == "config_error":
        log.failed("Config incomplete", result["error"])
        pytest.fail(ASSERT["config_missing"])

    # Container not running - skip all with detailed service status
    if state == "not_running":
        log.skipped(
            SKIP["container_not_running"],
            result.get("error", "Container not running"),
        )
        pytest.skip(SKIP["container_not_running"])

    # Fresh install at current_version (never upgraded) - fail
    if state == "fresh_install":
        log.failed(
            "Cannot rollback from fresh install",
            result["error"],
        )
        pytest.fail(
            ASSERT["fresh_install"].format(version=result["running_version"])
        )

    # Fresh install at new_version (no previous version) - skip all
    if state == "fresh_install_new":
        log.skipped(
            SKIP["fresh_install_new"].format(version=result["running_version"]),
            result["error"],
        )
        pytest.skip(SKIP["fresh_install_new"].format(version=result["running_version"]))

    # Already rolled back - skip all
    if state == "already_rolled_back":
        log.skipped(
            SKIP["not_needed"],
            f"Container already at {target} - no rollback needed",
        )
        pytest.skip(SKIP["not_needed"])

    # Rollback needed - proceed
    if state == "rollback_needed":
        _rollback_needed = True
        prev_ver = result.get("previous_version", "")
        log.passed(
            LOG["precondition_ok"].format(
                running_version=result["running_version"],
                target_version=target,
            ),
            f"✓ Running {result['running_version']}, previous: {prev_ver}\n"
            f"✓ Will rollback to {target}",
        )
        return

    # Unexpected version or unknown state - fail
    log.failed(
        LOG["precondition_unknown"].format(
            running_version=result.get("running_version", "unknown"),
        ),
        result.get("error", "Unknown state"),
    )
    pytest.fail(
        ASSERT["precondition_failed"].format(
            running_version=result.get("running_version", "unknown"),
            new_version=new_ver,
        )
    )


# =============================================================================
# TC-2: CHECK ROLLBACK IMAGE AVAILABLE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_check_rollback_image(host):
    """
    Test Case 2: Verify the rollback target image exists locally.

    If the image is not found, all subsequent tests are skipped because
    the rollback cannot proceed.
    """
    global _rollback_image_ok

    tag = ROLLBACK_VARS["rollback_image_tag"]
    log = TestLogger(TEST_NAMES["check_rollback_image"].format(tag=tag))

    if not _rollback_needed:
        log.skipped(SKIP["not_needed"], "Rollback precondition not met")
        pytest.skip(SKIP["not_needed"])
    log.check(LOG["checking_image"].format(tag=tag))

    result = check_rollback_image(host)

    if result["success"]:
        _rollback_image_ok = True
        log.passed(
            LOG["image_found"].format(tag=tag),
            f"✓ omnia_core:{tag} is available for rollback",
        )
    else:
        log.failed(
            LOG["image_not_found"].format(tag=tag),
            result["error"],
        )
        pytest.fail(ASSERT["image_not_found"].format(tag=tag))


# =============================================================================
# TC-3: DOWNLOAD OMNIA.SH + RUN ROLLBACK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_run_rollback(host):
    """
    Test Case 3: Download a fresh omnia.sh and execute --rollback.

    Steps:
    - Delete any existing omnia.sh in clone_path
    - Download from configured URL (branch → tag fallback)
    - Run omnia.sh --rollback with 'y' confirmation
    - Poll every 10s, show progress
    - PASS if rc=0
    """
    global _rollback_passed

    log = TestLogger(TEST_NAMES["run_rollback"])

    if not _rollback_image_ok:
        log.skipped(SKIP["image_not_available"], "Rollback image check failed")
        pytest.skip(SKIP["image_not_available"])

    tail_lines = ROLLBACK_VARS["tail_lines"]
    omnia_sh_path = ROLLBACK_VARS["omnia_sh_path"]

    # Step 1: Download omnia.sh (branch → tag fallback)
    branch_url = ROLLBACK_VARS["omnia_sh_branch_url"]
    log.check(LOG["downloading_omnia_sh"].format(url=branch_url))

    dl_result = download_omnia_sh_for_rollback(host)
    if not dl_result["success"]:
        log.failed(
            LOG["omnia_sh_fail"].format(error=dl_result["error"]),
            dl_result["error"],
        )
        pytest.fail(
            ASSERT["omnia_sh_download_failed"].format(
                url=dl_result["url"], path=dl_result["path"],
            )
        )
    print(f"    {LOG['omnia_sh_ok']}", flush=True)

    # Step 2: Run rollback
    log.check(LOG["rollback_start"])

    def _progress(elapsed: int) -> None:
        print(
            f"    {LOG['rollback_progress'].format(elapsed=elapsed)}",
            flush=True,
        )

    result = run_omnia_rollback(host, progress_callback=_progress)
    output = result.get("output", "")

    if result["success"]:
        _rollback_passed = True
        details = "✓ Rollback completed successfully"
        if output:
            details += (
                f"\n\n{LOG['output_header'].format(lines=tail_lines)}\n"
                + output
            )
        log.passed(LOG["rollback_ok"], details)
    else:
        fail_details = result["error"]
        if output:
            fail_details += (
                f"\n\n{LOG['output_header'].format(lines=tail_lines)}\n"
                + output
            )
        log.failed(
            LOG["rollback_fail"].format(rc=result.get("rc", "?")),
            fail_details,
        )
        pytest.fail(
            ASSERT["rollback_failed"].format(
                rc=result.get("rc", "?"),
                omnia_sh_path=omnia_sh_path,
            )
        )


# =============================================================================
# TC-4: VERIFY CONTAINER ROLLED BACK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_verify_rollback_container(host):
    """
    Test Case 4: Verify omnia_core is running the pre-upgrade version.

    Checks container is running, image tag matches, and omnia_version
    in metadata matches the original (current_version).
    """
    expected_ver = ROLLBACK_VARS["current_version"]
    log = TestLogger(
        TEST_NAMES["verify_rollback_container"].format(version=expected_ver)
    )

    if not _rollback_passed:
        log.skipped(SKIP["rollback_failed"], "Rollback execution failed")
        pytest.skip(SKIP["rollback_failed"])

    log.check(LOG["checking_container"])

    result = verify_rollback_container(host)

    # Print container info
    print(
        f"    {LOG['container_name'].format(name=result['container_name'])}",
        flush=True,
    )
    print(
        f"    {LOG['container_image'].format(image=result['container_image'])}",
        flush=True,
    )
    print(
        f"    {LOG['container_status'].format(status=result['container_status'])}",
        flush=True,
    )

    # Check running
    if not result["container_running"]:
        log.failed("Container not running after rollback", result["error"])
        pytest.fail(ASSERT["container_not_running"])

    # Check version
    if result["version"] == expected_ver:
        msg = LOG['container_version_ok'].format(
            version=result['version'], expected=expected_ver,
        )
        print(f"    {msg}", flush=True)
    else:
        msg = LOG['container_version_fail'].format(
            expected=expected_ver, actual=result.get('version', 'unknown'),
        )
        print(f"    {msg}", flush=True)

    if result["success"]:
        details = (
            f"✓ Container: {result['container_name']}\n"
            f"✓ Image:     {result['container_image']}\n"
            f"✓ Version:   {result['version']}\n"
            f"Rollback complete: → {expected_ver}"
        )
        log.passed(
            LOG["container_version_ok"].format(
                version=result["version"], expected=expected_ver,
            ),
            details,
        )
    else:
        log.failed(
            LOG["container_version_fail"].format(
                expected=expected_ver,
                actual=result.get("version", "unknown"),
            ),
            result["error"],
        )
        pytest.fail(
            ASSERT["container_wrong_version"].format(
                expected=expected_ver,
                actual=result.get("version", "unknown"),
            )
        )


# =============================================================================
# BACKUP VERIFY HELPER  (shared by TC-5 through TC-10)
# =============================================================================

def _run_rollback_verify(host, category: str):
    """
    Generic test body for rollback backup md5sum verification.

    Args:
        host: Testinfra host object
        category: ROLLBACK_VARS["verify_categories"] key
    """
    cfg = ROLLBACK_VARS["verify_categories"][category]
    backup_dir = cfg["backup_dir"]
    current_dir = cfg["current_dir"]

    log = TestLogger(TEST_NAMES[f"verify_{category}"])

    if not _rollback_passed:
        log.skipped(SKIP["rollback_failed"], "Rollback execution failed")
        pytest.skip(SKIP["rollback_failed"])

    log.check(LOG["checking_category"].format(category=category))

    result = verify_rollback_backup_md5sum(host, category)
    files = result.get("files", [])

    # Check if test was skipped due to missing source directory
    if result.get("skipped", False):
        log.skipped(
            result["error"],
            result["error"],
        )
        pytest.skip(result["error"])

    if not files:
        log.failed(
            LOG["no_files"].format(dir=backup_dir),
            result["error"],
        )
        pytest.fail(
            ASSERT["no_backup_dir"].format(
                category=category, dir=backup_dir,
            )
        )

    # Build details
    lines = []
    for f in files:
        if f["match"] == "✓":
            lines.append(LOG["file_ok"].format(name=f["name"]))
        elif f["match"] == "⊘":
            lines.append(LOG["file_skipped"].format(name=f["name"]))
        else:
            lines.append(LOG["file_mismatch"].format(name=f["name"]))
    details = "\n".join(lines)

    matched = sum(1 for f in files if f["match"] == "✓")
    skipped = sum(1 for f in files if f["match"] == "⊘")
    compared = len(files) - skipped
    mismatched = compared - matched

    if result["success"]:
        log.passed(
            LOG["all_match"].format(count=compared, category=category),
            details,
        )
    else:
        log.failed(
            LOG["some_mismatch"].format(
                mismatch=mismatched, total=compared, category=category,
            ),
            details,
        )
        pytest.fail(
            ASSERT["md5_mismatch"].format(
                mismatch=mismatched,
                total=compared,
                category=category,
                backup_dir=backup_dir,
                current_dir=current_dir,
            )
        )


# =============================================================================
# TC-5: VERIFY PROJECT_DEFAULT FILES RESTORED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_verify_project_default(host):
    """Test Case 5: Verify project_default files restored after rollback."""
    _run_rollback_verify(host, "project_default")


# =============================================================================
# TC-6: VERIFY QUADLET FILES RESTORED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_verify_quadlets(host):
    """Test Case 6: Verify quadlet files restored after rollback."""
    _run_rollback_verify(host, "quadlets")


# =============================================================================
# TC-7: VERIFY BOOT FILES RESTORED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_verify_boot(host):
    """Test Case 7: Verify boot files restored after rollback."""
    _run_rollback_verify(host, "boot")


# =============================================================================
# TC-8: VERIFY CLOUD-INIT FILES RESTORED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_verify_cloudinit(host):
    """Test Case 8: Verify cloud-init files restored after rollback."""
    _run_rollback_verify(host, "cloudinit")


# =============================================================================
# TC-9: VERIFY NODES FILES RESTORED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_verify_nodes(host):
    """Test Case 9: Verify nodes files restored after rollback."""
    _run_rollback_verify(host, "nodes")


# =============================================================================
# TC-10: VERIFY IMAGE DEFINITION FILES RESTORED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_verify_images(host):
    """Test Case 10: Verify image definition files restored after rollback."""
    _run_rollback_verify(host, "images")
