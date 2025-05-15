import subprocess
import pytest
import sys
import os
import json

# Add project root to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
import config

# Configuration
oim_ip = config.OIM_IP
password = config.OIM_PASS
CONTAINER_NAME = "omnia_provision"

def run_sshpass_command(cmd):
    """
    SSH into the remote host and execute 'podman exec' to get the software_config.json file.
    """
    remote_cmd = cmd
    
    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
        f"root@{oim_ip}", remote_cmd
    ]

    result = subprocess.run(ssh_command, capture_output=True, text=True)
    return result

def test_xcatd_installation():
    """
    SSH into the remote host and execute 'podman exec' to run lsxcatd -v inside the container.
    """
    cmd = f"podman exec -it {CONTAINER_NAME} lsxcatd -v"
    
    result = run_sshpass_command(cmd)
    assert result.returncode == 0, f"\nxcat is not installed. \nError:\n{result.stderr}"
    print("\nxcat is installed!")
        
def test_xcatd_services():
    """
    SSH into the remote host and execute 'podman exec' to run lsxcatd -v inside the container.
    """
    cmd = f"podman exec -it {CONTAINER_NAME} lsxcatd -a"
    
    result = run_sshpass_command(cmd)
    assert result.returncode == 0, f"\nxcatd services are not running.\nError:\n{result.stderr}"
    print("\nxcatd services are running")

def test_xcatd_status():

    cmd = f"podman exec -it {CONTAINER_NAME} systemctl is-active xcatd"
    
    xcat_status = run_sshpass_command(cmd).stdout
    print("\nxcat status: ",xcat_status)
    assert xcat_status == "active\n", f"Expected xcat to be active, but got {xcat_status}"

def test_xcat_perl_modules():
    
    tabdump = ["site", "nodetype", "nodelist", "networks"]
    cmd_failed = []
    
    for i in tabdump:
        cmd = f"podman exec -it {CONTAINER_NAME} tabdump {i}"
        result = run_sshpass_command(cmd)
        if result.returncode != 0:
            cmd_failed.append(cmd)
    if cmd_failed:
        print( f"xcat db and perl environment are not functional. \nError:\n{result.stderr}")
    else:
        print("\nxcat db and perl environment are functional")
  
