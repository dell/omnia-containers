"""
Messages for local_repo validation.

Contains all user-facing messages, error descriptions, and assertion messages
for the local_repo validation workflow.
"""

LOCAL_REPO_MSGS = {
    # ==========================================================================
    # Pulp Container Messages
    # ==========================================================================
    "pulp_check_start": "Checking Pulp container status...",
    "pulp_container_running": "Pulp container is running without errors",
    "pulp_container_not_running": "Pulp container is NOT running",
    "pulp_container_not_found": "Pulp container not found",
    "pulp_container_unhealthy": "Pulp container is unhealthy: {status}",
    "pulp_container_errors": "Pulp container has errors in logs",
    "pulp_validation_pass": "Pulp container validation PASSED",
    "pulp_validation_fail": "Pulp container validation FAILED",

    "pulp_not_running_instruction": """
ACTION REQUIRED: Pulp container is not running.
- Start the container: {runtime} start {container}
- Check container status: {runtime} ps -a | grep pulp
- View container logs: {runtime} logs {container}
""",
    "pulp_not_found_instruction": """
ACTION REQUIRED: Pulp container does not exist.
- Verify local_repo playbook has been executed
- Check container list: {runtime} ps -a
- Re-run local_repo playbook if needed
""",
    "pulp_unhealthy_instruction": """
ACTION REQUIRED: Pulp container is unhealthy.
- Check container health: {runtime} inspect {container}
- View container logs: {runtime} logs {container}
- Restart container: {runtime} restart {container}
""",
    "pulp_errors_instruction": """
ACTION REQUIRED: Pulp container has errors.
- View recent logs: {runtime} logs --tail 100 {container}
- Check for configuration issues
- Restart container: {runtime} restart {container}
""",

    # ==========================================================================
    # Custom Repo Accessibility Messages
    # ==========================================================================
    "repo_access_check_start": "Checking custom repo accessibility from OIM...",
    "repo_accessible": "Custom repo is accessible at {url}",
    "repo_not_accessible": "Custom repo is NOT accessible at {url}",
    "repo_api_success": "Pulp API responding at {endpoint}",
    "repo_api_fail": "Pulp API not responding at {endpoint}: {error}",
    "repo_access_validation_pass": "Custom repo accessibility validation PASSED",
    "repo_access_validation_fail": "Custom repo accessibility validation FAILED",

    "repo_not_accessible_instruction": """
ACTION REQUIRED: Custom repo is not accessible.
- URL: {url}
- Verify Pulp container is running
- Check network connectivity
- Verify firewall rules allow access
- Test manually: curl -s {url}
""",

    # ==========================================================================
    # local_repo Playbook Messages
    # ==========================================================================
    "playbook_start": "Starting local_repo playbook execution...",
    "playbook_success": "local_repo playbook completed successfully",
    "playbook_fail": "local_repo playbook execution FAILED: {error}",
    "playbook_timeout": "local_repo playbook execution timed out after {timeout}s",
    "playbook_not_found": "local_repo playbook not found at {path}",

    "playbook_fail_instruction": """
ACTION REQUIRED: local_repo playbook failed.
- Check playbook logs for details
- Verify inventory file exists at {inventory}
- Run manually inside omnia_core:
  ansible-playbook -i {inventory} {playbook}
- Error: {error}
""",
    "playbook_not_found_instruction": """
ACTION REQUIRED: local_repo playbook not found.
- Expected path: {path}
- Verify Omnia installation is complete
- Check if playbook exists inside omnia_core container
""",

    # ==========================================================================
    # Pulp Command Validation Messages
    # ==========================================================================
    "pulp_cmd_check_start": "Validating Pulp commands...",
    "pulp_cmd_success": "Pulp command succeeded: {command}",
    "pulp_cmd_fail": "Pulp command failed: {command}",
    "pulp_cmd_output": "Command output: {output}",
    "pulp_cmd_validation_pass": "Pulp command validation PASSED",
    "pulp_cmd_validation_fail": "Pulp command validation FAILED",

    "pulp_cmd_fail_instruction": """
ACTION REQUIRED: Pulp command failed.
- Command: {command}
- Error: {error}
- Verify Pulp container is running and healthy
- Check Pulp CLI configuration
- Run manually: {runtime} exec {container} {command}
""",

    # ==========================================================================
    # Package Download Status Messages
    # ==========================================================================
    "status_check_start": "Checking package download status...",
    "status_file_found": "Status file found: {path}",
    "status_file_not_found": "Status file NOT found: {path}",
    "status_all_success": "All packages downloaded successfully ({count} packages)",
    "status_some_failed": "{failed_count} package(s) failed to download",
    "status_parse_error": "Failed to parse status file: {error}",
    "status_validation_pass": "Package download validation PASSED",
    "status_validation_fail": "Package download validation FAILED",

    "status_file_not_found_instruction": """
ACTION REQUIRED: Status file not found.
- Expected path: {path}
- Verify local_repo playbook completed successfully
- Check if offline download was executed
""",
    "status_failed_packages_instruction": """
ACTION REQUIRED: Some packages failed to download.
- Failed packages: {packages}
- Check individual package status files in: {status_dir}
- Verify network connectivity
- Re-run local_repo playbook to retry failed downloads
""",

    # ==========================================================================
    # Package Status File Messages
    # ==========================================================================
    "package_status_check_start": "Checking individual package status files...",
    "package_status_success": "Package '{package}' downloaded successfully",
    "package_status_failed": "Package '{package}' download FAILED",
    "package_status_file_found": "Package status file found: {path}",
    "package_status_file_not_found": "Package status file not found: {path}",

    "package_failed_instruction": """
ACTION REQUIRED: Package download failed.
- Package: {package}
- Status file: {status_file}
- Check package availability in source repository
- Verify network connectivity
- Re-run local_repo playbook
""",

    # ==========================================================================
    # Container Runtime Messages
    # ==========================================================================
    "runtime_check_start": "Checking container runtime...",
    "runtime_found": "Container runtime found: {runtime}",
    "runtime_not_found": "No container runtime (podman/docker) found",

    "runtime_not_found_instruction": """
ACTION REQUIRED: No container runtime found.
- Install podman: dnf install -y podman
- Or install docker: dnf install -y docker-ce
- Verify installation: podman --version or docker --version
""",

    # ==========================================================================
    # General Validation Messages
    # ==========================================================================
    "validation_start": "Starting local_repo validation...",
    "validation_complete": "local_repo validation complete",
    "validation_all_passed": "All validations PASSED",
    "validation_some_failed": "Validation completed with {failed_count} failures",

    # ==========================================================================
    # Air-gap Image Registry Validation Messages
    # ==========================================================================
    "airgap_check_start": "Checking air-gap image registry configuration...",
    "airgap_check_skip": "Air-gap validation skipped (airgap_enabled=false)",
    "airgap_json_found": "JSON config file found: {path}",
    "airgap_json_not_found": "JSON config file NOT found: {path}",
    "airgap_images_valid": "All images in '{file}' point to local registry",
    "airgap_images_invalid": "Found {count} image(s) with external registry in '{file}'",
    "airgap_external_image": "External image found: {image}",
    "airgap_local_registry_ok": "Local registry is accessible at {registry}",
    "airgap_local_registry_fail": "Local registry NOT accessible at {registry}",
    "airgap_validation_pass": "Air-gap image registry validation PASSED",
    "airgap_validation_fail": "Air-gap image registry validation FAILED",

    "airgap_invalid_instruction": """
ACTION REQUIRED: JSON config files contain external registry references.
- For air-gapped environments, images must point to local registry
- External images found: {images}
- Expected registry prefix: {local_registry}
- Modify JSON files to use local registry or tar file references
- Re-run local_repo playbook after modifications
""",

    # ==========================================================================
    # Assertion Messages (for pytest)
    # ==========================================================================
    "assert_container_runtime": "Container runtime ({runtime}) must be available",
    "assert_pulp_container_exists": "Pulp container must exist",
    "assert_pulp_container_running": "Pulp container must be running",
    "assert_pulp_container_healthy": "Pulp container must be healthy",
    "assert_pulp_no_errors": "Pulp container must have no errors in logs",
    "assert_repo_accessible": "Custom repo must be accessible from OIM",
    "assert_pulp_api_responding": "Pulp API must be responding",
    "assert_pulp_cmd_success": "Pulp command '{command}' must succeed",
    "assert_status_file_exists": "Status file must exist at {path}",
    "assert_all_packages_success": "All packages must be downloaded successfully",
    "assert_playbook_success": "local_repo playbook must complete successfully",
    "assert_airgap_images": "All images must point to local registry in air-gapped mode",
}
