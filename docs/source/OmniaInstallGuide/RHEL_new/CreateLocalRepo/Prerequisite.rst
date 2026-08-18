Prerequisites
===============

For the ``local_repo.yml`` playbook to work seamlessly, ensure that the following prerequisites have been met before playbook execution:

1. Ensure that the ``omnia_core`` container is up and running.
2. The OIM should have access to the public network, in order to download and store the packages/images to the desired NFS share.
3. Ensure that all required certificates are stored using **Ansible Vault** to ensure complete confidentiality and integrity within the cluster.
4. Ensure that the repository URLs for the software packages are accessible. If not, the download will fail for that specific package.
5. By default, an active RHEL subscription may configure the repository to RHEL 10.1. However, for proper execution, Omnia requires the repository to be set to RHEL 10.0. Before starting the Omnia deployment, verify the current repository setting and, if needed, adjust it to RHEL 10.0.
    
    Command Examples:

        1. Check the current RHEL release setting ::

            subscription-manager release --show

        2. Set the RHEL release to 10.0 ::

            sudo subscription-manager release --set=10.0

.. important:: **Slurm Version Pinning Workaround**
    
    EPEL repositories now ship **Slurm 26.x** packages. This conflicts with the **Slurm 25.05.2** packages expected by Omnia v2.1.0.0. Before running Step 9 (Create Local Repositories), you must replace the contents of ``slurm_custom.json`` on both architecture paths to pin Slurm packages to version 25.05.2.
    
    **Affected Files:**
    
    * ``/opt/omnia/input/project_default/config/x86_64/rhel/10.0/slurm_custom.json``
    * ``/opt/omnia/input/project_default/config/aarch64/rhel/10.0/slurm_custom.json``
    
    For detailed instructions and the complete JSON content to use, see `Slurm Version Pinning Workaround <SlurmVersionPinningWorkaround.html>`_.
    
    Failure to apply this fix may result in version mismatch and installation failures during `Step 11: Set up Slurm on nodes <../OmniaCluster/BuildingCluster/install_slurm.html>`_. For troubleshooting steps if you encounter version issues, see `Slurm Version Mismatch (26.x vs 25.05.2) <../../../../troubleshootingguide.html#slurm-version-mismatch-26-x-vs-25-05-2>`_ in the Troubleshooting Guide.

