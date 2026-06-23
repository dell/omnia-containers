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
Omnia.sh Uninstall Test Cases.

This module tests the omnia.sh --uninstall workflow. Uninstall is driven from
tests with progress output every 10 seconds.

Test cases (executed in order):
1. Run omnia.sh --uninstall (skip if container not running)
2. Verify omnia_core container is removed
3. Verify omnia_core.container service file is removed
4. Verify fstab entry is removed
5. Verify mount is removed
"""

import pytest

from automation_library.core import TestLogger
from automation_library.omnia_sh.vars.omnia_sh_vars import TEST_VARS
from automation_library.omnia_sh.messages.omnia_sh_msgs import (
    TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS, SKIP_MSGS
)
from automation_library.omnia_sh.functions.omnia_sh_func import (
    check_container_running,
    check_container_not_running,
    check_service_not_exists,
    check_fstab_entry_removed,
    check_mount_removed,
    run_omnia_sh_uninstall_testinfra,
)


# =============================================================================
# MODULE-LEVEL STATE
# =============================================================================
_uninstall_skipped: bool = False
_uninstall_passed: bool = False


# =============================================================================
# UNINSTALL TEST (TC-1)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_omnia_sh_uninstall(host):
    """
    Test Case 1: Run omnia.sh --uninstall with progress output.

    Skip if omnia_core container is NOT running (nothing to uninstall).
    Uses background execution with 10-second progress updates.
    """
    global _uninstall_skipped
    log = TestLogger(TEST_NAMES["omnia_sh_uninstall"])

    # Check if container is running - skip if not
    container_result = check_container_running(host)
    if not container_result["success"]:
        _uninstall_skipped = True
        print(f"    │ {SKIP_MSGS['container_not_running']}", flush=True)
        log.skipped(SKIP_MSGS["container_not_running"])
        pytest.skip(SKIP_MSGS["container_not_running"])

    # Run uninstall with progress callback
    print("    ▸ Running omnia.sh --uninstall...", flush=True)

    def _progress(elapsed: int) -> None:
        print(f"    │ Running... {elapsed}s elapsed", flush=True)

    result = run_omnia_sh_uninstall_testinfra(host, progress_callback=_progress)

    global _uninstall_passed
    if result["success"]:
        _uninstall_passed = True
        # Show all output lines with │ prefix
        output_lines = result["output"].strip().split("\n")
        for line in output_lines:
            print(f"    │ {line}", flush=True)
        log.passed(LOG_MSGS["uninstall_success"], "")
    else:
        log.failed(LOG_MSGS["uninstall_failed"], result["error"])

    assert result["success"], ASSERT_MSGS["uninstall_failed"].format(error=result["error"])


# =============================================================================
# VERIFICATION TESTS (TC-2 to TC-5)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_uninstall_container_removed(host):
    """
    Test Case 2: Verify omnia_core container is NOT running after uninstall.

    Skip if uninstall was skipped (container was not running).
    """
    if not _uninstall_passed and not _uninstall_skipped:
        log = TestLogger(TEST_NAMES["cleanup_container_removed"])
        log.skipped("Uninstall test failed - skipping verification tests")
        pytest.skip("Uninstall test failed - skipping verification tests")

    log = TestLogger(TEST_NAMES["cleanup_container_removed"])
    result = check_container_not_running(host)

    if result["success"]:
        print(f"    │ {result['details']}", flush=True)
        log.passed(LOG_MSGS["cleanup_container_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["cleanup_container_still_running"], result["error"])

    assert result["success"], ASSERT_MSGS["cleanup_failed"].format(error=result["error"])


@pytest.mark.sanity
@pytest.mark.order(3)
def test_uninstall_service_file_removed(host):
    """
    Test Case 3: Verify omnia_core.container service file is removed.

    Skip if uninstall was skipped (container was not running).
    """
    if not _uninstall_passed and not _uninstall_skipped:
        log = TestLogger(TEST_NAMES["cleanup_service_removed"])
        log.skipped("Uninstall test failed - skipping verification tests")
        pytest.skip("Uninstall test failed - skipping verification tests")

    log = TestLogger(TEST_NAMES["cleanup_service_removed"])
    path = TEST_VARS["container_file"]
    result = check_service_not_exists(host)

    if result["success"]:
        print(f"    │ Path: {path}", flush=True)
        print(f"    │ {result['details']}", flush=True)
        log.passed(LOG_MSGS["cleanup_service_removed"], f"Path: {path}\n{result['details']}")
    else:
        log.failed(LOG_MSGS["cleanup_service_exists"], f"Path: {path}\n{result['error']}")

    assert result["success"], ASSERT_MSGS["cleanup_failed"].format(error=result["error"])


@pytest.mark.sanity
@pytest.mark.order(4)
def test_uninstall_fstab_entry_removed(host):
    """
    Test Case 4: Verify fstab entry for omnia_shared_path is removed.

    Skip if uninstall was skipped (container was not running).
    """
    if not _uninstall_passed and not _uninstall_skipped:
        log = TestLogger(TEST_NAMES["cleanup_fstab_removed"])
        log.skipped("Uninstall test failed - skipping verification tests")
        pytest.skip("Uninstall test failed - skipping verification tests")

    log = TestLogger(TEST_NAMES["cleanup_fstab_removed"])
    result = check_fstab_entry_removed(host)

    if result["success"]:
        print(f"    │ {result['details']}", flush=True)
        log.passed(LOG_MSGS["cleanup_fstab_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["cleanup_fstab_exists"], result["error"])

    assert result["success"], ASSERT_MSGS["cleanup_failed"].format(error=result["error"])


@pytest.mark.sanity
@pytest.mark.order(5)
def test_uninstall_mount_removed(host):
    """
    Test Case 5: Verify omnia_shared_path is NOT mounted.

    Skip if uninstall was skipped (container was not running).
    """
    if not _uninstall_passed and not _uninstall_skipped:
        log = TestLogger(TEST_NAMES["cleanup_mount_removed"])
        log.skipped("Uninstall test failed - skipping verification tests")
        pytest.skip("Uninstall test failed - skipping verification tests")

    log = TestLogger(TEST_NAMES["cleanup_mount_removed"])
    result = check_mount_removed(host)

    if result["success"]:
        print(f"    │ {result['details']}", flush=True)
        log.passed(LOG_MSGS["cleanup_mount_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["cleanup_mount_exists"], result["error"])

    assert result["success"], ASSERT_MSGS["cleanup_failed"].format(error=result["error"])
