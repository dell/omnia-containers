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
Prepare OIM Test Cases.

This module contains pytest test cases for verifying prepare_oim deployment.

Test cases:
1. Verify all expected services are running
2. Verify all expected containers are running
3. Verify openchami.target is active with all attached services
4. Verify omnia.target is active with all attached services
5. Verify Pulp API password is valid
6. Verify Pulp webserver certificate exists
7. Verify LDAP auth certificate exists (skip if LDAP disabled)
8. Verify ochami BSS service is active via CLI
9. Verify ochami SMD service is active via CLI
10. Verify Quadlet service files exist in /etc/containers/systemd/
11. Verify conditional Quadlet service files based on configuration
"""

import pytest

from automation_library.core import TestLogger
from automation_library.prepare_oim.vars import (
    QUADLET_DIR,
    ESSENTIAL_QUADLET_FILES,
)
from automation_library.prepare_oim.messages import (
    TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)
from automation_library.prepare_oim.functions import (
    is_ldap_enabled,
    is_build_stream_enabled,
    check_pulp_api_status,
    check_pulp_certificate,
    check_bss_service,
    check_smd_service,
    check_ldap_auth_certificate,
    check_all_services_status,
    check_all_containers_status,
    check_openchami_target_deps,
    check_omnia_target_deps,
)


# =============================================================================
# 1. CONSOLIDATED SERVICE STATUS TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_service_status(host):
    """
    Test Case 1: Verify all expected systemd services are running.

    Checks:
    - All OIM systemd services are active
    - All systemd targets are in expected state
    """
    log = TestLogger(TEST_NAMES["service_status"])
    log.check("Checking all systemd services and targets")

    result = check_all_services_status(host)

    if result["success"]:
        log.passed(LOG_MSGS["services_ok"], result["details"])
    else:
        log.failed(LOG_MSGS["services_failed"], result["details"])

    assert result["success"], (
        f"SERVICE STATUS CHECK FAILED: "
        f"{result['passed']}/{result['total']} in expected state\n"
        + result["details"]
    )


# =============================================================================
# 2. CONSOLIDATED CONTAINER STATUS TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_container_status(host):
    """
    Test Case 2: Verify all expected containers are running.

    Checks:
    - All OIM containers are in 'running' state
    - Container health checks pass
    """
    log = TestLogger(TEST_NAMES["container_status"])
    log.check("Checking all expected containers")

    result = check_all_containers_status(host)

    if result["success"]:
        log.passed(LOG_MSGS["containers_ok"], result["details"])
    else:
        log.failed(LOG_MSGS["containers_failed"], result["details"])

    assert result["success"], (
        f"CONTAINER STATUS CHECK FAILED: "
        f"{result['passed']}/{result['total']} in expected state\n"
        + result["details"]
    )


# =============================================================================
# 3. OPENCHAMI TARGET TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_openchami_target(host):
    """
    Test Case 3: Verify openchami.target is active with all attached services.

    Checks:
    - openchami.target systemd target is active
    - All expected dependencies are present and running
    """
    log = TestLogger(TEST_NAMES["openchami_target"])
    log.check("Comparing openchami.target dependencies against expected list")

    result = check_openchami_target_deps(host)

    if "error" in result and result.get("error"):
        log.failed(result["error"])
        assert False, result["error"]

    if result["success"]:
        log.passed(LOG_MSGS["openchami_target_ok"], result["details"])
    else:
        log.failed(LOG_MSGS["openchami_target_failed"], result["details"])

    assert result["success"], (
        "openchami.target dependency mismatch\n" + result["details"]
    )


# =============================================================================
# 4. OMNIA TARGET TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_omnia_target(host):
    """
    Test Case 4: Verify omnia.target is active with all attached services.

    Checks:
    - omnia.target systemd target is active
    - All expected dependencies are present and running
    """
    log = TestLogger(TEST_NAMES["omnia_target"])
    log.check("Comparing omnia.target dependencies against expected list")

    result = check_omnia_target_deps(host)

    if "error" in result and result.get("error"):
        log.failed(result["error"])
        assert False, result["error"]

    if result["success"]:
        log.passed(LOG_MSGS["omnia_target_ok"], result["details"])
    else:
        log.failed(LOG_MSGS["omnia_target_failed"], result["details"])

    assert result["success"], (
        "omnia.target dependency mismatch\n" + result["details"]
    )


# =============================================================================
# 5. PULP API PASSWORD TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_pulp_api_password(host):
    """
    Test Case 5: Verify Pulp API password is valid.

    Checks:
    - pulp_password from omnia_config_credentials.yml works
    - Pulp API responds with valid authentication
    """
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


# =============================================================================
# 6. PULP CERTIFICATE TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_pulp_certificate(host):
    """
    Test Case 6: Verify Pulp webserver certificate exists.

    Checks:
    - Certificate file exists in omnia_core container
    - Certificate is valid and readable
    """
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


# =============================================================================
# 7. LDAP AUTH CERTIFICATE TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_ldap_auth_certificate(host):
    """
    Test Case 7: Verify LDAP auth certificate exists (skip if LDAP disabled).

    Checks:
    - LDAP certificate file exists in omnia_core container
    - Skips gracefully if LDAP is not enabled in configuration
    """
    ldap_enabled = is_ldap_enabled(host)

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
        log.skipped(LOG_MSGS["ldap_cert_skipped"])


# =============================================================================
# 8. BSS SERVICE TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_bss_service_active(host):
    """
    Test Case 8: Verify ochami BSS service is active via CLI.

    Checks:
    - BSS (Boot Script Service) is running
    - ochami CLI can query BSS status successfully
    """
    log = TestLogger(TEST_NAMES["bss_service_active"])
    log.check("Checking ochami BSS service status")

    result = check_bss_service(host)

    if result["success"]:
        log.passed(LOG_MSGS["bss_service_active"], result["details"])
    else:
        log.failed(
            LOG_MSGS["bss_service_inactive"].format(status=result["status"]),
            result["error"]
        )

    assert result["success"], ASSERT_MSGS["bss_service_failed"].format(
        status=result["status"]
    )


# =============================================================================
# 9. SMD SERVICE TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_smd_service_active(host):
    """
    Test Case 9: Verify ochami SMD service is active via CLI.

    Checks:
    - SMD (State Management Database) is running
    - ochami CLI can query SMD status successfully
    """
    log = TestLogger(TEST_NAMES["smd_service_active"])
    log.check("Checking ochami SMD service status")

    result = check_smd_service(host)

    if result["success"]:
        log.passed(LOG_MSGS["smd_service_active"], result["details"])
    else:
        log.failed(
            LOG_MSGS["smd_service_inactive"].format(status=result["status"]),
            result["error"]
        )

    assert result["success"], ASSERT_MSGS["smd_service_failed"].format(
        status=result["status"]
    )


# =============================================================================
# 10. QUADLET SERVICE FILES VALIDATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_quadlet_service_files_exist(host):
    """
    Test Case 10: Verify Quadlet service files exist.

    Checks:
    - Essential Quadlet .container files exist in /etc/containers/systemd/
    - Validates Quadlet-based container orchestration is properly configured
    """
    log = TestLogger("Verify Quadlet service files exist")
    log.check(f"Checking Quadlet service files in {QUADLET_DIR}")

    missing_files = []
    found_files = []

    for quadlet_file in ESSENTIAL_QUADLET_FILES:
        file_path = f"{QUADLET_DIR}/{quadlet_file}"
        result = host.run(
            f"test -f {file_path} && echo EXISTS || echo NOT_FOUND"
        )

        if "EXISTS" in result.stdout:
            found_files.append(quadlet_file)
        else:
            missing_files.append(quadlet_file)

    total_result = host.run(
        f"ls {QUADLET_DIR}/*.container 2>/dev/null | wc -l"
    )
    total_count = total_result.stdout.strip()

    found_count = len(found_files)
    expected_count = len(ESSENTIAL_QUADLET_FILES)
    details = (
        f"Found {found_count}/{expected_count} essential Quadlet files "
        f"(Total: {total_count})\n"
    )
    for f in found_files:
        details += f"  ✓ {f}\n"
    for f in missing_files:
        details += f"  ✘ {f} (missing)\n"

    if not missing_files:
        log.passed("All essential Quadlet service files exist", details)
    else:
        log.failed("Missing Quadlet service files", details)

    assert not missing_files, (
        f"QUADLET FILES MISSING: {len(missing_files)} files not found\n"
        f"{details}"
    )


# =============================================================================
# 11. CONDITIONAL QUADLET SERVICE FILES VALIDATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_conditional_quadlet_files_exist(host):
    """
    Test Case 11: Verify conditional Quadlet service files based on config.

    Checks:
    - omnia_auth.container exists if LDAP is enabled
    - omnia_build_stream.container exists if build_stream is enabled
    - omnia_postgres.container exists if build_stream is enabled
    """
    log = TestLogger("Verify conditional Quadlet service files")
    log.check("Checking conditional Quadlet service files based on config")

    ldap_enabled = is_ldap_enabled(host)
    build_stream_enabled = is_build_stream_enabled(host)

    expected_files = []
    if ldap_enabled:
        expected_files.append("omnia_auth.container")
    if build_stream_enabled:
        expected_files.append("omnia_build_stream.container")
        expected_files.append("omnia_postgres.container")

    if not expected_files:
        log.skipped(
            "No conditional Quadlet files expected "
            "(LDAP and build_stream disabled)"
        )
        return

    missing_files = []
    found_files = []

    for quadlet_file in expected_files:
        file_path = f"{QUADLET_DIR}/{quadlet_file}"
        result = host.run(
            f"test -f {file_path} && echo EXISTS || echo NOT_FOUND"
        )

        if "EXISTS" in result.stdout:
            found_files.append(quadlet_file)
        else:
            missing_files.append(quadlet_file)

    details = (
        f"Configuration: LDAP={ldap_enabled}, "
        f"build_stream={build_stream_enabled}\n"
    )
    details += (
        f"Found {len(found_files)}/{len(expected_files)} "
        f"conditional Quadlet files\n"
    )
    for f in found_files:
        details += f"  ✓ {f}\n"
    for f in missing_files:
        details += f"  ✘ {f} (missing)\n"

    if not missing_files:
        log.passed("All conditional Quadlet service files exist", details)
    else:
        log.failed("Missing conditional Quadlet service files", details)

    assert not missing_files, (
        f"CONDITIONAL QUADLET FILES MISSING: {len(missing_files)} "
        f"files not found\n{details}"
    )
