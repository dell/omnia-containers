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

"""Custom Slurm config verification tests.

Tests in this module verify that custom Slurm settings supplied via
omnia_config.yml (slurm_cluster[].config_sources) are correctly applied to
the deployed Slurm configuration.

  TC55 - Custom global Slurm parameters in slurm.conf
  TC56 - Custom NodeName definitions in slurm.conf
  TC57 - Custom cgroup.conf parameters
  TC58 - Combined custom Slurm config verification
  TC59 - Custom PartitionName definitions
  TC60 - Custom slurmdbd.conf parameters
  TC61 - Custom config persists after scontrol reconfigure
  TC62 - NFS share slurm.conf/cgroup.conf matches local control node files
  TC63 - Configless mode on compute nodes
  TC64 - Job behavior with custom Slurm parameters
"""

import pytest

from automation_library.core import TestLogger
from automation_library.slurm.functions.custom_slurm_config_func import (
    verify_custom_slurm_global_params,
    verify_custom_slurm_nodename,
    verify_custom_partition_config,
    verify_custom_cgroup_config,
    verify_custom_slurmdbd_config,
    verify_custom_slurm_config_reconfigure,
    verify_nfs_slurm_config_sync,
    verify_configless_mode,
    verify_custom_config_job_behavior,
    verify_custom_slurm_config,
)


def _log_and_assert(log, result, test_name):
    """Helper to log per-item details and assert result."""
    if result.get("skipped"):
        log.check(result["message"])
        pytest.skip(result["message"])
        return

    for detail in result.get("details", []):
        log.check(f"  {detail}")

    if result["success"]:
        log.passed(result["message"])
    else:
        log.failed(result["message"])

    assert result["success"], result["message"]


# =============================================================================
# TC55: Custom global Slurm parameters in slurm.conf
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(55)
def test_custom_slurm_global_params(host):
    """Verify custom global Slurm parameters are applied in slurm.conf."""
    log = TestLogger("Verify custom Slurm global parameters")
    log.check("Reading custom config_sources from omnia_config.yml")
    _log_and_assert(log, verify_custom_slurm_global_params(host), "global params")


# =============================================================================
# TC56: Custom NodeName definitions in slurm.conf
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(56)
def test_custom_slurm_nodename_definitions(host):
    """Verify custom NodeName definitions are applied in slurm.conf."""
    log = TestLogger("Verify custom Slurm NodeName definitions")
    log.check("Reading custom NodeName entries from config_sources")
    _log_and_assert(log, verify_custom_slurm_nodename(host), "NodeName definitions")


# =============================================================================
# TC57: Custom cgroup.conf parameters
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(57)
def test_custom_cgroup_config(host):
    """Verify custom cgroup.conf parameters are applied."""
    log = TestLogger("Verify custom cgroup.conf parameters")
    log.check("Reading custom cgroup config from config_sources")
    _log_and_assert(log, verify_custom_cgroup_config(host), "cgroup config")


# =============================================================================
# TC58: Combined custom Slurm config verification
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(58)
def test_custom_slurm_config(host):
    """Run combined verification of all custom Slurm config."""
    log = TestLogger("Verify custom Slurm config end-to-end")
    log.check("Running all custom Slurm config checks")
    _log_and_assert(log, verify_custom_slurm_config(host), "combined custom config")


# =============================================================================
# TC59: Custom PartitionName definitions
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(59)
def test_custom_slurm_partition_definitions(host):
    """Verify custom PartitionName definitions are applied."""
    log = TestLogger("Verify custom Slurm PartitionName definitions")
    log.check("Reading custom PartitionName entries from config_sources")
    _log_and_assert(log, verify_custom_partition_config(host), "PartitionName definitions")


# =============================================================================
# TC60: Custom slurmdbd.conf parameters
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(60)
def test_custom_slurmdbd_config(host):
    """Verify custom slurmdbd.conf parameters are applied."""
    log = TestLogger("Verify custom slurmdbd.conf parameters")
    log.check("Reading custom slurmdbd config from config_sources")
    _log_and_assert(log, verify_custom_slurmdbd_config(host), "slurmdbd config")


# =============================================================================
# TC61: Custom config persists after scontrol reconfigure
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(61)
def test_custom_slurm_config_reconfigure(host):
    """Verify custom config persists after scontrol reconfigure."""
    log = TestLogger("Verify custom Slurm config persists after reconfigure")
    log.check("Running scontrol reconfigure")
    _log_and_assert(log, verify_custom_slurm_config_reconfigure(host), "reconfigure persistence")


# =============================================================================
# TC62: NFS share slurm.conf/cgroup.conf matches local control node files
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(62)
def test_nfs_slurm_config_sync(host):
    """Verify NFS share slurm.conf/cgroup.conf match local control node files."""
    log = TestLogger("Verify NFS share slurm config sync")
    log.check("Comparing local control node config files with NFS share")
    _log_and_assert(log, verify_nfs_slurm_config_sync(host), "NFS config sync")


# =============================================================================
# TC63: Configless mode on compute nodes
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(63)
def test_slurm_configless_mode(host):
    """Verify configless mode on compute nodes."""
    log = TestLogger("Verify Slurm configless mode")
    log.check("Checking compute node conf-cache against control node slurm.conf")
    _log_and_assert(log, verify_configless_mode(host), "configless mode")


# =============================================================================
# TC64: Job behavior with custom Slurm parameters
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(64)
def test_custom_slurm_job_behavior(host):
    """Verify job behavior with custom Slurm parameters."""
    log = TestLogger("Verify custom Slurm job behavior")
    log.check("Submitting short job to check custom params")
    _log_and_assert(log, verify_custom_config_job_behavior(host), "job behavior")
