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
Build Stream - Cleanup Pipeline Test Cases.

Test cases for cleanup pipeline automation:
1. Verify image groups exist for cleanup
2. Trigger cleanup pipeline (PIPELINE_TYPE=cleanup), auto-select latest BUILT group
3. Verify DB image_groups status updated to CLEANED
4. Verify S3 images deleted (3 per role: 1 rootfs + 2 EFI)
5. Verify registry images deleted via regctl

Markers:
    - sanity: Basic sanity tests
    - cleanup_manual: Cleanup pipeline tests (manual trigger only)
"""

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    trigger_cleanup_pipeline,
    select_image_for_cleanup,
    play_cleanup_stage_job,
    wait_for_cleanup_completion,
    get_catalog_roles,
    get_image_groups_for_job,
    get_all_image_groups,
    verify_registry_images,
    verify_s3_boot_images,
    SKIP_MSGS,
)


# =============================================================================
# MODULE-LEVEL STATE
# =============================================================================

_cleanup_state = {
    "job_id": None,
    "pipeline_id": None,
    "image_group_id": None,
    "cleanup_started": False,
    "cleanup_completed": False,
    "pre_cleanup_roles": [],
    "pre_cleanup_image_key": "",
}


def _skip_if_not_started(log):
    """Skip test if cleanup was not started."""
    if not _cleanup_state["cleanup_started"]:
        log.skipped("Cleanup not started", "Cleanup pipeline not triggered")
        pytest.skip("Cleanup pipeline not triggered")


def _skip_if_not_completed(log):
    """Skip test if cleanup did not complete."""
    if not _cleanup_state["cleanup_completed"]:
        log.skipped("Cleanup not completed", "Cleanup did not finish successfully")
        pytest.skip("Cleanup did not complete")


# =============================================================================
# TEST 1: VERIFY IMAGE GROUPS EXIST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.cleanup_manual
@pytest.mark.order(50)
def test_image_groups_for_cleanup(host):
    """
    Test 1: Verify image groups exist that can be cleaned up.

    Checks for BUILT image groups and captures pre-cleanup metadata.
    """
    log = TestLogger("Image Groups for Cleanup")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    log.check("Checking for image groups available for cleanup")

    result = get_all_image_groups(host)

    if not result["success"]:
        log.failed(
            "Failed to query image groups",
            result.get("error", "Database query failed")
        )
        pytest.fail(f"Failed to query image groups: {result.get('error', '')}")

    if not result["image_groups"]:
        log.passed(
            "No image groups in database yet",
            "Build pipeline needs to complete successfully first."
        )
        return

    built_groups = [g for g in result["image_groups"] if g["status"] == "BUILT"]
    cleaned_groups = [g for g in result["image_groups"] if g["status"] == "CLEANED"]

    details_lines = ["Image groups in database:"]
    for group in result["image_groups"]:
        sym = "B" if group["status"] == "BUILT" else "C" if group["status"] == "CLEANED" else "?"
        details_lines.append(
            f"  [{sym}] {group['id']} (status: {group['status']}, "
            f"job: {group['job_id'][:8]}...)"
        )

    if built_groups:
        latest = sorted(built_groups, key=lambda x: x.get("created_at", ""), reverse=True)[0]
        _cleanup_state["image_group_id"] = latest["id"]
        _cleanup_state["job_id"] = latest["job_id"]

        roles_result = get_catalog_roles(host, latest["job_id"])
        if roles_result["success"]:
            _cleanup_state["pre_cleanup_roles"] = roles_result["roles"]
            _cleanup_state["pre_cleanup_image_key"] = roles_result["image_key"]

        log.passed(
            f"Found {len(built_groups)} image group(s) available for cleanup",
            "\n".join(details_lines)
        )
    elif cleaned_groups:
        log.passed(
            f"All {len(cleaned_groups)} image group(s) already cleaned",
            "\n".join(details_lines)
        )
    else:
        log.passed(
            f"Found {len(result['image_groups'])} image group(s) with other status",
            "\n".join(details_lines)
        )


# =============================================================================
# TEST 2: TRIGGER CLEANUP PIPELINE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.cleanup_manual
@pytest.mark.order(51)
def test_trigger_cleanup_pipeline(host):
    """
    Test 2: Trigger cleanup pipeline with PIPELINE_TYPE=cleanup.

    Auto-selects the latest BUILT image group and waits for cleanup to complete.
    """
    import sys
    log = TestLogger("Trigger Cleanup Pipeline")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    image_group_id = _cleanup_state.get("image_group_id")
    if not image_group_id:
        log.skipped(
            "No BUILT image groups",
            "No BUILT image groups found. Build pipeline must complete successfully first."
        )
        pytest.skip("No BUILT image groups to clean")

    log.check("Triggering cleanup pipeline with PIPELINE_TYPE=cleanup")

    def _log_callback(msg):
        print(f"    │ {msg}", flush=True)
        sys.stdout.flush()

    result = trigger_cleanup_pipeline(host, log_callback=_log_callback)

    if not result["success"]:
        log.failed(
            f"Failed to trigger cleanup pipeline: {result['error']}",
            result.get("details", "")
        )
        pytest.fail(f"Failed to trigger cleanup pipeline: {result['error']}")

    _cleanup_state["cleanup_started"] = True
    _cleanup_state["pipeline_id"] = result["pipeline_id"]

    _log_callback("Auto-selecting image group for cleanup...")
    select_result = select_image_for_cleanup(
        host, result["pipeline_id"], log_callback=_log_callback
    )
    if select_result["success"]:
        _cleanup_state["image_group_id"] = select_result["image_group_id"]
        _log_callback(f"Image group selected: {select_result['image_group_id']}")

        # After selecting image, play the cleanup stage job (it's manual)
        _log_callback("Playing cleanup stage job...")
        cleanup_job_result = play_cleanup_stage_job(host, result["pipeline_id"], log_callback=_log_callback)
        if cleanup_job_result["success"]:
            _log_callback("Cleanup stage started successfully")
        else:
            _log_callback(f"⚠ Failed to start cleanup stage: {cleanup_job_result['error']}")
            _log_callback("You may need to manually play 'cleanup' job in GitLab")

        _log_callback("Waiting for cleanup to complete and DB to update...")
        cleanup_result = wait_for_cleanup_completion(
            host, select_result["image_group_id"],
            timeout=300, log_callback=_log_callback
        )
        if cleanup_result["success"]:
            _cleanup_state["cleanup_completed"] = True
            _log_callback(
                f"Image group {select_result['image_group_id']} cleaned successfully"
            )
        else:
            _log_callback(f"Cleanup completion check: {cleanup_result['error']}")
    else:
        _log_callback(f"Image selection failed: {select_result['error']}")
        _log_callback("Cleanup may require manual image selection in GitLab")

    log.passed(
        f"Cleanup pipeline {result['pipeline_id']} triggered",
        result["details"]
    )


# =============================================================================
# TEST 3: VERIFY IMAGE GROUPS CLEANED IN DB
# =============================================================================

@pytest.mark.sanity
@pytest.mark.cleanup_manual
@pytest.mark.order(52)
def test_image_groups_cleaned(host):
    """Test 3: Verify image groups have CLEANED status after cleanup."""
    log = TestLogger("Image Groups Cleaned (DB)")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_started(log)

    job_id = _cleanup_state["job_id"]
    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    log.check(f"Verifying image group status for job {job_id}")

    result = get_image_groups_for_job(host, job_id)

    if not result["success"] or not result["image_groups"]:
        log.failed(
            "Failed to get image groups",
            result.get("error", "No image groups found")
        )
        pytest.fail("Failed to get image groups")

    cleaned_groups = [g for g in result["image_groups"] if g["status"] == "CLEANED"]

    details_lines = ["Image groups after cleanup:"]
    for group in result["image_groups"]:
        sym = "CLEANED" if group["status"] == "CLEANED" else group["status"]
        details_lines.append(f"  [{sym}] {group['id']}")

    if cleaned_groups:
        log.passed(
            f"Found {len(cleaned_groups)} image group(s) with CLEANED status",
            "\n".join(details_lines)
        )
    else:
        log.failed(
            "No image groups with CLEANED status",
            "\n".join(details_lines)
        )
        pytest.fail("No image groups with CLEANED status after cleanup")


# =============================================================================
# TEST 4: VERIFY S3 IMAGES DELETED (3 per role)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.cleanup_manual
@pytest.mark.order(53)
def test_s3_images_deleted(host):
    """
    Test 4: Verify S3 boot images are deleted after cleanup.

    Checks that 3 files per role (1 rootfs + 2 EFI) are no longer
    present in s3://boot-images/ for the cleaned job.
    """
    log = TestLogger("S3 Images Deleted")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_started(log)

    job_id = _cleanup_state["job_id"]
    roles = _cleanup_state.get("pre_cleanup_roles", [])
    image_key = _cleanup_state.get("pre_cleanup_image_key", "")

    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    if not roles:
        roles_result = get_catalog_roles(host, job_id)
        if roles_result["success"]:
            roles = roles_result["roles"]
            image_key = roles_result["image_key"]

    if not roles:
        log.skipped("No catalog roles found", "Cannot verify S3 without roles")
        pytest.skip("No catalog roles found for S3 verification")

    log.check(f"Verifying S3 images are deleted for {len(roles)} roles")

    result = verify_s3_boot_images(host, job_id, roles, image_key)

    # After cleanup, we expect images to be MISSING (result should fail)
    if not result["success"] and len(result["missing_roles"]) == len(roles):
        details_lines = [f"All {len(roles)} roles' S3 images successfully deleted:"]
        for m in result["missing_roles"]:
            details_lines.append(
                f"  [DELETED] {m['role']} (rootfs: {m['rootfs']}, efi: {m['efi_files']})"
            )
        log.passed(
            f"S3 images deleted for all {len(roles)} roles",
            "\n".join(details_lines)
        )
    elif result["success"]:
        details_lines = ["S3 images still present after cleanup:"]
        for f in result["found_roles"]:
            details_lines.append(
                f"  [STILL EXISTS] {f['role']} "
                f"(rootfs: {f['rootfs']}, efi: {f['efi_files']})"
            )
        log.failed(
            f"S3 images NOT deleted: {len(result['found_roles'])} roles still have files",
            "\n".join(details_lines)
        )
        pytest.fail(
            f"S3 images not deleted for {len(result['found_roles'])} roles"
        )
    else:
        deleted = result.get("missing_roles", [])
        remaining = result.get("found_roles", [])
        details_lines = [f"Partial deletion: {len(deleted)}/{len(roles)} roles deleted"]
        for m in deleted:
            details_lines.append(
                f"  [DELETED] {m['role']} (rootfs: {m['rootfs']}, efi: {m['efi_files']})"
            )
        for f in remaining:
            details_lines.append(
                f"  [STILL EXISTS] {f['role']} "
                f"(rootfs: {f['rootfs']}, efi: {f['efi_files']})"
            )
        log.failed(
            f"Only {len(deleted)}/{len(roles)} roles' S3 images deleted",
            "\n".join(details_lines)
        )
        pytest.fail(
            f"S3 images not fully deleted: {len(remaining)} roles still have files"
        )


# =============================================================================
# TEST 5: VERIFY REGISTRY IMAGES DELETED (regctl)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.cleanup_manual
@pytest.mark.order(54)
def test_registry_images_deleted(host):
    """
    Test 5: Verify registry images are deleted after cleanup.

    Uses regctl repo ls to confirm that container images for the cleaned
    job are no longer listed in the registry.
    """
    log = TestLogger("Registry Images Deleted")

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    _skip_if_not_started(log)

    job_id = _cleanup_state["job_id"]
    roles = _cleanup_state.get("pre_cleanup_roles", [])
    image_key = _cleanup_state.get("pre_cleanup_image_key", "")

    if not job_id:
        log.skipped(SKIP_MSGS["no_job_id"], "No job_id available")
        pytest.skip(SKIP_MSGS["no_job_id"])

    if not roles:
        roles_result = get_catalog_roles(host, job_id)
        if roles_result["success"]:
            roles = roles_result["roles"]
            image_key = roles_result["image_key"]

    if not roles:
        log.skipped("No catalog roles found", "Cannot verify registry without roles")
        pytest.skip("No catalog roles found for registry verification")

    log.check(f"Verifying registry images are deleted for {len(roles)} roles")

    result = verify_registry_images(host, job_id, roles, image_key)

    # After cleanup, we expect images to be MISSING
    if not result["success"] and len(result["missing"]) == len(roles):
        details_lines = [
            f"All {len(roles)} roles' registry images successfully deleted",
            f"Registry: {result.get('registry_url', 'N/A')}",
        ]
        for role in result["missing"]:
            details_lines.append(f"  [DELETED] {role}")
        log.passed(
            f"Registry images deleted for all {len(roles)} roles",
            "\n".join(details_lines)
        )
    elif result["success"]:
        details_lines = ["Registry images still present after cleanup:"]
        for f in result["found"]:
            details_lines.append(f"  [STILL EXISTS] {f['role']} → {f['repo']}")
        log.failed(
            f"Registry images NOT deleted: {len(result['found'])} roles still exist",
            "\n".join(details_lines)
        )
        pytest.fail(
            f"Registry images not deleted for {len(result['found'])} roles"
        )
    else:
        deleted = result.get("missing", [])
        remaining = result.get("found", [])
        details_lines = [f"Partial deletion: {len(deleted)}/{len(roles)} roles deleted"]
        for role in deleted:
            details_lines.append(f"  [DELETED] {role}")
        for f in remaining:
            details_lines.append(f"  [STILL EXISTS] {f['role']} → {f['repo']}")
        log.failed(
            f"Only {len(deleted)}/{len(roles)} roles' registry images deleted",
            "\n".join(details_lines)
        )
        pytest.fail(
            f"Registry images not fully deleted: {len(remaining)} roles still exist"
        )
