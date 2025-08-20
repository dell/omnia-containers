# remote_utils.py
# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
# Copyright (c) 2025 Your Name or Company
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

import subprocess
import logging
from typing import Tuple

logging.basicConfig(level=logging.INFO)

"""
This module provides utility functions to perform remote operations via SSH and SCP.

It includes functionality to:
- Copy files to a remote machine using `scp` with password authentication.
- Run commands on a remote machine over SSH.
- Check if a remote node is reachable using `ping`.

Note: This script uses `sshpass`, which exposes passwords on the command line.
It's intended for quick automation tasks in trusted environments only.
"""

def copy_file_to_remote(
    user: str,
    password: str,
    ip: str,
    local_path: str,
    remote_path: str
) -> Tuple[int, str, str]:
    """
    Copy a file from the local machine to a remote machine using SCP.

    Args:
        user (str): Username for SSH login.
        password (str): Password for SSH login.
        ip (str): IP address of the remote host.
        local_path (str): Path to the local file.
        remote_path (str): Destination path on the remote host.

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
            timeout=15
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        logging.error("SCP file copy timed out")
        return -1, "", "File copy timed out"
    except subprocess.SubprocessError as exc:
        logging.error("SCP file copy failed: %s", exc)
        return -1, "", str(exc)


def run_remote_command(
    user: str,
    password: str,
    ip: str,
    cmd: str
) -> Tuple[int, str, str]:
    """
    Run a shell command on a remote machine via SSH.

    Args:
        user (str): Username for SSH login.
        password (str): Password for SSH login.
        ip (str): IP address of the remote host.
        cmd (str): Shell command to execute on the remote host.

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
            timeout=10
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        logging.error("SSH command timed out")
        return -1, "", "Command timed out"
    except subprocess.SubprocessError as exc:
        logging.error("SSH command failed: %s", exc)
        return -1, "", str(exc)


def check_node_reachability(
    ip: str,
    count: int = 3,
    timeout: int = 5
) -> Tuple[bool, str]:
    """
    Check if a node is reachable using ping.

    Args:
        ip (str): IP address of the node to check.
        count (int): Number of ping packets to send.
        timeout (int): Timeout in seconds for each ping packet.

    Returns:
        tuple: (reachable, output)
    """
    ping_command = ["ping", "-c", str(count), "-W", str(timeout), ip]

    try:
        result = subprocess.run(
            ping_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except subprocess.SubprocessError as exc:
        logging.error("Ping failed: %s", exc)
        return False, str(exc)

