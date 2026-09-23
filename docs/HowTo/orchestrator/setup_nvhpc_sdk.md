# NVIDIA HPC SDK Setup

Set up the NVIDIA HPC SDK on Slurm compiler and compute nodes for
GPU-accelerated HPC application development.

## Overview

Omnia places an NVIDIA HPC SDK setup script
(`/usr/local/bin/setup_nvhpc_sdk.sh`) on login-compiler and Slurm compute
nodes during provisioning. The setup follows a two-step manual workflow:

1. Run `--install` on one login-compiler node for each architecture to install
   via DNF and publish to shared storage.
2. Run the script without arguments on each compute node to bind-mount the
   matching architecture from shared storage.

### Architecture Support

The script detects the node architecture automatically:

| Architecture | Shared-storage subdirectory |
|---|---|
| `x86_64` | `Linux_x86_64` |
| `aarch64` | `Linux_aarch64` |

Both architecture subdirectories can coexist on the share. In a
mixed-architecture cluster, however, complete the install step once on an
x86_64 login-compiler node and once on an aarch64 login-compiler node before
setting up the respective compute nodes.

!!! info

    - [Slurm with GPU](slurm_with_gpu.md) -- GPU configuration for Slurm nodes
    - [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Validate cluster performance
    - [Set Up Slurm](deploy_slurm.md) -- Slurm cluster setup guide

## Prerequisites

- A catalog-defined login-compiler node and the target compute nodes are
  provisioned and running.
- The selected catalog contains the `nvhpc` RPM for every target architecture,
  and Repository Manager synchronized the `nvidia-hpc-sdk` repository.
- `slurm_cluster.nfs_storage_name` references shared storage defined in
  `storage_config.yml`. The optional `vast_storage_name` can select a separate
  VAST mount for `/hpc_tools`; when it is omitted or empty, provisioning uses
  the `nfs_storage_name` entry. `/hpc_tools/nvidia_sdk` must be writable on the
  login-compiler node before the install step.
- Run the script as `root`; it installs RPMs and writes `/etc/fstab`,
  `/etc/profile.d/nvhpc.sh`, and `/var/log/nvhpc_sdk_setup.log`.

!!! note
    The `nvidia-hpc-sdk` repository is included in the default
    [Repository Manager configuration](../../Reference/Configuration/repo_manager_config.md)
    for both x86_64 and aarch64 architectures.

## Procedure

### Step 1 -- Install on the Compiler Node

On one login-compiler node for the architecture being published, run:

```bash title="Run on: login-compiler node"
/usr/local/bin/setup_nvhpc_sdk.sh --install
```

!!! tip
    You can also use `-i` as a shorthand: `/usr/local/bin/setup_nvhpc_sdk.sh -i`

This performs the following actions in sequence:

1. Installs the `nvhpc` package via DNF from the pre-configured NVIDIA
   repository.
2. Copies the installed SDK from `/opt/nvidia/hpc_sdk` to the shared path
   `/hpc_tools/nvidia_sdk/nvhpc`.
3. Sets up a local bind mount:
   `/hpc_tools/nvidia_sdk/nvhpc` → `/opt/nvidia/nvhpc`.
4. Writes environment configuration to `/etc/profile.d/nvhpc.sh`.

To force the script to republish the locally installed SDK when the SDK is
already present on shared storage:

```bash title="Run on: login-compiler node"
/usr/local/bin/setup_nvhpc_sdk.sh --install --force
```

!!! note
    If NVHPC is already present on shared storage, the script skips the DNF
    check and copy, then proceeds directly to the bind mount and environment
    setup. `--force` repeats the local-package check and copies the local SDK
    to shared storage again; it does not reinstall an RPM that is already
    installed locally.

For a mixed-architecture cluster, repeat this step on a login-compiler node of
the other architecture. The script merges that architecture's
`Linux_<architecture>` directory into the same shared SDK root.

### Step 2 -- Set Up on Compute Nodes

On each Slurm compute node, run:

```bash title="Run on: compute node"
/usr/local/bin/setup_nvhpc_sdk.sh
```

This performs the following actions:

1. Validates that the NVHPC SDK exists on shared storage at
   `/hpc_tools/nvidia_sdk/nvhpc`.
2. Sets up a local bind mount:
   `/hpc_tools/nvidia_sdk/nvhpc` → `/opt/nvidia/nvhpc`.
3. Writes environment configuration to `/etc/profile.d/nvhpc.sh`.

!!! important

    Step 2 must be run after Step 1 is complete for that compute node's
    architecture. If the matching `Linux_x86_64` or `Linux_aarch64` directory
    is not found on shared storage, the script exits with an error.

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

Setup output and errors are appended to `/var/log/nvhpc_sdk_setup.log` on each
node. Check this file if the setup script fails:

```bash title="Run on: affected node"
cat /var/log/nvhpc_sdk_setup.log
```

## Next steps

- [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Validate cluster performance using the NVHPC SDK.
- [Slurm With GPU](slurm_with_gpu.md) -- Configure GPU support for Slurm nodes.

## Troubleshooting

- **NVHPC compilers not found after setup**: Verify that `/etc/profile.d/nvhpc.sh` exists and source it manually with `source /etc/profile.d/nvhpc.sh`.
- **Shared path not accessible**: Confirm that `/hpc_tools` is a mount point
  and `/hpc_tools/nvidia_sdk` is writable on the login-compiler node. Verify
  the required `nfs_storage_name`; if `vast_storage_name` is set, verify that
  it selects the intended separate VAST entry. An empty `vast_storage_name`
  intentionally reuses `nfs_storage_name`.
- **Architecture is missing on a compute node**: Run `--install` on a
  login-compiler node with the same architecture, then rerun setup on the
  compute node.















