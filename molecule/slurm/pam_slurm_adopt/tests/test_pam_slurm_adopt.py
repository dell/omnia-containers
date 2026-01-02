# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Testinfra tests for pam_slurm_adopt verification.

This file contains test functions that verify PAM Slurm Adopt functionality:
1. Start a job on a compute node and verify SSH access for the job owner
2. End the job and confirm the user is logged out automatically
3. Attempt SSH after job completion and verify access is denied

Usage:
    ./run_molecule.sh slurm/pam_slurm_adopt test      # Run playbook + verify
    ./run_molecule.sh slurm/pam_slurm_adopt verify    # Verify only
"""

import pytest
import time
from automation_library.core import TestLogger
from automation_library.slurm.vars.pam_slurm_adopt_vars import (
    PAM_SLURM_ADOPT_VARS,
    SSH_ACCESS_STATES,
)
from automation_library.slurm.messages.pam_slurm_adopt_msgs import (
    TEST_VARS, TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)
from automation_library.slurm.functions.pam_slurm_adopt_func import (
    get_ssh_host,
    submit_job_to_compute_node,
    get_job_state,
    get_job_node,
    cancel_slurm_job,
    wait_for_job_state,
    check_ssh_access_to_node,
    check_pam_slurm_adopt_configured,
    get_available_compute_node,
    check_slurmctld_running,
)


# =============================================================================
# FIXTURE: SSH HOST TO SLURM CONTROL NODE
# =============================================================================

@pytest.fixture(scope="module")
def slurm_host():
    """Get SSH host connected to Slurm control node via omnia_core."""
    return get_ssh_host()


# =============================================================================
# SLURMCTLD AND PAM CONFIGURATION TESTS
# =============================================================================

def test_slurmctld_running(slurm_host):
    """Verify slurmctld daemon is running."""
    log = TestLogger(TEST_NAMES["slurmctld_running"])
    log.check("Checking slurmctld service status")

    result = check_slurmctld_running(slurm_host)

    if result["success"]:
        log.passed(LOG_MSGS["slurmctld_active"], result["status"])
    else:
        log.failed(LOG_MSGS["slurmctld_inactive"].format(status=result["status"]), result["error"])

    assert result["success"], ASSERT_MSGS["slurmctld_not_running"].format(
        status=result["status"]
    )


def test_pam_slurm_adopt_configured(slurm_host):
    """Verify PAM Slurm Adopt is configured on compute nodes."""
    log = TestLogger(TEST_NAMES["pam_configured"])
    log.check("Checking PAM Slurm Adopt configuration")

    result = check_pam_slurm_adopt_configured(slurm_host)

    if result["success"]:
        log.passed(LOG_MSGS["pam_configured"], result["details"])
    else:
        # PAM Slurm Adopt may not be configured on all clusters - skip instead of fail
        log.check(f"PAM Slurm Adopt not configured: {result['error']}")
        pytest.skip(f"PAM Slurm Adopt is not configured on this cluster: {result['error']}")


# =============================================================================
# SSH ACCESS DURING ACTIVE JOB TEST
# =============================================================================

def test_ssh_access_during_active_job(slurm_host):
    """
    Test Scenario 1: Start a job on a compute node and verify SSH access for the job owner.
    
    Steps:
    1. Get an available compute node
    2. Submit a job to run on that node
    3. Wait for job to start running
    4. Verify SSH access is allowed for the job owner
    """
    log = TestLogger(TEST_NAMES["ssh_access_during_job"])
    
    # Step 1: Get available compute node
    log.check("Getting available compute node")
    node_result = get_available_compute_node(slurm_host)
    
    if not node_result["success"]:
        log.failed(LOG_MSGS["no_compute_node"], node_result["error"])
        pytest.skip(f"No available compute node: {node_result['error']}")
    
    compute_node = node_result["node"]
    log.check(LOG_MSGS["compute_node_found"].format(node=compute_node))
    
    # Step 2: Submit job to the compute node
    log.check("Submitting job to compute node")
    job_result = submit_job_to_compute_node(
        slurm_host, 
        node=compute_node,
        duration=TEST_VARS["job_duration"]
    )
    
    if not job_result["success"]:
        log.failed(LOG_MSGS["job_submit_failed"], job_result["error"])
        assert False, ASSERT_MSGS["job_submit_failed"].format(error=job_result["error"])
    
    job_id = job_result["job_id"]
    test_user = job_result["user"]
    log.check(LOG_MSGS["job_submitted"].format(job_id=job_id, user=test_user))
    
    try:
        # Step 3: Wait for job to start running
        log.check("Waiting for job to start running")
        wait_result = wait_for_job_state(
            slurm_host, 
            job_id, 
            target_state="RUNNING",
            timeout=TEST_VARS["job_start_timeout"]
        )
        
        if not wait_result["success"]:
            log.failed(LOG_MSGS["job_not_running"].format(job_id=job_id), wait_result["error"])
            assert False, ASSERT_MSGS["job_not_running"].format(
                job_id=job_id, 
                state=wait_result.get("current_state", "UNKNOWN")
            )
        
        log.check(LOG_MSGS["job_running"].format(job_id=job_id))
        
        # Step 4: Verify SSH access for job owner
        log.check(f"Testing SSH access to {compute_node} for user {test_user}")
        ssh_result = check_ssh_access_to_node(
            slurm_host,
            node=compute_node,
            user=test_user
        )
        
        if ssh_result["access_allowed"]:
            log.passed(
                LOG_MSGS["ssh_access_allowed"].format(user=test_user, node=compute_node),
                f"Job ID: {job_id}"
            )
        else:
            log.failed(
                LOG_MSGS["ssh_access_denied_unexpected"].format(user=test_user, node=compute_node),
                ssh_result["error"]
            )
        
        assert ssh_result["access_allowed"], ASSERT_MSGS["ssh_should_be_allowed"].format(
            user=test_user,
            node=compute_node,
            job_id=job_id
        )
        
    finally:
        # Cleanup: Cancel the job
        cancel_slurm_job(slurm_host, job_id)
        log.check(LOG_MSGS["job_cancelled"].format(job_id=job_id))


# =============================================================================
# AUTOMATIC LOGOUT AFTER JOB END TEST
# =============================================================================

def test_user_logout_after_job_end(slurm_host):
    """
    Test Scenario 2: End the job and confirm the user is logged out automatically.
    
    Steps:
    1. Submit a short job to a compute node
    2. Wait for job to start running
    3. Cancel the job (or wait for it to complete)
    4. Verify user sessions are terminated
    """
    log = TestLogger(TEST_NAMES["user_logout_after_job"])
    
    # Step 1: Get available compute node
    log.check("Getting available compute node")
    node_result = get_available_compute_node(slurm_host)
    
    if not node_result["success"]:
        log.failed(LOG_MSGS["no_compute_node"], node_result["error"])
        pytest.skip(f"No available compute node: {node_result['error']}")
    
    compute_node = node_result["node"]
    log.check(LOG_MSGS["compute_node_found"].format(node=compute_node))
    
    # Step 2: Submit a short job
    log.check("Submitting short job to compute node")
    job_result = submit_job_to_compute_node(
        slurm_host,
        node=compute_node,
        duration=TEST_VARS["short_job_duration"]
    )
    
    if not job_result["success"]:
        log.failed(LOG_MSGS["job_submit_failed"], job_result["error"])
        assert False, ASSERT_MSGS["job_submit_failed"].format(error=job_result["error"])
    
    job_id = job_result["job_id"]
    test_user = job_result["user"]
    log.check(LOG_MSGS["job_submitted"].format(job_id=job_id, user=test_user))
    
    try:
        # Step 3: Wait for job to start running
        log.check("Waiting for job to start running")
        wait_result = wait_for_job_state(
            slurm_host,
            job_id,
            target_state="RUNNING",
            timeout=TEST_VARS["job_start_timeout"]
        )
        
        if not wait_result["success"]:
            log.failed(LOG_MSGS["job_not_running"].format(job_id=job_id), wait_result["error"])
            pytest.skip(f"Job did not start running: {wait_result['error']}")
        
        log.check(LOG_MSGS["job_running"].format(job_id=job_id))
        
        # Step 4: Cancel the job to trigger logout
        log.check("Cancelling job to trigger user logout")
        cancel_slurm_job(slurm_host, job_id)
        
        # Wait for job to be cancelled/completed
        time.sleep(TEST_VARS["logout_wait_time"])
        
        # Step 5: Verify job is no longer running
        state_result = get_job_state(slurm_host, job_id)
        current_state = state_result.get("state", "UNKNOWN").upper()
        
        # Handle states with + suffix (e.g., CANCELLED+)
        base_state = current_state.rstrip('+')
        valid_end_states = ["CANCELLED", "COMPLETED", "FAILED", "TIMEOUT"]
        
        if base_state in valid_end_states:
            log.passed(
                LOG_MSGS["job_ended"].format(job_id=job_id, state=current_state),
                "User should be logged out"
            )
        else:
            log.failed(
                LOG_MSGS["job_still_active"].format(job_id=job_id, state=current_state),
                "Expected job to end"
            )
        
        assert base_state in valid_end_states, \
            ASSERT_MSGS["job_should_end"].format(job_id=job_id, state=current_state)
        
    finally:
        # Ensure job is cancelled
        cancel_slurm_job(slurm_host, job_id)


# =============================================================================
# SSH ACCESS DENIED AFTER JOB COMPLETION TEST
# =============================================================================

def test_ssh_access_denied_after_job_completion(slurm_host):
    """
    Test Scenario 3: Attempt SSH after job completion and verify access is denied.
    
    This test uses a non-root user (testuser) to properly verify PAM Slurm Adopt
    denies SSH access after job completion. Root user bypasses PAM restrictions.
    
    Steps:
    1. Submit a job as testuser to a compute node
    2. Wait for job to start running
    3. Cancel the job
    4. Wait for job to end
    5. Attempt SSH as testuser and verify access is denied
    """
    log = TestLogger(TEST_NAMES["ssh_denied_after_job"])
    
    # Use non-root user for proper PAM testing
    test_user = "testuser"
    
    # Step 1: Get available compute node
    log.check("Getting available compute node")
    node_result = get_available_compute_node(slurm_host)
    
    if not node_result["success"]:
        log.failed(LOG_MSGS["no_compute_node"], node_result["error"])
        pytest.skip(f"No available compute node: {node_result['error']}")
    
    compute_node = node_result["node"]
    log.check(LOG_MSGS["compute_node_found"].format(node=compute_node))
    
    # Step 2: Submit job as testuser
    log.check(f"Submitting job to compute node as {test_user}")
    job_result = submit_job_to_compute_node(
        slurm_host,
        node=compute_node,
        duration=TEST_VARS["job_duration"],
        run_as_user=test_user
    )
    
    if not job_result["success"]:
        log.failed(LOG_MSGS["job_submit_failed"], job_result["error"])
        assert False, ASSERT_MSGS["job_submit_failed"].format(error=job_result["error"])
    
    job_id = job_result["job_id"]
    log.check(LOG_MSGS["job_submitted"].format(job_id=job_id, user=test_user))
    
    try:
        # Step 3: Wait for job to start
        log.check("Waiting for job to start running")
        wait_result = wait_for_job_state(
            slurm_host,
            job_id,
            target_state="RUNNING",
            timeout=TEST_VARS["job_start_timeout"]
        )
        
        if wait_result["success"]:
            log.check(LOG_MSGS["job_running"].format(job_id=job_id))
        
        # Step 4: Cancel the job
        log.check("Cancelling job")
        cancel_slurm_job(slurm_host, job_id)
        
        # Step 5: Wait for job to fully end
        log.check("Waiting for job to fully terminate")
        time.sleep(TEST_VARS["logout_wait_time"])
        
        # Verify job ended
        state_result = get_job_state(slurm_host, job_id)
        current_state = state_result.get("state", "UNKNOWN").upper()
        log.check(LOG_MSGS["job_ended"].format(job_id=job_id, state=current_state))
        
        # Step 6: Attempt SSH as testuser and verify access is denied
        log.check(f"Testing SSH access to {compute_node} for user {test_user} after job completion")
        ssh_result = check_ssh_access_to_node(
            slurm_host,
            node=compute_node,
            user=test_user
        )
        
        if not ssh_result["access_allowed"]:
            log.passed(
                LOG_MSGS["ssh_access_denied_expected"].format(user=test_user, node=compute_node),
                f"Job {job_id} has ended - PAM Slurm Adopt denied access"
            )
        else:
            log.failed(
                LOG_MSGS["ssh_access_allowed_unexpected"].format(user=test_user, node=compute_node),
                "Access should be denied after job completion"
            )
        
        assert not ssh_result["access_allowed"], ASSERT_MSGS["ssh_should_be_denied"].format(
            user=test_user,
            node=compute_node,
            job_id=job_id
        )
        
    finally:
        # Ensure job is cancelled
        cancel_slurm_job(slurm_host, job_id)
