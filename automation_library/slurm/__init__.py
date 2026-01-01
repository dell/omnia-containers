
# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Slurm module - Functions, messages, and variables for Slurm automation.

This module contains two test scenarios:
- slurm_job_queueing: Job submission and queueing tests
- insufficient_resources: Resource limit handling tests

Usage:
    from automation_library.slurm.functions import submit_slurm_job, get_cluster_resources
    from automation_library.slurm.messages import TEST_NAMES
    from automation_library.slurm.vars import SLURM_JOB_QUEUEING_VARS, INSUFFICIENT_RESOURCES_VARS

"""
