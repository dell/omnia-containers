# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Local Repo Test Cases.

This module contains pytest test cases for verifying local_repo (Pulp) deployment.

Test cases:
1. Verify build_stream pipeline stage 'create-local-repository' COMPLETED (when enabled)
2. Verify Pulp container is running
3. Verify Pulp CLI connectivity (rpm repository list)
4. Verify Pulp API health (DB, workers, storage)
5. Verify repo metadata (repomd.xml) present for all distributions
6. Verify software download results (software.csv)
7. Verify per-package download results (status.csv)
8. Verify all RPM repositories synced in Pulp
9. Verify all RPM distributions published
10. Verify all container image repositories synced
11. Verify all file repositories synced
12. Verify RPM content reachable via HTTPS (repomd.xml)
13. Verify all software_config.json RPM packages in Pulp
"""

import pytest

from automation_library.core import (
    TestLogger,
    is_build_stream_enabled,
    get_build_stream_job_id,
    STAGE_CREATE_LOCAL_REPO,
)
from automation_library.local_repo.messages.local_repo_msgs import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
    TEST_VARS,
)
from automation_library.local_repo.functions.local_repo_func import (
    check_container_running,
    check_pulp_cli_repository_list,
    check_pulp_api_status,
    check_software_download_status,
    check_per_software_package_status,
    check_pulp_repo_metadata_present,
    check_pulp_repositories_synced,
    check_pulp_distributions_published,
    check_container_repos_synced,
    check_file_repos_synced,
    check_pulp_content_accessible,
    check_software_packages_in_pulp,
)
from molecule.conftest import build_stream_job_state


# ---------------------------------------------------------------------------
# 1. Build stream job stage validation
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(1)
def test_build_stream_job_stage(host):
    """
    Test 1: When build_stream is enabled, verify the create-local-repository
    pipeline stage completed successfully before running any Pulp checks.

    - Reads build_stream_job_id override from omnia_test_config.yml if set.
    - Falls back to the latest job in build_stream_db otherwise.
    - Prints the exact DB stage_state if not COMPLETED.
    - Skipped when build_stream is disabled.
    """
    stage = STAGE_CREATE_LOCAL_REPO
    if not is_build_stream_enabled(host):
        pytest.skip(LOG_MSGS["build_stream_disabled_skip"])

    log = TestLogger(TEST_NAMES["build_stream_job_stage"].format(stage=stage))

    result = get_build_stream_job_id(host, stage_name=stage)
    job_id = result.get("job_id") or "unknown"
    job_state = result.get("job_state") or "NOT FOUND"
    source = result.get("source", "database")

    # Set shared state so autouse fixture in conftest.py can skip remaining tests
    build_stream_job_state["checked"] = True
    build_stream_job_state["success"] = result["success"]
    build_stream_job_state["job_id"] = job_id
    build_stream_job_state["job_state"] = job_state
    build_stream_job_state["error"] = result.get("error", "")

    log.check(LOG_MSGS["build_stream_job_checking"].format(stage=stage, source=source))

    if result["success"]:
        log.passed(
            LOG_MSGS["build_stream_job_ok"].format(
                stage=stage, job_id=job_id, source=source
            )
        )
    else:
        log.failed(
            LOG_MSGS["build_stream_job_failed"].format(
                stage=stage, state=job_state, job_id=job_id
            ),
            result.get("error", "")
        )
        # Use pytest.fail() so this test shows as FAILED (not skipped)
        # Remaining tests will be SKIPPED via autouse fixture
        pytest.fail(
            ASSERT_MSGS["build_stream_job_stage_failed"].format(
                stage=stage, job_id=job_id, state=job_state
            )
        )


# ---------------------------------------------------------------------------
# 2. Pulp container running
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(2)
def test_pulp_container_running(host):
    container = TEST_VARS["pulp_container"]
    log = TestLogger(TEST_NAMES["pulp_container_running"])
    log.check(f"Verifying '{container}' container is running via podman ps")

    result = check_container_running(host, container)
    if result["success"]:
        log.passed(LOG_MSGS["container_running"].format(container=container), result["status"])
    else:
        log.failed(
            LOG_MSGS["container_not_running"].format(container=container),
            result.get("error")
        )

    assert result["success"], ASSERT_MSGS["container_not_running"].format(
        container=container,
        status=result.get("status", "unknown"),
    )


# ---------------------------------------------------------------------------
# 3. Pulp CLI connectivity
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(3)
def test_pulp_cli_repository_list(host):
    log = TestLogger(TEST_NAMES["pulp_cli_repo_list"])
    log.check("Running 'pulp rpm repository list' inside omnia_core container")

    result = check_pulp_cli_repository_list(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_cli_ok"], result.get("details") or "")
    else:
        log.failed(LOG_MSGS["pulp_cli_fail"], result.get("error") or "")

    assert result["success"], ASSERT_MSGS["pulp_cli_failed"]


# ---------------------------------------------------------------------------
# 4. Pulp API health
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(4)
def test_pulp_api_status(host):
    log = TestLogger(TEST_NAMES["pulp_api_status"])
    log.check("Querying 'pulp status' for DB connection, workers, content apps, storage")

    result = check_pulp_api_status(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_api_healthy"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pulp_api_unhealthy"], details)
        assert False, ASSERT_MSGS["pulp_api_unhealthy"].format(details=details)


# ---------------------------------------------------------------------------
# 5. Pulp repo metadata (repomd.xml) present
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(5)
def test_pulp_repo_metadata_present(host):
    """
    Test 5: Verify repomd.xml metadata is accessible for all published RPM distributions.

    Maps to: pulp_metadata_verification, validate_repo_metadata_creation_and_storage.
    """
    log = TestLogger(TEST_NAMES["repo_metadata_present"])
    log.check("Curling repomd.xml for each RPM distribution to verify metadata presence")

    result = check_pulp_repo_metadata_present(host)
    if result["success"]:
        log.passed(LOG_MSGS["repo_metadata_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["repo_metadata_fail"], details)
        assert False, ASSERT_MSGS["repo_metadata_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 6. Software download status (software.csv)
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(6)
def test_software_download_status(host):
    log = TestLogger(TEST_NAMES["software_download_status"])
    log.check("Parsing software.csv per architecture for download success/failure")

    result = check_software_download_status(host)
    if result["success"]:
        log.passed(LOG_MSGS["sw_download_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["sw_download_failed"], details)
        assert False, ASSERT_MSGS["sw_download_failed"].format(details=details)


# ---------------------------------------------------------------------------
# 7. Per-software package status (status.csv per software)
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(7)
def test_per_software_package_status(host):
    log = TestLogger(TEST_NAMES["per_software_package_status"])
    log.check("Parsing per-software status.csv for individual package download results")

    result = check_per_software_package_status(host)
    if result["success"]:
        log.passed(LOG_MSGS["pkg_status_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pkg_status_failed"], details)
        assert False, ASSERT_MSGS["pkg_status_failed"].format(details=details)


# ---------------------------------------------------------------------------
# 8. RPM repositories synced
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(8)
def test_pulp_repositories_synced(host):
    log = TestLogger(TEST_NAMES["pulp_repositories_synced"])
    log.check("Querying Pulp RPM repos for latest_version_href (sync indicator)")

    result = check_pulp_repositories_synced(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_repos_synced"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pulp_repos_not_synced"], details)
        assert False, ASSERT_MSGS["pulp_repos_not_synced"].format(details=details)


# ---------------------------------------------------------------------------
# 9. RPM distributions published
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(9)
def test_pulp_distributions_published(host):
    log = TestLogger(TEST_NAMES["pulp_distributions_published"])
    log.check("Querying Pulp RPM distributions for publication/repository attachment")

    result = check_pulp_distributions_published(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_distributions_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pulp_distributions_missing"], details)
        assert False, ASSERT_MSGS["pulp_distributions_missing"].format(details=details)


# ---------------------------------------------------------------------------
# 10. Container image repositories synced
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(10)
def test_container_repos_synced(host):
    log = TestLogger(TEST_NAMES["container_repos_synced"])
    log.check("Querying Pulp container repos for latest_version_href (sync indicator)")

    result = check_container_repos_synced(host)
    if result["success"]:
        log.passed(LOG_MSGS["container_repos_synced"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["container_repos_not_synced"], details)
        assert False, ASSERT_MSGS["container_repos_not_synced"].format(details=details)


# ---------------------------------------------------------------------------
# 11. File repositories synced
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(11)
def test_file_repos_synced(host):
    log = TestLogger(TEST_NAMES["file_repos_synced"])
    log.check("Querying Pulp file repos for latest_version_href (sync indicator)")

    result = check_file_repos_synced(host)
    if result["success"]:
        log.passed(LOG_MSGS["file_repos_synced"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["file_repos_not_synced"], details)
        assert False, ASSERT_MSGS["file_repos_not_synced"].format(details=details)


# ---------------------------------------------------------------------------
# 12. RPM content accessible via HTTPS (repomd.xml)
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(12)
def test_pulp_content_accessible(host):
    log = TestLogger(TEST_NAMES["pulp_content_accessible"])
    log.check("Curling repomd.xml for each RPM distribution base_path")

    result = check_pulp_content_accessible(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_content_accessible"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pulp_content_not_accessible"], details)
        assert False, ASSERT_MSGS["pulp_content_not_accessible"].format(details=details)


# ---------------------------------------------------------------------------
# 13. Software packages in Pulp
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(13)
def test_software_packages_in_pulp(host):
    log = TestLogger(TEST_NAMES["software_packages_in_pulp"])
    log.check("Loading software_config.json, extracting RPM packages, verifying each in Pulp")

    result = check_software_packages_in_pulp(host)

    if result["success"]:
        # Show full details with all individual package names
        details = result.get("details") or ""
        log.passed(LOG_MSGS["software_packages_ok"], details)
        return

    if "config" in (result.get("error") or "").lower():
        log.failed(LOG_MSGS["software_config_error"], result.get("error") or "")
        assert False, ASSERT_MSGS["software_config_error"].format(
            error=result.get("error") or ""
        )

    details = result.get("details") or result.get("error") or ""
    missing_count = result.get("missing_packages", 0)
    log.failed(
        LOG_MSGS["software_packages_missing"],
        f"Missing: {missing_count} packages\n{details}",
    )
    assert False, ASSERT_MSGS["software_packages_missing"].format(details=details)
