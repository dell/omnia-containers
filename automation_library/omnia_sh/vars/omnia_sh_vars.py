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


# =============================================================================
# OMNIA.SH VARIABLES - Hardcoded defaults (same as omnia.sh)
# =============================================================================

OMNIA_SH_VARS: Dict[str, Any] = {
    "container_name": "omnia_core",
    "ssh_port": 2222,
    "container_image_tag": "1.0",
    "omnia_shared_path": "/opt/omnia",
}


# =============================================================================
# TEST VARIABLES (for molecule/pytest tests)
# =============================================================================

TEST_VARS: Dict[str, Any] = {
    "container_name": "omnia_core",
    "container_file": "/etc/containers/systemd/omnia_core.container",
    "service_name": "omnia_core.service",
    "metadata_file": "/opt/omnia/.data/oim_metadata.yml",
    "ssh_alias": "omnia_core",
    "ssh_timeout": 5,
    "oim_server_ip": OIM_PREREQ_VARS.get("oim_server_ip", ""),
}
