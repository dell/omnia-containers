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

"""iDRAC verification functions for install_os automation."""

from typing import Dict, Any

from automation_library.core import run_on_oim
from automation_library.install_os.vars import INSTALL_OS_VARS


def check_idrac_reachable(
    host, bmc_ip: str, bmc_user: str = None, bmc_pass: str = None
) -> Dict[str, Any]:
    """Verify iDRAC is reachable via Redfish API."""
    user = bmc_user or "root"
    password = bmc_pass or ""
    cmd = run_on_oim(
        host,
        f"curl -sk -u '{user}:{password}' "
        f"-o /dev/null -w '%{{http_code}}' "
        f"'https://{bmc_ip}/redfish/v1/' 2>/dev/null",
    )
    status_code = cmd.stdout.strip()
    reachable = status_code == "200"
    return {
        "success": reachable,
        "bmc_ip": bmc_ip,
        "status_code": status_code,
        "error": "" if reachable else f"iDRAC not reachable at {bmc_ip} (HTTP {status_code})",
    }


def check_idrac_lc_status(
    host, bmc_ip: str, bmc_user: str = None, bmc_pass: str = None
) -> Dict[str, Any]:
    """Check iDRAC Lifecycle Controller status."""
    user = bmc_user or "root"
    password = bmc_pass or ""
    cmd = run_on_oim(
        host,
        f"curl -sk -u '{user}:{password}' "
        f"-X POST -H 'Content-Type: application/json' -d '{{}}' "
        f"'https://{bmc_ip}/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/"
        f"DellLCService/Actions/DellLCService.GetRemoteServicesAPIStatus' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "lc_status": "unknown",
            "error": f"Failed to query LC status: {cmd.stderr.strip()}",
        }
    try:
        import json
        data = json.loads(cmd.stdout)
        lc_status = data.get("LCStatus", "unknown")
        ready = lc_status.lower() == "ready"
        return {
            "success": ready,
            "lc_status": lc_status,
            "error": "" if ready else f"LC not ready: {lc_status}",
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "success": False,
            "lc_status": "unknown",
            "error": "Failed to parse LC status response",
        }


def check_virtual_media_status(
    host, bmc_ip: str, bmc_user: str = None, bmc_pass: str = None
) -> Dict[str, Any]:
    """Check current virtual media mount status."""
    user = bmc_user or "root"
    password = bmc_pass or ""
    cmd = run_on_oim(
        host,
        f"curl -sk -u '{user}:{password}' "
        f"'https://{bmc_ip}/redfish/v1/Managers/iDRAC.Embedded.1/"
        f"VirtualMedia' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "mounted": False,
            "error": f"Failed to query virtual media: {cmd.stderr.strip()}",
        }
    try:
        import json
        data = json.loads(cmd.stdout)
        members = data.get("Members", [])
        return {
            "success": True,
            "members_count": len(members),
            "error": "",
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "success": False,
            "mounted": False,
            "error": "Failed to parse virtual media response",
        }
