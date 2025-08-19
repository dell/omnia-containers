# test_remote_operations.py

import os
import pytest
from remote_utils import copy_file_to_remote, run_remote_command, check_node_reachability

# Replace with actual values or set as environment variables for secure testing
DEST_IP = os.getenv("DEST_IP", "100.98.83.155")
DEST_USER = os.getenv("DEST_USER", "root")
DEST_PASS = os.getenv("DEST_PASS", "dell")
LOCAL_FILE = "/root/example.txt"
REMOTE_PATH = "/root/prashanth/"

VALID_COMMAND = "echo hello"
INVALID_COMMAND = "someinvalidcommand1234"

@pytest.mark.parametrize("ip, expected", [(DEST_IP, True)])
def test_node_reachability(ip, expected):
    reachable, message = check_node_reachability(ip)
    assert reachable == expected, f"Node not reachable: {message}"

def test_copy_file_to_remote():
    code, out, err = copy_file_to_remote(DEST_USER, DEST_PASS, DEST_IP, LOCAL_FILE, REMOTE_PATH)
    assert code == 0, f"File copy failed: {err}"

def test_run_valid_remote_command():
    code, out, err = run_remote_command(DEST_USER, DEST_PASS, DEST_IP, VALID_COMMAND)
    assert code == 0
    assert out == "hello"
    assert err == ""

def test_run_invalid_remote_command():
    code, out, err = run_remote_command(DEST_USER, DEST_PASS, DEST_IP, INVALID_COMMAND)
    assert code != 0
    assert "not found" in err or "command" in err.lower()
