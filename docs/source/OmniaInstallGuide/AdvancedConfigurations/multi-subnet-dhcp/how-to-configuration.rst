.. _how-to-multi-subnet-dhcp-configuration:

Configuring Multi-Subnet DHCP
============================

Configure multi-subnet DHCP in Omnia to enable rack-based network provisioning with per-rack /24 subnets. This procedure covers editing the ``/opt/omnia/input/project_default/network_spec.yml`` file, validating the configuration, and deploying the CoreSMD changes to support multiple subnets via DHCP relay.

Prerequisites
-------------

Before configuring multi-subnet DHCP:

* Omnia Infrastructure Manager (OIM) deployed and operational with ``omnia_core`` container up and running (``prepare_oim.yml`` playbook executed successfully)
* Network switches configured with VLANs and DHCP relay helper-address pointing to the OIM CoreSMD server
* CoreSMD services deployed (CoreSMD v0.6.3+ required for multi-subnet support)
* Network topology documented with rack IDs, subnet allocations, gateway IPs, and VLAN assignments
* DHCP pool ranges planned and validated to avoid conflicts with static IPs and OIM admin IP
* PXE mapping file configured and validated for your deployment scenario. Ensure that the ``pxe_mapping_file.csv`` is aligned with your network topology. For sample configurations, see :doc:`../../samplefiles`.

.. important::
   Multi-Subnet DHCP requires DHCP relay agents configured on each subnet's gateway/router. Without proper DHCP relay configuration, DHCP requests from remote subnets will not reach the CoreSMD server.

Procedure
---------

1. Use SSH to connect to the ``omnia_core`` container on the OIM node.

   .. code-block:: bash

      ssh omnia_core

2. Navigate to the input directory and view the current ``network_spec.yml`` file.

   .. code-block:: bash

      cd /opt/omnia/input/project_default/
      cat network_spec.yml

3. Edit the ``network_spec.yml`` file to add the ``additional_subnets`` field under the ``admin_network`` section.

   .. code-block:: bash

      vi network_spec.yml

4. Add the ``additional_subnets`` array with subnet entries for each rack. For a complete description of subnet parameters and the multi-subnet DHCP architecture, see :doc:`concept-overview`.

   Example configuration for 2 racks:

   .. code-block:: yaml

      Networks:
      - admin_network:
          oim_nic_name: "eno1"
          subnet: "10.40.1.0"
          netmask_bits: "24"
          primary_oim_admin_ip: "10.40.1.111"
          primary_oim_bmc_ip: ""
          dynamic_range: "10.40.1.201-10.40.1.250"
          dns: []
          ntp_servers: []
          additional_subnets:
            - subnet: "10.40.2.0"
              netmask_bits: "24"
              router: "10.40.2.1"
              dynamic_range: "10.40.2.190-10.40.2.200"

            - subnet: "10.40.3.0"
              netmask_bits: "24"
              router: "10.40.3.1"
              dynamic_range: "10.40.3.190-10.40.3.200"

      - ib_network:
          subnet: "198.168.0.0"
          netmask_bits: "24"
          dns: []

   .. note::
      Leave ``additional_subnets: []`` (empty array) for single-subnet deployments. This maintains backward compatibility with existing configurations.

5. Execute the ``prepare_oim.yml`` playbook using the following command:

   .. code-block:: bash

      cd /omnia/prepare_oim
      ansible-playbook prepare_oim.yml

6. After successfully executing the ``prepare_oim.yml`` playbook, verify that all required services are running correctly by executing

   .. code-block:: bash

      systemctl list-dependencies openchami.target

7. Stop the openchami services before modifying the configuration:

   .. code-block:: bash

      systemctl stop openchami.target

8. Exit the ``omnia_core`` container and return to the OIM node host system. Then open the ``/etc/openchami/configs/coredhcp.yaml`` configuration file on the OIM node host system.

   .. code-block:: bash

      exit
      sudo vi /etc/openchami/configs/coredhcp.yaml

   In the ``coredhcp.yaml`` file, locate the **Multi-subnet configuration section (requires CoreSMD v0.6.3+)** heading. The steps below provide the same instructions documented in that section. Follow these steps to enable multi-subnet DHCP:

   1. Pull the new coresmd image:

      .. code-block:: bash

         podman pull ghcr.io/openchami/coresmd:v0.6.3

   2. Comment out the single-subnet coresmd and bootloop lines above the multi-subnet configuration section
   3. Uncomment the multi-subnet coresmd and bootloop blocks below the heading
   4. Update the CoreSMD container image version to the new coresmd version in the following files:

      - ``/etc/containers/systemd/coresmd-coredhcp.container``
      - ``/etc/containers/systemd/coresmd-coredns.container``

   5. Reload the systemd daemon:

      .. code-block:: bash

         systemctl daemon-reload

   6. Restart the openchami services:

      .. code-block:: bash

         systemctl restart openchami.target

.. note::
   The multi-subnet configuration section in ``coredhcp.yaml`` contains the specific coresmd and bootloop configuration blocks that need to be uncommented for multi-subnet DHCP to function correctly. Ensure these blocks are properly configured before restarting services.

.. 

9. Ensure that services such as CoreSMD and other dependent services are in an active state. If any of the core services fail to start, use the following commands to check the error logs:

   .. code-block:: bash

      journalctl -xeu coresmd-coredhcp
      journalctl -xeu coresmd-coredns

Verification
------------

After configuring multi-subnet DHCP, verify the following:

- Verify that CoreSMD has registered the additional subnets. Expected output should show ``subnet=`` directives for each additional subnet::

    podman logs coresmd-coredhcp | grep "subnet="

Configuration Examples
-----------------------

Ten-Rack Configuration
~~~~~~~~~~~~~~~~~~~~~~

For a large deployment with 10 racks:

.. code-block:: yaml

   Networks:
   - admin_network:
      oim_nic_name: "eno1"
      subnet: "10.40.1.0"
      netmask_bits: "24"
      primary_oim_admin_ip: "10.40.1.111"
      primary_oim_bmc_ip: ""
      dynamic_range: "10.40.1.201-10.40.1.250"
      dns: []
      ntp_servers: []
      additional_subnets:
         - subnet: "10.40.2.0"
           netmask_bits: "24"
           router: "10.40.2.1"
           dynamic_range: "10.40.2.190-10.40.2.200"
         - subnet: "10.40.3.0"
           netmask_bits: "24"
           router: "10.40.3.1"
           dynamic_range: "10.40.3.190-10.40.3.200"
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
