
# Slurm Issues


Issues related to the Slurm job scheduler, including controller failures, node
state problems, job submission errors, and GPU detection.

## `slurmctld` not starting


???+ note "Symptom"

    The Slurm controller daemon fails to start. Running ``systemctl status
    slurmctld` shows the service as `failed` or `inactive``.

??? note "Cause"

    - The `slurm.conf` file has syntax errors or references non-existent nodes.
    - The `munge` authentication service is not running.
    - File permissions on `/var/spool/slurmctld/` are incorrect.
    - The Slurm database daemon (`slurmdbd`) is unreachable and
      `AccountingStorageEnforce` is set.

??? note "Resolution"

    1. Check the slurmctld log for specific errors:

       ```bash
       tail -100 /var/log/slurm/slurmctld.log
       ```


    2. Verify munge is running:

       ```bash
       systemctl status munge
       ```


       If munge is not running, start it:

       ```bash
       systemctl start munge
       ```


    3. Validate the Slurm configuration:

       ```bash
       slurmd -C    # Show computed configuration
       slurmctld -Dvvv    # Run in foreground with verbose logging
       ```


    4. Fix spool directory permissions:

       ```bash
       chown -R slurm:slurm /var/spool/slurmctld/
       chmod 755 /var/spool/slurmctld/
       ```


    5. If slurmdbd is the issue, see the `slurmdbd connection issues`_ section
       below.

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

       ```bash
       scontrol show node compute-03 | grep -i reason
       ```


    2. Verify `slurmd` is running on the compute node:

       ```bash
       ssh compute-03 systemctl status slurmd
       ```


       If not running:

       ```bash
       ssh compute-03 systemctl start slurmd
       ```


    3. Test network connectivity:

       ```bash
       ping compute-03
       ssh compute-03 hostname
       ```


    4. Resume the node after fixing the underlying issue:

       ```bash
       scontrol update NodeName=compute-03 State=RESUME
       ```


    5. Verify the node returns to `idle`:

       ```bash
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

       ```bash
       sinfo
       ```


    2. Verify the user's Slurm account:

       ```bash
       sacctmgr show user <username>
       ```


       If the user is not configured:

       ```bash
       sacctmgr add user <username> account=default
       ```


    3. Verify a default partition exists in `slurm.conf`:

       ```text
       # /etc/slurm/slurm.conf
       PartitionName=normal Nodes=compute-[01-10] Default=YES MaxTime=INFINITE State=UP
       ```


    4. If resources are the issue, check available resources:

       ```bash
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
    - The MySQL/MariaDB database backend is down.
    - Network or firewall issues between the controller and the database node.
    - Incorrect database credentials in `slurmdbd.conf`.

??? note "Resolution"

    1. Check `slurmdbd` status:

       ```bash
       systemctl status slurmdbd
       ```


    2. Check the database backend:

       ```bash
       systemctl status mariadb    # or mysql
       ```


    3. Verify `slurmdbd.conf` settings:

       ```bash
       grep -i storage /etc/slurm/slurmdbd.conf
       ```


    4. Test database connectivity:

       ```bash
       mysql -u slurm -p -h localhost slurm_acct_db -e "SELECT 1;"
       ```


    5. Check the `slurmdbd` log:

       ```bash
       tail -100 /var/log/slurm/slurmdbd.log
       ```


    6. If credentials changed, update `slurmdbd.conf` and restart:

       ```bash
       systemctl restart slurmdbd
       systemctl restart slurmctld
       ```


## GPU not detected by Slurm


???+ note "Symptom"

    GPU nodes are provisioned but Slurm does not show GPU resources. Running
    `scontrol show node <gpu_node>` shows no `Gres` entries, or GPU jobs
    fail with:

    ```text
    srun: error: Unable to allocate resources: Requested node configuration is not available
    ```


??? note "Cause"

    - GPU drivers (CUDA or ROCm) are not installed on the compute node.
    - The `gres.conf` file does not list the GPUs.
    - The `slurm.conf` does not define GRES for the GPU nodes.
    - The `nvidia-smi` or `rocm-smi` tool does not detect the GPU hardware.

??? note "Resolution"

    1. Verify the GPU is visible to the OS:

       ```bash
       # NVIDIA
       ssh <gpu_node> nvidia-smi

       # AMD
       ssh <gpu_node> rocm-smi
       ```


    2. If the GPU driver is not installed, re-run the Omnia playbook with GPU
       tags:

       ```bash
       ssh omnia_core
       cd /omnia
       ansible-playbook playbooks/omnia.yml --tags gpu
       ```


    3. Verify `gres.conf` on the compute node:

       ```bash
       ssh <gpu_node> cat /etc/slurm/gres.conf
       ```


       Expected content:

       ```text
       # /etc/slurm/gres.conf
       NodeName=gpu-01 Name=gpu Type=a100 File=/dev/nvidia[0-3]
       ```


    4. Verify `slurm.conf` includes GRES definitions:

       ```text
       GresTypes=gpu
       NodeName=gpu-01 Gres=gpu:a100:4 ...
       ```


    5. After updating configuration files, restart Slurm services:

       ```bash
       # On the control node
       systemctl restart slurmctld

       # On the GPU compute node
       ssh <gpu_node> systemctl restart slurmd
       ```


    6. Confirm GPUs are registered:

       ```bash
       scontrol show node <gpu_node> | grep Gres
       ```


!!! info

    - [Setup Slurm](../HowTo/Slurm/setup_slurm.md) -- Slurm cluster setup guide.
    - [Slurm With Gpu](../HowTo/Slurm/slurm_with_gpu.md) -- GPU configuration for Slurm.
    - [Add Remove Nodes](../Operations/add_remove_nodes.md) -- Adding or removing Slurm nodes.
