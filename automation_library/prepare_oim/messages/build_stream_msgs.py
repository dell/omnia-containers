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
Prepare OIM - Build Stream Messages.

Test names, log messages, and assertion messages for build_stream
API health check and omnia_postgres DB tables verification.
"""

from typing import Dict

# =============================================================================
# TEST NAMES
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    "build_stream_health": "Verify build_stream API /health endpoint",
    "build_stream_health_skipped": "build_stream health check (build_stream not enabled - SKIPPED)",
    "postgres_db_tables": "Verify build_stream_db tables in omnia_postgres",
    "postgres_db_tables_skipped": "postgres DB tables check (build_stream not enabled - SKIPPED)",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # Health check
    "build_stream_healthy": "build_stream API is healthy",
    "build_stream_unhealthy": "build_stream API is {status}",
    "build_stream_skipped": "build_stream checks skipped (enable_build_stream is false)",
    "build_stream_config_missing": "build_stream_config.yml missing required key: {key}",
    # Postgres DB
    "postgres_db_ok": "All {count} tables found in build_stream_db",
    "postgres_db_fail": "build_stream_db missing {count} table(s)",
    "postgres_db_skipped": "postgres DB check skipped (enable_build_stream is false)",
}

# =============================================================================
# ASSERT MESSAGES
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "build_stream_health_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ BUILD STREAM HEALTH CHECK FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected: {{"status": "healthy"}} | Got: {status}
║ Error: {error}
║
║ HOW TO FIX:
║   1. Check container:  podman ps | grep omnia_build_stream
║   2. Check logs:       podman logs omnia_build_stream
║   3. Check service:    systemctl status playbook_watcher.service
║   4. Check config:     build_stream_host_ip / build_stream_port in build_stream_config.yml
║   5. Test manually:    curl -sk https://<host_ip>:<port>/health
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "postgres_db_tables_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ POSTGRES DB TABLES VERIFICATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Database: build_stream_db | Container: omnia_postgres
║ Missing tables: {missing}
║
║ HOW TO FIX:
║   1. Check container:     podman ps | grep omnia_postgres
║   2. Check logs:          podman logs omnia_postgres
║   3. Inspect tables:      podman exec omnia_postgres psql -U <user> -d build_stream_db -c "\\dt"
║   4. Re-run playbook:     ansible-playbook prepare_oim.yml
╚══════════════════════════════════════════════════════════════════════════════╝
""",
}
