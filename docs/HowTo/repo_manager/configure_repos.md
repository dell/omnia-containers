# Create Local Repositories

The repo_manager domain downloads all software packages to the Pulp container and facilitates
air-gapped installation (without access to a public network) on the cluster
nodes. The Pulp container, set up on an NFS share, acts as a centralized
storage unit and hosts all software packages and images required and supported
by Omnia. These packages or images are then accessed by the cluster nodes from
that NFS share.

## Overview

The repo_manager domain (collection: `omnia.repo_manager` v3.0.0) deploys an HTTPS Pulp content server and synchronizes catalog content for offline Omnia clusters. It supports RPM repositories and packages, container images, Python packages, files and source artifacts for `x86_64` and `aarch64`.

Once the Pulp container is ready, you provide inputs in the following files:

- `/opt/omnia/repo_manager/input/project_default/software_config.json`
- `/opt/omnia/repo_manager/input/project_default/repo_manager_config.yml`
- `/opt/omnia/repo_manager/input/project_default/repo_manager_endpoint_config.yml`

Based on these inputs, the required packages or images are accessed from the
container and downloaded to the cluster nodes (without Internet access).

With `repo_config` set to `always` in `software_config.json`, all images and
artifacts will be downloaded to the Pulp container present on the NFS share,
and the OIM serves as the default Pulp registry.

## Prerequisites

- The [Setup the OIM](../main/setup_oim.md) procedure is complete (main domain setup is complete).
- The [Initialize Domains](../main/initialize_domains.md) procedure is complete (repo_manager domain is initialized).
- The OIM has access to the public network, in order to download and store
  packages/images to the desired NFS share.
- All required certificates are stored using Ansible Vault to ensure complete
  confidentiality and integrity within the cluster.
- All repository URLs for the software packages are accessible. If not, the
  download will fail for that specific package.
- By default, an active RHEL subscription may configure the repository to
  RHEL 10.1. However, Omnia requires the repository to be set to **RHEL 10.0**.
  Before starting, verify and adjust:

   ```bash title="Run on: OIM host"
   subscription-manager release --show
   sudo subscription-manager release --set=10.0
   ```

- The [Configure Inputs](../main/configure_inputs.md) procedure is complete
  (`software_config.json`, `repo_manager_config.yml`, and `repo_manager_endpoint_config.yml` are configured).

## Procedure

1. **Initialize the repo_manager domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh -i repo_manager
    ```

    This stages input files and installs dependencies.

2. **Verify software_config.json is configured** with the desired software
   stacks:

    ```bash title="Run on: OIM host"
    cat /opt/omnia/repo_manager/input/project_default/software_config.json | python3 -m json.tool
    ```

    Confirm the `softwares` list includes all packages you need (e.g.,
    `service_k8s`, `slurm_custom`, `openldap`, `openmpi`, `ucx`,
    `csi_driver_powerscale`).

3. **Run the repo_manager domain**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run repo_manager --tags execute
    ```

    The domain will:

    - Download and save software packages/images to the Pulp container.
    - All cluster nodes can then access these packages from the Pulp container.

    !!! warning

        Initial synchronization can take a significant amount of time depending
        on the number of repositories, internet bandwidth, and selected software
        stacks. CUDA repositories are particularly large.

4. **Check the status report** after execution:

    After the repo_manager domain has been executed, a status report is displayed
    containing the status for each downloaded package along with the complete
    domain execution time:

    - **SUCCESS**: The package has been successfully downloaded to the Pulp container.
    - **FAILED**: The package couldn't be downloaded successfully.

!!! note

    - The repo_manager domain execution fails if any software package
      has a **FAILED** status. In such a scenario, re-run the repo_manager domain.
    - If any software package fails to download, other scripts/domains that
      rely on the package may also fail.
    - To download additional software packages, update
      `/opt/omnia/repo_manager/input/project_default/software_config.json` with the new
      software information and re-run the repo_manager domain.


### Metadata Report

After a successful execution of the repo_manager domain, a metadata file called
`localrepo_metadata.yml` is created under `/opt/omnia/repo_manager/offline_repo/.data/`.
This file captures the `repo_config` (`always`, `partial`) details provided
during domain execution. If the repo_manager domain is re-run, it compares the
current repository policy with the previously captured metadata:

- **If a change in policy is detected**, the system displays a warning:

   ```
   WARNING: Metadata has changed since last run. Execution may fail if there
   is no internet on OIM. Proceeding automatically in 15 seconds...
   ```

   The domain pauses for 15 seconds and then continues automatically. After
   successful execution, the metadata file is updated with the new policy.

- **If there is no change in policy**, the domain proceeds without prompting.


## Advanced Configuration

For advanced configuration options, see:

- [Add Additional Packages](adding_additional_packages.md) -- Add new software packages
- [Add Additional Repositories](adding_additional_repositories.md) -- Add new repositories
- [Configure Specific Software](configuring_specific_software.md) -- Configure specific software packages
- [Configure Default Packages and Admin Debug Packages](default_packages.md) -- Configure system and debug packages
- [Update Local Repositories](updating_local_repositories.md) -- Update after JSON changes
- [Resync Local Repositories](local_repository_resync.md) -- Resync repositories with remote sources


## Output Contract

After successful execution, the repo_manager domain produces the following output contract:

| Output | Location | Purpose |
|--------|----------|---------|
| `repo_status.yml` | `/opt/omnia/repo_manager/output/<project>/repo_status.yml` | Pulp URLs, repositories, file content and certificate paths for downstream consumers |
| Package/group state | `/opt/omnia/repo_manager/log/<os>/<version>/<arch>/` | Per-group CSV and worker results |
| Mirror indexes | `/opt/omnia/repo_manager/log/<os>/<version>/mirror_status/` | Composite catalog and Pulp mirror state |

### repo_status.yml Structure

The `repo_status.yml` file contains:

- HTTPS repository URLs for RPM repositories
- Container registry URLs for OCI images
- File content URLs for additional artifacts
- Certificate paths for HTTPS trust
- Repository status and availability information

This contract is consumed by:
- **image_build_manager** - For accessing OS images and container artifacts
- **Cluster workflows** - For package installation during provisioning
- **Administrators** - For manual repository access and verification


## Verification

Verify that local repositories were synced successfully:

```bash title="Run on: OIM host"
pulp rpm distribution list
```

Confirm that each expected repository distribution is listed and accessible.

## Next Steps


- [Build Cluster Images](../image_build_manager/build_images.md) -- Build OS boot images using the local repos.
- [Discover Nodes](../discovery/discover_nodes.md) -- Discover and PXE-boot target nodes.

## Troubleshooting

- **repo_manager domain fails with FAILED status for a package**: Re-run `repo_manager domain`. If the failure persists, verify that the repository URL is accessible and the package exists in the remote repository.
- **Pulp sync takes too long or times out**: Check network bandwidth and connectivity from the OIM to the remote repositories. CUDA repositories are particularly large.
- **Metadata warning about policy change**: This is expected when switching between `always` and `partial` policies. The domain proceeds automatically after 15 seconds.































