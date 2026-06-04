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
One Shot Log Extraction Automation - Functions.

Contains all helper functions for one-shot combined log extraction tests.

Reference: TCASES-LOGEX-2026-001 (v1.0.0)
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from ...core import run_on_remote_node
from ..vars.one_shot_log_extraction_vars import (
    BUNDLE_NAME_PATTERN,
    CMD_TEMPLATES,
    EXIT_CODES,
    LOG_COLLECTION_COMMAND,
    LOG_COLLECTION_CURATED_MODE,
    METADATA_REQUIRED_FIELDS,
    OUTPUT_PATHS,
    SHA256_CONFIG,
    TEST_FILES,
    WARNING_ENTRY_FIELDS,
    WARNING_PATTERNS,
)

# admin_ip is accepted by many functions for API consistency but not
# always used when commands target the container via podman directly.
# pylint: disable=unused-argument


# =============================================================================
# COLLECTION EXECUTION FUNCTIONS
# =============================================================================

def execute_log_collection(host, mode: str = "full", admin_ip: str = "") -> Tuple[bool, str, int]:
    """
    Execute the one-shot log collection command in omnia_core container.

    Args:
        host: Testinfra host object
        mode: Collection mode - "full" or "curated_support"
        admin_ip: Admin IP for remote execution

    Returns:
        Tuple of (success, output, exit_code)
    """
    if mode == "curated_support":
        command = LOG_COLLECTION_CURATED_MODE
    else:
        command = LOG_COLLECTION_COMMAND

    # Execute inside omnia_core container - use host.run() directly
    container_command = f"podman exec omnia_core bash -c '{command}'"
    result = host.run(container_command)

    success = result.rc in (EXIT_CODES["success"], EXIT_CODES["partial_success"])
    return success, result.stdout + result.stderr, result.rc


def verify_collection_started(output: str) -> bool:
    """
    Verify that collection pipeline started successfully.

    Args:
        output: Command output string

    Returns:
        True if collection started, False otherwise
    """
    start_indicators = [
        "PLAY [Stage globals]",
        "PLAY [Prepare targets and inventory]",
        "PLAY [Collect k8s",
        "PLAY [Collect slurm",
        "PLAY [Bundle collected logs",
        "OMNIA LOG COLLECTION COMPLETE",
    ]
    return any(indicator in output for indicator in start_indicators)


# =============================================================================
# WORKSPACE FUNCTIONS
# =============================================================================

def get_workspace_directory(host, admin_ip: str = "") -> Optional[str]:
    """
    Find the most recent workspace directory (bundle directory) inside container.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP for remote execution

    Returns:
        Workspace directory path or None if not found
    """
    # Find the most recent omnia_logs_* directory inside container
    output_root = OUTPUT_PATHS['default_output_root']
    dir_pattern = OUTPUT_PATHS['bundle_dir_pattern']
    cmd = (
        f"podman exec omnia_core bash -c "
        f"'ls -td {output_root}/{dir_pattern} 2>/dev/null | head -1'"
    )
    result = host.run(cmd)

    if result.rc == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def verify_workspace_created(host, admin_ip: str = "") -> Tuple[bool, Optional[str]]:
    """
    Verify workspace directory was created inside container.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP for remote execution

    Returns:
        Tuple of (exists, workspace_path)
    """
    workspace = get_workspace_directory(host, admin_ip)
    if workspace:
        cmd = f"podman exec omnia_core test -d {workspace} && echo 'exists' || echo 'not_exists'"
        result = host.run(cmd)
        return "exists" in result.stdout, workspace
    return False, None


# =============================================================================
# BUNDLE FUNCTIONS
# =============================================================================

def get_bundle_path(host, admin_ip: str = "") -> Optional[str]:
    """
    Find the most recent bundle archive inside container.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP for remote execution

    Returns:
        Bundle file path or None if not found
    """
    # Find the most recent omnia_logs_*.tar.gz file inside container
    output_root = OUTPUT_PATHS['default_output_root']
    cmd = (
        f"podman exec omnia_core bash -c "
        f"'ls -t {output_root}/omnia_logs_*/*.tar.gz 2>/dev/null | head -1'"
    )
    result = host.run(cmd)

    if result.rc == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def verify_bundle_created(host, admin_ip: str = "") -> Tuple[bool, Optional[str]]:
    """
    Verify bundle archive was created inside container.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP for remote execution

    Returns:
        Tuple of (exists, bundle_path)
    """
    bundle = get_bundle_path(host, admin_ip)
    if bundle:
        cmd = f"podman exec omnia_core test -f {bundle} && echo 'exists' || echo 'not_exists'"
        result = host.run(cmd)
        return "exists" in result.stdout, bundle
    return False, None


def verify_bundle_name_format(bundle_path: str) -> bool:
    """
    Verify bundle filename matches expected format.

    Format: omnia-logs-<identifier>-<YYYYMMDD-HHMMSS-TZ>.tar.gz

    Args:
        bundle_path: Full path to bundle file

    Returns:
        True if format matches, False otherwise
    """
    filename = os.path.basename(bundle_path)
    return bool(re.match(BUNDLE_NAME_PATTERN, filename))


def extract_bundle(host, bundle_path: str, extract_dir: str, admin_ip: str = "") -> bool:
    """
    Extract bundle archive to directory inside container.

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive
        extract_dir: Directory to extract to
        admin_ip: Admin IP for remote execution

    Returns:
        True if extraction successful, False otherwise
    """
    # Create extract directory inside container
    host.run(f"podman exec omnia_core mkdir -p {extract_dir}")

    cmd = f"podman exec omnia_core tar -xzf {bundle_path} -C {extract_dir}"
    result = host.run(cmd)
    return result.rc == 0


def list_bundle_contents(host, bundle_path: str, admin_ip: str = "") -> List[str]:
    """
    List contents of bundle archive inside container.

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive
        admin_ip: Admin IP for remote execution

    Returns:
        List of file paths in archive
    """
    cmd = f"podman exec omnia_core tar -tzf {bundle_path}"
    result = host.run(cmd)

    if result.rc == 0:
        return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    return []


def verify_bundle_contains_file(host, bundle_path: str, filename: str, admin_ip: str = "") -> bool:
    """
    Check if bundle contains a specific file.

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive
        filename: Filename to look for
        admin_ip: Admin IP for remote execution

    Returns:
        True if file found in bundle, False otherwise
    """
    contents = list_bundle_contents(host, bundle_path, admin_ip)
    return any(filename in item for item in contents)


# =============================================================================
# METADATA FUNCTIONS
# =============================================================================

def read_metadata(host, workspace_path: str, admin_ip: str = "") -> Optional[Dict[str, Any]]:
    """
    Read and parse metadata JSON from workspace inside container.

    Args:
        host: Testinfra host object
        workspace_path: Path to workspace directory
        admin_ip: Admin IP for remote execution

    Returns:
        Parsed metadata dict or None if not found/invalid
    """
    metadata_path = f"{workspace_path}/{OUTPUT_PATHS['metadata_filename']}"
    cmd = f"podman exec omnia_core cat {metadata_path}"
    result = host.run(cmd)

    if result.rc == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
    return None


def verify_metadata_exists(host, workspace_path: str, admin_ip: str = "") -> bool:
    """
    Verify metadata JSON file exists in workspace inside container.

    Args:
        host: Testinfra host object
        workspace_path: Path to workspace directory
        admin_ip: Admin IP for remote execution

    Returns:
        True if metadata exists, False otherwise
    """
    metadata_path = f"{workspace_path}/{OUTPUT_PATHS['metadata_filename']}"
    cmd = f"podman exec omnia_core test -f {metadata_path} && echo 'exists' || echo 'not_exists'"
    result = host.run(cmd)
    return "exists" in result.stdout


def verify_metadata_valid_json(host, workspace_path: str, admin_ip: str = "") -> bool:
    """
    Verify metadata is valid JSON format inside container.

    Args:
        host: Testinfra host object
        workspace_path: Path to workspace directory
        admin_ip: Admin IP for remote execution

    Returns:
        True if valid JSON, False otherwise
    """
    metadata_path = f"{workspace_path}/{OUTPUT_PATHS['metadata_filename']}"
    cmd = f"podman exec omnia_core python3 -c \"import json; json.load(open('{metadata_path}'))\""
    result = host.run(cmd)
    return result.rc == 0


def verify_metadata_required_fields(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify metadata contains all required fields.

    Args:
        metadata: Parsed metadata dictionary

    Returns:
        Tuple of (all_present, missing_fields)
    """
    missing = []
    for field in METADATA_REQUIRED_FIELDS:
        if field not in metadata:
            missing.append(field)
    return len(missing) == 0, missing


def verify_metadata_warning_entries(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify warning entries in metadata contain required fields.
    Per CSPEC-LOGEX-2026-001 Section 4.2.

    Args:
        metadata: Parsed metadata dictionary

    Returns:
        Tuple of (all_valid, missing_fields)
    """
    warnings = metadata.get("warnings", [])
    if not warnings:
        return True, []

    missing = []
    for idx, warning in enumerate(warnings):
        for field in WARNING_ENTRY_FIELDS:
            if field not in warning:
                missing.append(f"warnings[{idx}].{field}")
    return len(missing) == 0, missing


def verify_warning_message_format(warning: Dict[str, Any]) -> bool:
    """
    Verify warning message follows implementation format.
    Format: "Node <hostname> (<ip>) not reachable via SSH during
    stage <stage>: <detail>. Continuing bundle generation."

    Args:
        warning: Warning entry dictionary

    Returns:
        True if format contains expected elements, False otherwise
    """
    message = warning.get("message", "")
    node_name = warning.get("node_name", "")
    node_ip = warning.get("node_ip", "")

    # Check if message contains key elements
    return (
        node_name in message and
        node_ip in message and
        ("not reachable" in message or "unreachable" in message) and
        "Continuing bundle generation" in message
    )


# =============================================================================
# HASH FUNCTIONS
# =============================================================================

def compute_sha256(host, file_path: str, admin_ip: str = "") -> Optional[str]:
    """
    Compute SHA256 hash of a file inside container.

    Args:
        host: Testinfra host object
        file_path: Path to file
        admin_ip: Admin IP for remote execution

    Returns:
        SHA256 hash string or None if failed
    """
    cmd = f"podman exec omnia_core bash -c 'sha256sum {file_path} | awk \"{{print \\$1}}\"'"
    result = host.run(cmd)

    if result.rc == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def verify_hash_format(hash_value: str) -> bool:
    """
    Verify hash is valid SHA256 format (64-character hex).

    Args:
        hash_value: Hash string to verify

    Returns:
        True if valid format, False otherwise
    """
    # Validate that it's exactly 64 hex characters
    return bool(re.match(r'^[a-fA-F0-9]{64}$', hash_value))


def verify_hash_in_output(output: str) -> Optional[str]:
    """
    Extract SHA256 hash from command output.

    Args:
        output: Command output string

    Returns:
        Hash value if found, None otherwise
    """
    match = re.search(SHA256_CONFIG["hash_pattern"], output)
    if match:
        return match.group(1)  # Return the captured hash group
    return None


def verify_hash_match(hash1: str, hash2: str) -> bool:
    """
    Compare two hash values.

    Args:
        hash1: First hash value
        hash2: Second hash value

    Returns:
        True if hashes match, False otherwise
    """
    return hash1.lower() == hash2.lower()


# =============================================================================
# OUTPUT VERIFICATION FUNCTIONS
# =============================================================================

def verify_output_contains_path(
    output: str, path_type: str = "workspace"
) -> Tuple[bool, Optional[str]]:
    """
    Verify command output contains expected path.

    Args:
        output: Command output string
        path_type: Type of path to look for ("workspace" or "bundle")

    Returns:
        Tuple of (found, path_value)
    """
    if path_type == "workspace":
        pattern = r"Workspace:\s*(/\S+)"
    else:
        pattern = r"Bundle:\s*(/\S+\.tar\.gz)"

    match = re.search(pattern, output)
    if match:
        return True, match.group(1)
    return False, None


def verify_path_is_absolute(path: str) -> bool:
    """
    Verify path is absolute (starts with /).

    Args:
        path: Path string to verify

    Returns:
        True if absolute, False otherwise
    """
    return path.startswith("/")


def verify_warning_summary_in_output(output: str) -> Tuple[bool, int]:
    """
    Verify warning summary is present in output.

    Args:
        output: Command output string

    Returns:
        Tuple of (found, warning_count)
    """
    pattern = r"Warnings?:\s*(\d+)"
    match = re.search(pattern, output, re.IGNORECASE)
    if match:
        return True, int(match.group(1))
    return False, 0


# =============================================================================
# ERROR HANDLING FUNCTIONS
# =============================================================================

def set_directory_permissions(host, path: str, mode: str, admin_ip: str = "") -> bool:
    """
    Set permissions on a directory inside container.

    Args:
        host: Testinfra host object
        path: Directory path
        mode: Permission mode (e.g., "555", "755")
        admin_ip: Admin IP for remote execution

    Returns:
        True if successful, False otherwise
    """
    cmd = f"podman exec omnia_core chmod {mode} {path}"
    result = host.run(cmd)
    return result.rc == 0


def verify_not_writable_error(output: str) -> bool:
    """
    Verify output contains 'not writable' error message.

    Args:
        output: Command output string

    Returns:
        True if error found, False otherwise
    """
    return bool(re.search(WARNING_PATTERNS["output_not_writable"], output))


def verify_archive_failure_error(output: str) -> bool:
    """
    Verify output contains archive failure error message.

    Args:
        output: Command output string

    Returns:
        True if error found, False otherwise
    """
    return bool(re.search(WARNING_PATTERNS["archive_failure"], output)) or \
           bool(re.search(WARNING_PATTERNS["disk_full"], output))


def verify_unreachable_node_warning(output: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verify output contains unreachable node warning with hostname and IP.

    Args:
        output: Command output string

    Returns:
        Tuple of (found, hostname, ip)
    """
    match = re.search(WARNING_PATTERNS["unreachable_node"], output)
    if match:
        return True, match.group(1), match.group(2)
    return False, None, None


def verify_missing_source_warning(output: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verify output contains missing source file warning.

    Args:
        output: Command output string

    Returns:
        Tuple of (found, source_path, node_name)
    """
    match = re.search(WARNING_PATTERNS["missing_source"], output)
    if match:
        return True, match.group(1), match.group(2)
    return False, None, None


# =============================================================================
# TEST FILE MANAGEMENT FUNCTIONS
# =============================================================================

def create_temp_test_files(host, admin_ip: str = "") -> bool:
    """
    Create temporary test files for compatibility tests.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP for remote execution

    Returns:
        True if all files created, False otherwise
    """
    for path in TEST_FILES["temp_files"]:
        cmd = CMD_TEMPLATES["create_temp_file"].format(path=path)
        result = run_on_remote_node(host, cmd, admin_ip=admin_ip)
        if result.rc != 0:
            return False
    return True


def create_stale_test_file(host, admin_ip: str = "") -> bool:
    """
    Create stale test file with old timestamp.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP for remote execution

    Returns:
        True if file created, False otherwise
    """
    cmd = CMD_TEMPLATES["create_stale_file"].format(
        days=TEST_FILES["stale_age_days"],
        path=TEST_FILES["stale_log"]
    )
    result = run_on_remote_node(host, cmd, admin_ip=admin_ip)
    return result.rc == 0


def cleanup_test_files(host, admin_ip: str = "") -> bool:
    """
    Remove test files created during tests.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP for remote execution

    Returns:
        True if cleanup successful, False otherwise
    """
    all_files = TEST_FILES["temp_files"] + [TEST_FILES["stale_log"]]
    for path in all_files:
        cmd = CMD_TEMPLATES["remove_file"].format(path=path)
        run_on_remote_node(host, cmd, admin_ip=admin_ip)
    return True


def fill_disk_space(host, path: str, size_mb: int, admin_ip: str = "") -> bool:
    """
    Fill disk space with dummy file (for error testing).

    Args:
        host: Testinfra host object
        path: Directory to fill
        size_mb: Size in MB
        admin_ip: Admin IP for remote execution

    Returns:
        True if successful, False otherwise
    """
    cmd = CMD_TEMPLATES["fill_disk"].format(path=path, size_mb=size_mb)
    run_on_remote_node(host, cmd, admin_ip=admin_ip)
    return True  # dd may return non-zero on disk full, which is expected


def free_disk_space(host, path: str, admin_ip: str = "") -> bool:
    """
    Remove fill file to free disk space.

    Args:
        host: Testinfra host object
        path: Directory with fill file
        admin_ip: Admin IP for remote execution

    Returns:
        True if successful, False otherwise
    """
    cmd = CMD_TEMPLATES["remove_file"].format(path=f"{path}/fillfile")
    result = run_on_remote_node(host, cmd, admin_ip=admin_ip)
    return result.rc == 0


# =============================================================================
# IDEMPOTENCY FUNCTIONS
# =============================================================================

def get_bundle_content_checksum(host, bundle_path: str, admin_ip: str = "") -> Optional[str]:
    """
    Get checksum of bundle contents (excluding metadata timestamp).

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive
        admin_ip: Admin IP for remote execution

    Returns:
        Checksum string or None if failed
    """
    # Extract to temp directory
    extract_dir = "/tmp/bundle_check_" + str(int(time.time()))
    if not extract_bundle(host, bundle_path, extract_dir, admin_ip):
        return None

    cmd = CMD_TEMPLATES["content_checksum"].format(dir_path=extract_dir)
    result = run_on_remote_node(host, cmd, admin_ip=admin_ip)

    # Cleanup
    run_on_remote_node(host, f"rm -rf {extract_dir}", admin_ip=admin_ip)

    if result.rc == 0:
        return result.stdout.strip().split()[0]
    return None


def compare_bundle_contents(
    host,
    bundle1_path: str,
    bundle2_path: str,
    admin_ip: str = ""
) -> Tuple[bool, str, str]:
    """
    Compare contents of two bundles (excluding metadata timestamp).

    Args:
        host: Testinfra host object
        bundle1_path: Path to first bundle
        bundle2_path: Path to second bundle
        admin_ip: Admin IP for remote execution

    Returns:
        Tuple of (identical, checksum1, checksum2)
    """
    checksum1 = get_bundle_content_checksum(host, bundle1_path, admin_ip)
    checksum2 = get_bundle_content_checksum(host, bundle2_path, admin_ip)

    if checksum1 and checksum2:
        return checksum1 == checksum2, checksum1, checksum2
    return False, checksum1 or "", checksum2 or ""


# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

def cleanup_workspace(host, workspace_path: str, admin_ip: str = "") -> bool:
    """
    Remove workspace directory.

    Args:
        host: Testinfra host object
        workspace_path: Path to workspace directory
        admin_ip: Admin IP for remote execution

    Returns:
        True if cleanup successful, False otherwise
    """
    cmd = f"rm -rf {workspace_path}"
    result = run_on_remote_node(host, cmd, admin_ip=admin_ip)
    return result.rc == 0


def cleanup_bundle(host, bundle_path: str, admin_ip: str = "") -> bool:
    """
    Remove bundle archive.

    Args:
        host: Testinfra host object
        bundle_path: Path to bundle archive
        admin_ip: Admin IP for remote execution

    Returns:
        True if cleanup successful, False otherwise
    """
    cmd = CMD_TEMPLATES["remove_file"].format(path=bundle_path)
    result = run_on_remote_node(host, cmd, admin_ip=admin_ip)
    return result.rc == 0
