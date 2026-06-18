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
and checks that configuration files are correctly restored.

PREREQUISITES:
  - omnia_core is running at the upgraded version (e.g. 2.2.0.0)
  - A backup from the upgrade exists
  - The original image (e.g. omnia_core:2.1) is available locally

Test cases (executed in order):
1. Verify rollback image (omnia_core:2.1) is available
2. Download omnia.sh and run omnia.sh --rollback
3. Verify omnia_core rolled back to original version (2.1.0.0)
4. Verify project_default files restored (md5sum backup vs current)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.rollback.functions import (
    check_rollback_image,
    download_omnia_sh_for_rollback,
    run_omnia_rollback,
    verify_rollback_container,
    verify_project_default_restored,
)
from automation_library.rollback.vars import ROLLBACK_VARS
from automation_library.rollback.messages import (
    ROLLBACK_TEST_NAMES as TEST_NAMES,
    ROLLBACK_LOG_MSGS as LOG,
    ROLLBACK_ASSERT_MSGS as ASSERT,
    ROLLBACK_SKIP_MSGS as SKIP,
)


# =============================================================================
# MODULE-LEVEL GATES
# =============================================================================

_rollback_image_ok: bool = False
_rollback_passed: bool = False


# =============================================================================
# TC-1: CHECK ROLLBACK IMAGE AVAILABLE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_check_rollback_image(host):
    """
    Test Case 1: Verify the rollback target image exists locally.

    If the image is not found, all subsequent tests are skipped because
    the rollback cannot proceed.
    """
    global _rollback_image_ok
    tag = ROLLBACK_VARS["rollback_image_tag"]

    log = TestLogger(TEST_NAMES["check_rollback_image"].format(tag=tag))
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
# TC-2: DOWNLOAD OMNIA.SH + RUN ROLLBACK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_run_rollback(host):
    """
    Test Case 2: Download a fresh omnia.sh and execute --rollback.

    Steps:
    - Delete any existing omnia.sh in clone_path
    - Download from configured URL
    - Run omnia.sh --rollback with 'y' confirmation
    - Poll every 10s, show progress
    - PASS if rc=0
    """
    global _rollback_passed

    if not _rollback_image_ok:
        pytest.skip(SKIP["image_not_available"])

    tail_lines = ROLLBACK_VARS["tail_lines"]
    omnia_sh_path = ROLLBACK_VARS["omnia_sh_path"]

    log = TestLogger(TEST_NAMES["run_rollback"])

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
# TC-3: VERIFY CONTAINER ROLLED BACK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_verify_rollback_container(host):
    """
    Test Case 3: Verify omnia_core is running the pre-upgrade version.

    Checks container is running, image tag matches, and omnia_version
    in metadata matches the original (current_version).
    """
    if not _rollback_passed:
        pytest.skip(SKIP["rollback_failed"])

    expected_ver = ROLLBACK_VARS["current_version"]

    log = TestLogger(
        TEST_NAMES["verify_rollback_container"].format(version=expected_ver)
    )
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
        print(
            f"    {LOG['container_version_ok'].format(version=result['version'], expected=expected_ver)}",
            flush=True,
        )
    else:
        print(
            f"    {LOG['container_version_fail'].format(expected=expected_ver, actual=result.get('version', 'unknown'))}",
            flush=True,
        )

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
# TC-4: VERIFY PROJECT_DEFAULT FILES RESTORED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_verify_project_default(host):
    """
    Test Case 4: After rollback, project_default files should match backup.

    Uses md5sum to compare every file in the backup's project_default/
    against the current /opt/omnia/input/project_default/.  After a
    correct rollback, all files must match.
    """
    if not _rollback_passed:
        pytest.skip(SKIP["rollback_failed"])

    log = TestLogger(TEST_NAMES["verify_project_default"])
    log.check(LOG["checking_project_default"])

    result = verify_project_default_restored(host)
    files = result.get("files", [])

    if not files:
        log.failed("No project_default files found", result["error"])
        pytest.fail(result["error"])

    # Build details — collect results silently, show in final output
    lines = []
    for f in files:
        lines.append(
            LOG["file_ok" if f["match"] == "✓" else "file_mismatch"]
            .format(name=f["name"])
        )
    details = "\n".join(lines)

    matched = sum(1 for f in files if f["match"] == "✓")
    total = len(files)
    mismatched = total - matched

    if result["success"]:
        log.passed(
            f"All {total} project_default files match (md5sum)",
            details,
        )
    else:
        log.failed(
            f"{mismatched}/{total} project_default files differ",
            details,
        )
        pytest.fail(
            ASSERT["project_default_mismatch"].format(
                mismatch=mismatched, total=total,
            )
        )
