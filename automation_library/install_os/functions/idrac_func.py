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

"""iDRAC verification functions for install_os automation.

iDRAC Redfish API calls run inside the omnia_core container via
``run_in_container`` because the BMC network is reachable from
the container's network namespace.
"""

from typing import Dict, Any

from automation_library.core import run_in_container
from automation_library.install_os.vars import INSTALL_OS_VARS


def check_idrac_reachable(
    host, bmc_ip: str, bmc_user: str = None, bmc_pass: str = None
) -> Dict[str, Any]:
    """Verify iDRAC is reachable via Redfish API."""
    user = bmc_user or "root"
    password = bmc_pass or ""
    cmd = run_in_container(
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
    cmd = run_in_container(
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


def check_os_deployment_job_status(
    host, bmc_ip: str, bmc_user: str = None, bmc_pass: str = None
) -> Dict[str, Any]:
    """Check iDRAC OS deployment job status from job queue (legacy idrac_os_deployment)."""
    user = bmc_user or "root"
    password = bmc_pass or ""
    cmd = run_in_container(
        host,
        f"curl -sk -u '{user}:{password}' "
        f"'https://{bmc_ip}/redfish/v1/Managers/iDRAC.Embedded.1/Jobs' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "job_status": "unknown",
            "error": f"Failed to query OS deployment jobs: {cmd.stderr.strip()}",
        }
    try:
        import json
        data = json.loads(cmd.stdout)
        members = data.get("Members", [])
        if not members:
            return {
                "success": True,
                "job_status": "not_found",
                "job_count": 0,
                "error": "",
            }
        # Look for OSD: BootTONetworkISO job
        for member in members:
            job_url = member.get("@odata.id", "")
            if "OSD" in job_url or "BootToNetworkISO" in job_url:
                job_cmd = run_in_container(
                    host,
                    f"curl -sk -u '{user}:{password}' "
                    f"'https://{bmc_ip}{job_url}' 2>/dev/null",
                )
                if job_cmd.rc == 0:
                    job_data = json.loads(job_cmd.stdout)
                    return {
                        "success": True,
                        "job_status": job_data.get("JobStatus", "unknown"),
                        "job_name": job_data.get("Name", ""),
                        "job_message": job_data.get("Message", ""),
                        "job_count": len(members),
                        "error": "",
                    }
        return {
            "success": True,
            "job_status": "not_found",
            "job_count": len(members),
            "error": "No BootToNetworkISO job found",
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "success": False,
            "job_status": "unknown",
            "error": "Failed to parse job queue response",
        }


def check_virtual_media_status(
    host, bmc_ip: str, bmc_user: str = None, bmc_pass: str = None
) -> Dict[str, Any]:
    """Check iDRAC virtual media insertion status (new individual modules approach)."""
    user = bmc_user or "root"
    password = bmc_pass or ""
    cmd = run_in_container(
        host,
        f"curl -sk -u '{user}:{password}' "
        f"'https://{bmc_ip}/redfish/v1/Managers/iDRAC.Embedded.1/VirtualMedia' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "vm_status": "unknown",
            "error": f"Failed to query virtual media: {cmd.stderr.strip()}",
        }
    try:
        import json
        data = json.loads(cmd.stdout)
        members = data.get("Members", [])
        if not members:
            return {
                "success": True,
                "vm_status": "not_found",
                "vm_count": 0,
                "error": "",
            }
        # Check if any virtual media is inserted
        for member in members:
            vm_url = member.get("@odata.id", "")
            vm_cmd = run_in_container(
                host,
                f"curl -sk -u '{user}:{password}' "
                f"'https://{bmc_ip}{vm_url}' 2>/dev/null",
            )
            if vm_cmd.rc == 0:
                vm_data = json.loads(vm_cmd.stdout)
                inserted = vm_data.get("Inserted", False)
                media_type = vm_data.get("MediaTypes", [])
                if inserted:
                    return {
                        "success": True,
                        "vm_status": "inserted",
                        "media_type": media_type,
                        "vm_count": len(members),
                        "error": "",
                    }
        return {
            "success": True,
            "vm_status": "not_inserted",
            "vm_count": len(members),
            "error": "",
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "success": False,
            "vm_status": "unknown",
            "error": "Failed to parse virtual media response",
        }


def check_boot_override_status(
    host, bmc_ip: str, bmc_user: str = None, bmc_pass: str = None
) -> Dict[str, Any]:
    """Check iDRAC boot override status (new individual modules approach)."""
    user = bmc_user or "root"
    password = bmc_pass or ""
    cmd = run_in_container(
        host,
        f"curl -sk -u '{user}:{password}' "
        f"'https://{bmc_ip}/redfish/v1/Systems/System.Embedded.1' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "boot_status": "unknown",
            "error": f"Failed to query boot status: {cmd.stderr.strip()}",
        }
    try:
        import json
        data = json.loads(cmd.stdout)
        boot = data.get("Boot", {})
        boot_source = boot.get("BootSourceOverrideTarget", "")
        boot_enabled = boot.get("BootSourceOverrideEnabled", "")
        boot_mode = boot.get("BootSourceOverrideMode", "")
        
        return {
            "success": True,
            "boot_source": boot_source,
            "boot_enabled": boot_enabled,
            "boot_mode": boot_mode,
            "error": "",
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "success": False,
            "boot_status": "unknown",
            "error": "Failed to parse boot status response",
        }


def check_power_state(
    host, bmc_ip: str, bmc_user: str = None, bmc_pass: str = None
) -> Dict[str, Any]:
    """Check iDRAC power state (new individual modules approach)."""
    user = bmc_user or "root"
    password = bmc_pass or ""
    cmd = run_in_container(
        host,
        f"curl -sk -u '{user}:{password}' "
        f"'https://{bmc_ip}/redfish/v1/Systems/System.Embedded.1' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "power_state": "unknown",
            "error": f"Failed to query power state: {cmd.stderr.strip()}",
        }
    try:
        import json
        data = json.loads(cmd.stdout)
        power_state = data.get("PowerState", "unknown")
        
        return {
            "success": True,
            "power_state": power_state,
            "error": "",
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "success": False,
            "power_state": "unknown",
            "error": "Failed to parse power state response",
        }


def verify_nfs_share_accessible(
    host, nfs_share: str
) -> Dict[str, Any]:
    """Verify NFS share is accessible from OIM."""
    # Parse NFS share (format: <nfs_server_ip>:<nfs_share_path>/<iso_filename>)
    try:
        parts = nfs_share.split(":")
        if len(parts) != 2:
            return {
                "success": False,
                "error": f"Invalid NFS share format: {nfs_share}. Expected: <ip>:<path>/<file>",
            }
        nfs_server = parts[0]
        nfs_path = parts[1]
        
        # Check if NFS server is reachable
        ping_cmd = run_in_container(host, f"ping -c 1 -W 2 {nfs_server} 2>/dev/null")
        if ping_cmd.rc != 0:
            return {
                "success": False,
                "nfs_server": nfs_server,
                "error": f"NFS server {nfs_server} not reachable",
            }
        
        # Check if NFS path exists locally (assuming OIM is the NFS server)
        local_path = nfs_path.split("/")[0] if "/" in nfs_path else nfs_path
        check_cmd = run_in_container(host, f"test -d /{local_path} && echo 'EXISTS' || echo 'NOT_FOUND'")
        exists = "EXISTS" in check_cmd.stdout
        
        return {
            "success": exists,
            "nfs_server": nfs_server,
            "nfs_path": nfs_path,
            "error": "" if exists else f"NFS path /{local_path} not found on OIM",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to parse NFS share: {str(e)}",
        }
