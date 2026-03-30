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
Slurm vars module.
"""

from .slurm_vars import (
    JOB_SCRIPT_PATH,
    JOB_CPU_OVERREQUEST_SCRIPT_PATH,
    JOB2_SCRIPT_PATH,
    JOB3_SCRIPT_PATH,
    JOB4_SCRIPT_PATH,
    JOB5_SCRIPT_PATH,
    JOB6_SCRIPT_PATH,
    JOB7_SCRIPT_PATH,
    INSUF_JOB_REMOTE_PATH,
    MULTI_JOB_COUNT,
    VALID_PENDING_REASONS,
    MEMORY_REJECTION_ERRORS,
    PAM_CONFIG_PATH,
    QUEUEING_PENDING_REASONS,
    STABILITY_FLOOD_COUNT,
    STABILITY_RAPID_CYCLE_COUNT,
    STABILITY_SLEEP_JOB_SCRIPT,
    STABILITY_OVERSUBSCRIBE_SCRIPT_TPL,
    STABILITY_LONG_SLEEP_SCRIPT,
)

__all__ = [
    "JOB_SCRIPT_PATH",
    "JOB_CPU_OVERREQUEST_SCRIPT_PATH",
    "JOB2_SCRIPT_PATH",
    "JOB3_SCRIPT_PATH",
    "JOB4_SCRIPT_PATH",
    "JOB5_SCRIPT_PATH",
    "JOB6_SCRIPT_PATH",
    "JOB7_SCRIPT_PATH",
    "INSUF_JOB_REMOTE_PATH",
    "MULTI_JOB_COUNT",
    "VALID_PENDING_REASONS",
    "MEMORY_REJECTION_ERRORS",
    "PAM_CONFIG_PATH",
    "QUEUEING_PENDING_REASONS",
    "STABILITY_FLOOD_COUNT",
    "STABILITY_RAPID_CYCLE_COUNT",
    "STABILITY_SLEEP_JOB_SCRIPT",
    "STABILITY_OVERSUBSCRIBE_SCRIPT_TPL",
    "STABILITY_LONG_SLEEP_SCRIPT",
]
