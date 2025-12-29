"""Functions for OIM prerequisite checks with detailed reporting."""

import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ...core.formatting import Colors, Symbols, log as _log
from ..messages.oim_prereq_msgs import OIM_PREREQ_MSGS
from ..vars.oim_prereq_vars import OIM_PREREQ_VARS, USER_CONFIG_PATH


# =============================================================================
# Report Generator
# =============================================================================

class PrereqReport:
    """Generate detailed prerequisite check report with Linux theme."""

    WIDTH = 80  # Terminal width
    TOTAL_CHECKS = 14  # Total number of checks in the full suite (added hostname)

    def __init__(self):
        self.start_time = datetime.now()
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.check_number = 0

    def _box_top(self, title: str = ""):
        """Print top border of a box."""
        if title:
            title_str = f" {title} "
            padding = self.WIDTH - len(title_str) - 2
            left_pad = padding // 2
            right_pad = padding - left_pad
            print(f"{Colors.CYAN}{Symbols.CORNER_TL}{Symbols.DASH * left_pad}{Colors.BOLD}{Colors.WHITE}{title_str}{Colors.RESET}{Colors.CYAN}{Symbols.DASH * right_pad}{Symbols.CORNER_TR}{Colors.RESET}")
        else:
            print(f"{Colors.CYAN}{Symbols.CORNER_TL}{Symbols.DASH * (self.WIDTH - 2)}{Symbols.CORNER_TR}{Colors.RESET}")

    def _box_bottom(self):
        """Print bottom border of a box."""
        print(f"{Colors.CYAN}{Symbols.CORNER_BL}{Symbols.DASH * (self.WIDTH - 2)}{Symbols.CORNER_BR}{Colors.RESET}")

    def _box_line(self, text: str, align: str = "left"):
        """Print a line inside a box."""
        # Strip ANSI codes for length calculation
        clean_text = re.sub(r'\033\[[0-9;]*m', '', text)
        padding = self.WIDTH - len(clean_text) - 4

        if align == "center":
            left_pad = padding // 2
            right_pad = padding - left_pad
            print(f"{Colors.CYAN}{Symbols.PIPE}{Colors.RESET} {' ' * left_pad}{text}{' ' * right_pad} {Colors.CYAN}{Symbols.PIPE}{Colors.RESET}")
        else:
            print(f"{Colors.CYAN}{Symbols.PIPE}{Colors.RESET} {text}{' ' * padding} {Colors.CYAN}{Symbols.PIPE}{Colors.RESET}")

    def _separator(self, char: str = "─"):
        """Print a separator line."""
        print(f"{Colors.DIM}{char * self.WIDTH}{Colors.RESET}")

    def add_check(self, name: str, passed: bool, message: str, details: str = ""):
        """Add a check result to the report."""
        self.check_number += 1
        status = "PASS" if passed else "FAIL"
        self.checks.append({
            "name": name,
            "status": status,
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "number": self.check_number
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

        # Print immediately
        self._print_check(self.checks[-1])

    def _print_check(self, check: dict):
        """Print a single check result with professional formatting."""
        if check["passed"]:
            status_color = Colors.BRIGHT_GREEN
            status_icon = Symbols.CHECK
            status_text = "PASS"
        else:
            status_color = Colors.BRIGHT_RED
            status_icon = Symbols.CROSS
            status_text = "FAIL"

        # Status line
        print()
        print(f"  {status_color}{Colors.BOLD}[{status_icon}]{Colors.RESET} {Colors.WHITE}{Colors.BOLD}{check['name']}{Colors.RESET}")
        print(f"      {Colors.DIM}Status:{Colors.RESET}  {status_color}{status_text}{Colors.RESET}")
        print(f"      {Colors.DIM}Result:{Colors.RESET}  {check['message']}")

        # Details (if any)
        if check["details"]:
            print(f"      {Colors.DIM}Details:{Colors.RESET}")
            for line in check["details"].split("\n"):
                if line.strip():
                    # Highlight ACTION REQUIRED
                    if "ACTION REQUIRED" in line:
                        print(f"        {Colors.BRIGHT_YELLOW}{Symbols.ARROW} {line.strip()}{Colors.RESET}")
                    elif line.strip().startswith("-"):
                        print(f"        {Colors.CYAN}{Symbols.BULLET}{Colors.RESET} {line.strip()[1:].strip()}")
                    else:
                        print(f"        {Colors.DIM}{Symbols.PIPE}{Colors.RESET} {line.strip()}")

    def print_header(self):
        """Print report header."""
        print()
        self._box_top("OIM PREREQUISITE VALIDATION")
        self._box_line("")
        self._box_line(f"{Colors.CYAN}System Check Tool{Colors.RESET}", "center")
        self._box_line(f"{Colors.DIM}Validating prerequisites for OIM deployment{Colors.RESET}", "center")
        self._box_line("")
        self._box_bottom()
        print()

    def print_summary(self):
        """Print final summary report with professional formatting."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        total = self.passed + self.failed

        print()
        self._separator("═")
        print()

        # Title
        print(f"  {Colors.BOLD}{Colors.WHITE}PREREQUISITE CHECK SUMMARY{Colors.RESET}")
        print()

        # Time info
        print(f"  {Colors.DIM}┌─ Execution Details{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}  Started  : {Colors.WHITE}{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}  Finished : {Colors.WHITE}{end_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}  Duration : {Colors.WHITE}{duration:.2f}s{Colors.RESET}")
        print(f"  {Colors.DIM}└{'─' * 40}{Colors.RESET}")
        print()

        # Results summary
        pass_pct = (self.passed / total * 100) if total > 0 else 0

        not_executed = self.TOTAL_CHECKS - total
        print(f"  {Colors.DIM}┌─ Results Overview{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}  Total Checks : {Colors.BOLD}{Colors.WHITE}{self.TOTAL_CHECKS}{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}  Executed     : {Colors.WHITE}{total}{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_GREEN}{Symbols.CHECK} Passed{Colors.RESET}      : {Colors.BRIGHT_GREEN}{self.passed}{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_RED}{Symbols.CROSS} Failed{Colors.RESET}      : {Colors.BRIGHT_RED}{self.failed}{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.DIM}○ Not Executed{Colors.RESET}: {Colors.DIM}{not_executed}{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}")

        # Progress bar - 11 segments for 11 checks (passed=green, failed=red, remaining=gray)
        bar_segments = []
        for check in self.checks:
            if check["passed"]:
                bar_segments.append(f"{Colors.BRIGHT_GREEN}███{Colors.RESET}")
            else:
                bar_segments.append(f"{Colors.BRIGHT_RED}███{Colors.RESET}")
        # Add remaining uncompleted checks as gray
        remaining = self.TOTAL_CHECKS - total
        for _ in range(remaining):
            bar_segments.append(f"{Colors.DIM}░░░{Colors.RESET}")
        progress_bar = "".join(bar_segments)
        print(f"  {Colors.DIM}│{Colors.RESET}  Progress    : [{progress_bar}] {self.passed}/{self.TOTAL_CHECKS} passed")
        print(f"  {Colors.DIM}└{'─' * 40}{Colors.RESET}")
        print()

        # Detailed results table
        print(f"  {Colors.DIM}┌─ Check Results{Colors.RESET}")
        print(f"  {Colors.DIM}│{Colors.RESET}")

        for check in self.checks:
            num = f"{check['number']:02d}"
            if check["passed"]:
                status = f"{Colors.BRIGHT_GREEN}{Symbols.CHECK} PASS{Colors.RESET}"
            else:
                status = f"{Colors.BRIGHT_RED}{Symbols.CROSS} FAIL{Colors.RESET}"

            print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.WHITE}{num}{Colors.RESET}  {status}  {Colors.WHITE}{check['name']}{Colors.RESET}")
            print(f"  {Colors.DIM}│{Colors.RESET}       {Colors.DIM}{check['message']}{Colors.RESET}")
            # Show key details for important checks (omnia.sh, etc.)
            if check.get('details') and ('omnia.sh' in check['details'] or 'Omnia Branch' in check['details']):
                for line in check['details'].split('\n'):
                    if line.strip():
                        print(f"  {Colors.DIM}│{Colors.RESET}       {Colors.CYAN}{line.strip()}{Colors.RESET}")

        print(f"  {Colors.DIM}│{Colors.RESET}")
        print(f"  {Colors.DIM}└{'─' * 60}{Colors.RESET}")
        print()

        # Final status banner
        self._separator("═")
        if self.failed > 0:
            print()
            print(f"  {Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}  PREREQUISITE CHECK FAILED  {Colors.RESET}")
            print()
            print(f"  {Colors.BRIGHT_RED}{Symbols.CROSS}{Colors.RESET} {self.failed} check(s) failed. Review the errors above and fix the issues.")
            print(f"  {Colors.DIM}  Run the check again after fixing the problems.{Colors.RESET}")
        else:
            print()
            print(f"  {Colors.BG_GREEN}{Colors.WHITE}{Colors.BOLD}  ALL CHECKS PASSED  {Colors.RESET}")
            print()
            print(f"  {Colors.BRIGHT_GREEN}{Symbols.CHECK}{Colors.RESET} System is ready for OIM deployment.")
        print()
        self._separator("═")
        print()

    def save_report(self, filepath: str):
        """Save report to file (plain text without colors)."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        total = self.passed + self.failed

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("           OIM PREREQUISITE CHECK REPORT\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Generated : {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration  : {duration:.2f} seconds\n")
            f.write(f"Host      : {os.uname().nodename}\n")
            f.write("\n" + "-" * 70 + "\n")
            f.write("SUMMARY\n")
            f.write("-" * 70 + "\n\n")

            f.write(f"  Total Checks : {total}\n")
            f.write(f"  Passed       : {self.passed}\n")
            f.write(f"  Failed       : {self.failed}\n")
            f.write(f"  Success Rate : {(self.passed/total*100) if total > 0 else 0:.1f}%\n")

            f.write("\n" + "-" * 70 + "\n")
            f.write("DETAILED RESULTS\n")
            f.write("-" * 70 + "\n\n")

            for check in self.checks:
                status = "[PASS]" if check["passed"] else "[FAIL]"
                f.write(f"{check['number']:02d}. {status} {check['name']}\n")
                f.write(f"    Message: {check['message']}\n")
                # Show details for failed checks or important info (omnia.sh, branch info)
                if check["details"]:
                    show_details = not check["passed"] or 'omnia.sh' in check["details"] or 'Branch' in check["details"]
                    if show_details:
                        f.write("    Details:\n")
                        for line in check["details"].split("\n"):
                            if line.strip():
                                f.write(f"      {line.strip()}\n")
                f.write("\n")

            f.write("-" * 70 + "\n")
            if self.failed > 0:
                f.write(f"RESULT: FAILED ({self.failed} check(s) need attention)\n")
            else:
                f.write("RESULT: PASSED (System ready for deployment)\n")
            f.write("-" * 70 + "\n")


# Global report instance
_report = None


# Global flag for remote execution mode
_remote_mode = False
_ssh_prefix = ""


def _is_remote_mode() -> bool:
    """Check if running in remote mode."""
    oim_server = OIM_PREREQ_VARS.get("oim_server_ip", "")
    return oim_server and oim_server.strip() and oim_server.lower() not in ["", "localhost", "127.0.0.1"]


def _get_ssh_command() -> str:
    """Build SSH command prefix for remote execution using sshpass for password auth."""
    oim_server = OIM_PREREQ_VARS.get("oim_server_ip", "")
    ssh_user = OIM_PREREQ_VARS.get("oim_ssh_user", "root")
    ssh_port = OIM_PREREQ_VARS.get("oim_ssh_port", 22)
    ssh_password = OIM_PREREQ_VARS.get("oim_ssh_password", "")

    ssh_opts = "-o StrictHostKeyChecking=no -o ConnectTimeout=10"

    if ssh_password:
        # Use sshpass for password authentication
        ssh_cmd = f"sshpass -p '{ssh_password}' ssh {ssh_opts} -p {ssh_port} {ssh_user}@{oim_server}"
    else:
        # Use default SSH key authentication
        ssh_cmd = f"ssh {ssh_opts} -p {ssh_port} {ssh_user}@{oim_server}"

    return ssh_cmd


def _ensure_sshpass_installed() -> bool:
    """Ensure sshpass is installed for password-based SSH."""
    rc = subprocess.run(["which", "sshpass"], capture_output=True).returncode
    if rc != 0:
        _log("sshpass not found, installing...", "INFO")
        result = subprocess.run(
            ["dnf", "install", "-y", "--nogpgcheck", "sshpass"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            _log(f"Failed to install sshpass: {result.stderr}", "ERROR")
            return False
        _log("sshpass installed successfully", "OK")
    return True


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
            result = subprocess.run(remote_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
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
            result = subprocess.run(remote_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
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
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            _log(f"Shell command timed out after {timeout}s", "ERROR")
            return -1, "", "Command timed out"
        except Exception as e:
            _log(f"Shell exception: {str(e)}", "ERROR")
            return -1, "", str(e)


# =============================================================================
# 1. HOSTNAME CONFIGURATION (FIRST TASK)
# =============================================================================

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

    rc, stdout, stderr = run_command(["hostnamectl", "set-hostname", target_hostname])
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
        "message": f"Hostname set but verification failed. Expected: {target_hostname}, Got: {new_hostname}",
        "instruction": OIM_PREREQ_MSGS["hostname_manual_instruction"].format(
            hostname=target_hostname, error="Verification failed"
        )
    }


# =============================================================================
# 2. IPMI Tool - Install and Validate
# =============================================================================

def check_ipmi_tool() -> Dict:
    """Check if IPMI tool is installed, install if not."""
    _log("Checking IPMI tool...", "INFO")
    ipmi_tool = OIM_PREREQ_VARS["ipmi_tool"]
    rc, stdout, stderr = run_command([ipmi_tool, "-V"])

    if rc == 0:
        version = stdout.split("\n")[0] if stdout else "unknown"
        return {
            "installed": True,
            "version": version,
            "message": OIM_PREREQ_MSGS["ipmi_installed"].format(version=version)
        }

    # Not installed, try to install
    install_result = install_ipmi_tool()
    if install_result["success"]:
        # Verify installation
        rc, stdout, stderr = run_command([ipmi_tool, "-V"])
        if rc == 0:
            version = stdout.split("\n")[0] if stdout else "unknown"
            return {
                "installed": True,
                "version": version,
                "message": OIM_PREREQ_MSGS["ipmi_install_success"]
            }

    return {
        "installed": False,
        "version": None,
        "message": install_result.get("message", OIM_PREREQ_MSGS["ipmi_install_fail"].format(error="Unknown error")),
        "instruction": OIM_PREREQ_MSGS["ipmi_install_instruction"].format(error="Unknown error")
    }


def install_ipmi_tool() -> Dict:
    """Install IPMI tool from RHEL repo."""
    ipmi_package = OIM_PREREQ_VARS["ipmi_package"]
    rc, stdout, stderr = run_command(["dnf", "install", "-y", ipmi_package], timeout=120)

    if rc == 0:
        return {"success": True, "message": OIM_PREREQ_MSGS["ipmi_install_success"]}
    return {
        "success": False,
        "message": OIM_PREREQ_MSGS["ipmi_install_fail"].format(error=stderr),
        "error": stderr,
        "instruction": OIM_PREREQ_MSGS["ipmi_install_instruction"].format(error=stderr)
    }


def get_hardware_inventory() -> Dict:
    """Get OIM compute inventory including storage, DIMMs, and cores."""
    _log("Getting hardware inventory...", "INFO")
    inventory = {"cores": 0, "memory_gb": 0, "disk_gb": 0, "dimm_count": 0, "dimm_info": [], "storage_info": []}

    # CPU cores
    rc, stdout, _ = run_command(["nproc"])
    if rc == 0:
        inventory["cores"] = int(stdout)
        _log(f"CPU cores: {inventory['cores']}", "DEBUG")

    # Memory (meminfo is in KB, so divide by 1024*1024 to get GB)
    rc, stdout, _ = run_shell("grep MemTotal /proc/meminfo | awk '{print $2}'")
    if rc == 0 and stdout:
        mem_kb = int(stdout)
        inventory["memory_gb"] = mem_kb // 1024 // 1024  # KB -> MB -> GB
        _log(f"Memory: {mem_kb} KB = {inventory['memory_gb']} GB", "DEBUG")

    # Disk (root partition)
    rc, stdout, _ = run_shell("df -BG / | tail -1 | awk '{print $2}' | tr -d 'G'")
    if rc == 0 and stdout:
        inventory["disk_gb"] = int(stdout)

    # DIMM info
    rc, stdout, _ = run_command(["dmidecode", "-t", "memory"])
    if rc == 0:
        dimm_matches = re.findall(r"Size:\s+(\d+\s+\w+)", stdout)
        inventory["dimm_count"] = len([d for d in dimm_matches if "No Module" not in d])
        inventory["dimm_info"] = dimm_matches

    # Storage devices
    rc, stdout, _ = run_command(["lsblk", "-d", "-o", "NAME,SIZE,TYPE", "-n"])
    if rc == 0:
        inventory["storage_info"] = stdout.split("\n")

    return inventory


def validate_hardware() -> Dict:
    """Validate OIM hardware meets minimum requirements."""
    inventory = get_hardware_inventory()
    results = {"passed": True, "inventory": inventory, "checks": []}

    # Check cores
    min_cores = OIM_PREREQ_VARS["min_cores"]
    if inventory["cores"] >= min_cores:
        results["checks"].append({"name": "cores", "passed": True, "message": OIM_PREREQ_MSGS["hw_cores_pass"].format(cores=inventory["cores"])})
    else:
        results["passed"] = False
        results["checks"].append({"name": "cores", "passed": False, "message": OIM_PREREQ_MSGS["hw_cores_fail"].format(cores=inventory["cores"], min_cores=min_cores)})

    # Check memory
    min_memory = OIM_PREREQ_VARS["min_memory_gb"]
    if inventory["memory_gb"] >= min_memory:
        results["checks"].append({"name": "memory", "passed": True, "message": OIM_PREREQ_MSGS["hw_memory_pass"].format(memory_gb=inventory["memory_gb"])})
    else:
        results["passed"] = False
        results["checks"].append({"name": "memory", "passed": False, "message": OIM_PREREQ_MSGS["hw_memory_fail"].format(memory_gb=inventory["memory_gb"], min_memory_gb=min_memory)})

    # Check disk
    min_disk = OIM_PREREQ_VARS["min_disk_gb"]
    if inventory["disk_gb"] >= min_disk:
        results["checks"].append({"name": "disk", "passed": True, "message": OIM_PREREQ_MSGS["hw_disk_pass"].format(disk_gb=inventory["disk_gb"])})
    else:
        results["passed"] = False
        results["checks"].append({"name": "disk", "passed": False, "message": OIM_PREREQ_MSGS["hw_disk_fail"].format(disk_gb=inventory["disk_gb"], min_disk_gb=min_disk)})

    return results


# =============================================================================
# 1.1.1 OS Validation
# =============================================================================

def get_os_info() -> Dict:
    """Get OS name, version, and kernel info from remote server."""
    os_info = {"name": "", "version": "", "full": "", "kernel": "", "build": ""}

    # Read /etc/os-release via SSH on remote server
    rc, stdout, _ = run_shell("cat /etc/os-release 2>/dev/null")
    if rc == 0 and stdout:
        for line in stdout.split("\n"):
            if line.startswith("ID="):
                os_info["name"] = line.split("=")[1].strip().strip('"').lower()
            elif line.startswith("VERSION_ID="):
                os_info["version"] = line.split("=")[1].strip().strip('"')
            elif line.startswith("PRETTY_NAME="):
                os_info["full"] = line.split("=", 1)[1].strip().strip('"')

    # Get kernel version via uname -r
    rc, stdout, _ = run_shell("uname -r 2>/dev/null")
    if rc == 0 and stdout:
        os_info["kernel"] = stdout.strip()

    # Get full build info via uname -a
    rc, stdout, _ = run_shell("uname -a 2>/dev/null")
    if rc == 0 and stdout:
        os_info["build"] = stdout.strip()

    return os_info


def validate_os() -> Dict:
    """Validate OS against required OS, version, and kernel."""
    _log("Validating OS...", "INFO")
    os_info = get_os_info()
    required_os = OIM_PREREQ_VARS.get("required_os", "rhel").lower()
    required_version = OIM_PREREQ_VARS.get("required_os_version", "10")
    required_kernel = OIM_PREREQ_VARS.get("required_kernel_version", "")

    if not os_info["name"]:
        return {"passed": False, "os_info": os_info, "message": OIM_PREREQ_MSGS["os_not_detected"]}

    # Check OS name
    actual_os = os_info["name"].lower()
    if not actual_os.startswith(required_os):
        return {
            "passed": False,
            "os_info": os_info,
            "message": f"OS mismatch: {actual_os} != {required_os}",
            "details": f"ACTION REQUIRED: OS does not match.\n- Required: {required_os}\n- Actual: {actual_os}\n- Update 'required_os' in {USER_CONFIG_PATH} if this OS is acceptable."
        }

    # Check OS version
    actual_version = os_info["version"]
    if not actual_version.startswith(required_version):
        return {
            "passed": False,
            "os_info": os_info,
            "message": f"OS version mismatch: {actual_version} != {required_version}",
            "details": f"ACTION REQUIRED: OS version does not match.\n- Required: {required_version}\n- Actual: {actual_version}\n- Update 'required_os_version' in {USER_CONFIG_PATH} or upgrade OS."
        }

    # Check kernel version if required
    if required_kernel and required_kernel.strip():
        actual_kernel = os_info.get("kernel", "")
        if actual_kernel != required_kernel:
            return {
                "passed": False,
                "os_info": os_info,
                "message": f"Kernel version mismatch: {actual_kernel} != {required_kernel}",
                "details": f"ACTION REQUIRED: Kernel version does not match.\n- Required: {required_kernel}\n- Actual: {actual_kernel}\n- Update 'required_kernel_version' in {USER_CONFIG_PATH} or upgrade kernel."
            }

    return {"passed": True, "os_info": os_info, "message": OIM_PREREQ_MSGS["os_check_pass"].format(os_name=os_info["name"], os_version=os_info["version"])}


# =============================================================================
# 1.1.2 Network Interfaces Validation (PXE: eno1, Public: weno2)
# =============================================================================

def get_interface_info(interface_name: str) -> Dict:
    """Get info for a specific interface."""
    info = {"name": interface_name, "exists": False, "state": "", "ip": ""}

    # Check if interface exists
    rc, state_out, _ = run_shell(f"cat /sys/class/net/{interface_name}/operstate 2>/dev/null")
    if rc == 0:
        info["exists"] = True
        info["state"] = state_out.strip()

    # Get IP address
    rc, ip_out, _ = run_shell(f"ip -4 addr show {interface_name} 2>/dev/null | grep inet | awk '{{print $2}}'")
    if rc == 0 and ip_out:
        info["ip"] = ip_out.split("\n")[0]

    return info


def get_network_interfaces() -> List[Dict]:
    """Get list of all network interfaces."""
    interfaces = []
    rc, stdout, _ = run_shell("ls /sys/class/net/ 2>/dev/null")
    if rc == 0:
        for iface in stdout.split():
            if iface and iface != "lo":
                interfaces.append(get_interface_info(iface))
    return interfaces


def validate_network_interfaces() -> Dict:
    """Validate PXE and Public interfaces are available and UP."""
    _log("Validating network interfaces...", "INFO")
    pxe_iface = OIM_PREREQ_VARS["pxe_interface"]
    public_iface = OIM_PREREQ_VARS["public_interface"]

    results = {"passed": True, "checks": [], "interfaces": []}

    # Check PXE interface
    if pxe_iface:
        pxe_info = get_interface_info(pxe_iface)
        results["interfaces"].append(pxe_info)

        if not pxe_info["exists"]:
            results["passed"] = False
            results["checks"].append({
                "name": "pxe_interface",
                "passed": False,
                "message": OIM_PREREQ_MSGS["iface_pxe_not_found"].format(interface=pxe_iface),
                "instruction": OIM_PREREQ_MSGS["iface_pxe_not_found_instruction"].format(interface=pxe_iface, config_path=USER_CONFIG_PATH)
            })
        elif pxe_info["state"] != "up":
            results["passed"] = False
            results["checks"].append({
                "name": "pxe_interface",
                "passed": False,
                "message": OIM_PREREQ_MSGS["iface_pxe_down"].format(interface=pxe_iface),
                "instruction": OIM_PREREQ_MSGS["iface_pxe_down_instruction"].format(interface=pxe_iface)
            })
        else:
            results["checks"].append({
                "name": "pxe_interface",
                "passed": True,
                "message": OIM_PREREQ_MSGS["iface_pxe_found"].format(interface=pxe_iface)
            })
    else:
        results["checks"].append({
            "name": "pxe_interface",
            "passed": False,
            "message": OIM_PREREQ_MSGS["iface_not_configured"],
            "instruction": f"ACTION REQUIRED: Set 'pxe_interface' in {USER_CONFIG_PATH} with your PXE network interface name."
        })
        results["passed"] = False

    # Check Public interface
    if public_iface:
        public_info = get_interface_info(public_iface)
        results["interfaces"].append(public_info)

        if not public_info["exists"]:
            results["passed"] = False
            results["checks"].append({
                "name": "public_interface",
                "passed": False,
                "message": OIM_PREREQ_MSGS["iface_public_not_found"].format(interface=public_iface),
                "instruction": OIM_PREREQ_MSGS["iface_public_not_found_instruction"].format(interface=public_iface, config_path=USER_CONFIG_PATH)
            })
        elif public_info["state"] != "up":
            results["passed"] = False
            results["checks"].append({
                "name": "public_interface",
                "passed": False,
                "message": OIM_PREREQ_MSGS["iface_public_down"].format(interface=public_iface),
                "instruction": OIM_PREREQ_MSGS["iface_public_down_instruction"].format(interface=public_iface)
            })
        else:
            results["checks"].append({
                "name": "public_interface",
                "passed": True,
                "message": OIM_PREREQ_MSGS["iface_public_found"].format(interface=public_iface)
            })
    else:
        results["checks"].append({
            "name": "public_interface",
            "passed": False,
            "message": OIM_PREREQ_MSGS["iface_not_configured"],
            "instruction": f"ACTION REQUIRED: Set 'public_interface' in {USER_CONFIG_PATH} with your public network interface name."
        })
        results["passed"] = False

    return results


# =============================================================================
# PXE NIC IP Configuration
# =============================================================================

def configure_pxe_nic() -> Dict:
    """
    Configure PXE NIC IP address.

    Logic:
    1. If PXE NIC already has IP and force_configure_pxe is False:
       - Return success with message showing existing IP
    2. If PXE NIC already has IP and force_configure_pxe is True:
       - Remove existing IP and configure new one
    3. If PXE NIC has no IP:
       - Configure with user-provided IP or default (172.16.107.254/24)
    """
    _log("Checking PXE NIC IP configuration...", "INFO")

    pxe_iface = OIM_PREREQ_VARS.get("pxe_interface", "")
    pxe_ip = OIM_PREREQ_VARS.get("pxe_ip", "172.16.107.254/24")
    force_configure = OIM_PREREQ_VARS.get("force_configure_pxe", False)

    # Validate interface name
    if not pxe_iface:
        return {
            "passed": False,
            "configured": False,
            "message": f"PXE interface not configured in {USER_CONFIG_PATH}",
            "details": f"Set 'pxe_interface' in {USER_CONFIG_PATH}"
        }

    # Check if interface exists
    pxe_info = get_interface_info(pxe_iface)
    if not pxe_info["exists"]:
        return {
            "passed": False,
            "configured": False,
            "message": f"PXE interface {pxe_iface} does not exist",
            "details": f"Check interface name in {USER_CONFIG_PATH}"
        }

    # Get current IP
    current_ip = pxe_info.get("ip", "")
    _log(f"PXE interface {pxe_iface} current IP: {current_ip or 'None'}", "INFO")
    _log(f"Target IP: {pxe_ip}", "INFO")
    _log(f"Force configure: {force_configure}", "INFO")

    # Case 1: Already configured and not forcing reconfigure
    if current_ip and not force_configure:
        _log(f"PXE NIC already configured with IP {current_ip}", "INFO")
        return {
            "passed": True,
            "configured": True,
            "already_configured": True,
            "current_ip": current_ip,
            "message": f"PXE NIC {pxe_iface} already configured with IP: {current_ip}",
            "details": f"To reconfigure, set 'force_configure_pxe: true' in {USER_CONFIG_PATH}"
        }

    # Case 2: Force reconfigure - flush ALL IPs first
    if force_configure:
        _log(f"Force reconfigure enabled. Removing ALL IPs from {pxe_iface}...", "INFO")

        # Get the NetworkManager connection name for this interface
        rc, nm_conn, _ = run_shell(f"nmcli -t -f NAME,DEVICE con show --active 2>/dev/null | grep ':{pxe_iface}$' | cut -d: -f1")
        nm_conn = nm_conn.strip() if rc == 0 else ""

        if nm_conn:
            _log(f"Found NetworkManager connection '{nm_conn}' for {pxe_iface}", "INFO")
            # Remove all IPv4 addresses from NetworkManager connection
            run_shell(f"nmcli con mod '{nm_conn}' ipv4.addresses '' 2>/dev/null")
            run_shell(f"nmcli con mod '{nm_conn}' ipv4.method manual 2>/dev/null")

        # First, flush ALL IPv4 addresses from the interface
        _log(f"Flushing all IPv4 addresses from {pxe_iface}...", "INFO")
        run_shell(f"ip -4 addr flush dev {pxe_iface} 2>/dev/null")

        # Get any remaining IPs (in case flush didn't get everything)
        rc, all_ips_output, _ = run_shell(f"ip -4 addr show {pxe_iface} 2>/dev/null | grep inet | awk '{{print $2}}'")
        all_ips = all_ips_output.strip().split("\n") if all_ips_output.strip() else []

        if all_ips and all_ips[0]:
            _log(f"Found {len(all_ips)} remaining IP(s), removing individually...", "INFO")

            # Delete each IP individually
            for ip in all_ips:
                if ip.strip():
                    _log(f"Removing IP: {ip}", "INFO")
                    run_shell(f"ip addr del {ip} dev {pxe_iface} 2>/dev/null")

            # Final flush
            run_shell(f"ip -4 addr flush dev {pxe_iface} 2>/dev/null")

        # Verify all IPs are removed
        rc, remaining, _ = run_shell(f"ip -4 addr show {pxe_iface} 2>/dev/null | grep inet | wc -l")
        if remaining.strip() == "0":
            _log(f"All IPs removed from {pxe_iface}", "OK")
        else:
            _log(f"Warning: {remaining.strip()} IP(s) may still remain on {pxe_iface}", "WARN")

    # Case 3: Configure new IP
    _log(f"Configuring PXE NIC {pxe_iface} with IP {pxe_ip}...", "INFO")

    # Validate IP format (should be CIDR notation like 172.16.107.254/24)
    if "/" not in pxe_ip:
        pxe_ip = f"{pxe_ip}/24"  # Add default subnet if not provided
        _log(f"Added default subnet, using: {pxe_ip}", "DEBUG")

    # Try to configure via NetworkManager first (persistent)
    rc, nm_conn, _ = run_shell(f"nmcli -t -f NAME,DEVICE con show --active 2>/dev/null | grep ':{pxe_iface}$' | cut -d: -f1")
    nm_conn = nm_conn.strip() if rc == 0 else ""

    if nm_conn:
        _log(f"Configuring IP via NetworkManager connection '{nm_conn}'...", "INFO")
        # Set the new IP via NetworkManager
        run_shell(f"nmcli con mod '{nm_conn}' ipv4.addresses '{pxe_ip}'")
        run_shell(f"nmcli con mod '{nm_conn}' ipv4.method manual")
        # Apply changes
        run_shell(f"nmcli con up '{nm_conn}' 2>/dev/null")

    # Also add IP directly (immediate effect)
    rc, stdout, stderr = run_shell(f"ip addr replace {pxe_ip} dev {pxe_iface}")
    if rc != 0:
        return {
            "passed": False,
            "configured": False,
            "message": f"Failed to configure IP {pxe_ip} on {pxe_iface}",
            "details": f"Command: ip addr add {pxe_ip} dev {pxe_iface}\nError: {stderr}"
        }

    # Bring interface up if not already
    rc, stdout, stderr = run_command(["ip", "link", "set", pxe_iface, "up"])
    if rc != 0:
        _log(f"Warning: Could not bring interface up: {stderr}", "WARN")

    # Verify configuration
    new_info = get_interface_info(pxe_iface)
    if new_info.get("ip"):
        _log(f"PXE NIC configured successfully with IP {new_info['ip']}", "OK")
        return {
            "passed": True,
            "configured": True,
            "already_configured": False,
            "new_ip": new_info["ip"],
            "message": f"PXE NIC {pxe_iface} configured with IP: {new_info['ip']}",
            "details": f"Interface is {new_info['state']}"
        }

    return {
        "passed": False,
        "configured": False,
        "message": f"IP configuration failed - could not verify IP on {pxe_iface}",
        "details": "IP was added but verification failed"
    }


# =============================================================================
# NFS Validation
# =============================================================================

def check_nfs_reachable() -> Dict:
    """Check if NFS server is reachable and has sufficient capacity."""
    _log("Checking NFS server...", "INFO")
    nfs_server = OIM_PREREQ_VARS.get("nfs_server", "")
    nfs_path = OIM_PREREQ_VARS.get("nfs_share_path", "")
    min_capacity = OIM_PREREQ_VARS.get("nfs_min_capacity_gb", 100)

    if not nfs_server or nfs_server.strip() == "":
        return {
            "reachable": False,
            "message": "NFS server IP not configured",
            "details": OIM_PREREQ_MSGS["nfs_not_configured_instruction"].format(config_path=USER_CONFIG_PATH)
        }

    # Step 1: Ping NFS server
    _log(f"Pinging NFS server: {nfs_server}", "INFO")
    rc, stdout, stderr = run_command(["ping", "-c", "3", "-W", "5", nfs_server])

    if rc != 0:
        return {
            "reachable": False,
            "server": nfs_server,
            "message": f"NFS server {nfs_server} is NOT reachable",
            "details": OIM_PREREQ_MSGS["nfs_not_reachable_instruction"].format(server=nfs_server, config_path=USER_CONFIG_PATH)
        }

    _log(f"NFS server {nfs_server} is reachable", "OK")

    # Step 2: Ensure nfs-utils is installed
    _log("Checking if nfs-utils is installed...", "DEBUG")
    rc, _, _ = run_command(["rpm", "-q", "nfs-utils"])
    if rc != 0:
        _log("nfs-utils not installed, attempting to install...", "INFO")
        rc, _, stderr = run_command(["dnf", "install", "-y", "nfs-utils"], timeout=120)
        if rc != 0:
            return {
                "reachable": False,
                "server": nfs_server,
                "message": "NFS client (nfs-utils) not installed and installation failed",
                "details": f"ACTION REQUIRED: Install nfs-utils manually.\n- Run: sudo dnf install -y nfs-utils\n- Error: {stderr}"
            }
        _log("nfs-utils installed successfully", "OK")

    # Step 3: Check NFS share path if provided
    if not nfs_path or nfs_path.strip() == "":
        return {
            "reachable": True,
            "server": nfs_server,
            "message": f"NFS server {nfs_server} is reachable (share path not configured)",
            "details": f"Set 'nfs_share_path' in {USER_CONFIG_PATH} to check capacity"
        }

    # Step 4: Check if NFS share is exported
    _log(f"Checking NFS export: {nfs_server}:{nfs_path}", "INFO")
    rc, stdout, stderr = run_shell(f"showmount -e {nfs_server} 2>/dev/null")
    if rc != 0:
        return {
            "reachable": False,
            "server": nfs_server,
            "message": f"Cannot list NFS exports from {nfs_server}",
            "details": f"ACTION REQUIRED: showmount failed.\n- Error: {stderr}\n- Check if NFS server is running: systemctl status nfs-server\n- Check firewall allows NFS: firewall-cmd --list-services"
        }

    # Check if our path is in the exports or is a subdirectory of an exported path
    nfs_path_normalized = nfs_path.rstrip("/")
    export_found = False
    parent_export = None

    # Parse exports from showmount output
    for line in stdout.strip().split("\n"):
        if line.strip() and not line.startswith("Export"):
            # Extract export path (first part before space)
            export_path = line.strip().split()[0] if line.strip().split() else ""
            export_path_normalized = export_path.rstrip("/")

            # Check exact match
            if nfs_path_normalized == export_path_normalized or nfs_path == export_path:
                export_found = True
                _log(f"NFS share {nfs_path} found in exports (exact match)", "OK")
                break

            # Check if configured path is a subdirectory of an exported path
            if nfs_path_normalized.startswith(export_path_normalized + "/"):
                export_found = True
                parent_export = export_path
                _log(f"NFS share {nfs_path} is subdirectory of exported path {export_path}", "OK")
                break

    if not export_found:
        _log(f"NFS share {nfs_path} not found in exports", "WARN")
        # Format available exports nicely
        exports_list = "\n".join([f"  - {line.strip()}" for line in stdout.strip().split("\n") if line.strip() and not line.startswith("Export")])
        return {
            "reachable": False,
            "server": nfs_server,
            "message": f"NFS share '{nfs_path}' NOT found on server",
            "details": f"ACTION REQUIRED: The NFS share path does not exist on the server.\n- Configured path: {nfs_path}\n- Available exports on {nfs_server}:\n{exports_list}\n- Update 'nfs_share_path' in {USER_CONFIG_PATH} with a valid export path."
        }

    # Step 5: Mount temporarily and check capacity
    _log(f"Mounting NFS share temporarily to check capacity...", "INFO")
    tmp_mount = "/tmp/oim_nfs_check"

    # Cleanup function to always unmount (runs via SSH on remote server)
    def cleanup_mount():
        """Always cleanup temp mount on remote server."""
        _log(f"Cleaning up temp mount {tmp_mount}...", "DEBUG")
        run_shell(f"umount -f {tmp_mount} 2>/dev/null")
        run_shell(f"umount -l {tmp_mount} 2>/dev/null")  # Lazy unmount as fallback
        run_shell(f"rmdir {tmp_mount} 2>/dev/null")

    # Cleanup any existing mount first
    cleanup_mount()

    # Create temp mount point on remote server
    rc, _, stderr = run_shell(f"mkdir -p {tmp_mount}")
    if rc != 0:
        return {
            "reachable": True,
            "server": nfs_server,
            "message": f"Cannot create temp mount point",
            "details": f"Error: {stderr}"
        }

    # Mount NFS share - capture both stdout and stderr for error message
    rc, stdout, stderr = run_shell(f"mount -t nfs {nfs_server}:{nfs_path} {tmp_mount} 2>&1", timeout=60)
    mount_error = stdout or stderr or "Unknown error"
    if rc != 0:
        cleanup_mount()
        return {
            "reachable": False,
            "server": nfs_server,
            "message": f"NFS mount FAILED: {nfs_server}:{nfs_path}",
            "details": f"ACTION REQUIRED: Cannot mount NFS share.\n- Error: {mount_error.strip()}\n- Verify the share path '{nfs_path}' exists on the NFS server.\n- Check exports: showmount -e {nfs_server}\n- Check NFS server logs for access denied errors."
        }

    _log(f"NFS share mounted at {tmp_mount}", "OK")

    # Get available capacity
    rc, stdout, _ = run_shell(f"df -BG {tmp_mount} | tail -1 | awk '{{print $4}}' | tr -d 'G'")

    # Always cleanup - unmount immediately after getting capacity
    cleanup_mount()
    _log(f"Temp mount removed", "DEBUG")

    if rc != 0 or not stdout:
        return {
            "reachable": True,
            "server": nfs_server,
            "message": f"NFS mounted but cannot determine capacity",
            "details": "df command failed"
        }

    try:
        capacity_gb = int(stdout.strip())
    except ValueError:
        return {
            "reachable": True,
            "server": nfs_server,
            "message": f"NFS mounted but cannot parse capacity: {stdout}",
            "details": "Unexpected df output"
        }

    _log(f"NFS capacity: {capacity_gb} GB (minimum required: {min_capacity} GB)", "INFO")

    # Check capacity - FAIL if insufficient
    if capacity_gb < min_capacity:
        return {
            "reachable": False,  # FAIL - capacity insufficient
            "server": nfs_server,
            "capacity_gb": capacity_gb,
            "message": f"NFS capacity INSUFFICIENT: {capacity_gb} GB < {min_capacity} GB required",
            "details": OIM_PREREQ_MSGS["nfs_capacity_instruction"].format(
                capacity_gb=capacity_gb, min_capacity_gb=min_capacity, config_path=USER_CONFIG_PATH
            )
        }

    # PASS - capacity is sufficient
    return {
        "reachable": True,
        "server": nfs_server,
        "capacity_gb": capacity_gb,
        "message": f"NFS server {nfs_server} OK - {capacity_gb} GB available (min: {min_capacity} GB)",
        "details": f"Share: {nfs_path}\nAvailable: {capacity_gb} GB\nRequired: {min_capacity} GB"
    }


# =============================================================================
# 3. Internet Validation - Ping via Public Interface Only
# =============================================================================

def check_internet() -> Dict:
    """Check internet connectivity via public interface using ping."""
    _log("Checking internet connectivity...", "INFO")
    public_iface = OIM_PREREQ_VARS["public_interface"]
    check_host = OIM_PREREQ_VARS["internet_check_host"]
    timeout = OIM_PREREQ_VARS["internet_timeout"]

    if not public_iface:
        return {
            "available": False,
            "message": "Public interface not configured",
            "details": f"ACTION REQUIRED: Set 'public_interface' in {USER_CONFIG_PATH}"
        }

    # Ping via specific interface
    rc, stdout, stderr = run_command([
        "ping", "-c", "3", "-W", str(timeout), "-I", public_iface, check_host
    ])

    if rc == 0:
        return {
            "available": True,
            "interface": public_iface,
            "host": check_host,
            "message": OIM_PREREQ_MSGS["internet_ping_success"].format(host=check_host, interface=public_iface)
        }

    return {
        "available": False,
        "interface": public_iface,
        "host": check_host,
        "message": OIM_PREREQ_MSGS["internet_ping_fail"].format(host=check_host, interface=public_iface),
        "details": OIM_PREREQ_MSGS["internet_fail_instruction"].format(interface=public_iface)
    }


# =============================================================================
# RHEL Repo Check and Git Installation
# =============================================================================

def check_rhel_repo() -> Dict:
    """Check if any RHEL repository is configured."""
    _log("Checking RHEL repositories...", "INFO")
    rc, stdout, stderr = run_shell("dnf repolist 2>/dev/null")

    if rc == 0 and stdout:
        # Look for common RHEL repo patterns
        repos = []
        for line in stdout.split("\n"):
            line_lower = line.lower()
            if any(x in line_lower for x in ["baseos", "appstream", "rhel", "codeready", "powertools"]):
                repos.append(line.strip())

        if repos:
            return {
                "found": True,
                "repos": repos,
                "message": OIM_PREREQ_MSGS["repo_found"].format(repo=repos[0])
            }

    return {
        "found": False,
        "repos": [],
        "message": "No RHEL repository configured",
        "details": OIM_PREREQ_MSGS["repo_not_found_instruction"]
    }


def check_git() -> Dict:
    """Check if Git is installed."""
    _log("Checking Git installation...", "INFO")
    rc, stdout, stderr = run_command(["git", "--version"])

    if rc == 0:
        version_match = re.search(r"(\d+\.\d+\.?\d*)", stdout)
        version = version_match.group(1) if version_match else stdout
        return {
            "installed": True,
            "version": version,
            "message": OIM_PREREQ_MSGS["git_installed"].format(version=version)
        }

    return {
        "installed": False,
        "version": None,
        "message": OIM_PREREQ_MSGS["git_not_installed"]
    }


def install_git() -> Dict:
    """Install Git from RHEL repo if available."""
    # First check if repo is available
    repo_check = check_rhel_repo()
    if not repo_check["found"]:
        return {
            "success": False,
            "message": OIM_PREREQ_MSGS["git_repo_not_found"]
        }

    # Install git
    git_package = OIM_PREREQ_VARS["git_package"]
    rc, stdout, stderr = run_command(["dnf", "install", "-y", git_package], timeout=120)

    if rc == 0:
        return {
            "success": True,
            "message": OIM_PREREQ_MSGS["git_install_success"]
        }

    return {
        "success": False,
        "message": "Git installation FAILED",
        "error": stderr,
        "details": OIM_PREREQ_MSGS["git_install_instruction"].format(error=stderr, config_path=USER_CONFIG_PATH)
    }


def ensure_git_installed() -> Dict:
    """Check Git, install if not present."""
    git_check = check_git()

    if git_check["installed"]:
        return git_check

    # Try to install
    install_result = install_git()
    if install_result["success"]:
        # Verify installation
        return check_git()

    return {
        "installed": False,
        "version": None,
        "message": install_result.get("message", "Git installation failed"),
        "details": install_result.get("details", OIM_PREREQ_MSGS["git_install_instruction"].format(error="Unknown error", config_path=USER_CONFIG_PATH))
    }


# =============================================================================
# Podman Validation
# =============================================================================

def check_podman() -> Dict:
    """Check Podman installation and version."""
    _log("Checking Podman installation...", "INFO")
    min_version = OIM_PREREQ_VARS["podman_min_version"]

    rc, stdout, stderr = run_command(["podman", "--version"])
    if rc != 0:
        return {
            "passed": False,
            "installed": False,
            "version": None,
            "message": "Podman is NOT installed",
            "details": OIM_PREREQ_MSGS["podman_not_installed_instruction"]
        }

    version_match = re.search(r"(\d+\.\d+\.\d+)", stdout)
    if version_match:
        version = version_match.group(1)
        v_current = [int(x) for x in version.split(".")]
        v_min = [int(x) for x in min_version.split(".")]

        if v_current >= v_min:
            return {
                "passed": True,
                "installed": True,
                "version": version,
                "message": f"Podman version {version} >= {min_version}",
                "details": stdout
            }
        return {
            "passed": False,
            "installed": True,
            "version": version,
            "message": f"Podman version {version} is BELOW minimum {min_version}",
            "details": OIM_PREREQ_MSGS["podman_version_instruction"].format(
                version=version, min_version=min_version, config_path=USER_CONFIG_PATH
            )
        }

    return {
        "passed": False,
        "installed": True,
        "version": None,
        "message": f"Could not parse Podman version from: {stdout}",
        "details": "Unexpected version format. Please check Podman installation."
    }


# =============================================================================
# Omnia Repository Clone
# =============================================================================

def clone_omnia_repo() -> Dict:
    """Clone Omnia artifactory repository from configured URL."""
    _log("Checking Omnia artifactory repository...", "INFO")
    repo_url = OIM_PREREQ_VARS["omnia_repo_url"]
    branch = OIM_PREREQ_VARS["artifactory_branch"]
    clone_path = OIM_PREREQ_VARS["omnia_clone_path"]

    if not repo_url:
        return {
            "passed": False,
            "message": "Omnia repository URL not configured",
            "details": OIM_PREREQ_MSGS["omnia_repo_not_configured_instruction"].format(config_path=USER_CONFIG_PATH)
        }

    _log(f"Repo URL: {repo_url}", "DEBUG")
    _log(f"Branch: {branch}", "DEBUG")
    _log(f"Clone path: {clone_path}", "DEBUG")

    # Always delete existing folder and re-clone fresh
    rc, _, _ = run_shell(f"test -d {clone_path}")
    if rc == 0:
        _log(f"Removing existing directory {clone_path}...", "INFO")
        # Kill any running processes that might lock the directory
        run_shell(f"pkill -9 -f build_images 2>/dev/null; pkill -9 -f 'git clone' 2>/dev/null; sleep 1")
        # Force remove
        run_shell(f"rm -rf {clone_path} 2>/dev/null")
        # Verify it's removed, retry if needed
        rc, _, _ = run_shell(f"test -d {clone_path}")
        if rc == 0:
            _log(f"Retrying removal of {clone_path}...", "WARN")
            run_shell(f"rm -rf {clone_path}")

    # Clone fresh - create parent directory on remote server
    _log(f"Cloning repository to {clone_path}...", "INFO")
    parent_dir = "/".join(clone_path.rstrip("/").split("/")[:-1])
    if parent_dir:
        run_shell(f"mkdir -p {parent_dir}")

    # Use shallow clone (--depth 1) for faster cloning
    rc, stdout, stderr = run_command(["git", "clone", "--depth", "1", "-b", branch, repo_url, clone_path], timeout=300)

    if rc != 0:
        return {
            "passed": False,
            "message": f"Failed to clone Omnia artifactory",
            "details": OIM_PREREQ_MSGS["omnia_clone_instruction"].format(
                repo_url=repo_url, clone_path=clone_path, error=stderr, config_path=USER_CONFIG_PATH
            )
        }

    return {
        "passed": True,
        "message": f"Omnia artifactory cloned to {clone_path}",
        "details": f"Branch: {branch}"
    }


def download_omnia_sh() -> Dict:
    """Download omnia.sh script from the specified omnia_branch."""
    _log("Downloading omnia.sh...", "INFO")
    clone_path = OIM_PREREQ_VARS["omnia_clone_path"]
    omnia_branch = OIM_PREREQ_VARS.get("omnia_branch", "")

    if not omnia_branch or not omnia_branch.strip():
        return {
            "passed": False,
            "message": "omnia_branch not configured",
            "details": OIM_PREREQ_MSGS["omnia_sh_branch_not_configured"].format(config_path=USER_CONFIG_PATH)
        }

    # Create directory if it doesn't exist
    rc, _, _ = run_shell(f"test -d {clone_path}")
    if rc != 0:
        _log(f"Creating directory {clone_path}...", "INFO")
        rc, _, stderr = run_shell(f"mkdir -p {clone_path}")
        if rc != 0:
            return {
                "passed": False,
                "message": OIM_PREREQ_MSGS["omnia_sh_dir_create_fail"].format(clone_path=clone_path),
                "details": f"Error: {stderr}"
            }

    # Delete existing omnia.sh if present
    _log(f"Removing existing omnia.sh if present...", "DEBUG")
    run_shell(f"rm -f {clone_path}/omnia.sh 2>/dev/null")

    # Try both branch URL and tag URL
    branch_url = f"https://raw.githubusercontent.com/dell/omnia/refs/heads/{omnia_branch}/omnia.sh"
    tag_url = f"https://raw.githubusercontent.com/dell/omnia/refs/tags/{omnia_branch}/omnia.sh"

    # Try branch URL first
    _log(f"Trying branch URL: {branch_url}...", "INFO")
    rc, stdout, stderr = run_shell(f"cd {clone_path} && wget -q {branch_url} -O omnia.sh", timeout=60)

    if rc == 0:
        # Verify file was downloaded (not empty/error page)
        rc_check, size, _ = run_shell(f"stat -c%s {clone_path}/omnia.sh 2>/dev/null")
        if rc_check == 0 and size.strip().isdigit() and int(size.strip()) > 100:
            run_shell(f"chmod +x {clone_path}/omnia.sh")
            _log(f"omnia.sh downloaded from branch: {omnia_branch}", "OK")
            return {
                "passed": True,
                "message": OIM_PREREQ_MSGS["omnia_sh_download_success"].format(ref_type="branch", omnia_branch=omnia_branch),
                "details": f"URL: {branch_url}\nLocation: {clone_path}/omnia.sh"
            }

    # Branch URL failed, try tag URL
    _log(f"Branch URL failed, trying tag URL: {tag_url}...", "INFO")
    run_shell(f"rm -f {clone_path}/omnia.sh 2>/dev/null")
    rc, stdout, stderr = run_shell(f"cd {clone_path} && wget -q {tag_url} -O omnia.sh", timeout=60)

    if rc == 0:
        # Verify file was downloaded (not empty/error page)
        rc_check, size, _ = run_shell(f"stat -c%s {clone_path}/omnia.sh 2>/dev/null")
        if rc_check == 0 and size.strip().isdigit() and int(size.strip()) > 100:
            run_shell(f"chmod +x {clone_path}/omnia.sh")
            _log(f"omnia.sh downloaded from tag: {omnia_branch}", "OK")
            return {
                "passed": True,
                "message": OIM_PREREQ_MSGS["omnia_sh_download_success"].format(ref_type="tag", omnia_branch=omnia_branch),
                "details": f"URL: {tag_url}\nLocation: {clone_path}/omnia.sh"
            }

    # Both URLs failed
    return {
        "passed": False,
        "message": OIM_PREREQ_MSGS["omnia_sh_download_fail"],
        "details": OIM_PREREQ_MSGS["omnia_sh_download_instruction"].format(
            omnia_branch=omnia_branch, branch_url=branch_url, tag_url=tag_url
        )
    }


def build_container_images() -> Dict:
    """Build container images using build_images.sh script."""
    _log("Building container images...", "INFO")
    clone_path = OIM_PREREQ_VARS["omnia_clone_path"]
    container_images = OIM_PREREQ_VARS["container_images"]
    omnia_branch = OIM_PREREQ_VARS["omnia_branch"]

    # Check required: omnia_branch
    if not omnia_branch or not omnia_branch.strip():
        return {
            "passed": False,
            "message": "omnia_branch not configured",
            "details": OIM_PREREQ_MSGS["omnia_branch_not_configured"].format(config_path=USER_CONFIG_PATH)
        }

    # Check required: container_images
    if not container_images or not container_images.strip():
        return {
            "passed": False,
            "message": "container_images not configured",
            "details": OIM_PREREQ_MSGS["container_images_not_configured"].format(config_path=USER_CONFIG_PATH)
        }

    # Check if clone path exists
    rc, _, _ = run_shell(f"test -d {clone_path}")
    if rc != 0:
        return {
            "passed": False,
            "message": "Omnia artifactory not cloned",
            "details": OIM_PREREQ_MSGS["clone_path_not_found"].format(clone_path=clone_path, config_path=USER_CONFIG_PATH)
        }

    # Check if build_images.sh exists
    build_script = f"{clone_path}/build_images.sh"
    rc, _, _ = run_shell(f"test -f {build_script}")
    if rc != 0:
        return {
            "passed": False,
            "message": "build_images.sh not found",
            "details": OIM_PREREQ_MSGS["build_script_not_found"].format(script_path=build_script)
        }

    # Make script executable
    run_shell(f"chmod +x {build_script}")

    _log(f"Running: ./build_images.sh {container_images} omnia_branch={omnia_branch}", "INFO")

    # Run build_images.sh with LIVE output streaming
    build_cmd = f"cd {clone_path} && ./build_images.sh {container_images} omnia_branch={omnia_branch}"

    if _is_remote_mode():
        ssh_cmd = _get_ssh_command()
        escaped_cmd = build_cmd.replace("'", "'\\''")
        full_cmd = f"{ssh_cmd} '{escaped_cmd}'"
    else:
        full_cmd = build_cmd

    # Stream output in real-time
    output_lines = []
    try:
        process = subprocess.Popen(
            full_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Read and print output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.rstrip()
                output_lines.append(line)
                print(line)

        process.wait(timeout=1800)  # 30 minutes timeout
        rc = process.returncode

    except subprocess.TimeoutExpired:
        process.kill()
        print(f"TIMEOUT: Build exceeded 30 minutes")
        rc = -1
        output_lines.append("TIMEOUT: Build exceeded 30 minutes")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        rc = -1
        output_lines.append(f"ERROR: {str(e)}")

    stdout = "\n".join(output_lines)

    if rc == 0:
        return {
            "passed": True,
            "message": OIM_PREREQ_MSGS["container_build_success"].format(images=container_images),
            "details": f"Images: {container_images}\nOmnia Branch: {omnia_branch}"
        }

    return {
        "passed": False,
        "message": f"Failed to build container images: {container_images}",
        "details": OIM_PREREQ_MSGS["container_build_instruction"].format(
            images=container_images, omnia_branch=omnia_branch, exit_code=rc
        )
    }


# =============================================================================
# Full Validation with Stop-on-Failure and Detailed Report
# =============================================================================

def run_all_prereq_checks(stop_on_failure: bool = None, save_report: bool = True) -> Dict:
    """
    Run all prerequisite checks with detailed reporting.

    Args:
        stop_on_failure: If True, stop execution on first failure.
                         If None, uses skip_on_failure from user_config.yml (inverted)
        save_report: If True, save report to file

    Returns:
        Dict with all check results
    """
    global _report
    _report = PrereqReport()

    # Get stop_on_failure from config if not explicitly passed
    # skip_on_failure=True means stop_on_failure=False (continue on failure)
    if stop_on_failure is None:
        skip_on_failure = OIM_PREREQ_VARS.get("skip_on_failure", True)
        stop_on_failure = not skip_on_failure

    # Print header
    _report.print_header()

    # Show loaded configuration in a nice box
    print(f"  {Colors.DIM}┌─ Configuration{Colors.RESET}")
    # Use the exported config path
    config_path = USER_CONFIG_PATH
    print(f"  {Colors.DIM}│{Colors.RESET}  Config File     : {Colors.WHITE}{config_path}{Colors.RESET}")
    # Use the actual runtime stop_on_failure value (not from config)
    if stop_on_failure:
        print(f"  {Colors.DIM}│{Colors.RESET}  Stop on Failure : {Colors.BRIGHT_YELLOW}true{Colors.RESET} (stop on first failure)")
    else:
        print(f"  {Colors.DIM}│{Colors.RESET}  Stop on Failure : {Colors.BRIGHT_GREEN}false{Colors.RESET} (continue on failure)")

    # Show target OIM server
    oim_ip = OIM_PREREQ_VARS.get('oim_server_ip', '')
    oim_user = OIM_PREREQ_VARS.get('oim_ssh_user', 'root')
    if oim_ip and oim_ip.strip():
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_YELLOW}OIM Server{Colors.RESET}     : {Colors.BRIGHT_YELLOW}{oim_user}@{oim_ip}{Colors.RESET} (via SSH)")
    else:
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_RED}OIM Server{Colors.RESET}     : {Colors.BRIGHT_RED}(not configured){Colors.RESET}")

    print(f"  {Colors.DIM}│{Colors.RESET}  PXE Interface   : {Colors.CYAN}{OIM_PREREQ_VARS.get('pxe_interface') or '(not set)'}{Colors.RESET}")
    print(f"  {Colors.DIM}│{Colors.RESET}  Public Interface: {Colors.CYAN}{OIM_PREREQ_VARS.get('public_interface') or '(not set)'}{Colors.RESET}")
    print(f"  {Colors.DIM}│{Colors.RESET}  NFS Server      : {Colors.CYAN}{OIM_PREREQ_VARS.get('nfs_server') or '(not set)'}{Colors.RESET}")
    print(f"  {Colors.DIM}│{Colors.RESET}  NFS Share Path  : {Colors.CYAN}{OIM_PREREQ_VARS.get('nfs_share_path') or '(not set)'}{Colors.RESET}")
    print(f"  {Colors.DIM}│{Colors.RESET}  NFS Min Capacity: {Colors.CYAN}{OIM_PREREQ_VARS.get('nfs_min_capacity_gb', 100)} GB{Colors.RESET}")
    print(f"  {Colors.DIM}│{Colors.RESET}  Podman Min Ver  : {Colors.CYAN}{OIM_PREREQ_VARS.get('podman_min_version')}{Colors.RESET}")
    print(f"  {Colors.DIM}│{Colors.RESET}  Artifactory Repo: {Colors.CYAN}{OIM_PREREQ_VARS.get('omnia_repo_url') or '(not set)'}{Colors.RESET}")
    print(f"  {Colors.DIM}│{Colors.RESET}  Artifactory Br  : {Colors.CYAN}{OIM_PREREQ_VARS.get('artifactory_branch')}{Colors.RESET}")
    print(f"  {Colors.DIM}│{Colors.RESET}  Clone Path      : {Colors.CYAN}{OIM_PREREQ_VARS.get('omnia_clone_path')}{Colors.RESET}")
    reconfig = OIM_PREREQ_VARS.get('reconfigure_images', False)
    if reconfig:
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_GREEN}Reconfigure Imgs{Colors.RESET}: {Colors.BRIGHT_GREEN}true{Colors.RESET} (will clone & build)")
        print(f"  {Colors.DIM}│{Colors.RESET}  Container Images: {Colors.CYAN}{OIM_PREREQ_VARS.get('container_images') or '(default: core)'}{Colors.RESET}")
        omnia_br = OIM_PREREQ_VARS.get('omnia_branch')
        if omnia_br:
            print(f"  {Colors.DIM}│{Colors.RESET}  Omnia Branch    : {Colors.CYAN}{omnia_br}{Colors.RESET}")
        else:
            print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_RED}Omnia Branch{Colors.RESET}    : {Colors.BRIGHT_RED}(REQUIRED - not set){Colors.RESET}")
    else:
        print(f"  {Colors.DIM}│{Colors.RESET}  Reconfigure Imgs: {Colors.DIM}false{Colors.RESET} (skip git clone & build)")
    print(f"  {Colors.DIM}└{'─' * 60}{Colors.RESET}")
    print()

    # OIM server IP is REQUIRED - must run on remote host
    oim_server = OIM_PREREQ_VARS.get('oim_server_ip', '').strip()
    ssh_password = OIM_PREREQ_VARS.get('oim_ssh_password', '').strip()
    ssh_user = OIM_PREREQ_VARS.get('oim_ssh_user', 'root')

    if not oim_server or oim_server.lower() in ["localhost", "127.0.0.1"]:
        print(f"  {Colors.BRIGHT_RED}{Symbols.CROSS} ERROR: OIM Server IP not configured{Colors.RESET}")
        print()
        print(f"  {Colors.BRIGHT_YELLOW}ACTION REQUIRED:{Colors.RESET}")
        print(f"  {Colors.DIM}  1. Edit: {config_path}{Colors.RESET}")
        print(f"  {Colors.DIM}  2. Set 'oim_server_ip' to your OIM server IP address{Colors.RESET}")
        print(f"  {Colors.DIM}  3. Set 'oim_ssh_user' (default: root){Colors.RESET}")
        print(f"  {Colors.DIM}  4. Set 'oim_ssh_password' with SSH password{Colors.RESET}")
        print()
        return {
            "passed": False,
            "passed_count": 0,
            "failed_count": 1,
            "checks": {"OIM Server Config": {"passed": False, "message": f"oim_server_ip not configured in {config_path}"}}
        }

    if not ssh_password:
        print(f"  {Colors.BRIGHT_RED}{Symbols.CROSS} ERROR: SSH password not configured{Colors.RESET}")
        print()
        print(f"  {Colors.BRIGHT_YELLOW}ACTION REQUIRED:{Colors.RESET}")
        print(f"  {Colors.DIM}  Set 'oim_ssh_password' in: {config_path}{Colors.RESET}")
        print()
        return {
            "passed": False,
            "passed_count": 0,
            "failed_count": 1,
            "checks": {"SSH Config": {"passed": False, "message": f"oim_ssh_password not configured in {config_path}"}}
        }

    # Install sshpass for password authentication
    print(f"  {Colors.BRIGHT_BLUE}{Symbols.ARROW}{Colors.RESET} {Colors.BOLD}Checking sshpass for password authentication...{Colors.RESET}")
    if not _ensure_sshpass_installed():
        print(f"  {Colors.BRIGHT_RED}{Symbols.CROSS}{Colors.RESET} sshpass installation FAILED")
        print(f"  {Colors.DIM}  Install manually: sudo dnf install -y sshpass{Colors.RESET}")
        return {
            "passed": False,
            "passed_count": 0,
            "failed_count": 1,
            "checks": {"sshpass": {"passed": False, "message": "sshpass required for password auth"}}
        }

    # Test SSH connectivity
    print(f"  {Colors.BRIGHT_BLUE}{Symbols.ARROW}{Colors.RESET} {Colors.BOLD}Testing SSH connection to {oim_server}...{Colors.RESET}")
    rc, stdout, stderr = run_command(["echo", "SSH_OK"])
    if rc != 0 or "SSH_OK" not in stdout:
        print(f"  {Colors.BRIGHT_RED}{Symbols.CROSS}{Colors.RESET} SSH connection FAILED: {stderr}")
        print(f"  {Colors.DIM}  Check oim_server_ip, oim_ssh_user, and oim_ssh_password in:{Colors.RESET}")
        print(f"  {Colors.WHITE}  {config_path}{Colors.RESET}")
        return {
            "passed": False,
            "passed_count": 0,
            "failed_count": 1,
            "checks": {"SSH Connection": {"passed": False, "message": f"Cannot connect to {oim_server}"}}
        }
    print(f"  {Colors.BRIGHT_GREEN}{Symbols.CHECK}{Colors.RESET} SSH connection OK")
    print()

    print(f"  {Colors.BRIGHT_BLUE}{Symbols.ARROW}{Colors.RESET} {Colors.BOLD}Running prerequisite checks...{Colors.RESET}")
    print()

    all_passed = True

    # Check 1: HOSTNAME CONFIGURATION (FIRST TASK)
    result = configure_hostname()
    passed = result.get("passed", False)
    details = result.get("details", "")
    if result.get("already_configured"):
        details = f"Already set: {result.get('hostname', '')}\nDomain: {result.get('domain', '')}"
    elif result.get("hostname"):
        details = f"Hostname: {result.get('hostname', '')}\nDomain: {result.get('domain', '')}"
    _report.add_check("Hostname Configuration", passed, result.get("message", ""), details)
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 2: RHEL Repository (check before installing anything)
    result = check_rhel_repo()
    passed = result.get("found", False)
    details = "\n".join(result.get("repos", [])) if result.get("repos") else ""
    _report.add_check("RHEL Repository", passed, result.get("message", ""), details)
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 3: IPMI Tool
    result = check_ipmi_tool()
    passed = result.get("installed", False)
    _report.add_check("IPMI Tool", passed, result.get("message", ""), result.get("details", ""))
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 4: Hardware Inventory
    result = validate_hardware()
    passed = result.get("passed", False)
    details = ""
    msg = "Hardware meets requirements" if passed else "Hardware does NOT meet requirements"
    if "inventory" in result:
        inv = result["inventory"]
        min_cores = OIM_PREREQ_VARS.get("min_cores", 4)
        min_mem = OIM_PREREQ_VARS.get("min_memory_gb", 16)
        min_disk = OIM_PREREQ_VARS.get("min_disk_gb", 100)
        details = f"Cores: {inv.get('cores', 0)} (min: {min_cores})\nMemory: {inv.get('memory_gb', 0)} GB (min: {min_mem} GB)\nDisk: {inv.get('disk_gb', 0)} GB (min: {min_disk} GB)"
        if not passed:
            if inv.get('cores', 0) < min_cores:
                msg = f"CPU cores {inv.get('cores', 0)} < minimum {min_cores}"
            elif inv.get('memory_gb', 0) < min_mem:
                msg = f"Memory {inv.get('memory_gb', 0)} GB < minimum {min_mem} GB"
            elif inv.get('disk_gb', 0) < min_disk:
                msg = f"Disk {inv.get('disk_gb', 0)} GB < minimum {min_disk} GB"
    _report.add_check("Hardware Inventory", passed, msg, details)
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 5: OS Validation
    result = validate_os()
    passed = result.get("passed", False)
    details = ""
    if "os_info" in result:
        os_info = result['os_info']
        details = f"Detected: {os_info.get('full', 'Unknown')}"
        if os_info.get('kernel'):
            details += f"\nKernel: {os_info.get('kernel')}"
        if os_info.get('build'):
            details += f"\nBuild: {os_info.get('build')}"
    _report.add_check("OS Validation", passed, result.get("message", ""), details)
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 6: Network Interfaces
    result = validate_network_interfaces()
    passed = result.get("passed", False)
    details = ""
    if "checks" in result:
        for c in result["checks"]:
            details += f"{c['name']}: {c['message']}\n"
            if not c.get("passed", True) and c.get("instruction"):
                details += c["instruction"]
    _report.add_check("Network Interfaces", passed,
                      "PXE and Public interfaces validated" if passed else "Interface validation FAILED",
                      details)
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 7: PXE NIC IP Configuration (flush ALL IPs and reset)
    result = configure_pxe_nic()
    passed = result.get("passed", False)
    details = result.get("details", "")
    if result.get("already_configured"):
        details += f"\nCurrent IP: {result.get('current_ip', '')}"
    elif result.get("new_ip"):
        details += f"\nConfigured IP: {result.get('new_ip', '')}"
    _report.add_check("PXE NIC Configuration", passed, result.get("message", ""), details)
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 8: NFS Server
    result = check_nfs_reachable()
    passed = result.get("reachable", False)
    _report.add_check("NFS Server", passed, result.get("message", ""), result.get("details", ""))
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 9: Internet Connectivity
    result = check_internet()
    passed = result.get("available", False)
    _report.add_check("Internet Connectivity", passed, result.get("message", ""), result.get("details", ""))
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 10: Podman
    result = check_podman()
    passed = result.get("passed", False)
    _report.add_check("Podman", passed, result.get("message", ""), result.get("details", ""))
    if not passed and stop_on_failure:
        return _finish_report(_report, False, save_report)

    # Check 11-13: Git, Omnia Artifactory Clone, Build Container Images (only if reconfigure_images is true)
    reconfigure_images = OIM_PREREQ_VARS.get("reconfigure_images", False)

    if reconfigure_images:
        result = ensure_git_installed()
        passed = result.get("installed", False)
        _report.add_check("Git", passed, result.get("message", ""), result.get("details", ""))
        if not passed and stop_on_failure:
            return _finish_report(_report, False, save_report)

        # Check 12: Omnia Artifactory Clone
        result = clone_omnia_repo()
        passed = result.get("passed", False)
        _report.add_check("Omnia Artifactory", passed, result.get("message", ""), result.get("details", ""))
        if not passed and stop_on_failure:
            return _finish_report(_report, False, save_report)

        # Check 13: Build Container Images
        result = build_container_images()
        passed = result.get("passed", False)
        _report.add_check("Container Images", passed, result.get("message", ""), result.get("details", ""))
        if not passed and stop_on_failure:
            return _finish_report(_report, False, save_report)
    else:
        _log("Skipping Git, Omnia Artifactory, and Container Build (reconfigure_images: false)", "INFO")
        _report.add_check("Container Build", True, "Skipped (reconfigure_images: false)", "Set 'reconfigure_images: true' in user_config.yml to enable")

    # Check 14: Download omnia.sh (always runs - creates directory if needed)
    result = download_omnia_sh()
    passed = result.get("passed", False)
    _report.add_check("Download omnia.sh", passed, result.get("message", ""), result.get("details", ""))

    # Determine final status
    all_passed = _report.failed == 0

    return _finish_report(_report, all_passed, save_report)


def _finish_report(report: PrereqReport, all_passed: bool, save_report: bool = True) -> Dict:
    """Print summary, save report, and return final result."""
    report.print_summary()

    if save_report:
        # Save report in project root (same folder as user_config.yml)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        report_path = os.path.join(project_root, "oim_prereq_report.txt")
        report.save_report(report_path)
        _log(f"Report saved to: {report_path}", "INFO")

    return {
        "passed": all_passed,
        "passed_count": report.passed,
        "failed_count": report.failed,
        "checks": {c["name"]: {"passed": c["passed"], "message": c["message"]} for c in report.checks}
    }
