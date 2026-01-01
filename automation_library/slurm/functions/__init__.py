"""
Slurm functions module.

Exports functions from both slurm_job_queueing and insufficient_resources modules.
"""

from .slurm_job_queueing_func import (
    submit_slurm_job,
    submit_multiple_jobs,
    get_job_state,
    get_multiple_job_states,
    get_slurm_node_status,
    check_slurmctld_running,
    get_scheduler_info,
    cancel_slurm_jobs,
    validate_pending_reasons,
    get_ssh_host,
)

from .insufficient_resources_func import (
    get_cluster_resources,
    submit_job_with_excessive_cpus,
    submit_job_with_excessive_memory,
    submit_job_with_gpus,
    validate_insufficient_resource_response,
    get_ssh_host as get_insufficient_resources_ssh_host,
)

__all__ = [
    # slurm_job_queueing functions
    "submit_slurm_job",
    "submit_multiple_jobs",
    "get_job_state",
    "get_multiple_job_states",
    "get_slurm_node_status",
    "check_slurmctld_running",
    "get_scheduler_info",
    "cancel_slurm_jobs",
    "validate_pending_reasons",
    "get_ssh_host",
    # insufficient_resources functions
    "get_cluster_resources",
    "submit_job_with_excessive_cpus",
    "submit_job_with_excessive_memory",
    "submit_job_with_gpus",
    "validate_insufficient_resource_response",
    "get_insufficient_resources_ssh_host",
]
