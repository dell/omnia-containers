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
OIM Cleanup Test Cases.

This module contains pytest test cases for verifying oim_cleanup.yml execution.

Test cases:
1. Verify all OIM services are stopped and removed
2. Verify all OIM containers are removed
3. Verify all .container systemd files and omnia.target are removed
4. Verify OpenCHAMI volumes and secrets are removed
5. Verify credential files and vault key are removed
6. Verify firewall ports are removed
7. Verify cleanup directories are removed
8. Verify regctl binary, s3cmd and openchami packages are removed
9. Verify chronyd is stopped, disabled, and allow list removed
"""

import pytest

from automation_library.core import TestLogger
from automation_library.oim_cleanup.messages.oim_cleanup_msgs import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.oim_cleanup.functions import (
    check_services_removed,
    check_containers_removed,
    check_container_files_removed,
    check_volumes_secrets_removed,
    check_credential_files_removed,
    check_firewall_ports_removed,
    check_directories_removed,
    check_packages_removed,
    check_chronyd_removed,
)


# =============================================================================
# 1. SERVICES REMOVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_services_removed(host):
    """
    Test Case 1: Verify all OIM services are stopped and removed.

    Checks:
    - All OIM systemd services are stopped
    - Services are disabled and removed from systemd
    """
    log = TestLogger(TEST_NAMES["services_removed"])
    log.check("Checking all systemd services and targets")

    result = check_services_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["services_all_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["services_still_active"], result["details"])

    assert result["success"], ASSERT_MSGS["services_still_active"].format(
        details=result["error"]
    )


# =============================================================================
# 2. CONTAINERS REMOVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_containers_removed(host):
    """
    Test Case 2: Verify all OIM containers are removed.

    Checks:
    - No OIM containers exist in podman ps output
    - All container images are cleaned up
    """
    log = TestLogger(TEST_NAMES["containers_removed"])
    log.check("Checking all expected containers")

    result = check_containers_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["containers_all_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["containers_still_present"], result["details"])

    assert result["success"], ASSERT_MSGS["containers_still_present"].format(
        details=result["error"]
    )


# =============================================================================
# 3. CONTAINER FILES AND OMNIA TARGET REMOVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_container_files_removed(host):
    """
    Test Case 3: Verify all .container systemd files and omnia.target are removed.

    Checks:
    - All .container unit files are deleted
    - omnia.target systemd target is removed
    """
    log = TestLogger(TEST_NAMES["container_files_removed"])
    log.check("Checking .container systemd files and omnia.target")

    result = check_container_files_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["container_files_all_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["container_files_still_present"], result["details"])

    assert result["success"], ASSERT_MSGS["container_files_still_present"].format(
        details=result["error"]
    )


# =============================================================================
# 4. VOLUMES AND SECRETS REMOVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_volumes_secrets_removed(host):
    """
    Test Case 4: Verify OpenCHAMI volumes and secrets are removed.

    Checks:
    - All podman volumes are deleted
    - All podman secrets are removed
    """
    log = TestLogger(TEST_NAMES["volumes_secrets_removed"])
    log.check("Checking podman volumes and secrets")

    result = check_volumes_secrets_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["volumes_secrets_all_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["volumes_secrets_still_present"], result["details"])

    assert result["success"], ASSERT_MSGS["volumes_secrets_still_present"].format(
        details=result["error"]
    )


# =============================================================================
# 5. CREDENTIAL FILES REMOVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_credential_files_removed(host):
    """
    Test Case 5: Verify credential files and vault key are removed.

    Checks:
    - Ansible vault key file is deleted
    - Credential YAML files are removed
    - OIM metadata file is cleaned up
    """
    log = TestLogger(TEST_NAMES["credential_files_removed"])
    log.check("Checking credential and metadata files inside container")

    result = check_credential_files_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["credentials_all_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["credentials_still_present"], result["details"])

    assert result["success"], ASSERT_MSGS["credentials_still_present"].format(
        details=result["error"]
    )


# =============================================================================
# 6. FIREWALL PORTS REMOVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_firewall_ports_removed(host):
    """
    Test Case 6: Verify firewall ports are removed.

    Checks:
    - All OIM TCP ports are closed
    - All OIM UDP ports are closed
    - Firewall rules are cleaned up
    """
    log = TestLogger(TEST_NAMES["firewall_ports_removed"])
    log.check("Checking TCP and UDP firewall ports")

    result = check_firewall_ports_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["firewall_all_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["firewall_still_open"], result["details"])

    assert result["success"], ASSERT_MSGS["firewall_still_open"].format(
        details=result["error"]
    )


# =============================================================================
# 7. DIRECTORIES REMOVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_directories_removed(host):
    """
    Test Case 7: Verify cleanup directories are removed.

    Checks:
    - OIM data directories are deleted
    - Configuration directories are cleaned up
    """
    log = TestLogger(TEST_NAMES["directories_removed"])
    log.check("Checking cleanup directories on OIM host")

    result = check_directories_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["directories_all_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["directories_still_present"], result["details"])

    assert result["success"], ASSERT_MSGS["directories_still_present"].format(
        details=result["error"]
    )


# =============================================================================
# 8. REGCTL, S3CMD, PACKAGES REMOVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_packages_removed(host):
    """
    Test Case 8: Verify regctl binary, s3cmd and openchami packages are removed.

    Checks:
    - regctl binary is deleted
    - s3cmd package is uninstalled
    - openchami packages are removed
    """
    log = TestLogger(TEST_NAMES["packages_removed"])
    log.check("Checking regctl binary and openchami packages")

    result = check_packages_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["packages_all_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["packages_still_present"], result["details"])

    assert result["success"], ASSERT_MSGS["packages_still_present"].format(
        details=result["error"]
    )


# =============================================================================
# 9. CHRONYD REMOVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_chronyd_removed(host):
    """
    Test Case 9: Verify chronyd is stopped, disabled, and allow list removed.

    Checks:
    - chronyd service is stopped
    - chronyd is disabled from auto-start
    - chrony.conf allow list entries are removed
    """
    log = TestLogger(TEST_NAMES["chronyd_removed"])
    log.check("Checking chronyd service and chrony.conf")

    result = check_chronyd_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["chronyd_removed"], result["details"])
    else:
        log.failed(LOG_MSGS["chronyd_still_active"], result["details"])

    assert result["success"], ASSERT_MSGS["chronyd_still_active"].format(
        details=result["error"]
    )


