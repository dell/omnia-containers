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
from automation_library.core.host import get_testinfra_host
from automation_library.slurm.vars import MULTI_JOB_COUNT
from automation_library.slurm.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)
from automation_library.slurm.functions import (
    parse_login_ips_from_env,
    parse_login_ips_from_pxe_mapping,
    is_node_reachable,
    find_reachable_login_node,
    read_job_script,
    copy_job_script_to_login,
    submit_job_via_login,
    check_squeue,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def login_ips():
    """Collect login IPs from PXE mapping or env; skip tests if none available."""
    ips = parse_login_ips_from_pxe_mapping()
    if not ips:
        ips = parse_login_ips_from_env()
    if not ips:
        pytest.skip(TEST_ASSERT_MSGS["no_login_ips"])
    return ips


# =============================================================================
# TESTS
# =============================================================================

def test_submit_single_job_via_login_from_omnia_core(login_ips):
    """E2E: OIM -> omnia_core -> login node, submit job.sh and verify output.
    Job is submitted both from external IP or Internal IP"""
    log = TestLogger(TEST_NAMES["single_job_submission"])
    oim_host = get_testinfra_host()

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

    script_result = read_job_script()
    assert script_result["success"], \
        TEST_ASSERT_MSGS["job_script_not_found"].format(path=script_result["path"])
    log.passed(
        TEST_LOG_MSGS["job_script_read"].format(path=script_result["path"])
    )

    copy_result = copy_job_script_to_login(
        oim_host, login_ip, script_result["content"]
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

    queue_result = check_squeue(oim_host, login_ip, job_id)
    assert queue_result["success"], \
        TEST_ASSERT_MSGS["squeue_failed"].format(
            job_id=job_id, error=queue_result["error"]
        )
    log.passed(
        TEST_LOG_MSGS["squeue_success"].format(job_id=job_id)
    )


def test_submit_multiple_jobs_via_login_from_omnia_core(login_ips):
    """Submit multiple jobs sequentially from login node read from pxe_mapping file."""
    log = TestLogger(TEST_NAMES["multiple_job_submission"])
    oim_host = get_testinfra_host()

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

    script_result = read_job_script()
    assert script_result["success"], \
        TEST_ASSERT_MSGS["job_script_not_found"].format(path=script_result["path"])

    copy_result = copy_job_script_to_login(
        oim_host, login_ip, script_result["content"]
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
        msg = TEST_LOG_MSGS["job_submitted"].format(
            job_id=submit_result["job_id"]
        )
        log.passed(f"Job {i+1}/{MULTI_JOB_COUNT}: {msg}")


def test_job_submission_from_multiple_login_nodes(login_ips):
    """E2E: Submit job.sh from all login nodes in pxe_mapping file."""
    log = TestLogger(TEST_NAMES["multi_node_submission"])
    assert login_ips, TEST_ASSERT_MSGS["no_login_ips"]
    log.check(f"Login node IPs from pxe_mapping: {login_ips}")

    oim_host = get_testinfra_host()

    script_result = read_job_script()
    assert script_result["success"], \
        TEST_ASSERT_MSGS["job_script_not_found"].format(path=script_result["path"])
    log.passed(
        TEST_LOG_MSGS["job_script_read"].format(path=script_result["path"])
    )

    reachable_count = 0
    for login_ip in login_ips:
        log.check(f"Testing login node: {login_ip}")

        if not is_node_reachable(oim_host, login_ip):
            log.check(
                TEST_LOG_MSGS["login_node_unreachable"].format(
                    login_ip=login_ip
                )
            )
            continue

        reachable_count += 1

        copy_result = copy_job_script_to_login(
            oim_host, login_ip, script_result["content"]
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
        log.passed(
            f"{TEST_LOG_MSGS['sbatch_success']} -> {submit_result['output']}"
        )
        log.passed(
            TEST_LOG_MSGS["job_submitted"].format(
                job_id=submit_result["job_id"]
            )
        )

    if reachable_count == 0:
        pytest.fail(
            TEST_ASSERT_MSGS["no_reachable_nodes"].format(login_ips=login_ips)
        )
