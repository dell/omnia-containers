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
Additional Cloud-Init Module - Common Functions.

Common utilities for additional cloud-init configuration handling.
"""

import os
import pytest
from typing import Dict, Any, List, Optional

from automation_library.core import (
    TestLogger,
    load_input_file,
    get_input_value,
    get_functional_groups_from_pxe_mapping,
    get_nodes_info,
)
from ..vars.common_vars import ADDITIONAL_CLOUD_INIT_CONFIG_PATH


# Configuration cache
_config_cache: Dict[str, Any] = {}


def clear_cache():
    """Clear all caches. Call at start of test run."""
    _config_cache.clear()


def load_additional_cloud_init_config(host) -> Dict[str, Any]:
    """
    Load and parse the additional_cloud_init configuration file.

    Args:
        host: Testinfra host object

    Returns:
        Dict containing:
            - success (bool): True if config loaded successfully
            - error (str): Error message if failed
            - config (dict): Parsed configuration data
            - enabled (bool): True if feature is enabled
    """
    cache_key = "additional_cloud_init_config"
    if cache_key in _config_cache:
        return _config_cache[cache_key]

    try:
        # Get the config file path from provision_config.yml
        config_file_path = get_input_value(
            host, 
            "provision_config.yml", 
            "additional_cloud_init_config_file", 
            ""
        )
        
        if not config_file_path or config_file_path.strip() == "":
            result = {
                "success": True,
                "error": "",
                "config": {},
                "enabled": False,
            }
            _config_cache[cache_key] = result
            return result

        # Load the actual config file
        # Extract just the filename since load_input_file prepends INPUT_BASE_PATH
        config_filename = os.path.basename(config_file_path)
        config_data = load_input_file(host, config_filename)
        
        if not config_data:
            config_data = {}

        result = {
            "success": True,
            "error": "",
            "config": config_data,
            "enabled": bool(config_data),
        }
        
    except Exception as e:
        result = {
            "success": False,
            "error": f"Failed to load additional_cloud_init config: {str(e)}",
            "config": {},
            "enabled": False,
        }

    _config_cache[cache_key] = result
    return result


def get_functional_groups_from_config(host, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get functional groups from additional cloud-init config and validate against PXE mapping.

    Args:
        host: Testinfra host object
        config: Additional cloud-init configuration

    Returns:
        Dict containing:
            - success (bool): True if successful
            - error (str): Error message if failed
            - common_groups (list): Functional groups for common section
            - per_fg_groups (list): Per-FG functional groups
            - all_groups (set): All functional groups referenced
            - available_groups (set): Available groups in PXE mapping
    """
    try:
        # Get available functional groups from PXE mapping
        available_groups = get_functional_groups_from_pxe_mapping(host)
        
        # Get groups from config
        common_groups = []
        per_fg_groups = []
        all_groups = set()
        
        # If common section exists, applies to ALL groups in PXE mapping
        if config.get("common"):
            common_groups = list(available_groups)
            all_groups.update(available_groups)
        
        # Get per-FG groups
        groups_section = config.get("groups", {})
        if groups_section:
            per_fg_groups = list(groups_section.keys())
            all_groups.update(per_fg_groups)
        
        return {
            "success": True,
            "error": "",
            "common_groups": common_groups,
            "per_fg_groups": per_fg_groups,
            "all_groups": all_groups,
            "available_groups": available_groups,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get functional groups: {str(e)}",
            "common_groups": [],
            "per_fg_groups": [],
            "all_groups": set(),
            "available_groups": set(),
        }


def skip_if_additional_cloud_init_disabled(host, log: TestLogger = None):
    """Skip test if additional cloud-init is not enabled."""
    config_result = load_additional_cloud_init_config(host)
    
    if not config_result["success"]:
        reason = f"Failed to load config: {config_result['error']}"
        if log:
            log.skipped(reason, "Test skipped")
        pytest.skip(reason)
    
    if not config_result["enabled"]:
        reason = "Additional cloud-init is not enabled (empty or no config file)"
        if log:
            log.skipped(reason, "Test skipped")
        pytest.skip(reason)


def get_nodes_by_functional_group(host, functional_group: str) -> List[Dict[str, Any]]:
    """
    Get nodes for a specific functional group.

    Args:
        host: Testinfra host object
        functional_group: Functional group name

    Returns:
        List of node dictionaries from PXE mapping
    """
    try:
        return get_nodes_info(host, search_by="functional_group", search_value=functional_group)
    except Exception:
        return []


def get_all_nodes_for_common(host) -> List[Dict[str, Any]]:
    """
    Get all nodes from PXE mapping for common cloud-init section.

    Args:
        host: Testinfra host object

    Returns:
        List of all node dictionaries from PXE mapping
    """
    try:
        available_groups = get_functional_groups_from_pxe_mapping(host)
        all_nodes = []
        
        for fg in available_groups:
            nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
            all_nodes.extend(nodes)
            
        return all_nodes
    except Exception:
        return []
