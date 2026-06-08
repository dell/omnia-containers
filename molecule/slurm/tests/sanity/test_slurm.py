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

"""Slurm cluster test cases for OMNIA.

This module contains test cases to verify the health and status of a Slurm cluster:
  TC1  - All nodes from PXE mapping are joined to Slurm cluster
  TC2  - slurmctld service active on slurm control nodes
  TC3  - slurmd service active on slurm compute nodes
  TC4  - slurmd service active on login nodes (separate)
  TC5  - slurmd service active on login compiler nodes (separate)
  TC6  - munge service active on slurm control nodes
  TC7  - munge service active on slurm compute nodes
  TC8  - munge service active on login nodes
  TC9  - munge service active on login compiler nodes
  TC10 - All slurm compute nodes in idle state (sinfo)
  TC11 - All login and login compiler nodes in idle state (scontrol)
  TC12-TC23 - Passwordless SSH between all node type pairs
  TC24 - srun job from control node
  TC25 - sbatch job from control node verified via sacct
  TC26 - Root single sbatch job from login node(s)
  TC27 - Root multiple sbatch jobs from login node
  TC28 - Root sbatch from multiple login nodes (>1 required)
  TC29 - Drain/undrain queuing: PENDING while drained, RUNNING after undrain
  TC30 - Insufficient resources: job PENDING or rejected
  TC31 - Job queuing: first job RUNNING, second job PENDING on same node
  TC32 - ldapuser login on slurm control nodes
  TC33 - ldapuser login on login nodes
  TC34 - ldapuser login on login compiler nodes
  TC35 - ldapuser login blocked on slurm nodes (no running jobs)
  TC36 - Invalid LDAP username denied login
  TC37 - Invalid LDAP password denied login
  TC38 - LDAP user single sbatch job from login node(s)
  TC39 - LDAP user multiple sbatch jobs from login node
  TC40 - PAM support: ldapuser job from login node
  TC41 - PAM support: ldapuser job from control node
  TC42 - PAM support: ldapuser job from login_compiler node
  TC43 - OpenMPI job from ldapuser on login_compiler node
  TC44 - GPU Hello World job from ldapuser on login_compiler node
  TC45 - GPU Memory Stress Test job from ldapuser on login_compiler node

InfiniBand Tests (pre-check: IB_NIC_NAME and IB_IP present in PXE mapping)
  TC46 - IB Hardware & Link Verification (ibstat, ibstatus, ibv_devinfo, ibv_devices)
  TC47 - DOCA-OFED / MLNX_OFED installation on IB nodes
  TC48 - IB IP correctly assigned to IB interface
  TC49 - IB interface MTU verification (>= 2044 IPoIB standard)
  TC50 - IB subnet mask matches network_spec.yml ib_network
  TC51 - IB IP is within correct ib_network subnet
  TC52 - IB ping test between all IB-configured node pairs
  TC53 - UCX IB-only transport: MPI ping-pong with UCX_TLS=ib,sm,self, verify RDMA
  TC54 - UCX installation check on login_compiler nodes (ucx_info -v + available transports)
"""

import pytest
from automation_library.core import TestLogger
from automation_library.core import is_software_enabled
from automation_library.slurm.functions.slurm_func import (
    verify_slurmctld_active,
    verify_slurmd_active,
    verify_slurm_nodes_idle,
    verify_login_nodes_idle,
    verify_srun_job,
    verify_sbatch_job,
    verify_root_sbatch_from_login_node,
    verify_root_multi_sbatch_from_login_node,
    verify_drain_undrain_queuing,
    verify_insufficient_resources,
    verify_slurmd_on_login_nodes_only,
    verify_slurmd_on_login_compiler_nodes_only,
    verify_munge_on_control_nodes,
    verify_munge_on_slurm_nodes,
    verify_munge_on_login_nodes,
    verify_all_pxe_nodes_in_slurm_cluster,
    verify_munge_on_login_compiler_nodes,
    verify_passwordless_ssh,
    verify_root_sbatch_from_multiple_login_nodes,
)
from automation_library.slurm.functions.slurm_ib_func import (
    get_ib_nodes,
    verify_ib_hardware_and_link,
    verify_doca_ofed_installed,
    verify_ib_ip_assigned,
    verify_ib_mtu,
    verify_ib_subnet_mask,
    verify_ib_ip_in_subnet,
    verify_ib_ping,
    verify_ucx_installed,
    verify_ucx_ib_only,
)
from automation_library.slurm.functions.slurm_ldap_func import (
    verify_ldapuser_blocked_on_slurm_nodes,
    verify_pam_from_login_node,
    verify_pam_from_login_compiler_node,
    verify_pam_from_control_node,
    verify_openmpi_job,
    verify_job_queuing,
    verify_ldap_sbatch_from_login_nodes,
    verify_ldap_multi_sbatch_from_login_node,
    verify_ldapuser_login_on_control_nodes,
    verify_ldapuser_login_on_login_nodes,
    verify_ldapuser_login_on_login_compiler_nodes,
    verify_invalid_ldap_username,
    verify_invalid_ldap_password,
    set_ldapuser_home_permissions,
    verify_gpu_hello_job,
    verify_gpu_mem_stress_job,
)

# =============================================================================
# CLUSTER VERIFICATION TESTS (TC1)
# =============================================================================

# =============================================================================
# TC1: All nodes from PXE mapping are joined to Slurm cluster
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_all_pxe_nodes_in_slurm_cluster(host):
    """Test that all nodes in PXE mapping are joined to the Slurm cluster."""
    log = TestLogger("Verify all PXE mapping nodes are in Slurm cluster")
    log.check("Comparing PXE mapping nodes with Slurm cluster nodes")

    result = verify_all_pxe_nodes_in_slurm_cluster(host)

    log.check(f"  PXE nodes count: {len(result.get('pxe_nodes', []))}")
    log.check(f"  Slurm nodes count: {len(result.get('slurm_nodes', []))}")

    if result.get("missing_nodes"):
        log.check(f"  Missing nodes in Slurm cluster: {result['missing_nodes']}")
    if result.get("extra_nodes"):
        log.check(f"  Extra nodes in Slurm cluster (not in PXE): {result['extra_nodes']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# SERVICE TESTS (TC2-TC9)
# =============================================================================

# =============================================================================
# TC2: slurmctld service active on slurm control node(s)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_slurmctld_active_on_control_nodes(host):
    """Test that slurmctld service is active on all slurm control nodes."""
    log = TestLogger("Verify slurmctld is active on slurm control nodes")
    log.check("Checking slurmctld service on slurm control nodes")

    result = verify_slurmctld_active(host)

    # Log per-node details
    for node in result.get("details", []):
        status = "active" if node["active"] else "NOT active"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): slurmctld {status} [{node['output']}]")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC3: slurmd service active on slurm nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_slurmd_active_on_slurm_nodes(host):
    """Test that slurmd service is active on all slurm compute nodes."""
    log = TestLogger("Verify slurmd is active on slurm compute nodes")
    log.check("Checking slurmd service on slurm nodes")

    result = verify_slurmd_active(host)

    # Log per-node details
    for node in result.get("details", []):
        status = "active" if node["active"] else "NOT active"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): slurmd {status} [{node['output']}]")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC4: slurmd service active on login nodes (separate)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_slurmd_active_on_login_nodes_only(host):
    """Test that slurmd service is active on login nodes."""
    log = TestLogger("Verify slurmd is active on login nodes")
    log.check("Checking slurmd service on login nodes")

    result = verify_slurmd_on_login_nodes_only(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for node in result.get("details", []):
        status = "active" if node["active"] else "NOT active"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): slurmd {status} [{node['output']}]")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC4: slurmd service active on login compiler nodes (separate)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_slurmd_active_on_login_compiler_nodes_only(host):
    """Test that slurmd service is active on login compiler nodes."""
    log = TestLogger("Verify slurmd is active on login compiler nodes")
    log.check("Checking slurmd service on login compiler nodes")

    result = verify_slurmd_on_login_compiler_nodes_only(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for node in result.get("details", []):
        status = "active" if node["active"] else "NOT active"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): slurmd {status} [{node['output']}]")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC5: munge service active on slurm control nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_munge_active_on_control_nodes(host):
    """Test that munge service is active on slurm control nodes."""
    log = TestLogger("Verify munge is active on slurm control nodes")
    log.check("Checking munge service on slurm control nodes")

    result = verify_munge_on_control_nodes(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for node in result.get("details", []):
        status = "active" if node["active"] else "NOT active"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): munge {status} [{node['output']}]")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC6: munge service active on slurm compute nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_munge_active_on_slurm_nodes(host):
    """Test that munge service is active on slurm compute nodes."""
    log = TestLogger("Verify munge is active on slurm compute nodes")
    log.check("Checking munge service on slurm compute nodes")

    result = verify_munge_on_slurm_nodes(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for node in result.get("details", []):
        status = "active" if node["active"] else "NOT active"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): munge {status} [{node['output']}]")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC7: munge service active on login nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_munge_active_on_login_nodes(host):
    """Test that munge service is active on login nodes."""
    log = TestLogger("Verify munge is active on login nodes")
    log.check("Checking munge service on login nodes")

    result = verify_munge_on_login_nodes(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for node in result.get("details", []):
        status = "active" if node["active"] else "NOT active"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): munge {status} [{node['output']}]")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC8: munge service active on login compiler nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_munge_active_on_login_compiler_nodes(host):
    """Test that munge service is active on login compiler nodes."""
    log = TestLogger("Verify munge is active on login compiler nodes")
    log.check("Checking munge service on login compiler nodes")

    result = verify_munge_on_login_compiler_nodes(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for node in result.get("details", []):
        status = "active" if node["active"] else "NOT active"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): munge {status} [{node['output']}]")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# NODE IDLE STATE TESTS (TC9-TC10)
# =============================================================================

# =============================================================================
# TC9: All slurm compute nodes in idle state (sinfo)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_all_slurm_nodes_idle(host):
    """Test that all slurm compute nodes are in idle state using sinfo command."""
    log = TestLogger("Verify all slurm compute nodes are in idle state")
    log.check("Running sinfo on slurm control node")

    result = verify_slurm_nodes_idle(host)

    for ns in result.get("node_states", []):
        idle_str = "idle" if ns["idle"] else "NOT idle"
        log.check(f"  {ns['node']}: {ns['state']} ({idle_str})")

    if result.get("sinfo_output"):
        log.check(f"sinfo output:\n{result['sinfo_output']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC10: All login and login compiler nodes in idle state (scontrol)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_login_nodes_idle(host):
    """Test that all login and login compiler nodes are in idle state."""
    log = TestLogger("Verify all login and login compiler nodes are in idle state")
    log.check("Checking node state via scontrol for each login/login_compiler node")

    result = verify_login_nodes_idle(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for ns in result.get("node_states", []):
        idle_str = "idle" if ns["idle"] else "NOT idle"
        log.check(f"  {ns['node']}: {ns['state']} ({idle_str})")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# PASSWORDLESS SSH TESTS (TC11-TC22)
# =============================================================================

_SSH_NODE_TYPES = [
    "slurm_control_node",
    "slurm_node",
    "login_node",
    "login_compiler_node",
]


def _run_ssh_test(host, log, src_type, dst_type):
    """Helper to run and log passwordless SSH test."""
    result = verify_passwordless_ssh(host, src_type, dst_type)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for pr in result.get("pair_results", []):
        status = "OK" if pr["success"] else "FAILED"
        log.check(f"  {pr['src']} -> {pr['dst']}: {status}")
        if pr.get("error"):
            log.check(f"    Error: {pr['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


@pytest.mark.sanity
@pytest.mark.order(12)
def test_ssh_control_to_slurm(host):
    """TC11: Test passwordless SSH from slurm control nodes to slurm compute nodes."""
    log = TestLogger("Verify passwordless SSH: control -> slurm nodes")
    log.check("Testing SSH from control nodes to slurm nodes")
    _run_ssh_test(host, log, "slurm_control_node", "slurm_node")


@pytest.mark.sanity
@pytest.mark.order(13)
def test_ssh_control_to_login(host):
    """TC12: Test passwordless SSH from slurm control nodes to login nodes."""
    log = TestLogger("Verify passwordless SSH: control -> login nodes")
    log.check("Testing SSH from control nodes to login nodes")
    _run_ssh_test(host, log, "slurm_control_node", "login_node")


@pytest.mark.sanity
@pytest.mark.order(14)
def test_ssh_control_to_login_compiler(host):
    """TC13: Test passwordless SSH from slurm control nodes to login compiler nodes."""
    log = TestLogger("Verify passwordless SSH: control -> login compiler nodes")
    log.check("Testing SSH from control nodes to login compiler nodes")
    _run_ssh_test(host, log, "slurm_control_node", "login_compiler_node")


@pytest.mark.sanity
@pytest.mark.order(15)
def test_ssh_slurm_to_control(host):
    """TC14: Test passwordless SSH from slurm compute nodes to slurm control nodes."""
    log = TestLogger("Verify passwordless SSH: slurm nodes -> control")
    log.check("Testing SSH from slurm nodes to control nodes")
    _run_ssh_test(host, log, "slurm_node", "slurm_control_node")


@pytest.mark.sanity
@pytest.mark.order(16)
def test_ssh_slurm_to_login(host):
    """TC15: Test passwordless SSH from slurm compute nodes to login nodes."""
    log = TestLogger("Verify passwordless SSH: slurm nodes -> login nodes")
    log.check("Testing SSH from slurm nodes to login nodes")
    _run_ssh_test(host, log, "slurm_node", "login_node")


@pytest.mark.sanity
@pytest.mark.order(17)
def test_ssh_slurm_to_login_compiler(host):
    """TC16: Test passwordless SSH from slurm compute nodes to login compiler nodes."""
    log = TestLogger("Verify passwordless SSH: slurm nodes -> login compiler nodes")
    log.check("Testing SSH from slurm nodes to login compiler nodes")
    _run_ssh_test(host, log, "slurm_node", "login_compiler_node")


@pytest.mark.sanity
@pytest.mark.order(18)
def test_ssh_login_to_control(host):
    """TC17: Test passwordless SSH from login nodes to slurm control nodes."""
    log = TestLogger("Verify passwordless SSH: login nodes -> control")
    log.check("Testing SSH from login nodes to control nodes")
    _run_ssh_test(host, log, "login_node", "slurm_control_node")


@pytest.mark.sanity
@pytest.mark.order(19)
def test_ssh_login_to_slurm(host):
    """TC18: Test passwordless SSH from login nodes to slurm compute nodes."""
    log = TestLogger("Verify passwordless SSH: login nodes -> slurm nodes")
    log.check("Testing SSH from login nodes to slurm nodes")
    _run_ssh_test(host, log, "login_node", "slurm_node")


@pytest.mark.sanity
@pytest.mark.order(20)
def test_ssh_login_to_login_compiler(host):
    """TC19: Test passwordless SSH from login nodes to login compiler nodes."""
    log = TestLogger("Verify passwordless SSH: login nodes -> login compiler nodes")
    log.check("Testing SSH from login nodes to login compiler nodes")
    _run_ssh_test(host, log, "login_node", "login_compiler_node")


@pytest.mark.sanity
@pytest.mark.order(21)
def test_ssh_login_compiler_to_control(host):
    """TC20: Test passwordless SSH from login compiler nodes to slurm control nodes."""
    log = TestLogger("Verify passwordless SSH: login compiler -> control")
    log.check("Testing SSH from login compiler nodes to control nodes")
    _run_ssh_test(host, log, "login_compiler_node", "slurm_control_node")


@pytest.mark.sanity
@pytest.mark.order(22)
def test_ssh_login_compiler_to_slurm(host):
    """TC21: Test passwordless SSH from login compiler nodes to slurm compute nodes."""
    log = TestLogger("Verify passwordless SSH: login compiler -> slurm nodes")
    log.check("Testing SSH from login compiler nodes to slurm nodes")
    _run_ssh_test(host, log, "login_compiler_node", "slurm_node")


@pytest.mark.sanity
@pytest.mark.order(23)
def test_ssh_login_compiler_to_login(host):
    """TC22: Test passwordless SSH from login compiler nodes to login nodes."""
    log = TestLogger("Verify passwordless SSH: login compiler -> login nodes")
    log.check("Testing SSH from login compiler nodes to login nodes")
    _run_ssh_test(host, log, "login_compiler_node", "login_node")


# =============================================================================
# BASIC JOB TESTS (TC23-TC24)
# =============================================================================

# =============================================================================
# TC23: srun job from control node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(24)
def test_srun_job(host):
    """TC23: Test submitting a basic srun job from the control node.

    Runs: srun -N <total_slurm_nodes> hostname
    """
    log = TestLogger("Verify srun job execution from slurm control node")
    log.check("Submitting srun job on all slurm nodes")

    result = verify_srun_job(host)

    if result.get("output"):
        log.check(f"srun output:\n{result['output']}")
    log.check(f"Number of slurm nodes: {result.get('num_nodes', 0)}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC24: sbatch job from control node verified via sacct
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(25)
def test_sbatch_job(host):
    """TC24: Test submitting a basic sbatch job from the control node as root.

    Submits an sbatch job and verifies completion using sacct.
    """
    log = TestLogger("Verify sbatch job execution from slurm control node")
    log.check("Submitting sbatch job and verifying via sacct")

    result = verify_sbatch_job(host)

    if result.get("job_id"):
        log.check(f"Job ID: {result['job_id']}")
    if result.get("job_state"):
        log.check(f"Job state: {result['job_state']}")
    if result.get("output"):
        log.check(f"Submit output: {result['output']}")
    if result.get("job_output"):
        log.check(f"Job output:\n{result['job_output']}")

    output_status = "VERIFIED" if result.get("output_verified") else "FAILED"
    log.check(f"Output verification: {output_status}")

    if result["success"]:
        log.passed(result["message"])
        job_output = result.get("job_output", "")
        if job_output:
            assert "completed" in job_output.lower() or "Job" in job_output, \
                f"Job output does not contain expected completion message: {job_output}"
            log.check("Job output verification passed")
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# ROOT JOB SUBMISSION TESTS (TC25-TC30)
# =============================================================================

# =============================================================================
# TC25: Root single sbatch job from login node(s)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(26)
def test_root_sbatch_from_login_nodes(host):
    """TC25: Test submitting a single sbatch job as root from each login/login_compiler node."""
    log = TestLogger("Verify root sbatch job from login node(s)")
    log.check("Submitting single sbatch job as root from each login node")

    result = verify_root_sbatch_from_login_node(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for nr in result.get("node_results", []):
        status = "COMPLETED" if nr["success"] else "FAILED"
        log.check(f"  {nr['node']}: {status} (JobID: {nr.get('job_id', '')}, State: {nr.get('job_state', '')})")
        if nr.get("error"):
            log.check(f"    Error: {nr['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC26: Root multiple sbatch jobs from login node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(27)
def test_root_multi_sbatch_from_login_node(host):
    """TC26: Test submitting multiple sbatch jobs as root from a login node."""
    log = TestLogger("Verify root multiple sbatch jobs from login node")
    log.check("Submitting multiple sbatch jobs as root from login node")

    result = verify_root_multi_sbatch_from_login_node(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result.get("submit_node"):
        log.check(f"Submit node: {result['submit_node']}")
    for jr in result.get("job_results", []):
        status = "COMPLETED" if jr["success"] else "FAILED"
        log.check(f"  Job {jr['index']}: {status} (JobID: {jr.get('job_id', '')}, State: {jr.get('job_state', '')})")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC27: Root sbatch from multiple login nodes (>1 required)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(28)
def test_root_sbatch_from_multiple_login_nodes(host):
    """TC27: Test submitting sbatch jobs from multiple login nodes.

    Skips if only 1 or 0 login nodes found.
    """
    log = TestLogger("Verify root sbatch from multiple login nodes")
    log.check("Submitting sbatch jobs from each login node (>1 required)")

    result = verify_root_sbatch_from_multiple_login_nodes(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for nr in result.get("node_results", []):
        status = "COMPLETED" if nr["success"] else "FAILED"
        log.check(f"  {nr['node']}: {status} (JobID: {nr.get('job_id', '')}, State: {nr.get('job_state', '')})")
        if nr.get("error"):
            log.check(f"    Error: {nr['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC28: Drain/undrain queuing - PENDING while drained, RUNNING after undrain
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(29)
def test_drain_undrain_queuing(host):
    """TC28: Test job queuing when compute nodes are drained.

    Drains all slurm nodes, submits a job, verifies PENDING with reason,
    undrains nodes, verifies job transitions to COMPLETED.
    """
    log = TestLogger("Verify drain/undrain job queuing")
    log.check("Draining nodes, submitting job, verifying PENDING, undraining")

    result = verify_drain_undrain_queuing(host)

    for step in result.get("steps", []):
        step_name = step.get("step", "")
        step_ok = "OK" if step.get("success") else "FAILED"
        log.check(f"  Step: {step_name} - {step_ok}")
        if step.get("sinfo_output"):
            log.check(f"    sinfo: {step['sinfo_output']}")
        if step.get("state_reason"):
            log.check(f"    State/Reason: {step['state_reason']}")
        if step.get("final_state"):
            log.check(f"    Final state: {step['final_state']}")

    if result.get("job_id"):
        log.check(f"Job ID: {result['job_id']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC29: Insufficient resources - job PENDING or rejected
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(30)
def test_insufficient_resources(host):
    """TC29: Test submitting a job requesting more resources than available.

    Verifies that the job enters PENDING with a resource-related reason
    or is rejected outright by Slurm.
    """
    log = TestLogger("Verify insufficient resources job handling")
    log.check("Submitting job with excessive CPU request")

    result = verify_insufficient_resources(host)

    if result.get("job_id"):
        log.check(f"Job ID: {result['job_id']}")
    if result.get("job_state"):
        log.check(f"Job state: {result['job_state']}")
    if result.get("reason"):
        log.check(f"Reason: {result['reason']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC30: Job queuing - first RUNNING, second PENDING on same node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(31)
def test_job_queuing(host):
    """TC30: Test Slurm job queuing behavior.

    Submits a sleep job, waits for RUNNING, then submits a second job
    on the same node and verifies it goes to PENDING state.
    """
    log = TestLogger("Verify Slurm job queuing")
    log.check("Submitting first sleep job, then second on same node")

    result = verify_job_queuing(host)

    if result.get("job1_id"):
        log.check(f"Job 1 ID: {result['job1_id']} - State: {result.get('job1_state', '')}")
    if result.get("job1_squeue"):
        log.check(f"Job 1 squeue: {result['job1_squeue']}")
    if result.get("allocated_node"):
        log.check(f"Allocated node: {result['allocated_node']}")
    if result.get("job2_id"):
        log.check(f"Job 2 ID: {result['job2_id']} - State: {result.get('job2_state', '')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# LDAP USER TESTS (TC31-TC42)
# Prerequisites: set_ldapuser_home_permissions() is called as a prereq before
# the first LDAP test to ensure /home/<ldapuser> is writable on all nodes.
# =============================================================================

_LDAP_STATE = {"prereq_done": False}


def _skip_if_no_openldap(host):
    """Skip LDAP tests if openldap is not enabled in software_config.json."""
    if not is_software_enabled(host, "openldap"):
        pytest.skip("OpenLDAP is not enabled in software_config.json, skipping LDAP tests")


def _ensure_ldap_prereq(host):
    """Ensure LDAP home directory permissions are set before any LDAP test.

    This is a non-test prereq function. It runs set_ldapuser_home_permissions()
    once per test session to ensure /home/<ldapuser> has write+execute permissions
    on all cluster nodes before LDAP job submission tests begin.
    """
    if not _LDAP_STATE["prereq_done"]:
        set_ldapuser_home_permissions(host)
        _LDAP_STATE["prereq_done"] = True


# =============================================================================
# TC31: ldapuser login on slurm control nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(32)
def test_ldapuser_login_on_control_nodes(host):
    """TC31: Test that all LDAP users can SSH login to slurm control nodes."""
    _skip_if_no_openldap(host)
    _ensure_ldap_prereq(host)
    log = TestLogger("Verify ldapuser login on slurm control nodes")
    log.check("Testing ldapuser SSH login on slurm control nodes")

    result = verify_ldapuser_login_on_control_nodes(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result.get("ldap_users"):
        log.check(f"LDAP users: {', '.join(result['ldap_users'])}")

    for node in result.get("details", []):
        status = "OK" if node["login_success"] else "FAILED"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): login {status}")
        for ur in node.get("user_results", []):
            ur_status = "OK" if ur["login_success"] else "FAILED"
            log.check(f"    {ur['ldap_user']}: {ur_status}")
            if ur.get("error"):
                log.check(f"      Error: {ur['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC32: ldapuser login on login nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(33)
def test_ldapuser_login_on_login_nodes(host):
    """TC32: Test that all LDAP users can SSH login to login nodes."""
    _skip_if_no_openldap(host)
    log = TestLogger("Verify ldapuser login on login nodes")
    log.check("Testing ldapuser SSH login on login nodes")

    result = verify_ldapuser_login_on_login_nodes(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result.get("ldap_users"):
        log.check(f"LDAP users: {', '.join(result['ldap_users'])}")

    for node in result.get("details", []):
        status = "OK" if node["login_success"] else "FAILED"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): login {status}")
        for ur in node.get("user_results", []):
            ur_status = "OK" if ur["login_success"] else "FAILED"
            log.check(f"    {ur['ldap_user']}: {ur_status}")
            if ur.get("error"):
                log.check(f"      Error: {ur['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC33: ldapuser login on login compiler nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(34)
def test_ldapuser_login_on_login_compiler_nodes(host):
    """TC33: Test that all LDAP users can SSH login to login compiler nodes."""
    _skip_if_no_openldap(host)
    log = TestLogger("Verify ldapuser login on login compiler nodes")
    log.check("Testing ldapuser SSH login on login compiler nodes")

    result = verify_ldapuser_login_on_login_compiler_nodes(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result.get("ldap_users"):
        log.check(f"LDAP users: {', '.join(result['ldap_users'])}")

    for node in result.get("details", []):
        status = "OK" if node["login_success"] else "FAILED"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): login {status}")
        for ur in node.get("user_results", []):
            ur_status = "OK" if ur["login_success"] else "FAILED"
            log.check(f"    {ur['ldap_user']}: {ur_status}")
            if ur.get("error"):
                log.check(f"      Error: {ur['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC34: ldapuser login blocked on slurm nodes (no running jobs)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(35)
def test_ldapuser_blocked_on_slurm_nodes(host):
    """TC34: Test that all LDAP users login is blocked on slurm nodes when no jobs are running."""
    _skip_if_no_openldap(host)
    log = TestLogger("Verify ldapuser login blocked on idle slurm nodes")
    log.check("Testing ldapuser SSH login is blocked on slurm nodes")

    result = verify_ldapuser_blocked_on_slurm_nodes(host)

    if result.get("ldap_users"):
        log.check(f"LDAP users: {', '.join(result['ldap_users'])}")

    for node in result.get("details", []):
        status = "BLOCKED" if node["login_blocked"] else "NOT BLOCKED"
        log.check(f"  {node['hostname']} ({node.get('admin_ip', '')}): {status}")
        for ur in node.get("user_results", []):
            ur_status = "BLOCKED" if ur["login_blocked"] else "NOT BLOCKED"
            log.check(f"    {ur['ldap_user']}: {ur_status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC35: Invalid LDAP username denied login
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(36)
def test_invalid_ldap_username(host):
    """TC35: Test that an invalid (random) LDAP username is denied login on all nodes."""
    _skip_if_no_openldap(host)
    log = TestLogger("Verify invalid LDAP username denied login")
    log.check("Testing random invalid username on login/control nodes")

    result = verify_invalid_ldap_username(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result.get("invalid_user"):
        log.check(f"Invalid username tested: {result['invalid_user']}")
    for node in result.get("details", []):
        status = "DENIED" if node["login_denied"] else "ALLOWED (unexpected)"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): {status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC36: Invalid LDAP password denied login
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(37)
def test_invalid_ldap_password(host):
    """TC36: Test that all valid LDAP usernames with invalid (random) passwords are denied login."""
    _skip_if_no_openldap(host)
    log = TestLogger("Verify invalid LDAP password denied login")
    log.check("Testing valid usernames with random invalid passwords")

    result = verify_invalid_ldap_password(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result.get("ldap_users"):
        log.check(f"LDAP users tested: {', '.join(result['ldap_users'])}")
    for node in result.get("details", []):
        status = "DENIED" if node["login_denied"] else "ALLOWED (unexpected)"
        log.check(f"  {node['hostname']} ({node['admin_ip']}): {status}")
        for ur in node.get("user_results", []):
            ur_status = "DENIED" if ur["login_denied"] else "ALLOWED (unexpected)"
            log.check(f"    {ur['ldap_user']}: {ur_status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC37: LDAP user single sbatch job from login node(s)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(38)
def test_ldap_sbatch_from_login_nodes(host):
    """TC37: Test submitting a single sbatch job as ldapuser from each login/login_compiler node."""
    _skip_if_no_openldap(host)
    log = TestLogger("Verify LDAP user sbatch job from login node(s)")
    log.check("Submitting single sbatch job as ldapuser from each login node")

    result = verify_ldap_sbatch_from_login_nodes(host)

    for nr in result.get("node_results", []):
        status = "COMPLETED" if nr["success"] else "FAILED"
        log.check(f"  {nr['node']}: {status} (JobID: {nr.get('job_id', '')}, State: {nr.get('job_state', '')})")
        if nr.get("error"):
            log.check(f"    Error: {nr['error']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC38: LDAP user multiple sbatch jobs from login node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(39)
def test_ldap_multi_sbatch_from_login_node(host):
    """TC38: Test submitting multiple sbatch jobs as ldapuser from a login node."""
    _skip_if_no_openldap(host)
    log = TestLogger("Verify LDAP user multiple sbatch jobs from login node")
    log.check("Submitting multiple sbatch jobs as ldapuser from login node")

    result = verify_ldap_multi_sbatch_from_login_node(host)

    if result.get("submit_node"):
        log.check(f"Submit node: {result['submit_node']}")
    for jr in result.get("job_results", []):
        status = "COMPLETED" if jr["success"] else "FAILED"
        log.check(f"  Job {jr['index']}: {status} (JobID: {jr.get('job_id', '')}, State: {jr.get('job_state', '')})")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC39: PAM support - ldapuser job from login node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(40)
def test_pam_support_from_login_node(host):
    """TC39: Test PAM support: submit sleep job as ldapuser from login node.

    Verifies that ldapuser can login to slurm nodes during a running job
    and is blocked after the job completes.
    Skips if no login nodes are present in the cluster.
    """
    _skip_if_no_openldap(host)
    log = TestLogger("Verify PAM support from login node")
    log.check("Submitting sleep job as ldapuser from login node")

    result = verify_pam_from_login_node(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for step in result.get("steps", []):
        step_name = step.get("step", "")
        step_ok = "OK" if step.get("success") else "FAILED"
        log.check(f"  Step: {step_name} - {step_ok}")
        for detail in step.get("details", []):
            log.check(f"    {detail}")

    if result.get("job_id"):
        log.check(f"Job ID: {result['job_id']}")
    if result.get("submit_node"):
        log.check(f"Submit node: {result['submit_node']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC40: PAM support - ldapuser job from control node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(41)
def test_pam_support_from_control_node(host):
    """TC40: Test PAM support: submit sleep job as ldapuser from slurm control node.

    Verifies that ldapuser can login to slurm nodes during a running job
    and is blocked after the job completes.
    """
    _skip_if_no_openldap(host)
    log = TestLogger("Verify PAM support from slurm control node")
    log.check("Submitting sleep job as ldapuser from control node")

    result = verify_pam_from_control_node(host)

    for step in result.get("steps", []):
        step_name = step.get("step", "")
        step_ok = "OK" if step.get("success") else "FAILED"
        log.check(f"  Step: {step_name} - {step_ok}")
        for detail in step.get("details", []):
            log.check(f"    {detail}")

    if result.get("job_id"):
        log.check(f"Job ID: {result['job_id']}")
    if result.get("submit_node"):
        log.check(f"Submit node: {result['submit_node']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC41: PAM support - ldapuser job from login_compiler node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.ldap
@pytest.mark.order(42)
def test_pam_support_from_login_compiler_node(host):
    """TC41: Test PAM support: submit sleep job as ldapuser from login_compiler node.

    Verifies that ldapuser can login to slurm nodes during a running job
    and is blocked after the job completes.
    Skips if no login compiler nodes are present in the cluster.
    """
    _skip_if_no_openldap(host)
    log = TestLogger("Verify PAM support from login compiler node")
    log.check("Submitting sleep job as ldapuser from login compiler node")

    result = verify_pam_from_login_compiler_node(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for step in result.get("steps", []):
        step_name = step.get("step", "")
        step_ok = "OK" if step.get("success") else "FAILED"
        log.check(f"  Step: {step_name} - {step_ok}")
        for detail in step.get("details", []):
            log.check(f"    {detail}")

    if result.get("job_id"):
        log.check(f"Job ID: {result['job_id']}")
    if result.get("submit_node"):
        log.check(f"Submit node: {result['submit_node']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC42: OpenMPI job from ldapuser on login_compiler node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(43)
def test_openmpi_job(host):
    """TC42: Test submitting an OpenMPI compile+run job as ldapuser from a login_compiler node.

    Submits a job that compiles and runs a simple MPI C program,
    then verifies the expected output (Compilation successful, Hello World,
    MPI job completed successfully).
    """
    _skip_if_no_openldap(host)
    _ensure_ldap_prereq(host)
    log = TestLogger("Verify OpenMPI job from ldapuser on login_compiler node")
    log.check("Submitting MPI compile+run job as ldapuser")

    result = verify_openmpi_job(host)

    if result.get("submit_node"):
        log.check(f"Submit node: {result['submit_node']}")
    if result.get("job_id"):
        log.check(f"Job ID: {result['job_id']}")
    if result.get("job_state"):
        log.check(f"Job state: {result['job_state']}")
    if result.get("job_output"):
        log.check(f"Job output:\n{result['job_output']}")

    output_status = "VERIFIED" if result.get("output_verified") else "FAILED"
    log.check(f"Output verification: {output_status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC44: GPU Hello World job from ldapuser on login_compiler node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(44)
def test_gpu_hello_job(host):
    """TC44: Test submitting a GPU hello world job as ldapuser from login_compiler node.

    Submits a job that compiles and runs a simple CUDA program to detect GPUs
    and execute a basic kernel, then verifies the expected output.
    Skips if no GPU nodes are found in the cluster.
    """
    _skip_if_no_openldap(host)
    _ensure_ldap_prereq(host)
    log = TestLogger("Verify GPU hello world job from ldapuser on login_compiler node")
    log.check("Submitting GPU hello world job as ldapuser")

    result = verify_gpu_hello_job(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result.get("submit_node"):
        log.check(f"Submit node: {result['submit_node']}")
    if result.get("job_id"):
        log.check(f"Job ID: {result['job_id']}")
    if result.get("job_state"):
        log.check(f"Job state: {result['job_state']}")
    if result.get("job_output"):
        log.check(f"Job output:\n{result['job_output']}")

    output_status = "VERIFIED" if result.get("output_verified") else "FAILED"
    log.check(f"Output verification: {output_status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC45: GPU Memory Stress Test job from ldapuser on login_compiler node
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(45)
def test_gpu_mem_stress_job(host):
    """TC45: Test submitting a GPU memory stress test job as ldapuser from login_compiler node.

    Submits a job that allocates GPU memory and runs sustained compute workload
    across multiple GPU nodes, then verifies the expected output.
    Skips if no GPU nodes are found in the cluster.
    """
    _skip_if_no_openldap(host)
    _ensure_ldap_prereq(host)
    log = TestLogger("Verify GPU memory stress test job from ldapuser on login_compiler node")
    log.check("Submitting GPU memory stress test job as ldapuser")

    result = verify_gpu_mem_stress_job(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result.get("submit_node"):
        log.check(f"Submit node: {result['submit_node']}")
    if result.get("job_id"):
        log.check(f"Job ID: {result['job_id']}")
    if result.get("job_state"):
        log.check(f"Job state: {result['job_state']}")
    if result.get("job_output"):
        log.check(f"Job output:\n{result['job_output']}")

    output_status = "VERIFIED" if result.get("output_verified") else "FAILED"
    log.check(f"Output verification: {output_status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# INFINIBAND TESTS (TC46 – TC54)
# Pre-check: IB_NIC_NAME and IB_IP must be populated for at least one
# Slurm cluster node in the PXE mapping file.
# =============================================================================

def _skip_if_no_ib(host):
    """Skip the current test if no IB-configured nodes are found."""
    if not get_ib_nodes(host):
        pytest.skip("No IB-configured nodes (IB_NIC_NAME + IB_IP) found in PXE mapping")


def _log_ib_per_node(log, per_node: list):
    """Log per-node IB check results."""
    for n in per_node:
        hostname = n.get("hostname", n.get("node_ip", "unknown"))
        for key, val in n.get("checks", {}).items():
            if isinstance(val, dict):
                log.check(f"  [{hostname}] {key}: rc={val.get('rc','?')} output={str(val.get('output',''))[:120]}")
            else:
                log.check(f"  [{hostname}] {key}: {val}")
        for field in ("status", "mtu_status", "interface"):
            if field in n:
                log.check(f"  [{hostname}] {field}: {n[field]}")
        log.check(f"  [{hostname}] => {'PASS' if n.get('success') else 'FAIL'}")


# =============================================================================
# TC46 – IB Hardware & Link Verification
# =============================================================================

@pytest.mark.sanity
@pytest.mark.sanityib
@pytest.mark.order(46)
def test_ib_hardware_and_link(host):
    """TC46: Verify IB hardware and link state on all IB-configured nodes.

    Runs ibstat, ibstatus, ibv_devinfo, ibv_devices and verifies port is Active.
    Skips if no IB-configured nodes found in PXE mapping.
    """
    _skip_if_no_ib(host)
    log = TestLogger("TC46: IB Hardware & Link Verification")
    result = verify_ib_hardware_and_link(host)
    if result.get("skipped"):
        pytest.skip(result["message"])
    _log_ib_per_node(log, result.get("per_node", []))
    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])
    assert result["success"], result["message"]


# =============================================================================
# TC47 – DOCA-OFED Installation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.sanityib
@pytest.mark.order(47)
def test_doca_ofed_installed(host):
    """TC47: Verify DOCA-OFED (or MLNX_OFED) is installed on IB nodes.

    Checks ofed_info -s version, OFED RPMs, and ib_uverbs kernel module.
    Skips if no IB-configured nodes found in PXE mapping.
    """
    _skip_if_no_ib(host)
    log = TestLogger("TC47: DOCA-OFED Installation")
    result = verify_doca_ofed_installed(host)
    if result.get("skipped"):
        pytest.skip(result["message"])
    _log_ib_per_node(log, result.get("per_node", []))
    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])
    assert result["success"], result["message"]


# =============================================================================
# TC48 – IB IP Assignment
# =============================================================================

@pytest.mark.sanity
@pytest.mark.sanityib
@pytest.mark.order(48)
def test_ib_ip_assigned(host):
    """TC48: Verify the IB IP from PXE mapping is assigned to the IB
    interface on each IB-configured node.
    """
    _skip_if_no_ib(host)
    log = TestLogger("TC48: IB IP Assignment")
    result = verify_ib_ip_assigned(host)
    if result.get("skipped"):
        pytest.skip(result["message"])
    for n in result.get("per_node", []):
        log.check(f"  [{n.get('hostname')}] IB IP: {n.get('ib_ip')} - {n.get('status')}")
    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])
    assert result["success"], result["message"]


# =============================================================================
# TC49 – IB Interface MTU
# =============================================================================

@pytest.mark.sanity
@pytest.mark.sanityib
@pytest.mark.order(49)
def test_ib_mtu(host):
    """TC49: Verify IB interface MTU >= 2044 (IPoIB standard).

    Checks 'ip link show <ib_iface>' and validates MTU value.
    """
    _skip_if_no_ib(host)
    log = TestLogger("TC49: IB Interface MTU Verification")
    result = verify_ib_mtu(host)
    if result.get("skipped"):
        pytest.skip(result["message"])
    _log_ib_per_node(log, result.get("per_node", []))
    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])
    assert result["success"], result["message"]


# =============================================================================
# TC50 – IB Subnet Mask from network_spec.yml
# =============================================================================

@pytest.mark.sanity
@pytest.mark.sanityib
@pytest.mark.order(50)
def test_ib_subnet_mask(host):
    """TC50: Verify the IB interface subnet mask matches ib_network.netmask_bits
    from network_spec.yml on every IB-configured node.
    """
    _skip_if_no_ib(host)
    log = TestLogger("TC50: IB Subnet Mask vs network_spec.yml")
    result = verify_ib_subnet_mask(host)
    if result.get("skipped"):
        pytest.skip(result["message"])
    if result.get("subnet_info"):
        si = result["subnet_info"]
        log.check(f"Expected: {si['subnet']}/{si['netmask_bits']} (from network_spec.yml)")
    for n in result.get("per_node", []):
        log.check(f"  [{n.get('hostname')}] {n.get('status')}")
    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])
    assert result["success"], result["message"]


# =============================================================================
# TC51 – IB IP in Correct Subnet
# =============================================================================

@pytest.mark.sanity
@pytest.mark.sanityib
@pytest.mark.order(51)
def test_ib_ip_in_subnet(host):
    """TC51: Verify each node's IB_IP (from PXE mapping) falls within the
    ib_network subnet defined in network_spec.yml.
    """
    _skip_if_no_ib(host)
    log = TestLogger("TC51: IB IP Subnet Membership")
    result = verify_ib_ip_in_subnet(host)
    if result.get("skipped"):
        pytest.skip(result["message"])
    for n in result.get("per_node", []):
        log.check(f"  [{n.get('hostname')}] {n.get('status')}")
    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])
    assert result["success"], result["message"]


# =============================================================================
# TC52 – IB Ping
# =============================================================================

@pytest.mark.sanity
@pytest.mark.sanityib
@pytest.mark.order(52)
def test_ib_ping(host):
    """TC52: Verify IPoIB connectivity by pinging each node's IB IP from
    every other IB-configured node.  Requires >= 2 IB nodes.
    """
    _skip_if_no_ib(host)
    log = TestLogger("TC52: IB Ping Test")
    result = verify_ib_ping(host)
    if result.get("skipped"):
        pytest.skip(result["message"])
    for r in result.get("per_node", []):
        status = "PASS" if r["success"] else "FAIL"
        log.check(f"  {r.get('src')} -> {r.get('dst')} ({r.get('dst_ib_ip')}): {status}")
        if not r["success"]:
            log.check(f"    {r.get('output', '')[:200]}")
    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])
    assert result["success"], result["message"]


# =============================================================================
# TC56 – UCX Installation Check (login_compiler nodes)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.sanityib
@pytest.mark.order(53)
def test_ucx_installed_on_login_compiler(host):
    """TC56: Verify UCX is installed and functional on login_compiler/login nodes.

    Checks login_compiler nodes first; falls back to login nodes if none exist.
    Runs 'ucx_info -v' (version check) and 'ucx_info -d' (transport listing).
    Does NOT require IB hardware — pure software presence check.

    Skip conditions:
      - omnia_core container not running  (infrastructure issue, shown in skip msg)
      - No login_compiler or login nodes in PXE mapping (expected in minimal clusters)
    """
    log = TestLogger("TC56: UCX Installation Check (login_compiler/login nodes)")
    result = verify_ucx_installed(host)
    if result.get("skipped"):
        pytest.skip(result["message"])
    for n in result.get("per_node", []):
        status = "PASS" if n["success"] else "FAIL"
        node_label = f"{n['hostname']} [{n.get('node_type', '?')}]"
        log.check(f"  {node_label}: {status}")
        if n["success"]:
            log.check(f"    version   : {n.get('ucx_version', 'N/A')}")
            if n.get("transports"):
                log.check(f"    transports: {', '.join(n['transports'])}")
        else:
            log.check(f"    ERROR: {n.get('error', '')}")
    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])
    assert result["success"], result["message"]


# =============================================================================
# TC55 – UCX IB-Only Transport Verification
# =============================================================================

@pytest.mark.sanity
@pytest.mark.sanityib
@pytest.mark.order(54)
def test_ucx_ib_only_transport(host):
    """TC55: Three-phase UCX IB-only transport verification.

    Phase 1 – DOCA-OFED:
        Verify DOCA-OFED / MLNX-OFED is installed on all IB-configured nodes.
        (ofed_info -s, OFED RPMs, ib_uverbs kernel module)

    Phase 2 – UCX Installation:
        Verify UCX (ucx_info) is installed on login_compiler / login nodes.
        Lists available transports.

    Phase 3 – UCX IB Job:
        Submit MPI ping-pong job with UCX_TLS=ib,sm,self from login_compiler node.
        Verifies compile success, MPI ranks, IB transport selection, hardware
        counter increase, and large-message RDMA bandwidth >= 5 GB/s.

    Each phase must pass before the next is attempted.
    Skips if fewer than 2 IB-configured slurm compute nodes exist in PXE mapping.
    """
    _skip_if_no_ib(host)
    log = TestLogger("TC55: UCX IB-Only Transport Verification")

    # ------------------------------------------------------------------
    # Phase 1: DOCA-OFED installed on IB nodes
    # ------------------------------------------------------------------
    log.check("=" * 60)
    log.check("Phase 1: DOCA-OFED Installation Check")
    log.check("=" * 60)
    doca_result = verify_doca_ofed_installed(host)
    if doca_result.get("skipped"):
        pytest.skip(doca_result["message"])
    for n in doca_result.get("per_node", []):
        status = "PASS" if n["success"] else "FAIL"
        log.check(f"  {n['hostname']}: DOCA-OFED [{status}]")
        log.check(f"    ofed_version : {n['checks'].get('ofed_version', 'N/A')}")
        log.check(f"    rpms         : {n['checks'].get('rpms', 'N/A')[:80]}")
        log.check(f"    ib_uverbs    : {n['checks'].get('ib_uverbs_module', 'N/A')}")
    if doca_result["success"]:
        log.check("  Phase 1 PASSED: DOCA-OFED confirmed on all IB nodes")
    else:
        log.failed("Phase 1 FAILED: DOCA-OFED not installed — cannot proceed with UCX test")
        assert False, doca_result["message"]

    # ------------------------------------------------------------------
    # Phase 2: UCX installed on login_compiler / login nodes
    # ------------------------------------------------------------------
    log.check("=" * 60)
    log.check("Phase 2: UCX Installation Check")
    log.check("=" * 60)
    ucx_inst_result = verify_ucx_installed(host)
    if ucx_inst_result.get("skipped"):
        pytest.skip(ucx_inst_result["message"])
    for n in ucx_inst_result.get("per_node", []):
        status = "PASS" if n["success"] else "FAIL"
        node_label = f"{n['hostname']} [{n.get('node_type', '?')}]"
        log.check(f"  {node_label}: UCX [{status}]")
        if n["success"]:
            log.check(f"    version   : {n.get('ucx_version', 'N/A')}")
            if n.get("transports"):
                log.check(f"    transports: {', '.join(n['transports'])}")
        else:
            log.check(f"    ERROR: {n.get('error', '')}")
    if ucx_inst_result["success"]:
        log.check("  Phase 2 PASSED: UCX confirmed on all login-type nodes")
    else:
        log.failed("Phase 2 FAILED: UCX not installed — cannot proceed with UCX IB job")
        assert False, ucx_inst_result["message"]

    # ------------------------------------------------------------------
    # Phase 3: UCX IB-only transport job
    # ------------------------------------------------------------------
    log.check("=" * 60)
    log.check("Phase 3: UCX IB-Only Transport Job")
    log.check("=" * 60)
    result = verify_ucx_ib_only(host)
    if result.get("skipped"):
        pytest.skip(result["message"])

    log.check(f"  Submit node      : {result.get('submit_node', 'N/A')}")
    log.check(f"  Nodes under test : {result.get('nodes', 'unknown')}")
    log.check(f"  Job ID           : {result.get('job_id', 'N/A')}")

    for step in result.get("steps", []):
        step_name = step.get("step", "?")
        step_ok = step.get("success", False)
        status = "PASS" if step_ok else "FAIL"

        if step_name == "transfer_script":
            log.check(f"  [transfer_script] nodes={step.get('nodes')}"
                      f"  submit_node={step.get('submit_node', 'N/A')} -> {status}")
        elif step_name == "submit_job":
            log.check(f"  [submit_job] job_id={step.get('job_id')} -> {status}")
        elif step_name == "wait_complete":
            log.check(f"  [wait_complete] state={step.get('state')} -> {status}")
        elif step_name == "read_output":
            log.check(f"  [read_output] path={step.get('output_path')} -> {status}")
        elif step_name == "verify_output":
            log.check(f"  [compile]          {'PASS' if step.get('compile_ok') else 'FAIL'}")
            log.check(f"  [ranks_ran]        {'PASS' if step.get('ranks_ok') else 'FAIL'}")
            log.check(f"  [transport_ib]     {'PASS' if step.get('transport_ib') else 'FAIL'}"
                      f"  {step.get('transport_detail', '')}")
            log.check(f"  [tcp_not_used]     {'PASS' if not step.get('transport_tcp_found') else 'FAIL'}")
            log.check(f"  [counter_increase] {'PASS' if step.get('counter_increase') else 'FAIL'}"
                      f"  {step.get('counter_detail', '')}")
            log.check(f"  [bw_rdma]          {'PASS' if step.get('bw_ok') else 'FAIL'}"
                      f"  {step.get('bw_gbs', 0.0):.2f} GB/s")
            if not step_ok:
                for failure in step.get("failures", []):
                    log.check(f"    FAILURE: {failure}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])
        if result.get("job_output_snippet"):
            log.check("  --- job output (last 30 lines) ---")
            for line in result["job_output_snippet"].splitlines()[-30:]:
                log.check(f"  {line}")
    assert result["success"], result["message"]
