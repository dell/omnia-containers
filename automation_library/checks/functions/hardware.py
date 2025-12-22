"""Hardware validation functions for OIM prerequisite checks."""

import re
from typing import Dict

from ...core.formatting import log as _log
from ..messages.oim_prereq_msgs import OIM_PREREQ_MSGS
from ..vars.oim_prereq_vars import OIM_PREREQ_VARS
from .system import run_command, run_shell


def check_ipmi_tool() -> Dict:
    """Check if IPMI tool is installed, install if not."""
    _log("Checking IPMI tool...", "INFO")
    ipmi_tool = OIM_PREREQ_VARS["ipmi_tool"]
    rc, stdout, _ = run_command([ipmi_tool, "-V"])

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
        rc, stdout, _ = run_command([ipmi_tool, "-V"])
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
    rc, _, stderr = run_command(["dnf", "install", "-y", ipmi_package], timeout=120)

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
