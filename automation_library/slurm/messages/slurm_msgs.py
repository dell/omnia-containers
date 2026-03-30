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
Slurm - Messages and Test Variables.

This module contains all messages, status strings, error instructions,
and test variables for the slurm job submission automation.
"""

from typing import Dict


# =============================================================================
# TEST NAMES (displayed in test output header)
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    # Single job submission
    "single_job_submission": "E2E: Submit single job via login node from omnia_core",
    # Multiple job submission
    "multiple_job_submission": "Submit multiple jobs sequentially from login node",
    # Multi-node submission
    "multi_node_submission": "E2E: Submit job from all login nodes in pxe_mapping",
}


# =============================================================================
# TEST LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # Login node discovery
    "no_login_ips": "No login IPs found in pxe_mapping_file and LOGIN_NODE_IPS not set",
    "login_node_found": "Using login node: {login_ip}",
    "login_node_unreachable": "Skipping unreachable login node: {login_ip}",
    "no_reachable_nodes": "No reachable login nodes found among: {login_ips}",
    # Job script
    "job_script_read": "Read job.sh from {path}",
    "job_script_copied": "Copied job.sh to /home on {login_ip}",
    "job_script_copy_failed": "Failed to copy job.sh to /home on {login_ip}",
    "job_script_not_found": "job.sh not found at {path}",
    # Job submission
    "sbatch_success": "sbatch job.sh submitted successfully",
    "sbatch_failed": "sbatch failed",
    "job_submitted": "Job submitted with job_id={job_id}",
    "job_id_missing": "sbatch did not return a job id",
    "job_id_invalid": "Expected numeric job id, got: {job_id}",
    # squeue
    "squeue_success": "squeue -j {job_id} completed",
    "squeue_failed": "squeue -j {job_id} failed",
    # Insufficient-resource test messages
    "slurm_version_ok": "Slurm version: {version}",
    "sinfo_output": "sinfo output:\n{output}",
    "job_pending": "Job {job_id} is PENDING (reason: {reason})",
    "job_cleanup": "Cleaned up job {job_id}",
    "job_rejected": "sbatch correctly rejected: {error}",
    "job_completed": "Job {job_id} completed successfully",
}


# =============================================================================
# TEST ASSERT MESSAGES (user-friendly with instructions)
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "no_login_ips": (
        "No login IPs found in pxe_mapping_file and LOGIN_NODE_IPS not set; "
        "skipping tests"
    ),
    "no_reachable_nodes": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ NO REACHABLE LOGIN NODES
╠══════════════════════════════════════════════════════════════════════════════╣
║ Tested IPs: {login_ips}
║
║ HOW TO FIX:
║   1. Verify login nodes are powered on and booted
║   2. Check SSH connectivity from omnia_core: podman exec omnia_core ssh root@<IP> echo ok
║   3. Verify pxe_mapping_file has correct ADMIN_IP for login nodes
║   4. Set LOGIN_NODE_IPS env as fallback: export LOGIN_NODE_IPS=<ip1>,<ip2>
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "job_script_not_found": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ JOB SCRIPT NOT FOUND
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected: {path}
║
║ HOW TO FIX:
║   1. Ensure automation_library/slurm/job.sh exists in the project
║   2. Verify the file has correct permissions
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "job_script_copy_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ FAILED TO COPY JOB SCRIPT TO LOGIN NODE
╠══════════════════════════════════════════════════════════════════════════════╣
║ Login node: {login_ip}
║ Error: {error}
║
║ HOW TO FIX:
║   1. Verify SSH from omnia_core to login node: podman exec omnia_core ssh root@{login_ip} echo ok
║   2. Check /home directory permissions on login node
║   3. Verify passwordless SSH is configured
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "sbatch_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ SBATCH JOB SUBMISSION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Login node: {login_ip}
║ Error: {error}
║
║ HOW TO FIX:
║   1. Verify Slurm is running: sinfo --version
║   2. Check slurmctld status: systemctl status slurmctld
║   3. Verify job script syntax: cat /home/job.sh
║   4. Check Slurm logs: journalctl -u slurmctld -n 50
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "job_id_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ SBATCH DID NOT RETURN A JOB ID
╠══════════════════════════════════════════════════════════════════════════════╣
║ sbatch output: {output}
║
║ HOW TO FIX:
║   1. Check Slurm controller: systemctl status slurmctld
║   2. Verify partitions exist: sinfo
║   3. Check Slurm logs: journalctl -u slurmctld -n 50
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "job_id_invalid": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ INVALID JOB ID RETURNED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected: numeric job id
║ Got: {job_id}
║
║ HOW TO FIX:
║   1. Check sbatch --parsable output format
║   2. Verify Slurm accounting is configured
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "squeue_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ SQUEUE CHECK FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Job ID: {job_id}
║ Error: {error}
║
║ HOW TO FIX:
║   1. Verify Slurm is running: sinfo
║   2. Check job status manually: squeue -j {job_id}
║   3. Check Slurm logs: journalctl -u slurmctld -n 50
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "slurm_not_running": "Slurm is not running or unreachable: {error}",
    "sinfo_failed": "sinfo failed on {login_ip}: {error}",
    "sinfo_empty": "sinfo returned no output on {login_ip}",
    "expected_pending": "Job {job_id} expected PENDING but got {state} (reason: {reason})",
    "expected_rejection": "Expected sbatch to reject the job, but it succeeded: {output}",
    "unexpected_rejection_error": "Unexpected sbatch rejection error: {error}",
    "job_not_completed": "Job {job_id} expected COMPLETED but got {state} (reason: {reason})",
    "drain_failed": "Failed to drain node {node}: {error}",
    "node_not_drained": "Node {node} not in drain state; current state: {state}",
    "job_not_pending": "Job {job_id} expected PENDING but got {state} (reason: {reason})",
    "unexpected_pending_reason": "Unexpected pending reason for job {job_id}: {reason}",
    "resume_failed": "Failed to resume node {node}: {error}",
    "job_not_running_after_resume": (
        "Job {job_id} did not transition to RUNNING after resume; "
        "state={state}, reason={reason}"
    ),
    "fifo_violation": (
        "FIFO violation: job {job_a} (start={time_a}) started after "
        "job {job_b} (start={time_b})"
    ),
}


# =============================================================================
# LDAP TEST NAMES
# =============================================================================

LDAP_TEST_NAMES: Dict[str, str] = {
    "ldap_login_to_login_node": "LDAP: SSH login to login node",
    "ldap_login_to_compiler_node": "LDAP: SSH login to login compiler node",
    "ldap_submit_via_login": "LDAP: E2E job submission via login node",
    "ldap_submit_multiple": "LDAP: Multiple job submissions from login/compiler nodes",
    "ldap_submit_via_compiler": "LDAP: E2E job submission via login compiler node",
    "ldap_multi_node_submission": "LDAP: Submit job from all login nodes",
}


# =============================================================================
# LDAP LOG MESSAGES
# =============================================================================

LDAP_LOG_MSGS: Dict[str, str] = {
    "ssh_login_attempt": "Attempting SSH login to {login_ip} as {user}",
    "ssh_login_ok": "SSH login to {login_ip} as {user} succeeded",
    "ssh_whoami_ok": "whoami confirmed: {whoami}",
    "login_ip_found": "Using login node {login_ip}",
    "compiler_ip_found": "Using login compiler node {login_ip}",
    "job_script_created": "Created job.sh on {login_ip} as {user}",
    "job_submitted": "Job {job_id} submitted on {login_ip} as {user}",
    "job_waiting": "Job {job_id} completed",
    "job_completed": "Job {job_id} output verified",
    "cleanup": "Cleaned up job artifacts on {login_ip}",
    "multi_login_done": "Submitted {count} jobs on login node {login_ip}",
    "multi_compiler_done": "Submitted job on compiler node {login_ip}",
}


# =============================================================================
# LDAP ASSERT MESSAGES
# =============================================================================

LDAP_ASSERT_MSGS: Dict[str, str] = {
    "no_login_ips": "No login IPs found; skipping LDAP tests",
    "no_compiler_ips": "No login compiler IPs found; skipping LDAP compiler tests",
    "ldap_user_missing": "LDAP_USER env not set; skipping LDAP tests",
    "ldap_key_missing": "LDAP_SSH_KEY_PATH env not set; skipping LDAP tests",
    "job_script_not_found": "job.sh not found at {path}",
    "ssh_login_failed": "SSH login to {login_ip} as {user} failed: {error}",
    "ssh_whoami_mismatch": "whoami on {login_ip} returned '{whoami}', expected '{user}'",
    "script_create_failed": "Failed to create job.sh on {login_ip} as {user}: {error}",
    "sbatch_failed": "sbatch failed on {login_ip} as {user}: {error}",
    "job_id_missing": "sbatch did not return a job id; output: {output}",
    "squeue_failed": "Job {job_id} did not complete: {error}",
    "output_read_failed": "Failed to read output.txt on {login_ip} as {user}: {error}",
    "output_missing_text": "output.txt on {login_ip} as {user} missing 'Job completed'",
    "e2e_failed": "E2E job submission failed on {login_ip} as {user}: {error}",
}


# =============================================================================
# PAM TEST NAMES
# =============================================================================

PAM_TEST_NAMES: Dict[str, str] = {
    "pam_module_installed": "PAM: pam_slurm_adopt.so installed on compute nodes",
    "pam_config_present": "PAM: pam_slurm_adopt configured in /etc/pam.d/sshd",
    "pam_deny_no_job": "PAM: SSH denied to compute node when no active job",
    "pam_allow_with_job": "PAM: SSH allowed to compute node with running job",
    "pam_session_cleanup": "PAM: User processes cleaned up after job completion",
}


# =============================================================================
# PAM LOG MESSAGES
# =============================================================================

PAM_LOG_MSGS: Dict[str, str] = {
    "pam_module_found": "pam_slurm_adopt.so found at {path}",
    "pam_config_line": "PAM config line: {line}",
    "pam_config_ok": "pam_slurm_adopt configured in {config_path} on {node_ip}",
    "ssh_denied_ok": "SSH correctly denied for {user} on {node_ip} (no active job)",
    "ssh_denied_detail": "rc={rc}, stderr={stderr}",
    "ssh_allowed_ok": "SSH allowed for {user} on {node_ip} (job {job_id} running)",
    "ssh_whoami_ok": "whoami confirmed: {whoami}",
    "sleep_job_submitted": "Sleep job {job_id} submitted as {user}",
    "job_running_on": "Job {job_id} running on node {node}",
    "compute_ip_found": "Compute node IP resolved: {node_ip}",
    "job_cancelled": "Job {job_id} cancelled",
    "waiting_cleanup": "Waiting {seconds}s for process cleanup on {node_ip}",
    "no_processes": "No {user} processes found on {node_ip}",
}


# =============================================================================
# PAM ASSERT MESSAGES
# =============================================================================

# =============================================================================
# QUEUEING TEST NAMES
# =============================================================================

QUEUEING_TEST_NAMES: Dict[str, str] = {
    "single_pending_all_drained": "Queueing: Single job PENDING when all nodes drained",
    "multiple_pending_nodes_down": "Queueing: Multiple jobs PENDING when nodes down",
    "pending_reason_specific_node": "Queueing: PENDING reason when specific node down",
    "transition_running_after_resume": "Queueing: PENDING job transitions to RUNNING after resume",
    "multiple_transition_after_resume": "Queueing: Multiple PENDING jobs transition after resume",
    "scheduled_on_available_only": "Queueing: Job scheduled on available node only",
    "cpu_constrained_pending": "Queueing: CPU-constrained job stays PENDING",
    "memory_constrained_pending": "Queueing: Memory-constrained job stays PENDING",
    "gres_constrained_pending": "Queueing: GRES-constrained job stays PENDING",
    "fifo_scheduling_order": "Queueing: FIFO scheduling order verified",
    "priority_ordering_in_queue": "Queueing: Priority ordering in queue",
}


# =============================================================================
# QUEUEING LOG MESSAGES
# =============================================================================

QUEUEING_LOG_MSGS: Dict[str, str] = {
    "node_drained": "Node(s) drained: {node}",
    "node_verified_drained": "Node {node} verified in drain state: {state}",
    "node_resumed": "Node(s) resumed: {node}",
    "job_submitted": "Job {job_id} submitted",
    "job_submitted_targeting": "Job {job_id} submitted targeting node {node}",
    "job_submitted_cpus": "Job {job_id} submitted requesting {cpus} CPUs",
    "job_submitted_mem": "Job {job_id} submitted requesting {mem}GB memory",
    "job_submitted_gres": "Job {job_id} submitted requesting GRES {gres}",
    "job_pending": "Job {job_id} is PENDING (reason: {reason})",
    "job_pending_before_resume": "Job {job_id} confirmed PENDING before resume (reason: {reason})",
    "job_transitioned": "Job {job_id} transitioned to {state}",
    "job_allocated": "Job allocated to {node} (drained node {drained} excluded)",
    "all_jobs_pending": "All {count} jobs are PENDING",
    "sbatch_rejected": "sbatch correctly rejected: {error}",
    "node_info": "Node {node} info: {detail}",
    "fifo_verified": "FIFO order verified: {details}",
    "squeue_priority": "squeue priority output: {output}",
    "all_jobs_in_queue": "All {count} jobs found in queue: {ids}",
    "cleanup": "Cleanup complete",
}


# =============================================================================
# STABILITY TEST NAMES
# =============================================================================

STABILITY_TEST_NAMES: Dict[str, str] = {
    "mass_flood": "Stability: Mass job submission flood",
    "oversubscribed": "Stability: Oversubscribed CPU requests",
    "rapid_submit_cancel": "Stability: Rapid submit-cancel cycles",
    "drain_resume_under_load": "Stability: Drain/resume under active load",
    "slurmctld_restart_recovery": "Stability: slurmctld restart recovery",
}


# =============================================================================
# STABILITY LOG MESSAGES
# =============================================================================

STABILITY_LOG_MSGS: Dict[str, str] = {
    "ctrl_ip": "Using control node: {ctrl_ip}",
    "pid_before": "slurmctld PID before: {pid}",
    "pid_after": "slurmctld PID after: {pid}",
    "pid_stable": "slurmctld PID stable (no crash/restart)",
    "submitting_flood": "Submitting {count} jobs rapidly",
    "flood_submitted": "{accepted}/{count} jobs accepted by sbatch",
    "scheduler_responsive": "Scheduler is responsive",
    "queue_status": "Queue: total={total}, running={running}, pending={pending}",
    "no_jobs_dropped": "All {count} jobs accounted for in queue",
    "cancel_cleanup": "Cancelled all {name} jobs",
    "queue_drained": "Queue drained for {name}",
    "node_cpus": "Node {node}: {cpus} CPUs",
    "oversub_submitting": "Submitting {count} jobs each requesting {cpus} CPUs (total node={total})",
    "oversub_pending": "{pending} jobs correctly PENDING (insufficient resources)",
    "rapid_cycles": "Running {count} rapid submit-cancel cycles",
    "rapid_done": "{ok}/{count} cycles completed successfully",
    "no_orphans": "No orphaned jobs in queue",
    "no_zombies": "No zombie slurmd processes on {node_ip}",
    "drain_node": "Draining node {node}",
    "node_drained": "Node {node} drained",
    "resume_node": "Resuming node {node}",
    "node_resumed": "Node {node} resumed",
    "restarting_slurmctld": "Restarting slurmctld on {ctrl_ip}",
    "slurmctld_restarted": "slurmctld restarted successfully",
    "jobs_before_restart": "Jobs before restart: running={running}, pending={pending}",
    "jobs_after_restart": "Jobs after restart: running={running}, pending={pending}",
    "jobs_preserved": "Jobs preserved after slurmctld restart",
}


# =============================================================================
# STABILITY ASSERT MESSAGES
# =============================================================================

STABILITY_ASSERT_MSGS: Dict[str, str] = {
    "no_login_ips": "No login IPs found; skipping stability tests",
    "slurmctld_not_responsive": "slurmctld not responsive on {login_ip} ({context}): {error}",
    "pid_changed": "slurmctld PID changed from {pid_before} to {pid_after} ({context})",
    "flood_submit_failed": "Batch job submission failed: {error}",
    "jobs_dropped": "Jobs dropped: expected {expected}, found {found} (dropped {dropped})",
    "rapid_cycle_failed": "Rapid cycles failed: {ok}/{total} completed; {error}",
    "orphaned_jobs": "Orphaned jobs remain in queue: {remaining}",
    "zombie_slurmd": "Zombie slurmd processes on {node_ip}: {zombies}",
    "drain_failed": "Failed to drain node {node}: {error}",
    "resume_failed": "Failed to resume node {node}: {error}",
    "restart_failed": "Failed to restart slurmctld on {ctrl_ip}: {error}",
    "jobs_lost_after_restart": "Jobs lost after restart: {before} before, {after} after",
}


PAM_ASSERT_MSGS: Dict[str, str] = {
    "no_compute_ips": "No compute node IPs found; skipping PAM tests",
    "pam_config_read_failed": "Failed to read PAM config on {node_ip}: {error}",
    "pam_module_not_found": "pam_slurm_adopt.so not found on {node_ip}",
    "pam_config_missing": "pam_slurm_adopt not configured in /etc/pam.d/sshd on {node_ip}",
    "ssh_should_be_denied": "SSH to {node_ip} as {user} should be denied (no active job)",
    "ssh_should_be_allowed": (
        "SSH to {node_ip} as {user} should be allowed "
        "(job {job_id} running): {error}"
    ),
    "whoami_mismatch": "whoami on {node_ip} returned '{whoami}', expected '{user}'",
    "sleep_job_failed": "Failed to submit sleep job as {user}: {error}",
    "job_not_running": "Job {job_id} did not reach RUNNING state: {error}",
    "processes_not_cleaned": (
        "User {user} still has processes on {node_ip} after job completion: {procs}"
    ),
}


# =============================================================================
# NODE DRAIN JOB BEHAVIOR TEST NAMES
# =============================================================================

DRAIN_TEST_NAMES: Dict[str, str] = {
    "submit_multiple_all_drained": "Submit multiple jobs when all nodes drained",
    "submit_targeting_drained_node": "Submit jobs targeting a specific drained node",
    "submit_large_batch": "Submit large batch of jobs (10+)",
    "single_pending_all_drained": "Single job enters PENDING when all nodes drained",
    "multiple_pending": "Multiple jobs all show PENDING",
    "targeted_pending": "Job targeting specific drained node is PENDING",
    "reason_reqnodenotavail": "Reason is ReqNodeNotAvail when all nodes drained",
    "reason_nodedown": "Reason shows NodeDown for specifically downed node",
    "reason_updates_on_state_change": "Reason updates when node state changes",
    "jobs_survive_extended_downtime": "Jobs survive extended node downtime",
    "jobs_not_rejected_during_transition": "Jobs not rejected when submitting during node state transition",
    "resubmit_no_duplicates": "Resubmitting after node drain doesn't cause duplicates/failures",
    "single_pending_to_running": "Single PENDING job transitions to RUNNING after resume",
    "multiple_pending_to_running": "Multiple PENDING jobs all transition after resume",
    "partial_resume_transition": "Job transitions when only one node resumed",
    "no_manual_intervention": "No manual intervention required for transition",
    "long_pending_still_transitions": "Job that was PENDING for 10+ minutes still transitions",
    "fifo_ordering": "FIFO: earlier-submitted job starts first",
}


# =============================================================================
# NODE DRAIN JOB BEHAVIOR LOG MESSAGES
# =============================================================================

DRAIN_LOG_MSGS: Dict[str, str] = {
    "nodes_discovered": "Discovered compute nodes: {nodes}",
    "node_drained": "Node {node} drained successfully",
    "node_resumed": "Node {node} resumed successfully",
    "job_submitted": "Job {job_id} submitted successfully",
    "job_pending": "Job {job_id} is PENDING (reason: {reason})",
    "job_running": "Job {job_id} transitioned to RUNNING",
    "job_completed": "Job {job_id} completed successfully",
    "batch_submitted": "Submitted {count} jobs in batch",
    "fifo_verified": "FIFO order verified: job {job_a} started before job {job_b}",
}


# =============================================================================
# NODE DRAIN JOB BEHAVIOR ASSERT MESSAGES
# =============================================================================

DRAIN_ASSERT_MSGS: Dict[str, str] = {
    "no_compute_nodes": "No compute nodes found in cluster",
    "drain_failed": "Failed to drain node {node}: {error}",
    "resume_failed": "Failed to resume node {node}: {error}",
    "job_not_pending": "Job {job_id} expected PENDING but got {state}",
    "wrong_pending_reason": "Job {job_id} has unexpected pending reason: {reason}",
    "job_not_running": "Job {job_id} did not transition to RUNNING after resume; state={state}",
    "fifo_violation": "FIFO violation: job {job_a} (start={time_a}) started after job {job_b} (start={time_b})",
    "job_rejected": "Job was unexpectedly rejected during submission: {error}",
}


# =============================================================================
# RESOURCE LIMIT TEST NAMES
# =============================================================================

RESOURCE_LIMIT_TEST_NAMES: Dict[str, str] = {
    "exceed_cpu_pending": "Job requesting more CPUs than available goes to PENDING with PartitionConfig",
    "exceed_memory_rejected": "Job requesting more memory than available is rejected",
    "exceed_cpu_and_memory_pending": "Job requesting more CPU and memory goes to PENDING with PartitionConfig",
}


# =============================================================================
# RESOURCE LIMIT LOG MESSAGES
# =============================================================================

RESOURCE_LIMIT_LOG_MSGS: Dict[str, str] = {
    "cluster_resources": "Cluster resources - Node: {node}, CPUs: {cpus}, Memory: {memory_mb}MB",
    "job_script_created": "Created job script requesting {cpus} CPUs and {memory}MB memory",
    "job_submitted": "Job {job_id} submitted successfully",
    "job_pending": "Job {job_id} is PENDING (reason: {reason})",
    "job_rejected": "Job submission rejected as expected: {error}",
    "sinfo_output": "sinfo output: {output}",
}


# =============================================================================
# RESOURCE LIMIT ASSERT MESSAGES
# =============================================================================

RESOURCE_LIMIT_ASSERT_MSGS: Dict[str, str] = {
    "no_login_ips": "No login node IPs found in PXE mapping",
    "no_reachable_nodes": "No reachable login nodes found from: {login_ips}",
    "sinfo_failed": "Failed to get cluster resource info: {error}",
    "job_script_failed": "Failed to create job script: {error}",
    "submit_failed": "Job submission failed unexpectedly: {error}",
    "job_not_pending": "Job {job_id} expected PENDING but got {state}",
    "wrong_pending_reason": (
        "Job {job_id} expected reason containing 'PartitionConfig' but got: {reason}"
    ),
    "job_should_be_rejected": "Job requesting excessive memory should be rejected, but was accepted with job_id={job_id}",
    "cleanup_failed": "Failed to cleanup job {job_id}: {error}",
}
