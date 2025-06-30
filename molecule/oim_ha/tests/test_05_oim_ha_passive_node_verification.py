import pytest

container_name = "omnia_core"
# omnia_pcs_passive_nodes = False
# omnia_pcs_daemon_passive_nodes = False
# omnia_pcs_resources_passive_nodes = False
# omnia_pcs_online_node_list_passive_nodes = False


@pytest.mark.dependency(name='test_omnia_pcs_passive_nodes')
def test_omnia_pcs_passive_nodes(run_sshpass_command, get_oim_ha_nodes, check_if_oim_ha_is_enabled):
    print("\nVerifying omnia_pcs container status on passive nodes")
    global omnia_pcs_passive_nodes
    try:
        check_if_oim_ha_is_enabled(run_sshpass_command)
        nodes = get_oim_ha_nodes(run_sshpass_command)
        print(f"Checking omnia_pcs containers on nodes: {nodes}")
        
        failed = []
        for node in nodes:
            print(f"\nChecking omnia_pcs on node: {node}")
            cmd = (
                f"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
                f"{node} podman ps --filter name=omnia_pcs --format '{{{{.Status}}}}'"
            )
            result = run_sshpass_command(cmd)
            if result.returncode != 0 or not result.stdout.startswith("Up"):
                failed.append(node)
            else:
                print(f"omnia_pcs is running on node {node} with status: {result.stdout.strip()}")
        
        if failed:
            print(f"Failed nodes: {failed}")
            assert not failed, f"omnia_pcs not running on nodes: {failed}"
        else:
            print("omnia_pcs container is running on all passive nodes")
            omnia_pcs_passive_nodes = True
    except Exception as e:
        pytest.fail(f"Error in test_omnia_pcs_passive_nodes: {str(e)}")

@pytest.mark.dependency(name='test_omnia_pcs_passive_nodes')
def test_pcs_daemon_passive_nodes(run_sshpass_command, get_oim_ha_nodes, check_pcs_daemon_status):
    print("\nVerifying PCS daemon status on passive nodes")
    global omnia_pcs_daemon_passive_nodes
    try:
        nodes = get_oim_ha_nodes(run_sshpass_command)
        print(f"Checking PCS daemons on nodes: {nodes}")
        
        failed = []
        for node in nodes:
            status, error = check_pcs_daemon_status(run_sshpass_command, node)
            if not status:
                failed.append(f"{node}: {error}")
        
        if failed:
            print(f"Failed nodes: {failed}")
            assert not failed, f"PCS daemons failed on nodes: {failed}"
        else:
            print("All passive nodes have active PCS daemons")
            omnia_pcs_daemon_passive_nodes = True
    except Exception as e:
        pytest.fail(f"Error in test_pcs_daemon_passive_nodes: {str(e)}")

@pytest.mark.dependency(name='test_omnia_pcs_passive_nodes')
def test_pcs_resources_passive_nodes(run_sshpass_command, get_required_pcs_resources, check_pcs_resource_status, get_hostname, get_oim_ha_nodes):
    print("\nVerifying PCS resources on passive nodes")
    global omnia_pcs_resources_passive_nodes
    try:
        nodes = get_oim_ha_nodes(run_sshpass_command)
        print(f"Checking PCS resources on nodes: {nodes}")
        
        active = get_hostname(run_sshpass_command)
        print(f"Active node: {active}")
        resources = get_required_pcs_resources(run_sshpass_command, include_vips=True)
        print(f"Required PCS resources: {resources}")
        
        for node in nodes:
            print(f"\nChecking PCS resources on node: {node}")
            cmd = (
                f"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
                f"{node} podman exec -it omnia_pcs pcs resource"
            )
            result = run_sshpass_command(cmd)
            assert result.returncode == 0, f"Failed on node {node}: {result.stderr}"
            missing, not_started = check_pcs_resource_status(result.stdout, resources, active)
            
            if missing:
                print(f"Missing resources on {node}: {missing}")
                assert not missing, f"Missing on {node}: {missing}"
            
            if not_started:
                print(f"Not started resources on {node}: {not_started}")
                assert not not_started, f"Not started on {node}: {not_started}"
            else:
                print(f"All required resources are present and started on node {node}")
                omnia_pcs_resources_passive_nodes = True
    except Exception as e:
        pytest.fail(f"Error in test_pcs_resources_passive_nodes: {str(e)}")

@pytest.mark.dependency(name='test_omnia_pcs_passive_nodes')
def test_online_node_list_passive_node(run_sshpass_command, parse_online_nodes, get_oim_ha_nodes, get_hostname):
    print("\nVerifying online node status from passive nodes")
    global omnia_pcs_online_node_list_passive_nodes
    try:
        oim_ha_nodes = get_oim_ha_nodes(run_sshpass_command)

        for node in oim_ha_nodes:
            print(f"\nChecking online status from node: {node}")
            cmd = (
                f"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
                f"{node} podman exec -it omnia_pcs pcs status"
            )
            result = run_sshpass_command(cmd)
            assert result.returncode == 0, f"Failed to get status on {node}: {result.stderr}"
            online_nodes = parse_online_nodes(result.stdout)

            active_node = get_hostname(run_sshpass_command)
            
            # Get all nodes including active node
            expected_nodes = list(set(oim_ha_nodes + [active_node]))
            print(f"Expected nodes (including active node): {expected_nodes}")
            print(f"Online nodes: {online_nodes}")
            
            # Check if all expected nodes are in online nodes
            offline_nodes = [node for node in expected_nodes if node not in online_nodes]
            if offline_nodes:
                print(f"Offline nodes: {offline_nodes}")
                assert not offline_nodes, f"Not all expected nodes are online: {offline_nodes}"
            
            print("All expected nodes are online in the PCS cluster")
            omnia_pcs_online_node_list_passive_nodes = True
    except Exception as e:
        pytest.fail(f"\nError checking PCS status: {str(e)}")

# This is the master summary for TC-3699
@pytest.mark.qtest_id("TC-3699")
def test_tc_3699_summary():
    if omnia_pcs_passive_nodes and omnia_pcs_daemon_passive_nodes and omnia_pcs_resources_passive_nodes and omnia_pcs_online_node_list_passive_nodes: 
        print("TC-3699 checks failed")
    else:
        pytest.fail("All TC-3699 checks passed")
