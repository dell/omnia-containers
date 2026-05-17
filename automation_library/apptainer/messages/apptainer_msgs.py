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

"""Apptainer message constants used by the OMNIA automation library."""

TEST_PASSED = "PASSED"
TEST_FAILED = "FAILED"
TEST_SKIPPED = "SKIPPED"

# =============================================================================
# Node / Infrastructure Errors
# =============================================================================
ERROR_NO_SLURM_NODES = "No slurm compute nodes found in PXE mapping file"
ERROR_NO_SLURM_CONTROL_NODES = "No slurm control nodes found in PXE mapping file"
ERROR_NO_LOGIN_NODES = "No login or login compiler nodes found in PXE mapping file"
ERROR_NO_SIF_FILES = "No SIF files found in container_images directory"
ERROR_LDAP_CREDS_MISSING = "ldap_credentials not configured in omnia_test_config.yml"

# =============================================================================
# TC1 – Apptainer Installation
# =============================================================================
APPTAINER_INSTALL_PASSED = "Apptainer is installed and accessible on all slurm compute nodes"
APPTAINER_INSTALL_FAILED = "Apptainer is NOT installed or not accessible on one or more slurm compute nodes"
APPTAINER_NOT_IN_PATH = "apptainer binary not found in PATH on node {node} ({ip})"
APPTAINER_VERSION_FAILED = "apptainer --version failed on node {node} ({ip}): {error}"

# =============================================================================
# TC2 – Download Script Reads Image List
# =============================================================================
DOWNLOAD_SCRIPT_LIST_PASSED = "download_container_image.sh exists and container_image.list is present"
DOWNLOAD_SCRIPT_LIST_FAILED = "download_container_image.sh or container_image.list missing: {error}"
DOWNLOAD_SCRIPT_NOT_FOUND = "download_container_image.sh not found at {path}"
CONTAINER_IMAGE_LIST_NOT_FOUND = "container_image.list not found at {path}"

# =============================================================================
# TC3 – Images Downloaded from Pulp Only
# =============================================================================
PULP_ONLY_PASSED = "Script is configured to download images from Pulp registry only (no external fallback)"
PULP_ONLY_FAILED = "Script may have external registry fallback enabled: {detail}"

# =============================================================================
# TC4 – SIF Download Does Not Increase RAM
# =============================================================================
RAM_SIZE_PASSED = "RAM usage did not increase after SIF download (NFS-based download confirmed)"
RAM_SIZE_FAILED = "RAM usage increased unexpectedly after SIF download: {detail}"
RAM_SIZE_SKIPPED = "Skipping RAM check: no SIF files available or download script not found"

# =============================================================================
# TC5 – SIF Files in container_images Directory
# =============================================================================
SIF_IN_DIR_PASSED = "SIF files found in container_images directory: {files}"
SIF_IN_DIR_FAILED = "No SIF files found in container_images directory at {path}"

# =============================================================================
# TC6 – SIF File Format Validation
# =============================================================================
SIF_FORMAT_PASSED = "SIF file format validated successfully: {sif_file}"
SIF_FORMAT_FAILED = "SIF file format validation failed for {sif_file}: {error}"

# =============================================================================
# TC7 – SIF File Permissions
# =============================================================================
SIF_PERMS_PASSED = "SIF file permissions are correct (readable by all users) on all nodes"
SIF_PERMS_FAILED = "SIF file permissions are incorrect on one or more nodes: {detail}"

# =============================================================================
# TC8 – Script Skips Already Downloaded SIF (Idempotent)
# =============================================================================
SKIP_EXISTING_SIF_PASSED = "Script correctly skipped already-downloaded SIF files (idempotent)"
SKIP_EXISTING_SIF_FAILED = "Script did not skip existing SIF files: {error}"

# =============================================================================
# TC9 – Script Handles Missing Images Gracefully
# =============================================================================
MISSING_IMAGE_HANDLED_PASSED = "Script handled missing Pulp image gracefully with error message"
MISSING_IMAGE_HANDLED_FAILED = "Script did not handle missing Pulp image gracefully: {error}"

# =============================================================================
# TC10 – Single Node Apptainer Job via Slurm
# =============================================================================
SINGLE_NODE_JOB_PASSED = "Single-node Apptainer job completed successfully (JobID: {job_id})"
SINGLE_NODE_JOB_FAILED = "Single-node Apptainer job failed: {error}"
SINGLE_NODE_JOB_SUBMIT_FAILED = "Failed to submit single-node Apptainer job: {error}"
SINGLE_NODE_JOB_TIMEOUT = "Single-node Apptainer job {job_id} did not complete within {timeout}s"

# =============================================================================
# TC11 – Multi-Node Apptainer Job via Slurm
# =============================================================================
MULTI_NODE_JOB_PASSED = "Multi-node Apptainer job completed successfully on {nodes} node(s) (JobID: {job_id})"
MULTI_NODE_JOB_FAILED = "Multi-node Apptainer job failed: {error}"
MULTI_NODE_JOB_SKIPPED = "Skipping multi-node job: fewer than 2 compute nodes available"

# =============================================================================
# TC12 – No Root Privileges Required
# =============================================================================
NO_ROOT_REQUIRED_PASSED = "Apptainer container ran successfully without root privileges on {node}"
NO_ROOT_REQUIRED_FAILED = "Apptainer container requires root privileges or failed as non-root: {error}"
NO_ROOT_SKIPPED = "Skipping no-root test: no compute nodes available"

# =============================================================================
# TC13 – SIF File Readable by LDAP User
# =============================================================================
SIF_LDAP_READABLE_PASSED = "SIF file is readable by LDAP user on all tested nodes"
SIF_LDAP_READABLE_FAILED = "SIF file is NOT readable by LDAP user on one or more nodes: {error}"
SIF_LDAP_READABLE_SKIPPED = "Skipping LDAP SIF read test: LDAP credentials not configured"

# =============================================================================
# TC14 – Submit Apptainer Job as LDAP User
# =============================================================================
LDAP_JOB_PASSED = "Apptainer job as LDAP user completed successfully (JobID: {job_id})"
LDAP_JOB_FAILED = "Apptainer job as LDAP user failed: {error}"
LDAP_JOB_SKIPPED = "Skipping LDAP Apptainer job: LDAP credentials not configured"

# =============================================================================
# TC15 – SIF Reuse Without Re-Download
# =============================================================================
SIF_REUSE_PASSED = "SIF file was reused without re-download (mtime unchanged)"
SIF_REUSE_FAILED = "SIF file was re-downloaded unexpectedly: {error}"
SIF_REUSE_SKIPPED = "Skipping SIF reuse test: no SIF files available"

# =============================================================================
# TC16 – SIF Image Integrity
# =============================================================================
SIF_INTEGRITY_PASSED = "SIF image integrity verified successfully: {sif_file}"
SIF_INTEGRITY_FAILED = "SIF image integrity check failed for {sif_file}: {error}"

# =============================================================================
# TC17 – Concurrent Apptainer Jobs
# =============================================================================
CONCURRENT_JOBS_PASSED = "All {count} concurrent Apptainer jobs completed successfully"
CONCURRENT_JOBS_FAILED = "One or more concurrent Apptainer jobs failed: {error}"

# =============================================================================
# TC18 – Job with Invalid SIF File
# =============================================================================
INVALID_SIF_JOB_PASSED = "Job with invalid SIF file correctly failed with error message"
INVALID_SIF_JOB_FAILED = "Job with invalid SIF file did not fail as expected: {error}"

# =============================================================================
# TC19 – SIF Permission 600 Fails Job
# =============================================================================
PERM_600_FAIL_PASSED = "Job correctly failed with permission error when SIF file set to 600"
PERM_600_FAIL_FAILED = "Job did NOT fail with permission error as expected: {error}"
PERM_600_SKIPPED = "Skipping SIF permission test: no SIF files or LDAP user not configured"

# =============================================================================
# TC20 – GPU Accessible in Apptainer Container
# =============================================================================
GPU_IN_CONTAINER_PASSED = "GPU is accessible inside Apptainer container (--nv flag working)"
GPU_IN_CONTAINER_FAILED = "GPU is NOT accessible inside Apptainer container: {error}"
GPU_IN_CONTAINER_SKIPPED = "Skipping GPU container test: no GPU nodes available"

# =============================================================================
# TC21 – GPU Count Correct in Container
# =============================================================================
GPU_COUNT_PASSED = "GPU count matches between host ({host_count}) and container ({container_count})"
GPU_COUNT_FAILED = "GPU count mismatch: host={host_count}, container={container_count}"
GPU_COUNT_SKIPPED = "Skipping GPU count test: no GPU nodes available"

# =============================================================================
# TC22 – CUDA Workload in Container
# =============================================================================
CUDA_WORKLOAD_PASSED = "CUDA workload executed successfully inside Apptainer container (JobID: {job_id})"
CUDA_WORKLOAD_FAILED = "CUDA workload failed inside Apptainer container: {error}"
CUDA_WORKLOAD_SKIPPED = "Skipping CUDA workload test: no CUDA-enabled SIF image or GPU nodes"

# =============================================================================
# TC23 – GPU Memory Allocation in Container
# =============================================================================
GPU_MEMORY_PASSED = "GPU memory allocated and released correctly inside Apptainer container"
GPU_MEMORY_FAILED = "GPU memory allocation check failed: {error}"
GPU_MEMORY_SKIPPED = "Skipping GPU memory test: no GPU nodes available"

# =============================================================================
# TC24 – InfiniBand Accessible in Container
# =============================================================================
IB_IN_CONTAINER_PASSED = "InfiniBand devices are accessible inside Apptainer container"
IB_IN_CONTAINER_FAILED = "InfiniBand devices are NOT accessible inside Apptainer container: {error}"
IB_IN_CONTAINER_SKIPPED = "Skipping InfiniBand test: no InfiniBand-enabled nodes found"

# =============================================================================
# TC25 – NFS Mount Visible in Container
# =============================================================================
NFS_IN_CONTAINER_PASSED = "NFS mounts are visible inside Apptainer container and files are accessible"
NFS_IN_CONTAINER_FAILED = "NFS mounts are NOT visible or accessible inside Apptainer container: {error}"

# =============================================================================
# TC27 – Job Array in Containers
# =============================================================================
JOB_ARRAY_PASSED = "All {count} array job tasks completed successfully in containers"
JOB_ARRAY_FAILED = "Job array execution in containers failed: {error}"

# =============================================================================
# TC28 – Container Cleanup After Job Failure
# =============================================================================
CLEANUP_PASSED = "Container processes cleaned up correctly after job failure (no orphaned processes)"
CLEANUP_FAILED = "Container cleanup after job failure failed: {error}"

# =============================================================================
# TC29 – NFS and SIF After Node Reboot (Negative)
# =============================================================================
REBOOT_NFS_SIF_PASSED = "NFS mount and SIF files accessible on compute node after reboot"
REBOOT_NFS_SIF_FAILED = "NFS mount or SIF files NOT accessible after reboot: {error}"

# =============================================================================
# TC30 – Container Execution Post Reboot (Negative)
# =============================================================================
REBOOT_CONTAINER_EXEC_PASSED = "Apptainer container job ran successfully on rebooted node (JobID: {job_id})"
REBOOT_CONTAINER_EXEC_FAILED = "Apptainer container job failed on rebooted node: {error}"

# =============================================================================
# TC31 – Download Script Works After Reboot (Negative)
# =============================================================================
REBOOT_DOWNLOAD_SCRIPT_PASSED = "download_container_image.sh works correctly after node reboot"
REBOOT_DOWNLOAD_SCRIPT_FAILED = "download_container_image.sh failed after node reboot: {error}"
