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
Discovery Module - Messages.

Test names, log messages, and assertion messages for discovery tests.
"""

from typing import Dict

# =============================================================================
# TEST NAMES
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    # Build stream job stage (first test)
    "build_stream_job_stage": (
        "Verify build_stream pipeline stage '{stage}' completed successfully"
    ),
    # Common tests
    "nodes_booted": "Verify all cluster nodes are booted",
    "passwordless_ssh": "Verify passwordless SSH to all nodes",
    "hostname_sync": "Verify hostnames match PXE mapping",

    # Slurm tests
    "slurm_services": "Verify Slurm services running on all nodes",
    "cross_node_ssh": "Verify passwordless SSH across Slurm nodes",
    "sinfo_nodes": "Verify sinfo shows all compute nodes",
    "openmpi_installed": "Verify OpenMPI installation",
    "ucx_installed": "Verify UCX installation",

    # Discovery output verification tests
    "nodes_yaml_generated": "Verify nodes.yaml generated from mapping input",
    "bss_templates_created": "Verify BSS templates created per functional group",
    "cloudinit_templates_created": "Verify cloud-init templates created per functional group",

    # K8s tests
    "k8s_nodes_ready": "Verify all K8s nodes are Ready",

    # Package verification tests
    "node_packages": "Verify all required packages installed on all nodes",

    # PAM session termination
    "pam_session_termination": "Verify PAM slurm_adopt session termination behavior",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # Build stream job stage
    "build_stream_disabled_skip": (
        "build_stream is DISABLED — skipping job stage validation"
    ),
    "build_stream_job_checking": (
        "Checking build_stream stage '{stage}' (source: {source})"
    ),
    "build_stream_job_ok": (
        "Stage '{stage}' COMPLETED — job UUID: {job_id} (source: {source})"
    ),
    "build_stream_job_failed": (
        "Stage '{stage}' is '{state}' — expected COMPLETED (job: {job_id})"
    ),
    # Common
    "nodes_booted_ok": "All {count} nodes are booted and reachable",
    "nodes_booted_fail": "{failed}/{total} nodes not reachable",
    "ssh_ok": "Passwordless SSH working to all {count} nodes",
    "ssh_fail": "SSH failed for {failed} nodes",
    "hostname_ok": "All hostnames match PXE mapping",
    "hostname_fail": "{count} hostnames do not match",

    # Slurm
    "services_ok": "All services running on {node_type} nodes",
    "services_fail": "Services not running: {details}",
    "cross_ssh_ok": "Cross-node SSH working for all {count} pairs",
    "cross_ssh_fail": "Cross-node SSH failed for {count} pairs",
    "sinfo_ok": "sinfo shows all {count} compute nodes",
    "sinfo_fail": "sinfo missing {count} nodes",
    "openmpi_ok": "OpenMPI installed: {version}",
    "openmpi_fail": "OpenMPI not found",
    "ucx_ok": "UCX installed: {version}",
    "ucx_fail": "UCX not found",

    # Discovery output verification
    "nodes_yaml_ok": "nodes.yaml generated successfully",
    "nodes_yaml_fail": "nodes.yaml not found or invalid",
    "bss_templates_ok": "BSS templates generated for all {count} functional groups",
    "bss_templates_fail": "BSS templates missing for {missing} functional groups",
    "cloudinit_templates_ok": "Cloud-init templates generated for all {count} functional groups",
    "cloudinit_templates_fail": "Cloud-init templates missing for {missing} functional groups",

    # K8s
    "k8s_nodes_ok": "All {count} K8s nodes are Ready",
    "k8s_nodes_fail": "{not_ready} nodes not Ready",

    # Package verification
    "packages_ok": "All required packages installed on all {count} nodes",
    "packages_fail": "{failed}/{total} nodes have missing packages",

    # PAM session termination
    "pam_session_ok": "PAM adoption and auto-logout verified",
    "pam_session_fail": "PAM session termination not working",
}

# =============================================================================
# ASSERTION MESSAGES
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "nodes_not_booted": (
        "Not all nodes are booted.\n"
        "Failed: {failed_nodes}\n\n"
        "HOW TO FIX:\n"
        "  1. Check node power status via BMC\n"
        "  2. Verify network connectivity\n"
        "  3. Check PXE mapping admin IPs"
    ),

    "ssh_failed": (
        "Passwordless SSH failed.\n"
        "Failed: {failed_nodes}\n\n"
        "HOW TO FIX:\n"
        "  1. Re-run discovery.yml to setup SSH keys\n"
        "  2. Check SSH service on nodes\n"
        "  3. Verify firewall allows SSH"
    ),

    "hostname_mismatch": (
        "Hostnames do not match PXE mapping.\n"
        "{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Update PXE mapping or node hostnames\n"
        "  2. Re-run discovery.yml"
    ),

    "services_failed": (
        "Services not running.\n"
        "{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Check service status: systemctl status <service>\n"
        "  2. Check logs: journalctl -u <service>\n"
        "  3. Re-run discovery.yml"
    ),

    "cross_ssh_failed": (
        "Cross-node SSH failed.\n"
        "Failed pairs: {details}\n\n"
        "HOW TO FIX:\n"
        "  1. Verify SSH keys on all nodes\n"
        "  2. Re-run discovery.yml"
    ),

    "sinfo_failed": (
        "sinfo missing nodes.\n"
        "Expected: {expected}\n"
        "Missing: {missing}\n\n"
        "HOW TO FIX:\n"
        "  1. Check slurmd on missing nodes\n"
        "  2. Check slurm.conf NodeName entries"
    ),

    "openmpi_failed": (
        "OpenMPI not installed.\n\n"
        "HOW TO FIX:\n"
        "  1. Check NFS mount on login_compiler nodes\n"
        "  2. Run install_openmpi.sh manually"
    ),

    "ucx_failed": (
        "UCX not installed.\n\n"
        "HOW TO FIX:\n"
        "  1. Check NFS mount on login_compiler nodes\n"
        "  2. Run install_ucx.sh manually"
    ),

    "k8s_nodes_failed": (
        "K8s nodes not Ready.\n"
        "Not Ready: {not_ready}\n\n"
        "HOW TO FIX:\n"
        "  1. Check kubelet: systemctl status kubelet\n"
        "  2. Check node conditions: kubectl describe node <name>"
    ),

    "packages_failed": (
        "Required packages missing on nodes.\n"
        "Failed nodes: {failed_nodes}\n"
        "{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Check functional_groups_config.yml: "
        "podman exec omnia_core cat /opt/omnia/.data/functional_groups_config.yml\n"
        "  2. Verify package installation on node: ssh root@<node> rpm -qa | grep <pkg>\n"
        "  3. Re-run discovery/provision playbook to reinstall packages\n"
        "  4. Check package availability in local_repo"
    ),

    "nodes_yaml_failed": (
        "nodes.yaml not generated.\n"
        "{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Re-run discovery.yml\n"
        "  2. Check discovery logs: cat /opt/omnia/log/omnia.log\n"
        "  3. Verify PXE mapping file is valid"
    ),

    "bss_templates_failed": (
        "BSS templates not created for all functional groups.\n"
        "{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Re-run discovery.yml\n"
        "  2. Check BSS boot directory inside container\n"
        "  3. Verify PXE mapping functional groups"
    ),

    "cloudinit_templates_failed": (
        "Cloud-init templates not created for all functional groups.\n"
        "{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Re-run discovery.yml\n"
        "  2. Check cloud-init template directory inside container\n"
        "  3. Verify PXE mapping functional groups"
    ),

    "pam_session_failed": (
        "PAM slurm_adopt session termination not working.\n"
        "{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Check pam_slurm_adopt configuration on compute nodes\n"
        "  2. Verify slurmctld and slurmd are running\n"
        "  3. Check /etc/pam.d/sshd on compute nodes"
    ),

    "build_stream_job_stage_failed": (
        "BUILD STREAM STAGE VALIDATION FAILED\n"
        "Stage   : {stage}\n"
        "Job ID  : {job_id}\n"
        "Status  : {state}\n"
        "Expected: COMPLETED\n\n"
        "WHAT HAPPENED:\n"
        "  The build_stream pipeline stage did not complete successfully.\n"
        "  Discovery verification depends on the pipeline completing first.\n\n"
        "HOW TO FIX:\n"
        "  1. Check build_stream API logs on the OIM server\n"
        "  2. Query DB: podman exec omnia_postgres psql -U omnia -d build_stream_db\n"
        "            -c \"SELECT * FROM job_stages WHERE job_id = '{job_id}';\"\n"
        "  3. If FAILED, re-trigger the build_stream pipeline\n"
        "  4. If still RUNNING, wait for it to complete\n"
        "  5. To override: set build_stream_job_id in omnia_test_config.yml"
    ),
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================

SKIP_MSGS: Dict[str, str] = {
    "openmpi_not_enabled": "OpenMPI is not enabled in software_config.json",
    "ucx_not_enabled": "UCX is not enabled in software_config.json",
    "openldap_not_enabled": "OpenLDAP is not enabled in software_config.json",
    "ldms_not_enabled": "LDMS is not enabled in software_config.json",
    "no_nodes_for_packages": "No nodes found in PXE mapping for package verification",
    "no_slurm_nodes": "No Slurm nodes found in PXE mapping",
    "no_k8s_nodes": "No K8s nodes found in PXE mapping",
    "skip_detail_not_enabled": "Test skipped - {software} not enabled",
    "skip_detail_no_nodes": "Test skipped - no {node_type} nodes",
}
