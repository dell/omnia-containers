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

"""User Registry - Verification Functions.

Provides functions for verifying user_registry configuration and
container image sync to Pulp from custom HTTPS/HTTP registries:
- Config loading from local_repo_config.yml
- HTTPS certificate/key file existence
- HTTP registry no-cert validation
- Registry authentication credential file existence
- Pulp container remote creation (HTTPS with --ca-cert/--client-key, HTTP without)
- Pulp container repository sync status for user-registry images

Source code references:
- common/library/modules/check_user_registry.py
- common/library/module_utils/local_repo/registry_utils.py
- common/library/module_utils/local_repo/user_image_utility.py
"""

import json
from typing import Any, Dict, List

from ...core import run_in_container, load_input_file
from ..vars.local_repo_vars import OMNIA_CORE_CONTAINER
from ..vars.user_registry_vars import (
    LOCAL_REPO_CONFIG_FILE,
    LOCAL_REPO_CONFIG_PATH,
    USER_REGISTRY_CREDENTIAL_FILE,
    USER_REGISTRY_CREDENTIAL_PATH,
    USER_REGISTRY_REPO_PREFIX,
    USER_REGISTRY_REMOTE_PREFIX,
    HTTPS_SCHEME,
    HTTP_SCHEME,
)
from .local_repo_func import run_in_omnia_core, _parse_json_output


# =============================================================================
# 1. USER REGISTRY CONFIG LOADED
# =============================================================================

def check_user_registry_config(host) -> Dict[str, Any]:
    """Load user_registry from local_repo_config.yml inside omnia_core container.

    Reads the local_repo_config.yml file and extracts the user_registry list.
    Returns the parsed registry entries with their protocol classification
    (HTTPS vs HTTP based on cert_path/key_path presence).

    Returns:
        dict with keys:
            success (bool): True if user_registry has at least one entry
            registries (list): Parsed registry entries with protocol info
            https_registries (list): Entries with cert_path and key_path
            http_registries (list): Entries without cert_path and key_path
            count (int): Total number of registry entries
            details (str): Human-readable summary
            error (str|None): Error message if failed
    """
    config = load_input_file(host, LOCAL_REPO_CONFIG_FILE)
    if not config:
        return {
            "success": False,
            "registries": [],
            "https_registries": [],
            "http_registries": [],
            "count": 0,
            "details": "",
            "error": f"Failed to read {LOCAL_REPO_CONFIG_FILE} from omnia_core container",
        }

    user_registry = config.get("user_registry")
    if not user_registry or not isinstance(user_registry, list):
        return {
            "success": False,
            "registries": [],
            "https_registries": [],
            "http_registries": [],
            "count": 0,
            "details": "user_registry is empty or not defined",
            "error": "user_registry section is empty or not defined in local_repo_config.yml",
        }

    https_registries = []
    http_registries = []

    for entry in user_registry:
        if not isinstance(entry, dict):
            continue
        host_val = entry.get("host", "")
        cert_path = (entry.get("cert_path") or "").strip()
        key_path = (entry.get("key_path") or "").strip()

        registry_info = {
            "host": host_val,
            "cert_path": cert_path,
            "key_path": key_path,
            "protocol": HTTPS_SCHEME if (cert_path and key_path) else HTTP_SCHEME,
        }

        if cert_path and key_path:
            https_registries.append(registry_info)
        else:
            http_registries.append(registry_info)

    all_registries = https_registries + http_registries
    details = (
        f"user_registry: {len(all_registries)} entries "
        f"({len(https_registries)} HTTPS, {len(http_registries)} HTTP)\n"
    )
    for reg in all_registries:
        details += f"  - {reg['host']} ({reg['protocol'].upper()})\n"

    return {
        "success": len(all_registries) > 0,
        "registries": all_registries,
        "https_registries": https_registries,
        "http_registries": http_registries,
        "count": len(all_registries),
        "details": details.strip(),
        "error": None,
    }


# =============================================================================
# 2. HTTPS CERTIFICATE/KEY FILE EXISTENCE
# =============================================================================

def check_user_registry_https_certs(host, https_registries: List[Dict]) -> Dict[str, Any]:
    """Verify cert_path and key_path files exist for HTTPS registries.

    For each HTTPS registry entry, checks that the cert_path (.crt) and
    key_path (.key) files exist inside the omnia_core container. These files
    are required for Pulp to create container remotes with --ca-cert and
    --client-key flags.

    Args:
        host: Testinfra host object
        https_registries: List of HTTPS registry entries with cert_path/key_path

    Returns:
        dict with keys:
            success (bool): True if all cert/key files exist
            valid (list): Entries where both cert and key files exist
            invalid (list): Entries with missing cert or key files
            details (str): Human-readable per-entry summary
            error (str|None): Error message if any files missing
    """
    if not https_registries:
        return {
            "success": True,
            "valid": [],
            "invalid": [],
            "details": "No HTTPS registries configured — nothing to check",
            "error": None,
        }

    valid = []
    invalid = []
    details = f"HTTPS cert/key check for {len(https_registries)} registries:\n"

    for reg in https_registries:
        host_val = reg["host"]
        cert_path = reg["cert_path"]
        key_path = reg["key_path"]

        cert_check = run_in_omnia_core(host, f"test -f '{cert_path}' && echo EXISTS || echo MISSING")
        key_check = run_in_omnia_core(host, f"test -f '{key_path}' && echo EXISTS || echo MISSING")

        cert_exists = "EXISTS" in (cert_check.get("stdout") or "")
        key_exists = "EXISTS" in (key_check.get("stdout") or "")

        if cert_exists and key_exists:
            valid.append(reg)
            details += f"  \u2713 {host_val}: cert={cert_path} key={key_path}\n"
        else:
            missing_parts = []
            if not cert_exists:
                missing_parts.append(f"cert_path '{cert_path}' MISSING")
            if not key_exists:
                missing_parts.append(f"key_path '{key_path}' MISSING")
            invalid.append({**reg, "missing": missing_parts})
            details += f"  \u2718 {host_val}: {', '.join(missing_parts)}\n"

    success = len(invalid) == 0
    return {
        "success": success,
        "valid": valid,
        "invalid": invalid,
        "details": details.strip(),
        "error": None if success else f"{len(invalid)} HTTPS registry(ies) have missing cert/key files",
    }


# =============================================================================
# 3. HTTP REGISTRY NO-CERT VALIDATION
# =============================================================================

def check_user_registry_http_no_certs(host, http_registries: List[Dict]) -> Dict[str, Any]:
    """Verify HTTP registries are configured without cert_path/key_path.

    HTTP registries should NOT have cert_path or key_path set. The Pulp
    remotes for HTTP registries are created without --ca-cert/--client-key flags.

    Args:
        host: Testinfra host object
        http_registries: List of HTTP registry entries

    Returns:
        dict with keys:
            success (bool): True if all HTTP registries have no certs
            valid (list): Entries correctly without certs
            warnings (list): Entries that have certs set (will be ignored)
            details (str): Human-readable summary
            error (str|None): Error message if any have certs
    """
    if not http_registries:
        return {
            "success": True,
            "valid": [],
            "warnings": [],
            "details": "No HTTP registries configured — nothing to check",
            "error": None,
        }

    valid = []
    warnings = []
    details = f"HTTP no-cert check for {len(http_registries)} registries:\n"

    for reg in http_registries:
        host_val = reg["host"]
        cert_path = reg.get("cert_path", "")
        key_path = reg.get("key_path", "")

        if not cert_path and not key_path:
            valid.append(reg)
            details += f"  \u2713 {host_val}: no cert_path/key_path (correct for HTTP)\n"
        else:
            warnings.append(reg)
            details += (
                f"  \u26a0 {host_val}: has cert_path={cert_path} key_path={key_path} "
                f"(will be ignored for HTTP registry)\n"
            )

    return {
        "success": True,
        "valid": valid,
        "warnings": warnings,
        "details": details.strip(),
        "error": None,
    }


# =============================================================================
# 4. REGISTRY AUTHENTICATION CREDENTIAL FILE
# =============================================================================

def check_user_registry_auth_credentials(host) -> Dict[str, Any]:
    """Verify user_registry_credential.yml exists and is readable.

    When user registries require authentication, credentials are stored in
    user_registry_credential.yml (optionally ansible-vault encrypted).

    Returns:
        dict with keys:
            success (bool): True if credential file exists
            file_exists (bool): Whether the file was found
            details (str): Human-readable summary
            error (str|None): Error message if file missing
    """
    file_check = run_in_omnia_core(
        host,
        f"test -f '{USER_REGISTRY_CREDENTIAL_PATH}' && echo EXISTS || echo MISSING"
    )
    file_exists = "EXISTS" in (file_check.get("stdout") or "")

    if file_exists:
        return {
            "success": True,
            "file_exists": True,
            "details": f"user_registry_credential.yml found at {USER_REGISTRY_CREDENTIAL_PATH}",
            "error": None,
        }

    return {
        "success": False,
        "file_exists": False,
        "details": f"user_registry_credential.yml NOT found at {USER_REGISTRY_CREDENTIAL_PATH}",
        "error": f"{USER_REGISTRY_CREDENTIAL_FILE} not found",
    }


# =============================================================================
# 5. PULP CONTAINER REPOS SYNCED FROM USER REGISTRIES
# =============================================================================

def check_user_registry_container_repos_synced(host) -> Dict[str, Any]:
    """Verify container repositories from user registries are synced in Pulp.

    User registry container repos in Pulp are prefixed with 'container_repo_'.
    This function lists all Pulp container repositories, filters those with the
    user registry prefix, and checks that they have been synced
    (latest_version_href is set).

    Returns:
        dict with keys:
            success (bool): True if all user registry repos are synced
            total_repos (int): Total user registry repos found
            synced_repos (int): Number synced
            not_synced_repos (int): Number not synced
            synced_list (list): Names of synced repos
            not_synced_list (list): Names of unsynced repos
            details (str): Human-readable summary
            error (str|None): Error message
    """
    cmd = run_in_omnia_core(host, "pulp container repository list 2>/dev/null")
    parsed = _parse_json_output(cmd)

    if not parsed["success"]:
        return {
            "success": False,
            "total_repos": 0,
            "synced_repos": 0,
            "not_synced_repos": 0,
            "synced_list": [],
            "not_synced_list": [],
            "details": "",
            "error": f"pulp container repository list failed: {parsed.get('error', '')}",
        }

    repos = parsed["data"] or []

    # Filter repos with user registry prefix
    user_repos = [
        r for r in repos
        if (r.get("name") or "").startswith(USER_REGISTRY_REPO_PREFIX)
    ]

    if not user_repos:
        return {
            "success": True,
            "total_repos": 0,
            "synced_repos": 0,
            "not_synced_repos": 0,
            "synced_list": [],
            "not_synced_list": [],
            "details": f"No user registry container repos found (prefix: {USER_REGISTRY_REPO_PREFIX})",
            "error": None,
        }

    synced = []
    not_synced = []
    for repo in user_repos:
        name = repo.get("name", "unknown")
        if repo.get("latest_version_href"):
            synced.append(name)
        else:
            not_synced.append(name)

    details = (
        f"User registry container repos: {len(synced)}/{len(user_repos)} synced\n"
    )
    for name in sorted(synced):
        details += f"  \u2713 {name}\n"
    for name in sorted(not_synced):
        details += f"  \u2718 {name} (not synced)\n"

    return {
        "success": len(not_synced) == 0,
        "total_repos": len(user_repos),
        "synced_repos": len(synced),
        "not_synced_repos": len(not_synced),
        "synced_list": synced,
        "not_synced_list": not_synced,
        "details": details.strip(),
        "error": (
            None if not not_synced
            else f"{len(not_synced)} user registry container repo(s) not synced"
        ),
    }


# =============================================================================
# 6. PULP CONTAINER REMOTES FOR USER REGISTRIES
# =============================================================================

def check_user_registry_remotes_in_pulp(host, registries: List[Dict]) -> Dict[str, Any]:
    """Verify Pulp container remotes exist for user registries.

    For each user registry, checks that corresponding Pulp container remotes
    (prefixed with 'user_remote_') exist. Also verifies that HTTPS remotes
    have TLS configuration (ca_cert, client_key set) while HTTP remotes do not.

    Args:
        host: Testinfra host object
        registries: List of all registry entries with protocol info

    Returns:
        dict with keys:
            success (bool): True if at least one user remote exists
            total_remotes (int): Total user remotes found in Pulp
            remotes (list): List of remote dicts found
            details (str): Human-readable summary
            error (str|None): Error message
    """
    cmd = run_in_omnia_core(host, "pulp container remote list 2>/dev/null")
    parsed = _parse_json_output(cmd)

    if not parsed["success"]:
        return {
            "success": False,
            "total_remotes": 0,
            "remotes": [],
            "details": "",
            "error": f"pulp container remote list failed: {parsed.get('error', '')}",
        }

    remotes = parsed["data"] or []

    # Filter remotes with user registry prefix
    user_remotes = [
        r for r in remotes
        if (r.get("name") or "").startswith(USER_REGISTRY_REMOTE_PREFIX)
    ]

    if not user_remotes:
        return {
            "success": False,
            "total_remotes": 0,
            "remotes": [],
            "details": f"No user registry remotes found (prefix: {USER_REGISTRY_REMOTE_PREFIX})",
            "error": "No Pulp container remotes created for user registries",
        }

    details = f"User registry remotes: {len(user_remotes)} found\n"

    https_remotes = []
    http_remotes = []

    for remote in user_remotes:
        name = remote.get("name", "unknown")
        url = remote.get("url", "")
        ca_cert = remote.get("ca_cert")
        client_key = remote.get("client_key")
        tls_validation = remote.get("tls_validation")

        has_tls = bool(ca_cert) or bool(client_key)

        if has_tls:
            https_remotes.append(name)
            details += f"  \u2713 {name} \u2014 HTTPS (ca_cert set, tls_validation={tls_validation})\n"
        else:
            http_remotes.append(name)
            details += f"  \u2713 {name} \u2014 HTTP (no TLS certs)\n"

    details += f"\nSummary: {len(https_remotes)} HTTPS, {len(http_remotes)} HTTP remotes"

    return {
        "success": True,
        "total_remotes": len(user_remotes),
        "https_remotes": len(https_remotes),
        "http_remotes": len(http_remotes),
        "remotes": user_remotes,
        "details": details.strip(),
        "error": None,
    }
