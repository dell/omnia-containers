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

@pytest.mark.qtest_id("TC-3703")
def test_oim_ha_reboot_passwordless_ssh_compute_nodes(get_compute_nodes, run_sshpass_command, check_if_oim_ha_is_enabled):

    check_if_oim_ha_is_enabled(run_sshpass_command, use_ha=True)

    print("\nVerifying passwordless SSH to compute nodes\n")
    compute_nodes = get_compute_nodes(run_sshpass_command, use_ha=True)
    print(f"Checking compute nodes: {compute_nodes}")

    failed_nodes = []
    for node in compute_nodes:
        cmd = f"podman exec omnia_core ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node} hostname -s"
        result = run_sshpass_command(cmd, use_ha=True)
        if result.returncode != 0:
            failed_nodes.append(node)
            print(f"\nFailed SSH to compute node {node}: {result.stderr.strip()}")
        else:
            print(f"\nSSH to compute node {node}: {result.stdout.strip()}")

    if failed_nodes:
        pytest.fail(f"\nPasswordless SSH check failed for compute nodes: {failed_nodes}")
    else:
        print("\nPasswordless SSH to all compute nodes successful!")

@pytest.mark.qtest_id("TC-3704")
def test_oim_ha_reboot_passwordless_ssh_omnia_core(run_sshpass_command, check_if_oim_ha_is_enabled):

    check_if_oim_ha_is_enabled(run_sshpass_command, use_ha=True)
    
    print("\nVerifying passwordless SSH to omnia_core\n")
    ssh_command = "ssh -o StrictHostKeyChecking=no omnia_core uname -n"
    result = run_sshpass_command(ssh_command, use_ha=True)
    assert result.returncode == 0, print(f"\nFailed to verify passwordless SSH to omnia_core: {result.stderr}")
    print(f"\nPasswordless SSH to omnia_core: {result.stdout.strip()}\n")
