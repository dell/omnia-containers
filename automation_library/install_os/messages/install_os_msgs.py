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
Install OS - Messages and Test Variables.

This module contains all messages, status strings, error instructions,
and test variables for the install_os automation.
"""

from typing import Dict

# =============================================================================
# TEST NAMES (displayed in test output header)
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    # Pre-flight checks
    "source_iso_exists": "Verify source ISO exists at configured path",
    "source_iso_checksum": "Verify source ISO SHA-256 checksum matches",
    "tooling_available": "Verify required ISO tooling is installed",
    "idrac_reachable": "Verify iDRAC BMC is reachable via Redfish API",
    "idrac_lc_status": "Verify iDRAC Lifecycle Controller is ready",
    "virtual_media_status": "Verify iDRAC virtual media insertion status",
    "boot_override_status": "Verify iDRAC boot override status",
    "power_state": "Verify iDRAC power state",
    # ISO generation
    "output_iso_exists": "Verify repacked ISO was created",
    "output_iso_checksum": "Verify repacked ISO checksum is recorded",
    "kickstart_in_iso": "Verify kickstart.cfg exists in NFS output directory",
    "grub_config_in_iso": "Verify GRUB2 config references NFS kickstart",
    "manifest_exists": "Verify install manifest was generated",
    # Kickstart validation
    "kickstart_rootpw": "Verify Kickstart contains rootpw directive",
    "kickstart_sshkey": "Verify Kickstart contains sshkey directive",
    "kickstart_static_ip": "Verify Kickstart configures static admin/PXE IP",
    "kickstart_base_env": "Verify Kickstart sets Server with GUI environment",
    "user_kickstart_scan": "Scan user-provided Kickstart for required directives",
    # Post-install validation
    "ssh_reachable": "Verify installed node is reachable via SSH with OIM key",
    "os_version": "Verify installed OS version matches expected RHEL version",
    "architecture": "Verify installed node architecture is aarch64",
    "static_ip": "Verify static admin/PXE IP is configured on installed node",
    "gui_packages": "Verify Server with GUI packages are installed",
    "hostname": "Verify hostname is set correctly on installed node",
    # OS deployment
    "os_deployment_job": "Verify iDRAC OS deployment job status",
    "nfs_share_accessible": "Verify NFS share is accessible from OIM",
    # Playbook execution
    "playbook_execution": "Execute install_os_arm_node.yml playbook",
    # Negative tests
    "neg_missing_iso_config": "Verify playbook fails when iso_config.yml is missing",
    "neg_invalid_yaml": "Verify playbook fails for malformed YAML in iso_config.yml",
    "neg_invalid_iso_path": "Verify playbook fails for non-existent ISO source path",
    "neg_invalid_nfs_format": "Verify playbook fails for invalid NFS share format",
    "neg_empty_iso_config": "Verify playbook fails for empty iso_config.yml",
}

# =============================================================================
# TEST LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # Pre-flight
    "source_iso_found": "Source ISO found at {path}",
    "source_iso_not_found": "Source ISO NOT found at {path}",
    "checksum_match": "Source ISO checksum matches: {checksum}",
    "checksum_mismatch": "Source ISO checksum mismatch: expected {expected}, got {actual}",
    "tools_available": "All required tools available: {tools}",
    "tools_missing": "Missing tools: {missing}",
    "idrac_reachable": "iDRAC reachable at {bmc_ip} (HTTP {status_code})",
    "idrac_not_reachable": "iDRAC NOT reachable at {bmc_ip} (HTTP {status_code})",
    "lc_ready": "Lifecycle Controller ready (status: {status})",
    "lc_not_ready": "Lifecycle Controller NOT ready (status: {status})",
    "virtual_media_inserted": "Virtual media inserted: {media_type}",
    "virtual_media_not_inserted": "Virtual media status: {status}",
    "boot_override_configured": "Boot override: source={source}, enabled={enabled}, mode={mode}",
    "boot_override_failed": "Failed to check boot override: {error}",
    "power_state": "Power state: {state}",
    "power_state_failed": "Failed to check power state: {error}",
    # ISO generation
    "output_iso_found": "Repacked ISO found: {path}",
    "output_iso_not_found": "Repacked ISO NOT found in {path}",
    "manifest_found": "Install manifest found at {path}",
    "manifest_not_found": "Install manifest NOT found at {path}",
    "kickstart_found": "kickstart.cfg found in NFS output directory",
    "kickstart_not_found": "kickstart.cfg NOT found in NFS output directory",
    "grub_config_ok": "GRUB2 config correctly references NFS kickstart (inst.ks=nfs:...)",
    "grub_config_missing": "GRUB2 config does NOT reference NFS kickstart (inst.ks=nfs:...)",
    # Kickstart
    "rootpw_found": "rootpw directive found in Kickstart",
    "rootpw_missing": "rootpw directive NOT found in Kickstart",
    "sshkey_found": "sshkey directive found in Kickstart",
    "sshkey_missing": "sshkey directive NOT found in Kickstart",
    "static_ip_found": "Static IP {ip} configured in Kickstart",
    "static_ip_missing": "Static IP {ip} NOT found in Kickstart",
    "base_env_found": "Server with GUI environment configured in Kickstart",
    "base_env_missing": "Server with GUI environment NOT configured in Kickstart",
    # Post-install
    "ssh_connected": "SSH connection successful to {node_ip}",
    "ssh_failed": "SSH connection FAILED to {node_ip}",
    "os_version_match": "OS version matches: {version}",
    "os_version_mismatch": "OS version mismatch: expected {expected}, got {actual}",
    "arch_match": "Architecture matches: {arch}",
    "arch_mismatch": "Architecture mismatch: expected {expected}, got {actual}",
    "ip_configured": "Static IP {ip} is configured on node",
    "ip_not_configured": "Static IP {ip} NOT configured on node",
    "gui_installed": "Server with GUI packages installed (default target: {target})",
    "gui_not_installed": "Server with GUI packages NOT installed",
    "hostname_match": "Hostname matches: {hostname}",
    "hostname_mismatch": "Hostname mismatch: expected {expected}, got {actual}",
    # OS deployment
    "os_deployment_job_found": "OS deployment job found: {job_name} (status: {job_status})",
    "os_deployment_job_not_found": "OS deployment job NOT found in iDRAC job queue",
    "os_deployment_job_completed": "OS deployment job completed successfully",
    "os_deployment_job_failed": "OS deployment job FAILED: {message}",
    "nfs_share_reachable": "NFS share accessible: {nfs_server}:{nfs_path}",
    "nfs_share_not_reachable": "NFS share NOT accessible: {error}",
    # Playbook
    "playbook_started": "Starting install_os_arm_node.yml execution",
    "playbook_success": "install_os_arm_node.yml executed successfully",
    "playbook_failed": "install_os_arm_node.yml execution FAILED",
    # Negative tests
    "neg_validation_failed_correctly": "Playbook correctly failed validation (rc={rc})",
    "neg_validation_should_have_failed": "Playbook should have failed but exited rc={rc}",
    "neg_expected_error_found": "Expected error detected: {error}",
    "neg_expected_error_missing": "Expected error NOT detected in output",
}

# =============================================================================
# TEST ASSERT MESSAGES
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "source_iso_not_found": (
        "Source ISO not found at '{path}'. "
        "Place the RHEL 10.x AArch64 Server with GUI ISO at the configured path."
    ),
    "checksum_mismatch": (
        "Source ISO checksum mismatch. Expected: {expected}, Got: {actual}. "
        "The ISO may be corrupted. Re-download and retry."
    ),
    "tools_missing": (
        "Required ISO tools missing: {missing}. "
        "Install the missing packages and re-run."
    ),
    "idrac_not_reachable": (
        "iDRAC not reachable at {bmc_ip} (HTTP {status_code}). "
        "Verify network connectivity, BMC IP, and iDRAC status."
    ),
    "lc_not_ready": (
        "iDRAC Lifecycle Controller not ready (status: {status}). "
        "Wait for LC to become ready and retry."
    ),
    "virtual_media_failed": (
        "Failed to check virtual media: {error}. "
        "Check iDRAC virtual media configuration."
    ),
    "boot_override_failed": (
        "Failed to check boot override: {error}. "
        "Check iDRAC boot configuration."
    ),
    "power_state_failed": (
        "Failed to check power state: {error}. "
        "Check iDRAC power management configuration."
    ),
    "output_iso_not_found": (
        "Repacked ISO not found in {path}. "
        "Check playbook logs for ISO creation errors."
    ),
    "kickstart_not_in_iso": (
        "kickstart.cfg not found in NFS output directory. "
        "Check ISO creation role logs."
    ),
    "grub_config_missing": (
        "GRUB2 config does not reference NFS kickstart (inst.ks=nfs:...). "
        "Check grub_nfs.cfg.j2 template."
    ),
    "rootpw_missing": "rootpw directive missing from Kickstart file.",
    "sshkey_missing": "sshkey directive missing from Kickstart file.",
    "static_ip_missing": (
        "Static IP {ip} not configured in Kickstart. "
        "Verify network_spec.yml and PXE mapping."
    ),
    "base_env_missing": (
        "Server with GUI environment not configured in Kickstart. "
        "Check Kickstart template."
    ),
    "ssh_not_reachable": (
        "Installed node not reachable via SSH at {node_ip}. "
        "Check network connectivity and SSH configuration."
    ),
    "os_version_mismatch": (
        "OS version mismatch on installed node. "
        "Expected: {expected}, Got: {actual}."
    ),
    "arch_mismatch": (
        "Architecture mismatch on installed node. "
        "Expected: {expected}, Got: {actual}."
    ),
    "ip_not_configured": (
        "Static IP {ip} not configured on installed node. "
        "Check Kickstart network configuration."
    ),
    "gui_not_installed": (
        "Server with GUI packages not installed. "
        "Check Kickstart environment specification."
    ),
    "hostname_mismatch": (
        "Hostname mismatch. Expected: {expected}, Got: {actual}."
    ),
    "os_deployment_job_not_found": (
        "OS deployment job not found in iDRAC job queue. "
        "Check if idrac_os_deployment module executed successfully."
    ),
    "os_deployment_job_failed": (
        "OS deployment job failed: {message}. "
        "Check iDRAC job logs and NFS share accessibility."
    ),
    "nfs_share_not_accessible": (
        "NFS share not accessible from OIM: {error}. "
        "Verify NFS server is running and share is exported."
    ),
    # Negative tests
    "neg_should_have_failed": (
        "Playbook should have failed for invalid input but succeeded (rc={rc})."
    ),
    "neg_missing_error": (
        "Playbook failed but expected error pattern not found. "
        "Errors: {errors}"
    ),
}
