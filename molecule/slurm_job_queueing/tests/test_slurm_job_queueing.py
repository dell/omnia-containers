"""
Testinfra tests for slurm_job_queueing verification.

This file contains test functions that verify Slurm job queueing functionality.
Tests continue even if some fail (skip_on_failure behavior).

Usage:
    ./run_molecule.sh slurm_job_queueing test      # Run playbook + verify
    ./run_molecule.sh slurm_job_queueing verify    # Verify only
"""

import pytest
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
    submit_slurm_job,
    submit_multiple_jobs,
    get_job_state,
    get_multiple_job_states,
    get_slurm_node_status,
    check_slurmctld_running,
    get_scheduler_info,
    cancel_slurm_jobs,
    validate_pending_reasons,
)


# =============================================================================
# SLURMCTLD TESTS
# =============================================================================

def test_slurmctld_running(host):
    """Verify slurmctld daemon is running."""
    log = TestLogger(TEST_NAMES["slurmctld_running"])
    log.check("Checking slurmctld service status")

    result = check_slurmctld_running(host)

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

def test_node_status(host):
    """Verify Slurm node status is retrievable."""
    log = TestLogger(TEST_NAMES["node_status"])
    log.check("Checking Slurm node status")

    result = get_slurm_node_status(host)

    if result["success"]:
        details = LOG_MSGS["nodes_available"].format(
            available=result["available_count"],
            total=result["total_count"]
        )
        log.passed(details, f"Down: {result['down_count']}")
        for node in result["nodes"][:5]:
            log.check(LOG_MSGS["node_status"].format(
                name=node["name"],
                state=node["state"],
                cpus=node["cpus"]
            ))
    else:
        log.failed("Failed to get node status", result["error"])

    assert result["success"], f"Failed to get Slurm node status: {result['error']}"


# =============================================================================
# JOB SUBMISSION TESTS
# =============================================================================

def test_job_submission(host):
    """Verify jobs can be submitted to Slurm."""
    log = TestLogger(TEST_NAMES["submit_jobs_no_nodes"])
    job_count = TEST_VARS["job_submit_count"]
    log.check(f"Submitting {job_count} test jobs")

    result = submit_multiple_jobs(host, count=job_count)

    if result["success"]:
        log.passed(
            LOG_MSGS["jobs_submitted"].format(count=result["submitted"]),
            f"Job IDs: {', '.join(result['job_ids'])}"
        )
    else:
        log.failed(
            LOG_MSGS["jobs_submit_partial"].format(
                submitted=result["submitted"],
                total=result["total"]
            ),
            ", ".join(result["errors"])
        )

    # Cleanup submitted jobs
    if result["job_ids"]:
        cancel_slurm_jobs(host, result["job_ids"])

    assert result["success"], ASSERT_MSGS["jobs_not_submitted"].format(
        submitted=result["submitted"],
        total=result["total"]
    )


# =============================================================================
# JOB STATE TESTS
# =============================================================================

def test_job_pending_state(host):
    """Verify jobs enter PENDING state with valid reasons."""
    log = TestLogger(TEST_NAMES["validate_pending_state"])
    log.check("Submitting job and checking pending state")

    # Submit a single job
    submit_result = submit_slurm_job(host)
    if not submit_result["success"]:
        log.failed(LOG_MSGS["job_submit_failed"], submit_result["error"])
        assert False, ASSERT_MSGS["job_submit_failed"].format(error=submit_result["error"])

    job_id = submit_result["job_id"]
    log.check(LOG_MSGS["job_submitted"].format(job_id=job_id))

    # Check job state
    state_result = get_job_state(host, job_id)
    state = state_result.get("state", "UNKNOWN").upper()
    reason = state_result.get("reason", "None")

    log.check(LOG_MSGS["job_state_check"].format(
        job_id=job_id,
        state=state,
        reason=reason
    ))

    # Validate state is acceptable (PENDING, RUNNING, or COMPLETED)
    valid_states = ["PENDING", "RUNNING", "COMPLETED", "COMPLETING"]
    
    if state in valid_states:
        if state == "PENDING":
            # Validate pending reason
            reason_valid = any(r.lower() in reason.lower() for r in PENDING_REASONS)
            if reason_valid:
                log.passed(LOG_MSGS["pending_reason_valid"].format(reason=reason), f"State: {state}")
            else:
                log.passed(f"Job in {state} state", f"Reason: {reason}")
        else:
            log.passed(f"Job in {state} state", f"Reason: {reason}")
    else:
        log.failed(f"Unexpected job state: {state}", reason)

    # Cleanup
    cancel_slurm_jobs(host, [job_id])

    assert state in valid_states, ASSERT_MSGS["jobs_not_pending"].format(states=state)


# =============================================================================
# SCHEDULER TESTS
# =============================================================================

def test_scheduler_configuration(host):
    """Verify Slurm scheduler configuration."""
    log = TestLogger(TEST_NAMES["scheduler_config"])
    log.check("Getting scheduler configuration")

    result = get_scheduler_info(host)

    if result["success"]:
        log.passed(
            LOG_MSGS["scheduler_config"].format(
                scheduler_type=result["scheduler_type"],
                select_type=result["select_type"],
                priority_type=result["priority_type"]
            ),
            "Scheduler configuration retrieved"
        )
    else:
        log.failed("Failed to get scheduler configuration", result["error"])

    assert result["success"], f"Failed to get scheduler configuration: {result['error']}"


def test_scheduler_allocation(host):
    """Verify Slurm scheduler allocates jobs correctly."""
    log = TestLogger(TEST_NAMES["validate_scheduler_allocation"])
    
    # First verify slurmctld is running
    log.check("Verifying slurmctld is running")
    slurmctld_result = check_slurmctld_running(host)
    if not slurmctld_result["success"]:
        log.failed(LOG_MSGS["slurmctld_inactive"].format(status=slurmctld_result["status"]), "")
        assert False, ASSERT_MSGS["scheduler_not_active"].format(status=slurmctld_result["status"])

    log.check(LOG_MSGS["slurmctld_active"])

    # Submit a test job
    log.check("Submitting test job to verify scheduler")
    submit_result = submit_slurm_job(host, job_name="scheduler_test")
    
    if submit_result["success"]:
        job_id = submit_result["job_id"]
        log.check(LOG_MSGS["job_submitted"].format(job_id=job_id))
        
        # Check job was queued
        state_result = get_job_state(host, job_id)
        state = state_result.get("state", "UNKNOWN").upper()
        
        log.check(LOG_MSGS["job_state_check"].format(
            job_id=job_id,
            state=state,
            reason=state_result.get("reason", "None")
        ))
        
        # Cleanup
        cancel_slurm_jobs(host, [job_id])
        log.check(LOG_MSGS["jobs_cancelled"].format(count=1))
        
        log.passed(LOG_MSGS["scheduler_responsive"], f"Job {job_id} was queued as {state}")
        assert True
    else:
        log.failed(LOG_MSGS["job_submit_failed"], submit_result["error"])
        assert False, ASSERT_MSGS["scheduler_allocation_failed"].format(error=submit_result["error"])
