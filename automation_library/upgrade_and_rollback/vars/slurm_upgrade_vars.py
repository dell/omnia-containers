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
Slurm Upgrade Module - Variables.

Constants and configuration for post-upgrade Slurm cluster verification.

These tests validate the state of the Slurm cluster after the
``upgrade_slurm`` role has executed (NFS backup, cluster health,
service availability, and job execution).
"""

from typing import Dict, Any

# =============================================================================
# OIM METADATA & CONFIG PATHS (inside omnia_core container)
# =============================================================================
OIM_METADATA_PATH: str = "/opt/omnia/.data/oim_metadata.yml"
INPUT_PROJECT_DIR: str = "/opt/omnia/input/project_default"
OMNIA_CONFIG_FILE: str = "omnia_config.yml"
STORAGE_CONFIG_FILE: str = "storage_config.yml"
PROVISION_CONFIG_FILE: str = "provision_config.yml"

# =============================================================================
# FUNCTIONAL GROUP PREFIXES (from PXE mapping)
# =============================================================================
SLURM_CONTROL_NODE_FG: str = "slurm_control_node"
SLURM_NODE_FG: str = "slurm_node"

# =============================================================================
# NFS BACKUP PATHS (relative to slurm NFS mount)
# =============================================================================
SLURM_CONF_RELATIVE_PATH: str = "etc/slurm/slurm.conf"
MYSQL_DATADIR_RELATIVE: str = "var/lib/mysql"
MYSQL_IBDATA_FILE: str = "ibdata1"
MYSQL_SYSTEM_DB: str = "mysql"

# =============================================================================
# HPC TOOLS TRACKING FILES (cleaned during upgrade)
# =============================================================================
HPC_TOOLS_TRACKING_FILES = [
    "/hpc_tools/.done_cuda",
    "/hpc_tools/cuda/bin/nvcc",
]

# =============================================================================
# SERVICE NAMES
# =============================================================================
SLURMCTLD_SERVICE: str = "slurmctld"
SLURMD_SERVICE: str = "slurmd"
MUNGE_SERVICE: str = "munge"

# =============================================================================
# UPGRADE MANIFEST & GATE PATHS (inside omnia_core container)
# =============================================================================
UPGRADE_MANIFEST_PATH: str = "/opt/omnia/.data/upgrade_manifest.yml"
UPGRADE_PLAYBOOK_DIR: str = "/omnia/upgrade"
UPGRADE_PLAYBOOK_CMD: str = "ansible-playbook upgrade.yml --tags slurm"

# =============================================================================
# TIMEOUTS & POLLING
# =============================================================================
SQUEUE_RETRIES: int = 5
SQUEUE_RETRY_DELAY: int = 5
SINFO_RETRIES: int = 5
SINFO_RETRY_DELAY: int = 5
SBATCH_JOB_TIMEOUT: int = 120
SBATCH_POLL_INTERVAL: int = 5
SLURM_UPGRADE_TIMEOUT: int = 3600
SLURM_UPGRADE_POLL_INTERVAL: int = 30

# =============================================================================
# AGGREGATED VARS DICT (for convenient import)
# =============================================================================
SLURM_UPGRADE_VARS: Dict[str, Any] = {
    "oim_metadata_path": OIM_METADATA_PATH,
    "input_project_dir": INPUT_PROJECT_DIR,
    "omnia_config_file": OMNIA_CONFIG_FILE,
    "storage_config_file": STORAGE_CONFIG_FILE,
    "provision_config_file": PROVISION_CONFIG_FILE,
    "slurm_control_node_fg": SLURM_CONTROL_NODE_FG,
    "slurm_node_fg": SLURM_NODE_FG,
    "slurm_conf_relative_path": SLURM_CONF_RELATIVE_PATH,
    "mysql_datadir_relative": MYSQL_DATADIR_RELATIVE,
    "mysql_ibdata_file": MYSQL_IBDATA_FILE,
    "mysql_system_db": MYSQL_SYSTEM_DB,
    "hpc_tools_tracking_files": HPC_TOOLS_TRACKING_FILES,
    "slurmctld_service": SLURMCTLD_SERVICE,
    "slurmd_service": SLURMD_SERVICE,
    "munge_service": MUNGE_SERVICE,
    "squeue_retries": SQUEUE_RETRIES,
    "squeue_retry_delay": SQUEUE_RETRY_DELAY,
    "sinfo_retries": SINFO_RETRIES,
    "sinfo_retry_delay": SINFO_RETRY_DELAY,
    "sbatch_job_timeout": SBATCH_JOB_TIMEOUT,
    "sbatch_poll_interval": SBATCH_POLL_INTERVAL,
    "upgrade_manifest_path": UPGRADE_MANIFEST_PATH,
    "upgrade_playbook_dir": UPGRADE_PLAYBOOK_DIR,
    "upgrade_playbook_cmd": UPGRADE_PLAYBOOK_CMD,
    "slurm_upgrade_timeout": SLURM_UPGRADE_TIMEOUT,
    "slurm_upgrade_poll_interval": SLURM_UPGRADE_POLL_INTERVAL,
}
