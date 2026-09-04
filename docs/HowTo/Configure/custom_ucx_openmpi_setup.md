# Configure Custom UCX and OpenMPI

## Overview

This guide covers the setup of two HPC communication tools for Slurm compiler nodes:

- **UCX (Unified Communication X)**: High-performance communication library for MPI over InfiniBand/RoCE
- **OpenMPI**: MPI implementation that integrates with UCX and Slurm

**Default Stack (Automatic)**: DOCA UCX 1.20.0 + DOCA OpenMPI 4.1.9a1 (no manual steps required)

**Custom Stack (This Guide)**: User-specified versions compiled from source (manual steps documented here)

## Prerequisites

### System Requirements

- Omnia 2.2 deployment
- Slurm cluster with login/compiler nodes
- NFS storage configured for Slurm cluster (with `slurm_share: true` in storage_config.yml)
- Sufficient disk space on NFS storage for HPC tools (~2-5 GB)

### Software Versions

- **UCX**: Default 1.19.0 (configurable)
- **OpenMPI**: Default 5.0.8 (configurable)
- **Build Dependencies**: gcc-c++, make, pmix-devel, munge-devel (automatically included)

## Procedure

### Step 1: Configure software_config.json

**Location**: `/opt/omnia/input/project_default/software_config.json`

**Purpose**: Include UCX and OpenMPI in local repository download

Add or modify the following configuration:

```json
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "partial",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64"]},
        {"name": "slurm_custom", "arch": ["x86_64"]},
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
        {"name": "ucx", "version": "1.19.0", "arch": ["x86_64"]},
        {"name": "openmpi", "version": "5.0.8", "arch": ["x86_64"]}
    ],
    "slurm_custom": [
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"}
    ]
}
```

**Important Notes**:

- Adjust versions as needed (e.g., `ucx_version: "1.20.0"`, `openmpi_version: "4.1.9"`)
- Include all required Slurm node types
- Ensure architecture matches your hardware (x86_64 or aarch64)

### Step 2: Verify Input Config Files

Ensure the following files exist in `/opt/omnia/input/project_default/config/x86_64/rhel/10.0/`:

```bash
ls -la /opt/omnia/input/project_default/config/x86_64/rhel/10.0/ | grep -E "ucx|openmpi"
```

**Expected output**:

```text
-rw-r--r--. 1 root root  353 Jun 17 03:55 ucx.json
-rw-r--r--. 1 root root  555 Jun 17 03:55 openmpi.json
```

These files define the tarball URLs and build dependencies. They should be present by default in Omnia.

### Step 3: Run local_repo.yml

Execute the local repository playbook to download UCX and OpenMPI tarballs:

```bash
cd /omnia
ansible-playbook local_repo.yml
```

**What this does**:

- Downloads UCX tarball from GitHub: `https://github.com/openucx/ucx/releases/download/v{{ ucx_version }}/ucx-{{ ucx_version }}.tar.gz`
- Downloads OpenMPI tarball from GitHub: `https://download.open-mpi.org/release/open-mpi/v{{ openmpi_version.split('.')[:2] | join('.') }}/openmpi-{{ openmpi_version }}.tar.gz`
- Uploads both to Pulp
- Creates Pulp distributions with correct base paths
- Stores tarballs in `/opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/tarball/ucx/` and `openmpi/`

**Expected outcome**:

- Playbook completes with SUCCESS status
- Tarballs accessible via Pulp at: `https://<admin_nic_ip>:2225/pulp/content/opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/tarball/ucx/ucx.tar.gz`

**Verification**:

```bash
# Check Pulp distributions (if Pulp is running)
pulp file distribution list --limit 100 | grep -E "ucx|openmpi"

# Check local tarball directories
ls -la /opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/tarball/ucx/
ls -la /opt/omnia/offline_repo/cluster/x86_64/rhel/10.0/tarball/openmpi/
```

### Step 4: Run Slurm Provisioning

Execute the Slurm provisioning playbooks to provision login/compiler nodes:

```bash
cd /omnia
ansible-playbook provision.yml
```

**What this does**:

- Mounts configured NFS storage on OIM
- Populates `/hpc_tools` directory structure on NFS storage
- Mounts `/hpc_tools` on login/compiler nodes (bind mount from NFS)
- Copies installation scripts to `/usr/local/bin/` on nodes:
  - `install_ucx.sh`
  - `install_openmpi.sh`
  - `setup_doca_mpi_env.sh` (for DOCA stack)

**Expected outcome**:

- `/hpc_tools` is mounted on login/compiler nodes
- Installation scripts exist in `/usr/local/bin/` on nodes
- DOCA MPI environment is configured automatically (default stack)

**Pre-installation verification**:

```bash
# On OIM
mount | grep <local_mount_point>
ls -la <local_mount_point>/hpc_tools

# On compiler node (SSH to compiler node)
mountpoint -q /hpc_tools && echo "Mounted" || echo "Not mounted"
ls -la /usr/local/bin/ | grep -E "ucx|openmpi"
```

### Step 5: Compile UCX on Compiler Node

SSH to the designated compiler/login node and run:

```bash
# Check NFS mount
mountpoint -q /hpc_tools || echo "ERROR: /hpc_tools not mounted"

# Run UCX installation
/usr/local/bin/install_ucx.sh

# Source environment
source /etc/profile.d/ucx.sh

# Verify installation
ucx_info -v
```

**What this does**:

- Downloads UCX tarball from Pulp
- Extracts and compiles with gcc-c++ and make
- Installs to `/hpc_tools/benchmarks/ucx`
- Sets up environment variables in `/etc/profile.d/ucx.sh`

**Expected output**:

```text
===== UCX Installation Started =====
Installation Prefix: /hpc_tools/benchmarks/ucx
[INFO] Downloading UCX source code...
[INFO] UCX download completed
[INFO] Configuring UCX build...
[INFO] Building UCX with 8 threads...
[INFO] Installing UCX...
[SUCCESS] UCX installation verified - Version: 1.19.0
```

**Verification**:

```bash
$ ucx_info -v
UCX 1.19.0
```

### Step 6: Compile OpenMPI on Compiler Node

On the same compiler/login node:

```bash
# Run OpenMPI installation
/usr/local/bin/install_openmpi.sh

# Source environment
source /etc/profile.d/openmpi.sh

# Verify installation
mpirun --version
mpicc --version
```

**What this does**:

- Downloads OpenMPI tarball from Pulp
- Detects Slurm (if `sinfo` command exists) and enables Slurm integration
- Detects UCX (if `/hpc_tools/benchmarks/ucx/bin/ucx_info` exists) and enables UCX integration
- Compiles with detected integrations
- Installs to `/hpc_tools/benchmarks/openmpi`
- Sets up environment variables in `/etc/profile.d/openmpi.sh`

**Expected output**:

```text
===== OpenMPI Installation Started =====
[INFO] Detecting Slurm integration...
[INFO] Slurm detected - enabling Slurm integration
[INFO] Detecting UCX integration...
[INFO] UCX detected - enabling UCX integration
[INFO] Configuring OpenMPI build...
[INFO] Building OpenMPI with 8 threads...
[INFO] Installing OpenMPI...
===== OpenMPI Installation Summary =====
Installation Status: SUCCESS
Integration Status:
  - Slurm Integration: ENABLED
  - UCX Integration: ENABLED
```

**Verification**:

```bash
$ mpirun --version
mpirun (Open MPI) 5.0.8

$ mpicc --version
mpicc: OpenMPI 5.0.8
```

## Verification

### Complete Environment Verification

Verify that both UCX and OpenMPI are correctly installed and integrated:

```bash
# Source both environments
source /etc/profile.d/ucx.sh
source /etc/profile.d/openmpi.sh

# Check UCX
ucx_info -v

# Check OpenMPI
mpirun --version
mpicc --version

# Check OpenMPI configuration
ompi_info --param all | grep -E "ucx|slurm"
```

### Test MPI Application

Compile and run a simple MPI application:

```bash
# Create test program
cat > hello.c <<EOF
#include <mpi.h>
#include <stdio.h>
int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    printf("Hello from rank %d of %d\n", rank, size);
    MPI_Finalize();
    return 0;
}
EOF

# Compile with OpenMPI
mpicc hello.c -o hello

# Run with MPI
mpirun -np 2 ./hello
```

## Next Steps

- [NVIDIA HPC SDK Setup](https://omnia-devel.readthedocs.io/en/omnia-docs-v2.2.0.0-r../HowTo/orchestrator/setup_nvhpc_sdk.html) - Set up NVIDIA HPC SDK for GPU-accelerated applications
- [Slurm with GPU](https://omnia-devel.readthedocs.io/en/omnia-docs-v2.2.0.0-r../HowTo/orchestrator/slurm_with_gpu.html) - Configure GPU support for Slurm nodes
- [Run HPC Benchmarks](https://omnia-devel.readthedocs.io/en/omnia-docs-v2.2.0.0-r../HowTo/orchestrator/run_hpc_benchmarks.html) - Validate cluster performance using MPI applications

## Troubleshooting

### Issue: Validation Error "slurm_share should be true"

**Cause**: UCX/OpenMPI are in `software_config.json` but `storage_config.yml` doesn't have `slurm_share: true`

**Solution**: Ensure your Slurm NFS storage has `slurm_share: true` in `storage_config.yml`. This is required for HPC tools validation.

### Issue: /hpc_tools not mounted on nodes

**Cause**: Slurm storage not configured or provisioning not run

**Solution**:

1. Ensure Slurm storage is properly configured with `slurm_share: true`
2. Re-run Slurm provisioning to mount the storage

### Issue: Tarball download fails

**Cause**: Pulp not running or tarball not in repository

**Solution**:

1. Verify Pulp is running: `pulp status`
2. Check if tarball exists in Pulp: `pulp file distribution list | grep ucx`
3. Re-run `local_repo.yml` to download tarballs

### Issue: Compilation fails

**Cause**: Missing build dependencies or insufficient disk space

**Solution**:

1. Check build dependencies: `rpm -q gcc-c++ make pmix-devel munge-devel`
2. Review installation logs: `cat /var/log/ucx_installation.log` or `cat /var/log/openmpi_installation.log`
3. Ensure sufficient disk space in `/hpc_tools`

### Issue: UCX not detected by OpenMPI

**Cause**: UCX not installed or environment not sourced

**Solution**:

1. Verify UCX installation: `ls /hpc_tools/benchmarks/ucx/bin/ucx_info`
2. Source UCX environment before OpenMPI compilation: `source /etc/profile.d/ucx.sh`
3. Re-run OpenMPI installation

### Issue: Slurm not detected by OpenMPI

**Cause**: Slurm not installed or munge not configured

**Solution**:

1. Verify Slurm is installed: `rpm -q slurm`
2. Check if `sinfo` command works: `sinfo`
3. Ensure munge is configured: `systemctl status munge`

!!! note

All installation scripts write logs to the following locations:

- **UCX**: `/var/log/ucx_installation.log`
- **OpenMPI**: `/var/log/openmpi_installation.log`

Check these files if any installation step fails.



















