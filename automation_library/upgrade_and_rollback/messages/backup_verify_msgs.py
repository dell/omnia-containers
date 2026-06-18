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
Upgrade Module - Backup Verification Messages.

Test names, log messages, and assertion messages for verifying openchami
backup contents (quadlets, boot, cloud-init, nodes, images).
"""

from typing import Dict

# =============================================================================
# TEST NAMES
# =============================================================================

BACKUP_TEST_NAMES: Dict[str, str] = {
    "verify_quadlets": "Verify quadlet files backup (md5sum)",
    "verify_boot": "Verify boot files backup (md5sum)",
    "verify_cloudinit": "Verify cloud-init files backup (md5sum)",
    "verify_nodes": "Verify nodes files backup (md5sum)",
    "verify_images": "Verify image definition files backup (md5sum)",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

BACKUP_LOG_MSGS: Dict[str, str] = {
    "checking": "Verifying {category} backup (md5sum)",
    "file_ok": "✓ {name}",
    "file_mismatch": "✗ {name}",
    "file_skipped": "⊘ {name} (expected to differ)",
    "no_files": "No files found in {dir}",
    "all_match": "All {count} {category} files match (md5sum)",
    "some_mismatch": "{mismatch}/{total} {category} files differ",
}

# =============================================================================
# ASSERT MESSAGES
# =============================================================================

BACKUP_ASSERT_MSGS: Dict[str, str] = {
    "no_backup_dir": (
        "{category} backup directory not found: {dir}\n\n"
        "HOW TO FIX:\n"
        "  1. Verify upgrade completed: podman exec omnia_core "
        "grep omnia_version /opt/omnia/.data/oim_metadata.yml\n"
        "  2. Check backup: ls -la {dir}\n"
        "  3. Re-run upgrade if backup is missing"
    ),
    "md5_mismatch": (
        "{mismatch}/{total} {category} backup files do not match current.\n\n"
        "HOW TO FIX:\n"
        "  1. Compare: diff <(podman exec omnia_core md5sum {backup_dir}/FILE) "
        "<(md5sum {current_dir}/FILE)\n"
        "  2. Check if upgrade modified these files intentionally"
    ),
}

# =============================================================================
# SKIP MESSAGES
# =============================================================================

BACKUP_SKIP_MSGS: Dict[str, str] = {
    "pre_upgrade_failed": "Skipped — pre-upgrade check (TC-1) failed",
}
