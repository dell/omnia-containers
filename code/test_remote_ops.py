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

"""
Test suite for remote SSH utilities:
- Node reachability
- File transfer via SCP
- Remote command execution (valid and invalid)
"""

import pytest
from vars import DEST_USER, DEST_PASS, DEST_IP, LOCAL_FILE, REMOTE_PATH
from remote_utils import copy_file_to_remote, run_remote_command, check_node_reachability

VALID_COMMAND = "echo hello"
INVALID_COMMAND = "someinvalidcommand1234"


@pytest.mark.parametrize("ip, expected", [(DEST_IP, True)])
def test_node_reachability(ip: str, expected: bool) -> None:
    """
    Ensure the node is reachable via ping.
    """
    reachable, message = check_node_reachability(ip)
    assert reachable == expected, f"Ping failed: {message}"


def test_copy_file_to_remote() -> None:
    """
    Verify file copy to remote host using SCP.
    """
    code, out, err = copy_file_to_remote(DEST_USER, DEST_PASS, DEST_IP, LOCAL_FILE, REMOTE_PATH)
    assert code == 0, f"SCP failed: {err or out}"


def test_run_valid_remote_command() -> None:
    """
    Test running a valid remote command.
    """
    code, out, err = run_remote_command(DEST_USER, DEST_PASS, DEST_IP, VALID_COMMAND)
    assert code == 0, f"Command failed: {err}"
    assert out == "hello", f"Unexpected output: {out}"
    assert err == "", f"Unexpected stderr: {err}"


def test_run_invalid_remote_command() -> None:
    """
    Ensure invalid command triggers an error remotely.
    """
    code, _, err = run_remote_command(DEST_USER, DEST_PASS, DEST_IP, INVALID_COMMAND)
    assert code != 0, "Expected failure on invalid command."
    assert "not found" in err or "command" in err.lower(), f"Unexpected error message: {err}"
