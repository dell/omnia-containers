.. _how-to-multi-subnet-dhcp-configuration:

Configuring Multi-Subnet DHCP
==============================

Configure multi-subnet DHCP in Omnia to enable rack-based network provisioning with per-rack /24 subnets. This procedure covers editing the ``network_spec.yml`` file, validating the configuration, updating the CoreSMD container image, and deploying the CoreSMD changes to support multiple subnets via DHCP relay.

Prerequisites
-------------

Before configuring multi-subnet DHCP:

- Omnia Infrastructure Manager (OIM) deployed and operational with ``omnia_core`` container up and running (``prepare_oim.yml`` playbook executed successfully)

- Network switches configured with VLANs and DHCP relay helper-address pointing to the OIM CoreSMD server

- Network topology documented with rack IDs, subnet allocations, gateway IPs, and VLAN assignments

- DHCP pool ranges planned and validated to avoid conflicts with static IPs and OIM admin IP

- PXE mapping file configured and validated for your deployment scenario. Ensure that the ``pxe_mapping_file.csv`` is aligned with your network topology. For sample configurations, see `Sample Files`_.

.. important::

   Multi-Subnet DHCP requires DHCP relay agents configured on each subnet's gateway/router. Without proper DHCP relay configuration, DHCP requests from remote subnets will not reach the CoreSMD server.

Single-Subnet Baseline
-----------------------

Before converting to multi-subnet, verify your single-subnet deployment is working correctly.

**network_spec.yml (inside omnia_core container)**

Use SSH to connect to the ``omnia_core`` container and view the current configuration::

   ssh omnia_core
   cat /opt/omnia/input/project_default/network_spec.yml

A single-subnet configuration looks like this:

.. code-block:: yaml

   Networks:
   - admin_network:
       oim_nic_name: "eno12399np0"
       subnet: "10.40.1.0"
       netmask_bits: "24"
       primary_oim_admin_ip: "10.40.1.111"
       primary_oim_bmc_ip: ""
       router: "10.40.1.1"
       dynamic_range: "10.40.1.201-10.40.1.250"
       dns: []
       ntp_servers: []
       additional_subnets: []

   - ib_network:
       subnet: "198.168.0.0"
       netmask_bits: "24"
       dns: []

.. note::

   The ``router`` field is mandatory and specifies the gateway IP for the admin network (used as DHCP option 3). If no dedicated router is available, use the ``primary_oim_admin_ip`` value.

**Generated coredhcp.yaml (on OIM host)**

Exit the ``omnia_core`` container and view the CoreDHCP configuration on the OIM host::

   exit
   cat /etc/openchami/configs/coredhcp.yaml

For a single-subnet deployment, the file contains:

.. code-block:: yaml

   server4:
     listen:
       - "%eno12399np0"
     plugins:
       - server_id: 10.40.1.111
       - dns: 10.40.1.111
       - router: 10.40.1.1
       - netmask: 255.255.255.0
       # Single-subnet mode: positional argument format (coresmd v0.4.x)
       - coresmd: https://oimcp.omnia.test:8443 http://10.40.1.111:8081 /root_ca/root_ca.crt 30s 86400s true
       - bootloop: /tmp/coredhcp.db default 5m 10.40.1.201 10.40.1.250

**CoreSMD container quadlet files (on OIM host)**

The single-subnet deployment uses CoreSMD v0.4.3. Verify the container quadlet files::

   cat /etc/containers/systemd/coresmd-coredhcp.container

.. code-block:: ini

   [Unit]
   Description=The CoreSMD CoreDHCP container
   Wants=haproxy.service
   After=haproxy.service
   PartOf=openchami.target

   [Container]
   ContainerName=coresmd-coredhcp

   HostName=coresmd-coredhcp
   Image=ghcr.io/openchami/coresmd:v0.4.3

   # Capabilities
   AddCapability=NET_ADMIN
   AddCapability=NET_RAW

   # Volumes
   Volume=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/root_ca/root_ca.crt:ro,Z
   Volume=/etc/openchami/configs/coredhcp.yaml:/etc/coredhcp/config.yaml:ro,Z

   # Networks for the Container to use
   Network=host

   # Unsupported by generator options
   # Proxy settings
   PodmanArgs=--http-proxy=false

   [Service]
   Restart=always

::

   cat /etc/containers/systemd/coresmd-coredns.container

.. code-block:: ini

   [Unit]
   Description=The CoreSMD CoreDNS container
   Wants=haproxy.service
   After=haproxy.service
   PartOf=openchami.target

   [Container]
   ContainerName=coresmd-coredns

   HostName=coresmd-coredns
   Image=ghcr.io/openchami/coresmd:v0.4.3

   Exec=/coredns

   # Capabilities
   AddCapability=NET_ADMIN
   AddCapability=NET_RAW

   # Volumes
   Volume=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/root_ca/root_ca.crt:ro,Z
   Volume=/etc/openchami/configs/Corefile:/Corefile:ro,Z

   # Networks for the Container to use
   Network=host

   # Unsupported by generator options
   # Proxy settings
   PodmanArgs=--http-proxy=false

   [Service]
   Restart=always

Converting Single-Subnet to Multi-Subnet
------------------------------------------

Follow these steps to convert an existing single-subnet Omnia 2.2 deployment to multi-subnet.

Step 1: Update network_spec.yml
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use SSH to connect to the ``omnia_core`` container and edit ``network_spec.yml`` to add the additional subnets::

   ssh omnia_core
   vi /opt/omnia/input/project_default/network_spec.yml

Add the ``additional_subnets`` array with subnet entries for each rack. For a complete description of subnet parameters and the multi-subnet DHCP architecture, see `Multi-Subnet DHCP Overview`_.

Example configuration for 2 racks:

.. code-block:: yaml

   Networks:
   - admin_network:
       oim_nic_name: "eno12399np0"
       subnet: "10.40.1.0"
       netmask_bits: "24"
       primary_oim_admin_ip: "10.40.1.111"
       primary_oim_bmc_ip: ""
       router: "10.40.1.1"
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

Step 2: Run prepare_oim.yml
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Inside the ``omnia_core`` container, run the ``prepare_oim.yml`` playbook to regenerate the CoreDHCP configuration::

   cd /omnia/prepare_oim
   ansible-playbook prepare_oim.yml

Step 3: Verify the generated coredhcp.yaml
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Exit the ``omnia_core`` container and verify the updated CoreDHCP configuration on the OIM host::

   exit
   cat /etc/openchami/configs/coredhcp.yaml

The file will contain the single-subnet configuration as active, with the multi-subnet configuration commented out below it:

.. code-block:: yaml

   server4:
     listen:
       - "%eno12399np0"
     plugins:
       - server_id: 10.40.1.111
       - dns: 10.40.1.111
       - router: 10.40.1.1
       - netmask: 255.255.255.0
       # Single-subnet mode: positional argument format (coresmd v0.4.x)
       - coresmd: https://oimcp.omnia.test:8443 http://10.40.1.111:8081 /root_ca/root_ca.crt 30s 86400s true
       - bootloop: /tmp/coredhcp.db default 5m 10.40.1.201 10.40.1.250
       # -------------------------------------------------------------------
       # Multi-subnet configuration (requires coresmd v0.6.x+)
       # To enable multi-subnet DHCP:
       #   1. Pull the new coresmd image: podman pull ghcr.io/openchami/coresmd:v0.6.3
       #   2. Comment out the single-subnet coresmd and bootloop lines above
       #   3. Uncomment the multi-subnet coresmd and bootloop blocks below
       #   4. Replace the new coresmd image version in files: /etc/containers/systemd/coresmd-coredhcp.container /etc/containers/systemd/coresmd-coredns.container with the old version
       #   5. Reload daemon: systemctl daemon-reload
       #   6. Restart services: systemctl restart openchami.target
       # -------------------------------------------------------------------
       # - coresmd: |
       #     svc_base_uri=https://oimcp.omnia.test:8443
       #     ipxe_base_uri=http://10.40.1.111:8081
       #     ca_cert=/root_ca/root_ca.crt
       #     cache_valid=30s
       #     lease_time=86400s
       #     single_port=true
       #     rule=subnet:10.40.1.0/24,type:Node,routers:10.40.1.1,cidr:24
       #     rule=subnet:10.40.2.0/24,type:NodeBMC,routers:10.40.2.1,cidr:24
       #     rule=subnet:10.40.3.0/24,type:Node,routers:10.40.3.1,cidr:24
       #     rule=subnet:10.40.4.0/24,type:NodeBMC,routers:10.40.4.1,cidr:24
       #     rule=type:Node
       #     rule=type:NodeBMC
       #     rule=hostname:unknown-{04d}
       # - bootloop: |
       #     lease_file=/tmp/coredhcp.db
       #     script_path=default
       #     lease_time=5m
       #     subnet_pool=10.40.1.0/24,10.40.1.190,10.40.1.200
       #     subnet_pool=10.40.2.0/24,10.40.2.190,10.40.2.200
       #     subnet_pool=10.40.3.0/24,10.40.3.190,10.40.3.200
       #     subnet_pool=10.40.4.0/24,10.40.4.190,10.40.4.200

Step 4: Stop OpenCHAMI services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On the OIM host, stop all OpenCHAMI services before modifying the container configuration::

   systemctl stop openchami.target

Step 5: Pull the new CoreSMD image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pull the CoreSMD v0.6.3 image which supports multi-subnet DHCP::

   podman pull ghcr.io/openchami/coresmd:v0.6.3

Step 6: Enable multi-subnet in coredhcp.yaml
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On the OIM host, edit the CoreDHCP configuration to switch from single-subnet to multi-subnet mode::

   vi /etc/openchami/configs/coredhcp.yaml

Make the following changes:

1. **Comment out** the single-subnet ``coresmd`` and ``bootloop`` lines (add ``#`` prefix)
2. **Uncomment** the multi-subnet ``coresmd`` and ``bootloop`` blocks (remove ``#`` prefix)

The resulting file should look like this:

.. code-block:: yaml

   server4:
     listen:
       - "%eno12399np0"
     plugins:
       - server_id: 10.40.1.111
       - dns: 10.40.1.111
       - router: 10.40.1.1
       - netmask: 255.255.255.0
       # Single-subnet mode: positional argument format (coresmd v0.4.x)
       #- coresmd: https://oimcp.omnia.test:8443 http://10.40.1.111:8081 /root_ca/root_ca.crt 30s 86400s true
       #- bootloop: /tmp/coredhcp.db default 5m 10.40.1.201 10.40.1.250
       # -------------------------------------------------------------------
       # Multi-subnet configuration (requires coresmd v0.6.x+)
       # To enable multi-subnet DHCP:
       #   1. Pull the new coresmd image: podman pull ghcr.io/openchami/coresmd:v0.6.3
       #   2. Comment out the single-subnet coresmd and bootloop lines above
       #   3. Uncomment the multi-subnet coresmd and bootloop blocks below
       #   4. Replace the new coresmd image version in files: /etc/containers/systemd/coresmd-coredhcp.container /etc/containers/systemd/coresmd-coredns.container with the old version
       #   5. Reload daemon: systemctl daemon-reload
       #   6. Restart services: systemctl restart openchami.target
       # -------------------------------------------------------------------
       - coresmd: |
           svc_base_uri=https://oimcp.omnia.test:8443
           ipxe_base_uri=http://10.40.1.111:8081
           ca_cert=/root_ca/root_ca.crt
           cache_valid=30s
           lease_time=86400s
           single_port=true
           rule=subnet:10.40.1.0/24,type:Node,routers:10.40.1.1,cidr:24
           rule=subnet:10.40.2.0/24,type:NodeBMC,routers:10.40.2.1,cidr:24
           rule=subnet:10.40.3.0/24,type:Node,routers:10.40.3.1,cidr:24
           rule=subnet:10.40.4.0/24,type:NodeBMC,routers:10.40.4.1,cidr:24
           rule=type:Node
           rule=type:NodeBMC
           rule=hostname:unknown-{04d}
       - bootloop: |
           lease_file=/tmp/coredhcp.db
           script_path=default
           lease_time=5m
           subnet_pool=10.40.1.0/24,10.40.2.190,10.40.1.200
           subnet_pool=10.40.2.0/24,10.40.3.190,10.40.2.200
           subnet_pool=10.40.3.0/24,10.40.2.190,10.40.3.200
           subnet_pool=10.40.4.0/24,10.40.3.190,10.40.4.200

Step 7: Update coresmd-coredhcp.container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Update the CoreSMD CoreDHCP container quadlet file to use the new image version::

   vi /etc/containers/systemd/coresmd-coredhcp.container

Change the ``Image`` line from ``v0.4.3`` to ``v0.6.3``:

.. code-block:: ini

   [Unit]
   Description=The CoreSMD CoreDHCP container
   Wants=haproxy.service
   After=haproxy.service
   PartOf=openchami.target

   [Container]
   ContainerName=coresmd-coredhcp

   HostName=coresmd-coredhcp
   Image=ghcr.io/openchami/coresmd:v0.6.3

   # Capabilities
   AddCapability=NET_ADMIN
   AddCapability=NET_RAW

   # Volumes
   Volume=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/root_ca/root_ca.crt:ro,Z
   Volume=/etc/openchami/configs/coredhcp.yaml:/etc/coredhcp/config.yaml:ro,Z

   # Networks for the Container to use
   Network=host

   # Unsupported by generator options
   # Proxy settings
   PodmanArgs=--http-proxy=false

   [Service]
   Restart=always

Step 8: Update coresmd-coredns.container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Update the CoreSMD CoreDNS container quadlet file to use the new image version::

   vi /etc/containers/systemd/coresmd-coredns.container

Change the ``Image`` line from ``v0.4.3`` to ``v0.6.3``:

.. code-block:: ini

   [Unit]
   Description=The CoreSMD CoreDNS container
   Wants=haproxy.service
   After=haproxy.service
   PartOf=openchami.target

   [Container]
   ContainerName=coresmd-coredns

   HostName=coresmd-coredns
   Image=ghcr.io/openchami/coresmd:v0.6.3

   Exec=/coredns

   # Capabilities
   AddCapability=NET_ADMIN
   AddCapability=NET_RAW

   # Volumes
   Volume=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/root_ca/root_ca.crt:ro,Z
   Volume=/etc/openchami/configs/Corefile:/Corefile:ro,Z

   # Networks for the Container to use
   Network=host

   # Unsupported by generator options
   # Proxy settings
   PodmanArgs=--http-proxy=false

   [Service]
   Restart=always

Step 9: Reload systemd and restart services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reload the systemd daemon to pick up the quadlet file changes, then restart the OpenCHAMI services::

   systemctl daemon-reload
   systemctl restart openchami.target

Verification
------------

After configuring multi-subnet DHCP, verify the following:

1. **Verify all OpenCHAMI services are running**:

   ::

      systemctl list-dependencies openchami.target

   Ensure that services such as CoreSMD and other dependent services are in an active state.

2. **Verify CoreSMD has registered the additional subnets**. Expected output should show ``subnet=`` directives for each additional subnet:

   ::

      podman logs coresmd-coredhcp | grep "subnet="

3. **Check error logs** if any of the core services fail to start:

   ::

      journalctl -xeu coresmd-coredhcp
      journalctl -xeu coresmd-coredns

Configuration Examples
-----------------------

Ten-Rack Configuration
^^^^^^^^^^^^^^^^^^^^^^^

For a large deployment with 10 racks:

.. code-block:: yaml

   Networks:
   - admin_network:
       oim_nic_name: "eno1"
       subnet: "10.40.1.0"
       netmask_bits: "24"
       primary_oim_admin_ip: "10.40.1.111"
       primary_oim_bmc_ip: ""
       router: "10.40.1.1"
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

If you have any feedback about Omnia documentation, please reach out at omnia.readme@dell.com.
