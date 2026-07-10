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

"""Slurm Test Cases for Homogeneous Node Discovery Mode.

Test cases for validating homogeneous node discovery mode functionality in Slurm cluster configuration.

Test Coverage:
  TC-H01 - Validate node_discovery_mode configuration structure
  TC-H02 - Validate node_hardware_defaults configuration structure
  TC-H03 - Validate group names in PXE mapping exist in node_hardware_defaults
  TC-H04 - Verify homogeneous mode with user specs (0 iDRAC calls)
  TC-H05 - Verify homogeneous mode without user specs (group-level iDRAC)
  TC-H06 - Verify hardware specs match user-specified defaults
  TC-H07 - Verify mixed homogeneous mode (some groups with specs, some without)
  TC-H08 - Verify heterogeneous mode default behavior (1 iDRAC call per node)
"""

import pytest
from automation_library.core import TestLogger, load_input_file, OMNIA_CONFIG_FILE
from automation_library.slurm.functions.homogeneous_func import (
    validate_node_discovery_mode_config,
    validate_node_hardware_defaults_config,
    validate_group_names_in_pxe_mapping,
    verify_homogeneous_with_user_specs,
    verify_homogeneous_without_user_specs,
    verify_hardware_specs_match_user_specs,
    verify_mixed_homogeneous_mode,
    verify_heterogeneous_mode_default,
)


def _get_discovery_mode(host) -> str:
    """Get current node_discovery_mode from omnia_config.yml."""
    mode_result = validate_node_discovery_mode_config(host)
    if not mode_result.get("success"):
        return ""
    return str(mode_result.get("discovery_mode", "")).lower()


# =============================================================================
# CONFIGURATION VALIDATION TESTS (TC-H01 to TC-H03)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.homogeneous
@pytest.mark.order(100)
def test_h01_validate_node_discovery_mode_config(host):
    """
    Test Case H01: Validate node_discovery_mode Configuration Structure.

    Priority: P0 - Configuration Validation
    Test Type: Configuration Validation
    Markers: @pytest.mark.sanity, @pytest.mark.homogeneous

    Validates that node_discovery_mode is properly configured in omnia_config.yml
    and is set to either 'homogeneous' or 'heterogeneous'.
    """
    log = TestLogger("Validate node_discovery_mode configuration")
    log.check("Checking node_discovery_mode in omnia_config.yml")

    result = validate_node_discovery_mode_config(host)

    if result["success"]:
        log.check(f"  ✓ node_discovery_mode: {result.get('discovery_mode')}")
        log.passed(result["message"])
    else:
        log.failed(result["error"])

    assert result["success"], result["error"]


@pytest.mark.sanity
@pytest.mark.homogeneous
@pytest.mark.order(101)
def test_h02_validate_node_hardware_defaults_config(host):
    """
    Test Case H02: Validate node_hardware_defaults Configuration Structure.

    Priority: P0 - Configuration Validation
    Test Type: Configuration Validation
    Markers: @pytest.mark.sanity, @pytest.mark.homogeneous

    Validates that node_hardware_defaults (if configured) has proper structure
    with group names and hardware specifications.
    """
    log = TestLogger("Validate node_hardware_defaults configuration")
    log.check("Checking node_hardware_defaults in omnia_config.yml")

    result = validate_node_hardware_defaults_config(host)

    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    groups = result.get("groups_with_specs", [])
    if groups:
        log.check(f"  ✓ Groups with hardware specs: {groups}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["error"])

    assert result["success"], result["error"]


@pytest.mark.sanity
@pytest.mark.homogeneous
@pytest.mark.order(102)
def test_h03_validate_group_names_in_pxe_mapping(host):
    """
    Test Case H03: Validate Group Names in PXE Mapping.

    Priority: P1 - Configuration Validation
    Test Type: Configuration Validation
    Markers: @pytest.mark.sanity, @pytest.mark.homogeneous

    Validates that all group names defined in node_hardware_defaults
    exist in the PXE mapping configuration.
    """
    log = TestLogger("Validate group names in PXE mapping")
    log.check("Checking group names from node_hardware_defaults exist in PXE mapping")

    # Get group names from configuration
    config = load_input_file(host, OMNIA_CONFIG_FILE)
    slurm_clusters = config.get("slurm_cluster", [])
    if not slurm_clusters:
        log.skipped("No slurm_cluster configuration", "Check omnia_config.yml")
        pytest.skip("No slurm_cluster configuration")
        return

    cluster = slurm_clusters[0]
    node_hardware_defaults = cluster.get("node_hardware_defaults", {})

    if not node_hardware_defaults:
        log.check("  node_hardware_defaults not configured (skipping validation)")
        pytest.skip("node_hardware_defaults not configured")
        return

    groups_with_specs = list(node_hardware_defaults.keys())
    log.check(f"  Groups with specs: {groups_with_specs}")

    # Validate group names in PXE mapping
    result = validate_group_names_in_pxe_mapping(host, groups_with_specs)

    if result.get("pxe_groups"):
        log.check(f"  ✓ PXE mapping groups found: {sorted(result['pxe_groups'])}")

    if result.get("missing_groups"):
        log.check(f"  ✗ Missing groups: {result['missing_groups']}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["error"])

    assert result["success"], result["error"]


# =============================================================================
# HOMOGENEOUS MODE TESTS (TC-H04 to TC-H07)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.homogeneous
@pytest.mark.order(103)
def test_h04_verify_homogeneous_with_user_specs(host):
    """
    Test Case H04: Verify Homogeneous Mode with User Specs.

    Priority: P0 - Functional Validation
    Test Type: Functional Test
    Markers: @pytest.mark.sanity, @pytest.mark.homogeneous

    Validates homogeneous discovery behavior when all groups have user-specified
    hardware defaults. Expected: 0 iDRAC calls (all specs from configuration).
    """
    log = TestLogger("Verify homogeneous discovery with user specs")
    log.check("Validating homogeneous mode with user specs (0 iDRAC calls expected)")

    mode = _get_discovery_mode(host)
    if mode != "homogeneous":
        log.check(f"  Current mode: {mode or 'unknown'} (required: homogeneous)")
        pytest.skip(f"Homogeneous mode required; current: {mode or 'unknown'}")
        return

    result = verify_homogeneous_with_user_specs(host)

    # Log validation details
    behavior = result.get("discovery_behavior", {})
    log.check(f"  ✓ Discovery method: {behavior.get('discovery_method')}")
    log.check(f"  ✓ Expected iDRAC calls: {behavior.get('expected_idrac_calls')}")

    # Log per-node specs validation
    specs_validation = behavior.get("specs_validation", [])
    if specs_validation:
        log.check("  Node specs comparison:")
        for row in specs_validation:
            status = "✓" if row.get("specs_match") else "✗"
            log.check(f"    {status} {row.get('node')} (group={row.get('group')})")
            exp = row.get("expected", {})
            act = row.get("actual", {})
            
            # Show expected values
            log.check(
                f"      EXPECTED: Sockets={exp.get('sockets')} "
                f"CoresPerSocket={exp.get('cores')} "
                f"ThreadsPerCore={exp.get('threads')} "
                f"RealMemory={exp.get('memory')}"
            )
            
            # Show actual values
            log.check(
                f"      ACTUAL:   Sockets={act.get('sockets')} "
                f"CoresPerSocket={act.get('cores')} "
                f"ThreadsPerCore={act.get('threads')} "
                f"RealMemory={act.get('memory')}"
            )
            
            # Show differences if any
            if not row.get("specs_match"):
                diffs = []
                if exp.get('sockets') != act.get('sockets'):
                    diffs.append(f"Sockets: {exp.get('sockets')} vs {act.get('sockets')}")
                if exp.get('cores') != act.get('cores'):
                    diffs.append(f"CoresPerSocket: {exp.get('cores')} vs {act.get('cores')}")
                if exp.get('threads') != act.get('threads'):
                    diffs.append(f"ThreadsPerCore: {exp.get('threads')} vs {act.get('threads')}")
                if exp.get('memory') != act.get('memory'):
                    diffs.append(f"RealMemory: {exp.get('memory')} vs {act.get('memory')}")
                if diffs:
                    log.check(f"      MISMATCH: {', '.join(diffs)}")

    if result["success"]:
        log.passed(result["message"])
        assert True
    else:
        log.failed(result["error"])
        pytest.fail(result["error"])


@pytest.mark.sanity
@pytest.mark.homogeneous
@pytest.mark.order(104)
def test_h05_verify_homogeneous_without_user_specs(host):
    """
    Test Case H05: Verify Homogeneous Mode Without User Specs.

    Priority: P0 - Functional Validation
    Test Type: Functional Test
    Markers: @pytest.mark.sanity, @pytest.mark.homogeneous

    Validates homogeneous discovery behavior when at least one group has NO
    user-specified hardware defaults. Expected: 1 iDRAC call per group without specs.
    """
    log = TestLogger("Verify homogeneous discovery without user specs")
    log.check("Validating homogeneous mode without user specs (group-level iDRAC expected)")

    mode = _get_discovery_mode(host)
    if mode != "homogeneous":
        log.check(f"  Current mode: {mode or 'unknown'} (required: homogeneous)")
        pytest.skip(f"Homogeneous mode required; current: {mode or 'unknown'}")
        return

    result = verify_homogeneous_without_user_specs(host)

    # Skip if not applicable (all groups have specs)
    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result["success"]:
        behavior = result.get("discovery_behavior", {})
        log.check(f"  ✓ Discovery method: {behavior.get('discovery_method')}")
        log.check(f"  ✓ Expected iDRAC calls: {behavior.get('expected_idrac_calls')}")
        log.check(f"  ✓ Groups without specs: {behavior.get('groups_without_specs')}")

        log.passed(result["message"])
        assert True
    else:
        log.failed(result["error"])
        pytest.fail(result["error"])


@pytest.mark.sanity
@pytest.mark.homogeneous
@pytest.mark.order(105)
def test_h06_verify_hardware_specs_match_user_specs(host):
    """
    Test Case H06: Verify Hardware Specs Match User Specs.

    Priority: P0 - Functional Validation
    Test Type: Functional Test
    Markers: @pytest.mark.sanity, @pytest.mark.homogeneous

    Validates that actual hardware specs in slurm.conf match the user-specified
    defaults in node_hardware_defaults. Only applicable when user specs are configured.
    """
    log = TestLogger("Verify hardware specs match user specs")
    log.check("Validating slurm.conf node specs match node_hardware_defaults")

    mode = _get_discovery_mode(host)
    if mode != "homogeneous":
        log.check(f"  Current mode: {mode or 'unknown'} (required: homogeneous)")
        pytest.skip(f"Homogeneous mode required; current: {mode or 'unknown'}")
        return

    # Check if user specs are configured
    config = load_input_file(host, OMNIA_CONFIG_FILE)
    cluster = config.get("slurm_cluster", [])[0]
    if not cluster.get("node_hardware_defaults"):
        log.check("  node_hardware_defaults not configured (skipping)")
        pytest.skip("node_hardware_defaults not configured")
        return

    result = verify_hardware_specs_match_user_specs(host)

    if result["success"]:
        spec_val = result.get("spec_validation", {})
        log.check(f"  ✓ Spec source: {spec_val.get('spec_source')}")
        log.check(f"  ✓ Nodes validated: {result.get('cluster_state', {}).get('nodes_in_slurm_conf')}")

        log.passed(result["message"])
        assert True
    else:
        log.failed(result["error"])
        pytest.fail(result["error"])


@pytest.mark.sanity
@pytest.mark.homogeneous
@pytest.mark.order(106)
def test_h07_verify_mixed_homogeneous_mode(host):
    """
    Test Case H07: Verify Mixed Homogeneous Mode.

    Priority: P1 - Functional Validation
    Test Type: Functional Test
    Markers: @pytest.mark.sanity, @pytest.mark.homogeneous

    Validates mixed homogeneous scenario where some groups have user-specified
    hardware defaults and others do not. Expected: 0 iDRAC calls for groups with specs,
    1 iDRAC call per group without specs.
    """
    log = TestLogger("Verify mixed homogeneous mode")
    log.check("Validating mixed homogeneous scenario (some groups with specs, some without)")

    mode = _get_discovery_mode(host)
    if mode != "homogeneous":
        log.check(f"  Current mode: {mode or 'unknown'} (required: homogeneous)")
        pytest.skip(f"Homogeneous mode required; current: {mode or 'unknown'}")
        return

    result = verify_mixed_homogeneous_mode(host)

    # Skip if not applicable (all groups have specs or all without specs)
    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    if result["success"]:
        mixed = result.get("mixed_analysis", {})
        log.check(f"  ✓ Groups with specs: {mixed.get('groups_with_specs')}")
        log.check(f"  ✓ Groups without specs: {mixed.get('groups_without_specs')}")
        log.check(f"  ✓ Total nodes in slurm.conf: {result.get('cluster_state', {}).get('nodes_in_slurm_conf')}")

        log.passed(result["message"])
        assert True
    else:
        log.failed(result["error"])
        pytest.fail(result["error"])


# =============================================================================
# HETEROGENEOUS MODE TEST (TC-H08)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.homogeneous
@pytest.mark.order(107)
def test_h08_verify_heterogeneous_mode_default(host):
    """
    Test Case H08: Verify Heterogeneous Mode Default Behavior.

    Priority: P1 - Compatibility Validation
    Test Type: Functional Test
    Markers: @pytest.mark.sanity, @pytest.mark.homogeneous

    Validates heterogeneous mode (default behavior) where each node's hardware
    is discovered individually. Expected: 1 iDRAC call per node.
    """
    log = TestLogger("Verify heterogeneous mode default behavior")
    log.check("Validating heterogeneous mode behavior (1 iDRAC call per node expected)")

    mode = _get_discovery_mode(host)
    if mode != "heterogeneous":
        log.check(f"  Current mode: {mode or 'unknown'} (required: heterogeneous)")
        pytest.skip(f"Heterogeneous mode required; current: {mode or 'unknown'}")
        return

    result = verify_heterogeneous_mode_default(host)

    if result["success"]:
        default = result.get("default_analysis", {})
        log.check(f"  ✓ Current mode: {default.get('current_mode')}")
        log.check(f"  ✓ Is default: {default.get('is_default')}")
        log.check(f"  ✓ Total nodes: {default.get('total_nodes')}")

        log.passed(result["message"])
        assert True
    else:
        log.failed(result["error"])
        pytest.fail(result["error"])
