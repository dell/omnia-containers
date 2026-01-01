"""
PAM Slurm Adopt - Messages and Test Strings.

This module contains all messages, test names, and assertion messages
for PAM Slurm Adopt tests.

Usage:
    from automation_library.slurm.messages import (
        PAM_SLURM_ADOPT_TEST_VARS, PAM_SLURM_ADOPT_TEST_NAMES,
        PAM_SLURM_ADOPT_LOG_MSGS, PAM_SLURM_ADOPT_ASSERT_MSGS
    )

Author: Dell Technologies
"""

# =============================================================================
# TEST VARIABLES (for parameterization)
# =============================================================================

TEST_VARS = {
    "job_duration": 120,
    "short_job_duration": 30,
    "job_start_timeout": 60,
    "logout_wait_time": 5,
}

# =============================================================================
# TEST NAMES (displayed in test output)
# =============================================================================

TEST_NAMES = {
    "slurmctld_running": "Verify slurmctld daemon is running",
    "pam_configured": "Verify PAM Slurm Adopt is configured",
    "ssh_access_during_job": "Verify SSH access allowed during active job",
    "user_logout_after_job": "Verify user logout after job ends",
    "ssh_denied_after_job": "Verify SSH access denied after job completion",
}

# =============================================================================
# LOG MESSAGES (for TestLogger output)
# =============================================================================

TEST_LOG_MSGS = {
    # Slurmctld status
    "slurmctld_active": "slurmctld daemon is active and running",
    "slurmctld_inactive": "slurmctld is not active: {status}",
    
    # PAM configuration
    "pam_configured": "PAM Slurm Adopt is properly configured",
    "pam_not_configured": "PAM Slurm Adopt is not configured",
    
    # Compute node
    "compute_node_found": "Found available compute node: {node}",
    "no_compute_node": "No available compute node found",
    
    # Job submission
    "job_submitted": "Job {job_id} submitted for user {user}",
    "job_submit_failed": "Failed to submit job",
    "job_running": "Job {job_id} is now running",
    "job_not_running": "Job {job_id} did not start running",
    "job_cancelled": "Job {job_id} cancelled",
    "job_ended": "Job {job_id} ended with state: {state}",
    "job_still_active": "Job {job_id} is still active with state: {state}",
    
    # SSH access
    "ssh_access_allowed": "SSH access ALLOWED for user {user} to node {node}",
    "ssh_access_denied_expected": "SSH access correctly DENIED for user {user} to node {node}",
    "ssh_access_denied_unexpected": "SSH access unexpectedly DENIED for user {user} to node {node}",
    "ssh_access_allowed_unexpected": "SSH access unexpectedly ALLOWED for user {user} to node {node}",
}

# =============================================================================
# ASSERTION MESSAGES (for pytest assertions)
# =============================================================================

TEST_ASSERT_MSGS = {
    # Slurmctld
    "slurmctld_not_running": "slurmctld daemon is not running: {status}",
    
    # PAM configuration
    "pam_not_configured": "PAM Slurm Adopt is not configured: {error}",
    
    # Job submission
    "job_submit_failed": "Failed to submit job: {error}",
    "job_not_running": "Job {job_id} did not reach RUNNING state, current state: {state}",
    "job_should_end": "Job {job_id} should have ended, current state: {state}",
    
    # SSH access
    "ssh_should_be_allowed": "SSH access should be allowed for user {user} to node {node} during job {job_id}",
    "ssh_should_be_denied": "SSH access should be denied for user {user} to node {node} after job {job_id} completion",
}

# =============================================================================
# GENERAL MESSAGES
# =============================================================================

PAM_SLURM_ADOPT_MSGS = {
    "test_start": "Starting PAM Slurm Adopt test",
    "test_complete": "PAM Slurm Adopt test completed",
    "cleanup": "Cleaning up test resources",
}
