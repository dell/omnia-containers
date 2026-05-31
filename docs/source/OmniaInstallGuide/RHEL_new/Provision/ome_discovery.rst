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

