"""Messages for OIM prerequisite checks with user-friendly error instructions."""

OIM_PREREQ_MSGS = {
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
- Or adjust requirements in user_config.yml if this is intentional.
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
    "iface_not_configured": "Interface name not configured in user_config.yml",
    
    # Error instructions for Network Interfaces
    "iface_pxe_not_found_instruction": """
ACTION REQUIRED: PXE interface '{interface}' does not exist.
- Check the interface name: ip link show
- Update 'pxe_interface' in user_config.yml with correct interface name.
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
- Update 'public_interface' in user_config.yml with correct interface name.
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
- Or set 'pxe_ip' in user_config.yml and re-run.
- Error: {error}
""",

    # ==========================================================================
    # NFS
    # ==========================================================================
    "nfs_check_start": "Checking NFS connectivity...",
    "nfs_reachable": "NFS server reachable: {server}",
    "nfs_not_reachable": "NFS server NOT reachable: {server}",
    "nfs_capacity_pass": "NFS capacity validation passed: {capacity_gb} GB",
    "nfs_capacity_fail": "NFS capacity INSUFFICIENT: {capacity_gb} GB (minimum: {min_capacity_gb} GB)",
    "nfs_not_configured": "NFS server IP not configured in user_config.yml",
    
    # Error instructions for NFS
    "nfs_not_reachable_instruction": """
ACTION REQUIRED: Cannot reach NFS server '{server}'.
- Check if NFS server is running and accessible.
- Verify network connectivity: ping {server}
- Check firewall rules on both server and client.
- Verify 'nfs_server_ip' in user_config.yml is correct.
""",
    "nfs_capacity_instruction": """
ACTION REQUIRED: NFS storage capacity is insufficient.
- Available: {capacity_gb} GB
- Required: {min_capacity_gb} GB
- Either increase NFS storage capacity, or
- Reduce 'nfs_min_capacity_gb' in user_config.yml if this is acceptable.
""",
    "nfs_mount_fail_instruction": """
ACTION REQUIRED: Cannot mount NFS share.
- Error: {error}
- Check if NFS share is exported: showmount -e {server}
- Verify share path '{share_path}' is correct in user_config.yml.
- Check NFS client is installed: rpm -q nfs-utils
- Install if missing: sudo dnf install -y nfs-utils
""",
    "nfs_not_configured_instruction": """
ACTION REQUIRED: NFS server not configured.
- Set 'nfs_server_ip' in user_config.yml with your NFS server IP.
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
    "internet_no_public_interface": "Public interface not configured in user_config.yml",
    
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
    "podman_version_pass": "Podman version OK: {version}",
    "podman_version_fail": "Podman version {version} is BELOW minimum {min_version}",
    
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
- Or adjust 'podman_min_version' in user_config.yml if acceptable.
""",

    # ==========================================================================
    # Omnia Repository
    # ==========================================================================
    "omnia_clone_start": "Cloning Omnia repository...",
    "omnia_clone_success": "Omnia repository cloned/updated successfully",
    "omnia_clone_fail": "Omnia repository clone FAILED: {error}",
    "omnia_repo_not_configured": "Omnia repository URL not configured in user_config.yml",
    
    # Error instructions for Omnia Repository
    "omnia_clone_instruction": """
ACTION REQUIRED: Failed to clone Omnia repository.
- Check internet connectivity.
- Verify Git is installed: git --version
- Check repository URL in user_config.yml.
- Try manually: git clone {repo_url} {clone_path}
- Error: {error}
""",
    "omnia_repo_not_configured_instruction": """
ACTION REQUIRED: Omnia repository not configured.
- Set 'omnia_repo_url' in user_config.yml (default: https://github.com/dell/omnia.git)
- Set 'omnia_branch' (default: main)
- Set 'omnia_clone_path' (default: /opt/omnia)
""",

    # ==========================================================================
    # General
    # ==========================================================================
    "validation_start": "Starting OIM prerequisite validation...",
    "validation_complete": "OIM prerequisite validation complete",
    "validation_passed": "All prerequisite checks passed",
    "validation_failed": "Prerequisite validation failed: {failed_count} checks failed",
}
