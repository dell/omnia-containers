# Slurm with GPUs

Omnia automatically provisions GPU readiness on Slurm compute nodes
during cluster deployment. This guide describes the automated GPU
provisioning process and verification steps.

## Overview

When Omnia provisions Slurm nodes, GPU readiness is configured
automatically. No user action is required beyond standard Slurm
deployment. Nodes without NVIDIA GPU hardware are detected and skipped
without error.

Omnia configures:

- NVIDIA driver installation on each GPU-capable node
- CUDA toolkit on a shared NFS location
- DCGM for GPU monitoring and diagnostics
- Slurm GRES definitions (`GresTypes=gpu` with `AutoDetect=nvml`)

## Prerequisites

- Slurm is deployed and operational (see [Set Up Slurm](setup_slurm.md)).
- GPU-capable nodes are assigned to `slurm_node_x86_64` or
  `slurm_node_aarch64` functional groups.
- DCGM telemetry is enabled in `telemetry_config.yml` (enabled by
  default):

    ```yaml title="File: /opt/omnia/input/project_default/telemetry_config.yml"
    telemetry_sources:
      dcgm:
        metrics_enabled: true
    ```

## Automated Provisioning

### NVIDIA Driver

The NVIDIA driver is installed locally on each GPU-capable Slurm node
during provisioning.

### CUDA Toolkit

The CUDA toolkit is installed once to a shared NFS location and made
available to all Slurm nodes via a persistent mount at `/usr/local/cuda`.

- In clusters with a login or compiler node, the toolkit is installed by
  that node and published to the shared NFS path
- Compute nodes mount the already-installed toolkit directly
- In clusters without a login or compiler node, toolkit installation is
  coordinated across compute nodes to run exactly once

### DCGM

DCGM is installed on each GPU-capable Slurm node. The correct DCGM
package is selected based on the CUDA version. On clusters running CUDA
12 or later, the multinode diagnostic plugin is also installed. The
`nvidia-dcgm` service is enabled and started automatically.

- Set `telemetry_sources.dcgm.metrics_enabled` to `false` in
  `telemetry_config.yml` to skip DCGM installation.


## Verification

1. **Verify GPU drivers and CUDA**:

    ```bash title="Run on: GPU compute node"
    nvidia-smi
    nvcc --version
    ```

2. **Verify CUDA shared mount**:

    ```bash title="Run on: GPU compute node"
    mount | grep cuda
    ls /usr/local/cuda/
    ```

3. **Verify DCGM**:

    ```bash title="Run on: GPU compute node"
    systemctl status nvidia-dcgm
    dcgmi discovery -l
    ```

4. **Check Slurm GRES configuration**:

    ```bash title="Run on: Slurm controller node"
    scontrol show nodes | grep -i gres
    ```

    ```text title="Expected output"
    Gres=gpu:nvidia_a100:4
    GresUsed=gpu:nvidia_a100:0
    ```

5. **Submit a GPU job**:

    ```bash title="Run on: Slurm controller node"
    srun --gres=gpu:1 nvidia-smi
    ```

6. **Submit a multi-GPU batch job**:

    ```bash title="Run on: Slurm controller node"
    cat <<'EOF' > /tmp/gpu_test.sh
    #!/bin/bash
    #SBATCH --job-name=gpu_test
    #SBATCH --gres=gpu:2
    #SBATCH --nodes=1
    #SBATCH --time=00:05:00

    echo "Running on $(hostname)"
    echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
    nvidia-smi
    EOF

    sbatch /tmp/gpu_test.sh
    ```

## Next Steps

- [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Run GPU-accelerated benchmarks
- [Configure InfiniBand](../Networking/configure_infiniband.md) -- Enable
  GPUDirect RDMA over InfiniBand

## Troubleshooting

For Slurm troubleshooting, see
[Slurm Issues](../../Troubleshooting/slurm.md).
