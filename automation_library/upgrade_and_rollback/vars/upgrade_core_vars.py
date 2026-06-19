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

Configuration variables for the Omnia upgrade/rollback workflow.

From ``omnia_test_config.yml`` (upgrade section):
  - ``current_version``: Version currently running on OIM
  - ``new_version``: Target version for upgrade
  - ``repo_url``, ``repo_branch``, ``omnia_branch``: Build settings

Version validation (automatic, no operation flag needed):
  - Upgrade: Fails if current_version >= new_version
  - Rollback: Fails if running version != new_version (not upgraded yet)

Usage:
    from automation_library.upgrade_and_rollback.vars import UPGRADE_VARS
"""

from typing import Dict, Any, Tuple

from ...core import (
    load_omnia_test_config,
    OMNIA_CORE_CONTAINER,
    OMNIA_GIT_RAW_BASE_URL,
    OIM_METADATA_PATH,
)

_omnia_test_config = load_omnia_test_config()

# =============================================================================
# UPGRADE SECTION FROM CONFIG  (user-editable fields only)
# =============================================================================

_upgrade_config: Dict[str, Any] = _omnia_test_config.get("upgrade", {})

# =============================================================================
# SUPPORTED VERSIONS  (chronological order, oldest first)
# Add new entries here when a new Omnia release is supported.
# =============================================================================

SUPPORTED_VERSIONS: Tuple[str, ...] = (
    "2.1.0.0",
    "2.2.0.0",
)

# =============================================================================
# VERSION-SPECIFIC PROPERTIES
# =============================================================================
# Each supported version maps to a core_tag used by build_images.sh and
# podman to identify the container image.
#
# To add a new version:
#   1. Add "X.Y.Z.W" to SUPPORTED_VERSIONS above
#   2. Add "omnia_version_X_Y_Z_W_core_tag" below
# =============================================================================

VERSION_PROPERTIES: Dict[str, Dict[str, str]] = {
    "omnia_version_2_1_0_0": {
        "core_tag": "2.1",
    },
    "omnia_version_2_2_0_0": {
        "core_tag": "2.2",
    },
}

# =============================================================================
# DERIVED VALUES (from user config)
# =============================================================================

_current_version: str = _upgrade_config.get("current_version", "")
_new_version: str = _upgrade_config.get("new_version", "")
_new_version_key: str = f"omnia_version_{_new_version.replace('.', '_')}"
_new_core_tag: str = VERSION_PROPERTIES.get(_new_version_key, {}).get(
    "core_tag", _new_version.rsplit(".", 2)[0],
)

# Clone path is auto-derived — never user-configurable
_clone_path: str = f"/upgrade-{_new_version.replace('.', '-')}"

# =============================================================================
# UPGRADE VARIABLES  (single source of truth for functions + tests)
# =============================================================================

UPGRADE_VARS: Dict[str, Any] = {

    # =========================================================================
    # VERSION INFO  (from omnia_test_config.yml)
    # =========================================================================
    "current_version": _current_version,
    "new_version": _new_version,

    # =========================================================================
    # VERSION-SPECIFIC CORE TAGS  (maintained here, not in config)
    # =========================================================================
    "omnia_version_2_1_0_0_core_tag": VERSION_PROPERTIES["omnia_version_2_1_0_0"]["core_tag"],
    "omnia_version_2_2_0_0_core_tag": VERSION_PROPERTIES["omnia_version_2_2_0_0"]["core_tag"],

    # Resolved core_tag for the new_version (used by build_images.sh)
    "core_tag": _new_core_tag,

    # =========================================================================
    # REPOSITORY & BUILD  (from omnia_test_config.yml)
    # =========================================================================
    "repo_url": _upgrade_config.get("repo_url", ""),
    "repo_branch": _upgrade_config.get("repo_branch", ""),
    "omnia_branch": _upgrade_config.get("omnia_branch", ""),

    # omnia.sh download URLs (branch fallback → tag fallback)
    "omnia_sh_branch_url": (
        f"{OMNIA_GIT_RAW_BASE_URL}/"
        f"{_upgrade_config.get('omnia_branch', '')}/omnia.sh"
    ),
    "omnia_sh_tag_url": (
        f"{OMNIA_GIT_RAW_BASE_URL}/"
        f"refs/tags/{_upgrade_config.get('omnia_branch', '')}/omnia.sh"
    ),

    # Clone path — auto-derived from new_version, deleted and re-created on
    # every run to guarantee a fresh clone.
    "clone_path": _clone_path,

    # =========================================================================
    # CONTAINER / PATH CONSTANTS
    # =========================================================================
    "container_name": OMNIA_CORE_CONTAINER,
    "oim_metadata_path": OIM_METADATA_PATH,
    "backup_path": f"/opt/omnia/backups/upgrade/version_{_current_version}",
    "quadlet_file_path": "/etc/containers/systemd/omnia_core.container",

    # =========================================================================
    # TIMEOUTS & OUTPUT
    # =========================================================================
    "clone_timeout": 300,
    "build_timeout": 1800,
    "upgrade_timeout": 1200,
    "build_progress_interval": 10,
    "upgrade_poll_interval": 10,
    "tail_lines": 0,  # 0 = full output, N = last N lines
}


def get_core_tag_for_version(version: str) -> str:
    """
    Get the core_tag (podman image tag) for a given omnia version.

    Looks up ``omnia_version_X_Y_Z_W`` in VERSION_PROPERTIES.

    Args:
        version: Omnia version string (e.g., "2.1.0.0")

    Returns:
        Core tag string (e.g., "2.1")
    """
    key = f"omnia_version_{version.replace('.', '_')}"
    props = VERSION_PROPERTIES.get(key)
    if props:
        return props["core_tag"]
    return version.rsplit(".", 2)[0]
