# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Testinfra tests for omnia.sh installation verification.

This file contains minimal test functions that call the centralized
verification functions in omnia_sh_func.py.
"""

from automation_library.core import TestLogger
from automation_library.omnia_sh.messages.omnia_sh_msgs import (
    TEST_VARS, TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)
from automation_library.omnia_sh.functions.omnia_sh_func import (
    check_container_running,
    check_file_exists,
    check_service_running,
    check_ssh_to_container,
    check_ssh_from_container,
    check_metadata_file,
)


def test_omnia_core_container_running(host):
    """Verify omnia_core container is running."""
    log = TestLogger(TEST_NAMES["container_running"])
    log.check("Checking container: omnia_core")

    result = check_container_running(host)

    if result["success"]:
        d = result["details"]
        details = f"Container: {d['container']}\nStatus: {d['status']}\nImage: {d['image']}\nPorts: {d['ports']}"
        log.passed(LOG_MSGS["container_running"], details)
    else:
        log.failed(LOG_MSGS["container_not_running"], result["error"])

    assert result["success"], result["error"]


def test_omnia_core_container_file_exists(host):
    """Verify omnia_core.container file is present."""
    log = TestLogger(TEST_NAMES["container_file"])
    path = TEST_VARS["container_file"]
    log.check(f"Checking file: {path}")

    result = check_file_exists(host, path)

    if result["success"]:
        log.passed(LOG_MSGS["file_exists"], result["details"])
    else:
        log.failed(LOG_MSGS["file_not_found"], result["error"])

    assert result["success"], result["error"]


def test_omnia_core_service_running(host):
    """Verify omnia_core systemd service is running."""
    log = TestLogger(TEST_NAMES["service_running"])
    service = TEST_VARS["service_name"]
    log.check(f"Checking service: {service}")

    result = check_service_running(host, service)

    if result["success"]:
        log.passed(LOG_MSGS["service_active"], result["details"])
    else:
        log.failed(LOG_MSGS["service_inactive"].format(status=result["status"]), result["details"])

    assert result["success"], ASSERT_MSGS["service_not_active"].format(status=result["status"])


def test_oim_metadata_file_exists(host):
    """Verify oim_metadata.yml file is present."""
    log = TestLogger(TEST_NAMES["metadata_file"])
    path = TEST_VARS["metadata_file"]
    log.check(f"Checking file: {path}")

    result = check_metadata_file(host)

    if result["success"]:
        log.passed(LOG_MSGS["file_exists"], result["details"])
    else:
        log.failed(LOG_MSGS["file_not_found"], result["error"])

    assert result["success"], result["error"]


def test_passwordless_ssh_to_container(host):
    """Verify passwordless SSH from OIM server to omnia_core container."""
    log = TestLogger(TEST_NAMES["ssh_to_container"])
    alias = TEST_VARS["ssh_alias"]
    log.check(f"Testing SSH: OIM server → {alias}")

    result = check_ssh_to_container(host)

    if result["success"]:
        d = result["details"]
        details = f"Connected as: {d['user']}\nWorking directory: {d['workdir']}\nConnection: {d['connection']}"
        log.passed(LOG_MSGS["ssh_success"], details)
    else:
        log.failed(LOG_MSGS["ssh_failed"], result["error"])

    assert result["success"], ASSERT_MSGS["ssh_failed"].format(error=result["error"])


def test_passwordless_ssh_from_container_to_host(host):
    """Verify passwordless SSH from omnia_core container to OIM server."""
    log = TestLogger(TEST_NAMES["ssh_from_container"])
    alias = TEST_VARS["ssh_alias"]
    oim_ip = TEST_VARS["oim_server_ip"]

    assert oim_ip, ASSERT_MSGS["config_missing"]

    log.check(f"Testing SSH: {alias} → OIM server ({oim_ip})")

    result = check_ssh_from_container(host, oim_ip)

    if result["success"]:
        d = result["details"]
        details = f"Connected as: {d['user']}\nTarget: {d['target']}\nConnection: {d['connection']}"
        log.passed(LOG_MSGS["ssh_success"], details)
    else:
        log.failed(LOG_MSGS["ssh_failed"], result["error"])

    assert result["success"], ASSERT_MSGS["ssh_failed"].format(error=result["error"])
