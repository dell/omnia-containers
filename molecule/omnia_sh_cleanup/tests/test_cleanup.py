"""
Testinfra tests for omnia.sh cleanup verification.

These tests verify that cleanup (omnia.sh --uninstall) was successful.

Usage:
    ./run_molecule.sh cleanup    # Run uninstall + verify
"""

from automation_library.core import TestLogger
from automation_library.messages.omnia_sh_msgs import (
    TEST_VARS, TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)
from automation_library.functions.omnia_sh_func import (
    check_container_not_running,
    check_service_not_exists,
    check_fstab_entry_removed,
    check_mount_removed,
)


def test_cleanup_container_removed(host):
    """Verify omnia_core container is NOT running after cleanup."""
    log = TestLogger(TEST_NAMES["cleanup_container_removed"])
    log.check("Checking container is removed")

    result = check_container_not_running(host)

    if result["success"]:
        log.passed(LOG_MSGS["cleanup_container_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["cleanup_container_still_running"], result["error"])

    assert result["success"], ASSERT_MSGS["cleanup_failed"].format(error=result["error"])


def test_cleanup_service_file_removed(host):
    """Verify omnia_core.container service file is removed after cleanup."""
    log = TestLogger(TEST_NAMES["cleanup_service_removed"])
    path = TEST_VARS["container_file"]
    log.check(f"Checking service file removed: {path}")

    result = check_service_not_exists(host)

    if result["success"]:
        log.passed(LOG_MSGS["cleanup_service_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["cleanup_service_exists"], result["error"])

    assert result["success"], ASSERT_MSGS["cleanup_failed"].format(error=result["error"])


def test_cleanup_fstab_entry_removed(host):
    """Verify fstab entry for omnia_shared_path is removed after cleanup."""
    log = TestLogger(TEST_NAMES["cleanup_fstab_removed"])
    log.check("Checking fstab entry removed")

    result = check_fstab_entry_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["cleanup_fstab_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["cleanup_fstab_exists"], result["error"])

    assert result["success"], ASSERT_MSGS["cleanup_failed"].format(error=result["error"])


def test_cleanup_mount_removed(host):
    """Verify omnia_shared_path is NOT mounted after cleanup."""
    log = TestLogger(TEST_NAMES["cleanup_mount_removed"])
    log.check("Checking mount point removed")

    result = check_mount_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["cleanup_mount_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["cleanup_mount_exists"], result["error"])

    assert result["success"], ASSERT_MSGS["cleanup_failed"].format(error=result["error"])
