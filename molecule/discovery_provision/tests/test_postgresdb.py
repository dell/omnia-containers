# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import getpass
import pytest

def get_provision_password():
    """Prompt the user securely and handle edge cases."""
    while True:
        print("\nEnter provision password:", flush=True)
        password = getpass.getpass("")
        print("Confirm your password:", flush=True)
        recheck_passwd = getpass.getpass("")

        if recheck_passwd != password:
            print("\nPasswords do not match. Please try again.\n", flush=True)
        elif not password.strip():
            print("\nPassword cannot be empty. Please try again.\n", flush=True)
        else:
            print("\nPassword confirmed.\n", flush=True)
            return password

def test_postgres_db(run_sshpass_command, get_file_from_container, extract_create_table_sql, extract_columns_from_create_sql):
    create_omniadb_file_path = "/opt/omnia/shared_libraries/provision/db_operations/create_omniadb_tables.py"

    password = get_provision_password()

    # Get file content from container
    file_content = get_file_from_container(run_sshpass_command, create_omniadb_file_path)
    assert file_content, "\nStep 1 failed: File content is empty or could not be read."
    print("\nStep 1 passed: File content fetched.")

    # Extract CREATE TABLE SQL for nodeinfo
    try:
        sql = extract_create_table_sql(file_content, table="nodeinfo")
        print("\nStep 2 passed: CREATE TABLE SQL extracted.")
    except Exception as e:
        pytest.fail(f"\nStep 2 failed: {e}")

    # Extract expected column names from the SQL
    expected_columns = extract_columns_from_create_sql(sql)
    assert expected_columns, "\nStep 3 failed: No columns extracted from SQL."
    print(f"\nStep 3 passed: Expected columns: {sorted(expected_columns)}")
    print(f"Number of expected columns: {len(expected_columns)}")
    
    # Build query to fetch actual columns from DB
    query = (
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'cluster' AND table_name = 'nodeinfo';"
    )

    cmd = (
        f"podman exec -e PGPASSWORD='{password}' omnia_provision "
        f"psql -q -U postgres -d omniadb -t -A -c \"{query}\""
    )

    result = run_sshpass_command(cmd)
    assert result.returncode == 0, print(f"\nFailed to query column names.\nError:\n{result.stderr}")

    actual_columns = set(line.strip().lower() for line in result.stdout.splitlines() if line.strip())
    print(f"\nExtracted actual columns: {sorted(actual_columns)}")
    print(f"Number of actual columns: {len(actual_columns)}")

    # Compare expected vs actual
    missing = expected_columns - actual_columns
    extra = actual_columns - expected_columns

    assert not missing, print(f"\nMissing expected columns: {missing}")
    assert not extra, print(f"\nFound unexpected extra columns: {extra}")

    print("\nPostgres DB schema verification passed!")
