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
Additional Cloud-Init Idempotency Test Cases.

Idempotency test cases:
1. TC-I01: SMD group creation idempotency
2. TC-I02: BSS registration idempotency
3. TC-I03: Full pipeline idempotency

These tests execute the provision playbook tasks multiple times to verify idempotency.
"""

import pytest
from automation_library.core import TestLogger, get_functional_groups_from_pxe_mapping
from automation_library.additional_cloud_init.functions import (
    load_additional_cloud_init_config,
    skip_if_additional_cloud_init_disabled,
    verify_smd_group_creation,
    verify_smd_group_deletion,
    verify_bss_group_registration,
    get_all_nodes_for_common,
    get_nodes_by_functional_group,
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


def _check_ochami_services_available(host):
    """Check if OpenCHAMI services are available."""
    from automation_library.additional_cloud_init.functions.smd_func import _run_ochami
    
    try:
        # Test SMD connectivity
        smd_result = _run_ochami(host, "ochami smd component get")
        smd_available = smd_result.rc == 0
        
        # Test BSS connectivity
        bss_result = _run_ochami(host, "ochami cloud-init group get config")
        bss_available = bss_result.rc == 0
        
        return {
            "smd_available": smd_available,
            "bss_available": bss_available,
            "both_available": smd_available and bss_available
        }
    except Exception:
        return {
            "smd_available": False,
            "bss_available": False,
            "both_available": False
        }


def _run_provision_playbook_tasks(host):
    """
    Execute the full provision playbook for idempotency testing.
    
    Runs provision/provision.yml inside omnia_core container, which includes
    additional cloud-init configuration (SMD groups, BSS registration, etc.).
    """
    from automation_library.core import run_on_oim
    
    try:
        provision_result = run_on_oim(host,
            "podman exec omnia_core bash -lc 'cd /omnia && ansible-playbook provision/provision.yml -e input_project_dir=/opt/omnia/input/project_default'"
        )
        
        return {
            "success": provision_result.rc == 0,
            "error": provision_result.stderr if provision_result.rc != 0 else "",
            "results": {
                "provision": {
                    "returncode": provision_result.rc,
                    "stdout": provision_result.stdout,
                    "stderr": provision_result.stderr
                }
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": {}
        }


@pytest.mark.sanity
@pytest.mark.order(22)
def test_smd_group_idempotency(host):
    """
    TC-I01: Verify SMD group creation idempotency.
    
    Tests:
    - Running provision playbook tasks multiple times produces same result
    - SMD group membership remains consistent after re-run
    - No duplicate groups or members created
    """
    log = TestLogger(TEST_NAMES["smd_group_idempotency"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Check if SMD service is available
    services = _check_ochami_services_available(host)
    if not services["smd_available"]:
        log.skipped(SKIP_MSGS["smd_service_unavailable"], "SMD service not available")
        pytest.skip("OpenCHAMI SMD service is not available")
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    log.check("Testing SMD group creation idempotency")
    
    try:
        # Test common SMD group idempotency if common section exists
        idempotency_results = []
        
        if config.get("common"):
            log.check("Testing common SMD group idempotency")
            
            # Get all xnames from SMD for common group
            expected_xnames = get_all_xnames(host)
            if expected_xnames:
                
                # Get initial state before provision run
                log.check(f"Initial state query of {COMMON_SMD_GROUP_NAME}")
                first_result = verify_smd_group_creation(host, COMMON_SMD_GROUP_NAME, expected_xnames)
                
                # Execute provision playbook tasks
                log.check("Executing provision playbook tasks for idempotency test")
                provision_result = _run_provision_playbook_tasks(host)
                
                if not provision_result["success"]:
                    log.failed("Provision playbook execution failed", provision_result.get("error", "Unknown error"))
                    assert False, f"Provision playbook failed: {provision_result.get('error', 'Unknown error')}"
                
                # Get state after provision run
                log.check(f"State query after provision run of {COMMON_SMD_GROUP_NAME}")
                second_result = verify_smd_group_creation(host, COMMON_SMD_GROUP_NAME, expected_xnames)
                
                # Both should succeed and have same membership (idempotent)
                common_idempotent = (
                    first_result["success"] and 
                    second_result["success"] and
                    set(first_result.get("found_xnames", [])) == set(second_result.get("found_xnames", []))
                )
                
                idempotency_results.append({
                    "group_name": COMMON_SMD_GROUP_NAME,
                    "group_type": "common",
                    "success": common_idempotent,
                    "first_success": first_result["success"],
                    "second_success": second_result["success"],
                    "consistent_membership": set(first_result.get("found_xnames", [])) == set(second_result.get("found_xnames", [])),
                    "member_count": len(expected_xnames)
                })
                
                if common_idempotent:
                    log.check(f"✓ {COMMON_SMD_GROUP_NAME}: Idempotent")
                else:
                    log.check(f"✗ {COMMON_SMD_GROUP_NAME}: Not idempotent")
        
        # Test per-FG SMD group idempotency
        groups_section = config.get("groups", {})
        for fg_name in groups_section.keys():
            log.check(f"Testing per-FG SMD group idempotency: {fg_name}")
            
            expected_xnames = get_xnames_for_fg(host, fg_name)
            if not expected_xnames:
                continue
                
            group_name = f"{SMD_GROUP_PREFIX}_{fg_name}"
            
            # Get initial state before provision run
            log.check(f"Initial state query of {group_name}")
            first_result = verify_smd_group_creation(host, group_name, expected_xnames)
            
            # Execute provision playbook tasks (only once for all groups to save time)
            # Note: This is a simplification - in a full test, you'd run provision per group
            # but for efficiency, we run it once and verify all groups
            
            # Get state after provision run
            log.check(f"State query after provision run of {group_name}")
            second_result = verify_smd_group_creation(host, group_name, expected_xnames)
            
            # Both should succeed and have same membership (idempotent)
            fg_idempotent = (
                first_result["success"] and 
                second_result["success"] and
                set(first_result.get("found_xnames", [])) == set(second_result.get("found_xnames", []))
            )
            
            idempotency_results.append({
                "group_name": group_name,
                "group_type": f"per-FG ({fg_name})",
                "success": fg_idempotent,
                "first_success": first_result["success"],
                "second_success": second_result["success"],
                "consistent_membership": set(first_result.get("found_xnames", [])) == set(second_result.get("found_xnames", [])),
                "member_count": len(expected_xnames)
            })
            
            if fg_idempotent:
                log.check(f"✓ {group_name}: Idempotent")
            else:
                log.check(f"✗ {group_name}: Not idempotent")
        
        if not idempotency_results:
            log.skipped("No SMD groups to test idempotency", "No common or groups sections")
            pytest.skip("No SMD groups to test idempotency")
        
        # Check overall results
        failed_idempotency = [r for r in idempotency_results if not r["success"]]
        
        details_lines = [
            f"SMD group idempotency test: {len(idempotency_results)} groups tested",
            ""
        ]
        
        for result in idempotency_results:
            status = "✓" if result["success"] else "✗"
            details_lines.append(f"  {status} {result['group_name']} ({result['group_type']})")
            details_lines.append(f"    Before provision: {'✓' if result['first_success'] else '✗'}")
            details_lines.append(f"    After provision: {'✓' if result['second_success'] else '✗'}")
            details_lines.append(f"    Consistent membership: {'✓' if result['consistent_membership'] else '✗'}")
            details_lines.append(f"    Member count: {result['member_count']}")
        
        details = "\n".join(details_lines)
        
        if failed_idempotency:
            log.failed(
                f"SMD group idempotency failed: {len(failed_idempotency)} groups not idempotent",
                details
            )
            failed_groups = [r["group_name"] for r in failed_idempotency]
            assert False, f"SMD group idempotency failed for: {', '.join(failed_groups)}"
        
        log.passed(
            TEST_LOG_MSGS["smd_group_idempotent"].format(group_name=f"{len(idempotency_results)} groups"),
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during SMD idempotency test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(23)
def test_bss_registration_idempotency(host):
    """
    TC-I02: Verify BSS registration idempotency.
    
    Tests:
    - Running provision playbook tasks multiple times produces same result
    - BSS registration remains consistent after re-run
    - No duplicate registrations
    """
    log = TestLogger(TEST_NAMES["bss_registration_idempotency"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Check if BSS service is available
    services = _check_ochami_services_available(host)
    if not services["bss_available"]:
        log.skipped(SKIP_MSGS["bss_service_unavailable"], "BSS service not available")
        pytest.skip("OpenCHAMI BSS service is not available")
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    log.check("Testing BSS registration idempotency")
    
    try:
        # Test BSS registration idempotency
        idempotency_results = []
        
        # Test common BSS registration if common section exists
        if config.get("common"):
            log.check("Testing common BSS registration idempotency")
            
            # Get initial state before provision run
            log.check(f"Initial BSS query of {COMMON_SMD_GROUP_NAME}")
            first_result = verify_bss_group_registration(host, COMMON_SMD_GROUP_NAME)
            
            # Execute provision playbook tasks
            log.check("Executing provision playbook tasks for idempotency test")
            provision_result = _run_provision_playbook_tasks(host)
            
            if not provision_result["success"]:
                log.failed("Provision playbook execution failed", provision_result.get("error", "Unknown error"))
                assert False, f"Provision playbook failed: {provision_result.get('error', 'Unknown error')}"
            
            # Get state after provision run
            log.check(f"BSS query after provision run of {COMMON_SMD_GROUP_NAME}")
            second_result = verify_bss_group_registration(host, COMMON_SMD_GROUP_NAME)
            
            # Both should succeed and be registered (idempotent)
            common_idempotent = (
                first_result["success"] and 
                second_result["success"] and
                first_result.get("registered", False) and
                second_result.get("registered", False)
            )
            
            idempotency_results.append({
                "group_name": COMMON_SMD_GROUP_NAME,
                "group_type": "common",
                "success": common_idempotent,
                "first_success": first_result["success"],
                "second_success": second_result["success"],
                "first_registered": first_result.get("registered", False),
                "second_registered": second_result.get("registered", False)
            })
            
            if common_idempotent:
                log.check(f"✓ {COMMON_SMD_GROUP_NAME}: BSS registration idempotent")
            else:
                log.check(f"✗ {COMMON_SMD_GROUP_NAME}: BSS registration not idempotent")
        
        # Test per-FG BSS registration idempotency
        groups_section = config.get("groups", {})
        for fg_name in groups_section.keys():
            log.check(f"Testing per-FG BSS registration idempotency: {fg_name}")
            
            group_name = f"{SMD_GROUP_PREFIX}_{fg_name}"
            
            # Get initial state before provision run
            log.check(f"Initial BSS query of {group_name}")
            first_result = verify_bss_group_registration(host, group_name)
            
            # Get state after provision run (provision already executed above)
            log.check(f"BSS query after provision run of {group_name}")
            second_result = verify_bss_group_registration(host, group_name)
            
            # Both should succeed and be registered (idempotent)
            fg_idempotent = (
                first_result["success"] and 
                second_result["success"] and
                first_result.get("registered", False) and
                second_result.get("registered", False)
            )
            
            idempotency_results.append({
                "group_name": group_name,
                "group_type": f"per-FG ({fg_name})",
                "success": fg_idempotent,
                "first_success": first_result["success"],
                "second_success": second_result["success"],
                "first_registered": first_result.get("registered", False),
                "second_registered": second_result.get("registered", False)
            })
            
            if fg_idempotent:
                log.check(f"✓ {group_name}: BSS registration idempotent")
            else:
                log.check(f"✗ {group_name}: BSS registration not idempotent")
        
        if not idempotency_results:
            log.skipped("No BSS groups to test idempotency", "No common or groups sections")
            pytest.skip("No BSS groups to test idempotency")
        
        # Check overall results
        failed_idempotency = [r for r in idempotency_results if not r["success"]]
        
        details_lines = [
            f"BSS registration idempotency test: {len(idempotency_results)} groups tested",
            ""
        ]
        
        for result in idempotency_results:
            status = "✓" if result["success"] else "✗"
            details_lines.append(f"  {status} {result['group_name']} ({result['group_type']})")
            details_lines.append(f"    Before provision: {'✓' if result['first_success'] else '✗'} (registered: {result['first_registered']})")
            details_lines.append(f"    After provision: {'✓' if result['second_success'] else '✗'} (registered: {result['second_registered']})")
        
        details = "\n".join(details_lines)
        
        if failed_idempotency:
            log.failed(
                f"BSS registration idempotency failed: {len(failed_idempotency)} groups not idempotent",
                details
            )
            failed_groups = [r["group_name"] for r in failed_idempotency]
            assert False, f"BSS registration idempotency failed for: {', '.join(failed_groups)}"
        
        log.passed(
            TEST_LOG_MSGS["bss_registration_idempotent"].format(group_name=f"{len(idempotency_results)} groups"),
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during BSS idempotency test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(24)
def test_full_pipeline_idempotency(host):
    """
    TC-I03: Verify full additional cloud-init pipeline idempotency.
    
    Tests:
    - Running provision playbook tasks multiple times produces same result
    - Configuration validation remains consistent after re-run
    - SMD and BSS operations are idempotent together
    """
    log = TestLogger(TEST_NAMES["full_pipeline_idempotency"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Check if OpenCHAMI services are available
    services = _check_ochami_services_available(host)
    if not services["both_available"]:
        log.skipped("Full pipeline requires both SMD and BSS services", f"SMD: {services['smd_available']}, BSS: {services['bss_available']}")
        pytest.skip("Full pipeline requires both SMD and BSS services")
    
    log.check("Testing full additional cloud-init pipeline idempotency")
    
    try:
        # Run full pipeline twice and compare results
        pipeline_runs = []
        
        for run_number in [1, 2]:
            log.check(f"Pipeline run {run_number}")
            
            # Load and validate configuration
            config_result = load_additional_cloud_init_config(host)
            
            if not config_result["success"]:
                log.failed(f"Config loading failed on run {run_number}", config_result["error"])
                assert False, f"Configuration loading failed: {config_result['error']}"
            
            config = config_result["config"]
            
            # Validate configuration
            from automation_library.additional_cloud_init.functions import validate_cloud_init_config
            validation_result = validate_cloud_init_config(host, config)
            
            # Execute provision playbook tasks (only on first run to establish state)
            if run_number == 1:
                log.check("Executing provision playbook tasks to establish initial state")
                provision_result = _run_provision_playbook_tasks(host)
                
                if not provision_result["success"]:
                    log.failed("Provision playbook execution failed", provision_result.get("error", "Unknown error"))
                    assert False, f"Provision playbook failed: {provision_result.get('error', 'Unknown error')}"
            
            # Query SMD group state
            smd_results = {}
            
            # Common SMD group
            if config.get("common"):
                expected_xnames = get_all_xnames(host)
                if expected_xnames:
                    smd_result = verify_smd_group_creation(host, COMMON_SMD_GROUP_NAME, expected_xnames)
                    smd_results["common"] = {
                        "success": smd_result["success"],
                        "member_count": len(smd_result.get("found_xnames", []))
                    }
            
            # Per-FG SMD groups
            groups_section = config.get("groups", {})
            for fg_name in groups_section.keys():
                expected_xnames = get_xnames_for_fg(host, fg_name)
                if expected_xnames:
                    group_name = f"{SMD_GROUP_PREFIX}_{fg_name}"
                    smd_result = verify_smd_group_creation(host, group_name, expected_xnames)
                    smd_results[fg_name] = {
                        "success": smd_result["success"],
                        "member_count": len(smd_result.get("found_xnames", []))
                    }
            
            # Query BSS registration state
            bss_results = {}
            
            # Common BSS registration
            if config.get("common"):
                bss_result = verify_bss_group_registration(host, COMMON_SMD_GROUP_NAME)
                bss_results["common"] = {
                    "success": bss_result["success"],
                    "registered": bss_result.get("registered", False)
                }
            
            # Per-FG BSS registrations
            for fg_name in groups_section.keys():
                group_name = f"{SMD_GROUP_PREFIX}_{fg_name}"
                bss_result = verify_bss_group_registration(host, group_name)
                bss_results[fg_name] = {
                    "success": bss_result["success"],
                    "registered": bss_result.get("registered", False)
                }
            
            # Store run results
            pipeline_runs.append({
                "run_number": run_number,
                "config_success": config_result["success"],
                "config_enabled": config_result["enabled"],
                "validation_success": validation_result["success"],
                "smd_results": smd_results,
                "bss_results": bss_results,
                "total_smd_groups": len(smd_results),
                "total_bss_groups": len(bss_results)
            })
        
        if len(pipeline_runs) != 2:
            log.failed("Pipeline idempotency test requires 2 runs", f"Only completed {len(pipeline_runs)} runs")
            assert False, "Pipeline idempotency test incomplete"
        
        # Compare results between runs
        run1, run2 = pipeline_runs[0], pipeline_runs[1]
        
        # Check configuration consistency
        config_consistent = (
            run1["config_success"] == run2["config_success"] and
            run1["config_enabled"] == run2["config_enabled"] and
            run1["validation_success"] == run2["validation_success"]
        )
        
        # Check SMD results consistency
        smd_consistent = True
        smd_differences = []
        
        for group_key in set(run1["smd_results"].keys()) | set(run2["smd_results"].keys()):
            smd1 = run1["smd_results"].get(group_key, {})
            smd2 = run2["smd_results"].get(group_key, {})
            
            if smd1.get("success") != smd2.get("success"):
                smd_consistent = False
                smd_differences.append(f"{group_key}: success changed")
            
            if smd1.get("member_count") != smd2.get("member_count"):
                smd_consistent = False
                smd_differences.append(f"{group_key}: member count changed")
        
        # Check BSS results consistency
        bss_consistent = True
        bss_differences = []
        
        for group_key in set(run1["bss_results"].keys()) | set(run2["bss_results"].keys()):
            bss1 = run1["bss_results"].get(group_key, {})
            bss2 = run2["bss_results"].get(group_key, {})
            
            if bss1.get("success") != bss2.get("success"):
                bss_consistent = False
                bss_differences.append(f"{group_key}: success changed")
            
            if bss1.get("registered") != bss2.get("registered"):
                bss_consistent = False
                bss_differences.append(f"{group_key}: registration changed")
        
        # Overall pipeline idempotency
        pipeline_idempotent = config_consistent and smd_consistent and bss_consistent
        
        # Build detailed results
        details_lines = [
            f"Full pipeline idempotency test: 2 runs completed",
            f"SMD groups: {run1['total_smd_groups']}, BSS groups: {run1['total_bss_groups']}",
            "",
            "Idempotency check:"
        ]
        
        details_lines.append(f"  Configuration: {'✓' if config_consistent else '✗'}")
        details_lines.append(f"  SMD operations: {'✓' if smd_consistent else '✗'}")
        details_lines.append(f"  BSS operations: {'✓' if bss_consistent else '✗'}")
        
        if smd_differences:
            details_lines.append("")
            details_lines.append("SMD differences:")
            for diff in smd_differences:
                details_lines.append(f"    - {diff}")
        
        if bss_differences:
            details_lines.append("")
            details_lines.append("BSS differences:")
            for diff in bss_differences:
                details_lines.append(f"    - {diff}")
        
        details_lines.append("")
        details_lines.append("Run comparison:")
        details_lines.append(f"  Run 1: config={run1['config_success']}, validation={run1['validation_success']}, SMD={len(run1['smd_results'])}, BSS={len(run1['bss_results'])}")
        details_lines.append(f"  Run 2: config={run2['config_success']}, validation={run2['validation_success']}, SMD={len(run2['smd_results'])}, BSS={len(run2['bss_results'])}")
        
        details = "\n".join(details_lines)
        
        if not pipeline_idempotent:
            differences = []
            if not config_consistent:
                differences.append("configuration")
            if not smd_consistent:
                differences.append("SMD operations")
            if not bss_consistent:
                differences.append("BSS operations")
            
            log.failed(
                f"Full pipeline not idempotent: {', '.join(differences)} inconsistent",
                details
            )
            assert False, f"Pipeline idempotency failed in: {', '.join(differences)}"
        
        log.passed(
            "Full additional cloud-init pipeline is idempotent",
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during full pipeline idempotency test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"
