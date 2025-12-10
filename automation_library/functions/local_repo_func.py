"""
Functions for local_repo validation workflow.

This module provides functions to:
1. Validate Pulp container is running without errors
2. Validate custom repo accessibility from OIM
3. Validate Pulp API endpoints
4. Validate package download status via status.csv files
5. Validate air-gap image registry configuration
"""

import subprocess
import json
import csv
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..vars.local_repo_vars import LOCAL_REPO_VARS
from ..messages.local_repo_msgs import LOCAL_REPO_MSGS


# =============================================================================
# Logging Utilities
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"


class Symbols:
    """Unicode symbols for status indicators."""
    CHECK = "✔"
    CROSS = "✘"
    ARROW = "➜"
    BULLET = "●"


_debug_mode = False


def set_debug_mode(enabled: bool):
    """Enable or disable debug mode."""
    global _debug_mode
    _debug_mode = enabled


def _log(message: str, level: str = "INFO"):
    """Print log message with timestamp."""
    global _debug_mode
    
    if level == "DEBUG" and not _debug_mode:
        return
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": Colors.BLUE,
        "DEBUG": Colors.DIM,
        "WARN": Colors.YELLOW,
        "ERROR": Colors.BRIGHT_RED,
        "OK": Colors.BRIGHT_GREEN,
    }
    color = colors.get(level, "")
    print(f"{color}[{timestamp}] [{level}] {message}{Colors.RESET}")


# =============================================================================
# SSH and Command Execution
# =============================================================================

def _get_ssh_command() -> str:
    """Build SSH command prefix for remote execution."""
    server = LOCAL_REPO_VARS.get("oim_server_ip", "")
    user = LOCAL_REPO_VARS.get("oim_ssh_user", "root")
    port = LOCAL_REPO_VARS.get("oim_ssh_port", 22)
    password = LOCAL_REPO_VARS.get("oim_ssh_password", "")
    
    ssh_opts = "-o StrictHostKeyChecking=no -o ConnectTimeout=10"
    
    if password:
        return f"sshpass -p '{password}' ssh {ssh_opts} -p {port} {user}@{server}"
    else:
        return f"ssh {ssh_opts} -p {port} {user}@{server}"


def _is_remote_mode() -> bool:
    """Check if running in remote mode."""
    server = LOCAL_REPO_VARS.get("oim_server_ip", "")
    return server and server.strip() and server.lower() not in ["", "localhost", "127.0.0.1"]


def run_command(cmd: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command locally or remotely via SSH.
    Returns (returncode, stdout, stderr).
    """
    timeout = timeout or LOCAL_REPO_VARS.get("command_timeout", 60)
    
    if _is_remote_mode():
        ssh_cmd = _get_ssh_command()
        escaped_cmd = cmd.replace("'", "'\\''")
        full_cmd = f"{ssh_cmd} '{escaped_cmd}'"
        _log(f"Running remote: {cmd}", "DEBUG")
    else:
        full_cmd = cmd
        _log(f"Running local: {cmd}", "DEBUG")
    
    try:
        result = subprocess.run(
            full_cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        _log(f"Command timed out after {timeout}s", "ERROR")
        return -1, "", "Command timed out"
    except Exception as e:
        _log(f"Command exception: {str(e)}", "ERROR")
        return -1, "", str(e)


# =============================================================================
# Container Runtime Detection
# =============================================================================

def detect_container_runtime() -> Optional[str]:
    """Detect available container runtime (podman or docker)."""
    _log(LOCAL_REPO_MSGS["runtime_check_start"], "INFO")
    
    # Check for podman first (preferred on RHEL)
    rc, stdout, _ = run_command("which podman")
    if rc == 0:
        _log(LOCAL_REPO_MSGS["runtime_found"].format(runtime="podman"), "OK")
        return "podman"
    
    # Fallback to docker
    rc, stdout, _ = run_command("which docker")
    if rc == 0:
        _log(LOCAL_REPO_MSGS["runtime_found"].format(runtime="docker"), "OK")
        return "docker"
    
    _log(LOCAL_REPO_MSGS["runtime_not_found"], "ERROR")
    return None


# =============================================================================
# Pulp Container Validation
# =============================================================================

def validate_pulp_container() -> Dict:
    """
    Validate Pulp container is running without errors.
    
    Checks:
    1. Container exists
    2. Container is running
    3. Container health status
    4. No critical errors in logs
    """
    runtime = detect_container_runtime()
    pulp_container = LOCAL_REPO_VARS.get("pulp_container_name", "pulp")
    
    _log(LOCAL_REPO_MSGS["pulp_check_start"], "INFO")
    
    if not runtime:
        return {
            "passed": False,
            "exists": False,
            "running": False,
            "message": LOCAL_REPO_MSGS["runtime_not_found"],
            "instruction": LOCAL_REPO_MSGS["runtime_not_found_instruction"]
        }
    
    # Check if Pulp container exists and is running
    rc, stdout, stderr = run_command(
        f"{runtime} ps -a --format '{{{{.Names}}}}:{{{{.Status}}}}' | grep -E '^{pulp_container}:'"
    )
    
    if rc != 0 or not stdout:
        _log(LOCAL_REPO_MSGS["pulp_container_not_found"], "ERROR")
        return {
            "passed": False,
            "exists": False,
            "running": False,
            "message": LOCAL_REPO_MSGS["pulp_container_not_found"],
            "instruction": LOCAL_REPO_MSGS["pulp_not_found_instruction"].format(
                runtime=runtime
            )
        }
    
    # Parse status
    parts = stdout.split(":", 1)
    status = parts[1] if len(parts) > 1 else ""
    
    if "Up" not in status:
        _log(LOCAL_REPO_MSGS["pulp_container_not_running"], "ERROR")
        return {
            "passed": False,
            "exists": True,
            "running": False,
            "status": status,
            "message": LOCAL_REPO_MSGS["pulp_container_not_running"],
            "instruction": LOCAL_REPO_MSGS["pulp_not_running_instruction"].format(
                runtime=runtime, container=pulp_container
            )
        }
    
    _log(LOCAL_REPO_MSGS["pulp_container_running"], "OK")
    
    result = {
        "passed": True,
        "exists": True,
        "running": True,
        "status": status,
        "message": LOCAL_REPO_MSGS["pulp_container_running"],
        "warnings": []
    }
    
    # Check container health
    health_rc, health_stdout, _ = run_command(
        f"{runtime} inspect --format '{{{{.State.Health.Status}}}}' {pulp_container} 2>/dev/null"
    )
    
    if health_rc == 0:
        health = health_stdout.strip().strip("'")
        if health and health not in ["", "<no value>", "none"]:
            result["health"] = health
            if health != "healthy":
                result["warnings"].append(
                    LOCAL_REPO_MSGS["pulp_container_unhealthy"].format(status=health)
                )
                _log(LOCAL_REPO_MSGS["pulp_container_unhealthy"].format(status=health), "WARN")
    
    # Check for errors in container logs
    error_rc, error_stdout, _ = run_command(
        f"{runtime} logs --tail 100 {pulp_container} 2>&1 | grep -iE '(error|fatal|critical|exception)' | head -5"
    )
    
    if error_rc == 0 and error_stdout.strip():
        error_count = len(error_stdout.strip().split('\n'))
        result["warnings"].append(f"Pulp container has {error_count} error(s) in recent logs")
        result["log_errors"] = error_stdout.strip().split('\n')[:5]
        _log(LOCAL_REPO_MSGS["pulp_container_errors"], "WARN")
    
    return result


def get_pulp_container_health() -> Optional[str]:
    """Get health status of Pulp container."""
    runtime = detect_container_runtime()
    pulp_container = LOCAL_REPO_VARS.get("pulp_container_name", "pulp")
    
    if not runtime:
        return None
    
    rc, stdout, _ = run_command(
        f"{runtime} inspect --format '{{{{.State.Health.Status}}}}' {pulp_container} 2>/dev/null"
    )
    
    if rc != 0:
        return None
    
    health = stdout.strip().strip("'")
    return health if health and health not in ["<no value>", "none"] else None


# =============================================================================
# Custom Repo Accessibility Validation
# =============================================================================

def validate_custom_repo_access() -> Dict:
    """
    Validate custom repo is accessible from OIM.
    
    Checks:
    1. Base URL is accessible
    2. Pulp API status endpoint responds
    """
    base_url = LOCAL_REPO_VARS.get("custom_repo_base_url", "https://localhost:2225")
    endpoints = LOCAL_REPO_VARS.get("custom_repo_endpoints", ["/pulp/api/v3/status/"])
    
    _log(LOCAL_REPO_MSGS["repo_access_check_start"], "INFO")
    
    result = {
        "passed": True,
        "accessible": False,
        "endpoints_checked": [],
        "warnings": []
    }
    
    # Test base URL accessibility (use -k to skip SSL verification for self-signed certs)
    base_check_rc, base_check_stdout, _ = run_command(
        f"curl -s -k -o /dev/null -w '%{{http_code}}' --connect-timeout 10 {base_url}/pulp/api/v3/status/"
    )
    
    if base_check_rc == 0 and base_check_stdout.strip() in ["200", "301", "302"]:
        result["accessible"] = True
        result["message"] = LOCAL_REPO_MSGS["repo_accessible"].format(url=base_url)
        _log(result["message"], "OK")
    else:
        result["passed"] = False
        result["accessible"] = False
        result["message"] = LOCAL_REPO_MSGS["repo_not_accessible"].format(url=base_url)
        result["instruction"] = LOCAL_REPO_MSGS["repo_not_accessible_instruction"].format(url=base_url)
        result["http_code"] = base_check_stdout.strip()
        _log(result["message"], "ERROR")
        return result
    
    # Test specific endpoints
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        endpoint_rc, endpoint_stdout, _ = run_command(
            f"curl -s -k -o /dev/null -w '%{{http_code}}' --connect-timeout 10 {url}"
        )
        
        endpoint_result = {
            "endpoint": endpoint,
            "http_code": endpoint_stdout.strip(),
            "accessible": endpoint_rc == 0 and endpoint_stdout.strip() in ["200", "301", "302"]
        }
        result["endpoints_checked"].append(endpoint_result)
        
        if endpoint_result["accessible"]:
            _log(LOCAL_REPO_MSGS["repo_api_success"].format(endpoint=endpoint), "OK")
        else:
            result["warnings"].append(
                LOCAL_REPO_MSGS["repo_api_fail"].format(endpoint=endpoint, error=endpoint_stdout.strip())
            )
            _log(LOCAL_REPO_MSGS["repo_api_fail"].format(endpoint=endpoint, error=endpoint_stdout.strip()), "WARN")
    
    return result


# =============================================================================
# Pulp API Validation
# =============================================================================

def validate_pulp_api() -> Dict:
    """
    Validate Pulp API endpoints work correctly.
    
    Checks:
    1. RPM repositories endpoint
    2. RPM remotes endpoint
    3. RPM publications endpoint
    4. RPM distributions endpoint
    """
    runtime = detect_container_runtime()
    pulp_container = LOCAL_REPO_VARS.get("pulp_container_name", "pulp")
    pulp_api_base_url = LOCAL_REPO_VARS.get("pulp_api_base_url", "https://localhost:2225")
    pulp_api_username = LOCAL_REPO_VARS.get("pulp_api_username", "admin")
    pulp_api_password = LOCAL_REPO_VARS.get("pulp_api_password", "Dell1234")
    pulp_api_endpoints = LOCAL_REPO_VARS.get("pulp_api_endpoints", [
        "/pulp/api/v3/repositories/rpm/rpm/",
        "/pulp/api/v3/remotes/rpm/rpm/",
        "/pulp/api/v3/publications/rpm/rpm/",
        "/pulp/api/v3/distributions/rpm/rpm/",
    ])
    
    _log(LOCAL_REPO_MSGS["pulp_cmd_check_start"], "INFO")
    
    if not runtime:
        return {
            "passed": False,
            "message": LOCAL_REPO_MSGS["runtime_not_found"],
            "instruction": LOCAL_REPO_MSGS["runtime_not_found_instruction"]
        }
    
    result = {
        "passed": True,
        "endpoints": [],
        "warnings": [],
        "repo_count": None
    }
    
    # Test each Pulp API endpoint from inside the container
    for endpoint in pulp_api_endpoints:
        url = f"{pulp_api_base_url}{endpoint}"
        cmd_rc, cmd_stdout, cmd_stderr = run_command(
            f"{runtime} exec {pulp_container} curl -s -k -u {pulp_api_username}:{pulp_api_password} "
            f"-o /dev/null -w '%{{http_code}}' {url} 2>&1"
        )
        
        endpoint_name = endpoint.split('/')[-2] if endpoint.endswith('/') else endpoint.split('/')[-1]
        
        endpoint_result = {
            "endpoint": endpoint,
            "name": endpoint_name,
            "http_code": cmd_stdout.strip(),
            "passed": False
        }
        
        if cmd_rc == 0 and cmd_stdout.strip() == "200":
            endpoint_result["passed"] = True
            _log(LOCAL_REPO_MSGS["pulp_cmd_success"].format(command=endpoint_name), "OK")
        elif cmd_stdout.strip() == "401":
            result["passed"] = False
            endpoint_result["error"] = "Authentication failed"
            _log(LOCAL_REPO_MSGS["pulp_cmd_fail"].format(command=endpoint_name), "ERROR")
        elif cmd_stdout.strip() == "404":
            endpoint_result["error"] = "Not found (may not be configured)"
            result["warnings"].append(f"Pulp API '{endpoint_name}' endpoint not found")
            _log(f"Pulp API '{endpoint_name}' endpoint not found", "WARN")
        else:
            result["warnings"].append(f"Pulp API '{endpoint_name}' returned HTTP {cmd_stdout.strip()}")
            _log(f"Pulp API '{endpoint_name}' returned HTTP {cmd_stdout.strip()}", "WARN")
        
        result["endpoints"].append(endpoint_result)
    
    # Get count of repositories
    repo_count_rc, repo_count_stdout, _ = run_command(
        f"{runtime} exec {pulp_container} curl -s -k -u {pulp_api_username}:{pulp_api_password} "
        f"{pulp_api_base_url}/pulp/api/v3/repositories/rpm/rpm/ 2>&1 | grep -o '\"count\":[0-9]*' | head -1"
    )
    
    if repo_count_rc == 0 and repo_count_stdout.strip():
        count = repo_count_stdout.strip().split(':')[-1]
        result["repo_count"] = int(count)
        _log(f"Pulp has {count} RPM repositories configured", "OK")
    
    if result["passed"]:
        result["message"] = LOCAL_REPO_MSGS["pulp_cmd_validation_pass"]
    else:
        result["message"] = LOCAL_REPO_MSGS["pulp_cmd_validation_fail"]
    
    return result


# =============================================================================
# Package Download Status Validation
# =============================================================================

def validate_package_download_status() -> Dict:
    """
    Validate all packages are downloaded successfully by checking status.csv files.
    
    Logic:
    1. Check top-level status file exists
    2. Parse CSV to find failed packages
    3. Check individual package status files for details
    """
    top_level_status_file = LOCAL_REPO_VARS.get("top_level_status_file", "/diya/omnia/log/local_repo/x86_64/software.csv")
    package_status_dir = LOCAL_REPO_VARS.get("package_status_dir", "/diya/omnia/log/local_repo/x86_64")
    status_success_values = LOCAL_REPO_VARS.get("status_success_values", ["success", "completed", "downloaded", "ok"])
    status_failed_values = LOCAL_REPO_VARS.get("status_failed_values", ["failed", "error", "failure"])
    max_failed_to_show = LOCAL_REPO_VARS.get("max_failed_packages_to_show", 20)
    
    _log(LOCAL_REPO_MSGS["status_check_start"], "INFO")
    
    result = {
        "passed": True,
        "status_file_exists": False,
        "total_packages": 0,
        "success_count": 0,
        "failed_packages": [],
        "warnings": []
    }
    
    # Check if top-level status file exists
    rc, stdout, _ = run_command(f"test -f {top_level_status_file} && echo EXISTS")
    
    if "EXISTS" not in stdout:
        _log(LOCAL_REPO_MSGS["status_file_not_found"].format(path=top_level_status_file), "WARN")
        result["passed"] = True  # Not a failure, just skip
        result["skipped"] = True
        result["message"] = LOCAL_REPO_MSGS["status_file_not_found"].format(path=top_level_status_file)
        result["instruction"] = LOCAL_REPO_MSGS["status_file_not_found_instruction"].format(path=top_level_status_file)
        return result
    
    result["status_file_exists"] = True
    _log(LOCAL_REPO_MSGS["status_file_found"].format(path=top_level_status_file), "OK")
    
    # Read and parse the status file
    rc, content, stderr = run_command(f"cat {top_level_status_file}")
    
    if rc != 0 or not content:
        result["warnings"].append("Could not read status file")
        return result
    
    try:
        lines = content.strip().split('\n')
        
        if not lines:
            result["warnings"].append("Status file is empty")
            return result
        
        # Parse CSV content
        failed_packages = []
        success_count = 0
        total_count = 0
        
        # Try to detect CSV format using first line as header
        header = lines[0].lower()
        
        # Find status and package columns
        status_col_idx = None
        package_col_idx = None
        
        header_parts = [h.strip() for h in header.split(',')]
        for idx, col in enumerate(header_parts):
            if col in ['status', 'state', 'result']:
                status_col_idx = idx
            if col in ['package', 'name', 'pkg', 'component']:
                package_col_idx = idx
        
        # Parse data rows
        for line in lines[1:]:  # Skip header
            if not line.strip():
                continue
            
            parts = [p.strip() for p in line.split(',')]
            total_count += 1
            
            if status_col_idx is not None and status_col_idx < len(parts):
                status = parts[status_col_idx].lower()
            else:
                status = parts[-1].lower() if parts else ""
            
            if package_col_idx is not None and package_col_idx < len(parts):
                pkg_name = parts[package_col_idx]
            else:
                pkg_name = parts[0] if parts else f"package_{total_count}"
            
            if any(s in status for s in status_failed_values):
                failed_packages.append(pkg_name)
            elif any(s in status for s in status_success_values):
                success_count += 1
        
        result["total_packages"] = total_count
        result["success_count"] = success_count
        result["failed_packages"] = failed_packages
        
        # Report results
        if total_count == 0:
            result["warnings"].append("No packages found in status file")
        elif failed_packages:
            result["passed"] = False
            result["message"] = LOCAL_REPO_MSGS["status_some_failed"].format(failed_count=len(failed_packages))
            result["instruction"] = LOCAL_REPO_MSGS["status_failed_packages_instruction"].format(
                packages=", ".join(failed_packages[:max_failed_to_show]),
                status_dir=package_status_dir
            )
            _log(result["message"], "ERROR")
            
            # Get detailed failure info
            detailed_failures = _check_package_status_files(failed_packages[:max_failed_to_show], package_status_dir)
            if detailed_failures:
                result["detailed_failures"] = detailed_failures
        else:
            result["message"] = LOCAL_REPO_MSGS["status_all_success"].format(count=success_count)
            _log(result["message"], "OK")
    
    except Exception as e:
        result["warnings"].append(LOCAL_REPO_MSGS["status_parse_error"].format(error=str(e)))
        _log(LOCAL_REPO_MSGS["status_parse_error"].format(error=str(e)), "WARN")
    
    return result


def _check_package_status_files(failed_packages: List[str], package_status_dir: str) -> Dict[str, str]:
    """Check individual package status files for failure details."""
    detailed_failures = {}
    
    for pkg in failed_packages:
        # Try to find package-specific status file
        pkg_status_patterns = [
            f"{package_status_dir}/{pkg}/status.csv",
            f"{package_status_dir}/{pkg}_status.csv",
            f"{package_status_dir}/{pkg}/status.txt",
        ]
        
        for pattern in pkg_status_patterns:
            rc, stdout, _ = run_command(f"test -f {pattern} && cat {pattern}")
            if rc == 0 and stdout:
                # Extract failure reason from content
                lines = stdout.strip().split('\n')
                for line in lines:
                    if any(s in line.lower() for s in ['error', 'failed', 'failure']):
                        detailed_failures[pkg] = line.strip()[:100]
                        break
                if pkg not in detailed_failures:
                    detailed_failures[pkg] = "See status file for details"
                break
    
    return detailed_failures


# =============================================================================
# Air-gap Image Registry Validation
# =============================================================================

def validate_airgap_images() -> Dict:
    """
    Validate that JSON config files have images pointing to local registry
    instead of external registries (for air-gapped environments).
    
    Checks:
    1. If airgap_enabled is True, validate image references
    2. Images should point to local registry or be tar files
    3. External registries (docker.io, registry.k8s.io, etc.) should not be present
    """
    airgap_enabled = LOCAL_REPO_VARS.get("airgap_enabled", False)
    
    _log(LOCAL_REPO_MSGS["airgap_check_start"], "INFO")
    
    result = {
        "passed": True,
        "skipped": False,
        "external_images": [],
        "files_checked": [],
        "warnings": []
    }
    
    # Skip if air-gap validation is disabled
    if not airgap_enabled:
        result["skipped"] = True
        result["message"] = LOCAL_REPO_MSGS["airgap_check_skip"]
        _log(result["message"], "INFO")
        return result
    
    json_config_dir = LOCAL_REPO_VARS.get("json_config_dir", "/diya/omnia/input/project_default/config/x86_64/rhel/10.0")
    json_files = LOCAL_REPO_VARS.get("json_files_to_check", ["service_k8s.json"])
    external_registries = LOCAL_REPO_VARS.get("external_registries", [
        "docker.io/", "registry.k8s.io/", "ghcr.io/", "quay.io/", "gcr.io/", "k8s.gcr.io/", "mcr.microsoft.com/"
    ])
    local_registry = LOCAL_REPO_VARS.get("local_registry", "localhost:5000")
    
    # Check if local registry is accessible
    registry_rc, registry_stdout, _ = run_command(
        f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 5 http://{local_registry}/v2/_catalog"
    )
    
    if registry_rc == 0 and registry_stdout.strip() == "200":
        _log(LOCAL_REPO_MSGS["airgap_local_registry_ok"].format(registry=local_registry), "OK")
    else:
        result["warnings"].append(
            LOCAL_REPO_MSGS["airgap_local_registry_fail"].format(registry=local_registry)
        )
        _log(LOCAL_REPO_MSGS["airgap_local_registry_fail"].format(registry=local_registry), "WARN")
    
    # Check each JSON config file
    total_external_images = []
    
    for json_file in json_files:
        json_path = f"{json_config_dir}/{json_file}"
        
        # Check if file exists
        rc, stdout, _ = run_command(f"test -f {json_path} && cat {json_path}")
        
        if rc != 0 or not stdout:
            result["warnings"].append(LOCAL_REPO_MSGS["airgap_json_not_found"].format(path=json_file))
            _log(LOCAL_REPO_MSGS["airgap_json_not_found"].format(path=json_file), "WARN")
            continue
        
        _log(LOCAL_REPO_MSGS["airgap_json_found"].format(path=json_file), "OK")
        result["files_checked"].append(json_file)
        
        content = stdout
        external_images_in_file = []
        
        for registry in external_registries:
            if registry in content:
                # Extract the image names containing this registry
                # Match patterns like "package": "docker.io/something"
                pattern = rf'"package"\s*:\s*"({re.escape(registry)}[^"]+)"'
                matches = re.findall(pattern, content)
                external_images_in_file.extend(matches)
        
        if external_images_in_file:
            result["passed"] = False
            _log(LOCAL_REPO_MSGS["airgap_images_invalid"].format(count=len(external_images_in_file), file=json_file), "ERROR")
            for img in external_images_in_file[:5]:
                _log(LOCAL_REPO_MSGS["airgap_external_image"].format(image=img), "ERROR")
            total_external_images.extend(external_images_in_file)
        else:
            _log(LOCAL_REPO_MSGS["airgap_images_valid"].format(file=json_file), "OK")
    
    result["external_images"] = total_external_images
    
    # Summary
    if total_external_images:
        result["message"] = LOCAL_REPO_MSGS["airgap_validation_fail"]
        result["instruction"] = LOCAL_REPO_MSGS["airgap_invalid_instruction"].format(
            images=", ".join(total_external_images[:10]),
            local_registry=local_registry
        )
    else:
        result["message"] = LOCAL_REPO_MSGS["airgap_validation_pass"]
    
    return result


# =============================================================================
# local_repo Playbook Execution
# =============================================================================

def run_local_repo_playbook() -> Dict:
    """
    Execute local_repo playbook inside omnia_core container.
    
    Workflow:
    1. Check omnia_core is running
    2. Execute ansible-playbook inside container
    3. Return success/failure status
    """
    runtime = detect_container_runtime()
    omnia_core_container = LOCAL_REPO_VARS.get("omnia_core_container", "omnia_core")
    playbook_path = LOCAL_REPO_VARS.get("local_repo_playbook", "/omnia/local_repo/local_repo.yml")
    inventory = LOCAL_REPO_VARS.get("local_repo_inventory", "/opt/omnia/inventory")
    timeout = LOCAL_REPO_VARS.get("local_repo_timeout", 1800)
    
    _log(LOCAL_REPO_MSGS["playbook_start"], "INFO")
    
    if not runtime:
        return {
            "success": False,
            "message": LOCAL_REPO_MSGS["runtime_not_found"],
            "instruction": LOCAL_REPO_MSGS["runtime_not_found_instruction"]
        }
    
    # Check omnia_core is running
    rc, stdout, _ = run_command(
        f"{runtime} ps --format '{{{{.Names}}}}' | grep -E '^{omnia_core_container}$'"
    )
    
    if rc != 0 or omnia_core_container not in stdout:
        return {
            "success": False,
            "message": f"omnia_core container '{omnia_core_container}' is not running",
            "instruction": f"Start the container: {runtime} start {omnia_core_container}"
        }
    
    # Check if playbook exists
    rc, stdout, _ = run_command(
        f"{runtime} exec {omnia_core_container} test -f {playbook_path} && echo EXISTS"
    )
    
    if "EXISTS" not in stdout:
        _log(LOCAL_REPO_MSGS["playbook_not_found"].format(path=playbook_path), "ERROR")
        return {
            "success": False,
            "message": LOCAL_REPO_MSGS["playbook_not_found"].format(path=playbook_path),
            "instruction": LOCAL_REPO_MSGS["playbook_not_found_instruction"].format(path=playbook_path)
        }
    
    # Execute playbook
    playbook_cmd = f"{runtime} exec {omnia_core_container} ansible-playbook -i {inventory} {playbook_path}"
    rc, stdout, stderr = run_command(playbook_cmd, timeout=timeout)
    
    if rc == 0:
        _log(LOCAL_REPO_MSGS["playbook_success"], "OK")
        return {
            "success": True,
            "message": LOCAL_REPO_MSGS["playbook_success"],
            "output": stdout
        }
    
    error = stderr or stdout or "Unknown error"
    _log(LOCAL_REPO_MSGS["playbook_fail"].format(error=error), "ERROR")
    return {
        "success": False,
        "message": LOCAL_REPO_MSGS["playbook_fail"].format(error=error),
        "instruction": LOCAL_REPO_MSGS["playbook_fail_instruction"].format(
            inventory=inventory, playbook=playbook_path, error=error
        ),
        "output": stdout,
        "error": stderr
    }


# =============================================================================
# Full Validation Workflow
# =============================================================================

def run_full_validation(run_playbook: bool = False) -> Dict:
    """
    Run the complete local_repo validation workflow.
    
    Steps:
    1. Detect container runtime
    2. Validate Pulp container is running without errors
    3. Validate custom repo accessibility
    4. Validate Pulp API endpoints
    5. Run local_repo playbook (optional)
    6. Validate package download status
    7. Validate air-gap images (if enabled)
    
    Args:
        run_playbook: Whether to run local_repo playbook (default: False)
    
    Returns:
        Dict with overall validation results
    """
    _log(LOCAL_REPO_MSGS["validation_start"], "INFO")
    
    results = {
        "container_runtime": None,
        "pulp_container": None,
        "custom_repo_access": None,
        "pulp_api": None,
        "playbook": None,
        "package_status": None,
        "airgap_images": None,
        "overall_passed": True,
        "failed_count": 0,
        "warnings": []
    }
    
    # 1. Detect container runtime
    runtime = detect_container_runtime()
    if not runtime:
        results["container_runtime"] = {
            "passed": False,
            "message": LOCAL_REPO_MSGS["runtime_not_found"]
        }
        results["overall_passed"] = False
        results["failed_count"] += 1
        return results
    
    results["container_runtime"] = {
        "passed": True,
        "runtime": runtime,
        "message": LOCAL_REPO_MSGS["runtime_found"].format(runtime=runtime)
    }
    
    # 2. Validate Pulp container
    results["pulp_container"] = validate_pulp_container()
    if not results["pulp_container"].get("passed"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    if results["pulp_container"].get("warnings"):
        results["warnings"].extend(results["pulp_container"]["warnings"])
    
    # 3. Validate custom repo accessibility
    results["custom_repo_access"] = validate_custom_repo_access()
    if not results["custom_repo_access"].get("passed"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    if results["custom_repo_access"].get("warnings"):
        results["warnings"].extend(results["custom_repo_access"]["warnings"])
    
    # 4. Validate Pulp API endpoints
    results["pulp_api"] = validate_pulp_api()
    if not results["pulp_api"].get("passed"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    if results["pulp_api"].get("warnings"):
        results["warnings"].extend(results["pulp_api"]["warnings"])
    
    # 5. Run local_repo playbook (if requested)
    if run_playbook:
        results["playbook"] = run_local_repo_playbook()
        if not results["playbook"].get("success"):
            results["overall_passed"] = False
            results["failed_count"] += 1
    
    # 6. Validate package download status
    results["package_status"] = validate_package_download_status()
    if not results["package_status"].get("passed") and not results["package_status"].get("skipped"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    if results["package_status"].get("warnings"):
        results["warnings"].extend(results["package_status"]["warnings"])
    
    # 7. Validate air-gap images
    results["airgap_images"] = validate_airgap_images()
    if not results["airgap_images"].get("passed") and not results["airgap_images"].get("skipped"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    if results["airgap_images"].get("warnings"):
        results["warnings"].extend(results["airgap_images"]["warnings"])
    
    # Summary
    _log(LOCAL_REPO_MSGS["validation_complete"], "INFO")
    
    if results["overall_passed"]:
        _log(LOCAL_REPO_MSGS["validation_all_passed"], "OK")
    else:
        _log(LOCAL_REPO_MSGS["validation_some_failed"].format(failed_count=results["failed_count"]), "ERROR")
    
    return results


# =============================================================================
# Report Generation
# =============================================================================

def print_validation_report(results: Dict):
    """Print a formatted validation report."""
    print("\n" + "=" * 70)
    print("LOCAL_REPO VALIDATION REPORT")
    print("=" * 70)
    
    passed_items = []
    failed_items = []
    skipped_items = []
    warnings = results.get("warnings", [])
    
    # Collect results
    checks = [
        ("Container Runtime", results.get("container_runtime")),
        ("Pulp Container", results.get("pulp_container")),
        ("Custom Repo Access", results.get("custom_repo_access")),
        ("Pulp API", results.get("pulp_api")),
        ("Playbook Execution", results.get("playbook")),
        ("Package Status", results.get("package_status")),
        ("Air-gap Images", results.get("airgap_images")),
    ]
    
    for name, check in checks:
        if check is None:
            continue
        
        if check.get("skipped"):
            skipped_items.append(f"{name}: {check.get('message', 'Skipped')}")
        elif check.get("passed") or check.get("success"):
            passed_items.append(f"{name}: {check.get('message', 'Passed')}")
        else:
            failed_items.append(f"{name}: {check.get('message', 'Failed')}")
            if check.get("instruction"):
                failed_items.append(f"  → {check.get('instruction')[:200]}")
    
    # Print results
    print(f"\n{Colors.BRIGHT_GREEN}✅ PASSED ({len(passed_items)}):{Colors.RESET}")
    for item in passed_items:
        print(f"   • {item}")
    
    if warnings:
        print(f"\n{Colors.YELLOW}⚠️  WARNINGS ({len(warnings)}):{Colors.RESET}")
        for item in warnings:
            print(f"   • {item}")
    
    if skipped_items:
        print(f"\n{Colors.CYAN}⏭️  SKIPPED ({len(skipped_items)}):{Colors.RESET}")
        for item in skipped_items:
            print(f"   • {item}")
    
    if failed_items:
        print(f"\n{Colors.BRIGHT_RED}❌ FAILED ({len(failed_items)}):{Colors.RESET}")
        for item in failed_items:
            print(f"   • {item}")
    
    print("\n" + "=" * 70)
    total = len(passed_items) + len(failed_items) + len(skipped_items)
    print(f"SUMMARY: {len(passed_items)} passed, {len(failed_items)} failed, "
          f"{len(skipped_items)} skipped, {len(warnings)} warnings")
    print("=" * 70 + "\n")
