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

from .pam_slurm_adopt_func import (
    submit_job_to_compute_node,
    get_job_state as get_pam_job_state,
    get_job_node,
    cancel_slurm_job,
    wait_for_job_state,
    test_ssh_access_to_node,
    check_pam_slurm_adopt_configured,
    get_available_compute_node,
    get_ssh_host as get_pam_ssh_host,
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
    # pam_slurm_adopt functions
    "submit_job_to_compute_node",
    "get_pam_job_state",
    "get_job_node",
    "cancel_slurm_job",
    "wait_for_job_state",
    "test_ssh_access_to_node",
    "check_pam_slurm_adopt_configured",
    "get_available_compute_node",
    "get_pam_ssh_host",
]
