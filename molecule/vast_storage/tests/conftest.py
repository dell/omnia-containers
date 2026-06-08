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
"""Shared pytest fixtures for vast_storage test scenarios."""

import yaml
import pytest
from automation_library.core import STORAGE_CONFIG_PATH, run_in_container
from automation_library.slurm.functions.slurm_func import (
    get_slurm_nodes,
    get_slurm_control_nodes,
    get_login_nodes,
    get_login_compiler_nodes,
)


def _read_storage_config(host):
    """Read and parse storage_config.yml from the omnia_core container."""
    cmd = run_in_container(host, f"cat {STORAGE_CONFIG_PATH}")
    if cmd.rc != 0:
        return {}
    try:
        return yaml.safe_load(cmd.stdout) or {}
    except yaml.YAMLError:
        return {}


def _get_vast_mount_entry(host):
    """Return the vast_storage entry from storage_config.yml, or None."""
    config = _read_storage_config(host)
    for mount in config.get("mounts", []):
        if mount.get("name") == "vast_storage":
            return mount
    return None


def _first_ip(nodes):
    """Return admin_ip of the first node in a list, or None."""
    return nodes[0].get("admin_ip") if nodes else None


@pytest.fixture(scope="module")
def vast_config(host):
    """Return the VAST mount entry from storage config."""
    entry = _get_vast_mount_entry(host)
    if entry is None:
        pytest.skip("vast_storage not configured in storage_config.yml")
    return entry


@pytest.fixture(scope="module")
def compute_node_ip(host):
    """Return the IP of the first available slurm compute node."""
    nodes = get_slurm_nodes(host)
    if not nodes:
        pytest.skip("No slurm compute nodes found in PXE mapping")
    return _first_ip(nodes)


@pytest.fixture(scope="module")
def control_node_ip(host):
    """Return the IP of the first available slurm control node."""
    nodes = get_slurm_control_nodes(host)
    if not nodes:
        pytest.skip("No slurm control nodes found in PXE mapping")
    return _first_ip(nodes)


@pytest.fixture(scope="module")
def login_compiler_node_ip(host):
    """Return the IP of the first available login_compiler node."""
    nodes = get_login_compiler_nodes(host)
    if not nodes:
        pytest.skip("No login_compiler nodes found in PXE mapping")
    return _first_ip(nodes)


@pytest.fixture(scope="module")
def login_node_ip(host):
    """Return the IP of the first available login node."""
    nodes = get_login_nodes(host)
    if not nodes:
        pytest.skip("No login nodes found in PXE mapping")
    return _first_ip(nodes)
