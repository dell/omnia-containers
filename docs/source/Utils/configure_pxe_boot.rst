.. _set-pxe-boot-order:

Configure PXE Boot
==================

When PXE boot order is set on a node in Omnia, the node automatically retrieves and boots into the diskless image provided by the Omnia Infrastructure Manager (OIM). To configure PXE boot for nodes after they are provisioned with the Provision.yml playbook, do the following:

.. warning::
   This playbook will restart your servers and power them on if they are off. Any unsaved data will be lost.

Prerequisites
-------------

1. Dell iDRAC BMCs must be reachable from the Omnia Infrastructure Manager (OIM).
2. PXE boot order must be set/enabled in the BIOS/UEFI settings of the target nodes.
3. PXE support must be enabled in the NIC firmware.
4. iDRAC firmware must support the Boot Source Override API (iDRAC9 and later).
5. The OIM server providing the PXE boot image must be reachable by the target nodes.

Inventory Setup
---------------

Generate the inventory file based on the mapping file. 

.. note:: The inventory must contain a ``bmc`` group with at least one BMC IP address. 

For the sample map and inventory files, see :doc:`Sample Files <../OmniaInstallGuide/samplefiles>`.

Example inventory::

        [bmc]
        172.17.107.43
        172.17.107.44
        172.17.107.43

Running the Playbook
--------------------

The ``set_pxe_boot.yml`` playbook supports two execution modes:

**Mode 1: With Inventory File**

Run the playbook with an inventory file to configure PXE boot for specific nodes::

    ssh omnia_core
    cd /omnia/utils
    ansible-playbook set_pxe_boot.yml -i inventory

**Mode 2: Without Inventory File**

Run the playbook without an inventory file to configure PXE boot for all nodes in the mapping file::

    ssh omnia_core
    cd /omnia/utils
    ansible-playbook set_pxe_boot.yml

