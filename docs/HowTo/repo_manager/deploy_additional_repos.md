
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
  [Local Repo Config](../../Reference/Configuration/repo_manager_config.md).


## Procedure


1. In the `local_repo_config.yml` file, add your repository URLs under the key that matches the node architecture:

   - `additional_repos_x86_64`
   - `additional_repos_aarch64`

2. Rerun the `local_repo.yml` playbook for Omnia to sync the repositories and update the repository configuration.

3. For first time deployment, do the following:

   - Build images: [Build Cluster Images](../image_build_manager/build_images.md)
   - Discover nodes and PXE boot: [Discover Nodes](../Setup/../discovery/discover_nodes.md)

4. If you are deploying after cluster provisioning, refresh metadata and install packages on compute nodes.

   ```bash title="Run on: compute node"
   sudo dnf clean all
   sudo dnf makecache
   sudo dnf install -y <package-name>
   ```


## Verification

After provisioning, verify the additional repositories are available on the target nodes:

```bash title="Run on: target node"
dnf repolist
```

## Troubleshooting

- **Additional repository not available on nodes**: Verify the repository URL is correct in `local_repo_config.yml` and re-run `local_repo.yml`.
- **Package installation fails from additional repository**: Confirm that the repository metadata is valid and the GPG key (if specified) is accessible.

## Next Steps


- [Deploy Additional Packages](../repo_manager/deploy_additional_packages.md) -- Deploy additional software packages and container images on cluster nodes.
- [Apptainer](../orchestrator/use_apptainer.md) -- Pull and run container images using Apptainer.



















