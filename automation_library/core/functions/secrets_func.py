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
Core Module - Secrets Viewer.

Functions for viewing encrypted (ansible-vault) or plain YAML credential files.
"""

from typing import Dict, Any

import yaml

from .host_func import run_in_container


def view_credentials_file(host, file_path: str, key_file_path: str) -> Dict[str, Any]:
    """
    View credentials file content - handles both encrypted and plain YAML.

    If the file is encrypted with ansible-vault, it will be decrypted using the key file.
    If the file is plain YAML, it will be read directly.

    Args:
        host: Testinfra host object
        file_path: Path to the credentials file (inside omnia_core container)
        key_file_path: Path to the vault key file (inside omnia_core container)

    Returns:
        Dict with:
            - success: bool
            - content: dict (parsed YAML content)
            - error: str (error message if failed)
    """
    result = {
        "success": False,
        "content": {},
        "error": "",
    }

    # First, try to decrypt vault file
    cmd = run_in_container(
        host,
        f"ansible-vault view {file_path} --vault-password-file {key_file_path} 2>/dev/null"
    )

    if cmd.rc == 0:
        # Successfully decrypted
        content = cmd.stdout
    else:
        # Vault decrypt failed - file might be plain YAML, try reading directly
        cmd = run_in_container(host, f"cat {file_path}")
        if cmd.rc != 0:
            result["error"] = f"Failed to read credentials file: {cmd.stderr}"
            return result
        content = cmd.stdout

    # Parse YAML content
    try:
        parsed = yaml.safe_load(content)
        if not isinstance(parsed, dict):
            result["error"] = "Credentials file is not a valid YAML dictionary"
            return result
        result["content"] = parsed
        result["success"] = True
    except yaml.YAMLError as e:
        result["error"] = f"Failed to parse YAML: {str(e)}"

    return result


def get_credential_value(host, file_path: str, key_file_path: str, key: str) -> str:
    """
    Get a specific credential value from a credentials file.

    Args:
        host: Testinfra host object
        file_path: Path to the credentials file (inside omnia_core container)
        key_file_path: Path to the vault key file (inside omnia_core container)
        key: The key to retrieve from the credentials file

    Returns:
        The credential value as string, or empty string if not found/error
    """
    result = view_credentials_file(host, file_path, key_file_path)
    if not result["success"]:
        return ""
    return str(result["content"].get(key, ""))


def get_multiple_credentials(
    host, file_path: str, key_file_path: str, keys: list
) -> Dict[str, Any]:
    """
    Get multiple credential values from a credentials file.

    Args:
        host: Testinfra host object
        file_path: Path to the credentials file (inside omnia_core container)
        key_file_path: Path to the vault key file (inside omnia_core container)
        keys: List of keys to retrieve from the credentials file

    Returns:
        Dict with:
            - success: bool
            - values: dict mapping key -> value
            - error: str (error message if failed)
            - missing: list of keys that were not found
    """
    result = {
        "success": False,
        "values": {},
        "error": "",
        "missing": [],
    }

    creds_result = view_credentials_file(host, file_path, key_file_path)
    if not creds_result["success"]:
        result["error"] = creds_result["error"]
        return result

    content = creds_result["content"]
    for key in keys:
        if key in content:
            result["values"][key] = str(content[key])
        else:
            result["missing"].append(key)

    if result["missing"]:
        result["error"] = f"Missing credentials: {', '.join(result['missing'])}"
    else:
        result["success"] = True

    return result
