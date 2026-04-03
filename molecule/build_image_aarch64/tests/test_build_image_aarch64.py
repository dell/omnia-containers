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
Build Image aarch64 Test Cases.

This module contains pytest test cases for verifying build_image_aarch64 deployment.

Test cases:
1. Verify build_stream pipeline stage 'build-image-aarch64' COMPLETED (when enabled)
2. Verify functional_groups_config.yml exists and contains all roles/groups from pxe_mapping
3. Verify base and compute images are available in regctl registry
4. Verify all 3 images (initramfs, vmlinuz, rhel) are pushed to S3 bucket
5. Verify all expected packages are installed in S3 images

All tests skip gracefully when no aarch64 functional groups are found in pxe_mapping.
"""

import pytest
from automation_library.core import (
    TestLogger,
    get_functional_groups_from_pxe_mapping,
    is_build_stream_enabled,
    get_build_stream_job_id,
    STAGE_BUILD_IMAGE_AARCH64,
)
from molecule.conftest import build_stream_job_state
from automation_library.build_image.vars import BUILD_IMAGE_VARS
from automation_library.build_image.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.build_image.functions import (
    check_functional_group_file_exists,
    check_functional_group_content,
    check_regctl_registry_images,
    check_s3_bucket_images,
    verify_all_image_packages,
)


def _has_aarch64_groups(host) -> bool:
    """Return True when at least one aarch64 functional group is in pxe_mapping."""
    all_groups = get_functional_groups_from_pxe_mapping(host)
    return any("aarch64" in fg for fg in all_groups)


# Architecture constant for this test module
ARCH = "aarch64"

# =============================================================================
# 1. BUILD STREAM JOB STAGE VALIDATION (first test — gates all others)
# =============================================================================

@pytest.mark.order(1)
def test_build_stream_job_stage(host):
    """
    Test 1: When build_stream is enabled, verify the build-image-aarch64 pipeline
    stage completed successfully before running any other checks.

    - Reads build_stream_job_id override from user_config.yml if set.
    - Falls back to the latest job in build_stream_db otherwise.
    - Prints the exact DB stage_state if not COMPLETED.
    - Skipped when build_stream is disabled or no aarch64 FGs in pxe_mapping.
    - If job not COMPLETED, all remaining tests are SKIPPED (not failed).
    """
    if not _has_aarch64_groups(host):
        pytest.skip("No aarch64 functional groups found in pxe_mapping — skipping aarch64 tests")

    stage = STAGE_BUILD_IMAGE_AARCH64
    if not is_build_stream_enabled(host):
        pytest.skip(LOG_MSGS["build_stream_disabled_skip"])

    log = TestLogger(TEST_NAMES["build_stream_job_stage"].format(stage=stage))

    result = get_build_stream_job_id(host, stage_name=stage)
    job_id = result.get("job_id") or "unknown"
    job_state = result.get("job_state") or "NOT FOUND"
    source = result.get("source", "database")

    # Set shared state so autouse fixture in conftest.py can skip remaining tests
    build_stream_job_state["checked"] = True
    build_stream_job_state["success"] = result["success"]
    build_stream_job_state["job_id"] = job_id
    build_stream_job_state["job_state"] = job_state
    build_stream_job_state["error"] = result.get("error", "")

    log.check(LOG_MSGS["build_stream_job_checking"].format(stage=stage, source=source))

    if result["success"]:
        log.passed(
            LOG_MSGS["build_stream_job_ok"].format(
                stage=stage, job_id=job_id, source=source
            )
        )
    else:
        log.failed(
            LOG_MSGS["build_stream_job_failed"].format(
                stage=stage, state=job_state, job_id=job_id
            ),
            result.get("error", "")
        )
        # Use pytest.fail() so this test shows as FAILED (not skipped)
        # Remaining tests will be SKIPPED via autouse fixture
        pytest.fail(
            ASSERT_MSGS["build_stream_job_stage_failed"].format(
                stage=stage, job_id=job_id, state=job_state
            )
        )


# =============================================================================
# 2. FUNCTIONAL GROUP VALIDATION TESTS
# =============================================================================

@pytest.mark.order(2)
def test_functional_group_content(host):
    """Verify functional_groups_config.yml exists and contains all roles/groups from pxe_mapping."""
    if not _has_aarch64_groups(host):
        pytest.skip("No aarch64 functional groups found in pxe_mapping — skipping aarch64 tests")

    log = TestLogger(TEST_NAMES["functional_group_content"])
    file_path = BUILD_IMAGE_VARS["functional_group_file_path"]

    # Check file exists first - fail with clear message if not
    file_exists = check_functional_group_file_exists(host)
    if not file_exists["success"]:
        log.failed(
            LOG_MSGS["functional_group_file_not_found"].format(path=file_path),
            file_exists["error"]
        )
        assert False, ASSERT_MSGS["functional_group_file_not_found"].format(
            path=file_path, status=file_exists["status"]
        )

    result = check_functional_group_content(host, arch=ARCH)
    found_groups = result.get("found_functional_groups", [])
    missing_groups = result.get("missing_functional_groups", [])
    expected_groups = found_groups + missing_groups
    log.check(
        f"Validating content against {len(expected_groups)} {ARCH} "
        "functional groups from pxe_mapping"
    )

    if result["success"]:
        log.passed(
            LOG_MSGS["functional_group_content_ok"].format(count=len(expected_groups)),
            result["details"]
        )
    else:
        missing_all = missing_groups + result.get("missing_group_names", [])
        log.failed(
            LOG_MSGS["functional_group_content_missing"].format(count=len(missing_all)),
            result["error"]
        )

    assert result["success"], ASSERT_MSGS["functional_group_content_missing"].format(
        missing=", ".join(missing_groups + result.get("missing_group_names", [])),
        expected_list="\n".join([f"║   - {g}" for g in expected_groups])
    )


# =============================================================================
# REGCTL REGISTRY VALIDATION TESTS
# =============================================================================

@pytest.mark.order(3)
def test_regctl_registry_images(host):
    """Validate that base and compute images are available in regctl registry."""
    if not _has_aarch64_groups(host):
        pytest.skip("No aarch64 functional groups found in pxe_mapping — skipping aarch64 tests")

    log = TestLogger(TEST_NAMES["regctl_registry_images"])
    result = check_regctl_registry_images(host, arch=ARCH)
    found_count = len(result.get("found_images", []))
    registry_url = result.get('registry_url', 'unknown')
    build_stream_on = is_build_stream_enabled(host)

    mode_str = "build_stream ENABLED" if build_stream_on else "build_stream DISABLED"
    log.check(
        f"Checking regctl registry for {ARCH} base image + "
        f"{found_count} functional group images | {mode_str}"
    )

    # Build details with FULL registry image paths (hostname:port/image-name)
    details_lines = [
        f"Architecture: {ARCH}",
        f"Registry: {registry_url}",
        f"Mode: {mode_str} (regctl images do NOT contain UUID in name)",
    ]
    for img in result.get("found_images", []):
        # Show full registry path: hostname:port/image-name
        details_lines.append(f"✓ {registry_url}/{img}")
    for img in result.get("missing_images", []):
        details_lines.append(f"✗ {registry_url}/{img}: MISSING")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(LOG_MSGS["regctl_registry_images_ok"], details)
    else:
        log.failed(
            LOG_MSGS["regctl_registry_images_missing"].format(count=len(result["missing_images"])),
            details
        )

    assert result["success"], ASSERT_MSGS["regctl_registry_images_missing"].format(
        registry_url=result.get("registry_url", "unknown"),
        count=len(result["missing_images"]),
        missing_list="\n".join([f"║   - {img}" for img in result["missing_images"]])
    )


# =============================================================================
# S3 BUCKET VALIDATION TESTS
# =============================================================================

@pytest.mark.order(4)
def test_s3_bucket_images(host):
    """Verify all images are pushed to S3 bucket for all functional groups."""
    if not _has_aarch64_groups(host):
        pytest.skip("No aarch64 functional groups found in pxe_mapping — skipping aarch64 tests")

    log = TestLogger(TEST_NAMES["s3_bucket_images"])
    image_types = BUILD_IMAGE_VARS["image_types"]
    result = check_s3_bucket_images(host, arch=ARCH)

    # check_s3_bucket_images already returns skipped=True if no aarch64 groups
    if result.get("skipped"):
        log.skipped(result["details"])
        pytest.skip(result["details"])

    group_count = len(result.get("results", []))
    job_id = result.get("job_id")
    build_stream_on = is_build_stream_enabled(host)

    mode_str = (
        f"build_stream ENABLED (job UUID: {job_id})"
        if build_stream_on
        else "build_stream DISABLED (no UUID)"
    )
    log.check(
        f"Checking S3 bucket for {group_count} {ARCH} functional groups x "
        f"{len(image_types)} images each | {mode_str}"
    )

    # Build details for all functional groups with FULL S3 paths (shows UUID when build_stream enabled)
    details_lines = [f"Architecture: {ARCH}", f"Mode: {mode_str}"]
    for fg_result in result.get("results", []):
        fg = fg_result["functional_group"]
        if fg_result["success"]:
            details_lines.append(f"✓ {fg}:")
            for img in fg_result.get("image_details", []):
                # Show meaningful directory name with UUID (trimmed from full S3 path)
                display_path = img.get('display_path', img['filename'])
                details_lines.append(f"    {img['type']}: {display_path} ({img['size_human']})")
        else:
            missing_imgs = fg_result.get("missing_images", [])
            details_lines.append(f"✗ {fg}: missing {', '.join(missing_imgs)}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(LOG_MSGS["s3_bucket_images_ok"], details)
    else:
        failed_groups = [r for r in result["results"] if not r["success"]]
        log.failed(
            LOG_MSGS["s3_bucket_images_missing"].format(count=len(failed_groups)),
            details
        )
        assert_details = []
        for fg_res in failed_groups:
            fg_name = fg_res['functional_group']
            fg_missing = ', '.join(fg_res['missing_images'])
            assert_details.append(f"║   - {fg_name}: missing {fg_missing}")
        assert False, ASSERT_MSGS["s3_bucket_images_missing"].format(
            group="multiple groups",
            missing_list="\n".join(assert_details)
        )


# =============================================================================
# IMAGE PACKAGE VERIFICATION TESTS
# =============================================================================

@pytest.mark.order(5)
def test_all_image_packages(host):
    """Verify all packages are installed in ALL S3 images by mounting and checking RPM db."""
    if not _has_aarch64_groups(host):
        pytest.skip("No aarch64 functional groups found in pxe_mapping — skipping aarch64 tests")

    log = TestLogger(TEST_NAMES["image_packages"])
    result = verify_all_image_packages(host, arch=ARCH)

    # Check for prerequisite failure (squashfs-tools not installed)
    if result.get("prerequisite_failed"):
        error_msg = result.get("error", "Unknown error")
        log.failed("Prerequisite check failed", error_msg)
        pytest.fail(f"Prerequisite check failed:\n{error_msg}")

    # Build details showing ALL packages (installed/not installed) for each image
    details_lines = [f"Architecture: {ARCH}"]
    for fg_result in result.get("results", []):
        fg = fg_result["functional_group"]
        expected = fg_result.get("expected_count", 0)
        found = fg_result.get("found_count", 0)
        base_count = fg_result.get("base_package_count", 0)
        compute_count = fg_result.get("compute_package_count", 0)

        status = "✓" if fg_result["success"] else "✗"
        details_lines.append(f"{status} {fg}: {found}/{expected} packages")
        details_lines.append(f"    (base: {base_count}, compute: {compute_count})")

        # Show ALL packages with their status
        pkg_details = fg_result.get("package_details", [])
        installed = [p for p in pkg_details if p["status"] == "installed"]
        not_installed = [p for p in pkg_details if p["status"] == "missing"]

        if installed:
            details_lines.append(f"    INSTALLED ({len(installed)}):")
            for pkg in installed:
                details_lines.append(f"      ✓ {pkg['expected']} → {pkg['found']}")

        if not_installed:
            details_lines.append(f"    NOT INSTALLED ({len(not_installed)}):")
            for pkg in not_installed:
                details_lines.append(f"      ✗ {pkg['expected']}")

        if fg_result.get("error") and not fg_result["success"]:
            details_lines.append(f"    Error: {fg_result['error']}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(LOG_MSGS["image_packages_ok"], details)
    else:
        failed_count = result.get("failed_groups", 0)
        log.failed(LOG_MSGS["image_packages_failed"].format(count=failed_count), details)

    assert result["success"], result.get("error", "Image package verification failed")
