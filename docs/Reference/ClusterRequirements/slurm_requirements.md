# Slurm Requirements

This section outlines the key requirements for Slurm used by Omnia to deploy HPC clusters. For more information about the supported devices and software, see [Support Matrix](../index.md#support-matrix).

- Ensure that each slurm compute node has at least 64 GB RAM.
- In a mixed architecture environment where the Slurm control node and compute nodes use different architectures (for example, control node with x86_64 and compute nodes with aarch64), ensure that Slurm binaries for both architectures are compiled and available in the user repository.
- The Slurm RPM must be available in the user repository. If the Slurm RPM is not available, refer to [Slurm Quick Start Administrator Guide](https://slurm.schedmd.com/quickstart_admin.html) for instructions on building Slurm RPMs.
- If the Slurm RPMS are already available, update the value (`<hosted slurm repository url>`) in the URL of the `user_repo_url_x86_64` or `user_repo_url_aarch64` parameter in `/opt/omnia/input/project_default/local_repo_config.yml`.
- If the repository is hosted, use the URL created in the `local_repo_config.yml` file.

    ```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
    user_repo_url_x86_64:
      - { url: "<hosted slurm repository url>", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "slurm_custom" }

    user_repo_url_aarch64:
      - { url: "<hosted slurm repository url>", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "slurm_custom" }
    ```

    Run `ansible-playbook local_repo/local_repo.yml`.

- Create Slurm repository build for x86_64. See [Build Slurm repository for x86_64](../../HowTo/Slurm/build_slurm_repo.md) and [Host RPMS on Apache server](../../HowTo/Slurm/host_slurm_repo.md).
- After Slurm RPMS are generated, change the rpms in corresponding role accordingly if the rpm names are not matching with rpms in `input/config/x86_64/rhel/10.0/slurm_custom.json`.

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
- For VAST appliance setup, see [Configure VAST Storage](../../HowTo/Storage/configure_vast.md).

For details on what data lives on each mount, see [Slurm Storage Architecture](../../HowTo/Slurm/setup_slurm.md#slurm-storage-architecture).

## CUDA and DCGM

The following prerequisites must be satisfied before deploying Omnia on Slurm clusters where GPU-capable nodes are present. These apply in addition to general Slurm prerequisites.

**Repository Requirements**

- CUDA repository: Must be reachable from Slurm compute nodes. The CUDA repository must be accessible through the local Pulp repository configured during `local_repo.yml` execution.
- DCGM repository: Must be available in the configured local repository.

**NFS Requirements**

- The shared NFS or VAST path configured for Slurm HPC tools must be reachable from all Slurm compute nodes and all login/compiler nodes at provisioning time.
- Minimum recommended space for the `hpc_tools/cuda` path is **30 GB**.
- The NFS share must be exported with `no_root_squash`.

**Hardware Requirements**

- NVIDIA GPU hardware: Must be present on any Slurm node intended for GPU workloads. Nodes without GPU hardware are automatically skipped at runtime.

!!! note

    If repositories are not reachable or the NFS path is unavailable at provisioning time, GPU setup will fail on affected nodes and the DCGM service will not be started. Refer to the Manual Recovery section for remediation steps.

!!! info

    - [Set Up Slurm](../../HowTo/Slurm/setup_slurm.md) -- For detailed information on setting up the Slurm cluster.
    - [Slurm Configuration](../Configuration/omnia_config.md#slurm-configuration-parameters) -- For detailed information on Slurm configuration parameters.
