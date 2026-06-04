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
Slurm operations for OMNIA test automation.

This module provides functions to verify Slurm cluster health,
service status, and job execution from within the OMNIA test environment.
All remote access is done via host.py utilities (run_on_remote_node, etc.).
"""

import base64
import os
import re
import time
from typing import Dict, Any, List, Tuple

from automation_library.core import (
    get_nodes_info,
    get_functional_groups_from_pxe_mapping,
    run_on_remote_node,
)
from automation_library.slurm.vars.slurm_vars import (
    SLURM_CONTROL_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_FUNCTIONAL_GROUP,
    LOGIN_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
    SLURMCTLD_SERVICE,
    SLURMD_SERVICE,
    MUNGE_SERVICE,
    MUNGE_REQUIRED_GROUPS,
    SACCT_POLL_INTERVAL,
    SACCT_TIMEOUT,
    MULTI_JOB_COUNT,
    DRAIN_REASON,
    DRAIN_UNDRAIN_SETTLE_DELAY,
    DRAIN_JOB_TRANSITION_TIMEOUT,
)
from automation_library.slurm.messages.slurm_msgs import (
    ERROR_NO_SLURM_CONTROL_NODES,
    ERROR_NO_SLURM_NODES,
    ERROR_NO_LOGIN_NODES,
    SLURMCTLD_CHECK_PASSED,
    SLURMCTLD_CHECK_FAILED,
    SLURMD_CHECK_PASSED,
    SLURMD_CHECK_FAILED,
    SLURMD_LOGIN_CHECK_PASSED,
    SLURMD_LOGIN_CHECK_FAILED,
    MUNGE_CHECK_PASSED,
    MUNGE_CHECK_FAILED,
    SINFO_CHECK_PASSED,
    SINFO_CHECK_FAILED,
    SINFO_NO_OUTPUT,
    SINFO_COMMAND_FAILED,
    LOGIN_NODES_IDLE_PASSED,
    LOGIN_NODES_IDLE_FAILED,
    LOGIN_NODES_IDLE_NO_NODES,
    SRUN_CHECK_PASSED,
    SRUN_CHECK_FAILED,
    SRUN_NO_CONTROL_NODE,
    PXE_CLUSTER_VERIFY_PASSED,
    PXE_CLUSTER_VERIFY_FAILED,
    PXE_CLUSTER_VERIFY_NO_NODES,
    PXE_CLUSTER_VERIFY_NO_SLURM_NODES,
    PXE_CLUSTER_VERIFY_MISSING_NODES,
    PXE_CLUSTER_VERIFY_EXTRA_NODES,
    SBATCH_CHECK_PASSED,
    SBATCH_CHECK_FAILED,
    SBATCH_SUBMIT_FAILED,
    SBATCH_TIMEOUT,
    SBATCH_NO_CONTROL_NODE,
    SACCT_JOB_STATUS,
    ROOT_LOGIN_MULTI_PASSED,
    ROOT_LOGIN_MULTI_FAILED,
    ROOT_LOGIN_ALLNODES_PASSED,
    ROOT_LOGIN_ALLNODES_FAILED,
    ROOT_NO_LOGIN_NODES,
    DRAIN_QUEUE_PASSED,
    DRAIN_QUEUE_FAILED,
    DRAIN_FAILED,
    UNDRAIN_FAILED,
    DRAIN_JOB_NOT_PENDING,
    INSUFF_RESOURCE_PASSED,
    INSUFF_RESOURCE_FAILED,
    SLURMD_LOGIN_ONLY_PASSED,
    SLURMD_LOGIN_ONLY_FAILED,
    SLURMD_LOGINCOMP_ONLY_PASSED,
    SLURMD_LOGINCOMP_ONLY_FAILED,
    MUNGE_CONTROL_PASSED,
    MUNGE_CONTROL_FAILED,
    MUNGE_SLURM_PASSED,
    MUNGE_SLURM_FAILED,
    MUNGE_LOGIN_PASSED,
    MUNGE_LOGIN_FAILED,
    MUNGE_LOGINCOMP_PASSED,
    MUNGE_LOGINCOMP_FAILED,
    SSH_PASSWORDLESS_PASSED,
    SSH_PASSWORDLESS_FAILED,
    MULTI_LOGIN_JOB_PASSED,
    MULTI_LOGIN_JOB_FAILED,
    MULTI_LOGIN_SKIP,
)


# =============================================================================
# NODE DISCOVERY HELPERS
# =============================================================================

def _get_nodes_for_group(host, group_keyword: str) -> List[Dict[str, str]]:
    """Get all nodes whose functional_group contains the given keyword."""
    all_groups = get_functional_groups_from_pxe_mapping(host)
    nodes = []
    for fg in all_groups:
        if group_keyword in fg:
            fg_nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
            nodes.extend(fg_nodes)
    return nodes


def get_slurm_control_nodes(host) -> List[Dict[str, str]]:
    """Get all slurm control nodes from PXE mapping."""
    return _get_nodes_for_group(host, SLURM_CONTROL_NODE_FUNCTIONAL_GROUP)


def get_slurm_nodes(host) -> List[Dict[str, str]]:
    """Get all slurm compute/worker nodes from PXE mapping."""
    return _get_nodes_for_group(host, SLURM_NODE_FUNCTIONAL_GROUP)


def get_login_nodes(host) -> List[Dict[str, str]]:
    """Get all login nodes from PXE mapping."""
    all_groups = get_functional_groups_from_pxe_mapping(host)
    nodes = []
    for fg in all_groups:
        # Match login_node but NOT login_compiler_node
        if LOGIN_NODE_FUNCTIONAL_GROUP in fg and LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP not in fg:
            fg_nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
            nodes.extend(fg_nodes)
    return nodes


def get_login_compiler_nodes(host) -> List[Dict[str, str]]:
    """Get all login compiler nodes from PXE mapping."""
    return _get_nodes_for_group(host, LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP)


def get_all_munge_nodes(host) -> Dict[str, List[Dict[str, str]]]:
    """Get all nodes that require munge, grouped by functional group keyword.

    Returns:
        Dict mapping functional group keyword to list of node dicts.
    """
    result = {}
    all_groups = get_functional_groups_from_pxe_mapping(host)
    for fg in sorted(all_groups):
        for group_keyword in MUNGE_REQUIRED_GROUPS:
            if group_keyword in fg:
                fg_nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
                if fg_nodes:
                    result.setdefault(fg, []).extend(fg_nodes)
                break
    return result


def get_slurm_node_count(host) -> int:
    """Get total number of slurm compute nodes from PXE mapping."""
    return len(get_slurm_nodes(host))


def verify_all_pxe_nodes_in_slurm_cluster(host) -> Dict[str, Any]:
    """Verify that all nodes in PXE mapping are present in slurm.conf.

    Reads /etc/slurm/slurm.conf and extracts all NodeName entries,
    then compares with nodes from PXE mapping to ensure all PXE nodes
    are configured in Slurm.

    Returns:
        Dict with success, message, pxe_nodes, slurm_nodes, missing_nodes, extra_nodes, error.
    """
    # Get only nodes from slurm-specific functional groups (excludes k8s and other non-slurm nodes)
    slurm_fg_keywords = (
        SLURM_NODE_FUNCTIONAL_GROUP,
        LOGIN_NODE_FUNCTIONAL_GROUP,
        LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
    )
    all_groups = get_functional_groups_from_pxe_mapping(host)
    pxe_nodes = []
    for fg in all_groups:
        if any(kw in fg for kw in slurm_fg_keywords):
            fg_nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
            pxe_nodes.extend(fg_nodes)

    if not pxe_nodes:
        return {
            "success": False,
            "message": PXE_CLUSTER_VERIFY_NO_NODES,
            "pxe_nodes": [],
            "slurm_nodes": [],
            "missing_nodes": [],
            "extra_nodes": [],
            "error": "No nodes found in PXE mapping",
        }

    # Get control node to read slurm.conf
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_CONTROL_NODES,
            "pxe_nodes": [n["hostname"] for n in pxe_nodes],
            "slurm_nodes": [],
            "missing_nodes": [n["hostname"] for n in pxe_nodes],
            "extra_nodes": [],
            "error": "No slurm control node found to read slurm.conf",
        }

    control_node = control_nodes[0]
    control_ip = control_node.get("admin_ip")
    control_hostname = control_node.get("hostname", "unknown")

    # Read slurm.conf and extract NodeName entries
    slurm_conf_cmd = _safe_run_on_remote_node(
        host,
        "grep '^NodeName=' /etc/slurm/slurm.conf 2>/dev/null",
        control_ip
    )

    if slurm_conf_cmd.rc != 0:
        return {
            "success": False,
            "message": PXE_CLUSTER_VERIFY_NO_SLURM_NODES,
            "pxe_nodes": [n["hostname"] for n in pxe_nodes],
            "slurm_nodes": [],
            "missing_nodes": [n["hostname"] for n in pxe_nodes],
            "extra_nodes": [],
            "error": f"Failed to read slurm.conf on {control_hostname}: {slurm_conf_cmd.stderr.strip()}",
        }

    # Parse NodeName entries from slurm.conf
    slurm_nodes = set()
    for line in slurm_conf_cmd.stdout.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Extract NodeName value (e.g., "NodeName=snode1" or "NodeName=DEFAULT")
        if line.startswith("NodeName="):
            node_part = line.split()[0]
            node_name = node_part.split("=", 1)[1]

            # Skip DEFAULT and other special entries
            if node_name.upper() != "DEFAULT":
                slurm_nodes.add(node_name)

    if not slurm_nodes:
        return {
            "success": False,
            "message": PXE_CLUSTER_VERIFY_NO_SLURM_NODES,
            "pxe_nodes": [n["hostname"] for n in pxe_nodes],
            "slurm_nodes": [],
            "missing_nodes": [n["hostname"] for n in pxe_nodes],
            "extra_nodes": [],
            "error": "No NodeName entries found in slurm.conf",
        }

    # Compare PXE nodes with slurm.conf nodes
    pxe_hostnames = set(n["hostname"] for n in pxe_nodes)
    missing_nodes = pxe_hostnames - slurm_nodes
    extra_nodes = slurm_nodes - pxe_hostnames

    if missing_nodes:
        return {
            "success": False,
            "message": PXE_CLUSTER_VERIFY_FAILED,
            "pxe_nodes": sorted(pxe_hostnames),
            "slurm_nodes": sorted(slurm_nodes),
            "missing_nodes": sorted(missing_nodes),
            "extra_nodes": sorted(extra_nodes),
            "error": PXE_CLUSTER_VERIFY_MISSING_NODES.format(missing_nodes=", ".join(sorted(missing_nodes))),
        }

    if extra_nodes:
        return {
            "success": False,
            "message": PXE_CLUSTER_VERIFY_FAILED,
            "pxe_nodes": sorted(pxe_hostnames),
            "slurm_nodes": sorted(slurm_nodes),
            "missing_nodes": [],
            "extra_nodes": sorted(extra_nodes),
            "error": PXE_CLUSTER_VERIFY_EXTRA_NODES.format(extra_nodes=", ".join(sorted(extra_nodes))),
        }

    return {
        "success": True,
        "message": PXE_CLUSTER_VERIFY_PASSED.format(pxe_count=len(pxe_hostnames)),
        "pxe_nodes": sorted(pxe_hostnames),
        "slurm_nodes": sorted(slurm_nodes),
        "missing_nodes": [],
        "extra_nodes": [],
        "error": "",
    }


# =============================================================================
# SAFE REMOTE EXECUTION HELPER
# =============================================================================

class _FakeResult:
    """Minimal stand-in for a testinfra CommandResult on SSH failure."""
    def __init__(self, rc, stdout, stderr):
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr


def _safe_run_on_remote_node(host, cmd: str, admin_ip: str):
    """Wrapper around run_on_remote_node that catches RuntimeError.

    testinfra raises RuntimeError when SSH exit code is 255 (connection
    failure).  This wrapper converts that into a fake result object so
    callers can handle the error gracefully.
    """
    try:
        return run_on_remote_node(host, cmd, admin_ip)
    except RuntimeError as exc:
        return _FakeResult(
            rc=255,
            stdout="",
            stderr=f"SSH connection failed to {admin_ip}: {exc}",
        )


# =============================================================================
# SERVICE VERIFICATION HELPERS
# =============================================================================

def _check_service_on_node(host, admin_ip: str, service: str) -> Dict[str, Any]:
    """Check if a systemd service is active on a remote node.

    Args:
        host: Testinfra host connected to OIM server.
        admin_ip: Admin IP of the target node.
        service: Systemd service name.

    Returns:
        Dict with keys: service, active, enabled, output, error.
    """
    cmd_str = (
        f"systemctl is-active {service} && systemctl is-enabled {service} && "
        f"systemctl show {service} --property=ActiveState,SubState,MainPID --no-pager"
    )
    cmd = _safe_run_on_remote_node(host, cmd_str, admin_ip)
    output_lines = cmd.stdout.strip().split('\n')
    is_active = len(output_lines) > 0 and output_lines[0] == "active"
    is_enabled = len(output_lines) > 1 and output_lines[1] == "enabled"
    status_info = f"active={output_lines[0] if output_lines else 'unknown'}"
    if len(output_lines) > 1:
        status_info += f", enabled={output_lines[1]}"
    return {
        "service": service,
        "active": is_active,
        "enabled": is_enabled,
        "output": status_info,
        "error": "" if is_active else f"{service} not active",
    }


def _check_service_on_nodes(
    host,
    nodes: List[Dict[str, str]],
    service: str,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Check a service on a list of nodes.

    Returns:
        Tuple of (all_passed, per_node_details).
    """
    details = []
    all_passed = True

    for node in nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")

        if not admin_ip:
            details.append({
                "hostname": hostname, "admin_ip": "",
                "active": False, "output": "No IP available",
            })
            all_passed = False
            continue

        result = _check_service_on_node(host, admin_ip, service)
        details.append({
            "hostname": hostname, "admin_ip": admin_ip,
            "active": result["active"],
            "output": result["output"],
        })
        if not result["active"]:
            all_passed = False

    return all_passed, details


# =============================================================================
# VERIFICATION FUNCTIONS (TC1-TC6)
# =============================================================================

def verify_slurmctld_active(host) -> Dict[str, Any]:
    """TC1: Verify slurmctld service is active on all slurm control nodes.

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

    all_passed, details = _check_service_on_nodes(host, control_nodes, SLURMCTLD_SERVICE)

    return {
        "success": all_passed,
        "message": SLURMCTLD_CHECK_PASSED if all_passed else SLURMCTLD_CHECK_FAILED,
        "details": details,
        "error": "" if all_passed else SLURMCTLD_CHECK_FAILED,
    }


def verify_slurmd_active(host) -> Dict[str, Any]:
    """TC2: Verify slurmd service is active on all slurm compute nodes.

    Returns:
        Dict with success, message, details, error.
    """
    slurm_nodes = get_slurm_nodes(host)
    if not slurm_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_NODES,
            "details": [],
            "error": ERROR_NO_SLURM_NODES,
        }

    all_passed, details = _check_service_on_nodes(host, slurm_nodes, SLURMD_SERVICE)

    return {
        "success": all_passed,
        "message": SLURMD_CHECK_PASSED if all_passed else SLURMD_CHECK_FAILED,
        "details": details,
        "error": "" if all_passed else SLURMD_CHECK_FAILED,
    }


def verify_slurmd_active_on_login_nodes(host) -> Dict[str, Any]:
    """Verify slurmd service is active on all login and login compiler nodes.

    Returns:
        Dict with success, message, group_details (per functional group), error.
    """
    login_nodes = get_login_nodes(host)
    login_compiler_nodes = get_login_compiler_nodes(host)

    all_nodes_grouped = {}
    if login_nodes:
        all_nodes_grouped[LOGIN_NODE_FUNCTIONAL_GROUP] = login_nodes
    if login_compiler_nodes:
        all_nodes_grouped[LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP] = login_compiler_nodes

    if not all_nodes_grouped:
        return {
            "success": False,
            "message": ERROR_NO_LOGIN_NODES,
            "group_details": {},
            "error": ERROR_NO_LOGIN_NODES,
        }

    all_passed = True
    group_details = {}

    for func_group, nodes in all_nodes_grouped.items():
        passed, details = _check_service_on_nodes(host, nodes, SLURMD_SERVICE)
        group_details[func_group] = details
        if not passed:
            all_passed = False

    return {
        "success": all_passed,
        "message": SLURMD_LOGIN_CHECK_PASSED if all_passed else SLURMD_LOGIN_CHECK_FAILED,
        "group_details": group_details,
        "error": "" if all_passed else SLURMD_LOGIN_CHECK_FAILED,
    }


def verify_munge_active(host) -> Dict[str, Any]:
    """TC3: Verify munge service is active on all slurm-related nodes.

    Checks slurm control nodes, login nodes, login compiler nodes, and slurm nodes.

    Returns:
        Dict with success, message, group_details (per functional group), error.
    """
    munge_nodes_grouped = get_all_munge_nodes(host)
    if not munge_nodes_grouped:
        return {
            "success": False,
            "message": "No nodes found requiring munge service",
            "group_details": {},
            "error": "No nodes found requiring munge service",
        }

    all_passed = True
    group_details = {}

    for func_group, nodes in munge_nodes_grouped.items():
        passed, details = _check_service_on_nodes(host, nodes, MUNGE_SERVICE)
        group_details[func_group] = details
        if not passed:
            all_passed = False

    return {
        "success": all_passed,
        "message": MUNGE_CHECK_PASSED if all_passed else MUNGE_CHECK_FAILED,
        "group_details": group_details,
        "error": "" if all_passed else MUNGE_CHECK_FAILED,
    }


def verify_slurm_nodes_idle(host) -> Dict[str, Any]:
    """TC4: Check if all slurm nodes are in idle state using sinfo.

    Runs 'sinfo' on the first slurm control node and verifies all nodes
    are in idle (or idle~) state.

    Returns:
        Dict with success, message, sinfo_output, node_states, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_CONTROL_NODES,
            "sinfo_output": "",
            "node_states": [],
            "error": ERROR_NO_SLURM_CONTROL_NODES,
        }

    control_node = control_nodes[0]
    control_ip = control_node.get("admin_ip", "")
    control_hostname = control_node.get("hostname", "unknown")

    if not control_ip:
        return {
            "success": False,
            "message": f"Slurm control node {control_hostname} has no admin IP",
            "sinfo_output": "",
            "node_states": [],
            "error": "No admin IP for control node",
        }

    # Run sinfo with node-oriented output
    cmd = _safe_run_on_remote_node(host, "sinfo -N -h -o '%N %T'", control_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "message": SINFO_COMMAND_FAILED.format(node=control_hostname, error=cmd.stderr.strip()),
            "sinfo_output": cmd.stderr.strip(),
            "node_states": [],
            "error": cmd.stderr.strip(),
        }

    output = cmd.stdout.strip()
    if not output:
        return {
            "success": False,
            "message": SINFO_NO_OUTPUT.format(node=control_hostname),
            "sinfo_output": "",
            "node_states": [],
            "error": "Empty sinfo output",
        }

    # Parse sinfo output: each line is "NODENAME STATE"
    node_states = []
    all_idle = True
    for line in output.split('\n'):
        parts = line.strip().split()
        if len(parts) >= 2:
            node_name = parts[0]
            state = parts[1]
            # idle and idle~ (powered down) are acceptable idle states
            is_idle = state.lower() in ("idle", "idle~")
            node_states.append({
                "node": node_name,
                "state": state,
                "idle": is_idle,
            })
            if not is_idle:
                all_idle = False

    return {
        "success": all_idle,
        "message": SINFO_CHECK_PASSED if all_idle else SINFO_CHECK_FAILED,
        "sinfo_output": output,
        "node_states": node_states,
        "error": "" if all_idle else SINFO_CHECK_FAILED,
    }


def verify_login_nodes_idle(host) -> Dict[str, Any]:
    """Check if all login and login compiler nodes are in idle state.

    Uses scontrol on the control node to query state for each login node.
    Skips if no login or login_compiler nodes are configured.

    Returns:
        Dict with success, message, node_states, error.
    """
    login_nodes = get_login_nodes(host)
    login_compiler_nodes = get_login_compiler_nodes(host)
    all_login = login_nodes + login_compiler_nodes

    if not all_login:
        return {
            "success": True,
            "skipped": True,
            "message": LOGIN_NODES_IDLE_NO_NODES,
            "node_states": [],
            "error": "",
        }

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_CONTROL_NODES,
            "node_states": [],
            "error": ERROR_NO_SLURM_CONTROL_NODES,
        }
    control_ip = control_nodes[0].get("admin_ip", "")

    all_idle = True
    node_states = []

    for node in all_login:
        hostname = node.get("hostname", "unknown")
        cmd = _safe_run_on_remote_node(
            host,
            f"scontrol show node {hostname} 2>/dev/null | grep -oP 'State=\\K\\S+'",
            control_ip,
        )
        if cmd.rc != 0 or not cmd.stdout.strip():
            node_states.append({"node": hostname, "state": "UNKNOWN", "idle": False})
            all_idle = False
            continue
        state = cmd.stdout.strip().upper()
        is_idle = state.startswith("IDLE")
        node_states.append({"node": hostname, "state": state, "idle": is_idle})
        if not is_idle:
            all_idle = False

    failed = [n["node"] for n in node_states if not n["idle"]]
    return {
        "success": all_idle,
        "message": (LOGIN_NODES_IDLE_PASSED if all_idle
                    else LOGIN_NODES_IDLE_FAILED.format(details=", ".join(failed))),
        "node_states": node_states,
        "error": ("" if all_idle
                  else LOGIN_NODES_IDLE_FAILED.format(details=", ".join(failed))),
    }


def verify_srun_job(host) -> Dict[str, Any]:
    """TC5: Submit a basic srun job from the control node and verify success.

    Runs: srun -N <total_slurm_nodes> hostname
    from the first slurm control node.

    Returns:
        Dict with success, message, output, num_nodes, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": SRUN_NO_CONTROL_NODE,
            "output": "",
            "num_nodes": 0,
            "error": SRUN_NO_CONTROL_NODE,
        }

    control_node = control_nodes[0]
    control_ip = control_node.get("admin_ip", "")

    if not control_ip:
        return {
            "success": False,
            "message": "Slurm control node has no admin IP",
            "output": "",
            "num_nodes": 0,
            "error": "No admin IP for control node",
        }

    num_slurm_nodes = get_slurm_node_count(host)
    if num_slurm_nodes == 0:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_NODES,
            "output": "",
            "num_nodes": 0,
            "error": ERROR_NO_SLURM_NODES,
        }

    srun_cmd = f"srun -N {num_slurm_nodes} hostname"
    cmd = _safe_run_on_remote_node(host, srun_cmd, control_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "message": SRUN_CHECK_FAILED.format(error=cmd.stderr.strip()),
            "output": cmd.stdout.strip(),
            "num_nodes": num_slurm_nodes,
            "error": cmd.stderr.strip(),
        }

    # Verify we got output from all nodes
    hostnames = [line.strip() for line in cmd.stdout.strip().split('\n') if line.strip()]

    return {
        "success": True,
        "message": SRUN_CHECK_PASSED.format(num_nodes=num_slurm_nodes),
        "output": cmd.stdout.strip(),
        "num_nodes": num_slurm_nodes,
        "hostnames_returned": hostnames,
        "error": "",
    }


def verify_sbatch_job(host) -> Dict[str, Any]:
    """TC6: Submit a basic sbatch job from the control node as root and verify via sacct.

    Creates a temporary sbatch script on the control node, submits it,
    then polls sacct until the job completes or times out.

    Returns:
        Dict with success, message, job_id, job_state, output, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": SBATCH_NO_CONTROL_NODE,
            "job_id": "",
            "job_state": "",
            "output": "",
            "error": SBATCH_NO_CONTROL_NODE,
        }

    control_node = control_nodes[0]
    control_ip = control_node.get("admin_ip", "")

    if not control_ip:
        return {
            "success": False,
            "message": "Slurm control node has no admin IP",
            "job_id": "",
            "job_state": "",
            "output": "",
            "error": "No admin IP for control node",
        }

    num_slurm_nodes = get_slurm_node_count(host)
    if num_slurm_nodes == 0:
        return {
            "success": False,
            "message": ERROR_NO_SLURM_NODES,
            "job_id": "",
            "job_state": "",
            "output": "",
            "error": ERROR_NO_SLURM_NODES,
        }

    # Get the path to the sbatch job script
    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    job_script_local = os.path.join(jobs_dir, "basic_sbatch.sh")

    # Read the job script template and substitute node count
    with open(job_script_local, "r", encoding="utf-8") as f:
        job_script_content = f.read()

    job_script_content = job_script_content.replace(
        "{{SLURM_NUM_NODES}}", str(num_slurm_nodes)
    )
    job_script_content = job_script_content.replace("{{OUTPUT_PATH}}", "/home")

    # Transfer script to remote node using base64 encoding to avoid
    # quoting issues with run_on_remote_node (which wraps cmd in double quotes).
    encoded = base64.b64encode(job_script_content.encode()).decode()
    create_script_cmd = (
        f"echo {encoded} | base64 -d > /home/omnia_test_sbatch.sh && "
        f"chmod +x /home/omnia_test_sbatch.sh"
    )
    cmd = _safe_run_on_remote_node(host, create_script_cmd, control_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "message": f"Failed to create sbatch script on control node: {cmd.stderr.strip()}",
            "job_id": "",
            "job_state": "",
            "output": "",
            "error": cmd.stderr.strip(),
        }

    # Submit the sbatch job
    submit_cmd = "sbatch /home/omnia_test_sbatch.sh"
    cmd = _safe_run_on_remote_node(host, submit_cmd, control_ip)

    if cmd.rc != 0:
        return {
            "success": False,
            "message": SBATCH_SUBMIT_FAILED.format(error=cmd.stderr.strip()),
            "job_id": "",
            "job_state": "",
            "output": cmd.stdout.strip(),
            "error": cmd.stderr.strip(),
        }

    # Extract job ID from "Submitted batch job <ID>"
    submit_output = cmd.stdout.strip()
    match = re.search(r"Submitted batch job (\d+)", submit_output)
    if not match:
        return {
            "success": False,
            "message": f"Could not parse job ID from sbatch output: {submit_output}",
            "job_id": "",
            "job_state": "",
            "output": submit_output,
            "error": "Failed to parse job ID",
        }

    job_id = match.group(1)

    # Poll sacct for job completion
    start_time = time.time()
    job_state = ""
    while time.time() - start_time < SACCT_TIMEOUT:
        time.sleep(SACCT_POLL_INTERVAL)
        sacct_cmd = f"sacct -j {job_id} --format=JobID,State,ExitCode -n -P"
        cmd = _safe_run_on_remote_node(host, sacct_cmd, control_ip)

        if cmd.rc != 0:
            continue

        # Parse sacct output - look for the main job entry (not .batch or .extern)
        for line in cmd.stdout.strip().split('\n'):
            parts = line.strip().split('|')
            if len(parts) >= 2 and parts[0] == job_id:
                job_state = parts[1].strip()
                break

        if job_state in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"):
            break

    # Read job output from the compute node (Slurm writes --output on the allocated node)
    job_output = ""
    sacct_nodes_cmd = _safe_run_on_remote_node(
        host,
        f"sacct -j {job_id} --format=NodeList -n -P 2>/dev/null | head -1",
        control_ip,
    )
    if sacct_nodes_cmd.rc == 0 and sacct_nodes_cmd.stdout.strip() and sacct_nodes_cmd.stdout.strip() != "None assigned":
        nodelist_str = sacct_nodes_cmd.stdout.strip()
        expand_cmd = _safe_run_on_remote_node(
            host, f"scontrol show hostname {nodelist_str} 2>/dev/null", control_ip,
        )
        allocated_nodes = []
        if expand_cmd.rc == 0 and expand_cmd.stdout.strip():
            allocated_nodes = [n.strip() for n in expand_cmd.stdout.strip().split('\n') if n.strip()]
        else:
            allocated_nodes = [nodelist_str]

        # Build hostname -> IP map from slurm nodes
        slurm_nodes = get_slurm_nodes(host)
        node_ip_map = {n.get("hostname", ""): n.get("admin_ip", "") for n in slurm_nodes if n.get("hostname")}

        if allocated_nodes:
            first_node_ip = node_ip_map.get(allocated_nodes[0], "")
            if first_node_ip:
                read_out = _safe_run_on_remote_node(
                    host, f"cat /home/omnia_test_sbatch_{job_id}.out 2>/dev/null", first_node_ip,
                )
                if read_out.rc == 0:
                    job_output = read_out.stdout.strip()

    # Cleanup the script on control node (keep output files)
    _safe_run_on_remote_node(host, "rm -f /home/omnia_test_sbatch.sh", control_ip)

    if job_state == "COMPLETED":
        return {
            "success": True,
            "message": SBATCH_CHECK_PASSED.format(job_id=job_id),
            "job_id": job_id,
            "job_state": job_state,
            "output": submit_output,
            "job_output": job_output,
            "output_verified": bool(job_output),
            "error": "",
        }

    if not job_state:
        return {
            "success": False,
            "message": SBATCH_TIMEOUT.format(job_id=job_id, timeout=SACCT_TIMEOUT),
            "job_id": job_id,
            "job_state": "UNKNOWN",
            "output": submit_output,
            "job_output": job_output,
            "output_verified": False,
            "error": f"Job did not complete within {SACCT_TIMEOUT}s",
        }

    return {
        "success": False,
        "message": SBATCH_CHECK_FAILED.format(error=f"Job {job_id} ended with state: {job_state}"),
        "job_id": job_id,
        "job_state": job_state,
        "output": submit_output,
        "job_output": job_output,
        "output_verified": False,
        "error": SACCT_JOB_STATUS.format(job_id=job_id, state=job_state),
    }


# =============================================================================
# SHARED HELPERS for root-on-login-node tests
# =============================================================================

def _transfer_script_to_node(host, node_ip: str, local_path: str,
                             remote_path: str,
                             replacements: Dict[str, str]) -> Dict[str, Any]:
    """Read a local script, apply placeholder replacements, transfer via base64."""
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    encoded = base64.b64encode(content.encode()).decode()
    cmd = _safe_run_on_remote_node(
        host,
        f"echo {encoded} | base64 -d > {remote_path} && chmod a+rx {remote_path}",
        node_ip,
    )
    if cmd.rc != 0:
        return {"success": False, "error": cmd.stderr.strip()}
    return {"success": True, "error": ""}


def _submit_and_poll_root(host, submit_ip: str, control_ip: str,
                          remote_script: str) -> Dict[str, Any]:
    """Submit an sbatch job as root on *submit_ip*, poll on *control_ip*.

    Returns dict with success, job_id, job_state, error.
    """
    cmd = _safe_run_on_remote_node(host, f"sbatch {remote_script}", submit_ip)
    if cmd.rc != 0:
        return {"success": False, "job_id": "", "job_state": "",
                "error": cmd.stderr.strip()}

    match = re.search(r"Submitted batch job (\d+)", cmd.stdout.strip())
    if not match:
        return {"success": False, "job_id": "", "job_state": "",
                "error": f"Parse failed: {cmd.stdout.strip()}"}
    job_id = match.group(1)

    start = time.time()
    job_state = ""
    while time.time() - start < SACCT_TIMEOUT:
        time.sleep(SACCT_POLL_INTERVAL)
        sacct = _safe_run_on_remote_node(
            host, f"sacct -j {job_id} --format=JobID,State -n -P", control_ip,
        )
        if sacct.rc != 0:
            continue
        for line in sacct.stdout.strip().split('\n'):
            parts = line.strip().split('|')
            if len(parts) >= 2 and parts[0] == job_id:
                job_state = parts[1].strip()
                break
        if job_state in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"):
            break

    return {
        "success": job_state == "COMPLETED",
        "job_id": job_id,
        "job_state": job_state or "UNKNOWN",
        "error": "" if job_state == "COMPLETED" else f"Job {job_id} state: {job_state}",
    }


def _get_all_login_nodes(host) -> List[Dict[str, str]]:
    """Return combined list of login nodes + login compiler nodes."""
    nodes = get_login_nodes(host)
    nodes.extend(get_login_compiler_nodes(host))
    return nodes


# =============================================================================
# TC13: Root single sbatch job from login node
# =============================================================================

def verify_root_sbatch_from_login_node(host) -> Dict[str, Any]:
    """Submit a single sbatch job as root from each login/login_compiler node.

    Returns:
        Dict with success, message, node_results (list), error.
    """
    all_login = _get_all_login_nodes(host)
    if not all_login:
        return {"skipped": True, "message": ROOT_NO_LOGIN_NODES,
                "node_results": [], "error": ROOT_NO_LOGIN_NODES}

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "node_results": [], "error": ERROR_NO_SLURM_CONTROL_NODES}
    control_ip = control_nodes[0].get("admin_ip", "")

    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    num_nodes = get_slurm_node_count(host) or 1

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

        remote_script = "/home/omnia_test_root_single.sh"
        xfer = _transfer_script_to_node(
            host, node_ip,
            os.path.join(jobs_dir, "basic_sbatch.sh"),
            remote_script,
            {"{{SLURM_NUM_NODES}}": str(num_nodes), "{{OUTPUT_PATH}}": "/home"},
        )
        if not xfer["success"]:
            node_results.append({"node": hostname, "success": False,
                                 "job_id": "", "job_state": "",
                                 "error": xfer["error"]})
            all_passed = False
            continue

        result = _submit_and_poll_root(host, node_ip, control_ip, remote_script)
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", node_ip)

        node_results.append({
            "node": hostname, "success": result["success"],
            "job_id": result["job_id"], "job_state": result["job_state"],
            "error": result["error"],
        })
        if not result["success"]:
            all_passed = False

    msg = (ROOT_LOGIN_ALLNODES_PASSED.format(count=len(all_login))
           if all_passed
           else ROOT_LOGIN_ALLNODES_FAILED.format(
               error="One or more login nodes failed"))
    return {"success": all_passed, "message": msg,
            "node_results": node_results, "error": "" if all_passed else msg}


# =============================================================================
# TC14: Root multiple sbatch jobs from login node
# =============================================================================

def verify_root_multi_sbatch_from_login_node(host) -> Dict[str, Any]:
    """Submit MULTI_JOB_COUNT sbatch jobs as root from a login node.

    Returns:
        Dict with success, message, submit_node, job_results (list), error.
    """
    all_login = _get_all_login_nodes(host)
    if not all_login:
        return {"skipped": True, "message": ROOT_NO_LOGIN_NODES,
                "submit_node": "", "job_results": [],
                "error": ROOT_NO_LOGIN_NODES}

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "submit_node": "", "job_results": [],
                "error": ERROR_NO_SLURM_CONTROL_NODES}
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
    num_nodes = get_slurm_node_count(host) or 1
    remote_script = "/home/omnia_test_root_multi.sh"
    xfer = _transfer_script_to_node(
        host, node_ip,
        os.path.join(jobs_dir, "basic_sbatch.sh"),
        remote_script,
        {"{{SLURM_NUM_NODES}}": str(num_nodes), "{{OUTPUT_PATH}}": "/home"},
    )
    if not xfer["success"]:
        return {"success": False,
                "message": f"Script transfer failed: {xfer['error']}",
                "submit_node": hostname, "job_results": [],
                "error": xfer["error"]}

    all_passed = True
    job_results = []
    for i in range(MULTI_JOB_COUNT):
        result = _submit_and_poll_root(host, node_ip, control_ip, remote_script)
        job_results.append({
            "index": i + 1, "success": result["success"],
            "job_id": result["job_id"], "job_state": result["job_state"],
            "error": result["error"],
        })
        if not result["success"]:
            all_passed = False

    _safe_run_on_remote_node(host, f"rm -f {remote_script}", node_ip)

    msg = (ROOT_LOGIN_MULTI_PASSED.format(count=MULTI_JOB_COUNT, node=hostname)
           if all_passed
           else ROOT_LOGIN_MULTI_FAILED.format(node=hostname,
               error="One or more jobs failed"))
    return {"success": all_passed, "message": msg,
            "submit_node": hostname, "job_results": job_results,
            "error": "" if all_passed else msg}


# =============================================================================
# TC19: Drain nodes → submit → PENDING → undrain → RUNNING/COMPLETED
# =============================================================================

def verify_drain_undrain_queuing(host) -> Dict[str, Any]:
    """Drain all slurm compute nodes, submit a job, verify PENDING with reason,
    undrain, verify job transitions to RUNNING/COMPLETED.

    Returns:
        Dict with success, message, steps, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "steps": [], "error": ERROR_NO_SLURM_CONTROL_NODES}
    control_ip = control_nodes[0].get("admin_ip", "")

    slurm_nodes = get_slurm_nodes(host)
    if not slurm_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "steps": [], "error": ERROR_NO_SLURM_NODES}

    steps = []
    hostnames = [n.get("hostname", "") for n in slurm_nodes if n.get("hostname")]
    nodelist = ",".join(hostnames)

    # Step 1: Drain all slurm nodes
    drain_cmd = _safe_run_on_remote_node(
        host,
        f"scontrol update NodeName={nodelist} State=drain Reason='{DRAIN_REASON}'",
        control_ip,
    )
    if drain_cmd.rc != 0:
        return {"success": False,
                "message": DRAIN_FAILED.format(error=drain_cmd.stderr.strip()),
                "steps": steps, "error": drain_cmd.stderr.strip()}
    steps.append({"step": "drain_nodes", "success": True, "nodes": nodelist})
    time.sleep(DRAIN_UNDRAIN_SETTLE_DELAY)

    # Verify drained state
    sinfo = _safe_run_on_remote_node(host, "sinfo -N -h -o '%N %T'", control_ip)
    sinfo_output = sinfo.stdout.strip() if sinfo.rc == 0 else ""
    steps.append({"step": "verify_drained", "success": True,
                  "sinfo_output": sinfo_output})

    # Step 2: Submit a job (should go to PENDING)
    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    remote_script = "/home/omnia_test_drain.sh"
    xfer = _transfer_script_to_node(
        host, control_ip,
        os.path.join(jobs_dir, "basic_sbatch.sh"),
        remote_script,
        {"{{SLURM_NUM_NODES}}": "1", "{{OUTPUT_PATH}}": "/home"},
    )
    if not xfer["success"]:
        # Undrain before returning
        _safe_run_on_remote_node(
            host,
            f"scontrol update NodeName={nodelist} State=resume",
            control_ip,
        )
        return {"success": False,
                "message": f"Script transfer failed: {xfer['error']}",
                "steps": steps, "error": xfer["error"]}

    submit = _safe_run_on_remote_node(host, f"sbatch {remote_script}", control_ip)
    if submit.rc != 0:
        _safe_run_on_remote_node(
            host,
            f"scontrol update NodeName={nodelist} State=resume",
            control_ip,
        )
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False,
                "message": f"Job submit failed: {submit.stderr.strip()}",
                "steps": steps, "error": submit.stderr.strip()}

    match = re.search(r"Submitted batch job (\d+)", submit.stdout.strip())
    if not match:
        _safe_run_on_remote_node(
            host,
            f"scontrol update NodeName={nodelist} State=resume",
            control_ip,
        )
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False,
                "message": f"Parse job ID failed: {submit.stdout.strip()}",
                "steps": steps, "error": "Parse failed"}
    job_id = match.group(1)
    steps.append({"step": "submit_job", "success": True, "job_id": job_id})

    # Step 3: Verify job is PENDING with a reason
    time.sleep(DRAIN_UNDRAIN_SETTLE_DELAY)
    squeue = _safe_run_on_remote_node(
        host,
        f"squeue -j {job_id} -h -o '%T %r' 2>/dev/null",
        control_ip,
    )
    pending_output = squeue.stdout.strip() if squeue.rc == 0 else ""
    job_pending = pending_output.startswith("PENDING")
    pending_reason = pending_output.split(None, 1)[1] if job_pending and " " in pending_output else ""
    steps.append({"step": "verify_pending", "success": job_pending,
                  "state_reason": pending_output, "reason": pending_reason})

    if not job_pending:
        _safe_run_on_remote_node(host, f"scancel {job_id}", control_ip)
        _safe_run_on_remote_node(
            host,
            f"scontrol update NodeName={nodelist} State=resume",
            control_ip,
        )
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False,
                "message": DRAIN_JOB_NOT_PENDING.format(
                    job_id=job_id, state=pending_output),
                "steps": steps, "error": f"Not PENDING: {pending_output}"}

    # Step 4: Undrain all nodes
    undrain = _safe_run_on_remote_node(
        host,
        f"scontrol update NodeName={nodelist} State=resume",
        control_ip,
    )
    if undrain.rc != 0:
        _safe_run_on_remote_node(host, f"scancel {job_id}", control_ip)
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
        return {"success": False,
                "message": UNDRAIN_FAILED.format(error=undrain.stderr.strip()),
                "steps": steps, "error": undrain.stderr.strip()}
    steps.append({"step": "undrain_nodes", "success": True})
    time.sleep(DRAIN_UNDRAIN_SETTLE_DELAY)

    # Step 5: Wait for job to complete
    start = time.time()
    final_state = ""
    while time.time() - start < DRAIN_JOB_TRANSITION_TIMEOUT:
        time.sleep(SACCT_POLL_INTERVAL)
        sacct = _safe_run_on_remote_node(
            host,
            f"sacct -j {job_id} --format=JobID,State -n -P 2>/dev/null",
            control_ip,
        )
        if sacct.rc != 0:
            continue
        for line in sacct.stdout.strip().split('\n'):
            parts = line.strip().split('|')
            if len(parts) >= 2 and parts[0] == job_id:
                final_state = parts[1].strip()
                break
        if final_state in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"):
            break

    _safe_run_on_remote_node(host, f"rm -f {remote_script}", control_ip)
    completed = final_state == "COMPLETED"
    steps.append({"step": "verify_completed", "success": completed,
                  "final_state": final_state})

    return {
        "success": completed,
        "message": DRAIN_QUEUE_PASSED if completed else DRAIN_QUEUE_FAILED.format(
            error=f"Job {job_id} final state: {final_state}"),
        "job_id": job_id,
        "steps": steps,
        "error": "" if completed else f"Final state: {final_state}",
    }


# =============================================================================
# TC20: Insufficient resources job submission
# =============================================================================

def verify_insufficient_resources(host) -> Dict[str, Any]:
    """Submit a job requesting more CPUs than available per node.

    Verifies that the job enters PENDING with a resource-related reason
    (e.g., Resources, PartitionNodeLimit) or is rejected outright.

    Returns:
        Dict with success, message, job_id, job_state, reason, error.
    """
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "job_id": "", "job_state": "", "reason": "",
                "error": ERROR_NO_SLURM_CONTROL_NODES}
    control_ip = control_nodes[0].get("admin_ip", "")

    slurm_nodes = get_slurm_nodes(host)
    if not slurm_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "job_id": "", "job_state": "", "reason": "",
                "error": ERROR_NO_SLURM_NODES}

    # Query total CPUs on first node
    first_hostname = slurm_nodes[0].get("hostname", "")
    cpu_cmd = _safe_run_on_remote_node(
        host,
        f"sinfo -N -h -n {first_hostname} -o '%c' 2>/dev/null | head -1",
        control_ip,
    )
    try:
        node_cpus = int(cpu_cmd.stdout.strip())
    except (ValueError, AttributeError):
        node_cpus = 4
    # Request more CPUs than any single node has
    excessive_cpus = node_cpus * len(slurm_nodes) + 100

    # Submit job requesting excessive CPUs
    submit = _safe_run_on_remote_node(
        host,
        f"sbatch --ntasks={excessive_cpus} --wrap='hostname' "
        f"--output=/dev/null --error=/dev/null 2>&1",
        control_ip,
    )

    # Case 1: Submission rejected outright
    if submit.rc != 0:
        output = (submit.stdout.strip() + " " + submit.stderr.strip()).strip()
        return {
            "success": True,
            "message": INSUFF_RESOURCE_PASSED.format(
                detail=f"Job rejected: {output}"),
            "job_id": "", "job_state": "REJECTED",
            "reason": output,
            "error": "",
        }

    # Case 2: Job accepted — verify it goes PENDING with reason
    match = re.search(r"Submitted batch job (\d+)", submit.stdout.strip())
    if not match:
        return {"success": False,
                "message": f"Could not parse job ID: {submit.stdout.strip()}",
                "job_id": "", "job_state": "", "reason": "",
                "error": "Parse failed"}
    job_id = match.group(1)

    time.sleep(DRAIN_UNDRAIN_SETTLE_DELAY)
    squeue = _safe_run_on_remote_node(
        host,
        f"squeue -j {job_id} -h -o '%T %r' 2>/dev/null",
        control_ip,
    )
    state_reason = squeue.stdout.strip() if squeue.rc == 0 else ""
    parts = state_reason.split(None, 1)
    state = parts[0] if parts else ""
    reason = parts[1] if len(parts) > 1 else ""

    # Cancel the job
    _safe_run_on_remote_node(host, f"scancel {job_id}", control_ip)

    if state == "PENDING":
        return {
            "success": True,
            "message": INSUFF_RESOURCE_PASSED.format(
                detail=f"Job {job_id} PENDING with reason: {reason}"),
            "job_id": job_id, "job_state": state,
            "reason": reason,
            "error": "",
        }

    return {
        "success": False,
        "message": INSUFF_RESOURCE_FAILED.format(
            error=f"Job {job_id} in unexpected state: {state_reason}"),
        "job_id": job_id, "job_state": state,
        "reason": reason,
        "error": f"Unexpected state: {state_reason}",
    }


# =============================================================================
# Separate slurmd service checks (login nodes / login compiler nodes)
# =============================================================================

def verify_slurmd_on_login_nodes_only(host) -> Dict[str, Any]:
    """Verify slurmd service is active on login nodes only.

    Returns:
        Dict with success, skipped, message, details, error.
    """
    nodes = get_login_nodes(host)
    if not nodes:
        return {"success": True, "skipped": True,
                "message": "No login nodes found in PXE mapping - skipping",
                "details": [], "error": ""}

    all_passed, details = _check_service_on_nodes(host, nodes, SLURMD_SERVICE)
    return {
        "success": all_passed, "skipped": False,
        "message": SLURMD_LOGIN_ONLY_PASSED if all_passed else SLURMD_LOGIN_ONLY_FAILED,
        "details": details,
        "error": "" if all_passed else SLURMD_LOGIN_ONLY_FAILED,
    }


def verify_slurmd_on_login_compiler_nodes_only(host) -> Dict[str, Any]:
    """Verify slurmd service is active on login compiler nodes only.

    Returns:
        Dict with success, skipped, message, details, error.
    """
    nodes = get_login_compiler_nodes(host)
    if not nodes:
        return {"success": True, "skipped": True,
                "message": "No login compiler nodes found in PXE mapping - skipping",
                "details": [], "error": ""}

    all_passed, details = _check_service_on_nodes(host, nodes, SLURMD_SERVICE)
    return {
        "success": all_passed, "skipped": False,
        "message": SLURMD_LOGINCOMP_ONLY_PASSED if all_passed else SLURMD_LOGINCOMP_ONLY_FAILED,
        "details": details,
        "error": "" if all_passed else SLURMD_LOGINCOMP_ONLY_FAILED,
    }


# =============================================================================
# Separate munge service checks (per node type)
# =============================================================================

def verify_munge_on_control_nodes(host) -> Dict[str, Any]:
    """Verify munge service is active on slurm control nodes.

    Returns:
        Dict with success, skipped, message, details, error.
    """
    nodes = get_slurm_control_nodes(host)
    if not nodes:
        return {"success": True, "skipped": True,
                "message": "No slurm control nodes found in PXE mapping - skipping",
                "details": [], "error": ""}

    all_passed, details = _check_service_on_nodes(host, nodes, MUNGE_SERVICE)
    return {
        "success": all_passed, "skipped": False,
        "message": MUNGE_CONTROL_PASSED if all_passed else MUNGE_CONTROL_FAILED,
        "details": details,
        "error": "" if all_passed else MUNGE_CONTROL_FAILED,
    }


def verify_munge_on_slurm_nodes(host) -> Dict[str, Any]:
    """Verify munge service is active on slurm compute nodes.

    Returns:
        Dict with success, skipped, message, details, error.
    """
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": True, "skipped": True,
                "message": "No slurm compute nodes found in PXE mapping - skipping",
                "details": [], "error": ""}

    all_passed, details = _check_service_on_nodes(host, nodes, MUNGE_SERVICE)
    return {
        "success": all_passed, "skipped": False,
        "message": MUNGE_SLURM_PASSED if all_passed else MUNGE_SLURM_FAILED,
        "details": details,
        "error": "" if all_passed else MUNGE_SLURM_FAILED,
    }


def verify_munge_on_login_nodes(host) -> Dict[str, Any]:
    """Verify munge service is active on login nodes.

    Returns:
        Dict with success, skipped, message, details, error.
    """
    nodes = get_login_nodes(host)
    if not nodes:
        return {"success": True, "skipped": True,
                "message": "No login nodes found in PXE mapping - skipping",
                "details": [], "error": ""}

    all_passed, details = _check_service_on_nodes(host, nodes, MUNGE_SERVICE)
    return {
        "success": all_passed, "skipped": False,
        "message": MUNGE_LOGIN_PASSED if all_passed else MUNGE_LOGIN_FAILED,
        "details": details,
        "error": "" if all_passed else MUNGE_LOGIN_FAILED,
    }


def verify_munge_on_login_compiler_nodes(host) -> Dict[str, Any]:
    """Verify munge service is active on login compiler nodes.

    Returns:
        Dict with success, skipped, message, details, error.
    """
    nodes = get_login_compiler_nodes(host)
    if not nodes:
        return {"success": True, "skipped": True,
                "message": "No login compiler nodes found in PXE mapping - skipping",
                "details": [], "error": ""}

    all_passed, details = _check_service_on_nodes(host, nodes, MUNGE_SERVICE)
    return {
        "success": all_passed, "skipped": False,
        "message": MUNGE_LOGINCOMP_PASSED if all_passed else MUNGE_LOGINCOMP_FAILED,
        "details": details,
        "error": "" if all_passed else MUNGE_LOGINCOMP_FAILED,
    }


# =============================================================================
# Passwordless SSH between node types
# =============================================================================

def _get_nodes_by_type(host, node_type: str) -> List[Dict[str, str]]:
    """Return nodes for a given node type string."""
    if node_type == "slurm_control_node":
        return get_slurm_control_nodes(host)
    if node_type == "slurm_node":
        return get_slurm_nodes(host)
    if node_type == "login_node":
        return get_login_nodes(host)
    if node_type == "login_compiler_node":
        return get_login_compiler_nodes(host)
    return []


def verify_passwordless_ssh(host, src_type: str,
                            dst_type: str) -> Dict[str, Any]:
    """Verify passwordless SSH as root from all src_type nodes to all dst_type nodes.

    Args:
        src_type: Source node type (e.g., 'slurm_control_node').
        dst_type: Destination node type (e.g., 'slurm_node').

    Returns:
        Dict with success, skipped, message, pair_results, error.
    """
    src_nodes = _get_nodes_by_type(host, src_type)
    if not src_nodes:
        return {"success": True, "skipped": True,
                "message": f"No {src_type} nodes found in PXE mapping - skipping",
                "pair_results": [], "error": ""}

    dst_nodes = _get_nodes_by_type(host, dst_type)
    if not dst_nodes:
        return {"success": True, "skipped": True,
                "message": f"No {dst_type} nodes found in PXE mapping - skipping",
                "pair_results": [], "error": ""}

    all_passed = True
    pair_results = []

    for src in src_nodes:
        src_hostname = src.get("hostname", "unknown")
        src_ip = src.get("admin_ip", "")
        if not src_ip:
            pair_results.append({
                "src": src_hostname, "dst": "all",
                "success": False, "error": "No src admin IP",
            })
            all_passed = False
            continue

        for dst in dst_nodes:
            dst_hostname = dst.get("hostname", "unknown")
            dst_ip = dst.get("admin_ip", "")
            if not dst_ip:
                pair_results.append({
                    "src": src_hostname, "dst": dst_hostname,
                    "success": False, "error": "No dst admin IP",
                })
                all_passed = False
                continue

            # From src node, SSH to dst node and run hostname
            cmd = _safe_run_on_remote_node(
                host,
                f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
                f"-o ConnectTimeout={10} -o BatchMode=yes "
                f"{dst_ip} hostname",
                src_ip,
            )
            ok = cmd.rc == 0 and cmd.stdout.strip() != ""
            pair_results.append({
                "src": src_hostname, "dst": dst_hostname,
                "success": ok,
                "output": cmd.stdout.strip(),
                "error": "" if ok else cmd.stderr.strip(),
            })
            if not ok:
                all_passed = False

    msg = (SSH_PASSWORDLESS_PASSED.format(src_type=src_type, dst_type=dst_type)
           if all_passed
           else SSH_PASSWORDLESS_FAILED.format(src_type=src_type, dst_type=dst_type))
    return {
        "success": all_passed, "skipped": False,
        "message": msg,
        "pair_results": pair_results,
        "error": "" if all_passed else msg,
    }


# =============================================================================
# Multi-login-node job submission (only when >1 login nodes exist)
# =============================================================================

def verify_root_sbatch_from_multiple_login_nodes(host) -> Dict[str, Any]:
    """Submit sbatch jobs as root from each login node when >1 login nodes exist.

    Skips if only 1 (or 0) login nodes found (login_node only, not compiler).

    Returns:
        Dict with success, skipped, message, node_results, error.
    """
    login_nodes = get_login_nodes(host)
    if len(login_nodes) <= 1:
        return {"success": True, "skipped": True,
                "message": MULTI_LOGIN_SKIP.format(count=len(login_nodes)),
                "node_results": [], "error": ""}

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "skipped": False,
                "message": ERROR_NO_SLURM_CONTROL_NODES,
                "node_results": [], "error": ERROR_NO_SLURM_CONTROL_NODES}
    control_ip = control_nodes[0].get("admin_ip", "")

    jobs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "slurm_jobs",
    )
    num_nodes = get_slurm_node_count(host) or 1

    all_passed = True
    node_results = []

    for node in login_nodes:
        hostname = node.get("hostname", "unknown")
        node_ip = node.get("admin_ip", "")
        if not node_ip:
            node_results.append({"node": hostname, "success": False,
                                 "job_id": "", "job_state": "",
                                 "error": "No admin IP"})
            all_passed = False
            continue

        remote_script = "/home/omnia_test_multilogin.sh"
        xfer = _transfer_script_to_node(
            host, node_ip,
            os.path.join(jobs_dir, "basic_sbatch.sh"),
            remote_script,
            {"{{SLURM_NUM_NODES}}": str(num_nodes), "{{OUTPUT_PATH}}": "/home"},
        )
        if not xfer["success"]:
            node_results.append({"node": hostname, "success": False,
                                 "job_id": "", "job_state": "",
                                 "error": xfer["error"]})
            all_passed = False
            continue

        result = _submit_and_poll_root(host, node_ip, control_ip, remote_script)
        _safe_run_on_remote_node(host, f"rm -f {remote_script}", node_ip)

        node_results.append({
            "node": hostname, "success": result["success"],
            "job_id": result["job_id"], "job_state": result["job_state"],
            "error": result["error"],
        })
        if not result["success"]:
            all_passed = False

    msg = (MULTI_LOGIN_JOB_PASSED.format(count=len(login_nodes))
           if all_passed
           else MULTI_LOGIN_JOB_FAILED.format(
               error="One or more login nodes failed"))
    return {"success": all_passed, "skipped": False, "message": msg,
            "node_results": node_results, "error": "" if all_passed else msg}
