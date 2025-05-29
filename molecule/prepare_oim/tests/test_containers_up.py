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
        
def test_required_containers_running(get_required_containers, run_sshpass_command):
    """
    Checks that all required containers are present and running in podman.
    """
    required_containers = get_required_containers

    cmd = "podman ps --all --format '{{.Names}}: {{.Status}}'"
    result = run_sshpass_command(cmd)

    assert result.returncode == 0, f"\n❌ SSH command failed: {result.stderr}"

    containers_not_running = []
    containers_missing = []
    containers_running = []

    for container in required_containers:
        found = False
        for line in result.stdout.splitlines():
            if ": " not in line:
                continue
            name, status = line.split(": ", 1)
            if container in name:
                found = True
                if "Up" not in status:
                    containers_not_running.append(f"{container}: {status}")
                else:
                    containers_running.append(f"{container}: {status}")
                break
        if not found:
            containers_missing.append(container)

    assert not containers_missing, (
        f"\n❌ The following required containers are missing:\n" + "\n".join(containers_missing)
    )
    assert not containers_not_running, (
        f"\n❌ The following required containers are not running:\n" + "\n".join(containers_not_running)
    )

    print(f"\n✅ The following required containers are running:\n" + "\n".join(containers_running))

    
def test_pcs_resources_running(get_required_pcs_resources, run_sshpass_command):
    # List of expected resource names and their group
    expected_resources = get_required_pcs_resources
    
    cmd = f"podman exec -it omnia_pcs pcs resource"
    
    result = run_sshpass_command(cmd)
    
    assert result.returncode == 0, f"SSH command failed: {result.stderr}"

    pcs_output = result.stdout

    # Verify each resource is listed and in 'Started' state
    missing = []
    not_started = []
    
    print(pcs_output)
    for res in expected_resources:
        lines = [line.strip() for line in pcs_output.splitlines() if res in line]
        if not lines:
            missing.append(res)
            continue
        if not any("Started" in line for line in lines):
            not_started.append(res)

    assert not missing, f"Missing resources in PCS status: {missing}"
    assert not not_started, f"Resources not started: {not_started}"

    print("\n✅ All PCS resources are present and started.")


def test_pulp_status(run_sshpass_command):
    
    cmd = f"podman exec -it omnia_core pulp status"
    
    result = run_sshpass_command(cmd)
    assert result.returncode == 0, f"\npulp status is disabled.\nError:\n{result.stderr}"
    print("\npulp status is active")
