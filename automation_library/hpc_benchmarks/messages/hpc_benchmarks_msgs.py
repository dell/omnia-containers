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
HPC Benchmarks Automation - Messages.

All user-facing test names, log messages, and assertion messages for HPC
Benchmark staging and validation tests.
Spec: TSPEC-HPCBENCH-2026-001 v1.0.0
"""

from typing import Dict


# =============================================================================
# TEST NAMES  (shown in test report header)
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    # Functional
    "x86_64_json_parsing":        "TC-F01: x86_64 JSON Declaration Parsing",
    "aarch64_json_parsing":       "TC-F02: aarch64 JSON Declaration Parsing",
    "local_repo_sync_x86_64":     "TC-F03: Local Repo Sync — x86_64",
    "local_repo_sync_aarch64":    "TC-F04: Local Repo Sync — aarch64",
    "hpc_tools_dir_creation":     "TC-F05: hpc_tools Directory Creation",
    "parallel_copy_x86_64":       "TC-F06: Parallel Copy — x86_64 Artifacts",
    "parallel_copy_aarch64":      "TC-F07: Parallel Copy — aarch64 Artifacts",
    "msr_safe_x86_64_only":       "TC-F08: msr-safe x86_64-Only Staging",
    "container_first_guidance":   "TC-F09: Container-First Guidance for HPL/HPL-MxP/STREAM",
    "source_only_delivery":       "TC-F10: Source-Only Delivery — No Pre-Compilation",
    "per_tool_staging_report":    "TC-F11: Per-Tool Staging Outcome Report",
    "staging_summary_count":      "TC-F12: Staging Summary Count",
    "e2e_provisioning_x86_64":    "TC-F13: End-to-End Provisioning — x86_64",
    "e2e_provisioning_aarch64":   "TC-F14: End-to-End Provisioning — aarch64",
    "nfs_accessibility":          "TC-F15: NFS Accessibility from Cluster Nodes",
    "airgapped_staging":          "TC-F16: Air-Gapped Staging Compliance",
    "provisioning_idempotency":   "TC-F17: Provisioning Idempotency",
    "post_staging_validation":    "TC-F18: Post-Staging Validation Checks",
    # Idempotency
    "dir_creation_idempotency":   "TC-I01: Directory Creation Idempotency",
    "artifact_staging_idempotency": "TC-I02: Artifact Staging Idempotency and Re-Run Recovery",
    # Compatibility
    "rhel_compatibility":         "TC-C01: RHEL 10.x OS Compatibility",
    "arch_independence":          "TC-C02: Architecture Independence — Cross-Arch Failure Isolation",
    # Regression
    "cuda_flow_unaffected":       "TC-RT01: CUDA Existing Flow Unaffected",
    "nvhpc_flow_unaffected":      "TC-RT02: NVHPC SDK Existing Flow Unaffected",
    "container_image_flow":       "TC-RT03: Container Image Download Flow Unaffected",
    "openmpi_unaffected":         "TC-RT04: OpenMPI/UCX Configuration Unaffected",
    "existing_hpc_dirs_preserved": "TC-RT05: Existing hpc_tools Directory Structure Preserved",
    "empty_declaration":          "TC-RT06: Empty Benchmark Declaration — No New Directories Created",
    # Performance
    "staging_duration":           "TC-P01: Staging Duration — Full Tool Set (10 Tools)",
    "staging_overhead":           "TC-P02: Staging Overhead on Overall Provisioning",
    "report_availability":        "TC-P03: Staging Outcome Report Availability",
    # Negative / Error
    "missing_artifact_skip":      "TC-E01: Missing Local Repo Artifact — Graceful Skip",
    "malformed_json":             "TC-E02: Malformed JSON — Parse Failure",
    "msrsafe_aarch64_error":      "TC-E03: msr-safe Declared for aarch64 — Validation Error",
    "geopm_aarch64_warning":      "TC-E04: GEOPM aarch64 Declaration — Warning Emitted",
    "nfs_unavailable":            "TC-E05: NFS Unavailable During Staging",
    "unsupported_pkg_type":       "TC-E06: Unsupported Package Type Declaration",
}


# =============================================================================
# LOG MESSAGES  (shown during test execution)
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # JSON parsing
    "json_read_ok":             "slurm_custom.json read successfully for {arch}",
    "json_parse_ok":            "JSON parsed without schema errors for {arch}",
    "json_parse_fail":          "Failed to parse slurm_custom.json for {arch}: {error}",
    "packages_found":           "All expected benchmark packages found for {arch}: {pkgs}",
    "package_missing":          "Expected benchmark package missing in {arch} JSON: {pkg}",
    "msr_safe_present_x86_64":  "msr-safe correctly declared in x86_64 JSON",
    "msr_safe_absent_aarch64":  "msr-safe correctly absent from aarch64 JSON",
    "msr_safe_wrongly_present": "msr-safe found in aarch64 JSON — should be absent",
    "container_first_declared": "Container-First image declared: {pkg}:{tag}",
    "type_validation_ok":       "Package type validation passed for {arch}",
    "type_validation_fail":     "Package type error for {pkg}: expected {expected}, got {actual}",

    # Local repo
    "offline_repo_found":       "Offline repo tarball directory found for {arch}",
    "tarball_dir_found":        "Tarball directory exists: {path}",
    "tarball_dir_missing":      "Tarball directory missing for {pkg}: {path}",
    "all_tarballs_present":     "All declared benchmark tarballs present for {arch}",
    "tarballs_missing":         "Missing tarball directories for {arch}: {missing}",

    # hpc_tools directories
    "tool_dir_created":         "hpc_tools/{tool}/ directory exists",
    "tool_dir_missing":         "hpc_tools/{tool}/ directory not found",
    "all_tool_dirs_created":    "All benchmark tool directories present under hpc_tools/",
    "tool_dirs_missing":        "Missing benchmark tool directories: {missing}",

    # Artifact copy
    "artifacts_copied":         "Artifacts copied to hpc_tools/{tool}/ for {arch}",
    "artifacts_missing":        "No artifacts found in hpc_tools/{tool}/ for {arch}",
    "only_declared_staged":     "Only declared tools are staged — undeclared tools absent",
    "undeclared_tool_found":    "Undeclared tool directory found: {tool}",

    # msr-safe arch boundary
    "msr_safe_in_x86_64_path":  "msr-safe artifacts present in hpc_tools/msr-safe/ (x86_64)",
    "msr_safe_absent_aarch64_path": "msr-safe correctly absent from aarch64 offline_repo",
    "msr_safe_arch_boundary_ok": "msr-safe arch boundary enforced correctly",

    # Container-First
    "container_first_no_source": "HPL/HPL-MxP/STREAM not declared as source artifacts — correct",
    "container_first_guidance_present": "Container-First pull command guidance present in output",
    "container_first_source_found": "HPL/HPL-MxP/STREAM incorrectly declared as source artifact",

    # Source-only
    "no_compile_commands":      "No compile/make/build commands found in provisioning output",
    "compile_command_found":    "Unexpected compile command found: {cmd}",

    # Staging report
    "per_tool_report_present":  "Per-tool staging outcome report present in provisioning output",
    "per_tool_report_missing":  "Per-tool staging outcome report not found in provisioning output",
    "skipped_tool_named":       "Skipped tool named with reason in report: {tool}",
    "recovery_guidance_present": "Recovery guidance present in output for skipped tools",
    "summary_count_present":    "Staging summary count present: declared={declared}, staged={staged}, skipped={skipped}, failed={failed}",
    "summary_count_missing":    "Staging summary count not found in provisioning output",

    # NFS accessibility
    "nfs_mount_ok":             "/hpc_tools NFS mounted on node {ip}",
    "nfs_mount_fail":           "/hpc_tools not mounted on node {ip}",
    "tool_dir_accessible":      "hpc_tools/{tool}/ accessible from node {ip}",
    "tool_dir_not_accessible":  "hpc_tools/{tool}/ not accessible from node {ip}",
    "tarball_readable":         "Source tarball readable from NFS on node {ip}",

    # Air-gapped
    "airgap_staging_ok":        "Staging completed without external network access",
    "external_network_access":  "External network access detected during staging",

    # Idempotency
    "idempotency_no_changes":   "Second run produced 0 changes — idempotency confirmed",
    "idempotency_changes_found": "Second run showed changes — idempotency FAILED",
    "dirs_identical":           "hpc_tools/ directory structure identical after both runs",
    "dirs_differ":              "hpc_tools/ directory structure differs after re-run",

    # OS compatibility
    "rhel_version_ok":          "Node {ip} is RHEL {version} — compatible",
    "rhel_version_fail":        "Node {ip} OS version {version} does not meet RHEL 10.x requirement",

    # Arch independence
    "aarch64_unaffected":       "aarch64 staging unaffected by x86_64 error",
    "arch_cascade_failure":     "x86_64 error cascaded to aarch64 staging — unexpected",

    # Regression
    "cuda_path_ok":             "CUDA toolkit path /hpc_tools/cuda/ intact after benchmark staging",
    "nvhpc_path_ok":            "NVIDIA HPC SDK path /hpc_tools/nvidia_sdk/ intact",
    "container_images_ok":      "/hpc_tools/container_images/ unmodified after benchmark staging",
    "openmpi_env_ok":           "OpenMPI/UCX environment and library paths unchanged",
    "existing_dirs_preserved":  "All pre-existing hpc_tools/ subdirectories preserved",
    "existing_dir_modified":    "Pre-existing directory modified or missing: {dir}",
    "no_new_dirs_on_empty":     "No new benchmark directories created with empty declaration",
    "new_dirs_found_on_empty":  "Unexpected benchmark directories created: {dirs}",

    # Performance
    "staging_duration":         "Full benchmark staging completed in {secs}s (target: ≤{target}s)",
    "staging_overhead":         "Benchmark staging overhead: {pct}% (target: ≤{target}%)",
    "report_ready_in":          "Per-tool staging report appeared {secs}s after last copy (target: ≤{target}s)",

    # Negative
    "graceful_skip_ok":         "Missing artifact skipped gracefully; other tools staged normally",
    "abort_on_missing":         "Provisioning aborted instead of gracefully skipping missing tool",
    "malformed_json_blocked":   "Malformed JSON correctly blocked before ingestion",
    "malformed_json_not_blocked": "Malformed JSON was not caught before ingestion",
    "msrsafe_aarch64_blocked":  "msr-safe for aarch64 blocked with validation error",
    "msrsafe_aarch64_allowed":  "msr-safe was not blocked for aarch64 — enforcement missing",
    "geopm_warning_emitted":    "GEOPM aarch64 warning emitted in provisioning output",
    "geopm_warning_missing":    "GEOPM aarch64 warning not found in provisioning output",
    "nfs_fail_clear_error":     "NFS unavailability reported with clear error message",
    "nfs_fail_silent":          "NFS failure did not produce a clear error message",
    "unsupported_type_blocked": "Unsupported package type rejected before staging",
    "unsupported_type_allowed": "Unsupported package type was not rejected",
}


# =============================================================================
# ASSERTION MESSAGES  (shown on test failure)
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "no_cluster_nodes": (
        "No cluster nodes found in PXE mapping.\n"
        "Ensure cluster nodes are provisioned and listed in pxe_mapping_file.csv."
    ),
    "no_x86_64_nodes": (
        "No x86_64 cluster nodes found (functional group: slurm_node_x86_64).\n"
        "Ensure x86_64 nodes are provisioned and listed in pxe_mapping_file.csv."
    ),
    "no_aarch64_nodes": (
        "No aarch64 cluster nodes found (functional group: slurm_node_aarch64).\n"
        "Ensure aarch64 nodes are provisioned and listed in pxe_mapping_file.csv."
    ),
    "json_read_failed": (
        "Cannot read slurm_custom.json for {arch}.\n"
        "Expected: File at {path}\n"
        "Fix: Verify Omnia codebase is mounted at /omnia inside the container."
    ),
    "json_parse_failed": (
        "JSON parse error in slurm_custom.json for {arch}.\n"
        "Expected: Valid JSON with slurm_custom.cluster entries.\n"
        "Actual: {error}\n"
        "Fix: Correct JSON syntax in {path}"
    ),
    "packages_missing": (
        "Missing benchmark package declarations in {arch} slurm_custom.json.\n"
        "Expected: {expected}\n"
        "Missing: {missing}\n"
        "Fix: Add missing entries to {path}"
    ),
    "msr_safe_absent_x86_64": (
        "msr-safe not declared in x86_64 slurm_custom.json.\n"
        "Expected: msr-safe entry with type=tarball.\n"
        "Fix: Add msr-safe tarball declaration to {path}"
    ),
    "msr_safe_present_aarch64": (
        "msr-safe incorrectly declared in aarch64 slurm_custom.json.\n"
        "Expected: msr-safe absent from aarch64 declarations.\n"
        "Fix: Remove msr-safe entry from {path}\n"
        "Ref: BL-001, AC-6.2.1"
    ),
    "container_first_missing": (
        "Container-First image not declared in slurm_custom.json.\n"
        "Expected: nvcr.io/nvidia/hpc-benchmarks entry with type=image.\n"
        "Fix: Add container-first image declaration to {path}"
    ),
    "tarballs_missing": (
        "Benchmark tarballs missing in offline_repo for {arch}.\n"
        "Expected: Tarball directories under {base}\n"
        "Missing: {missing}\n"
        "Fix: Run local_repo.yml with correct benchmark declarations."
    ),
    "tool_dirs_missing": (
        "Benchmark tool directories not created under hpc_tools/.\n"
        "Expected: {expected}\n"
        "Missing: {missing}\n"
        "Fix: Run provision.yml to create hpc_tools benchmark directories."
    ),
    "artifacts_missing_x86_64": (
        "No artifacts found in hpc_tools/ for x86_64 tools.\n"
        "Expected: Source tarballs copied from offline_repo for each declared tool.\n"
        "Missing tools: {missing}\n"
        "Fix: Verify offline_repo is populated and run provision.yml."
    ),
    "artifacts_missing_aarch64": (
        "No artifacts found in hpc_tools/ for aarch64 tools.\n"
        "Expected: Source tarballs copied from offline_repo for each declared aarch64 tool.\n"
        "Missing tools: {missing}\n"
        "Fix: Verify aarch64 offline_repo is populated and run provision.yml."
    ),
    "msr_safe_arch_violation": (
        "msr-safe arch boundary violation detected.\n"
        "Expected: msr-safe present for x86_64; absent from aarch64 offline_repo.\n"
        "Actual: {details}\n"
        "Ref: BL-001, AC-6.2.1, VC-002"
    ),
    "container_first_source_declared": (
        "HPL/HPL-MxP/STREAM incorrectly declared as source artifact.\n"
        "Expected: No source declaration; Container-First guidance only.\n"
        "Ref: BL-003, TC-F09"
    ),
    "compile_commands_found": (
        "Compile/build commands detected in provisioning output.\n"
        "Expected: Omnia must not pre-compile any benchmark binary.\n"
        "Found: {cmds}\n"
        "Ref: BL-002, TC-F10"
    ),
    "per_tool_report_missing": (
        "Per-tool staging outcome report not found in provisioning output.\n"
        "Expected: Status (success/skipped/failed) for each declared tool.\n"
        "Fix: Check provisioning output for staging summary section.\n"
        "Ref: AC-6.4.1, TC-F11"
    ),
    "staging_summary_missing": (
        "Staging summary count not found in provisioning output.\n"
        "Expected: Summary with declared/staged/skipped/failed counts.\n"
        "Ref: AC-6.4.3, TC-F12"
    ),
    "e2e_x86_64_failed": (
        "End-to-end x86_64 provisioning failed.\n"
        "Expected: All x86_64 benchmark tool dirs and artifacts present.\n"
        "Details: {details}"
    ),
    "e2e_aarch64_failed": (
        "End-to-end aarch64 provisioning failed.\n"
        "Expected: All aarch64 benchmark tool dirs present; msr-safe absent.\n"
        "Details: {details}"
    ),
    "nfs_not_accessible": (
        "hpc_tools NFS share not accessible from node {ip}.\n"
        "Expected: /hpc_tools mounted and tool directories readable.\n"
        "Fix: Verify NFS mount: mount | grep /hpc_tools"
    ),
    "airgap_failed": (
        "Staging failed in air-gapped environment.\n"
        "Expected: Full staging from local repo without internet.\n"
        "Fix: Verify local repo is fully populated before provisioning."
    ),
    "idempotency_failed": (
        "Provisioning is not idempotent.\n"
        "Expected: Same hpc_tools/ structure after re-run; no duplicate dirs.\n"
        "Actual: {details}\n"
        "Ref: BL-005, AC-6.1.3"
    ),
    "rhel_version_mismatch": (
        "RHEL version requirement not met on {ip}.\n"
        "Expected: RHEL 10.x\n"
        "Actual: {version}\n"
        "Ref: VC-007, TC-C01"
    ),
    "arch_cascade_failure": (
        "x86_64 failure cascaded to aarch64 staging.\n"
        "Expected: aarch64 staging completes independently.\n"
        "Ref: BL-006, AC-6.2.4, TC-C02"
    ),
    "cuda_path_modified": (
        "CUDA toolkit path modified after benchmark staging.\n"
        "Expected: /hpc_tools/cuda/ unchanged.\n"
        "Ref: AC-6.3.2, TC-RT01"
    ),
    "nvhpc_path_modified": (
        "NVIDIA HPC SDK path modified after benchmark staging.\n"
        "Expected: /hpc_tools/nvidia_sdk/ unchanged.\n"
        "Ref: TC-RT02"
    ),
    "container_images_modified": (
        "/hpc_tools/container_images/ modified after benchmark staging.\n"
        "Expected: Container image directory unchanged.\n"
        "Ref: TC-RT03"
    ),
    "openmpi_env_changed": (
        "OpenMPI/UCX environment changed after benchmark staging.\n"
        "Expected: MPI execution results and environment unchanged.\n"
        "Ref: AC-6.3.4, TC-RT04"
    ),
    "existing_dirs_modified": (
        "Existing hpc_tools/ directories modified by benchmark staging.\n"
        "Expected: No modification to pre-existing subdirectories.\n"
        "Ref: AC-6.3.1, TC-RT05"
    ),
    "new_dirs_on_empty": (
        "New benchmark directories created despite empty declaration.\n"
        "Expected: No new benchmark dirs with empty slurm_custom.json.\n"
        "Ref: AC-6.3.3, TC-RT06"
    ),
    "staging_too_slow": (
        "Benchmark staging exceeded target duration.\n"
        "Expected: ≤{target}s\n"
        "Actual: {actual}s\n"
        "Ref: TC-P01, BSpec §6.1.6"
    ),
    "overhead_too_high": (
        "Benchmark staging overhead exceeds 10%.\n"
        "Expected: ≤{target}%\n"
        "Actual: {actual}%\n"
        "Ref: TC-P02, BSpec §6.1.6"
    ),
    "report_too_slow": (
        "Per-tool staging report not available within target time.\n"
        "Expected: ≤{target}s from end of last copy\n"
        "Actual: {actual}s\n"
        "Ref: TC-P03, BSpec §6.4.6"
    ),
    "graceful_skip_failed": (
        "Provisioning aborted due to missing artifact instead of skipping.\n"
        "Expected: Skipped tool logged with reason; other tools staged.\n"
        "Ref: AC-6.1.2, BL-004, TC-E01"
    ),
    "malformed_json_not_caught": (
        "Malformed JSON was not caught before ingestion.\n"
        "Expected: Clear parse error before any artifact ingestion.\n"
        "Ref: TC-E02"
    ),
    "msrsafe_aarch64_not_blocked": (
        "msr-safe for aarch64 was not blocked with validation error.\n"
        "Expected: Validation error before staging; other tools unaffected.\n"
        "Ref: AC-6.2.2, BL-001, TC-E03"
    ),
    "geopm_warning_not_emitted": (
        "GEOPM aarch64 warning not emitted.\n"
        "Expected: Operator-visible warning about limited aarch64 GEOPM support.\n"
        "Ref: AC-6.2.3, TC-E04"
    ),
    "nfs_error_not_clear": (
        "NFS unavailability did not produce a clear error message.\n"
        "Expected: Clear staging failure with NFS error logged.\n"
        "Ref: TC-E05"
    ),
    "unsupported_type_not_blocked": (
        "Unsupported package type was not rejected before staging.\n"
        "Expected: Validation error with specific message; other tools unaffected.\n"
        "Ref: FSpec §5.1.5, TC-E06"
    ),
}
