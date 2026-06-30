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
Upgrade Module - Prepare Upgrade Messages.

Messages for the ``prepare_upgrade.yml`` playbook execution test.
"""

from typing import Dict

# =============================================================================
# TEST NAMES — display names for each test case
# =============================================================================

PREPARE_TEST_NAMES: Dict[str, str] = {
    "run_prepare_upgrade": "Run prepare_upgrade.yml playbook",
}

# =============================================================================
# LOG MESSAGES — printed during test execution
# =============================================================================

PREPARE_LOG_MSGS: Dict[str, str] = {
    "start": "Running prepare_upgrade.yml inside omnia_core container",
    "progress": "  Playbook in progress... ({elapsed}s elapsed)",
    "ok": "✓ prepare_upgrade.yml completed successfully",
    "fail": "✗ prepare_upgrade.yml failed (rc={rc})",
    "output_header": "Playbook output (last {lines} lines):",
}

# =============================================================================
# ASSERTION MESSAGES — shown when tests fail (include HOW TO FIX)
# =============================================================================

PREPARE_ASSERT_MSGS: Dict[str, str] = {
    "playbook_failed": (
        "prepare_upgrade.yml failed with rc={rc}.\n\n"
        "HOW TO FIX:\n"
        "  1. Check log: podman exec omnia_core cat {log_file}\n"
        "  2. Re-run manually: podman exec omnia_core "
        "ansible-playbook {playbook_path}\n"
        "  3. Ensure backup is present and the upgrade completed successfully"
    ),
    "playbook_start_failed": (
        "Failed to start prepare_upgrade.yml inside omnia_core.\n\n"
        "HOW TO FIX:\n"
        "  1. Check container is running: podman ps | grep omnia_core\n"
        "  2. Verify playbook exists: podman exec omnia_core "
        "ls -la {playbook_path}\n"
        "  3. Check Ansible is available inside the container"
    ),
}

# =============================================================================
# SKIP MESSAGES — for pytest.skip() calls
# =============================================================================

PREPARE_SKIP_MSGS: Dict[str, str] = {
    "container_not_running": "omnia_core container is not running",
}
