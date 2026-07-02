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

"""Slurm Upgrade Precheck Test Cases.

Test cases to verify Slurm cluster state before Omnia upgrade:
  TC-1 - Submit sbatch job on 1 compute node and persist job ID for postcheck
"""

import os

import pytest
from automation_library.core import TestLogger
from automation_library.slurm.functions.slurm_func import (
    get_slurm_control_nodes,
    get_slurm_nodes,
    submit_upgrade_sbatch_job,
)

UPGRADE_JOB_ID_FILE = "/tmp/omnia_upgrade_slurm_job_id.txt"


@pytest.mark.sanity
@pytest.mark.order(1)
def test_slurm_upgrade_precheck_sbatch_job(host):
    """
    TC-1: Submit a basic sbatch job on 1 compute node before upgrade.

    Verifies Slurm can submit and complete a job prior to the upgrade.
    Persists the job ID to UPGRADE_JOB_ID_FILE so the postcheck can
    confirm slurmdbd accounting data is preserved across the upgrade.
    """
    log = TestLogger("Submit pre-upgrade sbatch job on 1 compute node")

    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        log.skipped("No slurm_control_node in PXE mapping", "Check PXE mapping file")
        pytest.skip("No slurm_control_node in PXE mapping")

    worker_nodes = get_slurm_nodes(host)
    if not worker_nodes:
        log.skipped("No slurm_node in PXE mapping", "Check PXE mapping file")
        pytest.skip("No slurm_node in PXE mapping")

    control_hostname = control_nodes[0].get("hostname", "unknown")
    log.check(
        f"Submitting 1-node sbatch job from control node: {control_hostname} "
        f"({len(worker_nodes)} worker node(s) available)"
    )

    result = submit_upgrade_sbatch_job(host)

    if result.get("submit_node"):
        print(f"    Submit node  : {result['submit_node']}", flush=True)
    if result.get("job_id"):
        print(f"    Job ID       : {result['job_id']}", flush=True)
    if result.get("job_state"):
        print(f"    Job state    : {result['job_state']}", flush=True)

    if not result["success"]:
        log.failed("Pre-upgrade sbatch job failed", result["error"])
        assert False, result["error"]

    job_id = result["job_id"]

    # Persist job ID to state file for postcheck
    with open(UPGRADE_JOB_ID_FILE, "w", encoding="utf-8") as fh:
        fh.write(job_id)

    print(f"    State file   : {UPGRADE_JOB_ID_FILE}", flush=True)

    details = (
        f"✓ Submit node          : {result['submit_node']}\n"
        f"✓ Job ID               : {job_id}\n"
        f"✓ Final state          : {result['job_state']}\n"
        f"✓ Job ID persisted to  : {UPGRADE_JOB_ID_FILE}"
    )
    log.passed(
        f"Pre-upgrade sbatch job completed and job ID persisted (JobID: {job_id})",
        details,
    )
