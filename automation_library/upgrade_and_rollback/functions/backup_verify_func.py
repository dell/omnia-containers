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
Upgrade Module - Backup Verification Functions.

Thin wrapper around the core ``compare_directory_md5sum`` utility.
Selects the correct command runners (OIM vs container) based on the
category configuration in ``BACKUP_VERIFY_VARS``.
"""

from functools import partial
from typing import Dict, Any

from ...core import run_in_container, run_on_oim, compare_directory_md5sum
from ..vars.backup_verify_vars import BACKUP_VERIFY_VARS


def verify_backup_md5sum(
    host,
    category: str,
) -> Dict[str, Any]:
    """
    Compare md5sum of all files in a backup directory against their
    current counterparts.

    The *category* selects paths from ``BACKUP_VERIFY_VARS`` (one of
    ``quadlets``, ``boot``, ``cloudinit``, ``nodes``, ``images``).

    Delegates to ``compare_directory_md5sum`` from the core module,
    choosing the correct command runner based on ``on_oim`` flag.

    Args:
        host: Testinfra host object
        category: Key in BACKUP_VERIFY_VARS (e.g. "quadlets")

    Returns:
        Dict with success, files (list of {name, match}), error
    """
    cfg = BACKUP_VERIFY_VARS.get(category)
    if cfg is None:
        return {
            "success": False,
            "files": [],
            "error": f"Unknown backup category: {category}",
        }

    container = BACKUP_VERIFY_VARS["container_name"]
    backup_dir = cfg["backup_dir"]
    current_dir = cfg["current_dir"]
    on_oim = cfg["on_oim"]
    exclude = cfg.get("exclude", [])

    # Check if source directory exists before attempting backup verification
    if on_oim:
        check_cmd = run_on_oim
    else:
        check_cmd = partial(run_in_container, container=container)
    
    dir_check = check_cmd(host, f"test -d {current_dir} && echo 'EXISTS' || echo 'NOT_EXISTS'")
    if dir_check.stdout.strip() != "EXISTS":
        return {
            "success": True,  # Skip test, not a failure
            "files": [],
            "error": f"Source directory {current_dir} does not exist - backup verification skipped",
            "skipped": True,
        }
    
    # Check if source directory has any files (for quadlets specifically)
    if category == "quadlets":
        files_check = check_cmd(host, f"ls -1 {current_dir}/*.container 2>/dev/null | wc -l")
        if files_check.stdout.strip() == "0":
            return {
                "success": True,  # Skip test, not a failure
                "files": [],
                "error": f"No .container files found in {current_dir} - backup verification skipped",
                "skipped": True,
            }

    # Backup files are always under /opt/omnia (shared volume) — container
    backup_cmd = partial(run_in_container, container=container)

    # Current files: OIM host or container depending on category
    if on_oim:
        current_cmd = run_on_oim
    else:
        current_cmd = partial(run_in_container, container=container)

    result = compare_directory_md5sum(
        host,
        backup_dir=backup_dir,
        current_dir=current_dir,
        backup_cmd_fn=backup_cmd,
        current_cmd_fn=current_cmd,
        exclude=exclude,
    )

    # Enrich error message with category context (exclude skipped files from count)
    if not result["success"] and result["files"]:
        mismatched = sum(1 for f in result["files"] if f["match"] == "✗")
        compared = sum(1 for f in result["files"] if f["match"] != "⊘")
        result["error"] = (
            f"{mismatched}/{compared} {category} backup files "
            f"do not match"
        )
    elif not result["files"]:
        # Check if this is expected (e.g., all files excluded for quadlets)
        if category == "quadlets":
            result["success"] = True  # Skip as success, not a failure
            result["error"] = f"No .container files found in {current_dir} (except omnia_core.container) - backup verification skipped"
            result["skipped"] = True
        else:
            result["error"] = f"No files found in {backup_dir}"

    return result
