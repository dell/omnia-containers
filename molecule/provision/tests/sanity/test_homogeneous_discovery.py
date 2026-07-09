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

"""Provision Slurm Test Cases for Homogeneous Node Discovery Mode.

Test cases for validating homogeneous node discovery mode functionality in Slurm cluster configuration.
"""

import pytest
from automation_library.core import TestLogger, load_input_file, OMNIA_CONFIG_FILE
from automation_library.provision.functions.homogeneous_func import (
    validate_node_discovery_mode_config,
    validate_node_hardware_defaults_config,
    validate_group_names_in_pxe_mapping,
    verify_homogeneous_with_user_specs,
    verify_homogeneous_without_user_specs,
    verify_hardware_specs_match_user_specs,
    verify_mixed_homogeneous_mode,
    verify_heterogeneous_mode_default,
)


class TestHomogeneousNodeDiscovery:
    """Test class for homogeneous node discovery mode testing."""
    
    @pytest.mark.sanity
    @pytest.mark.homogeneous
    @pytest.mark.order(100)
    def test_h01_validate_node_discovery_mode_config(self, host):
        """
        TC-H01: Validate node_discovery_mode Configuration Structure
        
        Priority: P0 - Configuration Validation
        Test Type: Configuration Validation
        Markers: @pytest.mark.sanity, @pytest.mark.homogeneous
        """
        log = TestLogger("Validate node_discovery_mode configuration structure")
        log.check("Testing node_discovery_mode configuration in omnia_config.yml")
        
        result = validate_node_discovery_mode_config(host)
        
        if result["success"]:
            log.passed(result["message"])
        else:
            log.failed(result["error"])
        
        assert result["success"], result["error"]
    
    @pytest.mark.sanity
    @pytest.mark.homogeneous
    @pytest.mark.order(101)
    def test_h02_validate_node_hardware_defaults_config(self, host):
        """
        TC-H02: Validate node_hardware_defaults Configuration Structure
        
        Priority: P0 - Configuration Validation
        Test Type: Configuration Validation
        Markers: @pytest.mark.sanity, @pytest.mark.homogeneous
        """
        log = TestLogger("Validate node_hardware_defaults configuration structure")
        log.check("Testing node_hardware_defaults configuration in omnia_config.yml")
        
        result = validate_node_hardware_defaults_config(host)
        
        if result["success"]:
            log.passed(result["message"])
            log.check(f"Groups with user specs: {result['groups_with_specs']}")
        else:
            log.failed(result["error"])
        
        assert result["success"], result["error"]
    
    @pytest.mark.sanity
    @pytest.mark.homogeneous
    @pytest.mark.order(102)
    def test_h03_validate_group_names_in_pxe_mapping(self, host):
        """
        TC-H03: Validate Group Names in PXE Mapping
        
        Priority: P1 - Configuration Validation
        Test Type: Configuration Validation
        Markers: @pytest.mark.sanity, @pytest.mark.homogeneous
        """
        log = TestLogger("Validate group names in PXE mapping")
        log.check("Testing group names from node_hardware_defaults exist in PXE mapping")
        
        # Get group names from test configuration
        config = load_input_file(host, OMNIA_CONFIG_FILE)
        slurm_clusters = config.get("slurm_cluster", [])
        cluster = slurm_clusters[0]
        node_hardware_defaults = cluster.get("node_hardware_defaults", {})
        groups_with_specs = list(node_hardware_defaults.keys())
        
        # Validate group names in PXE mapping
        result = validate_group_names_in_pxe_mapping(host, groups_with_specs)
        
        if result["success"]:
            log.passed(result["message"])
            log.check(f"PXE groups found: {result['pxe_groups']}")
        else:
            log.failed(result["error"])
        
        assert result["success"], result["error"]
    
    @pytest.mark.sanity
    @pytest.mark.homogeneous
    @pytest.mark.order(103)
    def test_h04_verify_homogeneous_with_user_specs(self, host):
        """
        TC-H04: Verify Node Discovery Behavior (Mode-Agnostic)
        
        Priority: P0 - Functional Validation
        Test Type: Functional Test
        Markers: @pytest.mark.sanity, @pytest.mark.homogeneous
        """
        log = TestLogger("Verify node discovery behavior (mode-agnostic)")
        log.check("Testing node discovery behavior based on current mode")
        
        result = verify_homogeneous_with_user_specs(host)
        
        if result["success"]:
            log.passed(result["message"])
            log.check(f"Mode: {result['mode']}")
            log.check(f"Discovery behavior: {result['discovery_behavior']}")
            log.check(f"Cluster state: {result['cluster_state']}")
        else:
            log.failed(result["error"])
        
        assert result["success"], result["error"]
    
    @pytest.mark.sanity
    @pytest.mark.homogeneous
    @pytest.mark.order(104)
    def test_h05_verify_homogeneous_without_user_specs(self, host):
        """
        TC-H05: Verify Node Discovery Without User Specs (Mode-Agnostic)
        
        Priority: P0 - Functional Validation
        Test Type: Functional Test
        Markers: @pytest.mark.sanity, @pytest.mark.homogeneous
        """
        log = TestLogger("Verify node discovery without user specs (mode-agnostic)")
        log.check("Testing node discovery behavior without user specs")
        
        result = verify_homogeneous_without_user_specs(host)
        
        if result["success"]:
            log.passed(result["message"])
            log.check(f"Mode: {result['mode']}")
            log.check(f"Discovery behavior: {result['discovery_behavior']}")
            log.check(f"Cluster state: {result['cluster_state']}")
        else:
            log.failed(result["error"])
        
        assert result["success"], result["error"]
    
    @pytest.mark.sanity
    @pytest.mark.homogeneous
    @pytest.mark.order(105)
    def test_h06_verify_hardware_specs_match_user_specs(self, host):
        """
        TC-H06: Verify Hardware Specs Validation (Mode-Agnostic)
        
        Priority: P0 - Functional Validation
        Test Type: Functional Test
        Markers: @pytest.mark.sanity, @pytest.mark.homogeneous
        """
        log = TestLogger("Verify hardware specs validation (mode-agnostic)")
        log.check("Testing hardware specs validation based on current mode")
        
        result = verify_hardware_specs_match_user_specs(host)
        
        if result["success"]:
            log.passed(result["message"])
            log.check(f"Mode: {result['mode']}")
            log.check(f"Spec validation: {result['spec_validation']}")
            log.check(f"Cluster state: {result['cluster_state']}")
        else:
            log.failed(result["error"])
        
        assert result["success"], result["error"]
    
    @pytest.mark.sanity
    @pytest.mark.homogeneous
    @pytest.mark.order(106)
    def test_h07_verify_mixed_homogeneous_mode(self, host):
        """
        TC-H07: Verify Mixed Mode Scenario (Mode-Agnostic)
        
        Priority: P1 - Functional Validation
        Test Type: Functional Test
        Markers: @pytest.mark.sanity, @pytest.mark.homogeneous
        """
        log = TestLogger("Verify mixed mode scenario (mode-agnostic)")
        log.check("Testing mixed mode configuration based on current mode")
        
        result = verify_mixed_homogeneous_mode(host)
        
        if result["success"]:
            log.passed(result["message"])
            log.check(f"Mode: {result['mode']}")
            log.check(f"Mixed analysis: {result['mixed_analysis']}")
            log.check(f"Cluster state: {result['cluster_state']}")
        else:
            log.failed(result["error"])
        
        assert result["success"], result["error"]
    
    @pytest.mark.sanity
    @pytest.mark.homogeneous
    @pytest.mark.order(107)
    def test_h08_verify_heterogeneous_mode_default(self, host):
        """
        TC-H08: Verify Default Mode Behavior (Mode-Agnostic)
        
        Priority: P1 - Compatibility Validation
        Test Type: Functional Test
        Markers: @pytest.mark.sanity, @pytest.mark.homogeneous
        """
        log = TestLogger("Verify default mode behavior (mode-agnostic)")
        log.check("Testing default mode behavior and configuration")
        
        result = verify_heterogeneous_mode_default(host)
        
        if result["success"]:
            log.passed(result["message"])
            log.check(f"Default analysis: {result['default_analysis']}")
            log.check(f"Cluster state: {result['cluster_state']}")
        else:
            log.failed(result["error"])
        
        assert result["success"], result["error"]
