Prerequisites
=================

* If you want to use OpenManage Enterprise (OME) for PXE mapping file generation, you must first discover the cluster nodes in OME and create static functional groups. For detailed procedures on OME discovery and static group creation, refer to :ref:`ome_pxe_generation` in :doc:`../composable_roles`.

* All target bare-metal servers (cluster nodes) should be reachable from the OIM.

* The UEFI boot setting should be configured in the BIOS settings before initiating PXE boot on the nodes.

* Manually configure the Admin and BMC network switches before running the provision tool. 

* Ensure that the external NFS is accessible by all the nodes intended to be booted and is reachable by admin network. 

* Set the IP address of the OIM. The OIM NIC connected to remote servers (through the switch) should be configured with two IPs (BMC IP and admin IP) in a shared LOM or hybrid set up. In the case dedicated network topology, a single IP (admin IP) is required.

    .. figure:: ../../../images/ControlPlaneNic.png

                *OIM NIC IP configuration in a LOM setup*

    .. figure:: ../../../images/ControlPlane_DedicatedNIC.png

                *OIM NIC IP configuration in a dedicated setup*

* To provision the bare metal servers, ensure the images are built using the ``build_image_x86_64.yml`` or ``build_image_aarch64.yml``.

* Ensure that all connection names under the network manager match their corresponding device names.

    To verify network connection names: ::

            nmcli connection

    To verify the device name: ::

             ip link show

    In the event of a mismatch, edit the file ``/etc/sysconfig/network-scripts/ifcfg-<nic name>`` using the vi editor.

* When discovering nodes via mapping files, all cluster nodes should be set up in PXE mode before running the playbooks.

.. note::

    * After the cluster has been configured and deployed, changing the OIM node is not supported. If you need to change the OIM node, you must redeploy the entire cluster.
   








