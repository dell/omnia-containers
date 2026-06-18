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
Upgrade Module - Prepare Upgrade Functions.

Functions for running and monitoring the ``prepare_upgrade.yml`` playbook
inside the omnia_core container.
"""

import time
from typing import Dict, Any, Optional, Callable

from ...core import run_in_container
from ..vars.prepare_upgrade_vars import PREPARE_UPGRADE_VARS


def run_prepare_upgrade(
    host,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> Dict[str, Any]:
    """
    Run ``prepare_upgrade.yml`` inside the omnia_core container.

    Starts the playbook in the background, polls every *poll_interval*
    seconds, and returns the last N lines of output on completion.

    Args:
        host: Testinfra host object
        progress_callback: Optional callable(elapsed_seconds) for progress

    Returns:
        Dict with success, rc, output (last N lines), error
    """
    container = PREPARE_UPGRADE_VARS["container_name"]
    playbook_path = PREPARE_UPGRADE_VARS["playbook_path"]
    log_file = PREPARE_UPGRADE_VARS["log_file"]
    poll_interval = PREPARE_UPGRADE_VARS["poll_interval"]
    tail_lines = PREPARE_UPGRADE_VARS["tail_lines"]

    rc_file = f"{log_file}.rc"

    # Start playbook in background; write exit code to rc_file on finish
    start_cmd = run_in_container(
        host,
        f"bash -c 'rm -f {rc_file}; "
        f"(ansible-playbook {playbook_path} > {log_file} 2>&1; "
        f"echo $? > {rc_file}) & echo $!'",
        container=container,
    )
    if start_cmd.rc != 0 or not start_cmd.stdout.strip():
        return {
            "success": False,
            "rc": start_cmd.rc,
            "output": "",
            "error": f"Failed to start playbook: {start_cmd.stderr.strip()}",
        }

    pid = start_cmd.stdout.strip()
    elapsed = 0

    # Poll until playbook finishes (rc_file appears when done)
    while True:
        time.sleep(poll_interval)
        elapsed += poll_interval

        if progress_callback:
            progress_callback(elapsed)

        check = run_in_container(
            host,
            f"test -f {rc_file} && echo DONE || echo RUNNING",
            container=container,
        )
        if check.stdout.strip() == "DONE":
            break

    # Read exit code from file
    rc_cmd = run_in_container(
        host, f"cat {rc_file} 2>/dev/null",
        container=container,
    )
    rc = int(rc_cmd.stdout.strip()) if rc_cmd.stdout.strip().isdigit() else 1

    # Get last N lines
    tail_cmd = run_in_container(
        host,
        f"tail -{tail_lines} {log_file} 2>/dev/null",
        container=container,
    )
    output = tail_cmd.stdout.strip() if tail_cmd.rc == 0 else ""

    return {
        "success": rc == 0,
        "rc": rc,
        "output": output,
        "error": "" if rc == 0 else f"Playbook exited with rc={rc}",
    }
