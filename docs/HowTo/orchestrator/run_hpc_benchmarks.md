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

### Pull benchmark tools

Omnia deploys the benchmark staging script to the shared HPC tools directory:

```text
/hpc_tools/scripts/pull_benchmarks.sh
```

The script detects the operating-system version and architecture of the node
on which it runs. It downloads benchmark artifacts from the matching
Repository Manager Pulp path.

Run the script as root on one provisioned node for each operating-system
version and architecture used by the Slurm cluster:

```bash
/hpc_tools/scripts/pull_benchmarks.sh
```

For example, running the script on a RHEL 10.0 x86_64 node uses:

Pulp path:

```text
x86_64/rhel/10.0/tarball/<tool>
```

Destination:

```text
/hpc_tools/platforms/rhel/10.0/x86_64/<tool>/
```

Running it on a RHEL 10.2 x86_64 node uses:

Pulp path:

```text
x86_64/rhel/10.2/tarball/<tool>
```

Destination:

```text
/hpc_tools/platforms/rhel/10.2/x86_64/<tool>/
```

Supported source benchmark tools include:

- `osu-micro-benchmarks`
- `imb`
- `likwid`
- `papi`
- `geopm`
- `sionlib`
- `msr-safe` on x86_64

Because `/hpc_tools` is shared, the script normally needs to run only once for
each unique operating-system version and architecture. Other nodes using the
same platform reuse the staged content.

Do not run the script concurrently on multiple nodes using the same platform
directory.

> **Note**
>
> The script stages source archives and a `PULP_MANIFEST`. It does not extract,
> compile, or install the benchmark software. The absence of an executable
> benchmark binary after download is expected.

#### Verify platform-specific benchmark artifacts

On a Slurm node, determine the selected platform directory:

```bash
source /hpc_tools/scripts/omnia_platform.sh
omnia_detect_platform
echo "$OMNIA_PLATFORM_ROOT"
```

List the downloaded artifacts:

```bash
find "$OMNIA_PLATFORM_ROOT" -maxdepth 2 -type f -print
```

Validate an OSU Micro-Benchmarks archive:

```bash
tar -tzf \
  "$OMNIA_PLATFORM_ROOT/osu-micro-benchmarks/osu-micro-benchmarks.tar.gz" \
  >/dev/null

echo $?
```

An exit status of 0 confirms that the archive is readable.

Example platform-specific artifact paths:

```text
/hpc_tools/platforms/rhel/10.0/x86_64/osu-micro-benchmarks/osu-micro-benchmarks.tar.gz
/hpc_tools/platforms/rhel/10.2/x86_64/osu-micro-benchmarks/osu-micro-benchmarks.tar.gz
```

Container images remain under the existing shared path:

```text
/hpc_tools/container_images/
```

Container image storage is not divided by the node operating-system version.

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

## Troubleshooting platform-specific benchmark content

### The script selects the wrong RHEL version

Check the operating system actually running on the node:

```bash
cat /etc/os-release
```

The benchmark script uses `VERSION_ID` from the running node. It does not use
the operating-system version written in `pxe_mapping_file.csv`.

If the mapping was changed but the node still reports the previous operating
system, reprovision and PXE boot the node with the required image.

### The platform directory does not exist

Run the benchmark pull script from a node using that platform:

```bash
/hpc_tools/scripts/pull_benchmarks.sh
```

The script creates the required platform and tool directories.

### A benchmark download returns HTTP 404

Confirm Repository Manager synchronized the tarball for the exact operating
system and architecture selected by the node.

Check:

```text
$OMNIA_DATA_PATH/repo_manager/output/<project>/repo_status.yml
```

The required operating-system version and architecture must have a successful
repository entry.

### The tool directory exists but no executable is present

This is expected. `pull_benchmarks.sh` downloads source archives only. Build the
software separately or use the catalog-selected benchmark container when
available.

### An incomplete tool directory is skipped

Inspect the exact platform-specific tool directory and its `PULP_MANIFEST`.
Remove only the incomplete tool directory after confirming it is safe to
re-download:

```bash
source /hpc_tools/scripts/omnia_platform.sh
omnia_detect_platform

rm -rf "$OMNIA_PLATFORM_ROOT/<tool>"
/hpc_tools/scripts/pull_benchmarks.sh
```

Do not remove `/hpc_tools/platforms` or another operating system's directory.

For the complete list, see [Slurm Issues](../../Troubleshooting/orchestrator/index.md).















