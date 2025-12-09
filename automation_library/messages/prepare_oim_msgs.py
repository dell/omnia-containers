"""
Messages for prepare_oim validation.

Contains all user-facing messages, error descriptions, and assertion messages
for the prepare_oim validation workflow.
"""

PREPARE_OIM_MSGS = {
    # ==========================================================================
    # SSH Connection Messages
    # ==========================================================================
    "ssh_connect_start": "Connecting to OIM server {server}...",
    "ssh_connect_success": "Successfully connected to OIM server {server}",
    "ssh_connect_fail": "Failed to connect to OIM server {server}: {error}",
    "ssh_connect_instruction": """
ACTION REQUIRED: Cannot connect to OIM server.
- Verify OIM server IP '{server}' is correct in user_config.yml
- Check SSH credentials (oim_ssh_user, oim_ssh_password)
- Ensure SSH service is running on the server
- Test manually: ssh {user}@{server}
- Error: {error}
""",

    # ==========================================================================
    # omnia_core Container Messages
    # ==========================================================================
    "omnia_core_check_start": "Checking omnia_core container status...",
    "omnia_core_running": "omnia_core container is running",
    "omnia_core_not_running": "omnia_core container is NOT running",
    "omnia_core_not_found": "omnia_core container not found",
    "omnia_core_exec_start": "Executing command in omnia_core container...",
    "omnia_core_exec_success": "Command executed successfully in omnia_core",
    "omnia_core_exec_fail": "Failed to execute command in omnia_core: {error}",
    
    "omnia_core_not_running_instruction": """
ACTION REQUIRED: omnia_core container is not running.
- Start the container: {runtime} start omnia_core
- Check container status: {runtime} ps -a | grep omnia_core
- View container logs: {runtime} logs omnia_core
""",
    "omnia_core_not_found_instruction": """
ACTION REQUIRED: omnia_core container does not exist.
- Verify Omnia installation is complete
- Check container list: {runtime} ps -a
- Re-run Omnia deployment if needed
""",

    # ==========================================================================
    # prepare_oim Playbook Messages
    # ==========================================================================
    "playbook_start": "Starting prepare_oim playbook execution...",
    "playbook_success": "prepare_oim playbook completed successfully",
    "playbook_fail": "prepare_oim playbook execution FAILED: {error}",
    "playbook_timeout": "prepare_oim playbook execution timed out after {timeout}s",
    "playbook_not_found": "prepare_oim playbook not found at {path}",
    
    "playbook_fail_instruction": """
ACTION REQUIRED: prepare_oim playbook failed.
- Check playbook logs for details
- Verify inventory file exists at {inventory}
- Run manually inside omnia_core:
  ansible-playbook -i {inventory} {playbook}
- Error: {error}
""",
    "playbook_not_found_instruction": """
ACTION REQUIRED: prepare_oim playbook not found.
- Expected path: {path}
- Verify Omnia installation is complete
- Check if playbook exists inside omnia_core container
""",

    # ==========================================================================
    # OpenCHAMI Container Validation Messages
    # ==========================================================================
    "openchami_check_start": "Validating OpenCHAMI containers...",
    "openchami_all_running": "All OpenCHAMI containers are running ({count} containers)",
    "openchami_containers_missing": "Missing OpenCHAMI containers: {containers}",
    "openchami_containers_not_running": "OpenCHAMI containers not running: {containers}",
    "openchami_containers_unhealthy": "Unhealthy OpenCHAMI containers: {containers}",
    "openchami_validation_pass": "OpenCHAMI container validation PASSED",
    "openchami_validation_fail": "OpenCHAMI container validation FAILED",
    
    "openchami_missing_instruction": """
ACTION REQUIRED: Required OpenCHAMI containers are missing.
- Missing containers: {containers}
- Check if prepare_oim playbook completed successfully
- View container list: {runtime} ps -a
- Re-run prepare_oim playbook if needed
""",
    "openchami_not_running_instruction": """
ACTION REQUIRED: OpenCHAMI containers are not running.
- Stopped containers: {containers}
- Start containers: {runtime} start <container_name>
- Check container logs: {runtime} logs <container_name>
- Restart OpenCHAMI service: systemctl restart openchami
""",
    "openchami_unhealthy_instruction": """
ACTION REQUIRED: OpenCHAMI containers are unhealthy.
- Unhealthy containers: {containers}
- Check container health: {runtime} inspect <container_name>
- View container logs: {runtime} logs <container_name>
- Restart unhealthy containers: {runtime} restart <container_name>
""",

    # ==========================================================================
    # OpenCHAMI Service Messages
    # ==========================================================================
    "openchami_service_check_start": "Checking OpenCHAMI service status...",
    "openchami_service_running": "OpenCHAMI service is running",
    "openchami_service_not_running": "OpenCHAMI service is NOT running",
    "openchami_service_not_found": "OpenCHAMI service not found",
    "openchami_service_enabled": "OpenCHAMI service is enabled",
    "openchami_service_disabled": "OpenCHAMI service is NOT enabled",
    
    "openchami_service_not_running_instruction": """
ACTION REQUIRED: OpenCHAMI service is not running.
- Start service: systemctl start openchami
- Check status: systemctl status openchami
- View logs: journalctl -u openchami
""",

    # ==========================================================================
    # Auth Container/Service Messages (LDAP-dependent)
    # ==========================================================================
    "auth_check_start": "Validating auth containers and service...",
    "auth_check_skip": "Skipping auth validation - LDAP not configured",
    "auth_ldap_enabled": "LDAP is enabled in software_config.json",
    "auth_ldap_disabled": "LDAP is NOT enabled in software_config.json",
    "auth_containers_running": "All auth containers are running",
    "auth_containers_missing": "Missing auth containers: {containers}",
    "auth_containers_not_running": "Auth containers not running: {containers}",
    "auth_service_running": "Auth service is running",
    "auth_service_not_running": "Auth service is NOT running",
    "auth_validation_pass": "Auth validation PASSED",
    "auth_validation_fail": "Auth validation FAILED",
    "auth_validation_skip": "Auth validation SKIPPED (LDAP not configured)",
    
    "auth_missing_instruction": """
ACTION REQUIRED: Auth containers are missing but LDAP is enabled.
- Missing containers: {containers}
- LDAP is configured in software_config.json
- Re-run prepare_oim playbook to deploy auth containers
- Or disable LDAP in software_config.json if not needed
""",
    "auth_not_running_instruction": """
ACTION REQUIRED: Auth containers are not running but LDAP is enabled.
- Stopped containers: {containers}
- Start containers: {runtime} start <container_name>
- Check logs: {runtime} logs <container_name>
""",
    "auth_service_not_running_instruction": """
ACTION REQUIRED: Auth service is not running but LDAP is enabled.
- Start auth service: systemctl start <auth_service>
- Check status: systemctl status <auth_service>
- View logs: journalctl -u <auth_service>
""",

    # ==========================================================================
    # omnia.target Validation Messages
    # ==========================================================================
    "omnia_target_check_start": "Validating omnia.target and dependencies...",
    "omnia_target_exists": "omnia.target exists",
    "omnia_target_not_found": "omnia.target NOT found",
    "omnia_target_active": "omnia.target is active",
    "omnia_target_inactive": "omnia.target is NOT active (state: {state})",
    "omnia_target_enabled": "omnia.target is enabled",
    "omnia_target_disabled": "omnia.target is NOT enabled",
    "omnia_target_validation_pass": "omnia.target validation PASSED",
    "omnia_target_validation_fail": "omnia.target validation FAILED",
    
    "omnia_target_not_found_instruction": """
ACTION REQUIRED: omnia.target systemd unit not found.
- Verify Omnia installation is complete
- Check if unit file exists: ls /etc/systemd/system/omnia.target
- Re-run Omnia deployment if needed
""",
    "omnia_target_inactive_instruction": """
ACTION REQUIRED: omnia.target is not active.
- Current state: {state}
- Start target: systemctl start omnia.target
- Check status: systemctl status omnia.target
- View logs: journalctl -u omnia.target
""",

    # ==========================================================================
    # omnia.target Dependencies Messages
    # ==========================================================================
    "dependencies_check_start": "Checking omnia.target dependencies...",
    "dependencies_all_active": "All omnia.target dependencies are active ({count} dependencies)",
    "dependencies_inactive": "Inactive dependencies: {dependencies}",
    "dependencies_failed": "Failed dependencies: {dependencies}",
    "dependencies_validation_pass": "Dependencies validation PASSED",
    "dependencies_validation_fail": "Dependencies validation FAILED",
    
    "dependencies_inactive_instruction": """
ACTION REQUIRED: Some omnia.target dependencies are not active.
- Inactive dependencies: {dependencies}
- Start each dependency: systemctl start <dependency>
- Check status: systemctl status <dependency>
- View logs: journalctl -u <dependency>
""",
    "dependencies_failed_instruction": """
ACTION REQUIRED: Some omnia.target dependencies have failed.
- Failed dependencies: {dependencies}
- Reset failed state: systemctl reset-failed <dependency>
- Restart dependency: systemctl restart <dependency>
- Check logs: journalctl -u <dependency>
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
    # software_config.json Messages
    # ==========================================================================
    "software_config_check_start": "Reading software_config.json...",
    "software_config_found": "software_config.json found at {path}",
    "software_config_not_found": "software_config.json NOT found at {path}",
    "software_config_parse_error": "Failed to parse software_config.json: {error}",
    
    "software_config_not_found_instruction": """
ACTION REQUIRED: software_config.json not found.
- Expected path: {path}
- Verify Omnia configuration is complete
- Create or copy software_config.json to the expected location
""",

    # ==========================================================================
    # General Validation Messages
    # ==========================================================================
    "validation_start": "Starting prepare_oim validation...",
    "validation_complete": "prepare_oim validation complete",
    "validation_all_passed": "All validations PASSED",
    "validation_some_failed": "Validation completed with {failed_count} failures",
    
    # ==========================================================================
    # Assertion Messages (for pytest)
    # ==========================================================================
    "assert_container_runtime": "Container runtime ({runtime}) must be available",
    "assert_container_exists": "Container '{container}' must exist",
    "assert_container_running": "Container '{container}' must be running",
    "assert_container_healthy": "Container '{container}' must be healthy",
    "assert_service_exists": "Service '{service}' must exist",
    "assert_service_running": "Service '{service}' must be running",
    "assert_service_enabled": "Service '{service}' must be enabled",
    "assert_target_exists": "Target '{target}' must exist",
    "assert_target_active": "Target '{target}' must be active",
    "assert_dependency_active": "Dependency '{dependency}' must be active",
    "assert_ldap_required": "LDAP is enabled - auth components are required",
    "assert_ssh_connection": "SSH connection to {server} must succeed",
    "assert_playbook_success": "prepare_oim playbook must complete successfully",
}
