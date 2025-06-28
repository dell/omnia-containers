import pytest
import yaml

container_name = "omnia_core"

def get_system_ips(run_sshpass_command):
    """Get all IP addresses from a remote system"""
    try:
        cmd = f"hostname -I"
        result = run_sshpass_command(cmd)
        if result.returncode == 0:
            return [ip.strip() for ip in result.stdout.split()]
        return []
    except Exception as e:
        pytest.fail(f"Error getting system IPs: {e}")

def get_virtual_ips(run_sshpass_command):
    """Read virtual IPs from configuration file"""
    try:
        cmd = f"podman exec {container_name} cat /opt/omnia/input/project_default/high_availability_config.yml"
        result = run_sshpass_command(cmd)
        if result.returncode != 0:
            pytest.fail(f"Failed to fetch project default configuration: {result.stderr}")
        config = yaml.safe_load(result.stdout)
        return (
                config['oim_ha']['admin_virtual_ip_address'],
                config['oim_ha']['bmc_virtual_ip_address']
            )
    except Exception as e:
        pytest.fail(f"Error reading configuration: {e}")

@pytest.mark.qtest_id("TC-3693")
def test_virtual_ips_configured(run_sshpass_command):
    """
    Test that the virtual IPs are properly configured on the OIM node
    """
    # Get virtual IPs from config
    admin_ip, bmc_ip = get_virtual_ips(run_sshpass_command)
    
    # Get system IPs from OIM node
    system_ips = get_system_ips(run_sshpass_command)
    
    # Verify virtual IPs are present
    admin_status = admin_ip in system_ips
    bmc_status = bmc_ip in system_ips
    
    print(f"\nVirtual IP Status:")
    print(f"Admin IP: {'Configured' if admin_status else 'NOT Configured'}")
    print(f"BMC IP: {'Configured' if bmc_status else 'NOT Configured'}")
    
    assert admin_status, print("Admin virtual IP is not configured")
    assert bmc_status, print("BMC virtual IP is not configured")
