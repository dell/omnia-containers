Prerequisites
===============

For the ``local_repo.yml`` playbook to work seamlessly, ensure that the following prerequisites have been met before playbook execution:

1. Ensure that the ``omnia_core``and ``pulp`` containers are up and running.
2. The OIM should have access to the public network, in order to download and store the packages/images to the desired NFS share.
3. Ensure that all required certificates are stored using **Ansible Vault** to ensure complete confidentiality and integrity within the cluster.
4. Ensure that the repository URLs for the software packages are accessible. If not, the download will fail for that specific package.
5. By default, an active RHEL subscription may configure the repository to RHEL 10.1. However, for proper execution, Omnia requires the repository to be set to RHEL 10.0. Before starting the Omnia deployment, verify the current repository setting and, if needed, adjust it to RHEL 10.0.
    
    Command Examples:

        1. Check the current RHEL release setting ::

            subscription-manager release --show

        2. Set the RHEL release to 10.0 ::

            sudo subscription-manager release --set=10.0

