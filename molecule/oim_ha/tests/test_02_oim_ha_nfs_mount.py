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

@pytest.mark.qtest_id("TC-3696")
def test_nfs_mount(run_sshpass_command, get_oim_ha_nodes, get_oim_shared_path, check_if_oim_ha_is_enabled):
    """
    Test that the shared path exists on all OIM_HA nodes from cluster layout
    """
    check_if_oim_ha_is_enabled(run_sshpass_command)
    # Get shared path from OIM metadata
    shared_path = get_oim_shared_path(run_sshpass_command)
    
    # Get OIM_HA nodes from cluster layout
    oim_ha_nodes = get_oim_ha_nodes(run_sshpass_command)
    
    try:
        if not oim_ha_nodes:
            pytest.fail("No OIM_HA nodes found in cluster layout")
        
        for node in oim_ha_nodes:
            hostname = node.split('.')[0]
            print(f"\nChecking nfs mount on {hostname} node:")
            cmd = f"podman exec omnia_core ssh -o StrictHostKeyChecking=no {hostname} cd {shared_path}"
            result = run_sshpass_command(cmd)
            
            if result.returncode != 0:
                pytest.fail(print(f"NFS mount {shared_path} does not exist on node {hostname}"))
            
            print(f"Shared path {shared_path} exists on node {hostname}")
        
        print("\nShared path exists on all OIM_HA nodes!")
    
    except Exception as e:
        pytest.fail(f"Error processing cluster layout: {str(e)}")
