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

"""Mount configuration verification tests.

This module validates the generic `mounts` section in storage_config.yml
as provisioned by the `mount_config` role.

Test Cases:
  TC-MOUNT-001  test_mount_point_exists - mount point directory exists on target nodes
  TC-MOUNT-002  test_mount_is_active - mount is active in /proc/mounts
  TC-MOUNT-003  test_mount_options - mount options match configuration
  TC-MOUNT-004  test_mount_fstab - persistent fstab entry exists
  TC-MOUNT-005  test_mount_params_resolution - mount_params profile resolved correctly
  TC-MOUNT-006  test_mount_on_oim - mount_on_oim entries mounted on OIM
  TC-MOUNT-007  test_node_subdir - node-specific subdirectory exists when node_key is set
  TC-MOUNT-008  test_bind_mounts - node_key bind mounts are active
  TC-MOUNT-009  test_bind_fstab - bind mount fstab entries are persistent
  TC-MOUNT-010  test_bind_isolation - per-node bind mount data isolation
  TC-MOUNT-011  test_groups_targeting - mount is absent on non-target nodes
"""

import pytest

from automation_library.core import TestLogger
from automation_library.mount_config import (
    verify_mount_point_exists,
    verify_volume_mounted,
    verify_mount_options,
    verify_fstab_entry,
    verify_node_subdirectory,
    verify_bind_mounts,
    verify_bind_fstab_entries,
    verify_bind_isolation,
    verify_mount_on_oim,
    verify_mount_permissions,
    resolve_node_key_value,
)
from automation_library.mount_config.messages import (
    TEST_NAMES,
    TEST_ASSERT_MSGS,
    SUCCESS_MESSAGES,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _node_label(node):
    """Return 'hostname (ip)' display label for a node dict."""
    hostname = node.get("hostname", "")
    ip = node.get("admin_ip", "")
    return f"{hostname} ({ip})" if hostname else ip


def _log_and_assert(log, result, test_name):
    """Log per-item details and assert result."""
    if result.get("skipped"):
        log.check(result.get("message", ""))
        pytest.skip(result.get("message", ""))
        return

    if result["success"]:
        log.passed(SUCCESS_MESSAGES.get("mount_verified", "Verified"))
    else:
        log.failed(result.get("error", ""))

    assert result["success"], f"{test_name}: {result.get('error', '')}"


# =============================================================================
# TC-MOUNT-001: Mount point exists
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_mount_point_exists(host, resolved_mount_configs):
    """Verify mount point directories exist on target nodes."""
    log = TestLogger(TEST_NAMES["tc_mount_001"])
    failures = []

    for mount in resolved_mount_configs:
        mount_point = mount["mount_point"]
        log.check(f"Checking mount '{mount['name']}' at {mount_point}")
        for node in mount["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_mount_point_exists(host, node_ip, mount_point)
            if not result["success"]:
                failures.append(
                    TEST_ASSERT_MSGS["mount_point_missing"].format(
                        mount_point=mount_point, node_ip=label
                    )
                )
            else:
                log.check(f"  Mount point exists on {label}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_001"])


# =============================================================================
# TC-MOUNT-002: Mount is active
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_mount_is_active(host, resolved_mount_configs):
    """Verify mounts are active in /proc/mounts on target nodes."""
    log = TestLogger(TEST_NAMES["tc_mount_002"])
    failures = []

    for mount in resolved_mount_configs:
        mount_point = mount["mount_point"]
        log.check(f"Checking mount active for '{mount['name']}' at {mount_point}")
        for node in mount["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_volume_mounted(host, node_ip, mount_point)
            if not result["success"]:
                failures.append(
                    TEST_ASSERT_MSGS["mount_not_active"].format(
                        mount_point=mount_point, node_ip=label
                    )
                )
            else:
                log.check(f"  Mount active on {label}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_002"])


# =============================================================================
# TC-MOUNT-003: Mount options
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_mount_options(host, resolved_mount_configs):
    """Verify mount options match configuration on target nodes."""
    log = TestLogger(TEST_NAMES["tc_mount_003"])
    failures = []

    for mount in resolved_mount_configs:
        mount_point = mount["mount_point"]
        expected_opts = mount["mount_opts"]
        log.check(f"Checking mount options for '{mount['name']}' at {mount_point}")
        for node in mount["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_mount_options(host, node_ip, mount_point, expected_opts)
            if not result["success"]:
                failures.append(
                    TEST_ASSERT_MSGS["options_mismatch"].format(
                        mount_point=mount_point,
                        expected=expected_opts,
                        actual=result.get("details", {}).get("actual_opts", ""),
                    )
                )
            else:
                log.check(f"  Mount options OK on {label}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_003"])


# =============================================================================
# TC-MOUNT-004: Fstab persistence
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_mount_fstab(host, resolved_mount_configs):
    """Verify fstab entries exist for mount points on target nodes."""
    log = TestLogger(TEST_NAMES["tc_mount_004"])
    failures = []

    for mount in resolved_mount_configs:
        mount_point = mount["mount_point"]
        expected_fs = mount["fs_type"]
        expected_opts = mount["mount_opts"]
        log.check(f"Checking fstab for '{mount['name']}' at {mount_point}")
        for node in mount["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_fstab_entry(
                host, node_ip, mount_point, expected_fs, expected_opts
            )
            if not result["success"]:
                failures.append(
                    TEST_ASSERT_MSGS["fstab_missing"].format(
                        mount_point=mount_point, node_ip=label
                    )
                )
            else:
                log.check(f"  Fstab entry OK on {label}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_004"])


# =============================================================================
# TC-MOUNT-005: Mount params resolution
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_mount_params_resolution(host, resolved_mount_configs):
    """Verify mount_params profiles are resolved correctly."""
    log = TestLogger(TEST_NAMES["tc_mount_006"])
    failures = []

    for mount in resolved_mount_configs:
        if not mount["entry"].get("mount_params"):
            continue

        mount_point = mount["mount_point"]
        log.check(f"Checking mount_params resolution for '{mount['name']}'")
        for node in mount["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_mount_options(host, node_ip, mount_point, mount["mount_opts"])
            if not result["success"]:
                failures.append(
                    TEST_ASSERT_MSGS["options_mismatch"].format(
                        mount_point=mount_point,
                        expected=mount["mount_opts"],
                        actual=result.get("details", {}).get("actual_opts", ""),
                    )
                )
            else:
                log.check(f"  mount_params resolved OK on {label}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_006"])


# =============================================================================
# TC-MOUNT-006: mount_on_oim
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_mount_on_oim(host, resolved_mount_configs):
    """Verify mounts with mount_on_oim:true are mounted on the OIM host."""
    log = TestLogger(TEST_NAMES["tc_mount_009"])
    oim_mounts = [m for m in resolved_mount_configs if m["entry"].get("mount_on_oim")]

    if not oim_mounts:
        pytest.skip("No mounts with mount_on_oim configured")

    failures = []
    for mount in oim_mounts:
        result = verify_mount_on_oim(host, mount["entry"])
        if not result["success"]:
            failures.append(result["error"])
        else:
            log.check(f"OIM mount OK for {mount['mount_point']}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_009"])


# =============================================================================
# TC-MOUNT-007: Node subdirectory exists
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_node_subdir(host, resolved_mount_configs):
    """Verify node-specific subdirectories exist when node_key is set."""
    log = TestLogger(TEST_NAMES["tc_mount_010"])
    node_key_mounts = [m for m in resolved_mount_configs if m["node_key"]]

    if not node_key_mounts:
        pytest.skip("No mounts with node_key configured")

    failures = []
    for mount in node_key_mounts:
        mount_point = mount["mount_point"]
        node_key = mount["node_key"]
        log.check(f"Checking node subdirectory for '{mount['name']}'")
        for node in mount["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_node_subdirectory(host, node_ip, mount_point, node_key)
            if not result["success"]:
                failures.append(result["error"])
            else:
                log.check(f"  Subdirectory {result['details']['subdir']} OK on {label}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_010"])


# =============================================================================
# TC-MOUNT-008: Bind mounts active
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_bind_mounts(host, resolved_mount_configs):
    """Verify node_key bind mount targets are active on target nodes."""
    log = TestLogger(TEST_NAMES["tc_mount_011"])
    bind_mounts = [m for m in resolved_mount_configs if m["bind_targets"]]

    if not bind_mounts:
        pytest.skip("No mounts with node_mount_point configured")

    failures = []
    for mount in bind_mounts:
        mount_point = mount["mount_point"]
        bind_targets = mount["bind_targets"]
        node_key = mount["node_key"]
        log.check(f"Checking bind mounts for '{mount['name']}'")

        for node in mount["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            node_key_value = resolve_node_key_value(host, node_ip, node_key)
            if not node_key_value:
                failures.append(f"Could not resolve node_key '{node_key}' on {label}")
                continue

            result = verify_bind_mounts(
                host, node_ip, bind_targets, mount_point, node_key_value
            )
            if not result["success"]:
                failures.append(result["error"])
            else:
                log.check(f"  Bind mounts OK on {label}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_011"])


# =============================================================================
# TC-MOUNT-009: Bind mount fstab entries
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_bind_fstab(host, resolved_mount_configs):
    """Verify bind mount fstab entries are persistent."""
    log = TestLogger(TEST_NAMES["tc_mount_012"])
    bind_mounts = [m for m in resolved_mount_configs if m["bind_targets"]]

    if not bind_mounts:
        pytest.skip("No mounts with node_mount_point configured")

    failures = []
    for mount in bind_mounts:
        bind_targets = mount["bind_targets"]
        log.check(f"Checking bind fstab entries for '{mount['name']}'")
        for node in mount["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_bind_fstab_entries(host, node_ip, bind_targets)
            if not result["success"]:
                failures.append(result["error"])
            else:
                log.check(f"  Bind fstab OK on {label}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_012"])


# =============================================================================
# TC-MOUNT-010: Bind mount isolation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_bind_isolation(host, resolved_mount_configs):
    """Verify per-node bind mount data isolation (need 2 nodes)."""
    log = TestLogger(TEST_NAMES["tc_mount_013"])
    bind_mounts = [m for m in resolved_mount_configs if m["bind_targets"]]

    if not bind_mounts:
        pytest.skip("No mounts with node_mount_point configured")

    failures = []
    for mount in bind_mounts:
        bind_targets = mount["bind_targets"]
        if len(mount["target_nodes"]) < 2:
            log.check(f"Skipping isolation for '{mount['name']}' (only one target node)")
            continue

        node_a = mount["target_nodes"][0].get("admin_ip", "")
        node_b = mount["target_nodes"][1].get("admin_ip", "")
        log.check(f"Checking bind isolation for '{mount['name']}'")

        for bind_target in bind_targets:
            result = verify_bind_isolation(host, node_a, node_b, bind_target)
            if not result["success"]:
                failures.append(result["error"])
            else:
                log.check(f"  Isolation OK for {bind_target}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_013"])


# =============================================================================
# TC-MOUNT-011: Groups targeting (negative)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(11)
def test_groups_targeting(host, resolved_mount_configs):
    """Verify mounts are not present on non-target nodes."""
    log = TestLogger(TEST_NAMES["tc_mount_007"])
    failures = []

    from automation_library.mount_config import get_non_target_nodes_for_mount

    for mount in resolved_mount_configs:
        mount_point = mount["mount_point"]
        non_target_nodes = get_non_target_nodes_for_mount(host, mount["entry"])

        if not non_target_nodes:
            continue

        log.check(f"Checking non-target nodes for '{mount['name']}'")
        for node in non_target_nodes:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_mount_point_exists(host, node_ip, mount_point)
            if result["success"]:
                failures.append(
                    f"Mount point {mount_point} unexpectedly found on {label}"
                )
            else:
                log.check(f"  Not present on {label} as expected")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_mount_007"])
