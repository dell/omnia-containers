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
Slurm reboot scenario verification functions.

This module provides functions to:
- Reboot slurm control, compute, login, and login_compiler nodes
- Wait for nodes to come back online
- Verify cloud-init completes successfully after reboot
- Verify all slurm services are active after reboot
- Verify slurmdbd data is preserved after control plane reboot
- Submit and verify sbatch and LDAP jobs after reboot
"""

import base64
import os
import re
import time
from typing import Dict, Any, List, Tuple

from automation_library.core import (
    run_on_remote_node,
)
from automation_library.slurm.vars.slurm_vars import (
    SLURMCTLD_SERVICE,
    SLURMD_SERVICE,
    SLURMDBD_SERVICE,
    MUNGE_SERVICE,
    REBOOT_WAIT_ONLINE_TIMEOUT,
    REBOOT_WAIT_ONLINE_POLL_INTERVAL,
    CLOUD_INIT_WAIT_TIMEOUT,
    CLOUD_INIT_WAIT_POLL_INTERVAL,
    SLURM_POST_REBOOT_SETTLE_DELAY,
    NODE_IDLE_WAIT_TIMEOUT,
    NODE_IDLE_WAIT_POLL_INTERVAL,
    SACCT_POLL_INTERVAL,
    SACCT_TIMEOUT,
    SSH_TIMEOUT,
)
from automation_library.slurm.messages.slurm_msgs import (
    ERROR_NO_SLURM_CONTROL_NODES,
    ERROR_NO_SLURM_NODES,
    ERROR_NO_LOGIN_NODES,
    REBOOT_INITIATED,
    REBOOT_INITIATE_FAILED,
    REBOOT_ONLINE_PASSED,
    REBOOT_ONLINE_FAILED,
    CLOUD_INIT_PASSED,
    CLOUD_INIT_FAILED,
    CLOUD_INIT_ALL_PASSED,
    CLOUD_INIT_ALL_FAILED,
    REBOOT_CONTROL_SERVICES_PASSED,
    REBOOT_CONTROL_SERVICES_FAILED,
    REBOOT_COMPUTE_SERVICES_PASSED,
    REBOOT_COMPUTE_SERVICES_FAILED,
    REBOOT_LOGIN_SERVICES_PASSED,
    REBOOT_LOGIN_SERVICES_FAILED,
    SLURMDBD_ACTIVE_PASSED,
    SLURMDBD_ACTIVE_FAILED,
    SLURMDBD_DATA_PASSED,
    SLURMDBD_DATA_FAILED,
    SLURMDBD_DATA_NO_JOB,
    NODES_IDLE_AFTER_REBOOT_PASSED,
    NODES_IDLE_AFTER_REBOOT_FAILED,
    REBOOT_SBATCH_PASSED,
    REBOOT_SBATCH_FAILED,
    REBOOT_LDAP_LOGIN_PASSED,
    REBOOT_LDAP_LOGIN_FAILED,
    REBOOT_LDAP_SBATCH_PASSED,
    REBOOT_LDAP_SBATCH_FAILED,
)
from .slurm_func import (
    _safe_run_on_remote_node,
    _check_service_on_nodes,
    get_slurm_control_nodes,
    get_slurm_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
)
from .slurm_ldap_func import (
    _get_ldap_credentials,
    _ldap_ssh_login,
    _submit_and_poll_ldap,
)


# =============================================================================
# REBOOT HELPERS
# =============================================================================

def _reboot_node(host, hostname: str, admin_ip: str) -> Dict[str, Any]:
    """Issue a reboot command on a remote node.

    Returns:
        Dict with success, message, error.
    """
    cmd = _safe_run_on_remote_node(host, "shutdown -r now", admin_ip)
    if cmd.rc not in (0, 255):
        return {
            "success": False,
            "message": REBOOT_INITIATE_FAILED.format(node=hostname, ip=admin_ip, error=cmd.stderr.strip()),
            "error": cmd.stderr.strip(),
        }
    return {
        "success": True,
        "message": REBOOT_INITIATED.format(node=hostname, ip=admin_ip),
        "error": "",
    }


def _reboot_all_nodes_parallel(host, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Issue reboot commands to all nodes in parallel (non-blocking).

    Args:
        host: Testinfra host object
        nodes: List of node dicts with hostname and admin_ip

    Returns:
        List of dicts with reboot initiation status per node
    """
    results = []
    for node in nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            results.append({
                "hostname": hostname,
                "admin_ip": "",
                "initiated": False,
                "error": "No admin IP",
            })
            continue

        reboot_result = _reboot_node(host, hostname, admin_ip)
        results.append({
            "hostname": hostname,
            "admin_ip": admin_ip,
            "initiated": reboot_result["success"],
            "error": reboot_result.get("error", ""),
        })

    return results


def _wait_for_all_nodes_online(host, nodes: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
    """Wait for all nodes to come back online after parallel reboot.

    Args:
        host: Testinfra host object
        nodes: List of node dicts with hostname and admin_ip

    Returns:
        Tuple of (all_online: bool, details: List[Dict])
    """
    details = []
    all_online = True

    for node in nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({
                "hostname": hostname,
                "admin_ip": "",
                "online": False,
                "elapsed": 0,
                "error": "No admin IP",
            })
            all_online = False
            continue

        wait_result = _wait_for_node_online(host, hostname, admin_ip)
        details.append({
            "hostname": hostname,
            "admin_ip": admin_ip,
            "online": wait_result["success"],
            "elapsed": wait_result.get("elapsed", 0),
            "error": wait_result.get("error", ""),
        })
        if not wait_result["success"]:
            all_online = False

    return all_online, details


def _wait_for_node_online(host, hostname: str, admin_ip: str) -> Dict[str, Any]:
    """Poll SSH until the node comes back online.

    Returns:
        Dict with success, online, elapsed, error.
    """
    start = time.time()
    while time.time() - start < REBOOT_WAIT_ONLINE_TIMEOUT:
        time.sleep(REBOOT_WAIT_ONLINE_POLL_INTERVAL)
        result = _safe_run_on_remote_node(host, "echo online", admin_ip)
        if result.rc == 0 and "online" in result.stdout:
            elapsed = int(time.time() - start)
            return {
                "success": True,
                "message": REBOOT_ONLINE_PASSED.format(node=hostname, ip=admin_ip),
                "elapsed": elapsed,
                "error": "",
            }
    return {
        "success": False,
        "message": REBOOT_ONLINE_FAILED.format(
            node=hostname, ip=admin_ip, timeout=REBOOT_WAIT_ONLINE_TIMEOUT,
        ),
        "elapsed": int(time.time() - start),
        "error": f"Node {hostname} ({admin_ip}) did not respond within {REBOOT_WAIT_ONLINE_TIMEOUT}s",
    }


def _wait_for_cloud_init(host, hostname: str, admin_ip: str) -> Dict[str, Any]:
    """Wait for cloud-init to report done on a node after reboot.

    Polls /var/log/cloud-init-output.log until it contains 'Cloud-Init has completed successfully'
    or times out.

    Returns:
        Dict with success, status, error.
    """
    start = time.time()
    while time.time() - start < CLOUD_INIT_WAIT_TIMEOUT:
        time.sleep(CLOUD_INIT_WAIT_POLL_INTERVAL)
        result = _safe_run_on_remote_node(host, "grep 'Cloud-Init has completed successfully' /var/log/cloud-init-output.log 2>/dev/null", admin_ip)
        if result.rc == 0 and "Cloud-Init has completed successfully" in result.stdout:
            return {
                "success": True,
                "message": CLOUD_INIT_PASSED.format(node=hostname, ip=admin_ip),
                "status": "Cloud-Init has completed successfully",
                "error": "",
            }
    # Final check to see what's in the log
    final_check = _safe_run_on_remote_node(host, "tail -50 /var/log/cloud-init-output.log 2>/dev/null", admin_ip)
    log_tail = final_check.stdout.strip() if final_check.rc == 0 else "log file not accessible"
    return {
        "success": False,
        "message": CLOUD_INIT_FAILED.format(node=hostname, ip=admin_ip, status="timeout"),
        "status": log_tail,
        "error": f"cloud-init did not complete within {CLOUD_INIT_WAIT_TIMEOUT}s on {hostname}. Last 50 lines of log: {log_tail}",
    }


def _reboot_and_wait(host, nodes: List[Dict[str, str]]) -> Tuple[bool, List[Dict[str, Any]]]:
    """Reboot a list of nodes, then wait for all to come back online.

    Returns:
        Tuple of (all_online, per_node_details).
    """
    node_details = []
    all_online = True

    for node in nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        detail = {"hostname": hostname, "admin_ip": admin_ip}

        if not admin_ip:
            detail.update({"rebooted": False, "online": False, "error": "No admin IP"})
            node_details.append(detail)
            all_online = False
            continue

        reboot_result = _reboot_node(host, hostname, admin_ip)
        detail["rebooted"] = reboot_result["success"]
        if not reboot_result["success"]:
            detail.update({"online": False, "error": reboot_result["error"]})
            node_details.append(detail)
            all_online = False
            continue

        # Brief sleep to allow the node to begin shutting down before we poll
        time.sleep(10)

        online_result = _wait_for_node_online(host, hostname, admin_ip)
        detail.update({
            "online": online_result["success"],
            "elapsed": online_result.get("elapsed", 0),
            "error": online_result.get("error", ""),
        })
        if not online_result["success"]:
            all_online = False

        node_details.append(detail)

    return all_online, node_details


# =============================================================================
# CLOUD-INIT VERIFICATION
# =============================================================================

def verify_cloud_init_after_reboot(host, nodes: List[Dict[str, str]]) -> Dict[str, Any]:
    """Verify cloud-init completed successfully on all given nodes after reboot.

    Args:
        host: Testinfra host
        nodes: List of node dicts with hostname and admin_ip

    Returns:
        Dict with success, message, details, error.
    """
    all_passed = True
    node_details = []

    for node in nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            node_details.append({"hostname": hostname, "admin_ip": "", "success": False, "status": "No admin IP"})
            all_passed = False
            continue

        result = _wait_for_cloud_init(host, hostname, admin_ip)
        node_details.append({
            "hostname": hostname,
            "admin_ip": admin_ip,
            "success": result["success"],
            "status": result.get("status", ""),
            "error": result.get("error", ""),
        })
        if not result["success"]:
            all_passed = False

    return {
        "success": all_passed,
        "message": CLOUD_INIT_ALL_PASSED if all_passed else CLOUD_INIT_ALL_FAILED,
        "details": node_details,
        "error": "" if all_passed else CLOUD_INIT_ALL_FAILED,
    }


# =============================================================================
# SLURMDBD VERIFICATION
# =============================================================================

def verify_slurmdbd_active(host) -> Dict[str, Any]:
    """Verify slurmdbd service is active on all slurm control nodes.

    Returns:
        Dict with success, message, details, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_CONTROL_NODES,
            "details": [],
            "error": ERROR_NO_SLURM_CONTROL_NODES,
        }

    all_passed, details = _check_service_on_nodes(host, control_nodes, SLURMDBD_SERVICE)
    return {
        "success": all_passed,
        "message": SLURMDBD_ACTIVE_PASSED if all_passed else SLURMDBD_ACTIVE_FAILED,
        "details": details,
        "error": "" if all_passed else SLURMDBD_ACTIVE_FAILED,
    }


def verify_slurmdbd_data_preserved(host, pre_reboot_job_id: str) -> Dict[str, Any]:
    """Verify that a pre-reboot job ID still appears in sacct after reboot.

    Args:
        host: Testinfra host
        pre_reboot_job_id: Job ID that was submitted before the reboot

    Returns:
        Dict with success, message, job_state, error.
    """
    if not pre_reboot_job_id:
        return {
            "success": False,
            "message": SLURMDBD_DATA_NO_JOB,
            "job_state": "",
            "error": SLURMDBD_DATA_NO_JOB,
        }

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_CONTROL_NODES,
            "job_state": "",
            "error": ERROR_NO_SLURM_CONTROL_NODES,
        }

    control_ip = control_nodes[0].get("admin_ip", "")
    sacct_cmd = (
        f"sacct -j {pre_reboot_job_id} --format=JobID,State,ExitCode -n -P 2>/dev/null"
    )
    result = _safe_run_on_remote_node(host, sacct_cmd, control_ip)

    if result.rc != 0 or not result.stdout.strip():
        return {
            "success": False,
            "message": SLURMDBD_DATA_FAILED.format(job_id=pre_reboot_job_id),
            "job_state": "",
            "error": f"sacct returned no data for job {pre_reboot_job_id}",
        }

    job_state = ""
    for line in result.stdout.strip().split("\n"):
        parts = line.strip().split("|")
        if len(parts) >= 2 and parts[0] == pre_reboot_job_id:
            job_state = parts[1].strip()
            break

    if not job_state:
        return {
            "success": False,
            "message": SLURMDBD_DATA_FAILED.format(job_id=pre_reboot_job_id),
            "job_state": "",
            "error": f"Job {pre_reboot_job_id} not found in sacct output",
        }

    return {
        "success": True,
        "message": SLURMDBD_DATA_PASSED.format(job_id=pre_reboot_job_id),
        "job_state": job_state,
        "error": "",
    }


# =============================================================================
# NODES IDLE AFTER REBOOT
# =============================================================================

def wait_for_nodes_idle_after_reboot(host) -> Dict[str, Any]:
    """Poll sinfo until all slurm nodes return to idle state after reboot.

    Returns:
        Dict with success, message, node_states, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_CONTROL_NODES,
            "node_states": [],
            "error": ERROR_NO_SLURM_CONTROL_NODES,
        }

    control_ip = control_nodes[0].get("admin_ip", "")
    start = time.time()
    node_states = []

    while time.time() - start < NODE_IDLE_WAIT_TIMEOUT:
        time.sleep(NODE_IDLE_WAIT_POLL_INTERVAL)
        cmd = _safe_run_on_remote_node(host, "sinfo -N -h -o '%N %T' 2>/dev/null", control_ip)
        if cmd.rc != 0:
            continue

        lines = [l.strip() for l in cmd.stdout.strip().split("\n") if l.strip()]
        node_states = []
        all_idle = True
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                state = parts[1].lower()
                node_states.append({"node": parts[0], "state": parts[1]})
                if "idle" not in state:
                    all_idle = False

        if all_idle and node_states:
            return {
                "success": True,
                "message": NODES_IDLE_AFTER_REBOOT_PASSED,
                "node_states": node_states,
                "error": "",
            }

    return {
        "success": False,
        "message": NODES_IDLE_AFTER_REBOOT_FAILED,
        "node_states": node_states,
        "error": f"Nodes did not return to idle within {NODE_IDLE_WAIT_TIMEOUT}s",
    }


# =============================================================================
# SBATCH AFTER REBOOT
# =============================================================================

def verify_sbatch_after_reboot(host) -> Dict[str, Any]:
    """Submit a simple sbatch job from the control node after reboot and verify it completes.

    Returns:
        Dict with success, message, job_id, job_state, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_CONTROL_NODES,
            "job_id": "",
            "job_state": "",
            "error": ERROR_NO_SLURM_CONTROL_NODES,
        }

    control_ip = control_nodes[0].get("admin_ip", "")
    num_nodes = get_slurm_node_count(host) or 1

    script_content = (
        "#!/bin/bash\n"
        f"#SBATCH --nodes={num_nodes}\n"
        "#SBATCH --job-name=omnia_reboot_test\n"
        "#SBATCH --output=/home/omnia_reboot_test_%j.out\n"
        "hostname\n"
        "echo 'reboot_test_completed'\n"
    )
    encoded = base64.b64encode(script_content.encode()).decode()
    create_cmd = (
        f"echo {encoded} | base64 -d > /home/omnia_reboot_sbatch.sh && "
        "chmod +x /home/omnia_reboot_sbatch.sh"
    )
    cmd = _safe_run_on_remote_node(host, create_cmd, control_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "message": REBOOT_SBATCH_FAILED.format(error=cmd.stderr.strip()),
            "job_id": "",
            "job_state": "",
            "error": cmd.stderr.strip(),
        }

    cmd = _safe_run_on_remote_node(host, "sbatch /home/omnia_reboot_sbatch.sh", control_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "message": REBOOT_SBATCH_FAILED.format(error=cmd.stderr.strip()),
            "job_id": "",
            "job_state": "",
            "error": cmd.stderr.strip(),
        }

    match = re.search(r"Submitted batch job (\d+)", cmd.stdout.strip())
    if not match:
        return {
            "success": False,
            "message": REBOOT_SBATCH_FAILED.format(error="Could not parse job ID"),
            "job_id": "",
            "job_state": "",
            "error": "Failed to parse job ID",
        }
    job_id = match.group(1)

    start = time.time()
    job_state = ""
    while time.time() - start < SACCT_TIMEOUT:
        time.sleep(SACCT_POLL_INTERVAL)
        sacct = _safe_run_on_remote_node(
            host, f"sacct -j {job_id} --format=JobID,State -n -P 2>/dev/null", control_ip,
        )
        if sacct.rc != 0:
            continue
        for line in sacct.stdout.strip().split("\n"):
            parts = line.strip().split("|")
            if len(parts) >= 2 and parts[0] == job_id:
                job_state = parts[1].strip()
                break
        if job_state in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"):
            break

    _safe_run_on_remote_node(host, "rm -f /home/omnia_reboot_sbatch.sh", control_ip)

    success = job_state == "COMPLETED"
    return {
        "success": success,
        "message": REBOOT_SBATCH_PASSED.format(job_id=job_id) if success
                   else REBOOT_SBATCH_FAILED.format(error=f"Job {job_id} state: {job_state}"),
        "job_id": job_id,
        "job_state": job_state or "UNKNOWN",
        "error": "" if success else f"Job {job_id} ended with state: {job_state}",
    }


# =============================================================================
# LDAP AFTER REBOOT
# =============================================================================

def verify_ldap_login_after_reboot(host) -> Dict[str, Any]:
    """Verify LDAP user can log in to allowed nodes after reboot.

    Returns:
        Dict with success, message, details, error.
    """
    creds = _get_ldap_credentials()
    if creds.get("error"):
        return {"success": False, "message": creds["error"], "details": [], "error": creds["error"]}

    ldap_user = creds["ldap_user"]
    ldap_password = creds["ldap_password"]

    allowed_nodes = []
    allowed_nodes.extend(get_slurm_control_nodes(host))
    allowed_nodes.extend(get_login_nodes(host))
    allowed_nodes.extend(get_login_compiler_nodes(host))

    if not allowed_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_CONTROL_NODES,
            "details": [],
            "error": ERROR_NO_SLURM_CONTROL_NODES,
        }

    all_passed = True
    details = []
    for node in allowed_nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({"hostname": hostname, "login_success": False, "error": "No admin IP"})
            all_passed = False
            continue
        result = _ldap_ssh_login(host, admin_ip, ldap_user, ldap_password)
        details.append({
            "hostname": hostname,
            "admin_ip": admin_ip,
            "login_success": result["login_success"],
            "error": result.get("error", ""),
        })
        if not result["login_success"]:
            all_passed = False

    return {
        "success": all_passed,
        "message": REBOOT_LDAP_LOGIN_PASSED if all_passed else REBOOT_LDAP_LOGIN_FAILED,
        "details": details,
        "error": "" if all_passed else REBOOT_LDAP_LOGIN_FAILED,
    }


def verify_ldap_sbatch_after_reboot(host) -> Dict[str, Any]:
    """Verify LDAP user can submit and complete an sbatch job after reboot.

    Submits from the first available login or login_compiler node.

    Returns:
        Dict with success, message, job_id, job_state, submit_node, error.
    """
    creds = _get_ldap_credentials()
    if creds.get("error"):
        return {
            "success": False, "message": creds["error"],
            "job_id": "", "job_state": "", "submit_node": "", "error": creds["error"],
        }

    ldap_user = creds["ldap_user"]
    ldap_password = creds["ldap_password"]

    login_nodes = get_login_nodes(host)
    login_compiler_nodes = get_login_compiler_nodes(host)
    submit_nodes = login_nodes + login_compiler_nodes

    if not submit_nodes:
        return {
            "success": False,
            "message": ERROR_NO_LOGIN_NODES,
            "job_id": "", "job_state": "", "submit_node": "",
            "error": ERROR_NO_LOGIN_NODES,
        }

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_CONTROL_NODES,
            "job_id": "", "job_state": "", "submit_node": "",
            "error": ERROR_NO_SLURM_CONTROL_NODES,
        }

    control_ip = control_nodes[0].get("admin_ip", "")
    num_nodes = get_slurm_node_count(host) or 1

    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    ldap_home = f"/home/{ldap_user}"
    remote_script = f"{ldap_home}/omnia_ldap_reboot_test.sh"

    node = submit_nodes[0]
    hostname = node.get("hostname", "unknown")
    node_ip = node.get("admin_ip", "")

    if not node_ip:
        return {
            "success": False,
            "message": f"Login node {hostname} has no admin IP",
            "job_id": "", "job_state": "", "submit_node": hostname,
            "error": "No admin IP",
        }

    with open(os.path.join(jobs_dir, "basic_sbatch.sh"), "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("{{SLURM_NUM_NODES}}", str(num_nodes)).replace("{{OUTPUT_PATH}}", ldap_home)
    encoded = base64.b64encode(content.encode()).decode()
    xfer = _safe_run_on_remote_node(
        host,
        f"echo {encoded} | base64 -d > {remote_script} && chmod a+rx {remote_script}",
        node_ip,
    )
    if xfer.rc != 0:
        return {
            "success": False,
            "message": REBOOT_LDAP_SBATCH_FAILED.format(error=xfer.stderr.strip()),
            "job_id": "", "job_state": "", "submit_node": hostname,
            "error": xfer.stderr.strip(),
        }

    result = _submit_and_poll_ldap(host, node_ip, control_ip, ldap_user, ldap_password, remote_script)
    _safe_run_on_remote_node(host, f"rm -f {remote_script}", node_ip)

    success = result.get("success", False)
    job_id = result.get("job_id", "")
    job_state = result.get("job_state", "UNKNOWN")
    return {
        "success": success,
        "message": REBOOT_LDAP_SBATCH_PASSED if success
                   else REBOOT_LDAP_SBATCH_FAILED.format(error=result.get("error", "")),
        "job_id": job_id,
        "job_state": job_state,
        "submit_node": hostname,
        "error": "" if success else result.get("error", ""),
    }


# =============================================================================
# TOP-LEVEL REBOOT SCENARIO FUNCTIONS
# =============================================================================

def reboot_and_verify_control_nodes(host) -> Dict[str, Any]:
    """Reboot all slurm control nodes and return online status + node list.

    Returns:
        Dict with success, message, nodes (list), details, error.
    """
    nodes = get_slurm_control_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "nodes": [], "details": [], "error": ERROR_NO_SLURM_CONTROL_NODES}

    all_online, details = _reboot_and_wait(host, nodes)
    msg = ("All slurm control nodes rebooted and came back online"
           if all_online else "One or more slurm control nodes failed to come back online")
    return {
        "success": all_online,
        "message": msg,
        "nodes": nodes,
        "details": details,
        "error": "" if all_online else msg,
    }


def reboot_and_verify_slurm_nodes(host) -> Dict[str, Any]:
    """Reboot all slurm compute nodes and return online status + node list.

    Returns:
        Dict with success, message, nodes (list), details, error.
    """
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "nodes": [], "details": [], "error": ERROR_NO_SLURM_NODES}

    all_online, details = _reboot_and_wait(host, nodes)
    msg = ("All slurm compute nodes rebooted and came back online"
           if all_online else "One or more slurm compute nodes failed to come back online")
    return {
        "success": all_online,
        "message": msg,
        "nodes": nodes,
        "details": details,
        "error": "" if all_online else msg,
    }


def reboot_and_verify_login_nodes(host) -> Dict[str, Any]:
    """Reboot all login nodes and return online status + node list.

    Returns:
        Dict with success, message, nodes (list), details, error.
    """
    nodes = get_login_nodes(host)
    if not nodes:
        return {"skipped": True, "message": ERROR_NO_LOGIN_NODES,
                "nodes": [], "details": [], "error": ERROR_NO_LOGIN_NODES}

    all_online, details = _reboot_and_wait(host, nodes)
    msg = ("All login nodes rebooted and came back online"
           if all_online else "One or more login nodes failed to come back online")
    return {
        "success": all_online,
        "message": msg,
        "nodes": nodes,
        "details": details,
        "error": "" if all_online else msg,
    }


def reboot_and_verify_login_compiler_nodes(host) -> Dict[str, Any]:
    """Reboot all login_compiler nodes and return online status + node list.

    Returns:
        Dict with success, message, nodes (list), details, error.
    """
    nodes = get_login_compiler_nodes(host)
    if not nodes:
        return {"skipped": True, "message": "No login_compiler nodes found in PXE mapping file",
                "nodes": [], "details": [], "error": ""}

    all_online, details = _reboot_and_wait(host, nodes)
    msg = ("All login_compiler nodes rebooted and came back online"
           if all_online else "One or more login_compiler nodes failed to come back online")
    return {
        "success": all_online,
        "message": msg,
        "nodes": nodes,
        "details": details,
        "error": "" if all_online else msg,
    }


def reboot_all_slurm_nodes_parallel(host) -> Dict[str, Any]:
    """Reboot ALL slurm nodes (control, compute, login, login_compiler) in parallel.

    Issues reboot commands to all nodes first, then waits for all to come online.
    This is faster than rebooting each node type sequentially.

    Returns:
        Dict with:
            - success: bool
            - message: str
            - node_types: dict with control_nodes, slurm_nodes, login_nodes, login_compiler_nodes
            - details: dict with per-node-type reboot details
            - error: str
    """
    # Gather all nodes
    control_nodes = get_slurm_control_nodes(host)
    slurm_nodes = get_slurm_nodes(host)
    login_nodes = get_login_nodes(host)
    login_compiler_nodes = get_login_compiler_nodes(host)

    all_nodes = []
    node_type_map = {}

    if control_nodes:
        all_nodes.extend(control_nodes)
        for node in control_nodes:
            node_type_map[node["admin_ip"]] = "control"

    if slurm_nodes:
        all_nodes.extend(slurm_nodes)
        for node in slurm_nodes:
            node_type_map[node["admin_ip"]] = "compute"

    if login_nodes:
        all_nodes.extend(login_nodes)
        for node in login_nodes:
            node_type_map[node["admin_ip"]] = "login"

    if login_compiler_nodes:
        all_nodes.extend(login_compiler_nodes)
        for node in login_compiler_nodes:
            node_type_map[node["admin_ip"]] = "login_compiler"

    if not all_nodes:
        return {
            "success": False,
            "message": "No slurm nodes found to reboot",
            "node_types": {
                "control_nodes": [],
                "slurm_nodes": [],
                "login_nodes": [],
                "login_compiler_nodes": [],
            },
            "details": {},
            "error": "No slurm nodes found",
        }

    # Issue all reboots in parallel
    _reboot_all_nodes_parallel(host, all_nodes)

    # Wait for all nodes to come online
    all_online, online_details = _wait_for_all_nodes_online(host, all_nodes)

    # Organize details by node type
    details_by_type = {
        "control": [],
        "compute": [],
        "login": [],
        "login_compiler": [],
    }

    for detail in online_details:
        node_type = node_type_map.get(detail["admin_ip"], "unknown")
        details_by_type[node_type].append(detail)

    msg = ("All slurm nodes rebooted and came back online"
           if all_online else "One or more slurm nodes failed to come back online")

    return {
        "success": all_online,
        "message": msg,
        "node_types": {
            "control_nodes": control_nodes,
            "slurm_nodes": slurm_nodes,
            "login_nodes": login_nodes,
            "login_compiler_nodes": login_compiler_nodes,
        },
        "details": details_by_type,
        "error": "" if all_online else msg,
    }


def verify_control_node_services_after_reboot(host) -> Dict[str, Any]:
    """Verify slurmctld, slurmdbd, and munge are active on control nodes after reboot.

    Returns:
        Dict with success, message, details, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "details": {}, "error": ERROR_NO_SLURM_CONTROL_NODES}

    time.sleep(SLURM_POST_REBOOT_SETTLE_DELAY)

    all_passed = True
    details = {}

    for service in (SLURMCTLD_SERVICE, SLURMDBD_SERVICE, MUNGE_SERVICE):
        passed, svc_details = _check_service_on_nodes(host, control_nodes, service)
        details[service] = svc_details
        if not passed:
            all_passed = False

    return {
        "success": all_passed,
        "message": REBOOT_CONTROL_SERVICES_PASSED if all_passed else REBOOT_CONTROL_SERVICES_FAILED,
        "details": details,
        "error": "" if all_passed else REBOOT_CONTROL_SERVICES_FAILED,
    }


def verify_compute_node_services_after_reboot(host) -> Dict[str, Any]:
    """Verify slurmd and munge are active on slurm compute nodes after reboot.

    Returns:
        Dict with success, message, details, error.
    """
    slurm_nodes = get_slurm_nodes(host)
    if not slurm_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    time.sleep(SLURM_POST_REBOOT_SETTLE_DELAY)

    all_passed = True
    details = {}

    for service in (SLURMD_SERVICE, MUNGE_SERVICE):
        passed, svc_details = _check_service_on_nodes(host, slurm_nodes, service)
        details[service] = svc_details
        if not passed:
            all_passed = False

    return {
        "success": all_passed,
        "message": REBOOT_COMPUTE_SERVICES_PASSED if all_passed else REBOOT_COMPUTE_SERVICES_FAILED,
        "details": details,
        "error": "" if all_passed else REBOOT_COMPUTE_SERVICES_FAILED,
    }


def verify_login_node_services_after_reboot(host) -> Dict[str, Any]:
    """Verify slurmd and munge are active on login and login_compiler nodes after reboot.

    Returns:
        Dict with success, message, details, error.
    """
    login_nodes = get_login_nodes(host)
    login_compiler_nodes = get_login_compiler_nodes(host)
    all_nodes = login_nodes + login_compiler_nodes

    if not all_nodes:
        return {"skipped": True, "message": ERROR_NO_LOGIN_NODES,
                "details": {}, "error": ""}

    time.sleep(SLURM_POST_REBOOT_SETTLE_DELAY)

    all_passed = True
    details = {}

    for service in (SLURMD_SERVICE, MUNGE_SERVICE):
        passed, svc_details = _check_service_on_nodes(host, all_nodes, service)
        details[service] = svc_details
        if not passed:
            all_passed = False

    return {
        "success": all_passed,
        "message": REBOOT_LOGIN_SERVICES_PASSED if all_passed else REBOOT_LOGIN_SERVICES_FAILED,
        "details": details,
        "error": "" if all_passed else REBOOT_LOGIN_SERVICES_FAILED,
    }
