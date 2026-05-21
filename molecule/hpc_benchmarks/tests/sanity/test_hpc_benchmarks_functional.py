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
HPC Benchmarks Functional, Idempotency, Compatibility, Regression, and
Performance Tests.

Test IDs:
  TC-F01  test_x86_64_json_parsing
  TC-F03  test_local_repo_sync_x86_64
  TC-F05  test_hpc_tools_dir_creation
  TC-F06  test_x86_64_artifact_copy
  TC-F08  test_msr_safe_x86_64_only
  TC-F09  test_container_first_guidance
  TC-F10  test_source_only_delivery
  TC-F11  test_per_tool_staging_report
  TC-F13  test_e2e_provisioning_x86_64
  TC-F15  test_nfs_accessibility
  TC-F16  test_airgapped_staging
  TC-F17  test_provisioning_idempotency
  TC-F18  test_post_staging_validation
  TC-I01  test_dir_creation_idempotency
  TC-I02  test_artifact_staging_idempotency
  TC-C01  test_rhel_compatibility
  TC-RT01 test_cuda_flow_unaffected
  TC-RT02 test_nvhpc_flow_unaffected
  TC-RT03 test_container_image_flow_unaffected
  TC-RT04 test_openmpi_unaffected
  TC-RT05 test_existing_hpc_dirs_preserved
  TC-RT06 test_empty_declaration_no_new_dirs
  TC-P01  test_staging_duration
  TC-P02  test_staging_overhead
  TC-P03  test_report_availability

Spec: TSPEC-HPCBENCH-2026-001 v1.0.0
"""

import pytest

from automation_library.core import TestLogger
from automation_library.hpc_benchmarks import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    verify_x86_64_json_parsing,
    verify_local_repo_sync_x86_64,
    verify_hpc_tools_dir_creation,
    verify_x86_64_artifact_copy,
    verify_msr_safe_x86_64_only,
    verify_container_first_guidance,
    verify_source_only_delivery,
    verify_per_tool_staging_report,
    verify_e2e_provisioning_x86_64,
    verify_nfs_accessibility,
    verify_airgapped_staging,
    verify_dir_creation_idempotency,
    verify_artifact_staging_idempotency,
    verify_post_staging_validation,
    verify_rhel_compatibility,
    verify_cuda_flow_unaffected,
    verify_nvhpc_flow_unaffected,
    verify_container_image_flow_unaffected,
    verify_openmpi_unaffected,
    verify_existing_hpc_dirs_preserved,
    verify_empty_declaration_no_new_dirs,
    measure_staging_duration,
    measure_staging_overhead,
    measure_report_availability,
)


# =============================================================================
# TC-F01: x86_64 JSON DECLARATION PARSING
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_x86_64_json_parsing(host):
    """
    TC-F01: Parse slurm_custom.json for x86_64; verify all benchmark packages
    declared with correct types; msr-safe present; container-first image
    declared.

    Acceptance criteria: AC-6.1.1
    """
    log = TestLogger(TEST_NAMES["x86_64_json_parsing"])

    result = verify_x86_64_json_parsing(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["packages_missing"].format(
            arch="x86_64",
            expected="imb, osu-micro-benchmarks, likwid, geopm, papi, msr-safe, sionlib",
            missing=result.get("error", ""),
            path="/omnia/input/config/x86_64/rhel/10.0/slurm_custom.json",
        )


# =============================================================================
# TC-F03: LOCAL REPO SYNC — x86_64
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_local_repo_sync_x86_64(host):
    """
    TC-F03: Run local_repo.yml; verify all x86_64 benchmark tarballs appear
    in offline_repo/cluster/x86_64/rhel/10.0/tarball/.

    Acceptance criteria: AC-6.1.1, FR-03
    """
    log = TestLogger(TEST_NAMES["local_repo_sync_x86_64"])

    result = verify_local_repo_sync_x86_64(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["tarballs_missing"].format(
            arch="x86_64",
            base="/opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/tarball",
            missing=result.get("missing", []),
        )


# =============================================================================
# TC-F05: hpc_tools DIRECTORY CREATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_hpc_tools_dir_creation(host, x86_64_node_ip):
    """
    TC-F05: Run provision.yml; verify hpc_tools/ directory created with one
    subdirectory per benchmark tool; permissions set to 0755.

    Acceptance criteria: AC-6.1.1, VC-001, BL-008
    """
    log = TestLogger(TEST_NAMES["hpc_tools_dir_creation"])

    result = verify_hpc_tools_dir_creation(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["tool_dirs_missing"].format(
            expected="osu-micro-benchmarks, imb, likwid, geopm, papi, msr-safe, sionlib",
            missing=result.get("missing", []),
        )


# =============================================================================
# TC-F06: PARALLEL COPY — x86_64 ARTIFACTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_x86_64_artifact_copy(host, x86_64_node_ip):
    """
    TC-F06: Run provision.yml; verify all x86_64 source tarballs copied to
    hpc_tools/<tool>/; only declared tools are staged; undeclared tools absent.

    Acceptance criteria: AC-6.1.1, VC-001, VC-003, BL-009
    """
    log = TestLogger(TEST_NAMES["parallel_copy_x86_64"])

    result = verify_x86_64_artifact_copy(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["artifacts_missing_x86_64"].format(
            missing=result.get("missing", [])
        )


# =============================================================================
# TC-F08: msr-safe x86_64-ONLY STAGING
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_msr_safe_x86_64_only(host, x86_64_node_ip):
    """
    TC-F08: Declare msr-safe only for x86_64; run full provisioning; verify
    msr-safe present in hpc_tools/msr-safe/ and absent from aarch64
    offline_repo path.

    Acceptance criteria: AC-6.2.1, BL-001, VC-002
    """
    log = TestLogger(TEST_NAMES["msr_safe_x86_64_only"])

    result = verify_msr_safe_x86_64_only(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["msr_safe_arch_violation"].format(
            details=result.get("error", "")
        )


# =============================================================================
# TC-F09: CONTAINER-FIRST GUIDANCE FOR HPL/HPL-MxP/STREAM
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_container_first_guidance(host, x86_64_node_ip):
    """
    TC-F09: Verify HPL/HPL-MxP/STREAM not declared as source artifacts;
    Container-First image (nvcr.io/nvidia/hpc-benchmarks:25.09) declared
    with type=image; pull_benchmarks.sh deployed to NFS scripts/.

    Acceptance criteria: BL-003, FR-08
    """
    log = TestLogger(TEST_NAMES["container_first_guidance"])

    result = verify_container_first_guidance(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["container_first_missing"]


# =============================================================================
# TC-F10: SOURCE-ONLY DELIVERY — NO PRE-COMPILATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_source_only_delivery(host):
    """
    TC-F10: Verify no compile/make/build commands in provisioning tasks;
    no pre-compiled binaries in hpc_tools/<tool>/ directories.

    Acceptance criteria: BL-002, FR-04
    """
    log = TestLogger(TEST_NAMES["source_only_delivery"])

    result = verify_source_only_delivery(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["compile_commands_found"].format(
            cmds=result.get("error", "")
        )


# =============================================================================
# TC-F11: PER-TOOL STAGING OUTCOME REPORT
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_per_tool_staging_report(host, x86_64_node_ip):
    """
    TC-F11: Run pull_benchmarks.sh on x86_64 node; verify per-tool staging
    report correctly shows:
    - Already-present tools → SKIPPED with [WARN] marker
    - Missing/deleted tools → DOWNLOADED with [SUCCESS] marker
    - Summary counts (Successful/Skipped/Failed) match individual results
    
    Test scenario: After initial staging, if a tool directory is deleted and
    script re-run, that tool should be downloaded while others are skipped.

    Acceptance criteria: AC-6.4.1, AC-6.4.4, VC-006, VC-010
    """
    log = TestLogger(TEST_NAMES["per_tool_staging_report"])

    result = verify_per_tool_staging_report(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["per_tool_report_missing"]


# =============================================================================
# TC-F13: END-TO-END PROVISIONING — x86_64
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(13)
def test_e2e_provisioning_x86_64(host, x86_64_node_ip):
    """
    TC-F13: Run full x86_64 pipeline (local_repo.yml → provision.yml);
    verify JSON declaration, offline repo sync, hpc_tools directories,
    artifact staging, and NFS accessibility from an x86_64 node.

    Acceptance criteria: AC-6.1.1, FR-01
    """
    log = TestLogger(TEST_NAMES["e2e_provisioning_x86_64"])

    result = verify_e2e_provisioning_x86_64(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["e2e_x86_64_failed"].format(
            details=result.get("error", "")
        )


# =============================================================================
# TC-F15: NFS ACCESSIBILITY FROM CLUSTER NODES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(15)
def test_nfs_accessibility(host, x86_64_node_ip):
    """
    TC-F15: Verify /hpc_tools NFS is mounted and all benchmark tool
    directories are accessible from an x86_64 cluster node; verify source
    tarball is readable.

    Acceptance criteria: AC-6.1.1, VC-008
    """
    log = TestLogger(TEST_NAMES["nfs_accessibility"])

    result = verify_nfs_accessibility(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["nfs_not_accessible"].format(
            ip=x86_64_node_ip
        )


# =============================================================================
# TC-F16: AIR-GAPPED STAGING COMPLIANCE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(16)
def test_airgapped_staging(host):
    """
    TC-F16: Disable external network on OIM; run local_repo.yml and
    provision.yml; verify staging completes from local repo only; no external
    network calls logged.

    Acceptance criteria: BL-007, AC-6.1.4
    """
    log = TestLogger(TEST_NAMES["airgapped_staging"])

    result = verify_airgapped_staging(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["airgap_failed"]


# =============================================================================
# TC-F17: PROVISIONING IDEMPOTENCY (alias for TC-I01)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(17)
def test_provisioning_idempotency(host):
    """
    TC-F17: Run provision.yml twice; verify hpc_tools/ structure identical;
    no duplicate directories; Ansible reports changed=0 on second run.

    Acceptance criteria: BL-005, AC-6.1.3
    """
    log = TestLogger(TEST_NAMES["provisioning_idempotency"])

    result = verify_dir_creation_idempotency(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["idempotency_failed"].format(
            details=result.get("error", "")
        )


# =============================================================================
# TC-F18: POST-STAGING VALIDATION CHECKS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(18)
def test_post_staging_validation(host, x86_64_node_ip):
    """
    TC-F18: After provisioning, run post-staging validation; verify all
    required benchmark directories reported as present; missing directory
    triggers warning log.

    Acceptance criteria: SB-006, FR-01
    """
    log = TestLogger(TEST_NAMES["post_staging_validation"])

    result = verify_post_staging_validation(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["tool_dirs_missing"].format(
            expected="osu-micro-benchmarks, imb, likwid, geopm, papi, msr-safe, sionlib",
            missing=result.get("missing", []),
        )


# =============================================================================
# TC-I01: DIRECTORY CREATION IDEMPOTENCY
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(19)
def test_dir_creation_idempotency(host):
    """
    TC-I01: Run hpc_tools directory creation task twice; verify directory
    structure identical; no Ansible changes on second run.

    Acceptance criteria: BL-005, AC-6.1.3
    """
    log = TestLogger(TEST_NAMES["dir_creation_idempotency"])

    result = verify_dir_creation_idempotency(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["idempotency_failed"].format(
            details=result.get("error", "")
        )


# =============================================================================
# TC-I02: ARTIFACT STAGING IDEMPOTENCY AND RE-RUN RECOVERY
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(20)
def test_artifact_staging_idempotency(host):
    """
    TC-I02: Stage artifacts; re-run provision.yml; verify artifact checksums
    identical; no stale content; re-run after missing tool is added stages
    it without disturbing other tools.

    Acceptance criteria: BL-005, AC-6.1.3
    """
    log = TestLogger(TEST_NAMES["artifact_staging_idempotency"])

    result = verify_artifact_staging_idempotency(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["idempotency_failed"].format(
            details=result.get("error", "")
        )


# =============================================================================
# TC-C01: RHEL 10.x OS COMPATIBILITY
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(21)
def test_rhel_compatibility(host, x86_64_node_ip):
    """
    TC-C01: Verify target cluster node is running RHEL 10.x; staging completes
    without OS-related errors.

    Acceptance criteria: VC-007
    """
    log = TestLogger(TEST_NAMES["rhel_compatibility"])

    result = verify_rhel_compatibility(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["rhel_version_mismatch"].format(
            ip=x86_64_node_ip,
            version=result.get("os_version", "unknown"),
        )


# =============================================================================
# TC-RT01: CUDA EXISTING FLOW UNAFFECTED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(23)
def test_cuda_flow_unaffected(host, x86_64_node_ip):
    """
    TC-RT01: Run benchmark staging on top of a provisioned system; verify
    /hpc_tools/cuda/ path and nvidia-smi output unchanged.

    Acceptance criteria: AC-6.3.2
    """
    log = TestLogger(TEST_NAMES["cuda_flow_unaffected"])

    result = verify_cuda_flow_unaffected(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["cuda_path_modified"]


# =============================================================================
# TC-RT02: NVHPC SDK EXISTING FLOW UNAFFECTED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(24)
def test_nvhpc_flow_unaffected(host, x86_64_node_ip):
    """
    TC-RT02: Run benchmark staging; verify /hpc_tools/nvidia_sdk/ path and
    NVIDIA HPC SDK environment unchanged.
    """
    log = TestLogger(TEST_NAMES["nvhpc_flow_unaffected"])

    result = verify_nvhpc_flow_unaffected(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["nvhpc_path_modified"]


# =============================================================================
# TC-RT03: CONTAINER IMAGE DOWNLOAD FLOW UNAFFECTED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(25)
def test_container_image_flow_unaffected(host, x86_64_node_ip):
    """
    TC-RT03: Run benchmark staging; verify /hpc_tools/container_images/,
    download_container_image.sh, and container_image.list are unmodified.
    """
    log = TestLogger(TEST_NAMES["container_image_flow"])

    result = verify_container_image_flow_unaffected(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["container_images_modified"]


# =============================================================================
# TC-RT04: OpenMPI/UCX CONFIGURATION UNAFFECTED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(26)
def test_openmpi_unaffected(host, x86_64_login_compiler_ip):
    """
    TC-RT04: Run benchmark staging; verify mpirun --version and OpenMPI/UCX
    library paths and environment variables unchanged on login/compiler node.
    
    Note: mpirun is only available on login/compiler nodes, not compute nodes.

    Acceptance criteria: AC-6.3.4
    """
    log = TestLogger(TEST_NAMES["openmpi_unaffected"])

    result = verify_openmpi_unaffected(host, x86_64_login_compiler_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["openmpi_env_changed"]


# =============================================================================
# TC-RT05: EXISTING hpc_tools DIRECTORY STRUCTURE PRESERVED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(27)
def test_existing_hpc_dirs_preserved(host, x86_64_node_ip):
    """
    TC-RT05: Record pre-existing hpc_tools/ subdirectories before benchmark
    staging; after staging, verify none removed or modified.

    Acceptance criteria: AC-6.3.1, VC-004
    """
    log = TestLogger(TEST_NAMES["existing_hpc_dirs_preserved"])

    result = verify_existing_hpc_dirs_preserved(host, x86_64_node_ip)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["existing_dirs_modified"].format(
            dir=result.get("error", "")
        )


# =============================================================================
# TC-RT06: EMPTY BENCHMARK DECLARATION — NO NEW DIRECTORIES CREATED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(28)
def test_empty_declaration_no_new_dirs(host):
    """
    TC-RT06: Use empty slurm_custom.json; run provision.yml; verify no new
    benchmark subdirectories created under hpc_tools/.

    Acceptance criteria: AC-6.3.3
    """
    log = TestLogger(TEST_NAMES["empty_declaration"])

    result = verify_empty_declaration_no_new_dirs(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["new_dirs_on_empty"]


# =============================================================================
# TC-P01: STAGING DURATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(29)
def test_staging_duration(host):
    """
    TC-P01: Measure elapsed time for full benchmark tool set staging.
    Target: ≤ 15 minutes (900 seconds).

    Acceptance criteria: BSpec §6.1.6
    """
    log = TestLogger(TEST_NAMES["staging_duration"])

    result = measure_staging_duration(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["staging_too_slow"].format(
            target=900,
            actual=result.get("duration_secs", "unknown"),
        )


# =============================================================================
# TC-P02: STAGING OVERHEAD
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(30)
def test_staging_overhead(host):
    """
    TC-P02: Verify benchmark staging adds ≤ 10% overhead to total
    provisioning time.

    Acceptance criteria: BSpec §6.1.6
    """
    log = TestLogger(TEST_NAMES["staging_overhead"])

    result = measure_staging_overhead(host)

    if result["success"]:
        log.passed(result["details"])
    else:
        log.failed(result["error"])
        assert result["success"], TEST_ASSERT_MSGS["overhead_too_high"].format(
            target=10,
            actual=result.get("overhead_pct", "unknown"),
        )
