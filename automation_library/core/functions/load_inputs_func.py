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
Core Input Loader - Centralized config file reader for omnia_core container.

Reads YAML/JSON config files from inside the omnia_core container with
automatic caching to avoid repeated podman exec calls.

Usage:
    from automation_library.core import load_input_file, get_input_value

    # Load entire config as dict
    config = load_input_file(host, "build_stream_config.yml")

    # Get a single value with default
    ip = get_input_value(host, "build_stream_config.yml", "build_stream_host_ip", default="")

    # Nested key access (dot-separated)
    port = get_input_value(host, "build_stream_config.yml", "api.port", default=8010)
"""

import json
from typing import Any, Dict

import yaml

from .host_func_full import run_in_container
from ..vars.paths_vars import INPUT_BASE_PATH

# =============================================================================
# CACHE
# =============================================================================

_input_cache: Dict[str, Any] = {}


def clear_input_cache():
    """Clear all cached input files. Call at start of test run if needed."""
    _input_cache.clear()


# =============================================================================
# CORE LOADER FUNCTIONS
# =============================================================================

def load_container_file(host, filepath: str) -> Dict[str, Any]:
    """
    Load any YAML/JSON file by full path from omnia_core container with caching.

    Unlike load_input_file which only reads from INPUT_BASE_PATH,
    this function accepts an absolute path inside the container.

    Args:
        host: Testinfra host object
        filepath: Absolute path inside container (e.g., "/opt/omnia/.data/oim_metadata.yml")

    Returns:
        Parsed config as dict, or empty dict if file not found or parse error
    """
    if filepath in _input_cache:
        return _input_cache[filepath]

    cmd = run_in_container(host, f"cat '{filepath}' 2>/dev/null")

    if cmd.rc != 0 or not cmd.stdout.strip():
        _input_cache[filepath] = {}
        return {}

    content = cmd.stdout.strip()

    try:
        if filepath.endswith((".yml", ".yaml")):
            config = yaml.safe_load(content) or {}
        elif filepath.endswith(".json"):
            config = json.loads(content)
        else:
            config = yaml.safe_load(content) or {}
    except (yaml.YAMLError, json.JSONDecodeError):
        config = {}

    _input_cache[filepath] = config
    return config


def load_input_file(host, filename: str) -> Dict[str, Any]:
    """
    Load a config file from omnia_core container with caching.

    Supports YAML (.yml, .yaml) and JSON (.json) files.
    Files are read from INPUT_BASE_PATH inside the omnia_core container.

    Args:
        host: Testinfra host object
        filename: Config filename (e.g., "build_stream_config.yml")

    Returns:
        Parsed config as dict, or empty dict if file not found or parse error
    """
    if filename in _input_cache:
        return _input_cache[filename]

    filepath = f"{INPUT_BASE_PATH}/{filename}"
    cmd = run_in_container(host, f"cat '{filepath}' 2>/dev/null")

    if cmd.rc != 0 or not cmd.stdout.strip():
        _input_cache[filename] = {}
        return {}

    content = cmd.stdout.strip()

    try:
        if filename.endswith((".yml", ".yaml")):
            config = yaml.safe_load(content) or {}
        elif filename.endswith(".json"):
            config = json.loads(content)
        else:
            config = yaml.safe_load(content) or {}
    except (yaml.YAMLError, json.JSONDecodeError):
        config = {}

    _input_cache[filename] = config
    return config


def get_input_value(host, filename: str, key: str, default: Any = None) -> Any:
    """
    Get a single value from a config file inside omnia_core container.

    Supports dot-separated keys for nested access:
        get_input_value(host, "config.yml", "api.port")
        -> config["api"]["port"]

    For list indexing, use bracket notation:
        get_input_value(host, "network_spec.yml", "Networks[0].admin_network.primary_oim_admin_ip")

    Args:
        host: Testinfra host object
        filename: Config filename (e.g., "build_stream_config.yml")
        key: Config key (supports dot notation for nested keys)
        default: Default value if key not found

    Returns:
        Value from config, or default if not found
    """
    config = load_input_file(host, filename)
    if not config:
        return default

    return _resolve_key(config, key, default)


def get_input_bool(host, filename: str, key: str, default: bool = False) -> bool:
    """
    Get a boolean value from a config file, handling string booleans.

    Handles: True/False, "true"/"false", "yes"/"no"

    Args:
        host: Testinfra host object
        filename: Config filename
        key: Config key (supports dot notation)
        default: Default value if key not found

    Returns:
        Boolean value
    """
    val = get_input_value(host, filename, key, default=default)
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "yes", "1")
    return default


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _resolve_key(data: Any, key: str, default: Any = None) -> Any:
    """
    Resolve a dot-separated key path in nested data.

    Supports:
        "simple_key"             -> data["simple_key"]
        "nested.key"             -> data["nested"]["key"]
        "Networks[0].admin_network" -> data["Networks"][0]["admin_network"]
    """
    parts = _parse_key_parts(key)
    current = data

    for part in parts:
        if isinstance(part, int):
            if isinstance(current, list) and 0 <= part < len(current):
                current = current[part]
            else:
                return default
        elif isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                return default
        else:
            return default

    return current


def _parse_key_parts(key: str) -> list:
    """
    Parse a dot-separated key with optional array indices.

    "Networks[0].admin_network.ip" -> ["Networks", 0, "admin_network", "ip"]
    "simple_key"                   -> ["simple_key"]
    """
    parts = []
    for segment in key.split("."):
        if "[" in segment and "]" in segment:
            name, rest = segment.split("[", 1)
            if name:
                parts.append(name)
            idx_str = rest.rstrip("]")
            try:
                parts.append(int(idx_str))
            except ValueError:
                parts.append(idx_str)
        else:
            parts.append(segment)
    return parts


# =============================================================================
# SOFTWARE CONFIG HELPERS
# =============================================================================

def is_software_enabled(host, software_name: str) -> bool:
    """
    Check if a software is enabled in software_config.json.

    Checks if the software_name exists in the softwares list.

    Args:
        host: Testinfra host object
        software_name: Software name to check (e.g., "openldap", "slurm", "ldms")

    Returns:
        True if software is in softwares list, False otherwise

    Example:
        if is_software_enabled(host, "openldap"):
            # Run OpenLDAP-specific tests
    """
    from ..vars.paths_vars import SOFTWARE_CONFIG_FILE
    softwares = get_input_value(host, SOFTWARE_CONFIG_FILE, "softwares")
    if not softwares:
        return False
    for software in softwares:
        if isinstance(software, dict) and software.get("name", "").lower() == software_name.lower():
            return True
    return False


def get_config_list_item(
    host,
    filename: str,
    list_key: str,
    filter_key: str = None,
    filter_value: str = None,
    return_key: str = None,
    fallback_keys: list = None
) -> Any:
    """
    Generic function to get an item from a config list/dict.

    This is a reusable utility for extracting values from config files that
    contain lists of items (e.g., nfs_client_params, softwares, etc.).

    Args:
        host: Testinfra host object
        filename: Config filename (e.g., "storage_config.yml")
        list_key: Key containing the list (e.g., "nfs_client_params")
        filter_key: Optional key to filter items by (e.g., "nfs_name")
        filter_value: Value to match for filter_key
        return_key: Key to return from matched item (e.g., "client_share_path")
        fallback_keys: List of fallback keys if return_key not found

    Returns:
        Matched value, full item dict if no return_key, or None if not found

    Examples:
        # Get NFS client path by name
        get_config_list_item(host, "storage_config.yml", "nfs_client_params",
                             filter_key="nfs_name", filter_value="nfs_slurm",
                             return_key="client_share_path")

        # Get first NFS client path
        get_config_list_item(host, "storage_config.yml", "nfs_client_params",
                             return_key="client_share_path")

        # Get LDMS sampler port from telemetry config
        get_config_list_item(host, "telemetry_config.yml", "ldms_sampler_port")
    """
    config = load_input_file(host, filename)
    if not config:
        return None

    items = config.get(list_key)
    if items is None:
        return None

    # If items is not a list, return the value directly or extract return_key
    if not isinstance(items, list):
        if return_key:
            if isinstance(items, dict):
                result = items.get(return_key)
                if result is None and fallback_keys:
                    for fb_key in fallback_keys:
                        result = items.get(fb_key)
                        if result is not None:
                            break
                return result
            return items
        return items

    # Handle list of items
    if not items:
        return None

    # If filter specified, find matching item
    if filter_key and filter_value:
        for item in items:
            if isinstance(item, dict) and item.get(filter_key) == filter_value:
                if return_key:
                    result = item.get(return_key)
                    if result is None and fallback_keys:
                        for fb_key in fallback_keys:
                            result = item.get(fb_key)
                            if result is not None:
                                break
                    return result
                return item
        return None

    # No filter - return first item's value or first item
    first = items[0]
    if return_key and isinstance(first, dict):
        result = first.get(return_key)
        if result is None and fallback_keys:
            for fb_key in fallback_keys:
                result = first.get(fb_key)
                if result is not None:
                    break
        return result
    return first


def get_nfs_client_mount_path(host, nfs_name: str = None) -> str:
    """
    Get NFS client mount path from storage_config.yml.

    Args:
        host: Testinfra host object
        nfs_name: Optional NFS name to filter (e.g., "nfs_slurm", "nfs_k8s")
                  If not provided, returns first NFS client path

    Returns:
        NFS client mount path string, or empty string if not found
    """
    from ..vars.paths_vars import STORAGE_CONFIG_FILE

    # Try nfs_client_params first (current format), then nfs_client (legacy)
    for list_key in ["nfs_client_params", "nfs_client"]:
        result = get_config_list_item(
            host, STORAGE_CONFIG_FILE, list_key,
            filter_key="nfs_name" if nfs_name else None,
            filter_value=nfs_name,
            return_key="client_share_path",
            fallback_keys=["client_mount_path"]
        )
        if result:
            return result

    return ""
