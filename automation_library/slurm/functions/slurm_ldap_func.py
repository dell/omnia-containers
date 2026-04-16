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
Slurm LDAP user operations for OMNIA test automation.

Verifies LDAP user SSH login, PAM (pam_slurm_adopt) behavior,
and OpenMPI job submission as ldapuser.
"""

import base64
import os
import random
import re
import string
import time
from typing import Dict, Any, List, Optional, Tuple

from automation_library.core import (
    load_input_file,
    load_user_config,
    run_on_remote_node,
)
from automation_library.core.vars import STORAGE_CONFIG_FILE
# LDAP user creation skipped - using existing credentials from user_config.yml
from automation_library.slurm.vars.slurm_vars import (
    SLURM_CONTROL_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_FUNCTIONAL_GROUP,
    LOGIN_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
    LDAP_LOGIN_ALLOWED_GROUPS,
    SSH_TIMEOUT,
    PAM_SLEEP_JOB_DURATION,
    PAM_JOB_POLL_INTERVAL,
    PAM_JOB_RUNNING_TIMEOUT,
    PAM_JOB_COMPLETE_TIMEOUT,
    PAM_LOGIN_RETRY_DELAY,
    PAM_LOGIN_RETRIES,
    SACCT_POLL_INTERVAL,
    SACCT_TIMEOUT,
    MULTI_JOB_COUNT,
)
from automation_library.slurm.messages.slurm_msgs import (
    LDAP_LOGIN_PASSED,
    LDAP_LOGIN_FAILED,
    LDAP_LOGIN_BLOCKED_PASSED,
    LDAP_LOGIN_BLOCKED_FAILED,
    LDAP_CREDS_MISSING,
    LDAP_SETUP_FAILED,
    PAM_TEST_PASSED,
    PAM_TEST_FAILED,
    PAM_JOB_SUBMIT_FAILED,
    PAM_JOB_NOT_RUNNING,
    PAM_LOGIN_DURING_JOB_FAILED,
    PAM_LOGIN_AFTER_JOB_OK,
    PAM_NO_ALLOCATED_NODES,
    MPI_JOB_PASSED,
    MPI_JOB_FAILED,
    MPI_SUBMIT_FAILED,
    MPI_NO_LOGIN_COMPILER,
    MPI_OUTPUT_VERIFICATION_FAILED,
    QUEUE_TEST_PASSED,
    QUEUE_TEST_FAILED,
    QUEUE_FIRST_NOT_RUNNING,
    QUEUE_SECOND_NOT_PENDING,
    LDAP_JOB_SINGLE_PASSED,
    LDAP_JOB_SINGLE_FAILED,
    LDAP_JOB_MULTI_PASSED,
    LDAP_JOB_MULTI_FAILED,
    LDAP_JOB_ALLNODES_PASSED,
    LDAP_JOB_ALLNODES_FAILED,
    LDAP_LOGIN_CONTROL_PASSED,
    LDAP_LOGIN_CONTROL_FAILED,
    LDAP_LOGIN_LOGIN_PASSED,
    LDAP_LOGIN_LOGIN_FAILED,
    LDAP_LOGIN_LOGINCOMP_PASSED,
    LDAP_LOGIN_LOGINCOMP_FAILED,
    INVALID_LDAP_USER_PASSED,
    INVALID_LDAP_USER_FAILED,
    INVALID_LDAP_PASS_PASSED,
    INVALID_LDAP_PASS_FAILED,
    LDAP_HOME_PERMS_PASSED,
    LDAP_HOME_PERMS_FAILED,
    LDAP_HOME_PERMS_ALL_PASSED,
    LDAP_HOME_PERMS_ALL_FAILED,
)
from .slurm_func import (
    _safe_run_on_remote_node,
    _FakeResult,
    get_slurm_control_nodes,
    get_slurm_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
    get_slurm_node_count,
    _get_all_login_nodes,
)


# =============================================================================
# LDAP CREDENTIAL & SSH HELPERS
# =============================================================================

def _get_ldap_credentials() -> Dict[str, str]:
    """Read LDAP credentials from user_config.yml.

    Reads ldap_credentials in 'username:password' format (supports comma-
    separated list; only the first pair is used).  Falls back to legacy
    ldap_user / ldap_password keys for backwards compatibility.
    """
    config = load_user_config()

    # Primary: ldap_credentials: "user:password" or "user:pass,user2:pass2"
    ldap_credentials = config.get("ldap_credentials", "")
    if ldap_credentials:
        first_cred = ldap_credentials.split(",")[0].strip()
        if ":" in first_cred:
            ldap_user, ldap_password = first_cred.split(":", 1)
            ldap_user = ldap_user.strip()
            ldap_password = ldap_password.strip()
            if ldap_user and ldap_password:
                return {
                    "ldap_user": ldap_user,
                    "ldap_password": ldap_password,
                    "error": "",
                }

    # Fallback: legacy separate keys
    ldap_user = config.get("ldap_user", "")
    ldap_password = config.get("ldap_password", "")
    if ldap_user and ldap_password:
        return {
            "ldap_user": ldap_user,
            "ldap_password": ldap_password,
            "error": "",
        }

    return {"error": LDAP_CREDS_MISSING}


def _get_all_ldap_credentials() -> Dict[str, Any]:
    """Read ALL LDAP credentials from user_config.yml.

    Reads ldap_credentials in 'username:password' format.  Supports comma-
    separated list for multiple users: "user1:pwd1, user2:pwd2, ...".
    Falls back to legacy ldap_user / ldap_password keys (single user).

    Returns:
        Dict with 'users' (list of dicts with ldap_user/ldap_password)
        and 'error' (empty string on success).
    """
    config = load_user_config()

    users = []

    # Primary: ldap_credentials: "user:password" or "user:pass,user2:pass2"
    ldap_credentials = config.get("ldap_credentials", "")
    if ldap_credentials:
        for cred_pair in ldap_credentials.split(","):
            cred_pair = cred_pair.strip()
            if ":" in cred_pair:
                ldap_user, ldap_password = cred_pair.split(":", 1)
                ldap_user = ldap_user.strip()
                ldap_password = ldap_password.strip()
                if ldap_user and ldap_password:
                    users.append({
                        "ldap_user": ldap_user,
                        "ldap_password": ldap_password,
                    })

    if users:
        return {"users": users, "error": ""}

    # Fallback: legacy separate keys
    ldap_user = config.get("ldap_user", "")
    ldap_password = config.get("ldap_password", "")
    if ldap_user and ldap_password:
        return {
            "users": [{"ldap_user": ldap_user, "ldap_password": ldap_password}],
            "error": "",
        }

    return {"users": [], "error": LDAP_CREDS_MISSING}


def _ldap_ssh_login(host, target_ip: str, ldap_user: str,
                    ldap_password: str) -> Dict[str, Any]:
    """Test SSH login to a node as ldapuser using sshpass from OIM.

    Runs 'whoami' on the target node to verify the logged-in identity.

    Returns:
        Dict with login_success, whoami_output, output, error.
    """
    ssh_cmd = (
        f"sshpass -p '{ldap_password}' ssh "
        f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        f"-o ConnectTimeout={SSH_TIMEOUT} "
        f"{ldap_user}@{target_ip} 'whoami'"
    )
    try:
        cmd = host.run(ssh_cmd)
        whoami_output = cmd.stdout.strip()
        login_ok = cmd.rc == 0 and whoami_output == ldap_user
        return {
            "login_success": login_ok,
            "whoami_output": whoami_output,
            "output": whoami_output,
            "rc": cmd.rc,
            "error": cmd.stderr.strip() if not login_ok else "",
        }
    except RuntimeError as exc:
        return {
            "login_success": False,
            "whoami_output": "",
            "output": "",
            "error": f"SSH connection failed: {exc}",
        }


def _run_as_ldapuser(host, target_ip: str, ldap_user: str,
                     ldap_password: str, command: str) -> Dict[str, Any]:
    """Run a command as ldapuser on a target node via sshpass from OIM.

    Returns:
        Dict with success, rc, stdout, stderr.
    """
    ssh_cmd = (
        f"sshpass -p '{ldap_password}' ssh "
        f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        f"-o ConnectTimeout={SSH_TIMEOUT} "
        f"{ldap_user}@{target_ip} '{command}'"
    )
    try:
        cmd = host.run(ssh_cmd)
        return {
            "success": cmd.rc == 0,
            "rc": cmd.rc,
            "stdout": cmd.stdout.strip(),
            "stderr": cmd.stderr.strip(),
        }
    except RuntimeError as exc:
        return {
            "success": False,
            "rc": 255,
            "stdout": "",
            "stderr": f"SSH connection failed: {exc}",
        }


def _setup_ldap_user(host) -> Dict[str, Any]:
    """Common setup: validate credentials for LDAP user login testing.

    Returns:
        Dict with success, ldap_user, ldap_password, error.
    """
    creds = _get_ldap_credentials()
    if creds.get("error"):
        return {"success": False, "ldap_user": "", "ldap_password": "",
                "error": creds["error"]}

    # Skip user creation - just test SSH login with existing credentials
    return {
        "success": True,
        "ldap_user": creds["ldap_user"],
        "ldap_password": creds["ldap_password"],
        "error": "",
    }


def _setup_all_ldap_users(host) -> Dict[str, Any]:
    """Common setup: validate ALL LDAP credentials for multi-user testing.

    Returns:
        Dict with success, users (list of {ldap_user, ldap_password}), error.
    """
    all_creds = _get_all_ldap_credentials()
    if all_creds.get("error"):
        return {"success": False, "users": [], "error": all_creds["error"]}

    return {
        "success": True,
        "users": all_creds["users"],
        "error": "",
    }


# =============================================================================
# LDAP HOME DIRECTORY PERMISSIONS
# =============================================================================

def set_ldapuser_home_permissions(host) -> Dict[str, Any]:
    """Set write and execute permissions on /home/<ldapuser>/ across all cluster nodes.

    Ensures each LDAP user can write and execute files in their home directory.
    Runs 'chmod u+rwx /home/<user>' as root on all slurm cluster nodes
    (control, compute, login, login_compiler).

    Returns:
        Dict with success, message, user_results (list), error.
    """
    all_creds = _get_all_ldap_credentials()
    if all_creds.get("error"):
        return {"success": False, "message": all_creds["error"],
                "user_results": [], "error": all_creds["error"]}

    users = all_creds["users"]

    # Gather all cluster nodes
    all_nodes = []
    control = get_slurm_control_nodes(host)
    if control:
        all_nodes.extend(control)
    slurm = get_slurm_nodes(host)
    if slurm:
        all_nodes.extend(slurm)
    login = get_login_nodes(host)
    if login:
        all_nodes.extend(login)
    login_comp = get_login_compiler_nodes(host)
    if login_comp:
        all_nodes.extend(login_comp)

    if not all_nodes:
        return {"success": False, "message": "No cluster nodes found",
                "user_results": [], "error": "No cluster nodes found"}

    all_passed = True
    user_results = []

    for user_cred in users:
        ldap_user = user_cred["ldap_user"]
        user_details = []
        user_ok = True

        for node in all_nodes:
            hostname = node.get("hostname", "unknown")
            admin_ip = node.get("admin_ip", "")
            if not admin_ip:
                user_details.append({
                    "hostname": hostname, "admin_ip": "",
                    "success": False, "error": "No IP available",
                })
                user_ok = False
                continue

            mkdir_cmd = (
                f"mkdir -p /home/{ldap_user} 2>/dev/null && "
                f"chown {ldap_user}:{ldap_user} /home/{ldap_user} 2>/dev/null && "
                f"chmod u+rwx /home/{ldap_user} 2>/dev/null && "
                f"ls -ld /home/{ldap_user}"
            )
            cmd = _safe_run_on_remote_node(host, mkdir_cmd, admin_ip)
            ok = cmd.rc == 0
            user_details.append({
                "hostname": hostname, "admin_ip": admin_ip,
                "success": ok,
                "output": cmd.stdout.strip() if ok else "",
                "error": cmd.stderr.strip() if not ok else "",
            })
            if not ok:
                user_ok = False

        user_results.append({
            "ldap_user": ldap_user,
            "success": user_ok,
            "message": (LDAP_HOME_PERMS_PASSED.format(user=ldap_user)
                        if user_ok
                        else LDAP_HOME_PERMS_FAILED.format(
                            user=ldap_user, error="See node details")),
            "node_details": user_details,
        })
        if not user_ok:
            all_passed = False

    msg = (LDAP_HOME_PERMS_ALL_PASSED.format(count=len(users))
           if all_passed
           else LDAP_HOME_PERMS_ALL_FAILED)
    return {
        "success": all_passed,
        "message": msg,
        "user_results": user_results,
        "error": "" if all_passed else msg,
    }


# =============================================================================
# JOB HELPERS
# =============================================================================

def _transfer_job_script(host, control_ip: str, script_local_path: str,
                         remote_path: str,
                         replacements: Dict[str, str]) -> Dict[str, Any]:
    """Read a local job script, apply replacements, and transfer to remote node.

    Returns:
        Dict with success and error.
    """
    with open(script_local_path, "r", encoding="utf-8") as f:
        content = f.read()

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    encoded = base64.b64encode(content.encode()).decode()
    cmd = _safe_run_on_remote_node(
        host,
        f"echo {encoded} | base64 -d > {remote_path} && chmod a+rx {remote_path}",
        control_ip,
    )
    if cmd.rc != 0:
        return {"success": False, "error": cmd.stderr.strip()}
    return {"success": True, "error": ""}


def _poll_job_state(host, control_ip: str, job_id: str,
                    target_state: str, timeout: int,
                    poll_interval: int) -> str:
    """Poll squeue/sacct until job reaches target_state or terminal state.

    Args:
        target_state: State to wait for (e.g., "RUNNING", "COMPLETED").
        timeout: Max seconds to wait.
        poll_interval: Seconds between polls.

    Returns:
        The observed job state.
    """
    start = time.time()
    observed = ""
    while time.time() - start < timeout:
        time.sleep(poll_interval)
        if target_state == "RUNNING":
            cmd = _safe_run_on_remote_node(
                host, f"squeue -j {job_id} -h -o '%T' 2>/dev/null", control_ip,
            )
        else:
            cmd = _safe_run_on_remote_node(
                host,
                f"sacct -j {job_id} --format=JobID,State -n -P 2>/dev/null",
                control_ip,
            )

        if cmd.rc != 0:
            continue

        if target_state == "RUNNING":
            observed = cmd.stdout.strip()
        else:
            for line in cmd.stdout.strip().split('\n'):
                parts = line.strip().split('|')
                if len(parts) >= 2 and parts[0] == job_id:
                    observed = parts[1].strip()
                    break

        if observed == target_state:
            return observed
        if observed in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"):
            return observed

    return observed


def _expand_nodelist(host, control_ip: str, nodelist_str: str) -> List[str]:
    """Expand Slurm nodelist notation (e.g., 'node[01-03]') into individual hostnames."""
    expand_cmd = _safe_run_on_remote_node(
        host,
        f"scontrol show hostname {nodelist_str} 2>/dev/null",
        control_ip,
    )
    if expand_cmd.rc == 0 and expand_cmd.stdout.strip():
        return [n.strip() for n in expand_cmd.stdout.strip().split('\n') if n.strip()]
    return [nodelist_str]


def _get_job_allocated_nodes(host, control_ip: str,
                             job_id: str) -> List[str]:
    """Get the list of node hostnames allocated to a running job (via squeue)."""
    cmd = _safe_run_on_remote_node(
        host,
        f"squeue -j {job_id} -h -o '%N' 2>/dev/null",
        control_ip,
    )
    if cmd.rc != 0 or not cmd.stdout.strip():
        return []
    return _expand_nodelist(host, control_ip, cmd.stdout.strip())


def _get_completed_job_nodes(host, control_ip: str,
                             job_id: str) -> List[str]:
    """Get the list of node hostnames from a completed job (via sacct)."""
    cmd = _safe_run_on_remote_node(
        host,
        f"sacct -j {job_id} --format=NodeList -n -P 2>/dev/null | head -1",
        control_ip,
    )
    if cmd.rc != 0 or not cmd.stdout.strip() or cmd.stdout.strip() == "None assigned":
        return []
    return _expand_nodelist(host, control_ip, cmd.stdout.strip())


def _get_node_ip_map(host) -> Dict[str, str]:
    """Build a hostname -> admin_ip map for slurm nodes."""
    nodes = get_slurm_nodes(host)
    return {n.get("hostname", ""): n.get("admin_ip", "") for n in nodes if n.get("hostname")}


# =============================================================================
# VERIFICATION FUNCTIONS
# =============================================================================

def verify_ldapuser_login(host) -> Dict[str, Any]:
    """Verify all LDAP users can SSH login to login, login_compiler, and control nodes.

    Tests each user from ldap_credentials on every node.

    Returns:
        Dict with success, message, ldap_users, group_details, error.
    """
    setup = _setup_all_ldap_users(host)
    if not setup["success"]:
        return {"success": False, "message": setup["error"],
                "ldap_users": [], "group_details": {}, "error": setup["error"]}

    users = setup["users"]

    nodes_grouped = {}
    control_nodes = get_slurm_control_nodes(host)
    if control_nodes:
        nodes_grouped[SLURM_CONTROL_NODE_FUNCTIONAL_GROUP] = control_nodes
    login_nodes = get_login_nodes(host)
    if login_nodes:
        nodes_grouped[LOGIN_NODE_FUNCTIONAL_GROUP] = login_nodes
    login_compiler_nodes = get_login_compiler_nodes(host)
    if login_compiler_nodes:
        nodes_grouped[LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP] = login_compiler_nodes

    if not nodes_grouped:
        return {"success": False, "message": "No login/control nodes found",
                "ldap_users": [], "group_details": {}, "error": "No login/control nodes found"}

    all_passed = True
    group_details = {}

    for func_group, nodes in nodes_grouped.items():
        group_details[func_group] = []
        for node in nodes:
            hostname = node.get("hostname", "unknown")
            admin_ip = node.get("admin_ip", "")
            if not admin_ip:
                group_details[func_group].append({
                    "hostname": hostname, "admin_ip": "",
                    "login_success": False, "user_results": [],
                    "error": "No IP available",
                })
                all_passed = False
                continue

            node_ok = True
            user_results = []
            for user_cred in users:
                ldap_user = user_cred["ldap_user"]
                ldap_password = user_cred["ldap_password"]
                result = _ldap_ssh_login(host, admin_ip, ldap_user, ldap_password)
                user_results.append({
                    "ldap_user": ldap_user,
                    "login_success": result["login_success"],
                    "whoami_output": result.get("whoami_output", ""),
                    "error": result["error"],
                })
                if not result["login_success"]:
                    node_ok = False

            group_details[func_group].append({
                "hostname": hostname, "admin_ip": admin_ip,
                "login_success": node_ok,
                "user_results": user_results,
                "error": "" if node_ok else "One or more users failed login",
            })
            if not node_ok:
                all_passed = False

    ldap_usernames = [u["ldap_user"] for u in users]
    return {
        "success": all_passed,
        "message": LDAP_LOGIN_PASSED if all_passed else LDAP_LOGIN_FAILED,
        "ldap_users": ldap_usernames,
        "group_details": group_details,
        "error": "" if all_passed else LDAP_LOGIN_FAILED,
    }


def verify_ldapuser_blocked_on_slurm_nodes(host) -> Dict[str, Any]:
    """Verify all LDAP users login fails on slurm nodes when no jobs are running.

    Tests each user from ldap_credentials on every slurm compute node.

    Returns:
        Dict with success, message, ldap_users, details, error.
    """
    setup = _setup_all_ldap_users(host)
    if not setup["success"]:
        return {"success": False, "message": setup["error"],
                "ldap_users": [], "details": [], "error": setup["error"]}

    users = setup["users"]

    slurm_nodes = get_slurm_nodes(host)
    if not slurm_nodes:
        return {"success": False, "message": "No slurm nodes found",
                "ldap_users": [], "details": [], "error": "No slurm nodes found"}

    all_correct = True
    details = []

    for node in slurm_nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({
                "hostname": hostname, "admin_ip": "",
                "login_blocked": False, "user_results": [],
                "error": "No IP available",
            })
            all_correct = False
            continue

        node_ok = True
        user_results = []
        for user_cred in users:
            ldap_user = user_cred["ldap_user"]
            ldap_password = user_cred["ldap_password"]
            result = _ldap_ssh_login(host, admin_ip, ldap_user, ldap_password)
            login_blocked = not result["login_success"]
            user_results.append({
                "ldap_user": ldap_user,
                "login_blocked": login_blocked,
                "error": "" if login_blocked else "Login should have been blocked",
            })
            if not login_blocked:
                node_ok = False

        details.append({
            "hostname": hostname, "admin_ip": admin_ip,
            "login_blocked": node_ok,
            "user_results": user_results,
            "error": "" if node_ok else "One or more users were not blocked",
        })
        if not node_ok:
            all_correct = False

    ldap_usernames = [u["ldap_user"] for u in users]
    return {
        "success": all_correct,
        "message": LDAP_LOGIN_BLOCKED_PASSED if all_correct else LDAP_LOGIN_BLOCKED_FAILED,
        "ldap_users": ldap_usernames,
        "details": details,
        "error": "" if all_correct else LDAP_LOGIN_BLOCKED_FAILED,
    }


def _verify_pam_support(host, submit_node_ip: str,
                        submit_node_hostname: str,
                        source_label: str) -> Dict[str, Any]:
    """Core PAM verification logic used by both login-node and control-node tests.

    1. Transfer sleep job to submit_node (as root).
    2. Submit job as ldapuser from submit_node via sshpass.
    3. Wait for RUNNING state.
    4. Verify ldapuser CAN login to allocated slurm nodes.
    5. Wait for job to complete.
    6. Verify ldapuser can NO LONGER login to allocated slurm nodes.

    Returns:
        Dict with success, message, steps (list of step results), error.
    """
    setup = _setup_ldap_user(host)
    if not setup["success"]:
        return {"success": False, "message": setup["error"],
                "steps": [], "error": setup["error"]}

    ldap_user = setup["ldap_user"]
    ldap_password = setup["ldap_password"]

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": "No control nodes",
                "steps": [], "error": "No slurm control nodes found"}
    control_ip = control_nodes[0].get("admin_ip", "")

    steps = []

    # Step 1: Transfer sleep job script to submit node (as root)
    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    remote_script = "/home/omnia_test_sleep.sh"
    xfer = _transfer_job_script(
        host, submit_node_ip,
        os.path.join(jobs_dir, "sleep_sbatch.sh"),
        remote_script,
        {"{{SLEEP_DURATION}}": str(PAM_SLEEP_JOB_DURATION),
         "{{OUTPUT_PATH}}": f"/home/{ldap_user}"},
    )
    if not xfer["success"]:
        return {"success": False,
                "message": f"Failed to transfer sleep job: {xfer['error']}",
                "steps": steps, "error": xfer["error"]}
    steps.append({"step": "transfer_script", "success": True})

    # Step 2: Submit job as ldapuser from submit_node
    submit_result = _run_as_ldapuser(
        host, submit_node_ip, ldap_user, ldap_password,
        f"sbatch {remote_script}",
    )
    if not submit_result["success"]:
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", submit_node_ip)
        return {
            "success": False,
            "message": PAM_JOB_SUBMIT_FAILED.format(error=submit_result["stderr"]),
            "steps": steps, "error": submit_result["stderr"],
        }

    match = re.search(r"Submitted batch job (\d+)", submit_result["stdout"])
    if not match:
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", submit_node_ip)
        return {
            "success": False,
            "message": f"Could not parse job ID: {submit_result['stdout']}",
            "steps": steps, "error": "Failed to parse job ID",
        }
    job_id = match.group(1)
    steps.append({"step": "submit_job", "success": True, "job_id": job_id})

    # Step 3: Wait for RUNNING state
    state = _poll_job_state(
        host, control_ip, job_id, "RUNNING",
        PAM_JOB_RUNNING_TIMEOUT, PAM_JOB_POLL_INTERVAL,
    )
    if state != "RUNNING":
        steps.append({"step": "wait_running", "success": False, "state": state})
        # Cancel job if pending
        _safe_run_on_remote_node(host, f"scancel {job_id}", control_ip)
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", submit_node_ip)
        return {
            "success": False,
            "message": PAM_JOB_NOT_RUNNING,
            "steps": steps, "error": f"Job state: {state}",
        }
    steps.append({"step": "wait_running", "success": True, "state": "RUNNING"})

    # Step 4: Get allocated nodes and verify ldapuser CAN login
    allocated = _get_job_allocated_nodes(host, control_ip, job_id)
    node_ip_map = _get_node_ip_map(host)

    if not allocated:
        steps.append({"step": "get_allocated", "success": False})
        _safe_run_on_remote_node(host, f"scancel {job_id}", control_ip)
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", submit_node_ip)
        return {
            "success": False,
            "message": PAM_NO_ALLOCATED_NODES.format(job_id=job_id),
            "steps": steps, "error": "No allocated nodes found",
        }
    steps.append({"step": "get_allocated", "success": True, "nodes": allocated})

    # Small delay to allow PAM/cgroup to register the job on allocated nodes
    time.sleep(PAM_LOGIN_RETRY_DELAY)

    login_during_ok = True
    login_during_details = []
    for node_hostname in allocated:
        node_ip = node_ip_map.get(node_hostname, "")
        if not node_ip:
            login_during_details.append({
                "node": node_hostname, "login_success": False,
                "error": "No IP found for hostname",
            })
            login_during_ok = False
            continue

        # Retry login a few times to allow PAM propagation
        login_ok = False
        last_error = ""
        for _ in range(PAM_LOGIN_RETRIES):
            result = _ldap_ssh_login(host, node_ip, ldap_user, ldap_password)
            if result["login_success"]:
                login_ok = True
                break
            last_error = result.get("error", "")
            time.sleep(PAM_LOGIN_RETRY_DELAY)

        login_during_details.append({
            "node": node_hostname, "ip": node_ip,
            "login_success": login_ok,
            "error": "" if login_ok else (
                f"{PAM_LOGIN_DURING_JOB_FAILED.format(node=node_hostname)}"
                f" | ssh_error: {last_error}"
            ),
        })
        if not login_ok:
            login_during_ok = False

    steps.append({
        "step": "login_during_job", "success": login_during_ok,
        "details": login_during_details,
    })

    # Step 5: Wait for job to complete
    state = _poll_job_state(
        host, control_ip, job_id, "COMPLETED",
        PAM_JOB_COMPLETE_TIMEOUT, PAM_JOB_POLL_INTERVAL,
    )
    steps.append({"step": "wait_complete", "success": state == "COMPLETED", "state": state})

    # Step 6: Verify ldapuser can NO LONGER login to allocated nodes
    # Wait a few seconds for PAM to revoke access
    time.sleep(PAM_LOGIN_RETRY_DELAY)

    login_after_blocked = True
    login_after_details = []
    for node_hostname in allocated:
        node_ip = node_ip_map.get(node_hostname, "")
        if not node_ip:
            login_after_details.append({
                "node": node_hostname, "login_blocked": False,
                "error": "No IP found",
            })
            login_after_blocked = False
            continue

        result = _ldap_ssh_login(host, node_ip, ldap_user, ldap_password)
        blocked = not result["login_success"]
        login_after_details.append({
            "node": node_hostname, "ip": node_ip,
            "login_blocked": blocked,
            "error": "" if blocked else PAM_LOGIN_AFTER_JOB_OK.format(node=node_hostname),
        })
        if not blocked:
            login_after_blocked = False

    steps.append({
        "step": "login_after_job", "success": login_after_blocked,
        "details": login_after_details,
    })

    # Cleanup script only (keep output files)
    _safe_run_on_remote_node(host, f"rm -f {remote_script}", submit_node_ip)

    all_passed = login_during_ok and login_after_blocked
    return {
        "success": all_passed,
        "message": PAM_TEST_PASSED if all_passed else PAM_TEST_FAILED.format(
            error="login during job or block after job failed"),
        "job_id": job_id,
        "submit_node": submit_node_hostname,
        "source": source_label,
        "steps": steps,
        "error": "" if all_passed else "PAM verification failed",
    }


def verify_pam_from_login_node(host) -> Dict[str, Any]:
    """Submit a sleep job as ldapuser from a login node, verify PAM support.

    Returns:
        Dict with success, skipped, message, steps, error.
    """
    login_nodes = get_login_nodes(host)
    if not login_nodes:
        return {"success": True, "skipped": True,
                "message": "No login nodes found in PXE mapping - skipping",
                "steps": [], "error": ""}

    node = login_nodes[0]
    result = _verify_pam_support(
        host, node.get("admin_ip", ""), node.get("hostname", "unknown"),
        "login_node",
    )
    result["skipped"] = False
    return result


def verify_pam_from_login_compiler_node(host) -> Dict[str, Any]:
    """Submit a sleep job as ldapuser from a login_compiler node, verify PAM support.

    Returns:
        Dict with success, skipped, message, steps, error.
    """
    login_compiler_nodes = get_login_compiler_nodes(host)
    if not login_compiler_nodes:
        return {"success": True, "skipped": True,
                "message": "No login compiler nodes found in PXE mapping - skipping",
                "steps": [], "error": ""}

    node = login_compiler_nodes[0]
    result = _verify_pam_support(
        host, node.get("admin_ip", ""), node.get("hostname", "unknown"),
        "login_compiler_node",
    )
    result["skipped"] = False
    return result


def verify_pam_from_control_node(host) -> Dict[str, Any]:
    """Submit a sleep job as ldapuser from the slurm control node, verify PAM support.

    Returns:
        Dict with success, message, steps, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": "No control nodes found",
                "steps": [], "error": "No slurm control nodes found"}

    node = control_nodes[0]
    return _verify_pam_support(
        host, node.get("admin_ip", ""), node.get("hostname", "unknown"),
        "slurm_control_node",
    )


def verify_openmpi_job(host) -> Dict[str, Any]:
    """Submit an OpenMPI compile+run job as ldapuser from a login_compiler node.

    The job compiles a simple MPI C program, runs it, and the output is
    verified for expected strings (Compilation successful, Hello World,
    MPI job completed successfully).

    Returns:
        Dict with success, message, job_id, job_state, job_output,
        submit_node, output_verified, error.
    """
    setup = _setup_ldap_user(host)
    if not setup["success"]:
        return {"success": False, "message": setup["error"],
                "job_id": "", "job_state": "", "job_output": "",
                "submit_node": "",
                "output_verified": False, "error": setup["error"]}

    ldap_user = setup["ldap_user"]
    ldap_password = setup["ldap_password"]

    login_compiler_nodes = get_login_compiler_nodes(host)
    if not login_compiler_nodes:
        return {"success": False, "message": MPI_NO_LOGIN_COMPILER,
                "job_id": "", "job_state": "", "job_output": "",
                "submit_node": "",
                "output_verified": False, "error": MPI_NO_LOGIN_COMPILER}

    submit_node = login_compiler_nodes[0]
    submit_ip = submit_node.get("admin_ip", "")
    submit_hostname = submit_node.get("hostname", "unknown")

    if not submit_ip:
        return {"success": False, "message": f"Login compiler node {submit_hostname} has no IP",
                "job_id": "", "job_state": "", "job_output": "",
                "submit_node": submit_hostname,
                "output_verified": False, "error": "No admin IP"}

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": "No control nodes found",
                "job_id": "", "job_state": "", "job_output": "",
                "submit_node": submit_hostname,
                "output_verified": False, "error": "No slurm control nodes found"}
    control_ip = control_nodes[0].get("admin_ip", "")

    # Read NFS client_share_path for nfs_slurm from storage_config.yml
    storage_config = load_input_file(host, STORAGE_CONFIG_FILE)
    nfs_share_path = ""
    for entry in storage_config.get("nfs_client_params", []):
        if entry.get("nfs_name") == "nfs_slurm":
            nfs_share_path = entry.get("client_share_path", "")
            break
    if not nfs_share_path:
        return {"success": False,
                "message": "Could not find client_share_path for nfs_slurm in storage_config.yml",
                "job_id": "", "job_state": "", "job_output": "",
                "submit_node": submit_hostname,
                "output_verified": False,
                "error": "nfs_slurm client_share_path not found in storage_config.yml"}

    # Transfer MPI job script to submit node (as root)
    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    remote_script = "/home/omnia_test_mpi.sh"
    xfer = _transfer_job_script(
        host, submit_ip,
        os.path.join(jobs_dir, "mpi_job.sh"),
        remote_script,
        {"{{NFS_CLIENT_SHARE_PATH}}": nfs_share_path,
         "{{OUTPUT_PATH}}": "/home"},
    )
    if not xfer["success"]:
        return {"success": False,
                "message": f"Failed to transfer MPI job: {xfer['error']}",
                "job_id": "", "job_state": "", "job_output": "",
                "submit_node": submit_hostname,
                "output_verified": False, "error": xfer["error"]}

    # Submit as root from login_compiler node
    cmd = _safe_run_on_remote_node(host, f"sbatch {remote_script}", submit_ip)
    if cmd.rc != 0:
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", submit_ip)
        return {
            "success": False,
            "message": MPI_SUBMIT_FAILED.format(error=cmd.stderr.strip()),
            "job_id": "", "job_state": "", "job_output": "",
            "submit_node": submit_hostname,
            "output_verified": False, "error": cmd.stderr.strip(),
        }

    match = re.search(r"Submitted batch job (\d+)", cmd.stdout.strip())
    if not match:
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", submit_ip)
        return {
            "success": False,
            "message": f"Could not parse MPI job ID: {cmd.stdout.strip()}",
            "job_id": "", "job_state": "", "job_output": "",
            "submit_node": submit_hostname,
            "output_verified": False, "error": "Failed to parse job ID",
        }
    job_id = match.group(1)

    # Poll for completion
    state = _poll_job_state(
        host, control_ip, job_id, "COMPLETED",
        SACCT_TIMEOUT, SACCT_POLL_INTERVAL,
    )

    # Read job output from the submit node (where output file is written)
    job_output = ""
    read_out = _safe_run_on_remote_node(
        host, f"cat /home/omnia_test_mpi_{job_id}.out 2>/dev/null", submit_ip,
    )
    if read_out.rc == 0:
        job_output = read_out.stdout.strip()
    else:
        # Try reading error file if output file doesn't exist
        read_err = _safe_run_on_remote_node(
            host, f"cat /home/omnia_test_mpi_{job_id}.err 2>/dev/null", submit_ip,
        )
        if read_err.rc == 0:
            job_output = f"ERROR: {read_err.stdout.strip()}"

    # Cleanup script only on submit node (keep output files)
    _safe_run_on_remote_node(host, f"rm -f {remote_script}", submit_ip)

    if state != "COMPLETED":
        return {
            "success": False,
            "message": MPI_JOB_FAILED.format(error=f"Job {job_id} state: {state}"),
            "job_id": job_id,
            "job_state": state or "UNKNOWN",
            "job_output": job_output,
            "submit_node": submit_hostname,
            "output_verified": False,
            "error": f"MPI job did not complete. State: {state}",
        }

    # Verify expected output strings
    expected_strings = [
        "Compilation successful",
        "Hello World from rank",
        "MPI job completed successfully",
    ]
    missing = [s for s in expected_strings if s not in job_output]
    output_verified = len(missing) == 0

    if not output_verified:
        return {
            "success": False,
            "message": MPI_OUTPUT_VERIFICATION_FAILED.format(
                error=f"Missing expected output: {missing}"),
            "job_id": job_id,
            "job_state": state,
            "job_output": job_output,
            "submit_node": submit_hostname,
            "output_verified": False,
            "error": f"Missing in output: {missing}",
        }

    return {
        "success": True,
        "message": MPI_JOB_PASSED.format(job_id=job_id),
        "job_id": job_id,
        "job_state": state,
        "job_output": job_output,
        "submit_node": submit_hostname,
        "output_verified": True,
        "error": "",
    }


def verify_job_queuing(host) -> Dict[str, Any]:
    """Verify Slurm job queuing: submit sleep job (RUNNING), submit 2nd on same node (PENDING).

    1. Submit a sleep job with --nodes=1 from the control node as root.
    2. Wait for it to reach RUNNING state and identify the allocated node.
    3. Submit a second sleep job targeting the SAME node (--nodelist).
    4. Verify the second job is in PENDING state via squeue.
    5. Cancel both jobs and cleanup.

    Returns:
        Dict with success, message, job1_id, job1_state, job2_id, job2_state,
        allocated_node, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": "No control nodes found",
                "job1_id": "", "job1_state": "", "job2_id": "", "job2_state": "",
                "allocated_node": "", "error": "No slurm control nodes found"}

    control_ip = control_nodes[0].get("admin_ip", "")
    if not control_ip:
        return {"success": False, "message": "Control node has no admin IP",
                "job1_id": "", "job1_state": "", "job2_id": "", "job2_state": "",
                "allocated_node": "", "error": "No admin IP"}

    # Transfer sleep job script to control node
    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    remote_script = "/home/omnia_test_queue.sh"
    xfer = _transfer_job_script(
        host, control_ip,
        os.path.join(jobs_dir, "sleep_sbatch.sh"),
        remote_script,
        {"{{SLEEP_DURATION}}": str(PAM_SLEEP_JOB_DURATION),
         "{{OUTPUT_PATH}}": "/home"},
    )
    if not xfer["success"]:
        return {"success": False, "message": f"Script transfer failed: {xfer['error']}",
                "job1_id": "", "job1_state": "", "job2_id": "", "job2_state": "",
                "allocated_node": "", "error": xfer["error"]}

    # Submit first sleep job
    cmd = _safe_run_on_remote_node(host, f"sbatch {remote_script}", control_ip)
    if cmd.rc != 0:
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False, "message": f"First job submit failed: {cmd.stderr.strip()}",
                "job1_id": "", "job1_state": "", "job2_id": "", "job2_state": "",
                "allocated_node": "", "error": cmd.stderr.strip()}

    match1 = re.search(r"Submitted batch job (\d+)", cmd.stdout.strip())
    if not match1:
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False, "message": f"Could not parse job1 ID: {cmd.stdout.strip()}",
                "job1_id": "", "job1_state": "", "job2_id": "", "job2_state": "",
                "allocated_node": "", "error": "Parse failed"}
    job1_id = match1.group(1)

    # Wait for first job to be RUNNING
    job1_state = _poll_job_state(
        host, control_ip, job1_id, "RUNNING",
        PAM_JOB_RUNNING_TIMEOUT, PAM_JOB_POLL_INTERVAL,
    )
    if job1_state != "RUNNING":
        _safe_run_on_remote_node(host, f"scancel {job1_id}", control_ip)
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False, "message": QUEUE_FIRST_NOT_RUNNING,
                "job1_id": job1_id, "job1_state": job1_state,
                "job2_id": "", "job2_state": "",
                "allocated_node": "", "error": f"Job1 state: {job1_state}"}

    # Get allocated node
    allocated = _get_job_allocated_nodes(host, control_ip, job1_id)
    if not allocated:
        _safe_run_on_remote_node(host, f"scancel {job1_id}", control_ip)
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False, "message": "Could not get allocated node for job1",
                "job1_id": job1_id, "job1_state": "RUNNING",
                "job2_id": "", "job2_state": "",
                "allocated_node": "", "error": "No allocated nodes"}
    target_node = allocated[0]

    # Verify job1 is RUNNING via squeue
    squeue_cmd = _safe_run_on_remote_node(
        host, f"squeue -j {job1_id} -h -o '%T %N' 2>/dev/null", control_ip,
    )
    job1_squeue = squeue_cmd.stdout.strip() if squeue_cmd.rc == 0 else ""

    # Submit second job targeting the SAME node
    cmd2 = _safe_run_on_remote_node(
        host,
        f"sbatch --nodelist={target_node} {remote_script}",
        control_ip,
    )
    if cmd2.rc != 0:
        _safe_run_on_remote_node(host, f"scancel {job1_id}", control_ip)
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False, "message": f"Second job submit failed: {cmd2.stderr.strip()}",
                "job1_id": job1_id, "job1_state": "RUNNING",
                "job2_id": "", "job2_state": "",
                "allocated_node": target_node, "error": cmd2.stderr.strip()}

    match2 = re.search(r"Submitted batch job (\d+)", cmd2.stdout.strip())
    if not match2:
        _safe_run_on_remote_node(host, f"scancel {job1_id}", control_ip)
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False, "message": f"Could not parse job2 ID: {cmd2.stdout.strip()}",
                "job1_id": job1_id, "job1_state": "RUNNING",
                "job2_id": "", "job2_state": "",
                "allocated_node": target_node, "error": "Parse failed"}
    job2_id = match2.group(1)

    # Wait a moment for scheduler, then check job2 state via squeue
    time.sleep(PAM_JOB_POLL_INTERVAL)
    squeue2 = _safe_run_on_remote_node(
        host, f"squeue -j {job2_id} -h -o '%T' 2>/dev/null", control_ip,
    )
    job2_state = squeue2.stdout.strip() if squeue2.rc == 0 else "UNKNOWN"

    # Cancel both jobs and cleanup
    _safe_run_on_remote_node(host, f"scancel {job1_id} {job2_id}", control_ip)
    # Cleanup script only (keep output files)
    _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)

    is_pending = job2_state == "PENDING"
    return {
        "success": is_pending,
        "message": QUEUE_TEST_PASSED if is_pending else QUEUE_SECOND_NOT_PENDING.format(state=job2_state),
        "job1_id": job1_id,
        "job1_state": "RUNNING",
        "job1_squeue": job1_squeue,
        "job2_id": job2_id,
        "job2_state": job2_state,
        "allocated_node": target_node,
        "error": "" if is_pending else f"Job2 state was {job2_state}, expected PENDING",
    }


# =============================================================================
# LDAP JOB SUBMISSION HELPERS
# =============================================================================

def _submit_and_poll_ldap(host, submit_ip: str, control_ip: str,
                          ldap_user: str, ldap_password: str,
                          remote_script: str) -> Dict[str, Any]:
    """Submit an sbatch job as ldapuser on *submit_ip*, poll on *control_ip*.

    Returns dict with success, job_id, job_state, error.
    """
    submit_result = _run_as_ldapuser(
        host, submit_ip, ldap_user, ldap_password,
        f"sbatch {remote_script}",
    )
    if not submit_result["success"]:
        return {"success": False, "job_id": "", "job_state": "",
                "error": submit_result["stderr"]}

    match = re.search(r"Submitted batch job (\d+)", submit_result["stdout"])
    if not match:
        return {"success": False, "job_id": "", "job_state": "",
                "error": f"Parse failed: {submit_result['stdout']}"}
    job_id = match.group(1)

    state = _poll_job_state(
        host, control_ip, job_id, "COMPLETED",
        SACCT_TIMEOUT, SACCT_POLL_INTERVAL,
    )
    return {
        "success": state == "COMPLETED",
        "job_id": job_id,
        "job_state": state or "UNKNOWN",
        "error": "" if state == "COMPLETED" else f"Job {job_id} state: {state}",
    }


# =============================================================================
# TC16: LDAP user single sbatch job from each login node
# =============================================================================

def verify_ldap_sbatch_from_login_nodes(host) -> Dict[str, Any]:
    """Submit a single sbatch job as ldapuser from each login/login_compiler node.

    Returns:
        Dict with success, message, node_results (list), error.
    """
    setup = _setup_ldap_user(host)
    if not setup["success"]:
        return {"success": False, "message": setup["error"],
                "node_results": [], "error": setup["error"]}
    ldap_user = setup["ldap_user"]
    ldap_password = setup["ldap_password"]

    all_login = _get_all_login_nodes(host)
    if not all_login:
        return {"success": False, "message": "No login or login compiler nodes found",
                "node_results": [], "error": "No login nodes"}

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": "No control nodes found",
                "node_results": [], "error": "No control nodes"}
    control_ip = control_nodes[0].get("admin_ip", "")

    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    remote_script = "/home/omnia_test_ldap_single.sh"

    all_passed = True
    node_results = []

    for node in all_login:
        hostname = node.get("hostname", "unknown")
        node_ip = node.get("admin_ip", "")
        if not node_ip:
            node_results.append({"node": hostname, "success": False,
                                 "job_id": "", "job_state": "",
                                 "error": "No admin IP"})
            all_passed = False
            continue

        xfer = _transfer_job_script(
            host, node_ip,
            os.path.join(jobs_dir, "basic_sbatch.sh"),
            remote_script,
            {"{{SLURM_NUM_NODES}}": "1", "{{OUTPUT_PATH}}": f"/home/{ldap_user}"},
        )
        if not xfer["success"]:
            node_results.append({"node": hostname, "success": False,
                                 "job_id": "", "job_state": "",
                                 "error": xfer["error"]})
            all_passed = False
            continue

        result = _submit_and_poll_ldap(
            host, node_ip, control_ip, ldap_user, ldap_password, remote_script,
        )
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", node_ip)

        node_results.append({
            "node": hostname, "success": result["success"],
            "job_id": result["job_id"], "job_state": result["job_state"],
            "error": result["error"],
        })
        if not result["success"]:
            all_passed = False

    msg = (LDAP_JOB_ALLNODES_PASSED.format(count=len(all_login))
           if all_passed
           else LDAP_JOB_ALLNODES_FAILED.format(
               error="One or more login nodes failed"))
    return {"success": all_passed, "message": msg,
            "node_results": node_results, "error": "" if all_passed else msg}


# =============================================================================
# TC17: LDAP user multiple sbatch jobs from login node
# =============================================================================

def verify_ldap_multi_sbatch_from_login_node(host) -> Dict[str, Any]:
    """Submit MULTI_JOB_COUNT sbatch jobs as ldapuser from a login node.

    Returns:
        Dict with success, message, submit_node, job_results (list), error.
    """
    setup = _setup_ldap_user(host)
    if not setup["success"]:
        return {"success": False, "message": setup["error"],
                "submit_node": "", "job_results": [],
                "error": setup["error"]}
    ldap_user = setup["ldap_user"]
    ldap_password = setup["ldap_password"]

    all_login = _get_all_login_nodes(host)
    if not all_login:
        return {"success": False, "message": "No login or login compiler nodes found",
                "submit_node": "", "job_results": [],
                "error": "No login nodes"}

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": "No control nodes found",
                "submit_node": "", "job_results": [],
                "error": "No control nodes"}
    control_ip = control_nodes[0].get("admin_ip", "")

    node = all_login[0]
    hostname = node.get("hostname", "unknown")
    node_ip = node.get("admin_ip", "")
    if not node_ip:
        return {"success": False, "message": f"Login node {hostname} has no IP",
                "submit_node": hostname, "job_results": [],
                "error": "No admin IP"}

    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    remote_script = "/home/omnia_test_ldap_multi.sh"
    xfer = _transfer_job_script(
        host, node_ip,
        os.path.join(jobs_dir, "basic_sbatch.sh"),
        remote_script,
        {"{{SLURM_NUM_NODES}}": "1", "{{OUTPUT_PATH}}": f"/home/{ldap_user}"},
    )
    if not xfer["success"]:
        return {"success": False,
                "message": f"Script transfer failed: {xfer['error']}",
                "submit_node": hostname, "job_results": [],
                "error": xfer["error"]}

    all_passed = True
    job_results = []
    for i in range(MULTI_JOB_COUNT):
        result = _submit_and_poll_ldap(
            host, node_ip, control_ip, ldap_user, ldap_password, remote_script,
        )
        job_results.append({
            "index": i + 1, "success": result["success"],
            "job_id": result["job_id"], "job_state": result["job_state"],
            "error": result["error"],
        })
        if not result["success"]:
            all_passed = False

    _safe_run_on_remote_node(host, f"rm -f {remote_script}", node_ip)

    msg = (LDAP_JOB_MULTI_PASSED.format(count=MULTI_JOB_COUNT, node=hostname)
           if all_passed
           else LDAP_JOB_MULTI_FAILED.format(node=hostname,
               error="One or more jobs failed"))
    return {"success": all_passed, "message": msg,
            "submit_node": hostname, "job_results": job_results,
            "error": "" if all_passed else msg}


# =============================================================================
# HELPER: LDAP login on a specific node type
# =============================================================================

def _verify_ldap_login_on_nodes(host, nodes: List[Dict[str, str]],
                                users: List[Dict[str, str]],
                                passed_msg: str,
                                failed_msg: str) -> Dict[str, Any]:
    """Test all LDAP users SSH login on a list of nodes.

    Args:
        users: List of dicts with ldap_user and ldap_password.

    Returns:
        Dict with success, message, ldap_users, details, error.
    """
    all_passed = True
    details = []

    for node in nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({
                "hostname": hostname, "admin_ip": "",
                "login_success": False, "user_results": [],
                "error": "No IP available",
            })
            all_passed = False
            continue

        node_ok = True
        user_results = []
        for user_cred in users:
            ldap_user = user_cred["ldap_user"]
            ldap_password = user_cred["ldap_password"]
            result = _ldap_ssh_login(host, admin_ip, ldap_user, ldap_password)
            user_results.append({
                "ldap_user": ldap_user,
                "login_success": result["login_success"],
                "whoami_output": result.get("whoami_output", ""),
                "error": result["error"],
            })
            if not result["login_success"]:
                node_ok = False

        details.append({
            "hostname": hostname, "admin_ip": admin_ip,
            "login_success": node_ok,
            "user_results": user_results,
            "error": "" if node_ok else "One or more users failed login",
        })
        if not node_ok:
            all_passed = False

    ldap_usernames = [u["ldap_user"] for u in users]
    return {
        "success": all_passed,
        "message": passed_msg if all_passed else failed_msg,
        "ldap_users": ldap_usernames,
        "details": details,
        "error": "" if all_passed else failed_msg,
    }


# =============================================================================
# Separate LDAP login test per node type
# =============================================================================

def verify_ldapuser_login_on_control_nodes(host) -> Dict[str, Any]:
    """Verify all LDAP users can SSH login to slurm control nodes.

    Returns:
        Dict with success, skipped, message, ldap_users, details, error.
    """
    setup = _setup_all_ldap_users(host)
    if not setup["success"]:
        return {"success": False, "skipped": False, "message": setup["error"],
                "ldap_users": [], "details": [], "error": setup["error"]}

    nodes = get_slurm_control_nodes(host)
    if not nodes:
        ldap_usernames = [u["ldap_user"] for u in setup["users"]]
        return {"success": True, "skipped": True,
                "message": "No slurm control nodes found in PXE mapping - skipping",
                "ldap_users": ldap_usernames, "details": [], "error": ""}

    result = _verify_ldap_login_on_nodes(
        host, nodes, setup["users"],
        LDAP_LOGIN_CONTROL_PASSED, LDAP_LOGIN_CONTROL_FAILED,
    )
    result["skipped"] = False
    return result


def verify_ldapuser_login_on_login_nodes(host) -> Dict[str, Any]:
    """Verify all LDAP users can SSH login to login nodes.

    Returns:
        Dict with success, skipped, message, ldap_users, details, error.
    """
    setup = _setup_all_ldap_users(host)
    if not setup["success"]:
        return {"success": False, "skipped": False, "message": setup["error"],
                "ldap_users": [], "details": [], "error": setup["error"]}

    nodes = get_login_nodes(host)
    if not nodes:
        ldap_usernames = [u["ldap_user"] for u in setup["users"]]
        return {"success": True, "skipped": True,
                "message": "No login nodes found in PXE mapping - skipping",
                "ldap_users": ldap_usernames, "details": [], "error": ""}

    result = _verify_ldap_login_on_nodes(
        host, nodes, setup["users"],
        LDAP_LOGIN_LOGIN_PASSED, LDAP_LOGIN_LOGIN_FAILED,
    )
    result["skipped"] = False
    return result


def verify_ldapuser_login_on_login_compiler_nodes(host) -> Dict[str, Any]:
    """Verify all LDAP users can SSH login to login compiler nodes.

    Returns:
        Dict with success, skipped, message, ldap_users, details, error.
    """
    setup = _setup_all_ldap_users(host)
    if not setup["success"]:
        return {"success": False, "skipped": False, "message": setup["error"],
                "ldap_users": [], "details": [], "error": setup["error"]}

    nodes = get_login_compiler_nodes(host)
    if not nodes:
        ldap_usernames = [u["ldap_user"] for u in setup["users"]]
        return {"success": True, "skipped": True,
                "message": "No login compiler nodes found in PXE mapping - skipping",
                "ldap_users": ldap_usernames, "details": [], "error": ""}

    result = _verify_ldap_login_on_nodes(
        host, nodes, setup["users"],
        LDAP_LOGIN_LOGINCOMP_PASSED, LDAP_LOGIN_LOGINCOMP_FAILED,
    )
    result["skipped"] = False
    return result


# =============================================================================
# Invalid LDAP credentials tests
# =============================================================================

def _generate_random_string(length: int = 12) -> str:
    """Generate a random alphanumeric string."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def verify_invalid_ldap_username(host) -> Dict[str, Any]:
    """Verify that an invalid (random) LDAP username is denied login.

    Tests on all login/login_compiler/control nodes.

    Returns:
        Dict with success, message, invalid_user, details, error.
    """
    invalid_user = "invalid_" + _generate_random_string(8)
    # Use a random password too
    invalid_password = _generate_random_string(16)

    nodes_to_test = []
    control = get_slurm_control_nodes(host)
    if control:
        nodes_to_test.extend(control)
    login = get_login_nodes(host)
    if login:
        nodes_to_test.extend(login)
    login_comp = get_login_compiler_nodes(host)
    if login_comp:
        nodes_to_test.extend(login_comp)

    if not nodes_to_test:
        return {"success": True, "skipped": True,
                "message": "No login/control nodes found in PXE mapping - skipping",
                "invalid_user": invalid_user, "details": [], "error": ""}

    all_denied = True
    details = []

    for node in nodes_to_test:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({
                "hostname": hostname, "admin_ip": "",
                "login_denied": False, "error": "No IP available",
            })
            all_denied = False
            continue

        result = _ldap_ssh_login(host, admin_ip, invalid_user, invalid_password)
        denied = not result["login_success"]
        details.append({
            "hostname": hostname, "admin_ip": admin_ip,
            "login_denied": denied,
            "error": "" if denied else "Invalid user was unexpectedly able to login",
        })
        if not denied:
            all_denied = False

    return {
        "success": all_denied, "skipped": False,
        "message": INVALID_LDAP_USER_PASSED if all_denied else INVALID_LDAP_USER_FAILED,
        "invalid_user": invalid_user,
        "details": details,
        "error": "" if all_denied else INVALID_LDAP_USER_FAILED,
    }


def verify_invalid_ldap_password(host) -> Dict[str, Any]:
    """Verify that all valid LDAP usernames with invalid (random) passwords are denied login.

    Tests each user from ldap_credentials on all login/login_compiler/control nodes.

    Returns:
        Dict with success, message, ldap_users, details, error.
    """
    all_creds = _get_all_ldap_credentials()
    if all_creds.get("error"):
        return {"success": False, "skipped": False,
                "message": all_creds["error"],
                "ldap_users": [], "details": [], "error": all_creds["error"]}

    users = all_creds["users"]
    ldap_usernames = [u["ldap_user"] for u in users]

    nodes_to_test = []
    control = get_slurm_control_nodes(host)
    if control:
        nodes_to_test.extend(control)
    login = get_login_nodes(host)
    if login:
        nodes_to_test.extend(login)
    login_comp = get_login_compiler_nodes(host)
    if login_comp:
        nodes_to_test.extend(login_comp)

    if not nodes_to_test:
        return {"success": True, "skipped": True,
                "message": "No login/control nodes found in PXE mapping - skipping",
                "ldap_users": ldap_usernames, "details": [], "error": ""}

    all_denied = True
    details = []

    for node in nodes_to_test:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({
                "hostname": hostname, "admin_ip": "",
                "login_denied": False, "user_results": [],
                "error": "No IP available",
            })
            all_denied = False
            continue

        node_ok = True
        user_results = []
        for user_cred in users:
            ldap_user = user_cred["ldap_user"]
            invalid_password = "wrong_" + _generate_random_string(16)
            result = _ldap_ssh_login(host, admin_ip, ldap_user, invalid_password)
            denied = not result["login_success"]
            user_results.append({
                "ldap_user": ldap_user,
                "login_denied": denied,
                "error": "" if denied else "Invalid password was unexpectedly accepted",
            })
            if not denied:
                node_ok = False

        details.append({
            "hostname": hostname, "admin_ip": admin_ip,
            "login_denied": node_ok,
            "user_results": user_results,
            "error": "" if node_ok else "Invalid password was unexpectedly accepted",
        })
        if not node_ok:
            all_denied = False

    return {
        "success": all_denied, "skipped": False,
        "message": INVALID_LDAP_PASS_PASSED if all_denied else INVALID_LDAP_PASS_FAILED,
        "ldap_users": ldap_usernames,
        "details": details,
        "error": "" if all_denied else INVALID_LDAP_PASS_FAILED,
    }
