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
  - **Slurm Compute Node**
  - **Minimal OS** 


Create Mapping File
-----------------------

Omnia supports two methods for discovering target nodes and creating PXE mapping files:

* **Manual PXE file Mapping**: Manually collect PXE NIC information of the nodes to be provisioned and manually define them in the **pxe_mapping_file.csv** file to be used by Omnia. See :ref:`manual_pxe_mapping` for detailed instructions.
* **OME-based BMC PXE file Generation** (Recommended): Use OpenManage Enterprise (OME) to discover the Omnia cluster nodes and generate the PXE mapping file using the ``discovery.yml`` playbook. See :ref:`ome_pxe_generation` for detailed instructions.


.. _manual_pxe_mapping:

Create PXE File Manually
------------------------

Manually collect PXE NIC information of the nodes to be provisioned and manually define them to Omnia using the **pxe_mapping_file.csv** file. Provide the file path to the ``pxe_mapping_file_path`` variable in ``/opt/omnia/input/project_default/provision_config.yml``.
Each node listed in the mapping file must be assigned with the following values: 
``FUNCTIONAL_GROUP_NAME``, ``GROUP_NAME``, ``SERVICE_TAG``, ``PARENT_SERVICE_TAG``, ``HOSTNAME``, ``ADMIN_MAC``, 
``ADMIN_IP``, ``BMC_MAC``, ``BMC_IP``, ``IB_NIC_NAME``, and ``IB_IP``.

Refer to the :ref:`Group Attributes <group-attributes-section>` table to assign the appropriate
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

.. note::
    **Minimal OS Functional Groups**: The ``os_x86_64`` and ``os_aarch64`` functional groups provide a clean operating system baseline designed for downstream platform software installation. These groups include only essential OS packages and LDMS telemetry packages, with no schedulers, container runtimes, or orchestration software. Use these groups when you need a clean OS environment without conflicts from pre-installed components.
    
    **Additional Packages Support**: Administrators can optionally include additional packages by creating ``additional_packages.json`` files in ``input/config/{arch}/rhel/10.0/``. For detailed instructions on configuring additional packages, see :ref:`adding_additional_packages`. When present, these packages are included in the Minimal OS images alongside the base and LDMS packages. If the file is absent or empty, images build successfully with the standard Minimal OS package set only.


.. _ome_pxe_generation:

Create PXE File Using OME
-------------------------

OME-based BMC discovery is the recommended method for discovering target nodes. This mechanism leverages OpenManage Enterprise to automatically discover servers through their BMC/iDRAC interfaces, reducing manual configuration effort.

.. note::
   In Dell Omnia deployments integrated with OpenManage Enterprise (OME), server identification and mapping during PXE boot rely on information retrieved from OME and iDRAC inventory. Depending on the DNS environment, the DnsName value may match the intended iDRAC hostname, or may return a reverse DNS name (e.g., pool‑<IP‑based>), which may not align with naming conventions required for cluster configuration. Due to differences between iDRAC configuration and OME‑reported hostnames, users must explicitly define GROUP_NAME and PARENT_SERVICE_TAG in the pxe_mapping_file to ensure accurate PXE provisioning and cluster setup in Omnia.

**Prerequisites**

Before proceeding with OME discovery, ensure the following:

- OpenManage Enterprise is installed and accessible
- All target servers have iDRAC configured with network connectivity
- OME has discovered the devices (servers are visible in OME inventory)
- You have administrative access to OME
- Ensure that servers have the correct NIC order and configuration to match your intended IP assignment scheme. You must verify NIC ordering in the server BIOS or iDRAC settings before discovery. When Omnia performs OME-based discovery, it uses the following logic:
  
  - **Admin IP**: The first discoverable NIC (typically the first Ethernet interface) will be used to generate the admin IP address in the PXE mapping file
  - **InfiniBand IP**: The first discoverable InfiniBand NIC will be used to generate the InfiniBand IP address in the PXE mapping file
  - **NIC MAC Address Selection**: During discovery, Omnia collects MAC addresses using priority-based selection.
  - **Admin (Non-iDRAC) NIC Selection:**
    - Priority 1: First NIC that is active/UP
    - Priority 2: If first NIC is down, use second NIC if UP
    - Priority 3: If all NICs are down, default to first NIC regardless of link state
    - Scans server NICs excluding the iDRAC/BMC NIC
    - NIC order determined by BIOS/iDRAC settings
  - **InfiniBand (IB) NIC Selection:**
    - If IB NIC detected: IB Nic Name captured and IB_IP assigned
    - If no IB NIC: IB fields left empty in CSV (expected behavior, does not affect provisioning)

- For a deployment with N Scalable Units, ensure one dedicated service_kube_node (Kubernetes worker node) for each Scalable Unit.
- Ensure that iDRAC hostnames follow the Omnia naming convention. In Omnia, the **node name** is the anchor identity for every compute node. It encodes the physical and logical location of the server, read left to right from the largest grouping down to the individual node.The iDRAC hostname should follow this pattern::

    idrac-<SU><1-100>R<000-999>OU<1-54><Type><Instance>

   - **Scalable Unit (SU)**: Represents a logical block of infrastructure — a group of racks deployed and managed together as a single unit. This allows the data center to grow in predictable, repeatable blocks. **Supported formats:** - ``SU1`` through ``SU100`` (case-insensitive: ``su1``, ``SU1``)
   - **R — Rack**: The **Rack** identifier represents the physical rack cabinet housing servers and networking equipment within the Scalable Unit. **Format:** ``R1`` through ``R999``
   - **OU — Open Rack v3 (ORv3) Unit Position**: The **OU** represents the vertical slot position in an ORv3-compliant rack. **Format:** ``OU1`` through ``OU54``
   - **C — Compute Node**: The **C** identifier distinguishes individual compute servers at a rack position. A dense chassis can hold multiple nodes, so the C number identifies each one.  **Format:** ``C1`` through ``C99``

  Example breakdown::

      SU02   R1   OU05   C7
      │      │     │      │
      │      │     │      └──  Compute Node number
      │      │     └─────────  ORv3 (Open Rack v3) Unit position in the rack
      │      └───────────────  Rack number within the Scalable Unit
      └──────────────────────  Scalable Unit number

  **For example** ``SU02R1OU05C7`` = Scalable Unit 02 → Rack 1 → ORv3 Unit position 5 → Compute Node 7.

  .. warning::
     If the iDRAC hostname is not set correctly using this convention before discovery, Omnia will generate incorrect PXE mapping information. Accurate, consistent naming is **mandatory**.

Procedure
----------

1. In OpenManage Enterprise, discover the cluster nodes that you want to provision with Omnia. For more information on discovering devices in OME, see the `OpenManage Enterprise User Guide <https://dl.dell.com/content/manual4/en/openmanage-enterprise-user-guide-en>`_.

2. After discovering the nodes, create static groups for each Omnia functional group type supported in Omnia. For more information on groups and functional group support in Omnia, see :ref:`group-attributes-section` and :ref:`functional-groups`.

   - ``slurm_control_node_x86_64``
   - ``slurm_node_x86_64``
   - ``login_compiler_node_x86_64``
   - ``service_kube_control_plane_x86_64``
   - ``service_kube_node_x86_64``
   - ``slurm_node_aarch64``
   - ``login_node_aarch64``
   - ``login_compiler_node_aarch64``
   - ``os_aarch64``
   - ``os_x86_64``

   To create static groups in OME:
   
   a. In the left navigation menu, navigate to **CUSTOM GROUPS** > **Static Groups**
   b. Click the ellipsis (...) next to **Static Groups** and select **Create Group**
   c. Provide the group name exactly matching the functional group name
   d. Add a description for the group.
   e. Click **Finish**
   
   Repeat this process for each functional group type you plan to use in your Omnia deployment.

3. After creating the static groups for each functional group type, add the discovered nodes to the corresponding static groups. To add the devices to the static groups:

   a. Select the static functional group from the list.
   b. Click **Add Devices**.
   c. In the **Add Devices to Group <static group name>** dialog box, select the servers that belong to a specific functional group.
   d. Click **Finish**
   
   Repeat this process for all functional groups, ensuring each server is assigned to the correct static group based on its intended role in the Omnia cluster.

.. note:: When you run the discovery.yml playbook, devices that are not assigned to any Omnia-supported custom static group will be considered as ``slurm_node_aarch64`` in the auto-generated PXE mapping file.

4. After creating the static groups in OME, configure the ``discovery_config.yml`` file with OME connection details and discovery parameters. The following table lists the parameters for ``discovery_config.yml``:

.. csv-table:: discovery_config.yml
   :file: ../../Tables/discovery_config.csv
   :header-rows: 1
   :keepspace:

5. Execute the ``discovery.yml`` playbook with the ``discovery_mechanism=ome`` parameter to generate the PXE mapping file automatically::

    ssh omnia_core
    cd /omnia/discovery
    ansible-playbook discovery.yml -e "discovery_mechanism=ome"

The ``discovery.yml`` file will automatically create the PXE mapping file in the ``/opt/omnia/input/project_default/`` directory. For example **bmc_pxe_mapping_file_<timestamp>.csv** with the discovered nodes from OME. The user can verify and edit the mapping file if necessary.

BMC Discovery Report
-------------------

The BMC Discovery Report is a CSV file generated automatically at the end of the OME (OpenManage Enterprise) server discovery process. It provides a consolidated view of all discovered servers along with the link status of each NIC type (BMC, Ethernet, and InfiniBand), enabling administrators to quickly identify connectivity issues before provisioning.

The report is generated alongside the existing PXE mapping file and shares the same timestamp for easy correlation.

Report Generation
~~~~~~~~~~~~~~~~

The discovery report is generated automatically when the discovery playbook runs::

    ansible-playbook discovery.yml -e "discovery_mechanism=ome"

The report is created after the PXE mapping file as the final step in the OME discovery workflow:

1. **Get OME credentials** — Authenticate with OpenManage Enterprise
2. **Collect server inventory** — Query OME for all discovered servers and their NIC details
3. **Generate PXE mapping file** — Create the PXE mapping CSV for provisioning
4. **Generate BMC discovery report** — Create the discovery report CSV with NIC link statuses

Output File Location
~~~~~~~~~~~~~~~~~~~

The report is saved to::

    /opt/omnia/discovery/bmc_discovery_report_<timestamp>.csv

Where ``<timestamp>`` is in ``YYYYMMDDTHHMMSS`` format (e.g., ``20260601T120000``), matching the PXE mapping file timestamp.

The PXE mapping file is saved to::

    /opt/omnia/input/<project_name>/bmc_pxe_mapping_file_<timestamp>.csv

Report Columns
~~~~~~~~~~~~~~

The discovery report CSV contains the following columns:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Column
     - Description
   * - ``SERVICE_TAG``
     - Dell service tag uniquely identifying the server.
   * - ``BMC_MAC``
     - MAC address of the BMC (iDRAC) network interface.
   * - ``BMC_IP``
     - IP address assigned to the BMC (iDRAC).
   * - ``BMC_NIC_STATUS``
     - Link status of the BMC NIC. Typically ``Up`` if the server is managed by OME.
   * - ``ETHERNET_NIC_MAC``
     - MAC address of the first Ethernet NIC (excluding iDRAC and InfiniBand NICs).
   * - ``ETHERNET_NIC_LINK_STATUS``
     - Link status of the Ethernet NIC (e.g., ``Up``, ``Unknown``, ``Down``).
   * - ``IB_NIC_NAME``
     - FQDD (Fully Qualified Device Descriptor) of the InfiniBand NIC port (e.g., ``InfiniBand.Slot.3-1``). Empty if no InfiniBand NIC is present.
   * - ``IB_NIC_LINK_STATUS``
     - Link status of the InfiniBand NIC (e.g., ``Up``, ``Unknown``, ``Down``). Empty if no InfiniBand NIC is present.

Sample Output
~~~~~~~~~~~~

.. code-block:: text

    SERVICE_TAG,BMC_MAC,BMC_IP,BMC_NIC_STATUS,ETHERNET_NIC_MAC,ETHERNET_NIC_LINK_STATUS,IB_NIC_NAME,IB_NIC_LINK_STATUS
    H94M8F3,B8:CE:F6:57:89:D0,172.16.0.101,UP,b0:7b:25:d8:4a:f4,Up,InfiniBand.Slot.3-1,Unknown
    J7KN2G4,A4:BF:01:12:34:56,172.16.0.102,UP,e4:43:4b:01:23:45,Up,,
    K5LP9H2,D0:94:66:AB:CD:EF,172.16.0.103,UP,24:6e:96:78:90:12,Unknown,InfiniBand.Slot.3-1,Up

NIC Link Statuses
~~~~~~~~~~~~~~~~

The report captures three categories of NIC link status:

**BMC NIC Status**

The BMC NIC status indicates whether the iDRAC is reachable from OME. Since OME manages the server, this is typically ``Reachable``.

**Ethernet NIC Link Status**

The Ethernet NIC link status reflects the physical link state of the first non-iDRAC, non-InfiniBand network port:

- **Up** — Cable connected and link established
- **Down** — No link detected (cable disconnected or switch port down)
- **Unknown** — iDRAC cannot determine the link state. This can occur when the NIC firmware has not been initialized or the server is powered off

.. note::

   When all Ethernet NICs report ``Unknown`` status, Omnia selects the first available Ethernet NIC as a fallback. InfiniBand NICs are never selected as the Ethernet/admin NIC.

**InfiniBand NIC Link Status**

The InfiniBand NIC link status reflects the state of the IB port:

- **Up** — InfiniBand link is active
- **Down** — No InfiniBand link detected
- **Unknown** — iDRAC reports the link state as unknown. This is common for InfiniBand NICs even when they are active at the OS level, as iDRAC may not have full visibility into InfiniBand link state

.. note::

   InfiniBand NIC selection uses a priority-based fallback: ``Up`` is preferred, followed by ``Unknown``, then ``Down``. This ensures an IB NIC is reported even when iDRAC cannot determine its link state.

Use Cases
~~~~~~~~~

**Pre-provisioning Health Check**

Before running ``provision.yml``, review the discovery report to verify:

- All servers have valid BMC IPs and MAC addresses
- Ethernet NICs are in ``Up`` state (required for PXE boot)
- InfiniBand NICs are detected on servers that require IB connectivity

**Troubleshooting NIC Connectivity**

If a server fails to PXE boot during provisioning:

1. Check the ``ETHERNET_NIC_LINK_STATUS`` in the discovery report
2. If the status is ``Down`` or ``Unknown``, verify the physical cable connection and switch port configuration
3. If the ``ETHERNET_NIC_MAC`` appears incorrect, check if InfiniBand NICs were incorrectly selected (this was fixed in Omnia)

**Inventory Auditing**

The report serves as a point-in-time snapshot of the cluster's NIC inventory, useful for:

- Verifying InfiniBand fabric connectivity across all nodes
- Tracking which servers have IB NICs installed
- Auditing MAC addresses for network security compliance

Relationship to PXE Mapping File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The discovery report and PXE mapping file are complementary:

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Attribute
     - PXE Mapping File
     - Discovery Report
   * - **Purpose**
     - Input for provisioning
     - Diagnostic and auditing
   * - **Editable**
     - Yes (user edits hostnames, groups)
     - No (read-only reference)
   * - **Contains NIC link status**
     - No
     - Yes
   * - **Contains IP assignments**
     - Yes (ADMIN_IP, BMC_IP, IB_IP)
     - Yes (BMC_IP only)
   * - **Contains hostnames**
     - Yes
     - No
   * - **Used by provision.yml**
     - Yes
     - No

Configuration
~~~~~~~~~~~~

The discovery report uses the following configuration variables defined in the OME discovery role:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Variable
     - Description
   * - ``discovery_report_dir``
     - Directory where the report is saved. Default: ``/opt/omnia/discovery``
   * - ``discovery_report_file``
     - Base file path for the report (timestamp is appended at runtime).

These variables are defined in ``discovery/roles/ome_discovery/vars/main.yml``.

Completion Message
~~~~~~~~~~~~~~~~~~

After discovery completes, a summary message is displayed with paths to both output files::

    ============================================================
    OME Discovery Complete
    ============================================================
    BMC PXE mapping file generated: /opt/omnia/input/project_default/bmc_pxe_mapping_file_20260601T120000.csv
    BMC discovery report generated: /opt/omnia/discovery/bmc_discovery_report_20260601T120000.csv
      (Lists link status of BMC, Ethernet, and InfiniBand NICs for each server)
    Total servers discovered: 10

    Next Steps:
    1. Review and edit the generated PXE mapping file.
    2. Review the discovery report for NIC link statuses.
    3. Update HOSTNAME, FUNCTIONAL_GROUP_NAME, GROUP_NAME as needed.
    4. Update pxe_mapping_file_path in provision_config.yml.
    5. Run: ansible-playbook provision/provision.yml
    ============================================================


.. _group-attributes-section:

Groups
------

Nodes that are located in the same place or similar hardware can be grouped together. To do so, update the mapping file with all necessary attributes for the nodes, based on their role within the cluster. Each group will have following attributes as indicated in the table below:


.. csv-table:: Group attributes
   :file: ../../Tables/group_attributes.csv
   :header-rows: 1
   :keepspace:

.. _functional-groups:

Functional Groups
------------------------

Nodes with similar functional roles or functionalities can be grouped together. The following table lists the functional groups available in Omnia.

.. note:: 
    
    * At least one functional group is mandatory, and you must not change the name of functional groups.
    * Ensure that the group nodes intended for a specific role must be associated with the corresponding functional group and must not be associated under multiple functional groups.
    * The functional groups are case-sensitive.
    * Omnia supports HA functionality for the ``service_cluster``. For more information, `click here <HighAvailability/index.html>`_.
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
| os_x86_64                               | default_packages.json, ldms.json                                                     |
+-----------------------------------------+--------------------------------------------------------------------------------------+
| os_aarch64                              | default_packages.json, ldms.json                                                     |
+-----------------------------------------+--------------------------------------------------------------------------------------+

.. note::
    The ``os_x86_64`` and ``os_aarch64`` functional groups support optional additional packages via ``additional_packages.json`` files. Create these files in ``input/config/{arch}/rhel/10.0/`` to include custom packages like ``podman``, diagnostic tools, or monitoring agents. If no additional packages are needed, the images build successfully with the standard package.




   



