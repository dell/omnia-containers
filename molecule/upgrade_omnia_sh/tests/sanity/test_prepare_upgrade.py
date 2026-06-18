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
Prepare Upgrade Test Cases.

Runs the ``prepare_upgrade.yml`` playbook inside the omnia_core container
after an upgrade has been performed. This playbook transforms 2.1 input
files to 2.2 format, restores credentials, and displays a migration summary.

Test cases (executed in order):
1. Run prepare_upgrade.yml playbook (with 10s progress, last 50 lines on finish)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.upgrade.functions import run_prepare_upgrade
from automation_library.upgrade.vars import PREPARE_UPGRADE_VARS
from automation_library.upgrade.messages import (
    PREPARE_TEST_NAMES as TEST_NAMES,
    PREPARE_LOG_MSGS as LOG,
    PREPARE_ASSERT_MSGS as ASSERT,
)


# =============================================================================
# TC-1: RUN PREPARE_UPGRADE.YML
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_run_prepare_upgrade(host):
    """
    Test Case 1: Run prepare_upgrade.yml inside omnia_core container.

    Steps:
    - Start playbook in background inside the container
    - Poll every 10 seconds, print progress
    - On completion, show last 50 lines of output
    - PASS if rc=0, FAIL otherwise
    """
    playbook_path = PREPARE_UPGRADE_VARS["playbook_path"]
    log_file = PREPARE_UPGRADE_VARS["log_file"]
    tail_lines = PREPARE_UPGRADE_VARS["tail_lines"]

    log = TestLogger(TEST_NAMES["run_prepare_upgrade"])

    log.check(LOG["start"])

    def _progress(elapsed: int) -> None:
        print(
            f"    {LOG['progress'].format(elapsed=elapsed)}",
            flush=True,
        )

    result = run_prepare_upgrade(host, progress_callback=_progress)
    output = result.get("output", "")

    if result["success"]:
        details = "✓ prepare_upgrade.yml completed (rc=0)"
        if output:
            details += (
                f"\n\n{LOG['output_header'].format(lines=tail_lines)}\n"
                + output
            )
        log.passed(LOG["ok"], details)
    else:
        fail_details = result["error"]
        if output:
            fail_details += (
                f"\n\n{LOG['output_header'].format(lines=tail_lines)}\n"
                + output
            )
        log.failed(
            LOG["fail"].format(rc=result.get("rc", "?")),
            fail_details,
        )
        pytest.fail(
            ASSERT["playbook_failed"].format(
                rc=result.get("rc", "?"),
                log_file=log_file,
                playbook_path=playbook_path,
            )
        )
