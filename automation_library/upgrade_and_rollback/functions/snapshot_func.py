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
K8s & Telemetry Upgrade - Snapshot Persistence.

Saves the collected pre-upgrade state as a JSON file on the OIM server
so that post-check tests can load and compare against the baseline.
"""

import json
from typing import Dict, Any

from ...core import run_on_oim
from ..vars.k8s_telemetry_upgrade_vars import SNAPSHOT_PATH


def save_precheck_snapshot(host, data: Dict[str, Any],
                           path: str = "") -> Dict[str, Any]:
    """
    Persist the pre-upgrade snapshot as JSON on the OIM server.

    Args:
        host: Testinfra host object
        data: Collected pre-check data dict
        path: Override snapshot file path (default: SNAPSHOT_PATH)

    Returns:
        Dict with success, path, error
    """
    target = path or SNAPSHOT_PATH
    payload = json.dumps(data, indent=2, default=str)

    # Write via shell to handle remote OIM
    # Use quoted heredoc delimiter ('SNAPSHOT_EOF') to prevent shell interpretation
    # No manual escaping needed since quoted heredoc preserves content literally
    write_cmd = f"cat > '{target}' << 'SNAPSHOT_EOF'\n{payload}\nSNAPSHOT_EOF"
    cmd = run_on_oim(host, write_cmd)
    if cmd.rc != 0:
        return {
            "success": False,
            "path": target,
            "error": f"Failed to write snapshot: {cmd.stderr.strip()}",
        }

    # Verify file exists and is non-empty
    verify = run_on_oim(host, f"test -s '{target}' && echo OK")
    if verify.rc != 0 or "OK" not in verify.stdout:
        return {
            "success": False,
            "path": target,
            "error": "Snapshot file empty or missing after write",
        }

    return {"success": True, "path": target, "error": ""}


def load_precheck_snapshot(host, path: str = "") -> Dict[str, Any]:
    """
    Load the pre-upgrade snapshot from the OIM server.

    Args:
        host: Testinfra host object
        path: Override snapshot file path (default: SNAPSHOT_PATH)

    Returns:
        Dict with success, data={...}, path, error
    """
    target = path or SNAPSHOT_PATH

    exists = run_on_oim(host, f"test -f '{target}' && echo OK")
    if exists.rc != 0 or "OK" not in exists.stdout:
        return {
            "success": False,
            "data": {},
            "path": target,
            "error": f"Snapshot file not found: {target}",
        }

    cmd = run_on_oim(host, f"cat '{target}'")
    if cmd.rc != 0:
        return {
            "success": False,
            "data": {},
            "path": target,
            "error": f"Failed to read snapshot: {cmd.stderr.strip()}",
        }

    try:
        data = json.loads(cmd.stdout.strip())
        return {"success": True, "data": data, "path": target, "error": ""}
    except (json.JSONDecodeError, TypeError) as exc:
        return {
            "success": False,
            "data": {},
            "path": target,
            "error": f"Invalid JSON in snapshot: {exc}",
        }
