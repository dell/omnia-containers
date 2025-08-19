# test_remote_operations.py
import pytest
from remote_utils import copy_file_to_remote, run_remote_command, check_node_reachability

"""
Test suite for remote operations:
- Node reachability via ping
- File copy to remote host via SCP
- Remote command execution (valid and invalid)

Tests assume password-based SSH access using sshpass.
Make sure DEST_USER, DEST_PASS, DEST_IP, LOCAL_FILE, and REMOTE_PATH are defined.
"""
VALID_COMMAND = "echo hello"
INVALID_COMMAND = "someinvalidcommand1234"

@pytest.mark.parametrize("ip, expected", [(DEST_IP, True)])
def test_node_reachability(ip, expected):
     """
    Test whether a node is reachable using ping.
    
    Args:
        ip (str): IP address of the target node.
        expected (bool): Expected reachability result.
    """
    reachable, message = check_node_reachability(ip)
    assert reachable == expected, f"Node not reachable: {message}"

def test_copy_file_to_remote():
     """
    Test copying a local file to a remote machine using SCP.
    
    Asserts that the return code is 0 and file transfer succeeded.
    """
    code, out, err = copy_file_to_remote(DEST_USER, DEST_PASS, DEST_IP, LOCAL_FILE, REMOTE_PATH)
    assert code == 0, f"File copy failed: {err}"

def test_run_valid_remote_command():
    """
    Test executing a valid shell command on the remote machine.

    Asserts that the output is correct and there are no errors.
    """
    code, out, err = run_remote_command(DEST_USER, DEST_PASS, DEST_IP, VALID_COMMAND)
    assert code == 0
    assert out == "hello"
    assert err == ""

def test_run_invalid_remote_command():
     """
    Test executing an invalid command on the remote machine.

    Asserts that an error occurs and the error message is meaningful.
    """
    code, out, err = run_remote_command(DEST_USER, DEST_PASS, DEST_IP, INVALID_COMMAND)
    assert code != 0
    assert "not found" in err or "command" in err.lower()
