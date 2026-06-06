# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Prepare OIM vars module.
"""

from .prepare_oim_vars import (
    OPENCHAMI_CONTAINERS,
    CORE_CONTAINERS,
    AUTH_CONTAINER,
    OMNIA_TARGET_SERVICES,
    OPENCHAMI_TARGET_SERVICES,
    PULP_CERT_PATH,
    LDAP_CERT_PATH,
    STORAGE_BACKEND_MINIO,
    STORAGE_BACKEND_POWERSCALE,
    S3_CONFIG_KEY,
    S3_PROVIDER_KEY,
    S3_ENDPOINT_URL_KEY,
    S3_EXPECTED_BUCKETS,
    MINIO_CONTAINER,
    MINIO_SERVICE,
    MINIO_DATA_DIR_SUFFIX,
    S3CMD_CONFIG_PATH,
    REGISTRY_PORT,
    REGCTL_CONFIG_PATH,
    REGCTL_BINARY_PATH,
)

from .build_stream_vars import (
    BUILD_STREAM_HOST_IP_KEY,
    BUILD_STREAM_PORT_KEY,
    BUILD_STREAM_HEALTH_PATH,
    POSTGRES_CONTAINER_NAME,
    POSTGRES_DB_NAME,
    POSTGRES_USER_CRED_KEY,
    POSTGRES_PASSWORD_CRED_KEY,
    POSTGRES_EXPECTED_TABLES,
)

__all__ = [
    "OPENCHAMI_CONTAINERS",
    "CORE_CONTAINERS",
    "AUTH_CONTAINER",
    "OMNIA_TARGET_SERVICES",
    "OPENCHAMI_TARGET_SERVICES",
    "PULP_CERT_PATH",
    "LDAP_CERT_PATH",
    "BUILD_STREAM_HOST_IP_KEY",
    "BUILD_STREAM_PORT_KEY",
    "BUILD_STREAM_HEALTH_PATH",
    "POSTGRES_CONTAINER_NAME",
    "POSTGRES_DB_NAME",
    "POSTGRES_USER_CRED_KEY",
    "POSTGRES_PASSWORD_CRED_KEY",
    "POSTGRES_EXPECTED_TABLES",
    "STORAGE_BACKEND_MINIO",
    "STORAGE_BACKEND_POWERSCALE",
    "S3_CONFIG_KEY",
    "S3_PROVIDER_KEY",
    "S3_ENDPOINT_URL_KEY",
    "S3_EXPECTED_BUCKETS",
    "MINIO_CONTAINER",
    "MINIO_SERVICE",
    "MINIO_DATA_DIR_SUFFIX",
    "S3CMD_CONFIG_PATH",
    "REGISTRY_PORT",
    "REGCTL_CONFIG_PATH",
    "REGCTL_BINARY_PATH",
]
