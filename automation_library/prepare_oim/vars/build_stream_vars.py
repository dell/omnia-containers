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
Prepare OIM - Build Stream Variables.

Constants for build_stream API health check and omnia_postgres DB verification.
All runtime values (port, host_ip, credentials) are read dynamically from
build_stream_config.yml and omnia_config_credentials.yml — nothing is hardcoded here.

Source references (inside omnia_core container):
  - build_stream role vars: /omnia/prepare_oim/roles/deploy_containers/build_stream/vars/main.yml
  - postgres role vars:     /omnia/prepare_oim/roles/deploy_containers/postgres/vars/main.yml
  - postgres SQL template:  /omnia/prepare_oim/roles/deploy_containers/postgres/templates/init_build_stream_db.sql.j2
"""

from typing import List

# =============================================================================
# BUILD STREAM API (omnia_build_stream container)
# Keys used to read runtime values from build_stream_config.yml via load_input_file
# =============================================================================

# Key names inside build_stream_config.yml
BUILD_STREAM_HOST_IP_KEY: str = "build_stream_host_ip"
BUILD_STREAM_PORT_KEY: str = "build_stream_port"

# Health endpoint path (protocol is always HTTPS per playbook vars)
BUILD_STREAM_HEALTH_PATH: str = "/health"

# =============================================================================
# POSTGRES CONTAINER (omnia_postgres)
# Deployed by prepare_oim postgres role when build_stream is enabled
# =============================================================================

# Container name — matches postgres_container_name in postgres/vars/main.yml
POSTGRES_CONTAINER_NAME: str = "omnia_postgres"

# Database name — matches postgres_db_name in postgres/vars/main.yml
POSTGRES_DB_NAME: str = "build_stream_db"

# Credential key names — read from omnia_config_credentials.yml via vault
POSTGRES_USER_CRED_KEY: str = "postgres_user"
POSTGRES_PASSWORD_CRED_KEY: str = "postgres_password"

# Expected tables — from init_build_stream_db.sql.j2 + alembic migrations
# Verified against live omnia_postgres container (build_stream_db, schema=public)
POSTGRES_EXPECTED_TABLES: List[str] = [
    "alembic_version",
    "artifact_metadata",
    "audit_events",
    "idempotency_keys",
    "job_stages",
    "jobs",
]
