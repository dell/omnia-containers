Discover Devices in OpenManage Enterprise and Create Static Groups
=====================================================================

This section provides detailed procedures for discovering Omnia cluster nodes in OpenManage Enterprise (OME), creating static functional groups to generate PXE mapping files for Omnia provisioning.

Prerequisites
-------------

Before proceeding with OME discovery, ensure the following:

- OpenManage Enterprise is installed and accessible
- All target servers have iDRAC configured with network connectivity
- OME has discovered the devices (servers are visible in OME inventory)
- You have administrative access to OME
- Ensure that servers have the correct NIC order and configuration to match your intended IP assignment scheme. When Omnia performs OME-based discovery, it uses the following NIC selection logic:
  
  - **Admin IP**: The first discoverable NIC (typically the first Ethernet interface) will be used to generate the admin IP address in the PXE mapping file
  - **InfiniBand IP**: The first discoverable InfiniBand NIC will be used to generate the InfiniBand IP address in the PXE mapping file.
  
Procedure 
-----------
1. In OpenManage Enterprise, discover the cluster nodes that you want to provision with Omnia. For more information on discovering devices in OME, see the `OpenManage Enterprise User Guide <https://dl.dell.com/content/manual4/en/openmanage-enterprise-user-guide-en>`_.

2. After discovering the nodes, create static groups for each Omnia functional group type supported in Omnia:

   - ``slurm_control_node_x86_64``
   - ``slurm_node_x86_64``
   - ``login_compiler_node_x86_64``
   - ``service_kube_control_plane_x86_64``
   - ``service_kube_node_x86_64``
   - ``slurm_node_aarch64``
   - ``login_node_aarch64``
   - ``login_compiler_node_aarch64``
   - ``os_aarch64``

   To create static groups in OME:
   
   a. In the left navigation menu, navigate to **CUSTOM GROUPS** > **Static Groups**
   b. Click the ellipsis (...) next to **Static Groups** and select **Create Group**
   c. Provide the group name exactly matching the functional group name
   d. Add a description for the group
   e. Click **Finish**
   
   Repeat this process for each functional group type you plan to use in your Omnia deployment.

3. After creating the static groups for each functional group type, add the discovered nodes to the corresponding static groups. To add the devices to the static groups:

   a. Select the static functional group from the list.
   b. Click **Add Devices**.
   c. In the **Add Devices to Group <static group name>** dialog box, select the servers that belong to a specific functional group.
   d. Click **Finish**
   
   Repeat this process for all functional groups, ensuring each server is assigned to the correct static group based on its intended role in the Omnia cluster.

BMC Discovery Report
-------------------

The BMC Discovery Report is a CSV file generated automatically at the end of the OME (OpenManage Enterprise) server discovery process. It provides a consolidated view of all discovered servers along with the link status of each NIC type (BMC, Ethernet, and InfiniBand), enabling administrators to quickly identify connectivity issues before provisioning.

The report is generated alongside the existing PXE mapping file and shares the same timestamp for easy correlation.

Report Generation
~~~~~~~~~~~~~~~~

The discovery report is generated automatically when the discovery playbook runs::

    ansible-playbook discovery/discovery.yml

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
     - Link status of the BMC NIC. Typically ``Reachable`` if the server is managed by OME.
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
    H94M8F3,B8:CE:F6:57:89:D0,172.16.0.101,Reachable,b0:7b:25:d8:4a:f4,Up,InfiniBand.Slot.3-1,Unknown
    J7KN2G4,A4:BF:01:12:34:56,172.16.0.102,Reachable,e4:43:4b:01:23:45,Up,,
    K5LP9H2,D0:94:66:AB:CD:EF,172.16.0.103,Reachable,24:6e:96:78:90:12,Unknown,InfiniBand.Slot.3-1,Up

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
3. If the ``ETHERNET_NIC_MAC`` appears incorrect, check if InfiniBand NICs were incorrectly selected (this was fixed in Omnia — see `Known issues`_)

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

Known Issues
~~~~~~~~~~~~

**ADMIN_MAC incorrectly selecting InfiniBand MAC (fixed)**

In earlier versions, when all Ethernet NICs reported ``Unknown`` link status, the fallback logic could select an InfiniBand NIC MAC address as the ``ADMIN_MAC`` in the PXE mapping file. This has been fixed by explicitly excluding InfiniBand NICs from the Ethernet NIC search.

**Blank link status for UNKNOWN NICs (fixed)**

When OME returned a ``null`` or empty ``LinkStatus`` for NICs in an unknown state, the discovery report showed blank values instead of ``Unknown``. This has been fixed to default empty link statuses to ``Unknown``.

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

