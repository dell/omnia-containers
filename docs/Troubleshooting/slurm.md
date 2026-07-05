
# Slurm Issues


Issues related to the Slurm job scheduler, including controller failures, node
state problems, job submission errors, and GPU detection.

## `slurmctld` not starting


???+ note "Symptom"

    The Slurm controller daemon fails to start. Running `systemctl status
    slurmctld` shows the service as `failed` or `inactive`.

??? note "Cause"

    - The `slurm.conf` file has syntax errors or references non-existent nodes.
    - The `munge` authentication service is not running.
    - File permissions on `/var/spool/slurmctld/` are incorrect.
    - The Slurm database daemon (`slurmdbd`) is unreachable and
      `AccountingStorageEnforce` is set.

??? note "Resolution"

    1. Check the slurmctld log for specific errors:

       ```bash title="Run on: Slurm controller node"
       tail -100 /var/log/slurm/slurmctld.log
       ```


    2. Verify munge is running:

       ```bash title="Run on: Slurm controller node"
       systemctl status munge
       ```


       If munge is not running, start it:

       ```bash title="Run on: Slurm controller node"
       systemctl start munge
       ```


    3. Validate the Slurm configuration:

       ```bash title="Run on: Slurm controller node"
       slurmd -C    # Show computed configuration
       slurmctld -Dvvv    # Run in foreground with verbose logging
       ```


    4. Fix spool directory permissions:

       ```bash title="Run on: Slurm controller node"
       chown -R slurm:slurm /var/spool/slurmctld/
       chmod 755 /var/spool/slurmctld/
       ```


    5. If slurmdbd is the issue, see the
       [slurmdbd connection issues](#slurmdbd-connection-issues) section below.

## Nodes Entering DRAINED State


???+ note "Symptom"

    Slurm nodes enter `DRAINED` state unexpectedly. Error messages include:

    ```text title="Expected output"
    State=IDLE+DRAIN Reason=Kill task failed
    ```

    or:

    ```text title="Expected output"
    State=DOWN+DRAIN Reason=Not responding
    ```

??? note "Cause"

    - The epilog script (`/etc/slurm/epilog.d/logout_user.sh`) is not
      executable.

??? note "Resolution"

    1. Fix the epilog script permissions and reconfigure Slurm:

       ```bash title="Run on: Slurm controller node"
       chmod 0755 /etc/slurm/epilog.d/logout_user.sh
       scontrol reconfigure
       ```

## Nodes stuck in DOWN state


???+ note "Symptom"

    `sinfo` shows one or more nodes in `down` or `down*` state:

    ```text
    PARTITION  AVAIL  TIMELIMIT  NODES  STATE  NODELIST
    normal*       up   infinite      1  down*  compute-03
    ```


??? note "Cause"

    - The `slurmd` service on the compute node is not running.
    - Network connectivity between the control node and the compute node is
      broken.
    - The node was manually set to DOWN and not resumed.
    - Hardware issues (memory errors, disk failures) triggered an automatic
      drain.

??? note "Resolution"

    1. Check why the node is down:

       ```bash title="Run on: Slurm controller node"
       scontrol show node compute-03 | grep -i reason
       ```


    2. Verify `slurmd` is running on the compute node:

       ```bash title="Run on: Slurm controller node"
       ssh compute-03 systemctl status slurmd
       ```


       If not running:

       ```bash title="Run on: Slurm controller node"
       ssh compute-03 systemctl start slurmd
       ```


    3. Test network connectivity:

       ```bash title="Run on: Slurm controller node"
       ping compute-03
       ssh compute-03 hostname
       ```


    4. Resume the node after fixing the underlying issue:

       ```bash title="Run on: Slurm controller node"
       scontrol update NodeName=compute-03 State=RESUME
       ```


    5. Verify the node returns to `idle`:

       ```bash title="Run on: Slurm controller node"
       sinfo -n compute-03
       ```


## Job submission failures


???+ note "Symptom"

    Submitting a job with `sbatch` or `srun` fails with errors such as:

    ```text
    sbatch: error: Batch job submission failed: Invalid account or account/partition combination specified
    srun: error: Unable to allocate resources: No partition specified or system default partition
    ```


??? note "Cause"

    - The user's account is not configured in Slurm accounting.
    - No default partition is defined in `slurm.conf`.
    - The requested resources exceed what is available in the cluster.

??? note "Resolution"

   1. Check available partitions:

       ```bash title="Run on: Slurm controller node"
       sinfo
       ```


   2. Verify a default partition exists in `slurm.conf`:

       ```text title="File: /etc/slurm/slurm.conf"
       PartitionName=normal Nodes=compute-[01-10] Default=YES MaxTime=INFINITE State=UP
       ```


   3. If resources are the issue, check available resources:

       ```bash title="Run on: Slurm controller node"
       sinfo -N -l
       squeue    # Check for jobs consuming resources
       ```


## `slurmdbd` connection issues


???+ note "Symptom"

    `slurmctld` logs show errors connecting to the Slurm database daemon:

    ```text
    error: slurmdbd: Sending PersistInit msg: CONNECTION REFUSED
    error: slurmdbd: DBD_ID_REGISTER failed
    ```


??? note "Cause"

    - The `slurmdbd` service is not running.
    - The MariaDB database backend is down.
    - Network or firewall issues between the controller and the database node.
    - Incorrect database credentials in `slurmdbd.conf`.

??? note "Resolution"

    1. Check `slurmdbd` status:

       ```bash title="Run on: Slurm controller node"
       systemctl status slurmdbd
       ```


    2. Check the database backend:

       ```bash title="Run on: Slurm controller node"
       systemctl status mariadb
       ```


    3. Verify `slurmdbd.conf` settings:

       ```bash title="Run on: Slurm controller node"
       grep -i storage /etc/slurm/slurmdbd.conf
       ```


    4. Test database connectivity:

       ```bash title="Run on: Slurm controller node"
       mysql -u slurm -p -h localhost slurm_acct_db -e "SELECT 1;"
       ```


    5. Check the `slurmdbd` log:

       ```bash title="Run on: Slurm controller node"
       tail -100 /var/log/slurm/slurmdbd.log
       ```


    6. If credentials changed, update `slurmdbd.conf` and restart:

       ```bash title="Run on: Slurm controller node"
       systemctl restart slurmdbd
       systemctl restart slurmctld
       ```


## NVIDIA GPU, CUDA, and DCGM Issues

### `nvidia-smi` not found or driver not communicating


???+ note "Symptom"

    `nvidia-smi: command not found` or `nvidia-smi` exits with a non-zero
    return code.

??? note "Cause"

    - NVIDIA driver installation failed during provisioning.
    - GPU hardware is absent on this node.

??? note "Resolution"

    1. Verify GPU hardware is present on the node:

       ```bash title="Run on: GPU compute node"
       lspci | grep -i nvidia
       ```

    2. If confirmed present, re-install the driver:

       ```bash title="Run on: GPU compute node"
       dnf install -y cuda-drivers
       ```

    3. Review the driver installation log for error details:

       ```bash title="Run on: GPU compute node"
       cat /var/log/nvidia_install.log
       ```

### CUDA toolkit not available on node


???+ note "Symptom"

    `nvcc: command not found` or `/usr/local/cuda` is empty.

??? note "Cause"

    - Toolkit installation did not complete on the designated installer
      node due to a repository or NFS error.
    - NFS mount for the CUDA toolkit was not established at provisioning
      time.

??? note "Resolution"

    1. Verify the NFS mount at `/usr/local/cuda` is present:

       ```bash title="Run on: GPU compute node"
       mount | grep cuda
       ```

    2. If absent, re-mount manually. If the toolkit is not installed on
       the NFS share, review the installation log on the installer node:

       ```bash title="Run on: installer node (login/compiler or compute)"
       cat /var/log/cuda_toolkit_install.log
       ```

### CUDA toolkit NFS mount failed


???+ note "Symptom"

    `/usr/local/cuda` is empty or not mounted after provisioning.

??? note "Cause"

    - NFS server was unreachable at provisioning time.
    - The NFS export is not configured with `no_root_squash`.

??? note "Resolution"

    1. Verify NFS server reachability from the node.

    2. Verify the NFS export includes `no_root_squash`.

    3. Re-mount manually:

       ```bash title="Run on: GPU compute node"
       mount -t nfs <NFS_SERVER>:<path>/hpc_tools/cuda /usr/local/cuda
       ```

    4. Verify the `fstab` entry is present for persistence.

### `nvidia-dcgm` service inactive or failed


???+ note "Symptom"

    `systemctl status nvidia-dcgm` shows `inactive` or `failed` state.

??? note "Cause"

    - DCGM package installation failed due to an unavailable repository
      or a CUDA version mismatch.
    - The NVIDIA driver was not functional at the time DCGM attempted to
      start.

??? note "Resolution"

    1. Verify driver is functional:

       ```bash title="Run on: GPU compute node"
       nvidia-smi
       ```

    2. Identify the installed CUDA version:

       ```bash title="Run on: GPU compute node"
       nvidia-smi | grep "CUDA Version"
       ```

    3. Re-install the matching DCGM package and restart the service.

    4. Review the DCGM setup log for errors:

       ```bash title="Run on: GPU compute node"
       cat /var/log/dcgm_setup.log
       ```

### DCGM not installed


???+ note "Symptom"

    `nvidia-dcgm` service is not present on the Slurm node, and
    `/var/log/dcgm_setup.log` is missing.

??? note "Cause"

    - `dcgm.metrics_enabled` is set to `false` under `telemetry_sources`
      in `telemetry_config.yml`, so Omnia intentionally skips DCGM
      installation during Slurm node cloud-init.

??? note "Resolution"

    1. Set `dcgm.metrics_enabled: true` under `telemetry_sources` in
       `input/telemetry_config.yml`.

    2. Re-run provisioning for affected Slurm nodes.

    3. Validate:

       ```bash title="Run on: GPU compute node"
       systemctl status nvidia-dcgm
       dcgmi discovery -l
       ```

### DCGM package version mismatch


???+ note "Symptom"

    DCGM package installation fails with `No match for argument` or
    `No packages found`.

??? note "Cause"

    - The CUDA major version on the node does not have a matching
      `datacenter-gpu-manager-4-cuda<N>` package available in the
      configured local repository.

??? note "Resolution"

    1. Verify the CUDA version:

       ```bash title="Run on: GPU compute node"
       nvidia-smi | grep "CUDA Version"
       ```

    2. Confirm the corresponding DCGM package is present in the local
       Pulp repository.

    3. Update `local_repo_config.yml` to include the correct DCGM
       package version and re-run `local_repo.yml`.

### `nvidia-peermem` not loading


???+ note "Symptom"

    `lsmod` does not show `nvidia_peermem`. Workloads requiring GPUDirect
    RDMA fail to initialize.

??? note "Cause"

    - Kernel headers were not available at provisioning time, causing the
      DKMS build to fail.
    - Base NVIDIA kernel modules were not loaded prior to
      `nvidia-peermem` load attempt.

??? note "Resolution"

    1. Verify kernel headers:

       ```bash title="Run on: GPU compute node"
       ls /lib/modules/$(uname -r)/build
       ```

    2. Install if missing:

       ```bash title="Run on: GPU compute node"
       dnf install -y kernel-devel-$(uname -r)
       ```

    3. Load the module:

       ```bash title="Run on: GPU compute node"
       modprobe nvidia-peermem
       ```

    4. Review the installation log:

       ```bash title="Run on: GPU compute node"
       cat /var/log/nvidia_peermem_install.log
       ```

!!! note
    If RDMA is not required for any workload on this node, this warning
    is non-blocking.


## Munge authentication failure


???+ note "Symptom"

    Slurm commands fail with authentication errors such as:

    ```text
    srun: error: Munge encode failed: Failed to access"/var/run/munge/munge.socket.2"
    slurmd: error: Munge authentication failed
    ```

??? note "Cause"

    - The `munge` service is not running on one or more nodes.
    - The Munge key is not identical across all nodes in the cluster.

??? note "Resolution"

    1. Verify Munge is running on all nodes:

       ```bash title="Run on: omnia_core container"
       ansible slurm_cluster -m shell -a "systemctl status munge"
       ```

    2. Verify the Munge key is identical across all nodes:

       ```bash title="Run on: omnia_core container"
       ansible slurm_cluster -m shell -a "md5sum /etc/munge/munge.key"
       ```

       All nodes should report the same MD5 hash.

    3. If keys differ, redistribute the key from the controller node and
       restart Munge on all affected nodes:

       ```bash title="Run on: affected node"
       systemctl restart munge
       ```

## MariaDB connection error


???+ note "Symptom"

    `slurmdbd` fails to start or `slurmctld` logs show database connection
    errors. The `sacctmgr` command returns errors.

??? note "Cause"

    - The MariaDB service is not running on the Slurm controller node.
    - Database credentials in `slurmdbd.conf` do not match the MariaDB
      configuration.
    - The Slurm database was not initialized.

??? note "Resolution"

    1. Check MariaDB is running on the control node:

       ```bash title="Run on: Slurm controller node"
       systemctl status mariadb
       ```

    2. Test database connectivity:

       ```bash title="Run on: Slurm controller node"
       mysql -u slurm -p -e "SHOW DATABASES;"
       ```

    3. If MariaDB is stopped, start it and restart Slurm services:

       ```bash title="Run on: Slurm controller node"
       systemctl start mariadb
       systemctl restart slurmdbd
       systemctl restart slurmctld
       ```

## `slurmctld` fails to start after config rollback


???+ note "Symptom"

    After rolling back a Slurm configuration backup, `slurmctld` fails to
    start.

??? note "Cause"

    - The backup may reference nodes that no longer exist in the cluster.

??? note "Resolution"

    1. Run cleanup and redeploy with `provision.yml`:

       ```bash title="Run on: omnia_core container"
       ansible-playbook /opt/omnia/utils/slurm_config_util.yml --tags slurm_cleanup
       ansible-playbook provision.yml
       ```

## New nodes show DOWN after adding


???+ note "Symptom"

    Newly added compute nodes appear as `down` in `sinfo` after running
    `provision.yml` and PXE booting.

??? note "Cause"

    - The `slurmd` service failed to start on the new node.
    - Cloud-init did not complete successfully.

??? note "Resolution"

    1. Verify `slurmd` is running on the new node:

       ```bash title="Run on: new compute node"
       systemctl status slurmd
       journalctl -u slurmd --no-pager -n 20
       ```

    2. Check cloud-init completed successfully:

       ```bash title="Run on: new compute node"
       cat /var/log/cloud-init-output.log | tail -20
       ```

    3. Resume the node from the controller:

       ```bash title="Run on: Slurm controller node"
       scontrol update nodename=<node> state=resume reason="added"
       ```

## Node still appears in sinfo after removal


???+ note "Symptom"

    After removing a node, it still appears in `sinfo` output.

??? note "Cause"

    - The `provision.yml` playbook did not complete successfully.
    - The Slurm controller has not been reconfigured.

??? note "Resolution"

    1. Verify that `provision.yml` completed successfully and check the
       Slurm controller logs:

       ```bash title="Run on: Slurm controller node"
       journalctl -u slurmctld --no-pager -n 20
       ```

    2. If jobs were running on the removed node, they may show as `FAILED`
       or `NODE_FAIL` in accounting:

       ```bash title="Run on: Slurm controller node"
       sacct --starttime=today --state=FAILED,NODE_FAIL
       ```

       Resubmit affected jobs as needed.

## CUDA Toolkit and DCGM Setup Failure: Manual Recovery


???+ note "Symptom"

    Automated GPU setup fails during provisioning.

??? note "Cause"

    - Repository unavailability, NFS connectivity issues, or node
      initialization errors.

??? note "Resolution"

    Perform all recovery steps as `root` on the affected node. Verify
    that the shared NFS path is reachable and repositories are accessible
    before proceeding.

    **Step 1: Verify Prerequisites**

    ```bash title="Run on: affected GPU node"
    showmount -e <NFS_SERVER_IP>
    lspci | grep -i nvidia
    dnf repolist | grep -i cuda
    df -h /usr/local
    ```

    **Step 2: Recover NVIDIA Driver**

    If `nvidia-smi` is missing or returning errors:

    ```bash title="Run on: affected GPU node"
    dnf install -y cuda-drivers
    nvidia-smi
    ```

    **Step 3: Recover CUDA Toolkit**

    The recovery procedure differs depending on the node topology.

    *Scenario A -- Login or compiler node present in the cluster:*

    The login/compiler node is the designated installer. It installs the
    toolkit to the shared NFS location at `/hpc_tools/cuda`. Compute nodes
    mount this path at `/usr/local/cuda`.

    On the login or compiler node:

    ```bash title="Run on: login/compiler node"
    ls /hpc_tools/cuda/bin/nvcc 2>/dev/null && echo "Toolkit present" || echo "Toolkit NOT present"
    ```

    If not present, trigger the installation manually:

    ```bash title="Run on: login/compiler node"
    CUDA_INSTALL_MANUAL=true /usr/local/bin/install_cuda_toolkit.sh
    ```

    On a compute node (after toolkit is confirmed on NFS):

    ```bash title="Run on: GPU compute node"
    mount | grep cuda
    ```

    If absent, re-mount manually:

    ```bash title="Run on: GPU compute node"
    mount -t nfs <NFS_SERVER>:<hpc_tools_path>/hpc_tools/cuda /usr/local/cuda
    ```

    *Scenario B -- No login or compiler node in the cluster:*

    Compute nodes install the toolkit themselves to `/hpc_tools/cuda`.

    ```bash title="Run on: any compute node"
    ls /hpc_tools/cuda/bin/nvcc 2>/dev/null && echo "Toolkit present" || echo "Toolkit NOT present"
    ```

    If not present:

    ```bash title="Run on: any compute node"
    CUDA_INSTALL_MANUAL=true /usr/local/bin/install_cuda_toolkit.sh
    ```

    !!! note
        Run this only after confirming no active toolkit installation is
        already in progress. Review `/var/log/cuda_toolkit_install.log`
        to check current installation status.

    **Step 4: Recover DCGM**

    If the `nvidia-dcgm` service is inactive or failed:

    ```bash title="Run on: GPU compute node"
    nvidia-smi | grep "CUDA Version"
    dnf install -y datacenter-gpu-manager-4-cuda<N>
    systemctl enable nvidia-dcgm
    systemctl start nvidia-dcgm
    ```

    Validate:

    ```bash title="Run on: GPU compute node"
    systemctl status nvidia-dcgm
    dcgmi discovery -l
    ```

    **Step 5: Recover nvidia-peermem (RDMA environments only)**

    ```bash title="Run on: GPU compute node"
    ls /lib/modules/$(uname -r)/build
    dnf install -y kernel-devel-$(uname -r)
    modprobe nvidia-peermem
    ```

    Validate:

    ```bash title="Run on: GPU compute node"
    lsmod | grep -E 'nv_peer_mem|nvidia_peermem'
    ```

    **Log file reference:**

    - `/var/log/nvidia_install.log` -- NVIDIA driver installation output
    - `/var/log/cuda_toolkit_install.log` -- CUDA toolkit installation
      output and timing
    - `/var/log/dcgm_setup.log` -- DCGM package install, service startup,
      GPU discovery
    - `/var/log/nvidia_peermem_install.log` -- nvidia-peermem DKMS build
      and load output

## Benchmark assets missing on Slurm nodes


???+ note "Symptom"

    - Benchmark tool directories are missing or incomplete under
      `/hpc_tools`.
    - Expected benchmark artifacts are not visible on
      login/compiler/compute nodes.

??? note "Cause"

    - Shared NFS path (`/hpc_tools`) is not mounted or not accessible.
    - `pull_benchmarks.sh` or `benchmark_tools.list` is missing under
      `/hpc_tools/scripts`.
    - Pulp mirror endpoint is unreachable from the node.
    - Required benchmark content is not available in local
      repository/Pulp.
    - Tool directory already exists and contains files (script skips
      re-download by design).
    - Architecture mismatch (for example, `msr-safe` on `aarch64`, which
      is skipped by design).

??? note "Resolution"

    1. Verify NFS and scripts path:

       ```bash title="Run on: affected node"
       ls -ld /hpc_tools
       ls -l /hpc_tools/scripts
       ```

       Expected files: `/hpc_tools/scripts/pull_benchmarks.sh` and
       `/hpc_tools/scripts/benchmark_tools.list`.

    2. Run the runtime staging script and review output:

       ```bash title="Run on: affected node"
       /hpc_tools/scripts/pull_benchmarks.sh
       ```

    3. Review the runtime log:

       ```bash title="Run on: affected node"
       tail -n 200 /var/log/pull_benchmarks.log
       ```

    4. Validate staged benchmark directories:

       ```bash title="Run on: affected node"
       ls -l /hpc_tools/osu-micro-benchmarks /hpc_tools/imb /hpc_tools/likwid /hpc_tools/papi
       ```

    5. If a tool was skipped as already present, remove that tool
       directory only if refresh is required, then re-run
       `/hpc_tools/scripts/pull_benchmarks.sh`.

!!! note
    `msr-safe` is expected only on `x86_64`.

## `sacct` erroring out or returning empty results


???+ note "Symptom"

    The `sacct` command returns no output or empty results when querying
    job accounting information.

??? note "Cause"

    - `slurmdbd` service is not running.
    - MariaDB service is not running (`slurmdbd` depends on MariaDB).
    - `slurmdbd` cannot communicate with the database.
    - Port 6819 (`slurmdbd` port) is not listening.

??? note "Resolution"

    1. Check if `slurmdbd` service is running:

       ```bash title="Run on: Slurm controller node"
       systemctl status slurmdbd
       ```

    2. Check if MariaDB service is running:

       ```bash title="Run on: Slurm controller node"
       systemctl status mariadb
       ```

    3. Check the `slurmdbd` logs:

       ```bash title="Run on: Slurm controller node"
       tail -50 /var/log/slurm/slurmdbd.log
       ```

    4. Check the `slurmdbd` port:

       ```bash title="Run on: Slurm controller node"
       ss -tlnp | grep 6819
       ```

    5. Restart the services accordingly:

       ```bash title="Run on: Slurm controller node"
       systemctl restart slurmdbd
       systemctl restart mariadb
       ```

## Slurm RPM build failures


???+ note "Symptom"

    `rpmbuild` fails when building Slurm RPMs from source.

??? note "Cause"

    - Missing development dependencies on the build host.
    - Missing kernel headers on aarch64 build hosts.
    - CUDA toolkit not installed before building with GPU support.

??? note "Resolution"

    1. Install missing development packages:

       ```bash title="Run on: build host"
       dnf install -y <missing-package>-devel
       ```

    2. For aarch64 builds, install kernel headers:

       ```bash title="Run on: aarch64 build host"
       dnf install -y kernel-devel kernel-headers
       ```

    3. Verify CUDA is installed before running `rpmbuild` with GPU support:

       ```bash title="Run on: build host"
       ls /usr/local/cuda/lib64/stubs/libnvidia-ml.so
       ```

!!! info

    - [Setup Slurm](../HowTo/Slurm/setup_slurm.md) -- Slurm cluster setup guide.
    - [Slurm With Gpu](../HowTo/Slurm/slurm_with_gpu.md) -- GPU configuration for Slurm.
    - [Add Remove Nodes](../Operations/add_remove_nodes.md) -- Adding or removing Slurm nodes.
