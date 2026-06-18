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
Omnia Core Upgrade Test Cases.

End-to-end upgrade workflow for the omnia_core container from one Omnia
version to another (e.g., 2.1.0.0 → 2.2.0.0).

IMPORTANT:
  All tests FAIL if upgrade.operation in omnia_test_config.yml is not
  set to 'upgrade' (or 'rollback'). This prevents accidental execution.
  If TC-1 (pre-upgrade check) fails, all subsequent tests are SKIPPED.

Test cases (executed in order):
1. Verify omnia_core is running the FROM version
2. Clone repo, build core image, download omnia.sh
3. Run omnia.sh --upgrade (with 10s progress output, last 50 lines on finish)
4. Verify omnia_core upgraded to TO version and container is healthy
5. Verify backup directory created (configs, input, metadata, openchami)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.upgrade_and_rollback.functions import (
    validate_upgrade_versions,
    validate_versions,
    validate_config,
    check_backup_exists,
    check_pre_upgrade_container,
    clone_upgrade_repo,
    build_core_image,
    verify_podman_image,
    download_omnia_sh,
    run_omnia_upgrade,
    verify_backup_directory,
    verify_post_upgrade_state,
)
from automation_library.upgrade_and_rollback.vars import (
    UPGRADE_VARS,
    SUPPORTED_VERSIONS,
)
from automation_library.upgrade_and_rollback.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
    SKIP_MSGS,
)


# =============================================================================
# MODULE-LEVEL GATE: skip TCs 2-8 if TC-1 fails
# =============================================================================

_pre_upgrade_passed: bool = False


# =============================================================================
# HELPER: validate config + versions for upgrade
# =============================================================================

def _gate_operation(log: TestLogger) -> None:
    """
    Validate upgrade config and version ordering (current < new).
    Calls pytest.fail() if invalid so every test fails with a HOW-TO-FIX msg.
    """
    # Config completeness
    cfg = validate_config()
    if not cfg["success"]:
        for field in cfg.get("missing", []):
            print(
                f"    {LOG['config_missing_field'].format(field=field)}",
                flush=True,
            )
        for field in cfg.get("blank", []):
            print(
                f"    {LOG['config_blank_field'].format(field=field)}",
                flush=True,
            )
        log.failed("Config validation failed", cfg["error"])
        pytest.fail(
            ASSERT["config_validation_failed"].format(error=cfg["error"])
        )

    # Version ordering (current < new required for upgrade)
    upgrade_ver = validate_upgrade_versions()
    if not upgrade_ver["success"]:
        log.failed(
            LOG["version_order_invalid"].format(
                current=upgrade_ver["current_version"],
                new=upgrade_ver["new_version"],
            ),
            upgrade_ver["error"],
        )
        pytest.fail(
            ASSERT["version_order_invalid"].format(
                current=upgrade_ver["current_version"],
                new=upgrade_ver["new_version"],
            )
        )

    # Versions in supported list
    ver_result = validate_versions()
    if not ver_result["success"]:
        log.failed(
            LOG["version_unsupported"].format(
                version=(
                    f"{ver_result['current_version']}/"
                    f"{ver_result['new_version']}"
                ),
                supported=", ".join(SUPPORTED_VERSIONS),
            ),
            ver_result["error"],
        )
        pytest.fail(
            ASSERT["version_unsupported"].format(
                version=(
                    f"{ver_result['current_version']}/"
                    f"{ver_result['new_version']}"
                ),
                supported=", ".join(SUPPORTED_VERSIONS),
            )
        )


def _skip_if_pre_upgrade_failed() -> None:
    """Skip this test if TC-1 did not pass."""
    if not _pre_upgrade_passed:
        pytest.skip(SKIP_MSGS["pre_upgrade_failed"])


# =============================================================================
# TC-1: PRE-UPGRADE VERSION CHECK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_pre_upgrade_version(host):
    """
    Test Case 1: Verify omnia_core container is running the expected FROM
    version.  If already at target, check whether a backup exists and report.
    Sets _pre_upgrade_passed so subsequent tests know whether to run.
    """
    global _pre_upgrade_passed
    current_ver = UPGRADE_VARS["current_version"]
    new_ver = UPGRADE_VARS["new_version"]
    backup_path = UPGRADE_VARS["backup_path"]

    log = TestLogger(
        TEST_NAMES["pre_upgrade_version"].format(from_version=current_ver)
    )

    _gate_operation(log)

    log.check(LOG["checking_container"])
    result = check_pre_upgrade_container(host)

    # Print container fields individually (proper indent)
    print(
        f"    {LOG['container_name'].format(name=result['container_name'])}",
        flush=True,
    )
    print(
        f"    {LOG['container_image'].format(image=result['container_image'])}",
        flush=True,
    )
    print(
        f"    {LOG['container_status'].format(status=result['container_status'])}",
        flush=True,
    )

    state = result.get("state", "error")

    if state == "not_running":
        log.failed("omnia_core container is not running", result["error"])
        pytest.fail(ASSERT["container_not_running"])

    if state == "already_at_target":
        print(
            f"    {LOG['already_at_target'].format(version=result['version'])}",
            flush=True,
        )
        # Check if backup exists → was upgrade already performed?
        if check_backup_exists(host):
            print(
                f"    {LOG['already_at_target_backup_found'].format(path=backup_path)}",
                flush=True,
            )
            detail_msg = (
                f"Already at version {result['version']}.\n"
                f"Backup found at {backup_path} — upgrade was performed.\n"
                f"To re-test: rollback first, then run again."
            )
        else:
            print(
                f"    {LOG['already_at_target_no_backup'].format(version=result['version'])}",
                flush=True,
            )
            detail_msg = (
                f"Already at version {result['version']}.\n"
                f"No backup found — no upgrade possible."
            )
        log.failed(
            LOG["already_at_target"].format(version=result["version"]),
            detail_msg,
        )
        pytest.fail(
            ASSERT["already_at_target_version"].format(
                version=result["version"], from_version=current_ver,
            )
        )

    if state == "unexpected_version":
        log.failed("Unexpected container version", result["error"])
        pytest.fail(
            ASSERT["pre_upgrade_wrong_version"].format(
                expected=current_ver, actual=result["version"],
            )
        )

    # SUCCESS — mark gate so TCs 2-8 proceed
    _pre_upgrade_passed = True

    details = (
        f"✓ Container: {result['container_name']}\n"
        f"✓ Image:     {result['container_image']}\n"
        f"✓ Version:   {result['version']}\n"
        f"Ready for upgrade: {current_ver} → {new_ver}"
    )
    log.passed(
        LOG["current_version_ok"].format(version=result["version"]),
        details,
    )


# =============================================================================
# TC-2: CLONE REPO + BUILD CORE IMAGE + DOWNLOAD OMNIA.SH
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_build_and_prepare(host):
    """
    Test Case 2: Clone repo, build core image, download omnia.sh.
    Skipped if TC-1 failed.
    """
    core_tag = UPGRADE_VARS["core_tag"]
    omnia_branch = UPGRADE_VARS["omnia_branch"]
    branch = UPGRADE_VARS["repo_branch"]

    log = TestLogger(
        TEST_NAMES["build_and_prepare"].format(core_tag=core_tag)
    )

    _gate_operation(log)
    _skip_if_pre_upgrade_failed()

    # ---- Step 1: Clone ----
    log.check(LOG["clone_start"].format(branch=branch))
    clone_result = clone_upgrade_repo(host)
    if not clone_result["success"]:
        log.failed(
            LOG["clone_fail"].format(error=clone_result["error"]),
            clone_result["error"],
        )
        pytest.fail(
            ASSERT["clone_failed"].format(
                url=UPGRADE_VARS["repo_url"], branch=branch,
                path=UPGRADE_VARS["clone_path"],
                error=clone_result["error"],
            )
        )
    print(f"    {LOG['clone_ok']}", flush=True)

    # ---- Step 2: Build core image (with progress) ----
    print(
        f"    {LOG['build_start'].format(core_tag=core_tag)}",
        flush=True,
    )

    def _progress(elapsed: int) -> None:
        print(
            f"    {LOG['build_progress'].format(elapsed=elapsed)}",
            flush=True,
        )

    build_result = build_core_image(host, progress_callback=_progress)

    if not build_result["success"]:
        log.failed(
            LOG["build_fail"].format(rc=build_result.get("rc", "?")),
            build_result["error"],
        )
        pytest.fail(
            ASSERT["build_failed"].format(
                omnia_branch=omnia_branch,
                rc=build_result.get("rc", "?"),
            )
        )
    print(
        f"    {LOG['build_ok'].format(core_tag=core_tag)}",
        flush=True,
    )

    # ---- Step 3: Verify podman image ----
    img_result = verify_podman_image(host, core_tag)
    if img_result["success"]:
        print(
            f"    {LOG['image_found'].format(tag=core_tag)}",
            flush=True,
        )
    else:
        log.failed(
            LOG["image_not_found"].format(tag=core_tag),
            img_result["error"],
        )
        pytest.fail(
            ASSERT["image_not_found"].format(core_tag=core_tag)
        )

    # ---- Step 4: Download omnia.sh ----
    dl_result = download_omnia_sh(host)
    if dl_result["success"]:
        print(f"    {LOG['omnia_sh_download_ok']}", flush=True)
    else:
        log.failed(
            LOG["omnia_sh_download_fail"].format(
                error=dl_result["error"],
            ),
            dl_result["error"],
        )
        pytest.fail(
            ASSERT["omnia_sh_download_failed"].format(
                url=dl_result.get("url", "N/A"),
                error=dl_result["error"],
                path=dl_result.get("path", "N/A"),
            )
        )

    details = (
        f"✓ Repository cloned ({branch})\n"
        f"✓ Core image built: omnia_core:{core_tag}\n"
        f"✓ omnia.sh downloaded"
    )
    log.passed(LOG["build_ok"].format(core_tag=core_tag), details)


# =============================================================================
# TC-3: RUN OMNIA.SH --UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_run_upgrade(host):
    """
    Test Case 3: Run omnia.sh --upgrade with automated interactive input.
    Prints progress every 10 seconds. Shows last 50 lines on completion.
    Skipped if TC-1 failed.
    """
    current_ver = UPGRADE_VARS["current_version"]
    new_ver = UPGRADE_VARS["new_version"]

    log = TestLogger(
        TEST_NAMES["run_upgrade"].format(
            from_version=current_ver, to_version=new_ver,
        )
    )

    _gate_operation(log)
    _skip_if_pre_upgrade_failed()

    log.check(LOG["upgrade_start"])
    print(
        f"    {LOG['upgrade_input'].format(input='1 then y')}",
        flush=True,
    )

    def _progress(elapsed: int) -> None:
        print(
            f"    {LOG['upgrade_progress'].format(elapsed=elapsed)}",
            flush=True,
        )

    result = run_omnia_upgrade(host, progress_callback=_progress)
    output = result.get("output", "")

    if result["success"]:
        details = f"✓ Upgrade {current_ver} → {new_ver} completed"
        if output:
            details += "\n\nUpgrade output (last 50 lines):\n" + output
        log.passed(LOG["upgrade_ok"], details)
    else:
        fail_details = result["error"]
        if output:
            fail_details += "\n\nUpgrade output (last 50 lines):\n" + output
        log.failed(
            LOG["upgrade_fail"].format(rc=result.get("rc", "?")),
            fail_details,
        )
        pytest.fail(
            ASSERT["upgrade_failed"].format(
                rc=result.get("rc", "?"),
                output=output[-500:] if len(output) > 500 else output,
                omnia_sh_path=result.get("omnia_sh_path", ""),
            )
        )


# =============================================================================
# TC-4: VERIFY POST-UPGRADE STATE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_verify_post_upgrade(host):
    """
    Test Case 4: Verify omnia_core upgraded and container is healthy.
    Skipped if TC-1 failed.
    """
    current_ver = UPGRADE_VARS["current_version"]
    new_ver = UPGRADE_VARS["new_version"]

    log = TestLogger(
        TEST_NAMES["verify_post_upgrade"].format(to_version=new_ver)
    )

    _gate_operation(log)
    _skip_if_pre_upgrade_failed()

    log.check(LOG["post_container_check"])
    result = verify_post_upgrade_state(host)

    # Print container fields individually (proper indent)
    print(
        f"    {LOG['post_container_name'].format(name=result['container_name'])}",
        flush=True,
    )
    print(
        f"    {LOG['post_container_image'].format(image=result['container_image'])}",
        flush=True,
    )
    print(
        f"    {LOG['post_container_status'].format(status=result['container_status'])}",
        flush=True,
    )

    if result["container_running"]:
        print(f"    {LOG['post_container_running']}", flush=True)
    else:
        print(f"    {LOG['post_container_not_running']}", flush=True)

    if result["version"]:
        if result["version"] == new_ver:
            print(
                f"    {LOG['post_version_ok'].format(version=result['version'], expected=new_ver)}",
                flush=True,
            )
        else:
            msg = LOG['post_version_fail'].format(
                expected=new_ver, actual=result['version'],
            )
            print(f"    {msg}", flush=True)

    if not result["container_running"]:
        log.failed(LOG["post_container_not_running"], result["error"])
        pytest.fail(ASSERT["post_container_not_running"])

    if not result["success"]:
        log.failed(
            LOG["post_version_fail"].format(
                expected=new_ver,
                actual=result.get("version", "unknown"),
            ),
            result["error"],
        )
        pytest.fail(
            ASSERT["post_upgrade_version_mismatch"].format(
                expected=new_ver,
                actual=result.get("version", "unknown"),
            )
        )

    details = (
        f"✓ Container: {result['container_name']}\n"
        f"✓ Image:     {result['container_image']}\n"
        f"✓ Version:   {result['version']}\n"
        f"Upgrade complete: {current_ver} → {new_ver}"
    )
    log.passed(
        LOG["post_version_ok"].format(
            version=result["version"], expected=new_ver,
        ),
        details,
    )


# =============================================================================
# TC-5: VERIFY BACKUP DIRECTORY
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_verify_backup_directory(host):
    """
    Test Case 5: Verify backup directory created with expected subdirs.

    Checks: configs/, input/, metadata/, openchami/
    """
    backup_path = UPGRADE_VARS["backup_path"]
    log = TestLogger(TEST_NAMES["verify_backup_directory"])

    _gate_operation(log)
    _skip_if_pre_upgrade_failed()

    log.check(LOG["backup_dir_check"].format(path=backup_path))
    result = verify_backup_directory(host)

    if result.get("error", "").startswith("Backup directory not found"):
        log.failed(
            LOG["backup_dir_not_found"].format(path=backup_path),
            result["error"],
        )
        pytest.fail(ASSERT["backup_dir_missing"].format(path=backup_path))

    sub_dirs = result.get("sub_dirs", {})
    lines = []
    for name, exists in sub_dirs.items():
        if exists:
            lines.append(f"✓ {name}/")
        else:
            lines.append(f"✗ {name}/")
    details = "\n".join(lines)

    if result["success"]:
        log.passed(
            LOG["backup_dir_found"].format(path=backup_path),
            details,
        )
    else:
        missing = [k for k, v in sub_dirs.items() if not v]
        log.failed(f"Missing: {', '.join(missing)}", details)
        pytest.fail(
            ASSERT["backup_dir_incomplete"].format(
                path=backup_path,
                missing=", ".join(missing),
            )
        )
