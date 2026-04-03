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
Build Stream Test Cases.

Verifies the build_stream deployment when enable_build_stream is true
in build_stream_config.yml. Both tests skip automatically when disabled.

Test cases:
1. Verify build_stream API /health endpoint returns {"status": "healthy"}
2. Verify all expected tables exist in build_stream_db (omnia_postgres)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.prepare_oim.messages import (
    BS_TEST_NAMES as TEST_NAMES,
    BS_TEST_LOG_MSGS as LOG_MSGS,
    BS_TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.prepare_oim.functions import (
    is_build_stream_enabled,
    check_build_stream_health,
    verify_postgres_db_tables,
)


# =============================================================================
# 1. BUILD STREAM API HEALTH CHECK
# =============================================================================

@pytest.mark.order(10)
def test_build_stream_health(host):
    """
    Test Case 1: Verify build_stream API /health endpoint.

    Reads build_stream_host_ip and build_stream_port exclusively from
    build_stream_config.yml — no fallback values.
    Calls https://<host_ip>:<port>/health on the OIM host (not inside container).
    Verifies HTTP 200 and {"status": "healthy"} response body.

    Skips if enable_build_stream is false.
    """
    if not is_build_stream_enabled(host):
        log = TestLogger(TEST_NAMES["build_stream_health_skipped"])
        log.check("Checking if build_stream is enabled")
        log.skipped(LOG_MSGS["build_stream_skipped"])
        pytest.skip("build_stream is not enabled in build_stream_config.yml")

    log = TestLogger(TEST_NAMES["build_stream_health"])
    log.check(
        "Verifying build_stream API /health endpoint "
        "(host_ip and port from build_stream_config.yml)"
    )

    result = check_build_stream_health(host)

    if result.get("skipped"):
        log.skipped(LOG_MSGS["build_stream_skipped"])
        pytest.skip(result.get("details", "build_stream not enabled"))

    if result["success"]:
        log.passed(LOG_MSGS["build_stream_healthy"], result["details"])
    else:
        log.failed(
            LOG_MSGS["build_stream_unhealthy"].format(status=result["status"]),
            result["error"]
        )
        assert False, ASSERT_MSGS["build_stream_health_failed"].format(
            status=result["status"],
            error=result["error"]
        )


# =============================================================================
# 2. POSTGRES DB TABLES CHECK
# =============================================================================

@pytest.mark.order(11)
def test_postgres_db_tables(host):
    """
    Test Case 2: Verify all expected tables exist in build_stream_db.

    Reads postgres_user from vault-encrypted omnia_config_credentials.yml
    via core get_credential_value (no hardcoded credentials).
    Executes psql query via podman exec on OIM using core exec_psql_query.
    Verifies all 6 expected tables:
        alembic_version, artifact_metadata, audit_events,
        idempotency_keys, job_stages, jobs

    Skips if enable_build_stream is false.
    """
    if not is_build_stream_enabled(host):
        log = TestLogger(TEST_NAMES["postgres_db_tables_skipped"])
        log.check("Checking if build_stream is enabled")
        log.skipped(LOG_MSGS["postgres_db_skipped"])
        pytest.skip("build_stream is not enabled in build_stream_config.yml")

    log = TestLogger(TEST_NAMES["postgres_db_tables"])
    log.check(
        "Verifying build_stream_db tables in omnia_postgres "
        "(credentials from omnia_config_credentials.yml)"
    )

    result = verify_postgres_db_tables(host)

    if result.get("skipped"):
        log.skipped(LOG_MSGS["postgres_db_skipped"])
        pytest.skip(result.get("details", "build_stream not enabled"))

    if result["success"]:
        log.passed(
            LOG_MSGS["postgres_db_ok"].format(count=len(result["found_tables"])),
            result["details"]
        )
    else:
        log.failed(
            LOG_MSGS["postgres_db_fail"].format(count=len(result["missing_tables"])),
            result["details"]
        )
        assert False, ASSERT_MSGS["postgres_db_tables_failed"].format(
            missing=", ".join(result["missing_tables"])
        )
