Step 11: Set up Slurm on nodes
==============

**Prerequisites**

* Provide the repository with slurm v25.X rpms.
.. note:: If any Slurm nodes (Slurm controller, compute nodes, login nodes, or login/compile nodes) have an InfiniBand interface and ``ib_network`` details are defined in network_spec.yml (`Update the Input Parameters for Discovering the Nodes <../../Provision/provisionparams.html>`_), the Slurm user repository must be built (See `Repository prerequisites <https://omnia-devel.readthedocs.io/en/omnia-docs-v2.1.0.0-rc1/RHEL_prereq.html#repository>`_) without UCX and openmpi support.
        Specifically: 

        * The Slurm user repository **must NOT include** the following packages: ucx, ucx-devel, openmpi, openmpi-devel.

        * Slurm itself must be compiled without UCX and openmpi support.

        After running ``discovery.yml`` and PXE-booting the nodes, DOCA-OFED is installed on nodes that have Mellanox InfiniBand cards. A static IP is assigned to the InfiniBand interface only if the interface is up. If the interface is down, the user must bring it up to enable IP assignment.

* Fill the mandatory parameters in ``omnia_config.yml``: `Input parameters for the cluster <../schedulerinputparams.html#id13>`_
* Fill the parameters in ``storage_config.yml``: `Input parameters for the cluster <../schedulerinputparams.html#id13>`_
* Add ``slurm_custom`` to ``software_config.json`` and add ``slurm_custom`` subgroups.
* Add ``slurm_custom`` repository URL to ``user_repo_url_x86_64`` or ``user_repo_url_aarch64`` in ``local_repo_config.yml``.


**Setup Slurm:**

1. To download the artifacts required to set up Slurm on the nodes, run the ``local_repo.yml`` playbook.
2. To build diskless images for cluster nodes, run build_image_x86_64.yml or build_image_aarch64.yml: `Build cluster node images <../../build_images.html>`_
3. To discover the potential cluster nodes, configure the boot script, and cloud-init based on the functional groups, run  the ``discovery.yml`` playbook: `Discover cluster nodes <../../Provision/index.html>`_
4. After successfully executing the ``discovery.yml`` playbook, you can PXE boot the slurm node, login node, and login compiler node simultaneously.

.. note:: If you want to deploy only Slurm clusters (``slurm_custom``), the ``idrac_telemetry_support`` parameter must be set to ``false`` in the ``telemetry_config.yml`` file. Omnia is Validated for Slurm version 25.05. If you use any other version, some functionality like PAM may not work.

5. To export openmpi, do the following: ::

                export MPI_HOME=/share_omnia/benchmarks/openmpi

                export PATH=$MPI_HOME/bin:$PATH

                export LD_LIBRARY_PATH=$MPI_HOME/lib:$MPI_HOME/lib64:$LD_LIBRARY_PATH

                <share_omnia> : nfs client share path for slurm in storage_config.yml
    

**Slurm with GPU:**

**Prerequisites**

* You must have the ``user_repo`` which is compiled with nvml and cgroup-v2. If slurm-nodes have GPU then you must provide at least one ``login_compiler_node``.

Automated CUDA and DCGM Provisioning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Overview

When Omnia provisions Slurm nodes, GPU readiness is configured automatically during node
initialization. No user action is required on individual nodes. The provisioning sequence covers
driver installation, CUDA toolkit availability, DCGM service setup, and optional GPUDirect RDMA
support. Nodes without NVIDIA GPU hardware are detected automatically and skipped without error.

CUDA Toolkit Availability

The CUDA toolkit is installed once to a shared NFS location and made available to all Slurm nodes
simultaneously. Compute nodes access the toolkit through a persistent NFS mount at
``/usr/local/cuda``. The toolkit is not installed redundantly on each node.

In clusters where a login or compiler node is present, the toolkit is installed and published to
the shared NFS path by that node. Compute nodes mount the already-installed toolkit directly.
In clusters without a login or compiler node, toolkit installation is coordinated automatically
across compute nodes to ensure it is performed exactly once.

NVIDIA Driver

The NVIDIA driver is installed locally on each GPU-capable Slurm node during provisioning. If the
driver is already present and functional from a prior provisioning cycle, installation is skipped.

DCGM Service

DCGM is installed on each GPU-capable Slurm node. The installed DCGM package is selected
automatically based on the CUDA version present on the node. On clusters running CUDA 12 or later,
the multinode diagnostic plugin is installed in addition to the base DCGM package.

The ``nvidia-dcgm`` systemd service is enabled and started automatically. GPU discovery is
performed and logged upon successful startup.

DCGM installation on Slurm nodes is governed by the ``metrics_enabled`` parameter under ``telemetry_sources.dcgm`` in the ``input/telemetry_config.yml`` file::

    # --------------------------------------------------------------------------
    # DCGM — NVIDIA Data Center GPU Manager
    # --------------------------------------------------------------------------
    # Collects: GPU temperature, utilization, memory, ECC errors, power
    # Requires: NVIDIA GPU driver installed on compute nodes
    dcgm:
      # Enable or disable DCGM metrics collection
      # Default: true
      metrics_enabled: true

* When set to ``true`` (default), Omnia installs NVIDIA DCGM on Slurm compute nodes during the cloud-init phase.
* When set to ``false``, DCGM installation is skipped.

.. note:: At present, DCGM-based metrics are not collected through the telemetry pipeline, even if DCGM is installed.

``nvidia-peermem`` (GPUDirect RDMA)

On nodes with RDMA-capable GPU hardware, the ``nvidia-peermem`` kernel module is installed and
loaded using DKMS. This enables GPUDirect RDMA peer memory access for high-performance MPI
workloads. Nodes without GPU hardware or without the required kernel headers are skipped. If the
module fails to load and no RDMA dependency exists in the workload environment, the failure is
treated as a non-blocking warning.

Post-Provisioning Verification

Use the following commands on any GPU-capable Slurm node to confirm successful provisioning::

    # Verify NVIDIA driver
    nvidia-smi

    # Verify CUDA toolkit
    nvcc --version

    # Verify DCGM service
    systemctl status nvidia-dcgm
    dcgmi discovery -l

    # Verify CUDA environment is available in session
    echo $CUDA_HOME
    nvcc --version

    # Verify NFS mount for CUDA toolkit
    mount | grep cuda

    # Verify nvidia-peermem (RDMA environments only)
    lsmod | grep -E 'nv_peer_mem|nvidia_peermem'

Manual Recovery: CUDA Toolkit and DCGM Setup Failure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If automated GPU setup fails during provisioning — due to repository unavailability, NFS
connectivity issues, or node initialization errors — the affected components can be recovered
manually on the impacted node. All recovery steps are safe to run on an already-provisioned node.

.. note:: Perform all recovery steps as ``root`` on the affected node. Verify that the
   shared NFS path is reachable and repositories are accessible before proceeding.

Step 1: Verify Prerequisites

Before attempting any recovery, confirm the following::

    # Verify NFS reachability
    showmount -e <NFS_SERVER_IP>

    # Verify GPU hardware presence
    lspci | grep -i nvidia

    # Verify repository access
    dnf repolist | grep -i cuda

    # Verify available disk space
    df -h /usr/local

Step 2: Recover NVIDIA Driver

If ``nvidia-smi`` is missing or returning errors::

    dnf install -y cuda-drivers

Validate::

    nvidia-smi

Step 3: Recover CUDA Toolkit

The CUDA toolkit recovery procedure differs depending on both the node type and whether a
login or compiler node is present in the cluster. Identify your scenario before proceeding.

**Scenario A — Login or Compiler Node present in the cluster**

In this topology, the login/compiler node is the designated installer. It installs the toolkit
to the shared NFS location at ``/hpc_tools/cuda``. Slurm compute nodes mount this path at
``/usr/local/cuda`` and do not perform any installation themselves.

*On the login or compiler node:*

Check whether the toolkit is installed::

    ls /hpc_tools/cuda/bin/nvcc 2>/dev/null && echo "Toolkit present" || echo "Toolkit NOT present"

If not present, trigger the installation manually::

    CUDA_INSTALL_MANUAL=true /usr/local/bin/install_cuda_toolkit.sh

.. note:: Run this only after confirming no active toolkit installation is already in progress.
   Review ``/var/log/cuda_toolkit_install.log`` to check current installation status.

Validate on the login/compiler node::

    ls /hpc_tools/cuda/bin/nvcc
    nvcc --version

*On a Slurm compute node (after toolkit is confirmed installed on NFS):*

The compute node accesses the toolkit via an NFS mount at ``/usr/local/cuda``. Verify the mount::

    mount | grep cuda

If the mount is absent, re-mount manually::

    mount -t nfs <NFS_SERVER>:<hpc_tools_path>/hpc_tools/cuda /usr/local/cuda

Validate on the compute node::

    ls /usr/local/cuda/bin/nvcc
    nvcc --version

**Scenario B — No Login or Compiler Node in the cluster**

In this topology, Slurm compute nodes are responsible for installing the toolkit themselves.
The NFS ``hpc_tools`` share is mounted at ``/hpc_tools`` on all compute nodes, and the toolkit
is installed to ``/hpc_tools/cuda`` by whichever node acquires the installation role.
``CUDA_HOME`` is set to ``/hpc_tools/cuda`` on all nodes.

Check whether the toolkit is installed on the shared NFS location::

    ls /hpc_tools/cuda/bin/nvcc 2>/dev/null && echo "Toolkit present" || echo "Toolkit NOT present"

If not present, trigger the installation manually on any compute node::

    CUDA_INSTALL_MANUAL=true /usr/local/bin/install_cuda_toolkit.sh

.. note:: Run this only after confirming no active toolkit installation is already in progress.
   Review ``/var/log/cuda_toolkit_install.log`` to check current installation status.

Validate::

    ls /hpc_tools/cuda/bin/nvcc
    nvcc --version

Step 4: Recover DCGM

If the ``nvidia-dcgm`` service is inactive or failed::

    # Verify CUDA version on node
    nvidia-smi | grep "CUDA Version"

    # Install the appropriate DCGM package
    dnf install -y datacenter-gpu-manager-4-cuda<N>

    # Enable and start the service
    systemctl enable nvidia-dcgm
    systemctl start nvidia-dcgm

Validate::

    systemctl status nvidia-dcgm
    dcgmi discovery -l
    journalctl -u nvidia-dcgm -n 100 --no-pager

Step 5: Recover ``nvidia-peermem`` (RDMA environments only)

If the ``nvidia-peermem`` module is not loaded::

    # Verify kernel headers are available
    ls /lib/modules/$(uname -r)/build

    # Install kernel headers if missing
    dnf install -y kernel-devel-$(uname -r)

    # Load the module
    modprobe nvidia-peermem

Validate::

    lsmod | grep -E 'nv_peer_mem|nvidia_peermem'

Log File Reference

+----------------------------------------+--------------------------------------------------------------+
| Log File                               | Content                                                      |
+========================================+==============================================================+
| ``/var/log/nvidia_install.log``        | NVIDIA driver installation output                           |
+----------------------------------------+--------------------------------------------------------------+
| ``/var/log/cuda_toolkit_install.log``  | CUDA toolkit installation output and timing                 |
+----------------------------------------+--------------------------------------------------------------+
| ``/var/log/dcgm_setup.log``            | DCGM package install, service startup, GPU discovery         |
+----------------------------------------+--------------------------------------------------------------+
| ``/var/log/nvidia_peermem_install.log``| ``nvidia-peermem`` DKMS build and load output               |
+----------------------------------------+--------------------------------------------------------------+


.. note:: If the iDRAC of a Slurm node is not accessible through OIM—because of issues such as an incorrect iDRAC port configuration or invalid credentials—the node configuration specified in ``/etc/slurm/slurm.conf`` for ``NodeName`` will default to: ``Sockets=2 CoresPerSocket=72 ThreadsPerCore=1 RealMemory=884736``. Update ``slurm.conf`` with the correct hardware values and run ``scontrol reconfigure`` to apply the changes.

Add new Slurm nodes
----------------------------

Omnia supports dynamic addition of Slurm compute nodes to an existing cluster. The process automatically updates the Slurm configuration and integrates new nodes into the cluster.

1. Update the PXE mapping file with new node entries. Add entries for new nodes with appropriate functional group assignments ``slurm_node_x86_64``.

.. note:: Addition of only ``slurm_node`` is supported.

2. Run the discovery playbook.
3. PXE reboot the newly added node.

Remove Slurm nodes
-----------------------

Omnia automatically handles node removal when nodes are deleted from the PXE mapping file or functional groups.

1. Update the PXE mapping file. Remove or reassign nodes that should no longer be part of the Slurm cluster.
2. Run the discovery playbook.

.. note:: Removal of only ``slurm_node`` is supported.

Slurm configuration validation and defaults
----------------------------------------------

Omnia includes a built-in validation system that checks Slurm configuration files for correctness before deployment. The input validator module validates all configuration files (slurm.conf, slurmdbd.conf, cgroup.conf, gres.conf, etc.) against Slurm 25.X specifications, ensuring parameter names are valid and values match expected types (integers, strings, booleans, arrays, etc.). You can provide custom configurations in ``omnia_config.yml`` > ``slurm_cluster`` > ``config_sources`` either as a file path or a mapping directly. For supported conf parameters, see `Slurm.conf <https://slurm.schedmd.com/slurm.conf.html>`_

Configuration merge control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``skip_merge`` parameter provides granular control over how Slurm configuration files are processed and applied to the cluster. By default, Omnia merges custom configuration sources with system defaults and existing configurations to ensure a complete and valid setup. However, when ``skip_merge`` is set to ``true``, any specific configuration source path under ``config_sources`` are applied directly to the cluster without any merging operations and is not applicable to mapping type ``config_sources``. The parameter accepts boolean values (``true`` or ``false``) and defaults to ``false``, ensuring that standard merge behavior is maintained unless explicitly modified. When using ``skip_merge: true``, administrators must ensure that the provided configuration file is complete and valid. Omnia does not supplement the file with default values or perform validation checks during the merge process.


.. note:: 
    * By default, there is a partition with name "normal" that is created with all the slurm compute nodes listed in the ``pxe_mapping`` file. 
        ::

            PartitionName=normal Nodes=<Comma-separated list of all compute nodes> MaxTime=INFINITE State=UP

    * If iDRAC is not reachable, then the default values of nodename information in ``slurm.conf`` are considered. ::

            NodeName=<nodename> Sockets=1 CoresPerSocket=1 ThreadsPerCore=1 RealMemory=3686


Default Slurm configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia provides a comprehensive default configuration optimized for HPC clusters. These defaults are automatically applied and can be overridden via custom configuration files.


Default slurm.conf parameters:

.. note:: The parameters ClusterName, SlurmctldHost, AccountingStorageHost cannot be modified.

::

    # Authentication and Security
        AuthType=auth/munge
        CredType=cred/munge
        SlurmUser=slurm
 
    # Controller Configuration
        ClusterName=cluster
        SlurmctldHost=<auto-detected>
        SlurmctldPort=6817
        SlurmctldTimeout=120
        SlurmctldLogFile=/var/log/slurm/slurmctld.log
        SlurmctldPidFile=/var/run/slurmctld.pid
        SlurmctldParameters=enable_configless
        StateSaveLocation=/var/spool/slurmctld
    
    # Compute Node Configuration
        SlurmdPort=6818
        SlurmdTimeout=300
        SlurmdLogFile=/var/log/slurm/slurmd.log
        SlurmdPidFile=/var/run/slurmd.pid
        SlurmdSpoolDir=/var/spool/slurmd
 
    # Accounting
        AccountingStorageHost=<auto-detected>
        AccountingStoragePort=6819
        AccountingStorageType=accounting_storage/slurmdbd
 
    # Job Execution
        SrunPortRange=60001-63000
        ReturnToService=2
        Epilog=/etc/slurm/epilog.d/logout_user.sh
        PrologFlags=contain
 
    # Scheduling
        SchedulerType=sched/backfill
        SelectType=select/linear
 
    # Resource Tracking
        TaskPlugin=task/cgroup
        ProctrackType=proctrack/cgroup
        JobAcctGatherType=jobacct_gather/linux
        JobAcctGatherFrequency=30
 
    # MPI Configuration
        MpiDefault=none
 
    # Plugin Directory
        PluginDir=/usr/lib64/slurm
 
    # Default Node Configuration
        NodeName=DEFAULT State=UNKNOWN
 
    # Default Partition Configuration
        PartitionName=DEFAULT Nodes=ALL Default=YES MaxTime=INFINITE State=UP
        PartitionName=normal Nodes=<compute_nodes> Default=YES MaxTime=INFINITE State=UP

Default slurmdbd.conf parameters:

.. note:: The parameters DbdHost, StorageHost cannot be modified.

::

    # Authentication
        AuthType=auth/munge
        SlurmUser=slurm
 
    # Database Daemon Configuration
        DbdHost=<auto-detected>
        DbdPort=6819
        LogFile=/var/log/slurm/slurmdbd.log
        PidFile=/var/run/slurmdbd.pid
        PluginDir=/usr/lib64/slurm
 
    # Database Connection
        StorageType=accounting_storage/mysql
        StorageHost=<auto-detected>
        StoragePort=3306
        StorageLoc=slurm_acct_db
        StorageUser=slurm
        StoragePass=<storage_password>

Default cgroup.conf parameters ::

    # Cgroup Plugin
        CgroupPlugin=autodetect
 
    # Resource Constraints
        ConstrainCores=yes
        ConstrainDevices=yes
        ConstrainRAMSpace=yes
        ConstrainSwapSpace=yes

Default gres.conf parameters ::

    # GPU Auto-Detection
        AutoDetect=nvml


Post Installation
----------------------

Pulling container images on a Slurm cluster node 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A helper script is provided to simplify pulling container images on cluster nodes. By default, the script downloads the **hpcbenchmarks** container from the site Pulp registry, but it can also be used to pull any other approved images available in Pulp.

It is recommended to run this script on a login or compiler node.

1. Verify if required paths exist. ::

    ls -l /hpc_tools/scripts
    ls -ld /hpc_tools/container_images

 The following should be available:

 * ``download_container_image.sh``
 * ``container_image.list``

 If missing, NFS is not mounted.

2. Verify if Apptainer is installed. :: 

    apptainer --version

3. Update image list (optional): By default, the list includes the HPC benchmarks image. To retrieve additional images from Pulp, add them to this list. ::

    vi /hpc_tools/scripts/container_image.list

 Format: ::
        
        <registry>/<namespace>/<image>:<tag>

 Example: ::

        docker.io/library/ubuntu:22.04

4. Run the download script. ::

    /hpc_tools/scripts/download_container_image.sh

 The script retrieves images from the Pulp mirror and saves them to ``/hpc_tools/container_images``.

5. Verify the downloaded images. ::

        ls -lh /hpc_tools/container_images
        apptainer inspect /hpc_tools/container_images/<image>.sif

6. Run a container (example).

  Run the following command to execute the container::

    apptainer exec /hpc_tools/container_images/hpc-benchmarks_25.09.sif --help

  Verify GPU Visibility Inside the Container

  To ensure GPUs are accessible within the container, run::

    apptainer exec --nv /hpc_tools/container_images/hpc-benchmarks_25.09.sif nvidia-smi

  HPL-MxP Quick Compute Test (2 GPUs)

  Execute a quick HPL-MxP benchmark test using two GPUs::

    srun -N 1 --ntasks-per-node=2 --gres=gpu:2 --mpi=pmix \
        apptainer exec --nv /hpc_tools/container_images/hpc-benchmarks_25.09.sif \
        /workspace/hpl-mxp-linux-x86_64/hpl-mxp.sh \
        --n 5000 --nb 512 \
        --nprow 1 --npcol 2 --nporder row \
        --gpu-affinity 0:1

.. note:: For detailed guidance on using Apptainer and NVIDIA HPC Benchmarks, refer to:

    * Apptainer User Documentation: https://apptainer.org/docs/user/main/
    * NVIDIA HPC Benchmarks (NGC Catalog): https://catalog.ngc.nvidia.com/orgs/nvidia/containers/hpc-benchmarks?version=25.09

HPC Benchmark Image Layer
^^^^^^^^^^^^^^^^^^^^^^^^^

After Slurm setup, benchmark assets are available from the shared ``hpc_tools`` workspace on Slurm-mounted storage. Source-based benchmarks are provided as staged sources for user-controlled build and run workflows.

Available tarball tools: OSU Micro-Benchmarks, IMB, LIKWID, PAPI, msr-safe (x86_64 only), GEOPM, SIONlib (optional).

HPL, HPL-MxP, and STREAM are documented as container-first benchmarks and should be used through the approved container workflow.

For container-first benchmarks, first check available image tags in your approved registry, then pull a specific tag.

Example command to list tags::

    curl -s <registry-endpoint>/v2/<repository>/tags/list | python3 -m json.tool

Example masked pull command::

    apptainer pull hpc-benchmarks.sif docker://<registry-endpoint>:<port>/nvidia/hpc-benchmarks:<tag>

Example command to pull selected tag::

    apptainer pull hpc-benchmarks.sif docker://<registry-endpoint>/<repository>:<tag>



.. _slurm-configuration-utilities:

Slurm configuration utilities
-----------------------------------

Create a backup, rollback, or cleanup of Slurm configuration files.

**Prerequisites**

* Access to the Omnia infrastructure is available.
* Proper configuration files are available.
* SSH access to Slurm controller node is available.

Backup Slurm configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create timestamped backups of Slurm configuration files.

1. Create a complete backup of Slurm configuration files with optional custom naming. Run the following command: ::

        bash
        ansible-playbook utils/slurm_config_util.yml --tags config_backup

2. Provide a backup base name or use a timestamp-only name. The backup is created at ``<client_share_path>/slurm_backups/<backup_name>/<controller_node>/``

Example: ::

    Enter backup base name (leave empty for timestamp-only): pre_upgrade
    Creating backup: pre_upgrade
    Backup completed successfully

Cleanup Slurm configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Remove existing Slurm configuration files from the live cluster directory.

Run the following command: ::

        bash
        ansible-playbook utils/slurm_config_util.yml --tags slurm_cleanup

* Before cleanup, take a config backup. It is recommended before deleting live configurations.
* The path where files are deleted: ``<client_share_path>/slurm/``

Example: ::

    Before cleanup, take a config backup? (y/n): y
    Enter backup base name (leave empty for timestamp-only): safety_backup

    This will delete /share/slurm. Type YES to continue: YES
    Deleted SLURM configuration directory successfully

Rollback Slurm configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Restore Slurm configuration from a previous backup with comprehensive validation.

Example: ::

    Available backups (newest first):
    1. backup_2024-02-01_120000 (controller: slurm-ctrl-01)
    2. pre_maintenance (controller: slurm-ctrl-01)
    3. backup_2024-01-15_143022 (controller: slurm-ctrl-01)
    ... (showing 10 of 15 total)

    Enter backup name to restore (or press Enter to abort): pre_maintenance

    Validating backup 'pre_maintenance'...
    ✓ slurm.conf exists
    ⚠ munge.key missing (optional but recommended)

    Take safety backup of current config before rollback? (y/n): y
    Enter backup base name (leave empty for timestamp-only): safety_before_rollback

    Restoring configuration files...
    Fixing file permissions...
    Restarting slurmdbd (config changed)...
    Reconfiguring SLURM controller...

    Rollback completed successfully!















 
