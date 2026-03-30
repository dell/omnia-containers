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
1. Verify Pulp container is running
2. Verify Pulp CLI connectivity (rpm repository list)
3. Verify Pulp API health (DB, workers, storage)
4. Verify software download results (software.csv)
5. Verify per-package download results (status.csv)
6. Verify all RPM repositories synced in Pulp
7. Verify all RPM distributions published
8. Verify all container image repositories synced
9. Verify all file repositories synced
10. Verify RPM content reachable via HTTPS (repomd.xml)
11. Verify all software_config.json RPM packages in Pulp
"""

from automation_library.core import TestLogger
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
    check_pulp_repositories_synced,
    check_pulp_distributions_published,
    check_container_repos_synced,
    check_file_repos_synced,
    check_pulp_content_accessible,
    check_software_packages_in_pulp,
)


# ---------------------------------------------------------------------------
# 1. Pulp container running
# ---------------------------------------------------------------------------
def test_pulp_container_running(host):
    container = TEST_VARS["pulp_container"]
    log = TestLogger(TEST_NAMES["pulp_container_running"])
    log.check(f"Verifying '{container}' container is running via podman ps")

    result = check_container_running(host, container)
    if result["success"]:
        log.passed(LOG_MSGS["container_running"].format(container=container), result["status"])
    else:
        log.failed(LOG_MSGS["container_not_running"].format(container=container), result.get("error"))

    assert result["success"], ASSERT_MSGS["container_not_running"].format(
        container=container,
        status=result.get("status", "unknown"),
    )


# ---------------------------------------------------------------------------
# 2. Pulp CLI connectivity
# ---------------------------------------------------------------------------
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
# 3. Pulp API health
# ---------------------------------------------------------------------------
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
# 4. Software download status (software.csv)
# ---------------------------------------------------------------------------
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
# 5. Per-software package status (status.csv per software)
# ---------------------------------------------------------------------------
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
# 6. RPM repositories synced
# ---------------------------------------------------------------------------
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
# 7. RPM distributions published
# ---------------------------------------------------------------------------
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
# 8. Container image repositories synced
# ---------------------------------------------------------------------------
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
# 9. File repositories synced
# ---------------------------------------------------------------------------
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
# 10. RPM content accessible via HTTPS (repomd.xml)
# ---------------------------------------------------------------------------
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
# 11. Software packages in Pulp
# ---------------------------------------------------------------------------
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
