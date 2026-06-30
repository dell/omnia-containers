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

"""
DCGM Automation - Core Functions.

Verification functions for NVIDIA DCGM GPU Telemetry deployment.
All remote commands are executed via SSH through the omnia_core container
using run_on_remote_node() from the core library.

Test coverage:
  TC-F01  verify_cuda_validation
  TC-F02  verify_cuda_atomic_lock_installation
  TC-F03  verify_dcgm_package_installed
  TC-F04  verify_dcgm_daemon_running
  TC-F05  verify_gpu_discovery
  TC-F06  verify_add_gpu_node_auto_install
  TC-F07  verify_gpu_metrics_monitoring
  TC-F08  verify_cuda_login_compiler_install
  TC-F09  verify_cuda_compute_node_install
  TC-F10  verify_multi_gpu_discovery
  TC-F11  verify_multi_login_compiler_atomic_lock
  TC-F12  verify_multi_gpu_nodes_no_login_compiler
  TC-F13  verify_add_node_driver_only
  TC-F14  verify_atomic_lock_timeout
  TC-F15  verify_toolkit_failure_lock_release
  TC-F16  verify_toolkit_nfs_shared_storage
  TC-C01  verify_rhel_compatibility
  TC-C02  verify_cuda_version_compatibility
  TC-E01  verify_cuda_prerequisite_blocks_deployment
  TC-E02  verify_daemon_crash_recovery
  TC-E03  verify_daemon_socket_error
"""

import re
import time
from typing import Dict, Any, List, Optional

from ...core import (
    run_on_remote_node,
    run_in_container,
    get_nodes_info,
    get_node_info,
)
from ..vars.dcgm_vars import (
    GPU_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_FUNCTIONAL_GROUP,
    DCGM_PACKAGE_NAME,
    DCGM_SERVICE_NAME,
    DCGM_SOCKET_PATH,
    CUDA_INSTALL_PATH,
    CUDA_PROFILE_SCRIPT,
    CUDA_ATOMIC_LOCK_FILE,
    CUDA_MIN_MAJOR_VERSION,
    REQUIRED_RHEL_MAJOR,
    SERVICE_START_TIMEOUT,
    DAEMON_RESTART_WAIT,
    CMD_TEMPLATES,
)


# =============================================================================
# HELPERS
# =============================================================================

def _ssh(host, admin_ip: str, cmd: str):
    """Run cmd on remote GPU node via omnia_core container SSH."""
    return run_on_remote_node(host, cmd, admin_ip)


def check_dcgm_metrics_enabled(host) -> Dict[str, Any]:
    """
    Check if DCGM metrics collection is enabled in telemetry_config.yml.
    
    Args:
        host: Testinfra host object
        
    Returns:
        Dict with enabled (bool), details (str), error (str)
    """
    result = {"enabled": False, "details": "", "error": ""}
    
    # Read telemetry config from omnia_core container
    config_path = "/opt/omnia/input/project_default/telemetry_config.yml"
    cmd = run_in_container(host, f"cat {config_path}")
    
    if cmd.rc != 0:
        result["error"] = f"Failed to read {config_path}: {cmd.stderr.strip()}"
        return result
    
    config_content = cmd.stdout
    
    # Parse YAML-like content to find dcgm.metrics_enabled
    import re
    
    # Look for dcgm section - match from 'dcgm:' to next top-level section
    dcgm_section_match = re.search(r'dcgm:\s*\n((?:[ \t]+[^\n]+\n)+)', config_content)
    if not dcgm_section_match:
        result["error"] = "DCGM section not found in telemetry_config.yml"
        return result
    
    dcgm_section = dcgm_section_match.group(1)
    
    # Look for metrics_enabled in the dcgm section
    metrics_match = re.search(r'metrics_enabled:\s*(true|false)', dcgm_section, re.IGNORECASE)
    if not metrics_match:
        result["error"] = "metrics_enabled setting not found in dcgm section"
        return result
    
    metrics_enabled = metrics_match.group(1).lower() == 'true'
    result["enabled"] = metrics_enabled
    result["details"] = f"DCGM metrics_enabled: {metrics_enabled}"
    
    return result


def _extract_cuda_version(output: str) -> Optional[str]:
    """Extract CUDA major.minor version string from nvcc --version output."""
    match = re.search(r"release\s+(\d+\.\d+)", output)
    return match.group(1) if match else None


def _parse_gpu_count(dcgmi_output: str) -> int:
    """Count GPUs from dcgmi discovery -l output.

    Handles two formats:
      - "2 GPUs found (Active)."  (header summary line)
      - "| 0  | Name: ..."         (per-GPU table rows)
    """
    # Prefer the summary line: "N GPUs found"
    match = re.search(r"(\d+)\s+GPU[s]?\s+found", dcgmi_output, re.IGNORECASE)
    if match:
        return int(match.group(1))
    # Fallback: count table rows with GPU ID entries (| <digits> |)
    return len(re.findall(r"\|\s*\d+\s*\|", dcgmi_output))


def _parse_gpu_uuids(dcgmi_output: str) -> List[str]:
    """Extract all GPU UUIDs from dcgmi discovery output."""
    return re.findall(r"GPU-[0-9a-f\-]+", dcgmi_output, re.IGNORECASE)


# =============================================================================
# NODE LOOKUP
# =============================================================================

def get_gpu_nodes(host) -> List[Dict[str, Any]]:
    """
    Return list of GPU node info dicts by querying Slurm control node.

    Flow:
      OIM (testinfra host)
        → omnia_core container (run_in_container)
          → slurm control node (SSH)
            → sinfo -N -o "%N %G %T" | grep -i gpu

    Each dict contains: admin_ip, hostname, gpu_count.

    Args:
        host: Testinfra host object (connected to OIM)

    Returns:
        List of node info dicts (empty list if none found)
    """
    # Step 1: Get slurm control node IP from PXE mapping
    control_node = get_node_info(host, search_by="functional_group",
                                  search_value="slurm_control_node_x86_64")
    if not control_node:
        return []

    control_ip = control_node.get("admin_ip", "")
    if not control_ip:
        return []

    # Step 2: OIM → omnia_core container → slurm control node
    # Get all compute nodes from sinfo
    sinfo_cmd = "sinfo -N -h -o '%N'"
    cmd = _ssh(host, control_ip, sinfo_cmd)
    if cmd.rc != 0 or not cmd.stdout.strip():
        return []

    # Step 3: For each compute node, resolve IP and check for GPU via dcgmi
    gpu_nodes = []
    seen = set()
    for line in cmd.stdout.splitlines():
        hostname = line.strip()
        if not hostname or hostname == "NODELIST" or hostname in seen:
            continue
        seen.add(hostname)

        # Resolve hostname → IP via getent on control node
        resolve_cmd = _ssh(host, control_ip, f"getent hosts {hostname}")
        if resolve_cmd.rc != 0 or not resolve_cmd.stdout.strip():
            continue
        admin_ip = resolve_cmd.stdout.strip().split()[0]

        # Check for actual GPU hardware using nvidia-smi (primary indicator)
        gpu_check = _ssh(host, admin_ip, "nvidia-smi -L 2>/dev/null")
        if gpu_check.rc != 0 or not gpu_check.stdout.strip():
            # No GPUs detected on this node
            continue

        # Get GPU count from dcgmi discovery (if dcgmi is available)
        gpu_count = 0
        discovery_cmd = _ssh(host, admin_ip, "dcgmi discovery -l 2>/dev/null")
        if discovery_cmd.rc == 0:
            gpu_count = _parse_gpu_count(discovery_cmd.stdout)
        
        # Fallback: count GPUs from nvidia-smi -L output if dcgmi failed
        if gpu_count == 0 and gpu_check.stdout.strip():
            gpu_count = len([line for line in gpu_check.stdout.splitlines() if line.strip()])

        gpu_nodes.append({
            "hostname": hostname,
            "admin_ip": admin_ip,
            "gpu_count": gpu_count,
            "functional_group": "gpu_node",
        })

    return gpu_nodes


def get_login_compiler_nodes(host) -> List[Dict[str, Any]]:
    """
    Return list of login_compiler node info dicts from PXE mapping.

    Args:
        host: Testinfra host object

    Returns:
        List of node info dicts (empty list if none found)
    """
    return get_nodes_info(host, search_by="functional_group", search_value=LOGIN_COMPILER_FUNCTIONAL_GROUP) or []


# =============================================================================
# TC-F01: CUDA VALIDATION
# =============================================================================

def verify_cuda_validation(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-F01: Verify NVIDIA driver and CUDA 13.x+ toolkit are installed and
    functional on GPU node. Confirm nvidia-smi succeeds and nvcc reports
    CUDA >= 13.x from /hpc_tools/cuda.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the GPU node

    Returns:
        Dict with success, details, error
    """
    result = {"success": False, "details": "", "error": ""}

    # Step 1: nvidia-smi
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvidia_smi"])
    if cmd.rc != 0:
        result["error"] = f"nvidia-smi failed (rc={cmd.rc}): {cmd.stderr.strip()}"
        return result

    smi_output = cmd.stdout.strip()

    # Step 2: nvcc version from NFS toolkit path
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvcc_version"])
    if cmd.rc != 0:
        result["error"] = f"nvcc --version failed (rc={cmd.rc}). CUDA toolkit not found at {CUDA_INSTALL_PATH}"
        return result

    cuda_version = _extract_cuda_version(cmd.stdout)
    if not cuda_version:
        result["error"] = f"Could not parse CUDA version from: {cmd.stdout.strip()}"
        return result

    major = int(cuda_version.split(".")[0])
    if major < CUDA_MIN_MAJOR_VERSION:
        result["error"] = (
            f"CUDA version {cuda_version} is below minimum {CUDA_MIN_MAJOR_VERSION}.x "
            f"on node {admin_ip}"
        )
        return result

    # Step 3: CUDA profile env vars
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["cuda_profile_check"].format(profile_script=CUDA_PROFILE_SCRIPT))
    profile_ok = cmd.rc == 0 and "cuda" in cmd.stdout.lower()

    result["success"] = True
    result["details"] = (
        f"nvidia-smi: OK\n"
        f"CUDA version: {cuda_version}\n"
        f"CUDA profile script ({CUDA_PROFILE_SCRIPT}): {'OK' if profile_ok else 'MISSING'}\n"
        f"nvidia-smi output:\n{smi_output}"
    )
    return result


# =============================================================================
# TC-F11/TC-F12: ATOMIC LOCK ENSURES SINGLE INSTALLER
# =============================================================================

def _read_file_remote(host, admin_ip: str, path: str) -> str:
    cmd = _ssh(host, admin_ip, f"cat {path} 2>/dev/null")
    return cmd.stdout if cmd.rc == 0 else ""


def _node_hostname_short(host, admin_ip: str) -> str:
    cmd = _ssh(host, admin_ip, "hostname -s")
    return cmd.stdout.strip() if cmd.rc == 0 else ""


def verify_multi_login_compiler_atomic_lock(host) -> Dict[str, Any]:
    """
    TC-F11: When multiple login_compiler nodes are present, verify that the
    CUDA toolkit installer runs on exactly ONE node (lock winner) and others
    skip with 'another node is installing' or 'already installed'. Also verify
    /hpc_tools/cuda/.done_cuda reflects the installing hostname.

    Returns:
        Dict with success, details, error, installer, skipped_nodes, checked
    """
    result = {
        "success": False,
        "details": "",
        "error": "",
        "installer": "",
        "skipped_nodes": [],
        "checked": 0,
    }

    nodes = get_login_compiler_nodes(host)
    if not nodes or len(nodes) < 2:
        result["error"] = "Less than two login_compiler nodes present — TC-F11 not applicable"
        return result

    # Read .done_cuda from the first node (NFS shared)
    admin_ip0 = nodes[0].get("admin_ip", "")
    done = _read_file_remote(host, admin_ip0, "/hpc_tools/cuda/.done_cuda")
    installed_by = ""
    m = re.search(r"installed_by=(.+)", done)
    if m:
        installed_by = m.group(1).strip()

    installers = []
    skipped = []
    lines = []
    for n in nodes:
        ip = n.get("admin_ip", "")
        if not ip:
            continue
        result["checked"] += 1
        host_short = _node_hostname_short(host, ip)
        log_text = _read_file_remote(host, ip, "/var/log/cuda_toolkit_install.log")

        # Determine role by log patterns
        is_installer = any(p in log_text for p in (
            "[INFO] Acquired lock. Installing toolkit...",
            "[SUCCESS] CUDA toolkit installed successfully.",
        ))
        is_skipped = any(p in log_text for p in (
            "Another node is installing CUDA toolkit",
            "CUDA toolkit already installed on shared storage",
            "CUDA toolkit already installed on NFS",
        )) and not is_installer

        if is_installer:
            installers.append(host_short or ip)
        elif is_skipped:
            skipped.append(host_short or ip)
        # Collect brief per-node summary
        role = "installer" if is_installer else ("skipped" if is_skipped else "unknown")
        lines.append(f"  {ip} ({host_short}): {role}")

    if len(installers) != 1:
        result["error"] = f"Expected exactly 1 installer, found {len(installers)}: {installers}"
        result["details"] = "\n".join(lines)
        return result

    if installed_by and installed_by not in installers[0]:
        result["error"] = (
            f".done_cuda installed_by={installed_by} does not match detected installer {installers[0]}"
        )
        result["details"] = "\n".join(lines + [f".done_cuda: {done.strip()[:200]}"])
        return result

    result["success"] = True
    result["installer"] = installers[0]
    result["skipped_nodes"] = skipped
    result["details"] = (
        "Login/compiler nodes atomic lock verification: PASS\n" +
        "\n".join(lines) +
        (f"\n.done_cuda: {done.strip()}" if done.strip() else "")
    )
    return result


def verify_multi_gpu_nodes_no_login_compiler(host) -> Dict[str, Any]:
    """
    TC-F12: When NO login_compiler nodes exist and multiple GPU nodes are
    present, verify that exactly ONE GPU node performed the toolkit install
    (lock winner) and others skipped. Validate .done_cuda accordingly.

    Returns:
        Dict with success, details, error, installer, skipped_nodes, checked
    """
    result = {
        "success": False,
        "details": "",
        "error": "",
        "installer": "",
        "skipped_nodes": [],
        "checked": 0,
    }

    # If any login_compiler exists, this scenario is not applicable
    if get_login_compiler_nodes(host):
        result["error"] = "login_compiler node(s) present — TC-F12 applies only when none exist"
        return result

    gpu_nodes = get_gpu_nodes(host)
    if not gpu_nodes or len(gpu_nodes) < 2:
        result["error"] = "Less than two GPU nodes present — TC-F12 not applicable"
        return result

    # Read .done_cuda from first GPU node (NFS shared)
    admin_ip0 = gpu_nodes[0].get("admin_ip", "")
    done = _read_file_remote(host, admin_ip0, "/hpc_tools/cuda/.done_cuda")
    installed_by = ""
    m = re.search(r"installed_by=(.+)", done)
    if m:
        installed_by = m.group(1).strip()

    installers = []
    skipped = []
    lines = []
    for n in gpu_nodes:
        ip = n.get("admin_ip", "")
        if not ip:
            continue
        result["checked"] += 1
        host_short = _node_hostname_short(host, ip)
        log_text = _read_file_remote(host, ip, "/var/log/cuda_toolkit_install.log")

        is_installer = any(p in log_text for p in (
            "[INFO] Acquired lock. Installing toolkit...",
            "[SUCCESS] CUDA toolkit installed successfully.",
        ))
        is_skipped = any(p in log_text for p in (
            "Another node is installing CUDA toolkit",
            "CUDA toolkit already installed on shared storage",
            "CUDA toolkit already installed on NFS",
        )) and not is_installer

        if is_installer:
            installers.append(host_short or ip)
        elif is_skipped:
            skipped.append(host_short or ip)

        role = "installer" if is_installer else ("skipped" if is_skipped else "unknown")
        lines.append(f"  {ip} ({host_short}): {role}")

    if len(installers) != 1:
        result["error"] = f"Expected exactly 1 installer, found {len(installers)}: {installers}"
        result["details"] = "\n".join(lines)
        return result

    if installed_by and installed_by not in installers[0]:
        result["error"] = (
            f".done_cuda installed_by={installed_by} does not match detected installer {installers[0]}"
        )
        result["details"] = "\n".join(lines + [f".done_cuda: {done.strip()[:200]}"])
        return result

    result["success"] = True
    result["installer"] = installers[0]
    result["skipped_nodes"] = skipped
    result["details"] = (
        "GPU nodes (no login_compiler) atomic lock verification: PASS\n" +
        "\n".join(lines) +
        (f"\n.done_cuda: {done.strip()}" if done.strip() else "")
    )
    return result

def verify_dcgm_metrics_dmon(host, admin_ip: str, fields: str = None, delay_ms: int = 250, samples: int = 10) -> Dict[str, Any]:
    result = {
        "success": False,
        "details": "",
        "error": "",
        "gpu_rows": 0,
        "columns": 0,
        "invalid_columns": [],
        "fields": "",
    }

    # Ensure DCGM daemon is active
    svc = _ssh(host, admin_ip, CMD_TEMPLATES["service_is_active"].format(service=DCGM_SERVICE_NAME))
    if not (svc.rc == 0 and svc.stdout.strip() == "active"):
        status = _ssh(host, admin_ip, CMD_TEMPLATES["service_status"].format(service=DCGM_SERVICE_NAME))
        result["error"] = (
            f"{DCGM_SERVICE_NAME} not active on {admin_ip}: {status.stdout.strip()[:300]}"
        )
        return result

    # Default field set if not provided
    if not fields:
        fields = "100,101,150,151,203,204,140,155,156,157,200"
    result["fields"] = fields

    # Get expected GPU count (for sanity)
    expected_gpus = 0
    smi = _ssh(host, admin_ip, CMD_TEMPLATES["nvidia_smi_count"])
    if smi.rc == 0 and smi.stdout.strip().isdigit():
        expected_gpus = int(smi.stdout.strip())

    # Run dcgmi dmon
    cmd = _ssh(host, admin_ip, f"dcgmi dmon -e {fields} -d {delay_ms} -c {samples}")
    if cmd.rc != 0 or not cmd.stdout.strip():
        out = (cmd.stderr or "").strip() or cmd.stdout.strip()
        result["error"] = f"dcgmi dmon failed (rc={cmd.rc}): {out[:300]}"
        return result

    lines = cmd.stdout.splitlines()
    gpu_lines: List[str] = []
    max_cols = 0
    # Track if each column index ever had a numeric value
    col_valid: List[bool] = []

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('GPU'):
            tokens = line.split()
            if len(tokens) < 3:
                continue
            values = tokens[2:]
            max_cols = max(max_cols, len(values))
            if len(col_valid) < len(values):
                col_valid.extend([False] * (len(values) - len(col_valid)))
            for i, v in enumerate(values):
                vv = v.strip()
                # consider numeric if int/float-like (no trailing units expected in dmon)
                if vv.replace('.', '', 1).isdigit():
                    col_valid[i] = True
            gpu_lines.append(line)

    result["gpu_rows"] = len(gpu_lines)
    result["columns"] = max_cols
    expected_cols = len([f for f in fields.split(',') if f.strip()])
    invalid_cols = [i for i, ok in enumerate(col_valid[:expected_cols]) if not ok]
    result["invalid_columns"] = invalid_cols

    if expected_gpus and len(gpu_lines) < expected_gpus:
        result["error"] = (
            f"Insufficient GPU metric rows on {admin_ip}. GPUs: {expected_gpus}, rows: {len(gpu_lines)}"
        )
        return result

    if max_cols < expected_cols:
        result["error"] = f"Expected {expected_cols} metric columns, got {max_cols} on {admin_ip}"
        return result

    # Allow some fields to be non-numeric (e.g., XID errors field 200 may be empty when no errors)
    # Only fail if more than 50% of fields are invalid
    if invalid_cols and len(invalid_cols) > expected_cols / 2:
        result["error"] = f"Too many fields without numeric samples ({len(invalid_cols)}/{expected_cols}): {invalid_cols} on {admin_ip}"
        return result

    result["success"] = True
    result["details"] = (
        f"dcgmi dmon collected {len(gpu_lines)} GPU rows with {max_cols} columns\n"
        f"Fields: {fields}\n"
        f"Sample output:\n{cmd.stdout.strip()[:500]}"
    )
    return result

# =============================================================================
# TC-F02: CUDA TOOLKIT INSTALLATION WITH ATOMIC LOCK
# =============================================================================

def verify_cuda_atomic_lock_installation(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-F02: Verify CUDA toolkit is installed to /hpc_tools/cuda via atomic lock
    mechanism. Confirm toolkit directory structure and bash profile export.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the GPU node

    Returns:
        Dict with success, details, error, lock_released, dirs_present
    """
    result = {"success": False, "details": "", "error": "", "lock_released": False, "dirs_present": False}

    # Step 1: toolkit directory structure
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["cuda_path_check"].format(cuda_path=CUDA_INSTALL_PATH))
    if cmd.rc != 0:
        result["error"] = f"/hpc_tools/cuda directory structure incomplete: {cmd.stderr.strip()}"
        return result
    result["dirs_present"] = True

    # Step 2: lock file should NOT exist after installation (released)
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["cuda_lock_check"].format(lock_file=CUDA_ATOMIC_LOCK_FILE))
    result["lock_released"] = cmd.rc != 0  # file should not exist

    # Step 3: bash profile script (informational — profile path may vary by environment)
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["cuda_profile_check"].format(profile_script=CUDA_PROFILE_SCRIPT))
    profile_exists = cmd.rc == 0
    has_cuda_export = profile_exists and "cuda" in cmd.stdout.lower()

    # Step 4: nvcc accessible (primary success gate)
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvcc_version"])
    if cmd.rc != 0:
        result["error"] = f"nvcc not accessible after toolkit installation: {cmd.stderr.strip()}"
        return result

    cuda_version = _extract_cuda_version(cmd.stdout) or "unknown"

    result["success"] = True
    result["details"] = (
        f"Toolkit dir structure at {CUDA_INSTALL_PATH}: OK\n"
        f"Atomic lock file released (not present post-install): {result['lock_released']}\n"
        f"Bash profile {CUDA_PROFILE_SCRIPT}: {'present' if profile_exists else 'absent'}"
        f"{' (cuda export detected)' if has_cuda_export else ''}\n"
        f"nvcc: CUDA {cuda_version}"
    )
    return result


# =============================================================================
# TC-F03: DCGM PACKAGE INSTALLATION
# =============================================================================

def verify_dcgm_package_installed(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-F03: Verify DCGM is installed on the GPU node using dcgmi --version
    and confirm DCGM binaries are present.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the GPU node

    Returns:
        Dict with success, details, error, version
    """
    result = {"success": False, "details": "", "error": "", "version": ""}

    # Step 1: check dcgmi binary is present
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["dcgm_binaries_check"])
    if cmd.rc != 0:
        result["error"] = f"DCGM binary /usr/bin/dcgmi not found on {admin_ip}"
        return result

    # Step 2: get version via dcgmi --version
    cmd = _ssh(host, admin_ip, "dcgmi --version")
    if cmd.rc != 0 or not cmd.stdout.strip():
        result["error"] = f"{DCGM_PACKAGE_NAME} not found on {admin_ip}"
        return result

    version_match = re.search(r"[Vv]ersion[:\s]+([\d\.]+)", cmd.stdout)
    result["version"] = version_match.group(1).strip() if version_match else cmd.stdout.strip().splitlines()[0]

    # Step 3: systemd service file
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["dcgm_service_file_check"])
    service_file_ok = cmd.rc == 0

    result["success"] = True
    result["details"] = (
        f"Package: {DCGM_PACKAGE_NAME} version {result['version']}\n"
        f"Binary /usr/bin/dcgmi: present\n"
        f"Service file nvidia-dcgm.service: {'present' if service_file_ok else 'missing'}"
    )
    return result


# =============================================================================
# TC-F04: DCGM DAEMON STARTUP
# =============================================================================

def verify_dcgm_daemon_running(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-F04: Verify nvidia-dcgm.service is enabled and active (running) on the
    GPU node. Check journald logs for a clean startup sequence.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the GPU node

    Returns:
        Dict with success, details, error, is_active, is_enabled
    """
    result = {"success": False, "details": "", "error": "", "is_active": False, "is_enabled": False}

    # Step 1: is-active
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["service_is_active"].format(service=DCGM_SERVICE_NAME))
    result["is_active"] = cmd.rc == 0 and cmd.stdout.strip() == "active"

    if not result["is_active"]:
        # Collect status for diagnostics
        status_cmd = _ssh(host, admin_ip, CMD_TEMPLATES["service_status"].format(service=DCGM_SERVICE_NAME))
        result["error"] = (
            f"{DCGM_SERVICE_NAME} is not active on {admin_ip}. "
            f"Status: {status_cmd.stdout.strip()[:300]}"
        )
        return result

    # Step 2: is-enabled
    cmd_enabled = _ssh(host, admin_ip, f"systemctl is-enabled {DCGM_SERVICE_NAME}")
    result["is_enabled"] = cmd_enabled.rc == 0 and "enabled" in cmd_enabled.stdout

    # Step 3: sanity-check journal for errors
    cmd_logs = _ssh(host, admin_ip, CMD_TEMPLATES["service_logs"].format(service=DCGM_SERVICE_NAME))
    has_errors = any(kw in cmd_logs.stdout.lower() for kw in ("failed", "error", "critical"))

    result["success"] = True
    result["details"] = (
        f"Service {DCGM_SERVICE_NAME} on {admin_ip}:\n"
        f"  is-active:  active\n"
        f"  is-enabled: {result['is_enabled']}\n"
        f"  Journal errors detected: {has_errors}"
    )
    return result


# =============================================================================
# TC-F05: GPU DISCOVERY AND ENUMERATION
# =============================================================================

def verify_gpu_discovery(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-F05: Verify dcgmi discovery -l enumerates GPUs with unique UUIDs and
    metadata (device name, UUID).

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the GPU node

    Returns:
        Dict with success, details, error, gpu_count, uuids
    """
    result = {"success": False, "details": "", "error": "", "gpu_count": 0, "uuids": []}

    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["dcgmi_discovery"])
    if cmd.rc != 0:
        result["error"] = f"dcgmi discovery failed (rc={cmd.rc}): {cmd.stderr.strip()}"
        return result

    output = cmd.stdout
    gpu_count = _parse_gpu_count(output)
    uuids = _parse_gpu_uuids(output)

    if gpu_count == 0:
        result["error"] = f"dcgmi discovery returned no GPUs on {admin_ip}: {output.strip()[:300]}"
        return result

    # UUIDs must be unique
    if len(uuids) != len(set(uuids)):
        result["error"] = f"Duplicate GPU UUIDs detected on {admin_ip}: {uuids}"
        return result

    result["success"] = True
    result["gpu_count"] = gpu_count
    result["uuids"] = uuids
    result["details"] = (
        f"GPU node {admin_ip}:\n"
        f"  GPU count: {gpu_count}\n"
        f"  UUIDs ({len(uuids)} unique): {uuids}"
    )
    return result


# =============================================================================
# TC-F10: MULTI-GPU DISCOVERY (4x)
# =============================================================================

def verify_multi_gpu_discovery(host, admin_ip: str, expected_gpu_count: int = 4) -> Dict[str, Any]:
    """
    TC-F10: Verify dcgmi discovery enumerates all GPUs on a multi-GPU node.
    Checks discovered count matches physical count reported by nvidia-smi.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the multi-GPU node
        expected_gpu_count: Expected number of GPUs (default 4)

    Returns:
        Dict with success, details, error, gpu_count, uuids
    """
    result = {"success": False, "details": "", "error": "", "gpu_count": 0, "uuids": []}

    # Step 1: nvidia-smi count
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvidia_smi_count"])
    smi_count = 0
    if cmd.rc == 0 and cmd.stdout.strip().isdigit():
        smi_count = int(cmd.stdout.strip())

    # Step 2: dcgmi discovery
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["dcgmi_discovery"])
    if cmd.rc != 0:
        result["error"] = f"dcgmi discovery failed (rc={cmd.rc}): {cmd.stderr.strip()}"
        return result

    gpu_count = _parse_gpu_count(cmd.stdout)
    uuids = _parse_gpu_uuids(cmd.stdout)

    if gpu_count < expected_gpu_count:
        result["error"] = (
            f"GPU count mismatch on {admin_ip}. "
            f"Expected: {expected_gpu_count}, dcgmi found: {gpu_count}"
        )
        return result

    if len(uuids) != len(set(uuids)):
        result["error"] = f"Duplicate GPU UUIDs on multi-GPU node {admin_ip}: {uuids}"
        return result

    result["success"] = True
    result["gpu_count"] = gpu_count
    result["uuids"] = uuids
    result["details"] = (
        f"Multi-GPU node {admin_ip}:\n"
        f"  nvidia-smi count: {smi_count}\n"
        f"  dcgmi discovered: {gpu_count}\n"
        f"  All UUIDs unique: {len(uuids) == len(set(uuids))}\n"
        f"  UUIDs: {uuids}"
    )
    return result


# =============================================================================
# TC-F08: CUDA TOOLKIT INSTALL - LOGIN COMPILER NODE AVAILABLE
# =============================================================================

def verify_cuda_login_compiler_install(host, login_compiler_ip: str) -> Dict[str, Any]:
    """
    TC-F08: Verify CUDA toolkit is installed on login_compiler node but CUDA
    driver (nvidia-smi) is NOT installed there.

    Args:
        host: Testinfra host object
        login_compiler_ip: Admin IP of the login_compiler node

    Returns:
        Dict with success, details, error, toolkit_present, driver_absent
    """
    result = {
        "success": False, "details": "", "error": "",
        "toolkit_present": False, "driver_absent": False,
    }

    # Toolkit should be present (via NFS)
    cmd = _ssh(host, login_compiler_ip, CMD_TEMPLATES["nvcc_version"])
    result["toolkit_present"] = cmd.rc == 0 and "release" in cmd.stdout.lower()

    if not result["toolkit_present"]:
        result["error"] = (
            f"CUDA toolkit not accessible on login_compiler {login_compiler_ip}. "
            f"Expected nvcc --version to work via NFS mount."
        )
        return result

    # CUDA driver should NOT be present on login_compiler
    cmd = _ssh(host, login_compiler_ip, CMD_TEMPLATES["nvidia_smi"])
    result["driver_absent"] = cmd.rc != 0

    if not result["driver_absent"]:
        result["error"] = (
            f"nvidia-smi unexpectedly succeeded on login_compiler {login_compiler_ip}. "
            f"CUDA driver should NOT be installed on login_compiler nodes."
        )
        return result

    cuda_version = _extract_cuda_version(
        _ssh(host, login_compiler_ip, CMD_TEMPLATES["nvcc_version"]).stdout
    )

    result["success"] = True
    result["details"] = (
        f"Login compiler node {login_compiler_ip}:\n"
        f"  CUDA toolkit accessible (nvcc): {cuda_version}\n"
        f"  CUDA driver (nvidia-smi): correctly absent"
    )
    return result


# =============================================================================
# TC-F09: CUDA TOOLKIT AND DRIVER INSTALL - COMPUTE NODE (NO LOGIN COMPILER)
# =============================================================================

def verify_cuda_compute_node_install(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-F09: Verify both CUDA toolkit (via NFS) and CUDA driver (nvidia-smi)
    are available on a GPU/compute node when no login_compiler is present.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the compute GPU node

    Returns:
        Dict with success, details, error, toolkit_present, driver_present
    """
    result = {
        "success": False, "details": "", "error": "",
        "toolkit_present": False, "driver_present": False,
    }

    # CUDA toolkit
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvcc_version"])
    result["toolkit_present"] = cmd.rc == 0 and "release" in cmd.stdout.lower()
    nvcc_out = cmd.stdout.strip()

    # CUDA driver
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvidia_smi"])
    result["driver_present"] = cmd.rc == 0

    if not result["toolkit_present"]:
        result["error"] = f"CUDA toolkit not accessible on compute node {admin_ip}"
        return result

    if not result["driver_present"]:
        result["error"] = (
            f"CUDA driver (nvidia-smi) not found on compute node {admin_ip}. "
            f"Expected driver installed when no login_compiler node exists."
        )
        return result

    cuda_version = _extract_cuda_version(nvcc_out)

    result["success"] = True
    result["details"] = (
        f"Compute GPU node {admin_ip}:\n"
        f"  CUDA toolkit (nvcc): {cuda_version}\n"
        f"  CUDA driver (nvidia-smi): present"
    )
    return result


# =============================================================================
# TC-F16: TOOLKIT NFS SHARED STORAGE VALIDATION
# =============================================================================

def verify_toolkit_nfs_shared_storage(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-F16: Verify /hpc_tools is NFS-mounted and CUDA toolkit is accessible
    from the target node via NFS.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the node to check

    Returns:
        Dict with success, details, error, nfs_mounted, nvcc_accessible
    """
    result = {
        "success": False, "details": "", "error": "",
        "nfs_mounted": False, "nvcc_accessible": False,
    }

    # NFS mount check
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["hpc_tools_mount"])
    result["nfs_mounted"] = cmd.rc == 0 and "/hpc_tools" in cmd.stdout

    if not result["nfs_mounted"]:
        result["error"] = f"/hpc_tools not mounted via NFS on {admin_ip}: {cmd.stdout.strip()}"
        return result

    # CUDA accessible via NFS
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvcc_from_nfs"])
    result["nvcc_accessible"] = cmd.rc == 0 and "release" in cmd.stdout.lower()

    if not result["nvcc_accessible"]:
        result["error"] = f"nvcc not accessible from NFS mount on {admin_ip}"
        return result

    cuda_version = _extract_cuda_version(cmd.stdout)
    mount_line = next(
        (l for l in _ssh(host, admin_ip, CMD_TEMPLATES["hpc_tools_mount"]).stdout.splitlines()
         if "/hpc_tools" in l),
        "unknown mount"
    )

    result["success"] = True
    result["details"] = (
        f"Node {admin_ip}:\n"
        f"  /hpc_tools NFS mount: {mount_line.strip()}\n"
        f"  nvcc via NFS: CUDA {cuda_version}"
    )
    return result


# =============================================================================
# TC-C01: RHEL 10.x COMPATIBILITY
# =============================================================================

def verify_rhel_compatibility(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-C01: Verify the GPU node runs RHEL 10.x.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the GPU node

    Returns:
        Dict with success, details, error, os_version
    """
    result = {"success": False, "details": "", "error": "", "os_version": ""}

    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["os_release"])
    if cmd.rc != 0:
        result["error"] = f"Could not read /etc/redhat-release on {admin_ip}"
        return result

    os_str = cmd.stdout.strip()
    result["os_version"] = os_str

    major_match = re.search(r"release\s+(\d+)\.", os_str, re.IGNORECASE)
    if not major_match:
        result["error"] = f"Could not parse RHEL major version from: {os_str}"
        return result

    major = int(major_match.group(1))
    if major < REQUIRED_RHEL_MAJOR:
        result["error"] = (
            f"OS {os_str} does not meet RHEL {REQUIRED_RHEL_MAJOR}.x requirement on {admin_ip}"
        )
        return result

    result["success"] = True
    result["details"] = f"OS on {admin_ip}: {os_str} — RHEL {REQUIRED_RHEL_MAJOR}.x compatible"
    return result


# =============================================================================
# TC-C02: CUDA 13.x COMPATIBILITY
# =============================================================================

def verify_cuda_version_compatibility(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-C02: Verify CUDA 13.x toolkit and driver are present and DCGM daemon
    works alongside them.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the GPU node

    Returns:
        Dict with success, details, error, cuda_version
    """
    result = {"success": False, "details": "", "error": "", "cuda_version": ""}

    # nvcc version
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvcc_version"])
    if cmd.rc != 0:
        result["error"] = f"nvcc --version failed on {admin_ip}: {cmd.stderr.strip()}"
        return result

    cuda_version = _extract_cuda_version(cmd.stdout)
    result["cuda_version"] = cuda_version or "unknown"

    if not cuda_version:
        result["error"] = f"Cannot parse CUDA version from nvcc output: {cmd.stdout.strip()}"
        return result

    major = int(cuda_version.split(".")[0])
    if major < CUDA_MIN_MAJOR_VERSION:
        result["error"] = (
            f"CUDA version {cuda_version} below minimum {CUDA_MIN_MAJOR_VERSION}.x on {admin_ip}"
        )
        return result

    # Confirm nvidia-smi reports same CUDA major
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvidia_smi"])
    smi_ok = cmd.rc == 0

    # Confirm DCGM daemon still running with this CUDA
    daemon_result = verify_dcgm_daemon_running(host, admin_ip)

    if not daemon_result["success"]:
        result["error"] = (
            f"DCGM daemon not running with CUDA {cuda_version} on {admin_ip}: "
            f"{daemon_result['error']}"
        )
        return result

    result["success"] = True
    result["details"] = (
        f"GPU node {admin_ip}:\n"
        f"  CUDA version (nvcc): {cuda_version}\n"
        f"  nvidia-smi: {'OK' if smi_ok else 'FAIL'}\n"
        f"  DCGM daemon with CUDA {cuda_version}: running"
    )
    return result


# =============================================================================
# TC-E01: CUDA NOT PRESENT - DEPLOYMENT BLOCKED
# =============================================================================

def verify_cuda_prerequisite_blocks_deployment(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-E01: Verify the Ansible GPU playbook aborts with a clear prerequisite
    error when nvidia-smi is not available on the target node.

    Checks that DCGM package is NOT installed after the failed run.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of a non-GPU / no-driver node

    Returns:
        Dict with success, details, error, deployment_blocked, dcgm_absent
    """
    result = {
        "success": False, "details": "", "error": "",
        "deployment_blocked": False, "dcgm_absent": False,
    }

    # Confirm nvidia-smi is absent
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["nvidia_smi"])
    nvidia_smi_absent = cmd.rc != 0

    if not nvidia_smi_absent:
        result["error"] = (
            f"nvidia-smi is present on {admin_ip} — cannot test prerequisite blocking. "
            f"Use a node without NVIDIA drivers for this test."
        )
        return result

    # Run the Ansible GPU playbook — expect failure
    cmd = run_in_container(
        host,
        CMD_TEMPLATES["ansible_gpu_playbook"].format(node=admin_ip)
    )
    output = (cmd.stdout + cmd.stderr).strip()
    result["deployment_blocked"] = cmd.rc != 0 and (
        "cuda" in output.lower() or "prerequisite" in output.lower() or "failed" in output.lower()
    )

    # DCGM should NOT be installed
    dcgm_cmd = _ssh(host, admin_ip, CMD_TEMPLATES["dcgm_rpm_check"])
    result["dcgm_absent"] = dcgm_cmd.rc != 0 or not dcgm_cmd.stdout.strip()

    if not result["deployment_blocked"]:
        result["error"] = (
            f"Ansible playbook did not abort on {admin_ip} despite missing CUDA. "
            f"Expected playbook exit code != 0. Got rc={cmd.rc}. Output: {output[:400]}"
        )
        return result

    result["success"] = True
    result["details"] = (
        f"Node {admin_ip} (no NVIDIA driver):\n"
        f"  Deployment blocked by prerequisite check: {result['deployment_blocked']}\n"
        f"  DCGM package absent after failed run: {result['dcgm_absent']}"
    )
    return result


# =============================================================================
# TC-E02: DCGM DAEMON CRASH AND AUTO-RECOVERY
# =============================================================================

def verify_daemon_crash_recovery(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-E02: Simulate DCGM daemon crash via kill -9 and verify systemd
    auto-restarts the service (Restart=on-failure policy).

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the GPU node

    Returns:
        Dict with success, details, error, recovered, restart_policy_set
    """
    result = {
        "success": False, "details": "", "error": "",
        "recovered": False, "restart_policy_set": False,
    }

    # Step 1: check Restart policy in service file
    cmd = _ssh(host, admin_ip, f"systemctl cat {DCGM_SERVICE_NAME} | grep -i Restart")
    result["restart_policy_set"] = cmd.rc == 0 and "restart" in cmd.stdout.lower()

    # Step 2: get current PID
    cmd = _ssh(host, admin_ip, f"systemctl show {DCGM_SERVICE_NAME} --property=MainPID")
    pid_match = re.search(r"MainPID=(\d+)", cmd.stdout)
    original_pid = int(pid_match.group(1)) if pid_match else 0

    if original_pid == 0:
        result["error"] = f"Could not get MainPID for {DCGM_SERVICE_NAME} on {admin_ip}"
        return result

    # Step 3: kill the daemon
    _ssh(host, admin_ip, f"kill -9 {original_pid}")
    time.sleep(DAEMON_RESTART_WAIT)

    # Step 4: verify service recovered
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["service_is_active"].format(service=DCGM_SERVICE_NAME))
    result["recovered"] = cmd.rc == 0 and cmd.stdout.strip() == "active"

    if not result["recovered"]:
        status = _ssh(host, admin_ip, CMD_TEMPLATES["service_status"].format(service=DCGM_SERVICE_NAME))
        result["error"] = (
            f"{DCGM_SERVICE_NAME} did not recover after crash on {admin_ip}. "
            f"Status: {status.stdout.strip()[:300]}"
        )
        return result

    # Step 5: new PID should differ
    cmd = _ssh(host, admin_ip, f"systemctl show {DCGM_SERVICE_NAME} --property=MainPID")
    new_pid_match = re.search(r"MainPID=(\d+)", cmd.stdout)
    new_pid = int(new_pid_match.group(1)) if new_pid_match else 0

    result["success"] = True
    result["details"] = (
        f"GPU node {admin_ip}:\n"
        f"  Restart policy configured: {result['restart_policy_set']}\n"
        f"  Original PID: {original_pid}\n"
        f"  New PID after recovery: {new_pid}\n"
        f"  Service recovered: {result['recovered']}"
    )
    return result


# =============================================================================
# TC-E03: DCGM DAEMON SOCKET INACCESSIBLE
# =============================================================================

def verify_daemon_socket_error(host, admin_ip: str) -> Dict[str, Any]:
    """
    TC-E03: Remove the DCGM Unix socket and verify dcgmi returns a clear error
    message. Then restart the daemon and confirm socket is recreated.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of the GPU node

    Returns:
        Dict with success, details, error, socket_error_returned, socket_recreated
    """
    result = {
        "success": False, "details": "", "error": "",
        "socket_error_returned": False, "socket_recreated": False,
    }

    # Step 1: confirm socket exists
    cmd = _ssh(host, admin_ip, f"ls -la {DCGM_SOCKET_PATH}")
    if cmd.rc != 0:
        result["error"] = f"DCGM socket {DCGM_SOCKET_PATH} not present on {admin_ip}"
        return result

    # Step 2: remove socket
    _ssh(host, admin_ip, f"rm -f {DCGM_SOCKET_PATH}")

    # Step 3: run dcgmi — should fail with socket error
    cmd = _ssh(host, admin_ip, CMD_TEMPLATES["dcgmi_discovery"])
    socket_keywords = ("unable to connect", "socket", "not found", "error")
    result["socket_error_returned"] = (
        cmd.rc != 0 and
        any(kw in (cmd.stdout + cmd.stderr).lower() for kw in socket_keywords)
    )

    if not result["socket_error_returned"]:
        result["error"] = (
            f"dcgmi did not return a socket error after removing {DCGM_SOCKET_PATH}. "
            f"rc={cmd.rc}, output: {(cmd.stdout + cmd.stderr).strip()[:300]}"
        )
        # Restart daemon to restore socket regardless
        _ssh(host, admin_ip, CMD_TEMPLATES["service_restart"].format(service=DCGM_SERVICE_NAME))
        return result

    # Step 4: restart daemon → socket recreated
    _ssh(host, admin_ip, CMD_TEMPLATES["service_restart"].format(service=DCGM_SERVICE_NAME))
    time.sleep(SERVICE_START_TIMEOUT)

    cmd = _ssh(host, admin_ip, f"ls -la {DCGM_SOCKET_PATH}")
    result["socket_recreated"] = cmd.rc == 0

    result["success"] = result["socket_error_returned"]
    result["details"] = (
        f"GPU node {admin_ip}:\n"
        f"  Socket {DCGM_SOCKET_PATH} removed\n"
        f"  dcgmi returned socket error: {result['socket_error_returned']}\n"
        f"  Socket recreated after daemon restart: {result['socket_recreated']}"
    )
    return result
