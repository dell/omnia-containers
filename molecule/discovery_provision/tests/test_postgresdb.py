import getpass
import pytest

def test_postgres_db(run_sshpass_command, get_file_from_container, extract_create_table_sql, extract_columns_from_create_sql):
    create_omniadb_file_path = "/opt/omnia/shared_libraries/provision/db_operations/create_omniadb_tables.py"

    # Step 1: Get file content from container
    file_content = get_file_from_container(run_sshpass_command, create_omniadb_file_path)
    assert file_content, "\n❌ Step 1 failed: File content is empty or could not be read."
    print("\n✅ Step 1 passed: File content fetched.")

    # Step 2: Extract CREATE TABLE SQL for nodeinfo
    try:
        sql = extract_create_table_sql(file_content, table="nodeinfo")
        print("\n✅ Step 2 passed: CREATE TABLE SQL extracted.")
    except Exception as e:
        pytest.fail(f"\n❌ Step 2 failed: {e}")

    # Step 3: Extract expected column names from the SQL
    expected_columns = extract_columns_from_create_sql(sql)
    assert expected_columns, "\n❌ Step 3 failed: No columns extracted from SQL."
    print(f"\n✅ Step 3 passed: Expected columns: {sorted(expected_columns)}")
    print(f"No of expected columns: {len(expected_columns)}")

    # Step 4: Prompt for password securely
    password = getpass.getpass("Enter provision password: ")
    assert password, print("❌ Password not provided")

    # Step 5: Build query to fetch actual columns from DB
    query = (
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'cluster' AND table_name = 'nodeinfo';"
    )

    cmd = (
        f"podman exec -e PGPASSWORD='{password}' omnia_provision "
        f"psql -q -U postgres -d omniadb -t -A -c \"{query}\""
    )

    result = run_sshpass_command(cmd)
    assert result.returncode == 0, print(f"\n❌ Failed to query column names.\nError:\n{result.stderr}")

    actual_columns = set(line.strip().lower() for line in result.stdout.splitlines() if line.strip())
    print(f"\n✅ Extracted actual columns: {sorted(actual_columns)}")
    print(f"No of actual columns: {len(expected_columns)}")

    # Step 6: Compare expected vs actual
    missing = expected_columns - actual_columns
    extra = actual_columns - expected_columns

    assert not missing, print(f"\n❌ Missing expected columns: {missing}")
    assert not extra, print(f"\n❌ Found unexpected extra columns: {extra}")
    
    print("\nPostgres DB successfully passed!")
