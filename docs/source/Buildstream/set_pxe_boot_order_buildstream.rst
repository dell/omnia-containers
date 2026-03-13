.. _set-pxe-boot-order:

Step 6: Set PXE Boot Order
==================

When PXE boot order is set on a node in Omnia, the node automatically retrieves and boots into the diskless image provided by the Omnia Infrastructure Manager (OIM).

Configure PXE Boot
------------------
To configure PXE boot for nodes after they are discovered with the ``discovery.yml`` playbook, do the following:

.. warning::
   This playbook will restart your servers and power them on if they are off. Any unsaved data will be lost.

Prerequisites
^^^^^^^^^^^^^

1. Dell iDRAC BMCs must be reachable from the Omnia Infrastructure Manager (OIM).
2. PXE boot order must be set/enabled in the BIOS/UEFI settings of the target nodes.
3. PXE support must be enabled in the NIC firmware.
4. The ``dellemc.openmanage`` Ansible collection must be installed.
5. iDRAC firmware must support the Boot Source Override API (iDRAC9 and later).
6. The TFTP/NFS/HTTP server providing the PXE boot image must be reachable by the target nodes.

Inventory Setup
^^^^^^^^^^^^^^^

Generate the inventory file based on the mapping file. 

.. note:: The inventory must contain a ``bmc`` group with at least one BMC IP address. 

For the sample map and inventory files, see :doc:`Sample Files <../OmniaInstallGuide/samplefiles>`.

Example inventory::

        [bmc]
        172.17.107.43
        172.17.107.44
        172.17.107.43

Running the Playbook
^^^^^^^^^^^^^^^^^^^^

Run the following command to configure PXE boot and restart the nodes::

    ssh omnia_core
    cd /omnia/utils
    ansible-playbook set_pxe_boot.yml -i inventory


Verification
------------

Troubleshooting
---------------