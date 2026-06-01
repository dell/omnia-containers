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

"""Slurm reboot scenario test cases for OMNIA.

This module contains test cases to verify the slurm cluster survives node reboots.
All node types (control, compute, login, login_compiler) are rebooted simultaneously.

  TC44 - Submit pre-reboot sbatch job (for slurmdbd data preservation check)
  TC45 - Reboot ALL slurm nodes in parallel and verify they come back online
  TC46 - Verify cloud-init completes on control and compute nodes after reboot
  TC47 - Verify cloud-init completes on login_compiler nodes after reboot (longer timeout)
  TC48 - Verify control node services (slurmctld, slurmdbd, munge) active after reboot
  TC49 - Verify compute node services (slurmd, munge) active after reboot
  TC50 - Verify login node services (slurmd, munge) active after reboot
  TC51 - Verify slurmdbd is active on control nodes after reboot
  TC52 - Verify slurmdbd data preserved: pre-reboot job found in sacct
  TC53 - Wait for slurm compute nodes to return to idle after reboot
  TC54 - Submit and verify sbatch job after reboot
  TC55 - Verify LDAP user login after reboot
  TC56 - Verify LDAP user sbatch job after reboot
  TC57 - Verify LDAP user OpenMPI job after reboot
"""

import os
import sys

# Add the project root to the Python path
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../.."),
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
from automation_library.core import TestLogger
from automation_library.slurm.functions.slurm_reboot_func import (
    reboot_all_slurm_nodes_parallel,
    verify_cloud_init_after_reboot,
    verify_control_node_services_after_reboot,
    verify_compute_node_services_after_reboot,
    verify_login_node_services_after_reboot,
    verify_slurmdbd_active,
    verify_slurmdbd_data_preserved,
    wait_for_nodes_idle_after_reboot,
    verify_sbatch_after_reboot,
    verify_ldap_login_after_reboot,
    verify_ldap_sbatch_after_reboot,
)
from automation_library.slurm.functions.slurm_func import verify_sbatch_job
from automation_library.slurm.functions.slurm_ldap_func import verify_openmpi_job

# =============================================================================
# Module-level shared state
# =============================================================================
_reboot_state: dict = {
    "pre_reboot_job_id": "",
    "control_nodes": [],
    "slurm_nodes": [],
    "login_nodes": [],
    "login_compiler_nodes": [],
}


# =============================================================================
# REBOOT SCENARIO
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(44)
def test_submit_pre_reboot_sbatch_job(host):
    """TC44: Submit a sbatch job before reboot to verify slurmdbd data preservation."""
    log = TestLogger("Submit pre-reboot sbatch job for slurmdbd verification")
    log.check("Submitting sbatch job before reboot")

    result = verify_sbatch_job(host)

    if result.get("job_id"):
        _reboot_state["pre_reboot_job_id"] = result["job_id"]
        log.check(f"Pre-reboot job ID: {result['job_id']} | State: {result.get('job_state', '')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(45)
def test_reboot_all_nodes_parallel(host):
    """TC45: Reboot ALL slurm nodes in parallel and verify they come back online."""
    log = TestLogger("Reboot ALL slurm nodes in parallel")
    log.check("Issuing reboot on all slurm nodes (control, compute, login, login_compiler) in parallel")

    result = reboot_all_slurm_nodes_parallel(host)

    # Store node lists for subsequent tests
    node_types = result.get("node_types", {})
    _reboot_state["control_nodes"] = node_types.get("control_nodes", [])
    _reboot_state["slurm_nodes"] = node_types.get("slurm_nodes", [])
    _reboot_state["login_nodes"] = node_types.get("login_nodes", [])
    _reboot_state["login_compiler_nodes"] = node_types.get("login_compiler_nodes", [])

    # Log details by node type
    details = result.get("details", {})
    for node_type, node_list in details.items():
        if node_list:
            log.check(f"  {node_type.upper()} nodes:")
            for detail in node_list:
                status = "ONLINE" if detail.get("online") else "OFFLINE"
                elapsed = detail.get("elapsed", 0)
                log.check(f"    {detail['hostname']} ({detail['admin_ip']}): {status} (elapsed: {elapsed}s)")
                if detail.get("error"):
                    log.check(f"      Error: {detail['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(46)
def test_cloud_init_after_reboot(host):
    """TC46: Verify cloud-init completes successfully on control and compute nodes after reboot."""
    log = TestLogger("Verify cloud-init after reboot")
    log.check("Checking cloud-init status on control and compute nodes")

    from automation_library.slurm.functions.slurm_func import (
        get_slurm_control_nodes,
        get_slurm_nodes,
    )

    control_nodes = get_slurm_control_nodes(host)
    slurm_nodes = get_slurm_nodes(host)
    all_nodes = control_nodes + slurm_nodes

    if not all_nodes:
        pytest.skip("No control or compute nodes found in PXE mapping")

    result = verify_cloud_init_after_reboot(host, all_nodes)

    for detail in result.get("details", []):
        status = "done" if detail.get("success") else "FAILED"
        log.check(f"  {detail['hostname']}: cloud-init {status} (status: {detail.get('status', '')})")
        if detail.get("error"):
            log.check(f"    Error: {detail['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(47)
def test_cloud_init_login_compiler_after_reboot(host):
    """TC47: Verify cloud-init completes successfully on login_compiler nodes after reboot.

    This test runs separately from TC46 because login_compiler nodes take longer
    to complete cloud-init (up to 40 minutes).
    """
    log = TestLogger("Verify cloud-init on login_compiler nodes after reboot")
    log.check("Checking cloud-init status on login_compiler nodes (longer timeout)")

    from automation_library.slurm.functions.slurm_func import get_login_compiler_nodes

    login_compiler_nodes = get_login_compiler_nodes(host)

    if not login_compiler_nodes:
        pytest.skip("No login_compiler nodes found in PXE mapping")

    result = verify_cloud_init_after_reboot(host, login_compiler_nodes)

    for detail in result.get("details", []):
        status = "done" if detail.get("success") else "FAILED"
        log.check(f"  {detail['hostname']}: cloud-init {status} (status: {detail.get('status', '')})")
        if detail.get("error"):
            log.check(f"    Error: {detail['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(48)
def test_control_node_services_after_reboot(host):
    """TC48: Verify slurmctld, slurmdbd, and munge are active on control nodes after reboot."""
    log = TestLogger("Verify control node services after reboot")
    log.check("Checking slurmctld, slurmdbd, munge on control nodes")

    result = verify_control_node_services_after_reboot(host)

    for service, details in result.get("details", {}).items():
        for node in details:
            status = "active" if node.get("active") else "INACTIVE"
            log.check(f"  CONTROL {node['hostname']}: {service} - {status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(49)
def test_compute_node_services_after_reboot(host):
    """TC49: Verify slurmd and munge are active on compute nodes after reboot."""
    log = TestLogger("Verify compute node services after reboot")
    log.check("Checking slurmd, munge on compute nodes")

    result = verify_compute_node_services_after_reboot(host)

    for service, details in result.get("details", {}).items():
        for node in details:
            status = "active" if node.get("active") else "INACTIVE"
            log.check(f"  COMPUTE {node['hostname']}: {service} - {status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(50)
def test_login_node_services_after_reboot(host):
    """TC50: Verify slurmd and munge are active on login nodes after reboot.

    Skips if no login nodes are configured.
    """
    log = TestLogger("Verify login node services after reboot")
    log.check("Checking slurmd, munge on login and login_compiler nodes")

    result = verify_login_node_services_after_reboot(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for service, details in result.get("details", {}).items():
        for node in details:
            status = "active" if node.get("active") else "INACTIVE"
            log.check(f"  LOGIN {node['hostname']}: {service} - {status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(51)
def test_slurmdbd_active_after_reboot(host):
    """TC51: Verify slurmdbd service is active on control nodes after reboot."""
    log = TestLogger("Verify slurmdbd service active after reboot")
    log.check("Checking slurmdbd service status on control nodes")

    result = verify_slurmdbd_active(host)

    for detail in result.get("details", []):
        status = "active" if detail.get("active") else "INACTIVE"
        log.check(f"  {detail['hostname']} ({detail['admin_ip']}): slurmdbd {status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(52)
def test_slurmdbd_data_preserved_after_reboot(host):
    """TC52: Verify slurmdbd preserved job history: pre-reboot job found in sacct after reboot."""
    log = TestLogger("Verify slurmdbd data preserved after reboot")

    pre_reboot_job_id = _reboot_state.get("pre_reboot_job_id", "")
    if not pre_reboot_job_id:
        pytest.skip("No pre-reboot job ID available (TC1 may have been skipped or failed)")

    log.check(f"Checking sacct for pre-reboot job ID: {pre_reboot_job_id}")

    result = verify_slurmdbd_data_preserved(host, pre_reboot_job_id)

    if result.get("job_state"):
        log.check(f"  Job {pre_reboot_job_id} state in sacct: {result['job_state']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(53)
def test_nodes_idle_after_reboot(host):
    """TC53: Wait for all slurm compute nodes to return to idle state after reboot."""
    log = TestLogger("Verify slurm nodes return to idle after reboot")
    log.check("Polling sinfo until all compute nodes are idle")

    result = wait_for_nodes_idle_after_reboot(host)

    for node in result.get("node_states", []):
        log.check(f"  {node['node']}: {node['state']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(54)
def test_sbatch_job_after_reboot(host):
    """TC54: Submit and verify sbatch job completes successfully after reboot."""
    log = TestLogger("Submit sbatch job after reboot")
    log.check("Submitting sbatch job from control node after reboot")

    result = verify_sbatch_after_reboot(host)

    if result.get("job_id"):
        log.check(f"  Job ID: {result['job_id']} | State: {result.get('job_state', '')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(55)
def test_ldap_login_after_reboot(host):
    """TC55: Verify LDAP user can log in to allowed nodes after reboot."""
    log = TestLogger("Verify LDAP user login after reboot")
    log.check("Attempting LDAP user SSH login on control, login, login_compiler nodes")

    result = verify_ldap_login_after_reboot(host)

    if result.get("skipped"):
        pytest.skip(result["message"])
        return

    for detail in result.get("details", []):
        status = "SUCCESS" if detail.get("login_success") else "FAILED"
        log.check(f"  {detail.get('hostname', 'unknown')} ({detail.get('admin_ip', '')}): login {status}")
        if detail.get("error"):
            log.check(f"    Error: {detail['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(56)
def test_ldap_sbatch_after_reboot(host):
    """TC56: Verify LDAP user can submit and complete an sbatch job after reboot."""
    log = TestLogger("Verify LDAP user sbatch job after reboot")
    log.check("Submitting sbatch job as LDAP user after reboot")

    result = verify_ldap_sbatch_after_reboot(host)

    if result.get("skipped"):
        pytest.skip(result["message"])
        return

    if result.get("job_id"):
        log.check(f"  Job ID: {result['job_id']} | State: {result.get('job_state', '')} | Node: {result.get('submit_node', '')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.negative
@pytest.mark.order(57)
def test_ldap_openmpi_job_after_reboot(host):
    """TC57: Verify LDAP user can submit and complete an OpenMPI job after reboot."""
    log = TestLogger("Verify LDAP user OpenMPI job after reboot")
    log.check("Submitting OpenMPI job as LDAP user from login_compiler node after reboot")

    result = verify_openmpi_job(host)

    if result.get("skipped"):
        pytest.skip(result["message"])
        return

    if result.get("job_id"):
        log.check(f"  Job ID: {result['job_id']} | State: {result.get('job_state', '')} | Node: {result.get('submit_node', '')}")

    if result.get("output_verification"):
        log.check(f"  Output verification: {result['output_verification']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]
