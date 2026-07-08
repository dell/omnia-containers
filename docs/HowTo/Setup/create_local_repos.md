
# Create Local Repositories


The `local_repo.yml` playbook, invoked from inside the `omnia_core` container,
downloads all software packages to the Pulp container and facilitates
air-gapped installation (without access to a public network) on the cluster
nodes. The Pulp container, set up on an NFS share, acts as a centralized
storage unit and hosts all software packages and images required and supported
by Omnia. These packages or images are then accessed by the cluster nodes from
that NFS share.

## Overview


Once the Pulp container is ready, you provide inputs in the following files:

- `/opt/omnia/input/project_default/software_config.json`
- `/opt/omnia/input/project_default/local_repo_config.yml`

Based on these inputs, the required packages or images are accessed from the
container and downloaded to the cluster nodes (without Internet access).

With `repo_config` set to `always` in `software_config.json`, all images and
artifacts will be downloaded to the Pulp container present on the NFS share,
and the OIM serves as the default Pulp registry.


## Prerequisites


- The [Prepare OIM](prepare_oim.md) procedure is complete (`omnia_core` and `pulp` containers are running).
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

- The [Configure Inputs](configure_inputs.md) procedure is complete
  (`software_config.json` and `local_repo_config.yml` are configured).


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Verify software_config.json is configured** with the desired software
   stacks:

   ```bash title="Run on: omnia_core container"
   cat /opt/omnia/input/project_default/software_config.json | python3 -m json.tool
   ```


   Confirm the `softwares` list includes all packages you need (e.g.,
   `service_k8s`, `slurm_custom`, `openldap`, `openmpi`, `ucx`,
   `csi_driver_powerscale`).

3. **Run the local_repo playbook**:

   ```bash title="Run on: omnia_core container"
   cd /omnia/local_repo
   ansible-playbook local_repo.yml
   ```


   The playbook will:

   - Download and save software packages/images to the Pulp container.
   - All cluster nodes can then access these packages from the Pulp container.

!!! warning

    Initial synchronization can take a significant amount of time depending
    on the number of repositories, internet bandwidth, and selected software
    stacks. CUDA repositories are particularly large.

4. **Check the status report** after execution:

   After `local_repo.yml` has been executed, a status report is displayed
   containing the status for each downloaded package along with the complete
   playbook execution time:

   - **SUCCESS**: The package has been successfully downloaded to the Pulp container.
   - **FAILED**: The package couldn't be downloaded successfully.

!!! note

    - The `local_repo.yml` playbook execution fails if any software package
      has a **FAILED** status. In such a scenario, re-run the `local_repo.yml`
      playbook.
    - If any software package fails to download, other scripts/playbooks that
      rely on the package may also fail.
    - To download additional software packages, update
      `/opt/omnia/input/project_default/software_config.json` with the new
      software information and re-run `local_repo.yml`.


## Metadata Report


After a successful execution of `local_repo.yml`, a metadata file called
`localrepo_metadata.yml` is created under `/opt/omnia/offline_repo/.data/`.
This file captures the `repo_config` (`always`, `partial`) details provided
during playbook execution. If `local_repo.yml` is re-run, it compares the
current repository policy with the previously captured metadata:

- **If a change in policy is detected**, the system displays a warning:

   ```
   WARNING: Metadata has changed since last run. Execution may fail if there
   is no internet on OIM. Proceeding automatically in 15 seconds...
   ```

   The playbook pauses for 15 seconds and then continues automatically. After
   successful execution, the metadata file is updated with the new policy.

- **If there is no change in policy**, the playbook proceeds without prompting.


## Configuring Specific Software


To include specific software, add the corresponding entry under `softwares`
in `software_config.json`:

| Software | Entry | Notes |
| --- | --- | --- |
| Kubernetes | `{"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]}` | Only the specified version is supported. |
| Slurm | `{"name": "slurm_custom", "arch": ["x86_64", "aarch64"]}` | Provide the corresponding repository in `user_repo_url_<arch>` of `local_repo_config.yml`. |
| OpenLDAP | `{"name": "openldap", "arch": ["x86_64"]}` | |
| OpenMPI | `{"name": "openmpi", "version": "5.0.8", "arch": ["x86_64"]}` | If you change the version, update `openmpi.json` in the config directory as well. |
| UCX | `{"name": "ucx", "version": "1.19.0", "arch": ["x86_64"]}` | |
| Dell CSI PowerScale | `{"name": "csi_driver_powerscale", "version": "v2.17.0", "arch": ["x86_64"]}` | |


## Default Packages and Admin Debug Packages


The `softwares` list in `software_config.json` supports two foundational
package entries:

- **`default_packages`** (Mandatory) -- Installs essential system packages and
  core dependencies required for basic Omnia cluster operation. This entry
  **must always** be present in the `softwares` list.

   ```json
   {"name": "default_packages", "arch": ["x86_64", "aarch64"]}
   ```

- **`admin_debug_packages`** (Optional) -- Installs debugging, profiling,
  and development tools (e.g., `gdb`, `strace`, `valgrind`, `gcc`, `perf`)
  on the cluster nodes. To enable, add the following entry to the `softwares`
  list:

   ```json
   {"name": "admin_debug_packages", "arch": ["x86_64", "aarch64"]}
   ```

The full list of packages included in each entry is defined in the
corresponding JSON files located at
`/opt/omnia/input/project_default/config/<architecture>/rhel/10.0/`.

!!! note

    - `default_packages` is mandatory and must not be removed from the
      `softwares` list.
    - Deploying `admin_debug_packages` increases the size of the local
      repository and requires additional disk space.
    - The accepted software names are taken from
      `/opt/omnia/input/project_default/config/<architecture>/<cluster_os_type>/<cluster_os_version>`.


## Updating Local Repositories after Modifying JSON Files


After `local_repo.yml` execution is complete, any modifications to a
`<software_name>.json` file (e.g., `service_k8s.json`, `slurm_custom.json`,
`additional_software.json`) will **not** be reflected automatically. Re-run the
playbook:

```bash title="Run on: omnia_core container"
ansible-playbook local_repo.yml
```


## Local Repository Resync


The Local Repository Resync feature updates the local RPM repositories by
synchronizing them with their respective remote sources. During
resynchronization, new and updated RPM packages are downloaded, repository
metadata is refreshed, and only incremental changes are fetched while
preserving the existing local cache.

**Resync all RPM repositories:**

```bash title="Run on: omnia_core container"
ansible-playbook local_repo.yml -e "resync_repos=all"
```

**Resync a specific RPM repository:**

```bash title="Run on: omnia_core container"
ansible-playbook local_repo.yml -e "resync_repos=x86_64_rhel_10.0_epel"
```

!!! note

    - Use `all` to resync all configured RPM repositories.
    - Specify the exact RPM repository name for targeted resync.
    - Existing RPM packages remain available during sync.
    - Logs are created in `/opt/omnia/log/local_repo/`.


## Log Files


The `local_repo.yml` playbook generates two types of log files:

1. **`standard.log`**: Located in `/opt/omnia/log/local_repo/<cluster_os_type>/<cluster_os_version>/`,
   contains the overall status of `local_repo.yml` execution.
2. **Package-based logs**: Each package download has its own log file at
   `/opt/omnia/log/local_repo/<cluster_os_type>/<cluster_os_version>/<arch_type>/<sw_name>/logs/`.

!!! note

    To view status of each software in `.csv` format, navigate to
    `/opt/omnia/log/local_repo/<cluster_os_type>/<cluster_os_version>/status.csv`.


## Next Steps


- [Build Cluster Images](build_cluster_images.md) -- Build OS boot images using the local repos.
- [Discover Nodes](discover_nodes.md) -- Discover and PXE-boot target nodes.


