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
Core Module - Build Stream Job Utilities.

Reusable helpers for any module that needs to interact with build_stream
job tracking in the omnia_postgres database.

All logic for resolving a job UUID (from user override or latest DB row)
and validating a stage completion lives here so that build_image, local_repo,
discovery, and any future module can share one implementation.

Public API
----------
is_build_stream_enabled(host)                          -> bool
get_build_stream_job_id(host, stage_name)              -> Dict
check_build_stream_stage(host, stage_name, job_id)     -> Dict
"""

import os
from typing import Dict, Any, Optional

import yaml

from .db_exec import query_db_row
from .load_inputs import load_input_file
from .secrets import get_credential_value
from .vars import (
    BUILD_STREAM_CONFIG_FILE,
    OMNIA_CREDENTIALS_PATH,
    OMNIA_CREDENTIALS_KEY_PATH,
)


# =============================================================================
# CONSTANTS
# =============================================================================

_POSTGRES_CONTAINER = "omnia_postgres"
_POSTGRES_DB = "build_stream_db"
_POSTGRES_USER_KEY = "postgres_user"
_COMPLETED_STATE = "COMPLETED"

# Well-known stage names — callers may pass any stage string, these are docs
STAGE_BUILD_IMAGE_X86_64 = "build-image-x86_64"
STAGE_BUILD_IMAGE_AARCH64 = "build-image-aarch64"
STAGE_CREATE_LOCAL_REPO = "create-local-repository"
STAGE_VALIDATE_IMAGE = "validate-image-on-test"
STAGE_PARSE_CATALOG = "parse-catalog"
STAGE_GENERATE_INPUT = "generate-input-files"


# =============================================================================
# USER CONFIG READER
# =============================================================================

def _get_user_config_job_id() -> str:
    """
    Read build_stream_job_id override from user_config.yml on the local machine.

    Returns the UUID string if set and non-empty, otherwise empty string.
    This is the local file (project root), NOT inside any container.
    """
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    user_config_path = os.path.join(project_root, "user_config.yml")
    if not os.path.exists(user_config_path):
        return ""
    try:
        with open(user_config_path, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh) or {}
        return str(config.get("build_stream_job_id", "") or "").strip()
    except (IOError, yaml.YAMLError):
        return ""


# =============================================================================
# POSTGRES HELPERS
# =============================================================================

def _get_pg_user(host) -> Optional[str]:
    """Read postgres_user from vault-encrypted omnia_config_credentials.yml."""
    return get_credential_value(
        host,
        OMNIA_CREDENTIALS_PATH,
        OMNIA_CREDENTIALS_KEY_PATH,
        _POSTGRES_USER_KEY,
    )


# =============================================================================
# PUBLIC API
# =============================================================================

def is_build_stream_enabled(host) -> bool:
    """
    Return True when enable_build_stream is ``true`` in build_stream_config.yml
    inside the omnia_core container.

    No fallback — if the config is absent or the key is missing returns False.
    """
    config = load_input_file(host, BUILD_STREAM_CONFIG_FILE)
    if not config:
        return False
    return bool(config.get("enable_build_stream", False))


def get_build_stream_job_id(host, stage_name: str) -> Dict[str, Any]:
    """
    Resolve the build_stream job UUID to use for a given pipeline stage.

    Resolution order
    ----------------
    1. If ``build_stream_job_id`` is set in ``user_config.yml`` (non-empty),
       that UUID is used as-is — no DB lookup is performed.
    2. Otherwise, query ``build_stream_db.job_stages`` for the latest row
       where ``stage_name = <stage_name>`` and ``stage_state = 'COMPLETED'``,
       ordered by ``started_at DESC``.

    In both cases the returned ``job_id`` is cross-checked against the parent
    ``jobs`` table to confirm the overall job is also ``COMPLETED``.

    Args:
        host:        Testinfra host object connected to OIM server.
        stage_name:  Stage name to look up (e.g. ``"build-image-x86_64"``).

    Returns:
        Dict with:
            ``success``   – bool.
            ``job_id``    – UUID string, or None if not resolved.
            ``stage``     – stage_name queried.
            ``job_state`` – actual job state from ``jobs`` table (or None).
            ``source``    – ``"user_config"`` or ``"database"``.
            ``error``     – error string, or None on success.
    """
    override_id = _get_user_config_job_id()

    if override_id:
        # ------------------------------------------------------------------ #
        # User pinned a specific job — validate it exists and is COMPLETED    #
        # ------------------------------------------------------------------ #
        pg_user = _get_pg_user(host)
        if not pg_user:
            return {
                "success": False,
                "job_id": override_id,
                "stage": stage_name,
                "job_state": None,
                "source": "user_config",
                "error": (
                    f"Failed to read '{_POSTGRES_USER_KEY}' from "
                    "omnia_config_credentials.yml"
                ),
            }

        # Check the stage itself — filter by BOTH job_id AND stage_name
        from .db_exec import exec_psql_query as _exec_psql
        _escaped_id = override_id.replace("'", "''")
        _escaped_stage = stage_name.replace("'", "''")
        _stage_sql = (
            f"SELECT stage_state FROM job_stages "
            f"WHERE job_id = '{_escaped_id}' AND stage_name = '{_escaped_stage}' "
            f"ORDER BY started_at DESC LIMIT 1;"
        )
        stage_check = _exec_psql(
            host,
            container=_POSTGRES_CONTAINER,
            db_user=pg_user,
            db_name=_POSTGRES_DB,
            sql=_stage_sql,
        )
        stage_state = stage_check["rows"][0] if (stage_check["success"] and stage_check["rows"]) else None

        # If the stage row doesn't exist for this job_id + stage_name, it's a wrong job_id
        if not stage_state:
            return {
                "success": False,
                "job_id": override_id,
                "stage": stage_name,
                "job_state": None,
                "source": "user_config",
                "error": (
                    f"job_id '{override_id}' not found — "
                    f"no '{stage_name}' stage entry exists for this job in "
                    f"{_POSTGRES_DB}.job_stages. "
                    "Check the UUID in user_config.yml under 'build_stream_job_id'."
                ),
            }

        # Cross-check parent job state
        job_check = query_db_row(
            host,
            container=_POSTGRES_CONTAINER,
            db_user=pg_user,
            db_name=_POSTGRES_DB,
            table="jobs",
            select_col="job_state",
            where_col="job_id",
            where_val=override_id,
            limit=1,
        )
        job_state = job_check["value"] if job_check["success"] else None

        if job_state != _COMPLETED_STATE:
            return {
                "success": False,
                "job_id": override_id,
                "stage": stage_name,
                "job_state": job_state or "NOT FOUND",
                "source": "user_config",
                "error": (
                    f"Job '{override_id}' (from user_config.yml) is in state "
                    f"'{job_state or 'NOT FOUND'}' — expected '{_COMPLETED_STATE}'. "
                    "The pipeline must complete before tests can run."
                ),
            }

        return {
            "success": True,
            "job_id": override_id,
            "stage": stage_name,
            "job_state": job_state,
            "source": "user_config",
            "error": None,
        }

    # ---------------------------------------------------------------------- #
    # Auto-resolve: find the latest COMPLETED stage from postgres             #
    # ---------------------------------------------------------------------- #
    pg_user = _get_pg_user(host)
    if not pg_user:
        return {
            "success": False,
            "job_id": None,
            "stage": stage_name,
            "job_state": None,
            "source": "database",
            "error": (
                f"Failed to read '{_POSTGRES_USER_KEY}' from "
                "omnia_config_credentials.yml"
            ),
        }

    # Find latest job_id where this stage is COMPLETED
    # Filter by both stage_name AND stage_state=COMPLETED so we get the
    # most recent successful run, not just the most recent attempt.
    from .db_exec import exec_psql_query as _exec_psql
    _escaped_stage = stage_name.replace("'", "''")
    _find_sql = (
        f"SELECT job_id FROM job_stages "
        f"WHERE stage_name = '{_escaped_stage}' "
        f"AND stage_state = '{_COMPLETED_STATE}' "
        f"ORDER BY started_at DESC LIMIT 1;"
    )
    stage_result = _exec_psql(
        host,
        container=_POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=_POSTGRES_DB,
        sql=_find_sql,
    )

    if not stage_result["success"]:
        return {
            "success": False,
            "job_id": None,
            "stage": stage_name,
            "job_state": None,
            "source": "database",
            "error": (
                f"DB query failed while looking for stage '{stage_name}': "
                f"{stage_result['error']}"
            ),
        }

    job_id = stage_result["rows"][0] if stage_result["rows"] else None
    if not job_id:
        # Check if the stage exists at all (any state) so we can give a better message
        _any_sql = (
            f"SELECT stage_state FROM job_stages "
            f"WHERE stage_name = '{_escaped_stage}' "
            f"ORDER BY started_at DESC LIMIT 1;"
        )
        any_result = _exec_psql(
            host,
            container=_POSTGRES_CONTAINER,
            db_user=pg_user,
            db_name=_POSTGRES_DB,
            sql=_any_sql,
        )
        latest_state = (any_result["rows"][0] if (any_result["success"] and any_result["rows"]) else None)
        if latest_state:
            return {
                "success": False,
                "job_id": None,
                "stage": stage_name,
                "job_state": latest_state,
                "source": "database",
                "error": (
                    f"Stage '{stage_name}' latest run is in state '{latest_state}' — "
                    f"expected '{_COMPLETED_STATE}'. "
                    "The build_stream pipeline has not completed successfully yet. "
                    "Wait for it to complete or check for failures."
                ),
            }
        return {
            "success": False,
            "job_id": None,
            "stage": stage_name,
            "job_state": "NOT FOUND",
            "source": "database",
            "error": (
                f"No '{stage_name}' stage entry found in {_POSTGRES_DB}.job_stages. "
                "The build_stream pipeline may not have run yet."
            ),
        }

    # Cross-check parent job state to be sure
    job_check = query_db_row(
        host,
        container=_POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=_POSTGRES_DB,
        table="jobs",
        select_col="job_state",
        where_col="job_id",
        where_val=job_id,
        limit=1,
    )
    job_state = job_check["value"] if job_check["success"] else None

    if job_state != _COMPLETED_STATE:
        return {
            "success": False,
            "job_id": job_id,
            "stage": stage_name,
            "job_state": job_state or "NOT FOUND",
            "source": "database",
            "error": (
                f"Latest job '{job_id}' overall state is '{job_state or 'NOT FOUND'}' "
                f"(expected '{_COMPLETED_STATE}'). "
                "The build_stream pipeline has not fully completed."
            ),
        }

    return {
        "success": True,
        "job_id": job_id,
        "stage": stage_name,
        "job_state": job_state,
        "source": "database",
        "error": None,
    }


def check_build_stream_stage(
    host,
    stage_name: str,
    job_id: str,
) -> Dict[str, Any]:
    """
    Verify that a specific pipeline stage completed successfully for a given job.

    Queries ``build_stream_db.job_stages`` for the row matching both
    ``job_id`` and ``stage_name`` and checks ``stage_state = 'COMPLETED'``.
    Returns the exact DB state so the caller can print it when it is not
    ``COMPLETED``.

    Args:
        host:        Testinfra host object.
        stage_name:  Stage name to check (e.g. ``"build-image-x86_64"``).
        job_id:      The job UUID to check the stage for.

    Returns:
        Dict with:
            ``success``      – bool, True only when stage_state is COMPLETED.
            ``stage``        – stage_name checked.
            ``job_id``       – job UUID checked.
            ``stage_state``  – exact value from DB (e.g. COMPLETED/FAILED/RUNNING).
            ``error``        – error string, or None on success.
    """
    pg_user = _get_pg_user(host)
    if not pg_user:
        return {
            "success": False,
            "stage": stage_name,
            "job_id": job_id,
            "stage_state": None,
            "error": (
                f"Failed to read '{_POSTGRES_USER_KEY}' from "
                "omnia_config_credentials.yml"
            ),
        }

    # We need both job_id AND stage_name to match — use exec_psql_query directly
    from .db_exec import exec_psql_query
    sql = (
        f"SELECT stage_state FROM job_stages "
        f"WHERE job_id = '{job_id}' AND stage_name = '{stage_name}' "
        f"ORDER BY started_at DESC LIMIT 1;"
    )
    result = exec_psql_query(
        host,
        container=_POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=_POSTGRES_DB,
        sql=sql,
    )

    if not result["success"]:
        return {
            "success": False,
            "stage": stage_name,
            "job_id": job_id,
            "stage_state": None,
            "error": result["error"],
        }

    stage_state = result["rows"][0] if result["rows"] else None

    if not stage_state:
        return {
            "success": False,
            "stage": stage_name,
            "job_id": job_id,
            "stage_state": None,
            "error": (
                f"Stage '{stage_name}' not found for job '{job_id}' "
                f"in {_POSTGRES_DB}.job_stages"
            ),
        }

    success = stage_state == _COMPLETED_STATE
    error = None if success else (
        f"Stage '{stage_name}' for job '{job_id}' is '{stage_state}' "
        f"(expected '{_COMPLETED_STATE}')"
    )

    return {
        "success": success,
        "stage": stage_name,
        "job_id": job_id,
        "stage_state": stage_state,
        "error": error,
    }
