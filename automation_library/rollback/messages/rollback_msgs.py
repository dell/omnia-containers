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
    "check_rollback_image": (
        "Verify rollback image (omnia_core:{tag}) is available"
    ),
    "run_rollback": "Download omnia.sh and run rollback",
    "verify_rollback_container": (
        "Verify omnia_core rolled back to {version}"
    ),
    "verify_project_default": (
        "Verify project_default files restored (md5sum)"
    ),
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

ROLLBACK_LOG_MSGS: Dict[str, str] = {
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

    # project_default files
    "checking_project_default": (
        "Verifying project_default backup vs current (md5sum)"
    ),
    "file_ok": "✓ {name}",
    "file_mismatch": "✗ {name}",
}

# =============================================================================
# ASSERT MESSAGES
# =============================================================================

ROLLBACK_ASSERT_MSGS: Dict[str, str] = {
    "image_not_found": (
        "Rollback image omnia_core:{tag} not found.\n\n"
        "HOW TO FIX:\n"
        "  1. Check: podman images | grep omnia_core\n"
        "  2. Ensure the original image was not removed during upgrade"
    ),
    "omnia_sh_download_failed": (
        "Failed to download omnia.sh from {url}.\n\n"
        "HOW TO FIX:\n"
        "  1. Check network connectivity\n"
        "  2. Verify URL is correct\n"
        "  3. Try: wget -q {url} -O {path}"
    ),
    "rollback_failed": (
        "omnia.sh --rollback failed with rc={rc}.\n\n"
        "HOW TO FIX:\n"
        "  1. Check output: cat /tmp/rollback.log\n"
        "  2. Re-run manually: {omnia_sh_path} --rollback\n"
        "  3. Check container status: podman ps -a"
    ),
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
    "project_default_mismatch": (
        "{mismatch}/{total} project_default files do not match after "
        "rollback.\n\n"
        "HOW TO FIX:\n"
        "  1. Compare backup vs current project_default files\n"
        "  2. Check: podman exec omnia_core ls -la "
        "/opt/omnia/input/project_default/"
    ),
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================

ROLLBACK_SKIP_MSGS: Dict[str, str] = {
    "image_not_available": "Skipped — rollback image not available",
    "rollback_failed": "Skipped — rollback execution failed",
}
