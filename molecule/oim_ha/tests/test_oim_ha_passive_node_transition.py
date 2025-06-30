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

container_name = "omnia_core"

@pytest.mark.qtest_id("TC-3701")
def test_virtual_ips_configured(get_virtual_ips, get_system_ips, run_sshpass_command):
    """
    Test that the virtual IPs are properly configured on the OIM passive node
    """
    # Get virtual IPs from config
    cmd = f"podman exec {container_name} cat /opt/omnia/input/project_default/high_availability_config.yml"
    result = run_sshpass_command(cmd, use_ha=True)
    admin_ip, bmc_ip = get_virtual_ips(result)

    # Get system IPs from OIM HA node
    cmd = "hostname -I"
    result = run_sshpass_command(cmd, use_ha=True)
    system_ips = get_system_ips(result)

    # Verify virtual IPs are present
    admin_status = admin_ip in system_ips
    bmc_status = bmc_ip in system_ips

    print("\nVirtual IP Status on passive node")
    print(f"Admin IP: {'Configured' if admin_status else 'Not Configured'}")
    print(f"BMC IP: {'Configured' if bmc_status else 'Not Configured'}")

    assert admin_status, "Admin virtual IP is not configured"
    assert bmc_status, "BMC virtual IP is not configured"
        
def test_required_containers_running(get_required_containers, run_sshpass_command):
    """
    Checks that all required containers are present and running in podman.
    """
    required_containers = get_required_containers(use_ha=True)

    cmd = "podman ps --all --format '{{.Names}}: {{.Status}}'"
    result = run_sshpass_command(cmd, use_ha=True)

    assert result.returncode == 0, f"\nSSH command failed: {result.stderr}"

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

    assert not containers_missing, print(
        f"\nThe following required containers are missing:\n" + "\n".join(containers_missing)
    )
    assert not containers_not_running, print(
        f"\nThe following required containers are not running:\n" + "\n".join(containers_not_running)
    )

    print(f"\nThe following required containers are running:\n" + "\n".join(containers_running))

    
def test_pcs_resources_running(get_required_pcs_resources, run_sshpass_command, get_hostname):
    """
    Verifies that all required PCS resources are:
    - Present in the pcs resource list
    - Started
    - Running on the expected node
    """
    expected_node = get_hostname(run_sshpass_command, use_ha=True)
    expected_resources = get_required_pcs_resources(use_ha=True)

    cmd = "podman exec -it omnia_pcs pcs resource"
    result = run_sshpass_command(cmd, use_ha=True)

    assert result.returncode == 0, f"SSH command failed: {result.stderr}"

    pcs_output = result.stdout

    missing_resources = []
    not_started_resources = []
    wrong_node_resources = []

    for res in expected_resources:
        lines = [line.strip() for line in pcs_output.splitlines() if res in line]
        
        if not lines:
            missing_resources.append(res)
            continue

        # Look for "Started <node>"
        started_line = next((line for line in lines if "Started" in line), None)
        if not started_line:
            not_started_resources.append(res)
            continue

        parts = started_line.split()
        node = parts[-1] if len(parts) >= 2 else None
        if node != expected_node:
            wrong_node_resources.append((res, node))

    if missing_resources:
        print(f"\nMissing resources from PCS output: {missing_resources}")
    if not_started_resources:
        print(f"\nResources found but not started: {not_started_resources}")
    if wrong_node_resources:
        print("\nResources running on the wrong node:")
        for res, node in wrong_node_resources:
            print(f"  Resource: {res}, Running on: {node}, Expected: {expected_node}")

    assert not missing_resources, print("Some PCS resources are missing")
    assert not not_started_resources, print("Some PCS resources are not started")
    assert not wrong_node_resources, print("Some PCS resources are not running on the expected node")

    print(f"\nAll PCS resources are present, started, and running on node: {expected_node}")


def test_pulp_status(run_sshpass_command):
    
    cmd = f"podman exec -it omnia_core pulp status"
    
    result = run_sshpass_command(cmd, use_ha=True)
    assert result.returncode == 0, print(f"\npulp status is disabled.\nError:\n{result.stderr}")
    print("\npulp status is active")
