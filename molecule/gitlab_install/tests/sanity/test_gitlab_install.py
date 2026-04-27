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
GitLab Install Sanity Test Cases.

This module contains pytest test cases for verifying GitLab deployment.

Test cases:
1. Verify GitLab packages are installed
2. Verify GitLab server is reachable
3. Verify gitlab-runner container running
4. Verify gitlab-runner quadlet file exists
5. Verify gitlab-runner service is running
6. Verify GitLab URL is accessible
7. Verify GitLab services are running
8. Verify GitLab server meets resource requirements
9. Verify puma workers configuration
10. Verify sidekiq concurrency configuration
11. Verify GitLab project exists
12. Verify GitLab project visibility
13. Verify GitLab default branch
"""

import pytest

from automation_library.core import TestLogger
from automation_library.gitlab.functions import (
    skip_if_build_stream_not_enabled,
    skip_if_gitlab_host_not_configured,
    verify_gitlab_packages_installed,
    verify_gitlab_server_reachable,
    verify_gitlab_runner_container,
    verify_gitlab_runner_quadlet_exists,
    verify_gitlab_runner_service_running,
    verify_gitlab_url_accessible,
    verify_gitlab_services_running,
    verify_gitlab_resources,
    verify_puma_workers,
    verify_sidekiq_concurrency,
    verify_gitlab_project_exists,
    verify_gitlab_project_visibility,
    verify_gitlab_default_branch,
)
from automation_library.gitlab.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)


# =============================================================================
# GITLAB SERVER TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_gitlab_packages_installed(host):
    """
    Test Case 1: Verify GitLab packages are installed on GitLab server.

    Checks: gitlab-ce package
    """
    log = TestLogger(TEST_NAMES["gitlab_packages_installed"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab packages are installed")
    result = verify_gitlab_packages_installed(host)

    details = (
        f"Expected: {result['expected']}\n"
        f"Installed: {result['installed']}\n"
        f"Not installed: {result['not_installed']}"
    )

    if result["success"]:
        log.passed(
            LOG_MSGS["packages_installed"].format(packages=result['installed']),
            details
        )
    else:
        log.failed(
            LOG_MSGS["packages_not_installed"].format(packages=result['not_installed']),
            details
        )

    assert result["success"], ASSERT_MSGS["packages_not_installed"].format(
        packages=result['not_installed']
    )


@pytest.mark.sanity
@pytest.mark.order(2)
def test_gitlab_server_reachable(host):
    """
    Test Case 2: Verify GitLab server is reachable from omnia_core container.
    """
    log = TestLogger(TEST_NAMES["gitlab_server_reachable"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab server reachability")
    result = verify_gitlab_server_reachable(host)

    if result["success"]:
        log.passed(LOG_MSGS["server_reachable"].format(host=result['gitlab_host']))
    else:
        log.failed(LOG_MSGS["server_not_reachable"].format(host=result['gitlab_host']),
                   result["error"])

    assert result["success"], ASSERT_MSGS["server_not_reachable"].format(
        host=result['gitlab_host']
    )


@pytest.mark.sanity
@pytest.mark.order(3)
def test_gitlab_runner_container(host):
    """
    Test Case 3: Verify gitlab-runner container is running on GitLab server.
    """
    log = TestLogger(TEST_NAMES["gitlab_runner_container"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking gitlab-runner container on GitLab server")
    result = verify_gitlab_runner_container(host)

    if result["success"]:
        log.passed(
            LOG_MSGS["container_running"].format(status=result['status']),
            f"Container: {result['container']}"
        )
    else:
        log.failed(LOG_MSGS["container_not_running"], result["error"])

    assert result["success"], ASSERT_MSGS["container_not_running"]


@pytest.mark.sanity
@pytest.mark.order(4)
def test_gitlab_runner_quadlet_exists(host):
    """
    Test Case 4: Verify gitlab-runner quadlet file exists on GitLab server.
    """
    log = TestLogger(TEST_NAMES["gitlab_runner_quadlet_exists"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking gitlab-runner quadlet file")
    result = verify_gitlab_runner_quadlet_exists(host)

    if result["success"]:
        log.passed(LOG_MSGS["quadlet_exists"].format(path=result['quadlet_path']))
    else:
        log.failed(LOG_MSGS["quadlet_not_found"].format(path=result['quadlet_path']),
                   result["error"])

    assert result["success"], ASSERT_MSGS["quadlet_not_found"].format(
        path=result['quadlet_path']
    )


@pytest.mark.sanity
@pytest.mark.order(5)
def test_gitlab_runner_service_running(host):
    """
    Test Case 5: Verify gitlab-runner systemd service is running on GitLab server.
    """
    log = TestLogger(TEST_NAMES["gitlab_runner_service_running"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking gitlab-runner service status")
    result = verify_gitlab_runner_service_running(host)

    if result["success"]:
        log.passed(LOG_MSGS["service_running"].format(status=result['status']))
    else:
        log.failed(LOG_MSGS["service_not_running"].format(status=result['status']),
                   result["error"])

    assert result["success"], ASSERT_MSGS["service_not_running"]


@pytest.mark.sanity
@pytest.mark.order(6)
def test_gitlab_url_accessible(host):
    """
    Test Case 6: Verify GitLab URL is accessible from OIM server.
    """
    log = TestLogger(TEST_NAMES["gitlab_url_accessible"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab URL accessibility from OIM")
    result = verify_gitlab_url_accessible(host)

    if result["success"]:
        log.passed(
            LOG_MSGS["gitlab_accessible"].format(
                url=result['url'],
                code=result['http_code']
            )
        )
    else:
        log.failed(LOG_MSGS["gitlab_not_accessible"].format(url=result['url']))

    assert result["success"], ASSERT_MSGS["gitlab_not_accessible"].format(
        url=result['url'],
        code=result['http_code']
    )


@pytest.mark.sanity
@pytest.mark.order(7)
def test_gitlab_services_running(host):
    """
    Test Case 7: Verify all GitLab services are running.
    """
    log = TestLogger(TEST_NAMES["gitlab_services_running"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab services")
    result = verify_gitlab_services_running(host)

    details = (
        f"Running: {result['running_services']}\n"
        f"Not running: {result['not_running']}\n"
        f"Status:\n" + "\n".join(
            f"  {k}: {v}" for k, v in result['service_status'].items()
        )
    )

    if result["success"]:
        log.passed(
            LOG_MSGS["gitlab_services_ok"].format(count=len(result['running_services'])),
            details
        )
    else:
        log.failed(
            LOG_MSGS["gitlab_services_failed"].format(services=result['not_running']),
            details
        )

    assert result["success"], ASSERT_MSGS["gitlab_services_not_running"].format(
        services=result['not_running']
    )


@pytest.mark.sanity
@pytest.mark.order(8)
def test_gitlab_resources(host):
    """
    Test Case 8: Verify GitLab server meets minimum resource requirements.

    Checks: CPU cores, memory (GB), storage (GB)
    """
    log = TestLogger(TEST_NAMES["gitlab_resources"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab server resources")
    result = verify_gitlab_resources(host)

    details = (
        f"CPU: {result['actual']['cpu_cores']} cores "
        f"(required: {result['required']['min_cpu_cores']}) "
        f"{'✓' if result['checks']['cpu'] else '✗'}\n"
        f"Memory: {result['actual']['memory_gb']} GB "
        f"(required: {result['required']['min_memory_gb']}) "
        f"{'✓' if result['checks']['memory'] else '✗'}\n"
        f"Storage: {result['actual']['storage_gb']} GB "
        f"(required: {result['required']['min_storage_gb']}) "
        f"{'✓' if result['checks']['storage'] else '✗'}"
    )

    if result["success"]:
        log.passed(LOG_MSGS["resources_ok"], details)
    else:
        log.failed(LOG_MSGS["resources_insufficient"], details)

    if not result["checks"]["cpu"]:
        assert False, ASSERT_MSGS["cpu_insufficient"].format(
            required=result['required']['min_cpu_cores'],
            actual=result['actual']['cpu_cores']
        )
    if not result["checks"]["memory"]:
        assert False, ASSERT_MSGS["memory_insufficient"].format(
            required=result['required']['min_memory_gb'],
            actual=result['actual']['memory_gb']
        )
    if not result["checks"]["storage"]:
        assert False, ASSERT_MSGS["storage_insufficient"].format(
            required=result['required']['min_storage_gb'],
            actual=result['actual']['storage_gb']
        )


@pytest.mark.sanity
@pytest.mark.order(9)
def test_puma_workers(host):
    """
    Test Case 9: Verify puma workers are configured correctly.
    """
    log = TestLogger(TEST_NAMES["puma_workers"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking puma workers configuration")
    result = verify_puma_workers(host)

    details = f"Expected: {result['expected']}, Actual: {result['actual']}"

    if result["success"]:
        log.passed(
            LOG_MSGS["puma_workers_ok"].format(workers=result['actual']),
            details
        )
    else:
        log.failed(
            LOG_MSGS["puma_workers_mismatch"].format(
                expected=result['expected'],
                actual=result['actual']
            ),
            details
        )

    assert result["success"], ASSERT_MSGS["puma_workers_mismatch"].format(
        expected=result['expected'],
        actual=result['actual']
    )


@pytest.mark.sanity
@pytest.mark.order(10)
def test_sidekiq_concurrency(host):
    """
    Test Case 10: Verify sidekiq concurrency is configured correctly.
    """
    log = TestLogger(TEST_NAMES["sidekiq_concurrency"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking sidekiq concurrency configuration")
    result = verify_sidekiq_concurrency(host)

    details = f"Expected: {result['expected']}, Actual: {result['actual']}"

    if result["success"]:
        log.passed(
            LOG_MSGS["sidekiq_ok"].format(concurrency=result['actual']),
            details
        )
    else:
        log.failed(
            LOG_MSGS["sidekiq_mismatch"].format(
                expected=result['expected'],
                actual=result['actual']
            ),
            details
        )

    assert result["success"], ASSERT_MSGS["sidekiq_mismatch"].format(
        expected=result['expected'],
        actual=result['actual']
    )


# =============================================================================
# PROJECT TEST CASES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_gitlab_project_exists(host):
    """
    Test Case 11: Verify GitLab project exists.
    """
    log = TestLogger(TEST_NAMES["gitlab_project_exists"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab project")
    result = verify_gitlab_project_exists(host)

    if result["success"]:
        log.passed(
            LOG_MSGS["project_exists"].format(
                name=result['project_name'],
                id=result['project_id']
            )
        )
    else:
        log.failed(LOG_MSGS["project_not_found"].format(name=result['project_name']))

    assert result["success"], ASSERT_MSGS["project_not_found"].format(
        name=result['project_name']
    )


@pytest.mark.sanity
@pytest.mark.order(12)
def test_gitlab_project_visibility(host):
    """
    Test Case 12: Verify GitLab project visibility.
    """
    log = TestLogger(TEST_NAMES["gitlab_project_visibility"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab project visibility")
    result = verify_gitlab_project_visibility(host)

    if result["success"]:
        details = f"Expected: {result['expected']}, Actual: {result['actual']}"
        log.passed(
            LOG_MSGS["visibility_ok"].format(visibility=result['expected']),
            details
        )
    else:
        details = result["error"]
        if "not found" in result["error"].lower():
            log.failed(
                f"Cannot check visibility - project '{result['project_name']}' does not exist",
                details
            )
        else:
            log.failed(
                f"Visibility mismatch: expected {result['expected']}, actual {result['actual']}",
                details
            )

    assert result["success"], result["error"]


@pytest.mark.sanity
@pytest.mark.order(13)
def test_gitlab_default_branch(host):
    """
    Test Case 13: Verify GitLab default branch.
    """
    log = TestLogger(TEST_NAMES["gitlab_default_branch"])

    skip_if_build_stream_not_enabled(host, log)
    skip_if_gitlab_host_not_configured(host, log)

    log.check("Checking GitLab default branch")
    result = verify_gitlab_default_branch(host)

    if result["success"]:
        details = f"Expected: {result['expected']}, Actual: {result['actual']}"
        log.passed(
            LOG_MSGS["default_branch_ok"].format(branch=result['expected']),
            details
        )
    else:
        details = result["error"]
        if "not found" in result["error"].lower():
            log.failed(
                f"Cannot check default branch - project '{result['project_name']}' does not exist",
                details
            )
        else:
            log.failed(
                f"Default branch mismatch: expected {result['expected']}, "
                f"actual {result['actual']}",
                details
            )

    assert result["success"], result["error"]
