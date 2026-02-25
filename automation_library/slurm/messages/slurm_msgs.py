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
