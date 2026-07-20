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

"""Cloud-init content tests for mount_config role.

This module verifies that the mount_config role generates correct cloud-init
content (cloud_init_groups_dict and host_mount_map) without running the
actual commands on nodes.

Test cases:
  TC-CI-001: Mount entries generate correct runcmd
  TC-CI-002: Bind mount entries generate correct runcmd
  TC-CI-003: Functional group prefix targeting
  TC-CI-004: GROUP_NAME targeting (host_mount_map)
  TC-CI-005: Non-target groups have no entries
  TC-CI-006: Mount params profile resolution in runcmd
"""

import csv
import json
import pytest
from automation_library.core import TestLogger, run_in_container, PXE_MAPPING_FILE_PATH
from automation_library.mount_config.functions.mount_config_func import (
    read_storage_config,
    get_mounts_entries,
)

# Test names
TEST_NAMES = {
    "tc_ci_001": "TC-CI-001: Mount entries generate correct runcmd",
    "tc_ci_002": "TC-CI-002: Bind mount entries generate correct runcmd",
    "tc_ci_003": "TC-CI-003: Functional group prefix targeting",
    "tc_ci_004": "TC-CI-004: GROUP_NAME targeting (host_mount_map)",
    "tc_ci_005": "TC-CI-005: Non-target groups have no entries",
    "tc_ci_006": "TC-CI-006: Mount params profile resolution in runcmd",
}

TEST_ASSERT_MSGS = {
    "missing_runcmd": "Missing runcmd for group '{group}': {detail}",
    "missing_command": "Missing command in runcmd: {cmd}",
    "incorrect_fstab": "Incorrect fstab entry: expected '{expected}', got '{actual}'",
    "missing_group": "Group '{group}' not in cloud_init_groups_dict",
    "unexpected_group": "Unexpected group '{group}' has runcmd entries",
    "missing_hostname": "Hostname '{hostname}' not in host_mount_map",
    "missing_host_mount": "Missing mount in host_mount_map for '{hostname}'",
    "host_mount_missing": "Mount '{mount_name}' missing in host_mount_map for host '{hostname}' (group '{group}'): expected present, actual missing",
    "host_mount_unexpected": "Mount '{mount_name}' unexpectedly present in host_mount_map for host '{hostname}' (group '{group}'): expected missing, actual present",
}


def _read_group_host_map(host) -> dict:
    """Read PXE mapping and return GROUP_NAME -> [hostnames] mapping."""
    group_host_map = {}
    cmd = run_in_container(host, f"cat {PXE_MAPPING_FILE_PATH}")
    if cmd.rc != 0 or not cmd.stdout.strip():
        return group_host_map

    reader = csv.DictReader(cmd.stdout.strip().splitlines())
    for row in reader:
        group_name = row.get("GROUP_NAME", "").strip()
        hostname = row.get("HOSTNAME", "").strip()
        if group_name and hostname:
            if group_name not in group_host_map:
                group_host_map[group_name] = []
            group_host_map[group_name].append(hostname)

    return group_host_map


def _run_mount_config_role(host) -> dict:
    """Run mount_config role in check mode and extract cloud_init_groups_dict.

    Returns:
        {"cloud_init_groups_dict": {...}, "host_mount_map": {...}}
    """
    # Run a temporary playbook inside omnia_core that executes the mount_config role
    # and writes the generated variables to JSON files
    cmd = """
    podman exec -i omnia_core python3 - <<'PYTHON'
import json
import yaml
import sys
import os

# Add omnia provision roles to path
sys.path.insert(0, '/omnia/provision')

# Read required configs
with open('/opt/omnia/input/project_default/storage_config.yml') as f:
    storage_config = yaml.safe_load(f)

with open('/opt/omnia/input/project_default/software_config.json') as f:
    software_config = json.load(f)

with open('/opt/omnia/input/project_default/omnia_config.yml') as f:
    omnia_config = yaml.safe_load(f)

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

# Build group_host_map from pxe_mapping
group_host_map = {}
for row in pxe_mapping:
    group_name = row.get('GROUP_NAME', '')
    hostname = row.get('HOSTNAME', '')
    if group_name and hostname:
        if group_name not in group_host_map:
            group_host_map[group_name] = []
        group_host_map[group_name].append(hostname)

# Initialize variables
cloud_init_groups_dict = {}
host_mount_map = {}

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

    # Add bind mount runcmd if node_key is specified
    if 'node_key' in mount and 'node_mount_point' in mount:
        node_key = mount['node_key']
        node_mount_points = mount['node_mount_point']
        if isinstance(node_mount_points, str):
            node_mount_points = [node_mount_points]

        # Add bind mount commands
        for nmp in node_mount_points:
            runcmd.extend([
                f"mkdir -pv {mount_point}/\\$(cloud-init query local_hostname){nmp}",
                f"mkdir -pv {nmp}",
                f"echo \\"{mount_point}/\\$(cloud-init query local_hostname){nmp} {nmp} none bind,_netdev 0 0\\" >> /etc/fstab",
                "mount -av"
            ])

    # Add runcmd to target groups
    for group in target_groups:
        if 'runcmd' not in cloud_init_groups_dict[group]:
            cloud_init_groups_dict[group]['runcmd'] = []
        cloud_init_groups_dict[group]['runcmd'].extend(runcmd)

    # Handle groups (GROUP_NAME) targeting
    if 'groups' in mount:
        target_hostnames = []
        for group_name in mount['groups']:
            if group_name in group_host_map:
                target_hostnames.extend(group_host_map[group_name])

        for hostname in target_hostnames:
            if hostname not in host_mount_map:
                host_mount_map[hostname] = {'mounts': [], 'runcmd': []}

            # Add mount to host_mount_map
            mount_array = [source, mount_point, fs_type, mnt_opts, dump_freq, fsck_pass]
            host_mount_map[hostname]['mounts'].append(mount_array)
            host_mount_map[hostname]['runcmd'].extend(runcmd)

# Write to temp files
with open('/tmp/cloud_init_groups_dict.json', 'w') as f:
    json.dump(cloud_init_groups_dict, f, indent=2)

with open('/tmp/host_mount_map.json', 'w') as f:
    json.dump(host_mount_map, f, indent=2)

print(json.dumps({
    'success': True,
    'groups_count': len(cloud_init_groups_dict),
    'hosts_count': len(host_mount_map)
}))
PYTHON
"""
    result = host.run(cmd, shell=True)

    if result.rc != 0:
        return {"success": False, "error": result.stderr}

    # Read the generated files
    cmd_read_groups = "podman exec omnia_core cat /tmp/cloud_init_groups_dict.json"
    result_read_groups = host.run(cmd_read_groups, shell=True)

    cmd_read_hosts = "podman exec omnia_core cat /tmp/host_mount_map.json"
    result_read_hosts = host.run(cmd_read_hosts, shell=True)

    if result_read_groups.rc != 0 or result_read_hosts.rc != 0:
        return {"success": False, "error": "Failed to read generated files"}

    # Parse the two JSON objects
    try:
        cloud_init_groups_dict = json.loads(result_read_groups.stdout.strip())
        host_mount_map = json.loads(result_read_hosts.stdout.strip())
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parse error: {e}"}

    return {
        "success": True,
        "cloud_init_groups_dict": cloud_init_groups_dict,
        "host_mount_map": host_mount_map
    }


@pytest.mark.sanity
@pytest.mark.order(1)
def test_mount_entries_runcmd(host):
    """TC-CI-001: Verify mount entries generate correct runcmd."""
    log = TestLogger(TEST_NAMES["tc_ci_001"])
    failures = []

    # Get storage config
    storage_config = read_storage_config(host)
    mounts = get_mounts_entries(host)

    # Run role and get generated content
    result = _run_mount_config_role(host)
    if not result.get("success"):
        pytest.skip(f"Failed to run mount_config role: {result.get('error')}")

    cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})

    # Check each mount entry
    for mount in mounts:
        mount_name = mount.get("name", "")
        mount_point = mount.get("mount_point", "")
        source = mount.get("source", "")

        log.check(f"Verifying runcmd for mount '{mount_name}' at {mount_point}")

        # Get target groups
        target_groups = []
        if "functional_group_prefix" in mount:
            prefixes = mount["functional_group_prefix"]
            for group_name in cloud_init_groups_dict.keys():
                if any(group_name.startswith(p) for p in prefixes):
                    target_groups.append(group_name)

        # Verify runcmd in target groups
        for group in target_groups:
            if group not in cloud_init_groups_dict:
                failures.append(TEST_ASSERT_MSGS["missing_group"].format(group=group))
                continue

            runcmd = cloud_init_groups_dict[group].get("runcmd", [])

            # Check for mkdir command
            mkdir_found = any(f"mkdir -pv {mount_point}" in cmd for cmd in runcmd)
            if not mkdir_found:
                failures.append(
                    TEST_ASSERT_MSGS["missing_command"].format(
                        cmd=f"mkdir -pv {mount_point}"
                    )
                )

            # Check for fstab echo command
            fstab_found = any(mount_point in cmd and ">> /etc/fstab" in cmd for cmd in runcmd)
            if not fstab_found:
                failures.append(
                    TEST_ASSERT_MSGS["missing_command"].format(
                        cmd=f"echo ... {mount_point} ... >> /etc/fstab"
                    )
                )

            # Check for mount -av
            mount_av_found = any("mount -av" in cmd for cmd in runcmd)
            if not mount_av_found:
                failures.append(
                    TEST_ASSERT_MSGS["missing_command"].format(cmd="mount -av")
                )

            log.check(f"  Mount runcmd OK for group {group}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_ci_001"])


@pytest.mark.sanity
@pytest.mark.order(2)
def test_bind_mount_entries_runcmd(host):
    """TC-CI-002: Verify bind mount entries generate correct runcmd."""
    log = TestLogger(TEST_NAMES["tc_ci_002"])
    failures = []

    # Get storage config
    mounts = get_mounts_entries(host)

    # Run role and get generated content
    result = _run_mount_config_role(host)
    if not result.get("success"):
        pytest.skip(f"Failed to run mount_config role: {result.get('error')}")

    cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})

    # Check each mount with node_key
    for mount in mounts:
        if "node_key" not in mount or "node_mount_point" not in mount:
            continue

        mount_name = mount.get("name", "")
        mount_point = mount.get("mount_point", "")
        node_key = mount.get("node_key", "")
        node_mount_points = mount.get("node_mount_point", [])

        if isinstance(node_mount_points, str):
            node_mount_points = [node_mount_points]

        log.check(f"Verifying bind mount runcmd for '{mount_name}' with node_key={node_key}")

        # Get target groups
        target_groups = []
        if "functional_group_prefix" in mount:
            prefixes = mount["functional_group_prefix"]
            for group_name in cloud_init_groups_dict.keys():
                if any(group_name.startswith(p) for p in prefixes):
                    target_groups.append(group_name)

        # Verify bind mount runcmd in target groups
        for group in target_groups:
            if group not in cloud_init_groups_dict:
                failures.append(TEST_ASSERT_MSGS["missing_group"].format(group=group))
                continue

            runcmd = cloud_init_groups_dict[group].get("runcmd", [])

            # Check for bind mount commands
            for nmp in node_mount_points:
                mkdir_bind_found = any(
                    f"mkdir -pv {mount_point}" in cmd and "$(cloud-init query" in cmd
                    for cmd in runcmd
                )
                if not mkdir_bind_found:
                    failures.append(
                        TEST_ASSERT_MSGS["missing_command"].format(
                            cmd=f"mkdir -pv {mount_point}/$(cloud-init query ...){nmp}"
                        )
                    )

                fstab_bind_found = any(
                    f"{nmp}" in cmd and "bind" in cmd and ">> /etc/fstab" in cmd
                    for cmd in runcmd
                )
                if not fstab_bind_found:
                    failures.append(
                        TEST_ASSERT_MSGS["missing_command"].format(
                            cmd=f"echo ... {nmp} ... bind ... >> /etc/fstab"
                        )
                    )

            log.check(f"  Bind mount runcmd OK for group {group}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_ci_002"])


@pytest.mark.sanity
@pytest.mark.order(3)
def test_functional_group_prefix_targeting(host):
    """TC-CI-003: Verify functional_group_prefix targeting works correctly."""
    log = TestLogger(TEST_NAMES["tc_ci_003"])
    failures = []

    # Get storage config
    mounts = get_mounts_entries(host)

    # Run role and get generated content
    result = _run_mount_config_role(host)
    if not result.get("success"):
        pytest.skip(f"Failed to run mount_config role: {result.get('error')}")

    cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})

    # Check each mount with functional_group_prefix
    for mount in mounts:
        if "functional_group_prefix" not in mount:
            continue

        mount_name = mount.get("name", "")
        prefixes = mount["functional_group_prefix"]

        log.check(f"Verifying functional_group_prefix targeting for '{mount_name}' with prefixes={prefixes}")

        # Determine which groups should have this mount
        expected_groups = set()
        non_target_groups = set()

        for group_name in cloud_init_groups_dict.keys():
            if any(group_name.startswith(p) for p in prefixes):
                expected_groups.add(group_name)
            else:
                non_target_groups.add(group_name)

        # Verify target groups have runcmd
        for group in expected_groups:
            if "runcmd" not in cloud_init_groups_dict[group] or not cloud_init_groups_dict[group]["runcmd"]:
                failures.append(
                    TEST_ASSERT_MSGS["missing_runcmd"].format(
                        group=group, detail=f"mount '{mount_name}' not found"
                    )
                )
            else:
                log.check(f"  Group {group} has runcmd for mount '{mount_name}'")

        # Verify non-target groups do NOT have this mount's runcmd
        mount_point = mount.get("mount_point", "")
        for group in non_target_groups:
            runcmd = cloud_init_groups_dict[group].get("runcmd", [])
            if any(mount_point in cmd for cmd in runcmd):
                failures.append(
                    TEST_ASSERT_MSGS["unexpected_group"].format(
                        group=group
                    )
                )
            else:
                log.check(f"  Group {group} correctly excluded from mount '{mount_name}'")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_ci_003"])


@pytest.mark.sanity
@pytest.mark.order(4)
def test_group_name_targeting(host):
    """TC-CI-004: Verify GROUP_NAME targeting populates host_mount_map correctly."""
    log = TestLogger(TEST_NAMES["tc_ci_004"])
    failures = []

    # Get storage config and PXE group mapping
    mounts = get_mounts_entries(host)
    group_host_map = _read_group_host_map(host)

    # Run role and get generated content
    result = _run_mount_config_role(host)
    if not result.get("success"):
        pytest.skip(f"Failed to run mount_config role: {result.get('error')}")

    host_mount_map = result.get("host_mount_map", {})

    # Check each mount with groups field
    group_mounts_found = False
    for mount in mounts:
        if "groups" not in mount or not mount["groups"]:
            continue

        group_mounts_found = True
        mount_name = mount.get("name", "")
        groups = mount["groups"]
        mount_point = mount.get("mount_point", "")

        log.check(f"Verifying mount '{mount_name}' at {mount_point} with groups={groups}")

        # Determine expected hostnames from PXE mapping for the configured groups
        expected_hostnames = set()
        for group_name in groups:
            for hostname in group_host_map.get(group_name, []):
                expected_hostnames.add(hostname)
                log.check(f"  Expected target hostname: {hostname} (group '{group_name}')")

        if not expected_hostnames:
            log.check(f"  No hostnames found in PXE mapping for groups {groups}")
            continue

        # Determine actual hostnames that have this mount in host_mount_map
        actual_hostnames = set()
        for hostname, data in host_mount_map.items():
            for mount_entry in data.get("mounts", []):
                if len(mount_entry) > 1 and mount_entry[1] == mount_point:
                    actual_hostnames.add(hostname)
                    break

        # Verify each expected hostname is present in host_mount_map
        for hostname in sorted(expected_hostnames):
            if hostname in actual_hostnames:
                log.check(f"  ✓ Mount '{mount_name}' present in host_mount_map for host '{hostname}'")
            else:
                log.check(f"  ✗ Mount '{mount_name}' missing in host_mount_map for host '{hostname}'")
                # Report the first matching group for this hostname
                group_for_host = next(
                    (g for g in groups if hostname in group_host_map.get(g, [])),
                    "",
                )
                failures.append(
                    TEST_ASSERT_MSGS["host_mount_missing"].format(
                        mount_name=mount_name,
                        hostname=hostname,
                        group=group_for_host,
                    )
                )

        # Verify no unexpected hostname has this mount
        unexpected_hostnames = actual_hostnames - expected_hostnames
        for hostname in sorted(unexpected_hostnames):
            log.check(f"  ✗ Mount '{mount_name}' unexpectedly present in host_mount_map for host '{hostname}'")
            failures.append(
                TEST_ASSERT_MSGS["host_mount_unexpected"].format(
                    mount_name=mount_name,
                    hostname=hostname,
                    group=groups[0] if groups else "",
                )
            )

    if not group_mounts_found:
        pytest.skip("No mounts with groups field found in storage_config.yml")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_ci_004"])


@pytest.mark.sanity
@pytest.mark.order(5)
def test_non_target_groups_empty(host):
    """TC-CI-005: Verify non-target groups have no mount entries."""
    log = TestLogger(TEST_NAMES["tc_ci_005"])
    failures = []

    # Get storage config
    storage_config = read_storage_config(host)
    mounts = get_mounts_entries(host)

    # Run role and get generated content
    result = _run_mount_config_role(host)
    if not result.get("success"):
        pytest.skip(f"Failed to run mount_config role: {result.get('error')}")

    cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})

    # Collect all target groups
    all_target_groups = set()

    for mount in mounts:
        if "functional_group_prefix" in mount:
            prefixes = mount["functional_group_prefix"]
            for group_name in cloud_init_groups_dict.keys():
                if any(group_name.startswith(p) for p in prefixes):
                    all_target_groups.add(group_name)

    # Check non-target groups
    non_target_groups = set(cloud_init_groups_dict.keys()) - all_target_groups

    for group in non_target_groups:
        runcmd = cloud_init_groups_dict[group].get("runcmd", [])
        if runcmd:
            failures.append(
                f"Non-target group '{group}' unexpectedly has runcmd: {runcmd}"
            )
        else:
            log.check(f"  Non-target group {group} correctly has no runcmd")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_ci_005"])


@pytest.mark.sanity
@pytest.mark.order(6)
def test_mount_params_resolution(host):
    """TC-CI-006: Verify mount_params profile resolution in runcmd."""
    log = TestLogger(TEST_NAMES["tc_ci_006"])
    failures = []

    # Get storage config
    storage_config = read_storage_config(host)
    mounts = get_mounts_entries(host)
    mount_params = storage_config.get("mount_params", {})

    # Run role and get generated content
    result = _run_mount_config_role(host)
    if not result.get("success"):
        pytest.skip(f"Failed to run mount_config role: {result.get('error')}")

    cloud_init_groups_dict = result.get("cloud_init_groups_dict", {})

    # Check each mount with mount_params
    for mount in mounts:
        if "mount_params" not in mount:
            continue

        mount_name = mount.get("name", "")
        mount_params_key = mount["mount_params"]
        mount_point = mount.get("mount_point", "")

        if mount_params_key not in mount_params:
            log.check(f"  Mount '{mount_name}' references non-existent mount_params '{mount_params_key}'")
            continue

        profile = mount_params[mount_params_key]
        expected_mnt_opts = mount.get("mnt_opts") or profile.get("mnt_opts", "defaults")

        log.check(f"Verifying mount_params resolution for '{mount_name}' using profile '{mount_params_key}'")

        # Get target groups
        target_groups = []
        if "functional_group_prefix" in mount:
            prefixes = mount["functional_group_prefix"]
            for group_name in cloud_init_groups_dict.keys():
                if any(group_name.startswith(p) for p in prefixes):
                    target_groups.append(group_name)

        # Verify fstab entry in target groups
        for group in target_groups:
            runcmd = cloud_init_groups_dict[group].get("runcmd", [])

            # Find fstab entry for this mount
            fstab_found = False
            for cmd in runcmd:
                if mount_point in cmd and ">> /etc/fstab" in cmd:
                    # Verify mount_opts are in the fstab entry
                    if expected_mnt_opts in cmd:
                        fstab_found = True
                        log.check(f"  mount_params resolved correctly in group {group}")
                    else:
                        failures.append(
                            TEST_ASSERT_MSGS["incorrect_fstab"].format(
                                expected=expected_mnt_opts,
                                actual=cmd
                            )
                        )

            if not fstab_found and not failures:
                failures.append(
                    TEST_ASSERT_MSGS["missing_command"].format(
                        cmd=f"fstab entry with {expected_mnt_opts}"
                    )
                )

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_ci_006"])
