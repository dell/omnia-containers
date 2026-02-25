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
    from automation_library.core.load_inputs import load_input_file, get_input_value

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

from .host import run_in_container
from .vars import INPUT_BASE_PATH

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
