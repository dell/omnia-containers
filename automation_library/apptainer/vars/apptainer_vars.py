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
Apptainer variables for OMNIA test automation.

This module contains constants and variables used for Apptainer testing.
"""

# =============================================================================
# HPC Tools Paths on Compute/Login Nodes (as deployed by Omnia)
# Matches DOWNLOAD_DIR and SCRIPT_DIR in download_container_image.sh.j2
# =============================================================================
COMPUTE_NODE_HPC_TOOLS_DIR = "/hpc_tools"
COMPUTE_NODE_CONTAINER_IMAGES_DIR = "/hpc_tools/container_images"
COMPUTE_NODE_SCRIPTS_DIR = "/hpc_tools/scripts"
COMPUTE_NODE_DOWNLOAD_SCRIPT = "/hpc_tools/scripts/download_container_image.sh"
COMPUTE_NODE_CONTAINER_IMAGE_LIST = "/hpc_tools/scripts/container_image.list"
APPTAINER_PULL_LOG = "/var/log/apptainer_pull.log"
CONTAINER_DOWNLOAD_LOG = "/var/log/container_image_download.log"

# =============================================================================
# NFS Config Name (from storage_config.yml nfs_client_params)
# =============================================================================
NFS_SLURM_NAME = "nfs_slurm"

# =============================================================================
# Apptainer Binary and File Format
# =============================================================================
APPTAINER_BINARY = "apptainer"
SIF_EXTENSION = ".sif"
SIF_READABLE_PERMISSIONS = "644"
SIF_RESTRICTED_PERMISSIONS = "600"

# =============================================================================
# SIF Download Configuration
# =============================================================================
SIF_DOWNLOAD_TIMEOUT = 1800
SIF_DOWNLOAD_POLL_INTERVAL = 30
SIF_DOWNLOAD_LOG = "/tmp/apptainer_download.log"

# =============================================================================
# Job Submission Configuration
# =============================================================================
APPTAINER_JOB_POLL_INTERVAL = 5
APPTAINER_JOB_TIMEOUT = 300
APPTAINER_SACCT_POLL_INTERVAL = 5
APPTAINER_SACCT_TIMEOUT = 300
APPTAINER_ARRAY_SIZE = 3
APPTAINER_CONCURRENT_JOB_COUNT = 5

# =============================================================================
# Reboot Test Configuration
# =============================================================================
REBOOT_WAIT_ONLINE_TIMEOUT = 900
REBOOT_WAIT_ONLINE_POLL_INTERVAL = 15
REBOOT_POST_SETTLE_DELAY = 30

# =============================================================================
# GPU and InfiniBand Detection Commands
# =============================================================================
GPU_LIST_CMD = "nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null"
GPU_COUNT_CMD = "nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | wc -l"
GPU_MEMORY_CMD = "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null"
INFINIBAND_DEVICES_CMD = "ls /dev/infiniband/ 2>/dev/null"
INFINIBAND_IBSTAT_CMD = "ibstat 2>/dev/null | grep -E 'State|Physical' | head -10"

# =============================================================================
# Temporary paths on remote nodes for test scripts/output
# =============================================================================
REMOTE_JOB_SCRIPT_DIR = "/tmp"
REMOTE_JOB_OUTPUT_DIR = "/tmp"
REMOTE_TEST_SIF_TMPDIR = "/tmp/apptainer_test_tmpdir"

# =============================================================================
# Permission test configuration
# =============================================================================
PERMISSION_TEST_TMPFILE = "/tmp/omnia_apptainer_perm_test"
PERMISSION_TEST_SIF_COPY = "/tmp/omnia_apptainer_perm_test.sif"
