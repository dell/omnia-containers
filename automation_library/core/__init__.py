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
Core utilities for automation library.

Modules:
- formatting: Colors, Symbols, log(), TestLogger
- host: Testinfra host connection utilities
- report: Test report generation
"""

from .formatting import Colors, Symbols, log, set_debug_mode, TestLogger, get_test_output
from .host import (
    get_testinfra_host,
    load_user_config,
    run_on_oim,
    run_in_container,
    run_on_remote_node,
    get_node_admin_ip,
    get_functional_groups_from_pxe_mapping,
    get_group_names_from_pxe_mapping,
)
from .report import TestReport, get_current_report, set_current_report
from .vars import PROVISION_CONFIG_PATH

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
    "load_user_config",
    "run_on_oim",
    "run_in_container",
    "run_on_remote_node",
    "get_node_admin_ip",
    "get_functional_groups_from_pxe_mapping",
    "get_group_names_from_pxe_mapping",
    # Report
    "TestReport",
    "get_current_report",
    "set_current_report",
    # Vars
    "PROVISION_CONFIG_PATH",
]
