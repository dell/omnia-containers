.. _how-to-multi-subnet-dhcp-configuration:

Configuring Multi-Subnet DHCP
============================

Configure multi-subnet DHCP in Omnia to enable rack-based network provisioning with per-rack /24 subnets. This procedure covers editing the ``network_spec.yml`` file, validating the configuration, and deploying the CoreDHCP changes to support multiple subnets via DHCP relay.

Prerequisites
-------------

Before configuring multi-subnet DHCP:

* Omnia cluster deployed and operational
* Network switches configured with VLANs and DHCP relay helper-address pointing to the OIM CoreDHCP server
* CoreDHCP and coresmd services deployed (coresmd v0.5+ required for multi-subnet support)
* Access to edit ``input/network_spec.yml`` on the OIM node
* Network topology documented with rack IDs, subnet allocations, gateway IPs, and VLAN assignments
* DHCP pool ranges planned and validated to avoid conflicts with static IPs and OIM admin IP

.. important::
   Multi-Subnet DHCP requires DHCP relay agents configured on each subnet's gateway/router. Without proper DHCP relay configuration, DHCP requests from remote subnets will not reach the CoreDHCP server.

Procedure
---------

1. Use SSH to connect to the ``omnia_core`` container on the OIM node.

   .. code-block:: bash

      ssh omnia_core

2. Navigate to the input directory and view the current ``network_spec.yml`` file.

   .. code-block:: bash

      cd /opt/omnia/input
      cat network_spec.yml

3. Edit the ``network_spec.yml`` file to add the ``additional_subnets`` field under the ``admin_network`` section.

   .. code-block:: bash

      vi network_spec.yml

4. Add the ``additional_subnets`` array with subnet entries for each rack. Each subnet entry requires the following parameters:

   * ``subnet``: Network address in CIDR format (e.g., ``10.40.1.0/24``)
   * ``netmask_bits``: CIDR prefix length (e.g., ``24``)
   * ``router``: Gateway/router IP for this subnet (used as DHCP option 3)
   * ``dynamic_range``: DHCP IP pool range in ``start_ip-end_ip`` format

   Example configuration for 2 racks:

   .. code-block:: yaml

      Networks:
      - admin_network:
          oim_nic_name: "eno1"
          subnet: "172.16.0.0"
          netmask_bits: "24"
          primary_oim_admin_ip: "172.16.107.254"
          primary_oim_bmc_ip: ""
          dynamic_range: "172.16.107.201-172.16.107.250"
          dns: []
          ntp_servers: []
          additional_subnets:
            - subnet: "10.40.1.0"
              netmask_bits: "24"
              router: "10.40.1.1"
              dynamic_range: "10.40.1.100-10.40.1.200"
            - subnet: "10.40.3.0"
              netmask_bits: "24"
              router: "10.40.3.1"
              dynamic_range: "10.40.3.100-10.40.3.200"

   .. note::
      Leave ``additional_subnets: []`` (empty array) for single-subnet deployments. This maintains backward compatibility with existing configurations.

5. Validate the configuration using Omnia's validation playbook.

   .. code-block:: bash

      cd /opt/omnia
      ansible-playbook validate_network_spec.yml

   The validation checks for:
   * Subnet CIDR format validity
   * Subnet overlap with admin network and between additional subnets
   * Dynamic range overlap within and between subnets
   * Router IP reachability
   * Dynamic range within subnet boundaries

6. If validation passes, deploy the CoreDHCP configuration changes.

   .. code-block:: bash

      cd /opt/omnia
      ansible-playbook deploy_openchami.yml

   This playbook:
   * Generates CoreDHCP configuration with subnet-aware directives (``subnet=`` and ``subnet_pool=``)
   * Deploys the custom ``coredhcp.yaml.j2`` template to the OpenCHAMI deployment
   * Restarts CoreDHCP service to load the new configuration

7. Verify that CoreDHCP is running with the new configuration.

   .. code-block:: bash

      podman exec coredhcp coredhcp --version
      podman logs coredhcp | tail -20

   Check the logs for subnet registration messages indicating that the additional subnets are loaded.

Verification
------------

After configuring multi-subnet DHCP, verify the following:

1. Verify that CoreDHCP has registered the additional subnets.

   .. code-block:: bash

      podman logs coredhcp | grep "subnet="

   Expected output should show ``subnet=`` directives for each additional subnet.

2. Verify that DHCP relay is functioning by checking that a node in a remote subnet can obtain an IP address.

   .. code-block:: bash

      # On the OIM node, check CoreDHCP logs for DHCP requests
      podman logs -f coredhcp

   Boot a node in a remote subnet and observe the DHCP request in the logs. The ``giaddr`` field should indicate the subnet gateway IP, and the assigned IP should be from the correct subnet pool.

3. Verify that the assigned IP address is from the correct subnet pool.

   .. code-block:: text

      Example: Node in Rack 2 (subnet 10.40.3.0/24) should receive IP 10.40.3.150
      Expected: IP in range 10.40.3.100-10.40.3.200

4. Verify that the node can PXE boot and provision successfully with the assigned IP address.

   .. code-block:: bash

      # Check node status in SMD
      # Verify node completed PXE boot and cloud-init provisioning

5. Verify that multiple nodes across different subnets can boot simultaneously without IP conflicts.

   .. code-block:: bash

      # Boot nodes in Rack 1 and Rack 2 simultaneously
      # Verify each receives IP from its respective subnet pool
      # Check CoreDHCP logs for proper giaddr-based routing

.. warning::
   If nodes are receiving IP addresses from the wrong subnet, verify that DHCP relay is correctly configured on the ToR switches and that the ``router`` parameter in ``network_spec.yml`` matches the ToR switch interface IP.

Configuration Examples
-----------------------

Two-Rack Configuration
~~~~~~~~~~~~~~~~~~~~~~~

For a deployment with 2 racks, each with its own /24 subnet:

.. code-block:: yaml

   Networks:
   - admin_network:
       oim_nic_name: "eno1"
       subnet: "172.16.0.0"
       netmask_bits: "24"
       primary_oim_admin_ip: "172.16.107.254"
       dynamic_range: "172.16.107.201-172.16.107.250"
       additional_subnets:
         - subnet: "10.40.1.0"
           netmask_bits: "24"
           router: "10.40.1.1"
           dynamic_range: "10.40.1.100-10.40.1.200"
         - subnet: "10.40.3.0"
           netmask_bits: "24"
           router: "10.40.3.1"
           dynamic_range: "10.40.3.100-10.40.3.200"

This configuration:
* Rack 1: Subnet ``10.40.1.0/24``, gateway ``10.40.1.1``, pool ``10.40.1.100-10.40.1.200``
* Rack 2: Subnet ``10.40.3.0/24``, gateway ``10.40.3.1``, pool ``10.40.3.100-10.40.3.200``

Ten-Rack Configuration
~~~~~~~~~~~~~~~~~~~~~~

For a large deployment with 10 racks:

.. code-block:: yaml

   Networks:
   - admin_network:
       oim_nic_name: "eno1"
       subnet: "172.16.0.0"
       netmask_bits: "24"
       primary_oim_admin_ip: "172.16.107.254"
       dynamic_range: "172.16.107.201-172.16.107.250"
       additional_subnets:
         - subnet: "10.40.1.0"
           netmask_bits: "24"
           router: "10.40.1.1"
           dynamic_range: "10.40.1.100-10.40.1.200"
         - subnet: "10.40.3.0"
           netmask_bits: "24"
           router: "10.40.3.1"
           dynamic_range: "10.40.3.100-10.40.3.200"
         - subnet: "10.40.5.0"
           netmask_bits: "24"
           router: "10.40.5.1"
           dynamic_range: "10.40.5.100-10.40.5.200"
         - subnet: "10.40.7.0"
           netmask_bits: "24"
           router: "10.40.7.1"
           dynamic_range: "10.40.7.100-10.40.7.200"
         - subnet: "10.40.9.0"
           netmask_bits: "24"
           router: "10.40.9.1"
           dynamic_range: "10.40.9.100-10.40.9.200"
         - subnet: "10.40.11.0"
           netmask_bits: "24"
           router: "10.40.11.1"
           dynamic_range: "10.40.11.100-10.40.11.200"
         - subnet: "10.40.13.0"
           netmask_bits: "24"
           router: "10.40.13.1"
           dynamic_range: "10.40.13.100-10.40.13.200"
         - subnet: "10.40.15.0"
           netmask_bits: "24"
           router: "10.40.15.1"
           dynamic_range: "10.40.15.100-10.40.15.200"
         - subnet: "10.40.17.0"
           netmask_bits: "24"
           router: "10.40.17.1"
           dynamic_range: "10.40.17.100-10.40.17.200"
         - subnet: "10.40.19.0"
           netmask_bits: "24"
           router: "10.40.19.1"
           dynamic_range: "10.40.19.100-10.40.19.200"

This configuration supports 10 racks with non-overlapping /24 subnets, each with 100 IP addresses available for DHCP allocation.

Common Configuration Errors
---------------------------

**Subnet Overlap**
- **Error**: Validation fails with "subnet overlap detected"
- **Cause**: Two subnets have overlapping CIDR ranges
- **Fix**: Ensure each subnet has a unique, non-overlapping CIDR

**Dynamic Range Outside Subnet**
- **Error**: Validation fails with "dynamic range not within subnet"
- **Cause**: DHCP pool range extends beyond subnet boundaries
- **Fix**: Ensure ``dynamic_range`` start and end IPs are within the subnet CIDR

**Gateway IP Unreachable**
- **Error**: Nodes cannot obtain IP addresses from remote subnet
- **Cause**: Router IP is not reachable from OIM or DHCP relay not configured
- **Fix**: Verify routing and DHCP relay configuration on ToR switches

**Wrong IP Assignment**
- **Error**: Node receives IP from wrong subnet pool
- **Cause**: ``giaddr`` not set correctly by DHCP relay
- **Fix**: Verify DHCP relay helper-address points to CoreDHCP server

Troubleshooting
---------------

For detailed troubleshooting procedures, see :doc:`../../troubleshootingguide/multi-subnet-dhcp`.

Next Steps
----------

After configuring multi-subnet DHCP:

* Review network architecture design patterns in :doc:`concept-network-architecture`
* Apply operational best practices in :doc:`how-to-best-practices`
* Reference the complete parameter documentation in :doc:`../../Tables/network_spec`
