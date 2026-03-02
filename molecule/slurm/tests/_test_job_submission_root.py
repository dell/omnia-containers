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

"""Slurm job submission tests from login nodes.

Validates:
- Single E2E Job Submission from login node using external IP/Internal IP as root user
- multiple job submissions from login node as root user
- Submissions from multiple login nodes as root user

Configuration (env-driven + PXE mapping discovery):
- Preferred: derive login node admin IPs from pxe_mapping_file via public core API
- Fallback: LOGIN_NODE_IPS env (comma-separated login node IPs)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.core.host import (
    get_testinfra_host,
    get_node_admin_ip,
    get_all_node_admin_ips,
    file_operation,
)
from automation_library.slurm.vars import MULTI_JOB_COUNT
from automation_library.slurm.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)
from automation_library.slurm.functions import (
    is_node_reachable,
    find_reachable_login_node,
    get_job_script_path,
    submit_job_via_login,
    check_squeue,
    check_job_scontrol,
)
# =============================================================================
# TESTS
# =============================================================================

def test_submit_single_job_via_login_from_omnia_core():
    """E2E: OIM -> omnia_core -> login node, submit job.sh and verify job completes.

    - If only one login node exists and it is unreachable, fail the test.
    - If multiple login nodes exist and some are unreachable, skip them and
      use the first reachable node to submit the job.
    - After submission, verify that the job state reaches COMPLETED.
    """
    log = TestLogger(TEST_NAMES["single_job_submission"])
    oim_host = get_testinfra_host()

    # Discover all login node IPs from PXE mapping
    login_ips = get_all_node_admin_ips(oim_host, functional_group="login_node_x86_64")
    assert login_ips, TEST_ASSERT_MSGS["no_login_ips"]
    log.check(f"Discovered login node IPs: {login_ips}")

    # Find a reachable login node
    login_ip = None
    for ip in login_ips:
        if is_node_reachable(oim_host, ip):
            login_ip = ip
            break
        else:
            if len(login_ips) == 1:
                pytest.fail(
                    TEST_ASSERT_MSGS["no_reachable_nodes"].format(login_ips=login_ips)
                )
            log.check(TEST_LOG_MSGS["login_node_unreachable"].format(login_ip=ip))

    assert login_ip, TEST_ASSERT_MSGS["no_reachable_nodes"].format(login_ips=login_ips)
    log.passed(TEST_LOG_MSGS["login_node_found"].format(login_ip=login_ip))

    script_result = file_operation(oim_host, login_ip, task="read", source=get_job_script_path())
    assert script_result["success"], \
        TEST_ASSERT_MSGS["job_script_not_found"].format(path=script_result.get("details", ""))
    log.passed(f"Read job.sh: {script_result['details']}")

    copy_result = file_operation(
        oim_host, login_ip, task="copy",
        source=script_result["content"], destination="/home"
    )
    assert copy_result["success"], \
        TEST_ASSERT_MSGS["job_script_copy_failed"].format(
            login_ip=login_ip, error=copy_result["error"]
        )
    log.passed(
        TEST_LOG_MSGS["job_script_copied"].format(login_ip=login_ip)
    )

    submit_result = submit_job_via_login(oim_host, login_ip)
    assert submit_result["success"], \
        TEST_ASSERT_MSGS["sbatch_failed"].format(
            login_ip=login_ip, error=submit_result["error"]
        )
    job_id = submit_result["job_id"]
    log.passed(f"{TEST_LOG_MSGS['sbatch_success']} -> {submit_result['output']}")
    log.passed(TEST_LOG_MSGS["job_submitted"].format(job_id=job_id))

    # Verify job reaches COMPLETED state
    scontrol_result = check_job_scontrol(oim_host, login_ip, job_id)
    assert scontrol_result["success"], \
        TEST_ASSERT_MSGS["job_not_completed"].format(
            job_id=job_id, state=scontrol_result["state"],
            reason=scontrol_result.get("error", "timeout")
        )
    assert scontrol_result["state"] == "COMPLETED", \
        TEST_ASSERT_MSGS["job_not_completed"].format(
            job_id=job_id, state=scontrol_result["state"],
            reason="unexpected terminal state"
        )
    log.passed(f"Job {job_id} completed successfully (state: {scontrol_result['state']})")


def test_submit_multiple_jobs_via_login_from_omnia_core():
    """Submit multiple jobs sequentially from login node read from pxe_mapping file."""
    log = TestLogger(TEST_NAMES["multiple_job_submission"])
    oim_host = get_testinfra_host()

   # Discover all login node IPs from PXE mapping
    login_ips = get_all_node_admin_ips(oim_host, functional_group="login_node_x86_64")
    assert login_ips, TEST_ASSERT_MSGS["no_login_ips"]
    log.check(f"Discovered login node IPs: {login_ips}")

    result = find_reachable_login_node(oim_host, login_ips)
    for ip in result["skipped"]:
        log.check(
            TEST_LOG_MSGS["login_node_unreachable"].format(login_ip=ip)
        )
    if not result["success"]:
        pytest.fail(
            TEST_ASSERT_MSGS["no_reachable_nodes"].format(login_ips=login_ips)
        )
    login_ip = result["login_ip"]
    log.passed(
        TEST_LOG_MSGS["login_node_found"].format(login_ip=login_ip)
    )

    script_result = file_operation(oim_host, login_ip, task="read", source=get_job_script_path())
    assert script_result["success"], \
        TEST_ASSERT_MSGS["job_script_not_found"].format(path=script_result.get("details", ""))

    copy_result = file_operation(
        oim_host, login_ip, task="copy",
        source=script_result["content"], destination="/home"
    )
    assert copy_result["success"], \
        TEST_ASSERT_MSGS["job_script_copy_failed"].format(
            login_ip=login_ip, error=copy_result["error"]
        )
    log.passed(
        TEST_LOG_MSGS["job_script_copied"].format(login_ip=login_ip)
    )

    log.check(f"Submitting {MULTI_JOB_COUNT} jobs sequentially...")
    for i in range(MULTI_JOB_COUNT):
        submit_result = submit_job_via_login(
            oim_host, login_ip
        )
        assert submit_result["success"], \
            TEST_ASSERT_MSGS["sbatch_failed"].format(
                login_ip=login_ip, error=submit_result["error"]
            )
        job_id = submit_result["job_id"]
        msg = TEST_LOG_MSGS["job_submitted"].format(job_id=job_id)
        log.passed(f"Job {i+1}/{MULTI_JOB_COUNT}: {msg}")

        # Verify job reaches COMPLETED state
        scontrol_result = check_job_scontrol(oim_host, login_ip, job_id)
        assert scontrol_result["success"], \
            TEST_ASSERT_MSGS["job_not_completed"].format(
                job_id=job_id, state=scontrol_result["state"],
                reason=scontrol_result.get("error", "timeout")
            )
        assert scontrol_result["state"] == "COMPLETED", \
            TEST_ASSERT_MSGS["job_not_completed"].format(
                job_id=job_id, state=scontrol_result["state"],
                reason="unexpected terminal state"
            )
        log.passed(f"Job {i+1}/{MULTI_JOB_COUNT}: Job {job_id} completed successfully (state: {scontrol_result['state']})")


def test_job_submission_from_multiple_login_nodes():
    """E2E: Submit job.sh from all login nodes in pxe_mapping file.

    Fails if any login node is unreachable.
    """
    log = TestLogger(TEST_NAMES["multi_node_submission"])
    oim_host = get_testinfra_host()

    login_ips = get_all_node_admin_ips(oim_host, functional_group="login_node_x86_64")
    assert login_ips, TEST_ASSERT_MSGS["no_login_ips"]
    log.check(f"Login node IPs from pxe_mapping: {login_ips}")

    # Fail if any login node is unreachable
    for ip in login_ips:
        assert is_node_reachable(oim_host, ip), \
            TEST_ASSERT_MSGS["no_reachable_nodes"].format(login_ips=[ip])

    script_result = file_operation(oim_host, login_ips[0], task="read", source=get_job_script_path())
    assert script_result["success"], \
        TEST_ASSERT_MSGS["job_script_not_found"].format(path=script_result.get("details", ""))
    log.passed(f"Read job.sh: {script_result['details']}")

    for login_ip in login_ips:
        log.check(f"Testing login node: {login_ip}")

        copy_result = file_operation(
            oim_host, login_ip, task="copy",
            source=script_result["content"], destination="/home"
        )
        assert copy_result["success"], \
            TEST_ASSERT_MSGS["job_script_copy_failed"].format(
                login_ip=login_ip, error=copy_result["error"]
            )
        log.passed(
            TEST_LOG_MSGS["job_script_copied"].format(login_ip=login_ip)
        )

        submit_result = submit_job_via_login(
            oim_host, login_ip
        )
        assert submit_result["success"], \
            TEST_ASSERT_MSGS["sbatch_failed"].format(
                login_ip=login_ip, error=submit_result["error"]
            )
        job_id = submit_result["job_id"]
        log.passed(
            f"{TEST_LOG_MSGS['sbatch_success']} -> {submit_result['output']}"
        )
        log.passed(
            TEST_LOG_MSGS["job_submitted"].format(job_id=job_id)
        )

        # Verify job reaches COMPLETED state
        scontrol_result = check_job_scontrol(oim_host, login_ip, job_id)
        assert scontrol_result["success"], \
            TEST_ASSERT_MSGS["job_not_completed"].format(
                job_id=job_id, state=scontrol_result["state"],
                reason=scontrol_result.get("error", "timeout")
            )
        assert scontrol_result["state"] == "COMPLETED", \
            TEST_ASSERT_MSGS["job_not_completed"].format(
                job_id=job_id, state=scontrol_result["state"],
                reason="unexpected terminal state"
            )
        log.passed(f"Job {job_id} completed successfully on {login_ip} (state: {scontrol_result['state']})")
