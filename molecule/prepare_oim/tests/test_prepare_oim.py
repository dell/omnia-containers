"""
Testinfra tests for prepare_oim verification.

This file contains test functions that verify prepare_oim deployment was successful.
Tests continue even if some fail (skip_on_failure behavior).

Usage:
    ./run_molecule.sh prepare_oim test      # Run playbook + verify
    ./run_molecule.sh prepare_oim verify    # Verify only
"""

import pytest
from automation_library.core import TestLogger
from automation_library.vars.prepare_oim_vars import (
    OPENCHAMI_CONTAINERS,
    CORE_CONTAINERS,
    AUTH_CONTAINER,
    is_ldap_enabled,
)
from automation_library.messages.prepare_oim_msgs import (
    TEST_VARS, TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)
from automation_library.functions.prepare_oim_func import (
    check_container_running,
    check_auth_container,
    check_omnia_target,
    check_openchami_target,
    check_service_dependencies,
)


# =============================================================================
# CONTAINER TESTS
# =============================================================================

@pytest.mark.parametrize("container", CORE_CONTAINERS)
def test_core_container_running(host, container):
    """Verify core infrastructure containers are running."""
    log = TestLogger(TEST_NAMES["container_running"].format(container=container))
    log.check(f"Checking container: {container}")

    result = check_container_running(host, container)

    if result["success"]:
        log.passed(LOG_MSGS["container_running"].format(container=container), result["status"])
    else:
        log.failed(LOG_MSGS["container_not_running"].format(container=container), result["error"])

    assert result["success"], ASSERT_MSGS["container_not_running"].format(
        container=container, status=result["status"]
    )


@pytest.mark.parametrize("container", OPENCHAMI_CONTAINERS)
def test_openchami_container_running(host, container):
    """Verify OpenChami containers are running."""
    log = TestLogger(TEST_NAMES["container_running"].format(container=container))
    log.check(f"Checking container: {container}")

    result = check_container_running(host, container)

    if result["success"]:
        log.passed(LOG_MSGS["container_running"].format(container=container), result["status"])
    else:
        log.failed(LOG_MSGS["container_not_running"].format(container=container), result["error"])

    assert result["success"], ASSERT_MSGS["container_not_running"].format(
        container=container, status=result["status"]
    )


def test_auth_container(host):
    """Verify auth container is running (only if LDAP enabled)."""
    ldap_enabled = is_ldap_enabled()

    if ldap_enabled:
        log = TestLogger(TEST_NAMES["auth_container"])
        log.check(f"Checking auth container: {AUTH_CONTAINER}")

        result = check_auth_container(host)

        if result["success"]:
            log.passed(LOG_MSGS["container_running"].format(container=AUTH_CONTAINER), result["status"])
        else:
            log.failed(LOG_MSGS["container_not_running"].format(container=AUTH_CONTAINER), result["error"])

        assert result["success"], ASSERT_MSGS["container_not_running"].format(
            container=AUTH_CONTAINER, status=result["status"]
        )
    else:
        log = TestLogger(TEST_NAMES["auth_container_skipped"])
        log.check("Checking if LDAP is configured")
        log.passed(LOG_MSGS["auth_skipped"], "LDAP not in software_config.json")
        pytest.skip("Auth container check skipped - LDAP not configured in software_config.json")


# =============================================================================
# SERVICE TESTS
# =============================================================================

def test_omnia_target_active(host):
    """Verify omnia.target is active."""
    log = TestLogger(TEST_NAMES["omnia_target_active"])
    target = TEST_VARS["omnia_target"]
    log.check(f"Checking target: {target}")

    result = check_omnia_target(host)

    if result["success"]:
        log.passed(LOG_MSGS["target_active"].format(target=target), result["details"])
    else:
        log.failed(LOG_MSGS["target_inactive"].format(target=target, status=result["status"]), result["error"])

    assert result["success"], ASSERT_MSGS["target_not_active"].format(
        target=target, status=result["status"]
    )


def test_openchami_target_active(host):
    """Verify openchami.target is active."""
    log = TestLogger(TEST_NAMES["openchami_target_active"])
    target = TEST_VARS["openchami_target"]
    log.check(f"Checking target: {target}")

    result = check_openchami_target(host)

    if result["success"]:
        log.passed(LOG_MSGS["target_active"].format(target=target), result["details"])
    else:
        log.failed(LOG_MSGS["target_inactive"].format(target=target, status=result["status"]), result["error"])

    assert result["success"], ASSERT_MSGS["target_not_active"].format(
        target=target, status=result["status"]
    )


def test_omnia_target_dependencies(host):
    """Verify all omnia.target dependencies are active."""
    log = TestLogger("Verify omnia.target dependencies are active")
    target = TEST_VARS["omnia_target"]
    log.check(f"Checking dependencies of {target}")

    result = check_service_dependencies(host, target)

    if result["success"]:
        log.passed(f"All {target} dependencies are active", result["details"])
    else:
        failed_list = ", ".join([f"{d['service']}({d['status']})" for d in result["failed"]])
        log.failed(f"Some dependencies not active: {failed_list}", result["error"])

    assert result["success"], (
        f"╔══════════════════════════════════════════════════════════════════════════════╗\n"
        f"║ OMNIA.TARGET DEPENDENCIES CHECK FAILED\n"
        f"╠══════════════════════════════════════════════════════════════════════════════╣\n"
        f"║ {result['details']}\n"
        f"║ Failed dependencies:\n"
        + "\n".join([f"║   - {d['service']}: {d['status']}" for d in result["failed"]])
        + f"\n║\n"
        f"║ HOW TO FIX:\n"
        f"║   1. Check failed services: systemctl status <service>\n"
        f"║   2. View logs: journalctl -u <service>\n"
        f"║   3. Restart failed services: systemctl restart <service>\n"
        f"║   4. List all dependencies: systemctl list-dependencies {target}\n"
        f"╚══════════════════════════════════════════════════════════════════════════════╝"
    )
