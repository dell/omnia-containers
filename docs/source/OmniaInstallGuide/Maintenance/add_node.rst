Add or Remove Slurm Nodes to the Cluster
========================================

Omnia supports addition and removal of Slurm compute nodes from an existing cluster. 

Add Slurm Node to the Cluster
-----------------------------

To add a new Slurm node to the cluster, follow these steps:

1. Update the PXE mapping file with new Slurm node entries. Add entries for new nodes with appropriate functional group assignments ``slurm_node_x86_64``.

.. Note:: While updating the mapping file, ensure that the existing nodes are not removed from the mapping file.

.. note:: Addition of new ``slurm_control_node`` is not supported.

2. Run the ``discovery.yml`` playbook to discover the new nodes. For more information, see :doc:`../RHEL_new/Provision/installprovisiontool`.
3. PXE boot the newly added nodes.
4. To enable telemetry collection using iDRAC telemetry service, run the ``telemetry.yml`` playbook. For steps to initiate telemetry collection, see :doc:`../RHEL_new/Telemetry/initialize_and_verify_telemetry`

.. note:: You do not need to run the ``telemetry.yml`` playbook if the service kubernetes cluster nodes are configured to collect telemetry data only using LDMS. By default, LDMS begins collection of data
    after ``discovery.yml`` playbook is executed.

Remove Slurm nodes
-----------------------

To remove a Slurm node from the cluster, follow these steps:

1. Update the PXE mapping file. Remove or reassign nodes that should no longer be part of the Slurm cluster.
2. Run the ``discovery.yml`` playbook.



