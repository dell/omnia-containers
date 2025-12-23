"""System configuration functions for OIM prerequisite checks."""

import subprocess
from typing import Dict, List, Optional, Tuple

from ...core.formatting import log as _log
from ..messages.oim_prereq_msgs import OIM_PREREQ_MSGS
from ..vars.oim_prereq_vars import OIM_PREREQ_VARS


# Global flag for remote execution mode
_remote_mode = False
_ssh_prefix = ""


def _is_remote_mode() -> bool:
    """Check if running in remote mode."""
    oim_server = OIM_PREREQ_VARS.get("oim_server_ip", "")
    return (oim_server and oim_server.strip() and
            oim_server.lower() not in ["", "localhost", "127.0.0.1"])


def _get_ssh_command() -> str:
    """Build SSH command prefix for remote execution using sshpass for password auth."""
    oim_server = OIM_PREREQ_VARS.get("oim_server_ip", "")
    ssh_user = OIM_PREREQ_VARS.get("oim_ssh_user", "root")
    ssh_port = OIM_PREREQ_VARS.get("oim_ssh_port", 22)
    ssh_password = OIM_PREREQ_VARS.get("oim_ssh_password", "")

    ssh_opts = "-o StrictHostKeyChecking=no -o ConnectTimeout=10"

    if ssh_password:
        # Use sshpass for password authentication
        ssh_cmd = (f"sshpass -p '{ssh_password}' ssh {ssh_opts} "
                   f"-p {ssh_port} {ssh_user}@{oim_server}")
    else:
        # Use default SSH key authentication
        ssh_cmd = f"ssh {ssh_opts} -p {ssh_port} {ssh_user}@{oim_server}"

    return ssh_cmd


def run_command(cmd: List[str], timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """Execute a command and return (returncode, stdout, stderr).
    If remote mode is enabled, runs command on remote OIM server via SSH.
    """
    timeout = timeout or OIM_PREREQ_VARS["command_timeout"]

    if _is_remote_mode():
        # Run via SSH on remote server
        ssh_cmd = _get_ssh_command()
        remote_cmd = f"{ssh_cmd} '{' '.join(cmd)}'"
        _log(f"Running remote: {' '.join(cmd)}", "DEBUG")
        try:
            result = subprocess.run(remote_cmd, shell=True, capture_output=True,
                                   text=True, timeout=timeout)
            if result.returncode != 0:
                _log(f"Remote command failed with rc={result.returncode}", "DEBUG")
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            _log(f"Remote command timed out after {timeout}s", "ERROR")
            return -1, "", "Command timed out"
        except Exception as e:
            _log(f"Remote command exception: {str(e)}", "ERROR")
            return -1, "", str(e)
    else:
        # Run locally
        _log(f"Running command: {' '.join(cmd)}", "DEBUG")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                _log(f"Command failed with rc={result.returncode}", "DEBUG")
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            _log(f"Command timed out after {timeout}s", "ERROR")
            return -1, "", "Command timed out"
        except FileNotFoundError:
            _log(f"Command not found: {cmd[0]}", "ERROR")
            return -1, "", f"Command not found: {cmd[0]}"
        except Exception as e:
            _log(f"Command exception: {str(e)}", "ERROR")
            return -1, "", str(e)


def run_shell(cmd: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """Execute a shell command and return (returncode, stdout, stderr).
    If remote mode is enabled, runs command on remote OIM server via SSH.
    """
    timeout = timeout or OIM_PREREQ_VARS["command_timeout"]

    if _is_remote_mode():
        # Run via SSH on remote server - escape the command properly
        ssh_cmd = _get_ssh_command()
        # Escape single quotes in the command
        escaped_cmd = cmd.replace("'", "'\\''")
        remote_cmd = f"{ssh_cmd} '{escaped_cmd}'"
        _log(f"Running remote shell: {cmd}", "DEBUG")
        try:
            result = subprocess.run(remote_cmd, shell=True, capture_output=True,
                                   text=True, timeout=timeout)
            if result.returncode != 0:
                return result.returncode, result.stdout.strip(), result.stderr.strip()
            else:
                return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            _log(f"Remote shell command timed out after {timeout}s", "ERROR")
            return -1, "", "Command timed out"
        except Exception as e:
            _log(f"Remote shell exception: {str(e)}", "ERROR")
            return -1, "", str(e)
    else:
        # Run locally
        _log(f"Running shell: {cmd}", "DEBUG")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True,
                                   text=True, timeout=timeout)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            _log(f"Shell command timed out after {timeout}s", "ERROR")
            return -1, "", "Command timed out"
        except Exception as e:
            _log(f"Shell exception: {str(e)}", "ERROR")
            return -1, "", str(e)


def validate_ssh_connection() -> Dict:
    """Validate SSH connection to OIM server before executing any configuration."""
    if not _is_remote_mode():
        return {"valid": True, "message": OIM_PREREQ_MSGS["ssh_running_locally"]}

    oim_server = OIM_PREREQ_VARS.get("oim_server_ip", "")
    ssh_user = OIM_PREREQ_VARS.get("oim_ssh_user", "root")
    ssh_password = OIM_PREREQ_VARS.get("oim_ssh_password", "")

    # Check required SSH parameters
    if not oim_server or not oim_server.strip():
        return {
            "valid": False,
            "message": OIM_PREREQ_MSGS["oim_server_not_configured"],
            "details": OIM_PREREQ_MSGS["oim_server_not_configured_details"]
        }

    if not ssh_password or not ssh_password.strip():
        return {
            "valid": False,
            "message": OIM_PREREQ_MSGS["ssh_password_not_configured"],
            "details": OIM_PREREQ_MSGS["ssh_password_not_configured_details"]
        }

    # Test SSH connection
    _log(OIM_PREREQ_MSGS["ssh_connection_test_start"].format(
        user=ssh_user, server=oim_server), "INFO")
    rc, _, stderr = run_shell("echo 'SSH connection test'")

    if rc == 0:
        _log(OIM_PREREQ_MSGS["ssh_connection_success"].format(
            user=ssh_user, server=oim_server), "OK")
        return {"valid": True, "message": OIM_PREREQ_MSGS["ssh_connection_success"].format(
            user=ssh_user, server=oim_server)}
    else:
        return {
            "valid": False,
            "message": OIM_PREREQ_MSGS["ssh_connection_failed"].format(
                user=ssh_user, server=oim_server),
            "details": OIM_PREREQ_MSGS["ssh_connection_error"].format(
                error=stderr or 'Authentication or network failure')
        }


def configure_hostname() -> Dict:
    """
    Configure hostname on the OIM server.

    This is the FIRST task that runs before all other checks.
    Sets the hostname using hostnamectl and verifies it has a domain.

    Returns:
        Dict with 'passed', 'configured', 'hostname', 'domain', 'message'
    """
    _log(OIM_PREREQ_MSGS["hostname_check_start"], "INFO")

    target_hostname = OIM_PREREQ_VARS.get("oim_hostname", "")

    # Check if hostname is configured in user_config.yml
    if not target_hostname:
        return {
            "passed": False,
            "configured": False,
            "hostname": "",
            "domain": "",
            "message": OIM_PREREQ_MSGS["hostname_not_configured"],
            "instruction": OIM_PREREQ_MSGS["hostname_instruction"]
        }

    # Validate hostname format (must contain a dot for domain)
    if "." not in target_hostname:
        return {
            "passed": False,
            "configured": False,
            "hostname": target_hostname,
            "domain": "",
            "message": OIM_PREREQ_MSGS["hostname_invalid"],
            "instruction": OIM_PREREQ_MSGS["hostname_instruction"]
        }

    # Get current hostname
    rc, current_hostname, _ = run_command(["hostname", "-f"])
    current_hostname = current_hostname.strip() if rc == 0 else ""

    _log(f"Current hostname: {current_hostname or 'not set'}", "INFO")
    _log(f"Target hostname: {target_hostname}", "INFO")

    # Check if already configured correctly
    if current_hostname == target_hostname:
        # Verify domain
        rc, domain, _ = run_command(["hostname", "-d"])
        domain = domain.strip() if rc == 0 else ""

        if domain:
            _log(OIM_PREREQ_MSGS["hostname_already_set"].format(hostname=target_hostname), "OK")
            return {
                "passed": True,
                "configured": True,
                "already_configured": True,
                "hostname": target_hostname,
                "domain": domain,
                "message": OIM_PREREQ_MSGS["hostname_already_set"].format(hostname=target_hostname),
                "details": f"Domain: {domain}"
            }

    # Set the hostname
    _log(OIM_PREREQ_MSGS["hostname_set_start"].format(hostname=target_hostname), "INFO")

    rc, _, stderr = run_command(["hostnamectl", "set-hostname", target_hostname])
    if rc != 0:
        return {
            "passed": False,
            "configured": False,
            "hostname": target_hostname,
            "domain": "",
            "message": OIM_PREREQ_MSGS["hostname_set_fail"].format(error=stderr),
            "instruction": OIM_PREREQ_MSGS["hostname_manual_instruction"].format(
                hostname=target_hostname, error=stderr
            )
        }

    # Verify the hostname was set
    rc, new_hostname, _ = run_command(["hostname", "-f"])
    new_hostname = new_hostname.strip() if rc == 0 else ""

    rc, domain, _ = run_command(["hostname", "-d"])
    domain = domain.strip() if rc == 0 else ""

    if new_hostname == target_hostname and domain:
        _log(OIM_PREREQ_MSGS["hostname_set_pass"].format(hostname=target_hostname), "OK")
        return {
            "passed": True,
            "configured": True,
            "already_configured": False,
            "hostname": new_hostname,
            "domain": domain,
            "message": OIM_PREREQ_MSGS["hostname_set_pass"].format(hostname=target_hostname),
            "details": f"Domain: {domain}"
        }

    # Hostname set but verification failed
    return {
        "passed": False,
        "configured": False,
        "hostname": new_hostname or target_hostname,
        "domain": domain,
        "message": (f"Hostname set but verification failed. "
                    f"Expected: {target_hostname}, Got: {new_hostname}"),
        "instruction": OIM_PREREQ_MSGS["hostname_manual_instruction"].format(
            hostname=target_hostname, error="Verification failed"
        )
    }
