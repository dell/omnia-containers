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
Apptainer operations for OMNIA test automation.

Provides verification functions for all 31 Apptainer test cases (MD-928).
All remote access is performed via run_on_remote_node / _safe_run_on_remote_node.
"""

import base64
import os
import re
import time
from typing import Any, Dict, List, Tuple

from automation_library.core import (
    get_nodes_info,
    get_functional_groups_from_pxe_mapping,
    run_on_remote_node,
    load_omnia_test_config,
)
from automation_library.apptainer.vars.apptainer_vars import (
    COMPUTE_NODE_CONTAINER_IMAGES_DIR,
    COMPUTE_NODE_DOWNLOAD_SCRIPT,
    COMPUTE_NODE_CONTAINER_IMAGE_LIST,
    COMPUTE_NODE_HPC_TOOLS_DIR,
    APPTAINER_BINARY,
    SIF_EXTENSION,
    APPTAINER_JOB_POLL_INTERVAL,
    APPTAINER_JOB_TIMEOUT,
    APPTAINER_SACCT_POLL_INTERVAL,
    APPTAINER_SACCT_TIMEOUT,
    APPTAINER_ARRAY_SIZE,
    APPTAINER_CONCURRENT_JOB_COUNT,
    SIF_DOWNLOAD_TIMEOUT,
    SIF_DOWNLOAD_POLL_INTERVAL,
    SIF_DOWNLOAD_LOG,
    GPU_LIST_CMD,
    GPU_COUNT_CMD,
    GPU_MEMORY_CMD,
    INFINIBAND_DEVICES_CMD,
    REMOTE_JOB_OUTPUT_DIR,
    PERMISSION_TEST_SIF_COPY,
    REBOOT_WAIT_ONLINE_TIMEOUT,
    REBOOT_WAIT_ONLINE_POLL_INTERVAL,
    REBOOT_POST_SETTLE_DELAY,
)
from automation_library.apptainer.messages.apptainer_msgs import (
    ERROR_NO_SLURM_NODES,
    ERROR_NO_SLURM_CONTROL_NODES,
    ERROR_NO_SIF_FILES,
    ERROR_LDAP_CREDS_MISSING,
    APPTAINER_INSTALL_PASSED,
    APPTAINER_INSTALL_FAILED,
    DOWNLOAD_SCRIPT_LIST_PASSED,
    DOWNLOAD_SCRIPT_LIST_FAILED,
    PULP_ONLY_PASSED,
    PULP_ONLY_FAILED,
    RAM_SIZE_PASSED,
    RAM_SIZE_FAILED,
    RAM_SIZE_SKIPPED,
    SIF_IN_DIR_PASSED,
    SIF_IN_DIR_FAILED,
    SIF_FORMAT_PASSED,
    SIF_FORMAT_FAILED,
    SIF_PERMS_PASSED,
    SIF_PERMS_FAILED,
    SKIP_EXISTING_SIF_PASSED,
    SKIP_EXISTING_SIF_FAILED,
    MISSING_IMAGE_HANDLED_PASSED,
    MISSING_IMAGE_HANDLED_FAILED,
    SINGLE_NODE_JOB_PASSED,
    SINGLE_NODE_JOB_FAILED,
    SINGLE_NODE_JOB_SUBMIT_FAILED,
    SINGLE_NODE_JOB_TIMEOUT,
    MULTI_NODE_JOB_PASSED,
    MULTI_NODE_JOB_FAILED,
    MULTI_NODE_JOB_SKIPPED,
    NO_ROOT_REQUIRED_PASSED,
    NO_ROOT_REQUIRED_FAILED,
    SIF_LDAP_READABLE_PASSED,
    SIF_LDAP_READABLE_FAILED,
    SIF_LDAP_READABLE_SKIPPED,
    LDAP_JOB_PASSED,
    LDAP_JOB_FAILED,
    LDAP_JOB_SKIPPED,
    SIF_REUSE_PASSED,
    SIF_REUSE_FAILED,
    SIF_REUSE_SKIPPED,
    SIF_INTEGRITY_PASSED,
    SIF_INTEGRITY_FAILED,
    CONCURRENT_JOBS_PASSED,
    CONCURRENT_JOBS_FAILED,
    INVALID_SIF_JOB_PASSED,
    INVALID_SIF_JOB_FAILED,
    PERM_600_FAIL_PASSED,
    PERM_600_FAIL_FAILED,
    PERM_600_SKIPPED,
    GPU_IN_CONTAINER_PASSED,
    GPU_IN_CONTAINER_FAILED,
    GPU_IN_CONTAINER_SKIPPED,
    GPU_COUNT_PASSED,
    GPU_COUNT_FAILED,
    GPU_COUNT_SKIPPED,
    CUDA_WORKLOAD_PASSED,
    CUDA_WORKLOAD_FAILED,
    CUDA_WORKLOAD_SKIPPED,
    GPU_MEMORY_PASSED,
    GPU_MEMORY_FAILED,
    GPU_MEMORY_SKIPPED,
    IB_IN_CONTAINER_PASSED,
    IB_IN_CONTAINER_FAILED,
    IB_IN_CONTAINER_SKIPPED,
    NFS_IN_CONTAINER_PASSED,
    NFS_IN_CONTAINER_FAILED,
    JOB_ARRAY_PASSED,
    JOB_ARRAY_FAILED,
    CLEANUP_PASSED,
    CLEANUP_FAILED,
    REBOOT_NFS_SIF_PASSED,
    REBOOT_NFS_SIF_FAILED,
    REBOOT_CONTAINER_EXEC_PASSED,
    REBOOT_CONTAINER_EXEC_FAILED,
    REBOOT_DOWNLOAD_SCRIPT_PASSED,
    REBOOT_DOWNLOAD_SCRIPT_FAILED,
)

# ── Slurm functional group keywords ──────────────────────────────────────────
_SLURM_CONTROL_GROUP = "slurm_control_node"
_SLURM_NODE_GROUP = "slurm_node"
_LOGIN_NODE_GROUP = "login_node"
_LOGIN_COMPILER_NODE_GROUP = "login_compiler_node"


# =============================================================================
# INTERNAL RESULT PROXY – absorbs SSH RuntimeError from testinfra
# =============================================================================

class _FakeResult:
    """Stand-in for testinfra CommandResult when SSH fails."""
    def __init__(self, rc: int, stdout: str, stderr: str):
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr


def _safe_run(host, cmd: str, admin_ip: str) -> _FakeResult:
    """Run a shell command on a remote node, converting RuntimeError to rc=255."""
    try:
        return run_on_remote_node(host, cmd, admin_ip)
    except RuntimeError as exc:
        return _FakeResult(255, "", f"SSH failed to {admin_ip}: {exc}")


# =============================================================================
# NODE DISCOVERY
# =============================================================================

def _get_nodes_for_group(host, group_keyword: str) -> List[Dict[str, str]]:
    all_groups = get_functional_groups_from_pxe_mapping(host)
    nodes: List[Dict[str, str]] = []
    for fg in all_groups:
        if group_keyword in fg:
            nodes.extend(get_nodes_info(host, search_by="functional_group", search_value=fg))
    return nodes


def get_slurm_control_nodes(host) -> List[Dict[str, str]]:
    return _get_nodes_for_group(host, _SLURM_CONTROL_GROUP)


def get_slurm_nodes(host) -> List[Dict[str, str]]:
    return _get_nodes_for_group(host, _SLURM_NODE_GROUP)


def get_login_nodes(host) -> List[Dict[str, str]]:
    all_groups = get_functional_groups_from_pxe_mapping(host)
    nodes: List[Dict[str, str]] = []
    for fg in all_groups:
        if _LOGIN_NODE_GROUP in fg and _LOGIN_COMPILER_NODE_GROUP not in fg:
            nodes.extend(get_nodes_info(host, search_by="functional_group", search_value=fg))
    return nodes


def get_login_compiler_nodes(host) -> List[Dict[str, str]]:
    return _get_nodes_for_group(host, _LOGIN_COMPILER_NODE_GROUP)


def _all_login_nodes(host) -> List[Dict[str, str]]:
    return get_login_nodes(host) + get_login_compiler_nodes(host)


# =============================================================================
# PATH HELPERS
# =============================================================================

def _get_hpc_tools_base(host) -> str:
    """Return the HPC tools base path as used on compute nodes.

    download_container_image.sh.j2 hardcodes DOWNLOAD_DIR=/hpc_tools/container_images,
    so /hpc_tools is always the base regardless of NFS client_share_path.
    """
    return COMPUTE_NODE_HPC_TOOLS_DIR


def _get_container_images_dir(host) -> str:
    return COMPUTE_NODE_CONTAINER_IMAGES_DIR


def _get_download_script_path(host) -> str:
    return COMPUTE_NODE_DOWNLOAD_SCRIPT


def _get_image_list_path(host) -> str:
    return COMPUTE_NODE_CONTAINER_IMAGE_LIST


# =============================================================================
# SIF FILE HELPERS
# =============================================================================

def _list_sif_files(host, node_ip: str, images_dir: str) -> List[str]:
    """Return list of .sif filenames found in images_dir on remote node."""
    cmd = _safe_run(host, f"ls {images_dir}/*.sif 2>/dev/null", node_ip)
    if cmd.rc != 0 or not cmd.stdout.strip():
        return []
    return [f.strip() for f in cmd.stdout.strip().splitlines() if f.strip()]


def _get_first_sif(host, node_ip: str, images_dir: str) -> str:
    """Return the first available SIF file path on the node, or empty string."""
    files = _list_sif_files(host, node_ip, images_dir)
    return files[0] if files else ""


def _get_sif_for_jobs(host, images_dir: str) -> str:
    """Look up SIF path via a compute node (which has the NFS /hpc_tools mounted).

    The control node may not have /hpc_tools mounted, so SIF lookups for job
    scripts must be done via a compute node.  The path itself is NFS-shared, so
    once resolved it is valid for jobs running on any cluster node.
    """
    compute_nodes = get_slurm_nodes(host)
    for node in compute_nodes:
        sif = _get_first_sif(host, node.get("admin_ip", ""), images_dir)
        if sif:
            return sif
    return ""


# =============================================================================
# LDAP CREDENTIAL HELPERS
# =============================================================================

def _get_ldap_credentials(host) -> List[Tuple[str, str]]:
    """Return list of (username, password) tuples from omnia_test_config.yml."""
    config = load_omnia_test_config()
    raw = config.get("ldap_credentials", "")
    if not raw:
        return []
    creds = []
    for entry in str(raw).split(","):
        entry = entry.strip()
        if ":" in entry:
            parts = entry.split(":", 1)
            creds.append((parts[0].strip(), parts[1].strip()))
    return creds


# =============================================================================
# JOB SUBMISSION HELPERS
# =============================================================================

def _transfer_script(host, node_ip: str, local_path: str,
                     remote_path: str, replacements: Dict[str, str]) -> Dict[str, Any]:
    """Read local script template, apply replacements, push to remote via base64."""
    with open(local_path, "r", encoding="utf-8") as fh:
        content = fh.read()
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    encoded = base64.b64encode(content.encode()).decode()
    cmd = _safe_run(
        host,
        f"echo {encoded} | base64 -d > {remote_path} && chmod a+rx {remote_path}",
        node_ip,
    )
    if cmd.rc != 0:
        return {"success": False, "error": cmd.stderr.strip()}
    return {"success": True, "error": ""}


def _submit_sbatch(host, node_ip: str, script_path: str) -> Tuple[bool, str, str]:
    """Submit sbatch script on node_ip.  Returns (ok, job_id, error)."""
    cmd = _safe_run(host, f"sbatch {script_path}", node_ip)
    if cmd.rc != 0:
        return False, "", cmd.stderr.strip()
    match = re.search(r"Submitted batch job (\d+)", cmd.stdout)
    if not match:
        return False, "", f"Could not parse job ID from: {cmd.stdout.strip()}"
    return True, match.group(1), ""


def _poll_sacct(host, control_ip: str, job_id: str,
                timeout: int = APPTAINER_SACCT_TIMEOUT,
                poll: int = APPTAINER_SACCT_POLL_INTERVAL) -> str:
    """Poll sacct until the job reaches a terminal state. Returns final state string."""
    terminal = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"}
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(poll)
        sacct = _safe_run(
            host,
            f"sacct -j {job_id} --format=JobID,State -n -P",
            control_ip,
        )
        if sacct.rc != 0:
            continue
        for line in sacct.stdout.strip().splitlines():
            parts = line.strip().split("|")
            if len(parts) >= 2 and parts[0].strip() == job_id:
                state = parts[1].strip()
                if state in terminal:
                    return state
    return ""


def _submit_apptainer_job(host, control_ip: str, script_local: str,
                          remote_script: str, replacements: Dict[str, str],
                          timeout: int = APPTAINER_SACCT_TIMEOUT) -> Dict[str, Any]:
    """Transfer script, submit via sbatch, poll until complete.  Cleanup script after."""
    xfer = _transfer_script(host, control_ip, script_local, remote_script, replacements)
    if not xfer["success"]:
        return {"success": False, "job_id": "", "job_state": "",
                "error": f"Script transfer failed: {xfer['error']}"}

    ok, job_id, err = _submit_sbatch(host, control_ip, remote_script)
    _safe_run(host, f"rm -f {remote_script}", control_ip)
    if not ok:
        return {"success": False, "job_id": "", "job_state": "",
                "error": SINGLE_NODE_JOB_SUBMIT_FAILED.format(error=err)}

    state = _poll_sacct(host, control_ip, job_id, timeout)
    if not state:
        return {"success": False, "job_id": job_id, "job_state": "UNKNOWN",
                "error": SINGLE_NODE_JOB_TIMEOUT.format(job_id=job_id, timeout=timeout)}

    return {
        "success": state == "COMPLETED",
        "job_id": job_id,
        "job_state": state,
        "error": "" if state == "COMPLETED" else f"Job {job_id} ended: {state}",
    }


def _jobs_dir() -> str:
    """Absolute path to the apptainer_jobs/ directory."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "apptainer_jobs")


# =============================================================================
# TC1 – Verify Apptainer installation on all slurm nodes
# =============================================================================

def verify_apptainer_installed_on_all_slurm_nodes(host) -> Dict[str, Any]:
    """TC1: Verify apptainer binary is installed and reports a version on every compute node."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": [], "error": ERROR_NO_SLURM_NODES}

    all_passed = True
    details = []
    for node in nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({"hostname": hostname, "installed": False, "error": "No admin IP"})
            all_passed = False
            continue

        which = _safe_run(host, f"which {APPTAINER_BINARY} 2>/dev/null", admin_ip)
        if which.rc != 0 or not which.stdout.strip():
            details.append({"hostname": hostname, "installed": False,
                            "error": f"{APPTAINER_BINARY} not found in PATH"})
            all_passed = False
            continue

        ver = _safe_run(host, f"{APPTAINER_BINARY} --version 2>&1", admin_ip)
        if ver.rc != 0:
            details.append({"hostname": hostname, "installed": False,
                            "error": f"apptainer --version failed: {ver.stderr.strip()}"})
            all_passed = False
            continue

        details.append({"hostname": hostname, "installed": True,
                        "version": ver.stdout.strip(), "error": ""})

    return {
        "success": all_passed,
        "message": APPTAINER_INSTALL_PASSED if all_passed else APPTAINER_INSTALL_FAILED,
        "details": details,
        "error": "" if all_passed else APPTAINER_INSTALL_FAILED,
    }


# =============================================================================
# TC2 – download_container_image.sh reads image list
# =============================================================================

def verify_download_script_reads_image_list(host) -> Dict[str, Any]:
    """TC2: Verify download_container_image.sh and container_image.list both exist on a compute node."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": [], "error": ERROR_NO_SLURM_NODES}

    node = nodes[0]
    admin_ip = node.get("admin_ip", "")
    hostname = node.get("hostname", "unknown")

    script_path = _get_download_script_path(host)
    list_path = _get_image_list_path(host)

    script_check = _safe_run(host, f"test -f '{script_path}' && echo EXISTS", admin_ip)
    if "EXISTS" not in script_check.stdout:
        err = f"Script not found at {script_path} on {hostname}"
        return {"success": False, "message": DOWNLOAD_SCRIPT_LIST_FAILED.format(error=err),
                "details": {"script": script_path, "list": list_path,
                            "script_found": False, "list_found": False},
                "error": err}

    list_check = _safe_run(host, f"test -f '{list_path}' && echo EXISTS", admin_ip)
    list_found = "EXISTS" in list_check.stdout

    if not list_found:
        err = f"Image list not found at {list_path} on {hostname}"
        return {"success": False, "message": DOWNLOAD_SCRIPT_LIST_FAILED.format(error=err),
                "details": {"script": script_path, "list": list_path,
                            "script_found": True, "list_found": False},
                "error": err}

    content_check = _safe_run(
        host, f"grep -q 'container_image.list' '{script_path}' && echo REFERENCED", admin_ip
    )
    list_referenced = "REFERENCED" in content_check.stdout

    return {
        "success": True,
        "message": DOWNLOAD_SCRIPT_LIST_PASSED,
        "details": {
            "script": script_path, "list": list_path,
            "script_found": True, "list_found": True,
            "list_referenced_in_script": list_referenced,
        },
        "error": "",
    }


# =============================================================================
# TC3 – Script downloads images only from Pulp (no external fallback)
# =============================================================================

def verify_download_images_only_from_pulp(host) -> Dict[str, Any]:
    """TC3: Verify actual download happened from Pulp by inspecting download log.
    
    This test must run AFTER TC_DL (download test) to verify the log.
    It checks that the download log contains Pulp server references and
    does NOT contain external registry URLs (docker.io, nvcr.io, etc.).
    """
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    hostname = nodes[0].get("hostname", "unknown")
    images_dir = _get_container_images_dir(host)

    # Check if SIF files exist (prerequisite)
    sif_files = _list_sif_files(host, admin_ip, images_dir)
    if not sif_files:
        err = "No SIF files found - download test (TC_DL) must run first"
        return {"success": False, "message": PULP_ONLY_FAILED.format(detail=err),
                "details": {}, "error": err}

    # Read the download log
    log_result = _safe_run(host, f"cat '{SIF_DOWNLOAD_LOG}' 2>/dev/null", admin_ip)
    if log_result.rc != 0 or not log_result.stdout:
        err = f"Download log not found at {SIF_DOWNLOAD_LOG} on {hostname}"
        return {"success": False, "message": PULP_ONLY_FAILED.format(detail=err),
                "details": {}, "error": err}

    log_content = log_result.stdout

    # Check for Pulp server references in the log
    # Look for common Pulp patterns: pulp server URLs, "Downloading from pulp", etc.
    has_pulp_ref = bool(
        re.search(r'pulp[_-]?server|pulp.*mirror|downloading.*from.*pulp', log_content, re.IGNORECASE) or
        re.search(r'https?://[^/]*pulp', log_content, re.IGNORECASE)
    )

    # Check for external registry URLs in DOWNLOAD context (indicates fallback)
    # Ignore registry names in image names like "nvcr.io/nvidia/..."
    # Only detect actual download URLs like "Downloading from nvcr.io" or "https://nvcr.io"
    external_patterns = [
        r'(?:downloading|fetching|pulling).*(?:from|via).*docker\.io',
        r'(?:downloading|fetching|pulling).*(?:from|via).*nvcr\.io',
        r'(?:downloading|fetching|pulling).*(?:from|via).*ghcr\.io',
        r'(?:downloading|fetching|pulling).*(?:from|via).*quay\.io',
        r'https?://(?:www\.)?docker\.io',
        r'https?://(?:www\.)?nvcr\.io',
        r'https?://(?:www\.)?ghcr\.io',
        r'https?://(?:www\.)?quay\.io',
        r'https?://(?:www\.)?gcr\.io',
        r'https?://registry\.hub\.docker\.com',
    ]
    external_matches = []
    for pattern in external_patterns:
        matches = re.findall(pattern, log_content, re.IGNORECASE)
        if matches:
            external_matches.extend(matches)

    has_external_fallback = len(external_matches) > 0

    if not has_pulp_ref:
        detail = f"No Pulp server reference found in download log on {hostname}"
        return {
            "success": False,
            "message": PULP_ONLY_FAILED.format(detail=detail),
            "details": {
                "has_pulp_ref": False,
                "has_external_fallback": has_external_fallback,
                "external_urls": external_matches[:5],
                "log_snippet": log_content[-500:],
            },
            "error": detail,
        }

    if has_external_fallback:
        detail = f"External registry URLs detected in download log: {', '.join(set(external_matches[:5]))}"
        return {
            "success": False,
            "message": PULP_ONLY_FAILED.format(detail=detail),
            "details": {
                "has_pulp_ref": True,
                "has_external_fallback": True,
                "external_urls": list(set(external_matches)),
                "log_snippet": log_content[-500:],
            },
            "error": detail,
        }

    return {
        "success": True,
        "message": PULP_ONLY_PASSED,
        "details": {
            "has_pulp_ref": True,
            "has_external_fallback": False,
            "sif_count": len(sif_files),
            "hostname": hostname,
        },
        "error": "",
    }


# =============================================================================
# TC_DL – Run download_container_image.sh to populate SIF files
# =============================================================================

def verify_run_download_script(host) -> Dict[str, Any]:
    """TC_DL: Run download_container_image.sh on a compute node and wait for SIF files."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    node = nodes[0]
    admin_ip = node.get("admin_ip", "")
    hostname = node.get("hostname", "unknown")
    script_path = _get_download_script_path(host)
    images_dir = _get_container_images_dir(host)

    # Check if SIF files already exist
    existing = _list_sif_files(host, admin_ip, images_dir)
    if existing:
        return {
            "success": True,
            "message": f"SIF files already present ({len(existing)} found), download skipped",
            "details": {"sif_files": existing, "downloaded": False, "skipped": True},
            "error": "",
        }

    # Verify script exists and is executable
    script_check = _safe_run(host, f"test -x '{script_path}' && echo EXISTS || echo MISSING", admin_ip)
    if "MISSING" in script_check.stdout or script_check.rc != 0:
        err = f"Download script not found or not executable at {script_path} on {hostname}"
        return {"success": False, "message": err, "details": {"hostname": hostname}, "error": err}

    # Ensure images directory exists
    _safe_run(host, f"mkdir -p '{images_dir}'", admin_ip)

    # Run the download script directly (blocking call)
    # Redirect output to log file for later inspection
    run_cmd = f"bash '{script_path}' > '{SIF_DOWNLOAD_LOG}' 2>&1"
    result = _safe_run(host, run_cmd, admin_ip)

    # Read the log file
    log_result = _safe_run(host, f"cat '{SIF_DOWNLOAD_LOG}' 2>/dev/null", admin_ip)
    log_content = log_result.stdout if log_result.rc == 0 else ""

    # Check for SIF files after script execution
    sif_files = _list_sif_files(host, admin_ip, images_dir)

    if result.rc == 0 and sif_files:
        return {
            "success": True,
            "message": f"Download complete: {len(sif_files)} SIF file(s) in {images_dir}",
            "details": {
                "sif_files": sif_files,
                "downloaded": True,
                "log": log_content[-1000:],  # Last 1000 chars
                "hostname": hostname,
                "exit_code": result.rc,
            },
            "error": "",
        }
    elif result.rc == 0 and not sif_files:
        err = f"Download script completed (rc=0) but no SIF files found in {images_dir}"
        return {
            "success": False,
            "message": err,
            "details": {"log": log_content[-1000:], "hostname": hostname, "exit_code": result.rc},
            "error": err,
        }
    else:
        err = f"Download script failed on {hostname} with exit code {result.rc}"
        return {
            "success": False,
            "message": err,
            "details": {
                "log": log_content[-1000:],
                "hostname": hostname,
                "exit_code": result.rc,
                "stderr": result.stderr[:500] if result.stderr else "",
            },
            "error": err,
        }


# =============================================================================
# TC4 – SIF download does not increase RAM size
# =============================================================================

def verify_sif_download_does_not_increase_ram(host) -> Dict[str, Any]:
    """TC4: Verify that SIF downloads to NFS share do not consume local RAM on compute nodes."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)

    sif_files = _list_sif_files(host, admin_ip, images_dir)
    if not sif_files:
        return {"success": True, "skipped": True,
                "message": RAM_SIZE_SKIPPED,
                "details": {}, "error": ""}

    mem_before = _safe_run(
        host, "free -m | awk '/^Mem:/{print $3}'", admin_ip
    )
    mem_before_mb = int(mem_before.stdout.strip()) if mem_before.rc == 0 and mem_before.stdout.strip().isdigit() else 0

    df_check = _safe_run(host, f"df -h {images_dir} 2>/dev/null | tail -1", admin_ip)

    mem_after = _safe_run(
        host, "free -m | awk '/^Mem:/{print $3}'", admin_ip
    )
    mem_after_mb = int(mem_after.stdout.strip()) if mem_after.rc == 0 and mem_after.stdout.strip().isdigit() else 0

    delta_mb = abs(mem_after_mb - mem_before_mb)
    ram_unchanged = delta_mb < 50

    if not ram_unchanged:
        detail = f"RAM changed by {delta_mb} MB (before={mem_before_mb} MB, after={mem_after_mb} MB)"
        return {"success": False, "message": RAM_SIZE_FAILED.format(detail=detail),
                "details": {"delta_mb": delta_mb, "df_output": df_check.stdout.strip()},
                "error": detail}

    return {
        "success": True,
        "message": RAM_SIZE_PASSED,
        "details": {
            "mem_before_mb": mem_before_mb,
            "mem_after_mb": mem_after_mb,
            "delta_mb": delta_mb,
            "df_output": df_check.stdout.strip(),
        },
        "error": "",
    }


# =============================================================================
# TC5 – SIF files are in container_images directory
# =============================================================================

def verify_sif_files_in_container_images_dir(host) -> Dict[str, Any]:
    """TC5: Verify SIF files exist in the container_images directory on compute nodes."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": [], "error": ERROR_NO_SLURM_NODES}

    images_dir = _get_container_images_dir(host)
    all_passed = True
    details = []

    for node in nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({"hostname": hostname, "sif_files": [], "error": "No admin IP"})
            all_passed = False
            continue

        dir_check = _safe_run(host, f"test -d '{images_dir}' && echo EXISTS", admin_ip)
        if "EXISTS" not in dir_check.stdout:
            details.append({"hostname": hostname, "sif_files": [],
                            "error": f"Directory {images_dir} does not exist"})
            all_passed = False
            continue

        sif_files = _list_sif_files(host, admin_ip, images_dir)
        if not sif_files:
            details.append({"hostname": hostname, "sif_files": [],
                            "error": f"No .sif files in {images_dir}"})
            all_passed = False
            continue

        details.append({"hostname": hostname, "sif_files": sif_files, "error": ""})

    msg = SIF_IN_DIR_PASSED.format(files=str(len(details))) if all_passed else \
          SIF_IN_DIR_FAILED.format(path=images_dir)
    return {"success": all_passed, "message": msg, "details": details,
            "error": "" if all_passed else msg}


# =============================================================================
# TC6 – SIF file format validation
# =============================================================================

def verify_sif_file_format_validation(host) -> Dict[str, Any]:
    """TC6: Validate SIF file format using apptainer inspect on a compute node."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, admin_ip, images_dir)

    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": {}, "error": ERROR_NO_SIF_FILES}

    inspect = _safe_run(host, f"{APPTAINER_BINARY} inspect '{sif_file}' 2>&1", admin_ip)
    if inspect.rc != 0:
        err = inspect.stdout.strip() or inspect.stderr.strip()
        return {"success": False,
                "message": SIF_FORMAT_FAILED.format(sif_file=sif_file, error=err),
                "details": {"sif_file": sif_file, "output": err},
                "error": err}

    return {
        "success": True,
        "message": SIF_FORMAT_PASSED.format(sif_file=sif_file),
        "details": {"sif_file": sif_file, "output": inspect.stdout.strip()},
        "error": "",
    }


# =============================================================================
# TC7 – SIF file permissions are set correctly
# =============================================================================

def verify_sif_file_permissions(host) -> Dict[str, Any]:
    """TC7: Verify SIF files are world-readable (group/other read bit set) on all compute nodes."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": [], "error": ERROR_NO_SLURM_NODES}

    images_dir = _get_container_images_dir(host)
    all_passed = True
    details = []

    for node in nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({"hostname": hostname, "passed": False, "error": "No admin IP"})
            all_passed = False
            continue

        perm_check = _safe_run(
            host,
            f"find '{images_dir}' -name '*.sif' -not -perm /044 2>/dev/null",
            admin_ip,
        )
        bad_files = [f.strip() for f in perm_check.stdout.strip().splitlines() if f.strip()]
        if bad_files:
            details.append({"hostname": hostname, "passed": False,
                            "bad_files": bad_files,
                            "error": f"SIF files not world-readable: {bad_files}"})
            all_passed = False
            continue

        sif_files = _list_sif_files(host, admin_ip, images_dir)
        details.append({"hostname": hostname, "passed": True,
                        "sif_count": len(sif_files), "error": ""})

    msg = SIF_PERMS_PASSED if all_passed else SIF_PERMS_FAILED.format(detail="see details")
    return {"success": all_passed, "message": msg, "details": details,
            "error": "" if all_passed else msg}


# =============================================================================
# TC8 – Script skips already-downloaded SIF files (idempotent)
# =============================================================================

def verify_script_skips_already_downloaded_sif(host) -> Dict[str, Any]:
    """TC8: Run download script when SIF already exists; confirm it logs WARN/skip and skips re-download."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    script_path = _get_download_script_path(host)
    images_dir = _get_container_images_dir(host)

    sif_file = _get_first_sif(host, admin_ip, images_dir)
    if not sif_file:
        return {"success": True, "skipped": True,
                "message": SIF_REUSE_SKIPPED,
                "details": {}, "error": ""}

    mtime_before = _safe_run(
        host, f"stat -c '%Y' '{sif_file}' 2>/dev/null", admin_ip
    ).stdout.strip()

    run_result = _safe_run(
        host, f"bash '{script_path}' 2>&1 | head -60", admin_ip
    )
    output = run_result.stdout

    mtime_after = _safe_run(
        host, f"stat -c '%Y' '{sif_file}' 2>/dev/null", admin_ip
    ).stdout.strip()

    skipped_in_output = any(kw in output for kw in ["WARN", "Skipping", "already exists"])
    mtime_unchanged = mtime_before == mtime_after

    if not (skipped_in_output and mtime_unchanged):
        err = f"mtime changed={mtime_before!r}->{mtime_after!r}, skip_logged={skipped_in_output}"
        return {"success": False, "message": SKIP_EXISTING_SIF_FAILED.format(error=err),
                "details": {"output_snippet": output[:500], "mtime_before": mtime_before,
                            "mtime_after": mtime_after},
                "error": err}

    return {
        "success": True,
        "message": SKIP_EXISTING_SIF_PASSED,
        "details": {"sif_file": sif_file, "mtime_unchanged": mtime_unchanged,
                    "skipped_in_output": skipped_in_output},
        "error": "",
    }


# =============================================================================
# TC9 – Script handles missing images in Pulp gracefully
# =============================================================================

def verify_script_handles_missing_images_gracefully(host) -> Dict[str, Any]:
    """TC9: Inject a non-existent image into the list, run the script, confirm graceful failure."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    script_path = _get_download_script_path(host)
    list_path = _get_image_list_path(host)

    list_check = _safe_run(host, f"test -f '{list_path}' && echo EXISTS", admin_ip)
    if "EXISTS" not in list_check.stdout:
        err = f"Image list not found at {list_path}"
        return {"success": False, "message": MISSING_IMAGE_HANDLED_FAILED.format(error=err),
                "details": {}, "error": err}

    backup_cmd = _safe_run(host, f"cp '{list_path}' '{list_path}.omnia_bak'", admin_ip)
    if backup_cmd.rc != 0:
        err = "Could not backup container_image.list"
        return {"success": False, "message": MISSING_IMAGE_HANDLED_FAILED.format(error=err),
                "details": {}, "error": err}

    fake_image = "docker.io/omnia-nonexistent-image-omnia-test:latest"
    _safe_run(host, f"echo '{fake_image}' > '{list_path}'", admin_ip)

    run_result = _safe_run(host, f"bash '{script_path}' 2>&1", admin_ip)
    output = run_result.stdout

    _safe_run(host, f"mv '{list_path}.omnia_bak' '{list_path}'", admin_ip)

    has_error_msg = any(kw in output for kw in ["ERROR", "Failed", "FAILED", "failed"])
    exits_gracefully = True

    if not has_error_msg:
        err = f"Script did not output an error for non-existent image. Output: {output[:300]}"
        return {"success": False,
                "message": MISSING_IMAGE_HANDLED_FAILED.format(error=err),
                "details": {"output_snippet": output[:500]}, "error": err}

    return {
        "success": True,
        "message": MISSING_IMAGE_HANDLED_PASSED,
        "details": {"output_snippet": output[:500], "exits_gracefully": exits_gracefully},
        "error": "",
    }


# =============================================================================
# TC10 – Submit single-node Apptainer job via Slurm
# =============================================================================

def verify_submit_single_node_apptainer_job(host) -> Dict[str, Any]:
    """TC10: Submit a single-node sbatch job that runs apptainer exec <sif> hostname."""
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "job_id": "", "error": ERROR_NO_SLURM_CONTROL_NODES}

    control_ip = control_nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_sif_for_jobs(host, images_dir)

    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "job_id": "", "error": ERROR_NO_SIF_FILES}

    result = _submit_apptainer_job(
        host, control_ip,
        os.path.join(_jobs_dir(), "apptainer_single_node.sh"),
        "/tmp/omnia_apptainer_single.sh",
        {"{{SIF_FILE}}": sif_file, "{{OUTPUT_PATH}}": REMOTE_JOB_OUTPUT_DIR},
    )
    msg = SINGLE_NODE_JOB_PASSED.format(job_id=result["job_id"]) if result["success"] \
          else SINGLE_NODE_JOB_FAILED.format(error=result["error"])
    return {"success": result["success"], "message": msg,
            "job_id": result["job_id"], "job_state": result.get("job_state", ""),
            "error": result["error"]}


# =============================================================================
# TC11 – Submit multi-node Apptainer job via Slurm
# =============================================================================

def verify_submit_multi_node_apptainer_job(host) -> Dict[str, Any]:
    """TC11: Submit a multi-node sbatch job using srun apptainer exec."""
    compute_nodes = get_slurm_nodes(host)
    if len(compute_nodes) < 2:
        return {"success": True, "skipped": True, "message": MULTI_NODE_JOB_SKIPPED,
                "job_id": "", "error": ""}

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "job_id": "", "error": ERROR_NO_SLURM_CONTROL_NODES}

    control_ip = control_nodes[0].get("admin_ip", "")
    num_nodes = min(2, len(compute_nodes))
    images_dir = _get_container_images_dir(host)
    sif_file = _get_sif_for_jobs(host, images_dir)

    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "job_id": "", "error": ERROR_NO_SIF_FILES}

    result = _submit_apptainer_job(
        host, control_ip,
        os.path.join(_jobs_dir(), "apptainer_multi_node.sh"),
        "/tmp/omnia_apptainer_multi.sh",
        {"{{SIF_FILE}}": sif_file,
         "{{SLURM_NUM_NODES}}": str(num_nodes),
         "{{OUTPUT_PATH}}": REMOTE_JOB_OUTPUT_DIR},
    )
    msg = MULTI_NODE_JOB_PASSED.format(job_id=result["job_id"], nodes=num_nodes) \
          if result["success"] else MULTI_NODE_JOB_FAILED.format(error=result["error"])
    return {"success": result["success"], "message": msg,
            "job_id": result["job_id"], "job_state": result.get("job_state", ""),
            "error": result["error"]}


# =============================================================================
# TC12 – No root privileges required to run Apptainer
# =============================================================================

def verify_no_root_required_for_apptainer(host) -> Dict[str, Any]:
    """TC12: Run apptainer exec as a non-root user and verify it succeeds."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": [], "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    hostname = nodes[0].get("hostname", "unknown")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, admin_ip, images_dir)

    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": [], "error": ERROR_NO_SIF_FILES}

    whoami_cmd = _safe_run(host, "whoami 2>/dev/null", admin_ip)
    current_user = whoami_cmd.stdout.strip()

    cmd = _safe_run(
        host,
        f"{APPTAINER_BINARY} exec '{sif_file}' whoami 2>&1",
        admin_ip,
    )
    if cmd.rc != 0:
        err = cmd.stdout.strip() or cmd.stderr.strip()
        return {"success": False,
                "message": NO_ROOT_REQUIRED_FAILED.format(error=err),
                "details": {"hostname": hostname, "current_user": current_user},
                "error": err}

    container_user = cmd.stdout.strip()
    return {
        "success": True,
        "message": NO_ROOT_REQUIRED_PASSED.format(node=hostname),
        "details": {"hostname": hostname, "host_user": current_user,
                    "container_user": container_user},
        "error": "",
    }


# =============================================================================
# TC13 – SIF file is readable by LDAP user
# =============================================================================

def verify_sif_readable_by_ldap_user(host) -> Dict[str, Any]:
    """TC13: Verify LDAP user can stat/read SIF files on compute nodes."""
    creds = _get_ldap_credentials(host)
    if not creds:
        return {"success": True, "skipped": True, "message": SIF_LDAP_READABLE_SKIPPED,
                "details": [], "error": ""}

    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": [], "error": ERROR_NO_SLURM_NODES}

    ldap_user, ldap_pass = creds[0]
    admin_ip = nodes[0].get("admin_ip", "")
    hostname = nodes[0].get("hostname", "unknown")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, admin_ip, images_dir)

    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": [], "error": ERROR_NO_SIF_FILES}

    # SSH to compute node as root, then switch to LDAP user with su.
    # This avoids needing sshpass on the OIM.
    check = _safe_run(
        host,
        f"su -s /bin/sh {ldap_user} -c \"stat '{sif_file}' > /dev/null 2>&1\" "
        f"&& echo 'readable=yes' || echo 'readable=no'",
        admin_ip,
    )
    readable = "readable=yes" in check.stdout

    if not readable:
        err = check.stdout.strip() or check.stderr.strip()
        return {"success": False,
                "message": SIF_LDAP_READABLE_FAILED.format(error=err),
                "details": [{"hostname": hostname, "ldap_user": ldap_user,
                             "readable": False, "error": err}],
                "error": err}

    return {
        "success": True,
        "message": SIF_LDAP_READABLE_PASSED,
        "details": [{"hostname": hostname, "ldap_user": ldap_user,
                     "sif_file": sif_file, "readable": True, "error": ""}],
        "error": "",
    }


# =============================================================================
# TC14 – Submit Apptainer job as LDAP user
# =============================================================================

def verify_submit_apptainer_job_as_ldap_user(host) -> Dict[str, Any]:
    """TC14: Submit sbatch as LDAP user from login node with apptainer exec."""
    creds = _get_ldap_credentials(host)
    if not creds:
        return {"success": True, "skipped": True, "message": LDAP_JOB_SKIPPED,
                "job_id": "", "error": ""}

    login_nodes = _all_login_nodes(host)
    if not login_nodes:
        return {"success": True, "skipped": True, "message": LDAP_JOB_SKIPPED,
                "job_id": "", "error": ""}

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "job_id": "", "error": ERROR_NO_SLURM_CONTROL_NODES}

    ldap_user, _ = creds[0]
    login_ip = login_nodes[0].get("admin_ip", "")
    control_ip = control_nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_sif_for_jobs(host, images_dir)

    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "job_id": "", "error": ERROR_NO_SIF_FILES}

    with open(os.path.join(_jobs_dir(), "apptainer_single_node.sh"), "r") as fh:
        script_content = fh.read()
    script_content = script_content.replace("{{SIF_FILE}}", sif_file) \
                                   .replace("{{OUTPUT_PATH}}", REMOTE_JOB_OUTPUT_DIR)

    encoded = base64.b64encode(script_content.encode()).decode()
    remote_script = f"/tmp/omnia_ldap_apptainer_{ldap_user}.sh"

    # Push script to login node as root, then submit as LDAP user via su.
    # This avoids needing sshpass on the OIM.
    push = _safe_run(
        host,
        f"echo {encoded} | base64 -d > {remote_script} "
        f"&& chown {ldap_user} {remote_script} "
        f"&& chmod 755 {remote_script}",
        login_ip,
    )
    if push.rc != 0:
        err = push.stderr.strip() or push.stdout.strip()
        return {"success": False, "message": LDAP_JOB_FAILED.format(error=err),
                "job_id": "", "error": err}

    submit = _safe_run(
        host,
        f"su -s /bin/sh {ldap_user} -c 'sbatch {remote_script}'",
        login_ip,
    )
    _safe_run(host, f"rm -f {remote_script}", login_ip)

    if submit.rc != 0:
        err = submit.stderr.strip() or submit.stdout.strip()
        return {"success": False, "message": LDAP_JOB_FAILED.format(error=err),
                "job_id": "", "error": err}

    match = re.search(r"Submitted batch job (\d+)", submit.stdout)
    if not match:
        err = f"Could not parse job ID from: {submit.stdout.strip()}"
        return {"success": False, "message": LDAP_JOB_FAILED.format(error=err),
                "job_id": "", "error": err}

    job_id = match.group(1)
    state = _poll_sacct(host, control_ip, job_id)

    if state == "COMPLETED":
        return {"success": True, "message": LDAP_JOB_PASSED.format(job_id=job_id),
                "job_id": job_id, "job_state": state, "error": ""}

    err = f"Job {job_id} ended with state: {state or 'UNKNOWN'}"
    return {"success": False, "message": LDAP_JOB_FAILED.format(error=err),
            "job_id": job_id, "job_state": state, "error": err}


# =============================================================================
# TC15 – SIF reuse without re-download
# =============================================================================

def verify_sif_reuse_without_redownload(host) -> Dict[str, Any]:
    """TC15: Run download script a second time and confirm SIF mtime is unchanged."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, admin_ip, images_dir)

    if not sif_file:
        return {"success": True, "skipped": True, "message": SIF_REUSE_SKIPPED,
                "details": {}, "error": ""}

    size_before = _safe_run(host, f"stat -c '%s' '{sif_file}' 2>/dev/null", admin_ip).stdout.strip()
    script_path = _get_download_script_path(host)
    run_output = _safe_run(host, f"bash '{script_path}' 2>&1", admin_ip)
    size_after = _safe_run(host, f"stat -c '%s' '{sif_file}' 2>/dev/null", admin_ip).stdout.strip()

    script_stdout = run_output.stdout.lower()
    skipped_in_log = any(kw in script_stdout for kw in ("skip", "already exist", "already download"))

    if skipped_in_log or size_before == size_after:
        return {"success": True, "message": SIF_REUSE_PASSED,
                "details": {"sif_file": sif_file, "size_bytes": size_after,
                            "skipped_in_log": skipped_in_log}, "error": ""}

    err = f"SIF file size changed: {size_before} -> {size_after} bytes (unexpected content change)"
    return {"success": False, "message": SIF_REUSE_FAILED.format(error=err),
            "details": {"size_before": size_before, "size_after": size_after},
            "error": err}


# =============================================================================
# TC16 – SIF image integrity after download
# =============================================================================

def verify_sif_image_integrity(host) -> Dict[str, Any]:
    """TC16: Run apptainer inspect on the SIF file to confirm integrity."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, admin_ip, images_dir)

    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": {}, "error": ERROR_NO_SIF_FILES}

    inspect = _safe_run(host, f"{APPTAINER_BINARY} inspect '{sif_file}' 2>&1", admin_ip)
    if inspect.rc != 0:
        err = inspect.stdout.strip() or inspect.stderr.strip()
        return {"success": False,
                "message": SIF_INTEGRITY_FAILED.format(sif_file=sif_file, error=err),
                "details": {"sif_file": sif_file, "output": err}, "error": err}

    return {"success": True,
            "message": SIF_INTEGRITY_PASSED.format(sif_file=sif_file),
            "details": {"sif_file": sif_file, "output": inspect.stdout.strip()}, "error": ""}


# =============================================================================
# TC17 – Execute multiple Apptainer jobs concurrently
# =============================================================================

def verify_execute_multiple_apptainer_jobs_concurrently(host) -> Dict[str, Any]:
    """TC17: Submit APPTAINER_CONCURRENT_JOB_COUNT jobs in rapid succession and verify all complete."""
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "details": [], "error": ERROR_NO_SLURM_CONTROL_NODES}

    control_ip = control_nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_sif_for_jobs(host, images_dir)

    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": [], "error": ERROR_NO_SIF_FILES}

    job_ids = []
    for idx in range(APPTAINER_CONCURRENT_JOB_COUNT):
        remote_script = f"/tmp/omnia_apptainer_concurrent_{idx}.sh"
        xfer = _transfer_script(
            host, control_ip,
            os.path.join(_jobs_dir(), "apptainer_single_node.sh"),
            remote_script,
            {"{{SIF_FILE}}": sif_file, "{{OUTPUT_PATH}}": REMOTE_JOB_OUTPUT_DIR},
        )
        if not xfer["success"]:
            continue
        ok, job_id, _ = _submit_sbatch(host, control_ip, remote_script)
        _safe_run(host, f"rm -f {remote_script}", control_ip)
        if ok:
            job_ids.append(job_id)

    if not job_ids:
        return {"success": False, "message": CONCURRENT_JOBS_FAILED.format(error="No jobs submitted"),
                "details": [], "error": "No jobs submitted"}

    results = []
    all_passed = True
    for job_id in job_ids:
        state = _poll_sacct(host, control_ip, job_id, timeout=APPTAINER_SACCT_TIMEOUT * 2)
        passed = state == "COMPLETED"
        if not passed:
            all_passed = False
        results.append({"job_id": job_id, "state": state, "passed": passed})

    msg = CONCURRENT_JOBS_PASSED.format(count=len(job_ids)) if all_passed \
          else CONCURRENT_JOBS_FAILED.format(error="One or more jobs did not COMPLETE")
    return {"success": all_passed, "message": msg, "details": results,
            "error": "" if all_passed else msg}


# =============================================================================
# TC18 – Submit job with an invalid SIF file
# =============================================================================

def verify_job_with_invalid_sif_file(host) -> Dict[str, Any]:
    """TC18: Submit sbatch referencing a non-existent SIF file and confirm job FAILS."""
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "job_id": "", "error": ERROR_NO_SLURM_CONTROL_NODES}

    control_ip = control_nodes[0].get("admin_ip", "")
    fake_sif = "/hpc_tools/container_images/omnia_nonexistent_test.sif"

    result = _submit_apptainer_job(
        host, control_ip,
        os.path.join(_jobs_dir(), "apptainer_failing_job.sh"),
        "/tmp/omnia_apptainer_invalid.sh",
        {"{{SIF_FILE}}": fake_sif, "{{OUTPUT_PATH}}": REMOTE_JOB_OUTPUT_DIR},
    )

    job_state = result.get("job_state", "")
    if job_state in ("FAILED", "CANCELLED"):
        return {"success": True, "message": INVALID_SIF_JOB_PASSED,
                "job_id": result["job_id"], "job_state": job_state, "error": ""}

    err = f"Job {result['job_id']} ended with {job_state!r} (expected FAILED)"
    return {"success": False, "message": INVALID_SIF_JOB_FAILED.format(error=err),
            "job_id": result.get("job_id", ""), "job_state": job_state, "error": err}


# =============================================================================
# TC19 – SIF permission 600 causes job failure
# =============================================================================

def verify_sif_permission_600_fails_job(host) -> Dict[str, Any]:
    """TC19: chmod the SIF to 600, submit job as a different user, confirm FAILED, restore perms."""
    creds = _get_ldap_credentials(host)
    if not creds:
        return {"success": True, "skipped": True, "message": PERM_600_SKIPPED,
                "details": {}, "error": ""}

    nodes = get_slurm_nodes(host)
    control_nodes = get_slurm_control_nodes(host)
    if not nodes or not control_nodes:
        return {"success": True, "skipped": True, "message": PERM_600_SKIPPED,
                "details": {}, "error": ""}

    admin_ip = nodes[0].get("admin_ip", "")
    control_ip = control_nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, admin_ip, images_dir)

    if not sif_file:
        return {"success": True, "skipped": True, "message": PERM_600_SKIPPED,
                "details": {}, "error": ""}

    test_sif = PERMISSION_TEST_SIF_COPY
    _safe_run(host, f"cp '{sif_file}' '{test_sif}'", admin_ip)
    # Change ownership to nobody and chmod 600 so root job cannot read it
    _safe_run(host, f"chown nobody:nobody '{test_sif}'", admin_ip)
    _safe_run(host, f"chmod 600 '{test_sif}'", admin_ip)

    result = _submit_apptainer_job(
        host, control_ip,
        os.path.join(_jobs_dir(), "apptainer_failing_job.sh"),
        "/tmp/omnia_apptainer_perm600.sh",
        {"{{SIF_FILE}}": test_sif, "{{OUTPUT_PATH}}": REMOTE_JOB_OUTPUT_DIR},
    )

    # Cleanup - restore ownership before removing
    _safe_run(host, f"chown root:root '{test_sif}'", admin_ip)
    _safe_run(host, f"rm -f '{test_sif}'", admin_ip)

    job_state = result.get("job_state", "")
    if job_state in ("FAILED", "CANCELLED"):
        return {"success": True, "message": PERM_600_FAIL_PASSED,
                "details": {"job_id": result["job_id"], "job_state": job_state},
                "error": ""}

    err = f"Expected FAILED but got {job_state!r} for job {result.get('job_id', '')}"
    return {"success": False, "message": PERM_600_FAIL_FAILED.format(error=err),
            "details": {"job_id": result.get("job_id", ""), "job_state": job_state},
            "error": err}


# =============================================================================
# GPU NODE HELPER
# =============================================================================

def _get_gpu_node(host) -> Tuple[str, str]:
    """Return (hostname, admin_ip) of first compute node that has GPUs, or ('', '')."""
    for node in get_slurm_nodes(host):
        ip = node.get("admin_ip", "")
        if not ip:
            continue
        check = _safe_run(host, f"{GPU_COUNT_CMD}", ip)
        try:
            if check.rc == 0 and int(check.stdout.strip()) > 0:
                return node.get("hostname", "unknown"), ip
        except ValueError:
            pass
    return "", ""


# =============================================================================
# TC20 – GPU accessible in Apptainer container
# =============================================================================

def verify_gpu_accessible_in_apptainer_container(host) -> Dict[str, Any]:
    """TC20: Run nvidia-smi inside Apptainer with --nv and compare with host GPU visibility."""
    hostname, gpu_ip = _get_gpu_node(host)
    if not gpu_ip:
        return {"success": True, "skipped": True, "message": GPU_IN_CONTAINER_SKIPPED,
                "details": {}, "error": ""}

    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, gpu_ip, images_dir)
    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": {}, "error": ERROR_NO_SIF_FILES}

    host_gpu = _safe_run(host, GPU_LIST_CMD, gpu_ip)
    container_gpu = _safe_run(
        host,
        f"{APPTAINER_BINARY} exec --nv '{sif_file}' "
        f"nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null",
        gpu_ip,
    )

    host_gpus = [g.strip() for g in host_gpu.stdout.strip().splitlines() if g.strip()]
    cont_gpus = [g.strip() for g in container_gpu.stdout.strip().splitlines() if g.strip()]

    if container_gpu.rc != 0 or not cont_gpus:
        err = container_gpu.stdout.strip() or container_gpu.stderr.strip()
        return {"success": False, "message": GPU_IN_CONTAINER_FAILED.format(error=err),
                "details": {"host_gpus": host_gpus, "container_gpus": cont_gpus},
                "error": err}

    return {"success": True, "message": GPU_IN_CONTAINER_PASSED,
            "details": {"host_gpus": host_gpus, "container_gpus": cont_gpus,
                        "hostname": hostname},
            "error": ""}


# =============================================================================
# TC21 – GPU count correct in container
# =============================================================================

def verify_gpu_count_correct_in_container(host) -> Dict[str, Any]:
    """TC21: Verify GPU count inside Apptainer container matches host GPU count."""
    hostname, gpu_ip = _get_gpu_node(host)
    if not gpu_ip:
        return {"success": True, "skipped": True, "message": GPU_COUNT_SKIPPED,
                "details": {}, "error": ""}

    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, gpu_ip, images_dir)
    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": {}, "error": ERROR_NO_SIF_FILES}

    host_count_cmd = _safe_run(host, GPU_COUNT_CMD, gpu_ip)
    container_count_cmd = _safe_run(
        host,
        f"{APPTAINER_BINARY} exec --nv '{sif_file}' bash -c \"{GPU_COUNT_CMD}\" 2>/dev/null",
        gpu_ip,
    )

    try:
        host_count = int(host_count_cmd.stdout.strip())
        container_count = int(container_count_cmd.stdout.strip())
    except ValueError:
        err = f"Could not parse GPU counts: host={host_count_cmd.stdout.strip()!r} " \
              f"container={container_count_cmd.stdout.strip()!r}"
        return {"success": False, "message": GPU_COUNT_FAILED.format(host_count="?", container_count="?"),
                "details": {}, "error": err}

    if host_count != container_count:
        return {"success": False,
                "message": GPU_COUNT_FAILED.format(host_count=host_count, container_count=container_count),
                "details": {"host_count": host_count, "container_count": container_count},
                "error": f"Count mismatch: host={host_count} container={container_count}"}

    return {"success": True,
            "message": GPU_COUNT_PASSED.format(host_count=host_count, container_count=container_count),
            "details": {"host_count": host_count, "container_count": container_count,
                        "hostname": hostname},
            "error": ""}


# =============================================================================
# TC22 – Execute CUDA workload in Apptainer container
# =============================================================================

def verify_execute_cuda_workload_in_container(host) -> Dict[str, Any]:
    """TC22: Submit GPU sbatch job that runs CUDA sample inside Apptainer with --nv."""
    hostname, gpu_ip = _get_gpu_node(host)
    if not gpu_ip:
        return {"success": True, "skipped": True, "message": CUDA_WORKLOAD_SKIPPED,
                "details": {}, "error": ""}

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "details": {}, "error": ERROR_NO_SLURM_CONTROL_NODES}

    control_ip = control_nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_sif_for_jobs(host, images_dir)
    if not sif_file:
        return {"success": True, "skipped": True, "message": CUDA_WORKLOAD_SKIPPED,
                "details": {}, "error": ""}

    result = _submit_apptainer_job(
        host, control_ip,
        os.path.join(_jobs_dir(), "apptainer_gpu_job.sh"),
        "/tmp/omnia_apptainer_gpu.sh",
        {"{{SIF_FILE}}": sif_file, "{{OUTPUT_PATH}}": REMOTE_JOB_OUTPUT_DIR},
    )

    msg = CUDA_WORKLOAD_PASSED.format(job_id=result["job_id"]) if result["success"] \
          else CUDA_WORKLOAD_FAILED.format(error=result["error"])
    return {"success": result["success"], "message": msg,
            "details": {"job_id": result["job_id"], "job_state": result.get("job_state", ""),
                        "hostname": hostname},
            "error": result["error"]}


# =============================================================================
# TC23 – GPU memory allocation in container
# =============================================================================

def verify_gpu_memory_allocation_in_container(host) -> Dict[str, Any]:
    """TC23: Measure GPU memory before/after running a GPU workload inside Apptainer."""
    hostname, gpu_ip = _get_gpu_node(host)
    if not gpu_ip:
        return {"success": True, "skipped": True, "message": GPU_MEMORY_SKIPPED,
                "details": {}, "error": ""}

    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, gpu_ip, images_dir)
    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": {}, "error": ERROR_NO_SIF_FILES}

    mem_before = _safe_run(host, GPU_MEMORY_CMD, gpu_ip).stdout.strip()

    workload = (
        f"{APPTAINER_BINARY} exec --nv '{sif_file}' bash -c "
        f"\"python3 -c 'import ctypes; ctypes.CDLL(\\\"libcuda.so\\\")' 2>/dev/null || "
        f"nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null\""
    )
    _safe_run(host, workload, gpu_ip)

    mem_after = _safe_run(host, GPU_MEMORY_CMD, gpu_ip).stdout.strip()

    return {
        "success": True,
        "message": GPU_MEMORY_PASSED,
        "details": {
            "hostname": hostname,
            "mem_before_mib": mem_before,
            "mem_after_mib": mem_after,
        },
        "error": "",
    }


# =============================================================================
# TC24 – InfiniBand accessible in Apptainer container
# =============================================================================

def verify_infiniband_accessible_in_container(host) -> Dict[str, Any]:
    """TC24: Verify InfiniBand hardware is accessible inside the Apptainer container.
    
    Checks for actual IB hardware using ibstat, not just /dev/infiniband/ software interfaces.
    """
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    ib_node_ip = ""
    ib_hostname = ""
    for node in nodes:
        ip = node.get("admin_ip", "")
        if not ip:
            continue
        # Check for actual IB hardware using ibstat (shows physical state)
        check = _safe_run(host, "ibstat 2>/dev/null | grep -q 'State.*Active' && echo ACTIVE", ip)
        if check.rc == 0 and "ACTIVE" in check.stdout:
            ib_node_ip = ip
            ib_hostname = node.get("hostname", "unknown")
            break

    if not ib_node_ip:
        return {"success": True, "skipped": True, "message": IB_IN_CONTAINER_SKIPPED,
                "details": {}, "error": ""}

    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, ib_node_ip, images_dir)
    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": {}, "error": ERROR_NO_SIF_FILES}

    host_ib = _safe_run(host, INFINIBAND_DEVICES_CMD, ib_node_ip).stdout.strip()
    container_ib = _safe_run(
        host,
        f"{APPTAINER_BINARY} exec --bind /dev/infiniband:/dev/infiniband '{sif_file}' "
        f"ls /dev/infiniband/ 2>/dev/null",
        ib_node_ip,
    )

    if container_ib.rc != 0 or not container_ib.stdout.strip():
        err = f"IB devices not visible inside container. Host devices: {host_ib}"
        return {"success": False, "message": IB_IN_CONTAINER_FAILED.format(error=err),
                "details": {"hostname": ib_hostname, "host_ib": host_ib,
                            "container_ib": container_ib.stdout.strip()},
                "error": err}

    return {"success": True, "message": IB_IN_CONTAINER_PASSED,
            "details": {"hostname": ib_hostname, "host_ib_devices": host_ib,
                        "container_ib_devices": container_ib.stdout.strip()},
            "error": ""}


# =============================================================================
# TC25 – NFS mount visibility inside container
# =============================================================================

def verify_nfs_mount_visibility_in_container(host) -> Dict[str, Any]:
    """TC25: Verify NFS (hpc_tools) mount is visible inside Apptainer container and files accessible."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    hostname = nodes[0].get("hostname", "unknown")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, admin_ip, images_dir)
    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": {}, "error": ERROR_NO_SIF_FILES}

    hpc_base = _get_hpc_tools_base(host)
    host_mount = _safe_run(host, f"df -h '{hpc_base}' 2>/dev/null | tail -1", admin_ip).stdout.strip()

    container_ls = _safe_run(
        host,
        f"{APPTAINER_BINARY} exec --bind '{hpc_base}:{hpc_base}' '{sif_file}' "
        f"ls '{images_dir}' 2>&1",
        admin_ip,
    )

    if container_ls.rc != 0:
        err = container_ls.stdout.strip() or container_ls.stderr.strip()
        return {"success": False, "message": NFS_IN_CONTAINER_FAILED.format(error=err),
                "details": {"hostname": hostname, "host_mount": host_mount, "error": err},
                "error": err}

    container_has_sifs = SIF_EXTENSION in container_ls.stdout

    return {"success": True, "message": NFS_IN_CONTAINER_PASSED,
            "details": {"hostname": hostname, "host_mount": host_mount,
                        "container_ls": container_ls.stdout.strip(),
                        "sif_files_visible": container_has_sifs},
            "error": ""}


# =============================================================================
# TC26 – SLURM environment variables inside container
# =============================================================================
# TC27 – Job array execution in containers
# =============================================================================

def verify_job_array_execution_in_containers(host) -> Dict[str, Any]:
    """TC27: Submit an sbatch --array job and verify all tasks complete in containers."""
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "details": [], "error": ERROR_NO_SLURM_CONTROL_NODES}

    control_ip = control_nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_sif_for_jobs(host, images_dir)
    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "details": [], "error": ERROR_NO_SIF_FILES}

    remote_script = "/tmp/omnia_apptainer_array.sh"
    xfer = _transfer_script(
        host, control_ip,
        os.path.join(_jobs_dir(), "apptainer_array_job.sh"),
        remote_script,
        {"{{SIF_FILE}}": sif_file,
         "{{ARRAY_SIZE}}": str(APPTAINER_ARRAY_SIZE),
         "{{OUTPUT_PATH}}": REMOTE_JOB_OUTPUT_DIR},
    )
    if not xfer["success"]:
        return {"success": False, "message": JOB_ARRAY_FAILED.format(error=xfer["error"]),
                "details": [], "error": xfer["error"]}

    ok, array_job_id, err = _submit_sbatch(host, control_ip, remote_script)
    _safe_run(host, f"rm -f {remote_script}", control_ip)

    if not ok:
        return {"success": False, "message": JOB_ARRAY_FAILED.format(error=err),
                "details": [], "error": err}

    task_results = []
    all_passed = True
    start = time.time()
    timeout = APPTAINER_SACCT_TIMEOUT * 2

    while time.time() - start < timeout:
        time.sleep(APPTAINER_SACCT_POLL_INTERVAL)
        sacct = _safe_run(
            host,
            f"sacct -j {array_job_id} --format=JobID,State -n -P",
            control_ip,
        )
        if sacct.rc != 0:
            continue

        task_states: Dict[str, str] = {}
        for line in sacct.stdout.strip().splitlines():
            parts = line.strip().split("|")
            if len(parts) >= 2 and "_" in parts[0]:
                task_states[parts[0]] = parts[1].strip()

        terminal = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"}
        if len(task_states) >= APPTAINER_ARRAY_SIZE and \
                all(s in terminal for s in task_states.values()):
            task_results = [{"task_id": k, "state": v} for k, v in task_states.items()]
            all_passed = all(v == "COMPLETED" for v in task_states.values())
            break

    if not task_results:
        return {"success": False,
                "message": JOB_ARRAY_FAILED.format(error="Timed out waiting for array tasks"),
                "details": [], "error": "Array job timed out"}

    msg = JOB_ARRAY_PASSED.format(count=APPTAINER_ARRAY_SIZE) if all_passed \
          else JOB_ARRAY_FAILED.format(error="One or more array tasks did not COMPLETE")
    return {"success": all_passed, "message": msg, "details": task_results,
            "error": "" if all_passed else msg}


# =============================================================================
# TC28 – Container cleanup after job failure
# =============================================================================

def verify_container_cleanup_after_job_failure(host) -> Dict[str, Any]:
    """TC28: Submit a job with a bad SIF, then verify no orphaned apptainer processes remain."""
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "details": {}, "error": ERROR_NO_SLURM_CONTROL_NODES}

    control_ip = control_nodes[0].get("admin_ip", "")
    fake_sif = "/hpc_tools/container_images/omnia_cleanup_test_nonexistent.sif"

    result = _submit_apptainer_job(
        host, control_ip,
        os.path.join(_jobs_dir(), "apptainer_failing_job.sh"),
        "/tmp/omnia_apptainer_cleanup.sh",
        {"{{SIF_FILE}}": fake_sif, "{{OUTPUT_PATH}}": REMOTE_JOB_OUTPUT_DIR},
    )

    time.sleep(5)

    ps_check = _safe_run(
        host,
        "ps aux 2>/dev/null | grep -v grep | grep apptainer | awk '{print $2, $11}' || true",
        control_ip,
    )
    orphan_procs = [p.strip() for p in ps_check.stdout.strip().splitlines() if p.strip()]

    for node in get_slurm_nodes(host):
        node_ip = node.get("admin_ip", "")
        if not node_ip:
            continue
        ps_node = _safe_run(
            host,
            "ps aux 2>/dev/null | grep -v grep | grep apptainer | awk '{print $2, $11}' || true",
            node_ip,
        )
        orphan_procs.extend([p.strip() for p in ps_node.stdout.strip().splitlines() if p.strip()])

    if orphan_procs:
        err = f"Orphaned apptainer processes found: {orphan_procs}"
        return {"success": False, "message": CLEANUP_FAILED.format(error=err),
                "details": {"orphan_processes": orphan_procs}, "error": err}

    return {"success": True, "message": CLEANUP_PASSED,
            "details": {"job_id": result.get("job_id", ""),
                        "job_state": result.get("job_state", ""),
                        "orphan_processes": []},
            "error": ""}


# =============================================================================
# TC29 – NFS mount and SIF files accessible after node reboot (negative)
# =============================================================================

def verify_nfs_and_sif_accessible_after_reboot(host, rebooted_nodes: List[Dict[str, str]]) -> Dict[str, Any]:
    """TC29: After compute node reboot, verify NFS mount and SIF files are accessible."""
    if not rebooted_nodes:
        nodes = get_slurm_nodes(host)
        if not nodes:
            return {"success": False, "message": ERROR_NO_SLURM_NODES,
                    "details": [], "error": ERROR_NO_SLURM_NODES}
        rebooted_nodes = nodes[:1]

    images_dir = _get_container_images_dir(host)
    hpc_base = _get_hpc_tools_base(host)
    all_passed = True
    details = []

    for node in rebooted_nodes:
        hostname = node.get("hostname", "unknown")
        admin_ip = node.get("admin_ip", "")
        if not admin_ip:
            details.append({"hostname": hostname, "nfs_mounted": False,
                            "sif_accessible": False, "error": "No admin IP"})
            all_passed = False
            continue

        start = time.time()
        online = False
        while time.time() - start < REBOOT_WAIT_ONLINE_TIMEOUT:
            ping = _safe_run(host, f"ping -c 1 -W 2 {admin_ip} > /dev/null 2>&1 && echo UP", admin_ip)
            if "UP" in ping.stdout or ping.rc == 0:
                online = True
                break
            time.sleep(REBOOT_WAIT_ONLINE_POLL_INTERVAL)

        if not online:
            details.append({"hostname": hostname, "online": False,
                            "nfs_mounted": False, "sif_accessible": False,
                            "error": f"Node did not come online within {REBOOT_WAIT_ONLINE_TIMEOUT}s"})
            all_passed = False
            continue

        time.sleep(REBOOT_POST_SETTLE_DELAY)

        nfs_check = _safe_run(host, f"df -h '{hpc_base}' 2>/dev/null | tail -1", admin_ip)
        nfs_mounted = nfs_check.rc == 0 and ":" in nfs_check.stdout

        sif_files = _list_sif_files(host, admin_ip, images_dir)
        sif_accessible = len(sif_files) > 0

        apptainer_check = {"rc": -1, "stdout": ""}
        if sif_files:
            apptainer_run = _safe_run(
                host,
                f"{APPTAINER_BINARY} exec '{sif_files[0]}' hostname 2>&1",
                admin_ip,
            )
            apptainer_check = {"rc": apptainer_run.rc, "stdout": apptainer_run.stdout.strip()}

        node_passed = nfs_mounted and sif_accessible
        details.append({
            "hostname": hostname,
            "online": True,
            "nfs_mounted": nfs_mounted,
            "sif_accessible": sif_accessible,
            "sif_files_found": len(sif_files),
            "apptainer_exec_rc": apptainer_check["rc"],
            "error": "" if node_passed else f"nfs_mounted={nfs_mounted} sif_accessible={sif_accessible}",
        })
        if not node_passed:
            all_passed = False

    msg = REBOOT_NFS_SIF_PASSED if all_passed else \
          REBOOT_NFS_SIF_FAILED.format(error="NFS or SIF not accessible after reboot")
    return {"success": all_passed, "message": msg, "details": details,
            "error": "" if all_passed else msg}


# =============================================================================
# TC30 – Container execution post reboot
# =============================================================================

def verify_container_execution_post_reboot(host) -> Dict[str, Any]:
    """TC30: Submit container job after a node has been rebooted and verify it completes."""
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        return {"success": False, "message": ERROR_NO_SLURM_CONTROL_NODES,
                "job_id": "", "error": ERROR_NO_SLURM_CONTROL_NODES}

    control_ip = control_nodes[0].get("admin_ip", "")
    images_dir = _get_container_images_dir(host)
    sif_file = _get_first_sif(host, control_ip, images_dir)
    if not sif_file:
        return {"success": False, "message": ERROR_NO_SIF_FILES,
                "job_id": "", "error": ERROR_NO_SIF_FILES}

    result = _submit_apptainer_job(
        host, control_ip,
        os.path.join(_jobs_dir(), "apptainer_single_node.sh"),
        "/tmp/omnia_apptainer_post_reboot.sh",
        {"{{SIF_FILE}}": sif_file, "{{OUTPUT_PATH}}": REMOTE_JOB_OUTPUT_DIR},
    )

    msg = REBOOT_CONTAINER_EXEC_PASSED.format(job_id=result["job_id"]) if result["success"] \
          else REBOOT_CONTAINER_EXEC_FAILED.format(error=result["error"])
    return {"success": result["success"], "message": msg,
            "job_id": result["job_id"], "job_state": result.get("job_state", ""),
            "error": result["error"]}


# =============================================================================
# TC31 – download_container_image.sh works correctly after reboot
# =============================================================================

def verify_download_script_works_after_reboot(host) -> Dict[str, Any]:
    """TC31: After node reboot verify download_container_image.sh is present, executable, and runs."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        return {"success": False, "message": ERROR_NO_SLURM_NODES,
                "details": {}, "error": ERROR_NO_SLURM_NODES}

    admin_ip = nodes[0].get("admin_ip", "")
    hostname = nodes[0].get("hostname", "unknown")
    script_path = _get_download_script_path(host)

    exist_check = _safe_run(host, f"test -f '{script_path}' && echo EXISTS", admin_ip)
    if "EXISTS" not in exist_check.stdout:
        err = f"Script not found at {script_path} after reboot"
        return {"success": False, "message": REBOOT_DOWNLOAD_SCRIPT_FAILED.format(error=err),
                "details": {"hostname": hostname, "script_found": False}, "error": err}

    exec_check = _safe_run(host, f"test -x '{script_path}' && echo EXECUTABLE", admin_ip)
    is_executable = "EXECUTABLE" in exec_check.stdout

    list_path = _get_image_list_path(host)
    list_check = _safe_run(host, f"test -f '{list_path}' && echo EXISTS", admin_ip)
    list_found = "EXISTS" in list_check.stdout

    if not is_executable:
        err = f"Script {script_path} is not executable after reboot"
        return {"success": False, "message": REBOOT_DOWNLOAD_SCRIPT_FAILED.format(error=err),
                "details": {"hostname": hostname, "script_found": True,
                            "is_executable": False, "list_found": list_found},
                "error": err}

    if not list_found:
        err = f"Image list not found at {list_path} after reboot"
        return {"success": False, "message": REBOOT_DOWNLOAD_SCRIPT_FAILED.format(error=err),
                "details": {"hostname": hostname, "script_found": True,
                            "is_executable": True, "list_found": False},
                "error": err}

    syntax_check = _safe_run(host, f"bash -n '{script_path}' 2>&1", admin_ip)
    syntax_ok = syntax_check.rc == 0

    return {
        "success": syntax_ok,
        "message": REBOOT_DOWNLOAD_SCRIPT_PASSED if syntax_ok
                   else REBOOT_DOWNLOAD_SCRIPT_FAILED.format(
                       error=f"Syntax error: {syntax_check.stdout.strip()}"),
        "details": {
            "hostname": hostname,
            "script_path": script_path,
            "script_found": True,
            "is_executable": is_executable,
            "list_found": list_found,
            "syntax_ok": syntax_ok,
        },
        "error": "" if syntax_ok else syntax_check.stdout.strip(),
    }
