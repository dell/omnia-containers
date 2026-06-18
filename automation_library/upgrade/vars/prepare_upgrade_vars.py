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
Upgrade Module - Prepare Upgrade Variables.

Variables for running and verifying the ``prepare_upgrade.yml`` playbook
inside the omnia_core container.
"""

from typing import Dict, Any

from .upgrade_core_vars import UPGRADE_VARS

# =============================================================================
# PREPARE UPGRADE CONSTANTS
# =============================================================================

CONTAINER_NAME: str = UPGRADE_VARS["container_name"]

PLAYBOOK_PATH: str = "/omnia/upgrade/prepare_upgrade.yml"

LOG_FILE: str = "/tmp/prepare_upgrade.log"

POLL_INTERVAL: int = 10

TAIL_LINES: int = 50

PREPARE_UPGRADE_VARS: Dict[str, Any] = {
    "container_name": CONTAINER_NAME,
    "playbook_path": PLAYBOOK_PATH,
    "log_file": LOG_FILE,
    "poll_interval": POLL_INTERVAL,
    "tail_lines": TAIL_LINES,
}
