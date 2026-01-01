"""
PAM Slurm Adopt - Core Functions.

This module contains all functions for testing PAM Slurm Adopt functionality:
- SSH access control during active Slurm jobs
- User logout verification after job completion
- SSH access denial after job ends

Usage:
    from automation_library.slurm.functions import (
        submit_job_to_compute_node,
        test_ssh_access_to_node,
        wait_for_job_state,
        check_pam_slurm_adopt_configured,
    )

Author: Dell Technologies
"""

import re
import time
import subprocess
from typing import Dict, Any, List, Optional

from ..vars.pam_slurm_adopt_vars import (
    PAM_SLURM_ADOPT_VARS,
    SSH_ACCESS_STATES,
    JOB_END_STATES,
    JOB_ACTIVE_STATES,
    PAM_SLURM_MODULE,
)


# =============================================================================
# SSH HOST CLASS (for direct SSH execution)
# =============================================================================

class SSHHost:
    """SSH host class that mimics testinfra host interface."""
    
    def __init__(self, target_ip: str, via_host: str = None):
        self.target_ip = target_ip
        self.via_host = via_host
        self.ssh_timeout = PAM_SLURM_ADOPT_VARS["ssh_timeout"]
    
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


def get_ssh_host(target_ip: str = None, via_host: str = None) -> SSHHost:
    """
    Create an SSHHost instance for Slurm operations.

    Args:
        target_ip: IP of the Slurm control node (default from config)
        via_host: intermediate host for SSH jump (default from config)

    Returns:
        SSHHost instance
    """
    target_ip = target_ip or PAM_SLURM_ADOPT_VARS["slurm_control_node"]
    via_host = via_host or PAM_SLURM_ADOPT_VARS["omnia_core_alias"]
    return SSHHost(target_ip, via_host)


# =============================================================================
# SLURMCTLD CHECK FUNCTIONS
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
        "error": cmd.stderr if cmd.rc != 0 else None
    }


# =============================================================================
# PAM CONFIGURATION CHECK FUNCTIONS
# =============================================================================

def check_pam_slurm_adopt_configured(host) -> Dict[str, Any]:
    """
    Check if PAM Slurm Adopt is configured on the system.

    Args:
        host: testinfra host object or SSHHost

    Returns:
        Dict with 'success', 'details', 'error'
    """
    # Check for pam_slurm_adopt in PAM configuration
    cmd = host.run(f"grep -r '{PAM_SLURM_MODULE}' /etc/pam.d/ 2>/dev/null")
    
    if cmd.rc == 0 and PAM_SLURM_MODULE in cmd.stdout:
        return {
            "success": True,
            "details": cmd.stdout,
            "error": None
        }
    
    # Also check if the module exists
    module_check = host.run(f"find /lib*/security/ -name '{PAM_SLURM_MODULE}' 2>/dev/null")
    
    if module_check.rc == 0 and module_check.stdout:
        return {
            "success": True,
            "details": f"Module found: {module_check.stdout}",
            "error": None
        }
    
    return {
        "success": False,
        "details": None,
        "error": "PAM Slurm Adopt module not found in configuration"
    }


# =============================================================================
# COMPUTE NODE FUNCTIONS
# =============================================================================

def get_available_compute_node(host) -> Dict[str, Any]:
    """
    Get an available compute node for testing.

    Args:
        host: testinfra host object or SSHHost

    Returns:
        Dict with 'success', 'node', 'error'
    """
    # Get nodes that are idle or mixed (can accept jobs)
    cmd = host.run("sinfo -N -o '%N|%T' --noheader | grep -E 'idle|mixed|allocated' | head -1")
    
    if cmd.rc == 0 and cmd.stdout:
        parts = cmd.stdout.split('|')
        if parts:
            node_name = parts[0].strip()
            return {
                "success": True,
                "node": node_name,
                "error": None
            }
    
    return {
        "success": False,
        "node": None,
        "error": "No available compute nodes found"
    }


# =============================================================================
# JOB SUBMISSION FUNCTIONS
# =============================================================================

def submit_job_to_compute_node(host, node: str, duration: int = 120, user: str = None) -> Dict[str, Any]:
    """
    Submit a job to a specific compute node.

    Args:
        host: testinfra host object or SSHHost
        node: target compute node name
        duration: job duration in seconds
        user: user to run the job as (default from config)

    Returns:
        Dict with 'success', 'job_id', 'user', 'error'
    """
    user = user or PAM_SLURM_ADOPT_VARS["test_user"]
    
    # Submit job with specific node requirement
    cmd = host.run(
        f"sbatch --job-name=pam_test --nodelist={node} --time=00:{duration//60 + 1}:00 "
        f"--nodes=1 --ntasks=1 --wrap='sleep {duration}; hostname'"
    )
    
    if cmd.rc == 0:
        match = re.search(r'Submitted batch job (\d+)', cmd.stdout)
        if match:
            return {
                "success": True,
                "job_id": match.group(1),
                "user": user,
                "node": node,
                "error": None
            }
        return {
            "success": False,
            "job_id": None,
            "user": user,
            "error": f"Could not parse job ID: {cmd.stdout}"
        }
    
    return {
        "success": False,
        "job_id": None,
        "user": user,
        "error": cmd.stderr or cmd.stdout or "Unknown error"
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
        Dict with 'success', 'state', 'reason', 'node', 'error'
    """
    cmd = host.run(f"squeue -j {job_id} -o '%T|%r|%N' --noheader 2>/dev/null")
    
    if cmd.rc == 0 and cmd.stdout:
        parts = cmd.stdout.split('|')
        return {
            "success": True,
            "state": parts[0].strip() if len(parts) > 0 else "UNKNOWN",
            "reason": parts[1].strip() if len(parts) > 1 else "None",
            "node": parts[2].strip() if len(parts) > 2 else None,
            "error": None
        }
    
    # Job might have completed - check sacct
    sacct_cmd = host.run(f"sacct -j {job_id} -o State --noheader -n 2>/dev/null | head -1")
    if sacct_cmd.rc == 0 and sacct_cmd.stdout:
        return {
            "success": True,
            "state": sacct_cmd.stdout.strip(),
            "reason": "Job completed",
            "node": None,
            "error": None
        }
    
    return {
        "success": False,
        "state": "UNKNOWN",
        "reason": None,
        "node": None,
        "error": "Could not get job state"
    }


def get_job_node(host, job_id: str) -> Dict[str, Any]:
    """
    Get the node where a job is running.

    Args:
        host: testinfra host object or SSHHost
        job_id: Slurm job ID

    Returns:
        Dict with 'success', 'node', 'error'
    """
    cmd = host.run(f"squeue -j {job_id} -o '%N' --noheader 2>/dev/null")
    
    if cmd.rc == 0 and cmd.stdout:
        return {
            "success": True,
            "node": cmd.stdout.strip(),
            "error": None
        }
    
    return {
        "success": False,
        "node": None,
        "error": "Could not get job node"
    }


def wait_for_job_state(host, job_id: str, target_state: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Wait for a job to reach a specific state.

    Args:
        host: testinfra host object or SSHHost
        job_id: Slurm job ID
        target_state: target state to wait for (e.g., "RUNNING")
        timeout: maximum time to wait in seconds

    Returns:
        Dict with 'success', 'current_state', 'error'
    """
    poll_interval = PAM_SLURM_ADOPT_VARS["poll_interval"]
    elapsed = 0
    
    while elapsed < timeout:
        state_result = get_job_state(host, job_id)
        current_state = state_result.get("state", "UNKNOWN").upper()
        
        if current_state == target_state.upper():
            return {
                "success": True,
                "current_state": current_state,
                "error": None
            }
        
        # Check if job has ended unexpectedly
        if current_state in JOB_END_STATES:
            return {
                "success": False,
                "current_state": current_state,
                "error": f"Job ended with state {current_state} before reaching {target_state}"
            }
        
        time.sleep(poll_interval)
        elapsed += poll_interval
    
    return {
        "success": False,
        "current_state": current_state,
        "error": f"Timeout waiting for job to reach {target_state}"
    }


# =============================================================================
# JOB CANCELLATION FUNCTIONS
# =============================================================================

def cancel_slurm_job(host, job_id: str) -> Dict[str, Any]:
    """
    Cancel a Slurm job.

    Args:
        host: testinfra host object or SSHHost
        job_id: Slurm job ID

    Returns:
        Dict with 'success', 'error'
    """
    cmd = host.run(f"scancel {job_id} 2>/dev/null")
    
    return {
        "success": cmd.rc == 0,
        "error": cmd.stderr if cmd.rc != 0 else None
    }


# =============================================================================
# SSH ACCESS TEST FUNCTIONS
# =============================================================================

def test_ssh_access_to_node(host, node: str, user: str = None) -> Dict[str, Any]:
    """
    Test SSH access to a compute node for a specific user.

    Args:
        host: testinfra host object or SSHHost (control node)
        node: target compute node name/IP
        user: user to test SSH access for

    Returns:
        Dict with 'access_allowed', 'output', 'error'
    """
    user = user or PAM_SLURM_ADOPT_VARS["test_user"]
    ssh_timeout = PAM_SLURM_ADOPT_VARS["ssh_timeout"]
    
    # Try to SSH from control node to compute node
    cmd = host.run(
        f"ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout={ssh_timeout} "
        f"{user}@{node} 'echo SSH_SUCCESS' 2>&1"
    )
    
    if cmd.rc == 0 and "SSH_SUCCESS" in cmd.stdout:
        return {
            "access_allowed": True,
            "output": cmd.stdout,
            "error": None
        }
    
    # Check for PAM rejection messages
    pam_rejection_indicators = [
        "Access denied",
        "Permission denied",
        "pam_slurm_adopt",
        "Connection closed",
        "not allowed",
    ]
    
    output = cmd.stdout + cmd.stderr
    is_pam_rejection = any(indicator.lower() in output.lower() for indicator in pam_rejection_indicators)
    
    return {
        "access_allowed": False,
        "output": output,
        "error": "SSH access denied" if is_pam_rejection else f"SSH failed: {output}"
    }
