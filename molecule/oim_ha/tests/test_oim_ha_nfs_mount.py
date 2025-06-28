import pytest

container_name = "omnia_core"

@pytest.mark.qtest_id("TC-3696")
def test_nfs_mount(run_sshpass_command, get_oim_ha_nodes, get_oim_shared_path):
    """
    Test that the shared path exists on all OIM_HA nodes from cluster layout
    """
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
