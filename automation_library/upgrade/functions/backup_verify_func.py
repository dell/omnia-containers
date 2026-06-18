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
    )

    # Enrich error message with category context
    if not result["success"] and result["files"]:
        mismatched = sum(1 for f in result["files"] if f["match"] != "✓")
        result["error"] = (
            f"{mismatched}/{len(result['files'])} {category} backup files "
            f"do not match"
        )
    elif not result["files"]:
        result["error"] = f"No files found in {backup_dir}"

    return result
