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
Slurm - Core Functions.

This module contains all reusable functions for slurm job submission tests.
Test functions should call these functions - all logic resides here.

Usage:
    from automation_library.slurm.functions import (
        is_node_reachable,
        run_ssh_from_omnia_core,
        copy_job_script_to_login,
        submit_job_via_login,
        check_squeue,
        find_reachable_login_node,
        read_job_script,
    )
"""

from typing import Dict, Any, List, Optional

from automation_library.core.host import (
    get_testinfra_host,
    run_in_container,
)
from ..vars.slurm_vars import get_job_script_path


# =============================================================================
# SSH HELPERS
# =============================================================================

def run_ssh_from_omnia_core(
    oim_host,
    login_ip: str,
    remote_cmd: str,
    key_path: Optional[str] = None,
):
    """Run command on login node via SSH from inside omnia_core container.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        remote_cmd: command to execute on the login node
        key_path: optional SSH private key path

    Returns:
        Result with stdout, stderr, rc attributes
    """
    ssh_opts = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    key_flag = f"-i {key_path}" if key_path else ""
    return run_in_container(
        oim_host,
        f"ssh {ssh_opts} {key_flag} root@{login_ip} '{remote_cmd}'",
    )


def is_node_reachable(
    oim_host,
    login_ip: str,
    key_path: Optional[str] = None,
) -> bool:
    """Check if a login node is reachable via SSH from omnia_core.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        key_path: optional SSH private key path

    Returns:
        True if the node responds to SSH, False otherwise
    """
    res = run_ssh_from_omnia_core(oim_host, login_ip, "echo ok", key_path)
    return res.rc == 0 and "ok" in res.stdout


def find_reachable_login_node(
    oim_host,
    login_ips: List[str],
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Find the first reachable login node from a list of IPs.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ips: list of login node admin IPs to try
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'login_ip', 'skipped', 'error'
    """
    skipped: List[str] = []
    for ip in login_ips:
        if is_node_reachable(oim_host, ip, key_path):
            return {
                "success": True,
                "login_ip": ip,
                "skipped": skipped,
                "error": None,
            }
        skipped.append(ip)

    return {
        "success": False,
        "login_ip": None,
        "skipped": skipped,
        "error": f"No reachable login nodes found among: {login_ips}",
    }


# =============================================================================
# JOB SCRIPT HELPERS
# =============================================================================

def read_job_script() -> Dict[str, Any]:
    """Read the default job.sh script from the project folder.

    Returns:
        Dict with 'success', 'content', 'path', 'error'
    """
    import os

    path = get_job_script_path()
    if not os.path.exists(path):
        return {
            "success": False,
            "content": None,
            "path": path,
            "error": f"job.sh not found at {path}",
        }

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "success": True,
        "content": content,
        "path": path,
        "error": None,
    }


def copy_job_script_to_login(
    oim_host,
    login_ip: str,
    job_script: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Copy job script content to /home/job.sh on the login node.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        job_script: content of the job script
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'details', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        "cd /home && cat > job.sh <<'EOF'\n" + job_script + "\nEOF\nchmod +x job.sh",
        key_path,
    )

    if res.rc == 0:
        return {
            "success": True,
            "details": f"Copied job.sh to /home on {login_ip}",
            "error": None,
        }

    return {
        "success": False,
        "details": None,
        "error": res.stderr or res.stdout,
    }


# =============================================================================
# JOB SUBMISSION / VERIFICATION
# =============================================================================

def submit_job_via_login(
    oim_host,
    login_ip: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit /home/job.sh via sbatch on the login node.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'job_id', 'output', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        "cd /home && sbatch --parsable job.sh",
        key_path,
    )

    if res.rc != 0:
        return {
            "success": False,
            "job_id": None,
            "output": res.stdout.strip(),
            "error": res.stderr or res.stdout,
        }

    raw_id = res.stdout.strip().split()[0] if res.stdout.strip() else ""
    if not raw_id:
        return {
            "success": False,
            "job_id": None,
            "output": res.stdout.strip(),
            "error": "sbatch did not return a job id",
        }

    if not raw_id.isdigit():
        return {
            "success": False,
            "job_id": raw_id,
            "output": res.stdout.strip(),
            "error": f"Expected numeric job id, got: {raw_id}",
        }

    return {
        "success": True,
        "job_id": raw_id,
        "output": res.stdout.strip(),
        "error": None,
    }


def check_squeue(
    oim_host,
    login_ip: str,
    job_id: str,
    key_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run squeue -j <job_id> on the login node and return the result.

    Args:
        oim_host: testinfra host object connected to OIM server
        login_ip: admin IP of the login node
        job_id: Slurm job ID to query
        key_path: optional SSH private key path

    Returns:
        Dict with 'success', 'output', 'error'
    """
    res = run_ssh_from_omnia_core(
        oim_host,
        login_ip,
        f"squeue -j {job_id}",
        key_path,
    )

    if res.rc == 0:
        return {
            "success": True,
            "output": res.stdout.strip(),
            "error": None,
        }

    return {
        "success": False,
        "output": res.stdout.strip(),
        "error": res.stderr or res.stdout,
    }
