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
Mount configuration verification functions.

This module validates the generic `mounts` and `swap` sections of
storage_config.yml as processed by the `mount_config` provision role.

It follows the existing return-dictionary pattern:
    {"success": bool, "error": str, "details": dict}
"""

import yaml
from typing import Any, Dict, List

from automation_library.core import (
    TestLogger,
    run_in_container,
    run_on_remote_node,
    get_nodes_info,
    get_functional_groups_from_pxe_mapping,
    STORAGE_CONFIG_PATH,
    OMNIA_CORE_CONTAINER,
)
from automation_library.powervault import (
    safe_run_on_remote_node,
    resolve_node_key_value,
    verify_mount_point_exists,
    verify_volume_mounted,
    verify_fstab_entry,
    verify_node_subdirectory,
    verify_bind_mounts,
    verify_bind_fstab_entries,
    verify_bind_isolation,
    FSTAB_PATH,
)

from ..vars import (
    DEFAULT_FS_TYPE,
    DEFAULT_MOUNT_OPTS,
    DEFAULT_DUMP_FREQ,
    DEFAULT_FSCK_PASS,
    DEFAULT_NODE_KEY,
    NODE_KEY_COMMANDS,
)

from ..messages import (
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SUCCESS_MESSAGES,
)


# =============================================================================
# CONFIGURATION READERS
# =============================================================================

def read_storage_config(host) -> Dict[str, Any]:
    """Read and parse storage_config.yml from the omnia_core container."""
    cmd = run_in_container(host, f"cat {STORAGE_CONFIG_PATH}")
    if cmd.rc != 0:
        return {}
    try:
        return yaml.safe_load(cmd.stdout) or {}
    except yaml.YAMLError:
        return {}


def get_mounts_entries(host) -> List[Dict[str, Any]]:
    """Return the `mounts` list from storage_config.yml."""
    config = read_storage_config(host)
    return config.get("mounts", []) or []


def get_swap_entries(host) -> List[Dict[str, Any]]:
    """Return the `swap` list from storage_config.yml."""
    config = read_storage_config(host)
    return config.get("swap", []) or []


def get_mount_params(host) -> Dict[str, Any]:
    """Return the `mount_params` section from storage_config.yml."""
    config = read_storage_config(host)
    return config.get("mount_params", {}) or {}


def skip_if_no_mounts(host) -> bool:
    """Return True if `mounts` is absent or empty."""
    return len(get_mounts_entries(host)) == 0


# =============================================================================
# MOUNT ENTRY RESOLUTION
# =============================================================================

def resolve_mount_fs_type(mount_entry: Dict[str, Any], mount_params: Dict[str, Any]) -> str:
    """Resolve the effective fs_type for a mount entry.

    Priority: mount_entry.fs_type > mount_params profile > default 'auto'
    """
    if mount_entry.get("fs_type"):
        return mount_entry["fs_type"]
    profile_name = mount_entry.get("mount_params", "")
    if profile_name and profile_name in mount_params:
        return mount_params[profile_name].get("fs_type", DEFAULT_FS_TYPE)
    return DEFAULT_FS_TYPE


def resolve_mount_opts(mount_entry: Dict[str, Any], mount_params: Dict[str, Any]) -> str:
    """Resolve the effective mount options for a mount entry.

    Priority: mount_entry.mnt_opts > mount_params profile > default 'defaults'
    """
    if mount_entry.get("mnt_opts"):
        return mount_entry["mnt_opts"]
    profile_name = mount_entry.get("mount_params", "")
    if profile_name and profile_name in mount_params:
        return mount_params[profile_name].get("mnt_opts", DEFAULT_MOUNT_OPTS)
    return DEFAULT_MOUNT_OPTS


def resolve_mount_dump_freq(mount_entry: Dict[str, Any], mount_params: Dict[str, Any]) -> str:
    """Resolve dump_freq for a mount entry."""
    if mount_entry.get("dump_freq"):
        return str(mount_entry["dump_freq"])
    profile_name = mount_entry.get("mount_params", "")
    if profile_name and profile_name in mount_params:
        return str(mount_params[profile_name].get("dump_freq", DEFAULT_DUMP_FREQ))
    return DEFAULT_DUMP_FREQ


def resolve_mount_fsck_pass(mount_entry: Dict[str, Any], mount_params: Dict[str, Any]) -> str:
    """Resolve fsck_pass for a mount entry."""
    if mount_entry.get("fsck_pass"):
        return str(mount_entry["fsck_pass"])
    profile_name = mount_entry.get("mount_params", "")
    if profile_name and profile_name in mount_params:
        return str(mount_params[profile_name].get("fsck_pass", DEFAULT_FSCK_PASS))
    return DEFAULT_FSCK_PASS


# =============================================================================
# NODE DISCOVERY
# =============================================================================

def get_target_nodes_for_mount(host, mount_entry: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return target nodes for a mount entry.

    Supports both `functional_group_prefix` and `groups` targeting.
    """
    prefix_list = mount_entry.get("functional_group_prefix", [])
    groups_list = mount_entry.get("groups", [])

    all_groups = get_functional_groups_from_pxe_mapping(host)

    matching_groups = set()
    if prefix_list:
        for group in all_groups:
            for prefix in prefix_list:
                if group.startswith(prefix):
                    matching_groups.add(group)
                    break
    if groups_list:
        for group in groups_list:
            if group in all_groups:
                matching_groups.add(group)

    nodes = []
    seen_ips = set()
    for group in matching_groups:
        group_nodes = get_nodes_info(
            host, search_by="functional_group", search_value=group
        )
        for node in group_nodes:
            ip = node.get("admin_ip", "")
            if ip and ip not in seen_ips:
                seen_ips.add(ip)
                nodes.append(node)

    return nodes


def get_non_target_nodes_for_mount(host, mount_entry: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return nodes that do NOT match the mount entry targeting."""
    target_nodes = get_target_nodes_for_mount(host, mount_entry)
    target_ips = {n.get("admin_ip", "") for n in target_nodes}

    all_groups = get_functional_groups_from_pxe_mapping(host)
    all_nodes = []
    seen_ips = set()
    for group in all_groups:
        for node in get_nodes_info(host, search_by="functional_group", search_value=group):
            ip = node.get("admin_ip", "")
            if ip and ip not in seen_ips and ip not in target_ips:
                seen_ips.add(ip)
                all_nodes.append(node)

    return all_nodes


# =============================================================================
# MOUNT VERIFICATION
# =============================================================================

def verify_mount_options(host, node_ip: str, mount_point: str, expected_opts: str) -> Dict[str, Any]:
    """Check mount options applied to mount_point.

    Args:
        expected_opts: Comma-separated mount options string

    Returns:
        {"success": bool, "error": str, "details": {"actual_opts": str, "missing_opts": list}}
    """
    log = TestLogger("verify_mount_options")
    log.check(TEST_LOG_MSGS["checking_mount_options"].format(mount_point=mount_point, node_ip=node_ip))

    cmd = safe_run_on_remote_node(
        host,
        f"grep '{mount_point}' /proc/mounts",
        node_ip,
    )
    output = cmd.stdout.strip()

    if not output:
        expected_list = [o.strip() for o in expected_opts.split(",") if o.strip()]
        return {
            "success": False,
            "error": f"No /proc/mounts entry for {mount_point} on {node_ip}",
            "details": {"actual_opts": "<not mounted>", "missing_opts": expected_list},
        }

    # Parse actual mount options and fs_type from /proc/mounts
    actual_opts = ""
    fs_type = ""
    for line in output.split("\n"):
        parts = line.strip().split()
        if len(parts) >= 4 and parts[1] == mount_point:
            fs_type = parts[2]
            actual_opts = parts[3]
            break

    actual_set = set(actual_opts.split(","))

    # Options that are only managed in userspace / fstab and not always shown
    USERSPACE_ONLY_OPTS = {"_netdev", "nofail", "noauto", "defaults"}

    # NFS options that may not appear in /proc/mounts for newer protocols (e.g. NFSv4)
    NFS_HIDDEN_OPTS = {"intr", "posix", "cto"}

    expected_list = [o.strip() for o in expected_opts.split(",") if o.strip()]
    missing = []
    userspace_missing = []

    for opt in expected_list:
        if opt in actual_set:
            continue
        if opt in USERSPACE_ONLY_OPTS:
            userspace_missing.append(opt)
        elif opt in NFS_HIDDEN_OPTS and fs_type in ("nfs", "nfs4"):
            userspace_missing.append(opt)
        else:
            missing.append(opt)

    # Validate userspace/hidden options against fstab
    if userspace_missing:
        fstab_cmd = safe_run_on_remote_node(
            host,
            f"grep '{mount_point}' {FSTAB_PATH}",
            node_ip,
        )
        fstab_opts_set = set()
        for fline in fstab_cmd.stdout.strip().split("\n"):
            fparts = fline.strip().split()
            if len(fparts) >= 4 and fparts[1] == mount_point:
                fstab_opts_set = set(fparts[3].split(","))
                break

        for opt in userspace_missing:
            if opt not in fstab_opts_set:
                missing.append(opt)

    success = len(missing) == 0
    return {
        "success": success,
        "error": "" if success else f"Missing mount options {missing} for {mount_point} on {node_ip}",
        "details": {"actual_opts": actual_opts, "missing_opts": missing},
    }


def _normalize_mode(mode: str) -> str:
    """Normalize a permission mode string for comparison.

    Handles leading zeros by interpreting both as octal, e.g.
    '0755' and '755' both normalize to '755'.
    Falls back to the original string for non-octal values.
    """
    try:
        return format(int(str(mode), 8), "o")
    except (ValueError, TypeError):
        return str(mode)


def verify_mount_permissions(
    host,
    node_ip: str,
    path: str,
    expected_owner: str,
    expected_group: str,
    expected_mode: str,
) -> Dict[str, Any]:
    """Check owner/group/mode of a path on a target node."""
    log = TestLogger("verify_mount_permissions")
    log.check(TEST_LOG_MSGS["checking_permissions"].format(path=path, node_ip=node_ip))

    cmd = safe_run_on_remote_node(
        host,
        f"stat -c '%U:%G %a' '{path}'",
        node_ip,
    )
    output = cmd.stdout.strip()
    if not output:
        return {
            "success": False,
            "error": f"Could not stat {path} on {node_ip}",
            "details": {"actual": ""},
        }

    parts = output.split()
    if len(parts) != 2:
        return {
            "success": False,
            "error": f"Unexpected stat output for {path} on {node_ip}: {output}",
            "details": {"actual": output},
        }

    actual_owner_group = parts[0]
    actual_mode = parts[1]
    expected_owner_group = f"{expected_owner}:{expected_group}"

    errors = []
    if actual_owner_group != expected_owner_group:
        errors.append(f"owner/group: expected {expected_owner_group}, got {actual_owner_group}")
    if _normalize_mode(actual_mode) != _normalize_mode(expected_mode):
        errors.append(f"mode: expected {expected_mode}, got {actual_mode}")

    success = len(errors) == 0
    return {
        "success": success,
        "error": "; ".join(errors) if errors else "",
        "details": {
            "actual_owner_group": actual_owner_group,
            "actual_mode": actual_mode,
            "expected_owner_group": expected_owner_group,
            "expected_mode": expected_mode,
        },
    }


def verify_mount_on_oim(host, mount_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Check that a mount entry with mount_on_oim:true is mounted on the OIM host."""
    log = TestLogger("verify_mount_on_oim")
    mount_point = mount_entry.get("mount_point", "")
    source = mount_entry.get("source", "")

    log.check(f"Checking OIM mount for {mount_point}")

    # Check mount is active
    result = host.run(f"mountpoint -q '{mount_point}' && echo mounted || echo not_mounted")
    is_mounted = result.stdout.strip() == "mounted"

    # Check fstab entry
    fstab_cmd = host.run(f"grep '{mount_point}' /etc/fstab")
    fstab_line = ""
    for line in fstab_cmd.stdout.strip().split("\n"):
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == mount_point:
            fstab_line = line.strip()
            break

    success = is_mounted and bool(fstab_line)
    error = ""
    if not is_mounted:
        error = f"Mount point {mount_point} is not mounted on OIM"
    elif not fstab_line:
        error = f"No fstab entry for {mount_point} on OIM"

    return {
        "success": success,
        "error": error,
        "details": {
            "mount_point": mount_point,
            "source": source,
            "is_mounted": is_mounted,
            "fstab_line": fstab_line,
        },
    }


# Re-export powervault helpers under mount_config namespace
__all__ = [
    # New mount_config functions
    "read_storage_config",
    "get_mounts_entries",
    "get_swap_entries",
    "get_mount_params",
    "skip_if_no_mounts",
    "resolve_mount_fs_type",
    "resolve_mount_opts",
    "resolve_mount_dump_freq",
    "resolve_mount_fsck_pass",
    "get_target_nodes_for_mount",
    "get_non_target_nodes_for_mount",
    "verify_mount_permissions",
    "verify_mount_on_oim",
    # Re-used powervault helpers
    "resolve_node_key_value",
    "verify_mount_point_exists",
    "verify_volume_mounted",
    "verify_mount_options",
    "verify_fstab_entry",
    "verify_node_subdirectory",
    "verify_bind_mounts",
    "verify_bind_fstab_entries",
    "verify_bind_isolation",
]
