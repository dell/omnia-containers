"""
Functions for prepare_oim validation workflow.

This module provides functions to:
1. SSH into OIM server
2. Execute commands in omnia_core container
3. Run prepare_oim playbook
4. Validate OpenCHAMI containers and services
5. Validate auth containers/services (LDAP-dependent)
6. Validate omnia.target and dependencies
"""

import subprocess
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..vars.prepare_oim_vars import PREPARE_OIM_VARS
from ..messages.prepare_oim_msgs import PREPARE_OIM_MSGS


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
    server = PREPARE_OIM_VARS.get("oim_server_ip", "")
    user = PREPARE_OIM_VARS.get("oim_ssh_user", "root")
    port = PREPARE_OIM_VARS.get("oim_ssh_port", 22)
    password = PREPARE_OIM_VARS.get("oim_ssh_password", "")
    
    ssh_opts = "-o StrictHostKeyChecking=no -o ConnectTimeout=10"
    
    if password:
        return f"sshpass -p '{password}' ssh {ssh_opts} -p {port} {user}@{server}"
    else:
        return f"ssh {ssh_opts} -p {port} {user}@{server}"


def _is_remote_mode() -> bool:
    """Check if running in remote mode."""
    server = PREPARE_OIM_VARS.get("oim_server_ip", "")
    return server and server.strip() and server.lower() not in ["", "localhost", "127.0.0.1"]


def run_command(cmd: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command locally or remotely via SSH.
    Returns (returncode, stdout, stderr).
    """
    timeout = timeout or PREPARE_OIM_VARS.get("command_timeout", 30)
    
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


def test_ssh_connection() -> Dict:
    """Test SSH connection to OIM server."""
    server = PREPARE_OIM_VARS.get("oim_server_ip", "")
    user = PREPARE_OIM_VARS.get("oim_ssh_user", "root")
    
    _log(PREPARE_OIM_MSGS["ssh_connect_start"].format(server=server), "INFO")
    
    rc, stdout, stderr = run_command("echo 'SSH_OK'")
    
    if rc == 0 and "SSH_OK" in stdout:
        _log(PREPARE_OIM_MSGS["ssh_connect_success"].format(server=server), "OK")
        return {"success": True, "message": PREPARE_OIM_MSGS["ssh_connect_success"].format(server=server)}
    
    error = stderr or "Connection failed"
    _log(PREPARE_OIM_MSGS["ssh_connect_fail"].format(server=server, error=error), "ERROR")
    return {
        "success": False,
        "message": PREPARE_OIM_MSGS["ssh_connect_fail"].format(server=server, error=error),
        "instruction": PREPARE_OIM_MSGS["ssh_connect_instruction"].format(
            server=server, user=user, error=error
        )
    }


# =============================================================================
# Container Runtime Detection
# =============================================================================

def detect_container_runtime() -> Optional[str]:
    """Detect available container runtime (podman or docker)."""
    _log(PREPARE_OIM_MSGS["runtime_check_start"], "INFO")
    
    # Check for podman first (preferred on RHEL)
    rc, stdout, _ = run_command("which podman")
    if rc == 0:
        _log(PREPARE_OIM_MSGS["runtime_found"].format(runtime="podman"), "OK")
        return "podman"
    
    # Fallback to docker
    rc, stdout, _ = run_command("which docker")
    if rc == 0:
        _log(PREPARE_OIM_MSGS["runtime_found"].format(runtime="docker"), "OK")
        return "docker"
    
    _log(PREPARE_OIM_MSGS["runtime_not_found"], "ERROR")
    return None


# =============================================================================
# omnia_core Container Operations
# =============================================================================

def check_omnia_core_status() -> Dict:
    """Check if omnia_core container is running."""
    container = PREPARE_OIM_VARS.get("omnia_core_container", "omnia_core")
    runtime = detect_container_runtime()
    
    if not runtime:
        return {
            "success": False,
            "running": False,
            "message": PREPARE_OIM_MSGS["runtime_not_found"],
            "instruction": PREPARE_OIM_MSGS["runtime_not_found_instruction"]
        }
    
    _log(PREPARE_OIM_MSGS["omnia_core_check_start"], "INFO")
    
    # Check if container exists and is running
    rc, stdout, stderr = run_command(
        f"{runtime} ps -a --format '{{{{.Names}}}}:{{{{.Status}}}}' | grep -E '^{container}:'"
    )
    
    if rc != 0 or not stdout:
        _log(PREPARE_OIM_MSGS["omnia_core_not_found"], "ERROR")
        return {
            "success": False,
            "running": False,
            "exists": False,
            "message": PREPARE_OIM_MSGS["omnia_core_not_found"],
            "instruction": PREPARE_OIM_MSGS["omnia_core_not_found_instruction"].format(runtime=runtime)
        }
    
    # Parse status
    parts = stdout.split(":", 1)
    status = parts[1] if len(parts) > 1 else ""
    
    if "Up" in status:
        _log(PREPARE_OIM_MSGS["omnia_core_running"], "OK")
        return {
            "success": True,
            "running": True,
            "exists": True,
            "status": status,
            "message": PREPARE_OIM_MSGS["omnia_core_running"]
        }
    
    _log(PREPARE_OIM_MSGS["omnia_core_not_running"], "ERROR")
    return {
        "success": False,
        "running": False,
        "exists": True,
        "status": status,
        "message": PREPARE_OIM_MSGS["omnia_core_not_running"],
        "instruction": PREPARE_OIM_MSGS["omnia_core_not_running_instruction"].format(runtime=runtime)
    }


def exec_in_omnia_core(cmd: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """Execute a command inside omnia_core container."""
    container = PREPARE_OIM_VARS.get("omnia_core_container", "omnia_core")
    runtime = detect_container_runtime() or "podman"
    timeout = timeout or PREPARE_OIM_VARS.get("command_timeout", 30)
    
    _log(f"Executing in {container}: {cmd}", "DEBUG")
    
    full_cmd = f"{runtime} exec {container} {cmd}"
    return run_command(full_cmd, timeout=timeout)


# =============================================================================
# prepare_oim Playbook Execution
# =============================================================================

def run_prepare_oim_playbook() -> Dict:
    """
    Execute prepare_oim playbook inside omnia_core container.
    
    Workflow:
    1. Check omnia_core is running
    2. Execute ansible-playbook inside container
    3. Return success/failure status
    """
    playbook_path = PREPARE_OIM_VARS.get("prepare_oim_playbook_path")
    inventory = PREPARE_OIM_VARS.get("prepare_oim_inventory")
    timeout = PREPARE_OIM_VARS.get("prepare_oim_timeout", 600)
    
    _log(PREPARE_OIM_MSGS["playbook_start"], "INFO")
    
    # Check omnia_core is running
    core_status = check_omnia_core_status()
    if not core_status.get("running"):
        return {
            "success": False,
            "message": core_status.get("message"),
            "instruction": core_status.get("instruction")
        }
    
    # Check if playbook exists
    rc, stdout, _ = exec_in_omnia_core(f"test -f {playbook_path} && echo EXISTS")
    if "EXISTS" not in stdout:
        _log(PREPARE_OIM_MSGS["playbook_not_found"].format(path=playbook_path), "ERROR")
        return {
            "success": False,
            "message": PREPARE_OIM_MSGS["playbook_not_found"].format(path=playbook_path),
            "instruction": PREPARE_OIM_MSGS["playbook_not_found_instruction"].format(path=playbook_path)
        }
    
    # Execute playbook
    playbook_cmd = f"ansible-playbook -i {inventory} {playbook_path}"
    rc, stdout, stderr = exec_in_omnia_core(playbook_cmd, timeout=timeout)
    
    if rc == 0:
        _log(PREPARE_OIM_MSGS["playbook_success"], "OK")
        return {
            "success": True,
            "message": PREPARE_OIM_MSGS["playbook_success"],
            "output": stdout
        }
    
    error = stderr or stdout or "Unknown error"
    _log(PREPARE_OIM_MSGS["playbook_fail"].format(error=error), "ERROR")
    return {
        "success": False,
        "message": PREPARE_OIM_MSGS["playbook_fail"].format(error=error),
        "instruction": PREPARE_OIM_MSGS["playbook_fail_instruction"].format(
            inventory=inventory, playbook=playbook_path, error=error
        ),
        "output": stdout,
        "error": stderr
    }


# =============================================================================
# software_config.json Operations
# =============================================================================

def read_software_config() -> Dict:
    """Read and parse software_config.json."""
    config_path = PREPARE_OIM_VARS.get("software_config_path")
    
    _log(PREPARE_OIM_MSGS["software_config_check_start"], "INFO")
    
    rc, stdout, stderr = run_command(f"cat {config_path} 2>/dev/null")
    
    if rc != 0 or not stdout:
        _log(PREPARE_OIM_MSGS["software_config_not_found"].format(path=config_path), "WARN")
        return {
            "success": False,
            "exists": False,
            "config": {},
            "message": PREPARE_OIM_MSGS["software_config_not_found"].format(path=config_path),
            "instruction": PREPARE_OIM_MSGS["software_config_not_found_instruction"].format(path=config_path)
        }
    
    try:
        config = json.loads(stdout)
        _log(PREPARE_OIM_MSGS["software_config_found"].format(path=config_path), "OK")
        return {
            "success": True,
            "exists": True,
            "config": config,
            "message": PREPARE_OIM_MSGS["software_config_found"].format(path=config_path)
        }
    except json.JSONDecodeError as e:
        _log(PREPARE_OIM_MSGS["software_config_parse_error"].format(error=str(e)), "ERROR")
        return {
            "success": False,
            "exists": True,
            "config": {},
            "message": PREPARE_OIM_MSGS["software_config_parse_error"].format(error=str(e))
        }


def is_ldap_enabled() -> bool:
    """Check if LDAP is enabled in software_config.json."""
    config_result = read_software_config()
    
    if not config_result.get("success"):
        return False
    
    config = config_result.get("config", {})
    ldap_key = PREPARE_OIM_VARS.get("ldap_config_key", "ldap")
    
    ldap_value = config.get(ldap_key, False)
    
    if ldap_value:
        _log(PREPARE_OIM_MSGS["auth_ldap_enabled"], "INFO")
    else:
        _log(PREPARE_OIM_MSGS["auth_ldap_disabled"], "INFO")
    
    return bool(ldap_value)


# =============================================================================
# OpenCHAMI Container Validation
# =============================================================================

def get_container_list() -> List[Dict]:
    """Get list of all containers with their status."""
    runtime = detect_container_runtime()
    
    if not runtime:
        return []
    
    rc, stdout, _ = run_command(
        f"{runtime} ps -a --format '{{{{.Names}}}}:{{{{.Status}}}}:{{{{.State}}}}'"
    )
    
    if rc != 0 or not stdout:
        return []
    
    containers = []
    for line in stdout.strip().split('\n'):
        if ':' in line:
            parts = line.split(':')
            containers.append({
                "name": parts[0].strip(),
                "status": parts[1].strip() if len(parts) > 1 else "",
                "state": parts[2].strip() if len(parts) > 2 else ""
            })
    
    return containers


def validate_openchami_containers() -> Dict:
    """Validate all required OpenCHAMI containers are present and running."""
    runtime = detect_container_runtime()
    expected_containers = PREPARE_OIM_VARS.get("openchami_containers", [])
    
    _log(PREPARE_OIM_MSGS["openchami_check_start"], "INFO")
    
    if not runtime:
        return {
            "passed": False,
            "message": PREPARE_OIM_MSGS["runtime_not_found"],
            "instruction": PREPARE_OIM_MSGS["runtime_not_found_instruction"]
        }
    
    existing_containers = get_container_list()
    existing_names = [c["name"] for c in existing_containers]
    
    # Check for missing containers
    missing = []
    not_running = []
    
    for expected in expected_containers:
        # Find matching container (exact or partial match)
        found = None
        for container in existing_containers:
            if expected in container["name"] or container["name"].endswith(expected):
                found = container
                break
        
        if not found:
            missing.append(expected)
        elif "Up" not in found.get("status", ""):
            not_running.append(expected)
    
    result = {
        "passed": True,
        "missing": missing,
        "not_running": not_running,
        "existing": existing_names,
        "expected": expected_containers
    }
    
    if missing:
        result["passed"] = False
        result["message"] = PREPARE_OIM_MSGS["openchami_containers_missing"].format(
            containers=", ".join(missing)
        )
        result["instruction"] = PREPARE_OIM_MSGS["openchami_missing_instruction"].format(
            containers=", ".join(missing), runtime=runtime
        )
        _log(result["message"], "ERROR")
    elif not_running:
        result["passed"] = False
        result["message"] = PREPARE_OIM_MSGS["openchami_containers_not_running"].format(
            containers=", ".join(not_running)
        )
        result["instruction"] = PREPARE_OIM_MSGS["openchami_not_running_instruction"].format(
            containers=", ".join(not_running), runtime=runtime
        )
        _log(result["message"], "ERROR")
    else:
        result["message"] = PREPARE_OIM_MSGS["openchami_all_running"].format(
            count=len(expected_containers)
        )
        _log(result["message"], "OK")
    
    return result


def get_container_health(container_name: str) -> Optional[str]:
    """Get health status of a container."""
    runtime = detect_container_runtime()
    
    if not runtime:
        return None
    
    rc, stdout, _ = run_command(
        f"{runtime} inspect --format '{{{{.State.Health.Status}}}}' {container_name} 2>/dev/null"
    )
    
    if rc != 0:
        return None
    
    health = stdout.strip().strip("'")
    return health if health and health not in ["<no value>", "none"] else None


def validate_openchami_containers_health() -> Dict:
    """Validate health status of OpenCHAMI containers."""
    runtime = detect_container_runtime()
    expected_containers = PREPARE_OIM_VARS.get("openchami_containers", [])
    
    if not runtime:
        return {"passed": False, "unhealthy": [], "message": PREPARE_OIM_MSGS["runtime_not_found"]}
    
    unhealthy = []
    
    for container in expected_containers:
        health = get_container_health(container)
        if health and health != "healthy":
            unhealthy.append(f"{container} ({health})")
    
    if unhealthy:
        return {
            "passed": False,
            "unhealthy": unhealthy,
            "message": PREPARE_OIM_MSGS["openchami_containers_unhealthy"].format(
                containers=", ".join(unhealthy)
            ),
            "instruction": PREPARE_OIM_MSGS["openchami_unhealthy_instruction"].format(
                containers=", ".join(unhealthy), runtime=runtime
            )
        }
    
    return {"passed": True, "unhealthy": [], "message": "All containers healthy"}


# =============================================================================
# OpenCHAMI Service Validation
# =============================================================================

def validate_openchami_service() -> Dict:
    """Validate OpenCHAMI systemd service status."""
    _log(PREPARE_OIM_MSGS["openchami_service_check_start"], "INFO")
    
    # Check if service exists
    rc, stdout, _ = run_command("systemctl list-unit-files openchami.service 2>/dev/null")
    
    if rc != 0 or "openchami.service" not in stdout:
        # Try alternative names
        rc, stdout, _ = run_command("systemctl list-unit-files 'openchami*' 2>/dev/null")
        if "openchami" not in stdout.lower():
            return {
                "passed": False,
                "exists": False,
                "message": PREPARE_OIM_MSGS["openchami_service_not_found"]
            }
    
    # Check if service is running
    rc, stdout, _ = run_command("systemctl is-active openchami.service 2>/dev/null")
    is_active = stdout.strip() == "active"
    
    # Check if service is enabled
    rc, stdout, _ = run_command("systemctl is-enabled openchami.service 2>/dev/null")
    is_enabled = stdout.strip() in ["enabled", "static"]
    
    if is_active:
        _log(PREPARE_OIM_MSGS["openchami_service_running"], "OK")
    else:
        _log(PREPARE_OIM_MSGS["openchami_service_not_running"], "ERROR")
    
    return {
        "passed": is_active,
        "exists": True,
        "active": is_active,
        "enabled": is_enabled,
        "message": PREPARE_OIM_MSGS["openchami_service_running"] if is_active 
                   else PREPARE_OIM_MSGS["openchami_service_not_running"],
        "instruction": None if is_active 
                       else PREPARE_OIM_MSGS["openchami_service_not_running_instruction"]
    }


# =============================================================================
# Auth Container/Service Validation (LDAP-dependent)
# =============================================================================

def validate_auth_containers() -> Dict:
    """
    Validate auth containers.
    Only validates if LDAP is enabled in software_config.json.
    """
    _log(PREPARE_OIM_MSGS["auth_check_start"], "INFO")
    
    # Check if LDAP is enabled
    if not is_ldap_enabled():
        _log(PREPARE_OIM_MSGS["auth_check_skip"], "INFO")
        return {
            "passed": True,
            "skipped": True,
            "ldap_enabled": False,
            "message": PREPARE_OIM_MSGS["auth_validation_skip"]
        }
    
    runtime = detect_container_runtime()
    auth_containers = PREPARE_OIM_VARS.get("auth_containers", [])
    
    if not runtime:
        return {
            "passed": False,
            "skipped": False,
            "ldap_enabled": True,
            "message": PREPARE_OIM_MSGS["runtime_not_found"],
            "instruction": PREPARE_OIM_MSGS["runtime_not_found_instruction"]
        }
    
    existing_containers = get_container_list()
    existing_names = [c["name"] for c in existing_containers]
    
    missing = []
    not_running = []
    
    for expected in auth_containers:
        found = None
        for container in existing_containers:
            if expected in container["name"] or container["name"].endswith(expected):
                found = container
                break
        
        if not found:
            missing.append(expected)
        elif "Up" not in found.get("status", ""):
            not_running.append(expected)
    
    result = {
        "passed": True,
        "skipped": False,
        "ldap_enabled": True,
        "missing": missing,
        "not_running": not_running
    }
    
    if missing:
        result["passed"] = False
        result["message"] = PREPARE_OIM_MSGS["auth_containers_missing"].format(
            containers=", ".join(missing)
        )
        result["instruction"] = PREPARE_OIM_MSGS["auth_missing_instruction"].format(
            containers=", ".join(missing), runtime=runtime
        )
        _log(result["message"], "ERROR")
    elif not_running:
        result["passed"] = False
        result["message"] = PREPARE_OIM_MSGS["auth_containers_not_running"].format(
            containers=", ".join(not_running)
        )
        result["instruction"] = PREPARE_OIM_MSGS["auth_not_running_instruction"].format(
            containers=", ".join(not_running), runtime=runtime
        )
        _log(result["message"], "ERROR")
    else:
        result["message"] = PREPARE_OIM_MSGS["auth_containers_running"]
        _log(result["message"], "OK")
    
    return result


def validate_auth_service() -> Dict:
    """
    Validate auth systemd service.
    Only validates if LDAP is enabled in software_config.json.
    """
    if not is_ldap_enabled():
        return {
            "passed": True,
            "skipped": True,
            "ldap_enabled": False,
            "message": PREPARE_OIM_MSGS["auth_validation_skip"]
        }
    
    auth_service_names = PREPARE_OIM_VARS.get("auth_service_names", [])
    
    for service_name in auth_service_names:
        rc, stdout, _ = run_command(f"systemctl is-active {service_name} 2>/dev/null")
        if stdout.strip() == "active":
            _log(PREPARE_OIM_MSGS["auth_service_running"], "OK")
            return {
                "passed": True,
                "skipped": False,
                "ldap_enabled": True,
                "service": service_name,
                "message": PREPARE_OIM_MSGS["auth_service_running"]
            }
    
    _log(PREPARE_OIM_MSGS["auth_service_not_running"], "ERROR")
    return {
        "passed": False,
        "skipped": False,
        "ldap_enabled": True,
        "message": PREPARE_OIM_MSGS["auth_service_not_running"],
        "instruction": PREPARE_OIM_MSGS["auth_service_not_running_instruction"]
    }


# =============================================================================
# omnia.target Validation
# =============================================================================

def validate_omnia_target() -> Dict:
    """Validate omnia.target systemd unit."""
    target_name = PREPARE_OIM_VARS.get("omnia_target_name", "omnia.target")
    
    _log(PREPARE_OIM_MSGS["omnia_target_check_start"], "INFO")
    
    # Check if target exists
    rc, stdout, _ = run_command(f"systemctl list-unit-files {target_name} 2>/dev/null")
    
    if rc != 0 or target_name not in stdout:
        _log(PREPARE_OIM_MSGS["omnia_target_not_found"], "ERROR")
        return {
            "passed": False,
            "exists": False,
            "message": PREPARE_OIM_MSGS["omnia_target_not_found"],
            "instruction": PREPARE_OIM_MSGS["omnia_target_not_found_instruction"]
        }
    
    _log(PREPARE_OIM_MSGS["omnia_target_exists"], "OK")
    
    # Check if target is active
    rc, stdout, _ = run_command(f"systemctl is-active {target_name} 2>/dev/null")
    state = stdout.strip()
    is_active = state == "active"
    
    # Check if target is enabled
    rc, stdout, _ = run_command(f"systemctl is-enabled {target_name} 2>/dev/null")
    is_enabled = stdout.strip() in ["enabled", "static"]
    
    if is_active:
        _log(PREPARE_OIM_MSGS["omnia_target_active"], "OK")
    else:
        _log(PREPARE_OIM_MSGS["omnia_target_inactive"].format(state=state), "ERROR")
    
    return {
        "passed": is_active,
        "exists": True,
        "active": is_active,
        "enabled": is_enabled,
        "state": state,
        "message": PREPARE_OIM_MSGS["omnia_target_active"] if is_active 
                   else PREPARE_OIM_MSGS["omnia_target_inactive"].format(state=state),
        "instruction": None if is_active 
                       else PREPARE_OIM_MSGS["omnia_target_inactive_instruction"].format(state=state)
    }


def get_omnia_target_dependencies() -> List[str]:
    """Get list of omnia.target dependencies."""
    target_name = PREPARE_OIM_VARS.get("omnia_target_name", "omnia.target")
    
    rc, stdout, _ = run_command(f"systemctl list-dependencies {target_name} --plain 2>/dev/null")
    
    if rc != 0 or not stdout:
        return []
    
    dependencies = [
        dep.strip() for dep in stdout.strip().split('\n')
        if dep.strip() and not dep.strip().startswith('●')
    ]
    
    return dependencies


def validate_omnia_target_dependencies() -> Dict:
    """Validate all omnia.target dependencies are running."""
    _log(PREPARE_OIM_MSGS["dependencies_check_start"], "INFO")
    
    dependencies = get_omnia_target_dependencies()
    
    if not dependencies:
        return {
            "passed": True,
            "dependencies": [],
            "inactive": [],
            "failed": [],
            "message": "No dependencies found"
        }
    
    inactive = []
    failed = []
    
    for dep in dependencies:
        # Skip special units
        if dep in ["-.mount", "system.slice"]:
            continue
        
        # Check if active
        rc, stdout, _ = run_command(f"systemctl is-active '{dep}' 2>/dev/null")
        status = stdout.strip()
        
        if status not in ["active", "static"]:
            inactive.append(f"{dep} ({status})")
        
        # Check if failed
        rc, stdout, _ = run_command(f"systemctl is-failed '{dep}' 2>/dev/null")
        if stdout.strip() == "failed":
            failed.append(dep)
    
    result = {
        "passed": True,
        "dependencies": dependencies,
        "inactive": inactive,
        "failed": failed
    }
    
    if failed:
        result["passed"] = False
        result["message"] = PREPARE_OIM_MSGS["dependencies_failed"].format(
            dependencies=", ".join(failed)
        )
        result["instruction"] = PREPARE_OIM_MSGS["dependencies_failed_instruction"].format(
            dependencies=", ".join(failed)
        )
        _log(result["message"], "ERROR")
    elif inactive:
        result["passed"] = False
        result["message"] = PREPARE_OIM_MSGS["dependencies_inactive"].format(
            dependencies=", ".join(inactive)
        )
        result["instruction"] = PREPARE_OIM_MSGS["dependencies_inactive_instruction"].format(
            dependencies=", ".join(inactive)
        )
        _log(result["message"], "ERROR")
    else:
        result["message"] = PREPARE_OIM_MSGS["dependencies_all_active"].format(
            count=len(dependencies)
        )
        _log(result["message"], "OK")
    
    return result


# =============================================================================
# Full Validation Workflow
# =============================================================================

def run_full_validation(run_playbook: bool = True) -> Dict:
    """
    Run the complete prepare_oim validation workflow.
    
    Steps:
    1. Test SSH connection
    2. Check omnia_core container
    3. Run prepare_oim playbook (optional)
    4. Validate OpenCHAMI containers
    5. Validate OpenCHAMI service
    6. Validate auth containers/service (if LDAP enabled)
    7. Validate omnia.target
    8. Validate omnia.target dependencies
    
    Args:
        run_playbook: Whether to run prepare_oim playbook (default: True)
    
    Returns:
        Dict with overall validation results
    """
    _log(PREPARE_OIM_MSGS["validation_start"], "INFO")
    
    results = {
        "ssh_connection": None,
        "omnia_core": None,
        "playbook": None,
        "openchami_containers": None,
        "openchami_service": None,
        "auth_containers": None,
        "auth_service": None,
        "omnia_target": None,
        "omnia_dependencies": None,
        "overall_passed": True,
        "failed_count": 0
    }
    
    # 1. Test SSH connection
    results["ssh_connection"] = test_ssh_connection()
    if not results["ssh_connection"].get("success"):
        results["overall_passed"] = False
        results["failed_count"] += 1
        return results
    
    # 2. Check omnia_core container
    results["omnia_core"] = check_omnia_core_status()
    if not results["omnia_core"].get("running"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    
    # 3. Run prepare_oim playbook (if requested and omnia_core is running)
    if run_playbook and results["omnia_core"].get("running"):
        results["playbook"] = run_prepare_oim_playbook()
        if not results["playbook"].get("success"):
            results["overall_passed"] = False
            results["failed_count"] += 1
    
    # 4. Validate OpenCHAMI containers
    results["openchami_containers"] = validate_openchami_containers()
    if not results["openchami_containers"].get("passed"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    
    # 5. Validate OpenCHAMI service
    results["openchami_service"] = validate_openchami_service()
    if not results["openchami_service"].get("passed"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    
    # 6. Validate auth containers (LDAP-dependent)
    results["auth_containers"] = validate_auth_containers()
    if not results["auth_containers"].get("passed") and not results["auth_containers"].get("skipped"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    
    # 7. Validate auth service (LDAP-dependent)
    results["auth_service"] = validate_auth_service()
    if not results["auth_service"].get("passed") and not results["auth_service"].get("skipped"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    
    # 8. Validate omnia.target
    results["omnia_target"] = validate_omnia_target()
    if not results["omnia_target"].get("passed"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    
    # 9. Validate omnia.target dependencies
    results["omnia_dependencies"] = validate_omnia_target_dependencies()
    if not results["omnia_dependencies"].get("passed"):
        results["overall_passed"] = False
        results["failed_count"] += 1
    
    # Summary
    _log(PREPARE_OIM_MSGS["validation_complete"], "INFO")
    
    if results["overall_passed"]:
        _log(PREPARE_OIM_MSGS["validation_all_passed"], "OK")
    else:
        _log(PREPARE_OIM_MSGS["validation_some_failed"].format(
            failed_count=results["failed_count"]
        ), "ERROR")
    
    return results
