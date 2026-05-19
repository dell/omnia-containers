Re-provisioning the Cluster
=============================

In the event that an existing Omnia cluster needs a fresh installation, the cluster can be re-provisioned.

If you deploy the service kubernetes cluster or slurm cluster freshly, ensure that the NFS server share path used by slurm or service kubernetes cluster is cleared manually. The NFS details are available in ``storage_config.yml``.

•	To reuse the same ``server_share_path`` and ``client_share_path``, do the following:

        1.	Power off all servers except the OIM.
        2.	From the OIM, go to the ``client_share_path`` and delete all contents in the respective client share path.
        3.  Run the ``provision.yml`` playbook. 
        4.  PXE boot the required nodes to be reprovisioned.

•	To use the new ``server_share_path`` and ``client_share_path``, do the following:

        1.  Run the ``provision.yml`` playbook. 
        2.  PXE boot the required nodes to be reprovisioned.

Re-provision Existing Nodes without Any Modifications
------------------------------------------------------

To re-provision the existing nodes without any modifications, PXE boot the required nodes to be reprovisioned.

The OS is automatically installed on every PXE boot if there are no modification in the cluster.


Re-provision the Nodes with Modifications
------------------------------------------

1. Update the mapping file (for mapping file discovery) or ensure nodes are configured in OME (for OME-based provisioning), and update ``software_config.json`` as required.
2. In the event of any modification to the ``software_config.json``, run the ``local_repo.yml`` playbook, and then run the ``build_image_x86_64.yml`` or ``build_image_aarch64.yml`` to build the new images. For more information, see :doc:`../RHEL_new/CreateLocalRepo/RunningLocalRepo`.
3. After the images are created, run the ``provision.yml`` playbook. For OME-based provisioning, use::

    ssh omnia_core
    cd /omnia/provision
    ansible-playbook provision.yml

   For more information, see :doc:`../RHEL_new/Provision/installprovisiontool`.
4. PXE boot the required nodes to be reprovisioned.

.. note:: The entire cluster needs to be reprovisioned if you want to reprovision the Slurm Control node and Kube Control Plane.    