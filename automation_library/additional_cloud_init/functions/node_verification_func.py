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
Additional Cloud-Init Module - Node Verification Functions.

Functions for verifying cloud-init files and command execution on provisioned nodes.
"""

from typing import Dict, Any, List

from automation_library.core import (
    run_on_remote_node,
    check_nodes_reachability,
)
from ..vars.common_vars import (
    ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
    ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL,
)


def verify_cloud_init_files_on_nodes(host, nodes: List[Dict[str, Any]], expected_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verify that write_files directive created files with correct content on nodes.

    Args:
        host: Testinfra host object
        nodes: List of node dicts with hostname and admin_ip
        expected_files: List of expected file dicts with path, content, permissions

    Returns:
        Dict with success, error, and per-node results
    """
    if not nodes:
        return {
            "success": True,
            "error": "",
            "node_results": [],
            "verified_files": 0,
            "details": "No nodes provided for file verification"
        }
    
    if not expected_files:
        return {
            "success": True,
            "error": "",
            "node_results": [],
            "verified_files": 0,
            "details": "No files expected to verify"
        }
    
    try:
        # Check node reachability first
        reachability = check_nodes_reachability(
            host, nodes,
            retry_limit=ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
            retry_interval=ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL
        )
        
        reachable_nodes = reachability["reachable"]
        unreachable_nodes = reachability["unreachable"]
        
        node_results = []
        overall_success = True
        
        # Verify files on reachable nodes
        for node in reachable_nodes:
            node_result = _verify_files_on_single_node(host, node, expected_files)
            node_results.append(node_result)
            if not node_result["success"]:
                overall_success = False
        
        # Add unreachable node results
        for node in unreachable_nodes:
            node_results.append({
                "hostname": node.get("hostname", "unknown"),
                "admin_ip": node.get("admin_ip", "unknown"),
                "success": False,
                "error": "Node unreachable",
                "file_results": []
            })
            overall_success = False
        
        error_messages = []
        if unreachable_nodes:
            error_messages.append(f"{len(unreachable_nodes)} nodes unreachable")
        
        failed_nodes = [r for r in node_results if not r["success"]]
        if failed_nodes:
            error_messages.append(f"{len(failed_nodes)} nodes failed file verification")
        
        return {
            "success": overall_success,
            "error": "; ".join(error_messages),
            "node_results": node_results,
            "verified_files": len(expected_files),
            "reachable_count": len(reachable_nodes),
            "unreachable_count": len(unreachable_nodes),
            "details": f"Verified {len(expected_files)} files on {len(reachable_nodes)}/{len(nodes)} nodes"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception during file verification: {str(e)}",
            "node_results": [],
            "verified_files": 0,
            "details": str(e)
        }


def _verify_files_on_single_node(host, node: Dict[str, Any], expected_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify files on a single node."""
    hostname = node.get("hostname", "unknown")
    admin_ip = node.get("admin_ip", "unknown")
    
    file_results = []
    node_success = True
    
    for file_spec in expected_files:
        file_path = file_spec.get("path")
        expected_content = file_spec.get("content", "")
        expected_permissions = file_spec.get("permissions", "0644")
        
        if not file_path:
            file_results.append({
                "path": "unknown",
                "success": False,
                "error": "No path specified in file spec"
            })
            node_success = False
            continue
        
        # Check if file exists
        check_cmd = f"test -f {file_path}"
        check_result = run_on_remote_node(host, check_cmd, admin_ip)
        
        if check_result.rc != 0:
            file_results.append({
                "path": file_path,
                "success": False,
                "error": f"File {file_path} does not exist"
            })
            node_success = False
            continue
        
        # Check file content if specified
        content_success = True
        content_error = ""
        
        if expected_content:
            cat_cmd = f"cat {file_path}"
            cat_result = run_on_remote_node(host, cat_cmd, admin_ip)
            
            if cat_result.rc != 0:
                content_success = False
                content_error = f"Could not read file content: {cat_result.stderr}"
            else:
                actual_content = cat_result.stdout.strip()
                expected_content_clean = expected_content.strip()
                
                if actual_content != expected_content_clean:
                    content_success = False
                    content_error = f"Content mismatch. Expected length: {len(expected_content_clean)}, Actual length: {len(actual_content)}"
        
        # Check file permissions if specified
        perm_success = True
        perm_error = ""
        
        if expected_permissions:
            stat_cmd = f"stat -c '%a' {file_path}"
            stat_result = run_on_remote_node(host, stat_cmd, admin_ip)
            
            if stat_result.rc != 0:
                perm_success = False
                perm_error = f"Could not check permissions: {stat_result.stderr}"
            else:
                actual_permissions = stat_result.stdout.strip()
                # Normalize: strip leading zeros for comparison
                # stat returns '644', config may specify '0644'
                actual_norm = actual_permissions.lstrip("0") or "0"
                expected_norm = expected_permissions.lstrip("0") or "0"
                if actual_norm != expected_norm:
                    perm_success = False
                    perm_error = f"Permission mismatch. Expected: {expected_permissions}, Actual: {actual_permissions}"
        
        file_success = content_success and perm_success
        file_error = "; ".join(filter(None, [content_error, perm_error]))
        
        file_results.append({
            "path": file_path,
            "success": file_success,
            "error": file_error,
            "content_verified": bool(expected_content),
            "permissions_verified": bool(expected_permissions)
        })
        
        if not file_success:
            node_success = False
    
    return {
        "hostname": hostname,
        "admin_ip": admin_ip,
        "success": node_success,
        "error": f"Failed files: {[f['path'] for f in file_results if not f['success']]}" if not node_success else "",
        "file_results": file_results
    }


def verify_runcmd_execution_on_nodes(host, nodes: List[Dict[str, Any]], expected_commands: List[str]) -> Dict[str, Any]:
    """
    Verify that runcmd directive executed commands on nodes.

    Args:
        host: Testinfra host object
        nodes: List of node dicts with hostname and admin_ip
        expected_commands: List of commands that should have been executed

    Returns:
        Dict with success, error, and per-node results
    """
    if not nodes:
        return {
            "success": True,
            "error": "",
            "node_results": [],
            "verified_commands": 0,
            "details": "No nodes provided for command verification"
        }
    
    if not expected_commands:
        return {
            "success": True,
            "error": "",
            "node_results": [],
            "verified_commands": 0,
            "details": "No commands expected to verify"
        }
    
    try:
        # Check node reachability first
        reachability = check_nodes_reachability(
            host, nodes,
            retry_limit=ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
            retry_interval=ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL
        )
        
        reachable_nodes = reachability["reachable"]
        unreachable_nodes = reachability["unreachable"]
        
        node_results = []
        overall_success = True
        
        # Verify commands on reachable nodes
        for node in reachable_nodes:
            node_result = _verify_commands_on_single_node(host, node, expected_commands)
            node_results.append(node_result)
            if not node_result["success"]:
                overall_success = False
        
        # Add unreachable node results
        for node in unreachable_nodes:
            node_results.append({
                "hostname": node.get("hostname", "unknown"),
                "admin_ip": node.get("admin_ip", "unknown"),
                "success": False,
                "error": "Node unreachable",
                "command_results": []
            })
            overall_success = False
        
        error_messages = []
        if unreachable_nodes:
            error_messages.append(f"{len(unreachable_nodes)} nodes unreachable")
        
        failed_nodes = [r for r in node_results if not r["success"]]
        if failed_nodes:
            error_messages.append(f"{len(failed_nodes)} nodes failed command verification")
        
        return {
            "success": overall_success,
            "error": "; ".join(error_messages),
            "node_results": node_results,
            "verified_commands": len(expected_commands),
            "reachable_count": len(reachable_nodes),
            "unreachable_count": len(unreachable_nodes),
            "details": f"Verified {len(expected_commands)} commands on {len(reachable_nodes)}/{len(nodes)} nodes"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception during command verification: {str(e)}",
            "node_results": [],
            "verified_commands": 0,
            "details": str(e)
        }


def _verify_commands_on_single_node(host, node: Dict[str, Any], expected_commands: List[str]) -> Dict[str, Any]:
    """Verify commands were executed on a single node by checking for evidence."""
    hostname = node.get("hostname", "unknown")
    admin_ip = node.get("admin_ip", "unknown")
    
    command_results = []
    node_success = True
    
    # For runcmd verification, we look for evidence in log files or created files
    # This is based on the example additional_cloud_init.yml commands
    
    for cmd in expected_commands:
        cmd_success = True
        cmd_error = ""
        
        # Check for specific evidence based on command patterns
        if ">> /var/log/" in cmd:
            # Command writes to log file - check if log entry exists
            log_file_match = cmd.split(">> ")[1].strip() if ">> " in cmd else None
            if log_file_match:
                check_cmd = f"test -f {log_file_match}"
                result = run_on_remote_node(host, check_cmd, admin_ip)
                
                if result.rc != 0:
                    cmd_success = False
                    cmd_error = f"Log file {log_file_match} not found"
                else:
                    # Check if file has content (command was executed)
                    size_cmd = f"stat -c '%s' {log_file_match}"
                    size_result = run_on_remote_node(host, size_cmd, admin_ip)
                    
                    if size_result.rc == 0 and size_result.stdout.strip() == "0":
                        cmd_success = False
                        cmd_error = f"Log file {log_file_match} is empty"
        
        elif "echo" in cmd and "successful" in cmd:
            # Success marker command - check for evidence in common log locations
            check_locations = ["/var/log/custom_setup.log", "/var/log/cloud-init-output.log"]
            found_evidence = False
            
            for log_location in check_locations:
                check_cmd = f"test -f {log_location} && grep -q 'successful' {log_location}"
                result = run_on_remote_node(host, check_cmd, admin_ip)
                
                if result.rc == 0:
                    found_evidence = True
                    break
            
            if not found_evidence:
                cmd_success = False
                cmd_error = "No evidence of successful execution found in logs"
        
        else:
            # Generic command - just check that cloud-init completed
            check_cmd = "cloud-init status"
            result = run_on_remote_node(host, check_cmd, admin_ip)
            
            if result.rc != 0:
                cmd_success = False
                cmd_error = "cloud-init status check failed"
            elif "done" not in result.stdout:
                cmd_success = False
                cmd_error = "cloud-init not completed"
        
        command_results.append({
            "command": cmd,
            "success": cmd_success,
            "error": cmd_error
        })
        
        if not cmd_success:
            node_success = False
    
    return {
        "hostname": hostname,
        "admin_ip": admin_ip,
        "success": node_success,
        "error": f"Failed commands: {[c['command'] for c in command_results if not c['success']]}" if not node_success else "",
        "command_results": command_results
    }


def verify_additional_cloud_init_integration(host, config: Dict[str, Any], nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Comprehensive integration test for additional cloud-init functionality.

    Verifies per-scope: common entries on all nodes, per-FG entries on FG nodes only.

    Args:
        host: Testinfra host object
        config: Additional cloud-init configuration
        nodes: List of nodes to verify (each node dict must have 'functional_group' key)

    Returns:
        Dict with success, error, and integration test results
    """
    try:
        integration_results = []
        overall_success = True
        
        # Group nodes by functional group for per-FG scoping
        nodes_by_fg = {}
        for node in nodes:
            fg = node.get("functional_group", "unknown")
            if fg not in nodes_by_fg:
                nodes_by_fg[fg] = []
            nodes_by_fg[fg].append(node)
        
        # Test write_files integration (per-scope)
        has_write_files = (
            config.get("common", {}).get("write_files") or
            any(fg_config.get("write_files") for fg_config in config.get("groups", {}).values())
        )
        
        if has_write_files:
            files_success = True
            files_errors = []
            
            # Common write_files → all nodes
            common_files = config.get("common", {}).get("write_files", [])
            if common_files:
                result = verify_cloud_init_files_on_nodes(host, nodes, common_files)
                if not result["success"]:
                    files_success = False
                    files_errors.append(f"common: {result['error']}")
            
            # Per-FG write_files → FG nodes only
            for fg_name, fg_config in config.get("groups", {}).items():
                fg_files = fg_config.get("write_files", [])
                if fg_files:
                    fg_nodes = nodes_by_fg.get(fg_name, [])
                    if fg_nodes:
                        result = verify_cloud_init_files_on_nodes(host, fg_nodes, fg_files)
                        if not result["success"]:
                            files_success = False
                            files_errors.append(f"{fg_name}: {result['error']}")
            
            integration_results.append({
                "test": "write_files_integration",
                "success": files_success,
                "error": "; ".join(files_errors),
                "details": "write_files verified per-scope"
            })
            if not files_success:
                overall_success = False
        
        # Test runcmd integration (per-scope)
        has_runcmd = (
            config.get("common", {}).get("runcmd") or
            any(fg_config.get("runcmd") for fg_config in config.get("groups", {}).values())
        )
        
        if has_runcmd:
            cmds_success = True
            cmds_errors = []
            
            # Common runcmd → all nodes
            common_cmds = config.get("common", {}).get("runcmd", [])
            if common_cmds:
                result = verify_runcmd_execution_on_nodes(host, nodes, common_cmds)
                if not result["success"]:
                    cmds_success = False
                    cmds_errors.append(f"common: {result['error']}")
            
            # Per-FG runcmd → FG nodes only
            for fg_name, fg_config in config.get("groups", {}).items():
                fg_cmds = fg_config.get("runcmd", [])
                if fg_cmds:
                    fg_nodes = nodes_by_fg.get(fg_name, [])
                    if fg_nodes:
                        result = verify_runcmd_execution_on_nodes(host, fg_nodes, fg_cmds)
                        if not result["success"]:
                            cmds_success = False
                            cmds_errors.append(f"{fg_name}: {result['error']}")
            
            integration_results.append({
                "test": "runcmd_integration",
                "success": cmds_success,
                "error": "; ".join(cmds_errors),
                "details": "runcmd verified per-scope"
            })
            if not cmds_success:
                overall_success = False
        
        return {
            "success": overall_success,
            "error": "; ".join([r["error"] for r in integration_results if r["error"]]),
            "integration_results": integration_results,
            "tests_run": len(integration_results),
            "details": f"Integration test completed with {len(integration_results)} test(s)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception during integration test: {str(e)}",
            "integration_results": [],
            "tests_run": 0,
            "details": str(e)
        }
