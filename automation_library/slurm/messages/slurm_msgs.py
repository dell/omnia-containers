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

"""Slurm message constants used by the OMNIA automation library."""

TEST_PASSED = "PASSED"
TEST_FAILED = "FAILED"
TEST_SKIPPED = "SKIPPED"

# =============================================================================
# Service Check Messages
# =============================================================================
ERROR_NO_NODES_FOUND = "No nodes found in PXE mapping file for functional group: {group}"
ERROR_NO_SLURM_CONTROL_NODES = "No slurm control nodes found in PXE mapping file"
ERROR_NO_SLURM_NODES = "No slurm nodes found in PXE mapping file"
ERROR_SERVICE_INACTIVE = "Service {service} is not active on node {node} ({ip})"
ERROR_NODE_UNREACHABLE = "Node {node} ({ip}) is unreachable"

STATUS_CHECKING_SERVICE = "Checking {service} on {node} ({ip})"
STATUS_SERVICE_ACTIVE = "{service} is active on {node} ({ip})"
STATUS_SERVICE_INACTIVE = "{service} is not active on {node} ({ip})"

# =============================================================================
# Slurmctld / Slurmd Messages
# =============================================================================
SLURMCTLD_CHECK_PASSED = "slurmctld service is active on all slurm control nodes"
SLURMCTLD_CHECK_FAILED = "slurmctld service is NOT active on one or more slurm control nodes"

SLURMD_CHECK_PASSED = "slurmd service is active on all slurm nodes"
SLURMD_CHECK_FAILED = "slurmd service is NOT active on one or more slurm nodes"

SLURMD_LOGIN_CHECK_PASSED = "slurmd service is active on all login and login compiler nodes"
SLURMD_LOGIN_CHECK_FAILED = "slurmd service is NOT active on one or more login/login compiler nodes"
ERROR_NO_LOGIN_NODES = "No login or login compiler nodes found in PXE mapping file"

# =============================================================================
# Munge Messages
# =============================================================================
MUNGE_CHECK_PASSED = "munge service is active on all required nodes"
MUNGE_CHECK_FAILED = "munge service is NOT active on one or more nodes"

# =============================================================================
# Sinfo Messages
# =============================================================================
SINFO_CHECK_PASSED = "All slurm nodes are in idle state"
SINFO_CHECK_FAILED = "One or more slurm nodes are NOT in idle state"
SINFO_NO_OUTPUT = "sinfo command returned no output on control node {node}"
SINFO_COMMAND_FAILED = "sinfo command failed on control node {node}: {error}"
LOGIN_NODES_IDLE_PASSED = "All login and login compiler nodes are in idle state"
LOGIN_NODES_IDLE_FAILED = "One or more login/login compiler nodes are NOT in idle state: {details}"
LOGIN_NODES_IDLE_NO_NODES = "No login or login compiler nodes found - skipping idle check"

# =============================================================================
# Srun Messages
# =============================================================================
SRUN_CHECK_PASSED = "srun job completed successfully on {num_nodes} node(s)"
SRUN_CHECK_FAILED = "srun job failed: {error}"
SRUN_NO_CONTROL_NODE = "Cannot run srun: no slurm control node found"

# =============================================================================
# Sbatch Messages
# =============================================================================
SBATCH_CHECK_PASSED = "sbatch job completed successfully (JobID: {job_id})"
SBATCH_CHECK_FAILED = "sbatch job failed: {error}"
SBATCH_SUBMIT_FAILED = "Failed to submit sbatch job: {error}"
SBATCH_TIMEOUT = "sbatch job {job_id} did not complete within {timeout}s"
SBATCH_NO_CONTROL_NODE = "Cannot run sbatch: no slurm control node found"
SACCT_JOB_STATUS = "Job {job_id} status: {state}"

# =============================================================================
# LDAP User Login Messages
# =============================================================================
LDAP_LOGIN_PASSED = "ldapuser login succeeded on all login/login_compiler/control nodes"
LDAP_LOGIN_FAILED = "ldapuser login failed on one or more nodes"
LDAP_LOGIN_BLOCKED_PASSED = "ldapuser login correctly blocked on slurm nodes with no running jobs"
LDAP_LOGIN_BLOCKED_FAILED = "ldapuser login was NOT blocked on one or more idle slurm nodes"
LDAP_CREDS_MISSING = "ldap_credentials in 'username:password' format required in omnia_test_config.yml"
LDAP_SETUP_FAILED = "LDAP user setup failed: {error}"

# =============================================================================
# PAM Support Messages
# =============================================================================
PAM_TEST_PASSED = "PAM support verified: ldapuser can login during job, blocked after completion"
PAM_TEST_FAILED = "PAM support verification failed: {error}"
PAM_JOB_SUBMIT_FAILED = "Failed to submit sleep job as ldapuser: {error}"
PAM_JOB_NOT_RUNNING = "Sleep job did not reach RUNNING state within timeout"
PAM_LOGIN_DURING_JOB_FAILED = "ldapuser could NOT login to allocated node {node} during running job"
PAM_LOGIN_AFTER_JOB_OK = "ldapuser can still login to node {node} after job completed (expected blocked)"
PAM_NO_ALLOCATED_NODES = "Could not determine allocated nodes for job {job_id}"

# =============================================================================
# OpenMPI Messages
# =============================================================================
MPI_JOB_PASSED = "OpenMPI job completed successfully (JobID: {job_id})"
MPI_JOB_FAILED = "OpenMPI job failed: {error}"
MPI_SUBMIT_FAILED = "Failed to submit MPI job as ldapuser: {error}"
MPI_NO_LOGIN_COMPILER = "No login compiler nodes found for MPI job submission"
MPI_CMD_NOT_FOUND = "mpirun/mpicc not available on login compiler node {node} - cannot run MPI job"
MPI_OUTPUT_VERIFICATION_FAILED = "MPI job output verification failed: {error}"

# =============================================================================
# Job Queuing Messages
# =============================================================================
QUEUE_TEST_PASSED = "Job queuing verified: first job RUNNING, second job PENDING on same node"
QUEUE_TEST_FAILED = "Job queuing verification failed: {error}"
QUEUE_FIRST_NOT_RUNNING = "First sleep job did not reach RUNNING state"
QUEUE_SECOND_NOT_PENDING = "Second job is not in PENDING state (actual: {state})"

# =============================================================================
# Root Job Submission from Login Nodes
# =============================================================================
ROOT_LOGIN_SINGLE_PASSED = "Root single sbatch job from login node {node} completed successfully (JobID: {job_id})"
ROOT_LOGIN_SINGLE_FAILED = "Root single sbatch job from login node {node} failed: {error}"
ROOT_LOGIN_MULTI_PASSED = "Root {count} sbatch jobs from login node {node} all completed successfully"
ROOT_LOGIN_MULTI_FAILED = "Root multi-job submission from login node {node} failed: {error}"
ROOT_LOGIN_ALLNODES_PASSED = "Root sbatch job from all {count} login node(s) completed successfully"
ROOT_LOGIN_ALLNODES_FAILED = "Root sbatch job from login nodes failed: {error}"
ROOT_NO_LOGIN_NODES = "No login or login compiler nodes found for root job submission"

# =============================================================================
# LDAP Job Submission from Login Nodes
# =============================================================================
LDAP_JOB_SINGLE_PASSED = "LDAP user single sbatch job from {node} completed successfully (JobID: {job_id})"
LDAP_JOB_SINGLE_FAILED = "LDAP user single sbatch job from {node} failed: {error}"
LDAP_JOB_MULTI_PASSED = "LDAP user {count} sbatch jobs from {node} all completed successfully"
LDAP_JOB_MULTI_FAILED = "LDAP user multi-job from {node} failed: {error}"
LDAP_JOB_ALLNODES_PASSED = "LDAP user sbatch job from all {count} login node(s) completed successfully"
LDAP_JOB_ALLNODES_FAILED = "LDAP user sbatch job from login nodes failed: {error}"

# =============================================================================
# Drain / Undrain Job Queuing Messages
# =============================================================================
DRAIN_QUEUE_PASSED = "Drain queuing verified: jobs PENDING while drained, transitioned to RUNNING/COMPLETED after undrain"
DRAIN_QUEUE_FAILED = "Drain queuing verification failed: {error}"
DRAIN_FAILED = "Failed to drain slurm nodes: {error}"
UNDRAIN_FAILED = "Failed to undrain slurm nodes: {error}"
DRAIN_JOB_NOT_PENDING = "Job {job_id} not in PENDING state after draining nodes (actual: {state})"

# =============================================================================
# Insufficient Resources Messages
# =============================================================================
INSUFF_RESOURCE_PASSED = "Insufficient resource job correctly handled: {detail}"
INSUFF_RESOURCE_FAILED = "Insufficient resource job not handled correctly: {error}"

# =============================================================================
# Separate LDAP Login Messages (per node type)
# =============================================================================
LDAP_LOGIN_CONTROL_PASSED = "ldapuser login succeeded on all slurm control nodes"
LDAP_LOGIN_CONTROL_FAILED = "ldapuser login failed on one or more slurm control nodes"
LDAP_LOGIN_LOGIN_PASSED = "ldapuser login succeeded on all login nodes"
LDAP_LOGIN_LOGIN_FAILED = "ldapuser login failed on one or more login nodes"
LDAP_LOGIN_LOGINCOMP_PASSED = "ldapuser login succeeded on all login compiler nodes"
LDAP_LOGIN_LOGINCOMP_FAILED = "ldapuser login failed on one or more login compiler nodes"

# =============================================================================
# Separate Slurmd Service Messages (per node type)
# =============================================================================
SLURMD_LOGIN_ONLY_PASSED = "slurmd service is active on all login nodes"
SLURMD_LOGIN_ONLY_FAILED = "slurmd service is NOT active on one or more login nodes"
SLURMD_LOGINCOMP_ONLY_PASSED = "slurmd service is active on all login compiler nodes"
SLURMD_LOGINCOMP_ONLY_FAILED = "slurmd service is NOT active on one or more login compiler nodes"

# =============================================================================
# Separate Munge Service Messages (per node type)
# =============================================================================
MUNGE_CONTROL_PASSED = "munge service is active on all slurm control nodes"
MUNGE_CONTROL_FAILED = "munge service is NOT active on one or more slurm control nodes"
MUNGE_SLURM_PASSED = "munge service is active on all slurm compute nodes"
MUNGE_SLURM_FAILED = "munge service is NOT active on one or more slurm compute nodes"
MUNGE_LOGIN_PASSED = "munge service is active on all login nodes"
MUNGE_LOGIN_FAILED = "munge service is NOT active on one or more login nodes"
MUNGE_LOGINCOMP_PASSED = "munge service is active on all login compiler nodes"
MUNGE_LOGINCOMP_FAILED = "munge service is NOT active on one or more login compiler nodes"

# =============================================================================
# Invalid LDAP Credentials Messages
# =============================================================================
INVALID_LDAP_USER_PASSED = "Invalid LDAP username correctly denied login on all tested nodes"
INVALID_LDAP_USER_FAILED = "Invalid LDAP username was NOT denied on one or more nodes"
INVALID_LDAP_PASS_PASSED = "Invalid LDAP password correctly denied login on all tested nodes"
INVALID_LDAP_PASS_FAILED = "Invalid LDAP password was NOT denied on one or more nodes"

# =============================================================================
# Passwordless SSH Messages
# =============================================================================
SSH_PASSWORDLESS_PASSED = "Passwordless SSH from {src_type} to {dst_type} succeeded on all node pairs"
SSH_PASSWORDLESS_FAILED = "Passwordless SSH from {src_type} to {dst_type} failed on one or more node pairs"

# =============================================================================
# Multi-Login Node Job Submission Messages
# =============================================================================
MULTI_LOGIN_JOB_PASSED = "Root sbatch job from {count} login nodes all completed successfully"
MULTI_LOGIN_JOB_FAILED = "Root sbatch job from multiple login nodes failed: {error}"
MULTI_LOGIN_SKIP = "Only {count} login node(s) found, need more than 1 - skipping"

# =============================================================================
# LDAP Home Directory Permissions Messages
# =============================================================================
LDAP_HOME_PERMS_PASSED = "Write and execute permissions set on /home/{user}/ across all nodes"
LDAP_HOME_PERMS_FAILED = "Failed to set permissions on /home/{user}/ on one or more nodes: {error}"
LDAP_HOME_PERMS_ALL_PASSED = "Home directory permissions set for all {count} LDAP user(s) across all nodes"
LDAP_HOME_PERMS_ALL_FAILED = "Home directory permission setup failed for one or more LDAP users"

# =============================================================================
# Reboot Messages
# =============================================================================
REBOOT_INITIATED = "Reboot initiated on {node} ({ip})"
REBOOT_INITIATE_FAILED = "Failed to initiate reboot on {node} ({ip}): {error}"
REBOOT_ONLINE_PASSED = "Node {node} ({ip}) is back online after reboot"
REBOOT_ONLINE_FAILED = "Node {node} ({ip}) did not come back online within {timeout}s"
REBOOT_WAIT_ONLINE_TIMEOUT = "Timed out waiting for node {node} ({ip}) to come back online"

CLOUD_INIT_PASSED = "cloud-init completed successfully on {node} ({ip})"
CLOUD_INIT_FAILED = "cloud-init did NOT complete successfully on {node} ({ip}): {status}"
CLOUD_INIT_ALL_PASSED = "cloud-init completed successfully on all rebooted nodes"
CLOUD_INIT_ALL_FAILED = "cloud-init failed or did not complete on one or more nodes"

REBOOT_CONTROL_SERVICES_PASSED = "All slurm control node services (slurmctld, slurmdbd, munge) are active after reboot"
REBOOT_CONTROL_SERVICES_FAILED = "One or more slurm control node services failed to recover after reboot"
REBOOT_COMPUTE_SERVICES_PASSED = "All slurm compute node services (slurmd, munge) are active after reboot"
REBOOT_COMPUTE_SERVICES_FAILED = "One or more slurm compute node services failed to recover after reboot"
REBOOT_LOGIN_SERVICES_PASSED = "All login/login_compiler node services (slurmd, munge) are active after reboot"
REBOOT_LOGIN_SERVICES_FAILED = "One or more login/login_compiler node services failed to recover after reboot"

SLURMDBD_ACTIVE_PASSED = "slurmdbd service is active on slurm control node(s)"
SLURMDBD_ACTIVE_FAILED = "slurmdbd service is NOT active on one or more slurm control nodes"
SLURMDBD_DATA_PASSED = "slurmdbd job history preserved after reboot: job {job_id} found in sacct"
SLURMDBD_DATA_FAILED = "slurmdbd job history NOT preserved after reboot: job {job_id} not found in sacct"
SLURMDBD_DATA_NO_JOB = "No pre-reboot job ID provided to verify slurmdbd data preservation"

NODES_IDLE_AFTER_REBOOT_PASSED = "All slurm nodes returned to idle state after reboot"
NODES_IDLE_AFTER_REBOOT_FAILED = "One or more slurm nodes did not return to idle state after reboot"

REBOOT_SBATCH_PASSED = "sbatch job completed successfully after reboot (JobID: {job_id})"
REBOOT_SBATCH_FAILED = "sbatch job failed after reboot: {error}"
REBOOT_LDAP_LOGIN_PASSED = "LDAP user login succeeded after reboot"
REBOOT_LDAP_LOGIN_FAILED = "LDAP user login failed after reboot"
REBOOT_LDAP_SBATCH_PASSED = "LDAP user sbatch job completed successfully after reboot"
REBOOT_LDAP_SBATCH_FAILED = "LDAP user sbatch job failed after reboot: {error}"

# =============================================================================
# PXE Mapping to Slurm Cluster Verification Messages
# =============================================================================
PXE_CLUSTER_VERIFY_PASSED = "All {pxe_count} nodes from PXE mapping are joined to the Slurm cluster"
PXE_CLUSTER_VERIFY_FAILED = "One or more nodes from PXE mapping are NOT joined to the Slurm cluster"
PXE_CLUSTER_VERIFY_NO_NODES = "No nodes found in PXE mapping"
PXE_CLUSTER_VERIFY_NO_SLURM_NODES = "No nodes found in Slurm cluster"
PXE_CLUSTER_VERIFY_MISSING_NODES = "Missing nodes in Slurm cluster: {missing_nodes}"
PXE_CLUSTER_VERIFY_EXTRA_NODES = "Extra nodes in Slurm cluster (not in PXE): {extra_nodes}"

# =============================================================================
# UCX IB-Only Transport Test Messages
# =============================================================================
UCX_IB_PASSED = "UCX IB-only transport verified: RDMA used for inter-node MPI communication"
UCX_IB_FAILED = "UCX IB-only transport verification failed: {error}"
UCX_IB_NO_NODES = "Need at least 2 IB-configured slurm compute nodes (IB_NIC_NAME + IB_IP) for UCX test"
UCX_IB_COMPILE_FAILED = "MPI ping-pong compile step failed (mpicc returned error)"
UCX_IB_RANKS_MISSING = "Not all MPI ranks completed (expected [Rank 0] and [Rank 1] in output)"
UCX_IB_TRANSPORT_TCP = "UCX selected TCP transport for inter-node communication (IB RDMA not enforced)"
UCX_IB_TRANSPORT_OK = "UCX confirmed IB/RDMA transport (rc_mlx5/dc_mlx5) for inter-node communication"
UCX_IB_COUNTER_NO_INCREASE = "IB port_xmit_data counters did not increase (no IB traffic detected)"
UCX_IB_COUNTER_OK = "IB port_xmit_data counters increased (IB traffic confirmed on hardware)"
UCX_IB_BW_LOW = "Large-message bandwidth ({bw:.2f} GB/s) below {threshold} GB/s RDMA threshold"
UCX_IB_BW_OK = "RDMA bandwidth confirmed: {bw:.2f} GB/s for {msg_size}B messages"
UCX_IB_JOB_FAILED = "UCX IB job did not complete successfully (final state: {state})"
UCX_IB_OUTPUT_UNREADABLE = "Could not read UCX IB job output from {path}"

UCX_INSTALLED_PASSED = "UCX is installed and functional on all login_compiler nodes"
UCX_INSTALLED_FAILED = "UCX not found or non-functional on some login_compiler nodes: {nodes}"
UCX_NO_LOGIN_COMPILER = "No login_compiler nodes found; skipping UCX installation check"
UCX_NO_SUBMIT_NODE = "No login_compiler node available to submit UCX job; cannot proceed"
