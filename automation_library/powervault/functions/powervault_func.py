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
PowerVault iSCSI storage verification functions.

All functions follow the return-dictionary pattern:
    {"success": bool, "error": str, "details": dict}
"""

import re
from typing import Any, Dict, List, Optional

import yaml

from automation_library.core import (
    TestLogger,
    run_in_container,
    run_on_remote_node,
    get_functional_groups_from_pxe_mapping,
    get_nodes_info,
)
from ..vars import (
    STORAGE_CONFIG_PATH,
    FSTAB_PATH,
    ISCSI_INITIATOR_PATH,
    DEFAULT_ISCSI_PORT,
    DEFAULT_FS_TYPE,
    DEFAULT_MOUNT_OPTS,
    DEFAULT_NODE_KEY,
    ISCSI_SETUP_LOG_TEMPLATE,
    ISCSI_SETUP_COMPLETE_MSG,
    NODE_KEY_COMMANDS,
    IO_TEST_FILE,
    IO_TEST_BS,
    IO_TEST_COUNT,
    IO_TEST_CHECKSUM_FILE,
    BIND_IO_TEST_FILE,
    PORT_CHECK_TIMEOUT,
    CMD_ISCSID_ACTIVE,
    CMD_ISCSID_ENABLED,
    CMD_MULTIPATHD_ACTIVE,
    CMD_MULTIPATHD_ENABLED,
    CMD_ISCSI_DISCOVERY,
    CMD_ISCSI_SESSION,
    CMD_ISCSI_SESSION_DETAIL,
    CMD_ISCSI_NODE_SHOW,
    CMD_MULTIPATH_LIST,
    CMD_CHECK_MOUNTPOINT,
    CMD_CHECK_DIR_EXISTS,
    CMD_GET_FSTAB,
    CMD_GET_PROC_MOUNTS,
    CMD_BLKID_FSTYPE,
    CMD_PARTED_PRINT,
    CMD_PORT_CHECK,
    CMD_DF,
    CMD_MOUNT_GREP,
)
from ..messages import TEST_LOG_MSGS


# =============================================================================
# SAFE REMOTE EXECUTION HELPER
# =============================================================================

class _FakeResult:
    """Minimal stand-in for a testinfra CommandResult on SSH failure."""
    def __init__(self, rc, stdout, stderr):
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr


def safe_run_on_remote_node(host, cmd: str, node_ip: str):
    """Wrapper around run_on_remote_node that catches RuntimeError.

    testinfra raises RuntimeError when SSH exit code is 255
    (connection failure). This wrapper converts that into a fake
    result object so callers can handle the error gracefully.
    """
    try:
        return run_on_remote_node(host, cmd, node_ip)
    except RuntimeError as exc:
        return _FakeResult(
            rc=255,
            stdout="",
            stderr=f"SSH connection failed to {node_ip}: {exc}",
        )


# =============================================================================
# CONFIGURATION READER FUNCTIONS
# =============================================================================

def read_storage_config(host) -> Dict[str, Any]:
    """Read and parse storage_config.yml from the omnia_core container.

    Args:
        host: Testinfra host object

    Returns:
        Parsed storage_config dict or empty dict on failure
    """
    cmd = run_in_container(host, f"cat {STORAGE_CONFIG_PATH}")
    if cmd.rc != 0:
        return {}
    try:
        return yaml.safe_load(cmd.stdout) or {}
    except yaml.YAMLError:
        return {}


def get_powervault_entries(host) -> List[Dict[str, Any]]:
    """Extract powervault_config list from storage_config.yml.

    Args:
        host: Testinfra host object

    Returns:
        List of powervault_config entries, or empty list
    """
    config = read_storage_config(host)
    return config.get("powervault_config", []) or []


def get_mount_params(host) -> Dict[str, Any]:
    """Extract mount_params section from storage_config.yml.

    Args:
        host: Testinfra host object

    Returns:
        Dict of mount_params profiles, or empty dict
    """
    config = read_storage_config(host)
    return config.get("mount_params", {}) or {}


def skip_if_no_powervault(host):
    """Return True if powervault_config is absent or empty, indicating skip."""
    entries = get_powervault_entries(host)
    return len(entries) == 0


def resolve_pv_fs_type(pv_entry: Dict, mount_params: Dict) -> str:
    """Resolve the effective fs_type for a PV entry.

    Priority: pv_entry.fs_type > mount_params profile > default 'xfs'
    """
    if pv_entry.get("fs_type"):
        return pv_entry["fs_type"]
    profile_name = pv_entry.get("mount_params", "")
    if profile_name and profile_name in mount_params:
        return mount_params[profile_name].get("fs_type", DEFAULT_FS_TYPE)
    return DEFAULT_FS_TYPE


def resolve_pv_mount_opts(pv_entry: Dict, mount_params: Dict) -> str:
    """Resolve the effective mount options for a PV entry.

    Priority: pv_entry.mnt_opts > mount_params profile > default
    """
    if pv_entry.get("mnt_opts"):
        return pv_entry["mnt_opts"]
    profile_name = pv_entry.get("mount_params", "")
    if profile_name and profile_name in mount_params:
        return mount_params[profile_name].get("mnt_opts", DEFAULT_MOUNT_OPTS)
    return DEFAULT_MOUNT_OPTS


# =============================================================================
# NODE DISCOVERY FUNCTIONS
# =============================================================================

def get_target_nodes(host, functional_group_prefix) -> List[Dict[str, str]]:
    """Return nodes matching any of the given functional_group_prefix values.

    Uses prefix matching against all functional groups in PXE mapping,
    mirroring the Ansible determine_target_groups.yml logic.

    Args:
        host: Testinfra host object
        functional_group_prefix: List of prefix strings or single string

    Returns:
        List of node info dicts with admin_ip, hostname, functional_group, etc.
    """
    if isinstance(functional_group_prefix, str):
        functional_group_prefix = [functional_group_prefix]

    all_groups = get_functional_groups_from_pxe_mapping(host)
    matching_groups = []
    for group in all_groups:
        for prefix in functional_group_prefix:
            if group.startswith(prefix):
                matching_groups.append(group)
                break

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


def get_non_target_nodes(host, functional_group_prefix) -> List[Dict[str, str]]:
    """Return nodes that do NOT match any of the functional_group_prefix values.

    Args:
        host: Testinfra host object
        functional_group_prefix: List of prefix strings or single string

    Returns:
        List of node info dicts for non-matching nodes
    """
    if isinstance(functional_group_prefix, str):
        functional_group_prefix = [functional_group_prefix]

    all_groups = get_functional_groups_from_pxe_mapping(host)
    non_matching_groups = []
    for group in all_groups:
        matched = False
        for prefix in functional_group_prefix:
            if group.startswith(prefix):
                matched = True
                break
        if not matched:
            non_matching_groups.append(group)

    nodes = []
    seen_ips = set()
    for group in non_matching_groups:
        group_nodes = get_nodes_info(
            host, search_by="functional_group", search_value=group
        )
        for node in group_nodes:
            ip = node.get("admin_ip", "")
            if ip and ip not in seen_ips:
                seen_ips.add(ip)
                nodes.append(node)

    return nodes


def resolve_node_key_value(host, node_ip: str, node_key: str) -> str:
    """Resolve the node-specific identifier value on a remote node.

    Args:
        host: Testinfra host object
        node_ip: Admin IP of the target node
        node_key: One of 'local_hostname', 'local_ipv4', 'instance_id'

    Returns:
        Resolved node identifier string, or empty string on failure
    """
    cmd_template = NODE_KEY_COMMANDS.get(node_key, NODE_KEY_COMMANDS[DEFAULT_NODE_KEY])
    result = safe_run_on_remote_node(host, cmd_template, node_ip)
    if result.rc == 0 and result.stdout.strip():
        return result.stdout.strip().split()[0]
    return ""


# =============================================================================
# iSCSI VERIFICATION FUNCTIONS
# =============================================================================

def verify_iscsi_service(host, node_ip: str) -> Dict[str, Any]:
    """Check iscsid is active and enabled on a target node.

    Returns:
        {"success": bool, "error": str, "details": {"active": str, "enabled": str}}
    """
    log = TestLogger("verify_iscsi_service")
    log.check(TEST_LOG_MSGS["checking_iscsid"].format(node_ip=node_ip))

    active_cmd = safe_run_on_remote_node(host, CMD_ISCSID_ACTIVE, node_ip)
    enabled_cmd = safe_run_on_remote_node(host, CMD_ISCSID_ENABLED, node_ip)

    active = active_cmd.stdout.strip()
    enabled = enabled_cmd.stdout.strip()

    success = active == "active" and enabled == "enabled"
    error = ""
    if not success:
        error = f"iscsid: active={active}, enabled={enabled} on {node_ip}"

    return {"success": success, "error": error, "details": {"active": active, "enabled": enabled}}


def verify_initiator_name(host, node_ip: str, expected_iqn: str) -> Dict[str, Any]:
    """Validate iSCSI initiator name on a target node.

    Returns:
        {"success": bool, "error": str, "details": {"actual": str, "expected": str}}
    """
    log = TestLogger("verify_initiator_name")
    log.check(TEST_LOG_MSGS["checking_initiator"].format(node_ip=node_ip))

    cmd = safe_run_on_remote_node(host, f"cat {ISCSI_INITIATOR_PATH}", node_ip)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": f"Cannot read {ISCSI_INITIATOR_PATH} on {node_ip}",
            "details": {"actual": "", "expected": expected_iqn},
        }

    content = cmd.stdout.strip()
    expected_line = f"InitiatorName={expected_iqn}"
    found = expected_line in content

    return {
        "success": found,
        "error": "" if found else f"Expected '{expected_line}' in initiatorname.iscsi on {node_ip}",
        "details": {"actual": content, "expected": expected_iqn},
    }


def verify_iscsi_discovery(host, node_ip: str, ip_list: List[str], port: int) -> Dict[str, Any]:
    """Check iSCSI discovery from all portal IPs.

    Returns:
        {"success": bool, "error": str, "details": {"discovered_iqn": str, "portal_results": list}}
    """
    log = TestLogger("verify_iscsi_discovery")
    discovered_iqn = ""
    portal_results = []

    for portal_ip in ip_list:
        log.check(TEST_LOG_MSGS["checking_discovery"].format(
            node_ip=node_ip, portal_ip=portal_ip, port=port
        ))
        cmd = safe_run_on_remote_node(
            host,
            CMD_ISCSI_DISCOVERY.format(ip=portal_ip, port=port),
            node_ip,
        )
        output = cmd.stdout.strip()
        # Discovery output format: <portal> <iqn>
        iqn = ""
        if output:
            for line in output.split("\n"):
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1].startswith("iqn."):
                    iqn = parts[1]
                    break
        portal_results.append({
            "portal_ip": portal_ip,
            "rc": cmd.rc,
            "iqn": iqn,
            "output": output,
        })
        if iqn and not discovered_iqn:
            discovered_iqn = iqn

    success = bool(discovered_iqn)
    error = "" if success else f"No target IQN discovered from any portal on {node_ip}"

    return {
        "success": success,
        "error": error,
        "details": {"discovered_iqn": discovered_iqn, "portal_results": portal_results},
    }


def verify_iscsi_sessions(host, node_ip: str, target_iqn: str = "") -> Dict[str, Any]:
    """Validate active iSCSI sessions on a target node.

    Returns:
        {"success": bool, "error": str, "details": {"session_count": int, "sessions": list}}
    """
    log = TestLogger("verify_iscsi_sessions")
    log.check(TEST_LOG_MSGS["checking_sessions"].format(node_ip=node_ip))

    cmd = safe_run_on_remote_node(host, CMD_ISCSI_SESSION, node_ip)
    output = cmd.stdout.strip()

    sessions = []
    if output:
        for line in output.split("\n"):
            line = line.strip()
            if line:
                sessions.append(line)

    session_count = len(sessions)
    success = session_count > 0

    if target_iqn and success:
        iqn_found = any(target_iqn in s for s in sessions)
        if not iqn_found:
            success = False

    error = "" if success else f"No active iSCSI sessions on {node_ip}"

    return {
        "success": success,
        "error": error,
        "details": {"session_count": session_count, "sessions": sessions},
    }


def verify_iscsi_startup_automatic(host, node_ip: str) -> Dict[str, Any]:
    """Check that node.startup is set to automatic for iSCSI nodes.

    Returns:
        {"success": bool, "error": str, "details": {"startup_value": str}}
    """
    log = TestLogger("verify_iscsi_startup_automatic")
    log.check(TEST_LOG_MSGS["checking_startup"].format(node_ip=node_ip))

    cmd = safe_run_on_remote_node(
        host,
        f"{CMD_ISCSI_NODE_SHOW} 2>/dev/null | grep 'node.startup'",
        node_ip,
    )
    output = cmd.stdout.strip()

    # Check all node.startup entries are 'automatic'
    all_automatic = True
    found_any = False
    for line in output.split("\n"):
        line = line.strip()
        if "node.startup" in line:
            found_any = True
            if "automatic" not in line:
                all_automatic = False
                break

    success = found_any and all_automatic
    error = ""
    if not found_any:
        error = f"No node.startup entries found on {node_ip}"
    elif not all_automatic:
        error = f"node.startup is not 'automatic' on {node_ip}"

    return {
        "success": success,
        "error": error,
        "details": {"startup_value": output},
    }


def _get_portal_session_states(host, node_ip: str) -> Dict[str, str]:
    """Parse 'iscsiadm -m session -P 1' to map each portal IP to its session state.

    Returns:
        dict mapping portal_ip -> session_state (e.g., "LOGGED_IN", "FREE", "TRANSPORT WAIT")
        Empty dict if no sessions found.
    """
    cmd = safe_run_on_remote_node(host, CMD_ISCSI_SESSION_DETAIL, node_ip)
    output = cmd.stdout.strip()
    if not output:
        return {}

    portal_states = {}
    current_portal_ip = None

    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("Current Portal:"):
            # Extract IP from "Current Portal: 10.43.4.21:3260,1"
            portal_part = line.split(":", 1)[1].strip()
            current_portal_ip = portal_part.split(":")[0].strip()
        elif "iSCSI Session State:" in line and current_portal_ip:
            # Extract state from "iSCSI Session State: LOGGED_IN"
            state = line.split(":", 1)[1].strip()
            portal_states[current_portal_ip] = state

    return portal_states


def verify_portal_reachability(host, node_ip: str, ip_list: List[str], port: int) -> Dict[str, Any]:
    """Test port connectivity and iSCSI session health from target node to each portal IP.

    Checks two things per portal:
    1. TCP port reachability (port open)
    2. iSCSI session state (must be LOGGED_IN)

    Returns:
        {"success": bool, "error": str, "details": {"results": list}}
    """
    log = TestLogger("verify_portal_reachability")
    results = []
    all_ok = True

    # Get session states for all portals in one call
    portal_states = _get_portal_session_states(host, node_ip)

    for portal_ip in ip_list:
        # Check 1: TCP port reachability
        log.check(TEST_LOG_MSGS["checking_port"].format(
            node_ip=node_ip, portal_ip=portal_ip, port=port
        ))
        cmd = safe_run_on_remote_node(
            host,
            CMD_PORT_CHECK.format(timeout=PORT_CHECK_TIMEOUT, ip=portal_ip, port=port),
            node_ip,
        )
        reachable = "reachable" in cmd.stdout.strip()

        # Check 2: iSCSI session health
        log.check(TEST_LOG_MSGS["checking_portal_session"].format(
            node_ip=node_ip, portal_ip=portal_ip
        ))
        session_state = portal_states.get(portal_ip, "NO_SESSION")
        session_healthy = session_state == "LOGGED_IN"

        portal_ok = reachable and session_healthy
        results.append({
            "portal_ip": portal_ip,
            "reachable": reachable,
            "session_state": session_state,
            "session_healthy": session_healthy,
        })
        if not portal_ok:
            all_ok = False

    errors = []
    unreachable = [r["portal_ip"] for r in results if not r["reachable"]]
    unhealthy = [
        f"{r['portal_ip']} (state: {r['session_state']})"
        for r in results if not r["session_healthy"]
    ]
    if unreachable:
        errors.append(f"Unreachable portals from {node_ip}: {unreachable}")
    if unhealthy:
        errors.append(f"Unhealthy iSCSI sessions from {node_ip}: {unhealthy}")

    return {"success": all_ok, "error": "; ".join(errors), "details": {"results": results}}


# =============================================================================
# MULTIPATH VERIFICATION FUNCTIONS
# =============================================================================

def verify_multipath_service(host, node_ip: str) -> Dict[str, Any]:
    """Check multipathd is active and enabled on a target node.

    Returns:
        {"success": bool, "error": str, "details": {"active": str, "enabled": str}}
    """
    log = TestLogger("verify_multipath_service")
    log.check(TEST_LOG_MSGS["checking_multipathd"].format(node_ip=node_ip))

    active_cmd = safe_run_on_remote_node(host, CMD_MULTIPATHD_ACTIVE, node_ip)
    enabled_cmd = safe_run_on_remote_node(host, CMD_MULTIPATHD_ENABLED, node_ip)

    active = active_cmd.stdout.strip()
    enabled = enabled_cmd.stdout.strip()

    success = active == "active" and enabled == "enabled"
    error = ""
    if not success:
        error = f"multipathd: active={active}, enabled={enabled} on {node_ip}"

    return {"success": success, "error": error, "details": {"active": active, "enabled": enabled}}


def verify_multipath_device(host, node_ip: str, volume_id: str) -> Dict[str, Any]:
    """Find and validate multipath device matching volume_id.

    Mirrors the logic in setup_iscsi_storage.sh.j2 lines 98-121:
    1. grep volume_id
    2. fallback to DellEMC,ME5
    3. fallback to DellEMC,ME4
    4. fallback to latest dm-*

    Returns:
        {"success": bool, "error": str, "details": {"mpath_device": str, "match_method": str}}
    """
    log = TestLogger("verify_multipath_device")
    log.check(TEST_LOG_MSGS["checking_mpath_device"].format(
        node_ip=node_ip, volume_id=volume_id
    ))

    cmd = safe_run_on_remote_node(host, CMD_MULTIPATH_LIST, node_ip)
    output = cmd.stdout.strip()

    if not output:
        return {
            "success": False,
            "error": f"No multipath output on {node_ip}",
            "details": {"mpath_device": "", "match_method": ""},
        }

    mpath_device = ""
    match_method = ""

    # Method 1: Match by volume_id
    if volume_id:
        for line in output.split("\n"):
            if volume_id.lower() in line.lower():
                parts = line.split()
                if parts:
                    mpath_device = parts[0]
                    match_method = "volume_id"
                    break

    # Method 2: Fallback to vendor match
    if not mpath_device:
        for vendor in ["DellEMC,ME5", "DellEMC,ME4"]:
            for line in output.split("\n"):
                if vendor.lower() in line.lower():
                    parts = line.split()
                    if parts:
                        mpath_device = parts[0]
                        match_method = f"vendor:{vendor}"
                        break
            if mpath_device:
                break

    # Method 3: Fallback to latest dm-*
    if not mpath_device:
        dm_devices = re.findall(r'dm-\d+', output)
        if dm_devices:
            dm_sorted = sorted(dm_devices, key=lambda x: int(x.split('-')[1]))
            latest_dm = dm_sorted[-1]
            for line in output.split("\n"):
                if latest_dm in line:
                    parts = line.split()
                    if parts:
                        mpath_device = parts[0]
                        match_method = "dm_fallback"
                        break

    success = bool(mpath_device)
    if success:
        log.check(TEST_LOG_MSGS["found_mpath_device"].format(
            device=mpath_device, node_ip=node_ip
        ))

    return {
        "success": success,
        "error": "" if success else f"No multipath device found for volume_id '{volume_id}' on {node_ip}",
        "details": {"mpath_device": mpath_device, "match_method": match_method},
    }


def verify_multipath_paths(host, node_ip: str, mpath_device: str, expected_path_count: int) -> Dict[str, Any]:
    """Count active paths on a multipath device.

    Returns:
        {"success": bool, "error": str, "details": {"path_count": int, "expected": int}}
    """
    log = TestLogger("verify_multipath_paths")
    log.check(TEST_LOG_MSGS["checking_mpath_paths"].format(node_ip=node_ip))

    cmd = safe_run_on_remote_node(
        host,
        f"multipath -ll {mpath_device} 2>/dev/null",
        node_ip,
    )
    output = cmd.stdout.strip()

    # Count lines with 'running' or 'active' status indicators
    path_count = 0
    for line in output.split("\n"):
        line_lower = line.strip().lower()
        # Active path lines contain status like "active ready running" or "active ghost"
        if re.search(r'\b(running|active)\b.*\b(ready|ghost|faulty)\b', line_lower):
            path_count += 1
        elif re.search(r'\d+:\d+:\d+:\d+', line) and "active" in line_lower:
            path_count += 1

    success = path_count >= expected_path_count
    error = ""
    if not success:
        error = f"Expected >= {expected_path_count} paths, got {path_count} on {node_ip}"

    return {
        "success": success,
        "error": error,
        "details": {"path_count": path_count, "expected": expected_path_count},
    }


# =============================================================================
# PARTITION, FILESYSTEM, AND MOUNT VERIFICATION FUNCTIONS
# =============================================================================

def verify_gpt_partition(host, node_ip: str, mpath_device: str) -> Dict[str, Any]:
    """Check GPT partition exists on multipath device.

    Returns:
        {"success": bool, "error": str, "details": {"partition": str, "table_type": str}}
    """
    log = TestLogger("verify_gpt_partition")
    device_path = f"/dev/mapper/{mpath_device}" if not mpath_device.startswith("/") else mpath_device
    log.check(TEST_LOG_MSGS["checking_partition"].format(device=device_path, node_ip=node_ip))

    cmd = safe_run_on_remote_node(
        host,
        CMD_PARTED_PRINT.format(device=device_path),
        node_ip,
    )
    output = cmd.stdout.strip()

    has_gpt = "gpt" in output.lower()
    # Check for partition 1
    has_partition = bool(re.search(r'^\s*1\s+', output, re.MULTILINE))

    # Also check if the partition device exists
    part_dev = f"{device_path}1" if not device_path.endswith("1") else device_path
    # For mapper devices like /dev/mapper/mpathX, partition is /dev/mapper/mpathX1
    part_check = safe_run_on_remote_node(
        host,
        f"test -e {part_dev} && echo exists || test -e /dev/mapper/{mpath_device}1 && echo exists || echo not_exists",
        node_ip,
    )
    part_exists = part_check.stdout.strip() == "exists"

    success = has_gpt and (has_partition or part_exists)

    return {
        "success": success,
        "error": "" if success else f"No GPT partition found on {device_path} on {node_ip}",
        "details": {"partition": f"{mpath_device}1", "table_type": "gpt" if has_gpt else "unknown"},
    }


def verify_filesystem_type(host, node_ip: str, mpath_device: str, expected_fs: str) -> Dict[str, Any]:
    """Validate filesystem type on the partition.

    Returns:
        {"success": bool, "error": str, "details": {"actual_fs": str, "expected_fs": str}}
    """
    log = TestLogger("verify_filesystem_type")
    log.check(TEST_LOG_MSGS["checking_fs_type"].format(node_ip=node_ip))

    # Try the partition device
    part_dev = f"/dev/mapper/{mpath_device}1" if not mpath_device.startswith("/") else f"{mpath_device}1"
    cmd = safe_run_on_remote_node(
        host,
        CMD_BLKID_FSTYPE.format(device=part_dev),
        node_ip,
    )
    actual_fs = cmd.stdout.strip()

    success = actual_fs.lower() == expected_fs.lower()

    return {
        "success": success,
        "error": "" if success else f"Expected fs_type '{expected_fs}', got '{actual_fs}' on {node_ip}",
        "details": {"actual_fs": actual_fs, "expected_fs": expected_fs},
    }


def verify_mount_point_exists(host, node_ip: str, mount_point: str) -> Dict[str, Any]:
    """Check mount point directory exists on target node.

    Returns:
        {"success": bool, "error": str, "details": {}}
    """
    log = TestLogger("verify_mount_point_exists")
    log.check(TEST_LOG_MSGS["checking_mount_point"].format(mount_point=mount_point, node_ip=node_ip))

    cmd = safe_run_on_remote_node(
        host,
        CMD_CHECK_DIR_EXISTS.format(path=mount_point),
        node_ip,
    )
    exists = cmd.stdout.strip() == "exists"

    return {
        "success": exists,
        "error": "" if exists else f"Mount point {mount_point} does not exist on {node_ip}",
        "details": {},
    }


def verify_volume_mounted(host, node_ip: str, mount_point: str, mpath_device: str = "") -> Dict[str, Any]:
    """Validate the volume is actively mounted at mount_point.

    Returns:
        {"success": bool, "error": str, "details": {"is_mountpoint": bool, "df_output": str}}
    """
    log = TestLogger("verify_volume_mounted")
    log.check(TEST_LOG_MSGS["checking_mount_active"].format(mount_point=mount_point, node_ip=node_ip))

    # Check mountpoint
    mp_cmd = safe_run_on_remote_node(
        host,
        CMD_CHECK_MOUNTPOINT.format(path=mount_point),
        node_ip,
    )
    is_mountpoint = "mounted" in mp_cmd.stdout.strip()

    # Check df
    df_cmd = safe_run_on_remote_node(
        host,
        CMD_DF.format(path=mount_point),
        node_ip,
    )
    df_output = df_cmd.stdout.strip()

    # Check mount entry
    mount_cmd = safe_run_on_remote_node(
        host,
        CMD_MOUNT_GREP.format(pattern=mount_point),
        node_ip,
    )
    mount_entry = mount_cmd.stdout.strip()

    success = is_mountpoint and bool(mount_entry)

    return {
        "success": success,
        "error": "" if success else f"{mount_point} is not actively mounted on {node_ip}",
        "details": {"is_mountpoint": is_mountpoint, "df_output": df_output, "mount_entry": mount_entry},
    }


def verify_mount_options(host, node_ip: str, mount_point: str, expected_opts: str) -> Dict[str, Any]:
    """Check mount options applied to mount_point.

    Args:
        expected_opts: Comma-separated mount options string (e.g., "defaults,_netdev,noatime")

    Returns:
        {"success": bool, "error": str, "details": {"actual_opts": str, "missing_opts": list}}
    """
    log = TestLogger("verify_mount_options")
    log.check(TEST_LOG_MSGS["checking_mount_opts"].format(mount_point=mount_point, node_ip=node_ip))

    cmd = safe_run_on_remote_node(
        host,
        f"grep '{mount_point}' /proc/mounts",
        node_ip,
    )
    output = cmd.stdout.strip()

    if not output:
        return {
            "success": False,
            "error": f"No /proc/mounts entry for {mount_point} on {node_ip}",
            "details": {"actual_opts": "", "missing_opts": []},
        }

    # Parse actual mount options from /proc/mounts (4th field)
    actual_opts = ""
    for line in output.split("\n"):
        parts = line.strip().split()
        if len(parts) >= 4 and parts[1] == mount_point:
            actual_opts = parts[3]
            break

    # Options that are only in fstab, not shown in /proc/mounts
    USERSPACE_ONLY_OPTS = {"_netdev", "nofail", "noauto", "defaults"}

    # Check each expected option against /proc/mounts (skip userspace-only)
    expected_list = [o.strip() for o in expected_opts.split(",") if o.strip()]
    actual_set = set(actual_opts.split(","))
    kernel_missing = [
        o for o in expected_list
        if o not in actual_set and o not in USERSPACE_ONLY_OPTS
        and not o.startswith("x-systemd")
    ]

    # Validate userspace-only options in fstab instead
    fstab_missing = []
    userspace_expected = [o for o in expected_list if o in USERSPACE_ONLY_OPTS and o != "defaults"]
    if userspace_expected:
        fstab_cmd = safe_run_on_remote_node(
            host,
            f"grep '{mount_point}' {FSTAB_PATH}",
            node_ip,
        )
        # Parse in Python: find line where 2nd field exactly matches mount_point
        fstab_opts_set = set()
        for fline in fstab_cmd.stdout.strip().split("\n"):
            fparts = fline.strip().split()
            if len(fparts) >= 4 and fparts[1] == mount_point:
                fstab_opts_set = set(fparts[3].split(","))
                break
        fstab_missing = [o for o in userspace_expected if o not in fstab_opts_set]

    missing = kernel_missing + fstab_missing
    success = len(missing) == 0

    return {
        "success": success,
        "error": "" if success else f"Missing mount options {missing} for {mount_point} on {node_ip}",
        "details": {"actual_opts": actual_opts, "missing_opts": missing},
    }


def verify_fstab_entry(host, node_ip: str, mount_point: str, expected_fs: str = "", expected_opts: str = "") -> Dict[str, Any]:
    """Validate persistent fstab entry for a mount point.

    Returns:
        {"success": bool, "error": str, "details": {"fstab_line": str}}
    """
    log = TestLogger("verify_fstab_entry")
    log.check(TEST_LOG_MSGS["checking_fstab"].format(mount_point=mount_point, node_ip=node_ip))

    cmd = safe_run_on_remote_node(
        host,
        f"grep '{mount_point}' {FSTAB_PATH}",
        node_ip,
    )
    output = cmd.stdout.strip()

    if not output:
        return {
            "success": False,
            "error": f"No fstab entry for {mount_point} on {node_ip}",
            "details": {"fstab_line": ""},
        }

    # Find the line matching mount_point exactly (as 2nd field)
    fstab_line = ""
    for line in output.split("\n"):
        parts = line.strip().split()
        if len(parts) >= 4 and parts[1] == mount_point:
            fstab_line = line.strip()
            break

    if not fstab_line:
        # Accept any line containing the mount_point
        fstab_line = output.split("\n")[0].strip()

    success = bool(fstab_line)
    error = ""

    # Optionally check fs_type
    if success and expected_fs:
        parts = fstab_line.split()
        if len(parts) >= 3:
            actual_fs = parts[2]
            if actual_fs != expected_fs:
                error = f"fstab fs_type mismatch: expected '{expected_fs}', got '{actual_fs}'"

    return {
        "success": success and not error,
        "error": error if error else ("" if success else f"No fstab entry for {mount_point} on {node_ip}"),
        "details": {"fstab_line": fstab_line},
    }


# =============================================================================
# BIND MOUNT VERIFICATION FUNCTIONS
# =============================================================================

def verify_node_subdirectory(host, node_ip: str, mount_point: str, node_key: str) -> Dict[str, Any]:
    """Check per-node subdirectory exists under mount point.

    Returns:
        {"success": bool, "error": str, "details": {"node_value": str, "subdir": str}}
    """
    log = TestLogger("verify_node_subdirectory")
    log.check(TEST_LOG_MSGS["checking_node_subdir"].format(mount_point=mount_point, node_ip=node_ip))

    node_value = resolve_node_key_value(host, node_ip, node_key)
    if not node_value:
        return {
            "success": False,
            "error": f"Could not resolve node_key '{node_key}' on {node_ip}",
            "details": {"node_value": "", "subdir": ""},
        }

    subdir = f"{mount_point}/{node_value}"
    cmd = safe_run_on_remote_node(
        host,
        CMD_CHECK_DIR_EXISTS.format(path=subdir),
        node_ip,
    )
    exists = cmd.stdout.strip() == "exists"

    return {
        "success": exists,
        "error": "" if exists else f"Node subdirectory {subdir} does not exist on {node_ip}",
        "details": {"node_value": node_value, "subdir": subdir},
    }


def verify_bind_mounts(host, node_ip: str, bind_targets: List[str], mount_point: str, node_key_value: str) -> Dict[str, Any]:
    """Validate bind mount targets are active mountpoints.

    Returns:
        {"success": bool, "error": str, "details": {"results": list}}
    """
    log = TestLogger("verify_bind_mounts")
    log.check(TEST_LOG_MSGS["checking_bind_mounts"].format(node_ip=node_ip))

    results = []
    all_ok = True

    for bind_target in bind_targets:
        source = f"{mount_point}/{node_key_value}{bind_target}"

        # Check source exists
        src_cmd = safe_run_on_remote_node(
            host,
            CMD_CHECK_DIR_EXISTS.format(path=source),
            node_ip,
        )
        src_exists = src_cmd.stdout.strip() == "exists"

        # Check target exists
        tgt_cmd = safe_run_on_remote_node(
            host,
            CMD_CHECK_DIR_EXISTS.format(path=bind_target),
            node_ip,
        )
        tgt_exists = tgt_cmd.stdout.strip() == "exists"

        # Check target is a mountpoint
        mp_cmd = safe_run_on_remote_node(
            host,
            CMD_CHECK_MOUNTPOINT.format(path=bind_target),
            node_ip,
        )
        is_mountpoint = mp_cmd.stdout.strip() == "mounted"

        # Check mount shows bind
        mount_cmd = safe_run_on_remote_node(
            host,
            CMD_MOUNT_GREP.format(pattern=bind_target),
            node_ip,
        )
        has_mount_entry = bool(mount_cmd.stdout.strip())

        ok = src_exists and tgt_exists and is_mountpoint
        if not ok:
            all_ok = False

        results.append({
            "bind_target": bind_target,
            "source": source,
            "source_exists": src_exists,
            "target_exists": tgt_exists,
            "is_mountpoint": is_mountpoint,
            "has_mount_entry": has_mount_entry,
            "success": ok,
        })

    return {
        "success": all_ok,
        "error": "" if all_ok else f"Some bind mounts failed on {node_ip}",
        "details": {"results": results},
    }


def verify_bind_fstab_entries(host, node_ip: str, bind_targets: List[str]) -> Dict[str, Any]:
    """Check bind mount fstab entries exist for all targets.

    Returns:
        {"success": bool, "error": str, "details": {"results": list}}
    """
    log = TestLogger("verify_bind_fstab_entries")
    log.check(TEST_LOG_MSGS["checking_bind_fstab"].format(node_ip=node_ip))

    fstab_cmd = safe_run_on_remote_node(host, CMD_GET_FSTAB, node_ip)
    fstab_content = fstab_cmd.stdout.strip()

    results = []
    all_ok = True

    for bind_target in bind_targets:
        # Look for fstab entry with bind mount pattern: <source> <target> none bind 0 0
        found = False
        for line in fstab_content.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 4 and parts[1] == bind_target and "bind" in parts[3]:
                found = True
                break
            # Also check if bind_target appears with 'none' fs_type and 'bind' option
            if bind_target in line and "bind" in line:
                found = True
                break

        results.append({"bind_target": bind_target, "found": found})
        if not found:
            all_ok = False

    return {
        "success": all_ok,
        "error": "" if all_ok else f"Some bind mount fstab entries missing on {node_ip}",
        "details": {"results": results},
    }


def verify_bind_isolation(host, node_a: str, node_b: str, bind_target: str) -> Dict[str, Any]:
    """Test data isolation between two nodes via bind mounts.

    Writes a test file on node_a and verifies it does NOT appear on node_b.

    Returns:
        {"success": bool, "error": str, "details": {}}
    """
    log = TestLogger("verify_bind_isolation")
    log.check(TEST_LOG_MSGS["checking_bind_isolation"].format(node_a=node_a, node_b=node_b))

    test_file = f"{bind_target}/isolation_test_file_{node_a.replace('.', '_')}"

    # Write test file on node A
    write_cmd = safe_run_on_remote_node(
        host,
        f"echo 'isolation_test' > {test_file}",
        node_a,
    )
    if write_cmd.rc != 0:
        return {
            "success": False,
            "error": f"Failed to write test file on {node_a}",
            "details": {},
        }

    # Check file does NOT exist on node B
    check_cmd = safe_run_on_remote_node(
        host,
        f"test -f {test_file} && echo exists || echo not_exists",
        node_b,
    )
    file_on_b = check_cmd.stdout.strip() == "exists"

    # Cleanup on node A
    safe_run_on_remote_node(host, f"rm -f {test_file}", node_a)

    success = not file_on_b

    return {
        "success": success,
        "error": "" if success else f"File written on {node_a} is visible on {node_b} at {bind_target}",
        "details": {},
    }


# =============================================================================
# FUNCTIONAL GROUP TARGETING VERIFICATION FUNCTIONS
# =============================================================================

def verify_functional_group_targeting(host, pv_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Verify PV mount is present only on matching functional groups.

    Returns:
        {"success": bool, "error": str, "details": {"target_results": list, "non_target_results": list}}
    """
    log = TestLogger("verify_functional_group_targeting")
    prefix_list = pv_entry.get("functional_group_prefix", [])
    mount_point = pv_entry.get("mount_point", "")
    name = pv_entry.get("name", "")
    log.check(TEST_LOG_MSGS["checking_group_targeting"].format(name=name))

    target_nodes = get_target_nodes(host, prefix_list)
    non_target_nodes = get_non_target_nodes(host, prefix_list)

    target_results = []
    non_target_results = []
    all_ok = True

    # Check mount IS present on target nodes
    for node in target_nodes[:3]:  # Sample up to 3
        ip = node.get("admin_ip", "")
        if not ip:
            continue
        mp_cmd = safe_run_on_remote_node(
            host,
            CMD_CHECK_MOUNTPOINT.format(path=mount_point),
            ip,
        )
        mounted = "mounted" in mp_cmd.stdout.strip()
        target_results.append({"node_ip": ip, "mounted": mounted})
        if not mounted:
            all_ok = False

    # Check mount is ABSENT on non-target nodes (sample up to 2)
    # Only flag if the mount is specifically an iSCSI/multipath device
    for node in non_target_nodes[:2]:
        ip = node.get("admin_ip", "")
        if not ip:
            continue
        # Check /proc/mounts for mount_point with dm-*/mapper source (iSCSI-specific)
        mount_cmd = safe_run_on_remote_node(
            host,
            f"grep '{mount_point}' /proc/mounts",
            ip,
        )
        # Parse in Python: find line where 2nd field exactly matches mount_point
        iscsi_mounted = False
        for mline in mount_cmd.stdout.strip().split("\n"):
            mparts = mline.strip().split()
            if len(mparts) >= 2 and mparts[1] == mount_point:
                source_dev = mparts[0]
                iscsi_mounted = "/dev/mapper/" in source_dev or "/dev/dm-" in source_dev
                break

        # Check fstab for iSCSI-specific entry (exact 2nd field, fs_type != none)
        fstab_cmd = safe_run_on_remote_node(
            host,
            f"grep '{mount_point}' {FSTAB_PATH} 2>/dev/null",
            ip,
        )
        fstab_count = 0
        for fline in fstab_cmd.stdout.strip().split("\n"):
            fparts = fline.strip().split()
            if (len(fparts) >= 3 and fparts[1] == mount_point
                    and fparts[2] != "none" and not fline.strip().startswith("#")):
                fstab_count += 1

        non_target_results.append({
            "node_ip": ip,
            "mounted": iscsi_mounted,
            "fstab_entries": fstab_count,
        })
        if iscsi_mounted or fstab_count > 0:
            all_ok = False

    return {
        "success": all_ok,
        "error": "" if all_ok else f"Functional group targeting mismatch for '{name}'",
        "details": {"target_results": target_results, "non_target_results": non_target_results},
    }


def verify_multiple_prefix_targeting(host, pv_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Verify multiple functional_group_prefix entries target all matching groups.

    Returns:
        {"success": bool, "error": str, "details": {"prefix_results": list}}
    """
    log = TestLogger("verify_multiple_prefix_targeting")
    prefix_list = pv_entry.get("functional_group_prefix", [])
    mount_point = pv_entry.get("mount_point", "")
    name = pv_entry.get("name", "")
    log.check(TEST_LOG_MSGS["checking_multi_prefix"].format(name=name))

    all_groups = get_functional_groups_from_pxe_mapping(host)
    prefix_results = []
    all_ok = True

    for prefix in prefix_list:
        matching_groups = [g for g in all_groups if g.startswith(prefix)]
        for group in matching_groups:
            group_nodes = get_nodes_info(
                host, search_by="functional_group", search_value=group
            )
            if not group_nodes:
                continue
            # Pick first node from this group
            node = group_nodes[0]
            ip = node.get("admin_ip", "")
            if not ip:
                continue

            mp_cmd = safe_run_on_remote_node(
                host,
                CMD_CHECK_MOUNTPOINT.format(path=mount_point),
                ip,
            )
            mounted = "mounted" in mp_cmd.stdout.strip()
            prefix_results.append({
                "prefix": prefix,
                "group": group,
                "node_ip": ip,
                "mounted": mounted,
            })
            if not mounted:
                all_ok = False

    return {
        "success": all_ok,
        "error": "" if all_ok else f"Some groups not targeted for '{name}'",
        "details": {"prefix_results": prefix_results},
    }


# =============================================================================
# I/O VERIFICATION FUNCTIONS
# =============================================================================

def verify_io_test(host, node_ip: str, mount_point: str) -> Dict[str, Any]:
    """Write/read test on PowerVault mount.

    Returns:
        {"success": bool, "error": str, "details": {}}
    """
    log = TestLogger("verify_io_test")
    log.check(TEST_LOG_MSGS["running_io_test"].format(mount_point=mount_point, node_ip=node_ip))

    test_path = f"{mount_point}/{IO_TEST_FILE}"
    checksum_path = IO_TEST_CHECKSUM_FILE

    # Write test file
    write_cmd = safe_run_on_remote_node(
        host,
        f"dd if=/dev/urandom of={test_path} bs={IO_TEST_BS} count={IO_TEST_COUNT} 2>/dev/null && echo write_ok",
        node_ip,
    )
    if "write_ok" not in write_cmd.stdout:
        # Cleanup
        safe_run_on_remote_node(host, f"rm -f {test_path}", node_ip)
        return {
            "success": False,
            "error": f"Write failed on {mount_point} on {node_ip}",
            "details": {},
        }

    # Compute checksum
    safe_run_on_remote_node(
        host,
        f"sha256sum {test_path} > {checksum_path}",
        node_ip,
    )

    # Verify checksum
    verify_cmd = safe_run_on_remote_node(
        host,
        f"sha256sum -c {checksum_path} && echo checksum_ok",
        node_ip,
    )
    checksum_ok = "checksum_ok" in verify_cmd.stdout

    # Cleanup
    safe_run_on_remote_node(host, f"rm -f {test_path} {checksum_path}", node_ip)

    return {
        "success": checksum_ok,
        "error": "" if checksum_ok else f"Checksum verification failed on {node_ip}",
        "details": {},
    }


def verify_bind_io_test(host, node_ip: str, bind_target: str, mount_point: str, node_key_value: str) -> Dict[str, Any]:
    """Validate I/O through bind mounts.

    Writes to bind target and verifies visibility at source.

    Returns:
        {"success": bool, "error": str, "details": {}}
    """
    log = TestLogger("verify_bind_io_test")
    log.check(TEST_LOG_MSGS["running_bind_io_test"].format(node_ip=node_ip))

    bind_file = f"{bind_target}/{BIND_IO_TEST_FILE}"

    # Write to bind target
    write_cmd = safe_run_on_remote_node(
        host,
        f"echo 'bind_io_test_data' > {bind_file}",
        node_ip,
    )
    if write_cmd.rc != 0:
        return {
            "success": False,
            "error": f"Write to bind target failed on {node_ip}",
            "details": {},
        }

    # Discover actual source path by finding the file under mount_point
    # The node_key_value from hostname may not exactly match cloud-init's value,
    # so we search for the test file under mount_point instead of computing the path
    find_cmd = safe_run_on_remote_node(
        host,
        f"find {mount_point}/ -maxdepth 8 -name '{BIND_IO_TEST_FILE}' -type f 2>/dev/null | head -1",
        node_ip,
    )
    found_path = find_cmd.stdout.strip()

    data_matches = False
    if found_path:
        read_cmd = safe_run_on_remote_node(
            host,
            f"cat '{found_path}'",
            node_ip,
        )
        data_matches = "bind_io_test_data" in read_cmd.stdout.strip()
    else:
        # Fallback: try computed path with node_key_value
        source_file = f"{mount_point}/{node_key_value}{bind_target}/{BIND_IO_TEST_FILE}"
        read_cmd = safe_run_on_remote_node(
            host,
            f"cat '{source_file}'",
            node_ip,
        )
        data_matches = "bind_io_test_data" in read_cmd.stdout.strip()

    # Cleanup
    safe_run_on_remote_node(host, f"rm -f {bind_file}", node_ip)

    return {
        "success": data_matches,
        "error": "" if data_matches else f"Bind I/O data mismatch on {node_ip}: file not found at source under {mount_point}",
        "details": {"found_source_path": found_path},
    }


# =============================================================================
# CLOUD-INIT AND LOGGING VERIFICATION FUNCTIONS
# =============================================================================

def verify_setup_log(host, node_ip: str, pv_name: str) -> Dict[str, Any]:
    """Check cloud-init runcmd log exists and shows completion.

    Returns:
        {"success": bool, "error": str, "details": {"log_exists": bool, "complete": bool, "errors": list}}
    """
    log = TestLogger("verify_setup_log")
    log.check(TEST_LOG_MSGS["checking_setup_log"].format(name=pv_name, node_ip=node_ip))

    log_path = ISCSI_SETUP_LOG_TEMPLATE.format(name=pv_name)

    # Check log exists
    exists_cmd = safe_run_on_remote_node(
        host,
        f"test -f {log_path} && echo exists || echo not_exists",
        node_ip,
    )
    log_exists = exists_cmd.stdout.strip() == "exists"

    if not log_exists:
        return {
            "success": False,
            "error": f"Setup log {log_path} does not exist on {node_ip}",
            "details": {"log_exists": False, "complete": False, "errors": []},
        }

    # Check completion message
    complete_cmd = safe_run_on_remote_node(
        host,
        f"grep '{ISCSI_SETUP_COMPLETE_MSG}' {log_path} && echo found || echo not_found",
        node_ip,
    )
    complete = "found" in complete_cmd.stdout.strip()

    # Check for script-level ERROR entries (from our log() function)
    # Only match lines starting with [timestamp] that contain ERROR
    # Ignore benign iSCSI tool messages like 'iscsiadm: initiator reported error'
    error_cmd = safe_run_on_remote_node(
        host,
        f"grep -E '^\\[.*\\].*ERROR' {log_path} || true",
        node_ip,
    )
    error_lines = [l.strip() for l in error_cmd.stdout.strip().split("\n") if l.strip()]

    success = log_exists and complete and len(error_lines) == 0

    return {
        "success": success,
        "error": "" if success else f"Setup log issues on {node_ip}: exists={log_exists}, complete={complete}, errors={len(error_lines)}",
        "details": {"log_exists": log_exists, "complete": complete, "errors": error_lines},
    }


def verify_cloud_init_groups_dict(host, pv_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Verify cloud_init_groups_dict contains powervault_scripts for matching groups.

    This is a pre-deployment check run inside omnia_core. It inspects the
    Ansible debug output or runs the role in check mode. For practical
    purposes, we verify the rendered script file exists in the container.

    Returns:
        {"success": bool, "error": str, "details": {}}
    """
    log = TestLogger("verify_cloud_init_groups_dict")
    log.check(TEST_LOG_MSGS["checking_cloud_init_dict"])

    pv_name = pv_entry.get("name", "")

    # Check if the template file exists in the mount_config role
    template_check = run_in_container(
        host,
        "test -f /omnia/provision/roles/mount_config/templates/setup_iscsi_storage.sh.j2 && echo exists || echo not_exists",
    )
    template_exists = template_check.stdout.strip() == "exists"

    # Check if process_single_powervault.yml task file exists
    task_check = run_in_container(
        host,
        "test -f /omnia/provision/roles/mount_config/tasks/process_single_powervault.yml && echo exists || echo not_exists",
    )
    task_exists = task_check.stdout.strip() == "exists"

    # Verify the powervault_config entry name exists in storage_config
    config = read_storage_config(host)
    pv_entries = config.get("powervault_config", []) or []
    name_found = any(e.get("name") == pv_name for e in pv_entries)

    success = template_exists and task_exists and name_found

    return {
        "success": success,
        "error": "" if success else f"Cloud-init integration check failed for '{pv_name}'",
        "details": {
            "template_exists": template_exists,
            "task_exists": task_exists,
            "name_in_config": name_found,
        },
    }


# =============================================================================
# FSTAB DUPLICATE VERIFICATION
# =============================================================================

def verify_no_duplicate_fstab(host, node_ip: str, mount_point: str) -> Dict[str, Any]:
    """Check for duplicate fstab entries for a mount point.

    Returns:
        {"success": bool, "error": str, "details": {"count": int}}
    """
    log = TestLogger("verify_no_duplicate_fstab")
    log.check(TEST_LOG_MSGS["checking_fstab_duplicates"].format(node_ip=node_ip))

    # Use grep + Python-side exact field matching to avoid awk $-variable
    # expansion issues through SSH double-quote wrapping
    cmd = safe_run_on_remote_node(
        host,
        f"grep '{mount_point}' {FSTAB_PATH} 2>/dev/null",
        node_ip,
    )

    # Count lines where 2nd field exactly matches mount_point (skip comments)
    count = 0
    for fline in cmd.stdout.strip().split("\n"):
        fparts = fline.strip().split()
        if (len(fparts) >= 2 and fparts[1] == mount_point
                and not fline.strip().startswith("#")):
            count += 1

    success = count == 1

    return {
        "success": success,
        "error": "" if success else f"Expected 1 fstab entry for {mount_point}, got {count} on {node_ip}",
        "details": {"count": count},
    }


def verify_mount_writable(host, node_ip: str, mount_path: str) -> Dict[str, Any]:
    """Verify a mount point is writable by creating and removing a temp file.

    Args:
        host: Testinfra host object
        node_ip: Target node IP
        mount_path: Mount path to test writability

    Returns:
        Dict with success, error, details keys
    """
    log = TestLogger("verify_mount_writable")
    test_file = f"{mount_path}/.omnia_write_test_{id(host)}"
    write_cmd = f"touch {test_file} && echo writable && rm -f {test_file}"
    log.check(TEST_LOG_MSGS.get(
        "checking_mount_writable",
        f"Checking writability of {mount_path} on {node_ip}",
    ))

    result = safe_run_on_remote_node(host, write_cmd, node_ip)
    writable = result.rc == 0 and "writable" in result.stdout.strip()

    return {
        "success": writable,
        "error": "" if writable else f"Mount {mount_path} is not writable on {node_ip}",
        "details": {"mount_path": mount_path, "writable": writable},
    }


SLURM_MANDATORY_BIND_MOUNTS = ["/var/lib/mysql", "/var/spool/slurm"]


def verify_slurm_mandatory_bind_mounts(
    host, node_ip: str, bind_targets: List[str]
) -> Dict[str, Any]:
    """Verify slurm_control_node has mandatory bind mounts configured and active.

    The mandatory bind paths are /var/lib/mysql and /var/spool/slurm.
    Each must be present in the entry's node_mount_point AND must be an
    active mountpoint on the target node.

    Args:
        host: Testinfra host object
        node_ip: Target node IP
        bind_targets: The entry's node_mount_point list

    Returns:
        Dict with success, error, details keys
    """
    results = []
    for mandatory in SLURM_MANDATORY_BIND_MOUNTS:
        configured = mandatory in bind_targets
        mounted = False
        if configured:
            chk = safe_run_on_remote_node(
                host,
                CMD_CHECK_MOUNTPOINT.format(path=mandatory),
                node_ip,
            )
            mounted = chk.rc == 0 and "mounted" in chk.stdout.strip()

        results.append({
            "path": mandatory,
            "configured": configured,
            "mounted": mounted,
            "success": configured and mounted,
        })

    all_ok = all(r["success"] for r in results)
    missing = [r["path"] for r in results if not r["success"]]

    return {
        "success": all_ok,
        "error": "" if all_ok else f"Mandatory bind mounts missing/inactive: {missing} on {node_ip}",
        "details": {"results": results, "missing": missing},
    }


def verify_mysql_data_on_mount(host, node_ip: str) -> Dict[str, Any]:
    """Verify MySQL/MariaDB data directory resides on PowerVault bind mount.

    Checks:
      1. /var/lib/mysql is a mountpoint (bind from PV)
      2. MariaDB/MySQL service is active
      3. MySQL data files exist (ibdata1 as indicator)
      4. slurm_acct_db database directory or table exists

    Args:
        host: Testinfra host object
        node_ip: Target node IP

    Returns:
        Dict with success, error, details keys
    """
    details = {
        "is_mountpoint": False,
        "service_active": False,
        "data_files_exist": False,
        "slurm_db_exists": False,
    }

    # 1. /var/lib/mysql is a mountpoint
    mp_cmd = safe_run_on_remote_node(
        host, CMD_CHECK_MOUNTPOINT.format(path="/var/lib/mysql"), node_ip
    )
    details["is_mountpoint"] = mp_cmd.rc == 0 and "mounted" in mp_cmd.stdout.strip()

    # 2. MariaDB/MySQL service active
    svc_cmd = safe_run_on_remote_node(
        host,
        "systemctl is-active mariadb 2>/dev/null || systemctl is-active mysqld 2>/dev/null",
        node_ip,
    )
    details["service_active"] = svc_cmd.rc == 0 and "active" in svc_cmd.stdout.strip()

    # 3. MySQL data files exist (ibdata1 is always present)
    data_cmd = safe_run_on_remote_node(
        host, "test -f /var/lib/mysql/ibdata1 && echo exists || echo missing", node_ip
    )
    details["data_files_exist"] = "exists" in data_cmd.stdout.strip()

    # 4. slurm_acct_db present (check via mysql or directory)
    db_cmd = safe_run_on_remote_node(
        host,
        "mysql -u root -e 'SHOW DATABASES' 2>/dev/null | grep -q slurm_acct_db && echo found || echo missing",
        node_ip,
    )
    details["slurm_db_exists"] = "found" in db_cmd.stdout.strip()

    errors = []
    if not details["is_mountpoint"]:
        errors.append("/var/lib/mysql is not a mountpoint")
    if not details["service_active"]:
        errors.append("MariaDB/MySQL service not active")
    if not details["data_files_exist"]:
        errors.append("MySQL data files not found in /var/lib/mysql")
    if not details["slurm_db_exists"]:
        errors.append("slurm_acct_db database not found")

    success = len(errors) == 0

    return {
        "success": success,
        "error": "" if success else "; ".join(errors),
        "details": details,
    }
