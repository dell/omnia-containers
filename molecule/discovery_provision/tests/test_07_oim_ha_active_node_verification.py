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

def test_omnia_pcs_active_node_TC_3698(run_sshpass_command,check_if_oim_ha_is_enabled):
    check_if_oim_ha_is_enabled(run_sshpass_command)
    global omnia_pcs_active_node
    print("\nVerifying omnia_pcs container status on active node")
    try:
        cmd = f"podman ps --filter name=omnia_pcs --format '{{{{.Status}}}}'"
        result = run_sshpass_command(cmd)
        assert result.returncode == 0 and result.stdout.startswith("Up"), "omnia_pcs not running on active node"
        print(f"omnia_pcs container is running on active node with status: {result.stdout.strip()}")
        omnia_pcs_active_node = True
    except Exception as e:
        pytest.fail(f"Error in test_omnia_pcs_active_node: {str(e)}")

def test_pcs_resources_active_node_TC_3698(check_if_oim_ha_is_enabled, run_sshpass_command, get_required_pcs_resources, check_pcs_resource_status, get_hostname):
    check_if_oim_ha_is_enabled(run_sshpass_command)
    global omnia_pcs_resources_active_node
    print("\nVerifying PCS resources on active node")
    try:
        resources = get_required_pcs_resources(run_sshpass_command, include_vips=True)
        print(f"Required PCS resources: {resources}")
        hostname = get_hostname(run_sshpass_command)
        print(f"Active node hostname: {hostname}")
        result = run_sshpass_command("podman exec -it omnia_pcs pcs resource")
        assert result.returncode == 0, f"PCS resource fetch failed: {result.stderr}"
        missing, not_started = check_pcs_resource_status(result.stdout, resources, hostname)
        assert not missing, f"Missing PCS resources: {missing}"
        assert not not_started, f"Resources not started on active node: {not_started}"
        print("All required PCS resources are present and started on active node")
        omnia_pcs_resources_active_node = True
    except Exception as e:
        pytest.fail(f"Error in test_pcs_resources_active_node: {str(e)}")

# def test_pcs_daemon_active_node_TC_3698(run_sshpass_command, get_hostname, check_if_oim_ha_is_enabled):
#     check_if_oim_ha_is_enabled(run_sshpass_command)
#     global omnia_pcs_daemon_active_node
#     print("\nVerifying PCS daemon status on active node")
#     try:
#         hostname = get_hostname(run_sshpass_command)
#         print(f"Checking PCS daemons on active node: {hostname}")
#         cmd = "podman exec omnia_pcs pcs status"
#         result = run_sshpass_command(cmd)
#         assert result.returncode == 0, f"Failed to get PCS status on active node {hostname}: {result.stderr}"
#         output = result.stdout.lower()
#         assert "corosync: active/enabled" in output, f"corosync not active/enabled on {hostname}"
#         assert "pacemaker: active/enabled" in output, f"pacemaker not active/enabled on {hostname}"
#         print(f"Both corosync and pacemaker daemons are active on active node {hostname}")
#         omnia_pcs_daemon_active_node = True
#     except Exception as e:
#         pytest.fail(f"Error in test_pcs_daemon_active_node: {str(e)}")

def test_online_node_list_active_node_TC_3698(run_sshpass_command, parse_online_nodes, get_oim_ha_nodes, get_hostname, check_if_oim_ha_is_enabled):
    check_if_oim_ha_is_enabled(run_sshpass_command)
    global omnia_pcs_online_node_list_active_node
    print("\nVerifying online node status from active node")
    try:
        result = run_sshpass_command("podman exec omnia_pcs pcs status")
        assert result.returncode == 0, f"PCS status fetch failed: {result.stderr}"
        online_nodes = parse_online_nodes(result.stdout)
        expected_nodes = get_oim_ha_nodes(run_sshpass_command)
        active_node = get_hostname(run_sshpass_command)
        
        # Get all nodes including active node
        expected_nodes = list(set(expected_nodes + [active_node]))
        print(f"Expected nodes (including active node): {expected_nodes}")
        print(f"Online nodes: {online_nodes}")
        
        # Check if all expected nodes are in online nodes
        offline_nodes = [node for node in expected_nodes if node not in online_nodes]
        if offline_nodes:
            print(f"Offline nodes: {offline_nodes}")
            assert not offline_nodes, f"Not all expected nodes are online: {offline_nodes}"
        
        print("All expected nodes are online in the PCS cluster")
        omnia_pcs_online_node_list_active_node = True
    except Exception as e:
        pytest.fail(f"Error in test_online_node_list_active_node: {str(e)}")

# This is the master summary for TC-3698
@pytest.mark.qtest_id("TC-3698")
def test_oim_ha_active_node_verification(check_if_oim_ha_is_enabled, run_sshpass_command):
    if check_if_oim_ha_is_enabled(run_sshpass_command):
        if omnia_pcs_active_node and omnia_pcs_daemon_active_node and omnia_pcs_resources_active_node and omnia_pcs_online_node_list_active_node: 
            print("All TC-3698 checks Passed")
        else:
            pytest.fail("TC-3698 checks Failed")
    else:
        pytest.skip("OIM HA is not enabled")
