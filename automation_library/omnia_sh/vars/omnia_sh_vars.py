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
Omnia.sh Test - Configuration Variables.

This module contains hardcoded variables for omnia.sh verification tests.
These values match the defaults in omnia.sh and should NOT be changed.

Usage:
    from automation_library.omnia_sh.vars.omnia_sh_vars import OMNIA_SH_VARS, TEST_VARS

"""

from typing import Dict, Any

from ...checks.vars.oim_prereq_vars import OIM_PREREQ_VARS
from ...core.vars import (
    OIM_SHARED_PATH as _CORE_OIM_SHARED_PATH,
    OIM_METADATA_PATH as _CORE_OIM_METADATA_PATH,
    OMNIA_CORE_CONTAINER as _CORE_CONTAINER,
)


# =============================================================================
# OMNIA.SH VARIABLES - Hardcoded defaults (same as omnia.sh)
# =============================================================================

OMNIA_SH_VARS: Dict[str, Any] = {
    "container_name": _CORE_CONTAINER,
    "ssh_port": 2222,
    "container_image_tag": "1.0",
    "omnia_shared_path": _CORE_OIM_SHARED_PATH,
}


# =============================================================================
# TEST VARIABLES (for molecule/pytest tests)
# =============================================================================

TEST_VARS: Dict[str, Any] = {
    "container_name": _CORE_CONTAINER,
    "container_file": f"/etc/containers/systemd/{_CORE_CONTAINER}.container",
    "service_name": f"{_CORE_CONTAINER}.service",
    "metadata_file": _CORE_OIM_METADATA_PATH,
    "ssh_alias": _CORE_CONTAINER,
    "ssh_timeout": 5,
    "oim_server_ip": OIM_PREREQ_VARS.get("oim_server_ip", ""),
}
