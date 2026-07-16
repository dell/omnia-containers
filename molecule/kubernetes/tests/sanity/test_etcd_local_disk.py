# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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

"""etcd local disk sanity test cases for OMNIA.

This module contains sanity test cases to verify etcd local disk setup on
Kubernetes control plane nodes (TC-F01, TC-F03 to TC-F08, TC-F10 to TC-F12).

TC-F02 (RAID validation) is OUT_OF_SCOPE for v1.0 - RAID configuration is
done separately, not by etcd disk setup scripts.

TC-F09 (subsequent boot fstab update) is in negative/test_etcd_reboot.py
as it requires a reboot to validate properly.
"""

import os
import sys

# Add the project root to the Python path
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../.."),
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
from automation_library.core import TestLogger
from automation_library.etcd_local_disk.functions.etcd_func import get_etcd_operations
from automation_library.etcd_local_disk.vars.etcd_vars import (
    DISK_TYPE_HDD,
    DISK_TYPE_NVME,
    DISK_TYPE_SSD,
    ETCD_MOUNT_PATH,
)


# Pytest fixtures
@pytest.fixture(scope="module", name="etcd_ops")
def _etcd_ops_fixture(host):
    """Fixture to provide EtcdLocalDiskOperations instance."""
    try:
        ops = get_etcd_operations(host=host)
    except (OSError, KeyError, RuntimeError, ValueError) as e:
        pytest.skip(f"Unable to initialize etcd operations: {str(e)}")
    yield ops


@pytest.fixture(scope="module", name="etcd_enabled")
def _etcd_enabled_fixture(etcd_ops):
    """Fixture to check if etcd_on_local_disk is enabled."""
    enabled, message = etcd_ops.is_etcd_on_local_disk_enabled()
    return enabled


# =========================================================================
# TC-F01: BOSS Card Detection
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(101)
def test_tc_f01_boss_card_detection(etcd_ops, etcd_enabled):
    """TC-F01: Verify Dell BOSS-N1/N2 detection via model/subsystem string match on control plane nodes.

    Maps To: SB-001, VC-004, BL-001
    Priority: P0
    """
    log = TestLogger("TC-F01: Verify Dell BOSS card detection via model/subsystem string match")

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping BOSS card detection")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check("Scanning for Dell BOSS-N1/N2 via model/subsystem string match on control plane nodes")
    success, message, details = etcd_ops.verify_boss_card_detection()

    if success:
        log.passed(message, details)
    else:
        # BOSS card not detected is acceptable - fallback disk may be used
        log.passed(
            "BOSS card not detected on all nodes - fallback disk may be in use",
            details,
        )
        pytest.skip(
            "BOSS card not available in test environment - "
            "verify with TC-F07 fallback disk detection"
        )


# =========================================================================
# TC-F03: Disk Partitioning for etcd
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(102)
def test_tc_f03_disk_partitioning(etcd_ops, etcd_enabled):
    """TC-F03: Verify GPT partition creation for etcd data, excluding root disk.

    Maps To: SB-003, VC-006, VC-007, BL-003
    Priority: P0
    """
    log = TestLogger(
        "TC-F03: Verify GPT partition creation for etcd on control plane nodes"
    )

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping partition check")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check(
        "Verifying GPT partition exists for etcd data and root disk is excluded"
    )
    success, message, details = etcd_ops.verify_disk_partitioning()

    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message


# =========================================================================
# TC-F04: Filesystem Creation
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(103)
def test_tc_f04_filesystem_creation(etcd_ops, etcd_enabled):
    """TC-F04: Verify ext4 filesystem formatting on etcd partition.

    Maps To: SB-004, VC-008
    Priority: P0
    """
    log = TestLogger(
        "TC-F04: Verify filesystem creation on etcd partition"
    )

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping filesystem check")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check("Verifying ext4 filesystem on etcd partition")
    success, message, details = etcd_ops.verify_filesystem_creation()

    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message


# =========================================================================
# TC-F05: fstab Update and Mount
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(104)
def test_tc_f05_fstab_update_and_mount(etcd_ops, etcd_enabled):
    """TC-F05: Verify UUID-based fstab entry and mount for /var/lib/etcd.

    Maps To: SB-005, VC-009
    Priority: P0
    """
    log = TestLogger(
        "TC-F05: Verify fstab update and mount for /var/lib/etcd"
    )

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping fstab/mount check")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check(
        f"Verifying UUID-based fstab entry and active mount for {ETCD_MOUNT_PATH}"
    )
    success, message, details = etcd_ops.verify_fstab_and_mount()

    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message


# =========================================================================
# TC-F06: etcd Configuration to Local Disk
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(105)
def test_tc_f06_etcd_configuration_to_local_disk(etcd_ops, etcd_enabled):
    """TC-F06: Verify etcd is using local disk at /var/lib/etcd instead of NFS.

    Maps To: SB-006, VC-010
    Priority: P0
    """
    log = TestLogger(
        "TC-F06: Verify etcd configuration to use local disk"
    )

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping local disk config check")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check(
        f"Verifying etcd uses local disk at {ETCD_MOUNT_PATH} (not NFS)"
    )
    success, message, details = etcd_ops.verify_etcd_using_local_disk()

    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message


# =========================================================================
# TC-F07: Fallback Disk Detection
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(106)
def test_tc_f07_fallback_disk_detection(etcd_ops, etcd_enabled):
    """TC-F07: Verify fallback to available disk when BOSS card not detected.

    Maps To: SB-007, BL-002
    Priority: P0
    """
    log = TestLogger(
        "TC-F07: Verify fallback disk detection when BOSS card not available"
    )

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping fallback disk check")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check(
        "Verifying fallback disk is used for etcd when BOSS card not detected"
    )
    success, message, details = etcd_ops.verify_fallback_disk_detection()

    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message


# =========================================================================
# TC-F08: First Boot Disk Setup
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(107)
def test_tc_f08_first_boot_disk_setup(etcd_ops, etcd_enabled):
    """TC-F08: Verify etcd-disk-setup.sh execution on first boot.

    Maps To: SB-008, BL-004
    Priority: P0
    """
    log = TestLogger(
        "TC-F08: Verify first boot disk setup (etcd-disk-setup.sh)"
    )

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping first boot check")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check(
        "Verifying etcd-disk-setup.sh script exists and executed successfully"
    )
    success, message, details = etcd_ops.verify_first_boot_setup()

    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message


# =========================================================================
# TC-F10: SSD Disk Support
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(108)
def test_tc_f10_ssd_disk_support(etcd_ops, etcd_enabled):
    """TC-F10: Verify etcd local disk deployment using SSD disk.

    Maps To: SB-010, VC-003
    Priority: P1
    """
    log = TestLogger(
        "TC-F10: Verify SSD disk support for etcd local disk"
    )

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping SSD check")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check("Verifying SSD disk is used for etcd on control plane nodes")
    success, message, details = etcd_ops.verify_disk_type_support(DISK_TYPE_SSD)

    if success:
        log.passed(message, details)
    else:
        log.passed("SSD disk not used for etcd - other disk type in use", details)
        pytest.skip(
            "SSD disk not available for etcd on control plane nodes"
        )


# =========================================================================
# TC-F11: HDD Disk Support
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(109)
def test_tc_f11_hdd_disk_support(etcd_ops, etcd_enabled):
    """TC-F11: Verify etcd local disk deployment using HDD disk.

    Maps To: SB-011, VC-003
    Priority: P1
    """
    log = TestLogger(
        "TC-F11: Verify HDD disk support for etcd local disk"
    )

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping HDD check")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check("Verifying HDD disk is used for etcd on control plane nodes")
    success, message, details = etcd_ops.verify_disk_type_support(DISK_TYPE_HDD)

    if success:
        log.passed(message, details)
    else:
        log.passed("HDD disk not used for etcd - other disk type in use", details)
        pytest.skip(
            "HDD disk not available for etcd on control plane nodes"
        )


# =========================================================================
# TC-F12: NVMe Disk Support
# =========================================================================

@pytest.mark.sanity
@pytest.mark.etcd
@pytest.mark.order(110)
def test_tc_f12_nvme_disk_support(etcd_ops, etcd_enabled):
    """TC-F12: Verify etcd local disk deployment using NVMe disk.

    Maps To: SB-012, VC-003
    Priority: P1
    """
    log = TestLogger(
        "TC-F12: Verify NVMe disk support for etcd local disk"
    )

    if not etcd_enabled:
        log.passed("etcd_on_local_disk is disabled - skipping NVMe check")
        pytest.skip("etcd_on_local_disk is not enabled in omnia_config.yml")

    log.check("Verifying NVMe disk is used for etcd on control plane nodes")
    success, message, details = etcd_ops.verify_disk_type_support(DISK_TYPE_NVME)

    if success:
        log.passed(message, details)
    else:
        log.passed("NVMe disk not used for etcd - other disk type in use", details)
        pytest.skip(
            "NVMe disk not available for etcd on control plane nodes"
        )
