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
Testinfra tests for prepare_oim verification.

This file contains test functions that verify prepare_oim deployment was successful.
Tests continue even if some fail (skip_on_failure behavior).

Usage:
    ./run_molecule.sh prepare_oim test      # Run playbook + verify
    ./run_molecule.sh prepare_oim verify    # Verify only
"""

import pytest
from automation_library.core import TestLogger
from automation_library.prepare_oim.vars import (
    OPENCHAMI_CONTAINERS,
    AUTH_CONTAINER,
    PULP_CONTAINER,
    is_ldap_enabled,
)
from automation_library.prepare_oim.messages import (
    TEST_VARS, TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)
from automation_library.prepare_oim.functions import (
    check_container_running,
    check_auth_container,
    check_omnia_target,
    check_openchami_target,
    check_pulp_api_status,
    check_pulp_certificate,
    check_service_dependencies,
    check_bss_service,
    check_smd_service,
    check_ldap_auth_certificate,
)


# =============================================================================
# CONTAINER TESTS
# =============================================================================

def test_pulp_container(host):
    """Verify Pulp container is running."""
    container = PULP_CONTAINER
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


def test_pulp_api_password(host):
    """Verify Pulp API password from omnia_config_credentials.yml is correctly configured."""
    log = TestLogger(TEST_NAMES["pulp_api_status"])
    log.check("Validating pulp_password from omnia_config_credentials.yml against Pulp API")

    result = check_pulp_api_status(host)

    if result["success"]:
        log.passed(LOG_MSGS["pulp_api_ok"], result["details"])
    else:
        log.failed(LOG_MSGS["pulp_api_fail"], result["error"])

    assert result["success"], ASSERT_MSGS["pulp_api_failed"].format(
        status=result["status"], error=result["error"]
    )


def test_pulp_certificate(host):
    """Verify Pulp webserver certificate exists inside omnia_core container."""
    log = TestLogger(TEST_NAMES["pulp_certificate"])
    log.check("Checking Pulp webserver certificate in omnia_core container")

    result = check_pulp_certificate(host)

    if result["success"]:
        log.passed(LOG_MSGS["pulp_cert_exists"], result["details"])
    else:
        log.failed(LOG_MSGS["pulp_cert_not_found"], result["error"])

    assert result["success"], ASSERT_MSGS["pulp_cert_not_found"].format(
        status=result["status"]
    )


def test_openchami_containers(host):
    """Verify all OpenCHAMI containers are running."""
    log = TestLogger("Verify OpenCHAMI containers are running")
    log.check(f"Checking {len(OPENCHAMI_CONTAINERS)} OpenCHAMI containers")

    passed_containers = []
    failed_containers = []

    for container in OPENCHAMI_CONTAINERS:
        result = check_container_running(host, container)
        if result["success"]:
            passed_containers.append({"name": container, "status": result["status"]})
        else:
            failed_containers.append({"name": container, "status": result["status"], "error": result["error"]})

    # Build detailed output
    details_lines = []
    for c in passed_containers:
        details_lines.append(f"✔ {c['name']}: {c['status']}")
    for c in failed_containers:
        details_lines.append(f"✘ {c['name']}: {c['status']}")

    details = "\n".join(details_lines)
    summary = f"{len(passed_containers)}/{len(OPENCHAMI_CONTAINERS)} containers running"

    if failed_containers:
        log.failed("OpenCHAMI containers check failed", f"{summary}\n{details}")
    else:
        log.passed("All OpenCHAMI containers running", f"{summary}\n{details}")

    assert len(failed_containers) == 0, (
        f"OpenCHAMI containers check failed: {summary}\n"
        f"Failed containers:\n" +
        "\n".join([f"  - {c['name']}: {c['status']}" for c in failed_containers])
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


def test_ldap_auth_certificate(host):
    """Verify LDAP auth certificate exists (only if LDAP enabled)."""
    ldap_enabled = is_ldap_enabled()

    if ldap_enabled:
        log = TestLogger(TEST_NAMES["ldap_auth_certificate"])
        log.check("Checking LDAP auth certificate in omnia_core container")

        result = check_ldap_auth_certificate(host)

        if result["success"]:
            log.passed(LOG_MSGS["ldap_cert_exists"], result["details"])
        else:
            log.failed(LOG_MSGS["ldap_cert_not_found"], result["error"])

        assert result["success"], ASSERT_MSGS["ldap_cert_not_found"].format(
            status=result["status"]
        )
    else:
        log = TestLogger(TEST_NAMES["ldap_auth_certificate_skipped"])
        log.check("Checking if LDAP is configured")
        log.passed(LOG_MSGS["ldap_cert_skipped"], "LDAP not in software_config.json")
        pytest.skip("LDAP auth certificate check skipped - LDAP not configured in software_config.json")


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


def test_bss_service_active(host):
    """Verify ochami BSS service is running via ochami CLI."""
    log = TestLogger(TEST_NAMES["bss_service_active"])
    log.check("Checking ochami BSS service status")

    result = check_bss_service(host)

    if result["success"]:
        log.passed(LOG_MSGS["bss_service_active"], result["details"])
    else:
        log.failed(LOG_MSGS["bss_service_inactive"].format(status=result["status"]), result["error"])

    assert result["success"], ASSERT_MSGS["bss_service_failed"].format(
        status=result["status"]
    )


def test_smd_service_active(host):
    """Verify ochami SMD service is healthy via ochami CLI."""
    log = TestLogger(TEST_NAMES["smd_service_active"])
    log.check("Checking ochami SMD service status")

    result = check_smd_service(host)

    if result["success"]:
        log.passed(LOG_MSGS["smd_service_active"], result["details"])
    else:
        log.failed(LOG_MSGS["smd_service_inactive"].format(status=result["status"]), result["error"])

    assert result["success"], ASSERT_MSGS["smd_service_failed"].format(
        status=result["status"]
    )
