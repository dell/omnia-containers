"""
PAM Slurm Adopt - Variables and Configuration.

This module contains all variables and configuration for PAM Slurm Adopt tests.

Usage:
    from automation_library.slurm.vars import (
        PAM_SLURM_ADOPT_VARS,
        SSH_ACCESS_STATES,
    )

Author: Dell Technologies
"""

from typing import List

# =============================================================================
# PAM SLURM ADOPT CONFIGURATION
# =============================================================================

PAM_SLURM_ADOPT_VARS = {
    "job_duration": 120,  # Duration of test job in seconds
    "short_job_duration": 30,  # Duration of short test job
    "job_start_timeout": 60,  # Timeout waiting for job to start
    "job_end_timeout": 30,  # Timeout waiting for job to end
    "logout_wait_time": 5,  # Time to wait after job ends for logout
    "ssh_timeout": 10,  # SSH connection timeout
    "poll_interval": 2,  # Polling interval for job state
    "slurm_control_node": "172.16.107.202",
    "slurm_compute_node": "172.16.107.205",  # Compute node IP for SSH tests
    "omnia_core_alias": "omnia_core",
    "test_user": "root",  # User to test SSH access with
}

# SSH access states
SSH_ACCESS_STATES = {
    "allowed": "ALLOWED",
    "denied": "DENIED",
    "error": "ERROR",
}

# Valid job states indicating job has ended
JOB_END_STATES: List[str] = [
    "CANCELLED",
    "COMPLETED",
    "FAILED",
    "TIMEOUT",
    "NODE_FAIL",
    "PREEMPTED",
]

# Valid job states indicating job is active
JOB_ACTIVE_STATES: List[str] = [
    "RUNNING",
    "COMPLETING",
]

# PAM configuration files to check
PAM_CONFIG_FILES: List[str] = [
    "/etc/pam.d/sshd",
    "/etc/pam.d/system-auth",
]

# Expected PAM module for Slurm
PAM_SLURM_MODULE = "pam_slurm_adopt.so"
