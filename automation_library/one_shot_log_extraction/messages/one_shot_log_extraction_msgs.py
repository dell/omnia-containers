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
One Shot Log Extraction Automation - Messages.

Contains all user-facing messages for one-shot log extraction tests.

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

from typing import Dict

# =============================================================================
# TEST NAMES - Maps to TC-IDs
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    # Functional Tests
    "tcf01_collection_invocation": "TC-F01: One-Shot Collection Invocation",
    "tcf02_source_collection": "TC-F02: Source Collection and Warning Accumulation",
    "tcf03_metadata_synthesis": "TC-F03: Metadata Synthesis and Inclusion",
    "tcf04_bundle_construction": "TC-F04: Bundle Construction with Deterministic Naming",
    "tcf05_hash_generation": "TC-F05: Integrity Hash Generation",
    "tcf06_completion_output": "TC-F06: User-Facing Completion Output",
    
    # Negative/Error Tests
    "tce01_output_not_writable": "TC-E01: Output Directory Not Writable",
    "tce02_unreachable_node": "TC-E02: Unreachable Node - Collection Continues with Warning",
    "tce03_missing_sources": "TC-E03: Missing Source Files - Warning Emitted",
    "tce04_archive_failure": "TC-E04: Archive Generation Failure",
    
    # Idempotency Tests
    "tci01_idempotency": "TC-I01: Collection Command Idempotency",
    
    # Compatibility Tests
    "tcc01_curated_mode": "TC-C01: Curated Support Mode - Exclude Temporary/Stale Logs",
    "tcc02_full_mode": "TC-C02: Full Collection Mode - Include All Logs",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

LOG_MSGS: Dict[str, str] = {
    # Collection Invocation (TC-F01)
    "collection_started": "Log collection command started successfully",
    "collection_failed_start": "Log collection command failed to start",
    "workspace_created": "Workspace directory created: {workspace}",
    "workspace_not_created": "Workspace directory was not created",
    "runtime_context_resolved": "Runtime context resolved - identified {node_count} nodes",
    
    # Source Collection (TC-F02)
    "k8s_logs_collected": "Kubernetes log sources collected successfully",
    "slurm_logs_collected": "Slurm log sources collected successfully",
    "source_iteration_complete": "All configured sources processed",
    "warnings_recorded": "Warnings recorded: {count}",
    
    # Metadata (TC-F03)
    "metadata_generated": "Metadata JSON generated successfully",
    "metadata_missing": "Metadata file not found in workspace",
    "metadata_valid_json": "Metadata is valid JSON format",
    "metadata_invalid_json": "Metadata is not valid JSON",
    "metadata_field_present": "Metadata field '{field}' is present",
    "metadata_field_missing": "Metadata field '{field}' is missing",
    
    # Bundle Construction (TC-F04)
    "bundle_created": "Bundle archive created: {bundle}",
    "bundle_not_created": "Bundle archive was not created",
    "bundle_name_valid": "Bundle filename matches expected format",
    "bundle_name_invalid": "Bundle filename does not match expected format: {name}",
    "bundle_readable": "Bundle archive is readable",
    "bundle_corrupted": "Bundle archive is corrupted or unreadable",
    "bundle_contents_valid": "Bundle contains expected logs and metadata",
    
    # Hash Generation (TC-F05)
    "hash_generated": "SHA256 hash generated: {hash}",
    "hash_not_generated": "SHA256 hash was not generated",
    "hash_format_valid": "Hash format is valid (64-character hex)",
    "hash_format_invalid": "Hash format is invalid: {hash}",
    "hash_match": "Generated hash matches independent recomputation",
    "hash_mismatch": "Hash mismatch - generated: {generated}, computed: {computed}",
    "hash_timeout": "Hash generation exceeded timeout ({timeout}s)",
    
    # Completion Output (TC-F06)
    "output_workspace_path": "Workspace path printed in output",
    "output_bundle_path": "Bundle path printed in output",
    "output_sha256": "SHA256 digest printed in output",
    "output_warning_summary": "Warning summary printed in output",
    "output_paths_absolute": "Paths are absolute and copy-paste ready",
    "output_paths_relative": "Paths are relative (expected absolute)",
    
    # Error: Output Not Writable (TC-E01)
    "output_not_writable_detected": "Output not writable error detected correctly",
    "output_not_writable_not_detected": "Expected 'not writable' error but command succeeded",
    "no_partial_artifacts": "No partial artifacts created",
    "partial_artifacts_found": "Partial artifacts found when none expected",
    "permissions_restored": "Output directory permissions restored",
    
    # Error: Unreachable Node (TC-E02)
    "unreachable_warning_emitted": "Warning emitted for unreachable node: {node} ({ip})",
    "collection_continued": "Collection continued despite unreachable node",
    "collection_aborted": "Collection aborted unexpectedly",
    "available_logs_collected": "Logs from reachable nodes collected successfully",
    
    # Error: Missing Sources (TC-E03)
    "missing_source_warning": "Warning emitted for missing source: {source} on {node}",
    "missing_source_no_warning": "No warning emitted for missing source",
    
    # Error: Archive Failure (TC-E04)
    "archive_failure_detected": "Archive failure error detected correctly",
    "archive_failure_not_detected": "Expected archive failure error but command succeeded",
    "disk_space_freed": "Disk space freed successfully",
    
    # Idempotency (TC-I01)
    "first_run_complete": "First collection run completed",
    "second_run_complete": "Second collection run completed",
    "bundles_different_names": "Bundle filenames differ (as expected - different timestamps)",
    "bundles_same_names": "Bundle filenames are identical (unexpected)",
    "contents_identical": "Bundle contents identical (excluding timestamp)",
    "contents_differ": "Bundle contents differ unexpectedly",
    
    # Compatibility: Curated Mode (TC-C01)
    "curated_mode_active": "Curated support mode is active",
    "temp_files_excluded": "Temporary files correctly excluded from bundle",
    "temp_files_included": "Temporary files incorrectly included in bundle",
    "stale_logs_excluded": "Stale logs correctly excluded from bundle",
    "stale_logs_included": "Stale logs incorrectly included in bundle",
    
    # Compatibility: Full Mode (TC-C02)
    "full_mode_active": "Full collection mode is active",
    "all_files_included": "All files correctly included in bundle",
    "files_missing": "Expected files missing from bundle",
}

# =============================================================================
# ASSERT MESSAGES
# =============================================================================

ASSERT_MSGS: Dict[str, str] = {
    # Collection
    "assert_collection_started": "Collection command should start without errors",
    "assert_workspace_created": "Workspace directory should be created",
    "assert_runtime_resolved": "Runtime context should be resolved",
    
    # Sources
    "assert_k8s_collected": "Kubernetes logs should be collected",
    "assert_slurm_collected": "Slurm logs should be collected",
    "assert_sources_complete": "All sources should be processed",
    
    # Metadata
    "assert_metadata_exists": "Metadata JSON should exist in workspace",
    "assert_metadata_valid": "Metadata should be valid JSON",
    "assert_metadata_fields": "Metadata should contain all required fields",
    
    # Bundle
    "assert_bundle_created": "Bundle archive should be created",
    "assert_bundle_name_format": (
        "Bundle name should match format: "
        "omnia-logs-<id>-<timestamp>.tar.gz"
    ),
    "assert_bundle_readable": "Bundle should be readable and extractable",
    "assert_bundle_contents": "Bundle should contain collected logs and metadata",
    
    # Hash
    "assert_hash_generated": "SHA256 hash should be generated",
    "assert_hash_format": "Hash should be 64-character hexadecimal",
    "assert_hash_match": "Generated hash should match independent computation",
    "assert_hash_time": "Hash should be computed within {timeout} seconds",
    
    # Output
    "assert_workspace_output": "Workspace path should be printed",
    "assert_bundle_output": "Bundle path should be printed",
    "assert_hash_output": "SHA256 should be printed",
    "assert_warnings_output": "Warning summary should be printed",
    "assert_paths_absolute": "Paths should be absolute",
    
    # Errors
    "assert_not_writable_error": "Command should fail with 'not writable' error",
    "assert_no_artifacts": "No partial artifacts should be created",
    "assert_unreachable_warning": "Warning should be emitted for unreachable node",
    "assert_missing_warning": "Warning should be emitted for missing source",
    "assert_archive_error": "Command should fail with archive error",
    
    # Idempotency
    "assert_different_names": "Bundle filenames should differ (timestamps)",
    "assert_same_contents": "Bundle contents should be identical",
    
    # Modes
    "assert_temp_excluded": "Temporary files should be excluded in curated mode",
    "assert_stale_excluded": "Stale logs should be excluded in curated mode",
    "assert_all_included": "All files should be included in full mode",
}

# =============================================================================
# ERROR MESSAGES
# =============================================================================

ERROR_MSGS: Dict[str, str] = {
    "output_not_writable": "Output directory not writable: {path}",
    "archive_failed": "Archive generation failed: {reason}",
    "node_unreachable": (
        "Node {hostname} ({ip}) unreachable; "
        "continuing collection for remaining nodes."
    ),
    "source_not_found": "Source file {source} not found on node {node}",
    "disk_full": "No space left on device",
    "permission_denied": "Permission denied: {path}",
}
