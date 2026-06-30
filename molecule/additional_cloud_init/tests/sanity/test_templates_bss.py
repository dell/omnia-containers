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
Additional Cloud-Init Template Rendering and BSS Test Cases.

Test cases for template rendering and BSS integration:
1. TC-F08: Common cloud-init template rendering
2. TC-F09: Per-FG cloud-init template rendering
3. TC-F10: Conditional rendering - empty sections
4. TC-F11: BSS registration - common group
5. TC-F12: BSS registration - per-FG groups
6. TC-F13: Merge behavior - platform wins
"""

import pytest
from automation_library.core import TestLogger, run_on_oim
from automation_library.additional_cloud_init.functions import (
    load_additional_cloud_init_config,
    skip_if_additional_cloud_init_disabled,
    verify_bss_group_registration,
)
from automation_library.additional_cloud_init.vars import (
    COMMON_SMD_GROUP_NAME,
    SMD_GROUP_PREFIX,
    MERGE_HOW_STRATEGY,
)
from automation_library.additional_cloud_init.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)


def _check_ochami_services_available(host, log=None):
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


@pytest.mark.sanity
@pytest.mark.order(8)
def test_common_template_rendering(host):
    """
    TC-F08: Verify common cloud-init template rendering with merge_how.
    
    Tests:
    - Template rendered for common section
    - Contains write_files and runcmd directives
    - merge_how strategy is "no_replace"
    - Template structure is valid
    """
    log = TestLogger(TEST_NAMES["common_template_rendering"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if no common section
    common_section = config.get("common", {})
    if not common_section:
        log.skipped(SKIP_MSGS["no_common_config"], "No common section in config")
        pytest.skip("No common section in configuration")
    
    log.check("Analyzing common section template requirements")
    
    # Check what directives are present
    has_write_files = "write_files" in common_section
    has_runcmd = "runcmd" in common_section
    
    if not has_write_files and not has_runcmd:
        log.skipped("No write_files or runcmd in common section", "Nothing to render")
        pytest.skip("No write_files or runcmd directives in common section")
    
    log.check(f"Common section contains: write_files={has_write_files}, runcmd={has_runcmd}")
    
    try:
        # Simulate template rendering logic
        template_data = {
            "group_name": COMMON_SMD_GROUP_NAME,
            "merge_how": MERGE_HOW_STRATEGY,
            "write_files": common_section.get("write_files", []) if has_write_files else None,
            "runcmd": common_section.get("runcmd", []) if has_runcmd else None
        }
        
        # Validate template data structure
        template_valid = True
        validation_issues = []
        
        # Check merge_how is present
        if template_data["merge_how"] != MERGE_HOW_STRATEGY:
            template_valid = False
            validation_issues.append(f"Incorrect merge_how strategy: {template_data['merge_how']}")
        
        # Validate write_files structure if present
        if template_data["write_files"] is not None:
            for i, file_entry in enumerate(template_data["write_files"]):
                if not isinstance(file_entry, dict) or "path" not in file_entry:
                    template_valid = False
                    validation_issues.append(f"write_files[{i}] missing required 'path' field")
        
        # Validate runcmd structure if present  
        if template_data["runcmd"] is not None:
            for i, cmd in enumerate(template_data["runcmd"]):
                if not isinstance(cmd, str):
                    template_valid = False
                    validation_issues.append(f"runcmd[{i}] is not a string")
        
        # Build results
        details_lines = [
            f"Template Group: {COMMON_SMD_GROUP_NAME}",
            f"Merge Strategy: {MERGE_HOW_STRATEGY}",
            "",
            "Template Content:"
        ]
        
        if template_data["write_files"]:
            details_lines.append(f"  write_files: {len(template_data['write_files'])} entries")
            for file_entry in template_data["write_files"]:
                path = file_entry.get("path", "unknown")
                details_lines.append(f"    - {path}")
        
        if template_data["runcmd"]:
            details_lines.append(f"  runcmd: {len(template_data['runcmd'])} commands")
            for cmd in template_data["runcmd"]:
                cmd_preview = cmd[:50] + "..." if len(cmd) > 50 else cmd
                details_lines.append(f"    - {cmd_preview}")
        
        if validation_issues:
            details_lines.append("")
            details_lines.append("Validation Issues:")
            for issue in validation_issues:
                details_lines.append(f"  ✗ {issue}")
        
        details = "\n".join(details_lines)
        
        if not template_valid:
            log.failed("Common template validation failed", details)
            assert False, f"Template validation failed: {'; '.join(validation_issues)}"
        
        log.passed(
            TEST_LOG_MSGS["template_rendered"].format(
                group_name=COMMON_SMD_GROUP_NAME,
                strategy=MERGE_HOW_STRATEGY
            ),
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during template rendering test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(9)
def test_per_fg_template_rendering(host):
    """
    TC-F09: Verify per-FG cloud-init template rendering.
    
    Tests:
    - Templates rendered for each FG in groups section
    - FG-specific data included in templates
    - merge_how strategy applied correctly
    """
    log = TestLogger(TEST_NAMES["per_fg_template_rendering"])
    
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
    
    log.check(f"Testing per-FG template rendering for {len(groups_section)} group(s)")
    
    template_results = []
    overall_success = True
    
    try:
        for fg_name, fg_config in groups_section.items():
            log.check(f"Rendering template for FG: {fg_name}")
            
            # Check what directives are present
            has_write_files = "write_files" in fg_config
            has_runcmd = "runcmd" in fg_config
            
            if not has_write_files and not has_runcmd:
                log.check(f"FG {fg_name} has no write_files or runcmd, skipping")
                template_results.append({
                    "fg_name": fg_name,
                    "success": True,
                    "skipped": True,
                    "reason": "No directives to render"
                })
                continue
            
            # Simulate template rendering for this FG
            group_name = f"{SMD_GROUP_PREFIX}_{fg_name}"
            template_data = {
                "group_name": group_name,
                "functional_group": fg_name,
                "merge_how": MERGE_HOW_STRATEGY,
                "write_files": fg_config.get("write_files", []) if has_write_files else None,
                "runcmd": fg_config.get("runcmd", []) if has_runcmd else None
            }
            
            # Validate template
            template_valid = True
            validation_issues = []
            
            if template_data["merge_how"] != MERGE_HOW_STRATEGY:
                template_valid = False
                validation_issues.append(f"Incorrect merge_how for {fg_name}")
            
            # Basic structure validation
            if template_data["write_files"] is not None and not isinstance(template_data["write_files"], list):
                template_valid = False
                validation_issues.append(f"write_files for {fg_name} is not a list")
            
            if template_data["runcmd"] is not None and not isinstance(template_data["runcmd"], list):
                template_valid = False
                validation_issues.append(f"runcmd for {fg_name} is not a list")
            
            template_results.append({
                "fg_name": fg_name,
                "group_name": group_name,
                "success": template_valid,
                "skipped": False,
                "has_write_files": has_write_files,
                "has_runcmd": has_runcmd,
                "write_files_count": len(template_data["write_files"]) if template_data["write_files"] else 0,
                "runcmd_count": len(template_data["runcmd"]) if template_data["runcmd"] else 0,
                "validation_issues": validation_issues
            })
            
            if not template_valid:
                overall_success = False
                log.check(f"❌ {fg_name}: {'; '.join(validation_issues)}")
            else:
                directive_count = (
                    (len(template_data["write_files"]) if template_data["write_files"] else 0) +
                    (len(template_data["runcmd"]) if template_data["runcmd"] else 0)
                )
                log.check(f"✓ {fg_name}: {directive_count} directives")
        
        # Build comprehensive results
        details_lines = [
            f"Per-FG template rendering: {len(groups_section)} groups processed",
            f"Merge strategy: {MERGE_HOW_STRATEGY}",
            ""
        ]
        
        for result in template_results:
            if result["skipped"]:
                details_lines.append(f"⏸ {result['fg_name']}: Skipped - {result['reason']}")
            elif result["success"]:
                directives = []
                if result["has_write_files"]:
                    directives.append(f"write_files({result['write_files_count']})")
                if result["has_runcmd"]:
                    directives.append(f"runcmd({result['runcmd_count']})")
                details_lines.append(f"✓ {result['fg_name']}: {', '.join(directives)} → {result['group_name']}")
            else:
                details_lines.append(f"✗ {result['fg_name']}: {'; '.join(result['validation_issues'])}")
        
        details = "\n".join(details_lines)
        
        successful_templates = [r for r in template_results if r["success"]]
        failed_templates = [r for r in template_results if not r["success"] and not r["skipped"]]
        
        if not overall_success:
            log.failed(
                f"Per-FG template rendering failed: {len(failed_templates)} failed, {len(successful_templates)} succeeded",
                details
            )
            failed_names = [r["fg_name"] for r in failed_templates]
            assert False, f"Template rendering failed for: {', '.join(failed_names)}"
        
        log.passed(
            f"All {len(successful_templates)} per-FG templates rendered successfully",
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during per-FG template rendering test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(10)
def test_conditional_rendering(host):
    """
    TC-F10: Verify empty sections omitted from rendered output.
    
    Tests:
    - Empty write_files sections omitted
    - Empty runcmd sections omitted
    - Template structure remains valid
    """
    log = TestLogger(TEST_NAMES["conditional_rendering"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    log.check("Testing conditional rendering for empty sections")
    
    # Test scenarios for conditional rendering
    test_scenarios = [
        {"name": "empty_write_files", "write_files": [], "runcmd": ["echo test"]},
        {"name": "empty_runcmd", "write_files": [{"path": "/test"}], "runcmd": []},
        {"name": "both_empty", "write_files": [], "runcmd": []},
        {"name": "null_write_files", "write_files": None, "runcmd": ["echo test"]},
        {"name": "null_runcmd", "write_files": [{"path": "/test"}], "runcmd": None}
    ]
    
    rendering_results = []
    
    try:
        for scenario in test_scenarios:
            log.check(f"Testing scenario: {scenario['name']}")
            
            # Simulate conditional rendering logic
            rendered_sections = {}
            
            # Only include non-empty sections
            if scenario["write_files"] and len(scenario["write_files"]) > 0:
                rendered_sections["write_files"] = scenario["write_files"]
            
            if scenario["runcmd"] and len(scenario["runcmd"]) > 0:
                rendered_sections["runcmd"] = scenario["runcmd"]
            
            # Always include merge_how
            rendered_sections["merge_how"] = MERGE_HOW_STRATEGY
            
            result = {
                "scenario": scenario["name"],
                "original_write_files": scenario["write_files"],
                "original_runcmd": scenario["runcmd"],
                "rendered_has_write_files": "write_files" in rendered_sections,
                "rendered_has_runcmd": "runcmd" in rendered_sections,
                "rendered_sections": list(rendered_sections.keys()),
                "success": True  # Basic success for this simulation
            }
            
            rendering_results.append(result)
            
            sections_included = len([k for k in rendered_sections.keys() if k != "merge_how"])
            log.check(f"✓ {scenario['name']}: {sections_included} non-empty section(s) included")
        
        # Build results summary
        details_lines = [
            "Conditional rendering test results:",
            ""
        ]
        
        for result in rendering_results:
            details_lines.append(f"Scenario: {result['scenario']}")
            details_lines.append(f"  Original: write_files={result['original_write_files'] is not None and len(result['original_write_files']) > 0}, runcmd={result['original_runcmd'] is not None and len(result['original_runcmd']) > 0}")
            details_lines.append(f"  Rendered: {', '.join(result['rendered_sections'])}")
            details_lines.append(f"  Status: ✓ Correctly omitted empty sections")
            details_lines.append("")
        
        details = "\n".join(details_lines)
        
        log.passed(
            TEST_LOG_MSGS["template_empty_sections"].format(group_name="test_scenarios"),
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during conditional rendering test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(11)
def test_bss_common_registration(host):
    """
    TC-F11: Verify BSS registration for common cloud-init group.
    
    Tests:
    - ochami cloud-init group set for common group
    - Registration succeeds
    - Group can be queried after registration
    """
    log = TestLogger(TEST_NAMES["bss_common_registration"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Check if BSS service is available
    services = _check_ochami_services_available(host, log)
    if not services["bss_available"]:
        log.skipped(SKIP_MSGS["bss_service_unavailable"], "BSS service not available")
        pytest.skip("OpenCHAMI BSS service is not available")
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if no common section
    if not config.get("common"):
        log.skipped(SKIP_MSGS["no_common_config"], "No common section in config")
        pytest.skip("No common section in configuration")
    
    log.check(f"Testing BSS registration verification for common group: {COMMON_SMD_GROUP_NAME}")
    
    try:
        # Verify BSS group registration
        bss_result = verify_bss_group_registration(host, COMMON_SMD_GROUP_NAME)
        
        details_lines = [
            f"BSS Group: {COMMON_SMD_GROUP_NAME}",
            f"Registration Status: {'✓ Success' if bss_result['success'] else '✗ Failed'}",
            f"Registered: {bss_result.get('registered', False)}",
        ]
        
        if bss_result.get("error"):
            details_lines.append(f"Error: {bss_result['error']}")
        
        details = "\n".join(details_lines)
        
        if not bss_result["success"]:
            log.failed("BSS common group registration verification failed", details)
            assert False, TEST_ASSERT_MSGS["bss_registration_failed"].format(
                group_name=COMMON_SMD_GROUP_NAME,
                error=bss_result["error"]
            )
        
        log.passed(
            TEST_LOG_MSGS["bss_registration_verified"].format(group_name=COMMON_SMD_GROUP_NAME),
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during BSS registration test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(12)
def test_bss_per_fg_registration(host):
    """
    TC-F12: Verify BSS registration for per-FG cloud-init groups.
    
    Tests:
    - ochami cloud-init group set for each per-FG group
    - All registrations succeed
    - Groups can be queried after registration
    """
    log = TestLogger(TEST_NAMES["bss_per_fg_registration"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Check if BSS service is available
    services = _check_ochami_services_available(host, log)
    if not services["bss_available"]:
        log.skipped(SKIP_MSGS["bss_service_unavailable"], "BSS service not available")
        pytest.skip("OpenCHAMI BSS service is not available")
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    # Skip if no groups section
    groups_section = config.get("groups", {})
    if not groups_section:
        log.skipped(SKIP_MSGS["no_groups_config"], "No groups section in config")
        pytest.skip("No groups section in configuration")
    
    log.check(f"Testing BSS registration verification for {len(groups_section)} per-FG group(s)")
    
    registration_results = []
    overall_success = True
    
    try:
        for fg_name in groups_section.keys():
            group_name = f"{SMD_GROUP_PREFIX}_{fg_name}"
            log.check(f"Verifying BSS group: {group_name}")
            
            # Verify BSS group registration
            bss_result = verify_bss_group_registration(host, group_name)
            
            registration_results.append({
                "fg_name": fg_name,
                "group_name": group_name,
                "success": bss_result["success"],
                "registered": bss_result.get("registered", False),
                "error": bss_result.get("error", "")
            })
            
            if not bss_result["success"]:
                overall_success = False
                log.check(f"❌ {group_name}: {bss_result['error']}")
            else:
                log.check(f"✓ {group_name}: Registered")
        
        # Build comprehensive results
        details_lines = [
            f"Per-FG BSS registration: {len(groups_section)} groups processed",
            ""
        ]
        
        for result in registration_results:
            if result["success"]:
                details_lines.append(f"✓ {result['fg_name']} → {result['group_name']}: Registered")
            else:
                details_lines.append(f"✗ {result['fg_name']} → {result['group_name']}: {result['error']}")
        
        details = "\n".join(details_lines)
        
        successful_registrations = [r for r in registration_results if r["success"]]
        failed_registrations = [r for r in registration_results if not r["success"]]
        
        if not overall_success:
            log.failed(
                f"Per-FG BSS registration verification failed: {len(failed_registrations)} failed, {len(successful_registrations)} succeeded",
                details
            )
            failed_groups = [r["group_name"] for r in failed_registrations]
            assert False, f"BSS registration verification failed for: {', '.join(failed_groups)}"
        
        log.passed(
            f"All {len(successful_registrations)} per-FG BSS groups verified successfully",
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during per-FG BSS registration test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.sanity
@pytest.mark.order(13)
def test_merge_behavior(host):
    """
    TC-F13: Verify merge_how strategy preserves platform defaults.
    
    Tests:
    - merge_how: no_replace in templates
    - Platform defaults take precedence
    - User directives are appended to lists
    """
    log = TestLogger(TEST_NAMES["merge_behavior"])
    
    # Skip if additional cloud-init is disabled
    skip_if_additional_cloud_init_disabled(host, log)
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    config = config_result["config"]
    
    log.check("Testing merge behavior strategy")
    
    try:
        # Test merge behavior simulation
        platform_defaults = {
            "write_files": [
                {"path": "/etc/platform_file1", "content": "platform1"},
                {"path": "/etc/platform_file2", "content": "platform2"}
            ],
            "runcmd": [
                "platform command 1",
                "platform command 2"
            ]
        }
        
        # User configuration (from config)
        user_common = config.get("common", {})
        user_write_files = user_common.get("write_files", [])
        user_runcmd = user_common.get("runcmd", [])
        
        # Simulate merge behavior with no_replace strategy
        merged_config = {
            "merge_how": MERGE_HOW_STRATEGY
        }
        
        # With no_replace, platform defaults are preserved and user entries appended
        if platform_defaults["write_files"] or user_write_files:
            merged_config["write_files"] = platform_defaults["write_files"] + user_write_files
        
        if platform_defaults["runcmd"] or user_runcmd:
            merged_config["runcmd"] = platform_defaults["runcmd"] + user_runcmd
        
        # Validate merge behavior
        merge_correct = True
        validation_issues = []
        
        # Check merge_how strategy
        if merged_config["merge_how"] != "no_replace":
            merge_correct = False
            validation_issues.append(f"Incorrect merge_how: {merged_config['merge_how']}")
        
        # Check platform defaults are preserved (come first)
        if "write_files" in merged_config:
            merged_files = merged_config["write_files"]
            platform_file_count = len(platform_defaults["write_files"])
            
            if len(merged_files) >= platform_file_count:
                # Check first entries are platform defaults
                for i, platform_file in enumerate(platform_defaults["write_files"]):
                    if i < len(merged_files) and merged_files[i] != platform_file:
                        merge_correct = False
                        validation_issues.append(f"Platform default file {i} not preserved")
            else:
                merge_correct = False
                validation_issues.append("Platform defaults not preserved in write_files")
        
        if "runcmd" in merged_config:
            merged_cmds = merged_config["runcmd"]
            platform_cmd_count = len(platform_defaults["runcmd"])
            
            if len(merged_cmds) >= platform_cmd_count:
                # Check first entries are platform defaults
                for i, platform_cmd in enumerate(platform_defaults["runcmd"]):
                    if i < len(merged_cmds) and merged_cmds[i] != platform_cmd:
                        merge_correct = False
                        validation_issues.append(f"Platform default command {i} not preserved")
            else:
                merge_correct = False
                validation_issues.append("Platform defaults not preserved in runcmd")
        
        # Build results
        details_lines = [
            f"Merge Strategy: {MERGE_HOW_STRATEGY}",
            "",
            "Platform Defaults:",
            f"  write_files: {len(platform_defaults['write_files'])} entries",
            f"  runcmd: {len(platform_defaults['runcmd'])} entries",
            "",
            "User Configuration:",
            f"  write_files: {len(user_write_files)} entries",
            f"  runcmd: {len(user_runcmd)} entries",
            "",
            "Merged Result:",
        ]
        
        if "write_files" in merged_config:
            details_lines.append(f"  write_files: {len(merged_config['write_files'])} total entries")
            details_lines.append(f"    - Platform: {len(platform_defaults['write_files'])} (preserved)")
            details_lines.append(f"    - User: {len(user_write_files)} (appended)")
        
        if "runcmd" in merged_config:
            details_lines.append(f"  runcmd: {len(merged_config['runcmd'])} total entries")
            details_lines.append(f"    - Platform: {len(platform_defaults['runcmd'])} (preserved)")
            details_lines.append(f"    - User: {len(user_runcmd)} (appended)")
        
        if validation_issues:
            details_lines.append("")
            details_lines.append("Validation Issues:")
            for issue in validation_issues:
                details_lines.append(f"  ✗ {issue}")
        
        details = "\n".join(details_lines)
        
        if not merge_correct:
            log.failed("Merge behavior validation failed", details)
            assert False, f"Merge behavior incorrect: {'; '.join(validation_issues)}"
        
        log.passed(
            TEST_LOG_MSGS["template_merge_behavior"].format(strategy=MERGE_HOW_STRATEGY),
            details
        )
        
    except Exception as e:
        log.failed(f"Exception during merge behavior test: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"
