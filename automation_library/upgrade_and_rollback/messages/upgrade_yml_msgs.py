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
Upgrade Module - upgrade.yml Execution Messages.

Test names, log messages, assertion messages, and skip messages for
automated execution of ``upgrade.yml`` component sub-flows.

Components covered (in upgrade order):
  oim → k8s → slurm → openchami
"""

from typing import Dict

# =============================================================================
# TEST NAMES — displayed in reports and TestLogger
# =============================================================================

UPGRADE_YML_TEST_NAMES: Dict[str, str] = {

    # Pre-flight
    "preflight": (
        "Verify upgrade pre-conditions (container running, playbook exists)"
    ),

    # Full upgrade
    "run_all": (
        "Run upgrade.yml (all components in order)"
    ),
    "verify_manifest": (
        "Verify upgrade_manifest.yml exists and is readable"
    ),

    # OIM
    "oim_verify": (
        "Verify OIM component status = completed in upgrade_manifest.yml"
    ),

    # Kubernetes
    "k8s_check_enabled": (
        "Check Kubernetes is enabled in software_config.json"
    ),
    "k8s_verify": (
        "Verify k8s component status = completed in upgrade_manifest.yml"
    ),

    # Slurm
    "slurm_check_enabled": (
        "Check Slurm is enabled in software_config.json"
    ),
    "slurm_verify": (
        "Verify slurm component status = completed in upgrade_manifest.yml"
    ),

    # OpenCHAMI
    "openchami_check_enabled": (
        "Check OpenCHAMI is enabled in software_config.json"
    ),
    "openchami_verify": (
        "Verify openchami component status = completed in upgrade_manifest.yml"
    ),
}

# =============================================================================
# ASSERT MESSAGES — used in pytest.fail() for clear failure reasons
# =============================================================================

UPGRADE_YML_ASSERT_MSGS: Dict[str, str] = {

    # Pre-flight
    "container_not_running": (
        "omnia_core container is not running. "
        "Check: podman ps | grep omnia_core"
    ),
    "playbook_not_found": (
        "upgrade.yml not found at {path} inside omnia_core container"
    ),
    "upgrade_already_running": (
        "upgrade.yml is already running inside omnia_core.\n"
        "Running process:\n{process_info}\n\n"
        "Wait for it to complete or check logs:\n"
        "  podman exec omnia_core cat {log_file}"
    ),

    # Run
    "run_failed": (
        "upgrade.yml [{tags}] failed with rc={rc}.\n\n"
        "Last {tail_lines} lines of output:\n{output}"
    ),
    "run_timeout": (
        "upgrade.yml [{tags}] timed out after {timeout}s.\n\n"
        "Last {tail_lines} lines of output:\n{output}"
    ),

    # Manifest
    "manifest_not_found": (
        "upgrade_manifest.yml not found at {path}. "
        "upgrade.yml may not have started."
    ),
    "manifest_parse_error": (
        "Failed to parse upgrade_manifest.yml: {error}"
    ),
    "manifest_status_not_completed": (
        "upgrade_status is '{status}' (expected 'completed')"
    ),

    # Component status
    "component_not_completed": (
        "Component '{component}' status is '{status}' "
        "(expected 'completed' or 'skipped')"
    ),
    "component_not_found": (
        "Component '{component}' not found in upgrade_manifest.yml. "
        "Ensure upgrade.yml ran with this component enabled."
    ),

    # Software config
    "software_config_read_failed": (
        "Failed to read software_config.json: {error}"
    ),
}

# =============================================================================
# SKIP MESSAGES — used in pytest.skip() for conditional tests
# =============================================================================

UPGRADE_YML_SKIP_MSGS: Dict[str, str] = {
    "preflight_failed": (
        "Skipped — pre-flight check failed (container not running or "
        "playbook not found)"
    ),
    "run_failed": (
        "Skipped — upgrade.yml execution failed in TC-2"
    ),
    "k8s_not_enabled": (
        "Skipped — service_k8s not found in software_config.json"
    ),
    "slurm_not_enabled": (
        "Skipped — slurm_custom not found in software_config.json"
    ),
    "openchami_not_enabled": (
        "Skipped — openchami not found in software_config.json"
    ),
    "already_completed": (
        "Skipped — upgrade already completed (upgrade_status=completed)"
    ),
}

# =============================================================================
# LOG MESSAGES — printed during test execution by TestLogger
# =============================================================================

UPGRADE_YML_LOG_MSGS: Dict[str, str] = {

    # --- Pre-flight ----------------------------------------------------------
    "checking_container": "Checking omnia_core container is running",
    "container_ok": "✓ omnia_core container is running",
    "container_not_running": "✗ omnia_core container is not running",

    "checking_playbook": "Checking upgrade.yml exists at {path}",
    "playbook_found": "✓ upgrade.yml found: {path}",
    "playbook_not_found": "✗ upgrade.yml not found at {path}",

    "checking_running": "Checking if upgrade.yml is currently running",
    "not_running": "✓ upgrade.yml not currently running",
    "already_running": "✗ upgrade.yml is already running",

    # --- Run -----------------------------------------------------------------
    "starting_upgrade": "Starting upgrade.yml [{tags}]",
    "upgrade_running": "upgrade.yml running... elapsed {elapsed}s",
    "upgrade_completed": "✓ upgrade.yml [{tags}] completed (rc={rc})",
    "upgrade_failed": "✗ upgrade.yml [{tags}] failed (rc={rc})",
    "upgrade_timeout": "✗ upgrade.yml [{tags}] timed out after {timeout}s",

    # --- Manifest ------------------------------------------------------------
    "checking_manifest": "Checking upgrade_manifest.yml at {path}",
    "manifest_found": "✓ upgrade_manifest.yml exists",
    "manifest_not_found": "✗ upgrade_manifest.yml not found",
    "manifest_status": "upgrade_status: {status}",

    # --- Component verification ----------------------------------------------
    "checking_component": "Verifying {component} status in upgrade_manifest.yml",
    "component_completed": "✓ {component}: {status}",
    "component_failed": "✗ {component}: {status}",
    "component_not_found": "✗ {component}: not found in manifest",

    # --- Software config check -----------------------------------------------
    "checking_software": "Checking if {software} is enabled in software_config.json",
    "software_enabled": "✓ {software} is enabled",
    "software_not_enabled": "↷ {software} is not enabled — skipping",
}
