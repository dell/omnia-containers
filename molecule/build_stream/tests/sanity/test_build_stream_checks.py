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
Build Stream Infrastructure Checks (v2.1).

Sanity tests to verify build_stream infrastructure is ready:
  1. Build stream enabled in config
  2. Build stream API health
  3. PostgreSQL database tables
  4. GitLab server accessible
  5. GitLab runner container running
"""

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled

from automation_library.build_stream.functions import (
    check_build_stream_health,
    verify_postgres_tables,
    verify_gitlab_server_running,
    verify_gitlab_runner_running,
    skip_if_build_stream_not_enabled,
)
from automation_library.build_stream.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)


# =============================================================================
# TEST 1: Build Stream Enabled
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_build_stream_enabled(host):
    """Verify build_stream is enabled in build_stream_config.yml."""
    log = TestLogger(TEST_NAMES["build_stream_enabled"])

    enabled = is_build_stream_enabled(host)

    if enabled:
        log.passed(TEST_LOG_MSGS["build_stream_enabled_ok"])
    else:
        log.failed(TEST_LOG_MSGS["build_stream_enabled_fail"])
        assert False, TEST_ASSERT_MSGS["build_stream_not_enabled"]


# =============================================================================
# TEST 2: Build Stream API Health
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_build_stream_health(host):
    """Verify build_stream API /health endpoint returns healthy."""
    log = TestLogger(TEST_NAMES["build_stream_health"])
    skip_if_build_stream_not_enabled(host, log)

    log.check("Checking Build Stream API health endpoint...")
    result = check_build_stream_health(host)

    details = f"URL: {result['url']}\nStatus: {result['status']}"
    if result["details"]:
        details += f"\n{result['details']}"

    if result["success"]:
        log.passed(TEST_LOG_MSGS["health_ok"], details)
    else:
        log.failed(
            TEST_LOG_MSGS["health_fail"].format(error=result["error"]),
            details
        )
        assert False, TEST_ASSERT_MSGS["health_failed"].format(error=result["error"])


# =============================================================================
# TEST 3: PostgreSQL Database Tables
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_postgres_tables(host):
    """Verify all expected tables exist in build_stream_db."""
    log = TestLogger(TEST_NAMES["postgres_tables"])
    skip_if_build_stream_not_enabled(host, log)

    log.check("Checking PostgreSQL database tables...")
    result = verify_postgres_tables(host)

    if result["success"]:
        log.passed(TEST_LOG_MSGS["postgres_ok"], result["details"])
    else:
        log.failed(
            TEST_LOG_MSGS["postgres_fail"].format(
                missing=", ".join(result["missing_tables"])
            ),
            result["details"]
        )
        assert False, TEST_ASSERT_MSGS["postgres_failed"].format(error=result["error"])


# =============================================================================
# TEST 4: GitLab Server Running
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_gitlab_server_running(host):
    """Verify GitLab server is running and accessible."""
    log = TestLogger(TEST_NAMES["gitlab_server"])
    skip_if_build_stream_not_enabled(host, log)

    log.check("Checking GitLab server accessibility...")
    result = verify_gitlab_server_running(host)

    details = f"URL: {result['url']}\nHTTP Code: {result['http_code']}"
    if result["details"]:
        details += f"\n{result['details']}"

    if result["success"]:
        log.passed(TEST_LOG_MSGS["gitlab_server_ok"], details)
    else:
        log.failed(
            TEST_LOG_MSGS["gitlab_server_fail"].format(error=result["error"]),
            details
        )
        assert False, TEST_ASSERT_MSGS["gitlab_server_failed"].format(error=result["error"])


# =============================================================================
# TEST 5: GitLab Runner Running
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_gitlab_runner_running(host):
    """Verify GitLab runner container is running."""
    log = TestLogger(TEST_NAMES["gitlab_runner"])
    skip_if_build_stream_not_enabled(host, log)

    log.check("Checking GitLab runner container...")
    result = verify_gitlab_runner_running(host)

    if result["success"]:
        log.passed(TEST_LOG_MSGS["gitlab_runner_ok"], result["details"])
    else:
        log.failed(
            TEST_LOG_MSGS["gitlab_runner_fail"].format(error=result["error"]),
            result.get("details", "")
        )
        assert False, TEST_ASSERT_MSGS["gitlab_runner_failed"].format(error=result["error"])
