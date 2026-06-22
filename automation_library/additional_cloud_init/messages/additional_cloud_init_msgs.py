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
Additional Cloud-Init Module - Messages.

Test names, log messages, and assertion messages for additional cloud-init tests.
"""

from typing import Dict

# =============================================================================
# TEST NAMES — displayed in reports and TestLogger
# =============================================================================

TEST_NAMES: Dict[str, str] = {
    # Functional test cases (TC-F01 to TC-F21)
    "empty_path_disabled": "Verify additional cloud-init disabled when config path is empty",
    "valid_path_loaded": "Verify configuration file loaded when valid path provided",
    "empty_config_sections": "Verify empty common/groups sections create no cloud-init",
    "ansible_fact_loader": "Verify Ansible fact loader parses YAML and sets enabled/data facts",
    "common_smd_group": "Verify common SMD group created with all XNAMEs",
    "per_fg_smd_group_single": "Verify per-FG SMD group created for single functional group",
    "per_fg_smd_group_multiple": "Verify multiple per-FG SMD groups created with correct filtering",
    "common_template_rendering": "Verify common cloud-init template rendering with merge_how",
    "per_fg_template_rendering": "Verify per-FG cloud-init template rendering",
    "conditional_rendering": "Verify empty sections omitted from rendered output",
    "bss_common_registration": "Verify BSS registration for common cloud-init group",
    "bss_per_fg_registration": "Verify BSS registration for per-FG cloud-init groups",
    "merge_behavior": "Verify merge_how strategy preserves platform defaults",
    "write_files_creation": "Verify write_files directive creates files on nodes",
    "runcmd_execution": "Verify runcmd directive executes commands on nodes",
    "end_to_end_common": "Verify end-to-end provisioning with common section only",
    "end_to_end_per_fg": "Verify end-to-end provisioning with per-FG section only",
    "end_to_end_combined": "Verify end-to-end provisioning with common and per-FG sections",
    "end_to_end_multiple_fgs": "Verify end-to-end provisioning with multiple functional groups",
    "end_to_end_mixed_directives": "Verify end-to-end provisioning with write_files and runcmd",
    "packages_integration": "Verify integration with additional_packages.json",
    
    # Error handling test cases (TC-E01 to TC-E15)
    "missing_config_file": "Verify error handling when config file does not exist",
    "invalid_yaml_syntax": "Verify error handling for invalid YAML syntax",
    "invalid_top_level_key": "Verify error handling for invalid top-level keys",
    "prohibited_key_common": "Verify error handling for prohibited keys in common section",
    "prohibited_key_groups": "Verify error handling for prohibited keys in groups section",
    "prohibited_key_packages": "Verify error handling for prohibited packages key",
    "unknown_allowed_key": "Verify error handling for unknown keys not in allowed set",
    "write_files_missing_path": "Verify error handling for write_files missing path",
    "runcmd_non_string": "Verify error handling for non-string runcmd entries",
    "invalid_fg_name": "Verify error handling for invalid functional group names",
    "write_files_not_list": "Verify error handling when write_files is not a list",
    "runcmd_not_list": "Verify error handling when runcmd is not a list",
    "empty_file_null_yaml": "Verify empty file (null YAML) treated as disabled",
    "multi_error_reporting": "Verify multi-error reporting in validation",
    "non_dict_root": "Verify error handling when config root is not a dictionary",
    
    # Idempotency test cases (TC-I01 to TC-I03)
    "smd_group_idempotency": "Verify SMD group creation idempotency",
    "bss_registration_idempotency": "Verify BSS registration idempotency",
    "full_pipeline_idempotency": "Verify full additional cloud-init pipeline idempotency",
    
    # Compatibility test cases (TC-C01 to TC-C03)
    "rhel_compatibility": "Verify additional cloud-init works on RHEL 10.x",
    "multiple_fgs_compatibility": "Verify compatibility with multiple functional groups",
    "upgrade_mode_compatibility": "Verify upgrade mode compatibility (skip delete/set)",
}

# =============================================================================
# LOG MESSAGES — for TestLogger during test execution
# =============================================================================

TEST_LOG_MSGS: Dict[str, str] = {
    # Configuration loading
    "config_disabled": "Additional cloud-init is disabled (empty config path)",
    "config_loaded": "Configuration loaded successfully from {config_path}",
    "config_empty": "Configuration file is empty, feature disabled",
    "config_validation_ok": "Configuration validation passed with no errors",
    "config_validation_failed": "{error_count} validation errors found",
    
    # Functional group processing
    "fgs_found": "Found {fg_count} functional groups in PXE mapping: {fg_list}",
    "common_applies_to": "Common section applies to {node_count} nodes across {fg_count} functional groups",
    "per_fg_applies_to": "Per-FG section applies to {node_count} nodes in functional group {fg_name}",
    
    # SMD group operations
    "smd_group_created": "SMD group '{group_name}' created with {member_count} members",
    "smd_group_deleted": "SMD group '{group_name}' deleted successfully",
    "smd_group_verified": "SMD group '{group_name}' verified with correct membership",
    "smd_group_idempotent": "SMD group '{group_name}' state is idempotent",
    
    # BSS operations
    "bss_group_registered": "BSS cloud-init group '{group_name}' registered successfully",
    "bss_registration_verified": "BSS registration for '{group_name}' verified",
    "bss_registration_idempotent": "BSS registration for '{group_name}' is idempotent",
    
    # Template rendering
    "template_rendered": "Cloud-init template rendered for '{group_name}' with merge_how {strategy}",
    "template_empty_sections": "Empty sections omitted from template for '{group_name}'",
    "template_merge_behavior": "Template preserves platform defaults with merge_how {strategy}",
    
    # Node verification
    "files_verified": "All {file_count} write_files verified on {node_count} nodes",
    "commands_verified": "All {command_count} runcmd commands verified on {node_count} nodes",
    "nodes_reachable": "{reachable_count}/{total_count} nodes reachable for verification",
    "cloud_init_completed": "Cloud-init completed successfully on {node_count} nodes",
    
    # Integration tests
    "integration_ok": "Integration test passed: {test_name}",
    "end_to_end_ok": "End-to-end test passed with {component_count} components verified",
    "packages_integration_ok": "Additional packages integration verified on {node_count} nodes",
    
    # Error conditions
    "validation_errors": "Validation failed with {error_count} error(s): {error_list}",
    "prohibited_keys_found": "Found {key_count} prohibited key(s): {key_list}",
    "invalid_fgs_found": "Found {fg_count} invalid functional group(s): {fg_list}",
}

# =============================================================================
# ASSERTION MESSAGES — shown when tests fail (include HOW TO FIX)
# =============================================================================

TEST_ASSERT_MSGS: Dict[str, str] = {
    "config_load_failed": (
        "Failed to load additional cloud-init configuration.\n"
        "Error: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Check provision_config.yml has correct additional_cloud_init_config_file path\n"
        "  2. Verify config file exists in datasets/project_default/\n"
        "  3. Validate YAML syntax: python -c 'import yaml; yaml.safe_load(open(\"<file>\"))'\n"
        "  4. Ensure file is readable and not empty"
    ),
    
    "validation_failed": (
        "Configuration validation failed.\n"
        "Errors found: {error_count}\n"
        "{error_details}\n\n"
        "HOW TO FIX:\n"
        "  1. Remove prohibited keys: {prohibited_keys}\n"
        "  2. Use only allowed keys: write_files, runcmd\n"
        "  3. Validate functional group names against PXE mapping\n"
        "  4. Ensure write_files entries have 'path' field\n"
        "  5. Ensure runcmd entries are strings"
    ),
    
    "smd_group_failed": (
        "SMD group creation/verification failed.\n"
        "Group: {group_name}\n"
        "Expected XNAMEs: {expected_count}\n"
        "Found XNAMEs: {found_count}\n"
        "Missing: {missing_xnames}\n"
        "Extra: {extra_xnames}\n\n"
        "HOW TO FIX:\n"
        "  1. Verify ochami SMD service is running\n"
        "  2. Check PXE mapping file has correct XNAMEs\n"
        "  3. Ensure nodes are discovered in SMD: ochami smd components get\n"
        "  4. Retry group creation: ochami smd groups post --group-name <name>\n"
        "  5. Check SMD database connectivity"
    ),
    
    "bss_registration_failed": (
        "BSS cloud-init group registration failed.\n"
        "Group: {group_name}\n"
        "Error: {error}\n\n"
        "HOW TO FIX:\n"
        "  1. Verify ochami BSS service is running\n"
        "  2. Check BSS connectivity: ochami cloud-init group list\n"
        "  3. Ensure cloud-init template is available\n"
        "  4. Retry registration: ochami cloud-init group set --name <name>\n"
        "  5. Check BSS database connectivity"
    ),
    
    "file_verification_failed": (
        "write_files verification failed on nodes.\n"
        "Failed nodes: {failed_nodes}\n"
        "Files not found: {missing_files}\n"
        "Permission mismatches: {permission_errors}\n"
        "Content mismatches: {content_errors}\n\n"
        "HOW TO FIX:\n"
        "  1. Check cloud-init completed: ssh root@<node> cloud-init status\n"
        "  2. Verify file exists: ssh root@<node> ls -la <file_path>\n"
        "  3. Check cloud-init logs: ssh root@<node> cat /var/log/cloud-init-output.log\n"
        "  4. Re-run provision playbook to apply cloud-init\n"
        "  5. Verify write_files syntax in additional_cloud_init.yml"
    ),
    
    "command_verification_failed": (
        "runcmd verification failed on nodes.\n"
        "Failed nodes: {failed_nodes}\n"
        "Commands not executed: {failed_commands}\n\n"
        "HOW TO FIX:\n"
        "  1. Check cloud-init completed: ssh root@<node> cloud-init status\n"
        "  2. Check command logs: ssh root@<node> cat /var/log/cloud-init-output.log\n"
        "  3. Verify command syntax in additional_cloud_init.yml\n"
        "  4. Check for command errors in /var/log/cloud-init.log\n"
        "  5. Re-run provision playbook to apply cloud-init"
    ),
    
    "functional_group_invalid": (
        "Invalid functional groups found in configuration.\n"
        "Invalid groups: {invalid_groups}\n"
        "Available groups: {available_groups}\n\n"
        "HOW TO FIX:\n"
        "  1. Check PXE mapping file: cat /opt/omnia/input/project_default/pxe_mapping_file.csv\n"
        "  2. Use only functional groups that exist in PXE mapping\n"
        "  3. Update additional_cloud_init.yml groups section\n"
        "  4. Verify node discovery completed: ochami smd components get"
    ),
    
    "node_unreachable": (
        "Nodes unreachable for verification.\n"
        "Unreachable nodes: {unreachable_nodes}\n"
        "Reachable nodes: {reachable_count}/{total_count}\n\n"
        "HOW TO FIX:\n"
        "  1. Check node connectivity: ping <admin_ip>\n"
        "  2. Verify SSH access: ssh root@<admin_ip> hostname\n"
        "  3. Check provision completed successfully\n"
        "  4. Verify cloud-init finished: ssh root@<admin_ip> cloud-init status\n"
        "  5. Re-run provision playbook if nodes failed"
    ),
    
    "integration_test_failed": (
        "Integration test failed.\n"
        "Failed components: {failed_components}\n"
        "Success rate: {success_count}/{total_count}\n\n"
        "HOW TO FIX:\n"
        "  1. Check individual component logs above\n"
        "  2. Verify all prerequisites are met\n"
        "  3. Check end-to-end provisioning flow\n"
        "  4. Validate configuration and template rendering\n"
        "  5. Re-run provision with additional cloud-init enabled"
    ),
}

# =============================================================================
# SKIP MESSAGES — for pytest.skip() calls
# =============================================================================

SKIP_MSGS: Dict[str, str] = {
    "additional_cloud_init_disabled": "Additional cloud-init is not enabled (empty or no config file)",
    "no_config_file": "No additional cloud-init config file specified in provision_config.yml",
    "empty_config": "Additional cloud-init config is empty or null",
    "no_functional_groups": "No functional groups found in PXE mapping file",
    "no_nodes_for_fg": "No nodes found for functional group {fg_name}",
    "no_common_config": "No common section in additional cloud-init config",
    "no_groups_config": "No groups section in additional cloud-init config",
    "no_write_files": "No write_files directive in configuration",
    "no_runcmd": "No runcmd directive in configuration",
    "smd_service_unavailable": "OpenCHAMI SMD service is not available",
    "bss_service_unavailable": "OpenCHAMI BSS service is not available",
    "upgrade_mode_active": "Upgrade mode is active, skipping delete/set operations",
    "lab_only_test": "Test marked as lab-only, requires physical hardware",
}
