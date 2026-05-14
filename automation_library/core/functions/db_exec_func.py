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
Core Module - Container Database Executor.

Generic utilities for running SQL queries against containerised databases
(PostgreSQL) without entering the container manually.

All execution flows through: OIM host → podman exec <container> psql ...
No direct TCP connections; no hardcoded credentials.

Public API
----------
exec_psql_query(host, container, db_user, db_name, sql) -> ContainerQueryResult
query_db_row(host, container, db_user, db_name, table, select_col,
             where_col, where_val, order_by, limit)      -> ContainerQueryResult
"""

from typing import Dict, Any, List, Optional


def exec_psql_query(
    host,
    container: str,
    db_user: str,
    db_name: str,
    sql: str,
) -> Dict[str, Any]:
    """
    Execute a SQL query inside a containerised PostgreSQL instance.

    Runs the query via ``podman exec <container> psql`` on the OIM host
    so no TCP port or password is required — the container's local Unix
    socket is used (peer/trust auth between the container process and psql).

    Unquoted output format (``-tA``) is used so callers receive clean,
    line-separated values without table borders or column headers.

    Args:
        host:      Testinfra host object (connected to OIM server).
        container: Name of the running podman container that hosts PostgreSQL.
        db_user:   PostgreSQL role / user name to connect as.
        db_name:   Database name to connect to.
        sql:       SQL statement to execute (single statement recommended).

    Returns:
        Dict with:
            ``success``  – bool, True when psql exits 0.
            ``rows``     – List[str], one entry per non-empty output line.
            ``stdout``   – raw stdout string from psql.
            ``stderr``   – raw stderr string from psql.
            ``rc``       – integer return code from psql.
            ``error``    – human-readable error string, or None on success.

    Example::

        result = exec_psql_query(
            host,
            container="omnia_postgres",
            db_user=pg_user,  # from get_credential_value()
            db_name="build_stream_db",
            sql="SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;",
        )
        if result["success"]:
            tables = result["rows"]
    """
    escaped_sql = sql.replace('"', '\\"')
    cmd_str = (
        f'podman exec {container} '
        f'psql -U {db_user} -d {db_name} -tAc "{escaped_sql}" 2>/dev/null'
    )
    cmd = host.run(cmd_str)

    rows: List[str] = [
        line.strip()
        for line in cmd.stdout.strip().split("\n")
        if line.strip()
    ]

    success = cmd.rc == 0
    error = None
    if not success:
        error = (
            f"psql query failed in container '{container}' "
            f"(rc={cmd.rc}): {cmd.stderr or cmd.stdout}"
        )

    return {
        "success": success,
        "rows": rows,
        "stdout": cmd.stdout,
        "stderr": cmd.stderr,
        "rc": cmd.rc,
        "error": error,
    }


def query_db_row(
    host,
    container: str,
    db_user: str,
    db_name: str,
    table: str,
    select_col: str,
    where_col: Optional[str] = None,
    where_val: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: int = 1,
) -> Dict[str, Any]:
    """
    Read one or more column values from a PostgreSQL table inside a container.

    This is the high-level convenience wrapper over exec_psql_query for the
    common pattern: "give me the value of column X from table Y where Z = V".
    Callers never need to construct SQL strings manually.

    Designed to be reusable across any module — prepare_oim, build_image,
    telemetry, etc. — without knowing the container internals.

    Args:
        host:       Testinfra host object (connected to OIM server).
        container:  Podman container that hosts PostgreSQL.
        db_user:    PostgreSQL role to connect as.
        db_name:    Database name to connect to.
        table:      Table name to query.
        select_col: Column(s) to SELECT.  Use ``*`` or ``col1,col2`` for multiple.
        where_col:  Optional column name for the WHERE clause filter.
        where_val:  Optional value for the WHERE clause filter.
                    String values are automatically single-quoted.
        order_by:   Optional ORDER BY clause (e.g. ``"created_at DESC"``).
        limit:      Maximum rows to return (default 1).  Pass 0 for no limit.

    Returns:
        Dict with:
            ``success``  – bool.
            ``rows``     – List[str], one entry per non-empty output line.
                           For single-column SELECTs each entry is the bare value.
                           For multi-column SELECTs each entry is pipe-separated (psql -tA default).
            ``value``    – convenience alias: ``rows[0]`` when success and rows non-empty,
                           otherwise ``None``.
            ``stdout``   – raw stdout from psql.
            ``rc``       – psql return code.
            ``error``    – error string, or None on success.

    Examples::

        # Get the job_id of the latest COMPLETED build-image-x86_64 job stage
        result = query_db_row(
            host,
            container="omnia_postgres",
            db_user=pg_user,  # from get_credential_value()
            db_name="build_stream_db",
            table="job_stages",
            select_col="job_id",
            where_col="stage_name",
            where_val="build-image-x86_64",
            order_by="started_at DESC",
            limit=1,
        )
        job_uuid = result["value"]  # e.g. "c01cdd28-..."

        # Get job_state for a known job_id
        result = query_db_row(
            host,
            container="omnia_postgres",
            db_user=pg_user,  # from get_credential_value()
            db_name="build_stream_db",
            table="jobs",
            select_col="job_state",
            where_col="job_id",
            where_val="c01cdd28-...",
        )
        state = result["value"]  # "COMPLETED"
    """
    clauses: List[str] = [f"SELECT {select_col} FROM {table}"]

    if where_col and where_val is not None:
        # Always single-quote the filter value for safety (values are test-time, not user input)
        escaped_val = str(where_val).replace("'", "''")
        clauses.append(f"WHERE {where_col} = '{escaped_val}'")

    if order_by:
        clauses.append(f"ORDER BY {order_by}")

    if limit and limit > 0:
        clauses.append(f"LIMIT {limit}")

    sql = " ".join(clauses) + ";"

    result = exec_psql_query(
        host,
        container=container,
        db_user=db_user,
        db_name=db_name,
        sql=sql,
    )

    value: Optional[str] = result["rows"][0] if result["success"] and result["rows"] else None

    return {
        "success": result["success"],
        "rows": result["rows"],
        "value": value,
        "stdout": result["stdout"],
        "rc": result["rc"],
        "error": result["error"],
    }
