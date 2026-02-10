Deploy Additional Repositories
===============================

1. In the ``local_repo_config.yml`` file, add your repository URLs under the key that matches the node architecture:

- `additional_repos_x86_64`
- `additional_repos_aarch64`

2. Rerun the ``local_repo.yml`` playbook for Omnia to sync the repositories and update the repository configuration.
3. For first time deployment, do the following:

* Build images: `Step 12: Build Cluster Node Images <../RHEL_new/build_images.html>`_
* Discover nodes and PXE boot: `Step 13: Discover cluster nodes <../RHEL_new/Provision/index.html>`_

4. If you are deploying after cluster provisioning, refresh metadata and install packages on compute nodes. ::

    bash
    sudo dnf clean all
    sudo dnf makecache
    sudo dnf install -y <package-name>








