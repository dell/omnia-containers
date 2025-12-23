# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
OIM Prerequisite Check - User-Facing Messages.

This module contains all user-facing messages, status strings, and error
instructions for the OIM prerequisite check tool.

Message Naming Convention:
    - *_check_start: Message shown when a check begins
    - *_pass / *_success: Message shown when a check passes
    - *_fail: Message shown when a check fails
    - *_instruction: Detailed instructions for fixing a failure

Placeholders:
    Messages use Python string formatting with named placeholders.
    Example: "OS validation passed: {os_name} {os_version}"

    Common placeholders:
        {config_path}   - Path to user_config.yml
        {interface}     - Network interface name
        {server}        - Server IP address
        {error}         - Error message from command
        {version}       - Software version string

Usage:
    from automation_library.messages.oim_prereq_msgs import OIM_PREREQ_MSGS

    # Format a message with placeholders
    msg = OIM_PREREQ_MSGS["os_check_pass"].format(os_name="rhel", os_version="10")

Author: Dell Technologies
"""

from typing import Dict

OIM_PREREQ_MSGS: Dict[str, str] = {
    # ==========================================================================
    # Hostname Configuration (FIRST TASK)
    # ==========================================================================
    "hostname_check_start": "Checking hostname configuration...",
    "hostname_set_start": "Setting hostname to {hostname}...",
    "hostname_set_pass": "Hostname set successfully: {hostname}",
    "hostname_already_set": "Hostname already configured: {hostname}",
    "hostname_verify_pass": "Hostname verified: {hostname} (domain: {domain})",
    "hostname_set_fail": "Failed to set hostname: {error}",
    "hostname_invalid": "Hostname is invalid or missing domain",
    "hostname_not_configured": "Hostname not configured in user_config.yml",

    # Error instructions for Hostname
    "hostname_instruction": """
ACTION REQUIRED: Configure hostname in user_config.yml.
- Set 'oim_hostname' to a valid FQDN (e.g., "oim.omnia.test")
- The hostname MUST include a domain (hostname.domain.tld)
- Example: oim_hostname: "oim.omnia.test"
""",
    "hostname_manual_instruction": """
ACTION REQUIRED: Manually set hostname.
- Run: hostnamectl set-hostname {hostname}
- Verify: hostname -f
- Error: {error}
""",

    # ==========================================================================
    # OS Validation
    # ==========================================================================
    "os_check_start": "Checking OS compatibility...",
    "os_check_pass": "OS validation passed: {os_name} {os_version}",
    "os_check_fail": "OS validation FAILED: {os_name} {os_version} is not supported",
    "os_not_detected": "Could not detect OS information",

    # Error instructions for OS
    "os_error_instruction": """
ACTION REQUIRED: Install a supported operating system.
- Supported OS: Red Hat Enterprise Linux (RHEL) 10
- Current OS: {os_name} {os_version}
- Please reinstall with RHEL 10 before proceeding.
""",

    # ==========================================================================
    # Hardware Validation
    # ==========================================================================
    "hw_check_start": "Checking hardware inventory...",
    "hw_cores_pass": "CPU cores validation passed: {cores} cores",
    "hw_cores_fail": "CPU cores validation FAILED: {cores} cores (minimum: {min_cores})",
    "hw_memory_pass": "Memory validation passed: {memory_gb} GB",
    "hw_memory_fail": "Memory validation FAILED: {memory_gb} GB (minimum: {min_memory_gb} GB)",
    "hw_disk_pass": "Disk validation passed: {disk_gb} GB",
    "hw_disk_fail": "Disk validation FAILED: {disk_gb} GB (minimum: {min_disk_gb} GB)",
    "hw_dimms_info": "DIMM slots: {dimm_count}",

    # Error instructions for Hardware
    "hw_error_instruction": """
ACTION REQUIRED: Upgrade hardware to meet minimum requirements.
- Minimum CPU cores: {min_cores} (Current: {cores})
- Minimum Memory: {min_memory_gb} GB (Current: {memory_gb} GB)
- Minimum Disk: {min_disk_gb} GB (Current: {disk_gb} GB)
- Or adjust requirements in {config_path} if this is intentional.
""",

    # ==========================================================================
    # IPMI
    # ==========================================================================
    "ipmi_check_start": "Checking IPMI tool...",
    "ipmi_installed": "IPMI tool installed: {version}",
    "ipmi_not_installed": "IPMI tool not installed, attempting installation...",
    "ipmi_install_success": "IPMI tool installed successfully",
    "ipmi_install_fail": "IPMI tool installation FAILED: {error}",

    # Error instructions for IPMI
    "ipmi_error_instruction": """
ACTION REQUIRED: Install IPMI tool manually.
- Run: sudo dnf install -y ipmitool
- Or check if RHEL repositories are configured correctly.
- Error: {error}
""",

    # ==========================================================================
    # Network Interfaces
    # ==========================================================================
    "iface_check_start": "Checking network interfaces...",
    "iface_check_pass": "Network interfaces validation passed: {count} interfaces found",
    "iface_check_fail": "Network interfaces validation FAILED",
    "iface_pxe_found": "PXE interface found and UP: {interface}",
    "iface_pxe_not_found": "PXE interface NOT FOUND: {interface}",
    "iface_pxe_down": "PXE interface is DOWN: {interface}",
    "iface_public_found": "Public interface found and UP: {interface}",
    "iface_public_not_found": "Public interface NOT FOUND: {interface}",
    "iface_public_down": "Public interface is DOWN: {interface}",
    "iface_not_configured": "Interface name not configured",

    # Error instructions for Network Interfaces
    "iface_pxe_not_found_instruction": """
ACTION REQUIRED: PXE interface '{interface}' does not exist.
- Check the interface name: ip link show
- Update 'pxe_interface' in {config_path} with correct interface name.
- Available interfaces can be found with: ls /sys/class/net/
""",
    "iface_pxe_down_instruction": """
ACTION REQUIRED: PXE interface '{interface}' is DOWN.
- Bring interface up: sudo ip link set {interface} up
- Check cable connection to the PXE network.
- Verify network configuration: nmcli device status
""",
    "iface_public_not_found_instruction": """
ACTION REQUIRED: Public interface '{interface}' does not exist.
- Check the interface name: ip link show
- Update 'public_interface' in {config_path} with correct interface name.
- Available interfaces can be found with: ls /sys/class/net/
""",
    "iface_public_down_instruction": """
ACTION REQUIRED: Public interface '{interface}' is DOWN.
- Bring interface up: sudo ip link set {interface} up
- Check cable connection to the public network.
- Verify network configuration: nmcli device status
""",

    # ==========================================================================
    # PXE NIC Configuration
    # ==========================================================================
    "pxe_nic_check_start": "Checking PXE NIC IP configuration...",
    "pxe_nic_already_configured": "PXE NIC {interface} already configured with IP: {ip}",
    "pxe_nic_configured": "PXE NIC {interface} configured with IP: {ip}",
    "pxe_nic_config_fail": "PXE NIC configuration FAILED: {error}",
    "pxe_nic_force_reconfig": "Force reconfigure enabled, removing existing IP...",

    # Error instructions for PXE NIC Configuration
    "pxe_nic_config_instruction": """
ACTION REQUIRED: Failed to configure PXE NIC IP.
- Check if you have root/sudo privileges.
- Manually configure: sudo ip addr add {ip} dev {interface}
- Or set 'pxe_ip' in {config_path} and re-run.
- Error: {error}
""",

    # ==========================================================================
    # NFS
    # ==========================================================================
    "nfs_check_start": "Checking NFS connectivity...",
    "nfs_reachable": "NFS server reachable: {server}",
    "nfs_not_reachable": "NFS server NOT reachable: {server}",
    "nfs_capacity_pass": "NFS capacity validation passed: {capacity_gb} GB",
    "nfs_capacity_fail": "NFS capacity INSUFFICIENT: {capacity_gb} GB (min: {min_capacity_gb} GB)",
    "nfs_not_configured": "NFS server IP not configured",

    # Error instructions for NFS
    "nfs_not_reachable_instruction": """
ACTION REQUIRED: Cannot reach NFS server '{server}'.
- Check if NFS server is running and accessible.
- Verify network connectivity: ping {server}
- Check firewall rules on both server and client.
- Verify 'nfs_server_ip' in {config_path} is correct.
""",
    "nfs_capacity_instruction": """
ACTION REQUIRED: NFS storage capacity is insufficient.
- Available: {capacity_gb} GB
- Required: {min_capacity_gb} GB
- Either increase NFS storage capacity, or
- Reduce 'nfs_min_capacity_gb' in {config_path} if this is acceptable.
""",
    "nfs_mount_fail_instruction": """
ACTION REQUIRED: Cannot mount NFS share.
- Error: {error}
- Check if NFS share is exported: showmount -e {server}
- Verify share path '{share_path}' is correct in {config_path}.
- Check NFS client is installed: rpm -q nfs-utils
- Install if missing: sudo dnf install -y nfs-utils
""",
    "nfs_not_configured_instruction": """
ACTION REQUIRED: NFS server not configured.
- Set 'nfs_server_ip' in {config_path} with your NFS server IP.
- Set 'nfs_share_path' with the NFS export path.
""",

    # ==========================================================================
    # Internet
    # ==========================================================================
    "internet_check_start": "Checking internet connectivity via public interface...",
    "internet_available": "Internet connectivity available via {interface}",
    "internet_not_available": "Internet connectivity NOT available via {interface}",
    "internet_ping_success": "Ping to {host} successful via {interface}",
    "internet_ping_fail": "Ping to {host} FAILED via {interface}",
    "internet_no_public_interface": "Public interface not configured",

    # Error instructions for Internet
    "internet_fail_instruction": """
ACTION REQUIRED: No internet connectivity via '{interface}'.
- Check if interface has an IP: ip addr show {interface}
- Check default gateway: ip route show
- Verify DNS configuration: cat /etc/resolv.conf
- Test connectivity: ping -I {interface} 8.8.8.8
- Check firewall rules: firewall-cmd --list-all
""",

    # ==========================================================================
    # RHEL Repo
    # ==========================================================================
    "repo_check_start": "Checking RHEL repositories...",
    "repo_found": "RHEL repository found: {repo}",
    "repo_not_found": "No RHEL repository configured",

    # Error instructions for RHEL Repo
    "repo_not_found_instruction": """
ACTION REQUIRED: No RHEL repository found.
- Register system with Red Hat: sudo subscription-manager register
- Attach subscription: sudo subscription-manager attach --auto
- Enable repos: sudo subscription-manager repos --enable=rhel-10-for-x86_64-baseos-rpms
- Or configure local repository if using offline installation.
""",

    # ==========================================================================
    # Git
    # ==========================================================================
    "git_check_start": "Checking Git installation...",
    "git_installed": "Git installed: version {version}",
    "git_not_installed": "Git not installed, attempting installation from RHEL repo...",
    "git_install_success": "Git installed successfully from RHEL repo",
    "git_install_fail": "Git installation FAILED: {error}",
    "git_repo_not_found": "No RHEL repository found to install Git",

    # Error instructions for Git
    "git_install_instruction": """
ACTION REQUIRED: Failed to install Git.
- Ensure RHEL repositories are configured.
- Install manually: sudo dnf install -y git
- Error: {error}
""",

    # ==========================================================================
    # Podman
    # ==========================================================================
    "podman_check_start": "Checking Podman installation...",
    "podman_installed": "Podman installed: {version}",
    "podman_not_installed": "Podman NOT installed",
    "podman_version_ok": "Podman version {version} >= {min_version}",
    "podman_version_pass": "Podman version OK: {version}",
    "podman_version_fail": "Podman version {version} is BELOW minimum {min_version}",
    "podman_version_low": "Podman version {version} is BELOW minimum {min_version}",

    # Error instructions for Podman
    "podman_not_installed_instruction": """
ACTION REQUIRED: Podman is not installed.
- Install Podman: sudo dnf install -y podman
- Verify installation: podman --version
""",
    "podman_version_instruction": """
ACTION REQUIRED: Podman version is too old.
- Current version: {version}
- Minimum required: {min_version}
- Upgrade Podman: sudo dnf update -y podman
- Or adjust 'podman_min_version' in {config_path} if acceptable.
""",

    # ==========================================================================
    # Omnia Repository
    # ==========================================================================
    "omnia_clone_start": "Cloning Omnia repository...",
    "omnia_clone_success": "Omnia repository cloned/updated successfully",
    "omnia_clone_fail": "Omnia repository clone FAILED: {error}",
    "omnia_repo_not_configured": "Omnia repository URL not configured",

    # Error instructions for Omnia Repository
    "omnia_clone_instruction": """
ACTION REQUIRED: Failed to clone Omnia repository.
- Check internet connectivity.
- Verify Git is installed: git --version
- Check repository URL in {config_path}.
- Try manually: git clone {repo_url} {clone_path}
- Error: {error}
""",
    "omnia_repo_not_configured_instruction": """
ACTION REQUIRED: Omnia repository not configured.
- Set 'omnia_repo_url' in {config_path} (default: https://github.com/dell/omnia.git)
- Set 'omnia_branch' (default: main)
- Set 'omnia_clone_path' (default: /opt/omnia)
""",

    # ==========================================================================
    # Container Build
    # ==========================================================================
    "container_build_start": "Building container images...",
    "container_build_success": "Container images built successfully: {images}",
    "container_build_fail": "Container build FAILED: {error}",
    "container_build_skipped": "Skipped (reconfigure_images: false)",

    # Error instructions for Container Build
    "container_build_instruction": """
ACTION REQUIRED: Container build failed.
- Command: ./build_images.sh {images} omnia_branch={omnia_branch}
- Exit code: {exit_code}
- Check the output above for errors.
- Check if Podman is running correctly.
- Verify network connectivity for pulling base images.
""",
    "container_images_not_configured": """
ACTION REQUIRED: Set 'container_images' in {config_path}.
- Specify comma-separated container images to build.
- Example: container_images: "core" or container_images: "core,auth"
""",
    "omnia_branch_not_configured": """
ACTION REQUIRED: Set 'omnia_branch' in {config_path}.
- This specifies which Omnia branch to use for container build.
- Example: omnia_branch: "main" or omnia_branch: "release-1.6"
""",
    "build_script_not_found": """
ACTION REQUIRED: Script not found at {script_path}.
- Check if repository was cloned correctly.
- Verify the artifactory_branch contains build_images.sh.
""",
    "clone_path_not_found": """
ACTION REQUIRED: Directory {clone_path} does not exist.
- Run the Omnia Artifactory check first to clone the repository.
- Or set 'omnia_clone_path' in {config_path} if using a different path.
""",

    # ==========================================================================
    # Download omnia.sh
    # ==========================================================================
    "omnia_sh_download_start": "Downloading omnia.sh...",
    "omnia_sh_download_success": "omnia.sh downloaded from {ref_type}: {omnia_branch}",
    "omnia_sh_download_fail": "Failed to download omnia.sh",

    # Error instructions for Download omnia.sh
    "omnia_sh_download_instruction": """
ACTION REQUIRED: Could not download omnia.sh from '{omnia_branch}'.
- Tried branch URL: {branch_url}
- Tried tag URL: {tag_url}
- Both failed. Check if '{omnia_branch}' is a valid branch or tag in the Omnia repository.
- Verify network connectivity and URL accessibility.
""",
    "omnia_sh_branch_not_configured": """
ACTION REQUIRED: Set 'omnia_branch' in {config_path}.
- This specifies which Omnia branch/tag to download omnia.sh from.
- Example: omnia_branch: "main" or omnia_branch: "v1.6.0"
""",
    "omnia_sh_dir_create_fail": "Failed to create directory {clone_path}",

    # ==========================================================================
    # SSH Connection
    # ==========================================================================
    "ssh_connection_ok": "SSH connection OK",
    "ssh_connection_fail": "SSH connection FAILED: {error}",
    "ssh_connection_test_start": "Testing SSH connection to {user}@{server}...",
    "ssh_connection_success": "SSH connection to {user}@{server} successful",
    "ssh_connection_failed": "SSH connection failed to {user}@{server}",
    "ssh_connection_error": "Connection error: {error}",
    "ssh_running_locally": "Running locally",
    "oim_server_not_configured": "OIM server IP not configured",
    "oim_server_not_configured_details": ("Configuration missing: oim_server_ip is required "
                                          "for remote execution"),
    "ssh_password_not_configured": "SSH password not configured",
    "ssh_password_not_configured_details": ("Configuration missing: oim_ssh_password is required "
                                            "for remote execution"),
    "ssh_check_config": ("Check oim_server_ip, oim_ssh_user, and oim_ssh_password "
                         "in {config_path}"),

    # ==========================================================================
    # Network Configuration
    # ==========================================================================
    "pxe_interface_not_configured": "PXE interface not configured",
    "pxe_interface_not_configured_details": ("Configuration missing: pxe_interface is required "
                                             "for network setup"),
    "pxe_interface_not_exist": "PXE interface {interface} does not exist on target server",
    "pxe_interface_not_exist_details": ("Interface {interface} not found - verify interface name "
                                        "or check available interfaces"),
    "ip_validation_failed": "IP configuration validation failed: {message}",
    "ip_conflict_detected": "PXE IP and iDRAC IP cannot be the same: {ip}",
    "ip_format_invalid": "Invalid IP format: {error}",
    "ip_configuration_valid": "IP configuration is valid",
    "network_type_lom": "lom",
    "network_type_dedicated": "dedicated",
    "pxe_nic_force_reconfigure": "Force reconfigure enabled. Removing ALL IPs from {interface}...",
    "pxe_nic_no_ips_found": "No IPs found on {interface}",
    "pxe_nic_ips_removed": "All IPs successfully removed from {interface}",
    "pxe_nic_configuring_lom": ("Configuring LOM network: PXE IP {pxe_ip} and iDRAC IP {idrac_ip} "
                                "on {interface}..."),
    "pxe_nic_configuring_dedicated": ("Configuring dedicated network: PXE IP {pxe_ip} "
                                      "on {interface}..."),
    "pxe_nic_lom_configured": "LOM network configured on {interface}",
    "pxe_nic_dedicated_configured": "Dedicated network configured on {interface}",
    "pxe_nic_lom_success": "LOM network configured successfully with IPs: {ips}",
    "pxe_nic_dedicated_success": "Dedicated network configured successfully with IP: {ip}",
    "interface_state_check": "Interface {interface} initial state: {state}",
    "interface_bring_up": "Bringing interface {interface} UP...",
    "interface_bring_up_warning": "Warning: Could not bring interface up initially: {error}",
    "interface_final_state": "Interface {interface} final state: {state}",
    "interface_not_up_warning": ("Warning: Interface {interface} is not UP "
                                 "after configuration"),

    # ==========================================================================
    # General
    # ==========================================================================
    "validation_start": "Starting OIM prerequisite validation...",
    "validation_complete": "OIM prerequisite validation complete",
    "validation_passed": "All prerequisite checks passed",
    "validation_failed": ("Prerequisite validation failed: {failed_count} "
                          "checks failed"),
}
