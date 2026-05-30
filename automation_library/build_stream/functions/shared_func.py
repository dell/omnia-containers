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
Build Stream Automation - Shared Functions.

This module provides shared functions used across build_stream automation.
All runtime values are read from config files via core module functions.
"""

from typing import Any, Dict

import pytest

from automation_library.core import (
    load_input_file,
    get_input_value,
    run_in_container,
    get_credential_value,
    is_build_stream_enabled,
    clear_input_cache,
    BUILD_STREAM_CONFIG_FILE,
    GITLAB_CONFIG_FILE,
    OMNIA_CREDENTIALS_PATH,
    OMNIA_CREDENTIALS_KEY_PATH,
)

from ..vars.build_stream_vars import (
    BUILD_STREAM_HOST_IP_KEY,
    BUILD_STREAM_PORT_KEY,
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
# BUILD STREAM CONFIGURATION READING FUNCTIONS
# =============================================================================

def get_build_stream_config(host) -> Dict[str, Any]:
    """Read build_stream_config.yml from container (cached by core)."""
    return load_input_file(host, BUILD_STREAM_CONFIG_FILE) or {}


def get_build_stream_host_ip(host) -> str:
    """Get build_stream_host_ip from build_stream_config.yml."""
    return get_input_value(host, BUILD_STREAM_CONFIG_FILE, BUILD_STREAM_HOST_IP_KEY, default="")


def get_build_stream_port(host) -> int:
    """Get build_stream_port from build_stream_config.yml."""
    return get_input_value(host, BUILD_STREAM_CONFIG_FILE, BUILD_STREAM_PORT_KEY, default=8056)


# =============================================================================
# GITLAB CONFIGURATION READING FUNCTIONS
# =============================================================================

def get_gitlab_host(host) -> str:
    """Get gitlab_host from gitlab_config.yml."""
    return get_input_value(host, GITLAB_CONFIG_FILE, "gitlab_host", default="")


def get_gitlab_https_port(host) -> int:
    """Get gitlab_https_port from gitlab_config.yml."""
    return get_input_value(host, GITLAB_CONFIG_FILE, "gitlab_https_port", default=443)


def get_gitlab_project_name(host) -> str:
    """Get gitlab_project_name from gitlab_config.yml."""
    return get_input_value(host, GITLAB_CONFIG_FILE, "gitlab_project_name", default="")


def get_gitlab_default_branch(host) -> str:
    """Get gitlab_default_branch from gitlab_config.yml."""
    return get_input_value(host, GITLAB_CONFIG_FILE, "gitlab_default_branch", default="main")


# =============================================================================
# CREDENTIAL FUNCTIONS
# =============================================================================

def get_postgres_user(host) -> str:
    """
    Get postgres_user from omnia_config_credentials.yml (cached).

    Falls back to 'omnia' if not found in credentials file.
    """
    cache_key = "postgres_user"
    if cache_key in _credentials_cache:
        return _credentials_cache[cache_key]

    user = get_credential_value(
        host,
        OMNIA_CREDENTIALS_PATH,
        OMNIA_CREDENTIALS_KEY_PATH,
        "postgres_user"
    )
    _credentials_cache[cache_key] = user or "omnia"
    return _credentials_cache[cache_key]


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
    _credentials_cache[cache_key] = password or ""
    return _credentials_cache[cache_key]


# =============================================================================
# OMNIA TEST CONFIG FUNCTIONS
# =============================================================================

def get_allow_pipeline_cancel(host) -> bool:
    """
    Get allow_pipeline_cancel from omnia_test_config.yml.

    If true, automation will auto-cancel running/pending pipelines.
    Default: False (requires manual cancellation).
    """
    import yaml
    import os

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "omnia_test_config.yml"
    )

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
        return config.get("allow_pipeline_cancel", False)
    except Exception:
        return False


def get_image_identifier(host) -> str:
    """
    Get image_identifier from omnia_test_config.yml.

    Used by BOTH deploy and cleanup pipelines to select which image group to use.
    If set, automation will use this specific image group.
    If empty, automation will auto-select the latest BUILT image group.

    Returns:
        Image group identifier string, or empty string for auto-select.
    """
    import yaml
    import os

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "omnia_test_config.yml"
    )

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
        return config.get("image_identifier", "") or ""
    except Exception:
        return ""


# =============================================================================
# SSH COMMAND EXECUTION (via omnia_core container to GitLab server)
# =============================================================================

def ssh_to_gitlab(host, command: str) -> Dict[str, Any]:
    """
    Execute command on GitLab server via SSH through omnia_core container.

    Uses the omnia_gitlab SSH key for authentication.

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

    ssh_cmd = (
        f"ssh -o StrictHostKeyChecking=no -o BatchMode=yes "
        f"-i /opt/omnia/ssh_config/.ssh/omnia_gitlab "
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
            "Test skipped - build_stream not enabled"
        )
        pytest.skip("build_stream is not enabled")
