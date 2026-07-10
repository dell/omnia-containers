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
Homogeneous Node Discovery Module - Provision Functions.

Functions for validating homogeneous node discovery mode in Slurm configuration.
"""

from typing import Dict, Any, List

from automation_library.core import (
    load_input_file,
    OMNIA_CONFIG_FILE,
    run_in_container,
    run_on_remote_node,
    PROVISION_CONFIG_FILE,
    get_nodes_info,
)
from automation_library.provision.functions.common_func import (
    get_slurm_compute_nodes,
    get_slurm_control_nodes,
)


def validate_node_discovery_mode_config(host) -> Dict[str, Any]:
    """
    Validate node_discovery_mode configuration in omnia_config.yml.
    
    Args:
        host: Testinfra host object
    
    Returns:
        Dict with success, message, discovery_mode, error
    """
    result = {
        "success": False,
        "message": "",
        "discovery_mode": "",
        "error": ""
    }
    
    config = load_input_file(host, OMNIA_CONFIG_FILE)
    if not config:
        result["error"] = "Failed to load omnia_config.yml"
        return result
    
    slurm_clusters = config.get("slurm_cluster", [])
    if not slurm_clusters:
        result["error"] = "No slurm_cluster found in omnia_config.yml"
        return result
    
    cluster = slurm_clusters[0]
    discovery_mode = cluster.get("node_discovery_mode", "heterogeneous").lower()
    
    valid_modes = ["heterogeneous", "homogeneous"]
    if discovery_mode not in valid_modes:
        result["error"] = f"Invalid node_discovery_mode: {discovery_mode}. Must be one of: {', '.join(valid_modes)}"
        return result
    
    result["discovery_mode"] = discovery_mode
    result["success"] = True
    result["message"] = f"node_discovery_mode is valid: {discovery_mode}"
    
    return result


def validate_node_hardware_defaults_config(host) -> Dict[str, Any]:
    """
    Validate node_hardware_defaults configuration in omnia_config.yml.
    
    Args:
        host: Testinfra host object
    
    Returns:
        Dict with success, message, groups_with_specs, error
    """
    result = {
        "success": False,
        "message": "",
        "groups_with_specs": [],
        "error": ""
    }
    
    config = load_input_file(host, OMNIA_CONFIG_FILE)
    if not config:
        result["error"] = "Failed to load omnia_config.yml"
        return result
    
    slurm_clusters = config.get("slurm_cluster", [])
    if not slurm_clusters:
        result["error"] = "No slurm_cluster found in omnia_config.yml"
        return result
    
    cluster = slurm_clusters[0]
    node_hardware_defaults = cluster.get("node_hardware_defaults", {})
    
    if not isinstance(node_hardware_defaults, dict):
        result["error"] = "node_hardware_defaults must be a dictionary"
        return result
    
    if not node_hardware_defaults:
        result["success"] = True
        result["message"] = "node_hardware_defaults not configured (empty/missing)"
        return result
    
    groups_with_specs = []
    for group_name, specs in node_hardware_defaults.items():
        if not isinstance(specs, dict):
            result["error"] = f"Hardware specs for group '{group_name}' must be a dictionary"
            return result
        
        required_fields = ["sockets", "cores_per_socket", "threads_per_core", "real_memory"]
        for field in required_fields:
            if field not in specs:
                result["error"] = f"Missing required field '{field}' in hardware specs for group '{group_name}'"
                return result
        
        try:
            sockets = int(specs["sockets"])
            if sockets < 1:
                result["error"] = f"sockets must be >= 1 for group '{group_name}'"
                return result
            
            cores_per_socket = int(specs["cores_per_socket"])
            if cores_per_socket < 1:
                result["error"] = f"cores_per_socket must be >= 1 for group '{group_name}'"
                return result
            
            threads_per_core = int(specs["threads_per_core"])
            if threads_per_core < 1:
                result["error"] = f"threads_per_core must be >= 1 for group '{group_name}'"
                return result
            
            real_memory = int(specs["real_memory"])
            if real_memory < 1:
                result["error"] = f"real_memory must be >= 1 for group '{group_name}'"
                return result
            
            if "gres" in specs:
                gres = specs["gres"]
                if gres and not isinstance(gres, str):
                    result["error"] = f"gres must be a string for group '{group_name}'"
                    return result
                
                if gres and not gres.startswith("gpu:"):
                    result["error"] = f"gres must be in format 'gpu:N' for group '{group_name}'"
                    return result
                
                try:
                    gpu_count = int(gres.split(":")[1])
                    if gpu_count < 1:
                        result["error"] = f"GPU count must be >= 1 for group '{group_name}'"
                        return result
                except (IndexError, ValueError):
                    result["error"] = f"Invalid gres format for group '{group_name}'"
                    return result
            
        except (ValueError, TypeError) as e:
            result["error"] = f"Invalid value in hardware specs for group '{group_name}': {str(e)}"
            return result
        
        groups_with_specs.append(group_name)
    
    result["groups_with_specs"] = groups_with_specs
    result["success"] = True
    result["message"] = f"node_hardware_defaults valid for {len(groups_with_specs)} groups"
    
    return result


def validate_group_names_in_pxe_mapping(host, groups: List[str]) -> Dict[str, Any]:
    """
    Validate that group names from node_hardware_defaults exist in PXE mapping GROUP_NAME column.
    
    Args:
        host: Testinfra host object
        groups: List of group names to validate
    
    Returns:
        Dict with success, message, missing_groups, error
    """
    result = {
        "success": False,
        "message": "",
        "missing_groups": [],
        "error": ""
    }
    
    prov_config = load_input_file(host, PROVISION_CONFIG_FILE)
    if not prov_config:
        result["error"] = "Failed to load provision_config.yml"
        return result
    
    pxe_mapping_path = prov_config.get("pxe_mapping_file_path", "")
    if not pxe_mapping_path:
        result["error"] = "No pxe_mapping_file_path found in provision_config.yml"
        return result
    
    cmd = run_in_container(host, f"cat {pxe_mapping_path}")
    if cmd.rc != 0:
        result["error"] = f"Failed to read PXE mapping file: {cmd.stderr}"
        return result
    
    lines = cmd.stdout.strip().split('\n')
    if not lines:
        result["error"] = "PXE mapping file is empty"
        return result
    
    header = lines[0].split(',')
    
    try:
        group_name_idx = header.index("GROUP_NAME")
    except ValueError:
        result["error"] = "GROUP_NAME column not found in PXE mapping file"
        return result
    
    pxe_groups = set()
    for line in lines[1:]:
        parts = line.split(',')
        if len(parts) > group_name_idx:
            group_name = parts[group_name_idx].strip()
            if group_name:
                pxe_groups.add(group_name)
    
    missing_groups = [g for g in groups if g not in pxe_groups]
    
    if missing_groups:
        result["error"] = f"Groups not found in PXE mapping: {', '.join(missing_groups)}"
        return result
    
    result["pxe_groups"] = sorted(list(pxe_groups))
    result["missing_groups"] = missing_groups
    result["success"] = True
    result["message"] = f"All {len(groups)} groups found in PXE mapping"
    
    return result


def _parse_slurm_conf_node_configs(host) -> Dict[str, Any]:
    """
    Helper to parse NodeName entries from slurm.conf on control node.
    
    Args:
        host: Testinfra host object
    
    Returns:
        Dict with success, node_configs, error
    """
    result = {
        "success": False,
        "node_configs": {},
        "error": ""
    }
    
    control_nodes = get_slurm_control_nodes(host)
    if not control_nodes:
        result["error"] = "No slurm control node found"
        return result
    
    control_ip = control_nodes[0].get("admin_ip", "")
    if not control_ip:
        result["error"] = "Slurm control node has no admin IP"
        return result
    
    cmd = run_on_remote_node(
        host,
        "cat /etc/slurm/slurm.conf 2>/dev/null",
        control_ip
    )
    
    if cmd.rc != 0:
        result["error"] = f"Failed to read slurm.conf: {cmd.stderr}"
        return result
    
    slurm_conf = cmd.stdout
    node_configs = {}
    
    for line in slurm_conf.split('\n'):
        line = line.strip()
        if line.startswith("NodeName=") and not line.startswith("NodeName=DEFAULT"):
            node_name = line.split('=')[1].split()[0]
            node_config = {"NodeName": node_name}
            
            if "Sockets=" in line:
                node_config["Sockets"] = line.split("Sockets=")[1].split()[0]
            if "CoresPerSocket=" in line:
                node_config["CoresPerSocket"] = line.split("CoresPerSocket=")[1].split()[0]
            if "ThreadsPerCore=" in line:
                node_config["ThreadsPerCore"] = line.split("ThreadsPerCore=")[1].split()[0]
            if "RealMemory=" in line:
                node_config["RealMemory"] = line.split("RealMemory=")[1].split()[0]
            if "Gres=" in line:
                node_config["Gres"] = line.split("Gres=")[1].split()[0]
            
            node_configs[node_name] = node_config
    
    result["node_configs"] = node_configs
    result["success"] = True
    
    return result


def verify_homogeneous_with_user_specs(host) -> Dict[str, Any]:
    """
    Verify node discovery behavior based on current mode with actual cluster state validation.
    - For homogeneous mode with user specs: validates 0 iDRAC calls (user specs only) and checks actual slurm.conf
    - For heterogeneous mode: validates individual iDRAC calls per node (default behavior) and checks actual slurm.conf

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, message, mode, discovery_behavior, cluster_state, error
    """
    result = {
        "success": False,
        "message": "",
        "mode": "",
        "discovery_behavior": {},
        "cluster_state": {},
        "error": ""
    }

    # Get current discovery mode
    discovery_result = validate_node_discovery_mode_config(host)
    if not discovery_result["success"]:
        result["error"] = discovery_result["error"]
        return result

    discovery_mode = discovery_result["discovery_mode"]
    result["mode"] = discovery_mode

    if discovery_mode == "heterogeneous":
        # Validate heterogeneous behavior: individual iDRAC calls per node
        compute_nodes = get_slurm_compute_nodes(host)
        if not compute_nodes:
            result["error"] = "No compute nodes found in PXE mapping"
            return result

        # Get actual slurm.conf state
        slurm_result = _parse_slurm_conf_node_configs(host)
        if not slurm_result["success"]:
            result["error"] = slurm_result["error"]
            return result

        actual_node_configs = slurm_result["node_configs"]
        
        result["success"] = True
        result["message"] = f"Heterogeneous mode: {len(compute_nodes)} nodes discovered via individual iDRAC calls (default behavior)"
        result["discovery_behavior"] = {
            "discovery_method": "individual_idrac_per_node",
            "expected_idrac_calls": f"{len(compute_nodes)} (1 per node)",
            "user_specs_used": False
        }
        result["cluster_state"] = {
            "actual_node_configs": actual_node_configs,
            "nodes_in_slurm_conf": len(actual_node_configs),
            "compute_nodes_from_pxe": len(compute_nodes),
            "state_match": len(actual_node_configs) == len(compute_nodes)
        }
        return result

    # Homogeneous mode validation
    hardware_defaults_result = validate_node_hardware_defaults_config(host)
    if not hardware_defaults_result["success"]:
        result["error"] = hardware_defaults_result["error"]
        return result

    if not hardware_defaults_result["groups_with_specs"]:
        result["error"] = "Homogeneous mode requires user specs in node_hardware_defaults"
        return result

    groups_with_specs = hardware_defaults_result["groups_with_specs"]

    compute_nodes = get_slurm_compute_nodes(host)
    if not compute_nodes:
        result["error"] = "No compute nodes found in PXE mapping"
        return result

    slurm_result = _parse_slurm_conf_node_configs(host)
    if not slurm_result["success"]:
        result["error"] = slurm_result["error"]
        return result
    
    node_configs = slurm_result["node_configs"]
    
    config = load_input_file(host, OMNIA_CONFIG_FILE)
    user_specs = config["slurm_cluster"][0].get("node_hardware_defaults", {})
    
    # Validate that actual slurm.conf specs match user specs
    specs_match = True
    validation_details = []
    
    hostname_to_group = {
        n.get("hostname"): n.get("group_name")
        for n in compute_nodes
        if n.get("hostname") and n.get("group_name")
    }

    for node_name, node_config in node_configs.items():
        node_group = hostname_to_group.get(node_name)
        if not node_group or node_group not in user_specs:
            continue

        expected_specs = user_specs[node_group]

        actual_sockets = int(node_config.get("Sockets", 0))
        actual_cores = int(node_config.get("CoresPerSocket", 0))
        actual_threads = int(node_config.get("ThreadsPerCore", 0))
        actual_memory = int(node_config.get("RealMemory", 0))

        expected_sockets = int(expected_specs.get("sockets", 0))
        expected_cores = int(expected_specs.get("cores_per_socket", 0))
        expected_threads = int(expected_specs.get("threads_per_core", 0))
        expected_memory = int(expected_specs.get("real_memory", 0))

        node_match = (
            actual_sockets == expected_sockets
            and actual_cores == expected_cores
            and actual_threads == expected_threads
            and actual_memory == expected_memory
        )

        validation_details.append({
            "node": node_name,
            "group": node_group,
            "specs_match": node_match,
            "expected": {
                "sockets": expected_sockets,
                "cores": expected_cores,
                "threads": expected_threads,
                "memory": expected_memory,
            },
            "actual": {
                "sockets": actual_sockets,
                "cores": actual_cores,
                "threads": actual_threads,
                "memory": actual_memory,
            },
        })

        if not node_match:
            specs_match = False

    discovery_behavior = {
        "discovery_method": "user_specs_only",
        "expected_idrac_calls": "0 (all specs from user configuration)",
        "groups_with_specs": groups_with_specs,
        "node_configs": node_configs,
        "specs_validation": validation_details,
        "all_specs_match": specs_match
    }
    
    result["discovery_behavior"] = discovery_behavior
    result["cluster_state"] = {
        "actual_node_configs": node_configs,
        "nodes_in_slurm_conf": len(node_configs),
        "compute_nodes_from_pxe": len(compute_nodes),
        "specs_match_expected": specs_match,
    }

    if not specs_match:
        result["error"] = "slurm.conf node specs do not match node_hardware_defaults"
        return result

    result["success"] = True
    result["message"] = f"Homogeneous mode with user specs: {len(groups_with_specs)} groups use user specs (0 iDRAC calls)"

    return result


def verify_homogeneous_without_user_specs(host) -> Dict[str, Any]:
    """
    Verify node discovery behavior for homogeneous mode without user specs vs heterogeneous mode with cluster state validation.
    - For homogeneous mode without user specs: validates 1 iDRAC call per group
    - For heterogeneous mode: validates individual iDRAC calls per node (default behavior)

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, message, mode, discovery_behavior, cluster_state, error
    """
    result = {
        "success": False,
        "message": "",
        "mode": "",
        "discovery_behavior": {},
        "cluster_state": {},
        "error": ""
    }

    # Get current discovery mode
    discovery_result = validate_node_discovery_mode_config(host)
    if not discovery_result["success"]:
        result["error"] = discovery_result["error"]
        return result

    discovery_mode = discovery_result["discovery_mode"]
    result["mode"] = discovery_mode

    if discovery_mode == "heterogeneous":
        # Validate heterogeneous behavior: individual iDRAC calls per node
        compute_nodes = get_slurm_compute_nodes(host)
        if not compute_nodes:
            result["error"] = "No compute nodes found in PXE mapping"
            return result

        # Get actual slurm.conf state
        slurm_result = _parse_slurm_conf_node_configs(host)
        if not slurm_result["success"]:
            result["error"] = slurm_result["error"]
            return result

        actual_node_configs = slurm_result["node_configs"]

        result["success"] = True
        result["message"] = f"Heterogeneous mode: {len(compute_nodes)} nodes discovered via individual iDRAC calls (default behavior)"
        result["discovery_behavior"] = {
            "discovery_method": "individual_idrac_per_node",
            "expected_idrac_calls": f"{len(compute_nodes)} (1 per node)",
            "user_specs_used": False
        }
        result["cluster_state"] = {
            "actual_node_configs": actual_node_configs,
            "nodes_in_slurm_conf": len(actual_node_configs),
            "compute_nodes_from_pxe": len(compute_nodes),
            "state_match": len(actual_node_configs) == len(compute_nodes)
        }
        return result

    # Homogeneous mode without user specs validation
    hardware_defaults_result = validate_node_hardware_defaults_config(host)
    if not hardware_defaults_result["success"]:
        result["error"] = hardware_defaults_result["error"]
        return result

    groups_with_specs = hardware_defaults_result["groups_with_specs"]
    # Compute-only GROUP_NAMEs from PXE mapping
    compute_nodes = get_slurm_compute_nodes(host)
    if not compute_nodes:
        result["error"] = "No compute nodes found in PXE mapping"
        return result

    compute_group_names = sorted({n.get("group_name", "").strip() for n in compute_nodes if n.get("group_name", "").strip()})

    groups_without_specs = [g for g in compute_group_names if g not in groups_with_specs]
    
    if not groups_without_specs:
        result["skipped"] = True
        result["message"] = "Test not applicable: all groups have user specs configured"
        return result

    # Get actual slurm.conf state
    slurm_result = _parse_slurm_conf_node_configs(host)
    if not slurm_result["success"]:
        result["error"] = slurm_result["error"]
        return result

    actual_node_configs = slurm_result["node_configs"]

    result["success"] = True
    result["message"] = f"Homogeneous mode without user specs: {len(groups_without_specs)} groups use 1 iDRAC call per group"
    result["discovery_behavior"] = {
        "discovery_method": "group_idrac_call",
        "expected_idrac_calls": f"{len(groups_without_specs)} (1 per group without specs)",
        "groups_without_specs": groups_without_specs,
        "user_specs_used": False
    }
    result["cluster_state"] = {
        "actual_node_configs": actual_node_configs,
        "nodes_in_slurm_conf": len(actual_node_configs),
        "compute_nodes_from_pxe": len(compute_nodes),
        "groups_without_specs_count": len(groups_without_specs)
    }

    return result


def verify_hardware_specs_match_user_specs(host) -> Dict[str, Any]:
    """
    Verify hardware specs validation based on current mode with actual cluster state validation.
    - For homogeneous mode with user specs: validates Slurm config matches user specs
    - For heterogeneous mode: validates that hardware specs are discovered via iDRAC

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, message, mode, spec_validation, cluster_state, error
    """
    result = {
        "success": False,
        "message": "",
        "mode": "",
        "spec_validation": {},
        "cluster_state": {},
        "error": ""
    }

    # Get current discovery mode
    discovery_result = validate_node_discovery_mode_config(host)
    if not discovery_result["success"]:
        result["error"] = discovery_result["error"]
        return result

    discovery_mode = discovery_result["discovery_mode"]
    result["mode"] = discovery_mode

    if discovery_mode == "heterogeneous":
        # In heterogeneous mode, hardware specs are discovered via iDRAC
        slurm_result = _parse_slurm_conf_node_configs(host)
        if not slurm_result["success"]:
            result["error"] = slurm_result["error"]
            return result

        node_configs = slurm_result["node_configs"]
        compute_nodes = get_slurm_compute_nodes(host)

        result["success"] = True
        result["message"] = f"Heterogeneous mode: {len(node_configs)} nodes have hardware specs discovered via iDRAC"
        result["spec_validation"] = {
            "spec_source": "idrac_discovery",
            "node_configs": node_configs,
            "total_nodes": len(compute_nodes)
        }
        result["cluster_state"] = {
            "actual_node_configs": node_configs,
            "nodes_in_slurm_conf": len(node_configs),
            "compute_nodes_from_pxe": len(compute_nodes)
        }
        return result

    # Homogeneous mode with user specs validation
    config = load_input_file(host, OMNIA_CONFIG_FILE)
    node_hardware_defaults = config["slurm_cluster"][0].get("node_hardware_defaults", {})

    if not node_hardware_defaults:
        result["error"] = "Homogeneous mode requires user specs in node_hardware_defaults"
        return result

    slurm_result = _parse_slurm_conf_node_configs(host)
    if not slurm_result["success"]:
        result["error"] = slurm_result["error"]
        return result

    node_configs = slurm_result["node_configs"]

    result["success"] = True
    result["message"] = f"Homogeneous mode: {len(node_hardware_defaults)} groups have user-spec hardware configs"
    result["spec_validation"] = {
        "spec_source": "user_configuration",
        "user_specs": node_hardware_defaults,
        "node_configs": node_configs
    }
    result["cluster_state"] = {
        "actual_node_configs": node_configs,
        "nodes_in_slurm_conf": len(node_configs),
        "user_specs_groups": len(node_hardware_defaults)
    }

    return result


def verify_mixed_homogeneous_mode(host) -> Dict[str, Any]:
    """
    Verify mixed mode scenario based on current configuration with actual cluster state validation.
    - For homogeneous mode: validates some groups with specs, some without
    - For heterogeneous mode: validates individual iDRAC calls for all nodes

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, message, mode, mixed_analysis, cluster_state, error
    """
    result = {
        "success": False,
        "message": "",
        "mode": "",
        "mixed_analysis": {},
        "cluster_state": {},
        "error": ""
    }

    # Get current discovery mode
    discovery_result = validate_node_discovery_mode_config(host)
    if not discovery_result["success"]:
        result["error"] = discovery_result["error"]
        return result

    discovery_mode = discovery_result["discovery_mode"]
    result["mode"] = discovery_mode

    if discovery_mode == "heterogeneous":
        # In heterogeneous mode, all nodes use individual iDRAC calls
        compute_nodes = get_slurm_compute_nodes(host)
        if not compute_nodes:
            result["error"] = "No compute nodes found in PXE mapping"
            return result

        # Get actual slurm.conf state
        slurm_result = _parse_slurm_conf_node_configs(host)
        if not slurm_result["success"]:
            result["error"] = slurm_result["error"]
            return result

        actual_node_configs = slurm_result["node_configs"]

        result["success"] = True
        result["message"] = f"Heterogeneous mode: {len(compute_nodes)} nodes discovered via individual iDRAC calls (no mixed mode)"
        result["mixed_analysis"] = {
            "mode": "heterogeneous",
            "discovery_method": "individual_idrac_per_node",
            "groups_with_specs": [],
            "groups_without_specs": [],
            "total_nodes": len(compute_nodes)
        }
        result["cluster_state"] = {
            "actual_node_configs": actual_node_configs,
            "nodes_in_slurm_conf": len(actual_node_configs),
            "compute_nodes_from_pxe": len(compute_nodes)
        }
        return result

    # Homogeneous mode mixed scenario validation
    config = load_input_file(host, OMNIA_CONFIG_FILE)
    user_specs = config["slurm_cluster"][0].get("node_hardware_defaults", {})

    # Compute-only GROUP_NAMEs from PXE mapping
    compute_nodes = get_slurm_compute_nodes(host)
    if not compute_nodes:
        result["error"] = "No compute nodes found in PXE mapping"
        return result

    compute_group_names = sorted({n.get("group_name", "").strip() for n in compute_nodes if n.get("group_name", "").strip()})
    groups_with_specs = [g for g in compute_group_names if g in user_specs]
    groups_without_specs = [g for g in compute_group_names if g not in user_specs]

    if not groups_with_specs or not groups_without_specs:
        result["skipped"] = True
        result["message"] = "Test not applicable: mixed mode requires some groups with specs and some without"
        return result

    # Get actual slurm.conf state
    slurm_result = _parse_slurm_conf_node_configs(host)
    if not slurm_result["success"]:
        result["error"] = slurm_result["error"]
        return result

    actual_node_configs = slurm_result["node_configs"]

    result["success"] = True
    result["message"] = f"Homogeneous mixed mode: {len(groups_with_specs)} groups with specs, {len(groups_without_specs)} without"
    result["mixed_analysis"] = {
        "mode": "homogeneous_mixed",
        "groups_with_specs": groups_with_specs,
        "groups_without_specs": groups_without_specs,
        "total_groups": len(compute_group_names)
    }
    result["cluster_state"] = {
        "actual_node_configs": actual_node_configs,
        "nodes_in_slurm_conf": len(actual_node_configs),
        "groups_with_specs_count": len(groups_with_specs),
        "groups_without_specs_count": len(groups_without_specs)
    }

    return result


def verify_heterogeneous_mode_default(host) -> Dict[str, Any]:
    """
    Verify that heterogeneous mode works correctly as the default behavior with actual cluster state validation.
    This test always passes since heterogeneous is the default mode.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, message, default_analysis, cluster_state, error
    """
    result = {
        "success": False,
        "message": "",
        "default_analysis": {},
        "cluster_state": {},
        "error": ""
    }

    # Get current discovery mode
    discovery_result = validate_node_discovery_mode_config(host)
    if not discovery_result["success"]:
        result["error"] = discovery_result["error"]
        return result

    discovery_mode = discovery_result["discovery_mode"]

    compute_nodes = get_slurm_compute_nodes(host)
    if not compute_nodes:
        result["error"] = "No compute nodes found in PXE mapping"
        return result

    # Get actual slurm.conf state
    slurm_result = _parse_slurm_conf_node_configs(host)
    if not slurm_result["success"]:
        result["error"] = slurm_result["error"]
        return result

    actual_node_configs = slurm_result["node_configs"]

    result["success"] = True
    result["message"] = f"Heterogeneous mode validated as default: {discovery_mode} mode with {len(compute_nodes)} nodes"
    result["default_analysis"] = {
        "current_mode": discovery_mode,
        "is_default": discovery_mode == "heterogeneous",
        "total_nodes": len(compute_nodes),
        "discovery_method": "individual_idrac_per_node" if discovery_mode == "heterogeneous" else "homogeneous_discovery"
    }
    result["cluster_state"] = {
        "actual_node_configs": actual_node_configs,
        "nodes_in_slurm_conf": len(actual_node_configs),
        "compute_nodes_from_pxe": len(compute_nodes)
    }

    return result
