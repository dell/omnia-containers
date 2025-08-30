# Copyright 2024 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.





import subprocess
import vars


class DBQueryError(RuntimeError):
    """Custom exception for database query errors."""
    pass

class StatusCheckError(RuntimeError):
    """Raised when unexpected statuses are found."""
    pass

def run_full_table_query(db_credentials, table_name, container_name, row):
    """
    Runs SELECT * FROM the specified table inside a podman container.
    Raises DBQueryError with a generic message on any failure.
    """
    query = f"SELECT {row} FROM {table_name};"

    cmd = (
        f"podman exec -i {container_name} "
        f"bash -c \"PGPASSWORD='{db_credentials['password']}' "
        f"psql -U {db_credentials['user']} "
        f"-d {db_credentials['database']} "
        f"-c \\\"{query}\\\"\""
    )

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        print("Query succeeded. \n Output:")
        print(output)
        return output
    except subprocess.CalledProcessError:
        raise DBQueryError("Database does not exist.")




def run_status_query(db_credentials, table_name, container_name, row):
    """
    Runs status query and validates node statuses.

    Returns:
        Dictionary of all nodes and their statuses.

    Raises:
        RuntimeError if any node (except 'oim') is not 'booted'.
    """
    try:
        output = run_full_table_query(db_credentials, table_name, container_name, row)
    except DBQueryError as e:
        raise RuntimeError(f"Failed to fetch data: {e}")

    lines = output.splitlines()
    if len(lines) < 3:
        raise RuntimeError("Query returned no data.")

    data_lines = lines[2:]  # skip headers

    node_status_map = {}
    invalid_nodes = {}

    for line in data_lines:
        if '|' not in line:
            continue
        parts = [part.strip() for part in line.split('|')]
        if len(parts) < 2:
            continue

        node, status = parts[0], parts[1]
        node_status_map[node] = status

        if node.lower() != 'oim' and status.lower() != vars.EXPECTED_STATUS:
            invalid_nodes[node] = status

    print("Node status map:", node_status_map)

    if invalid_nodes:
        print("Nodes with invalid status:")
        for node, status in invalid_nodes.items():
            print(f"  {node}: {status}")
        raise RuntimeError(f"Some nodes are not in '{vars.EXPECTED_STATUS}' state: {invalid_nodes}")

    print("All nodes are in '{vars.EXPECTED_STATUS}' state.")
    return node_status_map
