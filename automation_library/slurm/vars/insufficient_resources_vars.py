"""
Insufficient Resources - Variables and Configuration.

This module contains all variables and configuration for insufficient resources tests.

Usage:
    from automation_library.slurm.vars import (
        INSUFFICIENT_RESOURCES_VARS,
        RESOURCE_PENDING_REASONS,
        RESOURCE_REJECTION_ERRORS,
    )

Author: Dell Technologies
"""

from typing import List

# =============================================================================
# INSUFFICIENT RESOURCES CONFIGURATION
# =============================================================================

INSUFFICIENT_RESOURCES_VARS = {
    "job_wait_timeout": 30,
    "poll_interval": 5,
    "ssh_timeout": 10,
    "slurm_control_node": "172.16.107.202",
    "omnia_core_alias": "omnia_core",
    "excessive_multiplier": 10,
    "default_gpu_request": 100,
}

# Valid pending reasons for resource-related issues
RESOURCE_PENDING_REASONS: List[str] = [
    "Resources",
    "PartitionNodeLimit",
    "PartitionTimeLimit",
    "ReqNodeNotAvail",
    "QOSResourceLimit",
    "QOSMaxCpuPerUserLimit",
    "QOSMaxMemPerUserLimit",
    "QOSMaxGRESPerUser",
    "AssocMaxCpuMinutesPerJob",
    "AssocMaxJobsLimit",
    "InvalidQOS",
    "BadConstraints",
]

# Error messages indicating job rejection due to insufficient resources
RESOURCE_REJECTION_ERRORS: List[str] = [
    "Requested node configuration is not available",
    "Invalid generic resource",
    "Batch job submission failed",
    "error: CPU count per node can not be satisfied",
    "error: Memory specification can not be satisfied",
    "error: Unable to allocate resources",
    "error: Invalid generic resource",
    "error: Requested GRES option unsupported",
    "sbatch: error:",
]

# Slurm job states
JOB_STATES = {
    "pending": "PENDING",
    "running": "RUNNING",
    "completed": "COMPLETED",
    "failed": "FAILED",
    "cancelled": "CANCELLED",
}

# Resource types for testing
RESOURCE_TYPES = {
    "cpu": "cpus-per-task",
    "memory": "mem",
    "gpu": "gres=gpu",
    "nodes": "nodes",
}
