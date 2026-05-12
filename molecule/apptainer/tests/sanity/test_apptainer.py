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

"""Apptainer sanity and functional test cases for OMNIA (MD-928).

TC1  - Apptainer installed and accessible on all slurm compute nodes
TC2  - download_container_image.sh reads image list from scripts/ directory
TC3  - Script downloads images from Pulp registry only (no external fallback)
TC4  - SIF download to NFS does not increase local RAM
TC5  - SIF files present in container_images directory
TC6  - SIF file format validation (apptainer inspect)
TC7  - SIF file permissions readable by all users
TC8  - Script skips already-downloaded SIF files (idempotent)
TC9  - Script handles missing images in Pulp gracefully
TC10 - Submit single-node Apptainer job via Slurm
TC11 - Submit multi-node Apptainer job via Slurm
TC12 - No root privileges required to run Apptainer container
TC13 - SIF file readable by LDAP user
TC14 - Submit Apptainer job as LDAP user
TC15 - SIF reuse without re-download
TC16 - SIF image integrity verification (apptainer inspect)
TC17 - Execute multiple Apptainer jobs concurrently
TC18 - Submit job with invalid SIF file (expects FAILED)
TC19 - SIF with permissions 600 causes job failure
TC20 - GPU accessible in Apptainer container (--nv flag)
TC21 - GPU count correct inside Apptainer container
TC22 - Execute CUDA workload in Apptainer container
TC23 - GPU memory allocation/release inside container
TC24 - InfiniBand devices accessible inside Apptainer container
TC25 - NFS mount visible and accessible inside container
TC26 - SLURM environment variables accessible inside container
TC27 - Job array execution in Apptainer containers
TC28 - Container cleanup after job failure (no orphaned processes)
"""

import os
import sys

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../.."),
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
from automation_library.core import TestLogger
from automation_library.apptainer.functions.apptainer_func import (
    verify_apptainer_installed_on_all_slurm_nodes,
    verify_download_script_reads_image_list,
    verify_download_images_only_from_pulp,
    verify_run_download_script,
    verify_sif_download_does_not_increase_ram,
    verify_sif_files_in_container_images_dir,
    verify_sif_file_format_validation,
    verify_sif_file_permissions,
    verify_script_skips_already_downloaded_sif,
    verify_script_handles_missing_images_gracefully,
    verify_submit_single_node_apptainer_job,
    verify_submit_multi_node_apptainer_job,
    verify_no_root_required_for_apptainer,
    verify_sif_readable_by_ldap_user,
    verify_submit_apptainer_job_as_ldap_user,
    verify_sif_reuse_without_redownload,
    verify_sif_image_integrity,
    verify_execute_multiple_apptainer_jobs_concurrently,
    verify_job_with_invalid_sif_file,
    verify_sif_permission_600_fails_job,
    verify_gpu_accessible_in_apptainer_container,
    verify_gpu_count_correct_in_container,
    verify_execute_cuda_workload_in_container,
    verify_gpu_memory_allocation_in_container,
    verify_infiniband_accessible_in_container,
    verify_nfs_mount_visibility_in_container,
    verify_job_array_execution_in_containers,
    verify_container_cleanup_after_job_failure,
)


# =============================================================================
# TC1 – Apptainer installation on all slurm nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_apptainer_installation_on_all_slurm_nodes(host):
    """TC1: Verify Apptainer is installed and reports a version on every compute node."""
    log = TestLogger("Verify Apptainer installation on all slurm compute nodes")
    log.check("Running: which apptainer && apptainer --version on each node")

    result = verify_apptainer_installed_on_all_slurm_nodes(host)

    for detail in result.get("details", []):
        status = "OK" if detail.get("installed") else "MISSING"
        log.check(f"  {detail['hostname']}: apptainer {status} "
                  f"({detail.get('version', detail.get('error', ''))})")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC2 – download_container_image.sh reads image list
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_download_script_reads_image_list(host):
    """TC2: Verify download_container_image.sh and container_image.list both exist."""
    log = TestLogger("Verify download_container_image.sh reads image list")
    log.check("Checking script and image list presence on compute node")

    result = verify_download_script_reads_image_list(host)

    details = result.get("details", {})
    log.check(f"  Script: {details.get('script', 'N/A')} found={details.get('script_found', False)}")
    log.check(f"  List:   {details.get('list', 'N/A')} found={details.get('list_found', False)}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC3 – Script downloads images from Pulp only
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_script_downloads_images_only_from_pulp(host):
    """TC3: Verify actual download happened from Pulp by inspecting download log."""
    log = TestLogger("Verify images downloaded from Pulp only (no external fallback)")
    log.check("Analyzing download log for Pulp references and external registry URLs")

    result = verify_download_images_only_from_pulp(host)

    details = result.get("details", {})
    log.check(f"  Pulp reference in log: {details.get('has_pulp_ref', False)}")
    log.check(f"  External fallback detected: {details.get('has_external_fallback', False)}")
    
    if details.get('external_urls'):
        log.check(f"  External URLs found: {', '.join(details['external_urls'][:3])}")
    
    if details.get('sif_count'):
        log.check(f"  SIF files verified: {details['sif_count']}")
    
    if details.get('log_snippet') and not result["success"]:
        log.check(f"  Log snippet (last 300 chars):\n{details['log_snippet'][-300:]}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC_DL – Run download_container_image.sh to download SIF images
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_run_download_container_image_script(host):
    """TC_DL: Run download_container_image.sh on a compute node and verify SIF files appear."""
    log = TestLogger("Run download_container_image.sh to download SIF images")
    log.check("Executing download script on compute node (may take several minutes)")

    result = verify_run_download_script(host)

    details = result.get("details", {})
    if details.get("skipped"):
        log.check("  SIF files already present, download skipped")
    else:
        sif_files = details.get("sif_files", [])
        log.check(f"  Node: {details.get('hostname', 'N/A')}")
        log.check(f"  Exit code: {details.get('exit_code', 'N/A')}")
        log.check(f"  SIF files found: {len(sif_files)}")
        for sif in sif_files[:3]:
            log.check(f"    {sif}")
        if details.get("log"):
            log.check(f"  Script log (last 500 chars):\n{details['log'][-500:]}")
        if details.get("stderr"):
            log.check(f"  Stderr: {details['stderr']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC4 – SIF download does not increase RAM
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_sif_download_does_not_increase_ram(host):
    """TC4: Verify SIF download to NFS does not increase local compute node RAM."""
    log = TestLogger("Verify SIF download does not increase local RAM")
    log.check("Measuring free memory before and after SIF presence check")

    result = verify_sif_download_does_not_increase_ram(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    details = result.get("details", {})
    if details:
        log.check(f"  RAM before: {details.get('mem_before_mb', '?')} MB | "
                  f"after: {details.get('mem_after_mb', '?')} MB | "
                  f"delta: {details.get('delta_mb', '?')} MB")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC5 – SIF files in container_images directory
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_sif_files_in_container_images_dir(host):
    """TC5: Verify .sif files exist in the container_images directory on compute nodes."""
    log = TestLogger("Verify SIF files present in container_images directory")
    log.check("Listing *.sif in container_images/ on each compute node")

    result = verify_sif_files_in_container_images_dir(host)

    for detail in result.get("details", []):
        count = len(detail.get("sif_files", []))
        status = f"{count} SIF file(s)" if count else f"NONE — {detail.get('error', '')}"
        log.check(f"  {detail['hostname']}: {status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC6 – SIF file format validation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_sif_file_format_validation(host):
    """TC6: Run apptainer inspect on the first available SIF file to validate format."""
    log = TestLogger("Verify SIF file format (apptainer inspect)")
    log.check("Running apptainer inspect on first available SIF file")

    result = verify_sif_file_format_validation(host)

    details = result.get("details", {})
    log.check(f"  SIF file: {details.get('sif_file', 'N/A')}")
    if details.get("output"):
        log.check(f"  Inspect output (first line): {details['output'].splitlines()[0]}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC7 – SIF file permissions
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_sif_file_permissions(host):
    """TC7: Verify SIF files are world-readable on all compute nodes."""
    log = TestLogger("Verify SIF file permissions (readable by all users)")
    log.check("Checking for SIF files without read bit for group/other")

    result = verify_sif_file_permissions(host)

    for detail in result.get("details", []):
        status = "OK" if detail.get("passed") else f"FAIL — {detail.get('error', '')}"
        log.check(f"  {detail['hostname']}: permissions {status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC8 – Script skips already-downloaded SIF (idempotent / regression)
# =============================================================================

@pytest.mark.regression
@pytest.mark.order(9)
def test_script_skips_already_downloaded_sif(host):
    """TC8: Run download script when SIF exists; verify file is skipped and mtime unchanged."""
    log = TestLogger("Verify download script skips existing SIF (idempotent)")
    log.check("Running download script when SIF already present")

    result = verify_script_skips_already_downloaded_sif(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    details = result.get("details", {})
    log.check(f"  SIF file: {details.get('sif_file', 'N/A')}")
    log.check(f"  mtime unchanged: {details.get('mtime_unchanged', False)}")
    log.check(f"  skip logged in output: {details.get('skipped_in_output', False)}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC9 – Script handles missing images gracefully
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_script_handles_missing_images_gracefully(host):
    """TC9: Inject non-existent image into list; verify script logs error and exits gracefully."""
    log = TestLogger("Verify download script handles missing Pulp images gracefully")
    log.check("Injecting fake image into container_image.list and running script")

    result = verify_script_handles_missing_images_gracefully(host)

    details = result.get("details", {})
    if details.get("output_snippet"):
        log.check(f"  Script output (first 200 chars): {details['output_snippet'][:200]}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC10 – Single-node Apptainer job via Slurm
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_submit_single_node_apptainer_job(host):
    """TC10: Submit single-node sbatch job that runs apptainer exec <sif> hostname."""
    log = TestLogger("Submit single-node Apptainer job via Slurm")
    log.check("Transferring job script and submitting sbatch from control node")

    result = verify_submit_single_node_apptainer_job(host)

    log.check(f"  Job ID: {result.get('job_id', 'N/A')} | State: {result.get('job_state', 'N/A')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC11 – Multi-node Apptainer job via Slurm
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(12)
def test_submit_multi_node_apptainer_job(host):
    """TC11: Submit multi-node sbatch job using srun apptainer exec."""
    log = TestLogger("Submit multi-node Apptainer job via Slurm")
    log.check("Submitting multi-node sbatch with srun apptainer exec")

    result = verify_submit_multi_node_apptainer_job(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    log.check(f"  Job ID: {result.get('job_id', 'N/A')} | State: {result.get('job_state', 'N/A')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC12 – No root privileges required
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(13)
def test_no_root_privileges_required_for_apptainer(host):
    """TC12: Run apptainer exec as non-root and verify it succeeds."""
    log = TestLogger("Verify no root privileges required for Apptainer")
    log.check("Running apptainer exec as current user on compute node")

    result = verify_no_root_required_for_apptainer(host)

    details = result.get("details", {}) if isinstance(result.get("details"), dict) else {}
    if details:
        log.check(f"  Node: {details.get('hostname', 'N/A')} | "
                  f"host_user: {details.get('host_user', 'N/A')} | "
                  f"container_user: {details.get('container_user', 'N/A')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC13 – SIF file readable by LDAP user
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(14)
def test_sif_file_readable_by_ldap_user(host):
    """TC13: Verify LDAP user can stat/read the SIF file on compute node."""
    log = TestLogger("Verify SIF file readable by LDAP user")
    log.check("SSH as LDAP user and stat SIF file")

    result = verify_sif_readable_by_ldap_user(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    for detail in result.get("details", []):
        status = "readable" if detail.get("readable") else f"DENIED — {detail.get('error', '')}"
        log.check(f"  {detail.get('hostname', 'N/A')} [{detail.get('ldap_user', '?')}]: {status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC14 – Submit Apptainer job as LDAP user
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(15)
def test_submit_apptainer_job_as_ldap_user(host):
    """TC14: Submit sbatch job as LDAP user from login node with apptainer exec."""
    log = TestLogger("Submit Apptainer job as LDAP user")
    log.check("Submitting sbatch as LDAP user from login node")

    result = verify_submit_apptainer_job_as_ldap_user(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    log.check(f"  Job ID: {result.get('job_id', 'N/A')} | State: {result.get('job_state', 'N/A')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC15 – SIF reuse without re-download
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(16)
def test_sif_reuse_without_redownload(host):
    """TC15: Run download script again; verify SIF mtime is unchanged (skipped)."""
    log = TestLogger("Verify SIF reuse without re-download")
    log.check("Running download script second time and comparing mtime")

    result = verify_sif_reuse_without_redownload(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    details = result.get("details", {})
    log.check(f"  SIF file: {details.get('sif_file', 'N/A')} | mtime: {details.get('mtime', 'N/A')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC16 – SIF image integrity
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(17)
def test_sif_image_integrity(host):
    """TC16: Verify SIF image integrity using apptainer inspect."""
    log = TestLogger("Verify SIF image integrity (apptainer inspect)")
    log.check("Running apptainer inspect on SIF file")

    result = verify_sif_image_integrity(host)

    details = result.get("details", {})
    log.check(f"  SIF file: {details.get('sif_file', 'N/A')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC17 – Execute multiple Apptainer jobs concurrently
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(18)
def test_execute_multiple_apptainer_jobs_concurrently(host):
    """TC17: Submit 5 Apptainer jobs simultaneously and verify all COMPLETE."""
    log = TestLogger("Execute multiple Apptainer jobs concurrently")
    log.check("Submitting 5 sbatch Apptainer jobs in rapid succession")

    result = verify_execute_multiple_apptainer_jobs_concurrently(host)

    for detail in result.get("details", []):
        status = "COMPLETED" if detail.get("passed") else detail.get("state", "UNKNOWN")
        log.check(f"  Job {detail['job_id']}: {status}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC18 – Submit job with invalid SIF file
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(19)
def test_submit_job_with_invalid_sif_file(host):
    """TC18: Submit sbatch referencing non-existent SIF; verify job ends as FAILED."""
    log = TestLogger("Submit Apptainer job with invalid SIF file")
    log.check("Submitting job with non-existent SIF path (expects FAILED)")

    result = verify_job_with_invalid_sif_file(host)

    log.check(f"  Job ID: {result.get('job_id', 'N/A')} | State: {result.get('job_state', 'N/A')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC20 – GPU accessible in Apptainer container
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(21)
def test_gpu_accessible_in_apptainer_container(host):
    """TC20: Run nvidia-smi inside Apptainer with --nv flag and verify GPU visibility."""
    log = TestLogger("Verify GPU accessible in Apptainer container (--nv)")
    log.check("Running apptainer exec --nv <sif> nvidia-smi on GPU node")

    result = verify_gpu_accessible_in_apptainer_container(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    details = result.get("details", {})
    log.check(f"  Host GPUs: {details.get('host_gpus', [])}")
    log.check(f"  Container GPUs: {details.get('container_gpus', [])}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC21 – GPU count correct in container
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(22)
def test_gpu_count_correct_in_container(host):
    """TC21: Verify GPU count inside Apptainer container matches host GPU count."""
    log = TestLogger("Verify GPU count correct in Apptainer container")
    log.check("Comparing host GPU count vs container GPU count")

    result = verify_gpu_count_correct_in_container(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    details = result.get("details", {})
    log.check(f"  Host count: {details.get('host_count', '?')} | "
              f"Container count: {details.get('container_count', '?')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC22 – Execute CUDA workload in Apptainer container
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(23)
def test_execute_cuda_workload_in_container(host):
    """TC22: Submit GPU sbatch job running CUDA inside Apptainer with --nv."""
    log = TestLogger("Execute CUDA workload in Apptainer container")
    log.check("Submitting GPU sbatch job with apptainer exec --nv")

    result = verify_execute_cuda_workload_in_container(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    details = result.get("details", {})
    log.check(f"  Job ID: {details.get('job_id', 'N/A')} | State: {details.get('job_state', 'N/A')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC23 – GPU memory allocation in container
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(24)
def test_gpu_memory_allocation_in_container(host):
    """TC23: Verify GPU memory is allocated and released correctly inside Apptainer."""
    log = TestLogger("GPU memory allocation verification inside Apptainer container")
    log.check("Measuring GPU memory before/after container workload")

    result = verify_gpu_memory_allocation_in_container(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    details = result.get("details", {})
    log.check(f"  GPU memory before: {details.get('mem_before_mib', '?')} MiB | "
              f"after: {details.get('mem_after_mib', '?')} MiB")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC24 – InfiniBand accessible in Apptainer container
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(25)
def test_infiniband_accessible_in_apptainer_container(host):
    """TC24: Verify /dev/infiniband devices are visible inside Apptainer container."""
    log = TestLogger("Verify InfiniBand accessible in Apptainer container")
    log.check("Running apptainer exec --bind /dev/infiniband <sif> ls /dev/infiniband/")

    result = verify_infiniband_accessible_in_container(host)

    if result.get("skipped"):
        pytest.skip(result["message"])

    details = result.get("details", {})
    log.check(f"  Host IB devices: {details.get('host_ib_devices', 'none')}")
    log.check(f"  Container IB devices: {details.get('container_ib_devices', 'none')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC25 – NFS mount visible inside container
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(26)
def test_nfs_mount_visibility_inside_container(host):
    """TC25: Verify NFS (hpc_tools) is accessible inside Apptainer container."""
    log = TestLogger("Verify NFS mount visible inside Apptainer container")
    log.check("Running apptainer exec --bind <nfs> <sif> ls <container_images>")

    result = verify_nfs_mount_visibility_in_container(host)

    details = result.get("details", {})
    log.check(f"  Host NFS mount: {details.get('host_mount', 'N/A')}")
    log.check(f"  Container ls output: {str(details.get('container_ls', ''))[:100]}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC26 – Job array execution in containers
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(26)
def test_job_array_execution_in_containers(host):
    """TC26: Submit sbatch --array job; verify all array tasks COMPLETE in containers."""
    log = TestLogger("Verify job array execution in Apptainer containers")
    log.check("Submitting array job with apptainer exec inside each task")

    result = verify_job_array_execution_in_containers(host)

    for detail in result.get("details", []):
        log.check(f"  Task {detail.get('task_id', '?')}: {detail.get('state', 'UNKNOWN')}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC27 – Container cleanup after job failure
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(27)
def test_container_cleanup_after_job_failure(host):
    """TC27: Submit failing container job; verify no orphaned apptainer processes remain."""
    log = TestLogger("Test container cleanup after job failure")
    log.check("Submitting failing job then checking ps for orphaned apptainer processes")

    result = verify_container_cleanup_after_job_failure(host)

    details = result.get("details", {})
    log.check(f"  Job ID: {details.get('job_id', 'N/A')} | State: {details.get('job_state', 'N/A')}")
    log.check(f"  Orphaned processes: {details.get('orphan_processes', [])}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]
