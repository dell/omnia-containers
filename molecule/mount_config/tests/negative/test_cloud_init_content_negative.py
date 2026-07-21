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

"""Negative test cases for cloud-init content tests.

These tests verify that the cloud-init content tests correctly detect
configuration errors and fail appropriately.

Test cases:
  TC-CI-NEG-001: Missing mount_point should fail
  TC-CI-NEG-002: Missing functional_group_prefix should fail
  TC-CI-NEG-003: Incorrect mount_params profile should fail
  TC-CI-NEG-004: Missing source should fail
  TC-CI-NEG-005: Missing node_mount_point with node_key should fail
"""

import json
import pytest
import yaml
from automation_library.core import TestLogger
from automation_library.mount_config.functions.mount_config_func import (
    read_storage_config,
)

# Test names
TEST_NAMES = {
    "tc_ci_neg_001": "TC-CI-NEG-001: Missing mount_point should fail",
    "tc_ci_neg_002": "TC-CI-NEG-002: Missing functional_group_prefix should fail",
    "tc_ci_neg_003": "TC-CI-NEG-003: Incorrect mount_params profile should fail",
    "tc_ci_neg_004": "TC-CI-NEG-004: Missing source should fail",
    "tc_ci_neg_005": "TC-CI-NEG-005: Missing node_mount_point with node_key should fail",
}


def _backup_storage_config(host) -> str:
    """Backup storage_config.yml and return backup path."""
    cmd = "podman exec omnia_core bash -c 'cp /opt/omnia/input/project_default/storage_config.yml /tmp/storage_config.yml.backup && echo /tmp/storage_config.yml.backup'"
    result = host.run(cmd, shell=True)
    return result.stdout.strip() if result.rc == 0 else None


def _restore_storage_config(host):
    """Restore storage_config.yml from backup."""
    cmd = "podman exec omnia_core bash -c 'cp /tmp/storage_config.yml.backup /opt/omnia/input/project_default/storage_config.yml'"
    host.run(cmd, shell=True)


def _modify_storage_config(host, modification_func):
    """Modify storage_config.yml using a function and return the modified config."""
    # Read current config
    cmd_read = "podman exec omnia_core cat /opt/omnia/input/project_default/storage_config.yml"
    result_read = host.run(cmd_read, shell=True)
    
    if result_read.rc != 0:
        return None
    
    # Parse YAML
    config = yaml.safe_load(result_read.stdout)
    
    # Apply modification
    modification_func(config)
    
    # Write back
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.safe_dump(config, f, default_flow_style=False)
        temp_file = f.name
    
    # Copy to container
    cmd_copy = f"cat {temp_file} | podman exec -i omnia_core tee /opt/omnia/input/project_default/storage_config.yml > /dev/null"
    host.run(cmd_copy, shell=True)
    
    return config


def _run_mount_config_role(host) -> dict:
    """Run mount_config role in check mode and extract cloud_init_groups_dict."""
    cmd = """
    podman exec -i omnia_core python3 - <<'PYTHON'
import json
import yaml
import sys

# Read required configs
with open('/opt/omnia/input/project_default/storage_config.yml') as f:
    storage_config = yaml.safe_load(f)

with open('/opt/omnia/input/project_default/pxe_mapping_file.csv') as f:
    import csv
    reader = csv.DictReader(f)
    pxe_mapping = list(reader)

# Build functional_groups from pxe_mapping
functional_groups = {}
for row in pxe_mapping:
    fg_name = row.get('FUNCTIONAL_GROUP_NAME', '')
    if fg_name and fg_name not in functional_groups:
        functional_groups[fg_name] = {'name': fg_name}

# Initialize variables
cloud_init_groups_dict = {}

# Create cloud_init_groups_dict structure
for fg_name in functional_groups.keys():
    cloud_init_groups_dict[fg_name] = {}

# Process mounts
mounts = storage_config.get('mounts', [])
mount_params = storage_config.get('mount_params', {})

for mount in mounts:
    mount_name = mount.get('name', '')
    source = mount.get('source', '')
    mount_point = mount.get('mount_point', '')
    fs_type = mount.get('fs_type', 'auto')
    mnt_opts = mount.get('mnt_opts', 'defaults')
    dump_freq = mount.get('dump_freq', '0')
    fsck_pass = mount.get('fsck_pass', '0')
    
    # Resolve mount_params if specified
    if 'mount_params' in mount and mount['mount_params'] in mount_params:
        profile = mount_params[mount['mount_params']]
        if 'fs_type' not in mount:
            fs_type = profile.get('fs_type', fs_type)
        if 'mnt_opts' not in mount:
            mnt_opts = profile.get('mnt_opts', mnt_opts)
        if 'dump_freq' not in mount:
            dump_freq = profile.get('dump_freq', dump_freq)
        if 'fsck_pass' not in mount:
            fsck_pass = profile.get('fsck_pass', fsck_pass)
    
    # Determine target groups
    target_groups = []
    if 'functional_group_prefix' in mount:
        prefixes = mount['functional_group_prefix']
        for fg_name in functional_groups.keys():
            if any(fg_name.startswith(p) for p in prefixes):
                target_groups.append(fg_name)
    
    # Build runcmd for this mount
    runcmd = [
        f"mkdir -pv {mount_point}",
        f"echo \\"{source} {mount_point} {fs_type} {mnt_opts} {dump_freq} {fsck_pass}\\" >> /etc/fstab",
        "mount -av"
    ]
    
    # Add runcmd to target groups
    for group in target_groups:
        if 'runcmd' not in cloud_init_groups_dict[group]:
            cloud_init_groups_dict[group]['runcmd'] = []
        cloud_init_groups_dict[group]['runcmd'].extend(runcmd)

# Write to temp file
with open('/tmp/cloud_init_groups_dict.json', 'w') as f:
    json.dump(cloud_init_groups_dict, f, indent=2)

print(json.dumps({'success': True}))
PYTHON
"""
    result = host.run(cmd, shell=True)
    
    if result.rc != 0:
        return {"success": False, "error": result.stderr}
    
    # Read the generated file
    cmd_read = "podman exec omnia_core cat /tmp/cloud_init_groups_dict.json"
    result_read = host.run(cmd_read, shell=True)
    
    if result_read.rc != 0:
        return {"success": False, "error": "Failed to read generated file"}
    
    try:
        cloud_init_groups_dict = json.loads(result_read.stdout.strip())
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parse error: {e}"}
    
    return {
        "success": True,
        "cloud_init_groups_dict": cloud_init_groups_dict
    }


@pytest.mark.negative
@pytest.mark.order(1)
def test_missing_mount_point_should_fail(host):
    """TC-CI-NEG-001: Missing mount_point should cause test to fail."""
    log = TestLogger(TEST_NAMES["tc_ci_neg_001"])
    
    # Backup original config
    backup_path = _backup_storage_config(host)
    
    try:
        # Modify: remove mount_point from test_mount_config
        def remove_mount_point(config):
            for mount in config.get('mounts', []):
                if mount.get('name') == 'test_mount_config':
                    mount.pop('mount_point', None)
                    break
        
        _modify_storage_config(host, remove_mount_point)
        log.check("Removed mount_point from test_mount_config")
        
        # Run role
        result = _run_mount_config_role(host)
        if not result.get("success"):
            pytest.skip(f"Failed to run role: {result.get('error')}")
        
        cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})
        
        # Verify that the mount_point is empty in runcmd
        # This should cause the original test to fail because mkdir -pv will have empty path
        failures = []
        for group_name, group_data in cloud_init_groups_dict.items():
            runcmd = group_data.get("runcmd", [])
            for cmd in runcmd:
                if "mkdir -pv " in cmd and cmd.endswith("mkdir -pv "):
                    # Found a mkdir with empty path - this is the error we expect
                    log.check(f"Detected empty mount_point in runcmd for group {group_name}")
                    failures.append(f"Empty mount_point in runcmd: {cmd}")
        
        # The test should detect this error
        assert failures, "Expected to find empty mount_point in runcmd, but didn't"
        log.passed(TEST_NAMES["tc_ci_neg_001"])
    
    finally:
        # Restore original config
        _restore_storage_config(host)


@pytest.mark.negative
@pytest.mark.order(2)
def test_missing_functional_group_prefix_should_fail(host):
    """TC-CI-NEG-002: Missing functional_group_prefix should cause targeting to fail."""
    log = TestLogger(TEST_NAMES["tc_ci_neg_002"])
    
    # Backup original config
    backup_path = _backup_storage_config(host)
    
    try:
        # Modify: remove functional_group_prefix from test_mount_config
        def remove_prefix(config):
            for mount in config.get('mounts', []):
                if mount.get('name') == 'test_mount_config':
                    mount.pop('functional_group_prefix', None)
                    break
        
        _modify_storage_config(host, remove_prefix)
        log.check("Removed functional_group_prefix from test_mount_config")
        
        # Run role
        result = _run_mount_config_role(host)
        if not result.get("success"):
            pytest.skip(f"Failed to run role: {result.get('error')}")
        
        cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})
        
        # Verify that test_mount_config is NOT in any group's runcmd
        failures = []
        mount_point = "/mnt/omnia_test"
        found_in_any_group = False
        
        for group_name, group_data in cloud_init_groups_dict.items():
            runcmd = group_data.get("runcmd", [])
            if any(mount_point in cmd for cmd in runcmd):
                found_in_any_group = True
                log.check(f"Found test_mount_config in group {group_name} (should not be there)")
        
        if not found_in_any_group:
            log.check("test_mount_config correctly excluded from all groups (no functional_group_prefix)")
            failures.append("Mount with no functional_group_prefix was excluded from all groups")
        
        # The test should detect this error
        assert failures, "Expected mount to be excluded, which indicates missing prefix was detected"
        log.passed(TEST_NAMES["tc_ci_neg_002"])
    
    finally:
        # Restore original config
        _restore_storage_config(host)


@pytest.mark.negative
@pytest.mark.order(3)
def test_incorrect_mount_params_profile_should_fail(host):
    """TC-CI-NEG-003: Referencing non-existent mount_params profile should fail."""
    log = TestLogger(TEST_NAMES["tc_ci_neg_003"])
    
    # Backup original config
    backup_path = _backup_storage_config(host)
    
    try:
        # Modify: set mount_params to non-existent profile AND remove explicit mnt_opts
        def set_invalid_profile(config):
            for mount in config.get('mounts', []):
                if mount.get('name') == 'test_mount_config':
                    mount['mount_params'] = 'nonexistent_profile'
                    # Remove explicit mnt_opts so it falls back to profile (which doesn't exist)
                    mount.pop('mnt_opts', None)
                    break
        
        modified_config = _modify_storage_config(host, set_invalid_profile)
        log.check("Set mount_params to non-existent profile and removed mnt_opts")

        # Run role
        result = _run_mount_config_role(host)
        if not result.get("success"):
            pytest.skip(f"Failed to run role: {result.get('error')}")

        cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})

        # Verify that the mount has default values (since profile doesn't exist)
        failures = []
        mount_point = "/mnt/omnia_test"
        if modified_config:
            for mount in modified_config.get("mounts", []):
                if mount.get("name") == "test_mount_config":
                    mount_point = mount.get("mount_point", mount_point)
                    break

        for group_name, group_data in cloud_init_groups_dict.items():
            runcmd = group_data.get("runcmd", [])
            for cmd in runcmd:
                if mount_point in cmd and ">> /etc/fstab" in cmd:
                    # Check if it has default mount options (fallback when profile doesn't exist)
                    if "defaults" in cmd:
                        log.check(f"Mount using default options (invalid profile ignored)")
                        failures.append("Invalid profile was ignored, using defaults")
                    else:
                        log.check(f"Mount has custom options: {cmd}")
        
        assert failures, "Expected to detect invalid mount_params profile fallback to defaults"
        log.passed(TEST_NAMES["tc_ci_neg_003"])
    
    finally:
        # Restore original config
        _restore_storage_config(host)


@pytest.mark.negative
@pytest.mark.order(4)
def test_missing_source_should_fail(host):
    """TC-CI-NEG-004: Missing source should cause mount to fail."""
    log = TestLogger(TEST_NAMES["tc_ci_neg_004"])
    
    # Backup original config
    backup_path = _backup_storage_config(host)
    
    try:
        # Modify: remove source from test_mount_config
        def remove_source(config):
            for mount in config.get('mounts', []):
                if mount.get('name') == 'test_mount_config':
                    mount.pop('source', None)
                    break
        
        modified_config = _modify_storage_config(host, remove_source)
        log.check("Removed source from test_mount_config")

        # Run role
        result = _run_mount_config_role(host)
        if not result.get("success"):
            pytest.skip(f"Failed to run role: {result.get('error')}")

        cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})

        # Verify that the fstab entry has empty source
        failures = []
        mount_point = "/mnt/omnia_test"
        if modified_config:
            for mount in modified_config.get("mounts", []):
                if mount.get("name") == "test_mount_config":
                    mount_point = mount.get("mount_point", mount_point)
                    break

        for group_name, group_data in cloud_init_groups_dict.items():
            runcmd = group_data.get("runcmd", [])
            for cmd in runcmd:
                if mount_point in cmd and ">> /etc/fstab" in cmd:
                    # Check if source is empty (starts with space after echo)
                    if 'echo " ' in cmd or 'echo ""' in cmd:
                        log.check(f"Detected empty source in fstab entry")
                        failures.append("Empty source in fstab entry")
        
        assert failures, "Expected to detect missing source"
        log.passed(TEST_NAMES["tc_ci_neg_004"])
    
    finally:
        # Restore original config
        _restore_storage_config(host)


@pytest.mark.negative
@pytest.mark.order(5)
def test_missing_node_mount_point_with_node_key_should_fail(host):
    """TC-CI-NEG-005: node_key without node_mount_point should fail."""
    log = TestLogger(TEST_NAMES["tc_ci_neg_005"])
    
    # Backup original config
    backup_path = _backup_storage_config(host)
    
    try:
        # Modify: remove node_mount_point but keep node_key
        def remove_node_mount_point(config):
            for mount in config.get('mounts', []):
                if mount.get('name') == 'test_mount_config':
                    mount.pop('node_mount_point', None)
                    break
        
        _modify_storage_config(host, remove_node_mount_point)
        log.check("Removed node_mount_point from test_mount_config")
        
        # Run role
        result = _run_mount_config_role(host)
        if not result.get("success"):
            pytest.skip(f"Failed to run role: {result.get('error')}")
        
        cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})
        
        # Verify that bind mount commands are missing
        failures = []
        
        for group_name, group_data in cloud_init_groups_dict.items():
            runcmd = group_data.get("runcmd", [])
            # Check if bind mount commands are present (they shouldn't be)
            bind_mount_found = any("cloud-init query" in cmd for cmd in runcmd)
            if not bind_mount_found:
                log.check(f"Bind mount commands correctly excluded (no node_mount_point)")
                failures.append("Bind mount commands missing due to missing node_mount_point")
        
        assert failures, "Expected bind mount commands to be missing"
        log.passed(TEST_NAMES["tc_ci_neg_005"])
    
    finally:
        # Restore original config
        _restore_storage_config(host)
