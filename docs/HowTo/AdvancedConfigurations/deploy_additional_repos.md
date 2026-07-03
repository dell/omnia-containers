
# Deploy Additional Repositories


This section explains how to add extra RPM repositories to the Omnia local
repository so that packages can be installed ad-hoc on compute nodes.


## Overview


Packages from these repositories are intended for ad-hoc installation on
compute nodes using `dnf install` and are not used during image builds
through `additional_packages.json`.


## Prerequisites


- Omnia Infrastructure Manager (OIM) is deployed and operational.
- The `local_repo_config.yml` file is configured. See
  [Local Repo Config](../../Reference/Configuration/local_repo_config.md).


## Steps


1. In the `local_repo_config.yml` file, add your repository URLs under the key that matches the node architecture:

   - `additional_repos_x86_64`
   - `additional_repos_aarch64`

2. Rerun the `local_repo.yml` playbook for Omnia to sync the repositories and update the repository configuration.

3. For first time deployment, do the following:

   - Build images: [Build Cluster Images](../Setup/build_cluster_images.md)
   - Discover nodes and PXE boot: [Discover Nodes](../Setup/discover_nodes.md)

4. If you are deploying after cluster provisioning, refresh metadata and install packages on compute nodes.

   ```bash title="Run on: compute node"
   sudo dnf clean all
   sudo dnf makecache
   sudo dnf install -y <package-name>
   ```


## Next Steps


- [Deploy Additional Packages](deploy_additional_packages.md) -- Deploy additional software packages and container images on cluster nodes.
- [Apptainer](use_apptainer.md) -- Pull and run container images using Apptainer.
