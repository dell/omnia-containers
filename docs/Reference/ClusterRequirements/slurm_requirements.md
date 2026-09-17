# Slurm Requirements

This section outlines the key requirements for Slurm used by Omnia to deploy HPC clusters. For more information about the supported devices and software, see [Support Matrix](../index.md#support-matrix).

- Ensure that each slurm compute node has at least 64 GB RAM.
- In a mixed architecture environment where the Slurm control node and compute nodes use different architectures (for example, control node with x86_64 and compute nodes with aarch64), ensure that compatible Slurm packages for both architectures are available in the user repository.
- The Slurm RPMs required by the selected catalog must be available from a
  repository that the OIM can reach. Omnia consumes this repository; it does
  not build or host the RPMs.
- For every architecture used by the cluster, configure the hosted Slurm repository under `repositories."10.0".<architecture>.user_repos.slurm_custom` in `$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml`.

    ```yaml title="File: $OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml"
    repositories:
      "10.0":
        x86_64:
          user_repos:
            slurm_custom:
              url: "http://<host>/slurm-repo/x86_64"
        aarch64:
          user_repos:
            slurm_custom:
              url: "http://<host>/slurm-repo/aarch64"
    ```

    Configure only the architectures used by the cluster. Ensure that the selected catalog references `slurm_custom`, and that its Slurm package names match the hosted RPMs.

    Synchronize the catalog content and verify the result:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags download
        ./omnia.sh --run repo_manager --tags status
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager
        ansible-playbook playbooks/repo_manager.yml --tags download
        ansible-playbook playbooks/repo_manager.yml --tags status
        ```

- If the package names in the repository differ from the selected catalog,
  update the catalog so its Slurm package names match the available RPMs. See
  [Add an RPM Repository and Packages](../../HowTo/repo_manager/adding_additional_repositories.md).

## HPC Benchmark Image Layer

- Omnia supports an HPC Benchmark Image Layer for Slurm deployments.
- This capability is runtime script-driven:
    - Provisioning deploys `pull_benchmarks.sh` and `benchmark_tools.list` to `/hpc_tools/scripts`.
    - Runtime staging is executed via `/hpc_tools/scripts/pull_benchmarks.sh`.
- Benchmark artifacts are pulled from the local Pulp mirror path to `/hpc_tools/<tool>/`.
- The feature is staging-only; Omnia does not compile or execute benchmark workloads.
- Ensure Slurm shared storage (`/hpc_tools`) is available and local repository content is prepared before runtime staging.

**Operational notes**

- `msr-safe` is `x86_64` only and is automatically skipped on `aarch64`.
- If a destination directory already contains files, the tool is skipped to prevent overwrite.
- Runtime summary and per-tool outcomes are logged at:

    ```text title="Log file"
    /var/log/pull_benchmarks.log
    ```

## Shared Storage Requirements

Slurm requires shared storage mounts for configuration distribution, authentication, and HPC tools. Omnia supports two mount types for Slurm: a primary NFS mount and an optional VAST storage mount.

### Primary NFS mount

- An NFS server with at least **50 GB** of available storage is required. Increase based on cluster size and job data volume.
- The NFS share must be accessible from the OIM, Slurm controller, all compute nodes, and all login nodes.
- The NFS share must be exported with `no_root_squash` and **755 permissions**.
- Omnia uses this mount to store and distribute:
    - Slurm configuration files (`slurm.conf`, `slurmdbd.conf`, `cgroup.conf`, `gres.conf`)
    - Munge authentication keys (must be identical across all nodes)
    - Shared spool and state directories
- Set `mount_on_oim: true` in `storage_config.yml` so the OIM can write configuration and munge keys during provisioning.
- The `name` field in `storage_config.yml` must match the `nfs_storage_name` value in `omnia_config.yml`.

### VAST storage mount (optional)

- If a VAST storage appliance is available, it can serve as the high-performance backend for HPC tools and benchmarks via the `vast_storage_name` parameter in `omnia_config.yml`.
- RDMA transport requires InfiniBand or RoCE connectivity between cluster nodes and the VAST appliance.
- If `vast_storage_name` is not specified, Omnia uses the primary NFS mount for HPC tools.
- For VAST appliance setup, see [Configure VAST Storage](../../HowTo/Telemetry/configure_vast.md).

For details on what data lives on each mount, see [Slurm Storage Architecture](../../HowTo/orchestrator/deploy_slurm.md#slurm-storage-architecture).

## CUDA and DCGM

The following prerequisites must be satisfied before deploying Omnia on Slurm clusters where GPU-capable nodes are present. These apply in addition to general Slurm prerequisites.

**Repository Requirements**

- Synchronize the selected RHEL 10.0 Slurm catalog through Repository Manager
  before building the cluster images. The catalog must provide the NVIDIA
  driver, CUDA toolkit, DCGM, and matching kernel-development packages for
  each target architecture.
- Slurm compute nodes must be able to reach the repositories recorded in the
  successful Repository Manager `repo_status.yml`.

**DCGM Installation Configuration**

DCGM installation is controlled by `dcgm_enabled` in
`orchestrator_config.yml`. The shipped value enables installation on
GPU-capable Slurm nodes:

```yaml title="File: $ORCHESTRATOR_DATA_PATH/input/$OMNIA_PROJECT_NAME/orchestrator_config.yml"
dcgm_enabled: true
```

Set `dcgm_enabled: false` to skip DCGM installation. DCGM metrics collection
is not currently integrated into the Omnia Telemetry pipeline.

**NFS Requirements**

- The shared NFS or VAST path configured for Slurm HPC tools must be reachable from all Slurm compute nodes and all login/compiler nodes at provisioning time.
- Minimum recommended space for the `hpc_tools/cuda` path is **30 GB**.
- The NFS share must be exported with `no_root_squash`.

**Hardware Requirements**

- NVIDIA GPU hardware: Must be present on any Slurm node intended for GPU workloads. Nodes without GPU hardware are automatically skipped at runtime.

**NVIDIA Peer Memory**

Omnia attempts to build and load `nvidia-peermem` through DKMS after detecting
an NVIDIA GPU and a working driver. The `kernel-devel` package must match the
running kernel. Nodes without applicable GPU hardware skip the operation.
`nvidia-peermem` is required only for GPUDirect RDMA workloads.

!!! note

    If repositories are not reachable or the NFS path is unavailable at provisioning time, GPU setup will fail on affected nodes and the DCGM service will not be started. Refer to the Manual Recovery section for remediation steps.

!!! info

    - [Set Up Slurm](../../HowTo/orchestrator/deploy_slurm.md) -- For detailed information on setting up the Slurm cluster.
    - [Slurm Configuration](../Configuration/omnia_config.md#slurm-configuration-parameters) -- For detailed information on Slurm configuration parameters.














