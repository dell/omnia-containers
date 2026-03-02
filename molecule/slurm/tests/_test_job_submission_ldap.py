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

"""Slurm job submission tests from login nodes as LDAP user (via omnia_core)."""

import pytest

from automation_library.core import TestLogger
from automation_library.core.host import get_testinfra_host, load_user_config, get_all_node_admin_ips, file_operation
from automation_library.slurm.messages import (
    LDAP_TEST_NAMES as TEST_NAMES,
    LDAP_LOG_MSGS as LOG_MSGS,
    LDAP_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.slurm.functions import (
    run_ssh_as_user,
    get_job_script_path,
    submit_ldap_job,
    wait_ldap_job_complete,
    read_ldap_job_output,
    submit_and_verify_ldap_job,
    discover_ldap_user_from_node,
    check_job_scontrol,
    is_node_reachable,
)

_config = load_user_config()
LDAP_USERNAME = _config.get("ldap_username", "ldapuser")
LDAP_PASSWORD = _config.get("ldap_password", "ninja")


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def job_script_content():
    """Read job.sh from automation_library/job.sh."""
    result = file_operation(None, "", task="read", source=get_job_script_path())
    assert result["success"], ASSERT_MSGS["job_script_not_found"].format(path=result.get("details", ""))
    return result["content"]


# =============================================================================
# TESTS
# =============================================================================

def test_ldap_login_to_login_node():
    """Verify SSH login to login node as LDAP user and confirm whoami."""
    log = TestLogger(TEST_NAMES["ldap_login_to_login_node"])
    oim_host = get_testinfra_host()

    login_ips = get_all_node_admin_ips(oim_host, functional_group="login_node_x86_64")
    assert login_ips, ASSERT_MSGS["no_login_ips"]

    for ip in login_ips:
        assert is_node_reachable(oim_host, ip), f"Login node {ip} is unreachable"

    for login_ip in login_ips:
        log.check(LOG_MSGS["ssh_login_attempt"].format(login_ip=login_ip, user=LDAP_USERNAME))
        res = run_ssh_as_user(oim_host, login_ip, LDAP_USERNAME, "whoami", password=LDAP_PASSWORD)
        assert res.rc == 0, ASSERT_MSGS["ssh_login_failed"].format(
            login_ip=login_ip, user=LDAP_USERNAME, error=res.stderr or res.stdout
        )
        log.passed(LOG_MSGS["ssh_login_ok"].format(login_ip=login_ip, user=LDAP_USERNAME))

        whoami = res.stdout.strip()
        log.check(f"Verifying whoami output matches {LDAP_USERNAME}")
        assert whoami == LDAP_USERNAME, ASSERT_MSGS["ssh_whoami_mismatch"].format(
            login_ip=login_ip, user=LDAP_USERNAME, whoami=whoami
        )
        log.passed(f"whoami confirmed: {whoami} (rc={res.rc})")


def test_ldap_login_to_login_compiler_node():
    """Verify SSH login to login compiler node as LDAP user and confirm whoami."""
    log = TestLogger(TEST_NAMES["ldap_login_to_compiler_node"])
    oim_host = get_testinfra_host()

    login_compiler_ips = get_all_node_admin_ips(oim_host, functional_group="login_compiler")
    assert login_compiler_ips, ASSERT_MSGS["no_compiler_ips"]

    for ip in login_compiler_ips:
        assert is_node_reachable(oim_host, ip), f"Login compiler node {ip} is unreachable"

    for login_ip in login_compiler_ips:
        log.check(LOG_MSGS["ssh_login_attempt"].format(login_ip=login_ip, user=LDAP_USERNAME))
        res = run_ssh_as_user(oim_host, login_ip, LDAP_USERNAME, "whoami", password=LDAP_PASSWORD)
        assert res.rc == 0, ASSERT_MSGS["ssh_login_failed"].format(
            login_ip=login_ip, user=LDAP_USERNAME, error=res.stderr or res.stdout
        )
        log.passed(LOG_MSGS["ssh_login_ok"].format(login_ip=login_ip, user=LDAP_USERNAME))

        whoami = res.stdout.strip()
        log.check(f"Verifying whoami output matches {LDAP_USERNAME}")
        assert whoami == LDAP_USERNAME, ASSERT_MSGS["ssh_whoami_mismatch"].format(
            login_ip=login_ip, user=LDAP_USERNAME, whoami=whoami
        )
        log.passed(f"whoami confirmed: {whoami} (rc={res.rc})")


def test_submit_job_as_ldap_user_via_login_from_omnia_core(
    job_script_content
):
    """E2E: Submit job.sh from a login node as LDAP user via omnia_core and verify output."""
    log = TestLogger(TEST_NAMES["ldap_submit_via_login"])
    oim_host = get_testinfra_host()

    login_ips = get_all_node_admin_ips(oim_host, functional_group="login_node_x86_64")
    assert login_ips, ASSERT_MSGS["no_login_ips"]
    login_ip = login_ips[0]
    assert is_node_reachable(oim_host, login_ip), f"Login node {login_ip} is unreachable"

    log.check(f"Using login node {login_ip}, user {LDAP_USERNAME}")
    log.passed(LOG_MSGS["login_ip_found"].format(login_ip=login_ip))

    log.check("Creating job.sh on login node")
    result = file_operation(
        oim_host, login_ip, task="copy",
        source=job_script_content, destination=f"/home/{LDAP_USERNAME}",
        user=LDAP_USERNAME, password=LDAP_PASSWORD
    )
    assert result["success"], ASSERT_MSGS["script_create_failed"].format(
        login_ip=login_ip, user=LDAP_USERNAME, error=result["error"]
    )
    log.passed(LOG_MSGS["job_script_created"].format(login_ip=login_ip, user=LDAP_USERNAME))

    log.check("Submitting job via sbatch")
    result = submit_ldap_job(oim_host, login_ip, LDAP_USERNAME, password=LDAP_PASSWORD)
    assert result["success"], ASSERT_MSGS["sbatch_failed"].format(
        login_ip=login_ip, user=LDAP_USERNAME, error=result["error"]
    )
    job_id = result["job_id"]
    assert job_id, ASSERT_MSGS["job_id_missing"].format(output=result["output"])
    log.passed(LOG_MSGS["job_submitted"].format(job_id=job_id, login_ip=login_ip, user=LDAP_USERNAME))

    log.check(f"Waiting for job {job_id} to complete")
    wait_result = wait_ldap_job_complete(oim_host, login_ip, LDAP_USERNAME, job_id, timeout=120, password=LDAP_PASSWORD)
    assert wait_result["completed"], ASSERT_MSGS["squeue_failed"].format(
        job_id=job_id, error=wait_result["error"]
    )
    log.passed(LOG_MSGS["job_waiting"].format(job_id=job_id))

    scontrol_result = check_job_scontrol(oim_host, login_ip, job_id)
    assert scontrol_result["success"], f"Job {job_id} did not reach terminal state: {scontrol_result.get('error', 'timeout')}"
    assert scontrol_result["state"] == "COMPLETED", f"Job {job_id} expected COMPLETED but got {scontrol_result['state']}"
    log.passed(f"Job {job_id} completed successfully (state: {scontrol_result['state']})")

    log.check("Verifying job output")
    output_result = read_ldap_job_output(oim_host, login_ip, LDAP_USERNAME, password=LDAP_PASSWORD)
    assert output_result["success"], ASSERT_MSGS["output_read_failed"].format(
        login_ip=login_ip, user=LDAP_USERNAME, error=output_result["error"]
    )
    log.passed(f"output.txt: {output_result['output']}")
    assert "Job completed" in output_result["output"], ASSERT_MSGS["output_missing_text"].format(
        login_ip=login_ip, user=LDAP_USERNAME
    )
    log.passed(LOG_MSGS["job_completed"].format(job_id=job_id))

    file_operation(
        oim_host, login_ip, task="delete",
        destination=f"/home/{LDAP_USERNAME}",
        user=LDAP_USERNAME, password=LDAP_PASSWORD
    )
    log.passed(LOG_MSGS["cleanup"].format(login_ip=login_ip))


def test_submit_multiple_jobs_as_ldap_user(
    job_script_content
):
    """Submit multiple jobs as LDAP user from login and login compiler nodes."""
    log = TestLogger(TEST_NAMES["ldap_submit_multiple"])
    oim_host = get_testinfra_host()

    login_ips = get_all_node_admin_ips(oim_host, functional_group="login_node_x86_64")
    login_compiler_ips = get_all_node_admin_ips(oim_host, functional_group="login_compiler")

    if not login_ips and not login_compiler_ips:
        pytest.skip("No login or login compiler IPs available")

    for ip in login_ips:
        assert is_node_reachable(oim_host, ip), f"Login node {ip} is unreachable"
    for ip in login_compiler_ips:
        assert is_node_reachable(oim_host, ip), f"Login compiler node {ip} is unreachable"

    if login_ips:
        login_ip = login_ips[0]
        log.check(f"Submitting 2 jobs on login node {login_ip}")
        for i in range(2):
            result = submit_and_verify_ldap_job(
                oim_host, login_ip, LDAP_USERNAME, job_script_content, password=LDAP_PASSWORD
            )
            assert result["success"], ASSERT_MSGS["e2e_failed"].format(
                login_ip=login_ip, user=LDAP_USERNAME, error=result["error"]
            )
            scontrol_result = check_job_scontrol(oim_host, login_ip, result['job_id'])
            assert scontrol_result["success"], f"Job {result['job_id']} did not reach terminal state: {scontrol_result.get('error', 'timeout')}"
            assert scontrol_result["state"] == "COMPLETED", f"Job {result['job_id']} expected COMPLETED but got {scontrol_result['state']}"
            log.passed(f"Job {result['job_id']} completed successfully (state: {scontrol_result['state']})")
        log.passed(LOG_MSGS["multi_login_done"].format(count=2, login_ip=login_ip))

    if login_compiler_ips:
        compiler_ip = login_compiler_ips[0]
        log.check(f"Submitting 1 job on compiler node {compiler_ip}")
        result = submit_and_verify_ldap_job(
            oim_host, compiler_ip, LDAP_USERNAME, job_script_content, password=LDAP_PASSWORD
        )
        assert result["success"], ASSERT_MSGS["e2e_failed"].format(
            login_ip=compiler_ip, user=LDAP_USERNAME, error=result["error"]
        )
        scontrol_result = check_job_scontrol(oim_host, compiler_ip, result['job_id'])
        assert scontrol_result["success"], f"Job {result['job_id']} did not reach terminal state: {scontrol_result.get('error', 'timeout')}"
        assert scontrol_result["state"] == "COMPLETED", f"Job {result['job_id']} expected COMPLETED but got {scontrol_result['state']}"
        log.passed(f"Job {result['job_id']} completed successfully (state: {scontrol_result['state']})")
        log.passed(LOG_MSGS["multi_compiler_done"].format(login_ip=compiler_ip))


def test_submit_job_as_ldap_user_via_login_compiler_node(
    job_script_content
):
    """E2E: Submit job.sh from a login compiler node as LDAP user via omnia_core and verify output."""
    log = TestLogger(TEST_NAMES["ldap_submit_via_compiler"])
    oim_host = get_testinfra_host()

    login_compiler_ips = get_all_node_admin_ips(oim_host, functional_group="login_compiler")
    assert login_compiler_ips, ASSERT_MSGS["no_compiler_ips"]
    login_ip = login_compiler_ips[0]
    assert is_node_reachable(oim_host, login_ip), f"Login compiler node {login_ip} is unreachable"

    log.check(f"Using login compiler node {login_ip}, user {LDAP_USERNAME}")
    log.passed(LOG_MSGS["compiler_ip_found"].format(login_ip=login_ip))

    log.check("Creating job.sh on compiler node")
    result = file_operation(
        oim_host, login_ip, task="copy",
        source=job_script_content, destination=f"/home/{LDAP_USERNAME}",
        user=LDAP_USERNAME, password=LDAP_PASSWORD
    )
    assert result["success"], ASSERT_MSGS["script_create_failed"].format(
        login_ip=login_ip, user=LDAP_USERNAME, error=result["error"]
    )
    log.passed(LOG_MSGS["job_script_created"].format(login_ip=login_ip, user=LDAP_USERNAME))

    log.check("Submitting job via sbatch")
    result = submit_ldap_job(oim_host, login_ip, LDAP_USERNAME, password=LDAP_PASSWORD)
    assert result["success"], ASSERT_MSGS["sbatch_failed"].format(
        login_ip=login_ip, user=LDAP_USERNAME, error=result["error"]
    )
    job_id = result["job_id"]
    assert job_id, ASSERT_MSGS["job_id_missing"].format(output=result["output"])
    log.passed(LOG_MSGS["job_submitted"].format(job_id=job_id, login_ip=login_ip, user=LDAP_USERNAME))

    log.check(f"Waiting for job {job_id} to complete")
    wait_result = wait_ldap_job_complete(oim_host, login_ip, LDAP_USERNAME, job_id, timeout=120, password=LDAP_PASSWORD)
    assert wait_result["completed"], ASSERT_MSGS["squeue_failed"].format(
        job_id=job_id, error=wait_result["error"]
    )
    log.passed(LOG_MSGS["job_waiting"].format(job_id=job_id))

    scontrol_result = check_job_scontrol(oim_host, login_ip, job_id)
    assert scontrol_result["success"], f"Job {job_id} did not reach terminal state: {scontrol_result.get('error', 'timeout')}"
    assert scontrol_result["state"] == "COMPLETED", f"Job {job_id} expected COMPLETED but got {scontrol_result['state']}"
    log.passed(f"Job {job_id} completed successfully (state: {scontrol_result['state']})")

    log.check("Verifying job output")
    output_result = read_ldap_job_output(oim_host, login_ip, LDAP_USERNAME, password=LDAP_PASSWORD)
    assert output_result["success"], ASSERT_MSGS["output_read_failed"].format(
        login_ip=login_ip, user=LDAP_USERNAME, error=output_result["error"]
    )
    log.passed(f"output.txt: {output_result['output']}")
    assert "Job completed" in output_result["output"], ASSERT_MSGS["output_missing_text"].format(
        login_ip=login_ip, user=LDAP_USERNAME
    )
    log.passed(LOG_MSGS["job_completed"].format(job_id=job_id))

    file_operation(
        oim_host, login_ip, task="delete",
        destination=f"/home/{LDAP_USERNAME}",
        user=LDAP_USERNAME, password=LDAP_PASSWORD
    )
    log.passed(LOG_MSGS["cleanup"].format(login_ip=login_ip))


def test_submit_job_from_multiple_login_nodes_as_ldap_user(
    job_script_content
):
    """E2E: Submit job.sh from all login nodes as LDAP user and verify output."""
    log = TestLogger(TEST_NAMES["ldap_multi_node_submission"])
    oim_host = get_testinfra_host()

    login_ips = get_all_node_admin_ips(oim_host, functional_group="login_node_x86_64")
    assert login_ips, ASSERT_MSGS["no_login_ips"]

    for ip in login_ips:
        assert is_node_reachable(oim_host, ip), f"Login node {ip} is unreachable"

    log.check(f"Login node IPs: {login_ips}")

    for login_ip in login_ips:
        log.check(f"Submitting job on {login_ip} as {LDAP_USERNAME}")

        result = file_operation(
            oim_host, login_ip, task="copy",
            source=job_script_content, destination=f"/home/{LDAP_USERNAME}",
            user=LDAP_USERNAME, password=LDAP_PASSWORD
        )
        assert result["success"], \
            ASSERT_MSGS["script_create_failed"].format(
                login_ip=login_ip, user=LDAP_USERNAME,
                error=result["error"]
            )
        log.passed(
            LOG_MSGS["job_script_created"].format(
                login_ip=login_ip, user=LDAP_USERNAME
            )
        )

        result = submit_ldap_job(
            oim_host, login_ip, LDAP_USERNAME,
            password=LDAP_PASSWORD
        )
        assert result["success"], \
            ASSERT_MSGS["sbatch_failed"].format(
                login_ip=login_ip, user=LDAP_USERNAME,
                error=result["error"]
            )
        job_id = result["job_id"]
        assert job_id, \
            ASSERT_MSGS["job_id_missing"].format(output=result["output"])
        log.passed(
            LOG_MSGS["job_submitted"].format(
                job_id=job_id, login_ip=login_ip, user=LDAP_USERNAME
            )
        )

        wait_result = wait_ldap_job_complete(
            oim_host, login_ip, LDAP_USERNAME, job_id,
            timeout=120, password=LDAP_PASSWORD
        )
        assert wait_result["completed"], \
            ASSERT_MSGS["squeue_failed"].format(
                job_id=job_id, error=wait_result["error"]
            )
        log.passed(LOG_MSGS["job_waiting"].format(job_id=job_id))

        scontrol_result = check_job_scontrol(oim_host, login_ip, job_id)
        assert scontrol_result["success"], f"Job {job_id} did not reach terminal state: {scontrol_result.get('error', 'timeout')}"
        assert scontrol_result["state"] == "COMPLETED", f"Job {job_id} expected COMPLETED but got {scontrol_result['state']}"
        log.passed(f"Job {job_id} completed successfully (state: {scontrol_result['state']})")

        output_result = read_ldap_job_output(
            oim_host, login_ip, LDAP_USERNAME,
            password=LDAP_PASSWORD
        )
        assert output_result["success"], \
            ASSERT_MSGS["output_read_failed"].format(
                login_ip=login_ip, user=LDAP_USERNAME,
                error=output_result["error"]
            )
        log.passed(f"output.txt: {output_result['output']}")
        assert "Job completed" in output_result["output"], \
            ASSERT_MSGS["output_missing_text"].format(
                login_ip=login_ip, user=LDAP_USERNAME
            )
        log.passed(LOG_MSGS["job_completed"].format(job_id=job_id))

        file_operation(
            oim_host, login_ip, task="delete",
            destination=f"/home/{LDAP_USERNAME}",
            user=LDAP_USERNAME, password=LDAP_PASSWORD
        )
        log.passed(LOG_MSGS["cleanup"].format(login_ip=login_ip))
