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
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

import testinfra.host

from automation_library.core.host import (
    run_in_container,
    run_on_remote_node,
    get_testinfra_host,
    get_node_admin_ip,
    get_all_node_admin_ips,
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
            ips = get_all_node_admin_ips(host, functional_group=group)
            login_ips.extend(ips)
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
            ips = get_all_node_admin_ips(host, functional_group=group)
            compiler_ips.extend(ips)
    return compiler_ips


def parse_compute_node_ips_from_env() -> List[str]:
    """Read compute node IPs from COMPUTE_NODE_IPS environment variable."""
    value = os.environ.get("COMPUTE_NODE_IPS", "").strip()
    if not value:
        return []
    return [ip.strip() for ip in value.split(",") if ip.strip()]


def parse_compute_node_ips_from_pxe_mapping() -> List[str]:
    """Extract compute node admin IPs from PXE mapping via public core API."""
    host = get_testinfra_host()
    groups = get_functional_groups_from_pxe_mapping(host)
    compute_ips: List[str] = []
    for group in groups:
        lower = group.lower()
        if "slurm_node" in lower and "login" not in lower:
            ips = get_all_node_admin_ips(host, functional_group=group)
            compute_ips.extend(ips)
    return compute_ips


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
        ssh_cmd =(
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
    job_script: str,
    key_path: Optional[str] = None,
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
    password: Optional[str] = None,
    key_path: Optional[str] = None,
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
    timeout: int = 120,
    interval: int = 5,
    password: Optional[str] = None,
    key_path: Optional[str] = None,
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
    password: Optional[str] = None,
    key_path: Optional[str] = None,
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
    password: Optional[str] = None,
    key_path: Optional[str] = None,
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
    job_script: str,
    timeout: int = 120,
    password: Optional[str] = None,
    key_path: Optional[str] = None,
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
    create = create_ldap_job_script(oim_host, login_ip, user, job_script, key_path=key_path, password=password)
    if not create["success"]:
        return {"success": False, "job_id": None, "output": None, "error": create["error"]}

    submit = submit_ldap_job(oim_host, login_ip, user, password=password, key_path=key_path)
    if not submit["success"]:
        return {"success": False, "job_id": None, "output": submit["output"], "error": submit["error"]}

    job_id = submit["job_id"]
    wait = wait_ldap_job_complete(oim_host, login_ip, user, job_id, timeout=timeout, password=password, key_path=key_path)
    if not wait["completed"]:
        cleanup_ldap_job(oim_host, login_ip, user, password=password, key_path=key_path)
        return {"success": False, "job_id": job_id, "output": None, "error": wait["error"]}

    output = read_ldap_job_output(oim_host, login_ip, user, password=password, key_path=key_path)
    cleanup_ldap_job(oim_host, login_ip, user, password=password, key_path=key_path)

    if not output["success"]:
        return {"success": False, "job_id": job_id, "output": None, "error": output["error"]}

    return {"success": True, "job_id": job_id, "output": output["output"], "error": ""}


# =============================================================================
# PAM HELPERS
# =============================================================================

def check_pam_module_installed(
    oim_host: testinfra.host.Host,
    node_ip: str,
) -> Dict[str, Any]:
    """Check if pam_slurm_adopt.so exists on a compute node.

    Args:
        oim_host: testinfra host object connected to OIM server
        node_ip: admin IP of the compute node

    Returns:
        Dict with 'success', 'installed', 'path', 'error'
    """
    cmd = "find /usr/lib64/security /lib64/security /lib/security -name 'pam_slurm_adopt.so' 2>/dev/null | head -1"
    res = run_ssh_from_omnia_core(oim_host, node_ip, cmd)
    if res.rc != 0:
        return {
            "success": False, "installed": False,
            "path": None, "error": res.stderr or res.stdout,
        }
    path = res.stdout.strip()
    return {
        "success": True,
        "installed": bool(path),
        "path": path or None,
        "error": "",
    }


def check_pam_config(
    oim_host: testinfra.host.Host,
    node_ip: str,
) -> Dict[str, Any]:
    """Check if /etc/pam.d/sshd references pam_slurm_adopt on a compute node.

    Args:
        oim_host: testinfra host object connected to OIM server
        node_ip: admin IP of the compute node

    Returns:
        Dict with 'success', 'configured', 'pam_lines', 'error'
    """
    cmd = "cat /etc/pam.d/sshd"
    res = run_ssh_from_omnia_core(oim_host, node_ip, cmd)
    if res.rc != 0:
        return {
            "success": False, "configured": False,
            "pam_lines": "", "error": res.stderr or res.stdout,
        }
    content = res.stdout
    configured = "pam_slurm_adopt" in content
    return {
        "success": True,
        "configured": configured,
        "pam_lines": content,
        "error": "",
    }


def ssh_to_compute_as_user(
    oim_host: testinfra.host.Host,
    login_ip: str,
    node_ip: str,
    user: str,
    key_path: Optional[str] = None,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """SSH from login node to compute node as specified user (two-hop via omnia_core).

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        node_ip: admin IP of the compute node
        user: SSH username
        key_path: optional SSH private key path
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'success', 'stdout', 'stderr', 'rc'
    """
    inner_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    if password and not key_path:
        # For password auth, set up SSH_ASKPASS on the login node for the second hop.
        # Use printf with escaped double quotes to avoid single-quote collision
        # with run_ssh_as_user outer wrapping.
        inner_opts += " -o PubkeyAuthentication=no"
        askpass = "/tmp/_askpass_inner.sh"
        inner_cmd = (
            f"printf \"#!/bin/sh\\necho {password}\\n\" > {askpass} && "
            f"chmod +x {askpass} && "
            f"SSH_ASKPASS={askpass} SSH_ASKPASS_REQUIRE=force "
            f"ssh {inner_opts} {user}@{node_ip} whoami"
        )
    else:
        if key_path:
            inner_opts += f" -i {key_path}"
        inner_cmd = f"ssh {inner_opts} {user}@{node_ip} whoami"
    res = run_ssh_as_user(oim_host, login_ip, user, inner_cmd, key_path, password)
    return {
        "success": res.rc == 0,
        "stdout": res.stdout.strip(),
        "stderr": res.stderr.strip() if res.stderr else "",
        "rc": res.rc,
        "error": res.stderr or "" if res.rc != 0 else "",
    }


def submit_sleep_job_as_user(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    key_path: Optional[str] = None,
    sleep_seconds: int = 120,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a sleep job as specified user for PAM testing.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: SSH username
        key_path: optional SSH private key path
        sleep_seconds: how long the job should sleep
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'success', 'job_id', 'error'
    """
    cmd = f'sbatch --parsable --wrap="sleep {sleep_seconds}"'
    res = run_ssh_as_user(oim_host, login_ip, user, cmd, key_path, password)
    if res.rc != 0:
        return {
            "success": False, "job_id": None,
            "error": res.stderr or res.stdout,
        }
    raw_id = res.stdout.strip().split()[0] if res.stdout.strip() else ""
    if not raw_id or not raw_id.isdigit():
        return {
            "success": False, "job_id": None,
            "error": f"Expected numeric job id, got: {raw_id!r}",
        }
    return {"success": True, "job_id": raw_id, "error": ""}


def get_job_node(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    job_id: str,
    key_path: Optional[str] = None,
    timeout: int = 60,
    interval: int = 5,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Wait until a job is RUNNING and return the node it runs on.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: SSH username
        job_id: Slurm job ID
        key_path: optional SSH private key path
        timeout: max seconds to wait for RUNNING state
        interval: seconds between polls
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'success', 'node', 'error'
    """
    cmd = f'squeue -j {job_id} -h -o "%T %N"'
    start = time.time()
    while time.time() - start < timeout:
        res = run_ssh_as_user(oim_host, login_ip, user, cmd, key_path, password)
        output = res.stdout.strip()
        if output:
            parts = output.split()
            if len(parts) >= 2 and parts[0] == "RUNNING":
                return {"success": True, "node": parts[1], "error": ""}
        time.sleep(interval)
    return {
        "success": False, "node": None,
        "error": f"Job {job_id} not RUNNING after {timeout}s",
    }


def resolve_node_ip(
    oim_host: testinfra.host.Host,
    node_name: str,
) -> Dict[str, Any]:
    """Resolve a Slurm node name to its IP address via getent hosts.

    Args:
        oim_host: testinfra host object connected to OIM server
        node_name: Slurm node hostname

    Returns:
        Dict with 'success', 'ip', 'error'
    """
    res = run_in_container(oim_host, f"getent hosts {node_name}")
    if res.rc == 0 and res.stdout.strip():
        ip = res.stdout.strip().split()[0]
        return {"success": True, "ip": ip, "error": ""}
    return {
        "success": False, "ip": None,
        "error": f"Could not resolve {node_name}: {res.stderr or res.stdout}",
    }


def cancel_job_as_user(
    oim_host: testinfra.host.Host,
    login_ip: str,
    user: str,
    job_id: str,
    key_path: Optional[str] = None,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel a Slurm job as the specified user.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        user: SSH username
        job_id: Slurm job ID to cancel
        key_path: optional SSH private key path
        password: optional SSH password (uses SSH_ASKPASS)

    Returns:
        Dict with 'success', 'error'
    """
    res = run_ssh_as_user(
        oim_host, login_ip, user, f"scancel {job_id}", key_path, password
    )
    if res.rc == 0:
        return {"success": True, "error": ""}
    return {"success": False, "error": res.stderr or res.stdout}


def check_user_processes_on_node(
    oim_host: testinfra.host.Host,
    node_ip: str,
    user: str,
) -> Dict[str, Any]:
    """Check if a user still has processes running on a compute node.

    Args:
        oim_host: testinfra host object connected to OIM server
        node_ip: admin IP of the compute node
        user: username to check for

    Returns:
        Dict with 'success', 'has_processes', 'process_list', 'error'
    """
    cmd = f"pgrep -u {user} -a"
    res = run_ssh_from_omnia_core(oim_host, node_ip, cmd)
    if res.rc == 0 and res.stdout.strip():
        return {
            "success": True,
            "has_processes": True,
            "process_list": res.stdout.strip(),
            "error": "",
        }
    # rc != 0 means no matching processes (pgrep returns 1)
    return {
        "success": res.rc in (0, 1),
        "has_processes": False,
        "process_list": "",
        "error": "" if res.rc in (0, 1) else (res.stderr or res.stdout),
    }


# =============================================================================
# QUEUEING / NODE-DOWN HELPERS
# =============================================================================

@dataclass
class CmdResult:
    """Lightweight result object returned by ssh_cmd_direct."""
    returncode: int
    stdout: str
    stderr: str


def ssh_cmd_direct(
    login_ip: str,
    user: str,
    cmd: str,
    key_path: Optional[str] = None,
    timeout: int = 30,
) -> CmdResult:
    """Run a command on the login node via SSH from omnia_core.

    Args:
        login_ip: admin IP of the login node
        user: SSH username (typically 'root')
        cmd: command to execute on the login node
        key_path: optional SSH private key path
        timeout: command timeout in seconds (unused, kept for API compat)

    Returns:
        CmdResult with returncode, stdout, stderr
    """
    host = get_testinfra_host()
    res = run_ssh_from_omnia_core(host, login_ip, cmd, key_path)
    return CmdResult(
        returncode=res.rc,
        stdout=res.stdout if res.stdout else "",
        stderr=res.stderr if res.stderr else "",
    )


def get_compute_nodes(
    login_ip: str,
    user: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Discover Slurm compute node hostnames via sinfo.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'nodes' (list of hostnames), 'error'
    """
    res = ssh_cmd_direct(login_ip, user, 'sinfo -h -N -o "%N" | sort -u', key_path)
    if res.returncode != 0:
        return {"success": False, "nodes": [], "error": res.stderr or res.stdout}
    nodes = [n.strip() for n in res.stdout.strip().splitlines() if n.strip()]
    return {"success": True, "nodes": nodes, "error": ""}


def get_node_info(
    login_ip: str,
    user: str,
    node: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Get detailed info for a Slurm node via scontrol show node.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        node: Slurm node hostname
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'cpus', 'memory_mb', 'gres', 'state', 'error'
    """
    res = ssh_cmd_direct(login_ip, user, f"scontrol show node {node}", key_path)
    if res.returncode != 0:
        return {"success": False, "cpus": "", "memory_mb": "0", "gres": "(null)", "state": "", "error": res.stderr or res.stdout}
    output = res.stdout
    info: Dict[str, Any] = {"success": True, "cpus": "", "memory_mb": "0", "gres": "(null)", "state": "", "error": ""}
    for line in output.splitlines():
        for token in line.split():
            if token.startswith("CPUTot="):
                info["cpus"] = token.split("=", 1)[1]
            elif token.startswith("RealMemory="):
                info["memory_mb"] = token.split("=", 1)[1]
            elif token.startswith("Gres="):
                info["gres"] = token.split("=", 1)[1]
            elif token.startswith("State="):
                info["state"] = token.split("=", 1)[1]
    return info


def drain_node(
    login_ip: str,
    user: str,
    node: str,
    reason: str = "test",
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Drain a Slurm compute node.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        node: Slurm node hostname to drain
        reason: drain reason string
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'error'
    """
    res = ssh_cmd_direct(login_ip, user, f"scontrol update NodeName={node} State=drain Reason={reason}", key_path)
    if res.returncode == 0:
        return {"success": True, "error": ""}
    return {"success": False, "error": res.stderr or res.stdout}


def resume_node(
    login_ip: str,
    user: str,
    node: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Resume a drained Slurm compute node.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        node: Slurm node hostname to resume
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'error'
    """
    res = ssh_cmd_direct(login_ip, user, f"scontrol update NodeName={node} State=resume", key_path)
    if res.returncode == 0:
        return {"success": True, "error": ""}
    return {"success": False, "error": res.stderr or res.stdout}


def wait_node_state(
    login_ip: str,
    user: str,
    node: str,
    target_state: str,
    key_path: Optional[str] = None,
    timeout: int = 60,
    interval: int = 5,
) -> str:
    """Poll until a Slurm node reaches the target state.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        node: Slurm node hostname
        target_state: desired state substring (e.g. 'drain', 'idle')
        key_path: optional SSH private key path
        timeout: max seconds to wait
        interval: seconds between polls

    Returns:
        Current state string (may or may not contain target_state)
    """
    start = time.time()
    state = ""
    while time.time() - start < timeout:
        res = ssh_cmd_direct(login_ip, user, f"scontrol show node {node}", key_path)
        for token in res.stdout.split():
            if token.startswith("State="):
                state = token.split("=", 1)[1].lower()
                break
        if target_state.lower() in state:
            return state
        time.sleep(interval)
    return state


def create_job_script(
    login_ip: str,
    user: str,
    key_path: Optional[str] = None,
    sleep_seconds: int = 10,
) -> Dict[str, Any]:
    """Create a simple sleep job script on the login node.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        key_path: optional SSH private key path
        sleep_seconds: how long the job should sleep

    Returns:
        Dict with 'success', 'error'
    """
    cmd = (
        f"printf \"#!/bin/bash\\n#SBATCH --job-name=queue_test\\nsleep {sleep_seconds}\\n\""
        " > /tmp/queue_test.sh && chmod +x /tmp/queue_test.sh"
    )
    res = ssh_cmd_direct(login_ip, user, cmd, key_path)
    if res.returncode == 0:
        return {"success": True, "error": ""}
    return {"success": False, "error": res.stderr or res.stdout}


def submit_job_direct(
    login_ip: str,
    user: str,
    key_path: Optional[str] = None,
    nodelist: Optional[str] = None,
    cpus: Optional[int] = None,
    mem_gb: Optional[int] = None,
    gres: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a job script via sbatch on the login node.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        key_path: optional SSH private key path
        nodelist: optional --nodelist constraint
        cpus: optional --ntasks (CPU count)
        mem_gb: optional --mem in GB
        gres: optional --gres string (e.g. 'gpu:1')

    Returns:
        Dict with 'success', 'job_id', 'output', 'error'
    """
    cmd = "sbatch --parsable"
    if nodelist:
        cmd += f" --nodelist={nodelist}"
    if cpus:
        cmd += f" --ntasks={cpus}"
    if mem_gb:
        cmd += f" --mem={mem_gb}G"
    if gres:
        cmd += f" --gres={gres}"
    cmd += " /tmp/queue_test.sh"
    res = ssh_cmd_direct(login_ip, user, cmd, key_path)
    if res.returncode != 0:
        return {"success": False, "job_id": None, "output": res.stdout, "error": res.stderr or res.stdout}
    raw_id = res.stdout.strip().split()[0] if res.stdout.strip() else ""
    if not raw_id or not raw_id.isdigit():
        return {"success": False, "job_id": None, "output": res.stdout, "error": f"Expected numeric job id, got: {raw_id!r}"}
    return {"success": True, "job_id": raw_id, "output": res.stdout, "error": ""}


def poll_job_state_direct(
    login_ip: str,
    user: str,
    job_id: str,
    key_path: Optional[str] = None,
    timeout: int = 30,
    interval: int = 3,
) -> Dict[str, Any]:
    """Poll job state via squeue until timeout.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        job_id: Slurm job ID
        key_path: optional SSH private key path
        timeout: max seconds to poll
        interval: seconds between polls

    Returns:
        Dict with 'state', 'reason'
    """
    start = time.time()
    state = ""
    reason = ""
    while time.time() - start < timeout:
        res = ssh_cmd_direct(login_ip, user, f'squeue -j {job_id} -h -o "%T %r"', key_path)
        output = res.stdout.strip()
        if output:
            parts = output.split(None, 1)
            state = parts[0] if parts else ""
            reason = parts[1] if len(parts) > 1 else ""
            return {"state": state, "reason": reason}
        time.sleep(interval)
    return {"state": state, "reason": reason}


def wait_job_running(
    login_ip: str,
    user: str,
    job_id: str,
    key_path: Optional[str] = None,
    timeout: int = 180,
    interval: int = 5,
) -> Dict[str, Any]:
    """Wait for a job to reach RUNNING or COMPLETED state.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        job_id: Slurm job ID
        key_path: optional SSH private key path
        timeout: max seconds to wait
        interval: seconds between polls

    Returns:
        Dict with 'state', 'reason'
    """
    start = time.time()
    state = ""
    reason = ""
    while time.time() - start < timeout:
        res = ssh_cmd_direct(login_ip, user, f'squeue -j {job_id} -h -o "%T %r"', key_path)
        output = res.stdout.strip()
        if not output:
            # Job no longer in queue — likely COMPLETED
            return {"state": "COMPLETED", "reason": ""}
        parts = output.split(None, 1)
        state = parts[0] if parts else ""
        reason = parts[1] if len(parts) > 1 else ""
        if state in {"RUNNING", "COMPLETED"}:
            return {"state": state, "reason": reason}
        time.sleep(interval)
    return {"state": state, "reason": reason}


def get_job_start_time(
    login_ip: str,
    user: str,
    job_id: str,
    key_path: Optional[str] = None,
) -> str:
    """Get the start time of a job via sacct or scontrol.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        job_id: Slurm job ID
        key_path: optional SSH private key path

    Returns:
        Start time string, or empty string if unavailable
    """
    res = ssh_cmd_direct(login_ip, user, f"sacct -j {job_id} -n -o Start --parsable2 | head -1", key_path)
    start_time = res.stdout.strip()
    if start_time and start_time != "Unknown":
        return start_time
    # Fallback to scontrol
    res = ssh_cmd_direct(login_ip, user, f"scontrol show job {job_id} | grep -oP 'StartTime=\\K\\S+'", key_path)
    return res.stdout.strip()


# =============================================================================
# INSUFFICIENT-RESOURCE TEST HELPERS
# =============================================================================

def parse_slurm_control_ip_from_pxe_mapping() -> Optional[str]:
    """Extract the Slurm control node admin IP from PXE mapping.

    Looks for functional groups containing 'slurm_control' (case-insensitive).

    Returns:
        First matching admin IP, or None if not found
    """
    host = get_testinfra_host()
    groups = get_functional_groups_from_pxe_mapping(host)
    for group in groups:
        if "slurm_control" in group.lower():
            ips = get_all_node_admin_ips(host, functional_group=group)
            if ips:
                return ips[0]
    return None


def check_slurm_version(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Check Slurm version on the control node.

    Args:
        oim_host: testinfra host object connected to OIM server
        ctrl_ip: admin IP of the Slurm control node
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'version', 'error'
    """
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, "sinfo --version", key_path)
    if res.rc != 0:
        return {"success": False, "version": "", "error": res.stderr or res.stdout or "sinfo --version failed"}
    version = res.stdout.strip()
    return {"success": True, "version": version, "error": ""}


def check_sinfo(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    fmt: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run sinfo with a given format on the control node.

    Args:
        oim_host: testinfra host object connected to OIM server
        ctrl_ip: admin IP of the Slurm control node
        fmt: sinfo --Format string (e.g. 'NodeList,CPUs,CPUsState,StateCompact')
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'output', 'error'
    """
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, f"sinfo --Format={fmt}", key_path)
    if res.rc != 0:
        return {"success": False, "output": "", "error": res.stderr or res.stdout or "sinfo failed"}
    return {"success": True, "output": res.stdout.strip(), "error": ""}


def read_job_script_by_name(script_path: str) -> Dict[str, Any]:
    """Read a job script by its relative path (from project root).

    Args:
        script_path: relative path to the script (e.g. 'automation_library/slurm/_job2.sh')

    Returns:
        Dict with 'success', 'content', 'path', 'error'
    """
    abs_path = os.path.join(_get_project_root(), script_path)
    if not os.path.exists(abs_path):
        return {
            "success": False,
            "content": None,
            "path": abs_path,
            "error": f"Script not found at {abs_path}",
        }
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"success": True, "content": content, "path": abs_path, "error": ""}


def copy_script_to_remote(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    script_content: str,
    remote_path: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Copy a script to a remote node via SSH.

    Args:
        oim_host: testinfra host object connected to OIM server
        ctrl_ip: admin IP of the target node
        script_content: script file content
        remote_path: destination path on the remote node
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'error'
    """
    cmd = f"cat > {remote_path} <<'EOFSCRIPT'\n{script_content}\nEOFSCRIPT\nchmod +x {remote_path}"
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, cmd, key_path)
    if res.rc != 0:
        return {"success": False, "error": res.stderr or res.stdout or "copy failed"}
    return {"success": True, "error": ""}


def submit_remote_script(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    remote_path: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a job script on the remote node via sbatch.

    Args:
        oim_host: testinfra host object connected to OIM server
        ctrl_ip: admin IP of the target node
        remote_path: path to the script on the remote node
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'job_id', 'output', 'error'
    """
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, f"sbatch --parsable {remote_path}", key_path)
    if res.rc != 0:
        return {
            "success": False,
            "job_id": None,
            "output": res.stdout.strip() if res.stdout else "",
            "error": res.stderr or res.stdout or "sbatch failed",
        }
    raw_id = res.stdout.strip().split()[0] if res.stdout and res.stdout.strip() else ""
    if not raw_id or not raw_id.isdigit():
        return {
            "success": False,
            "job_id": raw_id or None,
            "output": res.stdout.strip() if res.stdout else "",
            "error": f"Expected numeric job id, got: {raw_id!r}",
        }
    return {"success": True, "job_id": raw_id, "output": res.stdout.strip(), "error": ""}


def poll_job_state(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    job_id: str,
    key_path: Optional[str] = None,
    timeout: int = 60,
    interval: int = 5,
) -> Dict[str, Any]:
    """Poll squeue for a job's state and reason.

    Args:
        oim_host: testinfra host object connected to OIM server
        ctrl_ip: admin IP of the target node
        job_id: Slurm job ID
        key_path: optional SSH private key path
        timeout: max seconds to poll
        interval: seconds between polls

    Returns:
        Dict with 'state', 'reason'
    """
    start = time.time()
    state = ""
    reason = ""
    while time.time() - start < timeout:
        res = run_ssh_from_omnia_core(
            oim_host, ctrl_ip, f'squeue -j {job_id} -h -o "%T %r"', key_path
        )
        output = res.stdout.strip() if res.stdout else ""
        if output:
            parts = output.split(None, 1)
            state = parts[0] if parts else ""
            reason = parts[1] if len(parts) > 1 else ""
            return {"state": state, "reason": reason}
        time.sleep(interval)
    return {"state": state, "reason": reason}


def check_job_scontrol(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    job_id: str,
    key_path: Optional[str] = None,
    timeout: int = 180,
    interval: int = 10,
) -> Dict[str, Any]:
    """Poll scontrol show job until the job reaches a terminal state.

    Args:
        oim_host: testinfra host object connected to OIM server
        ctrl_ip: admin IP of the target node
        job_id: Slurm job ID
        key_path: optional SSH private key path
        timeout: max seconds to wait
        interval: seconds between polls

    Returns:
        Dict with 'success', 'state', 'output', 'error'
    """
    start = time.time()
    last_state = ""
    while time.time() - start < timeout:
        res = run_ssh_from_omnia_core(
            oim_host, ctrl_ip, f"scontrol show job {job_id}", key_path
        )
        output = res.stdout.strip() if res.stdout else ""
        # Parse JobState= from output
        for token in output.split():
            if token.startswith("JobState="):
                last_state = token.split("=", 1)[1]
                break
        if last_state in {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"}:
            return {"success": True, "state": last_state, "output": output, "error": ""}
        time.sleep(interval)
    return {"success": False, "state": last_state, "output": "", "error": f"Job {job_id} did not reach terminal state within {timeout}s"}


def read_job_output(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    output_path: str = "output.txt",
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Read job output file from the remote node.

    Args:
        oim_host: testinfra host object connected to OIM server
        ctrl_ip: admin IP of the target node
        output_path: path to the output file on the remote node
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'content', 'error'
    """
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, f"cat {output_path}", key_path)
    if res.rc != 0:
        return {"success": False, "content": "", "error": res.stderr or res.stdout or "Failed to read output"}
    return {"success": True, "content": res.stdout.strip() if res.stdout else "", "error": ""}


def cleanup_job(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    job_id: str,
    remote_script_path: str,
    key_path: Optional[str] = None,
) -> None:
    """Cancel a job and remove the remote script and output files.

    Args:
        oim_host: testinfra host object connected to OIM server
        ctrl_ip: admin IP of the target node
        job_id: Slurm job ID to cancel
        remote_script_path: path to the script on the remote node
        key_path: optional SSH private key path
    """
    if job_id:
        run_ssh_from_omnia_core(oim_host, ctrl_ip, f"scancel {job_id} 2>/dev/null", key_path)
    run_ssh_from_omnia_core(
        oim_host, ctrl_ip,
        f"rm -f {remote_script_path} output.txt error.txt",
        key_path,
    )


def cleanup_jobs_direct(
    login_ip: str,
    user: str,
    job_ids: List[str],
    key_path: Optional[str] = None,
) -> None:
    """Cancel a list of jobs and remove the temp job script.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        job_ids: list of Slurm job IDs to cancel
        key_path: optional SSH private key path
    """
    for jid in job_ids:
        if jid:
            ssh_cmd_direct(login_ip, user, f"scancel {jid} 2>/dev/null", key_path)
    ssh_cmd_direct(login_ip, user, "rm -f /tmp/queue_test.sh", key_path)


# =============================================================================
# SCHEDULER STABILITY HELPERS
# =============================================================================

def check_slurmctld_active(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Check if slurmctld is responsive by running sinfo.

    Returns:
        Dict with 'success', 'responsive', 'error'
    """
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, "sinfo --version", key_path)
    if res.rc == 0:
        return {"success": True, "responsive": True, "error": ""}
    return {"success": True, "responsive": False, "error": res.stderr or res.stdout or "sinfo failed"}


def get_slurmctld_pid(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Get the PID of slurmctld on the control node.

    Returns:
        Dict with 'success', 'pid', 'error'
    """
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, "pgrep -o slurmctld", key_path)
    pid = res.stdout.strip() if res.stdout else ""
    if res.rc == 0 and pid:
        return {"success": True, "pid": pid, "error": ""}
    return {"success": False, "pid": None, "error": res.stderr or "slurmctld not found"}


def submit_batch_jobs(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    script_content: str,
    count: int,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit multiple jobs from inline script content.

    Writes the script to /tmp/_stability_job.sh on the control node,
    then runs sbatch --parsable <count> times.

    Returns:
        Dict with 'success', 'job_ids', 'error'
    """
    remote_path = "/tmp/_stability_job.sh"
    write_cmd = f"cat > {remote_path} <<'EOFSCRIPT'\n{script_content}\nEOFSCRIPT\nchmod +x {remote_path}"
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, write_cmd, key_path)
    if res.rc != 0:
        return {"success": False, "job_ids": [], "error": res.stderr or res.stdout or "script write failed"}

    job_ids: List[str] = []
    errors: List[str] = []
    for _ in range(count):
        res = run_ssh_from_omnia_core(oim_host, ctrl_ip, f"sbatch --parsable {remote_path}", key_path)
        if res.rc == 0 and res.stdout and res.stdout.strip():
            raw = res.stdout.strip().split()[0]
            if raw.isdigit():
                job_ids.append(raw)
            else:
                errors.append(f"Non-numeric id: {raw}")
        else:
            errors.append(res.stderr or res.stdout or "sbatch failed")

    run_ssh_from_omnia_core(oim_host, ctrl_ip, f"rm -f {remote_path}", key_path)

    if not job_ids:
        return {"success": False, "job_ids": [], "error": "; ".join(errors[:5])}
    return {"success": True, "job_ids": job_ids, "error": ""}


def count_queue_jobs(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    job_name: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Count jobs in the queue matching a job name.

    Returns:
        Dict with 'success', 'total', 'running', 'pending', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host, ctrl_ip, f'squeue -h -n {job_name} -o "%T"', key_path
    )
    if res.rc != 0:
        return {"success": False, "total": 0, "running": 0, "pending": 0,
                "error": res.stderr or res.stdout or "squeue failed"}
    lines = [l.strip() for l in (res.stdout or "").strip().splitlines() if l.strip()]
    running = sum(1 for l in lines if l == "RUNNING")
    pending = sum(1 for l in lines if l == "PENDING")
    return {"success": True, "total": len(lines), "running": running, "pending": pending, "error": ""}


def cancel_jobs_by_name(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    job_name: str,
    key_path: Optional[str] = None,
) -> None:
    """Cancel all jobs matching a given job name."""
    run_ssh_from_omnia_core(oim_host, ctrl_ip, f"scancel -n {job_name} 2>/dev/null", key_path)


def cancel_jobs_by_ids(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    job_ids: List[str],
    key_path: Optional[str] = None,
) -> None:
    """Cancel a list of jobs by their IDs."""
    if job_ids:
        ids_str = " ".join(job_ids)
        run_ssh_from_omnia_core(oim_host, ctrl_ip, f"scancel {ids_str} 2>/dev/null", key_path)


def submit_and_cancel_rapid(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    script_content: str,
    cycles: int,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run rapid submit-then-cancel cycles.

    Returns:
        Dict with 'success', 'completed_cycles', 'errors', 'error'
    """
    remote_path = "/tmp/_rapid_job.sh"
    write_cmd = f"cat > {remote_path} <<'EOFSCRIPT'\n{script_content}\nEOFSCRIPT\nchmod +x {remote_path}"
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, write_cmd, key_path)
    if res.rc != 0:
        return {"success": False, "completed_cycles": 0, "errors": [],
                "error": res.stderr or "script write failed"}

    completed = 0
    errors: List[str] = []
    for _ in range(cycles):
        res = run_ssh_from_omnia_core(oim_host, ctrl_ip, f"sbatch --parsable {remote_path}", key_path)
        if res.rc == 0 and res.stdout and res.stdout.strip():
            jid = res.stdout.strip().split()[0]
            if jid.isdigit():
                run_ssh_from_omnia_core(oim_host, ctrl_ip, f"scancel {jid} 2>/dev/null", key_path)
                completed += 1
            else:
                errors.append(f"Non-numeric id: {jid}")
        else:
            errors.append(res.stderr or "sbatch failed")

    run_ssh_from_omnia_core(oim_host, ctrl_ip, f"rm -f {remote_path}", key_path)

    return {
        "success": completed > 0,
        "completed_cycles": completed,
        "errors": errors[:10],
        "error": "; ".join(errors[:5]) if errors else "",
    }


def get_node_total_cpus(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Get total CPUs and node name from the first compute node via sinfo.

    Returns:
        Dict with 'success', 'cpus', 'node', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host, ctrl_ip, 'sinfo -h -N -o "%N %c" | head -1', key_path
    )
    if res.rc != 0 or not res.stdout or not res.stdout.strip():
        return {"success": False, "cpus": 0, "node": "",
                "error": res.stderr or "sinfo failed"}
    parts = res.stdout.strip().split()
    node = parts[0] if parts else ""
    cpus = 1
    if len(parts) > 1 and parts[1].isdigit():
        cpus = int(parts[1])
    return {"success": True, "cpus": cpus, "node": node, "error": ""}


def check_queue_empty(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    job_name: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Check if the queue has no jobs matching a given name.

    Returns:
        Dict with 'success', 'empty', 'remaining', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host, ctrl_ip, f'squeue -h -n {job_name} -o "%i"', key_path
    )
    if res.rc != 0:
        return {"success": False, "empty": False, "remaining": "",
                "error": res.stderr or "squeue failed"}
    lines = [l.strip() for l in (res.stdout or "").strip().splitlines() if l.strip()]
    return {"success": True, "empty": len(lines) == 0, "remaining": str(len(lines)), "error": ""}


def restart_slurmctld(
    oim_host: testinfra.host.Host,
    ctrl_ip: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Restart slurmctld on the control node.

    Returns:
        Dict with 'success', 'error'
    """
    res = run_ssh_from_omnia_core(oim_host, ctrl_ip, "systemctl restart slurmctld", key_path)
    if res.rc != 0:
        return {"success": False, "error": res.stderr or res.stdout or "restart failed"}
    time.sleep(3)
    check = run_ssh_from_omnia_core(oim_host, ctrl_ip, "sinfo --version", key_path)
    if check.rc != 0:
        return {"success": False, "error": "slurmctld did not recover after restart"}
    return {"success": True, "error": ""}


def check_no_zombie_slurmd(
    oim_host: testinfra.host.Host,
    node_ip: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Check for zombie slurmd processes on a compute node.

    Returns:
        Dict with 'success', 'has_zombies', 'zombie_list', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host, node_ip, "ps aux | grep slurmd | grep -i defunct", key_path
    )
    output = res.stdout.strip() if res.stdout else ""
    zombies = [l for l in output.splitlines() if "defunct" in l.lower()]
    return {
        "success": True,
        "has_zombies": len(zombies) > 0,
        "zombie_list": "\n".join(zombies),
        "error": "",
    }


def get_node_state(
    login_ip: str,
    user: str,
    node: str,
    key_path: Optional[str] = None,
) -> str:
    """Get the current state of a Slurm node.

    Returns:
        Node state string (e.g. 'idle', 'drained', 'mixed'), or empty on failure.
    """
    res = ssh_cmd_direct(login_ip, user, f"scontrol show node {node}", key_path)
    output = res.stdout or ""
    for token in output.split():
        if token.startswith("State="):
            return token.split("=", 1)[1].lower()
    return ""
