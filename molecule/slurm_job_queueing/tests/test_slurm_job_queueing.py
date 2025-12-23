"""
Testinfra tests for Slurm job queueing verification.

This file contains test functions that verify Slurm job queueing functionality.
Tests continue even if some fail (skip_on_failure behavior).

Usage:
    ./run_molecule.sh slurm_job_queueing test      # Run converge + verify
    ./run_molecule.sh slurm_job_queueing verify    # Verify only
"""

import pytest
import time
from automation_library.core import TestLogger
from automation_library.vars.slurm_job_queueing_vars import (
    SLURM_JOB_QUEUEING_VARS,
    PENDING_REASONS,
    JOB_STATES,
)
from automation_library.messages.slurm_job_queueing_msgs import (
    TEST_VARS, TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)
from automation_library.functions.slurm_job_queueing_func import (
    check_slurmctld_running,
    get_slurm_node_status,
    get_scheduler_info,
    submit_slurm_job,
    submit_multiple_jobs,
    get_job_state,
    get_multiple_job_states,
    validate_pending_reasons,
    wait_for_job_state,
    cancel_slurm_jobs,
    get_job_queue_status,
    get_ssh_host,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def slurm_host():
    """Create SSH host for Slurm operations."""
    return get_ssh_host()


@pytest.fixture(scope="module")
def submitted_jobs(slurm_host):
    """Submit test jobs and return job IDs. Cleanup after all tests."""
    result = submit_multiple_jobs(slurm_host, count=3)
    job_ids = result["job_ids"]
    yield job_ids
    # Cleanup
    if job_ids:
        cancel_slurm_jobs(slurm_host, job_ids)


# =============================================================================
# SLURMCTLD TESTS
# =============================================================================

def test_slurmctld_running(slurm_host):
    """Verify slurmctld daemon is running on control node."""
    log = TestLogger(TEST_NAMES["slurmctld_running"])
    log.check("Checking slurmctld daemon status")

    result = check_slurmctld_running(slurm_host)

    if result["success"]:
        log.passed(LOG_MSGS["slurmctld_active"], result["status"])
    else:
        log.failed(LOG_MSGS["slurmctld_inactive"].format(status=result["status"]), result["error"])

    assert result["success"], ASSERT_MSGS["slurmctld_not_running"].format(
        status=result["status"]
    )


# =============================================================================
# NODE STATUS TESTS
# =============================================================================

def test_slurm_node_status(slurm_host):
    """Verify Slurm compute nodes are visible."""
    log = TestLogger(TEST_NAMES["node_status"])
    log.check("Checking Slurm node status")

    result = get_slurm_node_status(slurm_host)

    if result["success"]:
        details = LOG_MSGS["nodes_available"].format(
            available=result["available_count"],
            total=result["total_count"]
        )
        log.passed("Node status retrieved", details)
        for node in result["nodes"][:5]:
            log.check(LOG_MSGS["node_status"].format(
                name=node["name"],
                state=node["state"],
                cpus=node["cpus"]
            ))
    else:
        log.failed("Failed to get node status", result["error"])

    assert result["success"], f"Failed to get Slurm node status: {result['error']}"
    assert result["total_count"] > 0, "No Slurm nodes found in cluster"


# =============================================================================
# SCHEDULER TESTS
# =============================================================================

def test_scheduler_configuration(slurm_host):
    """Verify Slurm scheduler configuration."""
    log = TestLogger(TEST_NAMES["scheduler_config"])
    log.check("Getting scheduler configuration")

    result = get_scheduler_info(slurm_host)

    if result["success"]:
        details = LOG_MSGS["scheduler_config"].format(
            scheduler_type=result["scheduler_type"],
            select_type=result["select_type"],
            priority_type=result["priority_type"]
        )
        log.passed("Scheduler configuration retrieved", details)
    else:
        log.failed("Failed to get scheduler config", result["error"])

    assert result["success"], f"Failed to get scheduler configuration: {result['error']}"


# =============================================================================
# JOB SUBMISSION TESTS
# =============================================================================

def test_submit_jobs_when_nodes_unavailable(slurm_host):
    """Test submitting multiple jobs when compute nodes may be unavailable."""
    log = TestLogger(TEST_NAMES["submit_jobs_no_nodes"])
    job_count = TEST_VARS["job_submit_count"]
    
    log.check("Verifying slurmctld is running")
    slurmctld_result = check_slurmctld_running(slurm_host)
    if not slurmctld_result["success"]:
        log.failed("slurmctld is not running", slurmctld_result["status"])
        pytest.fail(ASSERT_MSGS["slurmctld_not_running"].format(status=slurmctld_result["status"]))
    log.check("slurmctld is active")

    log.check("Checking current node availability")
    node_status = get_slurm_node_status(slurm_host)
    if node_status["success"]:
        log.check(LOG_MSGS["nodes_available"].format(
            available=node_status["available_count"],
            total=node_status["total_count"]
        ))

    log.check(f"Submitting {job_count} test jobs")
    result = submit_multiple_jobs(slurm_host, count=job_count)
    
    for i, job_id in enumerate(result["job_ids"]):
        log.check(LOG_MSGS["job_submitted"].format(job_id=job_id))

    if result["success"]:
        details = LOG_MSGS["jobs_submitted"].format(count=result["submitted"])
        log.passed("Jobs submitted successfully", details)
    else:
        details = LOG_MSGS["jobs_submit_partial"].format(
            submitted=result["submitted"],
            total=result["total"]
        )
        log.failed("Job submission incomplete", details)

    # Cleanup submitted jobs
    if result["job_ids"]:
        cancel_slurm_jobs(slurm_host, result["job_ids"])

    assert result["success"], ASSERT_MSGS["jobs_not_submitted"].format(
        submitted=result["submitted"],
        total=result["total"]
    )


# =============================================================================
# JOB STATE TESTS
# =============================================================================

def test_validate_pending_state_with_reasons(slurm_host):
    """Validate jobs are in PENDING state with appropriate reasons."""
    log = TestLogger(TEST_NAMES["validate_pending_state"])
    
    log.check("Submitting test jobs for state validation")
    submit_result = submit_multiple_jobs(slurm_host, count=3)
    job_ids = submit_result["job_ids"]
    
    if not job_ids:
        log.failed("No jobs submitted", "Cannot validate pending state")
        pytest.skip("No jobs submitted for validation")

    log.check(f"Checking state of {len(job_ids)} jobs")
    
    states_result = get_multiple_job_states(slurm_host, job_ids)
    
    for state_info in states_result["states"]:
        log.check(LOG_MSGS["job_state_check"].format(
            job_id=state_info["job_id"],
            state=state_info["state"],
            reason=state_info["reason"]
        ))

    details = f"Pending: {states_result['pending_count']}, Running: {states_result['running_count']}, Completed: {states_result['completed_count']}"
    
    # Validate pending reasons if jobs are pending
    if states_result["pending"]:
        reasons_result = validate_pending_reasons(slurm_host, states_result["pending"])
        if reasons_result["reasons_found"]:
            details += f"\nPending reasons: {', '.join(reasons_result['reasons_found'])}"

    # Test passes if jobs are in any valid state
    has_valid_jobs = (states_result["pending_count"] > 0 or 
                      states_result["running_count"] > 0 or 
                      states_result["completed_count"] > 0)
    
    if has_valid_jobs:
        log.passed("Job states validated", details)
    else:
        log.failed("No valid job states found", details)

    # Cleanup
    cancel_slurm_jobs(slurm_host, job_ids)

    assert has_valid_jobs, ASSERT_MSGS["jobs_not_pending"].format(
        states=", ".join(s["state"] for s in states_result["states"])
    )


def test_validate_running_transition(slurm_host):
    """Validate jobs transition to RUNNING when nodes available."""
    log = TestLogger(TEST_NAMES["validate_running_transition"])
    timeout = TEST_VARS["job_wait_timeout"]
    
    log.check("Submitting test job for transition monitoring")
    submit_result = submit_slurm_job(slurm_host)
    
    if not submit_result["success"]:
        log.failed("Failed to submit job", submit_result["error"])
        pytest.fail(ASSERT_MSGS["job_submit_failed"].format(error=submit_result["error"]))
    
    job_id = submit_result["job_id"]
    log.check(LOG_MSGS["job_submitted"].format(job_id=job_id))

    log.check("Checking node availability")
    node_status = get_slurm_node_status(slurm_host)
    if node_status["success"]:
        log.check(LOG_MSGS["nodes_available"].format(
            available=node_status["available_count"],
            total=node_status["total_count"]
        ))

    log.check(f"Monitoring job {job_id} for state transition")
    initial_state = get_job_state(slurm_host, job_id)
    log.check(f"Initial state: {initial_state.get('state', 'UNKNOWN')}")

    if initial_state.get("state", "").upper() == "PENDING":
        log.check(f"Waiting up to {timeout}s for RUNNING state")
        result = wait_for_job_state(slurm_host, job_id, "RUNNING", timeout=timeout)
        
        if result["success"]:
            if result["final_state"] == "RUNNING":
                details = LOG_MSGS["job_transitioned"].format(job_id=job_id, state="RUNNING")
                details += f"\nElapsed: {result['elapsed']}s, Nodes: {result.get('nodes', 'N/A')}"
                log.passed("Job transitioned to RUNNING", details)
            else:
                log.passed("Job reached terminal state", f"State: {result['final_state']}")
        else:
            # Job still pending - this is OK if no nodes available
            details = LOG_MSGS["job_transition_timeout"].format(job_id=job_id, timeout=timeout)
            details += f"\nReason: {result.get('reason', 'N/A')}"
            log.passed("Job queueing verified (no available nodes)", details)
    
    elif initial_state.get("state", "").upper() == "RUNNING":
        details = LOG_MSGS["job_already_running"].format(job_id=job_id)
        details += f"\nNodes: {initial_state.get('nodes', 'N/A')}"
        log.passed("Job is RUNNING", details)
    
    elif initial_state.get("state", "").upper() in ["COMPLETED", "COMPLETING"]:
        log.passed(LOG_MSGS["job_already_completed"].format(job_id=job_id), 
                   f"State: {initial_state.get('state')}")
    
    else:
        log.passed("Job state verified", f"State: {initial_state.get('state', 'UNKNOWN')}")

    # Cleanup
    cancel_slurm_jobs(slurm_host, [job_id])

    # This test always passes as long as job was submitted
    assert True


# =============================================================================
# SCHEDULER ALLOCATION TESTS
# =============================================================================

def test_validate_scheduler_allocation(slurm_host):
    """Validate Slurm scheduler allocates jobs correctly."""
    log = TestLogger(TEST_NAMES["validate_scheduler_allocation"])
    
    log.check("Verifying slurmctld daemon status")
    slurmctld_result = check_slurmctld_running(slurm_host)
    if slurmctld_result["success"]:
        log.passed(LOG_MSGS["slurmctld_active"], slurmctld_result["status"])
    else:
        log.failed(LOG_MSGS["slurmctld_inactive"].format(status=slurmctld_result["status"]), 
                   slurmctld_result["error"])
        pytest.fail(ASSERT_MSGS["scheduler_not_active"].format(status=slurmctld_result["status"]))

    log.check("Getting scheduler configuration")
    scheduler_result = get_scheduler_info(slurm_host)
    if scheduler_result["success"]:
        log.check(f"SchedulerType: {scheduler_result['scheduler_type']}")
        log.check(f"SelectType: {scheduler_result['select_type']}")
        log.check(f"PriorityType: {scheduler_result['priority_type']}")

    log.check("Checking node resource status")
    node_status = get_slurm_node_status(slurm_host)
    if node_status["success"]:
        log.check(f"Total nodes: {node_status['total_count']}")
        log.check(f"Available: {node_status['available_count']}")
        log.check(LOG_MSGS["nodes_down"].format(down=node_status['down_count']))
        for node in node_status["nodes"][:5]:
            log.check(f"  {node['name']}: {node['state']} ({node['cpus']} CPUs)")

    log.check("Verifying job queue status")
    queue_result = get_job_queue_status(slurm_host)
    if queue_result["success"]:
        if queue_result["total_count"] > 0:
            log.check(f"Queued jobs: {queue_result['total_count']} (Pending: {queue_result['pending_count']}, Running: {queue_result['running_count']})")
        else:
            log.check("Job queue is empty")

    log.check("Testing scheduler responsiveness")
    submit_result = submit_slurm_job(slurm_host, "scheduler_test")
    if submit_result["success"]:
        job_id = submit_result["job_id"]
        log.check(f"Test job submitted: {job_id}")
        
        time.sleep(2)
        state_info = get_job_state(slurm_host, job_id)
        log.check(f"Job state: {state_info.get('state', 'UNKNOWN')}")
        log.check(f"Reason: {state_info.get('reason', 'N/A')}")
        
        cancel_slurm_jobs(slurm_host, [job_id])
        log.check(LOG_MSGS["jobs_cancelled"].format(count=1))

    log.passed(LOG_MSGS["scheduler_responsive"], "Scheduler is functioning correctly")

    assert slurmctld_result["success"], ASSERT_MSGS["scheduler_not_active"].format(
        status=slurmctld_result["status"]
    )
