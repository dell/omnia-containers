Step 9: Create Local Repositories for the Cluster
==================================================

The ``local_repo.yml`` playbook, invoked from inside the ``omnia_core`` container, downloads all the software packages to the Pulp container and facilitates air-gapped installation (without access to public network) on the cluster nodes. The **Pulp container**, set up on an NFS share, acts as a centralized storage unit and hosts all software packages and images required and supported by Omnia. These packages or images are then accessed by the cluster nodes from that NFS share.

Once the Pulp container is ready, you can provide inputs in the ``/opt/omnia/input/project_default/software_config.json`` and ``/opt/omnia/input/project_default/local_repo_config.yml`` files. Based on these inputs, the required packages or images are accessed from the container and downloaded to the cluster nodes (without Internet access).

.. toctree::
    Prerequisite
    InputParameters    
    localrepos
    RunningLocalRepo
    AdminDebugPackages

