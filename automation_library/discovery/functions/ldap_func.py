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
Discovery Module - LDAP Login Validation Functions.

Validates LDAP user SSH login on cluster nodes.
Two scenarios:
  - Non-slurm nodes: LDAP user login should always succeed.
  - Slurm compute nodes: LDAP user login should be blocked when no jobs
    are running (pam_slurm_adopt), and allowed when jobs are running.

Reads ldap_user and ldap_password from user_config.yml.
"""

from typing import Dict, Any

from automation_library.core import (
    load_user_config,
    run_on_remote_node,
)
from ..vars.discovery_vars import (
    SSH_TIMEOUT,
    FUNCTIONAL_GROUP_SLURM_CONTROL,
)
from .discovery_func import get_nodes_by_functional_group, iter_grouped_nodes


def _get_ldap_credentials() -> Dict[str, str]:
    """
    Read LDAP credentials from user_config.yml.

    Returns:
        Dict with ldap_user and ldap_password, or error.
    """
    config = load_user_config()
    ldap_user = config.get("ldap_user", "")
    ldap_password = config.get("ldap_password", "")
    if not ldap_user or not ldap_password:
        return {"error": "ldap_user and ldap_password required in user_config.yml"}
    return {"ldap_user": ldap_user, "ldap_password": ldap_password, "error": ""}


def _test_ldap_ssh_login(
    host, target: str, ldap_user: str, ldap_password: str,
) -> Dict[str, Any]:
    """
    Test SSH login to a node as an LDAP user using sshpass.

    Args:
        host: Testinfra host object.
        target: Hostname or IP to SSH into (hostname preferred for LDAP/DNS).
        ldap_user: LDAP username.
        ldap_password: LDAP password.

    Returns:
        Dict with login_success bool, output, and error.
    """
    ssh_login_cmd = (
        f"sshpass -p '{ldap_password}' ssh "
        f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        f"-o ConnectTimeout={SSH_TIMEOUT} "
        f"{ldap_user}@{target} 'whoami' 2>/dev/null"
    )
    cmd = host.run(ssh_login_cmd)
    login_ok = cmd.rc == 0 and ldap_user in cmd.stdout.strip()
    return {
        "login_success": login_ok,
        "output": cmd.stdout.strip(),
        "error": cmd.stderr.strip() if not login_ok else "",
    }


def _check_slurm_running_jobs(
    host, admin_ip: str, ldap_user: str,
) -> bool:
    """
    Check if the LDAP user has running jobs on a slurm node.

    Returns:
        True if the user has running/pending jobs on this node.
    """
    cmd = run_on_remote_node(
        host,
        f"squeue -u {ldap_user} -h -t R,PD 2>/dev/null | wc -l",
        admin_ip,
    )
    if cmd.rc == 0:
        try:
            return int(cmd.stdout.strip()) > 0
        except ValueError:
            pass
    return False


def _check_slurm_node_result(
    host, hostname, admin_ip, ldap_user, ldap_password,
) -> Dict[str, Any]:
    """Check a single slurm node's LDAP login behavior."""
    has_jobs = _check_slurm_running_jobs(host, admin_ip, ldap_user)
    login_result = _test_ldap_ssh_login(
        host, hostname, ldap_user, ldap_password,
    )
    login_ok = login_result["login_success"]
    expected_login = has_jobs
    correct = login_ok == expected_login

    if not correct:
        error_msg = (
            "Login blocked but user has running jobs" if has_jobs
            else "Login allowed but user has no running jobs"
        )
    else:
        error_msg = ""

    return {
        "hostname": hostname, "admin_ip": admin_ip,
        "has_jobs": has_jobs, "login_success": login_ok,
        "expected_login": expected_login, "correct": correct,
        "error": error_msg,
    }


_SKIP_NO_NODES = {"success": False, "skipped": True, "error": "No nodes found", "group_results": {}}


def validate_ldap_login_non_slurm(host) -> Dict[str, Any]:
    """
    Validate LDAP user can SSH login on non-slurm nodes.

    Tests SSH login as LDAP user on all nodes EXCEPT slurm_node groups.
    These nodes (kube_control_plane, login_node, etc.) should always
    allow LDAP user login.

    Returns:
        Dict with success, group_results, and error.
    """
    creds = _get_ldap_credentials()
    if creds.get("error"):
        return {"success": False, "skipped": True, "error": creds["error"], "group_results": {}}

    ldap_user = creds["ldap_user"]
    ldap_password = creds["ldap_password"]

    all_grouped = get_nodes_by_functional_group(host)
    if not all_grouped:
        return _SKIP_NO_NODES

    non_slurm_groups = {
        fg: nodes for fg, nodes in all_grouped.items()
        if "slurm_node" not in fg
    }
    if not non_slurm_groups:
        return {
            "success": True, "skipped": True,
            "error": "No non-slurm nodes found", "group_results": {},
        }

    group_results = {}
    all_success = True

    for func_group, hostname, admin_ip in iter_grouped_nodes(non_slurm_groups):
        group_results.setdefault(func_group, [])
        if not admin_ip:
            group_results[func_group].append({
                "hostname": hostname, "login_success": False, "error": "No IP",
            })
            all_success = False
            continue

        login_result = _test_ldap_ssh_login(
            host, hostname, ldap_user, ldap_password,
        )
        group_results[func_group].append({
            "hostname": hostname, "admin_ip": admin_ip,
            "login_success": login_result["login_success"],
            "output": login_result["output"],
            "error": login_result["error"],
        })
        if not login_result["login_success"]:
            all_success = False

    return {
        "success": all_success, "skipped": False,
        "ldap_user": ldap_user,
        "group_results": group_results,
        "error": "" if all_success else "LDAP login failed on some non-slurm nodes",
    }


def validate_ldap_login_slurm_nodes(host) -> Dict[str, Any]:
    """
    Validate LDAP user login behavior on slurm_node groups.

    On slurm nodes, if the LDAP user has NO running jobs, the node
    should BLOCK SSH login (pam_slurm_adopt). If the user has running
    jobs, the node should allow login.

    Returns:
        Dict with success, group_results, and error.
    """
    creds = _get_ldap_credentials()
    if creds.get("error"):
        return {"success": False, "skipped": True, "error": creds["error"], "group_results": {}}

    ldap_user = creds["ldap_user"]
    ldap_password = creds["ldap_password"]

    all_grouped = get_nodes_by_functional_group(host)
    if not all_grouped:
        return _SKIP_NO_NODES

    slurm_groups = {
        fg: nodes for fg, nodes in all_grouped.items()
        if "slurm_node" in fg and FUNCTIONAL_GROUP_SLURM_CONTROL not in fg
    }
    if not slurm_groups:
        return {
            "success": True, "skipped": True,
            "error": "No slurm_node groups found", "group_results": {},
        }

    group_results = {}
    all_success = True

    for func_group, hostname, admin_ip in iter_grouped_nodes(slurm_groups):
        group_results.setdefault(func_group, [])
        if not admin_ip:
            group_results[func_group].append({
                "hostname": hostname, "has_jobs": False,
                "login_success": False, "expected_login": False,
                "correct": False, "error": "No IP",
            })
            all_success = False
            continue

        entry = _check_slurm_node_result(
            host, hostname, admin_ip, ldap_user, ldap_password,
        )
        group_results[func_group].append(entry)
        if not entry["correct"]:
            all_success = False

    return {
        "success": all_success, "skipped": False,
        "ldap_user": ldap_user,
        "group_results": group_results,
        "error": "" if all_success else "LDAP login behavior incorrect on some slurm nodes",
    }
