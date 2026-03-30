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

    # K8s tests
    "k8s_nodes_ready": "Verify all K8s nodes are Ready",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
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

    # K8s
    "k8s_nodes_ok": "All {count} K8s nodes are Ready",
    "k8s_nodes_fail": "{not_ready} nodes not Ready",
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
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================

SKIP_MSGS: Dict[str, str] = {
    "openmpi_not_enabled": "OpenMPI is not enabled in software_config.json",
    "ucx_not_enabled": "UCX is not enabled in software_config.json",
    "openldap_not_enabled": "OpenLDAP is not enabled in software_config.json",
    "ldms_not_enabled": "LDMS is not enabled in software_config.json",
    "no_slurm_nodes": "No Slurm nodes found in PXE mapping",
    "no_k8s_nodes": "No K8s nodes found in PXE mapping",
    "skip_detail_not_enabled": "Test skipped - {software} not enabled",
    "skip_detail_no_nodes": "Test skipped - no {node_type} nodes",
}
