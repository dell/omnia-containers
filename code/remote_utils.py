#  Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
import subprocess
from typing import Tuple

"""
Utility functions for performing remote operations via SSH and SCP.

Includes:
- File copying with SCP using sshpass
- Remote command execution over SSH
- Node reachability check via ping

NOTE: This uses `sshpass`, which exposes the password on the command line.
Use only in trusted environments.
"""

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def copy_file_to_remote(
    user: str,
    password: str,
    ip: str,
    local_path: str,
    remote_path: str
) -> Tuple[int, str, str]:
    """
    Copy a file from the local system to a remote host using SCP.

    Returns:
        tuple: (return_code, stdout, stderr)
    """
    scp_command = [
        "sshpass", "-p", password,
        "scp", "-o", "StrictHostKeyChecking=no",
        local_path,
        f"{user}@{ip}:{remote_path}"
    ]

    try:
        result = subprocess.run(
            scp_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            check=False  # Fix W1510
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        logging.error("SCP operation timed out.")
        return -1, "", "Timeout"
    except subprocess.SubprocessError as exc:
        logging.error("SCP operation failed: %s", exc)
        return -1, "", str(exc)


def run_remote_command(
    user: str,
    password: str,
    ip: str,
    cmd: str
) -> Tuple[int, str, str]:
    """
    Run a command on a remote host over SSH.

    Returns:
        tuple: (return_code, stdout, stderr)
    """
    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"{user}@{ip}",
        cmd
    ]

    try:
        result = subprocess.run(
            ssh_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False  # Fix W1510
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        logging.error("SSH command timed out.")
        return -1, "", "Timeout"
    except subprocess.SubprocessError as exc:
        logging.error("SSH command failed: %s", exc)
        return -1, "", str(exc)


def check_node_reachability(
    ip: str,
    count: int = 3,
    timeout: int = 5
) -> Tuple[bool, str]:
    """
    Check if a remote node is reachable using ping.

    Returns:
        tuple: (reachable, output)
    """
    ping_command = ["ping", "-c", str(count), "-W", str(timeout), ip]

    try:
        result = subprocess.run(
            ping_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False  # Fix W1510
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip()
    except subprocess.SubprocessError as exc:
        logging.error("Ping failed: %s", exc)
        return False, str(exc)
