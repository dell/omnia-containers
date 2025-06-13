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
import subprocess
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import config

oim_ip = config.OIM_IP
oim_password = config.OIM_PASS

# Shared constants
remote_user = "root"
container_name = "omnia_core"

@pytest.fixture
def service_nodes(run_sshpass_command):
    cmd = f"podman exec {container_name} cat /opt/omnia/omnia_inventory/cluster_layout"
    result = run_sshpass_command(cmd)

    assert result.returncode == 0, f"Failed to fetch cluster layout details: {result.stderr}"

    service_nodes = []
    collect = False
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            collect = (line == "[service_node]")
            continue
        if collect and line:
            service_nodes.append(line)

    if not service_nodes:
        pytest.fail("No service nodes found.")
    
    print("\nService nodes: ", service_nodes)
    return service_nodes

def test_validate_xcat_installed_on_service_nodes(run_sshpass_command, service_nodes):
    print("\nVerifying xCAT installation on service nodes")
    failed_nodes = []

    for node in service_nodes:
        hostname = node.split('.')[0]
        ssh_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {hostname} lsxcatd -v'"
        )
        ssh_result = run_sshpass_command(ssh_cmd)
        if ssh_result.returncode != 0:
            failed_nodes.append(hostname)
        else:
            print(f"xCAT is installed on node: {hostname}")

    if failed_nodes:
        pytest.fail(print(f"xCAT not installed on: {failed_nodes}"))

def test_validate_xcatd_status_on_service_nodes(run_sshpass_command, service_nodes):
    print("\nVerifying xcatd service status on service nodes")
    failed_nodes = []

    for node in service_nodes:
        hostname = node.split('.')[0]
        ssh_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {hostname} systemctl is-active xcatd'"
        )
        ssh_result = run_sshpass_command(ssh_cmd)
        if ssh_result.returncode != 0 or ssh_result.stdout.strip() != "active":
            failed_nodes.append(hostname)
        else:
            print(f"xcatd is active on node: {hostname}")

    if failed_nodes:
        pytest.fail(print(f"xcatd inactive or failed on: {failed_nodes}"))

def test_tabdump_functionality_on_service_nodes(run_sshpass_command, service_nodes):

    print("\nVerifying tabdump functionality on service nodes")
    failed_nodes = []

    tabdump_tables = ["site", "nodetype", "nodelist", "networks"]

    for node in service_nodes:
        hostname = node.split('.')[0]
        for table in tabdump_tables:
            ssh_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
                f"{hostname} tabdump {table}'"
            )
            ssh_result = run_sshpass_command(ssh_cmd)

            if ssh_result.returncode != 0:
                failed_nodes.append(f"{hostname}: tabdump {table}")

    if failed_nodes:
        print("\nSome tabdump commands failed:")
        for failure in failed_nodes:
            print(f" - {failure}")
        pytest.fail("xCAT tabdump failed on some nodes.")
    else:
        print("\nxCAT tabdump is functional on all service nodes.")

def test_omnia_pcs_container_in_service_nodes(run_sshpass_command, service_nodes):
    failed_nodes = []

    for node in service_nodes:
        hostname = node.split('.')[0]
        ssh_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
            f"{hostname} podman ps --filter name=omnia_pcs --format \"{{{{.Status}}}}\"'"
        )
        ssh_result = run_sshpass_command(ssh_cmd)
        status = ssh_result.stdout.strip()

        if ssh_result.returncode == 0 and status.startswith("Up"):
            print(f"omnia_pcs container is running on node: {hostname}")
        else:
            failed_nodes.append(hostname)

    if failed_nodes:
        pytest.fail(print(f"omnia_pcs container is inactive or not found on nodes: {failed_nodes}"))


