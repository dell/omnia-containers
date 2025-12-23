"""
Omnia.sh Test - Core Functions.

This module contains all functions for running and verifying omnia.sh.
Test functions should call these functions - all logic resides here.

Usage:
    from automation_library.functions.omnia_sh_func import (
        check_prerequisites,
        run_omnia_sh_install,
        verify_container_running,
        verify_ssh_connection,
        cleanup_omnia,
        # Test verification functions
        check_container_running,
        check_file_exists,
        check_service_running,
        check_ssh_to_container,
        check_ssh_from_container,
    )

Author: Dell Technologies
"""

import os
import subprocess
import time
from typing import Dict, Any, Tuple, Optional

from ..vars.omnia_sh_vars import OMNIA_SH_VARS, get_omnia_sh_path, validate_config
from ..messages.omnia_sh_msgs import OMNIA_SH_MSGS, TEST_VARS
from ...core.formatting import log as _log


# =============================================================================
# SHELL COMMAND EXECUTION
# =============================================================================

def run_command(cmd: list, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """
    Execute a command and return (returncode, stdout, stderr).

    Args:
        cmd: Command as list of strings
        timeout: Timeout in seconds (default from config)

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    timeout = timeout or OMNIA_SH_VARS["command_timeout"]
    _log(f"Running: {' '.join(cmd)}", "DEBUG")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        _log(f"Command timed out after {timeout}s", "ERROR")
        return -1, "", "Command timed out"
    except Exception as e:
        _log(f"Command failed: {str(e)}", "ERROR")
        return -1, "", str(e)


def run_shell(cmd: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command and return (returncode, stdout, stderr).

    Args:
        cmd: Command as string
        timeout: Timeout in seconds (default from config)

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    timeout = timeout or OMNIA_SH_VARS["command_timeout"]
    _log(f"Running shell: {cmd}", "DEBUG")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        _log(f"Command timed out after {timeout}s", "ERROR")
        return -1, "", "Command timed out"
    except Exception as e:
        _log(f"Command failed: {str(e)}", "ERROR")
        return -1, "", str(e)


def run_interactive(cmd: str, inputs: list, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """
    Execute an interactive command with predefined inputs.

    Args:
        cmd: Command as string
        inputs: List of inputs to provide (each followed by newline)
        timeout: Timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    timeout = timeout or OMNIA_SH_VARS["install_timeout"]
    _log(f"Running interactive: {cmd}", "DEBUG")

    try:
        # Join inputs with newlines
        input_str = "\n".join(inputs) + "\n"

        process = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input=input_str, timeout=timeout)
        return process.returncode, stdout.strip(), stderr.strip()

    except subprocess.TimeoutExpired:
        process.kill()
        _log(f"Interactive command timed out after {timeout}s", "ERROR")
        return -1, "", "Command timed out"
    except Exception as e:
        _log(f"Interactive command failed: {str(e)}", "ERROR")
        return -1, "", str(e)


# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================

def check_podman() -> Dict[str, Any]:
    """
    Check if Podman is installed.

    Returns:
        Dict with 'installed' (bool), 'version' (str), 'message' (str)
    """
    _log("Checking Podman installation...", "INFO")

    rc, stdout, _ = run_command(["podman", "--version"])

    if rc == 0:
        version = stdout.replace("podman version ", "")
        _log(OMNIA_SH_MSGS["podman_installed"].format(version=version), "OK")
        return {
            "installed": True,
            "version": version,
            "message": OMNIA_SH_MSGS["podman_installed"].format(version=version)
        }

    _log(OMNIA_SH_MSGS["podman_not_installed"], "ERROR")
    return {
        "installed": False,
        "version": "",
        "message": OMNIA_SH_MSGS["podman_not_installed"],
        "instruction": OMNIA_SH_MSGS["podman_install_instruction"]
    }


def check_hostname() -> Dict[str, Any]:
    """
    Check if hostname is configured with domain.

    Returns:
        Dict with 'valid' (bool), 'hostname' (str), 'domain' (str), 'message' (str)
    """
    _log("Checking hostname configuration...", "INFO")

    # Get hostname
    rc, hostname, _ = run_command(["hostname"])
    if rc != 0 or not hostname:
        return {
            "valid": False,
            "hostname": "",
            "domain": "",
            "message": OMNIA_SH_MSGS["hostname_invalid"],
            "instruction": OMNIA_SH_MSGS["hostname_instruction"]
        }

    # Get domain
    rc, domain, _ = run_command(["hostname", "-d"])
    if rc != 0 or not domain:
        return {
            "valid": False,
            "hostname": hostname,
            "domain": "",
            "message": OMNIA_SH_MSGS["hostname_invalid"],
            "instruction": OMNIA_SH_MSGS["hostname_instruction"]
        }

    _log(OMNIA_SH_MSGS["hostname_valid"].format(hostname=f"{hostname}"), "OK")
    return {
        "valid": True,
        "hostname": hostname,
        "domain": domain,
        "message": OMNIA_SH_MSGS["hostname_valid"].format(hostname=hostname)
    }


def check_omnia_core_image() -> Dict[str, Any]:
    """
    Check if omnia_core image exists locally.

    Returns:
        Dict with 'found' (bool), 'image' (str), 'tag' (str), 'message' (str)
    """
    _log("Checking omnia_core image...", "INFO")

    tag = OMNIA_SH_VARS["container_image_tag"]

    # Check for image with specific tag
    rc, stdout, _ = run_shell(
        f"podman images --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | "
        f"grep -E 'omnia_core:{tag}'"
    )

    if rc == 0 and stdout:
        _log(OMNIA_SH_MSGS["image_found"].format(image="omnia_core", tag=tag), "OK")
        return {
            "found": True,
            "image": "omnia_core",
            "tag": tag,
            "message": OMNIA_SH_MSGS["image_found"].format(
                image="omnia_core", tag=tag
            )
        }

    # Check for latest tag as fallback
    rc, stdout, _ = run_shell(
        "podman images --format '{{.Repository}}:{{.Tag}}' | "
        "grep -E 'omnia_core:latest'"
    )

    if rc == 0 and stdout:
        _log(OMNIA_SH_MSGS["image_found"].format(image="omnia_core", tag="latest"), "OK")
        return {
            "found": True,
            "image": "omnia_core",
            "tag": "latest",
            "message": OMNIA_SH_MSGS["image_found"].format(image="omnia_core", tag="latest")
        }

    _log(OMNIA_SH_MSGS["image_not_found"], "WARN")
    return {
        "found": False,
        "image": "",
        "tag": "",
        "message": OMNIA_SH_MSGS["image_not_found"],
        "instruction": OMNIA_SH_MSGS["image_build_instruction"]
    }


def check_omnia_sh_exists(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if omnia.sh script exists at the given path.

    Args:
        path: Path to omnia.sh (default: from config)

    Returns:
        Dict with 'exists' (bool), 'path' (str), 'message' (str)
    """
    path = path or get_omnia_sh_path()
    _log(f"Checking omnia.sh at {path}...", "INFO")

    if os.path.isfile(path):
        _log(OMNIA_SH_MSGS["omnia_sh_found"].format(path=path), "OK")
        return {
            "exists": True,
            "path": path,
            "message": OMNIA_SH_MSGS["omnia_sh_found"].format(path=path)
        }

    _log(OMNIA_SH_MSGS["omnia_sh_not_found"].format(path=path), "ERROR")
    return {
        "exists": False,
        "path": path,
        "message": OMNIA_SH_MSGS["omnia_sh_not_found"].format(path=path),
        "instruction": OMNIA_SH_MSGS["omnia_sh_not_found_instruction"]
    }


def check_prerequisites() -> Dict[str, Any]:
    """
    Run all prerequisite checks.

    Returns:
        Dict with 'passed' (bool), 'checks' (list of check results)
    """
    _log(OMNIA_SH_MSGS["prereq_check_start"], "INFO")

    checks = []
    all_passed = True

    # Validate config
    config_result = validate_config()
    if not config_result["valid"]:
        for error in config_result["errors"]:
            _log(OMNIA_SH_MSGS["config_error"].format(error=error), "ERROR")
        checks.append({"name": "Configuration", "passed": False, "errors": config_result["errors"]})
        all_passed = False
    else:
        _log(OMNIA_SH_MSGS["config_valid"], "OK")
        checks.append({"name": "Configuration", "passed": True})

    # Check Podman
    podman_result = check_podman()
    checks.append({"name": "Podman", "passed": podman_result["installed"], "details": podman_result})
    if not podman_result["installed"]:
        all_passed = False

    # Check hostname
    hostname_result = check_hostname()
    checks.append({"name": "Hostname", "passed": hostname_result["valid"], "details": hostname_result})
    if not hostname_result["valid"]:
        all_passed = False

    # Check image (warning only, not a failure)
    image_result = check_omnia_core_image()
    checks.append({"name": "Omnia Core Image", "passed": image_result["found"], "details": image_result})

    # Check omnia.sh exists
    omnia_sh_result = check_omnia_sh_exists()
    checks.append({"name": "omnia.sh", "passed": omnia_sh_result["exists"], "details": omnia_sh_result})
    if not omnia_sh_result["exists"]:
        all_passed = False

    if all_passed:
        _log(OMNIA_SH_MSGS["prereq_check_pass"], "OK")
    else:
        _log(OMNIA_SH_MSGS["prereq_check_fail"], "ERROR")

    return {
        "passed": all_passed,
        "checks": checks
    }


# =============================================================================
# OMNIA.SH EXECUTION
# =============================================================================

def build_install_inputs() -> list:
    """
    Build the list of inputs for omnia.sh --install based on configuration.
    Uses values from user_config.yml (NFS IP, path, password).

    Returns:
        List of input strings to provide to the interactive script
    """
    inputs = []
    share_option = OMNIA_SH_VARS["share_option"]

    if share_option == "Local":
        # Select "Local" option (option 2)
        inputs.append("2")
        # Provide shared path
        inputs.append(OMNIA_SH_VARS["omnia_shared_path"])

    elif share_option == "NFS":
        # Select "NFS" option (option 1)
        inputs.append("1")

        nfs_type = OMNIA_SH_VARS["nfs_type"]
        if nfs_type == "external":
            # Select "External" (option 1)
            inputs.append("1")
            # Provide NFS server IP (from user_config.yml nfs_server_ip)
            inputs.append(OMNIA_SH_VARS["nfs_server_ip"])
            # Provide NFS share path (from user_config.yml nfs_share_path)
            inputs.append(OMNIA_SH_VARS["nfs_share_path"])
            # Provide local mount path (same as NFS share path)
            inputs.append(OMNIA_SH_VARS["omnia_shared_path"])
        else:
            # Select "Internal" (option 2)
            inputs.append("2")
            # Provide OIM server IP
            inputs.append(OMNIA_SH_VARS["nfs_server_ip"])
            # Provide OIM share path
            inputs.append(OMNIA_SH_VARS["nfs_share_path"])

    # Provide password (from user_config.yml oim_ssh_password)
    inputs.append(OMNIA_SH_VARS["omnia_core_password"])
    # Confirm password
    inputs.append(OMNIA_SH_VARS["omnia_core_password"])

    return inputs


def run_omnia_sh_install(omnia_sh_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run omnia.sh --install with configured inputs.

    Args:
        omnia_sh_path: Path to omnia.sh script (default: from config)

    Returns:
        Dict with 'success' (bool), 'output' (str), 'message' (str)
    """
    omnia_sh_path = omnia_sh_path or get_omnia_sh_path()
    _log(OMNIA_SH_MSGS["install_start"], "INFO")

    # Check if script exists
    if not os.path.isfile(omnia_sh_path):
        return {
            "success": False,
            "output": "",
            "message": OMNIA_SH_MSGS["omnia_sh_not_found"].format(path=omnia_sh_path),
            "instruction": OMNIA_SH_MSGS["omnia_sh_not_found_instruction"]
        }

    # Make script executable
    run_shell(f"chmod +x {omnia_sh_path}")

    # Build inputs from user_config.yml values
    inputs = build_install_inputs()
    _log(f"Prepared {len(inputs)} inputs for interactive install", "DEBUG")
    _log(f"Share option: {OMNIA_SH_VARS['share_option']}", "DEBUG")

    # Run install
    cmd = f"{omnia_sh_path} --install"
    timeout = OMNIA_SH_VARS["install_timeout"]

    rc, stdout, stderr = run_interactive(cmd, inputs, timeout)

    if rc == 0:
        _log(OMNIA_SH_MSGS["install_success"], "OK")
        return {
            "success": True,
            "output": stdout,
            "message": OMNIA_SH_MSGS["install_success"]
        }

    error_msg = stderr or stdout or "Unknown error"
    _log(OMNIA_SH_MSGS["install_fail"], "ERROR")
    return {
        "success": False,
        "output": stdout,
        "error": error_msg,
        "message": OMNIA_SH_MSGS["install_fail"],
        "instruction": OMNIA_SH_MSGS["install_instruction"].format(error=error_msg)
    }


def run_omnia_sh_uninstall(omnia_sh_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run omnia.sh --uninstall.

    Args:
        omnia_sh_path: Path to omnia.sh script (default: from config)

    Returns:
        Dict with 'success' (bool), 'output' (str), 'message' (str)
    """
    omnia_sh_path = omnia_sh_path or get_omnia_sh_path()
    _log(OMNIA_SH_MSGS["uninstall_start"], "INFO")

    # Run uninstall with 'y' confirmation
    cmd = f"{omnia_sh_path} --uninstall"
    rc, stdout, stderr = run_interactive(cmd, ["y"], timeout=120)

    if rc == 0:
        _log(OMNIA_SH_MSGS["uninstall_success"], "OK")
        return {
            "success": True,
            "output": stdout,
            "message": OMNIA_SH_MSGS["uninstall_success"]
        }

    _log(OMNIA_SH_MSGS["uninstall_fail"], "ERROR")
    return {
        "success": False,
        "output": stdout,
        "error": stderr or stdout,
        "message": OMNIA_SH_MSGS["uninstall_fail"]
    }


# =============================================================================
# CONTAINER VERIFICATION
# =============================================================================

def verify_container_running() -> Dict[str, Any]:
    """
    Verify that omnia_core container is running.

    Returns:
        Dict with 'running' (bool), 'state' (str), 'message' (str)
    """
    _log(OMNIA_SH_MSGS["container_check_start"], "INFO")

    container_name = OMNIA_SH_VARS["container_name"]

    # Check if container exists and get its state
    rc, stdout, _ = run_shell(f"podman ps -a --format '{{{{.Names}}}} {{{{.State}}}}' | grep -E '^{container_name} '")

    if rc != 0 or not stdout:
        _log(OMNIA_SH_MSGS["container_not_found"].format(container_name=container_name), "ERROR")
        return {
            "running": False,
            "state": "not_found",
            "message": OMNIA_SH_MSGS["container_not_found"].format(container_name=container_name),
            "instruction": OMNIA_SH_MSGS["container_instruction"].format(container_name=container_name)
        }

    # Parse state
    parts = stdout.split()
    state = parts[1] if len(parts) > 1 else "unknown"

    if state.lower() == "running":
        _log(OMNIA_SH_MSGS["container_running"].format(container_name=container_name), "OK")
        return {
            "running": True,
            "state": state,
            "message": OMNIA_SH_MSGS["container_running"].format(container_name=container_name)
        }

    _log(OMNIA_SH_MSGS["container_not_running"].format(container_name=container_name), "ERROR")
    return {
        "running": False,
        "state": state,
        "message": OMNIA_SH_MSGS["container_not_running"].format(container_name=container_name),
        "instruction": OMNIA_SH_MSGS["container_instruction"].format(container_name=container_name)
    }


def wait_for_container(timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Wait for omnia_core container to start.

    Args:
        timeout: Timeout in seconds (default from config)

    Returns:
        Dict with 'started' (bool), 'elapsed' (int), 'message' (str)
    """
    timeout = timeout or OMNIA_SH_VARS["container_start_timeout"]
    _ = OMNIA_SH_VARS["container_name"]

    _log(OMNIA_SH_MSGS["container_wait_start"].format(timeout=timeout), "INFO")

    start_time = time.time()
    while time.time() - start_time < timeout:
        result = verify_container_running()
        if result["running"]:
            elapsed = int(time.time() - start_time)
            _log(OMNIA_SH_MSGS["container_wait_success"], "OK")
            return {
                "started": True,
                "elapsed": elapsed,
                "message": OMNIA_SH_MSGS["container_wait_success"]
            }
        time.sleep(2)

    elapsed = int(time.time() - start_time)
    _log(OMNIA_SH_MSGS["container_wait_timeout"].format(timeout=timeout), "ERROR")
    return {
        "started": False,
        "elapsed": elapsed,
        "message": OMNIA_SH_MSGS["container_wait_timeout"].format(timeout=timeout)
    }


# =============================================================================
# SSH VERIFICATION
# =============================================================================

def verify_ssh_connection() -> Dict[str, Any]:
    """
    Verify SSH connection to omnia_core container.

    Returns:
        Dict with 'connected' (bool), 'message' (str)
    """
    _log(OMNIA_SH_MSGS["ssh_check_start"], "INFO")

    ssh_port = OMNIA_SH_VARS["ssh_port"]

    # Try SSH connection using the omnia_core alias (uses ssh config)
    rc, stdout, _ = run_shell(
        "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 omnia_core 'echo SSH_OK'",
        timeout=30
    )

    if rc == 0 and "SSH_OK" in stdout:
        _log(OMNIA_SH_MSGS["ssh_check_pass"], "OK")
        return {
            "connected": True,
            "message": OMNIA_SH_MSGS["ssh_check_pass"]
        }

    _log(OMNIA_SH_MSGS["ssh_check_fail"], "ERROR")
    return {
        "connected": False,
        "message": OMNIA_SH_MSGS["ssh_check_fail"],
        "instruction": OMNIA_SH_MSGS["ssh_instruction"].format(ssh_port=ssh_port)
    }


# =============================================================================
# DIRECTORY VERIFICATION
# =============================================================================

def verify_directories() -> Dict[str, Any]:
    """
    Verify that required directories were created.

    Returns:
        Dict with 'all_exist' (bool), 'directories' (list), 'message' (str)
    """
    _log(OMNIA_SH_MSGS["dir_check_start"], "INFO")

    omnia_path = OMNIA_SH_VARS["omnia_shared_path"]

    required_dirs = [
        f"{omnia_path}/omnia",
        f"{omnia_path}/omnia/ssh_config/.ssh",
        f"{omnia_path}/omnia/log/core/container",
        f"{omnia_path}/omnia/input",
        f"{omnia_path}/omnia/.data",
    ]

    results = []
    all_exist = True

    for dir_path in required_dirs:
        exists = os.path.isdir(dir_path)
        results.append({
            "path": dir_path,
            "exists": exists
        })

        if exists:
            _log(OMNIA_SH_MSGS["dir_exists"].format(path=dir_path), "OK")
        else:
            _log(OMNIA_SH_MSGS["dir_not_exists"].format(path=dir_path), "ERROR")
            all_exist = False

    return {
        "all_exist": all_exist,
        "directories": results,
        "message": "All directories exist" if all_exist else "Some directories missing"
    }


# =============================================================================
# CLEANUP
# =============================================================================

def cleanup_omnia(omnia_sh_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Cleanup omnia_core container and configuration.

    Args:
        omnia_sh_path: Path to omnia.sh script (default: from config)

    Returns:
        Dict with 'success' (bool), 'message' (str)
    """
    if not OMNIA_SH_VARS["cleanup_after_test"]:
        _log(OMNIA_SH_MSGS["cleanup_skip"], "INFO")
        return {
            "success": True,
            "skipped": True,
            "message": OMNIA_SH_MSGS["cleanup_skip"]
        }

    _log(OMNIA_SH_MSGS["cleanup_start"], "INFO")

    omnia_sh_path = omnia_sh_path or get_omnia_sh_path()

    # Run uninstall
    result = run_omnia_sh_uninstall(omnia_sh_path)

    if result["success"]:
        _log(OMNIA_SH_MSGS["cleanup_success"], "OK")
        return {
            "success": True,
            "skipped": False,
            "message": OMNIA_SH_MSGS["cleanup_success"]
        }

    _log(OMNIA_SH_MSGS["cleanup_fail"].format(error=result.get("error", "")), "ERROR")
    return {
        "success": False,
        "skipped": False,
        "message": OMNIA_SH_MSGS["cleanup_fail"].format(error=result.get("error", ""))
    }


# =============================================================================
# FULL TEST EXECUTION
# =============================================================================

def run_full_test(omnia_sh_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the complete omnia.sh test suite.

    Args:
        omnia_sh_path: Path to omnia.sh script (default: from config)

    Returns:
        Dict with 'passed' (bool), 'results' (list), 'summary' (str)
    """
    omnia_sh_path = omnia_sh_path or get_omnia_sh_path()
    _log(OMNIA_SH_MSGS["test_start"], "INFO")

    results = []
    total = 0
    passed = 0
    failed = 0

    # 1. Check prerequisites
    prereq_result = check_prerequisites()
    results.append({"name": "Prerequisites", "passed": prereq_result["passed"], "details": prereq_result})
    total += 1
    if prereq_result["passed"]:
        passed += 1
    else:
        failed += 1
        return _build_test_result(results, total, passed, failed)

    # 2. Run install
    install_result = run_omnia_sh_install(omnia_sh_path)
    results.append({"name": "omnia.sh --install", "passed": install_result["success"], "details": install_result})
    total += 1
    if install_result["success"]:
        passed += 1
    else:
        failed += 1
        return _build_test_result(results, total, passed, failed)

    # 3. Wait for container
    wait_result = wait_for_container()
    results.append({"name": "Container started", "passed": wait_result["started"], "details": wait_result})
    total += 1
    if wait_result["started"]:
        passed += 1
    else:
        failed += 1

    # 4. Verify container running
    container_result = verify_container_running()
    results.append({"name": "Container running", "passed": container_result["running"], "details": container_result})
    total += 1
    if container_result["running"]:
        passed += 1
    else:
        failed += 1

    # 5. Verify SSH
    ssh_result = verify_ssh_connection()
    results.append({"name": "SSH connection", "passed": ssh_result["connected"], "details": ssh_result})
    total += 1
    if ssh_result["connected"]:
        passed += 1
    else:
        failed += 1

    # 6. Verify directories
    dir_result = verify_directories()
    results.append({"name": "Directories created", "passed": dir_result["all_exist"], "details": dir_result})
    total += 1
    if dir_result["all_exist"]:
        passed += 1
    else:
        failed += 1

    # 7. Cleanup (optional)
    cleanup_result = cleanup_omnia(omnia_sh_path)
    results.append({"name": "Cleanup", "passed": cleanup_result["success"], "details": cleanup_result})
    total += 1
    if cleanup_result["success"]:
        passed += 1
    else:
        failed += 1

    return _build_test_result(results, total, passed, failed)


def _build_test_result(results: list, total: int, passed: int, failed: int) -> Dict[str, Any]:
    """Build the final test result dictionary."""
    all_passed = failed == 0

    if all_passed:
        _log(OMNIA_SH_MSGS["test_pass"], "OK")
    else:
        _log(OMNIA_SH_MSGS["test_fail"].format(failed_count=failed), "ERROR")

    summary = OMNIA_SH_MSGS["test_summary"].format(total=total, passed=passed, failed=failed)
    _log(summary, "INFO")

    return {
        "passed": all_passed,
        "total": total,
        "passed_count": passed,
        "failed_count": failed,
        "results": results,
        "summary": summary
    }


# =============================================================================
# TEST VERIFICATION FUNCTIONS (for pytest/testinfra)
# =============================================================================
# These functions are called by test_omnia_sh.py to verify installation.
# They return structured results that the test file uses for assertions.

def check_container_running(host) -> Dict[str, Any]:
    """
    Check if omnia_core container is running.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'details', 'error'
    """
    container_name = OMNIA_SH_VARS["container_name"]

    cmd = host.run(f"podman ps --format '{{{{.Names}}}} {{{{.Status}}}}' | grep {container_name}")

    if cmd.rc == 0 and container_name in cmd.stdout:
        # Get detailed info
        status_cmd = host.run(
            f"podman ps --format '{{{{.Names}}}}|{{{{.Status}}}}|{{{{.Image}}}}|{{{{.Ports}}}}' | grep {container_name}"
        )
        parts = status_cmd.stdout.strip().split('|')

        return {
            "success": True,
            "details": {
                "container": parts[0] if len(parts) > 0 else container_name,
                "status": parts[1] if len(parts) > 1 else "unknown",
                "image": parts[2] if len(parts) > 2 else "unknown",
                "ports": parts[3] if len(parts) > 3 else "none",
            },
            "error": None
        }

    # Check if exists but not running
    exists_cmd = host.run(f"podman ps -a --format '{{{{.Names}}}} {{{{.Status}}}}' | grep {container_name}")
    if exists_cmd.rc == 0:
        return {
            "success": False,
            "details": None,
            "error": f"Container exists but not running: {exists_cmd.stdout.strip()}"
        }

    return {
        "success": False,
        "details": None,
        "error": "Container does not exist"
    }


def check_file_exists(host, path: str) -> Dict[str, Any]:
    """
    Check if a file exists on the remote host.

    Args:
        host: testinfra host object
        path: file path to check

    Returns:
        Dict with 'success', 'details', 'error'
    """
    f = host.file(path)

    if f.exists:
        info = host.run(f"ls -la {path}").stdout.strip()
        return {
            "success": True,
            "details": info,
            "error": None
        }

    return {
        "success": False,
        "details": None,
        "error": f"File not found: {path}"
    }


def check_service_running(host, service_name: str = None) -> Dict[str, Any]:
    """
    Check if a systemd service is running.

    Args:
        host: testinfra host object
        service_name: service name (default: omnia_core.service)

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    service_name = service_name or TEST_VARS["service_name"]

    status = host.run(f"systemctl is-active {service_name}").stdout.strip()
    info = host.run(f"systemctl status {service_name} --no-pager -l 2>/dev/null | head -10").stdout.strip()

    if status == "active":
        return {
            "success": True,
            "status": status,
            "details": info,
            "error": None
        }

    return {
        "success": False,
        "status": status,
        "details": info,
        "error": f"Service is {status}"
    }


def check_ssh_to_container(host, timeout: int = 5) -> Dict[str, Any]:
    """
    Check passwordless SSH from OIM server to omnia_core container.

    Args:
        host: testinfra host object
        timeout: SSH connection timeout

    Returns:
        Dict with 'success', 'details', 'error'
    """
    alias = TEST_VARS["ssh_alias"]

    cmd = host.run(f"ssh -o BatchMode=yes -o ConnectTimeout={timeout} {alias} 'whoami && pwd && echo SSH_OK'")
    output = cmd.stdout.strip()

    if cmd.rc == 0 and "SSH_OK" in output:
        lines = output.split('\n')
        return {
            "success": True,
            "details": {
                "user": lines[0] if len(lines) > 0 else "unknown",
                "workdir": lines[1] if len(lines) > 1 else "unknown",
                "connection": "passwordless (no password prompt)"
            },
            "error": None
        }

    return {
        "success": False,
        "details": None,
        "error": cmd.stderr.strip() or "SSH connection failed"
    }


def check_ssh_from_container(host, oim_ip: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Check passwordless SSH from omnia_core container back to OIM server.

    Args:
        host: testinfra host object
        oim_ip: OIM server IP address
        timeout: SSH connection timeout

    Returns:
        Dict with 'success', 'details', 'error'
    """
    alias = TEST_VARS["ssh_alias"]

    cmd = host.run(
        f"ssh -o BatchMode=yes -o ConnectTimeout={timeout} {alias} "
        f"'ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} {oim_ip} "
        f"whoami && echo SSH_REVERSE_OK'"
    )
    output = cmd.stdout.strip()

    if cmd.rc == 0 and "SSH_REVERSE_OK" in output:
        lines = output.split('\n')
        return {
            "success": True,
            "details": {
                "user": lines[0] if len(lines) > 0 else "unknown",
                "target": oim_ip,
                "connection": "passwordless (key-based auth)"
            },
            "error": None
        }

    return {
        "success": False,
        "details": None,
        "error": cmd.stderr.strip() or "Reverse SSH connection failed"
    }


def check_metadata_file(host) -> Dict[str, Any]:
    """
    Check if oim_metadata.yml file exists and return its content.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'details', 'error'
    """
    path = TEST_VARS["metadata_file"]
    f = host.file(path)

    if f.exists:
        content = host.run(f"head -15 {path}").stdout.strip()
        return {
            "success": True,
            "details": content,
            "error": None
        }

    return {
        "success": False,
        "details": None,
        "error": f"Metadata file not found: {path}"
    }


# =============================================================================
# CLEANUP VERIFICATION FUNCTIONS (for pytest/testinfra)
# =============================================================================
# These functions verify that cleanup was successful.

def check_container_not_running(host) -> Dict[str, Any]:
    """
    Verify omnia_core container is NOT running (cleanup verification).

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'details', 'error'
    """
    container_name = OMNIA_SH_VARS["container_name"]

    # Check if container is running
    cmd = host.run(f"podman ps --format '{{{{.Names}}}}' | grep -q {container_name}")

    if cmd.rc != 0:
        # Container not running - good
        return {
            "success": True,
            "details": f"Container {container_name} is not running",
            "error": None
        }

    return {
        "success": False,
        "details": None,
        "error": f"Container {container_name} is still running"
    }


def check_service_not_exists(host) -> Dict[str, Any]:
    """
    Verify omnia_core.service file does NOT exist (cleanup verification).

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'details', 'error'
    """
    service_file = TEST_VARS["container_file"]  # /etc/containers/systemd/omnia_core.container

    f = host.file(service_file)

    if not f.exists:
        return {
            "success": True,
            "details": f"Service file {service_file} removed",
            "error": None
        }

    return {
        "success": False,
        "details": None,
        "error": f"Service file still exists: {service_file}"
    }


def check_fstab_entry_removed(host, omnia_shared_path: str = None) -> Dict[str, Any]:
    """
    Verify fstab entry for omnia_shared_path is removed (cleanup verification).

    Args:
        host: testinfra host object
        omnia_shared_path: path to check in fstab (default from config)

    Returns:
        Dict with 'success', 'details', 'error'
    """
    if omnia_shared_path is None:
        omnia_shared_path = OMNIA_SH_VARS.get("omnia_shared_path", "/opt/omnia")

    cmd = host.run(f"grep -E '\\s+{omnia_shared_path}\\s+' /etc/fstab")

    if cmd.rc != 0:
        # No entry found - good
        return {
            "success": True,
            "details": f"No fstab entry for {omnia_shared_path}",
            "error": None
        }

    return {
        "success": False,
        "details": None,
        "error": f"fstab entry still exists: {cmd.stdout.strip()}"
    }


def check_mount_removed(host, omnia_shared_path: str = None) -> Dict[str, Any]:
    """
    Verify omnia_shared_path is NOT mounted (cleanup verification).

    Args:
        host: testinfra host object
        omnia_shared_path: path to check (default from config)

    Returns:
        Dict with 'success', 'details', 'error'
    """
    if omnia_shared_path is None:
        omnia_shared_path = OMNIA_SH_VARS.get("omnia_shared_path", "/opt/omnia")

    cmd = host.run(f"mountpoint -q {omnia_shared_path}")

    if cmd.rc != 0:
        # Not a mount point - good
        return {
            "success": True,
            "details": f"{omnia_shared_path} is not mounted",
            "error": None
        }

    return {
        "success": False,
        "details": None,
        "error": f"{omnia_shared_path} is still mounted"
    }
