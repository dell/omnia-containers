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
Additional Cloud-Init Module - SMD Functions.

SMD group management and BSS registration functions.
"""

import json
from typing import Dict, Any, List

from automation_library.core import run_on_oim
from ..vars.common_vars import SMD_GROUP_PREFIX, COMMON_SMD_GROUP_NAME

# Cache for access token
_access_token_cache = {"token": None}


def _get_ochami_token(host) -> str:
    """Generate and cache an ochami access token."""
    if _access_token_cache["token"]:
        return _access_token_cache["token"]
    result = run_on_oim(host, "sudo bash -lc gen_access_token")
    if result.rc == 0 and result.stdout.strip():
        _access_token_cache["token"] = result.stdout.strip()
    return _access_token_cache.get("token", "")


def _run_ochami(host, cmd: str):
    """Run an ochami command with the access token injected."""
    token = _get_ochami_token(host)
    env_prefix = ""
    if token:
        # Derive env var name from hostname (e.g. vastoim -> VASTOIM_ACCESS_TOKEN)
        hostname_result = run_on_oim(host, "hostname -s")
        hostname = hostname_result.stdout.strip().split(".")[0].upper()
        env_prefix = f"{hostname}_ACCESS_TOKEN={token} "
    return run_on_oim(host, f"{env_prefix}{cmd}")


def verify_smd_group_creation(host, group_name: str, xnames: List[str]) -> Dict[str, Any]:
    """
    Verify SMD group exists and has correct members (query-only validation).

    This function only queries existing state without creating/modifying groups.
    Assumes provision playbook has already created the groups.

    Args:
        host: Testinfra host object
        group_name: Name of the SMD group to verify
        xnames: List of expected XNAME identifiers for nodes

    Returns:
        Dict with success, error, and group details
    """
    try:
        if not xnames:
            return {
                "success": False,
                "error": "No XNAMEs provided for verification",
                "group_name": group_name,
                "expected_xnames": [],
                "found_xnames": [],
                "details": "Cannot verify group with empty XNAME list"
            }

        # Query existing group state (no creation)
        verify_result = _verify_group_membership(host, group_name, xnames)

        return {
            "success": verify_result["success"],
            "error": verify_result["error"],
            "group_name": group_name,
            "expected_xnames": xnames,
            "found_xnames": verify_result.get("found_xnames", []),
            "details": verify_result["details"]
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Exception during SMD group verification: {str(e)}",
            "group_name": group_name,
            "expected_xnames": xnames,
            "found_xnames": [],
            "details": f"Exception: {str(e)}"
        }




def _verify_group_membership(host, group_name: str, expected_xnames: List[str]) -> Dict[str, Any]:
    """Verify SMD group exists and has correct members (query-only)."""
    try:
        # Get group members (query existing state)
        get_cmd = f"ochami smd group get --name {group_name}"
        result = _run_ochami(host, get_cmd)
        
        if result.rc != 0:
            return {
                "success": False,
                "error": f"Group {group_name} not found or members query failed: {result.stderr}",
                "found_xnames": [],
                "details": f"Group verification failed with exit code {result.rc}"
            }
        
        # Parse the JSON output to get actual members
        try:
            groups_data = json.loads(result.stdout.strip())
            found_xnames = []
            for group in groups_data:
                if group.get("label") == group_name:
                    members = group.get("members", {}).get("ids", [])
                    found_xnames.extend(members)
                    break
            
        except (json.JSONDecodeError, Exception) as e:
            return {
                "success": False,
                "error": f"Failed to parse group members output: {str(e)}",
                "found_xnames": [],
                "details": f"Output parsing failed: {str(e)}"
            }
        
        # Compare expected vs found
        expected_set = set(expected_xnames)
        found_set = set(found_xnames)
        
        missing = expected_set - found_set
        extra = found_set - expected_set
        
        success = len(missing) == 0 and len(extra) == 0
        
        error = ""
        if missing:
            error += f"Missing XNAMEs: {sorted(missing)}. "
        if extra:
            error += f"Extra XNAMEs: {sorted(extra)}. "
        
        return {
            "success": success,
            "error": error.strip(),
            "found_xnames": found_xnames,
            "missing_xnames": sorted(missing),
            "extra_xnames": sorted(extra),
            "details": f"Group {group_name} has {len(found_xnames)} members (expected {len(expected_xnames)})"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception verifying group membership: {str(e)}",
            "found_xnames": [],
            "details": str(e)
        }


def verify_smd_group_deletion(host, group_name: str) -> Dict[str, Any]:
    """
    Verify SMD group does not exist (query-only validation).

    This function only queries existing state without deleting groups.
    Used for idempotency testing to verify groups were cleaned up.

    Args:
        host: Testinfra host object
        group_name: Name of the SMD group to verify

    Returns:
        Dict with success, error, and existence details
    """
    try:
        # Query group existence (no deletion)
        verify_cmd = f"ochami smd group get --name {group_name}"
        verify_result = _run_ochami(host, verify_cmd)

        # Group should not exist (non-zero exit code expected)
        group_exists = verify_result.rc == 0

        return {
            "success": not group_exists,
            "error": f"Group still exists (expected to be deleted)" if group_exists else "",
            "group_name": group_name,
            "group_exists": group_exists,
            "details": f"Group {'exists' if group_exists else 'does not exist'}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Exception during group existence verification: {str(e)}",
            "group_name": group_name,
            "group_exists": True,
            "details": str(e)
        }


def verify_bss_group_registration(host, group_name: str) -> Dict[str, Any]:
    """
    Verify BSS cloud-init group registration (query-only validation).

    This function only queries existing registration state without registering groups.
    Assumes provision playbook has already registered the groups.

    Args:
        host: Testinfra host object
        group_name: Name of the cloud-init group to verify

    Returns:
        Dict with success, error, and registration details
    """
    try:
        # Query existing registration state (no registration)
        verify_cmd = f"ochami cloud-init group get config {group_name}"
        verify_result = _run_ochami(host, verify_cmd)

        registered = verify_result.rc == 0

        return {
            "success": registered,
            "error": f"Group not found in BSS: {verify_result.stderr}" if not registered else "",
            "group_name": group_name,
            "registered": registered,
            "details": f"BSS registration {'found' if registered else 'not found'}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Exception during BSS registration verification: {str(e)}",
            "group_name": group_name,
            "registered": False,
            "details": str(e)
        }


def get_xnames_for_fg(host, functional_group: str) -> List[str]:
    """
    Get xnames for a functional group from the SMD group.

    Args:
        host: Testinfra host object
        functional_group: Functional group name (used as SMD group label)

    Returns:
        List of xname strings from the SMD group membership
    """
    try:
        get_cmd = f"ochami smd group get --name {functional_group}"
        result = _run_ochami(host, get_cmd)
        if result.rc != 0:
            return []
        groups_data = json.loads(result.stdout.strip())
        for group in groups_data:
            if group.get("label") == functional_group:
                return group.get("members", {}).get("ids", [])
        return []
    except Exception:
        return []


def get_all_xnames(host) -> List[str]:
    """
    Get all node xnames from SMD components.

    Args:
        host: Testinfra host object

    Returns:
        List of all node xname strings
    """
    try:
        result = _run_ochami(host, "ochami smd component get")
        if result.rc != 0:
            return []
        data = json.loads(result.stdout.strip())
        return [c["ID"] for c in data.get("Components", [])
                if c.get("Type") == "Node" and c.get("State") != "Empty"]
    except Exception:
        return []


def get_common_smd_group_name() -> str:
    """Get the SMD group name for common cloud-init."""
    return COMMON_SMD_GROUP_NAME


def get_per_fg_smd_group_name(functional_group: str) -> str:
    """Get the SMD group name for per-FG cloud-init."""
    return f"{SMD_GROUP_PREFIX}_{functional_group}"
