# NVIDIA HPC SDK Setup

Set up the NVIDIA HPC SDK on Slurm compiler and compute nodes for
GPU-accelerated HPC application development.

## Overview

Omnia pre-deploys an NVIDIA HPC SDK setup script
(`/usr/local/bin/setup_nvhpc_sdk.sh`) to all Slurm nodes during
provisioning. The setup follows a two-step manual workflow:

1. Run `--install` on the compiler node to install via DNF and publish
   to shared NFS.
2. Run the script (without arguments) on each compute node to mount
   from NFS.

### Architecture Support

The script detects the node architecture automatically:

| Architecture | NFS Subdirectory |
|---|---|
| `x86_64` | `Linux_x86_64` |
| `aarch64` | `Linux_aarch64` |

No separate configuration is required for mixed-architecture clusters.

!!! info

    - [Slurm with GPU](slurm_with_gpu.md) -- GPU configuration for Slurm nodes
    - [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Validate cluster performance
    - [Set Up Slurm](../orchestrator/deploy_slurm.md) -- Slurm cluster setup guide

## Prerequisites

- Slurm compiler node and compute nodes are provisioned and running.
- Shared NFS storage is mounted and the path `/hpc_tools/nvidia_sdk`
  is accessible on the compiler node before running the install step.
- NVIDIA package repositories are configured automatically during
  cloud-init. No manual repository setup is required.

!!! note
    The `nvidia-hpc-sdk` repository is included in the default
    [`local_repo_config.yml`](../../Reference/Configuration/repo_manager_config.md)
    for both x86_64 and aarch64 architectures.

## Procedure

### Step 1 -- Install on the Compiler Node

On the designated compiler/login node, run:

```bash title="Run on: compiler/login node"
/usr/local/bin/setup_nvhpc_sdk.sh --install
```

!!! tip
    You can also use `-i` as a shorthand: `/usr/local/bin/setup_nvhpc_sdk.sh -i`

This performs the following actions in sequence:

1. Installs the `nvhpc` package via DNF from the pre-configured NVIDIA
   repository.
2. Copies the installed SDK from `/opt/nvidia/hpc_sdk` to the shared
   NFS path `/hpc_tools/nvidia_sdk/nvhpc`.
3. Sets up a local bind mount:
   `/hpc_tools/nvidia_sdk/nvhpc` → `/opt/nvidia/nvhpc`.
4. Writes environment configuration to `/etc/profile.d/nvhpc.sh`.

To force a reinstall when the SDK is already present on NFS:

```bash title="Run on: compiler/login node"
/usr/local/bin/setup_nvhpc_sdk.sh --install --force
```

!!! note
    If NVHPC is already present on NFS, the script skips the DNF
    install and proceeds directly to the bind mount and environment
    setup, unless `--force` is specified.

### Step 2 -- Set Up on Compute Nodes

On each Slurm compute node, run:

```bash title="Run on: compute node"
/usr/local/bin/setup_nvhpc_sdk.sh
```

This performs the following actions:

1. Validates that the NVHPC SDK exists on NFS at
   `/hpc_tools/nvidia_sdk/nvhpc`.
2. Sets up a local bind mount:
   `/hpc_tools/nvidia_sdk/nvhpc` → `/opt/nvidia/nvhpc`.
3. Writes environment configuration to `/etc/profile.d/nvhpc.sh`.

!!! important
    Step 2 must be run after Step 1 is complete on the compiler node.
    If the SDK is not found on NFS, the script exits with an actionable
    error message.

### Environment Variables Configured

After setup, the following variables are available in all login shells
on both the compiler node and compute nodes:

| Variable | Value |
|---|---|
| `NVCOMPILERS` | `/opt/nvidia/nvhpc` |
| `NVARCH` | `Linux_x86_64` or `Linux_aarch64` (auto-detected) |
| `NVHPC_VERSION` | Auto-detected from the installed SDK version |
| `PATH` | Prepended with compiler `bin` and MPI `bin` directories |
| `MANPATH` | Appended with compiler `man` and MPI `man` directories |
| `MODULEPATH` | Prepended with the nvhpc `modulefiles` directory |

## Verification

After running the setup script, verify by sourcing the profile and
checking the compilers:

```bash title="Run on: compiler or compute node"
source /etc/profile.d/nvhpc.sh
nvc --version
nvc++ --version
nvfortran --version
```

### Logs

Setup output and errors are written to
`/var/log/nvhpc_sdk_setup.log` on each node. Check this file if the
setup script fails:

```bash title="Run on: affected node"
cat /var/log/nvhpc_sdk_setup.log
```

## Next Steps

- [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Validate cluster performance using the NVHPC SDK.
- [Slurm With GPU](slurm_with_gpu.md) -- Configure GPU support for Slurm nodes.

## Troubleshooting

- **NVHPC compilers not found after setup**: Verify that `/etc/profile.d/nvhpc.sh` exists and source it manually with `source /etc/profile.d/nvhpc.sh`.
- **NFS mount path not accessible**: Confirm that the NFS share is mounted at `/hpc_tools/nvidia_sdk` on the compiler node and that the path is writable.



















