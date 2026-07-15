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
Upgrade Module - upgrade.yml Execution Variables.

Variables for running and verifying the ``upgrade.yml`` playbook
(the per-component upgrade orchestrator) inside the omnia_core container.

Supported components (in upgrade order):
  oim → local_repo → build_image → provision → k8s → slurm → openchami

Usage:
    from automation_library.upgrade_and_rollback.vars import UPGRADE_YML_VARS
"""

from typing import Dict, Any, List

from ...core import OMNIA_CORE_CONTAINER
from ...core.vars import OMNIA_DATA_PATH, SOFTWARE_CONFIG_PATH
from .upgrade_core_vars import UPGRADE_VARS

# =============================================================================
# PATH CONSTANTS (using core module vars)
# =============================================================================

UPGRADE_YML_PLAYBOOK_PATH: str = "/omnia/upgrade/upgrade.yml"

UPGRADE_YML_LOG_FILE: str = "/tmp/upgrade_yml_run.log"

UPGRADE_YML_MANIFEST_PATH: str = f"{OMNIA_DATA_PATH}/upgrade_manifest.yml"

UPGRADE_YML_SOFTWARE_CONFIG_PATH: str = SOFTWARE_CONFIG_PATH

UPGRADE_YML_LOCK_PATH: str = f"{OMNIA_DATA_PATH}/upgrade_in_progress.lock"

# =============================================================================
# COMPONENT ORDER (must match upgrade.yml tag order)
# =============================================================================

ALL_UPGRADE_COMPONENTS: List[str] = [
    "oim",
    "k8s",
    "slurm",
    "openchami",
]

# Software config names used in software_config.json to detect enabled components
SOFTWARE_CONFIG_NAMES: Dict[str, str] = {
    "k8s": "service_k8s",
    "slurm": "slurm_custom",
    "openchami": "openchami",
}

# =============================================================================
# PER-COMPONENT TIMEOUTS (seconds)
# =============================================================================

UPGRADE_COMPONENT_TIMEOUTS: Dict[str, int] = {
    "oim": 3600,           # 1 hour  — OIM + Pulp container upgrade
    "k8s": 7200,           # 2 hours — K8s + Telemetry upgrade
    "slurm": 3600,         # 1 hour  — Slurm node upgrades + cloud-init
    "openchami": 2400,     # 40 min  — OpenCHAMI upgrade
}

# =============================================================================
# COMPONENT PREREQUISITES (dependencies for upgrade)
# Each component requires these to be completed/skipped before it can run.
# =============================================================================

UPGRADE_COMPONENT_PREREQUISITES: Dict[str, List[str]] = {
    "oim": [],                                    # First to upgrade, no deps
    "k8s": ["oim"],                               # After OIM
    "slurm": ["oim"],                             # After OIM
    "openchami": ["oim"],                         # After OIM
}

# =============================================================================
# UPGRADE_YML_VARS — single source of truth for functions + tests
# =============================================================================

UPGRADE_YML_VARS: Dict[str, Any] = {

    # =========================================================================
    # CONTAINER / PATH CONSTANTS
    # =========================================================================
    "container_name": OMNIA_CORE_CONTAINER,
    "playbook_path": UPGRADE_YML_PLAYBOOK_PATH,
    "log_file": UPGRADE_YML_LOG_FILE,
    "manifest_path": UPGRADE_YML_MANIFEST_PATH,
    "software_config_path": UPGRADE_YML_SOFTWARE_CONFIG_PATH,
    "upgrade_lock_path": UPGRADE_YML_LOCK_PATH,

    # =========================================================================
    # VERSION INFO (from upgrade vars)
    # =========================================================================
    "source_version": UPGRADE_VARS["current_version"],   # Upgrading FROM
    "target_version": UPGRADE_VARS["new_version"],        # Upgrading TO

    # =========================================================================
    # COMPONENT CONFIGURATION
    # =========================================================================
    "all_components": ALL_UPGRADE_COMPONENTS,
    "software_config_names": SOFTWARE_CONFIG_NAMES,
    "component_timeouts": UPGRADE_COMPONENT_TIMEOUTS,
    "component_prerequisites": UPGRADE_COMPONENT_PREREQUISITES,

    # =========================================================================
    # TIMEOUTS & POLLING
    # =========================================================================
    "default_timeout": 14400,  # 4 hours fallback for multi-tag or unknown runs
    "poll_interval": 30,       # seconds between polls during execution
    "tail_lines": 150,         # lines of log tail shown on completion/failure

    # =========================================================================
    # RETRY CONFIGURATION
    # K8s upgrades involve node reboots which can cause transient SSH failures.
    # Retrying lets upgrade.yml resume from the last completed component
    # (idempotent via upgrade_manifest.yml).
    # =========================================================================
    "max_retries": 3,          # total attempts (1 = no retry)
    "retry_delay": 120,        # seconds to wait between retries
}
