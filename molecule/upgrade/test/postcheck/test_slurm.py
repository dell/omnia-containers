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

"""Slurm Upgrade Postcheck Test Cases.

Test cases to verify Slurm accounting data is preserved after Omnia upgrade:
  TC-1 - Verify pre-upgrade job ID is still recorded in Slurm accounting DB (sacct)
"""

import os

import pytest
from automation_library.core import TestLogger
from automation_library.slurm.functions.slurm_func import get_slurm_control_nodes
from automation_library.slurm.functions.slurm_reboot_func import (
    verify_slurmdbd_data_preserved,
)

UPGRADE_JOB_ID_FILE = "/tmp/omnia_upgrade_slurm_job_id.txt"


@pytest.mark.sanity
@pytest.mark.order(1)
def test_slurm_upgrade_postcheck_sacct(host):
    """
    TC-1: Verify the pre-upgrade job ID is still in Slurm accounting DB after upgrade.

    Reads the job ID written by the precheck test from UPGRADE_JOB_ID_FILE and
    runs sacct on the control node to confirm the job record is preserved in
    slurmdbd across the Omnia upgrade.
    """
    log = TestLogger("Verify pre-upgrade job ID in sacct after upgrade")

    if not os.path.exists(UPGRADE_JOB_ID_FILE):
        log.skipped(
            "Pre-upgrade job ID file not found",
            f"Expected: {UPGRADE_JOB_ID_FILE}\nRun precheck tests before the upgrade.",
        )
        pytest.skip(f"Pre-upgrade job ID file not found: {UPGRADE_JOB_ID_FILE}")

    with open(UPGRADE_JOB_ID_FILE, "r", encoding="utf-8") as fh:
        job_id = fh.read().strip()

    if not job_id:
        log.skipped(
            "Empty job ID in pre-upgrade state file",
            f"Re-run precheck: {UPGRADE_JOB_ID_FILE}",
        )
        pytest.skip("Empty job ID in pre-upgrade state file")

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        log.skipped("No slurm_control_node in PXE mapping", "Check PXE mapping file")
        pytest.skip("No slurm_control_node in PXE mapping")

    control_hostname = control_nodes[0].get("hostname", "unknown")

    print(f"    Pre-upgrade Job ID : {job_id}", flush=True)
    print(f"    State file         : {UPGRADE_JOB_ID_FILE}", flush=True)
    print(f"    Control node       : {control_hostname}", flush=True)

    log.check(f"Querying sacct for pre-upgrade job ID {job_id} on {control_hostname}")

    result = verify_slurmdbd_data_preserved(host, job_id)

    if result.get("job_state"):
        print(f"    sacct job state    : {result['job_state']}", flush=True)

    if result["success"]:
        details = (
            f"✓ Job ID         : {job_id}\n"
            f"✓ sacct state    : {result['job_state']}\n"
            f"✓ slurmdbd accounting data preserved across upgrade"
        )
        log.passed(
            f"Pre-upgrade job {job_id} found in sacct (state: {result['job_state']})",
            details,
        )
    else:
        log.failed(
            f"Pre-upgrade job {job_id} not found in sacct after upgrade",
            result["error"],
        )
        assert False, (
            f"slurmdbd accounting data NOT preserved after upgrade.\n"
            f"Job ID {job_id} not found in sacct.\n"
            f"Error: {result['error']}\n\n"
            f"HOW TO FIX:\n"
            f"  1. Check slurmdbd service: systemctl status slurmdbd\n"
            f"  2. Check slurmdbd logs: journalctl -u slurmdbd -n 50\n"
            f"  3. Verify sacct manually: sacct -j {job_id}"
        )
