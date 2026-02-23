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
Slurm - Configuration Variables.

This module contains variables and helpers for slurm job submission tests.
Login node IPs are resolved from the PXE mapping file (header-based column
lookup) or from environment variables as a fallback.

Usage:
    from automation_library.slurm.vars import (
        JOB_SCRIPT_PATH,
        parse_login_ips_from_env,
        parse_login_ips_from_pxe_mapping,
    )
"""

import os
from typing import List

from automation_library.core.host import (
    _get_pxe_mapping_content,
    get_testinfra_host,
)


# =============================================================================
# CONSTANTS
# =============================================================================

# Relative path (under automation_library/) of the default job script
JOB_SCRIPT_PATH = "automation_library/job.sh"

# Number of jobs to submit in the multi-job test
MULTI_JOB_COUNT = 10


# =============================================================================
# LOGIN NODE DISCOVERY
# =============================================================================

def _get_project_root() -> str:
    """Get the project root directory."""
    # File is at automation_library/slurm/vars/slurm_vars.py
    # Go up 4 levels: slurm_vars.py -> vars -> slurm -> automation_library -> project_root
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def get_job_script_path() -> str:
    """Return absolute path to the default job script."""
    return os.path.join(_get_project_root(), JOB_SCRIPT_PATH)


def parse_login_ips_from_env() -> List[str]:
    """Read login node IPs from LOGIN_NODE_IPS environment variable."""
    value = os.environ.get("LOGIN_NODE_IPS", "").strip()
    if not value:
        return []
    return [ip.strip() for ip in value.split(",") if ip.strip()]


def parse_login_ips_from_pxe_mapping() -> List[str]:
    """Extract login node admin IPs from PXE mapping file inside omnia_core.

    Column positions are resolved from the CSV header row so the columns
    can appear in any order.
    """
    host = get_testinfra_host()
    pxe_content = _get_pxe_mapping_content(host)
    if not pxe_content:
        return []

    login_ips: List[str] = []
    lines = [line for line in pxe_content.split("\n") if line.strip()]
    if len(lines) < 2:
        return login_ips

    # Resolve column positions from the header row
    header = [col.strip().upper() for col in lines[0].split(",")]
    try:
        fg_idx = header.index("FUNCTIONAL_GROUP_NAME")
        hn_idx = header.index("HOSTNAME")
        ip_idx = header.index("ADMIN_IP")
    except ValueError:
        return login_ips

    for line in lines[1:]:  # skip header
        cols = line.split(",")
        if len(cols) <= max(fg_idx, hn_idx, ip_idx):
            continue
        functional_group = cols[fg_idx].strip().lower()
        hostname = cols[hn_idx].strip().lower()
        admin_ip = cols[ip_idx].strip()

        if "login" in functional_group or "login" in hostname:
            if admin_ip:
                login_ips.append(admin_ip)

    return login_ips
