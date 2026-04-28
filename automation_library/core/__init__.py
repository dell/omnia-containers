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
Core utilities for automation library.

Modules:
- formatting: Colors, Symbols, log(), TestLogger
- host: Testinfra host connection utilities
- report: Test report generation
"""

from .formatting import Colors, Symbols, log, set_debug_mode, TestLogger, get_test_output
from .host import (
    get_testinfra_host,
    load_omnia_test_config,
    get_dataset_path,
    run_on_oim,
    run_in_container,
    run_on_remote_node,
    get_node_info,
    get_nodes_info,
    check_container_running,
    make_verification_result,
    get_project_root,
    # Backward compatibility functions
    get_node_admin_ip,
    get_functional_groups_from_pxe_mapping,
    get_group_names_from_pxe_mapping,
)
from .load_inputs import (
    load_container_file,
    load_input_file,
    get_input_value,
    get_input_bool,
    clear_input_cache,
    is_software_enabled,
    get_config_list_item,
    get_nfs_client_mount_path,
)
from .report import TestReport, get_current_report, set_current_report
from .secrets import (
    view_credentials_file,
    get_credential_value,
    get_multiple_credentials,
)
from .db_exec import exec_psql_query, query_db_row
from .cloudinit import (
    get_cloudinit_status,
    wait_for_cloudinit,
    verify_cloudinit_status_multi,
)
from .build_stream import (
    is_build_stream_enabled,
    get_build_stream_job_id,
    check_build_stream_stage,
    STAGE_BUILD_IMAGE_X86_64,
    STAGE_BUILD_IMAGE_AARCH64,
    STAGE_CREATE_LOCAL_REPO,
    STAGE_VALIDATE_IMAGE,
    STAGE_PARSE_CATALOG,
    STAGE_GENERATE_INPUT,
)
from .vars import (
    # Base paths
    OIM_SHARED_PATH,
    OMNIA_DATA_PATH,
    OMNIA_AUTH_PATH,
    OMNIA_TELEMETRY_PATH,
    OMNIA_LOG_PATH,
    OMNIA_PULP_PATH,
    INPUT_BASE_PATH,
    # Input file names
    SOFTWARE_CONFIG_FILE,
    BUILD_STREAM_CONFIG_FILE,
    GITLAB_CONFIG_FILE,
    NETWORK_SPEC_FILE,
    PROVISION_CONFIG_FILE,
    TELEMETRY_CONFIG_FILE,
    STORAGE_CONFIG_FILE,
    OMNIA_CONFIG_FILE,
    OMNIA_CREDENTIALS_FILE,
    HA_CONFIG_FILE,
    PXE_MAPPING_FILE,
    # Full input file paths
    SOFTWARE_CONFIG_PATH,
    TELEMETRY_CONFIG_PATH,
    OMNIA_CONFIG_PATH,
    NETWORK_SPEC_PATH,
    PROVISION_CONFIG_PATH,
    STORAGE_CONFIG_PATH,
    HA_CONFIG_PATH,
    PXE_MAPPING_FILE_PATH,
    OMNIA_CREDENTIALS_PATH,
    OMNIA_CREDENTIALS_KEY_PATH,
    GITLAB_CONFIG_PATH,
    # Data paths
    SERVICE_CLUSTER_METADATA_PATH,
    OIM_METADATA_PATH,
    FUNCTIONAL_GROUPS_CONFIG_PATH,
    # Auth paths
    SLAPD_CONF_PATH,
    LDAP_CERT_PATH,
    # Telemetry paths
    BMC_GROUP_DATA_PATH,
    IDRAC_TELEMETRY_REPORT_PATH,
    # Pulp paths
    PULP_CERT_PATH,
    # Log paths
    LOCAL_REPO_LOG_PATH,
    # Container names
    OMNIA_CORE_CONTAINER,
    # K8s functional groups
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
    K8S_WORKER_NODE_FUNCTIONAL_GROUP,
    # Slurm functional groups
    SLURM_CONTROL_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_FUNCTIONAL_GROUP,
    SLURM_NODE_AARCH64_FUNCTIONAL_GROUP,
    LOGIN_NODE_FUNCTIONAL_GROUP,
    LOGIN_NODE_AARCH64_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP,
    LOGIN_COMPILER_NODE_AARCH64_FUNCTIONAL_GROUP,
)

__all__ = [
    # Formatting
    "Colors",
    "Symbols",
    "log",
    "set_debug_mode",
    "TestLogger",
    "get_test_output",
    # Host
    "get_testinfra_host",
    "load_omnia_test_config",
    "get_dataset_path",
    "run_on_oim",
    "run_in_container",
    "run_on_remote_node",
    "get_node_info",
    "get_nodes_info",
    "check_container_running",
    "make_verification_result",
    "get_project_root",
    "get_node_admin_ip",
    "get_functional_groups_from_pxe_mapping",
    "get_group_names_from_pxe_mapping",
    # Report
    "TestReport",
    "get_current_report",
    "set_current_report",
    # Input Loader
    "load_container_file",
    "load_input_file",
    "get_input_value",
    "get_input_bool",
    "clear_input_cache",
    "is_software_enabled",
    "get_config_list_item",
    "get_nfs_client_mount_path",
    # Secrets
    "view_credentials_file",
    "get_credential_value",
    "get_multiple_credentials",
    # DB executor
    "exec_psql_query",
    "query_db_row",
    # Build stream
    "is_build_stream_enabled",
    "get_build_stream_job_id",
    "check_build_stream_stage",
    "STAGE_BUILD_IMAGE_X86_64",
    "STAGE_BUILD_IMAGE_AARCH64",
    "STAGE_CREATE_LOCAL_REPO",
    "STAGE_VALIDATE_IMAGE",
    "STAGE_PARSE_CATALOG",
    "STAGE_GENERATE_INPUT",
    # Vars - Base paths
    "OIM_SHARED_PATH",
    "OMNIA_DATA_PATH",
    "OMNIA_AUTH_PATH",
    "OMNIA_TELEMETRY_PATH",
    "OMNIA_LOG_PATH",
    "OMNIA_PULP_PATH",
    "INPUT_BASE_PATH",
    # Vars - Input file names
    "SOFTWARE_CONFIG_FILE",
    "BUILD_STREAM_CONFIG_FILE",
    "GITLAB_CONFIG_FILE",
    "NETWORK_SPEC_FILE",
    "PROVISION_CONFIG_FILE",
    "TELEMETRY_CONFIG_FILE",
    "STORAGE_CONFIG_FILE",
    "OMNIA_CONFIG_FILE",
    "OMNIA_CREDENTIALS_FILE",
    "HA_CONFIG_FILE",
    "PXE_MAPPING_FILE",
    # Vars - Full input file paths
    "SOFTWARE_CONFIG_PATH",
    "TELEMETRY_CONFIG_PATH",
    "OMNIA_CONFIG_PATH",
    "NETWORK_SPEC_PATH",
    "PROVISION_CONFIG_PATH",
    "STORAGE_CONFIG_PATH",
    "HA_CONFIG_PATH",
    "PXE_MAPPING_FILE_PATH",
    "OMNIA_CREDENTIALS_PATH",
    "OMNIA_CREDENTIALS_KEY_PATH",
    "GITLAB_CONFIG_PATH",
    # Vars - Data paths
    "SERVICE_CLUSTER_METADATA_PATH",
    "OIM_METADATA_PATH",
    "FUNCTIONAL_GROUPS_CONFIG_PATH",
    # Vars - Auth paths
    "SLAPD_CONF_PATH",
    "LDAP_CERT_PATH",
    # Vars - Telemetry paths
    "BMC_GROUP_DATA_PATH",
    "IDRAC_TELEMETRY_REPORT_PATH",
    # Vars - Pulp paths
    "PULP_CERT_PATH",
    # Vars - Log paths
    "LOCAL_REPO_LOG_PATH",
    # Vars - Container names
    "OMNIA_CORE_CONTAINER",
    # Vars - K8s groups
    "K8S_CONTROL_PLANE_FUNCTIONAL_GROUP",
    "K8S_WORKER_NODE_FUNCTIONAL_GROUP",
    # Vars - Slurm groups
    "SLURM_CONTROL_NODE_FUNCTIONAL_GROUP",
    "SLURM_NODE_FUNCTIONAL_GROUP",
    "SLURM_NODE_AARCH64_FUNCTIONAL_GROUP",
    "LOGIN_NODE_FUNCTIONAL_GROUP",
    "LOGIN_NODE_AARCH64_FUNCTIONAL_GROUP",
    "LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP",
    "LOGIN_COMPILER_NODE_AARCH64_FUNCTIONAL_GROUP",
]
