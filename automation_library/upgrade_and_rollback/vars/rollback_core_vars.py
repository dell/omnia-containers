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
Rollback Module - Variables.

Configuration for the Omnia rollback workflow.  Reads the same
``upgrade`` section from ``omnia_test_config.yml`` — no fallback defaults.
If required fields are missing the test will fail explicitly.

Uses ``OMNIA_GIT_RAW_BASE_URL`` from core vars (``dell/omnia`` repo) for
omnia.sh download with branch → tag fallback, same pattern as the
oim-prereq-check and upgrade modules.
"""

from typing import Dict, Any

from ...core import (
    load_omnia_test_config,
    OMNIA_CORE_CONTAINER,
    OMNIA_GIT_RAW_BASE_URL,
    OIM_METADATA_PATH,
    INPUT_BASE_PATH,
)
from .upgrade_core_vars import get_core_tag_for_version

# =============================================================================
# CONFIG  (no fallback defaults — must be set in omnia_test_config.yml)
# =============================================================================

_omnia_test_config = load_omnia_test_config()
_upgrade_config: Dict[str, Any] = _omnia_test_config.get("upgrade", {})

_current_version: str = _upgrade_config.get("current_version", "")
_new_version: str = _upgrade_config.get("new_version", "")
_omnia_branch: str = _upgrade_config.get("omnia_branch", "")

# =============================================================================
# DERIVED VALUES
# =============================================================================

_clone_path: str = f"/upgrade-{_new_version.replace('.', '-')}"

# omnia.sh download URLs  (branch → tag fallback, from dell/omnia repo)
_branch_url: str = f"{OMNIA_GIT_RAW_BASE_URL}/{_omnia_branch}/omnia.sh"
_tag_url: str = (
    f"{OMNIA_GIT_RAW_BASE_URL}/refs/tags/{_omnia_branch}/omnia.sh"
)

# =============================================================================
# CONSOLIDATED DICT  (single source of truth for functions + tests)
# =============================================================================

ROLLBACK_VARS: Dict[str, Any] = {
    # Versions
    "current_version": _current_version,
    "new_version": _new_version,
    "rollback_image_tag": get_core_tag_for_version(_current_version),

    # Container
    "container_name": OMNIA_CORE_CONTAINER,

    # Paths
    "clone_path": _clone_path,
    "omnia_sh_path": f"{_clone_path}/omnia.sh",
    "backup_path": f"/opt/omnia/backups/upgrade/version_{_current_version}",

    # omnia.sh download (branch → tag fallback)
    "omnia_branch": _omnia_branch,
    "omnia_sh_branch_url": _branch_url,
    "omnia_sh_tag_url": _tag_url,

    # Metadata / project_default paths (from core)
    "oim_metadata_path": OIM_METADATA_PATH,
    "project_default_current_dir": INPUT_BASE_PATH,

    # =========================================================================
    # ROLLBACK BACKUP VERIFY CATEGORIES
    # After rollback the restored files must match their backup counterparts.
    # Same categories as upgrade backup_verify — quadlets, boot, cloudinit,
    # nodes, images, plus project_default.
    # =========================================================================
    "verify_categories": {
        "project_default": {
            "backup_dir": f"/opt/omnia/backups/upgrade/version_{_current_version}"
                          "/input/project_default",
            "current_dir": INPUT_BASE_PATH,
            "on_oim": False,
        },
        "quadlets": {
            "backup_dir": f"/opt/omnia/backups/upgrade/version_{_current_version}"
                          "/openchami/quadlets",
            "current_dir": "/etc/containers/systemd",
            "on_oim": True,
            "exclude": ["omnia_core.container"],  # Updated during rollback
        },
        "boot": {
            "backup_dir": f"/opt/omnia/backups/upgrade/version_{_current_version}"
                          "/openchami/openchami_data/workdir/boot",
            "current_dir": "/opt/omnia/openchami/workdir/boot",
            "on_oim": False,
        },
        "cloudinit": {
            "backup_dir": f"/opt/omnia/backups/upgrade/version_{_current_version}"
                          "/openchami/openchami_data/workdir/cloud-init",
            "current_dir": "/opt/omnia/openchami/workdir/cloud-init",
            "on_oim": False,
        },
        "nodes": {
            "backup_dir": f"/opt/omnia/backups/upgrade/version_{_current_version}"
                          "/openchami/openchami_data/workdir/nodes",
            "current_dir": "/opt/omnia/openchami/workdir/nodes",
            "on_oim": False,
        },
        "images": {
            "backup_dir": f"/opt/omnia/backups/upgrade/version_{_current_version}"
                          "/openchami/openchami_data/workdir/images",
            "current_dir": "/opt/omnia/openchami/workdir/images",
            "on_oim": False,
        },
    },

    # Timing
    "poll_interval": 10,
    "tail_lines": 0,  # 0 = full output, N = last N lines
    "rollback_timeout": 600,
}
