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
Upgrade Module - Variables.

Configuration variables for the Omnia upgrade workflow.
Values are loaded from omnia_test_config.yml with sensible defaults.
"""

from typing import Dict, Any

from ...core import load_omnia_test_config, OIM_SHARED_PATH, OMNIA_CORE_CONTAINER

_omnia_test_config = load_omnia_test_config()

# =============================================================================
# UPGRADE CONFIGURATION
# =============================================================================

# Upgrade section from omnia_test_config.yml
_upgrade_config = _omnia_test_config.get("upgrade", {})

UPGRADE_VARS: Dict[str, Any] = {
    # Version info
    "upgrade_from_version": _upgrade_config.get("from_version", "2.1.0.0"),
    "upgrade_to_version": _upgrade_config.get("to_version", "2.2.0.0"),

    # Artifactory clone settings for the NEW version
    "upgrade_repo_url": _upgrade_config.get(
        "repo_url", "https://github.com/dell/omnia-artifactory.git"
    ),
    "upgrade_repo_branch": _upgrade_config.get("repo_branch", "omnia-container"),
    "upgrade_clone_path": _upgrade_config.get(
        "clone_path",
        f"{OIM_SHARED_PATH}/upgrade-to-{_upgrade_config.get('to_version', '2.2')}"
    ),

    # Build image settings
    "omnia_branch": _upgrade_config.get("omnia_branch", "pub/q2_upgrade"),
    "core_tag": _upgrade_config.get("core_tag", "2.2"),

    # Container
    "container_name": OMNIA_CORE_CONTAINER,

    # Metadata path inside container
    "oim_metadata_path": "/opt/omnia/.data/oim_metadata.yml",

    # Backup path (created by omnia.sh --upgrade)
    "backup_base_path": OIM_SHARED_PATH,

    # Timeouts
    "clone_timeout": 300,
    "build_timeout": 1800,
    "upgrade_timeout": 1200,
}
