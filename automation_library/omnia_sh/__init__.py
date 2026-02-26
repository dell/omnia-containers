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
Omnia Shell Functions

Modular organization of Omnia shell deployment and management functions
organized by functionality: functions, variables, and messages.
"""

# Import specific items to avoid circular imports
# Note: Import functions first, then vars and messages to avoid circular dependency
from .functions.omnia_sh_func import (
    run_full_test,
    run_omnia_sh_install,
    run_omnia_sh_uninstall,
    verify_container_running,
    verify_ssh_connection,
    verify_directories,
    check_prerequisites,
    cleanup_omnia,
)
from .vars.omnia_sh_vars import OMNIA_SH_VARS
from .functions.omnia_sh_func import get_omnia_sh_path, validate_config
from .messages.omnia_sh_msgs import OMNIA_SH_MSGS, TEST_VARS, TEST_NAMES
