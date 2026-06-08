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
DCGM Functional, Idempotency, and Compatibility Test Cases.

Spec: TSPEC-DCGM-2026-001 v1.0.0

Test cases:
  TC-F01  test_cuda_validation
  TC-F02  test_cuda_atomic_lock_installation
  TC-F03  test_dcgm_package_installed
  TC-F04  test_dcgm_daemon_running
  TC-F05  test_gpu_discovery
  TC-F08  test_cuda_login_compiler_install
  TC-F09  test_cuda_compute_node_install
  TC-F10  test_multi_gpu_discovery
  TC-F16  test_toolkit_nfs_shared_storage
  TC-F18  test_nvidia_peer_mem_installed
  TC-C01  test_rhel_compatibility
  TC-C02  test_cuda_version_compatibility
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
    get_login_compiler_nodes,
    verify_cuda_validation,
    verify_dcgm_metrics_dmon,
    verify_cuda_atomic_lock_installation,
    verify_dcgm_package_installed,
    verify_dcgm_daemon_running,
    verify_gpu_discovery,
    verify_multi_gpu_discovery,
    verify_multi_login_compiler_atomic_lock,
    verify_multi_gpu_nodes_no_login_compiler,
    verify_cuda_login_compiler_install,
    verify_cuda_compute_node_install,
    verify_toolkit_nfs_shared_storage,
    verify_nvidia_peer_mem_all_gpu_nodes,
    verify_rhel_compatibility,
    verify_cuda_version_compatibility,
)
from automation_library.dcgm.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
)


# =============================================================================
# SHARED FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def all_gpu_nodes(host):
    """Return list of all GPU node info dicts. Skip module if none found."""
    nodes = get_gpu_nodes(host)
    if not nodes:
        pytest.skip(ASSERT["no_gpu_nodes"])
    return nodes


@pytest.fixture(scope="module")
def has_login_compiler(host):
    """Return True if any login_compiler nodes exist, False otherwise."""
    nodes = get_login_compiler_nodes(host)
    return bool(nodes)


# =============================================================================
# TC-F01: CUDA VALIDATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_cuda_validation(host, gpu_node_ip):
    """
    TC-F01: Verify NVIDIA driver and CUDA 13.x+ toolkit are installed and
    functional on GPU nodes. nvidia-smi must succeed; nvcc must report >= 13.x.
    Maps to: SB-001, VC-001, BL-002
    """
    log = TestLogger(TEST_NAMES["cuda_validation"])
    log.check(f"Verifying CUDA on GPU node {gpu_node_ip}")

    result = verify_cuda_validation(host, gpu_node_ip)

    if result["success"]:
        log.passed(LOG["nvidia_smi_ok"].format(ip=gpu_node_ip), result["details"])
    else:
        log.failed(LOG["nvidia_smi_fail"].format(ip=gpu_node_ip), result["error"])

    assert result["success"], ASSERT["nvidia_smi_failed"].format(
        ip=gpu_node_ip, rc="non-zero", stderr=result["error"]
    )


# =============================================================================
# TC-F02: CUDA TOOLKIT INSTALLATION WITH ATOMIC LOCK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_cuda_atomic_lock_installation(host, gpu_node_ip):
    """
    TC-F02: Verify CUDA toolkit is installed to /hpc_tools/cuda via atomic lock.
    Confirm directory structure, bash profile exports, and lock file released.
    Maps to: SB-002, VC-003, BL-003, BL-004
    """
    log = TestLogger(TEST_NAMES["cuda_atomic_lock"])
    log.check(f"Verifying CUDA atomic lock toolkit installation on {gpu_node_ip}")

    result = verify_cuda_atomic_lock_installation(host, gpu_node_ip)

    if result["success"]:
        log.passed(LOG["lock_file_released"], result["details"])
    else:
        log.failed(LOG["lock_file_created"].format(lock_path="/tmp/cuda_install.lock"), result["error"])

    assert result["success"], result["error"]


# =============================================================================
# TC-F03: DCGM PACKAGE INSTALLATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_dcgm_package_installed(host, gpu_node_ip):
    """
    TC-F03: Verify datacenter-gpu-manager RPM is installed and DCGM binaries
    are present on the GPU node.
    Maps to: SB-003, VC-008
    """
    log = TestLogger(TEST_NAMES["dcgm_package_install"])
    log.check(f"Checking datacenter-gpu-manager on {gpu_node_ip}")

    result = verify_dcgm_package_installed(host, gpu_node_ip)

    if result["success"]:
        log.passed(
            LOG["dcgm_pkg_installed"].format(ip=gpu_node_ip),
            result["details"]
        )
    else:
        log.failed(LOG["dcgm_pkg_not_found"].format(ip=gpu_node_ip), result["error"])

    assert result["success"], ASSERT["dcgm_not_installed"].format(ip=gpu_node_ip)


# =============================================================================
# TC-F04: DCGM DAEMON STARTUP
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_dcgm_daemon_running(host, gpu_node_ip):
    """
    TC-F04: Verify nvidia-dcgm.service is active (running) and enabled on
    the GPU node.
    Maps to: SB-004
    """
    log = TestLogger(TEST_NAMES["dcgm_daemon_startup"])
    log.check(f"Checking nvidia-dcgm.service on {gpu_node_ip}")

    result = verify_dcgm_daemon_running(host, gpu_node_ip)

    if result["success"]:
        log.passed(LOG["daemon_running"].format(ip=gpu_node_ip), result["details"])
    else:
        log.failed(LOG["daemon_not_running"].format(ip=gpu_node_ip), result["error"])

    assert result["success"], ASSERT["daemon_not_running"].format(
        ip=gpu_node_ip, status=result["error"]
    )


# =============================================================================
# TC-F05: GPU DISCOVERY AND ENUMERATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_gpu_discovery(host, gpu_node_ip):
    """
    TC-F05: Verify dcgmi discovery -l enumerates GPUs with unique UUIDs and
    metadata on the GPU node.
    Maps to: SB-005, VC-002
    """
    log = TestLogger(TEST_NAMES["gpu_discovery"])
    log.check(f"Running dcgmi discovery on {gpu_node_ip}")

    result = verify_gpu_discovery(host, gpu_node_ip)

    if result["success"]:
        log.passed(
            LOG["gpus_discovered"].format(count=result["gpu_count"], ip=gpu_node_ip),
            result["details"]
        )
    else:
        log.failed(LOG["gpu_count_mismatch"].format(
            expected=">=1", actual=result["gpu_count"]), result["error"]
        )

    assert result["success"], ASSERT["gpu_discovery_failed"].format(
        ip=gpu_node_ip, output=result["error"]
    )


# =============================================================================
# TC-F11: MULTIPLE LOGIN_COMPILER NODES — ONLY ONE INSTALLER (ATOMIC LOCK)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_multi_login_compiler_atomic_lock(host):
    """
    TC-F11: If multiple login_compiler nodes exist, verify CUDA toolkit install
    runs on exactly one node while others skip.
    """
    log = TestLogger(TEST_NAMES["multi_login_compiler_lock"])
    log.check("Verifying atomic lock behavior across login_compiler nodes")

    result = verify_multi_login_compiler_atomic_lock(host)

    if not result.get("checked"):
        log.skipped("Less than two login_compiler nodes — TC-F11 not applicable")
        pytest.skip("Less than two login_compiler nodes — TC-F11 not applicable")

    if result["success"]:
        log.passed("Atomic lock ensured single installer", result["details"])
    else:
        log.failed("Atomic lock behavior invalid", result["error"] + "\n" + result.get("details", ""))

    assert result["success"], result.get("error", "Atomic lock failed on login_compiler nodes")


# =============================================================================
# TC-F12: MULTIPLE GPU NODES WITHOUT LOGIN_COMPILER — ONLY ONE INSTALLER
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_multi_gpu_nodes_no_login_compiler(host):
    """
    TC-F12: If no login_compiler node exists and multiple GPU nodes are present,
    verify exactly one GPU node performed the toolkit installation while others skipped.
    """
    log = TestLogger(TEST_NAMES["multi_gpu_nodes_no_login"])
    log.check("Verifying atomic lock behavior across GPU nodes (no login_compiler)")

    result = verify_multi_gpu_nodes_no_login_compiler(host)

    # Not applicable if <2 GPU nodes or if login_compiler nodes exist
    if not result.get("checked"):
        reason = result.get("error", "Preconditions not met for TC-F12")
        log.skipped(reason)
        pytest.skip(reason)

    if result["success"]:
        log.passed("Atomic lock ensured single installer", result["details"])
    else:
        log.failed("Atomic lock behavior invalid", result["error"] + "\n" + result.get("details", ""))

    assert result["success"], result.get("error", "Atomic lock failed on GPU nodes (no login_compiler)")

# =============================================================================
# TC-F07: GPU JOB EXECUTION WITH METRICS MONITORING (dcgmi dmon)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_gpu_metrics_monitoring(host, gpu_node_ip):
    """
    TC-F07: Verify dcgmi dmon returns samples for the configured metric fields on each GPU node.
    """
    log = TestLogger(TEST_NAMES["gpu_metrics_monitoring"])
    log.check(f"Collecting DCGM metrics via dcgmi dmon on {gpu_node_ip}")

    result = verify_dcgm_metrics_dmon(host, gpu_node_ip)

    if result["success"]:
        log.passed("dcgmi dmon returned metrics", result["details"])
    else:
        log.failed("dcgmi dmon metrics collection failed", result["error"])

    assert result["success"], result.get("error", "dcgmi dmon metrics not generated")


# =============================================================================
# TC-F08: CUDA TOOLKIT INSTALL - LOGIN COMPILER NODE AVAILABLE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_cuda_login_compiler_install(host, login_compiler_ip):
    """
    TC-F08: Verify CUDA toolkit is accessible on login_compiler node but
    CUDA driver (nvidia-smi) is NOT installed there.
    Maps to: BL-002
    
    This test is parametrized to run on ALL login_compiler nodes.
    """
    log = TestLogger(TEST_NAMES["cuda_login_compiler"])
    log.check(f"Verifying CUDA install on login_compiler {login_compiler_ip}")

    result = verify_cuda_login_compiler_install(host, login_compiler_ip)

    if result["success"]:
        log.passed(LOG["nvcc_version_ok"].format(
            version="13.x+", path="/hpc_tools/cuda"), result["details"]
        )
    else:
        log.failed(LOG["nvcc_version_fail"].format(
            version="unknown", path="/hpc_tools/cuda"), result["error"]
        )

    assert result["success"], result["error"]


# =============================================================================
# TC-F09: CUDA TOOLKIT AND DRIVER INSTALL - COMPUTE NODE (NO LOGIN COMPILER)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_cuda_compute_node_install(host, gpu_node_ip, has_login_compiler):
    """
    TC-F09: Verify both CUDA toolkit (NFS) and CUDA driver (nvidia-smi) are
    present on GPU/compute nodes when no login_compiler exists.
    Maps to: BL-002
    """
    if has_login_compiler:
        pytest.skip(
            "login_compiler node is present — TC-F09 applies only when no login_compiler exists"
        )

    log = TestLogger(TEST_NAMES["cuda_compute_no_login"])
    log.check(f"Verifying CUDA toolkit + driver on compute node {gpu_node_ip}")

    result = verify_cuda_compute_node_install(host, gpu_node_ip)

    if result["success"]:
        log.passed(LOG["nvidia_smi_ok"].format(ip=gpu_node_ip), result["details"])
    else:
        log.failed(LOG["nvidia_smi_fail"].format(ip=gpu_node_ip), result["error"])

    assert result["success"], result["error"]


# =============================================================================
# TC-F10: MULTI-GPU DISCOVERY (4x GPUs)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_multi_gpu_discovery(host, all_gpu_nodes):
    """
    TC-F10: Verify dcgmi discovery enumerates all GPUs on a multi-GPU node
    (4x A100/H100/V100) with unique UUIDs.
    Maps to: SB-005, VC-002
    """
    multi_gpu_nodes = [n for n in all_gpu_nodes if n.get("gpu_count", 0) >= 4
                       or n.get("is_multi_gpu", False)]

    if not multi_gpu_nodes:
        pytest.skip("No multi-GPU node (4x) found in inventory — TC-F10 skipped")

    admin_ip = multi_gpu_nodes[0].get("admin_ip", "")
    log = TestLogger(TEST_NAMES["multi_gpu_discovery"])
    log.check(f"Running multi-GPU discovery on {admin_ip}")

    result = verify_multi_gpu_discovery(host, admin_ip, expected_gpu_count=4)

    if result["success"]:
        log.passed(
            LOG["gpus_discovered"].format(count=result["gpu_count"], ip=admin_ip),
            result["details"]
        )
    else:
        log.failed(LOG["gpu_count_mismatch"].format(
            expected=4, actual=result["gpu_count"]), result["error"]
        )

    assert result["success"], ASSERT["gpu_count_mismatch"].format(
        ip=admin_ip, expected=4, actual=result["gpu_count"]
    )


# =============================================================================
# TC-F16: TOOLKIT NFS SHARED STORAGE VALIDATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(12)
def test_toolkit_nfs_shared_storage(host, gpu_node_ip):
    """
    TC-F16: Verify /hpc_tools is NFS-mounted and CUDA toolkit is accessible
    from the GPU node via NFS.
    Maps to: BL-004
    """
    log = TestLogger(TEST_NAMES["toolkit_nfs_validation"])
    log.check(f"Verifying NFS toolkit access on {gpu_node_ip}")

    result = verify_toolkit_nfs_shared_storage(host, gpu_node_ip)

    if result["success"]:
        log.passed(LOG["cuda_nfs_accessible"].format(ip=gpu_node_ip), result["details"])
    else:
        log.failed(LOG["nfs_mount_ok"].format(ip=gpu_node_ip), result["error"])

    assert result["success"], ASSERT["cuda_nfs_not_accessible"].format(ip=gpu_node_ip)


# =============================================================================
# TC-F18: nvidia_peer_mem.ko MODULE INSTALLATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(13)
def test_nvidia_peer_mem_installed(host):
    """
    TC-F18: Verify nvidia_peer_mem kernel module is loaded and configured for
    auto-load on boot on ALL GPU nodes.
    Maps to: VC-006
    """
    log = TestLogger(TEST_NAMES["nvidia_peer_mem"])
    log.check("Verifying nvidia_peer_mem module across all GPU nodes")

    result = verify_nvidia_peer_mem_all_gpu_nodes(host)

    if not result["results"]:
        log.skipped(LOG["no_gpu_nodes"], "No GPU nodes found — TC-F18 skipped")
        pytest.skip(ASSERT["no_gpu_nodes"])

    if result["success"]:
        count = len(result["results"])
        log.passed(LOG["peer_mem_all_nodes_ok"].format(count=count), result["details"])
    else:
        log.failed(LOG["peer_mem_not_loaded"].format(ip=str(result["failed_nodes"])), result["error"])

    assert result["success"], ASSERT["peer_mem_not_loaded"].format(
        ip=str(result.get("failed_nodes", []))
    )


# =============================================================================
# TC-C01: RHEL 10.x OS COMPATIBILITY
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(14)
def test_rhel_compatibility(host, gpu_node_ip):
    """
    TC-C01: Verify GPU node OS is RHEL 10.x.
    Maps to: VC-008
    """
    log = TestLogger(TEST_NAMES["rhel_compatibility"])
    log.check(f"Checking OS version on {gpu_node_ip}")

    result = verify_rhel_compatibility(host, gpu_node_ip)

    if result["success"]:
        log.passed(LOG["rhel_version_ok"].format(version=result["os_version"]), result["details"])
    else:
        log.failed(LOG["rhel_version_fail"].format(version=result["os_version"]), result["error"])

    assert result["success"], ASSERT["rhel_version_mismatch"].format(
        ip=gpu_node_ip, version=result.get("os_version", "unknown")
    )


# =============================================================================
# TC-C02: CUDA 13.x COMPATIBILITY
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(16)
def test_cuda_version_compatibility(host, gpu_node_ip):
    """
    TC-C02: Verify CUDA 13.x toolkit and drivers are present and DCGM daemon
    operates correctly with CUDA 13.x.
    Maps to: VC-011
    """
    log = TestLogger(TEST_NAMES["cuda_compatibility"])
    log.check(f"Verifying CUDA 13.x compatibility on {gpu_node_ip}")

    result = verify_cuda_version_compatibility(host, gpu_node_ip)

    if result["success"]:
        log.passed(LOG["cuda_version_ok"].format(version=result["cuda_version"]), result["details"])
    else:
        log.failed(LOG["cuda_version_fail"].format(version=result["cuda_version"]), result["error"])

    assert result["success"], ASSERT["cuda_version_below_minimum"].format(
        ip=gpu_node_ip, version=result.get("cuda_version", "unknown")
    )
