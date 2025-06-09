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

import subprocess
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config

oim_ip = config.OIM_IP
oim_password = config.OIM_PASS

required_containers = ["omnia_core"]

def run_sshpass_command(cmd):
    ssh_cmd = [
        "sshpass", "-p", oim_password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"root@{oim_ip}", cmd
    ]
    return subprocess.run(ssh_cmd, capture_output=True, text=True)

def test_omnia_core_container_is_up():
    print("\nChecking required containers...\n")

    cmd = "podman ps --all --format '{{.Names}}: {{.Status}}'"
    result = run_sshpass_command(cmd)

    assert result.returncode == 0, f"\nSSH command failed:\n{result.stderr}"

    output = result.stdout.strip().splitlines()
    status_map = {line.split(": ")[0]: line.split(": ")[1] for line in output if ": " in line}

    missing = []
    not_running = []
    running = []

    for container in required_containers:
        if container not in status_map:
            missing.append(container)
        elif "Up" not in status_map[container]:
            not_running.append(f"{container}: {status_map[container]}")
        else:
            running.append(f"{container}: {status_map[container]}")

    assert not missing, print(f"\nMissing containers:\n" + "\n".join(missing))
    assert not not_running, print(f"\nContainers not running:\n" + "\n".join(not_running))

    print("\nAll required containers are running:\n" + "\n".join(running))
        
def test_ssh_to_omnia_core_container():

    # Check if the container is running and can respond to a command
    ssh_command = [
        "sshpass", "-p", oim_password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"root@{oim_ip}",
        "podman exec omnia_core echo CONTAINER_ACCESS_SUCCESS"
    ]

    try:
        result = subprocess.run(ssh_command, capture_output=True, text=True)
        assert result.returncode == 0, print(f"\nFailed to exec into omnia_core: {result.stderr}")
        assert "CONTAINER_ACCESS_SUCCESS" in result.stdout, print("\nContainer did not return expected output.")
        print("\nSuccessfully accessed omnia_core container.")
    except Exception as e:
        pytest.fail(f"Error accessing omnia_core container: {e}")
