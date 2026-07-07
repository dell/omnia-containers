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
PowerVault ME4/ME5 iSCSI Storage Validation Tests

Pre-Check:
  Reads storage_config.yml; all tests are skipped if 'powervault_config' is absent.
  All tests iterate over every powervault_config entry and its target nodes.

Test Cases:
  TC-PV-001  test_iscsid_service              - iscsid active and enabled on target nodes
  TC-PV-002  test_iscsi_initiator_name         - InitiatorName matches config
  TC-PV-003  test_iscsi_target_discovery       - iSCSI discovery from all portal IPs
  TC-PV-004  test_iscsi_sessions_active        - Active iSCSI sessions exist
  TC-PV-005  test_iscsi_startup_automatic      - node.startup = automatic
  TC-PV-006  test_iscsi_portal_reachability    - Portal IPs reachable on iSCSI port
  TC-PV-007  test_multipathd_service           - multipathd active and enabled
  TC-PV-008  test_multipath_device_exists      - Multipath device matches volume_id
  TC-PV-009  test_multipath_redundancy         - Multiple I/O paths per device
  TC-PV-010  test_gpt_partition                - GPT partition on multipath device
  TC-PV-011  test_filesystem_type              - Filesystem matches config fs_type
  TC-PV-012  test_mount_point_directory        - Mount point directory exists
  TC-PV-013  test_volume_mounted               - PV volume actively mounted
  TC-PV-014  test_mount_options                - Mount options applied correctly
  TC-PV-015  test_fstab_entry                  - Persistent fstab entry created
  TC-PV-016  test_node_subdirectory            - Per-node subdir under mount point
  TC-PV-017  test_bind_mounts                  - Bind mount targets active
  TC-PV-018  test_bind_fstab_entries           - Bind mount fstab entries persistent
  TC-PV-019  test_bind_isolation               - Per-node data separation via bind mounts
  TC-PV-020  test_functional_group_targeting   - PV mount only on correct groups
  TC-PV-021  test_multiple_prefix_targeting    - Multiple prefixes target all groups
  TC-PV-022  test_io_write_read                - Write/read I/O test on PV mount
  TC-PV-023  test_bind_io                      - Bind mount I/O test
  TC-PV-024  test_setup_log                    - Cloud-init runcmd log exists
  TC-PV-025  test_cloud_init_groups_dict       - powervault_scripts in groups dict
  TC-PV-026  test_no_duplicate_fstab           - No duplicate fstab entries
  TC-PV-027  test_slurm_mandatory_bind_mounts - Mandatory /var/lib/mysql & /var/spool/slurm mounts
  TC-PV-028  test_mysql_data_on_mount          - MySQL data directory on PV mount with slurm_acct_db
  TC-PV-029  test_all_mounts_writable          - All PV mounts (main + bind) are writable
"""

import pytest
from automation_library.core import TestLogger
from automation_library.powervault import (
    DEFAULT_ISCSI_PORT,
    DEFAULT_NODE_KEY,
    TEST_NAMES,
    TEST_ASSERT_MSGS,
    SUCCESS_MESSAGES,
)
from automation_library.powervault.functions import (
    resolve_node_key_value,
    verify_iscsi_service,
    verify_initiator_name,
    verify_iscsi_discovery,
    verify_iscsi_sessions,
    verify_iscsi_startup_automatic,
    verify_portal_reachability,
    verify_multipath_service,
    verify_multipath_device,
    verify_multipath_paths,
    verify_gpt_partition,
    verify_filesystem_type,
    verify_mount_point_exists,
    verify_volume_mounted,
    verify_mount_options,
    verify_fstab_entry,
    verify_node_subdirectory,
    verify_bind_mounts,
    verify_bind_fstab_entries,
    verify_bind_isolation,
    verify_functional_group_targeting,
    verify_multiple_prefix_targeting,
    verify_io_test,
    verify_bind_io_test,
    verify_setup_log,
    verify_cloud_init_groups_dict,
    verify_no_duplicate_fstab,
    verify_mount_writable,
    verify_slurm_mandatory_bind_mounts,
    verify_mysql_data_on_mount,
    SLURM_MANDATORY_BIND_MOUNTS,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _node_label(node):
    """Return 'hostname (ip)' display label for a node dict."""
    hostname = node.get("hostname", "")
    ip = node.get("admin_ip", "")
    return f"{hostname} ({ip})" if hostname else ip


# =============================================================================
# Category 1: iSCSI Infrastructure Validation (Target Nodes)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_iscsid_service(host, pv_configs):
    """
    TC-PV-001: Verify iSCSI daemon (iscsid) is enabled and running on all
    target nodes for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_001"])

    failures = []
    for pv in pv_configs:
        log.check(f"Checking PV '{pv['name']}' targets")
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_iscsi_service(host, node_ip)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["iscsid_active"].format(
                    node_ip=label, actual=result.get("error", "not active/enabled")
                ))
            else:
                log.check(SUCCESS_MESSAGES["iscsid_verified"].format(node_ip=label))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_001"])


@pytest.mark.sanity
@pytest.mark.order(2)
def test_iscsi_initiator_name(host, pv_configs):
    """
    TC-PV-002: Verify iSCSI initiator name configured correctly on all
    target nodes for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_002"])

    failures = []
    for pv in pv_configs:
        expected_iqn = pv["iscsi_initiator"]
        if not expected_iqn:
            log.check(f"Skipping PV '{pv['name']}' — no iscsi_initiator set")
            continue

        log.check(f"Checking PV '{pv['name']}' initiator: {expected_iqn}")
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_initiator_name(host, node_ip, expected_iqn)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["initiator_match"].format(
                    expected=expected_iqn,
                    actual=result["details"].get("actual", "unknown"),
                    node_ip=label,
                ))
            else:
                log.check(SUCCESS_MESSAGES["initiator_verified"].format(node_ip=label))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_002"])


@pytest.mark.sanity
@pytest.mark.order(3)
def test_iscsi_target_discovery(host, pv_configs):
    """
    TC-PV-003: Verify iSCSI target discovery succeeds from all portal IPs
    for every powervault_config entry on all target nodes.
    """
    log = TestLogger(TEST_NAMES["tc_pv_003"])

    failures = []
    for pv in pv_configs:
        ip_list = pv["ip_list"]
        if not ip_list:
            log.check(f"Skipping PV '{pv['name']}' — no portal IPs")
            continue

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            log.check(f"Checking PV '{pv['name']}' discovery on {label}")
            result = verify_iscsi_discovery(host, node_ip, ip_list, pv["port"])

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["discovery_success"].format(
                    portal_ip=", ".join(ip_list), port=pv["port"],
                    actual=result.get("error", "no IQN discovered"),
                ))
            else:
                log.check(f"Discovered IQN: {result['details']['discovered_iqn']}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_003"])


@pytest.mark.sanity
@pytest.mark.order(4)
def test_iscsi_sessions_active(host, pv_configs):
    """
    TC-PV-004: Verify iSCSI sessions are active on all target nodes
    per powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_004"])

    failures = []
    for pv in pv_configs:
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            log.check(f"Checking PV '{pv['name']}' sessions on {label}")
            result = verify_iscsi_sessions(host, node_ip)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["session_active"].format(
                    node_ip=label,
                    actual=f"{result['details'].get('session_count', 0)} sessions",
                ))
            else:
                log.check(f"Active sessions: {result['details']['session_count']}")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_004"])


@pytest.mark.sanity
@pytest.mark.order(5)
def test_iscsi_startup_automatic(host, pv_configs):
    """
    TC-PV-005: Verify iSCSI node startup set to automatic on all target nodes
    for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_005"])

    failures = []
    for pv in pv_configs:
        log.check(f"Checking PV '{pv['name']}' targets")
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_iscsi_startup_automatic(host, node_ip)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["startup_automatic"].format(
                    node_ip=label,
                    actual=result.get("error", "not automatic"),
                ))
            else:
                log.check(SUCCESS_MESSAGES["startup_verified"].format(node_ip=label))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_005"])


@pytest.mark.sanity
@pytest.mark.order(6)
def test_iscsi_portal_reachability(host, pv_configs):
    """
    TC-PV-006: Verify iSCSI portal port reachability for every powervault_config entry
    from all target nodes.
    """
    log = TestLogger(TEST_NAMES["tc_pv_006"])

    failures = []
    for pv in pv_configs:
        ip_list = pv["ip_list"]
        if not ip_list:
            log.check(f"Skipping PV '{pv['name']}' — no portal IPs")
            continue

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            log.check(f"Checking PV '{pv['name']}' portal reachability from {label}")
            result = verify_portal_reachability(host, node_ip, ip_list, pv["port"])

            for r in result["details"]["results"]:
                if not r["reachable"]:
                    failures.append(TEST_ASSERT_MSGS["port_reachable"].format(
                        port=pv["port"], portal_ip=r["portal_ip"], node_ip=label,
                        actual="unreachable",
                    ))
                if not r.get("session_healthy", True):
                    failures.append(TEST_ASSERT_MSGS["portal_session_healthy"].format(
                        portal_ip=r["portal_ip"], node_ip=label,
                        actual=r.get("session_state", "UNKNOWN"),
                    ))

            if result["success"]:
                log.check(SUCCESS_MESSAGES["ports_verified"].format(node_ip=label))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_006"])


# =============================================================================
# Category 2: Multipath Validation (Target Nodes)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_multipathd_service(host, pv_configs):
    """
    TC-PV-007: Verify multipathd service is enabled and running on all
    target nodes for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_007"])

    failures = []
    for pv in pv_configs:
        log.check(f"Checking PV '{pv['name']}' targets")
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_multipath_service(host, node_ip)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["multipathd_active"].format(
                    node_ip=label, actual=result.get("error", "not active/enabled")
                ))
            else:
                log.check(SUCCESS_MESSAGES["multipathd_verified"].format(node_ip=label))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_007"])


@pytest.mark.sanity
@pytest.mark.order(8)
def test_multipath_device_exists(host, pv_configs):
    """
    TC-PV-008: Verify multipath device exists and matches volume_id
    on all target nodes for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_008"])

    failures = []
    for pv in pv_configs:
        volume_id = pv["volume_id"]
        if not volume_id:
            log.check(f"Skipping PV '{pv['name']}' — no volume_id")
            continue

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            log.check(f"Checking PV '{pv['name']}' volume_id on {label}")
            result = verify_multipath_device(host, node_ip, volume_id)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["mpath_device_exists"].format(
                    volume_id=volume_id, node_ip=label,
                    actual=result.get("error", "not found"),
                ))
            else:
                log.check(SUCCESS_MESSAGES["mpath_device_verified"].format(
                    device=result["details"]["mpath_device"], node_ip=label
                ))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_008"])


@pytest.mark.sanity
@pytest.mark.order(9)
def test_multipath_redundancy(host, pv_configs):
    """
    TC-PV-009: Verify multipath device has multiple paths (redundancy)
    on all target nodes for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_009"])

    failures = []
    for pv in pv_configs:
        volume_id = pv["volume_id"]
        ip_list = pv["ip_list"]
        expected_paths = max(len(ip_list), 1)

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            mpath_result = verify_multipath_device(host, node_ip, volume_id)
            if not mpath_result["success"]:
                log.check(f"Skipping PV '{pv['name']}' on {label} — mpath device not found")
                continue

            mpath_device = mpath_result["details"]["mpath_device"]
            result = verify_multipath_paths(host, node_ip, mpath_device, expected_paths)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["mpath_has_paths"].format(
                    expected=expected_paths,
                    actual=result["details"]["path_count"],
                    node_ip=label,
                ))
            else:
                log.check(SUCCESS_MESSAGES["mpath_paths_verified"].format(
                    count=result["details"]["path_count"], node_ip=label
                ))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_009"])


# =============================================================================
# Category 3: Partition, Filesystem, and Mount Validation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_gpt_partition(host, pv_configs):
    """
    TC-PV-010: Verify GPT partition exists on multipath device
    on all target nodes for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_010"])

    failures = []
    for pv in pv_configs:
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            mpath_result = verify_multipath_device(host, node_ip, pv["volume_id"])
            if not mpath_result["success"]:
                log.check(f"Skipping PV '{pv['name']}' on {label} — mpath device not found")
                continue

            mpath_device = mpath_result["details"]["mpath_device"]
            result = verify_gpt_partition(host, node_ip, mpath_device)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["gpt_partition_exists"].format(
                    device=mpath_device, node_ip=label,
                    actual=result.get("error", "no GPT partition"),
                ))
            else:
                log.check(SUCCESS_MESSAGES["partition_verified"].format(node_ip=label))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_010"])


@pytest.mark.sanity
@pytest.mark.order(11)
def test_filesystem_type(host, pv_configs):
    """
    TC-PV-011: Verify filesystem formatted with correct type
    on all target nodes for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_011"])

    failures = []
    for pv in pv_configs:
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            mpath_result = verify_multipath_device(host, node_ip, pv["volume_id"])
            if not mpath_result["success"]:
                log.check(f"Skipping PV '{pv['name']}' on {label} — mpath device not found")
                continue

            mpath_device = mpath_result["details"]["mpath_device"]
            result = verify_filesystem_type(host, node_ip, mpath_device, pv["fs_type"])

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["fs_type_match"].format(
                    expected=pv["fs_type"],
                    actual=result["details"].get("actual_fs", "unknown"),
                    node_ip=label,
                ))
            else:
                log.check(SUCCESS_MESSAGES["fs_type_verified"].format(
                    fs_type=pv["fs_type"], node_ip=label
                ))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_011"])


@pytest.mark.sanity
@pytest.mark.order(12)
def test_mount_point_directory(host, pv_configs):
    """
    TC-PV-012: Verify mount point directory exists on all target nodes
    for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_012"])

    failures = []
    for pv in pv_configs:
        mount_point = pv["mount_point"]
        if not mount_point:
            log.check(f"Skipping PV '{pv['name']}' — no mount_point")
            continue

        log.check(f"Checking PV '{pv['name']}' mount_point={mount_point}")
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_mount_point_exists(host, node_ip, mount_point)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["mount_point_exists"].format(
                    mount_point=mount_point, node_ip=label,
                    actual="directory not found",
                ))
            else:
                log.check(SUCCESS_MESSAGES["mount_point_verified"].format(
                    mount_point=mount_point, node_ip=label
                ))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_012"])


@pytest.mark.sanity
@pytest.mark.order(13)
def test_volume_mounted(host, pv_configs):
    """
    TC-PV-013: Verify PowerVault volume is actively mounted on all target nodes
    for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_013"])

    failures = []
    for pv in pv_configs:
        mount_point = pv["mount_point"]
        if not mount_point:
            log.check(f"Skipping PV '{pv['name']}' — no mount_point")
            continue

        log.check(f"Checking PV '{pv['name']}' volume mount at {mount_point}")
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_volume_mounted(host, node_ip, mount_point)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["volume_mounted"].format(
                    mount_point=mount_point, node_ip=label,
                    actual="not mounted",
                ))
            else:
                log.check(SUCCESS_MESSAGES["volume_mount_verified"].format(
                    mount_point=mount_point, node_ip=label
                ))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_013"])


@pytest.mark.sanity
@pytest.mark.order(14)
def test_mount_options(host, pv_configs):
    """
    TC-PV-014: Verify mount options applied correctly on all target nodes
    for every powervault_config entry.
    Kernel-visible options checked in /proc/mounts; userspace options (_netdev, nofail) in fstab.
    """
    log = TestLogger(TEST_NAMES["tc_pv_014"])

    failures = []
    for pv in pv_configs:
        mount_point = pv["mount_point"]
        if not mount_point:
            log.check(f"Skipping PV '{pv['name']}' — no mount_point")
            continue

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            log.check(f"Checking PV '{pv['name']}' mount options on {label}")
            result = verify_mount_options(host, node_ip, mount_point, pv["mount_opts"])

            if not result["success"]:
                failures.append(
                    f"Mount options mismatch for PV '{pv['name']}' on {label}. "
                    f"Expected: {pv['mount_opts']}, "
                    f"Actual: {result['details'].get('actual_opts', 'unknown')}"
                )
            else:
                log.check(SUCCESS_MESSAGES["mount_opts_verified"].format(
                    mount_point=mount_point, node_ip=label
                ))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_014"])


@pytest.mark.sanity
@pytest.mark.order(15)
def test_fstab_entry(host, pv_configs):
    """
    TC-PV-015: Verify persistent fstab entry created on all target nodes
    for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_015"])

    failures = []
    for pv in pv_configs:
        mount_point = pv["mount_point"]
        if not mount_point:
            log.check(f"Skipping PV '{pv['name']}' — no mount_point")
            continue

        log.check(f"Checking PV '{pv['name']}' fstab for {mount_point}")
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_fstab_entry(host, node_ip, mount_point, expected_fs=pv["fs_type"])

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["fstab_entry_exists"].format(
                    mount_point=mount_point, node_ip=label,
                    actual=result.get("error", "entry not found"),
                ))
            else:
                log.check(SUCCESS_MESSAGES["fstab_verified"].format(
                    mount_point=mount_point, node_ip=label
                ))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_015"])


# =============================================================================
# Category 4: Bind Mount Validation (node_key + node_mount_point)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(16)
def test_node_subdirectory(host, pv_configs):
    """
    TC-PV-016: Verify node-specific subdirectory exists under mount point
    for every powervault_config entry with node_key defined.
    """
    log = TestLogger(TEST_NAMES["tc_pv_016"])

    tested_any = False
    failures = []
    for pv in pv_configs:
        node_key = pv["node_key"]
        if not node_key:
            log.check(f"Skipping PV '{pv['name']}' — no node_key")
            continue

        mount_point = pv["mount_point"]
        tested_any = True
        log.check(f"Checking PV '{pv['name']}' node subdirs under {mount_point}")

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_node_subdirectory(host, node_ip, mount_point, node_key)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["node_subdir_exists"].format(
                    subdir=result["details"].get("subdir", "unknown"), node_ip=label,
                    actual="directory not found",
                ))
            else:
                log.check(SUCCESS_MESSAGES["node_subdir_verified"].format(node_ip=label))

    if not tested_any:
        pytest.skip("No PV entries have node_key defined")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_016"])


@pytest.mark.sanity
@pytest.mark.order(17)
def test_bind_mounts(host, pv_configs):
    """
    TC-PV-017: Verify bind mount targets exist and are mounted
    for every powervault_config entry with node_key and node_mount_point.
    """
    log = TestLogger(TEST_NAMES["tc_pv_017"])

    tested_any = False
    failures = []
    for pv in pv_configs:
        node_key = pv["node_key"]
        bind_targets = pv["bind_targets"]
        if not node_key or not bind_targets:
            log.check(f"Skipping PV '{pv['name']}' — no bind mounts configured")
            continue

        mount_point = pv["mount_point"]
        tested_any = True
        log.check(f"Checking PV '{pv['name']}' bind mounts: {bind_targets}")

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            node_key_value = resolve_node_key_value(host, node_ip, node_key)
            if not node_key_value:
                failures.append(f"Could not resolve node_key '{node_key}' on {label}")
                continue

            result = verify_bind_mounts(host, node_ip, bind_targets, mount_point, node_key_value)

            for bind_result in result["details"]["results"]:
                bt = bind_result["bind_target"]
                if not bind_result["source_exists"]:
                    failures.append(TEST_ASSERT_MSGS["bind_source_exists"].format(
                        source=bind_result["source"], node_ip=label,
                        actual="source not found",
                    ))
                if not bind_result["target_exists"]:
                    failures.append(TEST_ASSERT_MSGS["bind_target_exists"].format(
                        target=bt, node_ip=label,
                        actual="target not found",
                    ))
                elif not bind_result["is_mountpoint"]:
                    failures.append(TEST_ASSERT_MSGS["bind_target_mounted"].format(
                        target=bt, node_ip=label,
                        actual="not a mountpoint",
                    ))

            if result["success"]:
                log.check(SUCCESS_MESSAGES["bind_mounts_verified"].format(node_ip=label))

    if not tested_any:
        pytest.skip("No PV entries have bind mounts configured")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_017"])


@pytest.mark.sanity
@pytest.mark.order(18)
def test_bind_fstab_entries(host, pv_configs):
    """
    TC-PV-018: Verify bind mount fstab entries are persistent
    for every powervault_config entry with node_mount_point.
    """
    log = TestLogger(TEST_NAMES["tc_pv_018"])

    tested_any = False
    failures = []
    for pv in pv_configs:
        bind_targets = pv["bind_targets"]
        if not bind_targets:
            log.check(f"Skipping PV '{pv['name']}' — no bind mounts")
            continue

        tested_any = True
        log.check(f"Checking PV '{pv['name']}' bind fstab entries")

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_bind_fstab_entries(host, node_ip, bind_targets)

            for bind_result in result["details"]["results"]:
                if not bind_result["found"]:
                    failures.append(TEST_ASSERT_MSGS["bind_fstab_entry"].format(
                        target=bind_result["bind_target"], node_ip=label,
                        actual="entry not found",
                    ))

            if result["success"]:
                log.check(SUCCESS_MESSAGES["bind_fstab_verified"].format(node_ip=label))

    if not tested_any:
        pytest.skip("No PV entries have bind mounts configured")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_018"])


@pytest.mark.sanity
@pytest.mark.order(19)
def test_bind_isolation(host, pv_configs):
    """
    TC-PV-019: Verify bind mount isolation (per-node data separation)
    for every powervault_config entry with bind mounts and >= 2 target nodes.
    """
    log = TestLogger(TEST_NAMES["tc_pv_019"])

    tested_any = False
    failures = []
    for pv in pv_configs:
        bind_targets = pv["bind_targets"]
        if not bind_targets:
            log.check(f"Skipping PV '{pv['name']}' — no bind mounts")
            continue

        if len(pv["target_nodes"]) < 2:
            log.check(f"Skipping PV '{pv['name']}' — need >= 2 target nodes")
            continue

        tested_any = True
        node_a = pv["target_nodes"][0]
        node_b = pv["target_nodes"][1]
        node_a_ip = node_a.get("admin_ip", "")
        node_b_ip = node_b.get("admin_ip", "")
        label_a = _node_label(node_a)
        label_b = _node_label(node_b)
        bind_target = bind_targets[0]

        log.check(f"Checking PV '{pv['name']}' bind isolation: {label_a} vs {label_b}")
        result = verify_bind_isolation(host, node_a_ip, node_b_ip, bind_target)

        if not result["success"]:
            failures.append(TEST_ASSERT_MSGS["bind_isolation"].format(
                node_a=label_a, node_b=label_b, path=bind_target,
                actual="file visible on both nodes",
            ))
        else:
            log.check(SUCCESS_MESSAGES["bind_isolation_verified"])

    if not tested_any:
        pytest.skip("No PV entries qualify for bind isolation test")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_019"])


# =============================================================================
# Category 5: Functional Group Targeting
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(20)
def test_functional_group_targeting(host, pv_configs):
    """
    TC-PV-020: Verify PowerVault mounted only on correct functional groups
    for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_020"])

    failures = []
    for pv in pv_configs:
        prefix_list = pv["prefix_list"]
        if not prefix_list:
            log.check(f"Skipping PV '{pv['name']}' — no prefix")
            continue

        log.check(f"Checking PV '{pv['name']}' group targeting: {prefix_list}")
        result = verify_functional_group_targeting(host, pv["entry"])

        for tr in result["details"]["target_results"]:
            if not tr["mounted"]:
                failures.append(TEST_ASSERT_MSGS["mount_present_on_target"].format(
                    mount_point=pv["mount_point"],
                    node_ip=tr["node_ip"],
                    actual="not mounted",
                ))

        for ntr in result["details"]["non_target_results"]:
            if ntr["mounted"]:
                failures.append(TEST_ASSERT_MSGS["mount_absent_on_non_target"].format(
                    mount_point=pv["mount_point"],
                    node_ip=ntr["node_ip"],
                    actual="mounted (should not be)",
                ))

        if result["success"]:
            log.check(SUCCESS_MESSAGES["group_targeting_verified"].format(name=pv["name"]))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_020"])


@pytest.mark.sanity
@pytest.mark.order(21)
def test_multiple_prefix_targeting(host, pv_configs):
    """
    TC-PV-021: Verify multiple functional group prefixes target all matching groups
    for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_021"])

    failures = []
    for pv in pv_configs:
        prefix_list = pv["prefix_list"]
        if not prefix_list:
            log.check(f"Skipping PV '{pv['name']}' — no prefix")
            continue

        log.check(f"Checking PV '{pv['name']}' multi-prefix targeting: {prefix_list}")
        result = verify_multiple_prefix_targeting(host, pv["entry"])

        for pr in result["details"]["prefix_results"]:
            if not pr["mounted"]:
                failures.append(TEST_ASSERT_MSGS["all_prefix_groups_targeted"].format(
                    actual=f"not mounted on {pr.get('node_ip', 'unknown')} (group={pr.get('group', '')})",
                ))
            else:
                log.check(f"Group '{pr['group']}' (prefix '{pr['prefix']}') has mount on {pr['node_ip']}")

        if result["success"]:
            log.check(SUCCESS_MESSAGES["multi_prefix_verified"].format(name=pv["name"]))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_021"])


# =============================================================================
# Category 6: I/O and Data Integrity
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(22)
def test_io_write_read(host, pv_configs):
    """
    TC-PV-022: Verify write/read test on PowerVault mount
    on all target nodes for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_022"])

    failures = []
    for pv in pv_configs:
        mount_point = pv["mount_point"]
        if not mount_point:
            log.check(f"Skipping PV '{pv['name']}' — no mount_point")
            continue

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            log.check(f"Checking PV '{pv['name']}' I/O on {label}")
            result = verify_io_test(host, node_ip, mount_point)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["io_checksum_match"].format(
                    node_ip=label,
                    actual=result.get("error", "checksum mismatch"),
                ))
            else:
                log.check(SUCCESS_MESSAGES["io_test_verified"].format(
                    mount_point=mount_point, node_ip=label
                ))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_022"])


@pytest.mark.sanity
@pytest.mark.order(23)
def test_bind_io(host, pv_configs):
    """
    TC-PV-023: Verify bind mount I/O test on all target nodes
    for every powervault_config entry with bind mounts configured.
    """
    log = TestLogger(TEST_NAMES["tc_pv_023"])

    tested_any = False
    failures = []
    for pv in pv_configs:
        bind_targets = pv["bind_targets"]
        node_key = pv["node_key"]
        if not bind_targets or not node_key:
            log.check(f"Skipping PV '{pv['name']}' — no bind mounts")
            continue

        mount_point = pv["mount_point"]
        bind_target = bind_targets[0]

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            node_key_value = resolve_node_key_value(host, node_ip, node_key)
            if not node_key_value:
                log.check(f"Skipping PV '{pv['name']}' on {label} — could not resolve node_key")
                continue

            tested_any = True
            log.check(f"Checking PV '{pv['name']}' bind I/O on {label}")
            result = verify_bind_io_test(
                host, node_ip, bind_target, mount_point, node_key_value
            )

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["bind_io_read_match"].format(
                    node_ip=label,
                    actual=result.get("error", "data mismatch"),
                ))
            else:
                log.check(SUCCESS_MESSAGES["bind_io_verified"].format(node_ip=label))

    if not tested_any:
        pytest.skip("No PV entries qualify for bind I/O test")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_023"])


# =============================================================================
# Category 7: Cloud-Init Integration and Logging
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(24)
def test_setup_log(host, pv_configs):
    """
    TC-PV-024: Verify cloud-init runcmd script execution log exists
    for every powervault_config entry on all target nodes.
    """
    log = TestLogger(TEST_NAMES["tc_pv_024"])

    failures = []
    for pv in pv_configs:
        pv_name = pv["name"]
        if not pv_name:
            log.check("Skipping PV entry with no name")
            continue

        log.check(f"Checking PV '{pv_name}' setup logs")
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_setup_log(host, node_ip, pv_name)

            if not result["details"]["log_exists"]:
                failures.append(TEST_ASSERT_MSGS["setup_log_exists"].format(
                    name=pv_name, node_ip=label,
                    actual="log file not found",
                ))
            elif not result["details"]["complete"]:
                failures.append(TEST_ASSERT_MSGS["setup_log_complete"].format(
                    node_ip=label,
                    actual="completion marker missing",
                ))
            elif len(result["details"]["errors"]) > 0:
                failures.append(TEST_ASSERT_MSGS["setup_log_no_errors"].format(
                    node_ip=label,
                    actual=f"{len(result['details']['errors'])} errors: {result['details']['errors'][:3]}",
                ))
            else:
                log.check(SUCCESS_MESSAGES["setup_log_verified"].format(
                    name=pv_name, node_ip=label
                ))

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_024"])


@pytest.mark.sanity
@pytest.mark.order(25)
def test_cloud_init_groups_dict(host, pv_configs):
    """
    TC-PV-025: Verify cloud_init_groups_dict contains powervault_scripts
    for every powervault_config entry.
    """
    log = TestLogger(TEST_NAMES["tc_pv_025"])

    failures = []
    for pv in pv_configs:
        log.check(f"Checking PV '{pv['name']}' cloud-init integration")
        result = verify_cloud_init_groups_dict(host, pv["entry"])

        if not result["success"]:
            failures.append(
                f"Cloud-init groups dict check failed for PV '{pv['name']}'. "
                f"Expected: template, task, and config entry present. "
                f"Actual: template_exists={result['details'].get('template_exists')}, "
                f"task_exists={result['details'].get('task_exists')}, "
                f"name_in_config={result['details'].get('name_in_config')}"
            )
        else:
            log.check(SUCCESS_MESSAGES["cloud_init_dict_verified"])

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_025"])


# =============================================================================
# Category 8: Error Handling and Edge Cases
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(26)
def test_no_duplicate_fstab(host, pv_configs):
    """
    TC-PV-026: Verify no duplicate fstab entries for every powervault_config entry
    on all target nodes.
    Uses exact field matching to avoid false positives from bind mount source paths.
    """
    log = TestLogger(TEST_NAMES["tc_pv_026"])

    failures = []
    for pv in pv_configs:
        mount_point = pv["mount_point"]
        if not mount_point:
            log.check(f"Skipping PV '{pv['name']}' — no mount_point")
            continue

        log.check(f"Checking PV '{pv['name']}' fstab duplicates for {mount_point}")
        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_no_duplicate_fstab(host, node_ip, mount_point)

            if not result["success"]:
                failures.append(TEST_ASSERT_MSGS["no_duplicate_fstab"].format(
                    mount_point=mount_point,
                    node_ip=label,
                    count=result["details"]["count"],
                ))

        # Also check bind mount fstab entries for duplicates
        for bind_target in pv["bind_targets"]:
            for node in pv["target_nodes"]:
                node_ip = node.get("admin_ip", "")
                label = _node_label(node)
                result = verify_no_duplicate_fstab(host, node_ip, bind_target)

                if not result["success"]:
                    failures.append(TEST_ASSERT_MSGS["no_duplicate_fstab"].format(
                        mount_point=bind_target,
                        node_ip=label,
                        count=result["details"]["count"],
                    ))

    assert not failures, "\n".join(failures)
    log.check(SUCCESS_MESSAGES["no_duplicate_fstab_verified"].format(
        node_ip="all target nodes"
    ))
    log.passed(TEST_NAMES["tc_pv_026"])


# =============================================================================
# Category 9: Slurm-Specific PowerVault Validation
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(27)
def test_slurm_mandatory_bind_mounts(host, pv_configs):
    """
    TC-PV-027: Verify mandatory bind mounts (/var/lib/mysql, /var/spool/slurm)
    are configured and active on all slurm_control_node targets.
    Only applies to PV entries whose functional_group_prefix includes
    'slurm_control_node'.
    """
    log = TestLogger(TEST_NAMES["tc_pv_027"])

    tested_any = False
    failures = []
    for pv in pv_configs:
        prefix_list = pv["prefix_list"]
        is_slurm = any(p.startswith("slurm_control_node") for p in prefix_list)
        if not is_slurm:
            log.check(f"Skipping PV '{pv['name']}' — not a slurm_control_node entry")
            continue

        tested_any = True
        bind_targets = pv["bind_targets"]
        log.check(
            f"Checking PV '{pv['name']}' mandatory slurm bind mounts: "
            f"{SLURM_MANDATORY_BIND_MOUNTS}"
        )

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_slurm_mandatory_bind_mounts(host, node_ip, bind_targets)

            for r in result["details"]["results"]:
                if not r["success"]:
                    failures.append(
                        TEST_ASSERT_MSGS["slurm_mandatory_bind_present"].format(
                            path=r["path"],
                            node_ip=label,
                            configured=r["configured"],
                            mounted=r["mounted"],
                        )
                    )

            if result["success"]:
                log.check(
                    SUCCESS_MESSAGES["slurm_mandatory_binds_verified"].format(
                        node_ip=label
                    )
                )

    if not tested_any:
        pytest.skip("No PV entries target slurm_control_node")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_027"])


@pytest.mark.sanity
@pytest.mark.order(28)
def test_mysql_data_on_mount(host, pv_configs):
    """
    TC-PV-028: Verify MySQL/MariaDB data directory resides on the PowerVault
    bind mount for slurm_control_node entries.
    Checks: /var/lib/mysql is a mountpoint, MariaDB service active,
    ibdata1 present, slurm_acct_db database exists.
    """
    log = TestLogger(TEST_NAMES["tc_pv_028"])

    tested_any = False
    failures = []
    for pv in pv_configs:
        prefix_list = pv["prefix_list"]
        is_slurm = any(p.startswith("slurm_control_node") for p in prefix_list)
        if not is_slurm:
            log.check(f"Skipping PV '{pv['name']}' — not a slurm_control_node entry")
            continue

        if "/var/lib/mysql" not in pv["bind_targets"]:
            log.check(f"Skipping PV '{pv['name']}' — /var/lib/mysql not in bind targets")
            continue

        tested_any = True
        log.check(f"Checking PV '{pv['name']}' MySQL data on PowerVault mount")

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)
            result = verify_mysql_data_on_mount(host, node_ip)

            if not result["success"]:
                actual = (
                    f"mountpoint={result['details']['is_mountpoint']}, "
                    f"service={result['details']['service_active']}, "
                    f"data_files={result['details']['data_files_exist']}, "
                    f"slurm_db={result['details']['slurm_db_exists']}"
                )
                failures.append(
                    TEST_ASSERT_MSGS["mysql_data_on_mount"].format(
                        node_ip=label, actual=actual
                    )
                )
            else:
                log.check(
                    SUCCESS_MESSAGES["mysql_data_verified"].format(node_ip=label)
                )

    if not tested_any:
        pytest.skip("No slurm_control_node PV entries with /var/lib/mysql bind mount")

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_028"])


@pytest.mark.sanity
@pytest.mark.order(29)
def test_all_mounts_writable(host, pv_configs):
    """
    TC-PV-029: Verify all PowerVault mounts (main mount point + all bind
    targets) are writable on all target nodes.
    """
    log = TestLogger(TEST_NAMES["tc_pv_029"])

    failures = []
    for pv in pv_configs:
        mount_point = pv["mount_point"]
        if not mount_point:
            log.check(f"Skipping PV '{pv['name']}' — no mount_point")
            continue

        all_paths = [mount_point] + list(pv["bind_targets"])
        log.check(f"Checking PV '{pv['name']}' writability: {all_paths}")

        for node in pv["target_nodes"]:
            node_ip = node.get("admin_ip", "")
            label = _node_label(node)

            for path in all_paths:
                result = verify_mount_writable(host, node_ip, path)

                if not result["success"]:
                    failures.append(
                        TEST_ASSERT_MSGS["mount_writable"].format(
                            mount_path=path,
                            node_ip=label,
                            actual="not writable",
                        )
                    )
                else:
                    log.check(
                        SUCCESS_MESSAGES["mount_writable_verified"].format(
                            mount_path=path, node_ip=label
                        )
                    )

    assert not failures, "\n".join(failures)
    log.passed(TEST_NAMES["tc_pv_029"])
