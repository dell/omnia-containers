Step 2: Create Mapping File with Node Information
===================================================

In Omnia, nodes are discovered and provisioned based on the  **groups** and **functional groups** defined in the mapping file. By combining both groups and functional groups, Omnia offers a powerful and flexible approach to managing large-scale node infrastructures, ensuring both logical organization and physical optimization of resources.


* A **group** is based on the physical characteristics of the nodes. It refers to nodes that are located in the same place or have similar hardware. For example, nodes in the same rack or SU (Scalable Unit) might be grouped together, with specific functional groups like **Service Kube Node** or **Slurm Control Node**. Groups help with physical organization and management of nodes.

   
* A **functional group** defines what a node does in the system. It is a way to categorize nodes based on their functionality. Functional groups help group nodes that perform similar tasks, making it easier to manage and assign resources.
  For example, a node could belong to a functional group such as:

  - **Service Kube Control Plane** 
  - **Service Kube Node** 
  - **Slurm Login Node** 
  - **Slurm Login/Compiler Node** 
  - **Slurm Control Node** 
  - **Slurm Node**

.. _pxe_mapping_file:

Create Mapping File
-----------------------
Manually collect PXE NIC information of the nodes to be provisioned and manually define them to Omnia using the **pxe_mapping_file.csv** file. Provide the file path to the ``pxe_mapping_file_path`` variable in ``/opt/omnia/input/project_default/provision_config.yml``.
Each node listed in the mapping file must be assigned with the following values: 
``FUNCTIONAL_GROUP_NAME``, ``GROUP_NAME``, ``SERVICE_TAG``, ``PARENT_SERVICE_TAG``, ``HOSTNAME``, ``ADMIN_MAC``, 
``ADMIN_IP``, ``BMC_MAC``, ``BMC_IP``, ``IB_NIC_NAME``, and ``IB_IP``.

Refer to the :ref:`Group Attributes <group-attributes-section>` table in :doc:`../../../OmniaInstallGuide/RHEL_new/composable_roles` to assign the appropriate
``GROUP_NAME`` and the :ref:`Types of Functional Groups <functional-groups-section>` table to
assign the correct ``FUNCTIONAL_GROUP_NAME`` for each node in the mapping file.

The following is the sample format of a mapping file for x86_64 cluster::

    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,a1:b2:c3:d4:e5:f6,172.16.107.52,a2:b3:c4:d5:e6:f7,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
    slurm_node_x86_64,grp1,ABCD34,ABFL82,slurm-node1,b1:c2:d3:e4:f5:a6,172.16.107.43,b2:c3:d4:e5:f6:a7,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
    slurm_node_x86_64,grp1,ABFG34,ABKD88,slurm-node2,c1:d2:e3:f4:a5:b6,172.16.107.44,c2:d3:e4:f5:a6:b7,172.17.107.44,InfiniBand.Slot.7-1,192.168.0.102
    login_compiler_node_x86_64,grp8,ABCD78,,login-compiler-node1,d1:e2:f3:a4:b5:c6,172.16.107.41,d2:e3:f4:a5:b6:c7,172.17.107.41,InfiniBand.Slot.7-1,192.168.0.103
    login_compiler_node_x86_64,grp8,ABFG78,,login-compiler-node2,e1:f2:a3:b4:c5:d6,172.16.107.42,e2:f3:a4:b5:c6:d7,172.17.107.42,InfiniBand.Slot.7-1,192.168.0.104
    service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,f1:a2:b3:c4:d5:e6,172.16.107.53,f2:a3:b4:c5:d6:e7,172.17.107.53,,InfiniBand.Slot.7-1,192.168.0.105
    service_kube_control_plane_x86_64,grp4,ABFH78,,service-kube-control-plane2,11:22:33:44:55:66,172.16.107.54,12:23:34:45:56:67,172.17.107.54,,InfiniBand.Slot.7-1,192.168.0.106
    service_kube_control_plane_x86_64,grp4,ABFH80,,service-kube-control-plane3,aa:bb:cc:dd:ee:01,172.16.107.55,ab:bc:cd:de:ef:12,172.17.107.55,,InfiniBand.Slot.7-1,192.168.0.107
    service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,33:44:55:66:77:88,172.16.107.56,34:45:56:67:78:89,172.17.107.56,InfiniBand.Slot.7-1,192.168.0.108
    service_kube_node_x86_64,grp5,ABKD88,,service-kube-node2,55:66:77:88:99:aa,172.16.107.57,56:67:78:89:aa:bb,172.17.107.57,InfiniBand.Slot.7-1,192.168.0.109
    os_x86_64,grp6,ABEF56,,os-node1,77:88:99:aa:bb:cc,172.16.107.60,78:89:aa:bb:cc:dd,172.17.107.60,,

The following is the sample format of a mapping file for x86_64 and aarch64 cluster::

    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,a1:b2:c3:d4:e5:f6,172.16.107.52,a2:b3:c4:d5:e6:f7,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
    slurm_node_aarch64,grp1,ABCD34,ABFL82,slurm-node1,b1:c2:d3:e4:f5:a6,172.16.107.43,b2:c3:d4:e5:f6:a7,172.17.107.43,InfiniBand.Slot.7-2,192.168.0.101
    slurm_node_aarch64,grp2,ABFG34,ABKD88,slurm-node2,c1:d2:e3:f4:a5:b6,172.16.107.44,c2:d3:e4:f5:a6:b7,172.17.107.44,NIC.InfiniBand.1-3,192.168.0.102
    login_compiler_node_aarch64,grp8,ABCD78,,login-compiler-node1,d1:e2:f3:a4:b5:c6,172.16.107.41,d2:e3:f4:a5:b6:c7,172.17.107.41,InfiniBand.PCIe.Slot.8-1,192.168.0.103
    login_node_aarch64,grp9,ABFG78,,login-node1,e1:f2:a3:b4:c5:d6,172.16.107.42,e2:f3:a4:b5:c6:d7,172.17.107.42,NIC.InfiniBand.1-1,192.168.0.104
    service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,f1:a2:b3:c4:d5:e6,172.16.107.53,f2:a3:b4:c5:d6:e7,172.17.107.53,,
    service_kube_control_plane_x86_64,grp4,ABFH78,,service-kube-control-plane2,11:22:33:44:55:66,172.16.107.54,12:23:34:45:56:67,172.17.107.54,,
    service_kube_control_plane_x86_64,grp4,ABFH80,,service-kube-control-plane3,aa:bb:cc:dd:ee:01,172.16.107.55,ab:bc:cd:de:ef:12,172.17.107.55,,
    service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,33:44:55:66:77:88,172.16.107.56,34:45:56:67:78:89,172.17.107.56,,
    service_kube_node_x86_64,grp5,ABKD88,,service-kube-node2,55:66:77:88:99:aa,172.16.107.57,56:67:78:89:aa:bb,172.17.107.57,,
    os_x86_64,grp6,ABEF56,,os-node1,77:88:99:aa:bb:cc,172.16.107.60,78:89:aa:bb:cc:dd,172.17.107.60,,
    os_aarch64,grp7,ABEF78,,os-node2,99:aa:bb:cc:dd:ee,172.16.107.61,9a:ab:bc:cd:de:ef,172.17.107.61,,



.. note::
    * Ensure that nodes belonging to the same group have the same parent. In the mapping file, node entries with the same ``GROUP_NAME`` must have the same parent specified in the ``PARENT_SERVICE_TAG`` column.
    * The header fields mentioned above are case sensitive.
    * The IP addresses provided in the mapping file are not validated by Omnia. Ensure that the correct IP addresses are provided. Incorrect IP addresses can cause unexpected failures.
    * The service tags provided in the mapping file are not validated by Omnia. Ensure that correct service tags are provided. Incorrect service tags can cause unexpected failures.
    * The hostnames provided should not contain the domain name of the nodes.
    * All fields mentioned in the mapping file are mandatory.
    * The ADMIN_MAC and BMC_MAC addresses provided in ``pxe_mapping_file.csv`` should refer to the PXE NIC and BMC NIC on the target nodes respectively.
    * Target servers should be configured to boot in PXE mode with the appropriate NIC as the first boot device.


.. _group-attributes-section:

Groups
------

Nodes that are located in the same place or similar hardware can be grouped together. To do so, update the mapping file with all necessary attributes for the nodes, based on their role within the cluster. Each group will have following attributes as indicated in the table below:


.. csv-table:: Group attributes
   :file: ../../Tables/group_attributes.csv
   :header-rows: 1
   :keepspace:

.. _functional-groups-section:

Functional Groups
------------------------

Nodes with similar functional roles or functionalities can be grouped together. The following table lists the functional groups available in Omnia.

.. note:: 
    
    * At least one functional group is mandatory, and you must not change the name of functional groups.
    * Ensure that the group nodes intended for a specific role must be associated with the corresponding functional group and must not be associated under multiple functional groups.
    * The functional groups are case-sensitive.
    * Omnia supports HA functionality for the ``service_cluster``. For more information, see `High Availability <../OmniaInstallGuide/RHEL_new/HighAvailability/index.html>`_.
    * To set up a service cluster, the ``service_kube_node`` must be present in the mapping file.

.. csv-table:: Types of Functional Groups
   :file: ../../Tables/omnia_roles.csv
   :header-rows: 1
   :keepspace:



Recommended Software by Functional Groups
------------------------------------------

.. caution:: Ensure that the ``software_config.json`` file contains all required inputs for the software to be deployed on each functional group.  For more information, see `Input parameters for Local Repositories <https://omnia-devel.readthedocs.io/en/latest/OmniaInstallGuide/RHEL_new/CreateLocalRepo/InputParameters.html>`_.

The following table lists the functional groups along with the recommended software to be deployed on each group.  

+-----------------------------------------+--------------------------------------------------------------------------------------+
| Functional Group Name                   | Recommended Software                                                                 |
+=========================================+======================================================================================+
| service_kube_control_plane_x86_64       | service_k8s.json                                                                     |
+-----------------------------------------+--------------------------------------------------------------------------------------+
| service_kube_node_x86_64                | service_k8s.json                                                                     |
+-----------------------------------------+--------------------------------------------------------------------------------------+
| slurm_control_node_x86_64               | slurm_custom.json, openldap.json, ldms.json                                          |
+-----------------------------------------+--------------------------------------------------------------------------------------+
| slurm_node_x86_64                       | slurm_custom.json, openldap.json, ldms.json                                          |
+-----------------------------------------+--------------------------------------------------------------------------------------+
| slurm_node_aarch64                      | slurm_custom.json, openldap.json, ldms.json                                          |
+-----------------------------------------+--------------------------------------------------------------------------------------+
| login_node_x86_64                       | slurm_custom.json, openldap.json, ldms.json                                          |
+-----------------------------------------+--------------------------------------------------------------------------------------+
| login_node_aarch64                      | slurm_custom.json, openldap.json, ldms.json                                          |
+-----------------------------------------+--------------------------------------------------------------------------------------+
| login_compiler_node_x86_64              | slurm_custom.json, openldap.json, ucx.json, openmpi.json, ldms.json                  |
+-----------------------------------------+--------------------------------------------------------------------------------------+
| login_compiler_node_aarch64             | slurm_custom.json, openldap.json, ucx.json, openmpi.json, ldms.json                  |
+-----------------------------------------+--------------------------------------------------------------------------------------+


Verification
--------------

Ensure that the PXE mapping file is correctly formatted and that all required fields are populated.

Next Steps
-----------

After creating the PXE mapping file, prepare the Omnia Infrastructure Manager by following the instructions in :doc:`preparing-oim-buildstream`.





   



