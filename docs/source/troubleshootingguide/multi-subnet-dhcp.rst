.. _troubleshooting-multi-subnet-dhcp:

Troubleshooting Multi-Subnet DHCP
=================================

Diagnose and resolve common issues with multi-subnet DHCP deployments. This guide covers DHCP relay problems, subnet configuration issues, IP assignment errors, network connectivity problems, and CoreDHCP service failures.

Common Issues and Symptoms
---------------------------

| Issue | Symptoms | Likely Cause |
|-------|----------|--------------|
| DHCP requests not reaching CoreDHCP | Nodes fail to obtain IP addresses, no DHCP requests in CoreDHCP logs | DHCP relay not configured, routing misconfiguration, firewall blocking DHCP traffic |
| Nodes receiving wrong IP addresses | Node in Rack 2 receives IP from Rack 1 subnet pool | giaddr not set correctly, subnet misconfiguration, DHCP relay misconfiguration |
| Subnet overlap conflicts | Validation fails with subnet overlap error | Overlapping CIDR ranges in network_spec.yml |
| VLAN misconfiguration | Nodes cannot communicate on VLAN, DHCP requests not forwarded | VLAN ID mismatch, trunk configuration errors |
| Gateway unreachable | Nodes cannot route traffic, DHCP option 3 incorrect | Wrong gateway IP in router parameter, routing not configured |
| DHCP pool exhaustion | Nodes cannot obtain IPs, pool at 100% utilization | Insufficient pool size, stale leases, IP conflicts |
| CoreDHCP service failure | CoreDHCP container not running, service crashes | Configuration errors, resource exhaustion, dependency failures |

Diagnostic Procedures
---------------------

Check CoreDHCP Service Status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify that CoreDHCP is running and healthy:

1. Check CoreDHCP container status.

   .. code-block:: bash

      podman ps -a | grep coredhcp

   Expected output: Container should be in "Up" status.

2. Check CoreDHCP service logs for errors.

   .. code-block:: bash

      podman logs coredhcp --tail 50

   Look for:
   - Subnet registration errors
   - Plugin loading failures
   - Configuration parsing errors

3. Verify CoreDHCP version supports multi-subnet.

   .. code-block:: bash

      podman exec coredhcp coredhcp --version

   Ensure coresmd v0.5+ is installed for multi-subnet support.

Check DHCP Relay Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify that DHCP relay is configured on ToR switches:

1. Check DHCP relay helper-address on ToR switch.

   .. code-block:: text

      show ip helper-address
      show running-config interface vlan <vlan-id>

   Expected: Helper-address pointing to CoreDHCP server IP (OIM admin IP).

2. Verify DHCP relay is enabled globally.

   .. code-block:: text

      show running-config | include ip dhcp relay

   Expected: ``ip dhcp relay`` should be present.

3. Test DHCP relay connectivity from ToR switch.

   .. code-block:: text

      ping <coredhcp-server-ip>

   Expected: Successful ping responses.

Check Network Connectivity
~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify routing between OIM and rack subnets:

1. Check routing table on OIM.

   .. code-block:: bash

      ip route show

   Expected: Routes to all rack subnets should be present.

2. Test connectivity to rack gateways.

   .. code-block:: bash

      ping -c 3 10.40.1.1
      ping -c 3 10.40.3.1

   Expected: Successful ping responses to all gateway IPs.

3. Test connectivity from rack subnet to CoreDHCP server.

   .. code-block:: text

      # On a node in the rack subnet
      ping <coredhcp-server-ip>

   Expected: Successful ping responses.

Check Subnet Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify subnet configuration in ``network_spec.yml``:

1. View the current configuration.

   .. code-block:: bash

      cat /opt/omnia/input/network_spec.yml

2. Validate the configuration.

   .. code-block:: bash

      cd /opt/omnia
      ansible-playbook validate_network_spec.yml

3. Check for common configuration errors:
   - Subnet CIDR overlaps
   - Dynamic range outside subnet boundaries
   - Gateway IP not in subnet
   - Netmask bits mismatch

DHCP Relay Issues
-----------------

DHCP Requests Not Reaching CoreDHCP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**
- Nodes fail to obtain IP addresses
- No DHCP requests visible in CoreDHCP logs
- Nodes timeout during PXE boot

**Diagnostic Steps**

1. Check CoreDHCP logs for any DHCP requests.

   .. code-block:: bash

      podman logs -f coredhcp

2. If no requests appear, check DHCP relay on ToR switch.

   .. code-block:: text

      show running-config interface vlan <vlan-id>
      show ip helper-address

3. Verify routing between ToR switch and CoreDHCP server.

   .. code-block:: text

      ping <coredhcp-server-ip>

4. Check firewall rules on intermediate devices.

   .. code-block:: text

      show access-lists
      show firewall

**Resolution**

1. Configure DHCP relay helper-address on ToR switch.

   .. code-block:: text

      interface Vlan1101
        ip helper-address 172.16.107.254
        exit

2. Ensure routing is configured between ToR switch and CoreDHCP server.

   .. code-block:: text

      ip route add 172.16.0.0/16 via <next-hop>

3. Verify firewall allows DHCP traffic (UDP ports 67, 68).

   .. code-block:: text

      access-list 101 permit udp any eq bootpc any eq bootps
      access-list 101 permit udp any eq bootps any eq bootpc

4. Restart DHCP relay service if needed.

   .. code-block:: text

      no ip dhcp relay
      ip dhcp relay

**Verification**

Boot a node in the affected subnet and observe DHCP requests in CoreDHCP logs.

giaddr Not Set Correctly
~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**
- Nodes receive IP addresses from wrong subnet pool
- CoreDHCP logs show giaddr as 0.0.0.0 or incorrect value
- IP assignment not matching expected subnet

**Diagnostic Steps**

1. Check CoreDHCP logs for giaddr values.

   .. code-block:: bash

      podman logs coredhcp | grep giaddr

2. Verify DHCP relay configuration on ToR switch.

   .. code-block:: text

      show running-config interface vlan <vlan-id>

3. Check that helper-address points to correct CoreDHCP server IP.

**Resolution**

1. Verify router parameter in ``network_spec.yml`` matches ToR SVI IP.

   .. code-block:: yaml

      additional_subnets:
        - subnet: "10.40.1.0"
          netmask_bits: "24"
          router: "10.40.1.1"  # Must match ToR SVI IP
          dynamic_range: "10.40.1.100-10.40.1.200"

2. Redeploy CoreDHCP configuration.

   .. code-block:: bash

      cd /opt/omnia
      ansible-playbook deploy_openchami.yml

3. Restart DHCP relay on ToR switch.

   .. code-block:: text

      no ip dhcp relay
      ip dhcp relay

**Verification**

Boot a node and verify it receives IP from correct subnet pool. Check CoreDHCP logs for correct giaddr.

Subnet Configuration Issues
--------------------------

Subnet Overlap Conflicts
~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**
- Validation fails with "subnet overlap detected"
- Nodes receive conflicting IP assignments
- Routing errors or unreachable subnets

**Diagnostic Steps**

1. Run validation playbook.

   .. code-block:: bash

      cd /opt/omnia
      ansible-playbook validate_network_spec.yml

2. Manually check subnet CIDR calculations.

3. Verify no overlapping ranges in ``network_spec.yml``.

**Resolution**

1. Identify overlapping subnets.

   .. code-block:: text

      Example overlap:
      Subnet 1: 10.40.1.0/24 (10.40.1.0 - 10.40.1.255)
      Subnet 2: 10.40.1.128/25 (10.40.1.128 - 10.40.1.255)  # OVERLAP

2. Correct subnet allocations to use non-overlapping CIDRs.

   .. code-block:: yaml

      # Correct configuration
      additional_subnets:
        - subnet: "10.40.1.0/24"
          netmask_bits: "24"
          router: "10.40.1.1"
          dynamic_range: "10.40.1.100-10.40.1.200"
        - subnet: "10.40.3.0/24"
          netmask_bits: "24"
          router: "10.40.3.1"
          dynamic_range: "10.40.3.100-10.40.3.200"

3. Re-validate configuration.

   .. code-block:: bash

      ansible-playbook validate_network_spec.yml

**Verification**

Validation should pass without errors. Redeploy CoreDHCP configuration.

Dynamic Range Outside Subnet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**
- Validation fails with "dynamic range not within subnet"
- DHCP pool includes addresses outside subnet boundaries

**Diagnostic Steps**

1. Run validation playbook.

   .. code-block:: bash

      ansible-playbook validate_network_spec.yml

2. Manually verify dynamic range is within subnet.

   .. code-block:: text

      Example error:
      Subnet: 10.40.1.0/24 (valid range: 10.40.1.1 - 10.40.1.254)
      Dynamic range: 10.40.1.100-10.40.3.200  # EXCEEDS SUBNET

**Resolution**

1. Correct dynamic range to stay within subnet boundaries.

   .. code-block:: yaml

      # Correct configuration
      additional_subnets:
        - subnet: "10.40.1.0/24"
          netmask_bits: "24"
          router: "10.40.1.1"
          dynamic_range: "10.40.1.100-10.40.1.200"  # Within subnet

2. Re-validate configuration.

   .. code-block:: bash

      ansible-playbook validate_network_spec.yml

**Verification**

Validation should pass. Redeploy CoreDHCP configuration.

VLAN Misconfiguration
~~~~~~~~~~~~~~~~~~~~

**Symptoms**
- Nodes cannot communicate on VLAN
- DHCP requests not forwarded
- Intermittent connectivity

**Diagnostic Steps**

1. Check VLAN configuration on ToR switch.

   .. code-block:: text

      show vlan brief
      show running-config interface vlan <vlan-id>

2. Verify VLAN ID matches ``network_spec.yml`` documentation.

3. Check switchport configuration on node ports.

   .. code-block:: text

      show running-config interface ethernet <port>

**Resolution**

1. Correct VLAN configuration on ToR switch.

   .. code-block:: text

      vlan 1101
        name Admin-Rack1
        exit

      interface Ethernet1/1
        switchport access vlan 1101
        exit

2. Verify trunk configuration for uplink ports.

   .. code-block:: text

      interface Port-channel1
        switchport trunk allowed vlan add 1101
        exit

3. Verify VLAN is active.

   .. code-block:: text

      show vlan brief

**Verification**

Test connectivity from node to gateway IP. Verify DHCP requests are forwarded.

CoreDHCP Service Issues
-----------------------

CoreDHCP Service Not Running
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**
- CoreDHCP container not running
- All DHCP requests fail
- No response to DHCP broadcasts

**Diagnostic Steps**

1. Check container status.

   .. code-block:: bash

      podman ps -a | grep coredhcp

2. Check container logs for exit reasons.

   .. code-block:: bash

      podman logs coredhcp

3. Check for configuration errors.

   .. code-block:: bash

      podman exec coredhcp coredhcp --check-config

**Resolution**

1. Start CoreDHCP container.

   .. code-block:: bash

      cd /opt/omnia
      ansible-playbook deploy_openchami.yml

2. If container fails to start, check configuration file.

   .. code-block:: bash

      cat /opt/omnia/config/coredhcp.yaml

3. Fix configuration errors and restart.

   .. code-block:: bash

      podman restart coredhcp

**Verification**

Check container status is "Up". Verify DHCP requests are processed.

Configuration Parsing Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**
- CoreDHCP fails to start or reload
- Configuration syntax errors in logs
- Subnet registration failures

**Diagnostic Steps**

1. Check CoreDHCP logs for parsing errors.

   .. code-block:: bash

      podman logs coredhcp | grep -i error

2. Validate configuration file syntax.

   .. code-block:: bash

      podman exec coredhcp coredhcp --check-config

3. Check CoreDHCP template generation.

   .. code-block:: bash

      cat /opt/omnia/config/coredhcp.yaml

**Resolution**

1. Identify syntax errors in configuration file.

2. Correct template or ``network_spec.yml`` configuration.

3. Regenerate configuration.

   .. code-block:: bash

      cd /opt/omnia
      ansible-playbook deploy_openchami.yml

**Verification**

CoreDHCP starts successfully. Logs show no parsing errors.

Plugin Loading Failures
~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**
- CoreDHCP fails to load coresmd plugin
- Multi-subnet functionality not working
- Plugin errors in logs

**Diagnostic Steps**

1. Check CoreDHCP logs for plugin errors.

   .. code-block:: bash

      podman logs coredhcp | grep -i plugin

2. Verify coresmd plugin is installed.

   .. code-block:: bash

      podman exec coredhcp ls /plugins/

3. Check coresmd version.

   .. code-block:: bash

      podman exec coredhcp coresmd --version

**Resolution**

1. Ensure coresmd v0.5+ is installed.

   .. code-block:: bash

      # Reinstall coresmd if needed
      cd /opt/omnia
      ansible-playbook deploy_openchami.yml

2. Verify plugin configuration in CoreDHCP config file.

3. Restart CoreDHCP.

   .. code-block:: bash

      podman restart coredhcp

**Verification**

Logs show plugin loaded successfully. Multi-subnet DHCP functions correctly.

IP Assignment Problems
---------------------

Nodes Receiving Wrong IP Addresses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**
- Node in Rack 2 receives IP from Rack 1 subnet pool
- giaddr not matching expected subnet
- IP assignment not rack-specific

**Diagnostic Steps**

1. Check CoreDHCP logs for giaddr values.

   .. code-block:: bash

      podman logs coredhcp | grep giaddr

2. Verify DHCP relay helper-address on ToR switch.

   .. code-block:: text

      show running-config interface vlan <vlan-id>

3. Verify router parameter in ``network_spec.yml``.

**Resolution**

1. Correct router parameter to match ToR SVI IP.

   .. code-block:: yaml

      additional_subnets:
        - subnet: "10.40.3.0/24"
          netmask_bits: "24"
          router: "10.40.3.1"  # Must match ToR SVI
          dynamic_range: "10.40.3.100-10.40.3.200"

2. Redeploy CoreDHCP configuration.

   .. code-block:: bash

      ansible-playbook deploy_openchami.yml

3. Restart DHCP relay on ToR switch.

**Verification**

Boot node and verify IP from correct subnet. Check giaddr in logs.

DHCP Pool Exhaustion
~~~~~~~~~~~~~~~~~~~

**Symptoms**
- Nodes cannot obtain IP addresses
- Pool utilization at 100%
- DHCP requests fail with no available addresses

**Diagnostic Steps**

1. Check pool utilization.

   .. code-block:: bash

      podman logs coredhcp | grep -i pool

2. Check for stale leases.

   .. code-block:: bash

      podman exec coredhcp coredhcp --show-leases

3. Monitor pool utilization trends.

**Resolution**

1. Increase pool size within subnet.

   .. code-block:: yaml

      additional_subnets:
        - subnet: "10.40.1.0/24"
          netmask_bits: "24"
          router: "10.40.1.1"
          dynamic_range: "10.40.1.50-10.40.1.250"  # Expanded pool

2. Clear stale leases if needed.

   .. code-block:: bash

      podman exec coredhcp coredhcp --clear-stale-leases

3. Add additional subnet if pool cannot be expanded.

**Verification**

Monitor pool utilization. Nodes successfully obtain IPs.

Debug Tools and Commands
-------------------------

Packet Capture
~~~~~~~~~~~~~~

Use packet capture to diagnose DHCP traffic:

1. Capture DHCP traffic on OIM admin interface.

   .. code-block:: bash

      tcpdump -i eno1 port 67 or port 68 -vv

2. Capture on ToR switch.

   .. code-block:: text

      monitor capture point attach cCAP all interface vlan <vlan-id> both
      monitor capture point start cCAP

3. Analyze captured packets for giaddr and DHCP options.

DHCP Log Analysis
~~~~~~~~~~~~~~~~

Analyze CoreDHCP logs for patterns:

1. Filter for specific subnet.

   .. code-block:: bash

      podman logs coredhcp | grep "10.40.1"

2. Filter for errors.

   .. code-block:: bash

      podman logs coredhcp | grep -i error

3. Monitor real-time DHCP activity.

   .. code-block:: bash

      podman logs -f coredhcp

SMD Integration Check
~~~~~~~~~~~~~~~~~~~~

Verify SMD integration for IP assignment:

1. Check SMD for MAC/interface data.

   .. code-block:: bash

      curl http://smd-service:8080/v1/nodes

2. Verify SMD data includes subnet information.

3. Check coresmd-SMD connectivity.

   .. code-block:: bash

      podman exec coredhcp curl http://smd-service:8080/v1/health

Escalation Path
---------------

If issues cannot be resolved using this guide:

1. Collect diagnostic information:
   - CoreDHCP logs
   - Network configuration files
   - Switch configurations
   - Packet captures

2. Document all troubleshooting steps taken.

3. Contact Dell support with collected information.

4. Provide:
   - Omnia version
   - Network topology diagram
   - ``network_spec.yml`` configuration
   - CoreDHCP logs
   - Switch configurations

Next Steps
----------

For configuration procedures, see :doc:`OmniaInstallGuide/AdvancedConfigurations/multi-subnet-dhcp/how-to-configuration`.

For network architecture details, see :doc:`OmniaInstallGuide/AdvancedConfigurations/multi-subnet-dhcp/concept-network-architecture`.

For best practices, see :doc:`OmniaInstallGuide/AdvancedConfigurations/multi-subnet-dhcp/how-to-best-practices`.
