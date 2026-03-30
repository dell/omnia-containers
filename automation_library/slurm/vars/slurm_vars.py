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

"""Slurm - Configuration Variables.

This module contains only constants for slurm job submission tests.
All functions reside in slurm_func.py.

Usage:
    from automation_library.slurm.vars import (
        JOB_SCRIPT_PATH,
        MULTI_JOB_COUNT,
    )
"""

# =============================================================================
# CONSTANTS
# =============================================================================

# Relative path (under automation_library/slurm/) of the default job script
JOB_SCRIPT_PATH = "automation_library/slurm/_job.sh"

# CPU over-request script for insufficient resources testing
JOB_CPU_OVERREQUEST_SCRIPT_PATH = "automation_library/slurm/_job_cpu_overrequest.sh"

# Insufficient-resource job scripts (mem over, CPU+mem over, CPU under, CPU exact, mem under, mem exact)
JOB2_SCRIPT_PATH = "automation_library/slurm/_job2.sh"
JOB3_SCRIPT_PATH = "automation_library/slurm/_job3.sh"
JOB4_SCRIPT_PATH = "automation_library/slurm/_job4.sh"
JOB5_SCRIPT_PATH = "automation_library/slurm/_job5.sh"
JOB6_SCRIPT_PATH = "automation_library/slurm/_job6.sh"
JOB7_SCRIPT_PATH = "automation_library/slurm/_job7.sh"

# Remote path where insufficient-resource job scripts are deployed
INSUF_JOB_REMOTE_PATH = "/tmp/insuf_job.sh"

# Number of jobs to submit in the multi-job test
MULTI_JOB_COUNT = 10

# Valid Slurm PENDING reason substrings (lowercased) for insufficient-resource tests
VALID_PENDING_REASONS = [
    "resources",
    "reqnodenotavail",
    "nodedown",
    "nodes required for job are down",
    "priority",
    "dependency",
    "partitiondown",
    "partitionnodedown",
    "partitionconfig",
]

# Expected error substrings (lowercased) when sbatch rejects a memory over-request
MEMORY_REJECTION_ERRORS = [
    "memory specification can not be satisfied",
    "requested node configuration is not available",
    "invalid",
    "resources",
]


# =============================================================================
# PAM CONSTANTS
# =============================================================================

# Path to SSH PAM configuration on compute nodes
PAM_CONFIG_PATH = "/etc/pam.d/sshd"


# =============================================================================
# QUEUEING CONSTANTS
# =============================================================================

# Valid Slurm PENDING reason substrings (lowercased for comparison)
QUEUEING_PENDING_REASONS = [
    "resources",
    "reqnodenotavail",
    "nodedown",
    "nodes required for job are down",
    "priority",
    "dependency",
    "partitiondown",
    "partitionnodedown",
    "partitionconfig",
]


# =============================================================================
# SCHEDULER STABILITY CONSTANTS
# =============================================================================

STABILITY_FLOOD_COUNT = 100

STABILITY_RAPID_CYCLE_COUNT = 50

STABILITY_SLEEP_JOB_SCRIPT = (
    "#!/bin/bash\n"
    "#SBATCH --job-name=stability_test\n"
    "#SBATCH --time=0-00:05:00\n"
    "#SBATCH --output=/dev/null\n"
    "#SBATCH --error=/dev/null\n"
    "sleep 30\n"
)

STABILITY_OVERSUBSCRIBE_SCRIPT_TPL = (
    "#!/bin/bash\n"
    "#SBATCH --job-name=oversub_test\n"
    "#SBATCH --cpus-per-task={cpus}\n"
    "#SBATCH --time=0-00:05:00\n"
    "#SBATCH --output=/dev/null\n"
    "#SBATCH --error=/dev/null\n"
    "sleep 30\n"
)

STABILITY_LONG_SLEEP_SCRIPT = (
    "#!/bin/bash\n"
    "#SBATCH --job-name=long_stability\n"
    "#SBATCH --time=0-00:10:00\n"
    "#SBATCH --output=/dev/null\n"
    "#SBATCH --error=/dev/null\n"
    "sleep 300\n"
)
