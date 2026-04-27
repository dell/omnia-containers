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
GitLab Cleanup Sanity Test Cases.

This module contains pytest test cases for verifying GitLab cleanup.

Test cases:
1. Verify GitLab packages are removed
2. Verify gitlab-runner container removed
3. Verify gitlab-runner quadlet file removed
4. Verify gitlab-runner service stopped
5. Verify GitLab URL is not accessible
6. Verify GitLab directories removed
7. Verify GitLab services stopped
"""

import pytest

from automation_library.core import TestLogger
from automation_library.gitlab.functions import (
    skip_if_build_stream_not_enabled,
    skip_if_gitlab_host_not_configured,
    verify_gitlab_packages_removed,
    verify_gitlab_runner_container_removed,
    verify_gitlab_runner_quadlet_removed,
    verify_gitlab_runner_service_stopped,
    verify_gitlab_url_not_accessible,
    verify_gitlab_directories_removed,
    verify_gitlab_services_stopped,
)
from automation_library.gitlab.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)


# =============================================================================
# GITLAB CLEANUP TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_gitlab_packages_removed(host):
    """
    Test Case 1: Verify GitLab packages are removed after cleanup.

    Checks: gitlab-ce package
    """
    log = TestLogger(TEST_NAMES["gitlab_packages_removed"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab packages are removed")
    result = verify_gitlab_packages_removed(host)

    details = (
        f"Expected removed: {result['expected_removed']}\n"
        f"Removed: {result['removed']}\n"
        f"Still installed: {result['still_installed']}"
    )

    if result["success"]:
        log.passed(
            LOG_MSGS["packages_removed"].format(packages=result['removed']),
            details
        )
    else:
        log.failed(
            LOG_MSGS["packages_still_installed"].format(packages=result['still_installed']),
            details
        )

    assert result["success"], ASSERT_MSGS["packages_still_installed"].format(
        packages=result['still_installed']
    )


@pytest.mark.sanity
@pytest.mark.order(2)
def test_gitlab_runner_container_removed(host):
    """
    Test Case 2: Verify gitlab-runner container is removed after cleanup.
    """
    log = TestLogger(TEST_NAMES["gitlab_runner_container_removed"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking gitlab-runner container is removed")
    result = verify_gitlab_runner_container_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["container_removed"])
    else:
        log.failed(LOG_MSGS["container_still_exists"], result["error"])

    assert result["success"], ASSERT_MSGS["container_still_exists"]


@pytest.mark.sanity
@pytest.mark.order(3)
def test_gitlab_runner_quadlet_removed(host):
    """
    Test Case 3: Verify gitlab-runner quadlet file is removed after cleanup.
    """
    log = TestLogger(TEST_NAMES["gitlab_runner_quadlet_removed"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking gitlab-runner quadlet file is removed")
    result = verify_gitlab_runner_quadlet_removed(host)

    if result["success"]:
        log.passed(LOG_MSGS["quadlet_removed"])
    else:
        log.failed(
            LOG_MSGS["quadlet_still_exists"].format(path=result['quadlet_path']),
            result["error"]
        )

    assert result["success"], ASSERT_MSGS["quadlet_still_exists"].format(
        path=result['quadlet_path']
    )


@pytest.mark.sanity
@pytest.mark.order(4)
def test_gitlab_runner_service_stopped(host):
    """
    Test Case 4: Verify gitlab-runner service is stopped after cleanup.
    """
    log = TestLogger(TEST_NAMES["gitlab_runner_service_stopped"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking gitlab-runner service is stopped")
    result = verify_gitlab_runner_service_stopped(host)

    if result["success"]:
        log.passed(LOG_MSGS["service_stopped"])
    else:
        log.failed(
            LOG_MSGS["service_still_running"].format(status=result['status']),
            result["error"]
        )

    assert result["success"], ASSERT_MSGS["service_still_running"]


@pytest.mark.sanity
@pytest.mark.order(5)
def test_gitlab_url_not_accessible(host):
    """
    Test Case 5: Verify GitLab URL is not accessible after cleanup.
    """
    log = TestLogger(TEST_NAMES["gitlab_url_not_accessible"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab URL is not accessible")
    result = verify_gitlab_url_not_accessible(host)

    if result["success"]:
        log.passed(LOG_MSGS["gitlab_not_accessible_cleanup"])
    else:
        log.failed(
            LOG_MSGS["gitlab_still_accessible"].format(url=result['url']),
            result["error"]
        )

    assert result["success"], ASSERT_MSGS["gitlab_still_accessible"].format(
        url=result['url']
    )


@pytest.mark.sanity
@pytest.mark.order(6)
def test_gitlab_directories_removed(host):
    """
    Test Case 6: Verify GitLab directories are removed after cleanup.
    """
    log = TestLogger(TEST_NAMES["gitlab_directories_removed"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab directories are removed")
    result = verify_gitlab_directories_removed(host)

    details = (
        f"Removed: {result['removed']}\n"
        f"Still existing: {result['existing']}"
    )

    if result["success"]:
        log.passed(LOG_MSGS["directories_removed"], details)
    else:
        log.failed(
            LOG_MSGS["directories_still_exist"].format(dirs=result['existing']),
            details
        )

    assert result["success"], ASSERT_MSGS["directories_still_exist"].format(
        dirs=result['existing']
    )


@pytest.mark.sanity
@pytest.mark.order(7)
def test_gitlab_services_stopped(host):
    """
    Test Case 7: Verify all GitLab services are stopped after cleanup.
    """
    log = TestLogger(TEST_NAMES["gitlab_services_stopped"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab services are stopped")
    result = verify_gitlab_services_stopped(host)

    if result["success"]:
        log.passed(LOG_MSGS["services_stopped"])
    else:
        log.failed(
            LOG_MSGS["services_still_running"].format(services=result['running']),
            result["error"]
        )

    assert result["success"], ASSERT_MSGS["services_still_running"].format(
        services=result['running']
    )
