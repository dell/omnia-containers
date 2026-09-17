# Configure Custom UCX and OpenMPI

## Overview

Orchestrator places manual UCX and OpenMPI installation scripts on
login-compiler nodes during provisioning. The scripts download the catalog
artifacts from Repo Manager, compile them, and install the shared toolchain
under `/hpc_tools/benchmarks/`.

The generated cloud-init also configures the DOCA MPI environment as the
default stack. It does not automatically execute the custom UCX or OpenMPI
compilation scripts.

## Prerequisites

- Use a catalog whose applicable functional layers include `ucx_group` and
  `openmpi_group`, with the `ucx` and `openmpi` tarball components. Orchestrator
  derives support from catalog group names and the scripts download those
  tarballs from Repo Manager.
- Complete Repo Manager and confirm that `repo_status.yml` reports
  `overall_status: success`.
- Include a catalog-supported login-compiler functional group in the active
  project's `pxe_mapping_file.csv`. You can use a Discovery-style name such as
  `login_compiler_node_aarch64` or a matching catalog-qualified name; the
  bundled catalog provides `login_compiler_node_rhel_10_0_aarch64`.
- Set `slurm_cluster.nfs_storage_name` to a shared-storage entry in
  `storage_config.yml`. To use a separate VAST mount for HPC tools, set the
  optional `vast_storage_name` to that entry; when it is omitted or empty,
  Orchestrator reuses the `nfs_storage_name` entry. Provisioning binds the
  selected storage's `slurm/hpc_tools` directory to `/hpc_tools` on supported
  Slurm nodes.
- Ensure the selected catalog packages include the build dependencies needed
  by the source archives.
- Run the installation scripts as `root`; they write under `/etc/profile.d`
  and `/var/log` as well as the shared filesystem.

!!! caution

    The supplied installers use the same `/hpc_tools/compile` and
    `/hpc_tools/benchmarks` paths for both architectures. Do not run them for
    x86_64 and aarch64 against the same share. Use an architecture-specific
    share or install only one architecture with these scripts.

## Procedure

1. Synchronize the selected UCX and OpenMPI catalog content:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags "precheck,download,status"
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags "precheck,download,status"
        ```

2. Confirm that Repo Manager published the selected tarballs and produced a
   successful status contract:

    ```bash title="Run on: OIM host"
    source /etc/profile.d/omnia-env.sh
    repo_manager_path="${REPO_MANAGER_DATA_PATH:-${OMNIA_DATA_PATH}/repo_manager}"
    cat "$repo_manager_path/output/$OMNIA_PROJECT_NAME/repo_status.yml"
    pulp file distribution list --limit 1000
    ```

3. Provision the Slurm nodes. This generates the shared `/hpc_tools` mount
   configuration and places `install_ucx.sh` and `install_openmpi.sh` under
   `/usr/local/bin/` on login-compiler nodes:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags provision
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags provision
        ```

4. On a provisioned login-compiler node, verify the shared mount and install
   UCX:

    ```bash title="Run on: login-compiler node"
    mountpoint -q /hpc_tools
    /usr/local/bin/install_ucx.sh
    source /etc/profile.d/ucx.sh
    ucx_info -v
    ```

    The script installs UCX under `/hpc_tools/benchmarks/ucx` and writes
    `/var/log/ucx_installation.log`.

5. Install OpenMPI after UCX:

    ```bash title="Run on: login-compiler node"
    /usr/local/bin/install_openmpi.sh
    source /etc/profile.d/openmpi.sh
    mpirun --version
    mpicc --version
    ```

    The script detects the shared UCX installation and Slurm commands when
    available. It installs OpenMPI under
    `/hpc_tools/benchmarks/openmpi` and writes
    `/var/log/openmpi_installation.log`.

## Verification

On the login-compiler node, confirm that both shared installations and their
environment files exist:

```bash title="Run on: login-compiler node"
test -x /hpc_tools/benchmarks/ucx/bin/ucx_info
test -x /hpc_tools/benchmarks/openmpi/bin/mpirun
test -f /etc/profile.d/ucx.sh
test -f /etc/profile.d/openmpi.sh
source /etc/profile.d/ucx.sh
source /etc/profile.d/openmpi.sh
ucx_info -v
mpirun --version
```

On the OIM, also verify that the provisioning contract succeeded:

```bash title="Run on: OIM host"
source /etc/profile.d/omnia-env.sh
orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_status.yml"
```

## Next steps

- [Set up NVIDIA HPC SDK](setup_nvhpc_sdk.md).
- [Configure Slurm with GPUs](slurm_with_gpu.md).
- [Run HPC benchmarks](run_hpc_benchmarks.md).

## Troubleshooting

- **`/hpc_tools` is not mounted:** Confirm that `nfs_storage_name` references
  an existing entry in `storage_config.yml`. If `vast_storage_name` is set,
  confirm that it references the intended separate VAST entry; otherwise the
  NFS entry supplies `/hpc_tools`. Then rerun provisioning.
- **A tarball cannot be downloaded:** Confirm that Repo Manager synchronized
  the `ucx` and `openmpi` catalog entries and that the Pulp endpoint and
  expected tarball paths in `repo_status.yml` are reachable.
- **UCX compilation fails:** Review
  `/var/log/ucx_installation.log` and verify that the catalog-selected image
  contains the required compiler and build packages.
- **OpenMPI does not use UCX:** Verify
  `/hpc_tools/benchmarks/ucx/bin/ucx_info` exists before rerunning
  `install_openmpi.sh`.
- **OpenMPI does not detect Slurm:** Verify that `sinfo` is available and
  Munge is configured before rerunning the installation.
