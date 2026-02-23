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
from pathlib import Path
from typing import List

import pytest

from automation_library.core.host import (
    _get_pxe_mapping_content,
    get_testinfra_host,
    run_in_container,
)


def _parse_login_ips_from_env() -> List[str]:
    """Read login node IPs from LOGIN_NODE_IPS environment variable."""
    value = os.environ.get("LOGIN_NODE_IPS", "").strip()
    if not value:
        return []
    return [ip.strip() for ip in value.split(",") if ip.strip()]


def _parse_login_ips_from_pxe_mapping() -> List[str]:
    """Extract login node admin IPs from PXE mapping file inside omnia_core."""
    host = get_testinfra_host()
    pxe_content = _get_pxe_mapping_content(host)
    if not pxe_content:
        return []

    # CSV header expected: FUNCTIONAL_GROUP_NAME,GROUP_NAME,...,HOSTNAME,ADMIN_MAC,ADMIN_IP,
    login_ips: List[str] = []
    lines = [line for line in pxe_content.split("\n") if line.strip()]
    if not lines:
        return login_ips

    for line in lines[1:]:  # skip header
        cols = line.split(",")
        if len(cols) < 7:
            continue
        functional_group = cols[0].lower()
        hostname = cols[4].lower()
        admin_ip = cols[6].strip()

        if "login" in functional_group or "login" in hostname:
            if admin_ip:
                login_ips.append(admin_ip)

    return login_ips


@pytest.fixture(scope="session")
def login_ips():
    """Collect login IPs from PXE mapping or env; skip tests if none available."""
    ips = _parse_login_ips_from_pxe_mapping()
    if not ips:
        ips = _parse_login_ips_from_env()
    if not ips:
        pytest.skip(
            "No login IPs found in pxe_mapping_file and LOGIN_NODE_IPS not set; skipping tests"
        )
    return ips


@pytest.fixture(scope="session")
def ssh_key_path():
    """Return SSH key path from env if provided."""
    return os.environ.get("SSH_KEY_PATH") or None


def _is_node_reachable(oim_host, login_ip: str, key_path: str | None = None) -> bool:
    """Check if a login node is reachable via SSH from omnia_core."""
    res = _run_ssh_from_omnia_core(oim_host, login_ip, "echo ok", key_path)
    return res.rc == 0 and "ok" in res.stdout


def _run_ssh_from_omnia_core(oim_host, login_ip: str, remote_cmd: str, key_path: str | None = None):
    """Run command on login node via SSH from inside omnia_core container."""
    ssh_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    key_flag = f"-i {key_path}" if key_path else ""
    return run_in_container(
        oim_host,
        f"ssh {ssh_opts} {key_flag} root@{login_ip} '{remote_cmd}'",
    )


def test_submit_single_job_via_login_from_omnia_core(login_ips, ssh_key_path):
    """E2E: OIM -> omnia_core -> login node, submit job.sh and verify output.
    Job is submitted both from external IP or  Internal IP"""

    # Step 1: Login to one of the login nodes
    oim_host = get_testinfra_host()
    login_ip = None
    for ip in login_ips:
        if _is_node_reachable(oim_host, ip, ssh_key_path):
            login_ip = ip
            break
        print(f"  Skipping unreachable login node: {ip}")
    assert login_ip, f"No reachable login nodes found among: {login_ips}"
    print(f"Step 1: Login to login node: {login_ip}")

    # Step 2: Read job.sh from the project folder and copy to /home
    repo_root = Path(__file__).resolve().parents[3]
    job_script_path = repo_root / "automation_library" / "job.sh"
    assert job_script_path.exists(), f"job.sh not found at {job_script_path}"
    job_script = job_script_path.read_text(encoding="utf-8")
    print(f"Step 2: Read job.sh from {job_script_path}")

    create_res = _run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        "cd /home && cat > job.sh <<'EOF'\n" + job_script + "\nEOF\nchmod +x job.sh",
        ssh_key_path,
    )
    assert create_res.rc == 0, f"Failed to create job.sh: {create_res.stderr or create_res.stdout}"
    print(f"  ✔ PASS: Copied job.sh to /home on {login_ip}")

    # Step 3: Run sbatch job.sh
    submit_res = _run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        "cd /home && sbatch --parsable job.sh",
        ssh_key_path,
    )
    assert submit_res.rc == 0, f"sbatch failed: {submit_res.stderr or submit_res.stdout}"
    print(f"Step 3: Ran sbatch job.sh → output: {submit_res.stdout.strip()}")

    # Step 4: Verify job is submitted with job_id generated
    job_id = submit_res.stdout.strip().split()[0]
    assert job_id, "sbatch did not return a job id"
    assert job_id.isdigit(), f"Expected numeric job id, got: {job_id}"
    print(f"Step 4: ✔ PASS: Job submitted successfully with job_id={job_id}")

    # Step 5: Run squeue -j <job_id>
    queue_res = _run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        f"squeue -j {job_id}",
        ssh_key_path,
    )
    assert queue_res.rc == 0, f"squeue failed: {queue_res.stderr or queue_res.stdout}"
    print(f"Step 5: squeue -j {job_id} output:\n{queue_res.stdout.strip()}")


def test_submit_multiple_jobs_via_login_from_omnia_core(login_ips, ssh_key_path):
    """Submit multiple jobs sequentially from login node read from pxe_mapping file."""

    # Step 1: Login to login node read from pxe mapping file
    oim_host = get_testinfra_host()
    login_ip = None
    for ip in login_ips:
        if _is_node_reachable(oim_host, ip, ssh_key_path):
            login_ip = ip
            break
        print(f"  Skipping unreachable login node: {ip}")
    assert login_ip, f"No reachable login nodes found among: {login_ips}"
    print(f"Step 1: Login to login node: {login_ip}")

    # Read job.sh from the project folder
    repo_root = Path(__file__).resolve().parents[3]
    job_script_path = repo_root / "automation_library" / "job.sh"
    assert job_script_path.exists(), f"job.sh not found at {job_script_path}"
    job_script = job_script_path.read_text(encoding="utf-8")

    # Step 2: Copy job.sh content to login /home directory
    create_res = _run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        "cd /home && cat > job.sh <<'EOF'\n" + job_script + "\nEOF\nchmod +x job.sh",
        ssh_key_path,
    )
    assert create_res.rc == 0, f"Failed to copy job.sh to /home: {create_res.stderr or create_res.stdout}"
    print(f"Step 2: ✔ PASS: Copied job.sh to /home on {login_ip}")

    # Step 3 & 4: Submit multiple jobs sequentially and verify each is submitted with job id
    print("Step 3 & 4: Submitting 10 jobs sequentially...")
    for i in range(10):
        submit_res = _run_ssh_from_omnia_core(
            oim_host,
            login_ip,
            "cd /home && sbatch --parsable job.sh",
            ssh_key_path,
        )
        assert submit_res.rc == 0, f"sbatch failed for job {i+1}: {submit_res.stderr or submit_res.stdout}"
        job_id = submit_res.stdout.strip().split()[0]
        assert job_id, f"sbatch did not return a job id for job {i+1}"
        assert job_id.isdigit(), f"Expected numeric job id for job {i+1}, got: {job_id}"
        print(f"  Job {i+1}/10: ✔ PASS: Submitted with job_id={job_id}")

def test_job_submission_from_multiple_login_nodes(login_ips, ssh_key_path):
    """E2E: Submit job.sh from all login nodes listed in pxe_mapping file and verify submission."""

    # Step 1: Read login node IPs from pxe_mapping file (provided by login_ips fixture)
    assert login_ips, "No login node IPs found in pxe_mapping file"
    print(f"Step 1: Login node IPs from pxe_mapping: {login_ips}")

    oim_host = get_testinfra_host()

    # Read job.sh from the project folder
    repo_root = Path(__file__).resolve().parents[3]
    job_script_path = repo_root / "automation_library" / "job.sh"
    assert job_script_path.exists(), f"job.sh not found at {job_script_path}"
    job_script = job_script_path.read_text(encoding="utf-8")
    print(f"  Read job.sh from {job_script_path}")

    reachable_count = 0
    for login_ip in login_ips:
        print(f"\n--- Login node: {login_ip} ---")

        # Check reachability before attempting job submission
        if not _is_node_reachable(oim_host, login_ip, ssh_key_path):
            print(f"  ⚠ SKIP: {login_ip} is unreachable, skipping")
            continue

        reachable_count += 1

        # Step 2: Login to each login node and copy job.sh to /home directory
        create_res = _run_ssh_from_omnia_core(
            oim_host,
            login_ip,
            "cd /home && cat > job.sh <<'EOF'\n" + job_script + "\nEOF\nchmod +x job.sh",
            ssh_key_path,
        )
        assert create_res.rc == 0, f"[{login_ip}] Failed to copy job.sh to /home: {create_res.stderr or create_res.stdout}"
        print(f"  Step 2: ✔ PASS: Copied job.sh to /home on {login_ip}")

        # Step 3: Run sbatch job.sh from each login node home directory
        submit_res = _run_ssh_from_omnia_core(
            oim_host,
            login_ip,
            "cd /home && sbatch --parsable job.sh",
            ssh_key_path,
        )
        assert submit_res.rc == 0, f"[{login_ip}] sbatch failed: {submit_res.stderr or submit_res.stdout}"
        print(f"  Step 3: Ran sbatch job.sh → output: {submit_res.stdout.strip()}")

        # Step 4: Verify job is submitted successfully from each login node
        job_id = submit_res.stdout.strip().split()[0]
        assert job_id, f"[{login_ip}] sbatch did not return a job id"
        assert job_id.isdigit(), f"[{login_ip}] Expected numeric job id, got: {job_id}"
        print(f"  Step 4: ✔ PASS: Job submitted from {login_ip} with job_id={job_id}")

    assert reachable_count > 0, f"No reachable login nodes found among: {login_ips}"


