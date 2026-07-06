# Slurm Issues

Issues related to the Slurm job scheduler, including node state problems, NVIDIA GPU/CUDA/DCGM, benchmarks, and accounting.

## Nodes entering DRAINED state

???+ note "Symptom"

    Slurm nodes enter `DRAINED` state unexpectedly. Error messages include:

    - `State=IDLE+DRAIN Reason=Kill task failed`
    - `State=DOWN+DRAIN Reason=Not responding`

??? note "Cause"

    Epilog script not executable.

??? note "Resolution"

    ```bash title="Run on: Slurm control node"
    chmod 0755 /etc/slurm/epilog.d/logout_user.sh
    scontrol reconfigure
    ```

## NVIDIA GPU, CUDA, and DCGM issues

### `nvidia-smi` not found or driver not communicating

???+ note "Symptom"

    `nvidia-smi: command not found` or `nvidia-smi` exits with a non-zero return code.

??? note "Cause"

    NVIDIA driver installation failed during provisioning, or GPU hardware is absent on the node.

??? note "Resolution"

    1. Verify GPU hardware is present on the node.
    2. If confirmed present, re-install the driver:

        ```bash title="Run on: compute node"
        dnf install -y cuda-drivers
        ```

    3. Review `/var/log/nvidia_install.log` for error details.

### CUDA Toolkit not available (`nvcc` not found)

???+ note "Symptom"

    `nvcc: command not found` or `/usr/local/cuda` is empty.

??? note "Cause"

    - Toolkit installation did not complete on the designated installer node due to a repository or NFS error.
    - NFS mount for the CUDA toolkit was not established at provisioning time.

??? note "Resolution"

    1. Verify the NFS mount at `/usr/local/cuda` is present:

        ```bash title="Run on: compute node"
        mount | grep cuda
        ```

    2. If absent, re-mount manually. If the toolkit is not installed on the NFS share, review `/var/log/cuda_toolkit_install.log` on the installer node.

### CUDA Toolkit NFS mount failed

???+ note "Symptom"

    `/usr/local/cuda` is empty or not mounted after provisioning.

??? note "Cause"

    NFS server was unreachable at provisioning time, or the NFS export is not configured with `no_root_squash`.

??? note "Resolution"

    1. Verify NFS server reachability from the node.
    2. Verify the NFS export includes `no_root_squash`.
    3. Re-mount manually:

        ```bash title="Run on: compute node"
        mount -t nfs <NFS_SERVER>:<path>/hpc_tools/cuda /usr/local/cuda
        ```

    4. Verify the `fstab` entry is present for persistence.

### `nvidia-dcgm` service inactive or failed

???+ note "Symptom"

    `systemctl status nvidia-dcgm` shows `inactive` or `failed` state.

??? note "Cause"

    - DCGM package installation failed due to an unavailable repository or a CUDA version mismatch.
    - The NVIDIA driver was not functional at the time DCGM attempted to start.

??? note "Resolution"

    1. Verify driver is functional: `nvidia-smi`.
    2. Identify the installed CUDA version: `nvidia-smi | grep "CUDA Version"`.
    3. Re-install the matching DCGM package and restart the service.
    4. Review `/var/log/dcgm_setup.log` for errors.

### DCGM not installed (`dcgm.metrics_enabled` disabled)

???+ note "Symptom"

    `nvidia-dcgm` service is not present on Slurm node, and `/var/log/dcgm_setup.log` is missing.

??? note "Cause"

    `dcgm.metrics_enabled` is set to `false` under `telemetry_sources` in `telemetry_config.yml`, so Omnia intentionally skips DCGM installation during Slurm node cloud-init.

??? note "Resolution"

    Set `dcgm.metrics_enabled: true` under `telemetry_sources` in `input/telemetry_config.yml`, re-run provisioning for affected Slurm nodes, then validate with `systemctl status nvidia-dcgm` and `dcgmi discovery -l`.

### DCGM package version mismatch

???+ note "Symptom"

    DCGM package installation fails with `No match for argument` or `No packages found`.

??? note "Cause"

    The CUDA major version on the node does not have a matching `datacenter-gpu-manager-4-cuda<N>` package available in the configured local repository.

??? note "Resolution"

    1. Verify the CUDA version: `nvidia-smi | grep "CUDA Version"`.
    2. Confirm the corresponding DCGM package is present in the local Pulp repository.
    3. Update `local_repo_config.yml` to include the correct DCGM package version and re-run `local_repo.yml`.

### `nvidia-peermem` not loading

???+ note "Symptom"

    `lsmod` does not show `nvidia_peermem`; workloads requiring GPUDirect RDMA fail to initialize.

??? note "Cause"

    - Kernel headers were not available at provisioning time, causing the DKMS build to fail.
    - Base NVIDIA kernel modules were not loaded prior to `nvidia-peermem` load attempt.

??? note "Resolution"

    1. Verify kernel headers:

        ```bash title="Run on: compute node"
        ls /lib/modules/$(uname -r)/build
        ```

    2. Install if missing:

        ```bash title="Run on: compute node"
        dnf install -y kernel-devel-$(uname -r)
        ```

    3. Load the module:

        ```bash title="Run on: compute node"
        modprobe nvidia-peermem
        ```

    4. Review `/var/log/nvidia_peermem_install.log` for details.

    !!! note

        If RDMA is not required for any workload on this node, this warning is non-blocking.

## CUDA Toolkit and DCGM setup failure: manual recovery

???+ note "Symptom"

    Automated GPU setup fails during provisioning.

??? note "Cause"

    Repository unavailability, NFS connectivity issues, or node initialization errors.

??? note "Resolution"

    Perform all recovery steps as `root` on the affected node. Verify that the shared NFS path is reachable and repositories are accessible before proceeding.

    **Step 1: Verify prerequisites**

    ```bash title="Run on: compute node"
    showmount -e <NFS_SERVER_IP>
    lspci | grep -i nvidia
    dnf repolist | grep -i cuda
    df -h /usr/local
    ```

    **Step 2: Recover NVIDIA driver**

    ```bash title="Run on: compute node"
    dnf install -y cuda-drivers
    nvidia-smi
    ```

    **Step 3: Recover CUDA Toolkit**

    - **Scenario A — Login or compiler node present**: The login/compiler node installs the toolkit to `/hpc_tools/cuda`. Compute nodes mount this path at `/usr/local/cuda`. On the login/compiler node:

        ```bash title="Run on: login/compiler node"
        ls /hpc_tools/cuda/bin/nvcc 2>/dev/null && echo "Toolkit present" || echo "Toolkit NOT present"
        CUDA_INSTALL_MANUAL=true /usr/local/bin/install_cuda_toolkit.sh
        ```

    - **Scenario B — No login or compiler node**: Compute nodes install the toolkit to `/hpc_tools/cuda` via NFS. On any compute node:

        ```bash title="Run on: compute node"
        ls /hpc_tools/cuda/bin/nvcc 2>/dev/null && echo "Toolkit present" || echo "Toolkit NOT present"
        CUDA_INSTALL_MANUAL=true /usr/local/bin/install_cuda_toolkit.sh
        ```

    !!! note

        Run the install script only after confirming no active toolkit installation is already in progress. Review `/var/log/cuda_toolkit_install.log` to check current installation status.

    **Step 4: Recover DCGM**

    ```bash title="Run on: compute node"
    nvidia-smi | grep "CUDA Version"
    dnf install -y datacenter-gpu-manager-4-cuda<N>
    systemctl enable nvidia-dcgm
    systemctl start nvidia-dcgm
    dcgmi discovery -l
    ```

    **Step 5: Recover `nvidia-peermem` (RDMA environments only)**

    ```bash title="Run on: compute node"
    ls /lib/modules/$(uname -r)/build
    dnf install -y kernel-devel-$(uname -r)
    modprobe nvidia-peermem
    lsmod | grep -E 'nv_peer_mem|nvidia_peermem'
    ```

    **Log file reference:**

    - `/var/log/nvidia_install.log` -- NVIDIA driver installation output
    - `/var/log/cuda_toolkit_install.log` -- CUDA toolkit installation output
    - `/var/log/dcgm_setup.log` -- DCGM package install, service startup, GPU discovery
    - `/var/log/nvidia_peermem_install.log` -- `nvidia-peermem` DKMS build and load output

## Benchmark assets missing on Slurm nodes

???+ note "Symptom"

    - Benchmark tool directories are missing or incomplete under `/hpc_tools`.
    - Expected benchmark artifacts are not visible on login/compiler/compute nodes.

??? note "Cause"

    - Shared NFS path (`/hpc_tools`) is not mounted or not accessible.
    - `pull_benchmarks.sh` or `benchmark_tools.list` is missing under `/hpc_tools/scripts`.
    - Pulp mirror endpoint is unreachable from the node.
    - Tool directory already exists and contains files (script skips re-download by design).
    - Architecture mismatch (for example, `msr-safe` on `aarch64`, which is skipped by design).

??? note "Resolution"

    1. Verify NFS and scripts path:

        ```bash title="Run on: compute node"
        ls -ld /hpc_tools
        ls -l /hpc_tools/scripts
        ```

    2. Run runtime staging script:

        ```bash title="Run on: compute node"
        /hpc_tools/scripts/pull_benchmarks.sh
        ```

    3. Review runtime log:

        ```bash title="Run on: compute node"
        tail -n 200 /var/log/pull_benchmarks.log
        ```

    4. Validate staged benchmark directories:

        ```bash title="Run on: compute node"
        ls -l /hpc_tools/osu-micro-benchmarks /hpc_tools/imb /hpc_tools/likwid /hpc_tools/papi /hpc_tools/geopm /hpc_tools/sionlib
        ```

    !!! note

        `msr-safe` is expected only on `x86_64`.

    5. If a tool was skipped as already present, remove that tool directory only if a refresh is required, then re-run `/hpc_tools/scripts/pull_benchmarks.sh`.

## `sacct` erroring out or returning empty results

???+ note "Symptom"

    The `sacct` command returns no output or empty results when querying job accounting information.

??? note "Cause"

    - `slurmdbd` service is not running.
    - MariaDB service is not running (`slurmdbd` depends on MariaDB).
    - `slurmdbd` cannot communicate with the database.
    - Port 6819 (`slurmdbd` port) is not listening.

??? note "Resolution"

    1. Check if `slurmdbd` is running:

        ```bash title="Run on: Slurm control node"
        systemctl status slurmdbd
        ```

    2. Check if MariaDB is running:

        ```bash title="Run on: Slurm control node"
        systemctl status mariadb
        ```

    3. Check `slurmdbd` logs:

        ```bash title="Run on: Slurm control node"
        tail -50 /var/log/slurm/slurmdbd.log
        ```

    4. Check the `slurmdbd` port:

        ```bash title="Run on: Slurm control node"
        ss -tlnp | grep 6819
        ```

    5. Restart the services:

        ```bash title="Run on: Slurm control node"
        systemctl restart slurmdbd
        systemctl restart mariadb
        ```

!!! info

    - [Setup Slurm](../HowTo/Slurm/setup_slurm.md) -- Slurm cluster setup guide.
    - [Slurm With GPU](../HowTo/Slurm/slurm_with_gpu.md) -- GPU configuration for Slurm.
    - [Add Remove Nodes](../Operations/add_remove_nodes.md) -- Adding or removing Slurm nodes.
