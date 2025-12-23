"""
Slurm Job Queueing - Core Functions.

This module contains all functions for running and verifying Slurm job queueing.
Test functions should call these functions - all logic resides here.

Usage:
    from automation_library.functions.slurm_job_queueing_func import (
        submit_slurm_job,
        get_job_state,
        get_slurm_node_status,
        check_slurmctld_running,
        get_scheduler_info,
        cancel_slurm_jobs,
        run_all_validations,
    )

Author: Dell Technologies
"""

import re
import time
import subprocess
from typing import Dict, Any, List, Optional

from ..vars.slurm_job_queueing_vars import (
    SLURM_JOB_QUEUEING_VARS,
    PENDING_REASONS,
    AVAILABLE_NODE_STATES,
)
from ..messages.slurm_job_queueing_msgs import SLURM_JOB_QUEUEING_MSGS


# =============================================================================
# SSH HOST CLASS (for direct SSH execution)
# =============================================================================

class SSHHost:
    """SSH host class that mimics testinfra host interface."""
    
    def __init__(self, target_ip: str, via_host: str = None):
        self.target_ip = target_ip
        self.via_host = via_host
        self.ssh_timeout = SLURM_JOB_QUEUEING_VARS["ssh_timeout"]
    
    def run(self, command: str, timeout: int = 60):
        """Run command on remote host via SSH."""
        if self.via_host:
            # Nested SSH: local -> omnia_core -> target
            escaped_command = command.replace('\\', '\\\\').replace('"', '\\"')
            ssh_cmd = (
                f'ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout={self.ssh_timeout} '
                f'{self.via_host} "ssh -o BatchMode=yes -o StrictHostKeyChecking=no '
                f'-o ConnectTimeout={self.ssh_timeout} {self.target_ip} \\"{escaped_command}\\""'
            )
        else:
            ssh_cmd = (
                f'ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout={self.ssh_timeout} '
                f'{self.target_ip} "{command}"'
            )
        
        try:
            result = subprocess.run(
                ssh_cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return CommandResult(result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return CommandResult(-1, "", "Command timed out")
        except Exception as e:
            return CommandResult(-1, "", str(e))


class CommandResult:
    """Command result class that mimics testinfra CommandResult."""
    
    def __init__(self, rc: int, stdout: str, stderr: str):
        self.rc = rc
        self.stdout = stdout.strip() if stdout else ""
        self.stderr = stderr.strip() if stderr else ""


# =============================================================================
# JOB SUBMISSION FUNCTIONS
# =============================================================================

def submit_slurm_job(host, job_name: str = "test_queue_job") -> Dict[str, Any]:
    """
    Submit a job to Slurm and return the job ID.

    Args:
        host: testinfra host object or SSHHost
        job_name: name for the submitted job

    Returns:
        Dict with 'success', 'job_id', 'error'
    """
    cmd = host.run(f"sbatch --job-name={job_name} --time=00:05:00 --nodes=1 --ntasks=1 --wrap='sleep 30; hostname'")
    
    if cmd.rc == 0:
        match = re.search(r'Submitted batch job (\d+)', cmd.stdout)
        if match:
            return {"success": True, "job_id": match.group(1), "error": None}
        return {"success": False, "job_id": None, "error": f"Could not parse job ID: {cmd.stdout}"}
    
    return {"success": False, "job_id": None, "error": cmd.stderr or cmd.stdout or "Unknown error"}


def submit_multiple_jobs(host, count: int = None, job_name: str = "test_queue_job") -> Dict[str, Any]:
    """
    Submit multiple jobs to Slurm.

    Args:
        host: testinfra host object or SSHHost
        count: number of jobs to submit (default from config)
        job_name: base name for the submitted jobs

    Returns:
        Dict with 'success', 'job_ids', 'submitted', 'failed', 'errors'
    """
    count = count or SLURM_JOB_QUEUEING_VARS["job_submit_count"]
    job_ids = []
    errors = []
    
    for i in range(count):
        result = submit_slurm_job(host, f"{job_name}_{i+1}")
        if result["success"]:
            job_ids.append(result["job_id"])
        else:
            errors.append(f"Job {i+1}: {result['error']}")
    
    return {
        "success": len(job_ids) == count,
        "job_ids": job_ids,
        "submitted": len(job_ids),
        "failed": count - len(job_ids),
        "total": count,
        "errors": errors
    }


# =============================================================================
# JOB STATE FUNCTIONS
# =============================================================================

def get_job_state(host, job_id: str) -> Dict[str, Any]:
    """
    Get the current state of a Slurm job.

    Args:
        host: testinfra host object or SSHHost
        job_id: Slurm job ID

    Returns:
        Dict with 'success', 'state', 'reason', 'nodes', 'partition', 'error'
    """
    cmd = host.run(f"squeue -j {job_id} -o '%T|%r|%N|%P' --noheader")
    
    if cmd.rc == 0 and cmd.stdout:
        parts = cmd.stdout.split('|')
        return {
            "success": True,
            "state": parts[0] if len(parts) > 0 else "UNKNOWN",
            "reason": parts[1] if len(parts) > 1 else "None",
            "nodes": parts[2] if len(parts) > 2 else "None",
            "partition": parts[3] if len(parts) > 3 else "None",
            "error": None
        }
    
    # Check sacct for completed jobs
    sacct_cmd = host.run(f"sacct -j {job_id} -o State --noheader -n | head -1")
    if sacct_cmd.rc == 0 and sacct_cmd.stdout:
        return {
            "success": True,
            "state": sacct_cmd.stdout.split()[0] if sacct_cmd.stdout else "UNKNOWN",
            "reason": "Completed",
            "nodes": "N/A",
            "partition": "N/A",
            "error": None
        }
    
    return {"success": False, "state": "UNKNOWN", "reason": None, "nodes": None, "partition": None, "error": "Job not found"}


def get_multiple_job_states(host, job_ids: List[str]) -> Dict[str, Any]:
    """
    Get states for multiple jobs.

    Args:
        host: testinfra host object or SSHHost
        job_ids: list of Slurm job IDs

    Returns:
        Dict with 'success', 'states', 'pending', 'running', 'completed', 'other'
    """
    states = []
    pending = []
    running = []
    completed = []
    other = []
    
    for job_id in job_ids:
        state_info = get_job_state(host, job_id)
        state = state_info.get("state", "UNKNOWN").upper()
        
        states.append({
            "job_id": job_id,
            "state": state,
            "reason": state_info.get("reason", "None"),
            "nodes": state_info.get("nodes", "None")
        })
        
        if state == "PENDING":
            pending.append(job_id)
        elif state == "RUNNING":
            running.append(job_id)
        elif state in ["COMPLETED", "COMPLETING"]:
            completed.append(job_id)
        else:
            other.append(job_id)
    
    return {
        "success": True,
        "states": states,
        "pending": pending,
        "running": running,
        "completed": completed,
        "other": other,
        "pending_count": len(pending),
        "running_count": len(running),
        "completed_count": len(completed)
    }


def validate_pending_reasons(host, job_ids: List[str]) -> Dict[str, Any]:
    """
    Validate that pending jobs have valid reasons.

    Args:
        host: testinfra host object or SSHHost
        job_ids: list of Slurm job IDs

    Returns:
        Dict with 'success', 'valid_reasons', 'invalid_reasons', 'details'
    """
    valid_reasons = []
    invalid_reasons = []
    
    for job_id in job_ids:
        state_info = get_job_state(host, job_id)
        state = state_info.get("state", "UNKNOWN").upper()
        reason = state_info.get("reason", "None")
        
        if state == "PENDING":
            if any(r.lower() in reason.lower() for r in PENDING_REASONS):
                valid_reasons.append({"job_id": job_id, "reason": reason})
            else:
                invalid_reasons.append({"job_id": job_id, "reason": reason})
    
    return {
        "success": len(invalid_reasons) == 0,
        "valid_reasons": valid_reasons,
        "invalid_reasons": invalid_reasons,
        "reasons_found": list(set(r["reason"] for r in valid_reasons)),
        "details": f"Valid: {len(valid_reasons)}, Invalid: {len(invalid_reasons)}"
    }


def wait_for_job_state(host, job_id: str, target_state: str = "RUNNING", 
                       timeout: int = None, poll_interval: int = None) -> Dict[str, Any]:
    """
    Wait for a job to reach a target state.

    Args:
        host: testinfra host object or SSHHost
        job_id: Slurm job ID
        target_state: state to wait for (default: RUNNING)
        timeout: max seconds to wait (default from config)
        poll_interval: seconds between checks (default from config)

    Returns:
        Dict with 'success', 'final_state', 'elapsed', 'details'
    """
    timeout = timeout or SLURM_JOB_QUEUEING_VARS["job_wait_timeout"]
    poll_interval = poll_interval or SLURM_JOB_QUEUEING_VARS["poll_interval"]
    
    start_time = time.time()
    final_state = None
    
    while time.time() - start_time < timeout:
        state_info = get_job_state(host, job_id)
        current_state = state_info.get("state", "UNKNOWN").upper()
        final_state = state_info
        
        if current_state == target_state.upper():
            elapsed = int(time.time() - start_time)
            return {
                "success": True,
                "final_state": current_state,
                "reason": state_info.get("reason"),
                "nodes": state_info.get("nodes"),
                "elapsed": elapsed,
                "details": f"Job {job_id} reached {target_state} in {elapsed}s"
            }
        
        # Check for terminal states
        if current_state in ["COMPLETED", "COMPLETING", "FAILED", "CANCELLED", "TIMEOUT"]:
            elapsed = int(time.time() - start_time)
            return {
                "success": True,
                "final_state": current_state,
                "reason": state_info.get("reason"),
                "nodes": state_info.get("nodes"),
                "elapsed": elapsed,
                "details": f"Job {job_id} reached terminal state {current_state}"
            }
        
        time.sleep(poll_interval)
    
    elapsed = int(time.time() - start_time)
    return {
        "success": False,
        "final_state": final_state.get("state") if final_state else "UNKNOWN",
        "reason": final_state.get("reason") if final_state else None,
        "nodes": final_state.get("nodes") if final_state else None,
        "elapsed": elapsed,
        "details": f"Job {job_id} did not reach {target_state} within {timeout}s"
    }


# =============================================================================
# NODE STATUS FUNCTIONS
# =============================================================================

def get_slurm_node_status(host) -> Dict[str, Any]:
    """
    Get the status of all Slurm compute nodes.

    Args:
        host: testinfra host object or SSHHost

    Returns:
        Dict with 'success', 'nodes', 'available_count', 'down_count', 'total_count', 'error'
    """
    cmd = host.run("sinfo -N -o '%N|%T|%P|%c|%m' --noheader")
    
    if cmd.rc != 0:
        return {
            "success": False,
            "nodes": [],
            "available_count": 0,
            "down_count": 0,
            "total_count": 0,
            "error": cmd.stderr or "Failed to get node status"
        }
    
    nodes = []
    available_count = 0
    down_count = 0
    
    for line in cmd.stdout.split('\n'):
        if not line.strip():
            continue
        parts = line.split('|')
        node = {
            "name": parts[0] if len(parts) > 0 else "unknown",
            "state": parts[1] if len(parts) > 1 else "unknown",
            "partition": parts[2] if len(parts) > 2 else "unknown",
            "cpus": parts[3] if len(parts) > 3 else "0",
            "memory": parts[4] if len(parts) > 4 else "0",
        }
        nodes.append(node)
        
        state_lower = node["state"].lower().rstrip('*')
        if state_lower in AVAILABLE_NODE_STATES:
            available_count += 1
        elif "down" in state_lower or "drain" in state_lower:
            down_count += 1
    
    return {
        "success": True,
        "nodes": nodes,
        "available_count": available_count,
        "down_count": down_count,
        "total_count": len(nodes),
        "error": None
    }


# =============================================================================
# SCHEDULER FUNCTIONS
# =============================================================================

def check_slurmctld_running(host) -> Dict[str, Any]:
    """
    Check if slurmctld daemon is running.

    Args:
        host: testinfra host object or SSHHost

    Returns:
        Dict with 'success', 'status', 'error'
    """
    cmd = host.run("systemctl is-active slurmctld")
    status = cmd.stdout.strip()
    
    return {
        "success": cmd.rc == 0 and status == "active",
        "status": status,
        "error": None if status == "active" else f"slurmctld is {status}"
    }


def get_scheduler_info(host) -> Dict[str, Any]:
    """
    Get Slurm scheduler configuration.

    Args:
        host: testinfra host object or SSHHost

    Returns:
        Dict with 'success', 'config', 'scheduler_type', 'select_type', 'priority_type', 'error'
    """
    cmd = host.run("scontrol show config | grep -E 'SchedulerType|SelectType|PriorityType'")
    
    if cmd.rc == 0:
        config = {}
        for line in cmd.stdout.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
        
        return {
            "success": True,
            "config": config,
            "scheduler_type": config.get("SchedulerType", "N/A"),
            "select_type": config.get("SelectType", "N/A"),
            "priority_type": config.get("PriorityType", "N/A"),
            "error": None
        }
    
    return {
        "success": False,
        "config": {},
        "scheduler_type": None,
        "select_type": None,
        "priority_type": None,
        "error": cmd.stderr or "Failed to get scheduler config"
    }


def get_job_queue_status(host) -> Dict[str, Any]:
    """
    Get current job queue status.

    Args:
        host: testinfra host object or SSHHost

    Returns:
        Dict with 'success', 'jobs', 'pending_count', 'running_count', 'total_count'
    """
    cmd = host.run("squeue -o '%i|%j|%T|%r' --noheader")
    
    if cmd.rc != 0:
        return {
            "success": False,
            "jobs": [],
            "pending_count": 0,
            "running_count": 0,
            "total_count": 0,
            "error": cmd.stderr
        }
    
    jobs = []
    pending_count = 0
    running_count = 0
    
    for line in cmd.stdout.split('\n'):
        if not line.strip():
            continue
        parts = line.split('|')
        job = {
            "job_id": parts[0] if len(parts) > 0 else "unknown",
            "name": parts[1] if len(parts) > 1 else "unknown",
            "state": parts[2] if len(parts) > 2 else "unknown",
            "reason": parts[3] if len(parts) > 3 else "None",
        }
        jobs.append(job)
        
        if job["state"].upper() == "PENDING":
            pending_count += 1
        elif job["state"].upper() == "RUNNING":
            running_count += 1
    
    return {
        "success": True,
        "jobs": jobs,
        "pending_count": pending_count,
        "running_count": running_count,
        "total_count": len(jobs),
        "error": None
    }


# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

def cancel_slurm_jobs(host, job_ids: List[str]) -> Dict[str, Any]:
    """
    Cancel multiple Slurm jobs.

    Args:
        host: testinfra host object or SSHHost
        job_ids: list of job IDs to cancel

    Returns:
        Dict with 'success', 'cancelled', 'failed', 'errors'
    """
    cancelled = []
    failed = []
    errors = []
    
    for job_id in job_ids:
        cmd = host.run(f"scancel {job_id} 2>/dev/null")
        if cmd.rc == 0:
            cancelled.append(job_id)
        else:
            failed.append(job_id)
            errors.append(f"Job {job_id}: {cmd.stderr}")
    
    return {
        "success": len(failed) == 0,
        "cancelled": cancelled,
        "failed": failed,
        "cancelled_count": len(cancelled),
        "errors": errors
    }


# =============================================================================
# FULL VALIDATION
# =============================================================================

def run_all_validations(host, skip_on_failure: bool = True) -> Dict[str, Any]:
    """
    Run all Slurm job queueing validations.
    Continues checking all items even if some fail.

    Args:
        host: testinfra host object or SSHHost
        skip_on_failure: if True, continue all validations even if some fail

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'summary'
    """
    results = []
    passed = 0
    failed = 0
    job_ids = []
    
    # 1. Check slurmctld
    slurmctld_result = check_slurmctld_running(host)
    results.append({
        "name": "slurmctld Running",
        "success": slurmctld_result["success"],
        "details": slurmctld_result["status"],
        "error": slurmctld_result.get("error")
    })
    if slurmctld_result["success"]:
        passed += 1
    else:
        failed += 1
    
    # 2. Check node status
    node_result = get_slurm_node_status(host)
    results.append({
        "name": "Node Status",
        "success": node_result["success"],
        "details": f"Available: {node_result['available_count']}/{node_result['total_count']}",
        "error": node_result.get("error")
    })
    if node_result["success"]:
        passed += 1
    else:
        failed += 1
    
    # 3. Submit test jobs
    submit_result = submit_multiple_jobs(host)
    job_ids = submit_result["job_ids"]
    results.append({
        "name": "Job Submission",
        "success": submit_result["success"],
        "details": f"Submitted: {submit_result['submitted']}/{submit_result['total']}",
        "error": ", ".join(submit_result["errors"]) if submit_result["errors"] else None
    })
    if submit_result["success"]:
        passed += 1
    else:
        failed += 1
    
    # 4. Check job states
    if job_ids:
        states_result = get_multiple_job_states(host, job_ids)
        results.append({
            "name": "Job States",
            "success": states_result["success"],
            "details": f"Pending: {states_result['pending_count']}, Running: {states_result['running_count']}, Completed: {states_result['completed_count']}",
            "error": None
        })
        if states_result["success"]:
            passed += 1
        else:
            failed += 1
        
        # 5. Validate pending reasons
        reasons_result = validate_pending_reasons(host, job_ids)
        results.append({
            "name": "Pending Reasons",
            "success": reasons_result["success"],
            "details": f"Reasons: {', '.join(reasons_result['reasons_found']) if reasons_result['reasons_found'] else 'N/A'}",
            "error": None
        })
        if reasons_result["success"]:
            passed += 1
        else:
            failed += 1
    
    # 6. Check scheduler config
    scheduler_result = get_scheduler_info(host)
    results.append({
        "name": "Scheduler Configuration",
        "success": scheduler_result["success"],
        "details": f"Scheduler: {scheduler_result['scheduler_type']}",
        "error": scheduler_result.get("error")
    })
    if scheduler_result["success"]:
        passed += 1
    else:
        failed += 1
    
    # Cleanup
    if job_ids:
        cancel_slurm_jobs(host, job_ids)
    
    total = passed + failed
    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "total": total,
        "job_ids": job_ids,
        "summary": SLURM_JOB_QUEUEING_MSGS["validation_summary"].format(
            total=total, passed=passed, failed=failed
        )
    }


# =============================================================================
# HOST FACTORY
# =============================================================================

def get_ssh_host(target_ip: str = None, via_host: str = None) -> SSHHost:
    """
    Create an SSHHost instance for Slurm operations.

    Args:
        target_ip: IP of the Slurm control node (default from config)
        via_host: intermediate host for SSH jump (default from config)

    Returns:
        SSHHost instance
    """
    target_ip = target_ip or SLURM_JOB_QUEUEING_VARS["slurm_control_node"]
    via_host = via_host or SLURM_JOB_QUEUEING_VARS["omnia_core_alias"]
    return SSHHost(target_ip, via_host)
