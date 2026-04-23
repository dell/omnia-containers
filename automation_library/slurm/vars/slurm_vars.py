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
Slurm variables for OMNIA test automation.

This module contains constants and variables used for Slurm testing.
"""

# =============================================================================
# Functional Group Names (from PXE mapping file)
# =============================================================================
SLURM_CONTROL_NODE_FUNCTIONAL_GROUP = "slurm_control_node"
SLURM_NODE_FUNCTIONAL_GROUP = "slurm_node"
LOGIN_NODE_FUNCTIONAL_GROUP = "login_node"
LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP = "login_compiler_node"

# =============================================================================
# Service Names
# =============================================================================
SLURMCTLD_SERVICE = "slurmctld"
SLURMD_SERVICE = "slurmd"
SLURMDBD_SERVICE = "slurmdbd"
MUNGE_SERVICE = "munge"

# =============================================================================
# All functional groups that must have munge active
# =============================================================================
MUNGE_REQUIRED_GROUPS = [
    SLURM_CONTROL_NODE_FUNCTIONAL_GROUP,
    LOGIN_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_FUNCTIONAL_GROUP,
]

# =============================================================================
# PXE Mapping File Path (inside omnia_core container)
# =============================================================================
PXE_MAPPING_FILE_PATH = "/opt/omnia/input/project_default/pxe_mapping_file.csv"

# =============================================================================
# Sbatch Job Configuration
# =============================================================================
SBATCH_JOB_POLL_INTERVAL = 5
SBATCH_JOB_TIMEOUT = 120
SACCT_POLL_INTERVAL = 5
SACCT_TIMEOUT = 120

# =============================================================================
# SSH Settings
# =============================================================================
SSH_TIMEOUT = 10

# =============================================================================
# LDAP User / PAM Test Configuration
# =============================================================================
PAM_SLEEP_JOB_DURATION = 40
PAM_JOB_POLL_INTERVAL = 3
PAM_JOB_RUNNING_TIMEOUT = 60
PAM_JOB_COMPLETE_TIMEOUT = 120
PAM_LOGIN_RETRY_DELAY = 5
PAM_LOGIN_RETRIES = 3

# =============================================================================
# Multi-Job / Drain / Resource Test Configuration
# =============================================================================
MULTI_JOB_COUNT = 3
DRAIN_REASON = "omnia_test_drain"
DRAIN_UNDRAIN_SETTLE_DELAY = 5
DRAIN_JOB_TRANSITION_TIMEOUT = 120

# =============================================================================
# Functional groups where ldapuser login should always succeed
# =============================================================================
LDAP_LOGIN_ALLOWED_GROUPS = [
    SLURM_CONTROL_NODE_FUNCTIONAL_GROUP,
    LOGIN_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
]

# =============================================================================
# Reboot Test Configuration
# =============================================================================
REBOOT_WAIT_ONLINE_TIMEOUT = 900
REBOOT_WAIT_ONLINE_POLL_INTERVAL = 15
CLOUD_INIT_WAIT_TIMEOUT = 900
CLOUD_INIT_WAIT_POLL_INTERVAL = 15
SLURM_POST_REBOOT_SETTLE_DELAY = 30
NODE_IDLE_WAIT_TIMEOUT = 600
NODE_IDLE_WAIT_POLL_INTERVAL = 10
