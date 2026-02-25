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
        LDAP_USERNAME,
        LDAP_PASSWORD,
    )
"""

# =============================================================================
# CONSTANTS
# =============================================================================

# Relative path (under automation_library/slurm/) of the default job script
JOB_SCRIPT_PATH = "automation_library/slurm/job.sh"

# Number of jobs to submit in the multi-job test
MULTI_JOB_COUNT = 10


# =============================================================================
# LDAP CONSTANTS
# =============================================================================

LDAP_USERNAME = "ldapuser"
LDAP_PASSWORD = "ninja"
