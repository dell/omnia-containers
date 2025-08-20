# test_remote_operations.py
# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# Copyright (c) 2025 Your Name or Company
# Licensed under the MIT License. See LICENSE file in the project root for full license information.

import pytest
from vars import DEST_USER, DEST_PASS, DEST_IP, LOCAL_FILE, REMOTE_PATH
from remote_utils import copy_file_to_remote, run_remote_command, check_node_reachability

"""
Test suite for remote operations:
- Node reachability via ping
- File copy to remote host via SCP
- Remote command execution (valid and invalid)
"""

VALID_COMMAND = "echo hello"
INVALID_COMMAND = "someinvalidcommand1234"


@pytest.mark.parametrize("ip, expected", [(DEST_IP, True)])
def test_node_reachability(ip: str, expected: bool) -> None:
    """
    Test whether a node is reachable using ping.
    """
    reachable, message = check_node_reachability(ip)
    assert reachable == expected, f"Node not reachable: {message}"


def test_copy_file_to_remote() -> None:
    """
    Test copying a local file to a remote machine using SCP.
    """
    code, _, err = copy_file_to_remote(DEST_USER, DEST_PASS, DEST_IP, LOCAL_FILE, REMOTE_PATH)
    assert code == 0, f"File copy failed: {err}"


def test_run_valid_remote_command() -> None:
    """
    Test executing a valid shell command on the remote machine.
    """
    code, out, err = run_remote_command(DEST_USER, DEST_PASS, DEST_IP, VALID_COMMAND)
    assert code == 0, f"Unexpected error: {err}"
    assert out == "hello", f"Unexpected output: {out}"
    assert err == "", f"Unexpected stderr: {err}"


def test_run_invalid_remote_command() -> None:
    """
    Test executing an invalid command on the remote machine.
    """
    code, _, err = run_remote_command(DEST_USER, DEST_PASS, DEST_IP, INVALID_COMMAND)
    assert code != 0, "Expected failure on invalid command"
    assert "not found" in err or "command" in err.lower(), f"Unexpected error message: {err}"

