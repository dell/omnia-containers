"""
Insufficient Resources - Messages and Test Strings.

This module contains all messages, test names, and assertion messages
for insufficient resources tests.

Usage:
    from automation_library.messages.insufficient_resources_msgs import (
        TEST_VARS, TEST_NAMES, TEST_LOG_MSGS, TEST_ASSERT_MSGS
    )

Author: Dell Technologies
"""

# =============================================================================
# TEST VARIABLES (for parameterization)
# =============================================================================

TEST_VARS = {
    "excessive_multiplier": 10,
    "default_gpu_request": 100,
    "job_wait_timeout": 30,
}

# =============================================================================
# TEST NAMES (displayed in test output)
# =============================================================================

TEST_NAMES = {
    "slurmctld_running": "Verify slurmctld daemon is running",
    "cluster_resources": "Get cluster resource information",
    "excessive_cpu": "Submit job with excessive CPU request",
    "excessive_memory": "Submit job with excessive memory request",
    "gpu_unavailable": "Submit job requesting unavailable GPUs",
    "excessive_cpu_memory": "Submit job with excessive CPU and memory",
    "validate_pending_reason": "Validate PENDING state with resource reason",
    "validate_rejection": "Validate job rejection with appropriate error",
}

# =============================================================================
# LOG MESSAGES (for TestLogger output)
# =============================================================================

TEST_LOG_MSGS = {
    # Cluster resources
    "cluster_resources_retrieved": "Cluster resources retrieved successfully",
    "node_resources": "{name}: {cpus} CPUs, {memory}MB memory",
    "max_resources": "Max CPUs: {max_cpus}, Max Memory: {max_memory}MB",
    
    # Job submission
    "job_submitted": "Job submitted: {job_id}",
    "job_submit_failed": "Job submission failed",
    "job_rejected": "Job rejected: {error}",
    
    # Resource validation
    "job_pending_resources": "Job PENDING due to resources: {reason}",
    "job_running_unexpected": "Job unexpectedly RUNNING",
    "unexpected_response": "Unexpected response from Slurm",
    
    # slurmctld
    "slurmctld_active": "slurmctld is active",
    "slurmctld_inactive": "slurmctld is not active: {status}",
    
    # Cleanup
    "jobs_cancelled": "Cancelled {count} test jobs",
}

# =============================================================================
# ASSERTION MESSAGES (for pytest assertions)
# =============================================================================

TEST_ASSERT_MSGS = {
    "slurmctld_not_running": "slurmctld daemon is not running: {status}",
    "cluster_resources_failed": "Failed to get cluster resources: {error}",
    "invalid_resource_response": "Invalid response for insufficient resource request: {details}",
    "job_should_not_run": "Job with excessive resources should not be RUNNING",
    "missing_pending_reason": "Job is PENDING but missing valid resource reason: {reason}",
    "unexpected_job_state": "Unexpected job state: {state}. Expected PENDING or rejection",
}

# =============================================================================
# REPORT MESSAGES
# =============================================================================

INSUFFICIENT_RESOURCES_MSGS = {
    "validation_summary": "Insufficient Resources: {passed}/{total} tests passed, {failed} failed",
    "test_header": "Insufficient Resources Tests",
    "test_description": "Validate Slurm behavior when jobs request more resources than available",
}
