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
Additional Cloud-Init Module - Validation Functions.

Validation functions for additional cloud-init configuration and constraints.
"""

import base64
import re
from typing import Dict, Any, List

from automation_library.core import run_in_container, get_functional_groups_from_pxe_mapping
from ..vars.common_vars import PROHIBITED_CLOUD_INIT_KEYS, ALLOWED_CLOUD_INIT_KEYS


def validate_cloud_init_config(host, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive L2 validation of additional cloud-init configuration.

    Args:
        host: Testinfra host object
        config: Configuration dictionary to validate

    Returns:
        Dict with success, error, and detailed validation results
    """
    errors = []
    
    try:
        # Validate top-level structure
        top_level_result = _validate_top_level_keys(config)
        if not top_level_result["success"]:
            errors.extend(top_level_result["errors"])
        
        # Validate common section if present
        if "common" in config:
            common_result = _validate_section_content(config["common"], "common")
            if not common_result["success"]:
                errors.extend(common_result["errors"])
        
        # Validate groups section if present
        if "groups" in config:
            groups_result = _validate_groups_section(host, config["groups"])
            if not groups_result["success"]:
                errors.extend(groups_result["errors"])
        
        success = len(errors) == 0
        
        return {
            "success": success,
            "error": "; ".join(errors) if errors else "",
            "errors": errors,
            "details": f"Validation {'passed' if success else 'failed'} with {len(errors)} error(s)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Validation exception: {str(e)}",
            "errors": [str(e)],
            "details": f"Exception during validation: {str(e)}"
        }


def _validate_top_level_keys(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate top-level keys are only 'common' or 'groups'."""
    allowed_top_level = {"common", "groups"}
    errors = []
    
    if not isinstance(config, dict):
        errors.append("Configuration root must be a dictionary")
        return {"success": False, "errors": errors}
    
    for key in config.keys():
        if key not in allowed_top_level:
            errors.append(f"Invalid top-level key '{key}'. Only 'common' and 'groups' are allowed")
    
    return {
        "success": len(errors) == 0,
        "errors": errors
    }


def _validate_section_content(section: Dict[str, Any], section_name: str) -> Dict[str, Any]:
    """Validate content within a common or per-FG section."""
    errors = []
    
    if not isinstance(section, dict):
        errors.append(f"Section '{section_name}' must be a dictionary")
        return {"success": False, "errors": errors}
    
    for key in section.keys():
        if key in PROHIBITED_CLOUD_INIT_KEYS:
            errors.append(f"Prohibited key '{key}' found in section '{section_name}'. Platform-managed keys not allowed")
        elif key not in ALLOWED_CLOUD_INIT_KEYS:
            errors.append(f"Unknown key '{key}' in section '{section_name}'. Only {list(ALLOWED_CLOUD_INIT_KEYS)} are allowed")
    
    # Validate write_files if present
    if "write_files" in section:
        write_files_result = validate_write_files(section["write_files"], section_name)
        if not write_files_result["success"]:
            errors.extend(write_files_result["errors"])
    
    # Validate runcmd if present
    if "runcmd" in section:
        runcmd_result = validate_runcmd(section["runcmd"], section_name)
        if not runcmd_result["success"]:
            errors.extend(runcmd_result["errors"])
    
    return {
        "success": len(errors) == 0,
        "errors": errors
    }


def _validate_groups_section(host, groups: Dict[str, Any]) -> Dict[str, Any]:
    """Validate groups section including FG name validation."""
    errors = []
    
    if not isinstance(groups, dict):
        errors.append("Groups section must be a dictionary")
        return {"success": False, "errors": errors}
    
    # Get available functional groups from PXE mapping
    try:
        available_fgs = get_functional_groups_from_pxe_mapping(host)
    except Exception as e:
        errors.append(f"Failed to get functional groups from PXE mapping: {str(e)}")
        return {"success": False, "errors": errors}
    
    for fg_name, fg_config in groups.items():
        # Validate functional group name
        if fg_name not in available_fgs:
            errors.append(f"Functional group '{fg_name}' not found in PXE mapping. Available: {sorted(available_fgs)}")
        
        # Validate functional group content
        fg_result = _validate_section_content(fg_config, f"groups.{fg_name}")
        if not fg_result["success"]:
            errors.extend(fg_result["errors"])
    
    return {
        "success": len(errors) == 0,
        "errors": errors
    }


def validate_write_files(write_files: Any, section_name: str) -> Dict[str, Any]:
    """
    Validate write_files directive structure.

    Args:
        write_files: write_files configuration
        section_name: Name of the section for error reporting

    Returns:
        Dict with success, error, and validation details
    """
    errors = []
    
    if not isinstance(write_files, list):
        errors.append(f"write_files in '{section_name}' must be a list")
        return {"success": False, "error": errors[0], "errors": errors}
    
    for i, file_entry in enumerate(write_files):
        if not isinstance(file_entry, dict):
            errors.append(f"write_files[{i}] in '{section_name}' must be a dictionary")
            continue
        
        if "path" not in file_entry:
            errors.append(f"write_files[{i}] in '{section_name}' missing required 'path' field")
    
    return {
        "success": len(errors) == 0,
        "error": "; ".join(errors) if errors else "",
        "errors": errors,
        "details": f"Validated {len(write_files) if isinstance(write_files, list) else 0} write_files entries"
    }


def validate_runcmd(runcmd: Any, section_name: str) -> Dict[str, Any]:
    """
    Validate runcmd directive structure.

    Args:
        runcmd: runcmd configuration
        section_name: Name of the section for error reporting

    Returns:
        Dict with success, error, and validation details
    """
    errors = []
    
    if not isinstance(runcmd, list):
        errors.append(f"runcmd in '{section_name}' must be a list")
        return {"success": False, "error": errors[0], "errors": errors}
    
    for i, cmd in enumerate(runcmd):
        if not isinstance(cmd, str):
            errors.append(f"runcmd[{i}] in '{section_name}' must be a string, got {type(cmd).__name__}")
    
    return {
        "success": len(errors) == 0,
        "error": "; ".join(errors) if errors else "",
        "errors": errors,
        "details": f"Validated {len(runcmd) if isinstance(runcmd, list) else 0} runcmd entries"
    }


def check_prohibited_keys(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for prohibited keys in the entire configuration.

    Args:
        config: Configuration dictionary to check

    Returns:
        Dict with success, error, and list of prohibited keys found
    """
    found_prohibited = []
    
    def _check_section(section: Dict[str, Any], path: str):
        """Recursively check a section for prohibited keys."""
        if not isinstance(section, dict):
            return
        
        for key in section.keys():
            if key in PROHIBITED_CLOUD_INIT_KEYS:
                found_prohibited.append(f"{path}.{key}" if path else key)
    
    # Check common section
    if "common" in config:
        _check_section(config["common"], "common")
    
    # Check groups sections
    if "groups" in config:
        for fg_name, fg_config in config["groups"].items():
            _check_section(fg_config, f"groups.{fg_name}")
    
    success = len(found_prohibited) == 0
    
    return {
        "success": success,
        "error": f"Prohibited keys found: {', '.join(found_prohibited)}" if not success else "",
        "prohibited_keys": found_prohibited,
        "details": f"Found {len(found_prohibited)} prohibited key(s)"
    }


def validate_functional_groups(host, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all functional groups in config exist in PXE mapping.

    Args:
        host: Testinfra host object
        config: Configuration dictionary

    Returns:
        Dict with success, error, and validation details
    """
    try:
        available_fgs = get_functional_groups_from_pxe_mapping(host)
        invalid_fgs = []
        
        # Check groups section
        if "groups" in config:
            for fg_name in config["groups"].keys():
                if fg_name not in available_fgs:
                    invalid_fgs.append(fg_name)
        
        success = len(invalid_fgs) == 0
        
        return {
            "success": success,
            "error": f"Invalid functional groups: {', '.join(invalid_fgs)}. Available: {sorted(available_fgs)}" if not success else "",
            "invalid_groups": invalid_fgs,
            "available_groups": sorted(available_fgs),
            "details": f"Validated functional groups, {len(invalid_fgs)} invalid"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to validate functional groups: {str(e)}",
            "invalid_groups": [],
            "available_groups": [],
            "details": f"Exception during validation: {str(e)}"
        }


# =============================================================================
# OMNIA VALIDATION PLAYBOOK INTEGRATION
# =============================================================================

_VALIDATION_PLAYBOOK_YAML = """\
---
- name: Set global facts
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Set project vars
      ansible.builtin.set_fact:
        input_project_dir: /opt/omnia/input/project_default
        project_name: project_default
        omnia_run_tags:
          - provision

- name: Run validation
  hosts: localhost
  connection: local
  roles:
    - role: /omnia/input_validation/roles/validate_input
"""

_VALIDATION_PLAYBOOK_PATH = "/tmp/omnia_validate_aci_test.yml"
_CONFIG_PATH = "/opt/omnia/input/project_default/additional_cloud_init.yml"
_BACKUP_PATH = "/opt/omnia/input/project_default/additional_cloud_init.yml.testbak"


def _ensure_validation_playbook(host):
    """Create the validation-only playbook in the container if not present."""
    check = run_in_container(host, f"test -f {_VALIDATION_PLAYBOOK_PATH}")
    if check.rc != 0:
        encoded = base64.b64encode(_VALIDATION_PLAYBOOK_YAML.encode()).decode()
        run_in_container(
            host,
            f"bash -c 'echo {encoded} | base64 -d > {_VALIDATION_PLAYBOOK_PATH}'"
        )


def run_omnia_validation_playbook(host, config_content=None, remove_config=False):
    """
    Run Omnia's actual provision validation pipeline with a test config.

    Temporarily replaces additional_cloud_init.yml inside the omnia_core
    container, executes the Omnia ``validate_input`` role (L1 + L2),
    then restores the original file.

    Args:
        host: Testinfra host object (connected to OIM)
        config_content: YAML string to write as the config file.
                        Pass None to keep the current file unchanged.
        remove_config: If True, temporarily remove the config file
                       (tests missing-file handling).

    Returns:
        Dict with:
            - validation_passed (bool): True if playbook exited cleanly
            - errors (list): Individual validation error strings
            - error_summary (str): Combined error text
            - output (str): Full ansible-playbook stdout
            - rc (int): Process return code
    """
    _ensure_validation_playbook(host)

    # Backup original config
    run_in_container(host, f"cp -f {_CONFIG_PATH} {_BACKUP_PATH}")

    try:
        if remove_config:
            run_in_container(host, f"rm -f {_CONFIG_PATH}")
        elif config_content is not None:
            encoded = base64.b64encode(config_content.encode()).decode()
            run_in_container(
                host,
                f"bash -c 'echo {encoded} | base64 -d > {_CONFIG_PATH}'"
            )

        # Run the validation playbook inside the container
        result = run_in_container(
            host,
            f"bash -lc 'cd /omnia && ANSIBLE_NOCOLOR=1 "
            f"ansible-playbook {_VALIDATION_PLAYBOOK_PATH} 2>&1'"
        )

        output = result.stdout or ""
        errors = _parse_validation_errors(output)
        error_summary = "; ".join(errors) if errors else ""

        return {
            "validation_passed": result.rc == 0,
            "errors": errors,
            "error_summary": error_summary,
            "output": output,
            "rc": result.rc,
        }
    finally:
        # Always restore original config
        run_in_container(host, f"test -f {_BACKUP_PATH} && mv {_BACKUP_PATH} {_CONFIG_PATH} || true")


def _parse_validation_errors(output):
    """Extract individual validation error messages from ansible-playbook output."""
    errors = []

    if "Errors:" not in output:
        return errors

    # Extract the Errors section from the fatal task message
    match = re.search(
        r'Errors:\s*(.*?)(?:\s*Invalid files:|\s*Log file:|\s*"|\s*$)',
        output,
        re.DOTALL,
    )
    if not match:
        return errors

    errors_text = match.group(1).strip()

    # Split on "Validation Error at" boundaries
    raw = re.split(r'(?=Validation Error at)', errors_text)
    for chunk in raw:
        chunk = chunk.strip().rstrip(";").strip()
        if chunk:
            errors.append(chunk)

    return errors
