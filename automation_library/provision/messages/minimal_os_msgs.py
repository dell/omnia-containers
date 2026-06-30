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
Minimal OS - Messages and Test Variables.

This module contains all messages, status strings, error instructions,
and test variables for the minimal_os automation.
"""

# Test names (displayed in test output header)
TEST_NAMES = {
    # Functional Tests (TC-F01 to TC-F17)
    "schema_validation": "TC-F01: Functional Group Schema Validation",
    "arch_x86_64": "TC-F02: Architecture Validation (x86_64)",
    "arch_aarch64": "TC-F03: Architecture Validation (aarch64)",
    "pxe_mapping": "TC-F04: Node Assignment via PXE Mapping",
    "base_packages": "TC-F05: Base OS Packages Present",
    "ldms_packages": "TC-F06: LDMS Packages Present",
    "excluded_packages": "TC-F07: Excluded Packages Verification",
    "image_storage": "TC-F08: Image Available in Object Storage",
    "additional_packages": "TC-F09: Additional Packages Support",
    "no_additional_packages": "TC-F10: Graceful Fallback (No Additional Packages)",
    "network_identity": "TC-F12: Network Identity Assignment",
    "ram_filesystem": "TC-F13: RAM-Based Root Filesystem",
    "handoff_services": "TC-F14: Handoff Service State",
    "ssh_access": "TC-F15: SSH Access with Authorized Keys",
    "package_manager": "TC-F16: Package Manager Functionality",
    "ldms_not_running": "TC-F17: LDMS Service State (Not Running)",
    # Negative Tests (TC-E01 to TC-E04)
    "arch_mismatch": "TC-E01: Architecture Mismatch Rejection",
    "mismatch_isolation": "TC-E02: Architecture Mismatch Isolation",
    "missing_image": "TC-E03: Missing Image Detection",
    "invalid_packages": "TC-E04: Invalid Additional Packages Handling",
    # Security Tests (TC-S01 to TC-S03)
    "network_isolation": "TC-S01: Management Network Isolation",
    "ssh_key_access": "TC-S02: SSH Key-Based Access Control",
    "no_credentials": "TC-S03: No Embedded Credentials",
}

# Test log messages
TEST_LOG_MSGS = {
    # Schema validation
    "schema_ok": "Functional groups validated successfully",
    "schema_failed": "Functional group schema validation failed",
    "groups_found": "Found functional groups: {groups}",
    "groups_not_found": "Minimal OS functional groups not found",
    # Architecture validation
    "arch_match": "Architecture validation passed for {node}",
    "arch_mismatch": "Architecture mismatch: expected {expected}, got {actual}",
    "no_nodes": "No nodes found for functional group {group}",
    # PXE mapping
    "pxe_valid": "PXE mapping valid with {count} nodes assigned",
    "pxe_invalid": "PXE mapping validation failed",
    "pxe_not_found": "PXE mapping file not found",
    # Base packages
    "base_pkg_ok": "All base OS packages present",
    "base_pkg_missing": "Missing base packages: {packages}",
    "base_pkg_failed": "Missing base packages: {packages}",
    # LDMS packages
    "ldms_pkg_ok": "LDMS packages and binaries present",
    "ldms_pkg_missing": "LDMS packages missing: {packages}",
    "ldms_pkg_failed": "LDMS packages missing: {packages}",
    "ldms_binary_ok": "ldmsd binary found at {path}",
    "ldms_binary_missing": "ldmsd binary not found in PATH",
    # Excluded packages
    "excluded_ok": "No excluded packages or services found",
    "excluded_found": "Found excluded packages: {packages}",
    "excluded_failed": "Found excluded packages: {packages}",
    "excluded_svc_found": "Found excluded services running: {services}",
    # Image storage
    "image_ok": "OS images available in object storage",
    "image_missing": "OS images not found in object storage",
    "image_found": "Found image: {image}",
    # Additional packages
    "addl_pkg_ok": "All additional packages installed",
    "addl_pkg_missing": "Missing additional packages: {packages}",
    "addl_pkg_empty": "additional_packages.json is empty or absent",
    # Network identity
    "network_ok": "Network identity verified for {node}",
    "network_failed": "Network identity verification failed",
    "hostname_match": "Hostname matches: {hostname}",
    "hostname_mismatch": "Hostname mismatch: expected {expected}, got {actual}",
    # RAM filesystem
    "ram_fs_ok": "Root filesystem is RAM-based (tmpfs)",
    "ram_fs_failed": "Root filesystem is not tmpfs",
    # Handoff services
    "handoff_ok": "Handoff service state verified",
    "handoff_failed": "Handoff service state verification failed",
    "required_svc_ok": "Required services running: {services}",
    "required_svc_missing": "Required services not running: {services}",
    "forbidden_svc_found": "Forbidden services running: {services}",
    # SSH access
    "ssh_ok": "SSH access properly configured",
    "ssh_failed": "SSH access verification failed",
    "ssh_key_ok": "SSH key authentication successful",
    "ssh_pwd_disabled": "Password authentication disabled",
    # Package manager
    "pkg_mgr_ok": "Package manager (dnf) functional",
    "pkg_mgr_failed": "Package manager verification failed",
    "repo_ok": "Local repository accessible",
    # LDMS not running
    "ldms_svc_ok": "LDMS service not running (as expected)",
    "ldms_svc_running": "LDMS service is running (unexpected)",
    # Architecture mismatch (negative)
    "mismatch_detected": "Architecture mismatch correctly detected",
    "mismatch_not_detected": "Architecture mismatch was NOT detected",
    # Security
    "sec_network_ok": "Provisioning traffic confined to management network",
    "sec_ssh_ok": "SSH restricted to OIM-provisioned keys",
    "sec_no_creds": "No embedded credentials found in image",
    "sec_creds_found": "Embedded credentials found: {details}",
}

# Test assert messages (user-friendly with instructions)
TEST_ASSERT_MSGS = {
    "schema_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F01: FUNCTIONAL GROUP SCHEMA VALIDATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Error: {error}
║
║ HOW TO FIX:
║   1. Verify os_x86_64 and os_aarch64 functional groups are defined
║   2. Check /opt/omnia/.data/functional_groups_config.yml
║   3. Ensure OIM is properly deployed with Omnia
║   4. Verify functional groups in PXE mapping file
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "arch_mismatch": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F02/F03: ARCHITECTURE VALIDATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Node: {node}
║ Expected: {expected} | Actual: {actual}
║
║ HOW TO FIX:
║   1. Verify node architecture: ssh root@<node_ip> 'uname -m'
║   2. Update PXE mapping to assign correct functional group
║   3. x86_64 nodes → os_x86_64, aarch64 nodes → os_aarch64
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pxe_mapping_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F04: PXE MAPPING VALIDATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Error: {error}
║
║ HOW TO FIX:
║   1. Check PXE mapping file path in provision_config.yml
║   2. Verify file exists at configured path
║   3. Ensure each node has a functional_group assigned
║   4. Verify no node is assigned to multiple groups
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "base_packages_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F05: BASE OS PACKAGES MISSING
╠══════════════════════════════════════════════════════════════════════════════╣
║ Missing: {missing}
║ Node: {node}
║
║ HOW TO FIX:
║   1. Verify image build includes all base packages
║   2. Check Pulp repository has required packages
║   3. Rebuild OS image with correct package list
║   4. Re-provision the node
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "ldms_packages_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F06: LDMS PACKAGES MISSING
╠══════════════════════════════════════════════════════════════════════════════╣
║ Error: {error}
║ Node: {node}
║
║ HOW TO FIX:
║   1. Verify ovis-ldms package is in Pulp repository
║   2. Check image build configuration includes LDMS
║   3. Rebuild OS image with LDMS packages
║   4. Verify: rpm -q ovis-ldms
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "excluded_packages_found": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F07: EXCLUDED PACKAGES FOUND
╠══════════════════════════════════════════════════════════════════════════════╣
║ Found: {packages}
║ Node: {node}
║
║ HOW TO FIX:
║   1. Minimal OS should NOT have Slurm, K8s, CUDA, MPI packages
║   2. Review image build configuration
║   3. Remove excluded packages from image definition
║   4. Rebuild and re-provision
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "additional_packages_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F09: ADDITIONAL PACKAGES MISSING
╠══════════════════════════════════════════════════════════════════════════════╣
║ Missing: {missing}
║ Node: {node}
║
║ HOW TO FIX:
║   1. Check software_config.json for additional_packages configuration
║   2. Verify packages are available in Pulp repository
║   3. Rebuild OS image with additional packages
║   4. Re-provision the node
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "network_identity_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F12: NETWORK IDENTITY VERIFICATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Error: {error}
║ Node: {node}
║
║ HOW TO FIX:
║   1. Verify node hostname matches PXE mapping assignment
║   2. Check admin IP is configured on the node
║   3. Verify NetworkManager is running and configured
║   4. Re-provision if network identity is incorrect
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "image_not_found": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F08: OS IMAGE NOT FOUND IN OBJECT STORAGE
╠══════════════════════════════════════════════════════════════════════════════╣
║ Missing: {arch} image
║
║ HOW TO FIX:
║   1. Images are built on-demand during node provisioning
║   2. Verify build_stream_config.yml is configured correctly
║   3. Check build logs for any errors
║   4. Image storage is managed by Omnia provisioning system
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "services_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F14: HANDOFF SERVICE STATE VERIFICATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Services not running: {missing}
║ Node: {node}
║
║ HOW TO FIX:
║   1. Required services: sshd, chronyd, NetworkManager
║   2. Forbidden services: slurmd, kubelet, docker, podman
║   3. Check image configuration for service enablement
║   4. Rebuild image with correct service state
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "handoff_services_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F14: HANDOFF SERVICE STATE VERIFICATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Required missing: {required_missing}
║ Forbidden running: {forbidden_running}
║ Node: {node}
║
║ HOW TO FIX:
║   1. Required services: sshd, chronyd, NetworkManager
║   2. Forbidden services: slurmd, kubelet, docker, podman
║   3. Check image configuration for service enablement
║   4. Rebuild image with correct service state
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "ssh_access_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F15: SSH ACCESS VERIFICATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Error: {error}
║ Node: {node}
║
║ HOW TO FIX:
║   1. Verify OIM SSH key is provisioned to node
║   2. Check /root/.ssh/authorized_keys on node
║   3. Verify sshd_config has PasswordAuthentication no
║   4. Check SSH service: systemctl status sshd
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "package_manager_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F16: PACKAGE MANAGER VERIFICATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Error: {error}
║ Node: {node}
║
║ HOW TO FIX:
║   1. Verify dnf binary exists on the node
║   2. Check local Pulp repository is accessible
║   3. Verify network connectivity to repository server
║   4. Check: dnf repolist
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "ram_filesystem_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F13: RAM-BASED ROOT FILESYSTEM VERIFICATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Root filesystem type: {fs_type}
║ Expected: tmpfs
║ Node: {node}
║
║ HOW TO FIX:
║   1. Verify PXE boot configuration loads image to RAM
║   2. Check initrd configuration for tmpfs root
║   3. Verify node is PXE booting (not local disk)
║   4. Check: df -T / (should show tmpfs)
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "ldms_running": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F17: LDMS SERVICE RUNNING (SHOULD NOT BE)
╠══════════════════════════════════════════════════════════════════════════════╣
║ LDMS service status: {status}
║ Node: {node}
║
║ HOW TO FIX:
║   1. LDMS should be installed but NOT running at handoff
║   2. Check image configuration for service enablement
║   3. Disable ldmsd service in image: systemctl disable ldmsd
║   4. Rebuild and re-provision
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "ldms_service_running": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-F17: LDMS SERVICE RUNNING (SHOULD NOT BE)
╠══════════════════════════════════════════════════════════════════════════════╣
║ Node: {node}
║
║ HOW TO FIX:
║   1. LDMS should be installed but NOT running at handoff
║   2. Check image configuration for service enablement
║   3. Disable ldmsd service in image: systemctl disable ldmsd
║   4. Rebuild and re-provision
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "arch_mismatch_not_detected": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-E01: ARCHITECTURE MISMATCH NOT DETECTED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Node: {node} (architecture: {actual_arch})
║ Assigned to: {assigned_group}
║
║ ISSUE: System should have rejected this assignment
║
║ HOW TO FIX:
║   1. Verify architecture validation is enabled
║   2. Check discovery validation logic
║   3. Ensure pre-provisioning checks are active
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "credentials_found": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-S03: EMBEDDED CREDENTIALS FOUND IN IMAGE
╠══════════════════════════════════════════════════════════════════════════════╣
║ Node: {node}
║
║ SECURITY ISSUE: OS image should not contain credentials
║
║ HOW TO FIX:
║   1. Remove hardcoded passwords from image
║   2. Remove embedded private keys
║   3. Clear password hashes from /etc/shadow
║   4. Rebuild image with clean credentials
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "security_credentials_found": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ TC-S03: EMBEDDED CREDENTIALS FOUND IN IMAGE
╠══════════════════════════════════════════════════════════════════════════════╣
║ Found: {details}
║
║ SECURITY ISSUE: OS image should not contain credentials
║
║ HOW TO FIX:
║   1. Remove hardcoded passwords from image
║   2. Remove embedded private keys
║   3. Clear password hashes from /etc/shadow
║   4. Rebuild image with clean credentials
╚══════════════════════════════════════════════════════════════════════════════╝
""",
}
