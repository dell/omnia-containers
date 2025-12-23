"""
Slurm Job Queueing - Variables and Configuration.

This module contains all variables and configuration for Slurm job queueing tests.

Usage:
    from automation_library.vars.slurm_job_queueing_vars import (
        SLURM_JOB_QUEUEING_VARS,
        PENDING_REASONS,
        JOB_STATES,
    )

Author: Dell Technologies
"""

from typing import List

# =============================================================================
# SLURM JOB QUEUEING CONFIGURATION
# =============================================================================

SLURM_JOB_QUEUEING_VARS = {
    "job_submit_count": 3,
    "job_wait_timeout": 60,
    "poll_interval": 5,
    "ssh_timeout": 10,
    "slurm_control_node": "172.16.107.102",
    "omnia_core_alias": "omnia_core",
}

# Valid pending reasons in Slurm
PENDING_REASONS: List[str] = [
    "Resources",
    "NodeDown",
    "PartitionDown",
    "ReqNodeNotAvail",
    "Priority",
    "Dependency",
    "BeginTime",
    "QOSMaxJobsPerUserLimit",
    "ReqNodeNotAvail",
    "None",
]

# Slurm job states
JOB_STATES = {
    "pending": "PENDING",
    "running": "RUNNING",
    "completed": "COMPLETED",
    "completing": "COMPLETING",
    "failed": "FAILED",
    "cancelled": "CANCELLED",
    "timeout": "TIMEOUT",
    "node_fail": "NODE_FAIL",
    "preempted": "PREEMPTED",
    "suspended": "SUSPENDED",
}

# Slurm node states
NODE_STATES = {
    "idle": "idle",
    "allocated": "allocated",
    "mixed": "mixed",
    "down": "down",
    "drain": "drain",
    "unknown": "unknown",
}

# Available node states (can run jobs)
AVAILABLE_NODE_STATES: List[str] = ["idle", "mixed", "allocated"]

# Unavailable node states (cannot run jobs)
UNAVAILABLE_NODE_STATES: List[str] = ["down", "drain", "unknown"]
