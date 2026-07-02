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
Prepare OIM functions module.
"""

from .prepare_oim_func import (
    # Config helpers
    is_ldap_enabled,
    is_build_stream_enabled,
    get_primary_oim_admin_ip,
    # Check functions
    check_container_running,
    check_pulp_api_status,
    check_pulp_certificate,
    check_bss_service,
    check_smd_service,
    check_ldap_auth_certificate,
    check_all_services_status,
    check_all_containers_status,
    check_openchami_target_deps,
    check_omnia_target_deps,
    get_expected_containers,
    get_expected_services,
)

from .build_stream_func import (
    check_build_stream_health,
    verify_postgres_db_tables,
)

from .storage_func import (
    get_storage_backend,
    get_s3_endpoint_url,
    verify_storage_backend,
    verify_s3cmd_working,
    verify_s3_buckets,
    verify_regctl_working,
    verify_s3_directories,
)

from .multi_subnet_func import (
    get_additional_subnets,
    has_additional_subnets,
    check_coredhcp_file_exists,
    check_coredhcp_multisubnet_mode,
    verify_subnet_entries_in_coredhcp,
    activate_multisubnet_coredhcp,
    verify_coresmd_running_image,
)

__all__ = [
    # Config helpers
    "is_ldap_enabled",
    "is_build_stream_enabled",
    "get_primary_oim_admin_ip",
    # Check functions
    "check_container_running",
    "check_pulp_api_status",
    "check_pulp_certificate",
    "check_bss_service",
    "check_smd_service",
    "check_ldap_auth_certificate",
    "check_all_services_status",
    "check_all_containers_status",
    "check_openchami_target_deps",
    "check_omnia_target_deps",
    "get_expected_containers",
    "get_expected_services",
    # Build stream functions
    "check_build_stream_health",
    "verify_postgres_db_tables",
    # Storage functions
    "get_storage_backend",
    "get_s3_endpoint_url",
    "verify_storage_backend",
    "verify_s3cmd_working",
    "verify_s3_buckets",
    "verify_regctl_working",
    "verify_s3_directories",
    # Multi-subnet functions
    "get_additional_subnets",
    "has_additional_subnets",
    "check_coredhcp_file_exists",
    "check_coredhcp_multisubnet_mode",
    "verify_subnet_entries_in_coredhcp",
    "activate_multisubnet_coredhcp",
    "verify_coresmd_running_image",
]
