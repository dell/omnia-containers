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

@pytest.mark.qtest_id("TC-3693")
def test_virtual_ips_configured_on_active_node(get_virtual_ips, get_system_ips, run_sshpass_command, check_if_oim_ha_is_enabled):
    """
    Test that the virtual IPs are properly configured on the OIM active node
    """
    check_if_oim_ha_is_enabled(run_sshpass_command)
    # Get virtual IPs from config
    cmd = f"podman exec {container_name} cat /opt/omnia/input/project_default/high_availability_config.yml"
    result = run_sshpass_command(cmd)
    admin_ip, bmc_ip = get_virtual_ips(result)

    # Get system IPs from OIM HA node
    cmd = "hostname -I"
    result = run_sshpass_command(cmd)
    system_ips = get_system_ips(result)

    # Verify virtual IPs are present
    admin_status = admin_ip in system_ips
    bmc_status = bmc_ip in system_ips

    print("\nVirtual IP Status on active node")
    print(f"Admin IP: {'Configured' if admin_status else 'Not Configured'}")
    print(f"BMC IP: {'Configured' if bmc_status else 'Not Configured'}")

    assert admin_status, "Admin virtual IP is not configured"
    assert bmc_status, "BMC virtual IP is not configured"
