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
Upgrade Module - Messages.

Test names, log messages, and assertion messages for the upgrade workflow.
"""

from typing import Dict

# =============================================================================
# TEST NAMES
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    "pre_upgrade_version": (
        "Verify current omnia_core container is running version {from_version}"
    ),
    "clone_upgrade_artifactory": (
        "Clone omnia-artifactory for upgrade to {to_version}"
    ),
    "build_core_image": (
        "Build omnia_core container image for {to_version}"
    ),
    "run_upgrade": (
        "Run omnia.sh --upgrade from {from_version} to {to_version}"
    ),
    "verify_backup": (
        "Verify backup folder created after upgrade"
    ),
    "verify_post_upgrade_version": (
        "Verify omnia_core upgraded to {to_version}"
    ),
    "verify_no_old_container": (
        "Verify no {from_version} omnia_core container running"
    ),
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # Pre-upgrade
    "checking_version": "Checking omnia_core container version...",
    "current_version_ok": (
        "omnia_core is running version {version} — ready for upgrade"
    ),
    "already_upgraded": (
        "omnia_core is already running version {version} — no upgrade needed"
    ),
    "already_upgraded_with_backup": (
        "omnia_core is running {version} and backup folder exists — "
        "cluster was already upgraded"
    ),

    # Clone
    "clone_start": "Cloning omnia-artifactory ({branch}) to {path}...",
    "clone_ok": "Artifactory cloned successfully to {path}",
    "clone_fail": "Failed to clone omnia-artifactory: {error}",

    # Build
    "build_start": (
        "Building core image: ./build_images.sh core "
        "omnia_branch={omnia_branch} core_tag={core_tag}"
    ),
    "build_ok": "Core image built successfully (tag: {core_tag})",
    "build_fail": "Core image build failed: {error}",
    "image_verify_ok": "Podman image verified: {image}:{tag}",
    "image_verify_fail": "Core image not found after build",

    # Upgrade
    "upgrade_start": "Running omnia.sh --upgrade...",
    "upgrade_ok": "omnia.sh --upgrade completed successfully",
    "upgrade_fail": "omnia.sh --upgrade failed: {error}",

    # Backup
    "backup_found": "Backup folder found: {path}",
    "backup_not_found": "No backup folder found under {base_path}",
    "backup_contents": "Backup contents: {items}",

    # Post-upgrade
    "post_version_ok": "omnia_core upgraded to {version}",
    "post_version_fail": (
        "Version mismatch after upgrade: expected {expected}, got {actual}"
    ),
    "no_old_container_ok": "No old {version} container running",
    "old_container_still_running": (
        "Old container still running: {details}"
    ),
}

# =============================================================================
# ASSERTION MESSAGES
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "pre_upgrade_wrong_version": (
        "Pre-upgrade version check failed.\n"
        "Expected: {expected}\n"
        "Actual: {actual}\n\n"
        "HOW TO FIX:\n"
        "  1. Verify omnia_core container is running: podman ps | grep omnia_core\n"
        "  2. Check metadata: podman exec omnia_core cat /opt/omnia/.data/oim_metadata.yml\n"
        "  3. If already upgraded, update 'upgrade.from_version' in omnia_test_config.yml"
    ),
    "already_at_target_version": (
        "Cluster is already at target version {version}.\n"
        "Backup folder present: {has_backup}\n\n"
        "INFO:\n"
        "  - If backup exists: cluster was already upgraded\n"
        "  - If no backup: cluster was deployed at {version} directly (no upgrade needed)"
    ),
    "container_not_running": (
        "omnia_core container is not running.\n\n"
        "HOW TO FIX:\n"
        "  1. Check container status: podman ps -a | grep omnia_core\n"
        "  2. Start container: podman start omnia_core\n"
        "  3. If not present, run omnia.sh --install first"
    ),
    "clone_failed": (
        "Failed to clone omnia-artifactory for upgrade.\n"
        "URL: {url}\n"
        "Branch: {branch}\n"
        "Path: {path}\n"
        "Error: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Check network connectivity from OIM server\n"
        "  2. Verify branch exists: git ls-remote --heads {url} {branch}\n"
        "  3. Check disk space on OIM server\n"
        "  4. Try manual clone: git clone -b {branch} {url} {path}"
    ),
    "build_failed": (
        "Core image build failed.\n"
        "Command: ./build_images.sh core omnia_branch={omnia_branch} core_tag={core_tag}\n"
        "Error: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Check build_images.sh output above for errors\n"
        "  2. Verify omnia_branch '{omnia_branch}' exists in Omnia repo\n"
        "  3. Check Podman: podman info\n"
        "  4. Check disk space: df -h\n"
        "  5. Try manually: cd {clone_path} && ./build_images.sh core "
        "omnia_branch={omnia_branch} core_tag={core_tag}"
    ),
    "image_not_found": (
        "Core container image not found after build.\n"
        "Expected image: omnia_core:{core_tag}\n\n"
        "HOW TO FIX:\n"
        "  1. Check podman images: podman images | grep omnia_core\n"
        "  2. Re-run build: cd {clone_path} && ./build_images.sh core "
        "omnia_branch={omnia_branch} core_tag={core_tag}"
    ),
    "upgrade_failed": (
        "omnia.sh --upgrade failed.\n"
        "Error: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Check omnia.sh output above for errors\n"
        "  2. Verify core image exists: podman images | grep omnia_core\n"
        "  3. Check container status: podman ps -a | grep omnia_core\n"
        "  4. Try manually: {omnia_sh_path} --upgrade"
    ),
    "backup_missing": (
        "Backup folder not found after upgrade.\n"
        "Expected under: {base_path}\n\n"
        "HOW TO FIX:\n"
        "  1. Check backup: ls -la {base_path}/ | grep backup\n"
        "  2. Verify omnia.sh --upgrade completed without errors\n"
        "  3. Check omnia.sh logs for backup creation step"
    ),
    "post_upgrade_version_mismatch": (
        "Version mismatch after upgrade.\n"
        "Expected: {expected}\n"
        "Actual: {actual}\n\n"
        "HOW TO FIX:\n"
        "  1. Check metadata: podman exec omnia_core "
        "cat /opt/omnia/.data/oim_metadata.yml\n"
        "  2. Check container: podman ps | grep omnia_core\n"
        "  3. The upgrade may have failed silently — check omnia.sh logs"
    ),
    "old_container_running": (
        "Old omnia_core container is still running after upgrade.\n"
        "Details: {details}\n\n"
        "HOW TO FIX:\n"
        "  1. Stop old container: podman stop <old_container_id>\n"
        "  2. Remove old container: podman rm <old_container_id>\n"
        "  3. Verify: podman ps | grep omnia"
    ),
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================

SKIP_MSGS: Dict[str, str] = {
    "upgrade_not_configured": (
        "Upgrade section not configured in omnia_test_config.yml"
    ),
    "container_not_running": "omnia_core container is not running",
    "already_upgraded": (
        "Cluster is already at target version {version}"
    ),
}
