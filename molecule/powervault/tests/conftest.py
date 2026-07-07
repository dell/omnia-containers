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
"""Shared pytest fixtures for powervault test scenarios."""

import pytest
from automation_library.powervault import (
    get_powervault_entries,
    get_mount_params,
    get_target_nodes,
    resolve_pv_fs_type,
    resolve_pv_mount_opts,
    resolve_node_key_value,
    DEFAULT_ISCSI_PORT,
    DEFAULT_NODE_KEY,
)


@pytest.fixture(scope="module")
def powervault_entries(host):
    """Return powervault_config list from storage_config.yml.

    Skips all tests if powervault_config is absent or empty.
    """
    entries = get_powervault_entries(host)
    if not entries:
        pytest.skip("PowerVault not configured in storage_config.yml")
    return entries


@pytest.fixture(scope="module")
def mount_params_config(host):
    """Return mount_params section from storage_config.yml."""
    return get_mount_params(host)


@pytest.fixture(scope="module")
def pv_configs(host, powervault_entries, mount_params_config):
    """Return list of resolved PV configurations with pre-computed values.

    Each item is a dict with:
        entry, name, mount_point, ip_list, port, volume_id, iscsi_initiator,
        node_key, bind_targets, prefix_list, fs_type, mount_opts,
        target_nodes, first_node_ip, first_node_key_value
    """
    configs = []
    for entry in powervault_entries:
        prefix = entry.get("functional_group_prefix", [])
        target_nodes = get_target_nodes(host, prefix)
        if not target_nodes:
            continue

        first_ip = target_nodes[0].get("admin_ip", "")
        first_hostname = target_nodes[0].get("hostname", "")
        node_key = entry.get("node_key", "")
        node_key_value = ""
        if node_key and first_ip:
            node_key_value = resolve_node_key_value(host, first_ip, node_key)

        configs.append({
            "entry": entry,
            "name": entry.get("name", ""),
            "mount_point": entry.get("mount_point", ""),
            "ip_list": entry.get("ip", []),
            "port": entry.get("port", DEFAULT_ISCSI_PORT),
            "volume_id": entry.get("volume_id", ""),
            "iscsi_initiator": entry.get("iscsi_initiator", ""),
            "node_key": node_key,
            "bind_targets": entry.get("node_mount_point", []),
            "prefix_list": prefix,
            "fs_type": resolve_pv_fs_type(entry, mount_params_config),
            "mount_opts": resolve_pv_mount_opts(entry, mount_params_config),
            "target_nodes": target_nodes,
            "first_node_ip": first_ip,
            "first_node_hostname": first_hostname,
            "first_node_label": (
                f"{first_hostname} ({first_ip})" if first_hostname else first_ip
            ),
            "first_node_key_value": node_key_value,
        })

    if not configs:
        pytest.skip("No PV entries with target nodes found")

    return configs
