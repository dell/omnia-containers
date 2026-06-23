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

"""Core Functions Module."""

# Host functions
from .host_func import (
    get_testinfra_host,
    load_omnia_test_config,
    load_omnia_test_credentials,
    encrypt_omnia_test_credentials,
    OMNIA_TEST_CONFIG_FILE,
    OMNIA_TEST_CREDENTIALS_FILE,
    OMNIA_TEST_CREDENTIALS_KEY,
    get_dataset_path,
    is_local_execution,
    run_on_oim,
    run_in_container,
    run_on_remote_node,
    get_node_info,
    get_nodes_info,
    check_container_running,
    make_verification_result,
    compare_directory_md5sum,
    download_omnia_sh,
    get_project_root,
    get_node_admin_ip,
    get_functional_groups_from_pxe_mapping,
    get_group_names_from_pxe_mapping,
)

# Node checks functions (connectivity + cloud-init)
from .node_checks_func import (
    # Connectivity cache
    clear_connectivity_cache,
    get_connectivity_cache,
    get_reachable_nodes,
    get_unreachable_nodes,
    is_node_reachable,
    get_node_error,
    # Connectivity checks
    check_node_connectivity_once,
    check_node_connectivity_with_retry,
    verify_nodes_connectivity,
    check_nodes_reachability,
    print_unreachable_nodes,
    # Cloud-init
    get_cloudinit_status,
    wait_for_cloudinit,
    verify_cloudinit_status,
)

# Formatting functions
from .formatting_func import (
    Colors,
    Symbols,
    log,
    set_debug_mode,
    TestLogger,
    get_test_output,
)

# Load inputs functions
from .load_inputs_func import (
    load_container_file,
    load_input_file,
    get_input_value,
    get_input_bool,
    clear_input_cache,
    is_software_enabled,
    get_config_list_item,
    get_nfs_client_mount_path,
)

# Report functions
from .report_func import (
    TestReport,
    get_current_report,
    set_current_report,
)

# Secrets functions
from .secrets_func import (
    view_credentials_file,
    get_credential_value,
    get_multiple_credentials,
)

# DB exec functions
from .db_exec_func import (
    exec_psql_query,
    query_db_row,
)

# Build stream functions
from .build_stream_func import (
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
