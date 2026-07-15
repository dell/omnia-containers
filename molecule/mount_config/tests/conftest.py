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
Shared pytest fixtures for mount_config test scenarios.
"""

import pytest

from automation_library.mount_config import (
    get_mounts_entries,
    get_mount_params,
    get_target_nodes_for_mount,
    resolve_node_key_value,
    resolve_mount_fs_type,
    resolve_mount_opts,
)


def _first_ip(nodes):
    """Return admin_ip of the first node in a list, or None."""
    return nodes[0].get("admin_ip", "") if nodes else None


@pytest.fixture(scope="module")
def mounts_entries(host):
    """Return the `mounts` list from storage_config.yml.

    Skips all tests if no mounts are configured.
    """
    entries = get_mounts_entries(host)
    if not entries:
        pytest.skip("No mounts configured in storage_config.yml")
    return entries


@pytest.fixture(scope="module")
def mount_params_config(host):
    """Return the `mount_params` section from storage_config.yml."""
    return get_mount_params(host)


@pytest.fixture(scope="module")
def resolved_mount_configs(host, mounts_entries, mount_params_config):
    """Return list of resolved mount configurations with target nodes.

    Each item is a dict with:
        entry, name, mount_point, source, fs_type, mount_opts,
        node_key, bind_targets, target_nodes, first_node_ip,
        first_node_key_value
    """
    configs = []
    for entry in mounts_entries:
        target_nodes = get_target_nodes_for_mount(host, entry)
        if not target_nodes:
            continue

        first_ip = _first_ip(target_nodes)
        first_hostname = target_nodes[0].get("hostname", "")
        node_key = entry.get("node_key", "")
        node_key_value = ""
        if node_key and first_ip:
            node_key_value = resolve_node_key_value(host, first_ip, node_key)

        configs.append({
            "entry": entry,
            "name": entry.get("name", ""),
            "mount_point": entry.get("mount_point", ""),
            "source": entry.get("source", ""),
            "fs_type": resolve_mount_fs_type(entry, mount_params_config),
            "mount_opts": resolve_mount_opts(entry, mount_params_config),
            "node_key": node_key,
            "bind_targets": entry.get("node_mount_point", []),
            "target_nodes": target_nodes,
            "first_node_ip": first_ip,
            "first_node_hostname": first_hostname,
            "first_node_label": (
                f"{first_hostname} ({first_ip})" if first_hostname else first_ip
            ),
            "first_node_key_value": node_key_value,
        })

    if not configs:
        pytest.skip("No mount entries with target nodes found")

    return configs
