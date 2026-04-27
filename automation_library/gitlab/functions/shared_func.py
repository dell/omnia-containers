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
GitLab Automation - Shared Functions.

This module provides shared functions used across GitLab automation.

For module-specific functions, see:
- gitlab_func.py - GitLab verification functions
"""

from typing import Any, Dict

import pytest

from ...core import (
    load_input_file,
    get_input_value,
    run_in_container,
    get_credential_value,
    is_build_stream_enabled,
    clear_input_cache,
    GITLAB_CONFIG_FILE,
    OMNIA_CREDENTIALS_PATH,
    OMNIA_CREDENTIALS_KEY_PATH,
)


# =============================================================================
# CACHING - Uses core/load_inputs.py cache
# =============================================================================

_credentials_cache: Dict[str, str] = {}


def clear_cache():
    """Clear all caches. Useful for testing or when config changes."""
    clear_input_cache()
    _credentials_cache.clear()


# =============================================================================
# CONFIGURATION READING FUNCTIONS (using core/load_inputs.py)
# =============================================================================

def get_gitlab_config(host) -> Dict[str, Any]:
    """Read gitlab_config.yml from container (cached by core)."""
    return load_input_file(host, GITLAB_CONFIG_FILE)


def get_gitlab_host(host) -> str:
    """Get gitlab_host from gitlab_config.yml."""
    return get_input_value(host, GITLAB_CONFIG_FILE, "gitlab_host", default="")


def get_gitlab_https_port(host) -> int:
    """Get gitlab_https_port from gitlab_config.yml."""
    return get_input_value(host, GITLAB_CONFIG_FILE, "gitlab_https_port", default=443)


def get_gitlab_project_name(host) -> str:
    """Get gitlab_project_name from gitlab_config.yml."""
    return get_input_value(host, GITLAB_CONFIG_FILE, "gitlab_project_name", default="")


def get_gitlab_puma_workers(host) -> int:
    """Get gitlab_puma_workers from gitlab_config.yml."""
    return get_input_value(host, GITLAB_CONFIG_FILE, "gitlab_puma_workers", default=2)


def get_gitlab_sidekiq_concurrency(host) -> int:
    """Get gitlab_sidekiq_concurrency from gitlab_config.yml."""
    return get_input_value(host, GITLAB_CONFIG_FILE, "gitlab_sidekiq_concurrency", default=10)


def get_gitlab_min_resources(host) -> Dict[str, int]:
    """Get minimum resource requirements from gitlab_config.yml."""
    return {
        "min_storage_gb": get_input_value(
            host, GITLAB_CONFIG_FILE, "gitlab_min_storage_gb", default=20
        ),
        "min_memory_gb": get_input_value(
            host, GITLAB_CONFIG_FILE, "gitlab_min_memory_gb", default=4
        ),
        "min_cpu_cores": get_input_value(
            host, GITLAB_CONFIG_FILE, "gitlab_min_cpu_cores", default=2
        ),
    }


# =============================================================================
# CREDENTIAL FUNCTIONS
# =============================================================================

def get_provision_password(host) -> str:
    """Get provision_password from omnia_config_credentials.yml (cached)."""
    cache_key = "provision_password"
    if cache_key in _credentials_cache:
        return _credentials_cache[cache_key]

    password = get_credential_value(
        host,
        OMNIA_CREDENTIALS_PATH,
        OMNIA_CREDENTIALS_KEY_PATH,
        "provision_password"
    )
    _credentials_cache[cache_key] = password
    return password


def get_gitlab_root_password(host) -> str:
    """Get gitlab_root_password from omnia_config_credentials.yml (cached)."""
    cache_key = "gitlab_root_password"
    if cache_key in _credentials_cache:
        return _credentials_cache[cache_key]

    password = get_credential_value(
        host,
        OMNIA_CREDENTIALS_PATH,
        OMNIA_CREDENTIALS_KEY_PATH,
        "gitlab_root_password"
    )
    _credentials_cache[cache_key] = password
    return password


# =============================================================================
# SSH COMMAND EXECUTION (via omnia_core container)
# =============================================================================

def ssh_to_gitlab(host, command: str) -> Dict[str, Any]:
    """
    Execute command on GitLab server via SSH through omnia_core container.

    Uses sshpass with provision_password for authentication.

    Args:
        host: Testinfra host object
        command: Command to execute on GitLab server

    Returns:
        Dict with success, rc, stdout, stderr, error keys
    """
    result = {
        "success": False,
        "rc": -1,
        "stdout": "",
        "stderr": "",
        "error": "",
    }

    gitlab_host = get_gitlab_host(host)
    if not gitlab_host:
        result["error"] = "gitlab_host not configured in gitlab_config.yml"
        return result

    provision_pwd = get_provision_password(host)
    if not provision_pwd:
        result["error"] = "provision_password not found in credentials"
        return result

    ssh_cmd = (
        f"sshpass -p '{provision_pwd}' ssh -o StrictHostKeyChecking=no "
        f"root@{gitlab_host} '{command}'"
    )

    cmd = run_in_container(host, ssh_cmd)
    result["rc"] = cmd.rc
    result["stdout"] = cmd.stdout.strip() if cmd.stdout else ""
    result["stderr"] = cmd.stderr.strip() if cmd.stderr else ""
    result["success"] = cmd.rc == 0

    if cmd.rc != 0:
        result["error"] = result["stderr"] or f"Command failed with rc={cmd.rc}"

    return result


# =============================================================================
# TEST HELPER FUNCTIONS
# =============================================================================

def skip_if_build_stream_not_enabled(host, log):
    """
    Skip test if build_stream is not enabled.

    Checks enable_build_stream in build_stream_config.yml.

    Args:
        host: Testinfra host object
        log: TestLogger instance
    """
    if not is_build_stream_enabled(host):
        log.skipped(
            "build_stream is not enabled (enable_build_stream=false)",
            "Test skipped - GitLab requires build_stream to be enabled"
        )
        pytest.skip("build_stream is not enabled")
