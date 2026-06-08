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

"""One-shot log extraction functions package."""
# pylint: disable=duplicate-code

from .one_shot_log_extraction_func import (
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
]
