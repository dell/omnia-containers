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
"""

from automation_library.core import TestLogger
from automation_library.prepare_oim.messages import (
    TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)
from automation_library.prepare_oim.functions import (
    is_ldap_enabled,
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

def test_service_status(host):
    """Check ALL systemd services and targets in one pass."""
    log = TestLogger("Verify all service/target status")
    log.check("Checking all systemd services and targets")

    result = check_all_services_status(host)

    for svc in result["results"]:
        if svc["verdict"] == "pass":
            log.passed(svc["message"])
        else:
            log.failed(svc["message"])

    summary = (
        f"{result['passed']}/{result['total']} services in expected state"
        + (f" ({result['failed']} failed)" if result["failed"] > 0 else "")
    )
    log.check(summary)

    if not result["success"]:
        failed_lines = "\n".join(
            [f"  - {s['message']}" for s in result["results"] if s["verdict"] == "fail"]
        )
        assert False, (
            f"SERVICE STATUS CHECK FAILED: {summary}\n"
            f"Failed:\n{failed_lines}"
        )


# =============================================================================
# 2. CONSOLIDATED CONTAINER STATUS TEST
# =============================================================================

def test_container_status(host):
    """Check ALL containers in one pass."""
    log = TestLogger("Verify all container status")
    log.check("Checking all expected containers")

    result = check_all_containers_status(host)

    for ctr in result["results"]:
        if ctr["verdict"] == "pass":
            log.passed(ctr["message"])
        else:
            log.failed(ctr["message"])

    summary = (
        f"{result['passed']}/{result['total']} containers in expected state"
        + (f" ({result['failed']} failed)" if result["failed"] > 0 else "")
    )
    log.check(summary)

    if not result["success"]:
        failed_lines = "\n".join(
            [f"  - {c['message']}" for c in result["results"] if c["verdict"] == "fail"]
        )
        assert False, (
            f"CONTAINER STATUS CHECK FAILED: {summary}\n"
            f"Failed:\n{failed_lines}"
        )


# =============================================================================
# 3. OPENCHAMI TARGET TEST
# =============================================================================

def test_openchami_target(host):
    """Compare openchami.target dependencies against expected list."""
    log = TestLogger("openchami.target dependency check")
    result = check_openchami_target_deps(host)

    if "error" in result and result.get("error"):
        log.failed(result["error"])
        assert False, result["error"]

    for dep in result["matched"]:
        log.passed(f"{dep}: attached")
    for dep in result["missing"]:
        log.failed(f"{dep}: expected but NOT attached")
    for dep in result["extra"]:
        log.failed(f"{dep}: attached but NOT expected")

    summary = (
        f"{len(result['matched'])} matched, "
        f"{len(result['missing'])} missing, "
        f"{len(result['extra'])} extra"
    )
    log.check(summary)

    if not result["success"]:
        lines = []
        for dep in result["missing"]:
            lines.append(f"  - MISSING: {dep}")
        for dep in result["extra"]:
            lines.append(f"  - EXTRA: {dep}")
        assert False, (
            f"openchami.target dependency mismatch: {summary}\n"
            + "\n".join(lines)
        )


# =============================================================================
# 4. OMNIA TARGET TEST
# =============================================================================

def test_omnia_target(host):
    """Compare omnia.target dependencies against expected list."""
    log = TestLogger("omnia.target dependency check")
    result = check_omnia_target_deps(host)

    if "error" in result and result.get("error"):
        log.failed(result["error"])
        assert False, result["error"]

    for dep in result["matched"]:
        log.passed(f"{dep}: attached")
    for dep in result["missing"]:
        log.failed(f"{dep}: expected but NOT attached")
    for dep in result["extra"]:
        log.failed(f"{dep}: attached but NOT expected")

    summary = (
        f"{len(result['matched'])} matched, "
        f"{len(result['missing'])} missing, "
        f"{len(result['extra'])} extra"
    )
    log.check(summary)

    if not result["success"]:
        lines = []
        for dep in result["missing"]:
            lines.append(f"  - MISSING: {dep}")
        for dep in result["extra"]:
            lines.append(f"  - EXTRA: {dep}")
        assert False, (
            f"omnia.target dependency mismatch: {summary}\n"
            + "\n".join(lines)
        )


# =============================================================================
# 5. PULP API PASSWORD TEST
# =============================================================================

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


# =============================================================================
# 6. PULP CERTIFICATE TEST
# =============================================================================

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


# =============================================================================
# 7. LDAP AUTH CERTIFICATE TEST
# =============================================================================

def test_ldap_auth_certificate(host):
    """Verify LDAP auth certificate exists (only if LDAP enabled)."""
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


# =============================================================================
# 9. SMD SERVICE TEST
# =============================================================================

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
