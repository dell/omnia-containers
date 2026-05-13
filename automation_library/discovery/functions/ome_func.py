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
    curl_parts = [
        "curl", "-s", "-k",
        "-D", "/tmp/ome_headers.txt",
        "-w", "'\\n%{http_code}'",
        "-X", method,
        f"--connect-timeout {OME_API_TIMEOUT}",
    ]

    if auth_token:
        curl_parts.append(f"-H 'X-Auth-Token: {auth_token}'")

    if method == "POST" and data:
        curl_parts.append("-H 'Content-Type: application/json'")
        curl_parts.append(f"-d '{json.dumps(data)}'")

    curl_parts.append(f"'{url}'")
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
    username = get_credential_value(host, OMNIA_CREDENTIALS_PATH, OMNIA_CREDENTIALS_KEY_PATH, "ome_username")
    password = get_credential_value(host, OMNIA_CREDENTIALS_PATH, OMNIA_CREDENTIALS_KEY_PATH, "ome_password")

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
