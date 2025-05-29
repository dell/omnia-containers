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

import pytest

CONTAINER_NAME = "omnia_provision"

def test_xcatd_installation(run_sshpass_command):
    """
    SSH into the remote host and execute 'podman exec' to run lsxcatd -v inside the container.
    """
    cmd = f"podman exec -it {CONTAINER_NAME} lsxcatd -v"
    
    result = run_sshpass_command(cmd)
    assert result.returncode == 0, f"\nxcat is not installed. \nError:\n{result.stderr}"
    print("\nxcat is installed!")
        
def test_xcatd_services(run_sshpass_command):
    """
    SSH into the remote host and execute 'podman exec' to run lsxcatd -v inside the container.
    """
    cmd = f"podman exec -it {CONTAINER_NAME} lsxcatd -a"
    
    result = run_sshpass_command(cmd)
    assert result.returncode == 0, f"\nxcatd services are not running.\nError:\n{result.stderr}"
    print("\nxcatd services are running")

def test_xcatd_status(run_sshpass_command):

    cmd = f"podman exec -it {CONTAINER_NAME} systemctl is-active xcatd"
    
    xcat_status = run_sshpass_command(cmd).stdout
    print("\nxcat status: ",xcat_status)
    assert xcat_status == "active\n", f"Expected xcat to be active, but got {xcat_status}"

def test_xcat_perl_modules(run_sshpass_command):
    
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
  
