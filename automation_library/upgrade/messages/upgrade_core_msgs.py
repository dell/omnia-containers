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

Test names, log messages, assertion messages, and skip messages for the
Omnia upgrade / rollback workflow.
"""

from typing import Dict

# =============================================================================
# TEST NAMES — displayed in reports and TestLogger
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    "pre_upgrade_version": (
        "Verify omnia_core container is running version {from_version}"
    ),
    "build_and_prepare": (
        "Clone repo, build core image (omnia_core:{core_tag}), "
        "download omnia.sh"
    ),
    "run_upgrade": (
        "Run omnia.sh --upgrade from {from_version} to {to_version}"
    ),
    "verify_backup_directory": (
        "Verify upgrade backup directory created"
    ),
    "verify_input_files": (
        "Verify input files backup integrity (md5sum)"
    ),
    "verify_quadlet_backup": (
        "Verify quadlet file (omnia_core.container) backed up"
    ),
    "verify_post_upgrade": (
        "Verify omnia_core upgraded to {to_version} and container is healthy"
    ),
}

# =============================================================================
# LOG MESSAGES — for TestLogger during test execution
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {

    # --- Operation validation ------------------------------------------------
    "operation_invalid": (
        "upgrade.operation is '{operation}' — must be 'upgrade' or 'rollback'"
    ),
    "version_unsupported": (
        "Version '{version}' is not in SUPPORTED_VERSIONS: {supported}"
    ),

    # --- Pre-upgrade ---------------------------------------------------------
    "checking_container": "Checking omnia_core container status",
    "container_info": (
        "Container: {name}\n"
        "  Image:  {image}\n"
        "  Status: {status}"
    ),
    "reading_version": "Reading omnia_version from metadata",
    "current_version_ok": (
        "omnia_core is running version {version} — ready for upgrade"
    ),
    "already_at_target": (
        "omnia_core is already at target version {version} — "
        "this is already the desired version"
    ),

    # --- Clone ---------------------------------------------------------------
    "clone_start": "Cloning upgrade repository ({branch})",
    "clone_ok": "Repository cloned successfully",
    "clone_fail": "Clone failed: {error}",

    # --- Build ---------------------------------------------------------------
    "build_start": "Building core image (omnia_core:{core_tag})",
    "build_progress": "  Build in progress... ({elapsed}s elapsed)",
    "build_ok": "Core image built successfully (omnia_core:{core_tag})",
    "build_fail": "Core image build FAILED (exit code {rc})",

    # --- Image verification --------------------------------------------------
    "image_found": "✓ Image verified: omnia_core:{tag}",
    "image_not_found": "✗ Image NOT found: omnia_core:{tag}",

    # --- omnia.sh download ---------------------------------------------------
    "omnia_sh_download_ok": "✓ omnia.sh downloaded and marked executable",
    "omnia_sh_download_fail": "✗ Failed to download omnia.sh: {error}",

    # --- Upgrade execution ---------------------------------------------------
    "upgrade_start": "Running omnia.sh --upgrade",
    "upgrade_input": "Auto-selecting upgrade option: '{input}'",
    "upgrade_progress": "  Upgrade in progress... ({elapsed}s elapsed)",
    "upgrade_ok": "omnia.sh --upgrade completed successfully",
    "upgrade_fail": "omnia.sh --upgrade FAILED (exit code {rc})",

    # --- Backup directory verification ---------------------------------------
    "backup_dir_check": "Checking backup directory: {path}",
    "backup_dir_found": "✓ Backup directory exists: {path}",
    "backup_dir_not_found": "✗ Backup directory not found: {path}",
    "backup_sub_ok": "  ✓ {name}/ present",
    "backup_sub_missing": "  ✗ {name}/ missing",

    # --- Input files backup verification -------------------------------------
    "input_files_check": "Comparing backup input files with current (md5sum)",
    "input_file_ok": "  ✓ {name} — validated (md5 match)",
    "input_file_mismatch": "  ✗ {name} — mismatch (backup: {bk_md5}, current: {cur_md5})",
    "input_files_none": "  No input files found in backup",

    # --- Quadlet backup verification -----------------------------------------
    "quadlet_check": "Checking quadlet backup: configs/omnia_core.container",
    "quadlet_ok": "✓ omnia_core.container backed up ({size} bytes)",
    "quadlet_not_found": "✗ omnia_core.container not found in backup",
    "quadlet_empty": "✗ omnia_core.container is empty (0 bytes)",

    # --- Post-upgrade --------------------------------------------------------
    "post_container_check": "Checking post-upgrade container state",
    "post_container_info": (
        "Container: {name}\n"
        "  Image:  {image}\n"
        "  Status: {status}"
    ),
    "post_version_ok": "✓ omnia_version: {version} (expected: {expected})",
    "post_version_fail": (
        "✗ Version mismatch: expected {expected}, found {actual}"
    ),
    "post_container_running": "✓ omnia_core container is running",
    "post_container_not_running": "✗ omnia_core container is NOT running",
}

# =============================================================================
# ASSERTION MESSAGES — shown when tests fail (include HOW TO FIX)
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "operation_invalid": (
        "upgrade.operation is '{operation}' in omnia_test_config.yml.\n"
        "Valid values: 'upgrade', 'rollback'\n\n"
        "HOW TO FIX:\n"
        "  1. Open omnia_test_config.yml\n"
        "  2. Set upgrade.operation to 'upgrade' or 'rollback'\n"
        "  3. Re-run the upgrade_omnia_sh scenario"
    ),
    "version_unsupported": (
        "Version '{version}' is not supported.\n"
        "Supported versions: {supported}\n\n"
        "HOW TO FIX:\n"
        "  1. Update upgrade.current_version / upgrade.new_version in omnia_test_config.yml\n"
        "  2. Ensure both versions are in the SUPPORTED_VERSIONS list"
    ),
    "container_not_running": (
        "omnia_core container is not running.\n\n"
        "HOW TO FIX:\n"
        "  1. Check container status: podman ps -a | grep omnia_core\n"
        "  2. Start container: systemctl start omnia_core.service\n"
        "  3. If not present, run omnia.sh --install first"
    ),
    "pre_upgrade_wrong_version": (
        "Pre-upgrade version check failed.\n"
        "Expected: {expected}\n"
        "Actual: {actual}\n\n"
        "HOW TO FIX:\n"
        "  1. Verify omnia_core container is running: podman ps | grep omnia_core\n"
        "  2. Check metadata: podman exec omnia_core cat /opt/omnia/.data/oim_metadata.yml\n"
        "  3. Update 'upgrade.current_version' in omnia_test_config.yml to match actual"
    ),
    "already_at_target_version": (
        "omnia_core is already at target version {version}.\n"
        "The cluster is already in the desired state — no upgrade needed.\n\n"
        "HOW TO FIX:\n"
        "  - If this is expected, the upgrade was already performed\n"
        "  - To re-test, rollback first or redeploy from {from_version}"
    ),
    "clone_failed": (
        "Failed to clone omnia-artifactory for upgrade.\n"
        "URL: {url}\nBranch: {branch}\nPath: {path}\n"
        "Error: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Check network: ping github.com\n"
        "  2. Verify branch: git ls-remote --heads {url} {branch}\n"
        "  3. Check disk space: df -h\n"
        "  4. Try manually: git clone -b {branch} {url} {path}"
    ),
    "build_failed": (
        "Core image build failed (exit code {rc}).\n\n"
        "HOW TO FIX:\n"
        "  1. Check build output above for errors\n"
        "  2. Verify omnia_branch '{omnia_branch}' exists\n"
        "  3. Check disk space: df -h\n"
        "  4. Re-run the build manually on the OIM server"
    ),
    "image_not_found": (
        "Core container image not found after build.\n"
        "Expected image: omnia_core:{core_tag}\n\n"
        "HOW TO FIX:\n"
        "  1. Check: podman images | grep omnia_core\n"
        "  2. Re-run the build on the OIM server"
    ),
    "omnia_sh_download_failed": (
        "Failed to download omnia.sh.\n"
        "URL: {url}\nError: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Check internet connectivity\n"
        "  2. Verify URL is reachable: curl -fI {url}\n"
        "  3. Download manually and place at {path}"
    ),
    "upgrade_failed": (
        "omnia.sh --upgrade failed.\n"
        "Exit code: {rc}\n"
        "Last output lines:\n{output}\n\n"
        "HOW TO FIX:\n"
        "  1. Check output above for specific errors\n"
        "  2. Verify core image: podman images | grep omnia_core\n"
        "  3. Check container: podman ps -a | grep omnia_core\n"
        "  4. Try manually: {omnia_sh_path} --upgrade"
    ),
    "backup_dir_missing": (
        "Backup directory not found after upgrade.\n"
        "Expected: {path}\n\n"
        "HOW TO FIX:\n"
        "  1. Check: podman exec omnia_core ls -la /opt/omnia/backups/upgrade/\n"
        "  2. Verify upgrade completed without errors"
    ),
    "backup_dir_incomplete": (
        "Backup directory is missing sub-directories.\n"
        "Backup path: {path}\n"
        "Missing: {missing}\n\n"
        "HOW TO FIX:\n"
        "  1. Check: podman exec omnia_core ls -laR {path}\n"
        "  2. The upgrade may have failed during backup creation"
    ),
    "input_files_mismatch": (
        "Some input files in the backup do not match current files.\n"
        "Backup path: {path}/input/\n\n"
        "HOW TO FIX:\n"
        "  1. Check: podman exec omnia_core ls -la {path}/input/\n"
        "  2. Compare manually with /opt/omnia/input/"
    ),
    "input_files_empty": (
        "No input files found in backup.\n"
        "Expected files in: {path}/input/\n\n"
        "HOW TO FIX:\n"
        "  1. Check: podman exec omnia_core ls -la {path}/input/\n"
        "  2. Verify /opt/omnia/input/ has files before upgrade"
    ),
    "quadlet_missing": (
        "Quadlet backup file not found.\n"
        "Expected: {path}/configs/omnia_core.container\n\n"
        "HOW TO FIX:\n"
        "  1. Check: podman exec omnia_core ls -la {path}/configs/\n"
        "  2. The upgrade may have failed during config backup"
    ),
    "post_upgrade_version_mismatch": (
        "Version mismatch after upgrade.\n"
        "Expected: {expected}\nActual: {actual}\n\n"
        "HOW TO FIX:\n"
        "  1. Check metadata: podman exec omnia_core "
        "cat /opt/omnia/.data/oim_metadata.yml\n"
        "  2. Check container tag: podman ps --format '{{{{.Image}}}}' "
        "--filter name=omnia_core\n"
        "  3. The upgrade may have failed silently — check logs"
    ),
    "post_container_not_running": (
        "omnia_core container is not running after upgrade.\n\n"
        "HOW TO FIX:\n"
        "  1. Check: systemctl status omnia_core.service\n"
        "  2. Start: systemctl start omnia_core.service\n"
        "  3. Check logs: journalctl -u omnia_core.service"
    ),
}

# =============================================================================
# SKIP MESSAGES — for pytest.skip() calls
# =============================================================================

SKIP_MSGS: Dict[str, str] = {
    "operation_not_configured": (
        "upgrade.operation not set to 'upgrade' or 'rollback' in "
        "omnia_test_config.yml (current: '{operation}')"
    ),
    "container_not_running": "omnia_core container is not running",
    "already_upgraded": (
        "omnia_core is already at target version {version}"
    ),
}
