# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
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

"""Main orchestration and reporting for OIM prerequisite checks."""

import os
import re
from datetime import datetime
from typing import Dict

from ...core import Colors, Symbols, log as _log
from ..vars.oim_prereq_vars import OIM_PREREQ_VARS, OMNIA_TEST_CONFIG_PATH

# Import all check functions
from .system import configure_hostname, validate_ssh_connection
from .validation import validate_os, check_podman
from .hardware import check_ipmi_tool, validate_hardware
from .network import (validate_network_interfaces, configure_pxe_nic,
                      check_internet, check_pxe_is_public_interface)
from .services import check_nfs_reachable
from .repository import (ensure_git_installed, clone_omnia_repo,
                        build_container_images, download_omnia_sh)


class PrereqReport:
    """Generate detailed prerequisite check report with Linux theme."""

    WIDTH = 80  # Terminal width
    TOTAL_CHECKS = 14  # Total number of checks in the full suite

    def __init__(self):
        self.start_time = datetime.now()
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.check_number = 0

    def _box_top(self, title: str = ""):
        """Print top border of a box."""
        if title:
            title_str = f" {title} "
            padding = self.WIDTH - len(title_str) - 2
            left_pad = padding // 2
            right_pad = padding - left_pad
            print(f"{Colors.CYAN}{Symbols.CORNER_TL}{Symbols.DASH * left_pad}"
                  f"{Colors.BOLD}{Colors.WHITE}{title_str}{Colors.RESET}"
                  f"{Colors.CYAN}{Symbols.DASH * right_pad}{Symbols.CORNER_TR}{Colors.RESET}")
        else:
            print(f"{Colors.CYAN}{Symbols.CORNER_TL}"
                  f"{Symbols.DASH * (self.WIDTH - 2)}{Symbols.CORNER_TR}{Colors.RESET}")

    def _box_bottom(self):
        """Print bottom border of a box."""
        print(f"{Colors.CYAN}{Symbols.CORNER_BL}"
              f"{Symbols.DASH * (self.WIDTH - 2)}{Symbols.CORNER_BR}{Colors.RESET}")

    def _box_line(self, text: str, align: str = "left"):
        """Print a line inside a box."""
        # Strip ANSI codes for length calculation
        clean_text = re.sub(r'\033\[[0-9;]*m', '', text)
        padding = self.WIDTH - len(clean_text) - 4

        if align == "center":
            left_pad = padding // 2
            right_pad = padding - left_pad
            print(f"{Colors.CYAN}{Symbols.PIPE}{Colors.RESET} {' ' * left_pad}{text}{' ' * right_pad} {Colors.CYAN}{Symbols.PIPE}{Colors.RESET}"
              f"")
        else:
            print(f"{Colors.CYAN}{Symbols.PIPE}{Colors.RESET} {text}{' ' * padding} {Colors.CYAN}{Symbols.PIPE}{Colors.RESET}"
              f"")

    def _separator(self, char: str = "─"):
        """Print a separator line."""
        print(f"{Colors.DIM}{char * self.WIDTH}{Colors.RESET}"
              f"")

    def add_check(self, name: str, passed: bool, message: str, details: str = "", *, skipped: bool = False):
        """Add a check result to the report."""
        self.check_number += 1
        if skipped:
            status = "SKIP"
        elif passed:
            status = "PASS"
        else:
            status = "FAIL"
        self.checks.append({
            "name": name,
            "status": status,
            "passed": passed,
            "skipped": skipped,
            "message": message,
            "details": details,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "number": self.check_number
        })
        if skipped:
            self.skipped += 1
        elif passed:
            self.passed += 1
        else:
            self.failed += 1

        # Print immediately
        self._print_check(self.checks[-1])

    def _print_check(self, check: dict):
        """Print a single check result with professional formatting."""
        if check.get("skipped"):
            status_color = Colors.BRIGHT_YELLOW
            status_icon = "○"
            status_text = "SKIP"
        elif check["passed"]:
            status_color = Colors.BRIGHT_GREEN
            status_icon = Symbols.CHECK
            status_text = "PASS"
        else:
            status_color = Colors.BRIGHT_RED
            status_icon = Symbols.CROSS
            status_text = "FAIL"

        # Status line
        print()
        print(f"  {status_color}{Colors.BOLD}[{status_icon}]{Colors.RESET} {Colors.WHITE}{Colors.BOLD}{check['name']}{Colors.RESET}"
              f"")
        print(f"      {Colors.DIM}Status:{Colors.RESET}  {status_color}{status_text}{Colors.RESET}"
              f"")
        print(f"      {Colors.DIM}Result:{Colors.RESET}"
              f"  {check['message']}")

        # Details (if any)
        if check["details"]:
            print(f"      {Colors.DIM}Details:{Colors.RESET}"
              f"")
            for line in check["details"].split("\n"):
                if line.strip():
                    # Highlight ACTION REQUIRED
                    if "ACTION REQUIRED" in line:
                        print(f"        {Colors.BRIGHT_YELLOW}{Symbols.ARROW} {line.strip()}{Colors.RESET}"
              f"")
                    elif line.strip().startswith("-"):
                        print(f"        {Colors.CYAN}{Symbols.BULLET}{Colors.RESET}"
              f" {line.strip()[1:].strip()}")
                    else:
                        print(f"        {Colors.DIM}{Symbols.PIPE}{Colors.RESET}"
              f" {line.strip()}")

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
        total = self.passed + self.failed + self.skipped

        print()
        self._separator("═")
        print()

        # Title
        print(f"  {Colors.BOLD}{Colors.WHITE}PREREQUISITE CHECK SUMMARY{Colors.RESET}"
              f"")
        print()

        # Time info
        print(f"  {Colors.DIM}┌─ Execution Details{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}  Started  : {Colors.WHITE}{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}  Finished : {Colors.WHITE}{end_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}  Duration : {Colors.WHITE}{duration:.2f}s{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}└{'─' * 40}{Colors.RESET}"
              f"")
        print()

        # Results summary

        not_executed = self.TOTAL_CHECKS - total
        print(f"  {Colors.DIM}┌─ Results Overview{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}  Total Checks : {Colors.BOLD}{Colors.WHITE}{self.TOTAL_CHECKS}{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}  Executed     : {Colors.WHITE}{total}{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_GREEN}{Symbols.CHECK} Passed{Colors.RESET}      : {Colors.BRIGHT_GREEN}{self.passed}{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_YELLOW}○ Skipped{Colors.RESET}     : {Colors.BRIGHT_YELLOW}{self.skipped}{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_RED}{Symbols.CROSS} Failed{Colors.RESET}      : {Colors.BRIGHT_RED}{self.failed}{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.DIM}○ Not Executed{Colors.RESET}: {Colors.DIM}{not_executed}{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}"
              f"")

        # Progress bar - continuous: green (passed+skipped) | red (failed) | gray (not executed)
        passed_count = self.passed + self.skipped
        bar_segments = []
        for _ in range(passed_count):
            bar_segments.append(f"{Colors.BRIGHT_GREEN}███{Colors.RESET}")
        for _ in range(self.failed):
            bar_segments.append(f"{Colors.BRIGHT_RED}███{Colors.RESET}")
        remaining = self.TOTAL_CHECKS - total
        for _ in range(remaining):
            bar_segments.append(f"{Colors.DIM}░░░{Colors.RESET}")
        progress_bar = "".join(bar_segments)
        print(f"  {Colors.DIM}│{Colors.RESET}"
              f"  Progress    : [{progress_bar}] {passed_count}/{self.TOTAL_CHECKS} passed")
        print(f"  {Colors.DIM}└{'─' * 40}{Colors.RESET}"
              f"")
        print()

        # Detailed results table
        print(f"  {Colors.DIM}┌─ Check Results{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}│{Colors.RESET}"
              f"")

        for check in self.checks:
            num = f"{check['number']:02d}"
            if check.get("skipped"):
                status = f"{Colors.BRIGHT_YELLOW}○ SKIP{Colors.RESET}"
            elif check["passed"]:
                status = f"{Colors.BRIGHT_GREEN}{Symbols.CHECK} PASS{Colors.RESET}"
            else:
                status = f"{Colors.BRIGHT_RED}{Symbols.CROSS} FAIL{Colors.RESET}"

            print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.WHITE}{num}{Colors.RESET}  {status}  {Colors.WHITE}{check['name']}{Colors.RESET}"
              f"")
            print(f"  {Colors.DIM}│{Colors.RESET}       {Colors.DIM}{check['message']}{Colors.RESET}"
              f"")
            # Show key details for important checks (omnia.sh, etc.)
            if check.get('details') and ('omnia.sh' in check['details'] or 'Omnia Branch' in check['details']):
                for line in check['details'].split('\n'):
                    if line.strip():
                        print(f"  {Colors.DIM}│{Colors.RESET}       {Colors.CYAN}{line.strip()}{Colors.RESET}"
              f"")

        print(f"  {Colors.DIM}│{Colors.RESET}"
              f"")
        print(f"  {Colors.DIM}└{'─' * 60}{Colors.RESET}"
              f"")
        print()

        # Final status banner
        self._separator("═")
        if self.failed > 0:
            print()
            print(f"  {Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}  PREREQUISITE CHECK FAILED  {Colors.RESET}"
              f"")
            print()
            print(f"  {Colors.BRIGHT_RED}{Symbols.CROSS}{Colors.RESET}"
              f" {self.failed} check(s) failed. Review the errors above and fix the issues.")
            print(f"  {Colors.DIM}  Run the check again after fixing the problems.{Colors.RESET}"
              f"")
        else:
            print()
            print(f"  {Colors.BG_GREEN}{Colors.WHITE}{Colors.BOLD}  ALL CHECKS PASSED  {Colors.RESET}"
              f"")
            print()
            print(f"  {Colors.BRIGHT_GREEN}{Symbols.CHECK}{Colors.RESET}"
              f" System is ready for OIM deployment.")
        print()
        self._separator("═")
        print()

    def save_report(self, filepath: str):
        """Save report to file (plain text without colors)."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        total = self.passed + self.failed + self.skipped

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
            f.write(f"  Skipped      : {self.skipped}\n")
            f.write(f"  Failed       : {self.failed}\n")
            f.write(f"  Success Rate : {(self.passed/total*100) if total > 0 else 0:.1f}%\n")

            f.write("\n" + "-" * 70 + "\n")
            f.write("DETAILED RESULTS\n")
            f.write("-" * 70 + "\n\n")

            for check in self.checks:
                if check.get("skipped"):
                    status = "[SKIP]"
                elif check["passed"]:
                    status = "[PASS]"
                else:
                    status = "[FAIL]"
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


def run_all_prereq_checks(stop_on_failure: bool = None, save_report: bool = True) -> Dict:
    """
    Run all prerequisite checks with detailed reporting.

    Args:
        stop_on_failure: If True, stop execution on first failure.
                         If None, uses skip_on_failure from omnia_test_config.yml (inverted)
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
    print(f"  {Colors.DIM}┌─ Configuration{Colors.RESET}"
              f"")
    # Use the exported config path
    config_path = OMNIA_TEST_CONFIG_PATH
    print(f"  {Colors.DIM}│{Colors.RESET}  Config File     : {Colors.WHITE}{config_path}{Colors.RESET}"
              f"")
    # Use the actual runtime stop_on_failure value (not from config)
    if stop_on_failure:
        print(f"  {Colors.DIM}│{Colors.RESET}  Stop on Failure : {Colors.BRIGHT_YELLOW}true{Colors.RESET}"
              f" (stop on first failure)")
    else:
        print(f"  {Colors.DIM}│{Colors.RESET}  Stop on Failure : {Colors.BRIGHT_GREEN}false{Colors.RESET}"
              f" (continue on failure)")

    # Show target OIM server
    oim_ip = OIM_PREREQ_VARS.get('oim_server_ip', '')
    oim_user = OIM_PREREQ_VARS.get('oim_ssh_user', 'root')
    if oim_ip and oim_ip.strip():
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_YELLOW}OIM Server{Colors.RESET}     : {Colors.BRIGHT_YELLOW}{oim_user}@{oim_ip}{Colors.RESET}"
              f" (via SSH)")
    else:
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_RED}OIM Server{Colors.RESET}     : {Colors.BRIGHT_RED}(not configured){Colors.RESET}"
              f"")
    print(f"  {Colors.DIM}│{Colors.RESET}  PXE Interface   : {Colors.CYAN}{OIM_PREREQ_VARS.get('pxe_interface') or '(not set)'}{Colors.RESET}"
              f"")
    print(f"  {Colors.DIM}│{Colors.RESET}  Public Interface: {Colors.CYAN}{OIM_PREREQ_VARS.get('public_interface') or '(not set)'}{Colors.RESET}"
              f"")
    print(f"  {Colors.DIM}│{Colors.RESET}  NFS Server      : {Colors.CYAN}{OIM_PREREQ_VARS.get('nfs_server') or '(not set)'}{Colors.RESET}"
              f"")
    print(f"  {Colors.DIM}│{Colors.RESET}  NFS Share Path  : {Colors.CYAN}{OIM_PREREQ_VARS.get('nfs_share_path') or '(not set)'}{Colors.RESET}"
              f"")
    print(f"  {Colors.DIM}│{Colors.RESET}  NFS Min Capacity: {Colors.CYAN}{OIM_PREREQ_VARS.get('nfs_min_capacity_gb', 100)} GB{Colors.RESET}"
              f"")
    print(f"  {Colors.DIM}│{Colors.RESET}  Podman Min Ver  : {Colors.CYAN}{OIM_PREREQ_VARS.get('podman_min_version')}{Colors.RESET}"
              f"")
    print(f"  {Colors.DIM}│{Colors.RESET}  Artifactory Repo: {Colors.CYAN}{OIM_PREREQ_VARS.get('omnia_repo_url') or '(not set)'}{Colors.RESET}"
              f"")
    print(f"  {Colors.DIM}│{Colors.RESET}  Artifactory Br  : {Colors.CYAN}{OIM_PREREQ_VARS.get('artifactory_branch')}{Colors.RESET}"
              f"")
    print(f"  {Colors.DIM}│{Colors.RESET}  Clone Path      : {Colors.CYAN}{OIM_PREREQ_VARS.get('omnia_clone_path')}{Colors.RESET}"
              f"")
    reconfig = OIM_PREREQ_VARS.get('reconfigure_images', False)
    if reconfig:
        print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_GREEN}Reconfigure Imgs{Colors.RESET}: {Colors.BRIGHT_GREEN}true{Colors.RESET}"
              f" (will clone & build)")
        core_tag = OIM_PREREQ_VARS.get('core_tag')
        if core_tag:
            print(f"  {Colors.DIM}│{Colors.RESET}  Core Tag        : {Colors.CYAN}{core_tag}{Colors.RESET}"
              f"")
        omnia_br = OIM_PREREQ_VARS.get('omnia_branch')
        if omnia_br:
            print(f"  {Colors.DIM}│{Colors.RESET}  Omnia Branch    : {Colors.CYAN}{omnia_br}{Colors.RESET}"
              f"")
        else:
            print(f"  {Colors.DIM}│{Colors.RESET}  {Colors.BRIGHT_RED}Omnia Branch{Colors.RESET}    : {Colors.BRIGHT_RED}(REQUIRED - not set){Colors.RESET}"
              f"")
    else:
        print(f"  {Colors.DIM}│{Colors.RESET}  Reconfigure Imgs: {Colors.DIM}false{Colors.RESET}"
              f" (skip git clone & build)")
    print(f"  {Colors.DIM}└{'─' * 60}{Colors.RESET}"
              f"")
    print()

    # First check SSH connectivity to OIM server before running any checks
    ssh_validation = validate_ssh_connection()
    if not ssh_validation["valid"]:
        _report.add_check("SSH Connectivity", False, ssh_validation["message"], ssh_validation.get("details", ""))
        return _finish_report(_report, False, save_report)

    _report.add_check("SSH Connectivity", True, ssh_validation["message"], "")

    # Run all checks
    _run_all_checks(stop_on_failure)

    # Determine final status
    all_passed = _report.failed == 0

    return _finish_report(_report, all_passed, save_report)


def _run_all_checks(stop_on_failure: bool):
    """Run all prerequisite checks."""
    # Check 1: Hostname Configuration (FIRST TASK)
    result = configure_hostname()
    passed = result.get("passed", False)
    details = ""
    if result.get("details"):
        details = result["details"]
    elif result.get("instruction"):
        details = result["instruction"]
    _report.add_check("Hostname Configuration", passed, result.get("message", ""), details)
    if not passed and stop_on_failure:
        return

    # Check 2: IPMI Tool
    result = check_ipmi_tool()
    passed = result.get("installed", False)
    details = result.get("instruction", "")
    _report.add_check("IPMI Tool", passed, result.get("message", ""), details)
    if not passed and stop_on_failure:
        return

    # Check 3: Hardware Validation
    result = validate_hardware()
    passed = result.get("passed", False)
    details = ""
    if "checks" in result:
        for c in result["checks"]:
            details += f"{c['name']}: {c['message']}\n"
    _report.add_check("Hardware Validation", passed,
                      "Hardware meets minimum requirements" if passed else "Hardware validation FAILED",
                      details)
    if not passed and stop_on_failure:
        return

    # Check 4: OS Validation
    result = validate_os()
    passed = result.get("passed", False)
    details = result.get("details", "")
    if result.get("os_info"):
        os_info = result["os_info"]
        if os_info.get('full'):
            details += f"\nOS: {os_info.get('full')}"
        if os_info.get('kernel'):
            details += f"\nKernel: {os_info.get('kernel')}"
        if os_info.get('build'):
            details += f"\nBuild: {os_info.get('build')}"
    _report.add_check("OS Validation", passed, result.get("message", ""), details)
    if not passed and stop_on_failure:
        return

    # Check 5: Network Interfaces
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
        return

    # Check 6: PXE NIC Configuration
    result = configure_pxe_nic()
    passed = result.get("passed", False)
    details = result.get("details", "")
    if result.get("already_configured"):
        details += f"\nCurrent IP: {result.get('current_ip', '')}"
    elif result.get("new_ip"):
        details += f"\nConfigured IP: {result.get('new_ip', '')}"
    _report.add_check("PXE NIC Configuration", passed, result.get("message", ""), details)
    if not passed and stop_on_failure:
        return

    # Check 6b: Warn if PXE interface appears to be an internet-facing NIC
    pxe_public_result = check_pxe_is_public_interface()
    if pxe_public_result.get("warning"):
        _log(pxe_public_result["message"], "WARN")
        _report.add_check(
            "PXE / Public Interface Overlap", True,
            pxe_public_result["message"],
            pxe_public_result.get("details", "")
        )

    # Check 7: NFS Server
    result = check_nfs_reachable()
    passed = result.get("reachable", False)
    _report.add_check("NFS Server", passed, result.get("message", ""), result.get("details", ""))
    if not passed and stop_on_failure:
        return

    # Check 8: Internet Connectivity
    result = check_internet()
    passed = result.get("available", False)
    _report.add_check("Internet Connectivity", passed, result.get("message", ""), result.get("details", ""))
    if not passed and stop_on_failure:
        return

    # Check 9: Podman
    result = check_podman()
    passed = result.get("passed", False)
    _report.add_check("Podman", passed, result.get("message", ""), result.get("details", ""))
    if not passed and stop_on_failure:
        return

    # Check 10-12: Git, Omnia Artifactory Clone, Build Container Images (only if reconfigure_images is true)
    reconfigure_images = OIM_PREREQ_VARS.get("reconfigure_images", False)

    if reconfigure_images:
        result = ensure_git_installed()
        passed = result.get("installed", False)
        _report.add_check("Git", passed, result.get("message", ""), result.get("details", ""))
        if not passed and stop_on_failure:
            return

        # Check 11: Omnia Artifactory Clone
        result = clone_omnia_repo()
        passed = result.get("passed", False)
        _report.add_check("Omnia Artifactory", passed, result.get("message", ""), result.get("details", ""))
        if not passed and stop_on_failure:
            return

        # Check 12: Build Container Images
        result = build_container_images()
        passed = result.get("passed", False)
        _report.add_check("Container Build", passed, result.get("message", ""), result.get("details", ""))
        if not passed and stop_on_failure:
            return
    else:
        _log("Skipping Git, Omnia Artifactory, and Container Build (reconfigure_images: false)", "INFO")
        skip_msg = "Skipped (reconfigure_images: false)"
        skip_details = "Set 'reconfigure_images: true' in omnia_test_config.yml to enable"
        _report.add_check("Git", True, skip_msg, skip_details, skipped=True)
        _report.add_check("Omnia Artifactory", True, skip_msg, skip_details, skipped=True)
        _report.add_check("Container Build", True, skip_msg, skip_details, skipped=True)

    # Check 13: Download omnia.sh (always runs - creates directory if needed)
    result = download_omnia_sh()
    passed = result.get("passed", False)
    _report.add_check("Download omnia.sh", passed, result.get("message", ""), result.get("details", ""))


def _finish_report(report: PrereqReport, all_passed: bool, save_report: bool = True) -> Dict:
    """Print summary, save report, and return final result."""
    report.print_summary()

    if save_report:
        # Save report in project root (same folder as omnia_test_config.yml)
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
