# Run HPC Benchmarks

Pull and run container images and benchmark tools on Slurm compute nodes
using the Omnia-provisioned HPC tools infrastructure.

## Overview

Omnia deploys helper scripts and a benchmark tools directory to the selected
Slurm shared storage during provisioning. This guide covers:

- Pulling container images from the local Pulp registry
- Running GPU and MPI benchmarks via Apptainer
- Staging source-only benchmark tarballs for a later build

## Prerequisites

- Slurm is deployed and operational (see [Set Up Slurm](deploy_slurm.md)).
- The selected Slurm catalog contains `apptainer`, the
  `nvcr.io/nvidia/hpc-benchmarks:25.09` image, and any source benchmark tools
  you intend to stage. Repository Manager must report those artifacts as
  successfully synchronized.
- `slurm_cluster.nfs_storage_name` points to shared storage defined in
  `storage_config.yml`. The optional `vast_storage_name` can select a separate
  VAST mount for `/hpc_tools`; when it is omitted or empty, provisioning uses
  the `nfs_storage_name` entry for `/hpc_tools`.
- For GPU benchmarks: GPU drivers are installed (see
  [Slurm with GPU](slurm_with_gpu.md)).
- Run the supplied download scripts as `root`; they write logs under
  `/var/log` and populate the shared filesystem.

## Procedure

### Pull Container Images

A helper script on the selected Slurm share pulls container images from the
local Pulp registry only; it has no internet fallback. By default, it
downloads the HPC benchmarks container.

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

    The script writes its summary to
    `/var/log/container_image_download.log` and Apptainer output to
    `/var/log/apptainer_pull.log`. It returns a nonzero status if any listed
    image cannot be pulled from Pulp.

4. **Verify the downloaded images**:

    ```bash title="Run on: login or compiler node"
    ls -lh /hpc_tools/container_images
    apptainer inspect /hpc_tools/container_images/<image>.sif
    ```

5. **Inspect the downloaded image**:

    ```bash title="Run on: login or compiler node"
    apptainer inspect /hpc_tools/container_images/hpc-benchmarks_25.09.sif
    ```

### Pull Benchmark Tools

Omnia deploys benchmark staging scripts to shared storage. Run the
pull script to download source-only benchmark tools:

```bash title="Run on: login or compiler node"
/hpc_tools/scripts/pull_benchmarks.sh
```

Available benchmark tools: `osu-micro-benchmarks`, `imb`, `likwid`,
`papi`, `geopm`, `sionlib`, `msr-safe` (x86_64 only).

The script autodetects `x86_64` or `aarch64`, downloads each selected tarball
from Pulp into `/hpc_tools/<tool>/`, and writes
`/var/log/pull_benchmarks.log`. It stages source archives; it does not extract,
build, or install them.

### Run HPL-MxP Benchmark

HPL, HPL-MxP, and STREAM are container-first benchmarks available via
the HPC benchmarks container image. This HPL-MxP example uses the x86_64 path
inside the 25.09 image and submits the job through Slurm:

```bash title="Run on: Slurm login or controller node"
srun -N 1 --ntasks-per-node=2 --gres=gpu:2 --mpi=pmix \
  apptainer exec --nv /hpc_tools/container_images/hpc-benchmarks_25.09.sif \
  /workspace/hpl-mxp-linux-x86_64/hpl-mxp.sh \
  --n 5000 --nb 512 \
  --nprow 1 --npcol 2 --nporder row \
  --gpu-affinity 0:1
```

### Run GPU Benchmark

```bash title="Run on: Slurm login or controller node"
srun --gres=gpu:1 apptainer exec --nv \
  /hpc_tools/container_images/hpc-benchmarks_25.09.sif nvidia-smi
```

## Verification

1. **Check benchmark job completed successfully**:

    ```bash title="Run on: Slurm login or controller node"
    sacct --starttime=today --format=JobName,State,Elapsed,ExitCode
    ```

    All benchmark jobs should show `COMPLETED` state with exit code `0:0`.

## Next steps

- [Configure InfiniBand](configure_infiniband.md) -- Optimize
  network performance for HPC workloads
- [Slurm with GPU](slurm_with_gpu.md) -- GPU provisioning details

## Troubleshooting

**Benchmark assets missing on Slurm nodes**

   Verify the shared path and scripts are present:

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

For the complete list, see [Slurm Issues](../../Troubleshooting/orchestrator/index.md).
















