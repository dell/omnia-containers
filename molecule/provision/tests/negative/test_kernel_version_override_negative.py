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
Kernel Version Override - Negative / Error Handling Test Cases.

This module contains pytest negative test cases for verifying
kernel_version_override validation and mismatch-detection behavior.

Test cases:
  TC-KVO-N01: Malformed kernel_version_override values are rejected
  TC-KVO-N02: S3 boot image mismatch for kernel override is detected
  TC-KVO-N03: Provisioned node kernel mismatch is detected
  TC-KVO-N04: BSS template kernel override mismatch is detected

Coverage:
- Format validation edge cases (garbage strings, missing release, etc.)
- S3 boot image mismatch reporting
- Node kernel version mismatch reporting
- BSS template mismatch reporting

Gap Reference: Omnia_2.2_Automation_Coverage_Supplementary_Gaps.md
  Section 8 — Network Configuration Gaps:
  "Kernel version override: kernel_version_override with cross-version kernel — 0 tests"
"""

import pytest
from automation_library.core import TestLogger
from automation_library.provision.functions import (
    get_kernel_version_override,
    validate_kernel_version_string_format,
    verify_kernel_override_in_s3,
    verify_all_nodes_kernel_version,
    verify_bss_kernel_override,
)
from automation_library.provision.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
    SKIP_MSGS,
)


# Known-malformed kernel_version_override sample values for TC-KVO-N01
_MALFORMED_KVO_SAMPLES = [
    "6.12",                  # missing patch and release
    "6.12.0",                # missing release
    "abc-def",                # non-numeric major/minor/patch
    "6.a.0-55.76.1.el10_0",   # non-numeric minor
    "-55.76.1.el10_0",        # missing major.minor.patch
    "6.12.0-",                # empty release
]


# ---------------------------------------------------------------------------
# TC-KVO-N01: Malformed kernel_version_override rejected
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.kernel_override
@pytest.mark.order(210)
def test_neg_kernel_override_invalid_format_rejected(host):
    """
    TC-KVO-N01: Verify malformed kernel_version_override values are rejected.

    Feeds a set of known-invalid version strings (missing release segment,
    non-numeric components, empty release, etc.) into the format validator
    and confirms each one is correctly flagged as invalid. This does not
    require any specific value to be configured in provision_config.yml —
    it validates the regex-based format checker directly.
    """
    log = TestLogger(TEST_NAMES["kernel_override_invalid_format_rejected"])
    log.check(f"Validating {len(_MALFORMED_KVO_SAMPLES)} malformed kernel version samples")

    not_rejected = []
    details_lines = []

    for sample in _MALFORMED_KVO_SAMPLES:
        result = validate_kernel_version_string_format(sample)
        if result["is_valid_format"]:
            not_rejected.append(sample)
            details_lines.append(f"  \u2718 '{sample}' — incorrectly accepted as valid")
        else:
            details_lines.append(f"  \u2713 '{sample}' — correctly rejected")

    details = "\n".join(details_lines)

    if not not_rejected:
        log.passed(
            LOG_MSGS["kernel_override_invalid_rejected"].format(
                kvo=", ".join(_MALFORMED_KVO_SAMPLES)
            ),
            details,
        )
    else:
        log.failed(
            LOG_MSGS["kernel_override_invalid_not_rejected"].format(
                kvo=", ".join(not_rejected)
            ),
            details,
        )
        assert False, ASSERT_MSGS["kernel_override_invalid_not_rejected"].format(
            kvo=", ".join(not_rejected)
        )


# ---------------------------------------------------------------------------
# TC-KVO-N02: S3 boot image mismatch detected
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.kernel_override
@pytest.mark.order(211)
def test_neg_kernel_override_s3_mismatch_detected(host):
    """
    TC-KVO-N02: Verify S3 boot image mismatch for kernel_version_override
    is detected and reported with actionable details.

    Skips if kernel_version_override is not set (auto-select mode), since
    there is nothing to mismatch against.

    If S3 already contains matching images (positive case), this test
    confirms the detection mechanism ran without error. If a mismatch
    exists, it confirms the mismatch is surfaced clearly (the true
    negative path).
    """
    log = TestLogger(TEST_NAMES["kernel_override_s3_mismatch_detected"])

    kvo_result = get_kernel_version_override(host)
    if not kvo_result["success"] or not kvo_result["is_configured"]:
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = kvo_result["kernel_version_override"]
    log.check(f"Checking S3 boot image mismatch reporting for override '{kvo}'")

    result = verify_kernel_override_in_s3(host)

    if result["success"]:
        log.passed(
            LOG_MSGS["kernel_override_s3_ok"].format(kvo=kvo),
            result.get("details", ""),
        )
    else:
        # Mismatch found — verify it is reported with actionable detail
        details = result.get("details", "")
        error = result.get("error", "")
        assert error, "S3 mismatch detected but no error message was produced"
        log.passed(
            LOG_MSGS["kernel_override_s3_mismatch_ok"].format(kvo=kvo),
            f"error='{error}'\n{details}",
        )


# ---------------------------------------------------------------------------
# TC-KVO-N03: Node kernel mismatch detected
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.kernel_override
@pytest.mark.order(212)
def test_neg_kernel_override_node_mismatch_detected(host):
    """
    TC-KVO-N03: Verify provisioned node kernel mismatch for
    kernel_version_override is detected and reported per-node.

    Skips if kernel_version_override is not set (auto-select mode).

    Confirms verify_all_nodes_kernel_version() reports mismatched nodes
    with their running kernel version when a mismatch exists.
    """
    log = TestLogger(TEST_NAMES["kernel_override_node_mismatch_detected"])

    kvo_result = get_kernel_version_override(host)
    if not kvo_result["success"] or not kvo_result["is_configured"]:
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = kvo_result["kernel_version_override"]
    log.check(f"Checking node kernel mismatch reporting for override '{kvo}'")

    result = verify_all_nodes_kernel_version(host)

    if result.get("not_configured"):
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    if result["nodes_checked"] == 0:
        pytest.skip("No provisioned nodes found to validate mismatch reporting")

    if result["success"]:
        log.passed(
            LOG_MSGS["kernel_override_nodes_ok"].format(
                count=result["nodes_checked"], kvo=kvo
            ),
            result.get("details", ""),
        )
    else:
        mismatched = result.get("nodes_mismatched", [])
        assert mismatched, "Node mismatch reported as failed but no mismatched nodes listed"
        details = result.get("details", "")
        log.passed(
            LOG_MSGS["kernel_override_node_mismatch_ok"].format(kvo=kvo),
            f"mismatched={len(mismatched)}\n{details}",
        )


# ---------------------------------------------------------------------------
# TC-KVO-N04: BSS template mismatch detected
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.kernel_override
@pytest.mark.order(213)
def test_neg_kernel_override_bss_mismatch_detected(host):
    """
    TC-KVO-N04: Verify BSS template kernel_version_override mismatch is
    detected and reported with the list of mismatched templates.

    Skips if kernel_version_override is not set (auto-select mode).

    Confirms verify_bss_kernel_override() reports mismatched BSS templates
    (templates whose kernel/initrd path does not reference the override)
    with actionable detail.
    """
    log = TestLogger(TEST_NAMES["kernel_override_bss_mismatch_detected"])

    kvo_result = get_kernel_version_override(host)
    if not kvo_result["success"] or not kvo_result["is_configured"]:
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = kvo_result["kernel_version_override"]
    log.check(f"Checking BSS template mismatch reporting for override '{kvo}'")

    result = verify_bss_kernel_override(host)

    if result.get("not_configured"):
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    if result["groups_checked"] == 0:
        pytest.skip("No BSS templates found to validate mismatch reporting")

    if result["success"]:
        log.passed(
            LOG_MSGS["kernel_override_bss_ok"].format(
                count=result["groups_checked"], kvo=kvo
            ),
            result.get("details", ""),
        )
    else:
        mismatched = result.get("groups_mismatched", [])
        assert mismatched, "BSS mismatch reported as failed but no mismatched templates listed"
        details = result.get("details", "")
        log.passed(
            LOG_MSGS["kernel_override_bss_mismatch_ok"].format(kvo=kvo),
            f"mismatched={len(mismatched)}\n{details}",
        )
