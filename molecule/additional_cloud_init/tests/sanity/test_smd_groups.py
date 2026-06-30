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
Additional Cloud-Init SMD Groups Test Cases.

Test cases for SMD group creation and management:
1. TC-F05: Common SMD group creation
2. TC-F06: Per-FG SMD group creation - single FG
3. TC-F07: Per-FG SMD group creation - multiple FGs
"""

import pytest
from automation_library.core import (
    TestLogger, 
    get_functional_groups_from_pxe_mapping,
    get_nodes_info,
)
from automation_library.additional_cloud_init.functions import (
    load_additional_cloud_init_config,
    get_functional_groups_from_config,
    skip_if_additional_cloud_init_disabled,
    verify_smd_group_creation,
    get_xnames_for_fg,
    get_all_xnames,
)
from automation_library.additional_cloud_init.vars import (
    COMMON_SMD_GROUP_NAME,
    SMD_GROUP_PREFIX,
)
from automation_library.additional_cloud_init.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)


def _get_xnames_from_nodes(nodes):
    """Extract XNAMEs from node list. Use hostname as XNAME if xname not present."""
    xnames = []
    for node in nodes:
        xname = node.get("xname") or node.get("hostname", f"unknown_{len(xnames)}")
        xnames.append(xname)
    return xnames


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
@pytest.mark.order(5)
def test_common_smd_group_creation(host):
    """
    TC-F05: Verify common SMD group created with all XNAMEs.
    
    Tests:
    - SMD group "additional_cloud_init" created
    - Group contains ALL nodes from PXE mapping
    - Group membership is correct
    """
    log = TestLogger(TEST_NAMES["common_smd_group"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if no common section
    if not config.get("common"):
        log.skipped(SKIP_MSGS["no_common_config"], "No common section in config")
        pytest.skip("No common section in configuration")
    
    log.check("Getting all nodes from PXE mapping for common SMD group")
    
    # Get all functional groups and their nodes
    try:
        available_fgs = get_functional_groups_from_pxe_mapping(host)
        if not available_fgs:
            log.skipped(SKIP_MSGS["no_functional_groups"], "No functional groups in PXE mapping")
            pytest.skip("No functional groups in PXE mapping")
        
        log.check(TEST_LOG_MSGS["fgs_found"].format(
            fg_count=len(available_fgs),
            fg_list=", ".join(sorted(available_fgs))
        ))
        
        # Collect all nodes from all functional groups
        all_nodes = []
        fg_node_counts = {}
        
        for fg in available_fgs:
            fg_nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
            all_nodes.extend(fg_nodes)
            fg_node_counts[fg] = len(fg_nodes)
        
        if not all_nodes:
            log.skipped("No nodes found in any functional group", "Check PXE mapping")
            pytest.skip("No nodes found in PXE mapping")
        
        # Get XNAMEs from SMD (PXE mapping doesn't have xnames)
        expected_xnames = get_all_xnames(host)
        if not expected_xnames:
            log.skipped("No xnames found in SMD", "SMD components not available")
            pytest.skip("No xnames found in SMD")
        
        log.check(TEST_LOG_MSGS["common_applies_to"].format(
            node_count=len(all_nodes),
            fg_count=len(available_fgs)
        ))
        
        # Verify SMD group creation
        log.check(f"Verifying common SMD group '{COMMON_SMD_GROUP_NAME}' with {len(expected_xnames)} members")
        
        smd_result = verify_smd_group_creation(host, COMMON_SMD_GROUP_NAME, expected_xnames)
        
        # Build detailed results
        grouped_nodes = _group_nodes_by_functional_group(all_nodes)
        details_lines = [
            f"SMD Group: {COMMON_SMD_GROUP_NAME}",
            f"Total nodes: {len(all_nodes)}",
            "",
            "Functional group breakdown:"
        ]
        
        for fg, fg_nodes in grouped_nodes.items():
            details_lines.append(f"  [{fg}] - {len(fg_nodes)} node(s)")
            for node in fg_nodes:
                hostname = node.get("hostname", "unknown")
                xname = node.get("xname") or hostname
                status = "✓" if smd_result["success"] else "✗"
                details_lines.append(f"    {status} {hostname} (XNAME: {xname})")
        
        details_lines.append("")
        details_lines.append(f"Expected XNAMEs: {len(expected_xnames)}")
        details_lines.append(f"Found XNAMEs: {len(smd_result.get('found_xnames', []))}")
        
        if smd_result.get("missing_xnames"):
            details_lines.append(f"Missing: {smd_result['missing_xnames']}")
        if smd_result.get("extra_xnames"):
            details_lines.append(f"Extra: {smd_result['extra_xnames']}")
        
        details = "\n".join(details_lines)
        
        if not smd_result["success"]:
            log.failed("Common SMD group verification failed", details)
            assert False, TEST_ASSERT_MSGS["smd_group_failed"].format(
                group_name=COMMON_SMD_GROUP_NAME,
                expected_count=len(expected_xnames),
                found_count=len(smd_result.get("found_xnames", [])),
                missing_xnames=smd_result.get("missing_xnames", []),
                extra_xnames=smd_result.get("extra_xnames", [])
            )
        
        log.passed(
            TEST_LOG_MSGS["smd_group_verified"].format(
                group_name=COMMON_SMD_GROUP_NAME,
                member_count=len(expected_xnames)
            ),
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during common SMD group verification test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(6)
def test_per_fg_smd_group_single(host):
    """
    TC-F06: Verify per-FG SMD group created for single functional group.
    
    Tests:
    - SMD group "additional_cloud_init_<fg>" created
    - Group contains only nodes from specified FG
    - Group membership filtering is correct
    """
    log = TestLogger(TEST_NAMES["per_fg_smd_group_single"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if no groups section
    groups_section = config.get("groups", {})
    if not groups_section:
        log.skipped(SKIP_MSGS["no_groups_config"], "No groups section in config")
        pytest.skip("No groups section in configuration")
    
    log.check(f"Testing per-FG SMD group creation for {len(groups_section)} group(s)")
    
    # Test the first functional group as single FG test
    first_fg = next(iter(groups_section.keys()))
    log.check(f"Testing single FG: {first_fg}")
    
    try:
        # Get nodes for this functional group
        fg_nodes = get_nodes_info(host, search_by="functional_group", search_value=first_fg)
        
        if not fg_nodes:
            log.skipped(SKIP_MSGS["no_nodes_for_fg"].format(fg_name=first_fg), f"No nodes for {first_fg}")
            pytest.skip(f"No nodes found for functional group {first_fg}")
        
        # Get XNAMEs from SMD group (PXE mapping doesn't have xnames)
        expected_xnames = get_xnames_for_fg(host, first_fg)
        if not expected_xnames:
            log.skipped(f"No xnames found in SMD for {first_fg}", "SMD group not found")
            pytest.skip(f"No xnames found in SMD for {first_fg}")
        group_name = f"{SMD_GROUP_PREFIX}_{first_fg}"
        
        log.check(TEST_LOG_MSGS["per_fg_applies_to"].format(
            node_count=len(fg_nodes),
            fg_name=first_fg
        ))
        
        # Verify SMD group creation
        log.check(f"Verifying per-FG SMD group '{group_name}' with {len(expected_xnames)} members")
        
        smd_result = verify_smd_group_creation(host, group_name, expected_xnames)
        
        # Build detailed results
        details_lines = [
            f"SMD Group: {group_name}",
            f"Functional Group: {first_fg}",
            f"Total nodes: {len(fg_nodes)}",
            "",
            "Node breakdown:"
        ]
        
        for node in fg_nodes:
            hostname = node.get("hostname", "unknown")
            admin_ip = node.get("admin_ip", "unknown")
            xname = node.get("xname") or hostname
            status = "✓" if smd_result["success"] else "✗"
            details_lines.append(f"  {status} {hostname} ({admin_ip}) - XNAME: {xname}")
        
        details_lines.append("")
        details_lines.append(f"Expected XNAMEs: {len(expected_xnames)}")
        details_lines.append(f"Found XNAMEs: {len(smd_result.get('found_xnames', []))}")
        
        details = "\n".join(details_lines)
        
        if not smd_result["success"]:
            log.failed(f"Per-FG SMD group verification failed for {first_fg}", details)
            assert False, TEST_ASSERT_MSGS["smd_group_failed"].format(
                group_name=group_name,
                expected_count=len(expected_xnames),
                found_count=len(smd_result.get("found_xnames", [])),
                missing_xnames=smd_result.get("missing_xnames", []),
                extra_xnames=smd_result.get("extra_xnames", [])
            )
        
        log.passed(
            TEST_LOG_MSGS["smd_group_verified"].format(
                group_name=group_name,
                member_count=len(expected_xnames)
            ),
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during per-FG SMD group verification test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(7)
def test_per_fg_smd_group_multiple(host):
    """
    TC-F07: Verify multiple per-FG SMD groups created with correct filtering.
    
    Tests:
    - Multiple SMD groups created for different FGs
    - Each group contains only nodes from its FG
    - No cross-contamination between groups
    """
    log = TestLogger(TEST_NAMES["per_fg_smd_group_multiple"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if no groups section
    groups_section = config.get("groups", {})
    if not groups_section:
        log.skipped(SKIP_MSGS["no_groups_config"], "No groups section in config")
        pytest.skip("No groups section in configuration")
    
    if len(groups_section) < 2:
        log.skipped("Multiple FG test requires at least 2 groups", f"Found {len(groups_section)} group(s)")
        pytest.skip(f"Multiple FG test requires at least 2 groups, found {len(groups_section)}")
    
    log.check(f"Testing multiple per-FG SMD group verification for {len(groups_section)} groups")
    
    group_results = []
    overall_success = True
    
    try:
        for fg_name in groups_section.keys():
            log.check(f"Verifying functional group: {fg_name}")
            
            # Get nodes for this functional group
            fg_nodes = get_nodes_info(host, search_by="functional_group", search_value=fg_name)
            
            if not fg_nodes:
                log.check(f"No nodes found for {fg_name}, skipping")
                group_results.append({
                    "fg_name": fg_name,
                    "success": True,
                    "skipped": True,
                    "reason": "No nodes found"
                })
                continue
            
            # Get XNAMEs from SMD group (PXE mapping doesn't have xnames)
            expected_xnames = get_xnames_for_fg(host, fg_name)
            if not expected_xnames:
                log.check(f"No xnames in SMD for {fg_name}, skipping")
                group_results.append({
                    "fg_name": fg_name,
                    "success": True,
                    "skipped": True,
                    "reason": "No xnames in SMD"
                })
                continue
            group_name = f"{SMD_GROUP_PREFIX}_{fg_name}"
            
            # Verify SMD group creation
            smd_result = verify_smd_group_creation(host, group_name, expected_xnames)
            
            group_results.append({
                "fg_name": fg_name,
                "group_name": group_name,
                "success": smd_result["success"],
                "skipped": False,
                "node_count": len(fg_nodes),
                "xname_count": len(expected_xnames),
                "error": smd_result.get("error", ""),
                "nodes": fg_nodes
            })
            
            if not smd_result["success"]:
                overall_success = False
                log.check(f"❌ {fg_name}: {smd_result['error']}")
            else:
                log.check(f"✓ {fg_name}: {len(expected_xnames)} members")
        
        # Build comprehensive results
        details_lines = [
            f"Multiple per-FG SMD groups: {len(groups_section)} groups processed",
            ""
        ]
        
        for result in group_results:
            if result["skipped"]:
                details_lines.append(f"⏸ {result['fg_name']}: Skipped - {result['reason']}")
            elif result["success"]:
                details_lines.append(f"✓ {result['fg_name']}: {result['node_count']} nodes → {result['group_name']}")
            else:
                details_lines.append(f"✗ {result['fg_name']}: FAILED - {result['error']}")
        
        details_lines.append("")
        details_lines.append("Per-FG node breakdown:")
        
        for result in group_results:
            if result["skipped"]:
                continue
            
            details_lines.append(f"  [{result['fg_name']}]:")
            for node in result.get("nodes", []):
                hostname = node.get("hostname", "unknown")
                xname = node.get("xname") or hostname
                status = "✓" if result["success"] else "✗"
                details_lines.append(f"    {status} {hostname} (XNAME: {xname})")
        
        details = "\n".join(details_lines)
        
        successful_groups = [r for r in group_results if r["success"] and not r["skipped"]]
        failed_groups = [r for r in group_results if not r["success"] and not r["skipped"]]
        
        if not overall_success:
            log.failed(
                f"Multiple per-FG SMD groups failed: {len(failed_groups)} failed, {len(successful_groups)} succeeded",
                details
            )
            failed_names = [r["fg_name"] for r in failed_groups]
            assert False, f"Per-FG SMD group verification failed for: {', '.join(failed_names)}"
        
        log.passed(
            f"All {len(successful_groups)} per-FG SMD groups verified successfully",
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during multiple per-FG SMD group verification test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"
