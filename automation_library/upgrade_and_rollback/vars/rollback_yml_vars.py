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
Rollback Module - rollback.yml Execution Variables.

Variables for running and verifying the ``rollback.yml`` playbook
(the per-component rollback orchestrator) inside the omnia_core container.

Rollback order (reverse of upgrade):
  slurm -> k8s -> build_stream -> oim

Usage:
    from automation_library.upgrade_and_rollback.vars import ROLLBACK_YML_VARS
"""

from typing import Dict, Any, List

from ...core import OMNIA_CORE_CONTAINER
from ...core.vars import (
    OMNIA_DATA_PATH,
    OMNIA_LOG_PATH,
    SOFTWARE_CONFIG_PATH,
)
from .upgrade_core_vars import UPGRADE_VARS

# =============================================================================
# PATH CONSTANTS (using core module vars)
# =============================================================================

ROLLBACK_YML_PLAYBOOK_PATH: str = "/omnia/upgrade/rollback.yml"

ROLLBACK_YML_LOG_FILE: str = (
    f"{OMNIA_LOG_PATH}/rollback_yml_run.log"
)

ROLLBACK_YML_MANIFEST_PATH: str = (
    f"{OMNIA_DATA_PATH}/rollback_manifest.yml"
)

ROLLBACK_YML_SOFTWARE_CONFIG_PATH: str = SOFTWARE_CONFIG_PATH

ROLLBACK_YML_LOCK_PATH: str = (
    f"{OMNIA_DATA_PATH}/upgrade_in_progress.lock"
)

# =============================================================================
# COMPONENT ORDER (reverse of upgrade - rollback undoes last first)
# =============================================================================

ALL_ROLLBACK_COMPONENTS: List[str] = [
    "slurm",
    "k8s",
    "build_stream",
    "oim",
]

# Software config names used in software_config.json
SOFTWARE_CONFIG_NAMES: Dict[str, str] = {
    "slurm": "slurm_custom",
    "k8s": "service_k8s",
    "build_stream": "build_stream",
}

# =============================================================================
# COMPONENT PREREQUISITES (dependencies for rollback)
# Rollback reverses upgrade order, so later upgrades roll back first.
# =============================================================================

ROLLBACK_COMPONENT_PREREQUISITES: Dict[str, List[str]] = {
    "slurm": [],
    "k8s": ["slurm"],
    "build_stream": ["slurm", "k8s"],
    "oim": ["slurm", "k8s", "build_stream"],
}

# =============================================================================
# ROLLBACK_YML_VARS - single source of truth for functions + tests
# =============================================================================

ROLLBACK_YML_VARS: Dict[str, Any] = {

    # Container / path constants
    "container_name": OMNIA_CORE_CONTAINER,
    "playbook_path": ROLLBACK_YML_PLAYBOOK_PATH,
    "log_file": ROLLBACK_YML_LOG_FILE,
    "manifest_path": ROLLBACK_YML_MANIFEST_PATH,
    "software_config_path": ROLLBACK_YML_SOFTWARE_CONFIG_PATH,
    "upgrade_lock_path": ROLLBACK_YML_LOCK_PATH,

    # Version info (from upgrade vars)
    "source_version": UPGRADE_VARS["new_version"],
    "target_version": UPGRADE_VARS["current_version"],

    # Component configuration
    "all_components": ALL_ROLLBACK_COMPONENTS,
    "software_config_names": SOFTWARE_CONFIG_NAMES,
    "component_prerequisites": ROLLBACK_COMPONENT_PREREQUISITES,

    # Polling
    "poll_interval": 30,
    "timeout": 14400,
    "tail_lines": 150,

    # Retry configuration
    "max_retries": 3,
    "retry_delay": 120,
}
