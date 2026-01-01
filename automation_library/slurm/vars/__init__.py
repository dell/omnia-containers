"""
Slurm vars module.

Exports variables from both slurm_job_queueing and insufficient_resources modules.
"""

from .slurm_job_queueing_vars import (
    SLURM_JOB_QUEUEING_VARS,
    PENDING_REASONS,
    JOB_STATES,
    NODE_STATES,
    AVAILABLE_NODE_STATES,
    UNAVAILABLE_NODE_STATES,
)

from .insufficient_resources_vars import (
    INSUFFICIENT_RESOURCES_VARS,
    RESOURCE_PENDING_REASONS,
    RESOURCE_REJECTION_ERRORS,
    JOB_STATES as INSUFFICIENT_RESOURCES_JOB_STATES,
    RESOURCE_TYPES,
)

from .pam_slurm_adopt_vars import (
    PAM_SLURM_ADOPT_VARS,
    SSH_ACCESS_STATES,
    JOB_END_STATES,
    JOB_ACTIVE_STATES,
)

__all__ = [
    # slurm_job_queueing vars
    "SLURM_JOB_QUEUEING_VARS",
    "PENDING_REASONS",
    "JOB_STATES",
    "NODE_STATES",
    "AVAILABLE_NODE_STATES",
    "UNAVAILABLE_NODE_STATES",
    # insufficient_resources vars
    "INSUFFICIENT_RESOURCES_VARS",
    "RESOURCE_PENDING_REASONS",
    "RESOURCE_REJECTION_ERRORS",
    "INSUFFICIENT_RESOURCES_JOB_STATES",
    "RESOURCE_TYPES",
    # pam_slurm_adopt vars
    "PAM_SLURM_ADOPT_VARS",
    "SSH_ACCESS_STATES",
    "JOB_END_STATES",
    "JOB_ACTIVE_STATES",
]
