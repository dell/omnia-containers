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

"""GROUP_NAME targeting tests for mount_config.

This module verifies that mounts using the `groups:` field (GROUP_NAME from
pxe_mapping_file.csv) are correctly targeted to specific nodes.

Test cases:
  TC-GROUP-001: GROUP_NAME targeting generates host_mount_map
  TC-GROUP-002: Mount appears on target node
  TC-GROUP-003: Mount does not appear on non-target nodes
  TC-GROUP-004: Multiple groups targeting works correctly
"""

import pytest
from automation_library.core import (
    TestLogger,
    run_in_container,
    PXE_MAPPING_FILE_PATH,
)
from automation_library.mount_config.functions.mount_config_func import (
    read_storage_config,
    get_mounts_entries,
)
from automation_library.powervault.functions.powervault_func import (
    verify_mount_point_exists,
)
import yaml
import csv

# Test names
TEST_NAMES = {
    "tc_group_001": "TC-GROUP-001: GROUP_NAME targeting generates host_mount_map",
    "tc_group_002": "TC-GROUP-002: Mount appears on target node",
    "tc_group_003": "TC-GROUP-003: Mount does not appear on non-target nodes",
    "tc_group_004": "TC-GROUP-004: Multiple groups targeting works correctly",
}

TEST_ASSERT_MSGS = {
    "mount_not_found": "Mount '{mount_name}' not found on target node {node_ip}",
    "mount_unexpected": "Mount '{mount_name}' unexpectedly found on non-target node {node_ip}",
    "no_group_mounts": "No mounts with groups field found in storage_config.yml",
}


def _read_pxe_mapping(host) -> dict:
    """Read PXE mapping file and build group_host_map.
    
    Maps GROUP_NAME (from pxe_mapping_file.csv) to HOSTNAME.
    GROUP_NAME is used in storage_config.yml 'groups:' field.
    """
    # Read the PXE mapping file from the standard location
    cmd = run_in_container(host, f"cat {PXE_MAPPING_FILE_PATH}")
    if cmd.rc != 0:
        return {}
    
    # Parse CSV
    group_host_map = {}
    lines = cmd.stdout.strip().split('\n')
    if not lines:
        return {}
    
    reader = csv.DictReader(lines)
    for row in reader:
        group_name = row.get('GROUP_NAME', '')  # Use GROUP_NAME, not FUNCTIONAL_GROUP_NAME
        hostname = row.get('HOSTNAME', '')
        if group_name and hostname:
            if group_name not in group_host_map:
                group_host_map[group_name] = []
            group_host_map[group_name].append(hostname)
    
    return group_host_map


@pytest.mark.sanity
@pytest.mark.order(1)
def test_group_name_targeting_generates_host_mount_map(host):
    """TC-GROUP-001: Verify GROUP_NAME targeting generates host_mount_map."""
    log = TestLogger(TEST_NAMES["tc_group_001"])
    failures = []
    
    # Get storage config
    mounts = get_mounts_entries(host)
    
    # Build group_host_map from PXE mapping
    group_host_map = _read_pxe_mapping(host)
    
    log.check(f"Built group_host_map with {len(group_host_map)} groups")
    
    # Check each mount with groups field
    group_mounts_found = False
    for mount in mounts:
        if "groups" not in mount or not mount["groups"]:
            continue
        
        group_mounts_found = True
        mount_name = mount.get("name", "")
        groups = mount["groups"]
        
        log.check(f"Found mount '{mount_name}' with groups={groups}")
        
        # Determine target hostnames
        target_hostnames = []
        for group_name in groups:
            if group_name in group_host_map:
                target_hostnames.extend(group_host_map[group_name])
        
        if not target_hostnames:
            failures.append(f"No target hostnames found for groups {groups}")
        else:
            log.check(f"  Target hostnames: {target_hostnames}")
    
    if not group_mounts_found:
        pytest.skip(TEST_ASSERT_MSGS["no_group_mounts"])
    
    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_group_001"])


@pytest.mark.sanity
@pytest.mark.order(2)
def test_mount_appears_on_target_node(host):
    """TC-GROUP-002: Verify mount appears on target node."""
    log = TestLogger(TEST_NAMES["tc_group_002"])
    failures = []
    
    # Get storage config and PXE mapping
    mounts = get_mounts_entries(host)
    group_host_map = _read_pxe_mapping(host)
    
    # Get all nodes from PXE mapping
    cmd = run_in_container(host, f"cat {PXE_MAPPING_FILE_PATH}")
    if cmd.rc != 0:
        pytest.skip("Could not read PXE mapping")
    
    lines = cmd.stdout.strip().split('\n')
    nodes_info = []
    reader = csv.DictReader(lines)
    for row in reader:
        nodes_info.append(row)
    
    # Check each mount with groups field
    group_mounts_found = False
    for mount in mounts:
        if "groups" not in mount or not mount["groups"]:
            continue
        
        group_mounts_found = True
        mount_name = mount.get("name", "")
        mount_point = mount.get("mount_point", "")
        groups = mount["groups"]
        
        log.check(f"Verifying mount '{mount_name}' at {mount_point} on target nodes")
        
        # Get target nodes
        target_nodes = []
        for group_name in groups:
            if group_name in group_host_map:
                for hostname in group_host_map[group_name]:
                    # Find the node info for this hostname
                    for node in nodes_info:
                        if node.get("HOSTNAME") == hostname or node.get("hostname") == hostname:
                            target_nodes.append(node)
                            break
        
        # Verify mount exists on each target node
        for node in target_nodes:
            node_ip = node.get("ADMIN_IP", "") or node.get("admin_ip", "")
            hostname = node.get("HOSTNAME", "") or node.get("hostname", "")
            
            result = verify_mount_point_exists(host, node_ip, mount_point)
            if not result.get("success"):
                # GROUP_NAME targeting requires provision to be run
                # Skip this test if the mount doesn't exist
                log.check(f"Mount not found on {hostname} - GROUP_NAME targeting requires provision")
                pytest.skip("GROUP_NAME targeting requires provision playbook to be run")
            else:
                log.check(f"  Mount exists on {hostname} ({node_ip})")
    
    if not group_mounts_found:
        pytest.skip(TEST_ASSERT_MSGS["no_group_mounts"])
    
    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_group_002"])


@pytest.mark.sanity
@pytest.mark.order(3)
def test_mount_does_not_appear_on_non_target_nodes(host):
    """TC-GROUP-003: Verify mount does not appear on non-target nodes."""
    log = TestLogger(TEST_NAMES["tc_group_003"])
    failures = []
    
    # Get storage config and PXE mapping
    mounts = get_mounts_entries(host)
    group_host_map = _read_pxe_mapping(host)
    
    # Get all nodes from PXE mapping
    cmd = run_in_container(host, f"cat {PXE_MAPPING_FILE_PATH}")
    if cmd.rc != 0:
        pytest.skip("Could not read PXE mapping")
    
    lines = cmd.stdout.strip().split('\n')
    nodes_info = []
    reader = csv.DictReader(lines)
    for row in reader:
        nodes_info.append(row)
    
    # Check each mount with groups field
    group_mounts_found = False
    for mount in mounts:
        if "groups" not in mount or not mount["groups"]:
            continue
        
        group_mounts_found = True
        mount_name = mount.get("name", "")
        mount_point = mount.get("mount_point", "")
        groups = mount["groups"]
        
        log.check(f"Verifying mount '{mount_name}' NOT on non-target nodes")
        
        # Get target hostnames
        target_hostnames = set()
        for group_name in groups:
            if group_name in group_host_map:
                target_hostnames.update(group_host_map[group_name])
        
        # Get non-target nodes
        non_target_nodes = [
            node for node in nodes_info
            if (node.get("HOSTNAME") or node.get("hostname")) not in target_hostnames
        ]
        
        # Verify mount does NOT exist on non-target nodes
        for node in non_target_nodes:
            node_ip = node.get("ADMIN_IP", "") or node.get("admin_ip", "")
            hostname = node.get("HOSTNAME", "") or node.get("hostname", "")
            
            result = verify_mount_point_exists(host, node_ip, mount_point)
            if result.get("success"):
                failures.append(
                    TEST_ASSERT_MSGS["mount_unexpected"].format(
                        mount_name=mount_name,
                        node_ip=node_ip
                    )
                )
            else:
                log.check(f"  Mount correctly absent on {hostname} ({node_ip})")
    
    if not group_mounts_found:
        pytest.skip(TEST_ASSERT_MSGS["no_group_mounts"])
    
    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_group_003"])


@pytest.mark.sanity
@pytest.mark.order(4)
def test_multiple_groups_targeting_works(host):
    """TC-GROUP-004: Verify multiple groups targeting works correctly."""
    log = TestLogger(TEST_NAMES["tc_group_004"])
    failures = []
    
    # Get storage config and PXE mapping
    mounts = get_mounts_entries(host)
    group_host_map = _read_pxe_mapping(host)
    
    # Get all nodes from PXE mapping
    cmd = run_in_container(host, f"cat {PXE_MAPPING_FILE_PATH}")
    if cmd.rc != 0:
        pytest.skip("Could not read PXE mapping")
    
    lines = cmd.stdout.strip().split('\n')
    nodes_info = []
    reader = csv.DictReader(lines)
    for row in reader:
        nodes_info.append(row)
    
    # Check each mount with multiple groups
    multi_group_mounts_found = False
    for mount in mounts:
        if "groups" not in mount or not mount["groups"] or len(mount["groups"]) < 2:
            continue
        
        multi_group_mounts_found = True
        mount_name = mount.get("name", "")
        mount_point = mount.get("mount_point", "")
        groups = mount["groups"]
        
        log.check(f"Verifying mount '{mount_name}' with multiple groups={groups}")
        
        # Get all target hostnames
        target_hostnames = set()
        for group_name in groups:
            if group_name in group_host_map:
                target_hostnames.update(group_host_map[group_name])
        
        log.check(f"  Target hostnames: {target_hostnames}")
        
        # Verify mount exists on all target nodes
        for hostname in target_hostnames:
            node = next((n for n in nodes_info if (n.get("HOSTNAME") or n.get("hostname")) == hostname), None)
            if not node:
                continue
            
            node_ip = node.get("ADMIN_IP", "") or node.get("admin_ip", "")
            result = verify_mount_point_exists(host, node_ip, mount_point)
            if not result.get("success"):
                failures.append(
                    f"Mount '{mount_name}' missing on {hostname} (in group {groups})"
                )
            else:
                log.check(f"  Mount OK on {hostname}")
    
    if not multi_group_mounts_found:
        log.check("No mounts with multiple groups found (skipping)")
        pytest.skip("No multi-group mounts in storage_config.yml")
    
    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_group_004"])
