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
Rollback Module - Messages.

Test names, log messages, assertion messages, and skip messages for the
Omnia rollback workflow tests.
"""

from typing import Dict

# =============================================================================
# TEST NAMES
# =============================================================================

ROLLBACK_TEST_NAMES: Dict[str, str] = {
    # Pre-check
    "precondition": "Verify rollback is needed ({new_version} → {target_version})",

    # Pre-rollback
    "check_rollback_image": (
        "Verify rollback image (omnia_core:{tag}) is available"
    ),

    # Rollback execution
    "run_rollback": "Download omnia.sh and run rollback",

    # Post-rollback container
    "verify_rollback_container": (
        "Verify omnia_core rolled back to {version}"
    ),

    # Post-rollback backup verify (per category)
    "verify_project_default": "Verify project_default files restored (md5sum)",
    "verify_quadlets": "Verify quadlet files restored (md5sum)",
    "verify_boot": "Verify boot files restored (md5sum)",
    "verify_cloudinit": "Verify cloud-init files restored (md5sum)",
    "verify_nodes": "Verify nodes files restored (md5sum)",
    "verify_images": "Verify image definition files restored (md5sum)",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

ROLLBACK_LOG_MSGS: Dict[str, str] = {
    # Pre-check
    "checking_precondition": (
        "Checking if rollback is needed ({new_version} → {target_version})"
    ),
    "precondition_ok": (
        "✓ Container at {running_version}, rollback to {target_version} needed"
    ),
    "precondition_not_needed": (
        "✗ Container already at {target_version} — no rollback needed"
    ),
    "precondition_unknown": (
        "✗ Container at {running_version} — cannot determine rollback eligibility"
    ),

    # Image check
    "checking_image": "Checking rollback image: omnia_core:{tag}",
    "image_found": "✓ omnia_core:{tag} available",
    "image_not_found": "✗ omnia_core:{tag} not found",

    # omnia.sh download
    "downloading_omnia_sh": "Downloading omnia.sh from {url}",
    "omnia_sh_ok": "✓ omnia.sh downloaded",
    "omnia_sh_fail": "✗ Failed to download omnia.sh: {error}",

    # Rollback execution
    "rollback_start": "Running omnia.sh --rollback",
    "rollback_progress": "  Rollback in progress... ({elapsed}s elapsed)",
    "rollback_ok": "✓ Rollback completed successfully",
    "rollback_fail": "✗ Rollback failed (rc={rc})",
    "output_header": "--- Last {lines} lines ---",

    # Container verification
    "checking_container": "Checking rolled-back container status",
    "container_name": "Container: {name}",
    "container_image": "Image:     {image}",
    "container_status": "Status:    {status}",
    "container_version_ok": (
        "✓ omnia_version: {version} (expected: {expected})"
    ),
    "container_version_fail": (
        "✗ Expected {expected}, found {actual}"
    ),

    # Backup verify (generic — used for all categories)
    "checking_category": "Verifying {category} backup vs current (md5sum)",
    "file_ok": "✓ {name}",
    "file_mismatch": "✗ {name}",
    "file_skipped": "⊘ {name} (expected to differ)",
    "no_files": "✗ No files found in {dir}",
    "all_match": "✓ All {count} {category} files match",
    "some_mismatch": "✗ {mismatch}/{total} {category} files differ",
}

# =============================================================================
# ASSERT MESSAGES
# =============================================================================

ROLLBACK_ASSERT_MSGS: Dict[str, str] = {
    # Pre-check
    "already_at_target": (
        "Container is already at {target_version} — no rollback needed.\n\n"
        "This means the system is already at the expected pre-upgrade version.\n"
        "Rollback is only applicable when running {new_version}."
    ),
    "precondition_failed": (
        "Cannot determine rollback eligibility.\n"
        "Running: {running_version}, expected: {new_version}.\n\n"
        "HOW TO FIX:\n"
        "  1. Verify upgrade was performed: podman exec omnia_core "
        "grep omnia_version /opt/omnia/.data/oim_metadata.yml\n"
        "  2. Ensure current_version and new_version are correct in "
        "omnia_test_config.yml"
    ),
    "config_missing": (
        "current_version or new_version not set in omnia_test_config.yml.\n\n"
        "HOW TO FIX:\n"
        "  Set upgrade.current_version and upgrade.new_version in "
        "omnia_test_config.yml"
    ),

    # Image
    "image_not_found": (
        "Rollback image omnia_core:{tag} not found.\n\n"
        "HOW TO FIX:\n"
        "  1. Check: podman images | grep omnia_core\n"
        "  2. Ensure the original image was not removed during upgrade"
    ),

    # Download
    "omnia_sh_download_failed": (
        "Failed to download omnia.sh from {url}.\n\n"
        "HOW TO FIX:\n"
        "  1. Check network connectivity\n"
        "  2. Verify URL is correct\n"
        "  3. Try: curl -f -o /tmp/omnia.sh {url}"
    ),

    # Rollback execution
    "rollback_failed": (
        "omnia.sh --rollback failed with rc={rc}.\n\n"
        "HOW TO FIX:\n"
        "  1. Check output: cat /tmp/rollback.log\n"
        "  2. Re-run manually: {omnia_sh_path} --rollback\n"
        "  3. Check container status: podman ps -a"
    ),

    # Container
    "container_wrong_version": (
        "After rollback, container is at {actual} instead of {expected}.\n\n"
        "HOW TO FIX:\n"
        "  1. Check metadata: podman exec omnia_core "
        "grep omnia_version /opt/omnia/.data/oim_metadata.yml\n"
        "  2. Check container: podman ps -a --filter name=omnia_core\n"
        "  3. Re-run rollback"
    ),
    "container_not_running": (
        "omnia_core container is not running after rollback.\n\n"
        "HOW TO FIX:\n"
        "  1. Check: podman ps -a --filter name=omnia_core\n"
        "  2. Check logs: podman logs omnia_core\n"
        "  3. Check systemd: systemctl status omnia_core"
    ),

    # Backup verify (generic)
    "md5_mismatch": (
        "{mismatch}/{total} {category} files do not match after rollback.\n\n"
        "HOW TO FIX:\n"
        "  1. Compare: diff {backup_dir}/ {current_dir}/\n"
        "  2. Check rollback log: cat /tmp/rollback.log"
    ),
    "no_backup_dir": (
        "No {category} backup files found in {dir}.\n\n"
        "HOW TO FIX:\n"
        "  1. Verify backup exists: ls -la {dir}\n"
        "  2. Ensure upgrade was run with backup enabled"
    ),
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================

ROLLBACK_SKIP_MSGS: Dict[str, str] = {
    "not_needed": "Skipped — rollback not needed (already at target version)",
    "container_not_running": "Skipped — omnia_core container not running",
    "fresh_install": (
        "Skipped — container is fresh install at {version}, never upgraded. "
        "Rollback not applicable."
    ),
    "fresh_install_new": (
        "Skipped — container is fresh install at {version}, "
        "no previous version found. Cannot rollback."
    ),
    "image_not_available": "Skipped — rollback image not available",
    "rollback_failed": "Skipped — rollback execution failed",
    "precondition_failed": "Skipped — rollback precondition check failed",
}
