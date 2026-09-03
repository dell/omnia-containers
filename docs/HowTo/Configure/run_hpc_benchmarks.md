# Run HPC Benchmarks

Pull and run container images and benchmark tools on Slurm compute nodes
using the Omnia-provisioned HPC tools infrastructure.

## Overview

Omnia deploys helper scripts and a benchmark tools directory to the
shared NFS storage during provisioning. This guide covers:

- Pulling container images from the local Pulp registry
- Running GPU and MPI benchmarks via Apptainer
- Using source-only benchmark tools

## Prerequisites

- Slurm is deployed and operational (see [Set Up Slurm](../orchestrator/deploy_slurm.md)).
- For GPU benchmarks: GPU drivers are installed (see
  [Slurm with GPU](slurm_with_gpu.md)).

## Procedure

### Pull Container Images

A helper script on the NFS share simplifies pulling container images from
the local Pulp registry. By default, it downloads the HPC benchmarks
container.

1. **Verify the scripts are available** on a login or compiler node:

    ```bash title="Run on: login or compiler node"
    ls -l /hpc_tools/scripts/download_container_image.sh
    ls -l /hpc_tools/scripts/container_image.list
    ```

2. **(Optional) Add additional images** to the list:

    ```bash title="Run on: login or compiler node"
    vi /hpc_tools/scripts/container_image.list
    ```

    Format: `<registry>/<namespace>/<image>:<tag>`

3. **Run the download script**:

    ```bash title="Run on: login or compiler node"
    /hpc_tools/scripts/download_container_image.sh
    ```

4. **Verify the downloaded images**:

    ```bash title="Run on: login or compiler node"
    ls -lh /hpc_tools/container_images
    apptainer inspect /hpc_tools/container_images/<image>.sif
    ```

5. **Test GPU visibility** inside a container:

    ```bash title="Run on: compute node"
    apptainer exec --nv /hpc_tools/container_images/hpc-benchmarks_25.09.sif nvidia-smi
    ```

### Pull Benchmark Tools

Omnia deploys benchmark staging scripts to shared storage. Run the
pull script to download source-only benchmark tools:

```bash title="Run on: login or compiler node"
/hpc_tools/scripts/pull_benchmarks.sh
```

Available benchmark tools: `osu-micro-benchmarks`, `imb`, `likwid`,
`papi`, `geopm`, `sionlib`, `msr-safe` (x86_64 only).

### Run HPL-MxP Benchmark

HPL, HPL-MxP, and STREAM are container-first benchmarks available via
the HPC benchmarks container image:

```bash title="Run on: compute node"
srun -N 1 --ntasks-per-node=2 --gres=gpu:2 --mpi=pmix \
  apptainer exec --nv /hpc_tools/container_images/hpc-benchmarks_25.09.sif \
  /workspace/hpl-mxp-linux-x86_64/hpl-mxp.sh \
  --n 5000 --nb 512 \
  --nprow 1 --npcol 2 --nporder row \
  --gpu-affinity 0:1
```

### Run GPU Benchmark

```bash title="Run on: Slurm controller node"
srun --gres=gpu:1 apptainer exec --nv \
  /hpc_tools/container_images/hpc-benchmarks_25.09.sif nvidia-smi
```

## Verification

1. **Check benchmark job completed successfully**:

    ```bash title="Run on: Slurm controller node"
    sacct --starttime=today --format=JobName,State,Elapsed,ExitCode
    ```

    All benchmark jobs should show `COMPLETED` state with exit code `0:0`.

## Next Steps

- [Configure InfiniBand](configure_infiniband.md) -- Optimize
  network performance for HPC workloads
- [Slurm with GPU](slurm_with_gpu.md) -- GPU provisioning details

## Troubleshooting

**Benchmark assets missing on Slurm nodes**
   Verify NFS path and scripts are present:

   ```bash title="Run on: affected node"
   ls -ld /hpc_tools
   ls -l /hpc_tools/scripts
   ```

   Run the staging script and review the log:

   ```bash title="Run on: affected node"
   /hpc_tools/scripts/pull_benchmarks.sh
   tail -n 200 /var/log/pull_benchmarks.log
   ```

   Validate staged benchmark directories:

   ```bash title="Run on: affected node"
   ls -l /hpc_tools/osu-micro-benchmarks /hpc_tools/imb /hpc_tools/likwid /hpc_tools/papi
   ```

!!! note
    `msr-safe` is expected only on `x86_64`.

For the complete list, see [Slurm Issues](../../Troubleshooting/orchestrator.md).


















