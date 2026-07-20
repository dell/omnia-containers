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
Slurm Upgrade Module - Functions.

Verification functions for post-upgrade Slurm cluster state.
Maps directly to the checks performed by the ``upgrade_slurm`` Ansible role:

  - NFS mount verification (nfs_client.yml)
  - Slurm config and MySQL backup verification (slurm_backup.yml)
  - Cluster health: no running jobs, all nodes idle (check_slurm_cluster.yml)
  - Service availability: slurmctld, slurmd, munge
  - Job execution: sbatch and srun post-upgrade

All functions accept a testinfra ``host`` object (connected to OIM)
and return a dict with at least ``success`` (bool) and ``message`` (str).
"""

import re
import time
from typing import Dict, Any, List

from automation_library.core import (
    run_in_container,
    run_on_remote_node,
    get_nodes_info,
    get_functional_groups_from_pxe_mapping,
    load_container_file,
)
from automation_library.local_repo.functions.local_repo_func import read_file_in_omnia_core
from automation_library.powervault.functions.powervault_func import read_storage_config
from automation_library.upgrade_and_rollback.vars.slurm_upgrade_vars import (
    OIM_METADATA_PATH,
    INPUT_PROJECT_DIR,
    OMNIA_CONFIG_FILE,
    STORAGE_CONFIG_FILE,
    SLURM_CONTROL_NODE_FG,
    SLURM_NODE_FG,
    SLURM_CONF_RELATIVE_PATH,
    MYSQL_DATADIR_RELATIVE,
    MYSQL_IBDATA_FILE,
    MYSQL_SYSTEM_DB,
    HPC_TOOLS_TRACKING_FILES,
    SLURMCTLD_SERVICE,
    SLURMD_SERVICE,
    MUNGE_SERVICE,
    SQUEUE_RETRIES,
    SQUEUE_RETRY_DELAY,
    SINFO_RETRIES,
    SINFO_RETRY_DELAY,
    SBATCH_JOB_TIMEOUT,
    SBATCH_POLL_INTERVAL,
    UPGRADE_MANIFEST_PATH,
    UPGRADE_PLAYBOOK_DIR,
    UPGRADE_PLAYBOOK_CMD,
    SLURM_UPGRADE_TIMEOUT,
    SLURM_UPGRADE_POLL_INTERVAL,
)
from automation_library.upgrade_and_rollback.messages.slurm_upgrade_msgs import (
    SLURM_UPGRADE_LOG_MSGS as LOG,
)


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

class _FakeResult:
    """Minimal stand-in for a testinfra CommandResult on SSH failure."""
    def __init__(self, rc, stdout, stderr):
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr


def _safe_run_on_remote(host, cmd: str, admin_ip: str):
    """Wrapper around run_on_remote_node that catches RuntimeError."""
    try:
        return run_on_remote_node(host, cmd, admin_ip)
    except RuntimeError as exc:
        return _FakeResult(
            rc=255,
            stdout="",
            stderr=f"SSH connection failed to {admin_ip}: {exc}",
        )


def _get_nodes_for_group(host, group_keyword: str) -> List[Dict[str, str]]:
    """Get all nodes whose functional_group contains the given keyword."""
    all_groups = get_functional_groups_from_pxe_mapping(host)
    nodes = []
    for fg in all_groups:
        if group_keyword in fg:
            fg_nodes = get_nodes_info(
                host, search_by="functional_group", search_value=fg,
            )
            nodes.extend(fg_nodes)
    return nodes


def _get_slurm_control_nodes(host) -> List[Dict[str, str]]:
    """Get all slurm control nodes from PXE mapping."""
    return _get_nodes_for_group(host, SLURM_CONTROL_NODE_FG)


def _get_slurm_compute_nodes(host) -> List[Dict[str, str]]:
    """Get all slurm compute nodes from PXE mapping."""
    return _get_nodes_for_group(host, SLURM_NODE_FG)


def _read_yaml_field(host, file_path: str, field: str) -> str:
    """Read a simple top-level YAML field from a file inside omnia_core."""
    result = run_in_container(host, f"cat {file_path}")
    if result.rc != 0:
        return ""
    pattern = rf'^\s*{re.escape(field)}\s*:\s*["\']?([^"\'#\n]+)["\']?'
    match = re.search(pattern, result.stdout, re.MULTILINE)
    return match.group(1).strip() if match else ""


# =============================================================================
# TC: UPGRADE GATE — CHECK METADATA + MANIFEST
# =============================================================================

def check_slurm_upgrade_state(host) -> Dict[str, Any]:
    """Check whether a Slurm upgrade is needed, completed, or skipped.

    1. Reads ``oim_metadata.yml`` → ``previous_omnia_version`` must exist
       (indicates an upgrade has occurred on the OIM).
    2. Reads ``upgrade_manifest.yml`` → ``component_status.slurm``:
       - ``completed``    → tests should proceed with verification
       - ``skipped``      → tests should be skipped
       - ``pending`` / ``in-progress`` → upgrade not yet done, needs trigger
       - manifest missing → upgrade not initiated, skip

    Returns:
        Dict with:
          - success (bool): True if gate check itself succeeded
          - is_upgrade (bool): True if OIM has previous_omnia_version set
          - slurm_status (str): component_status.slurm from manifest
          - needs_upgrade (bool): True if slurm upgrade should be triggered
          - should_skip (bool): True if all slurm tests should be skipped
          - omnia_version (str): current version
          - previous_version (str): previous version
          - message (str)
          - error (str)
    """
    result = {
        "success": False,
        "is_upgrade": False,
        "slurm_status": "",
        "needs_upgrade": False,
        "should_skip": True,
        "omnia_version": "",
        "previous_version": "",
        "message": "",
        "error": "",
    }

    # Step 1: Read oim_metadata.yml
    metadata = load_container_file(host, OIM_METADATA_PATH)
    if not metadata:
        result["error"] = f"Cannot read {OIM_METADATA_PATH}"
        result["message"] = LOG["metadata_read_failed"].format(
            error=result["error"],
        )
        return result

    omnia_version = metadata.get("omnia_version", "")
    previous_version = metadata.get("previous_omnia_version", "")
    result["omnia_version"] = omnia_version
    result["previous_version"] = previous_version

    if not previous_version:
        result["success"] = True
        result["is_upgrade"] = False
        result["should_skip"] = True
        result["message"] = LOG["metadata_no_upgrade"]
        return result

    result["is_upgrade"] = True

    # Step 2: Read upgrade_manifest.yml
    manifest = load_container_file(host, UPGRADE_MANIFEST_PATH)
    if not manifest:
        result["success"] = True
        result["should_skip"] = True
        result["message"] = LOG["manifest_not_found"]
        return result

    component_status = manifest.get("component_status", {})
    slurm_status = component_status.get("slurm", "pending")
    result["slurm_status"] = slurm_status

    if slurm_status == "completed":
        result["success"] = True
        result["should_skip"] = False
        result["needs_upgrade"] = False
        result["message"] = LOG["manifest_slurm_status"].format(
            status=slurm_status,
        )
    elif slurm_status == "skipped":
        result["success"] = True
        result["should_skip"] = True
        result["needs_upgrade"] = False
        result["message"] = LOG["manifest_slurm_status"].format(
            status=slurm_status,
        )
    else:
        # pending or in-progress → needs upgrade trigger
        result["success"] = True
        result["should_skip"] = False
        result["needs_upgrade"] = True
        result["message"] = LOG["manifest_slurm_status"].format(
            status=slurm_status,
        )

    return result


# =============================================================================
# TC: RUN SLURM UPGRADE PLAYBOOK
# =============================================================================

def run_slurm_upgrade(host, progress_callback=None) -> Dict[str, Any]:
    """Trigger the Slurm upgrade by running ``upgrade.yml --tags slurm``.

    Runs the playbook inside the omnia_core container in the background,
    polls for completion, and returns the result.

    Args:
        host: Testinfra host object (connected to OIM)
        progress_callback: Optional callable(elapsed: int) for progress output

    Returns:
        Dict with success, rc, output, error.
    """
    timeout = SLURM_UPGRADE_TIMEOUT
    poll_interval = SLURM_UPGRADE_POLL_INTERVAL

    log_file = "/tmp/slurm_upgrade_run.log"
    pid_file = "/tmp/slurm_upgrade_run.pid"
    rc_file = "/tmp/slurm_upgrade_run.rc"
    wrapper = "/tmp/slurm_upgrade_run.sh"

    # Write wrapper script inside the container
    run_in_container(
        host,
        f"cat > {wrapper} << 'SLURMEOF'\n"
        f"#!/bin/bash\n"
        f"cd {UPGRADE_PLAYBOOK_DIR}\n"
        f"{UPGRADE_PLAYBOOK_CMD}\n"
        f"echo $? > {rc_file}\n"
        f"SLURMEOF\n"
        f"chmod +x {wrapper}",
    )

    # Run wrapper in background inside the container
    run_in_container(
        host,
        f"nohup {wrapper} > {log_file} 2>&1 & echo $! > {pid_file}",
    )

    pid_cmd = run_in_container(host, f"cat {pid_file}")
    pid = pid_cmd.stdout.strip()

    elapsed = 0
    while elapsed < timeout:
        time.sleep(min(poll_interval, timeout - elapsed))
        elapsed += poll_interval

        alive = run_in_container(
            host, f"kill -0 {pid} 2>/dev/null; echo $?",
        )
        still_running = alive.stdout.strip() == "0"

        if progress_callback:
            progress_callback(elapsed)

        if not still_running:
            break

    if elapsed >= timeout:
        run_in_container(host, f"kill -9 {pid} 2>/dev/null || true")

    # Read exit code
    rc_cmd = run_in_container(host, f"cat {rc_file} 2>/dev/null || echo 1")
    rc_str = rc_cmd.stdout.strip().split("\n")[-1]
    try:
        rc = int(rc_str)
    except ValueError:
        rc = 1

    # Get last 50 lines of output
    log_cmd = run_in_container(host, f"tail -50 {log_file} 2>/dev/null")
    output = log_cmd.stdout.strip() if log_cmd.rc == 0 else ""

    # Clean up
    run_in_container(
        host, f"rm -f {log_file} {pid_file} {rc_file} {wrapper}",
    )

    if rc != 0 and elapsed >= timeout:
        return {
            "success": False,
            "rc": rc,
            "output": output,
            "error": LOG["upgrade_timeout"].format(timeout=timeout),
        }

    if rc != 0:
        return {
            "success": False,
            "rc": rc,
            "output": output,
            "error": LOG["upgrade_failed"].format(rc=rc),
        }

    return {
        "success": True,
        "rc": rc,
        "output": output,
        "error": "",
    }


# =============================================================================
# TC: VERIFY SLURM NFS MOUNT
# =============================================================================

def verify_slurm_nfs_mount(host) -> Dict[str, Any]:
    """Verify the Slurm NFS share is mounted on OIM.

    Reads omnia_config.yml → slurm_cluster[].nfs_storage_name,
    then storage_config.yml → mounts[] to find the mount_point,
    and checks it is actually mounted.

    Returns:
        Dict with success, message, mount_point, source, error.
    """
    result = {"success": False, 
        "message": "",
        "mount_point": "",
        "source": "",
        "error": ""
    }
    slurm_mount_name = None

    read_omnia_config = load_container_file(host, f"{INPUT_PROJECT_DIR}/{OMNIA_CONFIG_FILE}")
    if not read_omnia_config:
        result["message"] = LOG["nfs_config_error"].format(
                error="Cannot read omnia_config.yml",
            )
        result["success"] = False
        return result
    slurm_cluster = read_omnia_config.get("slurm_cluster")
    if not slurm_cluster or not isinstance(slurm_cluster, list):
        result["message"] = LOG["nfs_config_error"].format(
                error="Cannot read slurm_cluster from omnia_config.yml",
            )
        result["success"] = False
        return result
    slurm_mount_name = slurm_cluster[0].get("nfs_storage_name")
    if not slurm_mount_name:
        result["message"] = LOG["nfs_config_error"].format(
                error="Cannot read nfs_storage_name from omnia_config.yml",
            )
        result["success"] = False
        return result

    read_storage_cfg = load_container_file(host, f"{INPUT_PROJECT_DIR}/{STORAGE_CONFIG_FILE}")
    if not read_storage_cfg:
        result["success"] = False
        result["message"] = LOG["nfs_config_error"].format(error="Cannot read storage_config.yml")
        return result
    storage_config = read_storage_cfg.get("mounts")
    if not storage_config or not isinstance(storage_config, list):
        result["message"] = LOG["nfs_config_error"].format(
                error="Cannot read mounts from storage_config.yml",
            )
        result["success"] = False
        return result
    slurm_mount = next((m for m in storage_config if m.get("name") == slurm_mount_name), None)
    if not slurm_mount:
        result["message"] = LOG["nfs_config_error"].format(
                error=f"Cannot find mount '{slurm_mount_name}' in storage_config.yml",
            )
        result["success"] = False
        return result
        
    mount_check = host.run(f"findmnt -rn -o TARGET {slurm_mount["mount_point"]}")
    if (mount_check.rc != 0):
        result["message"] = LOG["nfs_config_error"].format(
                error=f"'{slurm_mount_name}' with mount point {slurm_mount["mount_point"]} not mounted on OIM",
            )
        result["success"] = False
        return result

    result["success"] = True
    result["message"] = "Slurm mount is successfully mounted on OIM"
    result["mount_point"] = slurm_mount["mount_point"]
    return result


# =============================================================================
# TC: VERIFY SLURM.CONF BACKUP IN NFS
# =============================================================================

def verify_slurm_conf_backup(host, mount_point: str) -> Dict[str, Any]:
    """Verify slurm.conf exists in the control node's NFS backup directory.

    Reads pxe_mapping_file to find the slurm_control_node_x86_64 hostname,
    then checks {mount_point}/slurm/{hostname}/etc/slurm/slurm.conf.

    Args:
        host: Testinfra host object
        mount_point: NFS mount point path

    Returns:
        Dict with success, message, path, ctld_hostname, error.
    """
    slurm_nfs = f"{mount_point}/slurm"

    # Find control node hostname from PXE mapping
    control_nodes = _get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": LOG["no_control_node"],
            "path": "",
            "ctld_hostname": "",
            "error": "No slurm control node found in PXE mapping",
        }

    ctld_hostname = control_nodes[0].get("hostname", "")
    ctld_dir = f"{slurm_nfs}/{ctld_hostname}"
    conf_path = f"{ctld_dir}/{SLURM_CONF_RELATIVE_PATH}"

    # Check ctld directory exists
    dir_check = host.run(f"test -d {ctld_dir}")
    if dir_check.rc != 0:
        return {
            "success": False,
            "message": LOG["slurm_conf_missing"].format(path=conf_path),
            "path": conf_path,
            "ctld_hostname": ctld_hostname,
            "error": f"Control node directory not found: {ctld_dir}",
        }

    # Check slurm.conf exists
    conf_check = host.run(f"test -f {conf_path}")
    if conf_check.rc != 0:
        return {
            "success": False,
            "message": LOG["slurm_conf_missing"].format(path=conf_path),
            "path": conf_path,
            "ctld_hostname": ctld_hostname,
            "error": f"slurm.conf not found at {conf_path}",
        }

    return {
        "success": True,
        "message": LOG["slurm_conf_found"].format(path=conf_path),
        "path": conf_path,
        "ctld_hostname": ctld_hostname,
        "error": "",
    }


# =============================================================================
# TC: VERIFY MYSQL DATADIR BACKUP IN NFS
# =============================================================================

def verify_mysql_datadir_backup(host, mount_point: str) -> Dict[str, Any]:
    """Verify MySQL datadir exists in the control node's NFS backup.

    Checks for ibdata1 OR mysql/ system database directory.

    Args:
        host: Testinfra host object
        mount_point: NFS mount point path

    Returns:
        Dict with success, message, path, ibdata_exists, mysql_db_exists, error.
    """
    slurm_nfs = f"{mount_point}/slurm"

    control_nodes = _get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": LOG["no_control_node"],
            "path": "",
            "ibdata_exists": False,
            "mysql_db_exists": False,
            "error": "No slurm control node found in PXE mapping",
        }

    ctld_hostname = control_nodes[0].get("hostname", "")
    mysql_dir = f"{slurm_nfs}/{ctld_hostname}/{MYSQL_DATADIR_RELATIVE}"

    ibdata_check = host.run(f"test -f {mysql_dir}/{MYSQL_IBDATA_FILE}")
    mysql_db_check = host.run(f"test -d {mysql_dir}/{MYSQL_SYSTEM_DB}")

    ibdata_exists = ibdata_check.rc == 0
    mysql_db_exists = mysql_db_check.rc == 0

    if ibdata_exists or mysql_db_exists:
        return {
            "success": True,
            "message": LOG["mysql_found"].format(
                ibdata=ibdata_exists, mysql_db=mysql_db_exists,
            ),
            "path": mysql_dir,
            "ibdata_exists": ibdata_exists,
            "mysql_db_exists": mysql_db_exists,
            "error": "",
        }

    return {
        "success": False,
        "message": LOG["mysql_missing"].format(path=mysql_dir),
        "path": mysql_dir,
        "ibdata_exists": False,
        "mysql_db_exists": False,
        "error": f"Neither ibdata1 nor mysql/ found in {mysql_dir}",
    }


# =============================================================================
# TC: VERIFY HPC TOOLS TRACKING FILES CLEANED
# =============================================================================

def verify_hpc_tracking_cleanup(host, mount_point: str) -> Dict[str, Any]:
    """Verify HPC tools tracking files were removed during upgrade.

    Args:
        host: Testinfra host object
        mount_point: NFS mount point path (e.g. /mnt/slurm_nfs)

    Returns:
        Dict with success, message, remaining_files, error.
    """
    slurm_nfs = f"{mount_point}/slurm"
    remaining = []

    for track_file in HPC_TOOLS_TRACKING_FILES:
        full_path = f"{slurm_nfs}{track_file}"
        check = host.run(f"test -e {full_path}")
        if check.rc == 0:
            remaining.append(full_path)

    if remaining:
        return {
            "success": False,
            "message": LOG["hpc_tracking_present"].format(
                path=", ".join(remaining),
            ),
            "remaining_files": remaining,
            "error": f"Tracking files still present: {', '.join(remaining)}",
        }

    return {
        "success": True,
        "message": LOG["hpc_tracking_clean"],
        "remaining_files": [],
        "error": "",
    }


# =============================================================================
# TC: VERIFY NO RUNNING JOBS
# =============================================================================

def verify_no_running_jobs(host) -> Dict[str, Any]:
    """Verify no active jobs are running on the Slurm cluster.

    Runs ``squeue -h | wc -l`` on the slurm control node.

    Returns:
        Dict with success, message, job_count, error.
    """
    control_nodes = _get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": LOG["no_control_node"],
            "job_count": -1,
            "error": "No slurm control node found in PXE mapping",
        }

    control_ip = control_nodes[0].get("admin_ip", "")
    cmd = "squeue -h | wc -l"

    # Retry logic matching the Ansible role
    last_result = None
    for _attempt in range(SQUEUE_RETRIES):
        result = _safe_run_on_remote(host, cmd, control_ip)
        last_result = result
        if result.rc == 0:
            break
        time.sleep(SQUEUE_RETRY_DELAY)

    if last_result.rc != 0:
        return {
            "success": False,
            "message": LOG["squeue_failed"].format(
                error=last_result.stderr.strip(),
            ),
            "job_count": -1,
            "error": f"squeue failed (rc={last_result.rc}): {last_result.stderr.strip()}",
        }

    try:
        job_count = int(last_result.stdout.strip())
    except ValueError:
        return {
            "success": False,
            "message": LOG["squeue_failed"].format(
                error=f"Invalid output: {last_result.stdout.strip()}",
            ),
            "job_count": -1,
            "error": f"Could not parse squeue output: {last_result.stdout.strip()}",
        }

    if job_count > 0:
        return {
            "success": False,
            "message": LOG["jobs_found"].format(count=job_count),
            "job_count": job_count,
            "error": f"{job_count} running job(s) detected",
        }

    return {
        "success": True,
        "message": LOG["no_jobs_found"],
        "job_count": 0,
        "error": "",
    }


# =============================================================================
# TC: VERIFY ALL COMPUTE NODES IDLE
# =============================================================================

def verify_all_nodes_idle(host) -> Dict[str, Any]:
    """Verify all Slurm compute nodes are in idle state.

    Queries sinfo on the control node and compares against PXE mapping.

    Returns:
        Dict with success, message, idle_nodes, non_idle_nodes, details, error.
    """
    control_nodes = _get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": LOG["no_control_node"],
            "idle_nodes": [],
            "non_idle_nodes": [],
            "details": [],
            "error": "No slurm control node found",
        }

    compute_nodes = _get_slurm_compute_nodes(host)
    if not compute_nodes:
        return {
            "success": False,
            "message": LOG["no_compute_nodes"],
            "idle_nodes": [],
            "non_idle_nodes": [],
            "details": [],
            "error": "No slurm compute nodes found",
        }

    control_ip = control_nodes[0].get("admin_ip", "")
    cmd = 'sinfo -h -N -o "%n %t"'

    last_result = None
    for _attempt in range(SINFO_RETRIES):
        result = _safe_run_on_remote(host, cmd, control_ip)
        last_result = result
        if result.rc == 0:
            break
        time.sleep(SINFO_RETRY_DELAY)

    if last_result.rc != 0:
        return {
            "success": False,
            "message": LOG["sinfo_failed"].format(
                error=last_result.stderr.strip(),
            ),
            "idle_nodes": [],
            "non_idle_nodes": [],
            "details": [],
            "error": f"sinfo failed (rc={last_result.rc}): {last_result.stderr.strip()}",
        }

    # Parse sinfo output: "hostname state"
    idle_set = set()
    node_states = {}
    for line in last_result.stdout.strip().split("\n"):
        parts = line.strip().split()
        if len(parts) >= 2:
            node_states[parts[0]] = parts[1]
            if parts[1] == "idle":
                idle_set.add(parts[0])

    compute_hostnames = [n.get("hostname", "") for n in compute_nodes]
    non_idle = [h for h in compute_hostnames if h not in idle_set]
    idle = [h for h in compute_hostnames if h in idle_set]

    details = []
    for h in compute_hostnames:
        details.append({
            "hostname": h,
            "state": node_states.get(h, "unknown"),
            "idle": h in idle_set,
        })

    if non_idle:
        return {
            "success": False,
            "message": LOG["non_idle_found"].format(
                count=len(non_idle), nodes=", ".join(non_idle),
            ),
            "idle_nodes": idle,
            "non_idle_nodes": non_idle,
            "details": details,
            "error": f"{len(non_idle)} compute node(s) not idle",
        }

    return {
        "success": True,
        "message": LOG["all_idle"].format(count=len(idle)),
        "idle_nodes": idle,
        "non_idle_nodes": [],
        "details": details,
        "error": "",
    }


# =============================================================================
# TC: VERIFY SERVICES ACTIVE POST-UPGRADE
# =============================================================================

def _check_service_on_nodes(
    host, nodes: List[Dict[str, str]], service: str,
) -> Dict[str, Any]:
    """Check a systemd service on multiple remote nodes.

    Returns:
        Dict with success, message, details (list of per-node results), error.
    """
    details = []
    all_active = True

    for node in nodes:
        ip = node.get("admin_ip", "")
        hostname = node.get("hostname", "unknown")
        result = _safe_run_on_remote(
            host,
            f"systemctl is-active {service}",
            ip,
        )
        active = result.rc == 0 and "active" in result.stdout.strip()
        details.append({
            "hostname": hostname,
            "admin_ip": ip,
            "active": active,
            "output": result.stdout.strip(),
        })
        if not active:
            all_active = False

    failed_nodes = [d["hostname"] for d in details if not d["active"]]

    if all_active:
        return {
            "success": True,
            "message": f"{service} is active on all {len(nodes)} node(s)",
            "details": details,
            "error": "",
        }

    return {
        "success": False,
        "message": f"{service} is NOT active on: {', '.join(failed_nodes)}",
        "details": details,
        "error": f"{service} inactive on {len(failed_nodes)} node(s)",
    }


def verify_slurmctld_post_upgrade(host) -> Dict[str, Any]:
    """Verify slurmctld is active on all slurm control nodes after upgrade."""
    control_nodes = _get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": LOG["no_control_node"],
            "details": [],
            "error": "No slurm control node found",
        }
    return _check_service_on_nodes(host, control_nodes, SLURMCTLD_SERVICE)


def verify_slurmd_post_upgrade(host) -> Dict[str, Any]:
    """Verify slurmd is active on all slurm compute nodes after upgrade."""
    compute_nodes = _get_slurm_compute_nodes(host)
    if not compute_nodes:
        return {
            "success": False,
            "message": LOG["no_compute_nodes"],
            "details": [],
            "error": "No slurm compute nodes found",
        }
    return _check_service_on_nodes(host, compute_nodes, SLURMD_SERVICE)


def verify_munge_post_upgrade(host) -> Dict[str, Any]:
    """Verify munge is active on all slurm control + compute nodes after upgrade."""
    control_nodes = _get_slurm_control_nodes(host)
    compute_nodes = _get_slurm_compute_nodes(host)
    all_nodes = control_nodes + compute_nodes
    if not all_nodes:
        return {
            "success": False,
            "message": "No slurm nodes found in PXE mapping",
            "details": [],
            "error": "No slurm nodes found",
        }
    return _check_service_on_nodes(host, all_nodes, MUNGE_SERVICE)


# =============================================================================
# TC: VERIFY SBATCH JOB POST-UPGRADE
# =============================================================================

def verify_sbatch_post_upgrade(host) -> Dict[str, Any]:
    """Submit and verify a sbatch test job from the slurm control node.

    Returns:
        Dict with success, message, job_id, job_state, error.
    """
    control_nodes = _get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": LOG["no_control_node"],
            "job_id": "",
            "job_state": "",
            "error": "No slurm control node found",
        }

    control_ip = control_nodes[0].get("admin_ip", "")

    # Submit a simple sbatch job
    submit_cmd = (
        "sbatch --wrap='hostname && sleep 2 && echo done' "
        "--output=/tmp/omnia_upgrade_test_%j.out 2>&1"
    )
    submit_result = _safe_run_on_remote(host, submit_cmd, control_ip)

    if submit_result.rc != 0:
        return {
            "success": False,
            "message": LOG["sbatch_failed"].format(
                error=submit_result.stderr.strip(),
            ),
            "job_id": "",
            "job_state": "",
            "error": f"sbatch submit failed: {submit_result.stderr.strip()}",
        }

    # Extract job ID from "Submitted batch job 12345"
    job_id_match = re.search(r'Submitted batch job (\d+)', submit_result.stdout)
    if not job_id_match:
        return {
            "success": False,
            "message": LOG["sbatch_failed"].format(
                error=f"Cannot parse job ID from: {submit_result.stdout.strip()}",
            ),
            "job_id": "",
            "job_state": "",
            "error": f"Cannot parse job ID: {submit_result.stdout.strip()}",
        }

    job_id = job_id_match.group(1)

    # Poll sacct for job completion
    elapsed = 0
    job_state = ""
    while elapsed < SBATCH_JOB_TIMEOUT:
        sacct_result = _safe_run_on_remote(
            host,
            f"sacct -j {job_id} --format=State --noheader -P 2>/dev/null | head -1",
            control_ip,
        )
        if sacct_result.rc == 0 and sacct_result.stdout.strip():
            job_state = sacct_result.stdout.strip()
            if job_state in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"):
                break
        time.sleep(SBATCH_POLL_INTERVAL)
        elapsed += SBATCH_POLL_INTERVAL

    # Cleanup output file
    _safe_run_on_remote(
        host,
        f"rm -f /tmp/omnia_upgrade_test_{job_id}.out",
        control_ip,
    )

    if job_state == "COMPLETED":
        return {
            "success": True,
            "message": LOG["sbatch_ok"].format(job_id=job_id, state=job_state),
            "job_id": job_id,
            "job_state": job_state,
            "error": "",
        }

    return {
        "success": False,
        "message": LOG["sbatch_failed"].format(
            error=f"Job {job_id} ended with state: {job_state or 'UNKNOWN (timeout)'}",
        ),
        "job_id": job_id,
        "job_state": job_state or "TIMEOUT",
        "error": f"Job {job_id} state: {job_state or 'UNKNOWN (timeout)'}",
    }


# =============================================================================
# TC: VERIFY SRUN JOB POST-UPGRADE
# =============================================================================

def verify_srun_post_upgrade(host) -> Dict[str, Any]:
    """Submit and verify a srun test job from the slurm control node.

    Returns:
        Dict with success, message, output, num_nodes, error.
    """
    control_nodes = _get_slurm_control_nodes(host)
    if not control_nodes:
        return {
            "success": False,
            "message": LOG["no_control_node"],
            "output": "",
            "num_nodes": 0,
            "error": "No slurm control node found",
        }

    control_ip = control_nodes[0].get("admin_ip", "")
    compute_nodes = _get_slurm_compute_nodes(host)
    num_nodes = min(len(compute_nodes), 1) if compute_nodes else 1

    srun_cmd = f"srun -N {num_nodes} hostname"
    result = _safe_run_on_remote(host, srun_cmd, control_ip)

    if result.rc == 0 and result.stdout.strip():
        hostnames = result.stdout.strip().split("\n")
        return {
            "success": True,
            "message": LOG["srun_ok"].format(num_nodes=len(hostnames)),
            "output": result.stdout.strip(),
            "num_nodes": len(hostnames),
            "error": "",
        }

    return {
        "success": False,
        "message": LOG["srun_failed"].format(
            error=result.stderr.strip() or "No output",
        ),
        "output": result.stdout.strip(),
        "num_nodes": 0,
        "error": f"srun failed (rc={result.rc}): {result.stderr.strip()}",
    }
