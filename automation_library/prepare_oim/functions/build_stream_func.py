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
Prepare OIM - Build Stream Functions.

Verification functions for:
1. build_stream API health check  (HTTPS /health endpoint on OIM)
2. omnia_postgres DB tables check (psql query via podman exec on OIM)

Both functions:
- Skip automatically when enable_build_stream is false
- Read ALL runtime values from config files — no fallback/default values
- Use core utilities: load_input_file, get_credential_value, exec_psql_query
"""

from typing import Dict, Any

from automation_library.core import (
    load_input_file,
    get_credential_value,
    BUILD_STREAM_CONFIG_FILE,
    OMNIA_CREDENTIALS_PATH,
    OMNIA_CREDENTIALS_KEY_PATH,
)
from automation_library.core import exec_psql_query

from ..vars.build_stream_vars import (
    BUILD_STREAM_HOST_IP_KEY,
    BUILD_STREAM_PORT_KEY,
    BUILD_STREAM_HEALTH_PATH,
    POSTGRES_CONTAINER_NAME,
    POSTGRES_DB_NAME,
    POSTGRES_USER_CRED_KEY,
    POSTGRES_EXPECTED_TABLES,
)


def _is_build_stream_enabled(host) -> bool:
    """Return True only when enable_build_stream is set to true in config."""
    config = load_input_file(host, BUILD_STREAM_CONFIG_FILE)
    if not config:
        return False
    return bool(config.get("enable_build_stream", False))


def _load_build_stream_config(host) -> Dict[str, Any]:
    """
    Load build_stream_config.yml.

    Returns parsed dict or empty dict if file is unreadable.
    Does NOT supply any fallback values for missing keys.
    """
    return load_input_file(host, BUILD_STREAM_CONFIG_FILE) or {}


# =============================================================================
# 1. BUILD STREAM API HEALTH CHECK
# =============================================================================

def check_build_stream_health(host) -> Dict[str, Any]:
    """
    Verify the build_stream API /health endpoint returns {"status": "healthy"}.

    Skips when enable_build_stream is false.

    Reads host_ip and port exclusively from build_stream_config.yml —
    no hardcoded defaults or fallback values.
    Runs curl directly on the OIM host (host.run) — not inside a container —
    because the omnia_build_stream container uses host networking.
    Protocol is always HTTPS (matches build_stream playbook vars).

    Args:
        host: Testinfra host object connected to OIM server.

    Returns:
        Dict with 'success', 'status', 'skipped', 'details', 'error'.
    """
    if not _is_build_stream_enabled(host):
        return {
            "success": True,
            "status": "skipped",
            "skipped": True,
            "details": "build_stream checks skipped (enable_build_stream is false)",
            "error": None,
        }

    config = _load_build_stream_config(host)

    host_ip = config.get(BUILD_STREAM_HOST_IP_KEY)
    port = config.get(BUILD_STREAM_PORT_KEY)

    if not host_ip or not port:
        missing = ", ".join(
            k for k, v in {
                BUILD_STREAM_HOST_IP_KEY: host_ip,
                BUILD_STREAM_PORT_KEY: port,
            }.items() if not v
        )
        return {
            "success": False,
            "status": "config_error",
            "skipped": False,
            "details": None,
            "error": (
                f"build_stream_config.yml is missing required key(s): {missing}"
            ),
        }

    url = f"https://{host_ip}:{port}{BUILD_STREAM_HEALTH_PATH}"

    http_code_cmd = host.run(
        f"curl -sk -o /dev/null -w '%{{http_code}}' {url} 2>/dev/null"
    )
    http_code = http_code_cmd.stdout.strip()

    if http_code_cmd.rc == 0 and http_code == "200":
        body_cmd = host.run(f"curl -sk {url} 2>/dev/null")
        body = body_cmd.stdout.strip()

        if '"healthy"' in body.replace(" ", ""):
            return {
                "success": True,
                "status": "healthy",
                "skipped": False,
                "details": f"GET {url} → {body}",
                "error": None,
            }

        return {
            "success": False,
            "status": "unhealthy",
            "skipped": False,
            "details": body,
            "error": f"GET {url} returned unexpected body: {body}",
        }

    return {
        "success": False,
        "status": "unreachable",
        "skipped": False,
        "details": None,
        "error": (
            f"GET {url} unreachable. "
            f"HTTP status: {http_code or 'N/A'} (curl rc={http_code_cmd.rc})"
        ),
    }


# =============================================================================
# 2. POSTGRES DB TABLES CHECK
# =============================================================================

def verify_postgres_db_tables(host) -> Dict[str, Any]:
    """
    Verify all expected tables exist in build_stream_db inside omnia_postgres.

    Skips when enable_build_stream is false.

    Reads postgres_user from vault-encrypted omnia_config_credentials.yml
    via get_credential_value (core secrets module) — no hardcoded credentials.
    Delegates the actual SQL execution to core's exec_psql_query utility,
    which runs psql via podman exec on the OIM host.

    Args:
        host: Testinfra host object connected to OIM server.

    Returns:
        Dict with 'success', 'status', 'skipped', 'found_tables',
        'missing_tables', 'details', 'error'.
    """
    if not _is_build_stream_enabled(host):
        return {
            "success": True,
            "status": "skipped",
            "skipped": True,
            "found_tables": [],
            "missing_tables": [],
            "details": "postgres DB check skipped (enable_build_stream is false)",
            "error": None,
        }

    pg_user = get_credential_value(
        host,
        OMNIA_CREDENTIALS_PATH,
        OMNIA_CREDENTIALS_KEY_PATH,
        POSTGRES_USER_CRED_KEY,
    )
    if not pg_user:
        return {
            "success": False,
            "status": "creds_error",
            "skipped": False,
            "found_tables": [],
            "missing_tables": POSTGRES_EXPECTED_TABLES,
            "details": None,
            "error": (
                f"Failed to read '{POSTGRES_USER_CRED_KEY}' from "
                "omnia_config_credentials.yml"
            ),
        }

    query_result = exec_psql_query(
        host,
        container=POSTGRES_CONTAINER_NAME,
        db_user=pg_user,
        db_name=POSTGRES_DB_NAME,
        sql=(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname='public' ORDER BY tablename;"
        ),
    )

    if not query_result["success"]:
        return {
            "success": False,
            "status": "query_failed",
            "skipped": False,
            "found_tables": [],
            "missing_tables": POSTGRES_EXPECTED_TABLES,
            "details": None,
            "error": query_result["error"],
        }

    found_tables = query_result["rows"]
    missing_tables = [t for t in POSTGRES_EXPECTED_TABLES if t not in found_tables]
    extra_tables = [t for t in found_tables if t not in POSTGRES_EXPECTED_TABLES]

    success = len(missing_tables) == 0 and len(extra_tables) == 0
    details_lines = [
        f"Database: {POSTGRES_DB_NAME} | Container: {POSTGRES_CONTAINER_NAME}",
        f"Tables: {len(found_tables)} found, {len(POSTGRES_EXPECTED_TABLES)} expected",
    ]
    for tbl in POSTGRES_EXPECTED_TABLES:
        sym = "\u2713" if tbl in found_tables else "\u2717"
        details_lines.append(f"  {sym} {tbl}")
    if extra_tables:
        details_lines.append(f"  Extra: {', '.join(extra_tables)}")

    error_parts = []
    if missing_tables:
        error_parts.append(f"Missing: {', '.join(missing_tables)}")
    if extra_tables:
        error_parts.append(f"Extra: {', '.join(extra_tables)}")

    return {
        "success": success,
        "status": "ok" if success else "table_mismatch",
        "skipped": False,
        "found_tables": found_tables,
        "missing_tables": missing_tables,
        "extra_tables": extra_tables,
        "details": "\n".join(details_lines),
        "error": f"{POSTGRES_DB_NAME}: {'; '.join(error_parts)}" if error_parts else None,
    }
