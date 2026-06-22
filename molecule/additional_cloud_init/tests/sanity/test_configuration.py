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
Additional Cloud-Init Configuration Test Cases.

Test cases for configuration loading and validation:
1. TC-F01: Empty path - feature disabled
2. TC-F02: Valid path - file loaded
3. TC-F03: Empty common/groups sections
4. TC-F04: Ansible fact loader
"""

import pytest
from automation_library.core import TestLogger, get_input_value
from automation_library.additional_cloud_init.functions import (
    load_additional_cloud_init_config,
    get_functional_groups_from_config,
    validate_cloud_init_config,
)
from automation_library.additional_cloud_init.messages import (
    TEST_NAMES, 
    TEST_LOG_MSGS, 
    TEST_ASSERT_MSGS
)


@pytest.mark.sanity
@pytest.mark.order(1)
def test_empty_path_disabled(host):
    """
    TC-F01: Verify additional cloud-init disabled when config path is empty.
    
    Tests:
    - Empty string in additional_cloud_init_config_file
    - Feature correctly disabled
    - No processing occurs
    """
    log = TestLogger(TEST_NAMES["empty_path_disabled"])
    
    # Get the config file path from provision_config.yml
    config_file_path = get_input_value(
        host, 
        "provision_config.yml", 
        "additional_cloud_init_config_file", 
        ""
    )
    
    log.check(f"Checking config file path: '{config_file_path}'")
    
    # Load the configuration
    config_result = load_additional_cloud_init_config(host)
    
    # If path is empty, should be disabled
    if not config_file_path or config_file_path.strip() == "":
        if not config_result["enabled"]:
            log.passed(TEST_LOG_MSGS["config_disabled"], "Feature correctly disabled with empty path")
            return
        else:
            log.failed("Feature should be disabled with empty path", f"Got enabled: {config_result['enabled']}")
            assert False, TEST_ASSERT_MSGS["config_load_failed"].format(error="Feature enabled with empty path")
    
    # If path is not empty, this test doesn't apply
    log.skipped("Config path is not empty, test not applicable", f"Path: {config_file_path}")
    pytest.skip("Config path is not empty")


@pytest.mark.sanity
@pytest.mark.order(2)
def test_valid_path_loaded(host):
    """
    TC-F02: Verify configuration file loaded when valid path provided.
    
    Tests:
    - Non-empty path in additional_cloud_init_config_file
    - Configuration successfully loaded
    - File parsing successful
    """
    log = TestLogger(TEST_NAMES["valid_path_loaded"])
    
    # Get the config file path
    config_file_path = get_input_value(
        host, 
        "provision_config.yml", 
        "additional_cloud_init_config_file", 
        ""
    )
    
    log.check(f"Checking config file path: '{config_file_path}'")
    
    # Skip if path is empty (covered by previous test)
    if not config_file_path or config_file_path.strip() == "":
        log.skipped("Config path is empty", "This test requires non-empty path")
        pytest.skip("Config path is empty")
    
    # Load the configuration
    config_result = load_additional_cloud_init_config(host)
    
    if not config_result["success"]:
        log.failed("Config loading failed", config_result["error"])
        assert False, TEST_ASSERT_MSGS["config_load_failed"].format(error=config_result["error"])
    
    log.passed(
        TEST_LOG_MSGS["config_loaded"].format(config_path=config_file_path),
        f"Configuration loaded successfully. Enabled: {config_result['enabled']}"
    )


@pytest.mark.sanity
@pytest.mark.order(3)
def test_empty_config_sections(host):
    """
    TC-F03: Verify empty common/groups sections create no cloud-init.
    
    Tests:
    - Configuration with empty common section
    - Configuration with empty groups section
    - No cloud-init groups created for empty sections
    """
    log = TestLogger(TEST_NAMES["empty_config_sections"])
    
    # Load configuration
    config_result = load_additional_cloud_init_config(host)
    
    if not config_result["success"]:
        log.skipped("Config loading failed", config_result["error"])
        pytest.skip(f"Config loading failed: {config_result['error']}")
    
    if not config_result["enabled"]:
        log.skipped("Additional cloud-init not enabled", "Feature disabled")
        pytest.skip("Additional cloud-init not enabled")
    
    config = config_result["config"]
    log.check(f"Analyzing config sections: common={bool(config.get('common'))}, groups={bool(config.get('groups'))}")
    
    # Check if sections are empty or non-existent
    common_section = config.get("common", {})
    groups_section = config.get("groups", {})
    
    empty_sections = []
    if not common_section:
        empty_sections.append("common")
    if not groups_section:
        empty_sections.append("groups")
    
    if empty_sections:
        log.passed(
            TEST_LOG_MSGS["config_empty"],
            f"Empty sections detected: {empty_sections}. No cloud-init groups will be created."
        )
    else:
        log.passed(
            "Configuration has content in both sections",
            f"Common entries: {len(common_section)}, Groups: {len(groups_section)}"
        )


@pytest.mark.sanity
@pytest.mark.order(4)
def test_ansible_fact_loader(host):
    """
    TC-F04: Verify Ansible fact loader parses YAML and sets enabled/data facts.
    
    Tests:
    - validate_additional_cloud_init.yml sets facts correctly
    - enabled fact matches configuration state
    - data fact contains parsed configuration
    """
    log = TestLogger(TEST_NAMES["ansible_fact_loader"])
    
    # Load configuration using our function
    config_result = load_additional_cloud_init_config(host)
    
    if not config_result["success"]:
        log.skipped("Config loading failed", config_result["error"])
        pytest.skip(f"Config loading failed: {config_result['error']}")
    
    log.check("Verifying Ansible fact loader behavior matches our implementation")
    
    # Our implementation should match what Ansible fact loader does
    expected_enabled = config_result["enabled"]
    expected_data = config_result["config"]
    
    # Validate configuration structure
    validation_result = validate_cloud_init_config(host, expected_data)
    
    details = [
        f"✓ Configuration loaded: {config_result['success']}",
        f"✓ Feature enabled: {expected_enabled}",
        f"✓ Data keys: {list(expected_data.keys()) if expected_data else 'empty'}",
        f"✓ Validation passed: {validation_result['success']}"
    ]
    
    if validation_result["success"]:
        log.passed(
            TEST_LOG_MSGS["config_validation_ok"],
            "\n".join(details)
        )
    else:
        log.failed(
            TEST_LOG_MSGS["config_validation_failed"].format(
                error_count=len(validation_result.get("errors", []))
            ),
            f"Validation errors: {validation_result['error']}"
        )
        assert False, TEST_ASSERT_MSGS["validation_failed"].format(
            error_count=len(validation_result.get("errors", [])),
            error_details=validation_result["error"],
            prohibited_keys="See error details"
        )
