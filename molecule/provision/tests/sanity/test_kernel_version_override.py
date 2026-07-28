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
Kernel Version Override Test Cases.

This module contains pytest test cases for verifying the kernel_version_override
feature in provision_config.yml.

Test Coverage:
- TC-KVO-01: Configuration — verify kernel_version_override is defined in
             /opt/omnia/input/project_default/provision_config.yml.
             If empty, all remaining kernel_override tests are skipped.
- TC-KVO-02: Format validation — verify format matches <major>.<minor>.<patch>-<release>
- TC-KVO-03: S3 boot image match — verify S3 contains vmlinuz/initramfs for the override
- TC-KVO-04: BSS template match — verify BSS templates reference the override kernel
- TC-KVO-05: Node kernel match — verify provisioned nodes run the overridden kernel
             (output: node_name : kernel_version)
- TC-KVO-06: Kernel consistency — verify all nodes run the same kernel version
             (identified from /root/omnia provision/roles/provision_validations analysis)
- TC-KVO-07: Per-functional-group S3 — verify S3 images per functional group match override
             (mirrors /root/omnia provision/roles/provision_validations/tasks/validate_image.yml)

All test cases output Expected and Actual values for clear diagnostics.

Gap Reference: Omnia_2.2_Automation_Coverage_Supplementary_Gaps.md
  Section 8 — Network Configuration Gaps:
  "Kernel version override: kernel_version_override with cross-version kernel — 0 tests"
"""

import pytest
from automation_library.core import TestLogger
from automation_library.provision.functions import (
    get_kernel_version_override,
    validate_kernel_version_override_format,
    verify_kernel_override_in_s3,
    verify_all_nodes_kernel_version,
    verify_bss_kernel_override,
    verify_kernel_consistency,
    verify_per_fg_s3_images,
)
from automation_library.provision.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# TC-KVO-01: KERNEL VERSION OVERRIDE CONFIGURATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(200)
def test_kernel_override_config(host):
    """
    TC-KVO-01: Verify kernel_version_override has a value defined in
    /opt/omnia/input/project_default/provision_config.yml.

    If the value is empty (auto-select mode), all remaining kernel_override
    tests will be skipped.
    """
    log = TestLogger(TEST_NAMES["kernel_override_config"])

    log.check("Reading kernel_version_override from provision_config.yml")
    result = get_kernel_version_override(host)

    if not result["success"]:
        details = (
            f"Expected : kernel_version_override readable from provision_config.yml\n"
            f"Actual   : Failed — {result['error']}"
        )
        log.failed(
            LOG_MSGS["kernel_override_read_fail"].format(error=result["error"]),
            details,
        )
        assert False, ASSERT_MSGS["kernel_override_config_failed"].format(
            details=result["error"]
        )

    kvo = result["kernel_version_override"]

    if result["is_configured"]:
        details = (
            f"Expected : kernel_version_override field exists in provision_config.yml\n"
            f"Actual   : '{kvo}'"
        )
        log.passed(
            LOG_MSGS["kernel_override_read_ok"].format(kvo=kvo),
            details,
        )
    else:
        details = (
            f"Expected : kernel_version_override field exists in provision_config.yml\n"
            f"Actual   : field exists, value is empty (auto-select mode)\n"
            f"Note     : All remaining kernel_override tests will be skipped"
        )
        log.passed(LOG_MSGS["kernel_override_not_set"], details)

    assert result["success"], ASSERT_MSGS["kernel_override_config_failed"].format(
        details=result.get("error", "Unknown error")
    )


# =============================================================================
# TC-KVO-02: KERNEL VERSION OVERRIDE FORMAT VALIDATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(201)
def test_kernel_override_format(host):
    """
    TC-KVO-02: Verify kernel_version_override format is valid.

    Expected format: <major>.<minor>.<patch>-<release>
    Example: 6.12.0-55.76.1.el10_0
    """
    log = TestLogger(TEST_NAMES["kernel_override_format"])

    log.check("Validating kernel_version_override format")
    result = validate_kernel_version_override_format(host)

    if not result["success"]:
        details = (
            f"Expected : kernel_version_override readable from provision_config.yml\n"
            f"Actual   : Failed — {result['error']}"
        )
        log.failed(
            LOG_MSGS["kernel_override_read_fail"].format(error=result["error"]),
            details,
        )
        assert False, ASSERT_MSGS["kernel_override_config_failed"].format(
            details=result["error"]
        )

    if result["is_empty"]:
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = result["kernel_version_override"]
    expected_fmt = "<major>.<minor>.<patch>-<release> (e.g. 6.12.0-55.76.1.el10_0)"
    valid_str = "VALID" if result["is_valid_format"] else "INVALID"

    details = (
        f"Expected : Format {expected_fmt}\n"
        f"Actual   : '{kvo}' — {valid_str}"
    )
    if not result["is_valid_format"] and result.get("details"):
        details += f"\n{result['details']}"

    if result["is_valid_format"]:
        log.passed(
            LOG_MSGS["kernel_override_format_ok"].format(kvo=kvo),
            details,
        )
    else:
        log.failed(
            LOG_MSGS["kernel_override_format_fail"].format(kvo=kvo),
            details,
        )

    assert result["is_valid_format"], ASSERT_MSGS["kernel_override_format_failed"].format(
        kvo=kvo
    )


# =============================================================================
# TC-KVO-03: S3 BOOT IMAGES MATCH KERNEL OVERRIDE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(202)
def test_kernel_override_s3_images(host):
    """
    TC-KVO-03: Verify S3 boot-images contain vmlinuz and initramfs
    matching the kernel_version_override.

    Skips if kernel_version_override is not set (auto-select mode).
    """
    log = TestLogger(TEST_NAMES["kernel_override_s3"])

    log.check("Checking S3 boot images for kernel_version_override match")
    result = verify_kernel_override_in_s3(host)

    if result.get("not_configured"):
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = result["kernel_version_override"]
    details = (
        f"Expected : S3 contains vmlinuz and initramfs matching '{kvo}'\n"
        f"Actual   :\n{result.get('details', '')}"
    )

    if result["success"]:
        log.passed(
            LOG_MSGS["kernel_override_s3_ok"].format(kvo=kvo),
            details,
        )
    else:
        log.failed(
            LOG_MSGS["kernel_override_s3_fail"].format(kvo=kvo),
            details,
        )
        assert False, ASSERT_MSGS["kernel_override_s3_failed"].format(
            kvo=kvo,
            details=result.get("details", ""),
        )


# =============================================================================
# TC-KVO-04: BSS TEMPLATES REFERENCE KERNEL OVERRIDE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(203)
def test_kernel_override_bss(host):
    """
    TC-KVO-04: Verify BSS boot templates reference the kernel_version_override.

    Skips if kernel_version_override is not set (auto-select mode).
    """
    log = TestLogger(TEST_NAMES["kernel_override_bss"])

    log.check("Checking BSS templates for kernel_version_override reference")
    result = verify_bss_kernel_override(host)

    if result.get("not_configured"):
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = result["kernel_version_override"]

    detail_lines = [
        f"Expected : All BSS templates reference kernel '{kvo}'",
        f"Actual   :",
    ]
    for tpl in result.get("groups_matched", []):
        detail_lines.append(f"  {tpl} : MATCH")
    for tpl in result.get("groups_mismatched", []):
        detail_lines.append(f"  {tpl} : MISSING")
    details = "\n".join(detail_lines)

    if result["success"]:
        log.passed(
            LOG_MSGS["kernel_override_bss_ok"].format(
                count=result["groups_checked"], kvo=kvo,
            ),
            details,
        )
    else:
        log.failed(
            LOG_MSGS["kernel_override_bss_fail"].format(
                mismatched=len(result["groups_mismatched"]),
                total=result["groups_checked"],
            ),
            details,
        )

    assert result["success"], ASSERT_MSGS["kernel_override_bss_failed"].format(
        kvo=kvo,
        details=result.get("details", ""),
    )


# =============================================================================
# TC-KVO-05: PROVISIONED NODES KERNEL VERSION MATCH
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(204)
def test_kernel_override_nodes(host):
    """
    TC-KVO-05: Verify all provisioned nodes run the kernel version
    specified by kernel_version_override.

    Uses PXE mapping file to discover nodes.
    Output shows node_name : kernel_version for each node.

    Skips if kernel_version_override is not set (auto-select mode).
    """
    log = TestLogger(TEST_NAMES["kernel_override_nodes"])

    log.check("Verifying kernel version on all provisioned nodes")
    result = verify_all_nodes_kernel_version(host)

    if result.get("not_configured"):
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = result["kernel_version_override"]
    total = result["nodes_checked"]
    matched_count = len(result.get("nodes_matched", []))

    detail_lines = [
        f"Expected : All nodes running kernel '{kvo}'",
        f"Actual   :",
    ]
    for m in result.get("nodes_matched", []):
        detail_lines.append(f"  {m['hostname']} : {m['running_kernel']}")
    for m in result.get("nodes_mismatched", []):
        detail_lines.append(
            f"  {m['hostname']} : {m['running_kernel'] or 'UNREACHABLE'} — MISMATCH"
        )
    detail_lines.append(f"Matched : {matched_count}/{total}")
    details = "\n".join(detail_lines)

    if result["success"]:
        log.passed(
            LOG_MSGS["kernel_override_nodes_ok"].format(count=total, kvo=kvo),
            details,
        )
    else:
        log.failed(
            LOG_MSGS["kernel_override_nodes_fail"].format(
                mismatched=len(result["nodes_mismatched"]), total=total,
            ),
            details,
        )

    assert result["success"], ASSERT_MSGS["kernel_override_nodes_failed"].format(
        kvo=kvo,
        details=details,
    )


# =============================================================================
# TC-KVO-06: KERNEL CONSISTENCY ACROSS ALL NODES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(205)
def test_kernel_consistency_across_nodes(host):
    """
    TC-KVO-06: Verify all provisioned nodes run the same kernel version.

    Identified from /root/omnia analysis:
      provision/roles/provision_validations/tasks/validate_image.yml selects
      a single kernel per functional group from S3. After provisioning, all
      nodes should therefore be running an identical kernel version.

    This test is independent of kernel_version_override — it verifies
    consistency regardless of whether an override is set.
    """
    log = TestLogger(TEST_NAMES["kernel_consistency"])

    # Skip when kernel_version_override is not configured
    kvo_result = get_kernel_version_override(host)
    if kvo_result["success"] and not kvo_result["is_configured"]:
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    log.check("Checking kernel version consistency across all provisioned nodes")
    result = verify_kernel_consistency(host)

    if not result["nodes"]:
        pytest.skip("No provisioned nodes found to check kernel consistency")

    kvo = result.get("kernel_version_override", "")
    is_configured = result.get("is_configured", False)

    # Build details with expected/actual if kernel_version_override is configured
    detail_lines = []
    if is_configured:
        matched = result.get("matched", [])
        mismatched = result.get("mismatched", [])
        detail_lines.append(
            f"Expected : All nodes running kernel '{kvo}'"
        )
        detail_lines.append(f"Actual   :")
        if mismatched:
            for m in mismatched:
                detail_lines.append(
                    f"  {m['hostname']} : {m['actual']} — MISMATCH"
                )
        for hostname in matched:
            node = next((n for n in result["nodes"] if n["hostname"] == hostname), None)
            if node:
                detail_lines.append(
                    f"  {hostname} : {node['running_kernel']}"
                )
        detail_lines.append(f"Matched : {len(matched)}/{len(result['nodes'])}")
    else:
        unique = result["unique_versions"]
        detail_lines.append(
            f"Expected : All provisioned nodes running identical kernel version"
        )
        detail_lines.append(f"Actual   :")
        for n in result["nodes"]:
            detail_lines.append(
                f"  {n['hostname']} : {n['running_kernel'] or 'UNREACHABLE'}"
            )
        detail_lines.append(f"Unique kernel versions : {len(unique)}")
        for v in unique:
            detail_lines.append(f"  - {v}")

    details = "\n".join(detail_lines)

    if result["success"]:
        if is_configured:
            log.passed(
                LOG_MSGS["kernel_override_nodes_ok"].format(
                    count=len(result["nodes"]),
                    kvo=kvo,
                ),
                details,
            )
        else:
            log.passed(
                LOG_MSGS["kernel_consistency_ok"].format(
                    count=len(result["nodes"]),
                    version=result["unique_versions"][0] if result["unique_versions"] else "N/A",
                ),
                details,
            )
    else:
        if is_configured:
            log.failed(
                LOG_MSGS["kernel_override_nodes_fail"].format(
                    mismatched=len(result.get("mismatched", [])),
                    total=len(result["nodes"]),
                ),
                details,
            )
        else:
            log.failed(
                LOG_MSGS["kernel_consistency_fail"].format(
                    versions=len(result["unique_versions"]), count=len(result["nodes"]),
                ),
                details,
            )

    assert result["success"], (
        ASSERT_MSGS["kernel_consistency_failed"].format(details=details)
        if not is_configured
        else ASSERT_MSGS["kernel_override_nodes_failed"].format(
            kvo=kvo, details=details
        )
    )


# =============================================================================
# TC-KVO-07: PER-FUNCTIONAL-GROUP S3 IMAGE VALIDATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(206)
def test_kernel_override_per_fg_s3(host):
    """
    TC-KVO-07: Verify S3 boot images exist per functional group matching the
    kernel_version_override.

    Identified from /root/omnia analysis:
      provision/roles/provision_validations/tasks/validate_image.yml validates
      images per functional group. Each functional group must have its own
      vmlinuz and initramfs matching the kernel_version_override in S3.

    Skips if kernel_version_override is not set (auto-select mode).
    """
    log = TestLogger(TEST_NAMES["kernel_override_per_fg_s3"])

    log.check("Checking per-functional-group S3 images for kernel override match")
    result = verify_per_fg_s3_images(host)

    if result.get("not_configured"):
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = result["kernel_version_override"]
    groups = result.get("groups", {})
    missing = result.get("missing_groups", [])

    detail_lines = [
        f"Expected : S3 images for each functional group match '{kvo}'",
        f"Actual   :",
    ]
    for fg in sorted(groups):
        status = "MATCH" if groups[fg]["has_both"] else "MISSING"
        detail_lines.append(f"  {fg} : {status}")
    details = "\n".join(detail_lines)

    if result["success"]:
        log.passed(
            LOG_MSGS["kernel_override_per_fg_s3_ok"].format(
                count=len(groups), kvo=kvo,
            ),
            details,
        )
    else:
        log.failed(
            LOG_MSGS["kernel_override_per_fg_s3_fail"].format(
                missing=len(missing), total=len(groups), kvo=kvo,
            ),
            details,
        )

    assert result["success"], ASSERT_MSGS["kernel_override_per_fg_s3_failed"].format(
        kvo=kvo,
        details=details,
    )
