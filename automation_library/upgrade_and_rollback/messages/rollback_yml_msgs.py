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
Rollback Module - rollback.yml Execution Messages.

Test names, log messages, assertion messages, and skip messages for
automated execution of ``rollback.yml`` component sub-flows.

Rollback order (reverse of upgrade):
  slurm -> k8s -> build_stream -> oim
"""

from typing import Dict

# =============================================================================
# TEST NAMES - displayed in reports and TestLogger
# =============================================================================

ROLLBACK_YML_TEST_NAMES: Dict[str, str] = {
    "preflight": (
        "Verify rollback pre-conditions "
        "(container running, playbook exists)"
    ),
    "lock_check": (
        "Verify no upgrade is currently in progress"
    ),
    "run_all": (
        "Run rollback.yml (all components in reverse order)"
    ),
    "verify_manifest": (
        "Verify rollback_manifest.yml exists and is readable"
    ),
    "slurm_check_enabled": (
        "Check Slurm is enabled in software_config.json"
    ),
    "slurm_verify": (
        "Verify slurm rollback completed "
        "in rollback_manifest.yml"
    ),
    "k8s_check_enabled": (
        "Check Kubernetes is enabled in software_config.json"
    ),
    "k8s_verify": (
        "Verify k8s rollback completed "
        "in rollback_manifest.yml"
    ),
    "build_stream_check_enabled": (
        "Check Build Stream is enabled in software_config.json"
    ),
    "build_stream_verify": (
        "Verify build_stream rollback completed "
        "in rollback_manifest.yml"
    ),
    "oim_verify": (
        "Verify OIM rollback completed "
        "in rollback_manifest.yml"
    ),
}

# =============================================================================
# ASSERT MESSAGES - used in pytest.fail() for clear failure reasons
# =============================================================================

ROLLBACK_YML_ASSERT_MSGS: Dict[str, str] = {
    "container_not_running": (
        "omnia_core container is not running. "
        "Check: podman ps | grep omnia_core"
    ),
    "playbook_not_found": (
        "rollback.yml not found at {path} "
        "inside omnia_core container"
    ),
    "rollback_already_running": (
        "rollback.yml is already running inside omnia_core.\n"
        "Running process:\n{process_info}\n\n"
        "Wait for it to complete or check logs:\n"
        "  podman exec omnia_core cat {log_file}"
    ),
    "upgrade_in_progress": (
        "An upgrade is currently in progress "
        "(lock file exists: {lock_path}).\n"
        "Wait for upgrade to complete before rolling back."
    ),
    "run_failed": (
        "rollback.yml [{tags}] failed with rc={rc}.\n\n"
        "Last {tail_lines} lines of output:\n{output}"
    ),
    "run_timeout": (
        "rollback.yml [{tags}] timed out after {timeout}s.\n\n"
        "Last {tail_lines} lines of output:\n{output}"
    ),
    "manifest_not_found": (
        "rollback_manifest.yml not found at {path}. "
        "rollback.yml may not have started."
    ),
    "manifest_parse_error": (
        "Failed to parse rollback_manifest.yml: {error}"
    ),
    "manifest_status_not_completed": (
        "rollback_status is '{status}' "
        "(expected 'completed')"
    ),
    "component_not_completed": (
        "Component '{component}' rollback status is '{status}' "
        "(expected 'completed' or 'skipped')"
    ),
    "component_not_found": (
        "Component '{component}' not found "
        "in rollback_manifest.yml. "
        "Ensure rollback.yml ran with this component."
    ),
    "software_config_read_failed": (
        "Failed to read software_config.json: {error}"
    ),
}

# =============================================================================
# SKIP MESSAGES - used in pytest.skip() for conditional tests
# =============================================================================

ROLLBACK_YML_SKIP_MSGS: Dict[str, str] = {
    "preflight_failed": (
        "Skipped - pre-flight check failed "
        "(container not running or playbook not found)"
    ),
    "run_failed": (
        "Skipped - rollback.yml execution failed in TC-3"
    ),
    "slurm_not_enabled": (
        "Skipped - slurm_custom not found "
        "in software_config.json"
    ),
    "k8s_not_enabled": (
        "Skipped - service_k8s not found "
        "in software_config.json"
    ),
    "build_stream_not_enabled": (
        "Skipped - build_stream not found "
        "in software_config.json"
    ),
    "already_completed": (
        "Skipped - rollback already completed "
        "(rollback_status=completed)"
    ),
}

# =============================================================================
# LOG MESSAGES - printed during test execution by TestLogger
# =============================================================================

ROLLBACK_YML_LOG_MSGS: Dict[str, str] = {
    "checking_container": (
        "Checking omnia_core container is running"
    ),
    "container_ok": (
        "omnia_core container is running"
    ),
    "container_not_running": (
        "omnia_core container is not running"
    ),
    "checking_playbook": (
        "Checking rollback.yml exists at {path}"
    ),
    "playbook_found": (
        "rollback.yml found: {path}"
    ),
    "playbook_not_found": (
        "rollback.yml not found at {path}"
    ),
    "checking_running": (
        "Checking if rollback.yml is currently running"
    ),
    "not_running": (
        "rollback.yml not currently running"
    ),
    "already_running": (
        "rollback.yml is already running"
    ),
    "checking_lock": (
        "Checking upgrade lock at {path}"
    ),
    "no_lock": "No upgrade in progress",
    "lock_exists": (
        "Upgrade lock exists - upgrade in progress"
    ),
    "starting_rollback": (
        "Starting rollback.yml [{tags}]"
    ),
    "rollback_running": (
        "rollback.yml running... elapsed {elapsed}s"
    ),
    "rollback_completed": (
        "rollback.yml [{tags}] completed (rc={rc})"
    ),
    "rollback_failed": (
        "rollback.yml [{tags}] failed (rc={rc})"
    ),
    "rollback_timeout": (
        "rollback.yml [{tags}] timed out "
        "after {timeout}s"
    ),
    "checking_manifest": (
        "Checking rollback_manifest.yml at {path}"
    ),
    "manifest_found": (
        "rollback_manifest.yml exists"
    ),
    "manifest_not_found": (
        "rollback_manifest.yml not found"
    ),
    "manifest_status": "rollback_status: {status}",
    "checking_component": (
        "Verifying {component} status "
        "in rollback_manifest.yml"
    ),
    "component_completed": (
        "{component}: {status}"
    ),
    "component_failed": (
        "{component}: {status}"
    ),
    "component_not_found": (
        "{component}: not found in manifest"
    ),
    "checking_software": (
        "Checking if {software} is enabled "
        "in software_config.json"
    ),
    "software_enabled": (
        "{software} is enabled"
    ),
    "software_not_enabled": (
        "{software} is not enabled - skipping"
    ),
}
