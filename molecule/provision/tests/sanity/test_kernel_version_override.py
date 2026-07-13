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
- TC-KVO-01: Configuration read — verify kernel_version_override is readable
- TC-KVO-02: Format validation — verify format matches <major>.<minor>.<patch>-<release>
- TC-KVO-03: S3 boot image match — verify S3 contains vmlinuz/initramfs for the override
- TC-KVO-04: Node kernel match — verify provisioned nodes run the overridden kernel
- TC-KVO-05: BSS template match — verify BSS templates reference the override kernel

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
)
from automation_library.provision.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# TC-KVO-01: KERNEL VERSION OVERRIDE CONFIGURATION READ
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(200)
def test_kernel_override_config(host):
    """
    TC-KVO-01: Verify kernel_version_override can be read from provision_config.yml.

    Checks:
    - provision_config.yml is readable inside omnia_core container
    - kernel_version_override field exists (can be empty or non-empty)
    - If set, the value is a non-empty string
    """
    log = TestLogger(TEST_NAMES["kernel_override_config"])

    log.check("Reading kernel_version_override from provision_config.yml")
    result = get_kernel_version_override(host)

    if not result["success"]:
        log.failed(
            LOG_MSGS["kernel_override_read_fail"].format(error=result["error"])
        )
        assert False, ASSERT_MSGS["kernel_override_config_failed"].format(
            details=result["error"]
        )

    if result["is_configured"]:
        log.passed(
            LOG_MSGS["kernel_override_read_ok"].format(
                kvo=result["kernel_version_override"]
            )
        )
    else:
        log.passed(LOG_MSGS["kernel_override_not_set"])

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

    Checks:
    - If empty: auto-select mode (valid)
    - If set: must match pattern <major>.<minor>.<patch>-<release>
      e.g. "6.12.0-55.76.1.el10_0"
    """
    log = TestLogger(TEST_NAMES["kernel_override_format"])

    log.check("Validating kernel_version_override format")
    result = validate_kernel_version_override_format(host)

    if not result["success"]:
        log.failed(
            LOG_MSGS["kernel_override_read_fail"].format(error=result["error"])
        )
        assert False, ASSERT_MSGS["kernel_override_config_failed"].format(
            details=result["error"]
        )

    if result["is_empty"]:
        log.passed(LOG_MSGS["kernel_override_not_set"])
        return

    kvo = result["kernel_version_override"]

    if result["is_valid_format"]:
        log.passed(LOG_MSGS["kernel_override_format_ok"].format(kvo=kvo))
    else:
        log.failed(LOG_MSGS["kernel_override_format_fail"].format(kvo=kvo))

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

    if not result["success"]:
        log.failed(
            LOG_MSGS["kernel_override_s3_fail"].format(
                kvo=result["kernel_version_override"]
            ),
            result.get("details", ""),
        )
        assert False, ASSERT_MSGS["kernel_override_s3_failed"].format(
            kvo=result["kernel_version_override"],
            details=result.get("details", ""),
        )

    log.passed(
        LOG_MSGS["kernel_override_s3_ok"].format(
            kvo=result["kernel_version_override"]
        ),
        result.get("details", ""),
    )


# =============================================================================
# TC-KVO-04: PROVISIONED NODES RUNNING OVERRIDDEN KERNEL
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(203)
def test_kernel_override_nodes(host):
    """
    TC-KVO-04: Verify all provisioned nodes run the kernel version
    specified by kernel_version_override.

    Skips if kernel_version_override is not set (auto-select mode).

    Checks:
    - SSH to each node and run 'uname -r'
    - Verify the output contains the kernel_version_override string
    """
    log = TestLogger(TEST_NAMES["kernel_override_nodes"])

    log.check("Verifying kernel version on all provisioned nodes")
    result = verify_all_nodes_kernel_version(host)

    if result.get("not_configured"):
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = result["kernel_version_override"]

    if result["success"]:
        log.passed(
            LOG_MSGS["kernel_override_nodes_ok"].format(
                count=result["nodes_checked"],
                kvo=kvo,
            ),
            result.get("details", ""),
        )
    else:
        log.failed(
            LOG_MSGS["kernel_override_nodes_fail"].format(
                mismatched=len(result["nodes_mismatched"]),
                total=result["nodes_checked"],
            ),
            result.get("details", ""),
        )

    assert result["success"], ASSERT_MSGS["kernel_override_nodes_failed"].format(
        kvo=kvo,
        details=result.get("details", ""),
    )


# =============================================================================
# TC-KVO-05: BSS TEMPLATES REFERENCE KERNEL OVERRIDE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.kernel_override
@pytest.mark.order(204)
def test_kernel_override_bss(host):
    """
    TC-KVO-05: Verify BSS boot templates reference the kernel_version_override.

    Skips if kernel_version_override is not set (auto-select mode).

    Checks:
    - BSS template JSON files inside omnia_core contain the override string
      in their kernel/initrd paths
    """
    log = TestLogger(TEST_NAMES["kernel_override_bss"])

    log.check("Checking BSS templates for kernel_version_override reference")
    result = verify_bss_kernel_override(host)

    if result.get("not_configured"):
        pytest.skip(SKIP_MSGS["kernel_override_not_configured"])

    kvo = result["kernel_version_override"]

    if result["success"]:
        log.passed(
            LOG_MSGS["kernel_override_bss_ok"].format(
                count=result["groups_checked"],
                kvo=kvo,
            ),
            result.get("details", ""),
        )
    else:
        log.failed(
            LOG_MSGS["kernel_override_bss_fail"].format(
                mismatched=len(result["groups_mismatched"]),
                total=result["groups_checked"],
            ),
            result.get("details", ""),
        )

    assert result["success"], ASSERT_MSGS["kernel_override_bss_failed"].format(
        kvo=kvo,
        details=result.get("details", ""),
    )
