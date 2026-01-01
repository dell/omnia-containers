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
Testinfra tests for insufficient_resources verification.

This file contains test functions that verify Slurm handles job submissions
with insufficient resources correctly (PENDING with valid reason or rejected).

Usage:
    ./run_molecule.sh slurm/insufficient_resources test      # Run playbook + verify
    ./run_molecule.sh slurm/insufficient_resources verify    # Verify only
"""

import pytest
from automation_library.core import TestLogger
from automation_library.slurm.vars.insufficient_resources_vars import (
    INSUFFICIENT_RESOURCES_VARS,
    RESOURCE_PENDING_REASONS,
    RESOURCE_REJECTION_ERRORS,
)
from automation_library.slurm.messages.insufficient_resources_msgs import (
    TEST_VARS, TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS
)
from automation_library.slurm.functions.insufficient_resources_func import (
    get_cluster_resources,
    submit_job_with_excessive_cpus,
    submit_job_with_excessive_memory,
    submit_job_with_gpus,
    get_job_state,
    validate_insufficient_resource_response,
    cancel_slurm_jobs,
    check_slurmctld_running,
    get_ssh_host,
)


# =============================================================================
# FIXTURE: SSH HOST TO SLURM CONTROL NODE
# =============================================================================

@pytest.fixture(scope="module")
def slurm_host():
    """Get SSH host connected to Slurm control node via omnia_core."""
    return get_ssh_host()


# =============================================================================
# SLURMCTLD TESTS
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


# =============================================================================
# CLUSTER RESOURCE TESTS
# =============================================================================

def test_cluster_resources(slurm_host):
    """Verify cluster resources can be retrieved."""
    log = TestLogger(TEST_NAMES["cluster_resources"])
    log.check("Getting cluster resource information")

    result = get_cluster_resources(slurm_host)

    if result["success"]:
        log.passed(
            LOG_MSGS["cluster_resources_retrieved"],
            f"Max CPUs: {result['max_cpus']}, Max Memory: {result['max_memory']}MB"
        )
        for node in result["nodes"][:5]:
            log.check(LOG_MSGS["node_resources"].format(
                name=node["name"],
                cpus=node["cpus"],
                memory=node["memory"]
            ))
    else:
        log.failed("Failed to get cluster resources", result["error"])

    assert result["success"], f"Failed to get cluster resources: {result['error']}"


# =============================================================================
# EXCESSIVE CPU TESTS
# =============================================================================

def test_excessive_cpu_request(slurm_host):
    """Verify job with excessive CPU request is handled correctly."""
    log = TestLogger(TEST_NAMES["excessive_cpu"])
    log.check("Submitting job with excessive CPU request")

    # Get cluster resources first
    resources = get_cluster_resources(slurm_host)
    if not resources["success"]:
        log.failed("Cannot get cluster resources", resources["error"])
        assert False, "Cannot get cluster resources"

    max_cpus = resources["max_cpus"]
    excessive_cpus = max_cpus * 10
    log.check(f"Max CPUs: {max_cpus}, Requesting: {excessive_cpus}")

    # Submit job with excessive CPUs
    result = submit_job_with_excessive_cpus(slurm_host, excessive_cpus)

    # Validate response
    validation = validate_insufficient_resource_response(result)

    if validation["valid"]:
        if validation["response_type"] == "pending":
            log.passed(
                LOG_MSGS["job_pending_resources"].format(reason=validation["reason"]),
                f"Job ID: {result.get('job_id', 'N/A')}"
            )
        elif validation["response_type"] == "rejected":
            log.passed(
                LOG_MSGS["job_rejected"].format(error=validation["error"]),
                "Job correctly rejected"
            )
    else:
        log.failed(LOG_MSGS["unexpected_response"], validation["details"])

    # Cleanup if job was submitted
    if result.get("job_id"):
        cancel_slurm_jobs(slurm_host, [result["job_id"]])

    assert validation["valid"], ASSERT_MSGS["invalid_resource_response"].format(
        details=validation["details"]
    )


# =============================================================================
# EXCESSIVE MEMORY TESTS
# =============================================================================

def test_excessive_memory_request(slurm_host):
    """Verify job with excessive memory request is handled correctly."""
    log = TestLogger(TEST_NAMES["excessive_memory"])
    log.check("Submitting job with excessive memory request")

    # Get cluster resources first
    resources = get_cluster_resources(slurm_host)
    if not resources["success"]:
        log.failed("Cannot get cluster resources", resources["error"])
        assert False, "Cannot get cluster resources"

    max_memory = resources["max_memory"]
    excessive_memory = max_memory * 10
    log.check(f"Max Memory: {max_memory}MB, Requesting: {excessive_memory}MB")

    # Submit job with excessive memory
    result = submit_job_with_excessive_memory(slurm_host, excessive_memory)

    # Validate response
    validation = validate_insufficient_resource_response(result)

    if validation["valid"]:
        if validation["response_type"] == "pending":
            log.passed(
                LOG_MSGS["job_pending_resources"].format(reason=validation["reason"]),
                f"Job ID: {result.get('job_id', 'N/A')}"
            )
        elif validation["response_type"] == "rejected":
            log.passed(
                LOG_MSGS["job_rejected"].format(error=validation["error"]),
                "Job correctly rejected"
            )
    else:
        log.failed(LOG_MSGS["unexpected_response"], validation["details"])

    # Cleanup if job was submitted
    if result.get("job_id"):
        cancel_slurm_jobs(slurm_host, [result["job_id"]])

    assert validation["valid"], ASSERT_MSGS["invalid_resource_response"].format(
        details=validation["details"]
    )


# =============================================================================
# GPU RESOURCE TESTS
# =============================================================================

def test_gpu_request_unavailable(slurm_host):
    """Verify job requesting unavailable GPUs is handled correctly."""
    log = TestLogger(TEST_NAMES["gpu_unavailable"])
    log.check("Submitting job requesting GPUs")

    # Request excessive GPUs (100)
    result = submit_job_with_gpus(slurm_host, gpu_count=100)

    # Validate response
    validation = validate_insufficient_resource_response(result)

    if validation["valid"]:
        if validation["response_type"] == "pending":
            log.passed(
                LOG_MSGS["job_pending_resources"].format(reason=validation["reason"]),
                f"Job ID: {result.get('job_id', 'N/A')}"
            )
        elif validation["response_type"] == "rejected":
            log.passed(
                LOG_MSGS["job_rejected"].format(error=validation["error"]),
                "Job correctly rejected - GPUs not available"
            )
    else:
        log.failed(LOG_MSGS["unexpected_response"], validation["details"])

    # Cleanup if job was submitted
    if result.get("job_id"):
        cancel_slurm_jobs(slurm_host, [result["job_id"]])

    assert validation["valid"], ASSERT_MSGS["invalid_resource_response"].format(
        details=validation["details"]
    )


# =============================================================================
# COMBINED EXCESSIVE RESOURCE TESTS
# =============================================================================

def test_excessive_cpu_and_memory(slurm_host):
    """Verify job with both excessive CPU and memory is handled correctly."""
    log = TestLogger(TEST_NAMES["excessive_cpu_memory"])
    log.check("Submitting job with excessive CPU and memory")

    # Get cluster resources
    resources = get_cluster_resources(slurm_host)
    if not resources["success"]:
        log.failed("Cannot get cluster resources", resources["error"])
        assert False, "Cannot get cluster resources"

    excessive_cpus = resources["max_cpus"] * 10
    excessive_memory = resources["max_memory"] * 10

    log.check(f"Requesting: {excessive_cpus} CPUs, {excessive_memory}MB memory")

    # Submit job with both excessive resources
    cmd = slurm_host.run(
        f"sbatch --job-name=test_excess_both --cpus-per-task={excessive_cpus} "
        f"--mem={excessive_memory} --time=00:01:00 --wrap='hostname' 2>&1"
    )

    result = {
        "success": cmd.rc == 0,
        "stdout": cmd.stdout,
        "stderr": cmd.stderr,
        "rc": cmd.rc,
        "job_id": None
    }

    # Parse job ID if submitted
    import re
    match = re.search(r'Submitted batch job (\d+)', cmd.stdout)
    if match:
        result["job_id"] = match.group(1)

    # Validate response
    validation = validate_insufficient_resource_response(result)

    if validation["valid"]:
        log.passed(
            f"Job handled correctly: {validation['response_type']}",
            validation["details"]
        )
    else:
        log.failed(LOG_MSGS["unexpected_response"], validation["details"])

    # Cleanup
    if result.get("job_id"):
        cancel_slurm_jobs(slurm_host, [result["job_id"]])

    assert validation["valid"], ASSERT_MSGS["invalid_resource_response"].format(
        details=validation["details"]
    )
