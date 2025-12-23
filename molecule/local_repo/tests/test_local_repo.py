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
Testinfra tests for local_repo verification.

Validations:
- Pulp container is running
- Pulp CLI commands work
- status.csv indicates all packages downloaded successfully
- software_config.json packages exist in Pulp
- Pulp API status is healthy
- Pulp repositories are synced
- Pulp distributions are published
- No failed tasks in Pulp
- Pulp content is accessible via HTTP
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
    check_status_csv_all_packages_downloaded,
    check_software_packages_in_pulp,
    check_pulp_api_status,
    check_pulp_repositories_synced,
    check_pulp_distributions_published,
    check_pulp_no_failed_tasks,
    check_pulp_content_accessible,
)


def test_pulp_container_running(host):
    container = TEST_VARS["pulp_container"]
    log = TestLogger(TEST_NAMES["pulp_container_running"])
    log.check(f"Checking container: {container}")

    result = check_container_running(host, container)
    if result["success"]:
        log.passed(LOG_MSGS["container_running"].format(container=container), result["status"])
    else:
        log.failed(LOG_MSGS["container_not_running"].format(container=container), result.get("error"))

    assert result["success"], ASSERT_MSGS["container_not_running"].format(
        container=container,
        status=result.get("status", "unknown"),
    )


def test_pulp_cli_repository_list(host):
    log = TestLogger(TEST_NAMES["pulp_cli_repo_list"])
    log.check("Running pulp command inside omnia_core")

    result = check_pulp_cli_repository_list(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_cli_ok"], result.get("details") or "")
    else:
        log.failed(LOG_MSGS["pulp_cli_fail"], result.get("error") or "")

    assert result["success"], ASSERT_MSGS["pulp_cli_failed"]


def test_status_csv_all_packages_downloaded(host):
    log = TestLogger(TEST_NAMES["status_csv"])
    log.check("Validating status.csv inside omnia_core")

    result = check_status_csv_all_packages_downloaded(host)
    if result["success"]:
        log.passed(LOG_MSGS["status_csv_no_failures"], (result.get("details") or "").strip())
        return

    roots = ", ".join(TEST_VARS.get("status_search_roots", []))
    if result.get("error") == "status.csv not found":
        log.failed(LOG_MSGS["status_csv_missing"], roots)
        assert False, ASSERT_MSGS["status_csv_missing"].format(roots=roots)

    details = result.get("details") or result.get("error") or ""
    log.failed(LOG_MSGS["status_csv_has_failures"], details)
    assert False, ASSERT_MSGS["status_csv_failed"].format(details=details)


def test_software_packages_in_pulp(host):
    """
    Verify that all packages defined in software_config.json exist in Pulp.
    
    This test:
    1. Reads software_config.json from omnia_core container
    2. Loads corresponding config/<arch>/<os>/<version>/<software>.json files
    3. Extracts all RPM package names and their expected repos
    4. Verifies each package exists in Pulp using 'pulp rpm content list'
    """
    log = TestLogger(TEST_NAMES["software_packages_in_pulp"])
    log.check("Parsing software_config.json and verifying packages in Pulp")

    result = check_software_packages_in_pulp(host)
    
    if result["success"]:
        summary = f"Found: {result.get('found_packages', 0)}/{result.get('total_packages', 0)} packages"
        log.passed(LOG_MSGS["software_packages_ok"], summary)
        return

    # Handle config load errors
    if "config" in (result.get("error") or "").lower():
        log.failed(LOG_MSGS["software_config_error"], result.get("error") or "")
        assert False, ASSERT_MSGS["software_config_error"].format(error=result.get("error") or "")

    # Handle missing packages
    details = result.get("details") or result.get("error") or ""
    missing_count = result.get("missing_packages", 0)
    log.failed(
        LOG_MSGS["software_packages_missing"],
        f"Missing: {missing_count} packages\n{details}"
    )
    assert False, ASSERT_MSGS["software_packages_missing"].format(details=details)


def test_pulp_api_status(host):
    """
    Verify Pulp API status is healthy.
    
    This test:
    1. Runs 'pulp status' command
    2. Checks database connection is active
    3. Verifies online workers are available
    """
    log = TestLogger(TEST_NAMES["pulp_api_status"])
    log.check("Checking Pulp API status (database, workers)")
    
    result = check_pulp_api_status(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_api_healthy"], result.get("details") or "")
    else:
        log.failed(LOG_MSGS["pulp_api_unhealthy"], result.get("details") or result.get("error") or "")
        assert False, ASSERT_MSGS["pulp_api_unhealthy"].format(details=result.get("details") or result.get("error") or "")


def test_pulp_repositories_synced(host):
    """
    Verify all Pulp RPM repositories are synced.
    
    This test:
    1. Lists all RPM repositories
    2. Checks each has a latest_version_href (indicating sync completed)
    """
    log = TestLogger(TEST_NAMES["pulp_repositories_synced"])
    log.check("Checking Pulp repositories sync status")
    
    result = check_pulp_repositories_synced(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_repos_synced"], result.get("details") or "")
    else:
        log.failed(LOG_MSGS["pulp_repos_not_synced"], result.get("details") or "")
        assert False, ASSERT_MSGS["pulp_repos_not_synced"].format(details=result.get("details") or result.get("error") or "")


def test_pulp_distributions_published(host):
    """
    Verify Pulp RPM distributions are published.
    
    This test:
    1. Lists all RPM distributions
    2. Checks each has a publication or repository attached
    """
    log = TestLogger(TEST_NAMES["pulp_distributions_published"])
    log.check("Checking Pulp distributions publication status")
    
    result = check_pulp_distributions_published(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_distributions_ok"], result.get("details") or "")
    else:
        log.failed(LOG_MSGS["pulp_distributions_missing"], result.get("details") or "")
        assert False, ASSERT_MSGS["pulp_distributions_missing"].format(details=result.get("details") or result.get("error") or "")


def test_pulp_no_failed_tasks(host):
    """
    Verify no failed tasks in Pulp task queue.
    
    This test:
    1. Lists failed tasks in Pulp
    2. Fails if any failed tasks are found
    """
    log = TestLogger(TEST_NAMES["pulp_no_failed_tasks"])
    log.check("Checking for failed tasks in Pulp")
    
    result = check_pulp_no_failed_tasks(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_no_failed_tasks"], result.get("details") or "")
    else:
        log.failed(LOG_MSGS["pulp_has_failed_tasks"], result.get("details") or "")
        assert False, ASSERT_MSGS["pulp_failed_tasks"].format(details=result.get("details") or result.get("error") or "")


def test_pulp_content_accessible(host):
    """
    Verify Pulp content is accessible via HTTP.
    
    This test:
    1. Gets a distribution's base_path
    2. Attempts to access repomd.xml via HTTP
    3. Verifies content serving pipeline is working
    """
    log = TestLogger(TEST_NAMES["pulp_content_accessible"])
    log.check("Checking Pulp content accessibility via HTTP")
    
    result = check_pulp_content_accessible(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_content_accessible"], result.get("details") or "")
    else:
        log.failed(LOG_MSGS["pulp_content_not_accessible"], result.get("details") or "")
        assert False, ASSERT_MSGS["pulp_content_not_accessible"].format(details=result.get("details") or result.get("error") or "")
