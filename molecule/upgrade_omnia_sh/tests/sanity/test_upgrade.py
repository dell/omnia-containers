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
Omnia Upgrade Test Cases.

End-to-end upgrade workflow from one Omnia version to another
(e.g., 2.1.0.0 → 2.2.0.0).

Test cases (executed in order):
1. Verify current omnia_core is running the FROM version (e.g., 2.1.0.0)
2. Clone omnia-artifactory (new version) to upgrade clone path
3. Build new omnia_core container image
4. Run omnia.sh --upgrade
5. Verify backup folder created
6. Verify omnia_core upgraded to TO version (e.g., 2.2.0.0)
7. Verify no old (FROM version) container running
"""

import pytest

from automation_library.core import TestLogger, check_container_running
from automation_library.upgrade.functions import (
    get_current_omnia_version,
    verify_pre_upgrade_state,
    clone_upgrade_artifactory,
    build_upgrade_core_image,
    run_omnia_upgrade,
    verify_backup_folder,
    verify_post_upgrade_version,
    verify_no_old_container,
)
from automation_library.upgrade.vars import UPGRADE_VARS
from automation_library.upgrade.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG,
    TEST_ASSERT_MSGS as ASSERT,
    SKIP_MSGS,
)


# =============================================================================
# TC-1: PRE-UPGRADE VERSION CHECK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_pre_upgrade_version(host):
    """
    Test Case 1: Verify omnia_core container is running the expected FROM version.

    Reads oim_metadata.yml inside omnia_core container and checks omnia_version.
    If already at target version:
      - With backup folder → cluster was already upgraded (skip)
      - Without backup folder → deployed at target version directly (skip)
    """
    from_version = UPGRADE_VARS["upgrade_from_version"]
    to_version = UPGRADE_VARS["upgrade_to_version"]

    log = TestLogger(
        TEST_NAMES["pre_upgrade_version"].format(from_version=from_version)
    )

    log.check(LOG["checking_version"])

    result = verify_pre_upgrade_state(host)

    if not result["success"]:
        # Check if already at target version (informational skip)
        if result["state"] in ("already_upgraded", "already_at_target"):
            version = result["version"]
            has_backup = result["has_backup"]
            if has_backup:
                log.skipped(
                    LOG["already_upgraded_with_backup"].format(version=version),
                    f"Backup folder exists — cluster was previously upgraded"
                )
            else:
                log.skipped(
                    LOG["already_upgraded"].format(version=version),
                    f"No backup folder — cluster deployed at {version} directly"
                )
            pytest.skip(
                ASSERT["already_at_target_version"].format(
                    version=version, has_backup=has_backup
                )
            )

        # Container not running or unexpected version
        if result["state"] == "error":
            log.failed("Pre-upgrade check failed", result["error"])
            assert False, ASSERT["container_not_running"]

        log.failed("Unexpected version", result["error"])
        assert False, ASSERT["pre_upgrade_wrong_version"].format(
            expected=from_version, actual=result["version"]
        )

    # Build details
    metadata = result.get("metadata", {})
    details_lines = [
        f"✓ omnia_core container running",
        f"✓ omnia_version: {result['version']}",
        f"  oim_hostname: {metadata.get('oim_hostname', 'N/A')}",
        f"  oim_crt: {metadata.get('oim_crt', 'N/A')}",
        f"  oim_shared_path: {metadata.get('oim_shared_path', 'N/A')}",
        f"  omnia_share_option: {metadata.get('omnia_share_option', 'N/A')}",
        f"",
        f"Ready for upgrade: {from_version} → {to_version}",
    ]
    details = "\n".join(details_lines)

    log.passed(
        LOG["current_version_ok"].format(version=result["version"]),
        details,
    )


# =============================================================================
# TC-2: CLONE OMNIA-ARTIFACTORY
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_clone_upgrade_artifactory(host):
    """
    Test Case 2: Clone omnia-artifactory for the new version.

    Clones the configured repo/branch to the upgrade clone path.
    Verifies build_images.sh exists in the cloned repo.
    """
    to_version = UPGRADE_VARS["upgrade_to_version"]
    repo_url = UPGRADE_VARS["upgrade_repo_url"]
    branch = UPGRADE_VARS["upgrade_repo_branch"]
    clone_path = UPGRADE_VARS["upgrade_clone_path"]

    log = TestLogger(
        TEST_NAMES["clone_upgrade_artifactory"].format(to_version=to_version)
    )

    log.check(LOG["clone_start"].format(branch=branch, path=clone_path))

    result = clone_upgrade_artifactory(host)

    if result["success"]:
        details_lines = [
            f"✓ Repository cloned successfully",
            f"  URL: {repo_url}",
            f"  Branch: {branch}",
            f"  Path: {clone_path}",
            f"  build_images.sh: present",
        ]
        log.passed(
            LOG["clone_ok"].format(path=clone_path),
            "\n".join(details_lines),
        )
    else:
        log.failed(
            LOG["clone_fail"].format(error=result["error"]),
            result["error"],
        )
        assert False, ASSERT["clone_failed"].format(
            url=repo_url, branch=branch, path=clone_path,
            error=result["error"],
        )


# =============================================================================
# TC-3: BUILD CORE IMAGE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_build_upgrade_core_image(host):
    """
    Test Case 3: Build the new omnia_core container image.

    Runs: ./build_images.sh core omnia_branch=<branch> core_tag=<tag>
    Verifies the image exists in podman images after build.
    """
    to_version = UPGRADE_VARS["upgrade_to_version"]
    omnia_branch = UPGRADE_VARS["omnia_branch"]
    core_tag = UPGRADE_VARS["core_tag"]
    clone_path = UPGRADE_VARS["upgrade_clone_path"]

    log = TestLogger(
        TEST_NAMES["build_core_image"].format(to_version=to_version)
    )

    log.check(
        LOG["build_start"].format(omnia_branch=omnia_branch, core_tag=core_tag)
    )

    result = build_upgrade_core_image(host)

    if result["success"]:
        details_lines = [
            f"✓ Core image built successfully",
            f"  Image: {result.get('image_name', 'omnia_core')}",
            f"  Tag: {core_tag}",
            f"  omnia_branch: {omnia_branch}",
        ]
        log.passed(
            LOG["build_ok"].format(core_tag=core_tag),
            "\n".join(details_lines),
        )
    else:
        log.failed(
            LOG["build_fail"].format(error=result["error"]),
            result["error"],
        )
        assert False, ASSERT["build_failed"].format(
            omnia_branch=omnia_branch, core_tag=core_tag,
            clone_path=clone_path, error=result["error"],
        )


# =============================================================================
# TC-4: RUN OMNIA.SH --UPGRADE
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_run_omnia_upgrade(host):
    """
    Test Case 4: Run omnia.sh --upgrade.

    Executes the upgrade command with automatic confirmation.
    Verifies the command completes with exit code 0.
    """
    from_version = UPGRADE_VARS["upgrade_from_version"]
    to_version = UPGRADE_VARS["upgrade_to_version"]
    clone_path = UPGRADE_VARS["upgrade_clone_path"]

    log = TestLogger(
        TEST_NAMES["run_upgrade"].format(
            from_version=from_version, to_version=to_version,
        )
    )

    log.check(LOG["upgrade_start"])

    result = run_omnia_upgrade(host)

    if result["success"]:
        # Show last 20 lines of output for context
        output_lines = result.get("output", "").strip().split("\n")
        tail_lines = output_lines[-20:] if len(output_lines) > 20 else output_lines
        details = "\n".join([
            f"✓ omnia.sh --upgrade completed successfully",
            f"  Path: {clone_path}/omnia.sh",
            f"",
            f"Output (last {len(tail_lines)} lines):",
        ] + [f"  {line}" for line in tail_lines])

        log.passed(LOG["upgrade_ok"], details)
    else:
        log.failed(
            LOG["upgrade_fail"].format(error=result["error"]),
            result.get("output", ""),
        )
        assert False, ASSERT["upgrade_failed"].format(
            error=result["error"],
            omnia_sh_path=f"{clone_path}/omnia.sh",
        )


# =============================================================================
# TC-5: VERIFY BACKUP FOLDER
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_verify_backup_folder(host):
    """
    Test Case 5: Verify backup folder created during upgrade.

    Checks that a backup directory exists under the omnia shared path
    containing the pre-upgrade data.
    """
    backup_base = UPGRADE_VARS["backup_base_path"]

    log = TestLogger(TEST_NAMES["verify_backup"])

    result = verify_backup_folder(host)

    if result["success"]:
        backup_path = result["backup_path"]
        all_paths = result.get("all_backup_paths", [backup_path])
        contents = result.get("contents", [])

        details_lines = [f"✓ Backup folder found: {backup_path}"]
        if len(all_paths) > 1:
            details_lines.append(f"  All backup paths found:")
            for p in all_paths:
                details_lines.append(f"    - {p}")

        if contents:
            details_lines.append(f"  Contents ({len(contents)} items):")
            for item in contents[:10]:
                details_lines.append(f"    {item}")
            if len(contents) > 10:
                details_lines.append(f"    ... and {len(contents) - 10} more")

        log.passed(
            LOG["backup_found"].format(path=backup_path),
            "\n".join(details_lines),
        )
    else:
        log.failed(
            LOG["backup_not_found"].format(base_path=backup_base),
            result["error"],
        )
        assert False, ASSERT["backup_missing"].format(base_path=backup_base)


# =============================================================================
# TC-6: VERIFY POST-UPGRADE VERSION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_verify_post_upgrade_version(host):
    """
    Test Case 6: Verify omnia_core is now running the target version.

    Reads oim_metadata.yml and confirms omnia_version matches the
    upgrade target version.
    """
    from_version = UPGRADE_VARS["upgrade_from_version"]
    to_version = UPGRADE_VARS["upgrade_to_version"]

    log = TestLogger(
        TEST_NAMES["verify_post_upgrade_version"].format(to_version=to_version)
    )

    result = verify_post_upgrade_version(host)

    if result["success"]:
        metadata = result.get("metadata", {})
        details_lines = [
            f"✓ omnia_core upgraded to {to_version}",
            f"  Previous version: {from_version}",
            f"  Current version: {result['actual']}",
            f"  oim_hostname: {metadata.get('oim_hostname', 'N/A')}",
            f"  oim_shared_path: {metadata.get('oim_shared_path', 'N/A')}",
        ]
        log.passed(
            LOG["post_version_ok"].format(version=to_version),
            "\n".join(details_lines),
        )
    else:
        log.failed(
            LOG["post_version_fail"].format(
                expected=to_version, actual=result.get("actual", "unknown"),
            ),
            result["error"],
        )
        assert False, ASSERT["post_upgrade_version_mismatch"].format(
            expected=to_version, actual=result.get("actual", "unknown"),
        )


# =============================================================================
# TC-7: VERIFY NO OLD CONTAINER RUNNING
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_verify_no_old_container(host):
    """
    Test Case 7: Verify no old omnia_core container is still running.

    After upgrade, only one omnia_core container should be running
    and it should be the new version. No leftover 2.1 containers.
    """
    from_version = UPGRADE_VARS["upgrade_from_version"]
    to_version = UPGRADE_VARS["upgrade_to_version"]

    log = TestLogger(
        TEST_NAMES["verify_no_old_container"].format(from_version=from_version)
    )

    result = verify_no_old_container(host)

    running = result.get("running_containers", [])
    all_containers = result.get("all_containers", [])

    details_lines = [f"Running omnia_core containers: {len(running)}"]
    for c in running:
        details_lines.append(
            f"  ✓ {c['name']} (ID: {c['id'][:12]}) "
            f"image={c.get('image', 'N/A')} status={c.get('status', 'N/A')}"
        )

    stopped = [c for c in all_containers if c not in running]
    if stopped:
        details_lines.append(f"Stopped containers: {len(stopped)}")
        for c in stopped:
            details_lines.append(
                f"  - {c['name']} (ID: {c['id'][:12]}) "
                f"image={c.get('image', 'N/A')} status={c.get('status', 'N/A')}"
            )

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            LOG["no_old_container_ok"].format(version=from_version),
            details,
        )
    else:
        log.failed(
            LOG["old_container_still_running"].format(details=result["error"]),
            details,
        )
        assert False, ASSERT["old_container_running"].format(
            details=result["error"],
        )
