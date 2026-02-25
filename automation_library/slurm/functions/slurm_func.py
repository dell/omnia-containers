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

"""
Slurm - Core Functions.

This module contains all reusable functions for slurm job submission tests.
Test functions should call these functions - all logic resides here.

Usage:
    from automation_library.slurm.functions import (
        is_node_reachable,
        run_ssh_from_omnia_core,
        copy_job_script_to_login,
        submit_job_via_login,
        check_squeue,
        find_reachable_login_node,
        read_job_script,
    )
"""
import os
import time
from typing import Dict, Any, List, Optional

import testinfra.host

from automation_library.core.host import (
    run_in_container,
    get_testinfra_host,
    get_node_admin_ip,
    get_functional_groups_from_pxe_mapping,
)
from ..vars.slurm_vars import JOB_SCRIPT_PATH


# =============================================================================
# NODE DISCOVERY & PATH HELPERS
# =============================================================================

def _get_project_root() -> str:
    """Get the project root directory."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def get_job_script_path() -> str:
    """Return absolute path to the default job script."""
    return os.path.join(_get_project_root(), JOB_SCRIPT_PATH)


def parse_login_ips_from_env() -> List[str]:
    """Read login node IPs from LOGIN_NODE_IPS environment variable."""
    value = os.environ.get("LOGIN_NODE_IPS", "").strip()
    if not value:
        return []
    return [ip.strip() for ip in value.split(",") if ip.strip()]


def parse_login_ips_from_pxe_mapping() -> List[str]:
    """Extract login node admin IPs from PXE mapping via public core API."""
    host = get_testinfra_host()
    groups = get_functional_groups_from_pxe_mapping(host)
    login_ips: List[str] = []
    for group in groups:
        if "login" in group.lower():
            ip = get_node_admin_ip(host, functional_group=group)
            if ip:
                login_ips.append(ip)
    return login_ips


def parse_login_compiler_ips_from_env() -> List[str]:
    """Read login compiler node IPs from LOGIN_COMPILER_NODE_IPS env var."""
    value = os.environ.get("LOGIN_COMPILER_NODE_IPS", "").strip()
    if not value:
        return []
    return [ip.strip() for ip in value.split(",") if ip.strip()]


def parse_login_compiler_ips_from_pxe_mapping() -> List[str]:
    """Extract login compiler node admin IPs via public core API."""
    host = get_testinfra_host()
    groups = get_functional_groups_from_pxe_mapping(host)
    compiler_ips: List[str] = []
    for group in groups:
        if "login_compiler" in group.lower():
            ip = get_node_admin_ip(host, functional_group=group)
            if ip:
                compiler_ips.append(ip)
    return compiler_ips


def parse_ldap_user_from_env() -> str:
    """Read LDAP username from LDAP_USER environment variable."""
    return os.environ.get("LDAP_USER", "").strip()


def parse_ldap_key_path_from_env() -> str:
    """Read LDAP SSH key path from LDAP_SSH_KEY_PATH environment variable."""
    return os.environ.get("LDAP_SSH_KEY_PATH", "").strip()


# =============================================================================
# SSH HELPERS
# =============================================================================

def run_ssh_from_omnia_core(
    oim_host: testinfra.host.Host,
    login_ip: str,
    remote_cmd: str,
    key_path: Optional[str] = None,
):
    """Run command on login node via SSH from inside omnia_core container.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        remote_cmd: command to execute on the login node
        key_path: optional SSH private key path

    Returns:
        Result with stdout, stderr, rc attributes
    """
    ssh_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    key_flag = f"-i {key_path}" if key_path else ""
    return run_in_container(
        oim_host,
        f"ssh {ssh_opts} {key_flag} root@{login_ip} '{remote_cmd}'",
    )


def is_node_reachable(
    oim_host: testinfra.host.Host,
    login_ip: str,
    key_path: Optional[str] = None,
) -> bool:
    """Check if a login node is reachable via SSH from omnia_core.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        key_path: optional SSH private key path

    Returns:
        True if the node responds to SSH, False otherwise
    """
    res = run_ssh_from_omnia_core(oim_host, login_ip, "echo ok", key_path)
    return res.rc == 0 and "ok" in res.stdout


def find_reachable_login_node(
    oim_host: testinfra.host.Host,
    login_ips: List[str],
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Find the first reachable login node from a list of IPs.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ips: list of login node admin IPs to try
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'login_ip', 'skipped', 'error'
    """
    skipped: List[str] = []
    for ip in login_ips:
        if is_node_reachable(oim_host, ip, key_path):
            return {
                "success": True,
                "login_ip": ip,
                "skipped": skipped,
                "error": "",
            }
        skipped.append(ip)

    return {
        "success": False,
        "login_ip": None,
        "skipped": skipped,
        "error": f"No reachable login nodes found among: {login_ips}",
    }


# =============================================================================
# JOB SCRIPT HELPERS
# =============================================================================

def read_job_script() -> Dict[str, Any]:
    """Read the default job.sh script from the project folder.

    Returns:
        Dict with 'success', 'content', 'path', 'error'
    """
    path = get_job_script_path()
    if not os.path.exists(path):
        return {
            "success": False,
            "content": None,
            "path": path,
            "error": f"job.sh not found at {path}",
        }

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "success": True,
        "content": content,
        "path": path,
        "error": "",
    }


def copy_job_script_to_login(
    oim_host: testinfra.host.Host,
    login_ip: str,
    job_script: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Copy job script content to /home/job.sh on the login node.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        job_script: content of the job script
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'details', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        "cd /home && cat > job.sh <<'EOF'\n" + job_script + "\nEOF\nchmod +x job.sh",
        key_path,
    )

    if res.rc == 0:
        return {
            "success": True,
            "details": f"Copied job.sh to /home on {login_ip}",
            "error": "",
        }

    return {
        "success": False,
        "details": None,
        "error": res.stderr or res.stdout,
    }


# =============================================================================
# JOB SUBMISSION / VERIFICATION
# =============================================================================

def submit_job_via_login(
    oim_host: testinfra.host.Host,
    login_ip: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit /home/job.sh via sbatch on the login node.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'job_id', 'output', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        "cd /home && sbatch --parsable job.sh",
        key_path,
    )

    if res.rc != 0:
        return {
            "success": False,
            "job_id": None,
            "output": res.stdout.strip(),
            "error": res.stderr or res.stdout,
        }

    raw_id = res.stdout.strip().split()[0] if res.stdout.strip() else ""
    if not raw_id:
        return {
            "success": False,
            "job_id": None,
            "output": res.stdout.strip(),
            "error": "sbatch did not return a job id",
        }

    if not raw_id.isdigit():
        return {
            "success": False,
            "job_id": raw_id,
            "output": res.stdout.strip(),
            "error": f"Expected numeric job id, got: {raw_id}",
        }

    return {
        "success": True,
        "job_id": raw_id,
        "output": res.stdout.strip(),
        "error": "",
    }


def check_squeue(
    oim_host: testinfra.host.Host,
    login_ip: str,
    job_id: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run squeue -j <job_id> on the login node and return the result.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        job_id: Slurm job ID to query
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'output', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        f"squeue -j {job_id}",
        key_path,
    )

    if res.rc == 0:
        return {
            "success": True,
            "output": res.stdout.strip(),
            "error": "",
        }

    return {
        "success": False,
        "output": res.stdout.strip(),
        "error": res.stderr or res.stdout,
    }


# =============================================================================
# LDAP USER HELPERS
# =============================================================================

def run_ssh_as_user(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    remote_cmd: str,
    key_path: Optional[str] = None,
    password: Optional[str] = None,
) -> Any:
    """Run SSH command to login node as specified user via omnia_core container.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: SSH username (e.g. LDAP user)
        remote_cmd: command to execute on the login node
        key_path: optional SSH private key path
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Result with stdout, stderr, rc attributes
    """
    base_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    if key_path:
        ssh_opts = f"{base_opts} -o BatchMode=yes -i {key_path}"
        ssh_cmd = f"ssh {ssh_opts} {user}@{login_ip} '{remote_cmd}'"
    elif password:
        ssh_opts = f"{base_opts} -o PubkeyAuthentication=no"
        askpass_script = "/tmp/_askpass.sh"
        ssh_cmd = (
            f"printf '#!/bin/sh\\necho {password}\\n' > {askpass_script} && "
            f"chmod +x {askpass_script} && "
            f"SSH_ASKPASS={askpass_script} SSH_ASKPASS_REQUIRE=force "
            f"ssh {ssh_opts} {user}@{login_ip} '{remote_cmd}'"
        )
    else:
        ssh_opts = base_opts
        ssh_cmd = f"ssh {ssh_opts} {user}@{login_ip} '{remote_cmd}'"
    return run_in_container(oim_host, ssh_cmd)


def discover_ldap_user_from_node(
    oim_host: testinfra.host.Host, login_ip: str, key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Discover an LDAP/non-system user on a login node via getent passwd.

    Queries the node for users with UID >= 1000 that have a valid login shell
    (not nologin/false). Returns the first such user found.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'user', 'uid', 'error'
    """
    cmd = "getent passwd | grep -v nologin | grep -v /bin/false"
    res = run_ssh_from_omnia_core(oim_host, login_ip, cmd, key_path)
    if res.rc != 0:
        return {"success": False, "user": None, "uid": None,
                "error": res.stderr or res.stdout or "getent failed"}
    for line in res.stdout.strip().splitlines():
        parts = line.split(":")
        if len(parts) >= 4:
            try:
                uid = int(parts[2])
            except ValueError:
                continue
            if uid >= 1000:
                return {"success": True, "user": parts[0], "uid": uid, "error": ""}
    return {"success": False, "user": None, "uid": None,
            "error": "No LDAP/non-system user found on node"}


def create_ldap_job_script(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    key_path: Optional[str],
    job_script: str,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Create job.sh in the LDAP user's home directory on the login node.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: LDAP username
        key_path: optional SSH private key path
        job_script: content of the job script
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'success', 'error'
    """
    cmd = f"cd /home/{user} && cat > job.sh <<'JOBEOF'\n{job_script}\nJOBEOF\nchmod +x job.sh"
    res = run_ssh_as_user(oim_host, login_ip, user, cmd, key_path, password)
    if res.rc == 0:
        return {"success": True, "error": ""}
    return {"success": False, "error": res.stderr or res.stdout}


def submit_ldap_job(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    key_path: Optional[str],
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit job.sh via sbatch as LDAP user on the login node.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: LDAP username
        key_path: optional SSH private key path
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'success', 'job_id', 'output', 'error'
    """
    cmd = f"cd /home/{user} && sbatch --parsable job.sh"
    res = run_ssh_as_user(oim_host, login_ip, user, cmd, key_path, password)
    if res.rc != 0:
        return {
            "success": False, "job_id": None,
            "output": res.stdout.strip(), "error": res.stderr or res.stdout,
        }
    raw_id = res.stdout.strip().split()[0] if res.stdout.strip() else ""
    if not raw_id or not raw_id.isdigit():
        return {
            "success": False, "job_id": raw_id or None,
            "output": res.stdout.strip(),
            "error": f"Expected numeric job id, got: {raw_id!r}",
        }
    return {
        "success": True, "job_id": raw_id,
        "output": res.stdout.strip(), "error": "",
    }


def wait_ldap_job_complete(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    job_id: str,
    key_path: Optional[str],
    timeout: int = 120,
    interval: int = 5,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Poll squeue until job disappears (completed) or timeout is reached.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: LDAP username
        job_id: Slurm job ID to wait for
        key_path: optional SSH private key path
        timeout: max seconds to wait
        interval: seconds between polls
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'completed', 'elapsed', 'error'
    """
    start = time.time()
    while time.time() - start < timeout:
        res = run_ssh_as_user(oim_host, login_ip, user, f"squeue -j {job_id} -h", key_path, password)
        output = res.stdout.strip()
        if res.rc != 0 or not output:
            return {"completed": True, "elapsed": int(time.time() - start), "error": ""}
        time.sleep(interval)
    return {
        "completed": False,
        "elapsed": int(time.time() - start),
        "error": f"Job {job_id} still in queue after {timeout}s",
    }


def read_ldap_job_output(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    key_path: Optional[str],
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Read output.txt from the LDAP user's home directory.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: LDAP username
        key_path: optional SSH private key path
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'success', 'output', 'error'
    """
    cmd = f"cat /home/{user}/output.txt"
    res = run_ssh_as_user(oim_host, login_ip, user, cmd, key_path, password)
    if res.rc == 0:
        return {"success": True, "output": res.stdout.strip(), "error": ""}
    return {"success": False, "output": res.stdout.strip(), "error": res.stderr or res.stdout}


def cleanup_ldap_job(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    key_path: Optional[str],
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Remove job artifacts from LDAP user's home directory.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: LDAP username
        key_path: optional SSH private key path
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'success', 'error'
    """
    cmd = f"cd /home/{user} && rm -f job.sh output.txt error.txt slurm-*.out"
    res = run_ssh_as_user(oim_host, login_ip, user, cmd, key_path, password)
    if res.rc == 0:
        return {"success": True, "error": ""}
    return {"success": False, "error": res.stderr or res.stdout}


def submit_and_verify_ldap_job(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    key_path: Optional[str],
    job_script: str,
    timeout: int = 120,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """End-to-end: create script, submit, wait, verify output, cleanup.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: LDAP username
        key_path: optional SSH private key path
        job_script: content of the job script
        timeout: max seconds to wait for job completion
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'success', 'job_id', 'output', 'error'
    """
    create = create_ldap_job_script(oim_host, login_ip, user, key_path, job_script, password)
    if not create["success"]:
        return {"success": False, "job_id": None, "output": None, "error": create["error"]}

    submit = submit_ldap_job(oim_host, login_ip, user, key_path, password)
    if not submit["success"]:
        return {"success": False, "job_id": None, "output": submit["output"], "error": submit["error"]}

    job_id = submit["job_id"]
    wait = wait_ldap_job_complete(oim_host, login_ip, user, job_id, key_path, timeout=timeout, password=password)
    if not wait["completed"]:
        cleanup_ldap_job(oim_host, login_ip, user, key_path, password)
        return {"success": False, "job_id": job_id, "output": None, "error": wait["error"]}

    output = read_ldap_job_output(oim_host, login_ip, user, key_path, password)
    cleanup_ldap_job(oim_host, login_ip, user, key_path, password)

    if not output["success"]:
        return {"success": False, "job_id": job_id, "output": None, "error": output["error"]}

    return {"success": True, "job_id": job_id, "output": output["output"], "error": ""}
