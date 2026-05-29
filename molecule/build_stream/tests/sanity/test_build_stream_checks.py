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
Build Stream - Infrastructure Checks Test Cases.

Test cases for verifying build_stream infrastructure:
1. Build stream enabled check
2. Build stream API health check
3. PostgreSQL database tables check
4. GitLab server running check
5. GitLab runner running check

These tests run BEFORE pipeline tests to ensure infrastructure is ready.
"""

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    check_build_stream_health,
    verify_postgres_tables,
    verify_gitlab_server_running,
    verify_gitlab_runner_running,
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# TEST 1: BUILD STREAM ENABLED CHECK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(1)
def test_build_stream_enabled(host):
    """
    Test 1: Verify build_stream is enabled in build_stream_config.yml.

    This is the first test - if build_stream is not enabled, all other
    tests in this module will be skipped.
    """
    log = TestLogger(TEST_NAMES["build_stream_enabled"])

    log.check("Checking if build_stream is enabled in build_stream_config.yml")

    if is_build_stream_enabled(host):
        log.passed(TEST_LOG_MSGS["build_stream_enabled_ok"])
    else:
        log.failed(
            TEST_LOG_MSGS["build_stream_enabled_fail"],
            "enable_build_stream is false or not set in build_stream_config.yml"
        )
        pytest.fail(TEST_ASSERT_MSGS["build_stream_not_enabled"])


# =============================================================================
# TEST 2: BUILD STREAM API HEALTH CHECK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(2)
def test_build_stream_health(host):
    """
    Test 2: Verify build_stream API /health endpoint returns healthy.

    Checks that the omnia_build_stream container is running and responding.
    """
    log = TestLogger(TEST_NAMES["build_stream_health"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    log.check("Checking build_stream API health endpoint")

    result = check_build_stream_health(host)

    if result["success"]:
        log.passed(TEST_LOG_MSGS["health_ok"], result.get("details", ""))
    else:
        log.failed(
            TEST_LOG_MSGS["health_fail"].format(error=result["error"]),
            f"URL: {result.get('url', 'N/A')}\nStatus: {result.get('status', 'N/A')}"
        )
        pytest.fail(TEST_ASSERT_MSGS["health_failed"].format(error=result["error"]))


# =============================================================================
# TEST 3: POSTGRESQL DATABASE TABLES CHECK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(3)
def test_postgres_tables(host):
    """
    Test 3: Verify all expected tables exist in build_stream_db.

    Checks that omnia_postgres container has all required tables.
    """
    log = TestLogger(TEST_NAMES["postgres_tables"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    log.check("Checking PostgreSQL database tables in build_stream_db")

    result = verify_postgres_tables(host)

    if result["success"]:
        log.passed(TEST_LOG_MSGS["postgres_ok"], result.get("details", ""))
    else:
        log.failed(
            TEST_LOG_MSGS["postgres_fail"].format(missing=", ".join(result.get("missing_tables", []))),
            result.get("details", "")
        )
        pytest.fail(TEST_ASSERT_MSGS["postgres_failed"].format(error=result["error"]))


# =============================================================================
# TEST 4: GITLAB SERVER RUNNING CHECK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(4)
def test_gitlab_server_running(host):
    """
    Test 4: Verify GitLab server is running and accessible.

    Checks that GitLab server responds to HTTP requests.
    """
    log = TestLogger(TEST_NAMES["gitlab_server"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    log.check("Checking GitLab server accessibility")

    result = verify_gitlab_server_running(host)

    if result["success"]:
        log.passed(TEST_LOG_MSGS["gitlab_server_ok"], result.get("details", ""))
    else:
        log.failed(
            TEST_LOG_MSGS["gitlab_server_fail"].format(error=result["error"]),
            f"URL: {result.get('url', 'N/A')}\nHTTP Code: {result.get('http_code', 'N/A')}"
        )
        pytest.fail(TEST_ASSERT_MSGS["gitlab_server_failed"].format(error=result["error"]))


# =============================================================================
# TEST 5: GITLAB RUNNER RUNNING CHECK
# =============================================================================

@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(5)
def test_gitlab_runner_running(host):
    """
    Test 5: Verify GitLab runner container is running on GitLab server.

    Checks that gitlab-runner container is running and ready to execute jobs.
    """
    log = TestLogger(TEST_NAMES["gitlab_runner"])

    if not is_build_stream_enabled(host):
        log.skipped(SKIP_MSGS["build_stream_disabled"], "Test skipped")
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    log.check("Checking GitLab runner container status")

    result = verify_gitlab_runner_running(host)

    if result["success"]:
        log.passed(TEST_LOG_MSGS["gitlab_runner_ok"], result.get("details", ""))
    else:
        log.failed(
            TEST_LOG_MSGS["gitlab_runner_fail"].format(error=result["error"]),
            f"Container: {result.get('container', 'N/A')}\nStatus: {result.get('status', 'N/A')}"
        )
        pytest.fail(TEST_ASSERT_MSGS["gitlab_runner_failed"].format(error=result["error"]))
