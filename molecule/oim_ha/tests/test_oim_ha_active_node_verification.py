import pytest

@pytest.mark.dependency(name="test_omnia_pcs_active_node")
def test_omnia_pcs_active_node(run_sshpass_command,check_if_oim_ha_is_enabled):
    print("\nVerifying omnia_pcs container status on active node")
    try:
        check_if_oim_ha_is_enabled(run_sshpass_command)
        cmd = f"podman ps --filter name=omnia_pcs --format '{{{{.Status}}}}'"
        result = run_sshpass_command(cmd)
        assert result.returncode == 0 and result.stdout.startswith("Up"), "omnia_pcs not running on active node"
        print(f"omnia_pcs container is running on active node with status: {result.stdout.strip()}")
    except Exception as e:
        pytest.fail(f"Error in test_omnia_pcs_active_node: {str(e)}")

@pytest.mark.dependency(name="test_pcs_resources_active_node", depends=["test_omnia_pcs_active_node"])
def test_pcs_resources_active_node(run_sshpass_command, get_required_pcs_resources_HA, check_pcs_resource_status, get_hostname):
    print("\nVerifying PCS resources on active node")
    try:
        resources = get_required_pcs_resources_HA(run_sshpass_command)
        print(f"Required PCS resources: {resources}")
        hostname = get_hostname(run_sshpass_command)
        print(f"Active node hostname: {hostname}")
        result = run_sshpass_command("podman exec -it omnia_pcs pcs resource")
        assert result.returncode == 0, f"PCS resource fetch failed: {result.stderr}"
        missing, not_started = check_pcs_resource_status(result.stdout, resources, hostname)
        assert not missing, f"Missing PCS resources: {missing}"
        assert not not_started, f"Resources not started on active node: {not_started}"
        print("All required PCS resources are present and started on active node")
    except Exception as e:
        pytest.fail(f"Error in test_pcs_resources_active_node: {str(e)}")

@pytest.mark.dependency(name="test_pcs_daemon_active_node", depends=["test_omnia_pcs_active_node"])
def test_pcs_daemon_active_node(run_sshpass_command, get_hostname):
    print("\nVerifying PCS daemon status on active node")
    try:
        hostname = get_hostname(run_sshpass_command)
        print(f"Checking PCS daemons on active node: {hostname}")
        cmd = "podman exec omnia_pcs pcs status"
        result = run_sshpass_command(cmd)
        assert result.returncode == 0, f"Failed to get PCS status on active node {hostname}: {result.stderr}"
        output = result.stdout.lower()
        assert "corosync: active/enabled" in output, f"corosync not active/enabled on {hostname}"
        assert "pacemaker: active/enabled" in output, f"pacemaker not active/enabled on {hostname}"
        print(f"Both corosync and pacemaker daemons are active on active node {hostname}")
    except Exception as e:
        pytest.fail(f"Error in test_pcs_daemon_active_node: {str(e)}")

@pytest.mark.dependency(name="test_online_node_list_active_node", depends=["test_omnia_pcs_active_node"])
def test_online_node_list_active_node(run_sshpass_command, parse_online_nodes, get_oim_ha_nodes, get_hostname):
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
    except Exception as e:
        pytest.fail(f"Error in test_online_node_list_active_node: {str(e)}")

# This is the master summary for TC-3698
@pytest.mark.qtest_id("TC-3698")
@pytest.mark.dependency(
    depends=[
        "test_omnia_pcs_active_node",
        "test_pcs_resources_active_node",
        "test_pcs_daemon_active_node",
        "test_online_node_list_active_node"
    ]
)
def test_tc_3698_summary():
    print("All TC-3698 checks passed")
