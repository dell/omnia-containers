"""
Slurm Job Queueing - Messages and Test Strings.

This module contains all messages, test names, and assertion messages
for Slurm job queueing tests.

Usage:
    from automation_library.messages.slurm_job_queueing_msgs import (
        TEST_VARS, TEST_NAMES, TEST_LOG_MSGS, TEST_ASSERT_MSGS
    )

Author: Dell Technologies
"""

# =============================================================================
# TEST VARIABLES (for parameterization)
# =============================================================================

TEST_VARS = {
    "job_submit_count": 3,
    "job_wait_timeout": 60,
    "poll_interval": 5,
}

# =============================================================================
# TEST NAMES (displayed in test output)
# =============================================================================

TEST_NAMES = {
    "submit_jobs_no_nodes": "Submit multiple jobs when compute nodes are unavailable",
    "validate_pending_state": "Validate jobs are in PENDING state with appropriate reasons",
    "validate_running_transition": "Validate jobs transition to RUNNING when nodes available",
    "validate_scheduler_allocation": "Validate Slurm scheduler allocates jobs correctly",
    "slurmctld_running": "Verify slurmctld daemon is running",
    "node_status": "Check Slurm node status",
    "job_state": "Check job state: {job_id}",
    "scheduler_config": "Verify Slurm scheduler configuration",
}

# =============================================================================
# LOG MESSAGES (for TestLogger output)
# =============================================================================

TEST_LOG_MSGS = {
    # Job submission
    "job_submitted": "Job submitted successfully: {job_id}",
    "job_submit_failed": "Failed to submit job",
    "jobs_submitted": "All {count} jobs submitted successfully",
    "jobs_submit_partial": "Only {submitted}/{total} jobs submitted",
    
    # Job states
    "job_pending": "Job {job_id} is in PENDING state",
    "job_running": "Job {job_id} is in RUNNING state",
    "job_completed": "Job {job_id} has completed",
    "job_state_check": "Job {job_id}: State={state}, Reason={reason}",
    
    # Pending reasons
    "pending_reason_valid": "Pending reason is valid: {reason}",
    "pending_reason_invalid": "Invalid pending reason: {reason}",
    "pending_reasons_found": "Pending reasons: {reasons}",
    
    # State transitions
    "job_transitioned": "Job {job_id} transitioned to {state}",
    "job_transition_timeout": "Job {job_id} did not transition within {timeout}s",
    "job_already_running": "Job {job_id} is already RUNNING",
    "job_already_completed": "Job {job_id} already completed",
    
    # Scheduler
    "scheduler_active": "Slurm scheduler is active",
    "scheduler_inactive": "Slurm scheduler is not active",
    "scheduler_config": "Scheduler: {scheduler_type}, Select: {select_type}, Priority: {priority_type}",
    "scheduler_responsive": "Scheduler is responsive",
    
    # Nodes
    "nodes_available": "Available nodes: {available}/{total}",
    "nodes_down": "Down/Drained nodes: {down}",
    "node_status": "{name}: {state} ({cpus} CPUs)",
    
    # slurmctld
    "slurmctld_active": "slurmctld is active",
    "slurmctld_inactive": "slurmctld is not active: {status}",
    
    # Cleanup
    "jobs_cancelled": "Cancelled {count} test jobs",
    "cleanup_complete": "Test cleanup complete",
}

# =============================================================================
# ASSERTION MESSAGES (for pytest assertions)
# =============================================================================

TEST_ASSERT_MSGS = {
    "job_submit_failed": "Failed to submit job: {error}",
    "jobs_not_submitted": "Failed to submit all jobs. Submitted: {submitted}/{total}",
    "jobs_not_pending": "Expected jobs in PENDING state, got: {states}",
    "invalid_pending_reason": "Invalid pending reason: {reason}. Expected one of: {expected}",
    "jobs_not_running": "Jobs did not transition to RUNNING within {timeout}s",
    "scheduler_not_active": "Slurm scheduler (slurmctld) is not active: {status}",
    "scheduler_allocation_failed": "Scheduler did not allocate jobs correctly: {error}",
    "no_nodes_available": "No compute nodes available for job execution",
    "slurmctld_not_running": "slurmctld daemon is not running: {status}",
}

# =============================================================================
# REPORT MESSAGES
# =============================================================================

SLURM_JOB_QUEUEING_MSGS = {
    "validation_summary": "Slurm Job Queueing: {passed}/{total} tests passed, {failed} failed",
    "test_header": "Slurm Job Queueing Tests",
    "test_target": "Target: {target}",
    "test_via": "Via: {via}",
    "connectivity_pass": "Connected to {hostname}",
    "connectivity_fail": "Cannot connect to {target}",
}
