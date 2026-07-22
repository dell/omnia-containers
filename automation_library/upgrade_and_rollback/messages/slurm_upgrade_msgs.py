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
Slurm Upgrade Module - Messages.

String constants for Slurm upgrade post-verification test output.
"""

# =============================================================================
# TEST NAMES (displayed in TestLogger)
# =============================================================================
SLURM_UPGRADE_TEST_NAMES = {
    "pre_upgrade_verify": "Verify Slurm cluster health before upgrade",
    "pre_upgrade_capture": "Capture Slurm cluster state before upgrade",
    "upgrade_gate": "Slurm upgrade gate — check metadata and manifest",
    "run_slurm_upgrade": "Trigger Slurm upgrade playbook",
    "nfs_mount": "Verify Slurm NFS share is mounted on OIM",
    "slurm_conf_backup": "Verify slurm.conf exists in NFS backup",
    "mysql_datadir_backup": "Verify MySQL datadir exists in NFS backup",
    "hpc_tracking_cleanup": "Verify HPC tools tracking files cleaned up",
    "no_running_jobs": "Verify no active jobs on Slurm cluster",
    "all_nodes_idle": "Verify all Slurm compute nodes are idle",
    "slurmctld_active": "Verify slurmctld active on control nodes post-upgrade",
    "slurmd_active": "Verify slurmd active on compute nodes post-upgrade",
    "munge_active": "Verify munge active on all Slurm nodes post-upgrade",
    "sbatch_post_upgrade": "Verify sbatch job succeeds post-upgrade",
    "srun_post_upgrade": "Verify srun job succeeds post-upgrade",
}

# =============================================================================
# LOG MESSAGES (check / progress output)
# =============================================================================
SLURM_UPGRADE_LOG_MSGS = {
    # Pre-upgrade
    "verifying_pre_upgrade": "Verifying Slurm cluster health before upgrade",
    "capturing_pre_upgrade": "Capturing Slurm cluster state before upgrade",
    "cluster_healthy": "Slurm cluster is healthy: {idle_nodes} idle nodes, {job_count} running jobs",
    "cluster_unhealthy": "Slurm cluster has issues: {issues}",
    "state_captured": "Captured pre-upgrade state: {jobs} jobs, {nodes} nodes, version {version}",
    "state_saved": "Saved pre-upgrade state to {file_path}",
    # Gate
    "reading_metadata": "Reading oim_metadata.yml to determine upgrade state",
    "metadata_ok": "Upgrade detected: {previous} → {current}",
    "metadata_no_upgrade": "Not an upgrade scenario (no previous_omnia_version)",
    "metadata_read_failed": "Failed to read oim_metadata.yml: {error}",
    "reading_manifest": "Reading upgrade_manifest.yml for component_status.slurm",
    "manifest_slurm_status": "Manifest component_status.slurm = {status}",
    "manifest_not_found": "upgrade_manifest.yml not found — upgrade not initiated",
    "manifest_read_failed": "Failed to read upgrade_manifest.yml: {error}",
    "triggering_upgrade": "Slurm not yet upgraded — triggering upgrade playbook",
    "upgrade_running": "Slurm upgrade in progress… elapsed {elapsed}s",
    "upgrade_completed": "Slurm upgrade playbook completed (rc={rc})",
    "upgrade_failed": "Slurm upgrade playbook failed (rc={rc})",
    "upgrade_timeout": "Slurm upgrade timed out after {timeout}s",
    # NFS
    "checking_nfs": "Checking Slurm NFS mount on OIM",
    "nfs_mounted": "Slurm NFS share mounted at {mount_point}",
    "nfs_not_mounted": "Slurm NFS share is NOT mounted",
    "nfs_config_error": "Failed to read NFS configuration: {error}",
    # Backup
    "checking_slurm_conf": "Checking slurm.conf in NFS backup at {path}",
    "slurm_conf_found": "slurm.conf found at {path}",
    "slurm_conf_missing": "slurm.conf NOT found at {path}",
    "checking_mysql": "Checking MySQL datadir in NFS backup at {path}",
    "mysql_found": "MySQL datadir found (ibdata1={ibdata}, mysql_db={mysql_db})",
    "mysql_missing": "MySQL datadir NOT found at {path}",
    # HPC tracking
    "checking_hpc_tracking": "Checking HPC tools tracking files are cleaned up",
    "hpc_tracking_clean": "All HPC tracking files cleaned up",
    "hpc_tracking_present": "HPC tracking file still present: {path}",
    # Cluster state
    "checking_running_jobs": "Checking for running jobs on Slurm cluster",
    "no_jobs_found": "No running jobs on Slurm cluster",
    "jobs_found": "{count} running job(s) detected on Slurm cluster",
    "squeue_failed": "squeue command failed: {error}",
    "checking_idle": "Checking all compute nodes are in idle state",
    "all_idle": "All {count} compute nodes are in idle state",
    "non_idle_found": "{count} compute node(s) are NOT idle: {nodes}",
    "sinfo_failed": "sinfo command failed: {error}",
    # Services
    "checking_service": "Checking {service} on {hostname} ({ip})",
    "service_active": "{service} is active on {hostname}",
    "service_inactive": "{service} is NOT active on {hostname} ({ip})",
    # Jobs
    "submitting_sbatch": "Submitting sbatch test job from control node",
    "sbatch_ok": "sbatch job completed (JobID: {job_id}, State: {state})",
    "sbatch_failed": "sbatch job failed: {error}",
    "submitting_srun": "Submitting srun test job from control node",
    "srun_ok": "srun job completed on {num_nodes} node(s)",
    "srun_failed": "srun job failed: {error}",
    # Control node
    "no_control_node": "No slurm control node found in PXE mapping",
    "no_compute_nodes": "No slurm compute nodes found in PXE mapping",
    "control_unreachable": "Slurm control node {hostname} ({ip}) is unreachable",
}

# =============================================================================
# ASSERT MESSAGES (pytest.fail output)
# =============================================================================
SLURM_UPGRADE_ASSERT_MSGS = {
    "metadata_read_failed": (
        "Cannot read oim_metadata.yml from omnia_core container.\n"
        "Error: {error}\n"
        "Ensure omnia_core container is running and /opt/omnia/.data/oim_metadata.yml exists."
    ),
    "upgrade_playbook_failed": (
        "Slurm upgrade playbook failed with rc={rc}.\n"
        "Last output:\n{output}\n"
        "Check ansible logs on the OIM for details."
    ),
    "upgrade_timeout": (
        "Slurm upgrade playbook did not complete within {timeout}s.\n"
        "The process may still be running. Check the OIM for status."
    ),
    "nfs_not_mounted": (
        "Slurm NFS share is not mounted on OIM.\n"
        "The upgrade_slurm role should mount the NFS share via nfs_client.yml.\n"
        "Check storage_config.yml mounts and NFS server reachability."
    ),
    "nfs_config_error": (
        "Failed to read Slurm NFS configuration from omnia_config.yml / storage_config.yml.\n"
        "Error: {error}\n"
        "Ensure omnia_config.yml has slurm_cluster[].nfs_storage_name and "
        "storage_config.yml has matching mounts[] entries."
    ),
    "slurm_conf_missing": (
        "slurm.conf not found at {path}.\n"
        "The NFS backup must contain the control node's slurm configuration.\n"
        "Verify the slurm_control_node_x86_64 host directory exists on the NFS share."
    ),
    "ctld_dir_missing": (
        "Slurm control node directory not found on NFS at {path}.\n"
        "Expected: {nfs_mount}/slurm/<control_hostname>/\n"
        "Ensure the NFS share contains the slurm control node backup."
    ),
    "mysql_missing": (
        "MySQL datadir not found in NFS backup at {path}.\n"
        "Expected ibdata1 or mysql/ system database.\n"
        "Verify MariaDB data was backed up to the NFS share."
    ),
    "hpc_tracking_present": (
        "HPC tools tracking file(s) still present after upgrade: {files}.\n"
        "The upgrade_slurm role should remove these tracking files.\n"
        "Mount point: {mount_point}"
    ),
    "running_jobs": (
        "Slurm cluster has {count} active running job(s).\n"
        "All jobs must be drained/stopped before upgrade can proceed.\n"
        "Run: scancel --all on the control node."
    ),
    "squeue_failed": (
        "Failed to check running jobs on Slurm cluster.\n"
        "Error: {error}\n"
        "Ensure slurmctld is running on the control node."
    ),
    "non_idle_nodes": (
        "Upgrade requires all compute nodes to be IDLE.\n"
        "{count} node(s) are not idle: {nodes}\n"
        "Drain and stop jobs, then re-run upgrade."
    ),
    "sinfo_failed": (
        "Failed to query node states from Slurm controller.\n"
        "Error: {error}\n"
        "Ensure slurmctld is running and reachable."
    ),
    "slurmctld_inactive": (
        "slurmctld is NOT active on one or more control nodes after upgrade.\n"
        "Failed nodes: {nodes}\n"
        "Check systemctl status slurmctld on the control node(s)."
    ),
    "slurmd_inactive": (
        "slurmd is NOT active on one or more compute nodes after upgrade.\n"
        "Failed nodes: {nodes}\n"
        "Check systemctl status slurmd on the compute node(s)."
    ),
    "munge_inactive": (
        "munge is NOT active on one or more Slurm nodes after upgrade.\n"
        "Failed nodes: {nodes}\n"
        "Check systemctl status munge on the affected node(s)."
    ),
    "no_control_node": (
        "No slurm control node found in PXE mapping.\n"
        "Ensure pxe_mapping_file.csv has slurm_control_node_* entries."
    ),
    "no_compute_nodes": (
        "No slurm compute nodes found in PXE mapping.\n"
        "Ensure pxe_mapping_file.csv has slurm_node_* entries."
    ),
    "sbatch_failed": (
        "Post-upgrade sbatch job failed.\n"
        "Error: {error}\n"
        "Verify Slurm cluster is healthy after upgrade."
    ),
    "srun_failed": (
        "Post-upgrade srun job failed.\n"
        "Error: {error}\n"
        "Verify Slurm cluster is healthy after upgrade."
    ),
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================
SLURM_UPGRADE_SKIP_MSGS = {
    "not_upgrade": "Not an upgrade scenario — previous_omnia_version not set in oim_metadata.yml",
    "slurm_skipped": "Slurm upgrade was skipped in manifest (component_status.slurm = skipped)",
    "manifest_missing": "upgrade_manifest.yml not found — upgrade not initiated, skipping",
    "gate_not_passed": "Slurm upgrade gate did not pass — skipping post-upgrade checks",
    "no_slurm_cluster": "No Slurm cluster configured (no slurm_cluster in omnia_config.yml)",
    "no_control_node": "No slurm control node found in PXE mapping — skipping",
    "no_compute_nodes": "No slurm compute nodes found in PXE mapping — skipping",
    "nfs_not_configured": "No NFS storage configured for Slurm cluster — skipping NFS checks",
}
