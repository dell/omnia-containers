# remote_utils.py

import subprocess
"""
This module provides utility functions to perform remote operations via SSH and SCP.
It includes functionality to:
- Copy files to a remote machine using `scp` with password authentication.
- Run commands on a remote machine over SSH.
- Check if a remote node is reachable using `ping`.

Note: This script uses `sshpass`, which exposes passwords on the command line.
It's intended for quick automation tasks in trusted environments only.
"""

def copy_file_to_remote(user, password, ip, local_path, remote_path):
      """
    Copy a file from the local machine to a remote machine using SCP.

    Args:
        user (str): Username for SSH login.
        password (str): Password for SSH login (used by sshpass).
        ip (str): IP address of the remote host.
        local_path (str): Path to the local file.
        remote_path (str): Destination path on the remote host.

    Returns:
        tuple: (return_code, stdout, stderr)
            return_code (int): 0 if successful, -1 if an error occurred.
            stdout (str): Standard output from the command.
            stderr (str): Standard error from the command or exception message.
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
        return -1, "", "File copy timed out"
    except Exception as e:
        return -1, "", str(e)

def run_remote_command(user, password, ip, cmd):
        """
    Run a shell command on a remote machine via SSH.

    Args:
        user (str): Username for SSH login.
        password (str): Password for SSH login (used by sshpass).
        ip (str): IP address of the remote host.
        cmd (str): Shell command to execute on the remote host.

    Returns:
        tuple: (return_code, stdout, stderr)
            return_code (int): 0 if successful, -1 if an error occurred.
            stdout (str): Output from the command.
            stderr (str): Error output or exception message.
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
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def check_node_reachability(ip, count=3, timeout=5):
     """
    Check if a node (IP address) is reachable using the ping command.

    Args:
        ip (str): IP address of the node to check.
        count (int): Number of ping packets to send (default is 3).
        timeout (int): Timeout in seconds for each ping packet (default is 5).

    Returns:
        tuple: (reachable, output)
            reachable (bool): True if the node is reachable, False otherwise.
            output (str): The ping output or error message.
    """
    ping_command = ["ping", "-c", str(count), "-W", str(timeout), ip]

    try:
        result = subprocess.run(
            ping_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return False, str(e)
