Discovery Mechanisms for Target Node Information
========================================================

Omnia supports two discovery mechanisms for discovering target nodes for provisioning:

* **OME-based BMC Discovery** (Recommended): Uses OpenManage Enterprise (OME) to automatically discover and manage target servers via their BMC/iDRAC interfaces.
* **Mapping File Discovery**: Manually collect PXE NIC information for target servers and define them to Omnia using the **pxe_mapping_file.csv** file.

OME-based BMC Discovery
-------------------------

OME-based BMC discovery is the recommended method for discovering target nodes. This mechanism leverages OpenManage Enterprise to automatically discover servers through their BMC/iDRAC interfaces, reducing manual configuration effort.

.. note::
   In Dell Omnia deployments integrated with OpenManage Enterprise (OME), server identification and mapping during PXE boot rely on information retrieved from OME and iDRAC inventory. Depending on the DNS environment, the DnsName value may match the intended iDRAC hostname, or may return a reverse DNS name (e.g., pool‑<IP‑based>), which may not align with naming conventions required for cluster configuration. Due to differences between iDRAC configuration and OME‑reported hostnames, users must explicitly define GROUP_NAME and PARENT_SERVICE_TAG in the pxe_mapping_file to ensure accurate PXE provisioning and cluster setup in Omnia..

**Prerequisites**

Before initiating OME-based BMC discovery, ensure the following:

- OpenManage Enterprise is already installed and configured
- All iDRAC IPs for all the servers are preconfigured
- OME has already discovered the devices
- Functional Groups are created in OME
- Server location is already specified in iDRAC Hostname

To use OME-based discovery:

1. Ensure OpenManage Enterprise (OME) is accessible from the Omnia Infrastructure Manager (OIM) and configured with the target servers.
2. Configure the ``discovery_config.yml`` file with OME connection details and discovery parameters.
3. Execute the ``discovery.yml`` playbook with the ``discovery_mechanism=ome`` parameter::

    ssh omnia_core
    cd /omnia/discovery
    ansible-playbook discovery.yml -e "discovery_mechanism=ome"

For detailed configuration of ``discovery_config.yml``, see :doc:`provisionparams`.

Mapping File Discovery
-----------------------

Target nodes for provisioning can also be discovered using the mapping file method.
Manually collect PXE NIC information for target servers and manually define them to Omnia using the **pxe_mapping_file.csv** file. Provide the file path to the ``pxe_mapping_file`` variable in ``/opt/omnia/input/project_default/provision_config.yml``.
A sample format is shown below:

::

    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,xx:yy:zz:aa:bb:cc,172.16.107.52,xx:yy:zz:aa:bb:dd,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
    slurm_node_x86_64,grp1,ABCD34,ABFL82,slurm-node1,aa:bb:cc:dd:ee:ff,172.16.107.43,aa:bb:cc:dd:ee:gg,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
    slurm_node_x86_64,grp1,ABFG34,ABKD88,slurm-node2,aa:bb:cc:dd:ee:ff,172.16.107.44,aa:bb:cc:dd:ff:gg,172.17.107.44,InfiniBand.Slot.7-1,192.168.0.102
    login_compiler_node_x86_64,grp8,ABCD78,,login-compiler-node1,aa:bb:cc:dd:ee:gg,172.16.107.41,aa:bb:cc:dd:ee:bb,172.17.107.41,InfiniBand.Slot.7-1,192.168.0.103
    login_compiler_node_x86_64,grp8,ABFG78,,login-compiler-node2,aa:bb:cc:dd:ee:gg,172.16.107.42,aa:bb:cc:dd:ee:bb,172.17.107.42,InfiniBand.Slot.7-1,192.168.0.104
    service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,aa:bb:cc:dd:ee:ff,172.16.107.53,xx:yy:zz:aa:bb:ff,172.17.107.53,,InfiniBand.Slot.7-1,192.168.0.105
    service_kube_control_plane_x86_64,grp4,ABFH78,,service-kube-control-plane2,aa:bb:cc:dd:ee:hh,172.16.107.54,xx:yy:zz:aa:bb:hh,172.17.107.54,,InfiniBand.Slot.7-1,192.168.0.106
    service_kube_control_plane_x86_64,grp4,ABFH80,,service-kube-control-plane3,aa:bb:cc:dd:ee:ii,172.16.107.55,xx:yy:zz:aa:bb:ii,172.17.107.55,,InfiniBand.Slot.7-1,192.168.0.107
    service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,aa:bb:cc:dd:ee:jj,172.16.107.56,xx:yy:zz:aa:bb:jj,172.17.107.56,InfiniBand.Slot.7-1,192.168.0.108
    service_kube_node_x86_64,grp5,ABKD88,,service-kube-node2,aa:bb:cc:dd:ee:kk,172.16.107.57,xx:yy:zz:aa:bb:ff,172.17.107.57,InfiniBand.Slot.7-1,192.168.0.109


.. note::
    * The header fields mentioned above are case sensitive.
    * The IP addresses provided in the mapping file are not validated by Omnia. Ensure that the correct IP addresses are provided. Incorrect IP addresses can cause unexpected failures.
    * The service tags provided in the mapping file are not validated by Omnia. Ensure that correct service tags are provided. Incorrect service tags can cause unexpected failures.
    * The hostnames provided should not contain the domain name of the nodes.
    * The PARENT_SERVICE_TAG is required only for slurm nodes.
    * The ADMIN_MAC and BMC_MAC addresses provided in ``pxe_mapping_file.csv`` should refer to the PXE NIC and BMC NIC on the target nodes respectively.
    * IB_NIC_NAME and IB_IP are for nodes with IB NIC connectivity. The IB_NIC_NAME should specify the Active IB Port (e.g., "InfiniBand.Slot.7-1").
    * Target servers should be configured to boot in PXE mode with the appropriate NIC as the first boot device.
    * When using the OME-based discovery mechanism, the PXE mapping will be automatically populated. The user can verify and edit the mapping file if necessary. The file path should be provided in the ``provision_config.yml`` file.