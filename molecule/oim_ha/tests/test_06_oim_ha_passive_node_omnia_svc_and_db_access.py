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

import os
import pytest

@pytest.mark.qtest_id("TC-3702")
def test_passive_node_postgres_db_access(run_sshpass_command):
    print("\nVerifying PostgreSQL DB access on passive node\n")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    assert postgres_password, "Missing environment variable: POSTGRES_PASSWORD"

    # Simple query to test connection
    query = "SELECT version();"
    
    # Construct podman psql command
    cmd = (
        f"podman exec -e PGPASSWORD='{postgres_password}' omnia_provision "    
        f"psql -q -U postgres -d omniadb -t -A -c \"{query}\""
    )

    result = run_sshpass_command(cmd, use_ha=True)
    assert result.returncode == 0, f"Failed to connect to PostgreSQL DB: {result.stderr}"

    output = result.stdout.strip()
    assert output, print("No output received from PostgreSQL DB.")
    print(f"\nSuccessfully accessed PostgreSQL DB. Version info:\n{output}")

@pytest.mark.qtest_id("TC-3702")
def test_passive_node_omnia_svc(run_sshpass_command):
    print("\nVerifying omnia.service status on passive node\n")
    cmd = "podman exec omnia_provision systemctl is-active omnia.service"
    result = run_sshpass_command(cmd, use_ha=True)
    assert result.returncode == 0 and result.stdout.strip() == "active", \
        print(f"\nomnia.service is inactive: {result.stdout.strip()}")
    print("\nomnia.service is active.")
