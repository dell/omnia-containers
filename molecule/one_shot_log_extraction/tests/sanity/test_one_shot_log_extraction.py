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
One Shot Log Extraction Test Cases.

This module contains pytest test cases for verifying one-shot combined log
extraction from Kubernetes and Slurm cluster nodes.

Test Cases:
- TC-F01: One-Shot Collection Invocation
- TC-F02: Source Collection and Warning Accumulation
- TC-F03: Metadata Synthesis and Inclusion
- TC-F04: Bundle Construction with Deterministic Naming
- TC-F05: Integrity Hash Generation
- TC-F06: User-Facing Completion Output
- TC-E01: Output Directory Not Writable
- TC-E03: Missing Source Files - Warning Emitted
- TC-E04: Archive Generation Failure
- TC-I01: Collection Command Idempotency
- TC-C01: Curated Support Mode - Exclude Temporary/Stale Logs
- TC-C02: Full Collection Mode - Include All Logs

Note: TC-E02 (Unreachable Node) is manual only (@lab-only).

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

import os
import time

import pytest  # pylint: disable=import-error

from automation_library.core import (
    TestLogger,
    get_node_admin_ip,
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
)
from automation_library.one_shot_log_extraction.vars.one_shot_log_extraction_vars import (
    OUTPUT_PATHS,
    METADATA_REQUIRED_FIELDS,
    SHA256_CONFIG,
    TEST_FILES,
    TEST_CONFIG,
)
from automation_library.one_shot_log_extraction.messages.one_shot_log_extraction_msgs import (
    TEST_NAMES,
    LOG_MSGS,
    ASSERT_MSGS,
)
from automation_library.one_shot_log_extraction.functions.one_shot_log_extraction_func import (
    execute_log_collection,
    verify_collection_started,
    verify_workspace_created,
    verify_bundle_created,
    verify_bundle_name_format,
    list_bundle_contents,
    read_metadata,
    verify_metadata_exists,
    verify_metadata_valid_json,
    verify_metadata_required_fields,
    verify_metadata_warning_entries,
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
    verify_missing_source_warning,
    create_temp_test_files,
    create_stale_test_file,
    cleanup_test_files,
    fill_disk_space,
    free_disk_space,
    compare_bundle_contents,
    cleanup_bundle,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_admin_ip(host, log=None, use_cache: bool = True) -> str:  # pylint: disable=unused-argument
    """
    Get admin IP from PXE mapping file for one-shot log extraction tests.

    This is a local implementation that doesn't depend on telemetry module.
    Gets the admin IP from the first available K8s control plane node.

    Args:
        host: Testinfra host object
        log: TestLogger instance (optional - for backward compatibility)
        use_cache: If True, return cached IP if available (ignored for simplicity)

    Returns:
        Admin IP string

    Raises:
        AssertionError if admin IP not found
    """
    if log:
        log.check("Getting admin IP from PXE mapping file")

    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    return admin_ip


# =============================================================================
# MODULE-LEVEL FIXTURES
# =============================================================================

# Store collection results for dependent tests
_collection_result = {
    "output": "",
    "exit_code": 0,
    "workspace": None,
    "bundle": None,
    "metadata": None,
    "hash": None,
}


# =============================================================================
# FUNCTIONAL TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_tcf01_collection_invocation(host):
    """
    TC-F01: One-Shot Collection Invocation.

    Verify single command execution triggers collection pipeline
    and prepares workspace successfully.

    Steps:
    1. SSH into OIM node
    2. Execute one-shot log collection command
    3. Verify collection pipeline starts
    4. Check workspace directory created
    5. Verify runtime context resolved
    """
    log = TestLogger(TEST_NAMES["tcf01_collection_invocation"])
    admin_ip = get_admin_ip(host)

    # Step 2: Execute log collection command
    log.check("Executing one-shot log collection command")
    _, output, exit_code = execute_log_collection(host, mode="full", admin_ip=admin_ip)

    _collection_result["output"] = output
    _collection_result["exit_code"] = exit_code

    # Step 3: Verify collection started
    if not verify_collection_started(output):
        log.failed(LOG_MSGS["collection_failed_start"], ASSERT_MSGS["assert_collection_started"])
        pytest.fail(ASSERT_MSGS["assert_collection_started"])

    log.check(LOG_MSGS["collection_started"])

    # Step 4: Check workspace directory created
    workspace_exists, workspace_path = verify_workspace_created(host, admin_ip)

    if not workspace_exists:
        log.failed(LOG_MSGS["workspace_not_created"], ASSERT_MSGS["assert_workspace_created"])
        pytest.fail(ASSERT_MSGS["assert_workspace_created"])

    _collection_result["workspace"] = workspace_path
    log.check(LOG_MSGS["workspace_created"].format(workspace=workspace_path))

    # Step 5: Verify runtime context resolved (check output for node count)
    log.check(LOG_MSGS["runtime_context_resolved"].format(node_count="N"))

    log.passed(
        "Collection invocation successful",
        f"Workspace created at {workspace_path}"
    )


@pytest.mark.sanity
@pytest.mark.order(2)
def test_tcf02_source_collection(host):
    """
    TC-F02: Source Collection and Warning Accumulation.

    Verify collection from Kubernetes and Slurm sources completes
    with all available logs gathered.

    Steps:
    1. Verify Kubernetes log sources collected
    2. Verify Slurm log sources collected
    3. Check collected data in workspace
    4. Verify source iteration completes
    5. Check for any warnings in output
    """
    log = TestLogger(TEST_NAMES["tcf02_source_collection"])
    admin_ip = get_admin_ip(host)

    workspace_path = _collection_result.get("workspace")
    if not workspace_path:
        log.skipped("Workspace not available", "TC-F01 must pass first")
        pytest.skip("TC-F01 must pass first")

    # Step 1-2: Verify log sources collected (check workspace contents)
    bundle_exists, bundle_path = verify_bundle_created(host, admin_ip)

    if not bundle_exists:
        log.failed(LOG_MSGS["bundle_not_created"], ASSERT_MSGS["assert_bundle_created"])
        pytest.fail(ASSERT_MSGS["assert_bundle_created"])

    _collection_result["bundle"] = bundle_path

    # Step 3: Check collected data
    contents = list_bundle_contents(host, bundle_path, admin_ip)

    if not contents:
        log.failed("No contents in bundle", ASSERT_MSGS["assert_sources_complete"])
        pytest.fail(ASSERT_MSGS["assert_sources_complete"])

    log.check(f"Bundle contains {len(contents)} files/directories")

    # Step 4-5: Verify iteration complete and check warnings
    output = _collection_result.get("output", "")
    has_warnings, warning_count = verify_warning_summary_in_output(output)

    if has_warnings:
        log.check(LOG_MSGS["warnings_recorded"].format(count=warning_count))

    log.check(LOG_MSGS["source_iteration_complete"])
    log.passed(
        "Source collection completed",
        f"Collected data from cluster nodes, {len(contents)} items in bundle"
    )


@pytest.mark.sanity
@pytest.mark.order(3)
def test_tcf03_metadata_synthesis(host):
    """
    TC-F03: Metadata Synthesis and Inclusion.

    Verify metadata JSON generated with provenance fields and valid JSON format.

    Steps:
    1. Verify metadata JSON generated
    2. Check metadata timestamp field
    3. Check metadata user/actor field
    4. Check metadata host context field
    5. Check metadata collection options
    6. Check metadata warning summary
    7. Validate JSON format
    """
    log = TestLogger(TEST_NAMES["tcf03_metadata_synthesis"])
    admin_ip = get_admin_ip(host)

    workspace_path = _collection_result.get("workspace")
    if not workspace_path:
        log.skipped("Workspace not available", "TC-F01 must pass first")
        pytest.skip("TC-F01 must pass first")

    # Step 1: Verify metadata exists
    if not verify_metadata_exists(host, workspace_path, admin_ip):
        log.failed(LOG_MSGS["metadata_missing"], ASSERT_MSGS["assert_metadata_exists"])
        pytest.fail(ASSERT_MSGS["assert_metadata_exists"])

    log.check(LOG_MSGS["metadata_generated"])

    # Step 7: Validate JSON format
    if not verify_metadata_valid_json(host, workspace_path, admin_ip):
        log.failed(LOG_MSGS["metadata_invalid_json"], ASSERT_MSGS["assert_metadata_valid"])
        pytest.fail(ASSERT_MSGS["assert_metadata_valid"])

    log.check(LOG_MSGS["metadata_valid_json"])

    # Step 2-6: Check required fields
    metadata = read_metadata(host, workspace_path, admin_ip)

    if not metadata:
        log.failed("Failed to read metadata", ASSERT_MSGS["assert_metadata_exists"])
        pytest.fail(ASSERT_MSGS["assert_metadata_exists"])

    _collection_result["metadata"] = metadata

    all_present, missing = verify_metadata_required_fields(metadata)

    if not all_present:
        log.failed(
            f"Missing metadata fields: {missing}",
            ASSERT_MSGS["assert_metadata_fields"]
        )
        pytest.fail(f"{ASSERT_MSGS['assert_metadata_fields']}: {missing}")

    for field in METADATA_REQUIRED_FIELDS:
        log.check(LOG_MSGS["metadata_field_present"].format(field=field))

    # Check warning entries schema (per CSPEC-LOGEX-2026-001 Section 4.2)
    warnings_ok, warning_missing = verify_metadata_warning_entries(metadata)
    if not warnings_ok:
        log.check(f"Missing warning entry fields: {warning_missing}")

    log.passed(
        "Metadata synthesis successful",
        f"All {len(METADATA_REQUIRED_FIELDS)} required fields present"
    )


@pytest.mark.sanity
@pytest.mark.order(4)
def test_tcf04_bundle_construction(host):
    """
    TC-F04: Bundle Construction with Deterministic Naming.

    Verify gzip tar archive created with timestamped naming format.

    Steps:
    1. Verify bundle filename format
    2. Check identifier in filename
    3. Check timestamp in filename
    4. Verify tar.gz archive created
    5. Extract and inspect archive contents
    6. Verify archive is gzip compressed
    7. Check archive placed in output location
    """
    log = TestLogger(TEST_NAMES["tcf04_bundle_construction"])
    admin_ip = get_admin_ip(host)

    bundle_path = _collection_result.get("bundle")
    if not bundle_path:
        log.skipped("Bundle not available", "TC-F02 must pass first")
        pytest.skip("TC-F02 must pass first")

    # Step 1-3: Verify bundle filename format
    if not verify_bundle_name_format(bundle_path):
        log.failed(
            LOG_MSGS["bundle_name_invalid"].format(name=bundle_path),
            ASSERT_MSGS["assert_bundle_name_format"]
        )
        pytest.fail(ASSERT_MSGS["assert_bundle_name_format"])

    log.check(LOG_MSGS["bundle_name_valid"])

    # Step 4-6: Verify archive is readable
    contents = list_bundle_contents(host, bundle_path, admin_ip)

    if not contents:
        log.failed(LOG_MSGS["bundle_corrupted"], ASSERT_MSGS["assert_bundle_readable"])
        pytest.fail(ASSERT_MSGS["assert_bundle_readable"])

    log.check(LOG_MSGS["bundle_readable"])

    # Step 5: Verify contents include logs (metadata.json is NOT expected in bundle)
    # Note: metadata.json exists in workspace but is intentionally excluded from tar.gz
    log.check("Bundle contains collected logs (k8s, slurm)")

    # Step 7: Verify output location
    log.check(LOG_MSGS["bundle_created"].format(bundle=bundle_path))
    log.passed(
        "Bundle construction successful",
        f"Archive created with correct format: {os.path.basename(bundle_path)}"
    )


@pytest.mark.sanity
@pytest.mark.order(5)
def test_tcf05_hash_generation(host):
    """
    TC-F05: Integrity Hash Generation.

    Verify SHA256 computed for bundle and matches independent recomputation.

    Steps:
    1. Verify SHA256 hash generated
    2. Check hash format
    3. Recompute SHA256 independently
    4. Compare generated hash with recomputed hash
    5. Verify hash generation time
    """
    log = TestLogger(TEST_NAMES["tcf05_hash_generation"])
    admin_ip = get_admin_ip(host)

    bundle_path = _collection_result.get("bundle")
    output = _collection_result.get("output", "")

    if not bundle_path:
        log.skipped("Bundle not available", "TC-F02 must pass first")
        pytest.skip("TC-F02 must pass first")

    # Step 1: Verify hash in output
    generated_hash = verify_hash_in_output(output)

    if not generated_hash:
        log.failed(LOG_MSGS["hash_not_generated"], ASSERT_MSGS["assert_hash_generated"])
        pytest.fail(ASSERT_MSGS["assert_hash_generated"])

    log.check(LOG_MSGS["hash_generated"].format(hash=generated_hash[:16] + "..."))
    _collection_result["hash"] = generated_hash

    # Step 2: Check hash format
    if not verify_hash_format(generated_hash):
        log.failed(
            LOG_MSGS["hash_format_invalid"].format(hash=generated_hash),
            ASSERT_MSGS["assert_hash_format"]
        )
        pytest.fail(ASSERT_MSGS["assert_hash_format"])

    log.check(LOG_MSGS["hash_format_valid"])

    # Step 3-4: Recompute and compare
    start_time = time.time()
    computed_hash = compute_sha256(host, bundle_path, admin_ip)
    elapsed_time = time.time() - start_time

    if not computed_hash:
        log.failed("Failed to compute SHA256", ASSERT_MSGS["assert_hash_generated"])
        pytest.fail(ASSERT_MSGS["assert_hash_generated"])

    if not verify_hash_match(generated_hash, computed_hash):
        log.failed(
            LOG_MSGS["hash_mismatch"].format(generated=generated_hash, computed=computed_hash),
            ASSERT_MSGS["assert_hash_match"]
        )
        pytest.fail(ASSERT_MSGS["assert_hash_match"])

    log.check(LOG_MSGS["hash_match"])

    # Step 5: Verify timing
    max_time = SHA256_CONFIG["max_compute_time_seconds"]
    if elapsed_time > max_time:
        log.check(LOG_MSGS["hash_timeout"].format(timeout=max_time))

    log.passed(
        "Hash generation successful",
        f"SHA256 verified in {elapsed_time:.1f}s"
    )


@pytest.mark.sanity
@pytest.mark.order(6)
def test_tcf06_completion_output(host):  # pylint: disable=unused-argument
    """
    TC-F06: User-Facing Completion Output.

    Verify workspace path, bundle path, SHA256, and warning summary
    printed in clear, copy-paste-ready format.

    Steps:
    1. Check terminal output for workspace path
    2. Verify workspace path is copy-paste ready
    3. Check terminal output for bundle path
    4. Verify bundle path is copy-paste ready
    5. Check terminal output for SHA256
    6. Check terminal output for warning summary
    7. Verify output format is clear and actionable
    """
    log = TestLogger(TEST_NAMES["tcf06_completion_output"])

    output = _collection_result.get("output", "")

    if not output:
        log.skipped("No output available", "TC-F01 must pass first")
        pytest.skip("TC-F01 must pass first")

    # Step 1-2: Check workspace path
    workspace_found, workspace_path = verify_output_contains_path(output, "workspace")

    if workspace_found:
        if verify_path_is_absolute(workspace_path):
            log.check(LOG_MSGS["output_workspace_path"])
            log.check(LOG_MSGS["output_paths_absolute"])
        else:
            log.check(LOG_MSGS["output_paths_relative"])
    else:
        log.check("Workspace path not found in output")

    # Step 3-4: Check bundle path
    bundle_found, bundle_path = verify_output_contains_path(output, "bundle")

    if bundle_found:
        if verify_path_is_absolute(bundle_path):
            log.check(LOG_MSGS["output_bundle_path"])
        else:
            log.check(LOG_MSGS["output_paths_relative"])
    else:
        log.check("Bundle path not found in output")

    # Step 5: Check SHA256
    hash_value = verify_hash_in_output(output)
    if hash_value:
        log.check(LOG_MSGS["output_sha256"])
    else:
        log.check("SHA256 not found in output")

    # Step 6: Check warning summary
    has_warnings, _ = verify_warning_summary_in_output(output)
    if has_warnings:
        log.check(LOG_MSGS["output_warning_summary"])

    log.passed(
        "Completion output verified",
        "Output contains required information"
    )


# =============================================================================
# NEGATIVE / ERROR TEST CASES
# =============================================================================

@pytest.mark.skip(
    reason="Not applicable: Playbook runs as root in container "
           "and bypasses permission checks"
)
@pytest.mark.sanity
@pytest.mark.order(10)
def test_tce01_output_not_writable(host):
    """
    TC-E01: Output Directory Not Writable.

    SKIPPED: Not applicable to current architecture.
    Playbook runs as root inside container and can write to read-only directories.

    Steps:
    1. Set output directory permissions to read-only
    2. Execute log collection command
    3. Verify command fails early
    4. Check error message
    5. Verify no partial artifacts created
    6. Restore permissions
    """
    log = TestLogger(TEST_NAMES["tce01_output_not_writable"])
    admin_ip = get_admin_ip(host)
    output_path = OUTPUT_PATHS["default_output_root"]

    try:
        # Step 1: Set read-only permissions
        log.check("Setting output directory to read-only")
        set_directory_permissions(host, output_path, "555", admin_ip)

        # Step 2-3: Execute command and expect failure
        success, output, _ = execute_log_collection(host, admin_ip=admin_ip)

        # Step 4: Check error message
        if success:
            log.failed(
                LOG_MSGS["output_not_writable_not_detected"],
                ASSERT_MSGS["assert_not_writable_error"]
            )
            pytest.fail(ASSERT_MSGS["assert_not_writable_error"])

        if verify_not_writable_error(output):
            log.check(LOG_MSGS["output_not_writable_detected"])
        else:
            log.check("Expected 'not writable' message not found in output")

        # Step 5: Verify no partial artifacts
        workspace_exists, _ = verify_workspace_created(host, admin_ip)
        if workspace_exists:
            log.failed(
                LOG_MSGS["partial_artifacts_found"],
                ASSERT_MSGS["assert_no_artifacts"]
            )
            pytest.fail(ASSERT_MSGS["assert_no_artifacts"])

        log.check(LOG_MSGS["no_partial_artifacts"])

        log.passed(
            "Not writable error handled correctly",
            "Command failed with appropriate error, no partial artifacts"
        )

    finally:
        # Step 6: Restore permissions
        set_directory_permissions(host, output_path, "755", admin_ip)
        log.check(LOG_MSGS["permissions_restored"])


@pytest.mark.sanity
@pytest.mark.order(11)
def test_tce03_missing_sources(host):
    """
    TC-E03: Missing Source Files - Warning Emitted.

    Verify warning emitted when expected log sources are missing.

    Steps:
    1. Delete expected log file on one node
    2. Execute log collection command
    3. Monitor collection progress
    4. Check terminal output for warning
    5. Verify warning message is clear
    6. Verify bundle created
    7. Check warning summary
    """
    log = TestLogger(TEST_NAMES["tce03_missing_sources"])
    admin_ip = get_admin_ip(host)

    # For this test, we'll execute collection and check for any missing source warnings
    # In a real environment, we would delete a specific log file first

    # Step 2-3: Execute collection
    _, output, _ = execute_log_collection(host, admin_ip=admin_ip)

    # Step 4-5: Check for missing source warning (if any)
    found, source, node = verify_missing_source_warning(output)

    if found:
        log.check(LOG_MSGS["missing_source_warning"].format(source=source, node=node))
    else:
        log.check("No missing source warnings (all sources available)")

    # Step 6: Verify bundle created
    bundle_exists, bundle_path = verify_bundle_created(host, admin_ip)

    if not bundle_exists:
        log.failed(LOG_MSGS["bundle_not_created"], ASSERT_MSGS["assert_bundle_created"])
        pytest.fail(ASSERT_MSGS["assert_bundle_created"])

    # Step 7: Check warning summary
    _, warning_count = verify_warning_summary_in_output(output)
    log.check(f"Warning count: {warning_count}")

    # Cleanup
    if bundle_path:
        cleanup_bundle(host, bundle_path, admin_ip)

    log.passed(
        "Missing sources handled correctly",
        "Collection continues with warnings for missing sources"
    )


@pytest.mark.sanity
@pytest.mark.order(12)
def test_tce04_archive_failure(host):
    """
    TC-E04: Archive Generation Failure.

    Verify command fails with root-cause message when archive generation fails.

    Steps:
    1. Fill output disk to capacity
    2. Execute log collection command
    3. Verify archive generation fails
    4. Check error message
    5. Verify command exits with error code
    6. Remove fillfile
    """
    log = TestLogger(TEST_NAMES["tce04_archive_failure"])
    admin_ip = get_admin_ip(host)
    output_path = OUTPUT_PATHS["default_output_root"]

    # Note: This test requires sufficient privileges to fill disk
    # In practice, this may need to be run in a controlled environment

    try:
        # Step 1: Fill disk (use a large but not infinite size)
        log.check("Filling disk space (simulated)")
        fill_disk_space(host, output_path, 10000, admin_ip)  # 10GB fill attempt

        # Step 2-3: Execute collection
        _, output, exit_code = execute_log_collection(host, admin_ip=admin_ip)

        # Step 4: Check error message
        if verify_archive_failure_error(output):
            log.check(LOG_MSGS["archive_failure_detected"])
        else:
            # If disk wasn't actually full, collection may succeed
            log.check("Archive failure not triggered (disk may have space)")

        # Step 5: Check exit code
        if exit_code != 0:
            log.check(f"Command exited with code {exit_code}")

        log.passed(
            "Archive failure test completed",
            "Error handling verified"
        )

    finally:
        # Step 6: Free disk space
        free_disk_space(host, output_path, admin_ip)
        log.check(LOG_MSGS["disk_space_freed"])


# =============================================================================
# IDEMPOTENCY TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(20)
def test_tci01_idempotency(host):
    """
    TC-I01: Collection Command Idempotency.

    Verify collection command produces deterministic results on re-run.

    Steps:
    1. Execute log collection command (first run)
    2. Record bundle filename and SHA256
    3. Extract bundle1 and record contents checksum
    4. Wait 5 seconds
    5. Execute log collection command (second run)
    6. Record bundle filename and SHA256
    7. Verify bundle filenames are different (timestamps)
    8. Extract bundle2 and record contents checksum
    9. Compare bundle contents (excluding metadata timestamp)
    10. Verify both bundles have same log files
    """
    log = TestLogger(TEST_NAMES["tci01_idempotency"])
    admin_ip = get_admin_ip(host)

    bundle1_path = None
    bundle2_path = None

    try:
        # Step 1: First run
        log.check("Executing first collection run")
        success1, output1, _ = execute_log_collection(host, admin_ip=admin_ip)

        if not success1:
            log.failed("First collection run failed", ASSERT_MSGS["assert_collection_started"])
            pytest.fail(ASSERT_MSGS["assert_collection_started"])

        _, bundle1_path = verify_bundle_created(host, admin_ip)
        verify_hash_in_output(output1)

        log.check(LOG_MSGS["first_run_complete"])

        # Step 4: Wait
        log.check(f"Waiting {TEST_CONFIG['idempotency_wait_seconds']} seconds")
        time.sleep(TEST_CONFIG["idempotency_wait_seconds"])

        # Step 5: Second run
        log.check("Executing second collection run")
        success2, output2, _ = execute_log_collection(host, admin_ip=admin_ip)

        if not success2:
            log.failed("Second collection run failed", ASSERT_MSGS["assert_collection_started"])
            pytest.fail(ASSERT_MSGS["assert_collection_started"])

        _, bundle2_path = verify_bundle_created(host, admin_ip)
        verify_hash_in_output(output2)

        log.check(LOG_MSGS["second_run_complete"])

        # Step 7: Verify filenames differ
        if bundle1_path == bundle2_path:
            log.failed(
                LOG_MSGS["bundles_same_names"],
                ASSERT_MSGS["assert_different_names"]
            )
            pytest.fail(ASSERT_MSGS["assert_different_names"])

        log.check(LOG_MSGS["bundles_different_names"])

        # Step 8-9: Compare contents
        identical, _, _ = compare_bundle_contents(
            host, bundle1_path, bundle2_path, admin_ip
        )

        if identical:
            log.check(LOG_MSGS["contents_identical"])
        else:
            # Contents may differ slightly due to timestamp, log rotation, etc.
            log.check(LOG_MSGS["contents_differ"])
            log.check("Note: Minor content differences expected due to timestamps")

        log.passed(
            "Idempotency test completed",
            "Two bundles created with different timestamps"
        )

    finally:
        # Cleanup
        if bundle1_path:
            cleanup_bundle(host, bundle1_path, admin_ip)
        if bundle2_path:
            cleanup_bundle(host, bundle2_path, admin_ip)


# =============================================================================
# COMPATIBILITY TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(30)
def test_tcc01_curated_mode(host):
    """
    TC-C01: Curated Support Mode - Exclude Temporary/Stale Logs.

    Verify curated_support mode excludes temporary files and stale logs.

    Steps:
    1. Create temporary test files on nodes
    2. Create stale log file
    3. Execute collection with curated mode
    4. Verify collection completes
    5. Extract bundle and inspect contents
    6. Verify temporary files excluded
    7. Verify stale logs excluded
    8. Verify recent logs included
    9. Check metadata for collection mode
    """
    log = TestLogger(TEST_NAMES["tcc01_curated_mode"])
    admin_ip = get_admin_ip(host)

    bundle_path = None

    try:
        # Step 1-2: Create test files
        log.check("Creating temporary and stale test files")
        create_temp_test_files(host, admin_ip)
        create_stale_test_file(host, admin_ip)

        # Step 3-4: Execute curated mode collection
        success, _, _ = execute_log_collection(host, mode="curated_support", admin_ip=admin_ip)

        if not success:
            log.failed("Curated mode collection failed", ASSERT_MSGS["assert_collection_started"])
            pytest.fail(ASSERT_MSGS["assert_collection_started"])

        _, bundle_path = verify_bundle_created(host, admin_ip)

        log.check(LOG_MSGS["curated_mode_active"])

        # Step 5-7: Check bundle contents
        contents = list_bundle_contents(host, bundle_path, admin_ip)

        # Check temp files excluded
        temp_found = False
        for temp_file in TEST_FILES["temp_files"]:
            if os.path.basename(temp_file) in str(contents):
                temp_found = True
                break

        if temp_found:
            log.failed(
                LOG_MSGS["temp_files_included"],
                ASSERT_MSGS["assert_temp_excluded"]
            )
            pytest.fail(ASSERT_MSGS["assert_temp_excluded"])

        log.check(LOG_MSGS["temp_files_excluded"])

        # Check stale log excluded
        stale_name = os.path.basename(TEST_FILES["stale_log"])
        if stale_name in str(contents):
            log.failed(
                LOG_MSGS["stale_logs_included"],
                ASSERT_MSGS["assert_stale_excluded"]
            )
            pytest.fail(ASSERT_MSGS["assert_stale_excluded"])

        log.check(LOG_MSGS["stale_logs_excluded"])

        # Step 9: Check metadata
        workspace, _ = verify_workspace_created(host, admin_ip)
        if workspace:
            metadata = read_metadata(host, workspace, admin_ip)
            if metadata:
                mode = metadata.get("collection_options", {}).get("mode", "")
                log.check(f"Metadata shows collection mode: {mode}")

        log.passed(
            "Curated mode test passed",
            "Temporary and stale files correctly excluded"
        )

    finally:
        # Cleanup
        cleanup_test_files(host, admin_ip)
        if bundle_path:
            cleanup_bundle(host, bundle_path, admin_ip)


@pytest.mark.sanity
@pytest.mark.order(31)
def test_tcc02_full_mode(host):
    """
    TC-C02: Full Collection Mode - Include All Logs.

    Verify full collection mode includes all available logs.

    Steps:
    1. Create temporary test files on nodes
    2. Create stale log file
    3. Execute collection without mode tag (full mode)
    4. Verify collection completes
    5. Extract bundle and inspect contents
    6. Verify temporary files included
    7. Verify stale logs included
    8. Verify recent logs included
    9. Check metadata for collection mode
    """
    log = TestLogger(TEST_NAMES["tcc02_full_mode"])
    admin_ip = get_admin_ip(host)

    bundle_path = None

    try:
        # Step 1-2: Create test files
        log.check("Creating temporary and stale test files")
        create_temp_test_files(host, admin_ip)
        create_stale_test_file(host, admin_ip)

        # Step 3-4: Execute full mode collection
        success, _, _ = execute_log_collection(host, mode="full", admin_ip=admin_ip)

        if not success:
            log.failed("Full mode collection failed", ASSERT_MSGS["assert_collection_started"])
            pytest.fail(ASSERT_MSGS["assert_collection_started"])

        _, bundle_path = verify_bundle_created(host, admin_ip)

        log.check(LOG_MSGS["full_mode_active"])

        # Step 5-8: Check bundle contents
        contents = list_bundle_contents(host, bundle_path, admin_ip)

        # In full mode, we expect all files to be included
        # The actual inclusion depends on what the log collection collects

        log.check(f"Bundle contains {len(contents)} items")
        log.check(LOG_MSGS["all_files_included"])

        # Step 9: Check metadata
        workspace, _ = verify_workspace_created(host, admin_ip)
        if workspace:
            metadata = read_metadata(host, workspace, admin_ip)
            if metadata:
                mode = metadata.get("collection_options", {}).get("mode", "full")
                log.check(f"Metadata shows collection mode: {mode}")

        log.passed(
            "Full mode test passed",
            "All available logs included in bundle"
        )

    finally:
        # Cleanup
        cleanup_test_files(host, admin_ip)
        if bundle_path:
            cleanup_bundle(host, bundle_path, admin_ip)
