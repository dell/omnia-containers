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
Backup Verification Test Cases.

Verifies the integrity of openchami backup files taken during upgrade
by comparing md5sum of each backup file against its current counterpart.

Test cases (executed in order):
6.  Verify quadlet files backup (backup vs /etc/containers/systemd/)
7.  Verify boot files backup (backup vs /opt/omnia/openchami/workdir/boot/)
8.  Verify cloud-init files backup (backup vs workdir/cloud-init/)
9.  Verify nodes files backup (backup vs workdir/nodes/)
10. Verify image definition files backup (backup vs workdir/images/)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.upgrade.functions.backup_verify_func import (
    verify_backup_md5sum,
)
from automation_library.upgrade.vars.backup_verify_vars import (
    BACKUP_VERIFY_VARS,
)
from automation_library.upgrade.messages.backup_verify_msgs import (
    BACKUP_TEST_NAMES as TEST_NAMES,
    BACKUP_LOG_MSGS as LOG,
    BACKUP_ASSERT_MSGS as ASSERT,
    BACKUP_SKIP_MSGS as SKIP,
)


# =============================================================================
# HELPER
# =============================================================================

def _run_backup_verify(host, category: str, order_num: int):
    """
    Generic test body for backup md5sum verification.

    Args:
        host: Testinfra host object
        category: BACKUP_VERIFY_VARS key (quadlets, boot, etc.)
        order_num: Test order number (for display only)
    """
    cfg = BACKUP_VERIFY_VARS[category]
    backup_dir = cfg["backup_dir"]
    current_dir = cfg["current_dir"]

    log = TestLogger(TEST_NAMES[f"verify_{category}"])
    log.check(LOG["checking"].format(category=category))

    result = verify_backup_md5sum(host, category)
    files = result.get("files", [])

    if not files:
        log.failed(
            LOG["no_files"].format(dir=backup_dir),
            result["error"],
        )
        pytest.fail(
            ASSERT["no_backup_dir"].format(
                category=category, dir=backup_dir,
            )
        )

    # Build details — only show in final output
    lines = []
    for f in files:
        lines.append(LOG[
            "file_ok" if f["match"] == "✓" else "file_mismatch"
        ].format(name=f["name"]))
    details = "\n".join(lines)

    matched = sum(1 for f in files if f["match"] == "✓")
    total = len(files)
    mismatched = total - matched

    if result["success"]:
        log.passed(
            LOG["all_match"].format(count=total, category=category),
            details,
        )
    else:
        log.failed(
            LOG["some_mismatch"].format(
                mismatch=mismatched, total=total, category=category,
            ),
            details,
        )
        pytest.fail(
            ASSERT["md5_mismatch"].format(
                mismatch=mismatched,
                total=total,
                category=category,
                backup_dir=backup_dir,
                current_dir=current_dir,
            )
        )


# =============================================================================
# TC-6: VERIFY QUADLET FILES BACKUP
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_verify_quadlet_backup(host):
    """
    Test Case 6: Verify quadlet files backup against /etc/containers/systemd/.
    """
    _run_backup_verify(host, "quadlets", 6)


# =============================================================================
# TC-7: VERIFY BOOT FILES BACKUP
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_verify_boot_backup(host):
    """
    Test Case 7: Verify boot files backup (bss-*.yaml).
    """
    _run_backup_verify(host, "boot", 7)


# =============================================================================
# TC-8: VERIFY CLOUD-INIT FILES BACKUP
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_verify_cloudinit_backup(host):
    """
    Test Case 8: Verify cloud-init files backup (ci-*.yaml).
    """
    _run_backup_verify(host, "cloudinit", 8)


# =============================================================================
# TC-9: VERIFY NODES FILES BACKUP
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_verify_nodes_backup(host):
    """
    Test Case 9: Verify nodes files backup (groups-*.yml, nodes.yaml).
    """
    _run_backup_verify(host, "nodes", 9)


# =============================================================================
# TC-10: VERIFY IMAGES FILES BACKUP
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_verify_images_backup(host):
    """
    Test Case 10: Verify image definition files backup (*.yaml).
    """
    _run_backup_verify(host, "images", 10)
