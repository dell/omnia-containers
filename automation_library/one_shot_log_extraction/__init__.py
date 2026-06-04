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
One-Shot Log Extraction Automation Module

Verification functions for one-shot combined log extraction from Kubernetes
and Slurm cluster nodes. Covers:
  - Collection invocation and workspace creation
  - Source collection with warning accumulation
  - Metadata synthesis and validation
  - Bundle construction with deterministic naming
  - Integrity hash generation and verification
  - Error handling (permissions, unreachable nodes, archive failures)
  - Idempotency and collection mode compatibility

Spec: TCASES-LOGEX-2026-001 v1.0.0
"""

from .functions import (
    execute_log_collection,
    verify_collection_started,
    get_workspace_directory,
    verify_workspace_created,
    get_bundle_path,
    verify_bundle_created,
    verify_bundle_name_format,
    extract_bundle,
    list_bundle_contents,
    verify_bundle_contains_file,
    read_metadata,
    verify_metadata_exists,
    verify_metadata_valid_json,
    verify_metadata_required_fields,
    verify_metadata_warning_entries,
    verify_warning_message_format,
    compute_sha256,
    verify_hash_format,
    verify_hash_in_output,
    verify_hash_match,
    verify_output_contains_path,
    verify_path_is_absolute,
    verify_warning_summary_in_output,
    set_directory_permissions,
    verify_not_writable_error,
    verify_archive_failure_error,
    verify_unreachable_node_warning,
    verify_missing_source_warning,
    create_temp_test_files,
    create_stale_test_file,
    cleanup_test_files,
    fill_disk_space,
    free_disk_space,
    get_bundle_content_checksum,
    compare_bundle_contents,
    cleanup_workspace,
    cleanup_bundle,
)
from .vars import (
    LOG_COLLECTION_COMMAND,
    LOG_COLLECTION_CURATED_MODE,
    COLLECT_PLAYBOOK_PATH,
    BUNDLE_NAME_PATTERN,
    OUTPUT_PATHS,
    METADATA_REQUIRED_FIELDS,
    WARNING_ENTRY_FIELDS,
    COLLECTION_MODES,
    SHA256_CONFIG,
    TIMEOUTS,
    EXIT_CODES,
    WARNING_PATTERNS,
)
from .messages import TEST_NAMES, LOG_MSGS, ASSERT_MSGS, ERROR_MSGS

__all__ = [
    "execute_log_collection",
    "verify_collection_started",
    "get_workspace_directory",
    "verify_workspace_created",
    "get_bundle_path",
    "verify_bundle_created",
    "verify_bundle_name_format",
    "extract_bundle",
    "list_bundle_contents",
    "verify_bundle_contains_file",
    "read_metadata",
    "verify_metadata_exists",
    "verify_metadata_valid_json",
    "verify_metadata_required_fields",
    "verify_metadata_warning_entries",
    "verify_warning_message_format",
    "compute_sha256",
    "verify_hash_format",
    "verify_hash_in_output",
    "verify_hash_match",
    "verify_output_contains_path",
    "verify_path_is_absolute",
    "verify_warning_summary_in_output",
    "set_directory_permissions",
    "verify_not_writable_error",
    "verify_archive_failure_error",
    "verify_unreachable_node_warning",
    "verify_missing_source_warning",
    "create_temp_test_files",
    "create_stale_test_file",
    "cleanup_test_files",
    "fill_disk_space",
    "free_disk_space",
    "get_bundle_content_checksum",
    "compare_bundle_contents",
    "cleanup_workspace",
    "cleanup_bundle",
    "LOG_COLLECTION_COMMAND",
    "LOG_COLLECTION_CURATED_MODE",
    "COLLECT_PLAYBOOK_PATH",
    "BUNDLE_NAME_PATTERN",
    "OUTPUT_PATHS",
    "METADATA_REQUIRED_FIELDS",
    "WARNING_ENTRY_FIELDS",
    "COLLECTION_MODES",
    "SHA256_CONFIG",
    "TIMEOUTS",
    "EXIT_CODES",
    "WARNING_PATTERNS",
    "TEST_NAMES",
    "LOG_MSGS",
    "ASSERT_MSGS",
    "ERROR_MSGS",
]
