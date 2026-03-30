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

"""Resource limit job behavior tests for Slurm.

Validates job behavior when requesting resources exceeding cluster capacity:
1. Job requesting more CPUs than available goes to PENDING with PartitionConfig reason
2. Job requesting more memory than available is rejected
3. Job requesting both excessive CPU and memory goes to PENDING with PartitionConfig reason

Configuration (env-driven + PXE mapping discovery):
- Preferred: derive login node admin IPs from pxe_mapping_file via public core API
- Fallback: LOGIN_NODE_IPS env (comma-separated login node IPs)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.slurm.messages import (
    RESOURCE_LIMIT_TEST_NAMES,
    RESOURCE_LIMIT_LOG_MSGS,
    RESOURCE_LIMIT_ASSERT_MSGS,
)
from automation_library.slurm.functions import (
    setup_resource_limit_test_env,
    get_cluster_resources,
    create_resource_job_script,
    submit_resource_job_script,
    poll_job_state_direct,
    cleanup_resource_test,
)


# =============================================================================
# TESTS
# =============================================================================

def test_job_pending_when_exceeding_cpu():
    """Verify job goes to PENDING with PartitionConfig when requesting more CPUs than available.

    Test Steps:
    1. Slurm should be up and running
    2. Log into login node
    3. Run sinfo to observe allocated CPUs
    4. Create job script requesting more CPUs than available
    5. Submit the job
    6. Verify job is in PENDING state with PartitionConfig reason
    """
    log = TestLogger(RESOURCE_LIMIT_TEST_NAMES["exceed_cpu_pending"])
    job_ids = []

    # Set up test environment
    env_result = setup_resource_limit_test_env()
    assert env_result["success"], env_result["error"]
    login_ip = env_result["login_ip"]
    log.passed(f"Using login node: {login_ip}")

    try:
        # Get cluster resources
        resources = get_cluster_resources(login_ip)
        assert resources["success"], RESOURCE_LIMIT_ASSERT_MSGS["sinfo_failed"].format(error=resources["error"])
        log.passed(RESOURCE_LIMIT_LOG_MSGS["cluster_resources"].format(
            node=resources["node"],
            cpus=resources["cpus"],
            memory_mb=resources["memory_mb"]
        ))

        # Request more CPUs than available (e.g., available + 1)
        requested_cpus = resources["cpus"] + 1
        log.check(f"Requesting {requested_cpus} CPUs (available: {resources['cpus']})")

        # Create job script
        script_result = create_resource_job_script(
            login_ip, "root",
            cpus=requested_cpus,
            job_name="exceed_cpu_test"
        )
        assert script_result["success"], RESOURCE_LIMIT_ASSERT_MSGS["job_script_failed"].format(
            error=script_result["error"]
        )
        log.passed(RESOURCE_LIMIT_LOG_MSGS["job_script_created"].format(
            cpus=requested_cpus, memory=0
        ))

        # Submit job
        submit_result = submit_resource_job_script(login_ip)
        assert submit_result["success"], RESOURCE_LIMIT_ASSERT_MSGS["submit_failed"].format(
            error=submit_result["error"]
        )
        job_id = submit_result["job_id"]
        job_ids.append(job_id)
        log.passed(RESOURCE_LIMIT_LOG_MSGS["job_submitted"].format(job_id=job_id))

        # Check job state - should be PENDING with PartitionConfig reason
        state_result = poll_job_state_direct(login_ip, "root", job_id, timeout=30)
        state = state_result.get("state", "")
        reason = state_result.get("reason", "")

        assert state == "PENDING", RESOURCE_LIMIT_ASSERT_MSGS["job_not_pending"].format(
            job_id=job_id, state=state
        )
        log.passed(RESOURCE_LIMIT_LOG_MSGS["job_pending"].format(job_id=job_id, reason=reason))

        # Verify reason contains PartitionConfig
        assert "PartitionConfig" in reason or "ReqNodeNotAvail" in reason, \
            RESOURCE_LIMIT_ASSERT_MSGS["wrong_pending_reason"].format(job_id=job_id, reason=reason)
        log.passed(f"Job {job_id} has correct pending reason: {reason}")

    finally:
        cleanup_resource_test(login_ip, "root", job_ids)


def test_job_rejected_when_exceeding_memory():
    """Verify job is rejected when requesting more memory than available.

    Test Steps:
    1. Slurm should be up and running
    2. Log into login node
    3. Run sinfo to observe maximum memory allocated
    4. Create job script requesting more memory than available
    5. Submit the job
    6. Verify job is rejected or goes to PENDING with appropriate reason
    """
    log = TestLogger(RESOURCE_LIMIT_TEST_NAMES["exceed_memory_rejected"])
    job_ids = []

    # Set up test environment
    env_result = setup_resource_limit_test_env()
    assert env_result["success"], env_result["error"]
    login_ip = env_result["login_ip"]
    log.passed(f"Using login node: {login_ip}")

    try:
        # Get cluster resources
        resources = get_cluster_resources(login_ip)
        assert resources["success"], RESOURCE_LIMIT_ASSERT_MSGS["sinfo_failed"].format(error=resources["error"])
        log.passed(RESOURCE_LIMIT_LOG_MSGS["cluster_resources"].format(
            node=resources["node"],
            cpus=resources["cpus"],
            memory_mb=resources["memory_mb"]
        ))

        # Request more memory than available (e.g., available + 2GB)
        requested_memory_mb = resources["memory_mb"] + 2048
        log.check(f"Requesting {requested_memory_mb}MB memory (available: {resources['memory_mb']}MB)")

        # Create job script
        script_result = create_resource_job_script(
            login_ip, "root",
            memory_mb=requested_memory_mb,
            job_name="exceed_mem_test"
        )
        assert script_result["success"], RESOURCE_LIMIT_ASSERT_MSGS["job_script_failed"].format(
            error=script_result["error"]
        )
        log.passed(RESOURCE_LIMIT_LOG_MSGS["job_script_created"].format(
            cpus=0, memory=requested_memory_mb
        ))

        # Submit job - may be rejected or accepted as PENDING
        submit_result = submit_resource_job_script(login_ip)

        if not submit_result["success"]:
            # Job was rejected as expected
            log.passed(RESOURCE_LIMIT_LOG_MSGS["job_rejected"].format(error=submit_result["error"]))
            return

        # Job was accepted - check if it's PENDING with appropriate reason
        job_id = submit_result["job_id"]
        job_ids.append(job_id)
        log.check(f"Job {job_id} was accepted, checking state...")

        state_result = poll_job_state_direct(login_ip, "root", job_id, timeout=30)
        state = state_result.get("state", "")
        reason = state_result.get("reason", "")

        # Job should be PENDING with a resource-related reason
        if state == "PENDING":
            log.passed(RESOURCE_LIMIT_LOG_MSGS["job_pending"].format(job_id=job_id, reason=reason))
            # Accept various resource-related reasons
            valid_reasons = ["PartitionConfig", "Resources", "ReqNodeNotAvail"]
            has_valid_reason = any(r in reason for r in valid_reasons)
            assert has_valid_reason, RESOURCE_LIMIT_ASSERT_MSGS["wrong_pending_reason"].format(
                job_id=job_id, reason=reason
            )
            log.passed(f"Job {job_id} is PENDING with valid reason: {reason}")
        else:
            # If job is not PENDING, it should have been rejected
            pytest.fail(RESOURCE_LIMIT_ASSERT_MSGS["job_should_be_rejected"].format(job_id=job_id))

    finally:
        cleanup_resource_test(login_ip, "root", job_ids)


def test_job_pending_when_exceeding_cpu_and_memory():
    """Verify job goes to PENDING with PartitionConfig when requesting more CPU and memory.

    Test Steps:
    1. Slurm should be up and running
    2. Log into login node
    3. Run sinfo to observe maximum CPU and memory available
    4. Create job script requesting more CPUs and memory than available
    5. Submit the job
    6. Verify job is in PENDING state with PartitionConfig reason
    """
    log = TestLogger(RESOURCE_LIMIT_TEST_NAMES["exceed_cpu_and_memory_pending"])
    job_ids = []

    # Set up test environment
    env_result = setup_resource_limit_test_env()
    assert env_result["success"], env_result["error"]
    login_ip = env_result["login_ip"]
    log.passed(f"Using login node: {login_ip}")

    try:
        # Get cluster resources
        resources = get_cluster_resources(login_ip)
        assert resources["success"], RESOURCE_LIMIT_ASSERT_MSGS["sinfo_failed"].format(error=resources["error"])
        log.passed(RESOURCE_LIMIT_LOG_MSGS["cluster_resources"].format(
            node=resources["node"],
            cpus=resources["cpus"],
            memory_mb=resources["memory_mb"]
        ))

        # Request more CPUs and memory than available
        requested_cpus = resources["cpus"] + 1
        requested_memory_mb = resources["memory_mb"] + 2048
        log.check(f"Requesting {requested_cpus} CPUs (available: {resources['cpus']}) and "
                  f"{requested_memory_mb}MB memory (available: {resources['memory_mb']}MB)")

        # Create job script
        script_result = create_resource_job_script(
            login_ip, "root",
            cpus=requested_cpus,
            memory_mb=requested_memory_mb,
            job_name="exceed_cpu_mem_test"
        )
        assert script_result["success"], RESOURCE_LIMIT_ASSERT_MSGS["job_script_failed"].format(
            error=script_result["error"]
        )
        log.passed(RESOURCE_LIMIT_LOG_MSGS["job_script_created"].format(
            cpus=requested_cpus, memory=requested_memory_mb
        ))

        # Submit job
        submit_result = submit_resource_job_script(login_ip)
        assert submit_result["success"], RESOURCE_LIMIT_ASSERT_MSGS["submit_failed"].format(
            error=submit_result["error"]
        )
        job_id = submit_result["job_id"]
        job_ids.append(job_id)
        log.passed(RESOURCE_LIMIT_LOG_MSGS["job_submitted"].format(job_id=job_id))

        # Check job state - should be PENDING with PartitionConfig reason
        state_result = poll_job_state_direct(login_ip, "root", job_id, timeout=30)
        state = state_result.get("state", "")
        reason = state_result.get("reason", "")

        assert state == "PENDING", RESOURCE_LIMIT_ASSERT_MSGS["job_not_pending"].format(
            job_id=job_id, state=state
        )
        log.passed(RESOURCE_LIMIT_LOG_MSGS["job_pending"].format(job_id=job_id, reason=reason))

        # Verify reason contains PartitionConfig
        assert "PartitionConfig" in reason or "ReqNodeNotAvail" in reason, \
            RESOURCE_LIMIT_ASSERT_MSGS["wrong_pending_reason"].format(job_id=job_id, reason=reason)
        log.passed(f"Job {job_id} has correct pending reason: {reason}")

    finally:
        cleanup_resource_test(login_ip, "root", job_ids)
