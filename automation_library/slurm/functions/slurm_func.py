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
    get_testinfra_host,
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
# TEST ENVIRONMENT SETUP FUNCTIONS
# =============================================================================

def test_env_setup() -> Dict[str, Any]:
    """Set up test environment for drain/resume tests.
    
    Returns:
        Dict with 'success', 'login_ip', 'compute_nodes', 'error'
    """
    from automation_library.core.host import get_testinfra_host
    env_result = setup_drain_test_env(get_testinfra_host())
    if not env_result["success"]:
        return {
            "success": False,
            "login_ip": "",
            "compute_nodes": [],
            "error": env_result["error"]
        }
    return env_result


def drained_nodes_setup(test_env: Dict[str, Any]) -> Dict[str, Any]:
    """Set up all nodes in drained state for testing.
    
    Args:
        test_env: Test environment dictionary containing login_ip and compute_nodes
        
    Returns:
        Dict with 'success', 'login_ip', 'compute_nodes', 'drained_nodes', 'error'
    """
    login_ip = test_env["login_ip"]
    compute_nodes = test_env["compute_nodes"]
    
    # Drain all nodes
    drain_result = setup_all_drained_nodes(login_ip, "root", compute_nodes)
    if not drain_result["success"]:
        return {
            "success": False,
            "login_ip": login_ip,
            "compute_nodes": compute_nodes,
            "drained_nodes": [],
            "error": drain_result["error"]
        }
    
    return {
        "success": True,
        "login_ip": login_ip,
        "compute_nodes": compute_nodes,
        "drained_nodes": drain_result["nodes"],
        "error": ""
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
    """Discover Slurm compute node hostnames and admin IPs via sinfo.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        key_path: optional SSH private key path

    Returns:
        Dict with:
        - 'success': bool
        - 'nodes': list of hostnames (for backward compatibility)
        - 'admin_ips': list of admin IPs (NodeAddr from sinfo)
        - 'error': str
    """
    # %N = NodeHostName, %o = NodeAddr (admin IP)
    res = ssh_cmd_direct(login_ip, user, 'sinfo -h -N -o "%N|%o" | sort -u', key_path)
    if res.returncode != 0:
        return {"success": False, "nodes": [], "admin_ips": [], "error": res.stderr or res.stdout}

    nodes = []
    admin_ips = []
    for line in res.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        hostname = parts[0].strip() if len(parts) > 0 else ""
        node_addr = parts[1].strip() if len(parts) > 1 else ""
        if hostname and hostname not in nodes:
            nodes.append(hostname)
            admin_ips.append(node_addr)

    return {"success": True, "nodes": nodes, "admin_ips": admin_ips, "error": ""}


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
# TEST ENVIRONMENT SETUP HELPERS
# =============================================================================

def setup_slurm_test_env(
    oim_host,
    login_functional_group: str = "login_node_x86_64",
    slurm_functional_group: str = "slurm_node_x86_64",
    user: str = "root",
    sleep_seconds: int = 30,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Set up test environment with login node and compute nodes.

    Discovers login nodes and compute nodes from PXE mapping, finds a
    reachable login node, and creates a job script.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_functional_group: functional group for login nodes
        slurm_functional_group: functional group for slurm compute nodes
        user: SSH username
        sleep_seconds: sleep duration for job script
        key_path: optional SSH private key path

    Returns:
        Dict with:
        - 'success': bool
        - 'login_ip': str (admin IP of reachable login node)
        - 'compute_nodes': list of compute node hostnames
        - 'compute_ips': list of compute node admin IPs
        - 'error': str
    """
    from automation_library.core.host import get_nodes_info

    # Discover login nodes
    login_nodes = get_nodes_info(oim_host, search_by="functional_group", search_value="login_node_x86_64")
    login_ips = [node["admin_ip"] for node in login_nodes if node.get("admin_ip")]
    if not login_ips:
        return {"success": False, "login_ip": "", "compute_nodes": [], "compute_ips": [], "error": "No login nodes found"}

    # Find reachable login node
    result = find_reachable_login_node(oim_host, login_ips)
    if not result["success"]:
        return {"success": False, "login_ip": "", "compute_nodes": [], "compute_ips": [], "error": "No reachable login nodes"}
    login_ip = result["login_ip"]

    # Discover compute nodes from PXE mapping
    compute_nodes_info = get_nodes_info(oim_host, search_by="functional_group", search_value="slurm_node_x86_64")
    compute_nodes = [node["hostname"] for node in compute_nodes_info if node.get("hostname")]
    compute_ips = [node["admin_ip"] for node in compute_nodes_info if node.get("admin_ip")]

    if not compute_nodes:
        return {"success": False, "login_ip": login_ip, "compute_nodes": [], "compute_ips": [], "error": "No compute nodes found"}

    # Create job script on login node
    script_result = create_job_script(login_ip, user, key_path, sleep_seconds)
    if not script_result["success"]:
        return {"success": False, "login_ip": login_ip, "compute_nodes": compute_nodes, "compute_ips": compute_ips, "error": f"Failed to create job script: {script_result['error']}"}

    return {
        "success": True,
        "login_ip": login_ip,
        "compute_nodes": compute_nodes,
        "compute_ips": compute_ips,
        "error": ""
    }


def drain_all_nodes(
    login_ip: str,
    user: str,
    compute_nodes: List[str],
    reason: str = "testing",
    key_path: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Drain all compute nodes.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        compute_nodes: list of compute node hostnames to drain
        reason: drain reason string
        key_path: optional SSH private key path
        timeout: seconds to wait for each node to reach drain state

    Returns:
        Dict with:
        - 'success': bool
        - 'drained_nodes': list of successfully drained nodes
        - 'failed_nodes': list of nodes that failed to drain
        - 'error': str
    """
    drained_nodes = []
    failed_nodes = []
    errors = []

    for node in compute_nodes:
        result = drain_node(login_ip, user, node, reason, key_path)
        if not result["success"]:
            failed_nodes.append(node)
            errors.append(f"{node}: {result['error']}")
            continue

        state = wait_node_state(login_ip, user, node, "drain", key_path, timeout)
        if "drain" in state.lower():
            drained_nodes.append(node)
        else:
            failed_nodes.append(node)
            errors.append(f"{node}: did not reach drain state (state={state})")

    return {
        "success": len(failed_nodes) == 0,
        "drained_nodes": drained_nodes,
        "failed_nodes": failed_nodes,
        "error": "; ".join(errors) if errors else ""
    }


def drain_single_node(
    login_ip: str,
    user: str,
    node: str,
    reason: str = "testing_single",
    key_path: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Drain a single compute node.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        node: compute node hostname to drain
        reason: drain reason string
        key_path: optional SSH private key path
        timeout: seconds to wait for node to reach drain state

    Returns:
        Dict with:
        - 'success': bool
        - 'node': str (the drained node hostname)
        - 'error': str
    """
    result = drain_node(login_ip, user, node, reason, key_path)
    if not result["success"]:
        return {"success": False, "node": node, "error": result["error"]}

    state = wait_node_state(login_ip, user, node, "drain", key_path, timeout)
    if "drain" not in state.lower():
        return {"success": False, "node": node, "error": f"Node did not reach drain state (state={state})"}

    return {"success": True, "node": node, "error": ""}


def resume_all_nodes(
    login_ip: str,
    user: str,
    compute_nodes: List[str],
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Resume all compute nodes.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        compute_nodes: list of compute node hostnames to resume
        key_path: optional SSH private key path

    Returns:
        Dict with:
        - 'success': bool
        - 'resumed_nodes': list of successfully resumed nodes
        - 'failed_nodes': list of nodes that failed to resume
        - 'error': str
    """
    resumed_nodes = []
    failed_nodes = []
    errors = []

    for node in compute_nodes:
        result = resume_node(login_ip, user, node, key_path)
        if result["success"]:
            resumed_nodes.append(node)
        else:
            failed_nodes.append(node)
            errors.append(f"{node}: {result['error']}")

    return {
        "success": len(failed_nodes) == 0,
        "resumed_nodes": resumed_nodes,
        "failed_nodes": failed_nodes,
        "error": "; ".join(errors) if errors else ""
    }


def cleanup_test_env(
    login_ip: str,
    user: str,
    compute_nodes: List[str],
    job_ids: List[str] = None,
    key_path: Optional[str] = None,
) -> None:
    """Cleanup test environment by resuming nodes and cancelling jobs.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        compute_nodes: list of compute node hostnames to resume
        job_ids: optional list of job IDs to cancel
        key_path: optional SSH private key path
    """
    # Resume all nodes
    resume_all_nodes(login_ip, user, compute_nodes, key_path)

    # Cancel any remaining jobs
    if job_ids:
        cleanup_jobs_direct(login_ip, user, job_ids, key_path)


# =============================================================================
# DRAIN/RESUME TEST FIXTURE HELPERS
# =============================================================================

def setup_drain_test_env(oim_host, sleep_seconds: int = 30) -> Dict[str, Any]:
    """Set up test environment for drain/resume tests.
    
    This is a helper function that wraps setup_slurm_test_env for convenience
    in drain/resume test scenarios.
    
    Args:
        oim_host: testinfra host object connected to OIM server
        sleep_seconds: sleep duration for job script
        
    Returns:
        Dict with test environment data
    """
    env_result = setup_slurm_test_env(oim_host, sleep_seconds=sleep_seconds)
    if not env_result["success"]:
        return env_result
    
    return {
        "success": True,
        "oim_host": oim_host,
        "login_ip": env_result["login_ip"],
        "compute_nodes": env_result["compute_nodes"],
        "compute_ips": env_result["compute_ips"],
        "error": ""
    }


def setup_all_drained_nodes(
    login_ip: str,
    user: str,
    compute_nodes: List[str],
    key_path: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Set up test with all compute nodes drained.
    
    Args:
        login_ip: admin IP of the login node
        user: SSH username
        compute_nodes: list of compute node hostnames to drain
        key_path: optional SSH private key path
        timeout: seconds to wait for each node to reach drain state
        
    Returns:
        Dict with 'success', 'nodes', 'job_ids', 'error'
    """
    # Drain all nodes
    drain_result = drain_all_nodes(login_ip, user, compute_nodes, timeout=timeout, key_path=key_path)
    if not drain_result["success"]:
        return {
            "success": False,
            "nodes": compute_nodes,
            "job_ids": [],
            "error": drain_result["error"]
        }
    
    return {
        "success": True,
        "nodes": compute_nodes,
        "job_ids": [],
        "error": ""
    }


def setup_single_drained_node(
    login_ip: str,
    user: str,
    compute_nodes: List[str],
    node_index: int = 0,
    key_path: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Set up test with a single compute node drained.
    
    Args:
        login_ip: admin IP of the login node
        user: SSH username
        compute_nodes: list of compute node hostnames
        node_index: index of node to drain (default: 0 for first node)
        key_path: optional SSH private key path
        timeout: seconds to wait for node to reach drain state
        
    Returns:
        Dict with 'success', 'node', 'job_ids', 'error'
    """
    if node_index >= len(compute_nodes):
        return {
            "success": False,
            "node": "",
            "job_ids": [],
            "error": f"Node index {node_index} out of range (0-{len(compute_nodes)-1})"
        }
    
    node = compute_nodes[node_index]
    
    # Drain the specified node
    drain_result = drain_single_node(login_ip, user, node, timeout=timeout, key_path=key_path)
    if not drain_result["success"]:
        return {
            "success": False,
            "node": node,
            "job_ids": [],
            "error": drain_result["error"]
        }
    
    return {
        "success": True,
        "node": node,
        "job_ids": [],
        "error": ""
    }


def cleanup_drain_test(
    login_ip: str,
    user: str,
    compute_nodes: List[str],
    job_ids: List[str] = None,
    key_path: Optional[str] = None,
) -> None:
    """Clean up after drain/resume tests.
    
    This is a wrapper around cleanup_test_env for convenience.
    
    Args:
        login_ip: admin IP of the login node
        user: SSH username
        compute_nodes: list of compute node hostnames to resume
        job_ids: optional list of job IDs to cancel
        key_path: optional SSH private key path
    """
    cleanup_test_env(login_ip, user, compute_nodes, job_ids, key_path)


def setup_test_env_with_all_drained(oim_host, sleep_seconds: int = 30) -> Dict[str, Any]:
    """Set up test environment with all compute nodes drained.
    
    This is a convenience function that combines setup_drain_test_env and setup_all_drained_nodes.
    
    Args:
        oim_host: testinfra host object connected to OIM server
        sleep_seconds: sleep duration for job script
        
    Returns:
        Dict with 'success', 'login_ip', 'compute_nodes', 'job_ids', 'error'
    """
    # Set up test environment
    env_result = setup_drain_test_env(oim_host, sleep_seconds)
    if not env_result["success"]:
        return env_result
    
    # Drain all nodes
    drain_result = setup_all_drained_nodes(
        env_result["login_ip"], "root", env_result["compute_nodes"]
    )
    if not drain_result["success"]:
        return {
            "success": False,
            "login_ip": env_result["login_ip"],
            "compute_nodes": env_result["compute_nodes"],
            "job_ids": [],
            "error": drain_result["error"]
        }
    
    return {
        "success": True,
        "login_ip": env_result["login_ip"],
        "compute_nodes": env_result["compute_nodes"],
        "job_ids": drain_result["job_ids"],
        "error": ""
    }


# =============================================================================
# PAM TEST FIXTURE HELPERS
# =============================================================================

def setup_pam_test_env(oim_host, sleep_seconds: int = 60) -> Dict[str, Any]:
    """Set up test environment for PAM SSH access tests.
    
    Args:
        oim_host: testinfra host object connected to OIM server
        sleep_seconds: sleep duration for job script
        
    Returns:
        Dict with 'success', 'oim_host', 'login_ip', 'compute_nodes', 
             'compute_node', 'compute_ip', 'error'
    """
    env_result = setup_slurm_test_env(oim_host, sleep_seconds=sleep_seconds)
    if not env_result["success"]:
        return env_result
    
    compute_node = env_result["compute_nodes"][0]
    compute_ip = env_result["compute_ips"][0] if env_result["compute_ips"] else None
    
    if not compute_ip:
        return {
            "success": False,
            "oim_host": oim_host,
            "login_ip": env_result["login_ip"],
            "compute_nodes": env_result["compute_nodes"],
            "compute_node": "",
            "compute_ip": None,
            "error": f"Could not resolve IP for compute node {compute_node}"
        }
    
    return {
        "success": True,
        "oim_host": oim_host,
        "login_ip": env_result["login_ip"],
        "compute_nodes": env_result["compute_nodes"],
        "compute_node": compute_node,
        "compute_ip": compute_ip,
        "error": ""
    }


def setup_running_job_for_pam(
    login_ip: str,
    compute_node: str,
    user: str = "root",
    sleep_seconds: int = 60,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Set up a running job for PAM SSH access tests.
    
    Args:
        login_ip: admin IP of the login node
        compute_node: compute node hostname to target
        user: SSH username
        sleep_seconds: sleep duration for the job
        key_path: optional SSH private key path
        
    Returns:
        Dict with 'success', 'job_id', 'job_ids', 'error'
    """
    job_ids = []
    
    # Create a longer sleep job
    script_result = create_job_script(login_ip, user, sleep_seconds=sleep_seconds, key_path=key_path)
    if not script_result["success"]:
        return {"success": False, "job_id": None, "job_ids": [], "error": script_result["error"]}
    
    # Submit job targeting specific compute node
    submit_result = submit_job_direct(login_ip, user, nodelist=compute_node, key_path=key_path)
    if not submit_result["success"]:
        return {"success": False, "job_id": None, "job_ids": [], "error": submit_result["error"]}
    
    job_id = submit_result["job_id"]
    job_ids.append(job_id)
    
    # Wait for job to reach RUNNING state
    wait_result = wait_job_running(login_ip, user, job_id, timeout=120, key_path=key_path)
    if wait_result["state"] != "RUNNING":
        return {
            "success": False, 
            "job_id": job_id, 
            "job_ids": job_ids,
            "error": f"Job did not reach RUNNING state: {wait_result['state']}"
        }
    
    return {
        "success": True,
        "job_id": job_id,
        "job_ids": job_ids,
        "error": ""
    }


def cleanup_pam_test(
    login_ip: str,
    user: str,
    compute_nodes: List[str],
    job_ids: List[str] = None,
    key_path: Optional[str] = None,
) -> None:
    """Clean up after PAM SSH access tests.
    
    Args:
        login_ip: admin IP of the login node
        user: SSH username
        compute_nodes: list of compute node hostnames to resume
        job_ids: optional list of job IDs to cancel
        key_path: optional SSH private key path
    """
    cleanup_test_env(login_ip, user, compute_nodes, job_ids, key_path)


# =============================================================================
# RESOURCE LIMIT TEST FIXTURE HELPERS
# =============================================================================

def setup_resource_limit_test_env() -> Dict[str, Any]:
    """Set up test environment for resource limit tests.
    
    Returns:
        Dict with 'success', 'login_ip', 'error'
    """
    from automation_library.core.host import get_nodes_info
    
    oim_host = get_testinfra_host()
    
    # Discover login nodes
    login_nodes_info = get_nodes_info(oim_host, search_by="functional_group", search_value="login_node_x86_64")
    login_ips = [node["admin_ip"] for node in login_nodes_info if node.get("admin_ip")]
    
    if not login_ips:
        return {
            "success": False,
            "login_ip": "",
            "error": "No login node IPs found in PXE mapping"
        }
    
    # Find reachable login node
    result = find_reachable_login_node(oim_host, login_ips)
    if not result["success"]:
        return {
            "success": False,
            "login_ip": "",
            "error": f"No reachable login nodes found from: {login_ips}"
        }
    
    return {
        "success": True,
        "login_ip": result["login_ip"],
        "error": ""
    }


def get_cluster_resources(login_ip: str, user: str = "root", key_path: Optional[str] = None) -> Dict[str, Any]:
    """Get cluster resource information (CPUs and memory per node).

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'node', 'cpus', 'memory_mb', 'error'
    """
    # Get node name and CPUs: sinfo -h -N -o "%N %c" | head -1
    res = ssh_cmd_direct(login_ip, user, 'sinfo -h -N -o "%N %c" | head -1', key_path)
    if res.returncode != 0 or not res.stdout.strip():
        return {"success": False, "node": "", "cpus": 0, "memory_mb": 0,
                "error": res.stderr or "sinfo failed"}

    parts = res.stdout.strip().split()
    node = parts[0] if parts else ""
    cpus = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0

    # Get memory: sinfo -h -N -o "%N %m" | head -1
    res_mem = ssh_cmd_direct(login_ip, user, 'sinfo -h -N -o "%N %m" | head -1', key_path)
    memory_mb = 0
    if res_mem.returncode == 0 and res_mem.stdout.strip():
        mem_parts = res_mem.stdout.strip().split()
        if len(mem_parts) > 1 and mem_parts[1].isdigit():
            memory_mb = int(mem_parts[1])

    return {
        "success": True,
        "node": node,
        "cpus": cpus,
        "memory_mb": memory_mb,
        "error": ""
    }


def create_resource_job_script(
    login_ip: str,
    user: str = "root",
    cpus: int = None,
    memory_mb: int = None,
    job_name: str = "resource_test",
    sleep_seconds: int = 30,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a job script with specified resource requirements.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        cpus: number of CPUs to request (optional)
        memory_mb: memory in MB to request (optional)
        job_name: name for the job
        sleep_seconds: sleep duration for the job
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'path', 'error'
    """
    script_path = "/tmp/resource_test_job.sh"

    # Build SBATCH directives
    sbatch_lines = [
        "#!/bin/bash",
        f"#SBATCH --job-name={job_name}",
        "#SBATCH --output=/tmp/resource_test_output.txt",
        "#SBATCH --error=/tmp/resource_test_error.txt",
        "#SBATCH --time=0-00:30:00",
    ]

    if cpus is not None:
        sbatch_lines.append(f"#SBATCH --cpus-per-task={cpus}")

    if memory_mb is not None:
        # Convert MB to format Slurm expects (M suffix)
        sbatch_lines.append(f"#SBATCH --mem={memory_mb}M")

    sbatch_lines.extend([
        "",
        'echo "Starting resource test job..."',
        f"sleep {sleep_seconds}",
        'echo "Job completed."',
    ])

    script_content = "\n".join(sbatch_lines)

    # Write script to login node
    cmd = f"cat > {script_path} << 'EOFSCRIPT'\n{script_content}\nEOFSCRIPT\nchmod +x {script_path}"
    res = ssh_cmd_direct(login_ip, user, cmd, key_path)

    if res.returncode != 0:
        return {"success": False, "path": script_path, "error": res.stderr or res.stdout}

    return {"success": True, "path": script_path, "error": ""}


def submit_resource_job_script(
    login_ip: str,
    user: str = "root",
    script_path: str = "/tmp/resource_test_job.sh",
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a job script via sbatch.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        script_path: path to the job script
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'job_id', 'error'
    """
    res = ssh_cmd_direct(login_ip, user, f"sbatch --parsable {script_path}", key_path)

    if res.returncode != 0:
        return {"success": False, "job_id": None, "error": res.stderr or res.stdout}

    raw_id = res.stdout.strip().split()[0] if res.stdout.strip() else ""
    if not raw_id or not raw_id.isdigit():
        return {"success": False, "job_id": None, "error": f"Expected numeric job id, got: {raw_id!r}"}

    return {"success": True, "job_id": raw_id, "error": ""}


def cleanup_resource_test(
    login_ip: str,
    user: str = "root",
    job_ids: List[str] = None,
    key_path: Optional[str] = None,
) -> None:
    """Cleanup job script and cancel any jobs.

    Args:
        login_ip: admin IP of the login node
        user: SSH username
        job_ids: optional list of job IDs to cancel
        key_path: optional SSH private key path
    """
    if job_ids:
        cleanup_jobs_direct(login_ip, user, job_ids, key_path)
    ssh_cmd_direct(login_ip, user, "rm -f /tmp/resource_test_job.sh /tmp/resource_test_output.txt /tmp/resource_test_error.txt", key_path)
