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
Additional Cloud-Init Module - Function Exports.

Re-exports functions from sub-files for external use.
"""

from .common_func import (
    get_functional_groups_from_config,
    load_additional_cloud_init_config,
    skip_if_additional_cloud_init_disabled,
    get_nodes_by_functional_group,
    get_all_nodes_for_common,
)
from .validation_func import (
    validate_cloud_init_config,
    validate_functional_groups,
    check_prohibited_keys,
    validate_write_files,
    validate_runcmd,
    run_omnia_validation_playbook,
)
from .smd_func import (
    verify_smd_group_creation,
    verify_smd_group_deletion,
    verify_bss_group_registration,
    get_xnames_for_fg,
    get_all_xnames,
)
from .node_verification_func import (
    verify_cloud_init_files_on_nodes,
    verify_runcmd_execution_on_nodes,
    verify_additional_cloud_init_integration,
)
