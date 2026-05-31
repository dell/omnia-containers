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
Build Stream Database Functions.

Functions for querying build_stream_db in omnia_postgres container.
All runtime values are read from config files via core module functions.
"""

from typing import Dict, Any, List, Optional

from automation_library.core import exec_psql_query, query_db_row
from automation_library.core import POSTGRES_CONTAINER, POSTGRES_DB

from .shared_func import get_postgres_user
from ..vars.build_stream_vars import STAGE_STATE_COMPLETED, EXPECTED_TABLES


def verify_postgres_tables(host) -> Dict[str, Any]:
    """
    Verify all expected tables exist in build_stream_db.

    Args:
        host: Testinfra host object connected to OIM server.

    Returns:
        Dict with 'success', 'found_tables', 'missing_tables', 'details', 'error'.
    """
    result = {
        "success": False,
        "found_tables": [],
        "missing_tables": [],
        "details": "",
        "error": "",
    }

    pg_user = get_postgres_user(host)
    if not pg_user:
        result["error"] = "Failed to read postgres_user from omnia_config_credentials.yml"
        return result

    query_result = exec_psql_query(
        host,
        container=POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=POSTGRES_DB,
        sql="SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;",
    )

    if not query_result["success"]:
        result["error"] = query_result["error"]
        return result

    found_tables = query_result["rows"]
    missing_tables = [t for t in EXPECTED_TABLES if t not in found_tables]

    result["found_tables"] = found_tables
    result["missing_tables"] = missing_tables
    result["success"] = len(missing_tables) == 0

    details_lines = [
        f"Database: {POSTGRES_DB} | Container: {POSTGRES_CONTAINER}",
        f"Tables: {len(found_tables)} found, {len(EXPECTED_TABLES)} expected",
    ]
    for tbl in EXPECTED_TABLES:
        sym = "\u2713" if tbl in found_tables else "\u2717"
        details_lines.append(f"  {sym} {tbl}")

    result["details"] = "\n".join(details_lines)

    if missing_tables:
        result["error"] = f"Missing tables: {', '.join(missing_tables)}"

    return result


def get_job_by_id(host, job_id: str) -> Dict[str, Any]:
    """
    Get job details by job_id.

    Args:
        host: Testinfra host object
        job_id: UUID of the job

    Returns:
        Dict with 'success', 'job_id', 'job_state', 'client_id', 'created_at', 'error'.
    """
    result = {
        "success": False,
        "job_id": job_id,
        "job_state": "",
        "client_id": "",
        "created_at": "",
        "error": "",
    }

    pg_user = get_postgres_user(host)
    if not pg_user:
        result["error"] = "Failed to read postgres_user from credentials"
        return result

    sql = f"SELECT job_state, client_id, created_at FROM jobs WHERE job_id = '{job_id}';"
    query_result = exec_psql_query(
        host,
        container=POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=POSTGRES_DB,
        sql=sql,
    )

    if not query_result["success"]:
        result["error"] = query_result["error"]
        return result

    if not query_result["rows"]:
        result["error"] = f"Job {job_id} not found"
        return result

    parts = query_result["rows"][0].split("|")
    if len(parts) >= 3:
        result["job_state"] = parts[0].strip()
        result["client_id"] = parts[1].strip()
        result["created_at"] = parts[2].strip()
        result["success"] = True

    return result


def get_latest_job(host) -> Dict[str, Any]:
    """
    Get the latest job from the database.

    Args:
        host: Testinfra host object

    Returns:
        Dict with 'success', 'job_id', 'job_state', 'created_at', 'error'.
    """
    result = {
        "success": False,
        "job_id": "",
        "job_state": "",
        "created_at": "",
        "error": "",
    }

    pg_user = get_postgres_user(host)
    if not pg_user:
        result["error"] = "Failed to read postgres_user from credentials"
        return result

    sql = "SELECT job_id, job_state, created_at FROM jobs ORDER BY created_at DESC LIMIT 1;"
    query_result = exec_psql_query(
        host,
        container=POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=POSTGRES_DB,
        sql=sql,
    )

    if not query_result["success"]:
        result["error"] = query_result["error"]
        return result

    if not query_result["rows"]:
        result["error"] = "No jobs found in database"
        return result

    parts = query_result["rows"][0].split("|")
    if len(parts) >= 3:
        result["job_id"] = parts[0].strip()
        result["job_state"] = parts[1].strip()
        result["created_at"] = parts[2].strip()
        result["success"] = True

    return result


def get_job_stages(host, job_id: str) -> Dict[str, Any]:
    """
    Get all stages for a job.

    Args:
        host: Testinfra host object
        job_id: UUID of the job

    Returns:
        Dict with 'success', 'stages' (list of dicts), 'error'.
    """
    result = {
        "success": False,
        "stages": [],
        "error": "",
    }

    pg_user = get_postgres_user(host)
    if not pg_user:
        result["error"] = "Failed to read postgres_user from credentials"
        return result

    sql = (
        f"SELECT stage_name, stage_state, started_at, ended_at, error_code "
        f"FROM job_stages WHERE job_id = '{job_id}' ORDER BY started_at;"
    )
    query_result = exec_psql_query(
        host,
        container=POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=POSTGRES_DB,
        sql=sql,
    )

    if not query_result["success"]:
        result["error"] = query_result["error"]
        return result

    stages = []
    for row in query_result["rows"]:
        parts = row.split("|")
        if len(parts) >= 5:
            stages.append({
                "stage_name": parts[0].strip(),
                "stage_state": parts[1].strip(),
                "started_at": parts[2].strip(),
                "ended_at": parts[3].strip(),
                "error_code": parts[4].strip(),
            })

    result["stages"] = stages
    result["success"] = True
    return result


def get_stage_state(host, job_id: str, stage_name: str) -> Dict[str, Any]:
    """
    Get the state of a specific stage for a job.

    Args:
        host: Testinfra host object
        job_id: UUID of the job
        stage_name: Name of the stage

    Returns:
        Dict with 'success', 'stage_name', 'stage_state', 'error_code', 'error'.
    """
    result = {
        "success": False,
        "stage_name": stage_name,
        "stage_state": "",
        "error_code": "",
        "error": "",
    }

    pg_user = get_postgres_user(host)
    if not pg_user:
        result["error"] = "Failed to read postgres_user from credentials"
        return result

    sql = (
        f"SELECT stage_state, error_code FROM job_stages "
        f"WHERE job_id = '{job_id}' AND stage_name = '{stage_name}' "
        f"ORDER BY started_at DESC LIMIT 1;"
    )
    query_result = exec_psql_query(
        host,
        container=POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=POSTGRES_DB,
        sql=sql,
    )

    if not query_result["success"]:
        result["error"] = query_result["error"]
        return result

    if not query_result["rows"]:
        result["error"] = f"Stage '{stage_name}' not found for job {job_id}"
        return result

    parts = query_result["rows"][0].split("|")
    if len(parts) >= 2:
        result["stage_state"] = parts[0].strip()
        result["error_code"] = parts[1].strip()
        result["success"] = True

    return result


def verify_stage_completed(host, job_id: str, stage_name: str) -> Dict[str, Any]:
    """
    Verify that a specific stage completed successfully.

    Args:
        host: Testinfra host object
        job_id: UUID of the job
        stage_name: Name of the stage

    Returns:
        Dict with 'success', 'stage_name', 'stage_state', 'details', 'error'.
    """
    result = {
        "success": False,
        "stage_name": stage_name,
        "stage_state": "",
        "details": "",
        "error": "",
    }

    stage_result = get_stage_state(host, job_id, stage_name)
    if not stage_result["success"]:
        result["error"] = stage_result["error"]
        return result

    result["stage_state"] = stage_result["stage_state"]

    if stage_result["stage_state"] == STAGE_STATE_COMPLETED:
        result["success"] = True
        result["details"] = f"Stage '{stage_name}' completed successfully"
    else:
        result["error"] = (
            f"Stage '{stage_name}' is '{stage_result['stage_state']}' "
            f"(expected '{STAGE_STATE_COMPLETED}')"
        )
        if stage_result["error_code"]:
            result["error"] += f" - Error: {stage_result['error_code']}"

    return result


def get_images_for_job(host, job_id: str) -> Dict[str, Any]:
    """
    Get all images created for a job.

    Args:
        host: Testinfra host object
        job_id: UUID of the job

    Returns:
        Dict with 'success', 'images' (list of dicts), 'error'.
    """
    result = {
        "success": False,
        "images": [],
        "error": "",
    }

    pg_user = get_postgres_user(host)
    if not pg_user:
        result["error"] = "Failed to read postgres_user from credentials"
        return result

    sql = (
        f"SELECT i.id, i.role, i.image_name, ig.id as group_id "
        f"FROM images i "
        f"JOIN image_groups ig ON i.image_group_id = ig.id "
        f"WHERE ig.job_id = '{job_id}';"
    )
    query_result = exec_psql_query(
        host,
        container=POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=POSTGRES_DB,
        sql=sql,
    )

    if not query_result["success"]:
        result["error"] = query_result["error"]
        return result

    images = []
    for row in query_result["rows"]:
        parts = row.split("|")
        if len(parts) >= 4:
            images.append({
                "id": parts[0].strip(),
                "role": parts[1].strip(),
                "image_name": parts[2].strip(),
                "group_id": parts[3].strip(),
            })

    result["images"] = images
    result["success"] = True
    return result


def get_image_groups_for_job(host, job_id: str) -> Dict[str, Any]:
    """
    Get all image groups for a job.

    Args:
        host: Testinfra host object
        job_id: UUID of the job

    Returns:
        Dict with 'success', 'image_groups' (list of dicts), 'error'.
    """
    result = {
        "success": False,
        "image_groups": [],
        "error": "",
    }

    pg_user = get_postgres_user(host)
    if not pg_user:
        result["error"] = "Failed to read postgres_user from credentials"
        return result

    sql = (
        f"SELECT id, status, created_at "
        f"FROM image_groups WHERE job_id = '{job_id}';"
    )
    query_result = exec_psql_query(
        host,
        container=POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=POSTGRES_DB,
        sql=sql,
    )

    if not query_result["success"]:
        result["error"] = query_result["error"]
        return result

    groups = []
    for row in query_result["rows"]:
        parts = row.split("|")
        if len(parts) >= 3:
            groups.append({
                "id": parts[0].strip(),
                "status": parts[1].strip(),
                "created_at": parts[2].strip(),
            })

    result["image_groups"] = groups
    result["success"] = True
    return result


def get_all_image_groups(host) -> Dict[str, Any]:
    """
    Get all image groups from the database.

    Args:
        host: Testinfra host object

    Returns:
        Dict with 'success', 'image_groups' (list of dicts), 'error'.
    """
    result = {
        "success": False,
        "image_groups": [],
        "error": "",
    }

    pg_user = get_postgres_user(host)
    if not pg_user:
        result["error"] = "Failed to read postgres_user from credentials"
        return result

    sql = "SELECT id, job_id, status, created_at FROM image_groups ORDER BY created_at DESC;"
    query_result = exec_psql_query(
        host,
        container=POSTGRES_CONTAINER,
        db_user=pg_user,
        db_name=POSTGRES_DB,
        sql=sql,
    )

    if not query_result["success"]:
        result["error"] = query_result["error"]
        return result

    groups = []
    for row in query_result["rows"]:
        parts = row.split("|")
        if len(parts) >= 4:
            groups.append({
                "id": parts[0].strip(),
                "job_id": parts[1].strip(),
                "status": parts[2].strip(),
                "created_at": parts[3].strip(),
            })

    result["image_groups"] = groups
    result["success"] = True
    return result
