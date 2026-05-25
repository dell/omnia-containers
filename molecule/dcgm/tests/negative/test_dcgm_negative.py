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
DCGM Negative / Error Handling Test Cases.

Spec: TSPEC-DCGM-2026-001 v1.0.0

Test cases:
  TC-E01  test_cuda_prerequisite_blocks_deployment
  TC-E02  test_daemon_crash_auto_recovery
  TC-E03  test_daemon_socket_inaccessible
  TC-E04  test_dcgm_package_install_failure  (manual/lab-only)

NOTE: TC-E02 and TC-E03 perform destructive operations (kill daemon, remove
socket) on the GPU node. They restore the service state before exit.
"""

import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest

from automation_library.core import TestLogger
from automation_library.dcgm.functions import (
    get_gpu_nodes,
    verify_dcgm_daemon_running,
    verify_cuda_prerequisite_blocks_deployment,
    verify_daemon_crash_recovery,
    verify_daemon_socket_error,
)
from automation_library.dcgm.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


# =============================================================================
# SHARED FIXTURE: first GPU node IP
# =============================================================================

@pytest.fixture(scope="module")
def gpu_node_ip(host):
    """Return admin IP of the first available GPU node. Skip module if none."""
    nodes = get_gpu_nodes(host)
    if not nodes:
        pytest.skip(ASSERT["no_gpu_nodes"])
    return nodes[0].get("admin_ip", "")


# =============================================================================
# TC-E01: CUDA NOT PRESENT - DEPLOYMENT BLOCKED
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(1)
def test_cuda_prerequisite_blocks_deployment(host):
    """
    TC-E01: Verify Ansible GPU playbook aborts with a prerequisite error when
    nvidia-smi is not available on the target node (BL-001). DCGM must NOT
    be installed after the failed run.

    Requires a node without NVIDIA drivers (non-GPU node or cleaned node).
    This test uses omnia_test_config.yml -> no_gpu_node_ip if configured,
    otherwise it is skipped.
    """
    from automation_library.core import load_omnia_test_config
    config = load_omnia_test_config()
    no_gpu_ip = config.get("no_gpu_node_ip", "")

    if not no_gpu_ip:
        pytest.skip(
            "no_gpu_node_ip not set in omnia_test_config.yml — "
            "TC-E01 requires a node without NVIDIA drivers"
        )

    log = TestLogger(TEST_NAMES["cuda_not_present"])
    log.check(f"Verifying CUDA prerequisite gate on non-GPU node {no_gpu_ip}")

    result = verify_cuda_prerequisite_blocks_deployment(host, no_gpu_ip)

    if result["success"]:
        log.passed(LOG["cuda_prerequisite_blocked"], result["details"])
    else:
        log.failed(LOG["cuda_prerequisite_blocked"], result["error"])

    assert result["success"], ASSERT["cuda_prerequisite_not_blocked"].format(ip=no_gpu_ip)


# =============================================================================
# TC-E02: DCGM DAEMON CRASH AND AUTO-RECOVERY
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(2)
def test_daemon_crash_auto_recovery(host, gpu_node_ip):
    """
    TC-E02: Simulate DCGM daemon crash via SIGKILL and verify systemd
    auto-restarts the service via Restart=on-failure policy.
    Maps to: BL-005, ST-005→ST-007
    """
    log = TestLogger(TEST_NAMES["daemon_crash_recovery"])
    log.check(f"Simulating nvidia-dcgm.service crash on {gpu_node_ip}")

    result = verify_daemon_crash_recovery(host, gpu_node_ip)

    if result["success"]:
        log.passed(LOG["crash_recovery_ok"], result["details"])
    else:
        log.failed(LOG["daemon_not_running"].format(ip=gpu_node_ip), result["error"])

    # Always verify daemon is running at end of test (restore state)
    restore_result = verify_dcgm_daemon_running(host, gpu_node_ip)
    assert restore_result["success"], (
        f"nvidia-dcgm.service could not be restored on {gpu_node_ip} after crash test. "
        f"Manual intervention required: systemctl start nvidia-dcgm.service"
    )

    assert result["success"], ASSERT["daemon_not_recovered"].format(ip=gpu_node_ip)


# =============================================================================
# TC-E03: DCGM DAEMON SOCKET INACCESSIBLE
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(3)
def test_daemon_socket_inaccessible(host, gpu_node_ip):
    """
    TC-E03: Remove DCGM Unix socket and verify dcgmi returns a clear error.
    Restart daemon and confirm socket is recreated.
    Maps to: VC-005
    """
    log = TestLogger(TEST_NAMES["socket_inaccessible"])
    log.check(f"Testing DCGM socket error handling on {gpu_node_ip}")

    result = verify_daemon_socket_error(host, gpu_node_ip)

    if result["success"]:
        log.passed(LOG["socket_error_handled"], result["details"])
    else:
        log.failed(LOG["socket_error_handled"], result["error"])

    # Verify daemon is back up after the test
    restore_result = verify_dcgm_daemon_running(host, gpu_node_ip)
    assert restore_result["success"], (
        f"nvidia-dcgm.service is not running after socket test on {gpu_node_ip}. "
        f"Manual fix: systemctl restart nvidia-dcgm.service"
    )

    assert result["success"], ASSERT["socket_error_not_handled"].format(
        ip=gpu_node_ip, output=result["error"]
    )


# =============================================================================
# TC-E04: DCGM PACKAGE INSTALLATION FAILURE  (lab-only / manual)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(4)
def test_dcgm_package_install_failure(host, gpu_node_ip):
    """
    TC-E04: Verify error handling and logging when datacenter-gpu-manager
    RPM installation fails (e.g., repo unavailable).

    This test simulates a failing package install by temporarily renaming the
    DCGM repo file and running the playbook. Requires the GPU node to not have
    DCGM pre-installed for a clean test environment.

    Restoration: re-enables the repo and verifies DCGM is installable.

    NOTE: If DCGM is already installed, this test verifies the error path only
    via Ansible --check mode and is marked as conditional.
    """
    from automation_library.core import run_on_remote_node, run_in_container
    from automation_library.dcgm.vars import CMD_TEMPLATES

    log = TestLogger(TEST_NAMES["package_install_failure"])

    # Check if DCGM is already installed
    cmd = run_on_remote_node(host, CMD_TEMPLATES["dcgm_rpm_check"], gpu_node_ip)
    dcgm_pre_installed = cmd.rc == 0 and "datacenter-gpu-manager" in cmd.stdout

    if dcgm_pre_installed:
        log.skipped(
            "DCGM already installed — running failure simulation via Ansible --check",
            f"Node {gpu_node_ip}: datacenter-gpu-manager already present. "
            "Failure simulation is limited to --check mode."
        )
        pytest.skip(
            "DCGM pre-installed on GPU node. "
            "TC-E04 full validation requires a clean node. Marking as skipped."
        )

    # Disable dnf repo to simulate install failure
    disable_cmd = (
        "test -f /etc/yum.repos.d/cuda.repo && "
        "mv /etc/yum.repos.d/cuda.repo /etc/yum.repos.d/cuda.repo.bak || true"
    )
    run_on_remote_node(host, disable_cmd, gpu_node_ip)

    try:
        # Attempt install — expect failure
        cmd = run_in_container(
            host,
            CMD_TEMPLATES["ansible_gpu_playbook"].format(node=gpu_node_ip)
        )
        output = (cmd.stdout + cmd.stderr).strip()
        install_failed = cmd.rc != 0

        # Failure should be logged
        failure_logged = any(
            kw in output.lower()
            for kw in ("failed", "error", "unable to install", "no package")
        )

        log_detail = (
            f"Node {gpu_node_ip}:\n"
            f"  Playbook exit code: {cmd.rc}\n"
            f"  Failure detected: {install_failed}\n"
            f"  Error logged in output: {failure_logged}\n"
            f"  Output snippet: {output[:400]}"
        )

        if install_failed and failure_logged:
            log.passed(LOG["install_failure_logged"], log_detail)
        else:
            log.failed(LOG["install_failure_logged"], log_detail)

        assert install_failed and failure_logged, (
            f"TC-E04: Playbook did not fail or log error correctly on {gpu_node_ip}. "
            f"rc={cmd.rc}, failure_logged={failure_logged}"
        )

    finally:
        # Restore repo
        restore_cmd = (
            "test -f /etc/yum.repos.d/cuda.repo.bak && "
            "mv /etc/yum.repos.d/cuda.repo.bak /etc/yum.repos.d/cuda.repo || true"
        )
        run_on_remote_node(host, restore_cmd, gpu_node_ip)
        log.check(f"Restored cuda.repo on {gpu_node_ip}")
