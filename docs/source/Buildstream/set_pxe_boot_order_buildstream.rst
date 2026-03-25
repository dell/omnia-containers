.. _set-pxe-boot-order:

Step 6: PXE Boot the Nodes Using the PXE Boot Utility
=====================================================

After successful execution of the BuildStreaM pipeline, use the ``set_pxe_boot.yml`` playbook utility to configure PXE boot for the target nodes. This playbook restarts the nodes and automatically loads the diskless images on the nodes.

.. warning::
   The ``set_pxe_boot.yml`` playbook will restart your servers and power them on if they are off. Any unsaved data will be lost.

Prerequisites
---------------

* Dell iDRAC BMCs must be reachable from the Omnia Infrastructure Manager (OIM).
* PXE boot order must be set/enabled in the BIOS/UEFI settings of the target nodes.
* PXE support must be enabled in the NIC firmware.
* iDRAC firmware must support the Boot Source Override API (iDRAC9 and later).
* The TFTP/NFS/HTTP server providing the PXE boot image must be reachable by the target nodes.

Procedure
----------

1. Generate the inventory file based on the mapping file. 

.. note:: The inventory must contain a ``bmc`` group with at least one BMC IP address. 

For the sample map and inventory files, see :doc:`Sample Files <../OmniaInstallGuide/samplefiles>`.

Example inventory::

        [bmc]
        172.17.107.43
        172.17.107.44
        172.17.107.43

2. Run the ``set_pxe_boot.yml`` playbook to configure PXE boot and restart the nodes::

    ssh omnia_core
    cd /omnia/utils
    ansible-playbook set_pxe_boot.yml -i inventory

The playbook will:
- Restart the nodes
- Power them on if they are off
- Configure PXE boot order
- Load the diskless image provided by the Omnia Infrastructure Manager (OIM)

Next Steps
----------
(Optional) Initialize telemetry collection for the nodes. See :doc:`buildstream_telemetry` for detailed instructions.


