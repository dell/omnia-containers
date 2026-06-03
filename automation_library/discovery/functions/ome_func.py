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
Discovery Module - OME (OpenManage Enterprise) Functions.

Functions for connecting to OME and retrieving static groups under Custom Groups.
"""

import base64
import json
from typing import Dict, Any, List

from automation_library.core import (
    run_in_container,
    load_input_file,
    get_credential_value,
)
from automation_library.core.vars import (
    OMNIA_CREDENTIALS_PATH,
    OMNIA_CREDENTIALS_KEY_PATH,
    DISCOVERY_CONFIG_FILE,
)
from ..vars import (
    OME_API_TIMEOUT,
    OME_SESSION_ENDPOINT,
    OME_GROUPS_ENDPOINT,
    OME_GROUP_DEVICES_ENDPOINT,
)


# Module-level cache for OME session
_ome_session_cache: Dict[str, Any] = {}


def clear_ome_cache():
    """Clear OME session cache."""
    global _ome_session_cache
    _ome_session_cache.clear()


def _ome_api_request(
    host,
    ome_ip: str,
    endpoint: str,
    method: str = "GET",
    data: Dict = None,
    auth_token: str = None,
) -> Dict[str, Any]:
    """
    Make HTTP request to OME REST API via curl inside omnia_core container.

    Args:
        host: Testinfra host object
        ome_ip: OME IP address
        endpoint: API endpoint
        method: HTTP method (GET, POST)
        data: JSON data for POST
        auth_token: X-Auth-Token for authenticated requests

    Returns:
        Dict with success, status_code, response, headers, error
    """
    result = {
        "success": False,
        "status_code": 0,
        "response": {},
        "headers": {},
        "error": "",
    }

    url = f"https://{ome_ip}{endpoint}"

    # Build curl command with headers output
    # Use single quotes for URL to prevent shell interpretation of $ in OData queries
    curl_parts = [
        "curl", "-s", "-k",
        "-D", "/tmp/ome_headers.txt",
        "-w", "'\\n%{http_code}'",
        "-X", method,
        f"--connect-timeout {OME_API_TIMEOUT}",
    ]

    if auth_token:
        curl_parts.append(f"-H 'X-Auth-Token: {auth_token}'")

    # Use single quotes for URL to prevent $ interpretation in OData filters
    curl_parts.append(f"'{url}'")

    if method == "POST" and data:
        curl_parts.insert(3, "-H 'Content-Type: application/json'")
        # Write JSON to temp file to avoid shell escaping issues
        json_data = json.dumps(data)
        b64_data = base64.b64encode(json_data.encode()).decode()
        # Use bash -c with base64 decode for POST data
        curl_cmd = " ".join(curl_parts)
        cmd_str = (
            f"bash -c \"echo '{b64_data}' | base64 -d > /tmp/ome_post.json "
            f"&& {curl_cmd} -d @/tmp/ome_post.json\""
        )
    else:
        cmd_str = " ".join(curl_parts)

    cmd = run_in_container(host, cmd_str)
    if cmd.rc != 0:
        result["error"] = f"curl failed: {cmd.stderr}"
        return result

    lines = cmd.stdout.strip().split("\n")
    if not lines:
        result["error"] = "Empty response from OME"
        return result

    try:
        result["status_code"] = int(lines[-1])
    except ValueError:
        result["error"] = f"Invalid status code: {lines[-1]}"
        return result

    body = "\n".join(lines[:-1])
    if body:
        try:
            result["response"] = json.loads(body)
        except json.JSONDecodeError:
            result["response"] = {}

    # Read headers
    headers_cmd = run_in_container(host, "cat /tmp/ome_headers.txt 2>/dev/null")
    if headers_cmd.rc == 0:
        for line in headers_cmd.stdout.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                result["headers"][key.strip()] = val.strip()

    if 200 <= result["status_code"] < 300:
        result["success"] = True
    else:
        err_msg = result["response"].get("error", {}).get("message", "Unknown error")
        result["error"] = f"HTTP {result['status_code']}: {err_msg}"

    return result


def get_ome_session(host) -> Dict[str, Any]:
    """
    Create authenticated session with OME.

    Uses existing get_credential_value from core module.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, token, ome_ip, error
    """
    global _ome_session_cache

    result = {
        "success": False,
        "token": "",
        "ome_ip": "",
        "error": "",
    }

    if _ome_session_cache.get("token"):
        result["token"] = _ome_session_cache["token"]
        result["ome_ip"] = _ome_session_cache["ome_ip"]
        result["success"] = True
        return result

    # Get discovery config
    config = load_input_file(host, DISCOVERY_CONFIG_FILE)
    if not config:
        result["error"] = "discovery_config.yml not found"
        return result

    if not config.get("enable_bmc_discovery", False):
        result["error"] = "BMC discovery not enabled"
        return result

    ome_ip = config.get("ome_ip", "")
    if not ome_ip:
        result["error"] = "OME IP not configured"
        return result

    result["ome_ip"] = ome_ip

    # Get credentials using existing core function
    username = get_credential_value(
        host, OMNIA_CREDENTIALS_PATH, OMNIA_CREDENTIALS_KEY_PATH, "ome_username"
    )
    password = get_credential_value(
        host, OMNIA_CREDENTIALS_PATH, OMNIA_CREDENTIALS_KEY_PATH, "ome_password"
    )

    if not username or not password:
        result["error"] = "OME credentials not found"
        return result

    session_data = {
        "UserName": username,
        "Password": password,
        "SessionType": "API",
    }

    resp = _ome_api_request(host, ome_ip, OME_SESSION_ENDPOINT, method="POST", data=session_data)
    if not resp["success"]:
        result["error"] = f"Failed to create OME session: {resp['error']}"
        return result

    # Token is in response headers
    token = resp["headers"].get("X-Auth-Token", "")
    if not token:
        result["error"] = "No X-Auth-Token in OME response headers"
        return result

    _ome_session_cache["token"] = token
    _ome_session_cache["ome_ip"] = ome_ip

    result["token"] = token
    result["success"] = True
    return result


def get_ome_static_groups(host) -> Dict[str, Any]:
    """
    Get static groups from OME (under Custom Groups > Static Groups).

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, groups (list of name, id), error
    """
    result = {
        "success": False,
        "groups": [],
        "error": "",
    }

    session = get_ome_session(host)
    if not session["success"]:
        result["error"] = session["error"]
        return result

    # First get all groups to find "Static Groups" parent
    resp = _ome_api_request(
        host,
        session["ome_ip"],
        OME_GROUPS_ENDPOINT,
        auth_token=session["token"]
    )

    if not resp["success"]:
        result["error"] = f"Failed to get OME groups: {resp['error']}"
        return result

    # Find Static Groups parent ID
    all_groups = resp["response"].get("value", [])
    static_groups_id = None
    for g in all_groups:
        if g.get("Name") == "Static Groups":
            static_groups_id = g.get("Id")
            break

    if not static_groups_id:
        result["error"] = "Static Groups parent not found in OME"
        return result

    # Get subgroups of Static Groups
    resp2 = _ome_api_request(
        host,
        session["ome_ip"],
        f"/api/GroupService/Groups({static_groups_id})/SubGroups",
        auth_token=session["token"]
    )

    if not resp2["success"]:
        result["error"] = f"Failed to get Static Groups subgroups: {resp2['error']}"
        return result

    subgroups = resp2["response"].get("value", [])
    for g in subgroups:
        result["groups"].append({
            "name": g.get("Name", ""),
            "id": g.get("Id", 0),
        })

    result["success"] = True
    return result


def get_ome_group_device_ips(host, group_id: int) -> Dict[str, Any]:
    """
    Get device IPs (management/BMC IPs) from an OME group.

    Args:
        host: Testinfra host object
        group_id: OME group ID

    Returns:
        Dict with success, ips (list), error
    """
    result = {
        "success": False,
        "ips": [],
        "error": "",
    }

    session = get_ome_session(host)
    if not session["success"]:
        result["error"] = session["error"]
        return result

    endpoint = OME_GROUP_DEVICES_ENDPOINT.format(group_id=group_id)
    resp = _ome_api_request(
        host,
        session["ome_ip"],
        endpoint,
        auth_token=session["token"]
    )

    if not resp["success"]:
        result["error"] = f"Failed to get group devices: {resp['error']}"
        return result

    devices = resp["response"].get("value", [])
    ips = []
    for device in devices:
        # Get management IP from DeviceManagement array
        mgmt_info = device.get("DeviceManagement", [])
        for mgmt in mgmt_info:
            ip = mgmt.get("NetworkAddress", "")
            if ip:
                ips.append(ip)
                break

    result["ips"] = sorted(list(set(ips)))
    result["success"] = True
    return result


def get_ome_all_devices(host) -> Dict[str, Any]:
    """
    Get all devices from OME (servers only, device_type=1000).

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, devices (list of device info), error
    """
    result = {
        "success": False,
        "devices": [],
        "error": "",
    }

    session = get_ome_session(host)
    if not session["success"]:
        result["error"] = session["error"]
        return result

    # Get all devices with type filter for servers (1000)
    # URL-encode $filter and spaces to avoid shell interpretation
    endpoint = "/api/DeviceService/Devices?%24filter=Type%20eq%201000"
    resp = _ome_api_request(
        host,
        session["ome_ip"],
        endpoint,
        auth_token=session["token"]
    )

    if not resp["success"]:
        result["error"] = f"Failed to get OME devices: {resp['error']}"
        return result

    devices = resp["response"].get("value", [])
    for device in devices:
        device_id = device.get("Id", 0)
        device_name = device.get("DeviceName", "")
        identifier = device.get("Identifier", "")
        model = device.get("Model", "")

        # Get management IP
        mgmt_ip = ""
        mgmt_info = device.get("DeviceManagement", [])
        for mgmt in mgmt_info:
            ip = mgmt.get("NetworkAddress", "")
            if ip:
                mgmt_ip = ip
                break

        result["devices"].append({
            "id": device_id,
            "name": device_name,
            "identifier": identifier,
            "model": model,
            "ip": mgmt_ip,
        })

    result["success"] = True
    return result


def get_ome_device_inventory(
    host, device_id: int, inventory_type: str = "serverNetworkInterfaces"
) -> Dict[str, Any]:
    """
    Get device inventory details from OME.

    Args:
        host: Testinfra host object
        device_id: OME device ID
        inventory_type: Type of inventory (serverNetworkInterfaces, deviceNics, etc.)

    Returns:
        Dict with success, inventory (list), error
    """
    result = {
        "success": False,
        "inventory": [],
        "error": "",
    }

    session = get_ome_session(host)
    if not session["success"]:
        result["error"] = session["error"]
        return result

    # URL-encode single quotes in inventory type parameter
    endpoint = f"/api/DeviceService/Devices({device_id})/InventoryDetails(%27{inventory_type}%27)"
    resp = _ome_api_request(
        host,
        session["ome_ip"],
        endpoint,
        auth_token=session["token"]
    )

    if not resp["success"]:
        result["error"] = f"Failed to get device inventory: {resp['error']}"
        return result

    result["inventory"] = resp["response"].get("InventoryInfo", [])
    result["success"] = True
    return result


def get_ome_device_details_by_service_tag(host, service_tag: str) -> Dict[str, Any]:
    """
    Get detailed device info from OME by service tag.

    Returns first_nic_mac (first active non-iDRAC NIC) and ib_nic_name.

    Args:
        host: Testinfra host object
        service_tag: Device service tag

    Returns:
        Dict with success, device_id, first_nic_mac, first_nic_name,
        ib_nic_name, ib_nic_status, ib_nic_exists, error
    """
    result = {
        "success": False,
        "device_id": 0,
        "first_nic_mac": "",
        "first_nic_name": "",
        "ib_nic_name": "",
        "ib_nic_status": "",  # "Up", "Down", or "" if no IB NIC
        "ib_nic_exists": False,  # True if any IB NIC found (regardless of status)
        "error": "",
    }

    session = get_ome_session(host)
    if not session["success"]:
        result["error"] = session["error"]
        return result

    # Find device by service tag (URL-encode $filter, spaces, and quotes)
    endpoint = f"/api/DeviceService/Devices?%24filter=Identifier%20eq%20%27{service_tag}%27"
    resp = _ome_api_request(
        host,
        session["ome_ip"],
        endpoint,
        auth_token=session["token"]
    )

    if not resp["success"]:
        result["error"] = f"Failed to find device: {resp['error']}"
        return result

    devices = resp["response"].get("value", [])
    if not devices:
        result["error"] = f"Device with service tag '{service_tag}' not found in OME"
        return result

    device = devices[0]
    device_id = device.get("Id", 0)
    result["device_id"] = device_id

    # Get NIC inventory
    nic_result = get_ome_device_inventory(host, device_id, "serverNetworkInterfaces")
    if not nic_result["success"]:
        result["error"] = nic_result["error"]
        return result

    nic_info_list = nic_result["inventory"]

    # Find first non-iDRAC NIC with LinkStatus "Up"; fall back to first non-iDRAC NIC
    fallback_nic_name = ""
    fallback_nic_mac = ""

    for nic in nic_info_list:
        nic_id = nic.get("NicId", "")
        if "iDRAC" in nic_id.upper():
            continue

        ports = nic.get("Ports", [])
        for port in ports:
            partitions = port.get("Partitions", [])
            if not partitions:
                continue
            mac = partitions[0].get("CurrentMacAddress", "")
            if not mac:
                continue

            # Remember first non-iDRAC NIC as fallback
            if not fallback_nic_mac:
                fallback_nic_name = nic_id
                fallback_nic_mac = mac

            # Prefer port with LinkStatus "Up"
            link_status = (port.get("LinkStatus") or "").strip()
            if link_status.upper() == "UP":
                result["first_nic_name"] = nic_id
                result["first_nic_mac"] = mac
                break

        if result["first_nic_mac"]:
            break

    # Use fallback if no NIC with link up was found
    if not result["first_nic_mac"] and fallback_nic_mac:
        result["first_nic_name"] = fallback_nic_name
        result["first_nic_mac"] = fallback_nic_mac

    # Get InfiniBand NIC: FQDD contains "InfiniBand"
    # Track both UP and DOWN status for validation
    ib_nic_found = False
    ib_nic_down_name = ""
    for nic in nic_info_list:
        nic_id = nic.get("NicId", "")
        if "infiniband" not in nic_id.lower():
            continue
        ib_nic_found = True
        result["ib_nic_exists"] = True
        for port in nic.get("Ports", []):
            link_status = (port.get("LinkStatus") or "").strip()
            port_id = port.get("PortId", "")
            nic_name = port_id if port_id else nic_id

            if link_status.upper() == "UP":
                result["ib_nic_name"] = nic_name
                result["ib_nic_status"] = "Up"
                break
            elif link_status.upper() == "DOWN" and not ib_nic_down_name:
                # Remember first DOWN IB NIC
                ib_nic_down_name = nic_name

        if result["ib_nic_name"]:
            break

    # If no UP IB NIC found but DOWN exists, record it
    if not result["ib_nic_name"] and ib_nic_down_name:
        result["ib_nic_status"] = "Down"

    result["success"] = True
    return result


def get_ome_devices_without_static_group(host) -> Dict[str, Any]:
    """
    Get devices from OME that are NOT assigned to any static group.

    These devices will get the default functional group (slurm_node_aarch64)
    during discovery.

    Args:
        host: Testinfra host object

    Returns:
        Dict with success, unassigned_devices (list), assigned_count, total_count, error
    """
    result = {
        "success": False,
        "unassigned_devices": [],
        "assigned_count": 0,
        "total_count": 0,
        "error": "",
    }

    # Get all devices
    all_devices_result = get_ome_all_devices(host)
    if not all_devices_result["success"]:
        result["error"] = all_devices_result["error"]
        return result

    all_devices = all_devices_result["devices"]
    result["total_count"] = len(all_devices)

    # Get all static groups
    static_groups_result = get_ome_static_groups(host)
    if not static_groups_result["success"]:
        result["error"] = static_groups_result["error"]
        return result

    # Build set of device IDs that are in static groups
    assigned_device_ids = set()
    for group in static_groups_result["groups"]:
        group_devices = get_ome_group_device_ips(host, group["id"])
        if group_devices["success"]:
            # We need device IDs, not IPs - let's get them properly
            session = get_ome_session(host)
            if session["success"]:
                endpoint = f"/api/GroupService/Groups({group['id']})/Devices"
                resp = _ome_api_request(
                    host,
                    session["ome_ip"],
                    endpoint,
                    auth_token=session["token"]
                )
                if resp["success"]:
                    for device in resp["response"].get("value", []):
                        assigned_device_ids.add(device.get("Id", 0))

    result["assigned_count"] = len(assigned_device_ids)

    # Find unassigned devices
    for device in all_devices:
        if device["id"] not in assigned_device_ids:
            result["unassigned_devices"].append(device)

    result["success"] = True
    return result
