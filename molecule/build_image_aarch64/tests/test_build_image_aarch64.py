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
1. Verify functional_groups_config.yml exists and contains all roles/groups from pxe_mapping
2. Verify base and compute images are available in regctl registry
3. Verify all 3 images (initramfs, vmlinuz, rhel) are pushed to S3 bucket
4. Verify all expected packages are installed in S3 images
"""

import pytest
from automation_library.core import TestLogger
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


# Architecture constant for this test module
ARCH = "aarch64"


# =============================================================================
# FUNCTIONAL GROUP VALIDATION TESTS
# =============================================================================

def test_functional_group_content(host):
    """Verify functional_groups_config.yml exists and contains all roles/groups from pxe_mapping."""
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

def test_regctl_registry_images(host):
    """Validate that base and compute images are available in regctl registry."""
    log = TestLogger(TEST_NAMES["regctl_registry_images"])
    result = check_regctl_registry_images(host, arch=ARCH)
    found_count = len(result.get("found_images", []))
    log.check(
        f"Checking regctl registry for {ARCH} base image + "
        f"{found_count} functional group images"
    )

    # Build details
    details_lines = [
        f"Architecture: {ARCH}",
        f"Registry: {result.get('registry_url', 'unknown')}",
    ]
    for img in result.get("found_images", []):
        details_lines.append(f"✓ {img}")
    for img in result.get("missing_images", []):
        details_lines.append(f"✗ {img}: MISSING")
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

def test_s3_bucket_images(host):
    """Verify all images are pushed to S3 bucket for all functional groups."""
    log = TestLogger(TEST_NAMES["s3_bucket_images"])
    image_types = BUILD_IMAGE_VARS["image_types"]
    result = check_s3_bucket_images(host, arch=ARCH)
    group_count = len(result.get("results", []))
    log.check(
        f"Checking S3 bucket for {group_count} {ARCH} functional groups x "
        f"{len(image_types)} images each"
    )

    # Build details for all functional groups with actual image names and sizes
    details_lines = [f"Architecture: {ARCH}"]
    for fg_result in result.get("results", []):
        fg = fg_result["functional_group"]
        if fg_result["success"]:
            details_lines.append(f"✓ {fg}:")
            for img in fg_result.get("image_details", []):
                details_lines.append(f"    {img['type']}: {img['filename']} ({img['size_human']})")
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

def test_all_image_packages(host):
    """Verify all packages are installed in ALL S3 images by mounting and checking RPM db."""
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
