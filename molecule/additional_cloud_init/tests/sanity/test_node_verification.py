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
Additional Cloud-Init Node Verification Test Cases.

Test cases for verifying cloud-init execution on nodes:
1. TC-F14: write_files file creation
2. TC-F15: runcmd command execution  
3. TC-F16: End-to-end common only
4. TC-F17: End-to-end per-FG only
5. TC-F18: End-to-end common + per-FG
6. TC-F19: End-to-end multiple FGs
7. TC-F20: End-to-end mixed directives
8. TC-F21: Integration with additional packages
"""

import pytest
from automation_library.core import (
    TestLogger,
    check_nodes_reachability,
    get_functional_groups_from_pxe_mapping,
    get_nodes_info,
)
from automation_library.additional_cloud_init.functions import (
    load_additional_cloud_init_config,
    get_functional_groups_from_config,
    skip_if_additional_cloud_init_disabled,
    verify_cloud_init_files_on_nodes,
    verify_runcmd_execution_on_nodes,
    verify_additional_cloud_init_integration,
    get_all_nodes_for_common,
    get_nodes_by_functional_group,
)
from automation_library.additional_cloud_init.vars import (
    ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
    ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL,
)
from automation_library.additional_cloud_init.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)


def _group_nodes_by_functional_group(nodes):
    """Group nodes by functional group for display."""
    groups = {}
    for node in nodes:
        fg = node.get("functional_group", "unknown")
        if fg not in groups:
            groups[fg] = []
        groups[fg].append(node)
    return groups


@pytest.mark.sanity
@pytest.mark.order(14)
def test_write_files_creation(host):
    """
    TC-F14: Verify write_files directive creates files on nodes.
    
    Tests:
    - Files created with correct paths
    - File content matches configuration
    - File permissions are correct
    """
    log = TestLogger(TEST_NAMES["write_files_creation"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    common_section = config.get("common", {})
    groups_section = config.get("groups", {})
    
    common_files = common_section.get("write_files", [])
    has_per_fg_files = any(fg.get("write_files") for fg in groups_section.values())
    
    # Skip if no write_files to test
    if not common_files and not has_per_fg_files:
        log.skipped(SKIP_MSGS["no_write_files"], "No write_files directive in configuration")
        pytest.skip("No write_files directive in configuration")
    
    overall_success = True
    scope_results = []
    total_files = 0
    
    try:
        # 1. Verify common write_files on ALL nodes
        if common_files:
            all_nodes = get_all_nodes_for_common(host)
            if all_nodes:
                log.check(f"Verifying {len(common_files)} common write_files on {len(all_nodes)} node(s)")
                common_result = verify_cloud_init_files_on_nodes(host, all_nodes, common_files)
                scope_results.append(("common", common_files, all_nodes, common_result))
                total_files += len(common_files)
                if not common_result["success"]:
                    overall_success = False
        
        # 2. Verify per-FG write_files on FG-specific nodes ONLY
        for fg_name, fg_config in groups_section.items():
            fg_files = fg_config.get("write_files", [])
            if fg_files:
                fg_nodes = get_nodes_by_functional_group(host, fg_name)
                if fg_nodes:
                    log.check(f"Verifying {len(fg_files)} {fg_name} write_files on {len(fg_nodes)} node(s)")
                    fg_result = verify_cloud_init_files_on_nodes(host, fg_nodes, fg_files)
                    scope_results.append((fg_name, fg_files, fg_nodes, fg_result))
                    total_files += len(fg_files)
                    if not fg_result["success"]:
                        overall_success = False
        
        if not scope_results:
            log.skipped("No nodes found for write_files verification", "Check PXE mapping")
            pytest.skip("No nodes found for write_files verification")
        
        # Build details
        details_lines = [
            f"write_files verification: {total_files} files verified per-scope",
            ""
        ]
        
        for scope_name, files, nodes, result in scope_results:
            status = "✓" if result["success"] else "✗"
            reachable = result.get("reachable_count", len(nodes))
            details_lines.append(f"{status} [{scope_name}]: {len(files)} file(s) on {reachable} node(s)")
            
            for file_spec in files:
                details_lines.append(f"    - {file_spec.get('path', 'unknown')}")
            
            for node_result in result.get("node_results", []):
                hostname = node_result.get("hostname", "unknown")
                node_status = "✓" if node_result.get("success") else "✗"
                details_lines.append(f"    {node_status} {hostname}")
                if not node_result.get("success") and node_result.get("error"):
                    details_lines.append(f"      Error: {node_result['error']}")
        
        details = "\n".join(details_lines)
        
        if not overall_success:
            log.failed("write_files verification failed", details)
            failed_scopes = [name for name, _, _, r in scope_results if not r["success"]]
            assert False, TEST_ASSERT_MSGS["file_verification_failed"].format(
                failed_nodes=failed_scopes,
                missing_files="Check details above",
                permission_errors="Check details above",
                content_errors="Check details above"
            )
        
        log.passed(
            TEST_LOG_MSGS["files_verified"].format(
                file_count=total_files,
                node_count=sum(r.get("reachable_count", 0) for _, _, _, r in scope_results)
            ),
            details
        )
        
    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception during write_files verification: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(15)
def test_runcmd_execution(host):
    """
    TC-F15: Verify runcmd directive executes commands on nodes.
    
    Tests:
    - Commands executed on nodes
    - Command output/logs present
    - Commands completed successfully
    """
    log = TestLogger(TEST_NAMES["runcmd_execution"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    common_section = config.get("common", {})
    groups_section = config.get("groups", {})
    
    common_cmds = common_section.get("runcmd", [])
    has_per_fg_cmds = any(fg.get("runcmd") for fg in groups_section.values())
    
    # Skip if no runcmd to test
    if not common_cmds and not has_per_fg_cmds:
        log.skipped(SKIP_MSGS["no_runcmd"], "No runcmd directive in configuration")
        pytest.skip("No runcmd directive in configuration")
    
    overall_success = True
    scope_results = []
    total_cmds = 0
    
    try:
        # 1. Verify common runcmd on ALL nodes
        if common_cmds:
            all_nodes = get_all_nodes_for_common(host)
            if all_nodes:
                log.check(f"Verifying {len(common_cmds)} common runcmd on {len(all_nodes)} node(s)")
                common_result = verify_runcmd_execution_on_nodes(host, all_nodes, common_cmds)
                scope_results.append(("common", common_cmds, all_nodes, common_result))
                total_cmds += len(common_cmds)
                if not common_result["success"]:
                    overall_success = False
        
        # 2. Verify per-FG runcmd on FG-specific nodes ONLY
        for fg_name, fg_config in groups_section.items():
            fg_cmds = fg_config.get("runcmd", [])
            if fg_cmds:
                fg_nodes = get_nodes_by_functional_group(host, fg_name)
                if fg_nodes:
                    log.check(f"Verifying {len(fg_cmds)} {fg_name} runcmd on {len(fg_nodes)} node(s)")
                    fg_result = verify_runcmd_execution_on_nodes(host, fg_nodes, fg_cmds)
                    scope_results.append((fg_name, fg_cmds, fg_nodes, fg_result))
                    total_cmds += len(fg_cmds)
                    if not fg_result["success"]:
                        overall_success = False
        
        if not scope_results:
            log.skipped("No nodes found for runcmd verification", "Check PXE mapping")
            pytest.skip("No nodes found for runcmd verification")
        
        # Build details
        details_lines = [
            f"runcmd verification: {total_cmds} commands verified per-scope",
            ""
        ]
        
        for scope_name, cmds, nodes, result in scope_results:
            status = "✓" if result["success"] else "✗"
            reachable = result.get("reachable_count", len(nodes))
            details_lines.append(f"{status} [{scope_name}]: {len(cmds)} command(s) on {reachable} node(s)")
            
            for cmd in cmds:
                cmd_preview = cmd[:60] + "..." if len(cmd) > 60 else cmd
                details_lines.append(f"    - {cmd_preview}")
            
            for node_result in result.get("node_results", []):
                hostname = node_result.get("hostname", "unknown")
                node_status = "✓" if node_result.get("success") else "✗"
                details_lines.append(f"    {node_status} {hostname}")
                if not node_result.get("success") and node_result.get("error"):
                    details_lines.append(f"      Error: {node_result['error']}")
        
        details = "\n".join(details_lines)
        
        if not overall_success:
            log.failed("runcmd verification failed", details)
            failed_scopes = [name for name, _, _, r in scope_results if not r["success"]]
            assert False, TEST_ASSERT_MSGS["command_verification_failed"].format(
                failed_nodes=failed_scopes,
                failed_commands="Check details above"
            )
        
        log.passed(
            TEST_LOG_MSGS["commands_verified"].format(
                command_count=total_cmds,
                node_count=sum(r.get("reachable_count", 0) for _, _, _, r in scope_results)
            ),
            details
        )
        
    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception during runcmd verification: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(16)
def test_end_to_end_common_only(host):
    """
    TC-F16: Verify end-to-end provisioning with common section only.
    
    Tests:
    - Common cloud-init applied to all nodes
    - No per-FG specific configuration
    - All nodes receive same cloud-init
    """
    log = TestLogger(TEST_NAMES["end_to_end_common"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if no common section or has groups section
    common_section = config.get("common", {})
    groups_section = config.get("groups", {})
    
    if not common_section:
        log.skipped(SKIP_MSGS["no_common_config"], "No common section in config")
        pytest.skip("No common section in configuration")
    
    if groups_section:
        log.skipped("Common-only test not applicable", "Configuration has groups section")
        pytest.skip("Configuration has groups section, not common-only")
    
    log.check("Testing end-to-end common-only cloud-init provisioning")
    
    try:
        # Get all nodes for common cloud-init
        all_nodes = get_all_nodes_for_common(host)
        
        if not all_nodes:
            log.skipped("No nodes found for common cloud-init", "Check PXE mapping")
            pytest.skip("No nodes found for common cloud-init")
        
        # Check node reachability first
        reachability = check_nodes_reachability(
            host, all_nodes,
            retry_limit=ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
            retry_interval=ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL
        )
        
        reachable_nodes = reachability["reachable"]
        unreachable_nodes = reachability["unreachable"]
        
        if not reachable_nodes:
            log.skipped("No reachable nodes for verification", f"{len(unreachable_nodes)} unreachable")
            pytest.skip("No reachable nodes for verification")
        
        # Run comprehensive integration test
        integration_result = verify_additional_cloud_init_integration(host, config, reachable_nodes)
        
        # Group results by functional group
        grouped_nodes = _group_nodes_by_functional_group(all_nodes)
        
        details_lines = [
            f"End-to-end common-only test: {len(all_nodes)} total nodes",
            f"Reachable: {len(reachable_nodes)}, Unreachable: {len(unreachable_nodes)}",
            "",
            "Functional group breakdown:"
        ]
        
        for fg, fg_nodes in grouped_nodes.items():
            reachable_in_fg = [n for n in fg_nodes if n in reachable_nodes]
            details_lines.append(f"  [{fg}] - {len(reachable_in_fg)}/{len(fg_nodes)} reachable")
            
            for node in fg_nodes:
                hostname = node.get("hostname", "unknown")
                if node in reachable_nodes:
                    details_lines.append(f"    ✓ {hostname}")
                else:
                    details_lines.append(f"    ✗ {hostname} (unreachable)")
        
        details_lines.append("")
        details_lines.append("Integration test results:")
        for test_result in integration_result.get("integration_results", []):
            test_name = test_result.get("test", "unknown")
            success = test_result.get("success", False)
            status = "✓" if success else "✗"
            details_lines.append(f"  {status} {test_name}")
        
        details = "\n".join(details_lines)
        
        if unreachable_nodes or not integration_result["success"]:
            error_parts = []
            if unreachable_nodes:
                error_parts.append(f"{len(unreachable_nodes)} nodes unreachable")
            if not integration_result["success"]:
                error_parts.append("Integration test failed")
            
            log.failed("End-to-end common-only test failed", details)
            assert False, TEST_ASSERT_MSGS["integration_test_failed"].format(
                failed_components=integration_result.get("error", "See details"),
                success_count=integration_result.get("tests_run", 0) - len([r for r in integration_result.get("integration_results", []) if not r["success"]]),
                total_count=integration_result.get("tests_run", 0)
            )
        
        log.passed(
            TEST_LOG_MSGS["end_to_end_ok"].format(component_count=integration_result.get("tests_run", 0)),
            details
        )
        
    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception during end-to-end common test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(17)
def test_end_to_end_per_fg_only(host):
    """
    TC-F17: Verify end-to-end provisioning with per-FG section only.
    
    Tests:
    - Per-FG cloud-init applied to specific nodes
    - No common configuration
    - Each FG gets FG-specific cloud-init
    """
    log = TestLogger(TEST_NAMES["end_to_end_per_fg"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if no groups section or has common section
    common_section = config.get("common", {})
    groups_section = config.get("groups", {})
    
    if not groups_section:
        log.skipped(SKIP_MSGS["no_groups_config"], "No groups section in config")
        pytest.skip("No groups section in configuration")
    
    if common_section:
        log.skipped("Per-FG-only test not applicable", "Configuration has common section")
        pytest.skip("Configuration has common section, not per-FG-only")
    
    log.check(f"Testing end-to-end per-FG-only cloud-init provisioning for {len(groups_section)} group(s)")
    
    try:
        fg_test_results = []
        overall_success = True
        
        for fg_name in groups_section.keys():
            log.check(f"Testing per-FG provisioning for: {fg_name}")
            
            # Get nodes for this functional group
            fg_nodes = get_nodes_by_functional_group(host, fg_name)
            
            if not fg_nodes:
                log.check(f"⏸ {fg_name}: No nodes found")
                fg_test_results.append({
                    "fg_name": fg_name,
                    "success": True,
                    "skipped": True,
                    "reason": "No nodes found"
                })
                continue
            
            # Check reachability
            reachability = check_nodes_reachability(
                host, fg_nodes,
                retry_limit=ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
                retry_interval=ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL
            )
            
            reachable_nodes = reachability["reachable"]
            
            if not reachable_nodes:
                log.check(f"⏸ {fg_name}: No reachable nodes")
                fg_test_results.append({
                    "fg_name": fg_name,
                    "success": True,
                    "skipped": True,
                    "reason": "No reachable nodes"
                })
                continue
            
            # Create per-FG config for integration test
            fg_only_config = {
                "groups": {fg_name: groups_section[fg_name]}
            }
            
            # Run integration test for this FG
            integration_result = verify_additional_cloud_init_integration(host, fg_only_config, reachable_nodes)
            
            fg_test_results.append({
                "fg_name": fg_name,
                "success": integration_result["success"],
                "skipped": False,
                "total_nodes": len(fg_nodes),
                "reachable_nodes": len(reachable_nodes),
                "integration_result": integration_result
            })
            
            if not integration_result["success"]:
                overall_success = False
                log.check(f"✗ {fg_name}: Integration failed")
            else:
                log.check(f"✓ {fg_name}: {len(reachable_nodes)} nodes verified")
        
        # Build comprehensive results
        details_lines = [
            f"End-to-end per-FG-only test: {len(groups_section)} functional groups",
            ""
        ]
        
        for result in fg_test_results:
            if result["skipped"]:
                details_lines.append(f"⏸ {result['fg_name']}: Skipped - {result['reason']}")
            elif result["success"]:
                details_lines.append(f"✓ {result['fg_name']}: {result['reachable_nodes']}/{result['total_nodes']} nodes verified")
            else:
                details_lines.append(f"✗ {result['fg_name']}: Integration failed")
        
        details = "\n".join(details_lines)
        
        successful_fgs = [r for r in fg_test_results if r["success"]]
        failed_fgs = [r for r in fg_test_results if not r["success"] and not r["skipped"]]
        
        if not overall_success:
            log.failed(
                f"Per-FG-only end-to-end test failed: {len(failed_fgs)} failed, {len(successful_fgs)} succeeded",
                details
            )
            failed_names = [r["fg_name"] for r in failed_fgs]
            assert False, f"Per-FG end-to-end test failed for: {', '.join(failed_names)}"
        
        log.passed(
            f"All {len(successful_fgs)} per-FG end-to-end tests passed",
            details
        )
        
    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception during end-to-end per-FG test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(18)
def test_end_to_end_combined(host):
    """
    TC-F18: Verify end-to-end provisioning with common + per-FG sections.
    
    Tests:
    - Common cloud-init applied to all nodes
    - Per-FG cloud-init applied to specific nodes
    - Merged configuration works correctly
    """
    log = TestLogger(TEST_NAMES["end_to_end_combined"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if missing either common or groups section
    common_section = config.get("common", {})
    groups_section = config.get("groups", {})
    
    if not common_section:
        log.skipped(SKIP_MSGS["no_common_config"], "No common section in config")
        pytest.skip("No common section in configuration")
    
    if not groups_section:
        log.skipped(SKIP_MSGS["no_groups_config"], "No groups section in config")
        pytest.skip("No groups section in configuration")
    
    log.check("Testing end-to-end combined (common + per-FG) cloud-init provisioning")
    
    try:
        # Get all nodes (will receive common cloud-init)
        all_nodes = get_all_nodes_for_common(host)
        
        if not all_nodes:
            log.skipped("No nodes found for combined test", "Check PXE mapping")
            pytest.skip("No nodes found for combined test")
        
        # Check overall reachability
        reachability = check_nodes_reachability(
            host, all_nodes,
            retry_limit=ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
            retry_interval=ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL
        )
        
        reachable_nodes = reachability["reachable"]
        unreachable_nodes = reachability["unreachable"]
        
        if not reachable_nodes:
            log.skipped("No reachable nodes for verification", f"{len(unreachable_nodes)} unreachable")
            pytest.skip("No reachable nodes for verification")
        
        # Run comprehensive integration test with full config
        integration_result = verify_additional_cloud_init_integration(host, config, reachable_nodes)
        
        # Group results by functional group
        grouped_nodes = _group_nodes_by_functional_group(all_nodes)
        
        details_lines = [
            f"End-to-end combined test:",
            f"  Common section: applies to {len(all_nodes)} nodes",
            f"  Groups section: {len(groups_section)} functional groups",
            f"  Reachable: {len(reachable_nodes)}, Unreachable: {len(unreachable_nodes)}",
            ""
        ]
        
        # Show which nodes get which configuration
        details_lines.append("Configuration application:")
        for fg, fg_nodes in grouped_nodes.items():
            reachable_in_fg = [n for n in fg_nodes if n in reachable_nodes]
            fg_has_specific_config = fg in groups_section
            
            config_type = "Common + Per-FG" if fg_has_specific_config else "Common only"
            details_lines.append(f"  [{fg}] - {len(reachable_in_fg)}/{len(fg_nodes)} reachable ({config_type})")
            
            for node in reachable_in_fg:
                hostname = node.get("hostname", "unknown")
                details_lines.append(f"    ✓ {hostname}")
        
        if unreachable_nodes:
            details_lines.append("")
            details_lines.append("Unreachable nodes:")
            for node in unreachable_nodes:
                hostname = node.get("hostname", "unknown")
                details_lines.append(f"    ✗ {hostname}")
        
        details_lines.append("")
        details_lines.append("Integration test results:")
        for test_result in integration_result.get("integration_results", []):
            test_name = test_result.get("test", "unknown")
            success = test_result.get("success", False)
            status = "✓" if success else "✗"
            details_lines.append(f"  {status} {test_name}")
        
        details = "\n".join(details_lines)
        
        if unreachable_nodes or not integration_result["success"]:
            error_parts = []
            if unreachable_nodes:
                error_parts.append(f"{len(unreachable_nodes)} nodes unreachable")
            if not integration_result["success"]:
                error_parts.append("Integration test failed")
            
            log.failed("End-to-end combined test failed", details)
            assert False, TEST_ASSERT_MSGS["integration_test_failed"].format(
                failed_components=integration_result.get("error", "See details"),
                success_count=integration_result.get("tests_run", 0) - len([r for r in integration_result.get("integration_results", []) if not r["success"]]),
                total_count=integration_result.get("tests_run", 0)
            )
        
        log.passed(
            TEST_LOG_MSGS["end_to_end_ok"].format(component_count=integration_result.get("tests_run", 0)),
            details
        )
        
    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception during end-to-end combined test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(19)  
def test_end_to_end_multiple_fgs(host):
    """
    TC-F19: Verify end-to-end provisioning with multiple functional groups.
    
    Tests:
    - Multiple FGs configured simultaneously
    - Each FG gets correct cloud-init
    - No cross-contamination between FGs
    """
    log = TestLogger(TEST_NAMES["end_to_end_multiple_fgs"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if not enough groups
    groups_section = config.get("groups", {})
    if len(groups_section) < 2:
        log.skipped("Multiple FG test requires at least 2 groups", f"Found {len(groups_section)} group(s)")
        pytest.skip(f"Multiple FG test requires at least 2 groups, found {len(groups_section)}")
    
    log.check(f"Testing end-to-end provisioning with {len(groups_section)} functional groups")
    
    try:
        # Test each functional group individually
        fg_results = []
        all_test_nodes = []
        
        for fg_name in groups_section.keys():
            log.check(f"Processing functional group: {fg_name}")
            
            # Get nodes for this FG
            fg_nodes = get_nodes_by_functional_group(host, fg_name)
            
            if not fg_nodes:
                fg_results.append({
                    "fg_name": fg_name,
                    "success": True,
                    "skipped": True,
                    "reason": "No nodes found"
                })
                continue
            
            all_test_nodes.extend(fg_nodes)
            
            # Check reachability for this FG
            reachability = check_nodes_reachability(
                host, fg_nodes,
                retry_limit=ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
                retry_interval=ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL
            )
            
            reachable_nodes = reachability["reachable"]
            
            if not reachable_nodes:
                fg_results.append({
                    "fg_name": fg_name,
                    "success": True,
                    "skipped": True,
                    "reason": "No reachable nodes"
                })
                continue
            
            # Create FG-specific config for testing
            fg_config = {"groups": {fg_name: groups_section[fg_name]}}
            
            # Add common section if it exists (applies to all FGs)
            if config.get("common"):
                fg_config["common"] = config["common"]
            
            # Run integration test for this FG
            integration_result = verify_additional_cloud_init_integration(host, fg_config, reachable_nodes)
            
            fg_results.append({
                "fg_name": fg_name,
                "success": integration_result["success"],
                "skipped": False,
                "total_nodes": len(fg_nodes),
                "reachable_nodes": len(reachable_nodes),
                "integration_details": integration_result.get("details", "")
            })
        
        # Remove duplicate nodes from all_test_nodes
        unique_test_nodes = []
        seen_ips = set()
        for node in all_test_nodes:
            admin_ip = node.get("admin_ip")
            if admin_ip and admin_ip not in seen_ips:
                unique_test_nodes.append(node)
                seen_ips.add(admin_ip)
        
        # Build comprehensive results
        details_lines = [
            f"Multiple FG end-to-end test: {len(groups_section)} functional groups",
            f"Total unique nodes: {len(unique_test_nodes)}",
            ""
        ]
        
        for result in fg_results:
            if result["skipped"]:
                details_lines.append(f"⏸ {result['fg_name']}: Skipped - {result['reason']}")
            elif result["success"]:
                details_lines.append(f"✓ {result['fg_name']}: {result['reachable_nodes']}/{result['total_nodes']} nodes verified")
            else:
                details_lines.append(f"✗ {result['fg_name']}: Integration failed")
        
        details_lines.append("")
        details_lines.append("Functional group configuration:")
        for fg_name in groups_section.keys():
            fg_config = groups_section[fg_name]
            has_write_files = bool(fg_config.get("write_files"))
            has_runcmd = bool(fg_config.get("runcmd"))
            details_lines.append(f"  [{fg_name}]: write_files={has_write_files}, runcmd={has_runcmd}")
        
        details = "\n".join(details_lines)
        
        successful_fgs = [r for r in fg_results if r["success"]]
        failed_fgs = [r for r in fg_results if not r["success"] and not r["skipped"]]
        
        overall_success = len(failed_fgs) == 0
        
        if not overall_success:
            log.failed(
                f"Multiple FG end-to-end test failed: {len(failed_fgs)} failed, {len(successful_fgs)} succeeded",
                details
            )
            failed_names = [r["fg_name"] for r in failed_fgs]
            assert False, f"Multiple FG end-to-end test failed for: {', '.join(failed_names)}"
        
        log.passed(
            f"All {len(successful_fgs)} functional groups verified successfully",
            details
        )
        
    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception during multiple FG test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(20)
def test_end_to_end_mixed_directives(host):
    """
    TC-F20: Verify end-to-end provisioning with write_files and runcmd.
    
    Tests:
    - Both write_files and runcmd work together
    - Files created before commands run
    - Commands can reference created files
    """
    log = TestLogger(TEST_NAMES["end_to_end_mixed_directives"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Check for mixed directives
    has_mixed_common = False
    has_mixed_groups = False
    
    common_section = config.get("common", {})
    if common_section.get("write_files") and common_section.get("runcmd"):
        has_mixed_common = True
    
    groups_section = config.get("groups", {})
    for fg_config in groups_section.values():
        if fg_config.get("write_files") and fg_config.get("runcmd"):
            has_mixed_groups = True
            break
    
    if not has_mixed_common and not has_mixed_groups:
        log.skipped("Mixed directives test requires both write_files and runcmd", "No mixed directives found")
        pytest.skip("No mixed directives (write_files + runcmd) found in configuration")
    
    log.check("Testing end-to-end provisioning with mixed write_files and runcmd directives")
    
    try:
        # Get all nodes that will be affected
        test_nodes = []
        
        if has_mixed_common:
            test_nodes.extend(get_all_nodes_for_common(host))
        
        if has_mixed_groups:
            for fg_name, fg_config in groups_section.items():
                if fg_config.get("write_files") and fg_config.get("runcmd"):
                    fg_nodes = get_nodes_by_functional_group(host, fg_name)
                    test_nodes.extend(fg_nodes)
        
        # Remove duplicates
        unique_nodes = []
        seen_ips = set()
        for node in test_nodes:
            admin_ip = node.get("admin_ip")
            if admin_ip and admin_ip not in seen_ips:
                unique_nodes.append(node)
                seen_ips.add(admin_ip)
        
        if not unique_nodes:
            log.skipped("No nodes found for mixed directives test", "Check PXE mapping")
            pytest.skip("No nodes found for mixed directives test")
        
        # Check reachability
        reachability = check_nodes_reachability(
            host, unique_nodes,
            retry_limit=ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
            retry_interval=ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL
        )
        
        reachable_nodes = reachability["reachable"]
        unreachable_nodes = reachability["unreachable"]
        
        if not reachable_nodes:
            log.skipped("No reachable nodes for verification", f"{len(unreachable_nodes)} unreachable")
            pytest.skip("No reachable nodes for verification")
        
        # Run comprehensive integration test
        integration_result = verify_additional_cloud_init_integration(host, config, reachable_nodes)
        
        # Analyze mixed directives
        mixed_sections = []
        if has_mixed_common:
            mixed_sections.append({
                "section": "common",
                "write_files_count": len(common_section.get("write_files", [])),
                "runcmd_count": len(common_section.get("runcmd", []))
            })
        
        for fg_name, fg_config in groups_section.items():
            if fg_config.get("write_files") and fg_config.get("runcmd"):
                mixed_sections.append({
                    "section": f"groups.{fg_name}",
                    "write_files_count": len(fg_config.get("write_files", [])),
                    "runcmd_count": len(fg_config.get("runcmd", []))
                })
        
        details_lines = [
            f"Mixed directives end-to-end test:",
            f"  Sections with mixed directives: {len(mixed_sections)}",
            f"  Total nodes: {len(unique_nodes)} ({len(reachable_nodes)} reachable)",
            ""
        ]
        
        details_lines.append("Mixed directive sections:")
        for section_info in mixed_sections:
            details_lines.append(f"  [{section_info['section']}]:")
            details_lines.append(f"    write_files: {section_info['write_files_count']} entries")
            details_lines.append(f"    runcmd: {section_info['runcmd_count']} entries")
        
        details_lines.append("")
        details_lines.append("Integration test results:")
        for test_result in integration_result.get("integration_results", []):
            test_name = test_result.get("test", "unknown")
            success = test_result.get("success", False)
            status = "✓" if success else "✗"
            details_lines.append(f"  {status} {test_name}")
        
        details = "\n".join(details_lines)
        
        if unreachable_nodes or not integration_result["success"]:
            error_parts = []
            if unreachable_nodes:
                error_parts.append(f"{len(unreachable_nodes)} nodes unreachable")
            if not integration_result["success"]:
                error_parts.append("Integration test failed")
            
            log.failed("Mixed directives end-to-end test failed", details)
            assert False, TEST_ASSERT_MSGS["integration_test_failed"].format(
                failed_components=integration_result.get("error", "See details"),
                success_count=integration_result.get("tests_run", 0) - len([r for r in integration_result.get("integration_results", []) if not r["success"]]),
                total_count=integration_result.get("tests_run", 0)
            )
        
        log.passed(
            TEST_LOG_MSGS["end_to_end_ok"].format(component_count=integration_result.get("tests_run", 0)),
            details
        )
        
    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception during mixed directives test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(21)
def test_packages_integration(host):
    """
    TC-F21: Verify integration with additional_packages.json.
    
    Tests:
    - Packages from additional_packages.json are available
    - runcmd can use installed packages
    - Package installation completed before cloud-init
    """
    log = TestLogger(TEST_NAMES["packages_integration"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Collect package-dependent commands per-scope
    common_section = config.get("common", {})
    groups_section = config.get("groups", {})
    
    common_pkg_cmds = []
    for cmd in common_section.get("runcmd", []):
        if any(pkg in cmd for pkg in ["rpm -q", "tree", "wget", "curl", "git"]):
            common_pkg_cmds.append(cmd)
    
    per_fg_pkg_cmds = {}
    for fg_name, fg_config in groups_section.items():
        for cmd in fg_config.get("runcmd", []):
            if any(pkg in cmd for pkg in ["rpm -q", "tree", "wget", "curl", "git"]):
                if fg_name not in per_fg_pkg_cmds:
                    per_fg_pkg_cmds[fg_name] = []
                per_fg_pkg_cmds[fg_name].append(cmd)
    
    if not common_pkg_cmds and not per_fg_pkg_cmds:
        log.skipped("No package-dependent commands found", "No runcmd using common packages")
        pytest.skip("No package-dependent commands found in runcmd")
    
    total_pkg_cmds = len(common_pkg_cmds) + sum(len(v) for v in per_fg_pkg_cmds.values())
    log.check(f"Testing package integration with {total_pkg_cmds} package-dependent command(s)")
    
    try:
        overall_success = True
        scope_results = []
        
        # 1. Verify common package commands on ALL nodes
        if common_pkg_cmds:
            all_nodes = get_all_nodes_for_common(host)
            if all_nodes:
                log.check(f"Verifying {len(common_pkg_cmds)} common package command(s) on {len(all_nodes)} node(s)")
                common_result = verify_runcmd_execution_on_nodes(host, all_nodes, common_pkg_cmds)
                scope_results.append(("common", common_pkg_cmds, all_nodes, common_result))
                if not common_result["success"]:
                    overall_success = False
        
        # 2. Verify per-FG package commands on FG-specific nodes ONLY
        for fg_name, fg_cmds in per_fg_pkg_cmds.items():
            fg_nodes = get_nodes_by_functional_group(host, fg_name)
            if fg_nodes:
                log.check(f"Verifying {len(fg_cmds)} {fg_name} package command(s) on {len(fg_nodes)} node(s)")
                fg_result = verify_runcmd_execution_on_nodes(host, fg_nodes, fg_cmds)
                scope_results.append((fg_name, fg_cmds, fg_nodes, fg_result))
                if not fg_result["success"]:
                    overall_success = False
        
        if not scope_results:
            log.skipped("No nodes found for package integration test", "Check PXE mapping")
            pytest.skip("No nodes found for package integration test")
        
        # Build details
        details_lines = [
            f"Package integration test: {total_pkg_cmds} commands verified per-scope",
            ""
        ]
        
        for scope_name, cmds, nodes, result in scope_results:
            status = "✓" if result["success"] else "✗"
            reachable = result.get("reachable_count", len(nodes))
            details_lines.append(f"{status} [{scope_name}]: {len(cmds)} command(s) on {reachable} node(s)")
            
            for cmd in cmds:
                cmd_preview = cmd[:60] + "..." if len(cmd) > 60 else cmd
                details_lines.append(f"    - {cmd_preview}")
            
            for node_result in result.get("node_results", []):
                hostname = node_result.get("hostname", "unknown")
                node_status = "✓" if node_result.get("success") else "✗"
                details_lines.append(f"    {node_status} {hostname}")
                if not node_result.get("success") and node_result.get("error"):
                    details_lines.append(f"      Error: {node_result['error']}")
        
        details = "\n".join(details_lines)
        
        if not overall_success:
            log.failed("Package integration test failed", details)
            failed_scopes = [name for name, _, _, r in scope_results if not r["success"]]
            assert False, TEST_ASSERT_MSGS["command_verification_failed"].format(
                failed_nodes=failed_scopes,
                failed_commands="Package-dependent commands"
            )
        
        log.passed(
            TEST_LOG_MSGS["packages_integration_ok"].format(
                node_count=sum(r.get("reachable_count", 0) for _, _, _, r in scope_results)
            ),
            details
        )
        
    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception during package integration test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"
