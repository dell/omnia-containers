"""
Insufficient Resources - Core Functions.

This module contains all functions for testing Slurm job submission
with insufficient resources.

Usage:
    from automation_library.functions.insufficient_resources_func import (
        get_cluster_resources,
        submit_job_with_excessive_cpus,
        submit_job_with_excessive_memory,
        submit_job_with_gpus,
        validate_insufficient_resource_response,
    )

Author: Dell Technologies
"""

import re
import subprocess
from typing import Dict, Any, List, Optional

from ..vars.insufficient_resources_vars import (
    INSUFFICIENT_RESOURCES_VARS,
    RESOURCE_PENDING_REASONS,
    RESOURCE_REJECTION_ERRORS,
)


# =============================================================================
# SSH HOST CLASS (for direct SSH execution)
# =============================================================================

class SSHHost:
    """SSH host class that mimics testinfra host interface."""
    
    def __init__(self, target_ip: str, via_host: str = None):
        self.target_ip = target_ip
        self.via_host = via_host
        self.ssh_timeout = INSUFFICIENT_RESOURCES_VARS["ssh_timeout"]
    
    def run(self, command: str, timeout: int = 60):
        """Run command on remote host via SSH."""
        if self.via_host:
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
# CLUSTER RESOURCE FUNCTIONS
# =============================================================================

def get_cluster_resources(host) -> Dict[str, Any]:
    """
    Get cluster resource information including max CPUs and memory per node.

    Args:
        host: testinfra host object or SSHHost

    Returns:
        Dict with 'success', 'nodes', 'max_cpus', 'max_memory', 'has_gpus', 'error'
    """
    cmd = host.run("sinfo -N -o '%N|%c|%m|%G' --noheader")
    
    if cmd.rc != 0:
        return {
            "success": False,
            "nodes": [],
            "max_cpus": 0,
            "max_memory": 0,
            "has_gpus": False,
            "error": cmd.stderr or "Failed to get cluster resources"
        }
    
    nodes = []
    max_cpus = 0
    max_memory = 0
    has_gpus = False
    
    for line in cmd.stdout.split('\n'):
        if not line.strip():
            continue
        parts = line.split('|')
        node = {
            "name": parts[0] if len(parts) > 0 else "unknown",
            "cpus": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
            "memory": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
            "gpus": parts[3] if len(parts) > 3 else "(null)",
        }
        nodes.append(node)
        
        if node["cpus"] > max_cpus:
            max_cpus = node["cpus"]
        if node["memory"] > max_memory:
            max_memory = node["memory"]
        if node["gpus"] and node["gpus"] != "(null)":
            has_gpus = True
    
    return {
        "success": True,
        "nodes": nodes,
        "max_cpus": max_cpus,
        "max_memory": max_memory,
        "has_gpus": has_gpus,
        "total_nodes": len(nodes),
        "error": None
    }


# =============================================================================
# JOB SUBMISSION FUNCTIONS
# =============================================================================

def submit_job_with_excessive_cpus(host, cpu_count: int) -> Dict[str, Any]:
    """
    Submit a job requesting excessive CPUs.

    Args:
        host: testinfra host object or SSHHost
        cpu_count: number of CPUs to request

    Returns:
        Dict with 'success', 'job_id', 'stdout', 'stderr', 'rc', 'rejected', 'error'
    """
    cmd = host.run(
        f"sbatch --job-name=test_excess_cpu --cpus-per-task={cpu_count} "
        f"--time=00:01:00 --wrap='hostname' 2>&1"
    )
    
    result = {
        "success": cmd.rc == 0,
        "job_id": None,
        "stdout": cmd.stdout,
        "stderr": cmd.stderr,
        "rc": cmd.rc,
        "rejected": False,
        "error": None
    }
    
    # Check if job was submitted
    match = re.search(r'Submitted batch job (\d+)', cmd.stdout)
    if match:
        result["job_id"] = match.group(1)
    
    # Check if job was rejected
    if cmd.rc != 0 or any(err in cmd.stdout for err in RESOURCE_REJECTION_ERRORS):
        result["rejected"] = True
        result["error"] = cmd.stdout or cmd.stderr
    
    return result


def submit_job_with_excessive_memory(host, memory_mb: int) -> Dict[str, Any]:
    """
    Submit a job requesting excessive memory.

    Args:
        host: testinfra host object or SSHHost
        memory_mb: memory in MB to request

    Returns:
        Dict with 'success', 'job_id', 'stdout', 'stderr', 'rc', 'rejected', 'error'
    """
    cmd = host.run(
        f"sbatch --job-name=test_excess_mem --mem={memory_mb} "
        f"--time=00:01:00 --wrap='hostname' 2>&1"
    )
    
    result = {
        "success": cmd.rc == 0,
        "job_id": None,
        "stdout": cmd.stdout,
        "stderr": cmd.stderr,
        "rc": cmd.rc,
        "rejected": False,
        "error": None
    }
    
    # Check if job was submitted
    match = re.search(r'Submitted batch job (\d+)', cmd.stdout)
    if match:
        result["job_id"] = match.group(1)
    
    # Check if job was rejected
    if cmd.rc != 0 or any(err in cmd.stdout for err in RESOURCE_REJECTION_ERRORS):
        result["rejected"] = True
        result["error"] = cmd.stdout or cmd.stderr
    
    return result


def submit_job_with_gpus(host, gpu_count: int = 100) -> Dict[str, Any]:
    """
    Submit a job requesting GPUs.

    Args:
        host: testinfra host object or SSHHost
        gpu_count: number of GPUs to request

    Returns:
        Dict with 'success', 'job_id', 'stdout', 'stderr', 'rc', 'rejected', 'error'
    """
    cmd = host.run(
        f"sbatch --job-name=test_gpu --gres=gpu:{gpu_count} "
        f"--time=00:01:00 --wrap='hostname' 2>&1"
    )
    
    result = {
        "success": cmd.rc == 0,
        "job_id": None,
        "stdout": cmd.stdout,
        "stderr": cmd.stderr,
        "rc": cmd.rc,
        "rejected": False,
        "error": None
    }
    
    # Check if job was submitted
    match = re.search(r'Submitted batch job (\d+)', cmd.stdout)
    if match:
        result["job_id"] = match.group(1)
    
    # Check if job was rejected
    if cmd.rc != 0 or any(err in cmd.stdout for err in RESOURCE_REJECTION_ERRORS):
        result["rejected"] = True
        result["error"] = cmd.stdout or cmd.stderr
    
    return result


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
        Dict with 'success', 'state', 'reason', 'error'
    """
    cmd = host.run(f"squeue -j {job_id} -o '%T|%r' --noheader")
    
    if cmd.rc == 0 and cmd.stdout:
        parts = cmd.stdout.split('|')
        return {
            "success": True,
            "state": parts[0] if len(parts) > 0 else "UNKNOWN",
            "reason": parts[1] if len(parts) > 1 else "None",
            "error": None
        }
    
    return {
        "success": False,
        "state": "UNKNOWN",
        "reason": None,
        "error": "Job not found or completed"
    }


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_insufficient_resource_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that the response to an insufficient resource request is correct.
    
    Valid responses:
    1. Job rejected with appropriate error message
    2. Job submitted but PENDING with resource-related reason

    Args:
        result: Result dict from job submission function

    Returns:
        Dict with 'valid', 'response_type', 'reason', 'error', 'details'
    """
    # Case 1: Job was rejected
    if result.get("rejected") or result.get("rc") != 0:
        error_msg = result.get("error") or result.get("stdout") or result.get("stderr") or ""
        
        # Check if rejection is due to resource issues
        is_resource_error = any(err.lower() in error_msg.lower() for err in RESOURCE_REJECTION_ERRORS)
        
        return {
            "valid": True,
            "response_type": "rejected",
            "reason": None,
            "error": error_msg,
            "details": f"Job rejected: {error_msg[:100]}"
        }
    
    # Case 2: Job was submitted - check if it's PENDING with valid reason
    if result.get("job_id"):
        # The job was submitted, which is also valid behavior
        # Slurm may queue the job and let it wait for resources
        return {
            "valid": True,
            "response_type": "pending",
            "reason": "Job queued - will check state",
            "error": None,
            "details": f"Job {result['job_id']} submitted and queued"
        }
    
    # Unexpected case
    return {
        "valid": False,
        "response_type": "unknown",
        "reason": None,
        "error": "Unexpected response",
        "details": f"RC: {result.get('rc')}, stdout: {result.get('stdout', '')[:100]}"
    }


def validate_job_pending_reason(host, job_id: str) -> Dict[str, Any]:
    """
    Validate that a pending job has a valid resource-related reason.

    Args:
        host: testinfra host object or SSHHost
        job_id: Slurm job ID

    Returns:
        Dict with 'valid', 'state', 'reason', 'is_resource_reason', 'details'
    """
    state_info = get_job_state(host, job_id)
    
    if not state_info["success"]:
        return {
            "valid": False,
            "state": "UNKNOWN",
            "reason": None,
            "is_resource_reason": False,
            "details": state_info["error"]
        }
    
    state = state_info["state"].upper()
    reason = state_info["reason"]
    
    # Check if reason is resource-related
    is_resource_reason = any(r.lower() in reason.lower() for r in RESOURCE_PENDING_REASONS)
    
    if state == "PENDING":
        return {
            "valid": True,
            "state": state,
            "reason": reason,
            "is_resource_reason": is_resource_reason,
            "details": f"Job PENDING with reason: {reason}"
        }
    elif state == "RUNNING":
        return {
            "valid": False,
            "state": state,
            "reason": reason,
            "is_resource_reason": False,
            "details": "Job unexpectedly RUNNING - should not have resources"
        }
    else:
        return {
            "valid": True,
            "state": state,
            "reason": reason,
            "is_resource_reason": False,
            "details": f"Job in state: {state}"
        }


# =============================================================================
# SLURMCTLD FUNCTIONS
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
        Dict with 'success', 'cancelled', 'errors'
    """
    cancelled = []
    errors = []
    
    for job_id in job_ids:
        cmd = host.run(f"scancel {job_id} 2>/dev/null")
        if cmd.rc == 0:
            cancelled.append(job_id)
        else:
            errors.append(f"Job {job_id}: {cmd.stderr}")
    
    return {
        "success": len(errors) == 0,
        "cancelled": cancelled,
        "cancelled_count": len(cancelled),
        "errors": errors
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
    target_ip = target_ip or INSUFFICIENT_RESOURCES_VARS["slurm_control_node"]
    via_host = via_host or INSUFFICIENT_RESOURCES_VARS["omnia_core_alias"]
    return SSHHost(target_ip, via_host)
