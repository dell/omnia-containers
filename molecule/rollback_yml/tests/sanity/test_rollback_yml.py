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
Omnia rollback.yml - End-to-End Rollback Automation Test.

Runs the full ``rollback.yml`` playbook (all components) inside the
omnia_core container and verifies every component rolled back
successfully.

Execution order
---------------
  TC-1  (order 1)  Pre-flight          - container running + rollback.yml
  TC-2  (order 2)  Lock check          - no upgrade in progress
  TC-3  (order 3)  Run rollback.yml    - all components, reverse order
  TC-4  (order 4)  Verify manifest     - rollback_manifest.yml readable
  TC-5  (order 5)  Verify Slurm        - component_status[slurm]
  TC-6  (order 6)  Verify K8s          - component_status[k8s]
  TC-7  (order 7)  Verify Build Stream - component_status[build_stream]
  TC-8  (order 8)  Verify OIM          - component_status[oim]

Gate logic
----------
  TC-2 through TC-8 are SKIPPED if TC-1 (pre-flight) fails.
  TC-4 through TC-8 are SKIPPED if TC-3 (rollback run) fails.
  TC-5 is SKIPPED if slurm_custom not in software_config.json.
  TC-6 is SKIPPED if service_k8s not in software_config.json.
  TC-7 is SKIPPED if build_stream not in software_config.json.

Usage
-----
  ./run_molecule.sh rollback_yml verify -- -k rollback_yml
  ./run_molecule.sh rollback_yml test
"""

import time

import pytest

from automation_library.core import TestLogger
from automation_library.upgrade_and_rollback.functions import (
    check_rollback_yml_exists,
    check_upgrade_lock,
    run_rollback_yml,
    verify_rollback_manifest,
    verify_rollback_manifest_component_status,
    check_rollback_software_component_enabled,
)
from automation_library.upgrade_and_rollback.vars import (
    ROLLBACK_YML_VARS,
)
from automation_library.upgrade_and_rollback.messages import (
    ROLLBACK_YML_ASSERT_MSGS as ASSERT,
    ROLLBACK_YML_SKIP_MSGS as SKIP,
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
def test_rollback_yml_preflight(host):
    """
    TC-1: Verify that rollback.yml can be run.

    Checks:
    - omnia_core container is running and reachable
    - rollback.yml exists inside the container
    - rollback.yml is not already running
    """
    global _PREFLIGHT_PASSED  # pylint: disable=global-statement
    playbook_path = ROLLBACK_YML_VARS["playbook_path"]

    log = TestLogger(
        "TC-1 - Verify pre-conditions for rollback.yml"
    )

    log.check("Checking omnia_core container is running")
    result = check_rollback_yml_exists(host)

    if not result["container_running"]:
        log.failed(
            "omnia_core container not running",
            result["error"],
        )
        pytest.fail(ASSERT["container_not_running"])

    log.check(
        f"Checking rollback.yml exists at {playbook_path}"
    )
    if not result["playbook_exists"]:
        log.failed(
            f"rollback.yml not found at {playbook_path}",
            result["error"],
        )
        pytest.fail(ASSERT["playbook_not_found"].format(
            path=playbook_path,
        ))

    log.check(
        "Checking if rollback.yml is currently running"
    )
    if result.get("playbook_running", False):
        log.failed(
            "rollback.yml playbook is currently running",
            result["error"],
        )
        pytest.fail(ASSERT["rollback_already_running"].format(
            process_info=result.get("process_info", ""),
            log_file=ROLLBACK_YML_VARS["log_file"],
        ))

    _PREFLIGHT_PASSED = True

    log.passed(
        "Pre-conditions satisfied",
        (
            f"container running\n"
            f"rollback.yml present: {playbook_path}\n"
            f"rollback.yml not currently running"
        ),
    )


# =============================================================================
# TC-2  Verify no upgrade in progress
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_rollback_yml_lock_check(host):
    """
    TC-2: Verify no upgrade is currently in progress.

    Checks that the upgrade lock file does not exist.
    Rollback should not run while an upgrade is active.
    """
    log = TestLogger(
        "TC-2 - Verify no upgrade in progress"
    )

    _skip_if_preflight_failed()

    lock_path = ROLLBACK_YML_VARS["upgrade_lock_path"]
    log.check(f"Checking upgrade lock at {lock_path}")

    result = check_upgrade_lock(host)

    if result["lock_exists"]:
        log.failed(
            "Upgrade lock exists - upgrade in progress",
            f"Lock file: {lock_path}",
        )
        pytest.fail(ASSERT["upgrade_in_progress"].format(
            lock_path=lock_path,
        ))

    log.passed(
        "No upgrade in progress",
        f"Lock file not found: {lock_path}",
    )


# =============================================================================
# TC-3  Run full rollback.yml
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_rollback_yml_run(host):
    """
    TC-3: Run the full rollback.yml (all components) inside omnia_core.

    Runs: ansible-playbook /omnia/upgrade/rollback.yml
          -e skip_approval=true

    Components are rolled back in reverse order:
      slurm -> k8s -> build_stream -> oim

    Components gated by software_config.json are automatically
    skipped by rollback.yml if the relevant software entry is absent.

    Progress is printed every 30s.
    """
    tail_lines = ROLLBACK_YML_VARS["tail_lines"]
    log_file = ROLLBACK_YML_VARS["log_file"]
    max_retries = ROLLBACK_YML_VARS["max_retries"]
    retry_delay = ROLLBACK_YML_VARS["retry_delay"]

    log = TestLogger(
        "TC-3 - Run rollback.yml (all components)"
    )

    _skip_if_preflight_failed()

    # Check if rollback is already completed
    manifest_result = verify_rollback_manifest(host)
    if manifest_result["success"]:
        rollback_status = manifest_result.get(
            "rollback_status", "",
        )
        if rollback_status == "completed":
            component_lines = "\n".join(
                f"  {k}: {v}"
                for k, v in manifest_result.get(
                    "component_status", {},
                ).items()
            )
            log.skipped(
                "Rollback already completed",
                (
                    f"rollback_status: {rollback_status}\n"
                    f"Component status:\n{component_lines}"
                ),
            )
            pytest.skip(SKIP["already_completed"])

    def progress(elapsed):
        mins, secs = divmod(elapsed, 60)
        print(
            f"    rollback.yml running... "
            f"{int(mins)}m {int(secs)}s elapsed",
            flush=True,
        )

    for attempt in range(1, max_retries + 1):
        log.check(
            f"Running rollback.yml "
            f"(attempt {attempt}/{max_retries})"
        )

        result = run_rollback_yml(
            host, progress_callback=progress,
        )

        if result["success"]:
            log.passed(
                f"rollback.yml completed (rc={result['rc']})",
                (
                    f"Tags: {result['tags']}\n"
                    f"Log: podman exec omnia_core "
                    f"cat {log_file}"
                ),
            )
            return

        if attempt < max_retries:
            rc = result["rc"]
            log.check(
                f"rollback.yml attempt {attempt} "
                f"failed (rc={rc}), "
                f"retrying in {retry_delay}s"
            )
            time.sleep(retry_delay)
        else:
            rc = result["rc"]
            output = result["output"]
            log.failed(
                f"rollback.yml failed after "
                f"{max_retries} attempts (rc={rc})",
                (
                    f"Error: {result['error']}\n"
                    f"Output (last {tail_lines} lines):\n"
                    f"{output}"
                ),
            )
            pytest.fail(ASSERT["run_failed"].format(
                tags=result["tags"],
                rc=rc,
                tail_lines=tail_lines,
                output=output,
            ))


# =============================================================================
# TC-4  Verify rollback_manifest.yml
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_rollback_yml_verify_manifest(host):
    """
    TC-4: Verify rollback_manifest.yml exists and
    rollback_status = completed.
    """
    log = TestLogger(
        "TC-4 - Verify rollback_manifest.yml"
    )

    _skip_if_preflight_failed()

    manifest_path = ROLLBACK_YML_VARS["manifest_path"]
    log.check(
        f"Checking rollback_manifest.yml at {manifest_path}"
    )

    result = verify_rollback_manifest(host)

    if not result["exists"]:
        log.failed(
            "rollback_manifest.yml not found",
            result["error"],
        )
        pytest.fail(ASSERT["manifest_not_found"].format(
            path=manifest_path,
        ))

    if not result["success"]:
        log.failed(
            "Failed to parse rollback_manifest.yml",
            result["error"],
        )
        pytest.fail(ASSERT["manifest_parse_error"].format(
            error=result["error"],
        ))

    rollback_status = result.get("rollback_status", "")
    component_status = result.get("component_status", {})

    component_lines = "\n".join(
        f"  {k}: {v}" for k, v in component_status.items()
    )
    details = (
        f"rollback_status: {rollback_status}\n"
        f"Components:\n{component_lines}"
    )

    if rollback_status == "completed":
        log.passed(
            "rollback_manifest.yml verified", details,
        )
    else:
        log.check(
            f"rollback_status is '{rollback_status}' "
            f"(expected 'completed')",
        )


# =============================================================================
# TC-5  Verify Slurm rollback (conditional)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_rollback_yml_verify_slurm(host):
    """
    TC-5: Verify Slurm component completed in
    rollback_manifest.yml.

    This test is SKIPPED if slurm_custom is not in
    software_config.json.
    """
    log = TestLogger(
        "TC-5 - Verify Slurm rollback status"
    )

    _skip_if_preflight_failed()

    log.check(
        "Checking if Slurm is enabled in "
        "software_config.json"
    )
    sw_result = check_rollback_software_component_enabled(
        host, "slurm_custom",
    )
    if not sw_result["enabled"]:
        log.skipped(
            "slurm_custom not enabled - "
            "skipping Slurm verification"
        )
        pytest.skip(SKIP["slurm_not_enabled"])

    log.check(
        "Verifying Slurm component status "
        "in rollback_manifest.yml"
    )
    result = verify_rollback_manifest_component_status(
        host, "slurm",
    )

    if result["success"]:
        log.passed(
            f"Slurm component: {result['status']}",
            f"Component: slurm\n"
            f"Status: {result['status']}",
        )
    else:
        log.failed(
            f"Slurm component: {result['status']}",
            result["error"],
        )
        pytest.fail(
            ASSERT["component_not_completed"].format(
                component="slurm",
                status=result["status"],
            )
        )


# =============================================================================
# TC-6  Verify K8s rollback (conditional)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_rollback_yml_verify_k8s(host):
    """
    TC-6: Verify K8s component completed in
    rollback_manifest.yml.

    This test is SKIPPED if service_k8s is not in
    software_config.json.
    """
    log = TestLogger(
        "TC-6 - Verify K8s rollback status"
    )

    _skip_if_preflight_failed()

    log.check(
        "Checking if K8s is enabled in "
        "software_config.json"
    )
    sw_result = check_rollback_software_component_enabled(
        host, "service_k8s",
    )
    if not sw_result["enabled"]:
        log.skipped(
            "service_k8s not enabled - "
            "skipping K8s verification"
        )
        pytest.skip(SKIP["k8s_not_enabled"])

    log.check(
        "Verifying K8s component status "
        "in rollback_manifest.yml"
    )
    result = verify_rollback_manifest_component_status(
        host, "k8s",
    )

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
        pytest.fail(
            ASSERT["component_not_completed"].format(
                component="k8s",
                status=result["status"],
            )
        )


# =============================================================================
# TC-7  Verify Build Stream rollback (conditional)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_rollback_yml_verify_build_stream(host):
    """
    TC-7: Verify Build Stream component completed in
    rollback_manifest.yml.

    This test is SKIPPED if build_stream is not in
    software_config.json.
    """
    log = TestLogger(
        "TC-7 - Verify Build Stream rollback status"
    )

    _skip_if_preflight_failed()

    log.check(
        "Checking if Build Stream is enabled in "
        "software_config.json"
    )
    sw_result = check_rollback_software_component_enabled(
        host, "build_stream",
    )
    if not sw_result["enabled"]:
        log.skipped(
            "build_stream not enabled - "
            "skipping Build Stream verification"
        )
        pytest.skip(SKIP["build_stream_not_enabled"])

    log.check(
        "Verifying build_stream component status "
        "in rollback_manifest.yml"
    )
    result = verify_rollback_manifest_component_status(
        host, "build_stream",
    )

    if result["success"]:
        log.passed(
            f"Build Stream component: {result['status']}",
            f"Component: build_stream\n"
            f"Status: {result['status']}",
        )
    else:
        log.failed(
            f"Build Stream component: {result['status']}",
            result["error"],
        )
        pytest.fail(
            ASSERT["component_not_completed"].format(
                component="build_stream",
                status=result["status"],
            )
        )


# =============================================================================
# TC-8  Verify OIM rollback
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_rollback_yml_verify_oim(host):
    """
    TC-8: Verify OIM component completed in
    rollback_manifest.yml.

    OIM is always rolled back (not conditional on
    software_config.json).
    """
    log = TestLogger(
        "TC-8 - Verify OIM rollback status"
    )

    _skip_if_preflight_failed()

    log.check(
        "Verifying OIM component status "
        "in rollback_manifest.yml"
    )
    result = verify_rollback_manifest_component_status(
        host, "oim",
    )

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
        pytest.fail(
            ASSERT["component_not_completed"].format(
                component="oim",
                status=result["status"],
            )
        )
