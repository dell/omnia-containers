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
- Single E2E Job Submission from login node using external IP/Inetrnal IP as root user
- multiple job submissions from login node as root user
- Submissions from multiple login nodes as root user

Configuration (env-driven + PXE mapping discovery):
- Preferred: derive login node admin IPs from pxe_mapping_file via _get_pxe_mapping_content
- Fallback: LOGIN_NODE_IPS env (comma-separated login node IPs)
- SSH_KEY_PATH: optional private key path for SSH auth; passwordless assumed if unset
"""

import os

import pytest

from automation_library.core.host import get_testinfra_host
from automation_library.slurm.vars import (
    MULTI_JOB_COUNT,
    parse_login_ips_from_env,
    parse_login_ips_from_pxe_mapping,
)
from automation_library.slurm.messages import (
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)
from automation_library.slurm.functions import (
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
def _login_ips():
    """Collect login IPs from PXE mapping or env; skip tests if none available."""
    ips = parse_login_ips_from_pxe_mapping()
    if not ips:
        ips = parse_login_ips_from_env()
    if not ips:
        pytest.skip(TEST_ASSERT_MSGS["no_login_ips"])
    return ips


@pytest.fixture(scope="session")
def _ssh_key_path():
    """Return SSH key path from env if provided."""
    return os.environ.get("SSH_KEY_PATH") or None


# =============================================================================
# TESTS
# =============================================================================

def test_submit_single_job_via_login_from_omnia_core(_login_ips, _ssh_key_path):
    """E2E: OIM -> omnia_core -> login node, submit job.sh and verify output.
    Job is submitted both from external IP or  Internal IP"""

    # Step 1: Find a reachable login node
    oim_host = get_testinfra_host()
    result = find_reachable_login_node(oim_host, _login_ips, _ssh_key_path)
    for ip in result["skipped"]:
        print(f"  {TEST_LOG_MSGS['login_node_unreachable'].format(login_ip=ip)}")
    assert result["success"], TEST_ASSERT_MSGS["no_reachable_nodes"].format(login_ips=_login_ips)
    login_ip = result["login_ip"]
    print(f"Step 1: {TEST_LOG_MSGS['login_node_found'].format(login_ip=login_ip)}")

    # Step 2: Read job.sh from the project folder and copy to /home
    script_result = read_job_script()
    assert script_result["success"], TEST_ASSERT_MSGS["job_script_not_found"].format(
        path=script_result["path"]
    )
    print(f"Step 2: {TEST_LOG_MSGS['job_script_read'].format(path=script_result['path'])}")

    copy_result = copy_job_script_to_login(oim_host, login_ip, script_result["content"], _ssh_key_path)
    assert copy_result["success"], TEST_ASSERT_MSGS["job_script_copy_failed"].format(
        login_ip=login_ip, error=copy_result["error"]
    )
    print(f"  {TEST_LOG_MSGS['job_script_copied'].format(login_ip=login_ip)}")

    # Step 3: Run sbatch job.sh
    submit_result = submit_job_via_login(oim_host, login_ip, _ssh_key_path)
    assert submit_result["success"], TEST_ASSERT_MSGS["sbatch_failed"].format(
        login_ip=login_ip, error=submit_result["error"]
    )
    job_id = submit_result["job_id"]
    print(f"Step 3: {TEST_LOG_MSGS['sbatch_success']} -> output: {submit_result['output']}")

    # Step 4: Verify job is submitted with job_id generated
    print(f"Step 4: {TEST_LOG_MSGS['job_submitted'].format(job_id=job_id)}")

    # Step 5: Run squeue -j <job_id>
    queue_result = check_squeue(oim_host, login_ip, job_id, _ssh_key_path)
    assert queue_result["success"], TEST_ASSERT_MSGS["squeue_failed"].format(
        job_id=job_id, error=queue_result["error"]
    )
    print(f"Step 5: {TEST_LOG_MSGS['squeue_success'].format(job_id=job_id)}\n{queue_result['output']}")


def test_submit_multiple_jobs_via_login_from_omnia_core(_login_ips, _ssh_key_path):
    """Submit multiple jobs sequentially from login node read from pxe_mapping file."""

    # Step 1: Find a reachable login node
    oim_host = get_testinfra_host()
    result = find_reachable_login_node(oim_host, _login_ips, _ssh_key_path)
    for ip in result["skipped"]:
        print(f"  {TEST_LOG_MSGS['login_node_unreachable'].format(login_ip=ip)}")
    assert result["success"], TEST_ASSERT_MSGS["no_reachable_nodes"].format(login_ips=_login_ips)
    login_ip = result["login_ip"]
    print(f"Step 1: {TEST_LOG_MSGS['login_node_found'].format(login_ip=login_ip)}")

    # Step 2: Read and copy job.sh
    script_result = read_job_script()
    assert script_result["success"], TEST_ASSERT_MSGS["job_script_not_found"].format(
        path=script_result["path"]
    )

    copy_result = copy_job_script_to_login(oim_host, login_ip, script_result["content"], _ssh_key_path)
    assert copy_result["success"], TEST_ASSERT_MSGS["job_script_copy_failed"].format(
        login_ip=login_ip, error=copy_result["error"]
    )
    print(f"Step 2: {TEST_LOG_MSGS['job_script_copied'].format(login_ip=login_ip)}")

    # Step 3 & 4: Submit multiple jobs sequentially and verify each is submitted with job id
    print(f"Step 3 & 4: Submitting {MULTI_JOB_COUNT} jobs sequentially...")
    for i in range(MULTI_JOB_COUNT):
        submit_result = submit_job_via_login(oim_host, login_ip, _ssh_key_path)
        assert submit_result["success"], TEST_ASSERT_MSGS["sbatch_failed"].format(
            login_ip=login_ip, error=submit_result["error"]
        )
        print(f"  Job {i+1}/{MULTI_JOB_COUNT}: {TEST_LOG_MSGS['job_submitted'].format(job_id=submit_result['job_id'])}")


def test_job_submission_from_multiple_login_nodes(_login_ips, _ssh_key_path):
    """E2E: Submit job.sh from all login nodes listed in pxe_mapping file and verify submission."""

    # Step 1: Read login node IPs from pxe_mapping file (provided by login_ips fixture)
    assert _login_ips, TEST_ASSERT_MSGS["no_login_ips"]
    print(f"Step 1: Login node IPs from pxe_mapping: {_login_ips}")

    oim_host = get_testinfra_host()

    # Read job.sh from the project folder
    script_result = read_job_script()
    assert script_result["success"], TEST_ASSERT_MSGS["job_script_not_found"].format(
        path=script_result["path"]
    )
    print(f"  {TEST_LOG_MSGS['job_script_read'].format(path=script_result['path'])}")

    reachable_count = 0
    for login_ip in _login_ips:
        print(f"\n--- Login node: {login_ip} ---")

        # Check reachability before attempting job submission
        if not is_node_reachable(oim_host, login_ip, _ssh_key_path):
            print(f"  {TEST_LOG_MSGS['login_node_unreachable'].format(login_ip=login_ip)}")
            continue

        reachable_count += 1

        # Step 2: Copy job.sh to /home directory
        copy_result = copy_job_script_to_login(oim_host, login_ip, script_result["content"], _ssh_key_path)
        assert copy_result["success"], TEST_ASSERT_MSGS["job_script_copy_failed"].format(
            login_ip=login_ip, error=copy_result["error"]
        )
        print(f"  Step 2: {TEST_LOG_MSGS['job_script_copied'].format(login_ip=login_ip)}")

        # Step 3: Run sbatch job.sh from each login node home directory
        submit_result = submit_job_via_login(oim_host, login_ip, _ssh_key_path)
        assert submit_result["success"], TEST_ASSERT_MSGS["sbatch_failed"].format(
            login_ip=login_ip, error=submit_result["error"]
        )
        print(f"  Step 3: {TEST_LOG_MSGS['sbatch_success']} -> output: {submit_result['output']}")

        # Step 4: Verify job is submitted successfully from each login node
        print(f"  Step 4: {TEST_LOG_MSGS['job_submitted'].format(job_id=submit_result['job_id'])}")

    assert reachable_count > 0, TEST_ASSERT_MSGS["no_reachable_nodes"].format(login_ips=_login_ips)
