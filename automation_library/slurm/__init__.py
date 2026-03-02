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
Slurm module - Functions, messages, and variables for slurm job submission automation.
"""

from .functions import (
    get_job_script_path,
    parse_login_ips_from_env,
    parse_login_ips_from_pxe_mapping,
    parse_login_compiler_ips_from_env,
    parse_login_compiler_ips_from_pxe_mapping,
    parse_ldap_user_from_env,
    parse_ldap_key_path_from_env,
    is_node_reachable,
    run_ssh_from_omnia_core,
    submit_job_via_login,
    check_squeue,
    find_reachable_login_node,
    run_ssh_as_user,
    discover_ldap_user_from_node,
    create_ldap_job_script,
    submit_ldap_job,
    wait_ldap_job_complete,
    read_ldap_job_output,
    cleanup_ldap_job,
    submit_and_verify_ldap_job,
)
from .vars import (
    JOB_SCRIPT_PATH,
    MULTI_JOB_COUNT,
)
from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    LDAP_TEST_NAMES,
    LDAP_LOG_MSGS,
    LDAP_ASSERT_MSGS,
)

from . import functions as _functions
from . import vars as _vars
from . import messages as _messages

__all__ = list(_functions.__all__) + list(_vars.__all__) + list(_messages.__all__)
