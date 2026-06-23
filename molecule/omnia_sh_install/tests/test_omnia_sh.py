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
Omnia.sh Install Test Cases.

This module tests the omnia.sh --install workflow. Install is driven from
tests with progress output every 10 seconds..

Test cases (executed in order):
1. Install omnia.sh (validate NFS, download, run --install) - skip if container running
2. Verify omnia_core container is running
3. Verify omnia_core.container file exists
4. Verify omnia_core service is running
5. Verify oim_metadata.yml file exists inside container
6. Verify passwordless SSH to container works
7. Verify passwordless SSH from container works
"""

import pytest

from automation_library.core import TestLogger
from automation_library.omnia_sh.vars.omnia_sh_vars import TEST_VARS, OMNIA_SH_VARS
from automation_library.omnia_sh.messages.omnia_sh_msgs import (
    TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS, SKIP_MSGS
)
from automation_library.omnia_sh.functions.omnia_sh_func import (
    check_container_running,
    check_file_exists,
    check_service_running,
    check_ssh_to_container,
    check_ssh_from_container,
    check_metadata_file,
    validate_nfs_config,
    download_omnia_sh_script,
    run_omnia_sh_install_testinfra,
    setup_internal_nfs_server,
)

# Module-level flag to track install success
_install_passed = False


# =============================================================================
# INSTALL TEST (TC-1) - Combined NFS validation, download, and install
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_omnia_sh_install(host):
    """
    Test Case 1: Install omnia.sh (validate NFS, download, run --install).

    This test combines:
    - NFS configuration validation
    - Download omnia.sh script with fallback
    - Run omnia.sh --install

    Skip entire test if omnia_core container is already running.
    For internal NFS, sets up NFS server before install.
    """
    global _install_passed
    log = TestLogger(TEST_NAMES["omnia_sh_install"])

    # Step 1: Check if container already running - skip install but allow verifications
    container_result = check_container_running(host)
    if container_result["success"]:
        # Container running = install not needed, but verification tests should run
        _install_passed = True
        print(f"    │ {SKIP_MSGS['container_running']}", flush=True)
        log.skipped(SKIP_MSGS["container_running"])
        pytest.skip(SKIP_MSGS["container_running"])

    # Step 2: Validate NFS configuration
    print("    ▸ Validating NFS configuration...", flush=True)
    nfs_result = validate_nfs_config()
    if not nfs_result["success"]:
        log.failed(LOG_MSGS["nfs_config_invalid"], nfs_result["error"])
        assert False, ASSERT_MSGS["nfs_config_invalid"].format(
            missing_fields=", ".join(nfs_result.get("missing_fields", []))
        )
    print(f"    ✓ NFS config valid: {nfs_result['share_option']}/{nfs_result['nfs_type'] or 'N/A'}", flush=True)

    # Step 3: Download omnia.sh
    print("    ▸ Downloading omnia.sh...", flush=True)
    download_result = download_omnia_sh_script(host)
    if not download_result["success"]:
        log.failed(LOG_MSGS["download_failed"], download_result["error"])
        assert False, ASSERT_MSGS["download_failed"].format(error=download_result["error"])
    print(f"    ✓ Downloaded: {download_result['path']} ({download_result['ref_type']})", flush=True)

    # Step 4: For internal NFS, setup NFS server first
    if OMNIA_SH_VARS["share_option"] == "NFS" and OMNIA_SH_VARS["nfs_type"] == "internal":
        print("    ▸ Setting up internal NFS server...", flush=True)
        nfs_setup_result = setup_internal_nfs_server(host)
        if not nfs_setup_result["success"]:
            log.failed(LOG_MSGS["internal_nfs_failed"], nfs_setup_result["error"])
            pytest.fail(nfs_setup_result["error"])
        print(f"    ✓ {nfs_setup_result['details']}", flush=True)

    # Step 5: Run omnia.sh --install with progress callback
    print("    ▸ Running omnia.sh --install...", flush=True)

    def _progress(elapsed: int) -> None:
        print(f"    │ Running... {elapsed}s elapsed", flush=True)

    result = run_omnia_sh_install_testinfra(host, progress_callback=_progress)

    if result["success"]:
        # Show all output lines with │ prefix
        output_lines = result["output"].strip().split("\n")
        for line in output_lines:
            print(f"    │ {line}", flush=True)
        details = f"share_option: {nfs_result['share_option']}\nnfs_type: {nfs_result['nfs_type'] or 'N/A'}"
        log.passed(LOG_MSGS["install_success"], details)
        # Mark install as passed for subsequent tests
        _install_passed = True
    else:
        log.failed(LOG_MSGS["install_failed"], result["error"])

    assert result["success"], ASSERT_MSGS["install_failed"].format(error=result["error"])


# =============================================================================
# VERIFICATION TESTS (TC-2 to TC-7)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_omnia_core_container_running(host):
    """
    Test Case 2: Verify omnia_core container is running.

    Checks:
    - Container exists and is in 'running' state
    - Reports container image, status, and ports
    """
    log = TestLogger(TEST_NAMES["container_running"])

    result = check_container_running(host)

    if result["success"]:
        d = result["details"]
        details = (
            f"Container: {d['container']}\n"
            f"Status: {d['status']}\n"
            f"Image: {d['image']}\n"
            f"Ports: {d['ports']}"
        )
        log.passed(LOG_MSGS["container_running"], details)
    else:
        log.failed(LOG_MSGS["container_not_running"], result["error"])

    assert result["success"], result["error"]


@pytest.mark.sanity
@pytest.mark.order(3)
def test_omnia_core_container_file_exists(host):
    """
    Test Case 3: Verify omnia_core.container file is present.

    Checks:
    - Systemd container unit file exists at expected path
    - File is readable and has correct permissions
    """
    if not _install_passed:
        log = TestLogger(TEST_NAMES["container_file"])
        log.skipped(SKIP_MSGS["install_failed"])
        pytest.skip(SKIP_MSGS["install_failed"])
    log = TestLogger(TEST_NAMES["container_file"])
    path = TEST_VARS["container_file"]

    result = check_file_exists(host, path)

    if result["success"]:
        log.passed(LOG_MSGS["file_exists"], f"Path: {path}\n{result['details']}")
    else:
        log.failed(LOG_MSGS["file_not_found"], f"Path: {path}\n{result['error']}")

    assert result["success"], result["error"]


@pytest.mark.sanity
@pytest.mark.order(4)
def test_omnia_core_service_running(host):
    """
    Test Case 4: Verify omnia_core systemd service is running.

    Checks:
    - Service is active (running)
    - Service is enabled for auto-start
    """
    if not _install_passed:
        log = TestLogger(TEST_NAMES["service_running"])
        log.skipped(SKIP_MSGS["install_failed"])
        pytest.skip(SKIP_MSGS["install_failed"])
    log = TestLogger(TEST_NAMES["service_running"])
    service = TEST_VARS["service_name"]

    result = check_service_running(host, service)

    if result["success"]:
        log.passed(LOG_MSGS["service_active"], f"Service: {service}\n{result['details']}")
    else:
        log.failed(
            LOG_MSGS["service_inactive"].format(status=result["status"]),
            f"Service: {service}\n{result['details']}"
        )

    assert result["success"], ASSERT_MSGS["service_not_active"].format(status=result["status"])


@pytest.mark.sanity
@pytest.mark.order(5)
def test_oim_metadata_file_exists(host):
    """
    Test Case 5: Verify oim_metadata.yml file is present inside container.

    Checks:
    - Metadata file exists at /opt/omnia/.data/oim_metadata.yml
    - File contains valid YAML with OIM configuration
    """
    if not _install_passed:
        log = TestLogger(TEST_NAMES["metadata_file"])
        log.skipped(SKIP_MSGS["install_failed"])
        pytest.skip(SKIP_MSGS["install_failed"])
    log = TestLogger(TEST_NAMES["metadata_file"])
    path = TEST_VARS["metadata_file"]

    result = check_metadata_file(host)

    if result["success"]:
        log.passed(LOG_MSGS["file_exists"], f"Path: {path}\n{result['details']}")
    else:
        log.failed(LOG_MSGS["file_not_found"], f"Path: {path}\n{result['error']}")

    assert result["success"], result["error"]


@pytest.mark.sanity
@pytest.mark.order(6)
def test_passwordless_ssh_to_container(host):
    """
    Test Case 6: Verify passwordless SSH from OIM server to omnia_core container.

    Checks:
    - SSH connection works without password prompt
    - Can execute commands inside container via SSH
    """
    if not _install_passed:
        log = TestLogger(TEST_NAMES["ssh_to_container"])
        log.skipped(SKIP_MSGS["install_failed"])
        pytest.skip(SKIP_MSGS["install_failed"])
    log = TestLogger(TEST_NAMES["ssh_to_container"])
    alias = TEST_VARS["ssh_alias"]

    result = check_ssh_to_container(host)

    if result["success"]:
        d = result["details"]
        details = (
            f"Direction: OIM server → {alias}\n"
            f"Connected as: {d['user']}\n"
            f"Working directory: {d['workdir']}\n"
            f"Connection: {d['connection']}"
        )
        log.passed(LOG_MSGS["ssh_success"], details)
    else:
        log.failed(LOG_MSGS["ssh_failed"], f"Direction: OIM server → {alias}\n{result['error']}")

    assert result["success"], ASSERT_MSGS["ssh_failed"].format(error=result["error"])


@pytest.mark.sanity
@pytest.mark.order(7)
def test_passwordless_ssh_from_container_to_host(host):
    """
    Test Case 7: Verify passwordless SSH from omnia_core container to OIM server.

    Checks:
    - SSH connection from container to OIM works without password
    - Bidirectional SSH connectivity is established

    Note:
    - Uses localhost when oim_server_ip is not configured (local execution)
    """
    if not _install_passed:
        log = TestLogger(TEST_NAMES["ssh_from_container"])
        log.skipped(SKIP_MSGS["install_failed"])
        pytest.skip(SKIP_MSGS["install_failed"])
    log = TestLogger(TEST_NAMES["ssh_from_container"])
    alias = TEST_VARS["ssh_alias"]
    oim_ip = TEST_VARS["oim_server_ip"]

    # If oim_server_ip is not configured, test against localhost
    if not oim_ip:
        oim_ip = "localhost"

    result = check_ssh_from_container(host, oim_ip)

    if result["success"]:
        d = result["details"]
        details = (
            f"Direction: {alias} → OIM server ({oim_ip})\n"
            f"Connected as: {d['user']}\n"
            f"Target: {d['target']}\n"
            f"Connection: {d['connection']}"
        )
        log.passed(LOG_MSGS["ssh_success"], details)
    else:
        log.failed(LOG_MSGS["ssh_failed"], f"Direction: {alias} → OIM server ({oim_ip})\n{result['error']}")

    assert result["success"], ASSERT_MSGS["ssh_failed"].format(error=result["error"])
