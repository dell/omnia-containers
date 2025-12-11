"""
Omnia.sh - Messages and Test Variables.

This module contains all messages, status strings, error instructions,
and test variables for the omnia.sh automation.
"""

from typing import Dict
from automation_library.vars.omnia_sh_vars import OMNIA_SH_VARS
from automation_library.vars.oim_prereq_vars import OIM_PREREQ_VARS

# =============================================================================
# TEST VARIABLES (for molecule/pytest tests)
# =============================================================================

TEST_VARS = {
    "container_file": "/etc/containers/systemd/omnia_core.container",
    "service_name": f"{OMNIA_SH_VARS['container_name']}.service",
    "metadata_file": f"{OMNIA_SH_VARS['omnia_shared_path']}/omnia/.data/oim_metadata.yml",
    "ssh_alias": OMNIA_SH_VARS["container_name"],
    "oim_server_ip": OIM_PREREQ_VARS.get("oim_server_ip", ""),
    "ssh_timeout": 5,
}

# Test names (displayed in test output header)
TEST_NAMES = {
    "container_file": "Verify omnia_core.container file exists",
    "service_running": "Verify omnia_core service is running",
    "metadata_file": "Verify oim_metadata.yml file exists",
    "ssh_to_container": "Verify passwordless SSH: OIM server → omnia_core",
    "ssh_from_container": "Verify passwordless SSH: omnia_core → OIM server",
}

# Test log messages
TEST_LOG_MSGS = {
    "file_exists": "File exists",
    "file_not_found": "File NOT found",
    "service_active": "Service is active",
    "service_inactive": "Service is {status}",
    "ssh_success": "Passwordless SSH successful",
    "ssh_failed": "Passwordless SSH FAILED",
}

# Test assert messages
TEST_ASSERT_MSGS = {
    "file_not_found": "File not found: {path}",
    "service_not_active": "Expected 'active', got '{status}'",
    "ssh_failed": "SSH failed: {error}",
    "config_missing": "oim_server_ip not configured",
}

# =============================================================================
# FUNCTION MESSAGES (for omnia_sh_func.py)
# =============================================================================

OMNIA_SH_MSGS: Dict[str, str] = {
    
    # =========================================================================
    # CONFIGURATION VALIDATION
    # =========================================================================
    "config_valid": "Configuration validation passed",
    "config_invalid": "Configuration validation failed",
    "config_error": "Configuration error: {error}",
    
    # =========================================================================
    # PREREQUISITES
    # =========================================================================
    "prereq_check_start": "Checking prerequisites for omnia.sh...",
    "prereq_check_pass": "All prerequisites met",
    "prereq_check_fail": "Prerequisites check failed",
    
    "podman_installed": "Podman is installed: {version}",
    "podman_not_installed": "Podman is NOT installed",
    "podman_install_instruction": """
ACTION REQUIRED: Install Podman.
- Run: sudo dnf install -y podman
- Verify: podman --version
""",
    
    "hostname_valid": "Hostname is valid: {hostname}",
    "hostname_invalid": "Hostname is invalid or not configured with domain",
    "hostname_instruction": """
ACTION REQUIRED: Configure hostname with domain.
- Set hostname: hostnamectl set-hostname <hostname>.<domain>
- Example: hostnamectl set-hostname oim.example.com
""",
    
    "image_found": "Omnia core image found: {image}:{tag}",
    "image_not_found": "Omnia core image not found locally",
    "image_pull_start": "Pulling omnia_core image from Docker Hub...",
    "image_pull_success": "Successfully pulled omnia_core image",
    "image_pull_fail": "Failed to pull omnia_core image",
    "image_build_instruction": """
ACTION REQUIRED: Build omnia_core image locally.
- Clone: git clone https://github.com/dell/omnia-artifactory -b omnia-container
- Build: cd omnia-artifactory && ./build_images.sh core omnia_branch=<branch>
""",
    
    # =========================================================================
    # OMNIA.SH EXECUTION
    # =========================================================================
    "omnia_sh_found": "omnia.sh script found at: {path}",
    "omnia_sh_not_found": "omnia.sh script NOT found at: {path}",
    "omnia_sh_not_found_instruction": """
ACTION REQUIRED: Download omnia.sh script.
- Ensure omnia.sh is present in the expected location.
- Or run the OIM prereq check to download it.
""",
    
    "install_start": "Starting omnia.sh --install...",
    "install_success": "omnia.sh --install completed successfully",
    "install_fail": "omnia.sh --install failed",
    "install_timeout": "omnia.sh --install timed out after {timeout} seconds",
    "install_instruction": """
ACTION REQUIRED: omnia.sh installation failed.
- Check the output above for errors.
- Verify all prerequisites are met.
- Check if shared path exists and is writable.
- Error: {error}
""",
    
    "uninstall_start": "Starting omnia.sh --uninstall...",
    "uninstall_success": "omnia.sh --uninstall completed successfully",
    "uninstall_fail": "omnia.sh --uninstall failed",
    
    # =========================================================================
    # CONTAINER VERIFICATION
    # =========================================================================
    "container_check_start": "Checking omnia_core container status...",
    "container_running": "Container {container_name} is running",
    "container_not_running": "Container {container_name} is NOT running",
    "container_not_found": "Container {container_name} not found",
    "container_instruction": """
ACTION REQUIRED: Container is not running.
- Check container logs: podman logs {container_name}
- Check systemd service: systemctl status {container_name}.service
- Try restarting: systemctl restart {container_name}.service
""",
    
    "container_wait_start": "Waiting for container to start (timeout: {timeout}s)...",
    "container_wait_success": "Container started successfully",
    "container_wait_timeout": "Container did not start within {timeout} seconds",
    
    # =========================================================================
    # SSH VERIFICATION
    # =========================================================================
    "ssh_check_start": "Checking SSH connectivity to omnia_core...",
    "ssh_check_pass": "SSH connection to omnia_core successful",
    "ssh_check_fail": "SSH connection to omnia_core failed",
    "ssh_instruction": """
ACTION REQUIRED: SSH connection failed.
- Check if container is running: podman ps | grep omnia_core
- Check SSH port: ss -tlnp | grep {ssh_port}
- Check SSH config: cat ~/.ssh/config | grep omnia_core
- Try manual SSH: ssh -p {ssh_port} root@localhost
""",
    
    # =========================================================================
    # DIRECTORY VERIFICATION
    # =========================================================================
    "dir_check_start": "Checking required directories...",
    "dir_exists": "Directory exists: {path}",
    "dir_not_exists": "Directory NOT found: {path}",
    "dir_instruction": """
ACTION REQUIRED: Required directory not found.
- Expected path: {path}
- Check if omnia.sh completed successfully.
- Check shared path permissions.
""",
    
    # =========================================================================
    # CLEANUP
    # =========================================================================
    "cleanup_start": "Starting cleanup...",
    "cleanup_success": "Cleanup completed successfully",
    "cleanup_fail": "Cleanup failed: {error}",
    "cleanup_skip": "Skipping cleanup (cleanup_after_test: false)",
    
    # =========================================================================
    # TEST RESULTS
    # =========================================================================
    "test_start": "Starting omnia.sh test...",
    "test_pass": "All omnia.sh tests PASSED",
    "test_fail": "omnia.sh tests FAILED: {failed_count} test(s) failed",
    "test_summary": """
Test Summary:
- Total: {total}
- Passed: {passed}
- Failed: {failed}
""",
}
