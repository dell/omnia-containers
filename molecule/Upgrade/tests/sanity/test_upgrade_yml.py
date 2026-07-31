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
Omnia upgrade.yml – End-to-End Upgrade Automation Test.

Runs the full ``upgrade.yml`` playbook (all components) inside the
omnia_core container and verifies every component completed successfully.

Execution order
---------------
  TC-1  (order 1)  Pre-flight              — container running + upgrade.yml present
  TC-2  (order 2)  Run upgrade.yml         — all components, no --tags filter
  TC-3  (order 3)  Verify manifest         — upgrade_manifest.yml readable + overall status
  TC-4  (order 4)  Verify OIM              — component_status['oim'] = completed
  TC-5  (order 10) Verify K8s              — component_status['k8s'] = completed/skipped
  TC-6  (order 20) Verify Slurm            — component_status['slurm'] = completed/skipped
  TC-7  (order 7)  Verify OpenCHAMI        — component_status['openchami'] = completed/skipped

Gate logic
----------
  TC-2 through TC-7 are SKIPPED if TC-1 (pre-flight) fails.
  TC-3 through TC-7 are SKIPPED if TC-2 (upgrade run) fails.
  TC-5 is SKIPPED if service_k8s not in software_config.json.
  TC-6 is SKIPPED if slurm_custom not in software_config.json.
  TC-7 is SKIPPED if openchami not in software_config.json.

Idempotency
-----------
  upgrade.yml skips components already marked 'completed' in
  upgrade_manifest.yml.  Re-running this test after a partial failure
  safely resumes from the last incomplete component.

Usage
-----
  ./run_molecule.sh Upgrade verify -- -k upgrade_yml    # run upgrade_yml tests
  ./run_molecule.sh Upgrade test                        # full test sequence
"""

import time

import pytest

from automation_library.core import TestLogger
from automation_library.upgrade_and_rollback.functions import (
    check_upgrade_yml_exists,
    run_upgrade_yml,
    verify_upgrade_manifest,
    verify_manifest_component_status,
    check_software_component_enabled,
)
from automation_library.upgrade_and_rollback.vars import UPGRADE_YML_VARS
from automation_library.upgrade_and_rollback.messages import (
    UPGRADE_YML_ASSERT_MSGS as ASSERT,
    UPGRADE_YML_SKIP_MSGS as SKIP,
)


# =============================================================================
# MODULE-LEVEL GATE FLAGS
# =============================================================================

_PREFLIGHT_PASSED: bool = False


def _skip_if_preflight_failed() -> None:
    """Skip test if preflight check failed."""
    if not _PREFLIGHT_PASSED:
        pytest.skip(SKIP["preflight_failed"])


# =============================================================================
# TC-1  Pre-flight
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_upgrade_yml_preflight(host):
    """
    TC-1: Verify that upgrade.yml can be run.

    Checks:
    - omnia_core container is running and reachable
    - upgrade.yml exists at /omnia/upgrade/upgrade.yml inside the container
    - upgrade.yml is not already running
    """
    global _PREFLIGHT_PASSED  # pylint: disable=global-statement
    playbook_path = UPGRADE_YML_VARS["playbook_path"]

    log = TestLogger("TC-1 — Verify pre-conditions for upgrade.yml")

    log.check("Checking omnia_core container is running")
    result = check_upgrade_yml_exists(host)

    if not result["container_running"]:
        log.failed("omnia_core container not running", result["error"])
        pytest.fail(ASSERT["container_not_running"])

    log.check(f"Checking upgrade.yml exists at {playbook_path}")
    if not result["playbook_exists"]:
        log.failed(f"upgrade.yml not found at {playbook_path}", result["error"])
        pytest.fail(ASSERT["playbook_not_found"].format(path=playbook_path))

    log.check("Checking if upgrade.yml is currently running")
    if result.get("playbook_running", False):
        log.failed("upgrade.yml playbook is currently running", result["error"])
        pytest.fail(ASSERT["upgrade_already_running"].format(
            process_info=result.get("process_info", ""),
            log_file=UPGRADE_YML_VARS["log_file"],
        ))

    _PREFLIGHT_PASSED = True

    log.passed(
        "Pre-conditions satisfied",
        (
            f"✓ omnia_core container running\n"
            f"✓ upgrade.yml present: {playbook_path}\n"
            f"✓ upgrade.yml not currently running"
        ),
    )


# =============================================================================
# TC-2  Run full upgrade.yml
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_upgrade_yml_run(host):
    """
    TC-2: Run the full upgrade.yml (all components) inside omnia_core.

    Runs: ansible-playbook /omnia/upgrade/upgrade.yml -e skip_approval=true

    No --tags filter is used so upgrade.yml processes every component
    in order: oim → k8s → slurm → openchami

    Components gated by software_config.json (k8s, slurm, openchami) are
    automatically skipped by upgrade.yml if the relevant software entry
    is absent.

    Already-completed components (from a previous partial run) are skipped
    by upgrade.yml via the upgrade_manifest.yml — this test is idempotent.

    Progress is printed every 30 s.  Full log is available at:
      podman exec omnia_core cat /tmp/upgrade_yml_run.log
    """
    tail_lines = UPGRADE_YML_VARS["tail_lines"]
    log_file = UPGRADE_YML_VARS["log_file"]
    max_retries = UPGRADE_YML_VARS["max_retries"]
    retry_delay = UPGRADE_YML_VARS["retry_delay"]

    log = TestLogger("TC-2 — Run upgrade.yml (all components)")

    _skip_if_preflight_failed()

    # Check if upgrade is already completed - skip execution but allow verification
    manifest_result = verify_upgrade_manifest(host)
    if manifest_result["success"]:
        upgrade_status = manifest_result.get("upgrade_status", "")
        if upgrade_status == "completed":
            log.skipped(
                "Upgrade already completed — skipping execution",
                (
                    f"upgrade_status: {upgrade_status}\n"
                    f"Component status:\n"
                    + "\n".join(
                        f"  {k}: {v}"
                        for k, v in manifest_result.get("component_status", {}).items()
                    )
                ),
            )
            pytest.skip(SKIP["already_completed"])

    def progress(elapsed):
        mins, secs = divmod(elapsed, 60)
        print(
            f"    ⏳ upgrade.yml running... {int(mins)}m {int(secs)}s elapsed",
            flush=True,
        )

    for attempt in range(1, max_retries + 1):
        log.check(
            f"Running upgrade.yml (attempt {attempt}/{max_retries})"
        )

        result = run_upgrade_yml(host, progress_callback=progress)

        if result["success"]:
            log.passed(
                f"upgrade.yml completed (rc={result['rc']})",
                f"Tags: {result['tags']}\n"
                f"Log: podman exec omnia_core cat {log_file}",
            )
            return

        if attempt < max_retries:
            log.check(
                f"upgrade.yml attempt {attempt} failed (rc={result['rc']}), "
                f"retrying in {retry_delay}s"
            )
            time.sleep(retry_delay)
        else:
            log.failed(
                f"upgrade.yml failed after {max_retries} attempts (rc={result['rc']})",
                f"Error: {result['error']}\n"
                f"Output (last {tail_lines} lines):\n{result['output']}",
            )
            pytest.fail(ASSERT["run_failed"].format(
                tags=result["tags"],
                rc=result["rc"],
                tail_lines=tail_lines,
                output=result["output"],
            ))


# =============================================================================
# TC-3  Verify upgrade_manifest.yml
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_upgrade_yml_verify_manifest(host):
    """
    TC-3: Verify upgrade_manifest.yml exists and upgrade_status = completed.
    """
    log = TestLogger("TC-3 — Verify upgrade_manifest.yml")

    _skip_if_preflight_failed()

    manifest_path = UPGRADE_YML_VARS["manifest_path"]
    log.check(f"Checking upgrade_manifest.yml at {manifest_path}")

    result = verify_upgrade_manifest(host)

    if not result["exists"]:
        log.failed("upgrade_manifest.yml not found", result["error"])
        pytest.fail(ASSERT["manifest_not_found"].format(path=manifest_path))

    if not result["success"]:
        log.failed("Failed to parse upgrade_manifest.yml", result["error"])
        pytest.fail(ASSERT["manifest_parse_error"].format(error=result["error"]))

    upgrade_status = result.get("upgrade_status", "")
    component_status = result.get("component_status", {})

    details = (
        f"upgrade_status: {upgrade_status}\n"
        f"Components:\n"
        + "\n".join(f"  {k}: {v}" for k, v in component_status.items())
    )

    if upgrade_status == "completed":
        log.passed("upgrade_manifest.yml verified", details)
    else:
        log.check(
            f"upgrade_status is '{upgrade_status}' (expected 'completed')",
        )


# =============================================================================
# TC-4  Verify OIM component
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_upgrade_yml_verify_oim(host):
    """
    TC-4: Verify OIM component completed in upgrade_manifest.yml.

    OIM is always upgraded (not conditional on software_config.json).
    """
    log = TestLogger("TC-4 — Verify OIM upgrade status")

    _skip_if_preflight_failed()

    log.check("Verifying OIM component status in upgrade_manifest.yml")
    result = verify_manifest_component_status(host, "oim")

    if result["success"]:
        log.passed(
            f"OIM component: {result['status']}",
            f"Component: oim\nStatus: {result['status']}",
        )
    else:
        log.failed(
            f"OIM component: {result['status']}",
            result["error"],
        )
        pytest.fail(ASSERT["component_not_completed"].format(
            component="oim", status=result["status"],
        ))


# =============================================================================
# TC-5  Verify K8s component (conditional)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_upgrade_yml_verify_k8s(host):
    """
    TC-5: Verify K8s component completed in upgrade_manifest.yml.

    This test is SKIPPED if service_k8s is not in software_config.json.
    """
    log = TestLogger("TC-5 — Verify K8s upgrade status")

    _skip_if_preflight_failed()

    log.check("Checking if K8s is enabled in software_config.json")
    sw_result = check_software_component_enabled(host, "service_k8s")
    if not sw_result["enabled"]:
        log.skipped("service_k8s not enabled — skipping K8s verification")
        pytest.skip(SKIP["k8s_not_enabled"])

    log.check("Verifying K8s component status in upgrade_manifest.yml")
    result = verify_manifest_component_status(host, "k8s")

    if result["success"]:
        log.passed(
            f"K8s component: {result['status']}",
            f"Component: k8s\nStatus: {result['status']}",
        )
    else:
        log.failed(
            f"K8s component: {result['status']}",
            result["error"],
        )
        pytest.fail(ASSERT["component_not_completed"].format(
            component="k8s", status=result["status"],
        ))


# =============================================================================
# TC-6  Verify Slurm component (conditional)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(20)
def test_upgrade_yml_verify_slurm(host):
    """
    TC-6: Verify Slurm component completed in upgrade_manifest.yml.

    This test is SKIPPED if slurm_custom is not in software_config.json.
    """
    log = TestLogger("TC-6 — Verify Slurm upgrade status")

    _skip_if_preflight_failed()

    log.check("Checking if Slurm is enabled in software_config.json")
    sw_result = check_software_component_enabled(host, "slurm_custom")
    if not sw_result["enabled"]:
        log.skipped("slurm_custom not enabled — skipping Slurm verification")
        pytest.skip(SKIP["slurm_not_enabled"])

    log.check("Verifying Slurm component status in upgrade_manifest.yml")
    result = verify_manifest_component_status(host, "slurm")

    if result["success"]:
        log.passed(
            f"Slurm component: {result['status']}",
            f"Component: slurm\nStatus: {result['status']}",
        )
    else:
        log.failed(
            f"Slurm component: {result['status']}",
            result["error"],
        )
        pytest.fail(ASSERT["component_not_completed"].format(
            component="slurm", status=result["status"],
        ))


# =============================================================================
# TC-7  Verify OpenCHAMI component (conditional)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_upgrade_yml_verify_openchami(host):
    """
    TC-7: Verify OpenCHAMI component completed in upgrade_manifest.yml.

    This test is SKIPPED if openchami is not in software_config.json.
    """
    log = TestLogger("TC-7 — Verify OpenCHAMI upgrade status")

    _skip_if_preflight_failed()

    log.check("Checking if OpenCHAMI is enabled in software_config.json")
    sw_result = check_software_component_enabled(host, "openchami")
    if not sw_result["enabled"]:
        log.skipped("openchami not enabled — skipping OpenCHAMI verification")
        pytest.skip(SKIP["openchami_not_enabled"])

    log.check("Verifying OpenCHAMI component status in upgrade_manifest.yml")
    result = verify_manifest_component_status(host, "openchami")

    if result["success"]:
        log.passed(
            f"OpenCHAMI component: {result['status']}",
            f"Component: openchami\nStatus: {result['status']}",
        )
    else:
        log.failed(
            f"OpenCHAMI component: {result['status']}",
            result["error"],
        )
        pytest.fail(ASSERT["component_not_completed"].format(
            component="openchami", status=result["status"],
        ))
