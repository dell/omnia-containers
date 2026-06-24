Step 11: Configure Slurm on Cluster Nodes
========================================

Overview
--------

Omnia supports deploying Slurm across designated cluster nodes to provide workload scheduling and resource management for HPC environments. Supported node roles include:

* Slurm controller node
* Slurm compute node
* Slurm login node
* Slurm login/compile node

Supported Version
-----------------

**Supported Slurm Version:** 25.05

Omnia validation and testing are performed against Slurm 25.05. Deploying other versions of Slurm may result in unsupported or unexpected behavior.

Functional Groups
-----------------

Define the following functional groups in your pxe mapping inventory file.

.. list-table:: Functional Groups
   :widths: 35 15 45 20
   :header-rows: 1

   * - Functional Group
     - Architecture
     - Description
     - Required/Optional
   * - ``slurm_control_node_x86_64``
     - x86_64
     - Slurm controller node running ``slurmctld`` and ``slurmdbd``
     - Only one mandatory
   * - ``slurm_node_x86_64``
     - x86_64
     - Slurm compute node running ``slurmd``
     - At least one mandatory
   * - ``slurm_node_aarch64``
     - aarch64
     - Slurm compute node running ``slurmd``
     - At least one mandatory
   * - ``login_node_x86_64``
     - x86_64
     - User login node
     - Optional
   * - ``login_node_aarch64``
     - aarch64
     - User login node
     - Optional
   * - ``login_compiler_node_x86_64``
     - x86_64
     - Login node with compilation tools
     - Optional only one
   * - ``login_compiler_node_aarch64``
     - aarch64
     - Login node with compilation tools
     - Optional only one

.. note:: Slurm controller nodes are supported only on x86_64 systems.

Prerequisites
------------

Software Repository Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before deploying Slurm:

1. Create a repository or add an existing repository containing Slurm RPM packages. Add the repository URL to ``user_repo_url_<arch>`` in ``local_repo_config.yml``.

   **Note:**

   * The slurm packages in the repository must not be built with UCX or OpenMPI support.
   * The repository should not contain the following packages: ucx, ucx-devel, openmpi, openmpi-devel

2. Add ``slurm_custom`` to ``software_config.json``.
3. Define the required ``slurm_custom`` subgroups from the list for the images to be built: ``slurm_control_node``, ``slurm_node``, ``login_node``, ``login_compiler_node``
4. Populate the pxe_mapping file csv with the required fields: ``FUNCTIONAL_GROUP_NAME``, ``GROUP_NAME``, ``SERVICE_TAG``, ``PARENT_SERVICE_TAG``, ``HOSTNAME``, ``ADMIN_MAC``, ``ADMIN_IP``, ``BMC_MAC``, ``BMC_IP``, ``IB_NIC_NAME``, ``IB_IP``

InfiniBand Requirements
^^^^^^^^^^^^^^^^^^^^^^^

For using InfiniBand interface in the slurm cluster, ensure that ``ib_network`` is configured in ``network_spec.yml``. and IB_MAC address is populated in the pxe_mapping file.

DOCA-OFED Requirements
^^^^^^^^^^^^^^^^^^^^^^

DOCA-OFED is automatically installed on systems with Mellanox InfiniBand adapters, when doca repo is configured in ``local_repo_config.yml``. A static IP address is assigned only when the InfiniBand interface is operational.
If the interface is down, manually bring it up before IP assignment can occur.

Telemetry Requirements
^^^^^^^^^^^^^^^^^^^^^^

For deployments that use only ``slurm_custom``:

.. code-block:: yaml

   idrac_telemetry_support: false

Set this parameter in ``telemetry_config.yml``.

Configuration
------------

1. Configure Local Repositories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the Slurm repository URL in ``local_repo_config.yml``.

Example:

.. code-block:: yaml

   user_repo_url_x86_64:
     - { url: "http://<repo_ip>/slurm_x86_64/", name: "slurm_custom" }

   user_repo_url_aarch64:
     - { url: "http://<repo_ip>/slurm_aarch64/", name: "slurm_custom" }

2. Configure Software Components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add ``slurm_custom`` and its associated node types to ``software_config.json``.

Example:

.. code-block:: json

   {
     "cluster_os_type": "rhel",
     "cluster_os_version": "10.0",
     "repo_config": "partial",
     "softwares": [
       {
         "name": "default_packages",
         "arch": ["x86_64", "aarch64"]
       },
       {
         "name": "slurm_custom",
         "arch": ["x86_64", "aarch64"]
       }
     ],
     "slurm_custom": [
       { "name": "slurm_control_node" },
       { "name": "slurm_node" },
       { "name": "login_node" },
       { "name": "login_compiler_node" }
     ]
   }

3. Creating the PXE Mapping CSV
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Populate the pxe_mapping file csv with the required fields. Refer `PXE mapping CSV <../../Provision/composable_roles.html#create-pxe-file-manually>`_

Example:

.. code-block:: csv

   FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
   slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,a1:b2:c3:d4:e5:f6,172.16.107.52,a2:b3:c4:d5:e6:f7,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
   slurm_node_x86_64,grp1,ABCD34,ABFL82,slurm-node1,b1:c2:d3:e4:f5:a6,172.16.107.43,b2:c3:d4:e5:f6:a7,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
   login_node_x86_64,grp1,ABFG34,ABKD88,login-node2,c1:d2:e3:f4:a5:b6,172.16.107.44,c2:d3:e4:f5:a6:b7,172.17.107.44,InfiniBand.Slot.7-1,192.168.0.102
   login_compiler_node_x86_64,grp8,ABCD78,,login-compiler-node1,d1:e2:f3:a4:b5:c6,172.16.107.41,d2:e3:f4:a5:b6:c7,172.17.107.41,InfiniBand.Slot.7-1,192.168.0.103

4. Configure Slurm cluster parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Populate the required slurm specific parameters in ``omnia_config.yml``. (For parameter details, see: `Parameters for Slurm setup <../schedulerinputparams.html#id1>`)

.. code-block:: yaml

   slurm_cluster:
     - cluster_name: slurm_cluster
       nfs_storage_name: nfs_slurm
       vast_storage_name: vast_storage
       config_sources:

5. Configure Storage for Slurm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Slurm uses NFS storage and optional VAST(NFS storage) for operational purposes. `Parameters for storage configuration <../schedulerinputparams.html#id4>` for details. Populate the parameters in ``storage_config.yml``.

.. code-block:: yaml

   mounts:
     - name: "nfs_slurm"
       source: "172.16.107.168:/mnt/share/omnia"
       mount_point: "/share_omnia"
       fs_type: "nfs"
       mnt_opts: "nosuid,rw,sync,hard,intr"
       mount_on_oim: true
       functional_group_prefix: ["slurm", "login"]
     - name: "vast_storage"
       source: "172.16.107.77:/share/vast"
       mount_point: "/mnt/vast"
       mount_params: "vast_rdma"
       mount_on_oim: true
       functional_group_prefix: ["slurm_node", "login"]

6. Configure Telemetry
^^^^^^^^^^^^^^^^^^^^^^

Review and update ``telemetry_config.yml`` as follows for Slurm-only deployment:

.. code-block:: yaml

   idrac_telemetry_support: false

Deployment Workflow
-------------------

The Slurm deployment process consists of the following stages:

1. Prepare OIM
2. Download software artifacts
3. Build slurm cluster images
4. Discover and configure nodes
5. PXE boot nodes

Step 1: Prepare OIM
^^^^^^^^^^^^^^^^^^

Prepare the Omnia Infrastructure Manager (OIM).

.. code-block:: bash

   ansible-playbook prepare_oim.yml

**Verification**

Review the playbook output and logs to confirm successful completion.

Step 2: Download Artifacts
^^^^^^^^^^^^^^^^^^^^^^^^^^

Download required packages and repositories.

.. code-block:: bash

   ansible-playbook local_repo.yml

**Verification**

Confirm repository synchronization completed successfully by checking the repository logs.

Step 3: Build Diskless Images
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build cluster node images. See `Build images <../../build_images.html>` for more information.

**x86_64**

.. code-block:: bash

   ansible-playbook build_image_x86_64.yml

**aarch64**

.. code-block:: bash

   ansible-playbook build_image_aarch64.yml -i <inventory_file>

**Verification**

Verify that the images are built successfully by checking the image build logs.

Step 4: Configure Nodes
^^^^^^^^^^^^^^^^^^^^^^^

Run the ``provision.yml`` playbook to discover potential cluster nodes, configure the boot script, and cloud-init based on the functional groups in pxe mapping csv file. See `Provision cluster nodes <../../Provision/index.html>` for more information.

.. code-block:: bash

   ansible-playbook provision.yml

**Verification**

Verify that:

* Nodes are discovered successfully.
* Cloud-init files are generated.
* provision logs show successful configuration.

Step 5: PXE Boot Nodes
^^^^^^^^^^^^^^^^^^^^^^

After ``provision.yml`` completes, PXE boot all Slurm-related nodes:

* Controller node
* Compute nodes
* Login nodes
* Login/compile node

**Option 1: Manual PXE Boot**

Configure each node to boot from the network.

**Option 2: Automated PXE Boot**

See `Set PXE boot <../../../Utils/configure_pxe_boot.html>` for more information.

.. code-block:: bash

   ansible-playbook utils/set_pxe_boot.yml

**Verification**

Ensure all nodes boot successfully and become reachable.

Automated GPU Provisioning
---------------------------

**Overview**

Omnia automatically configures GPU software during node initialization. The process includes:

* NVIDIA driver installation
* CUDA toolkit deployment
* NVIDIA DCGM installation
* Optional GPUDirect RDMA support

Nodes without NVIDIA GPUs are detected automatically and skipped.

**CUDA Toolkit Deployment**

The CUDA toolkit is installed once and shared through NFS.

Compute nodes access CUDA using::

    /usr/local/cuda

**Behavior**

* When login_compiler nodes exist, CUDA is installed on one of these nodes and exported through NFS.
* Compute nodes mount the existing toolkit.
* In compute-only clusters, installation is coordinated automatically to ensure a single installation occurs.

**NVIDIA Driver Installation**

GPU-capable nodes automatically install the NVIDIA driver during provisioning.

**NVIDIA DCGM**

DCGM is installed on each GPU-capable Slurm node. The installed DCGM package is selected automatically based on the CUDA version present on the node. On clusters running CUDA 12 or later, the multinode diagnostic plugin is installed in addition to the base DCGM package.

DCGM installation is controlled through the ``metrics_enabled`` parameter in the ``telemetry_sources.dcgm`` section of the ``input/telemetry_config.yml`` file:

.. code-block:: yaml

   telemetry_sources:
     dcgm:
       metrics_enabled: true

**Behavior**

.. list-table::
   :header-rows: 1

   * - Value
     - Result
   * - ``true``
     - Install DCGM during cloud-init
   * - ``false``
     - Skip DCGM installation

The ``nvidia-dcgm`` service is automatically enabled and started.

.. note:: DCGM metrics collection is not currently integrated into the Omnia telemetry pipeline.

**Post-Provisioning Verification**

Use the following commands on any GPU-capable Slurm node to confirm successful provisioning:

.. code-block:: bash

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

Node Management
---------------

**Add Slurm Compute Nodes**

Omnia supports dynamically adding Slurm compute nodes to an existing cluster.

**Steps**:

1. Add the new node entries to the PXE mapping file.
2. Assign the appropriate functional group:
   - ``slurm_node_x86_64``
   - ``slurm_node_aarch64``
3. Run the provisioning playbook:

.. code-block:: bash

   ansible-playbook provision/provision.yml

4. PXE reboot the newly added node
5. Verify the node is added to the cluster:

.. code-block:: bash

   sinfo

.. note:: Dynamic node addition is supported only for slurm_node functional groups.

**Remove Slurm Nodes**

Omnia supports removing Slurm compute nodes from an existing cluster.

**Steps**:

1. Remove the node from the PXE mapping file or reassign it to a different functional group.
2. Run the provisioning playbook:

.. code-block:: bash

   ansible-playbook provision/provision.yml

.. note:: Dynamic node removal is supported only for slurm_node functional groups.

Slurm Configuration Management
-------------------------------

Omnia provides flexible mechanisms to manage Slurm configuration files such as slurm.conf, slurmdbd.conf, cgroup.conf, and gres.conf. Administrators can either use the default configurations provided by Omnia or supply custom configurations through the config_sources parameter in omnia_config.yml.

Default Slurm Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia provides a comprehensive default configuration optimized for HPC clusters. These defaults are automatically applied and can be overridden via custom configuration files.

**Default Partition Configuration**

- By default, a partition named "normal" is created with all Slurm compute nodes listed in the PXE mapping file
- Configuration: ``PartitionName=normal Nodes=<Comma-separated list of all compute nodes> MaxTime=INFINITE State=UP``

**Default Node Configuration**

- If iDRAC is not reachable, the default values of nodename information in slurm.conf are considered
- Configuration: ``NodeName=<nodename> Sockets=1 CoresPerSocket=1 ThreadsPerCore=1 RealMemory=3686``

**Default slurm.conf parameters**

.. note:: The parameters ClusterName, SlurmctldHost, AccountingStorageHost cannot be modified.

.. code-block:: bash

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

**Default slurmdbd.conf parameters**

.. note:: The parameters DbdHost, StorageHost cannot be modified.

.. code-block:: bash

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

**Default cgroup.conf parameters**

.. code-block:: bash

    # Cgroup Plugin
    CgroupPlugin=autodetect

    # Resource Constraints
    ConstrainCores=yes
    ConstrainDevices=yes
    ConstrainRAMSpace=yes
    ConstrainSwapSpace=yes

**Default gres.conf parameters**

.. code-block:: bash

    # GPU Auto-Detection
    AutoDetect=nvml

Configuration Sources
^^^^^^^^^^^^^^^^^^^^^

Custom configuration files can be supplied in one of the following ways:

**1. Parameter-Based Configuration (Mapping)**

Specify individual configuration parameters directly in config_sources. Omnia merges these values with the default configuration.

.. code-block:: yaml

   slurm_cluster:
     - cluster_name: slurm_cluster
       nfs_storage_name: nfs_slurm
       vast_storage_name: vast_storage
       config_sources:
         slurm:
           SlurmctldTimeout: 60
           SlurmdTimeout: 150
         cgroup:
           CgroupPlugin: autodetect
           AllowedRAMSpace: 100

**2. File-Based Configuration**

Provide complete custom configuration files for one or more Slurm components.

.. code-block:: yaml

   slurm_cluster:
     - cluster_name: slurm_cluster
       nfs_storage_name: nfs_slurm
       config_sources:
         slurm: /path/to/custom_slurm.conf
         cgroup: /path/to/custom_cgroup.conf
         slurmdbd: /path/to/custom_slurmdbd.conf
         gres: /path/to/custom_gres.conf

For supported configuration parameters, refer to the Slurm documentation:

- `slurm.conf <https://slurm.schedmd.com/slurm.conf.html>`_
- `slurmdbd.conf <https://slurm.schedmd.com/slurmdbd.conf.html>`_
- Other Slurm configuration files applicable to your deployment

Configuration Merge Behavior (skip_merge)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Omnia merges user-provided configurations with existing and default configuration values to produce a complete and valid configuration. The skip_merge parameter provides control over this behavior.

Default value: false

**Default Behavior (skip_merge: false)**

- Custom configurations are merged with Omnia defaults
- Missing parameters may be populated from the default configuration
- Configuration validation is performed before deployment

**Direct Configuration Deployment (skip_merge: true)**

When skip_merge is enabled, file-based configuration sources are applied directly without any merge operations.

.. code-block:: yaml

   slurm_cluster:
     - cluster_name: slurm_cluster
       nfs_storage_name: nfs_slurm
       skip_merge: true
       config_sources:
         slurm: /path/to/custom_slurm.conf
         cgroup: /path/to/custom_cgroup.conf
         slurmdbd: /path/to/custom_slurmdbd.conf
         gres: /path/to/custom_gres.conf

.. important::
   - Applicable only to file-based config_sources
   - Not supported for mapping-based configurations
   - The provided configuration file must be complete and valid
   - Omnia does not supplement missing values from defaults
   - No merge processing is performed before deployment

Configuration Validation
^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia includes a built-in validation framework that verifies Slurm configuration files before deployment. The validator checks configuration files such as:

- slurm.conf
- slurmdbd.conf
- cgroup.conf
- gres.conf
- Other supported Slurm configuration files

Validation ensures that:

- Configuration parameters are recognized by the supported Slurm version
- Parameter values match expected data types (integer, string, boolean, array, etc.)
- Common configuration errors are detected before deployment

This validation process helps prevent invalid Slurm configurations from being applied to the cluster and improves deployment reliability.

Container Images and Benchmark Tool Management
----------------------------------------------

**Pulling Container Images on Slurm Cluster Nodes**

A helper script is provided to simplify pulling container images on cluster nodes. By default, the script downloads the hpcbenchmarks container from the site Pulp registry, but it can also be used to pull any other approved images available in Pulp.

**Recommended**: Run this script on a login or compiler node.

**Steps**:

1. Verify if required paths exist:

.. code-block:: bash

   ls -l /hpc_tools/scripts
   ls -ld /hpc_tools/container_images

The following should be available:

- download_container_image.sh
- container_image.list

If missing, NFS is not mounted.

2. Verify if Apptainer is installed:

.. code-block:: bash

   apptainer --version

3. Update image list (optional): By default, the list includes the HPC benchmarks image. To retrieve additional images from Pulp, add them to this list:

.. code-block:: bash

   vi /hpc_tools/scripts/container_image.list

Format:

.. code-block:: text

   <registry>/<namespace>/<image>:<tag>

Example:

.. code-block:: text

   docker.io/library/ubuntu:22.04

4. Run the download script:

.. code-block:: bash

   /hpc_tools/scripts/download_container_image.sh

The script retrieves images from the Pulp mirror and saves them to ``/hpc_tools/container_images``.

5. Verify the downloaded images:

.. code-block:: bash

   ls -lh /hpc_tools/container_images
   apptainer inspect /hpc_tools/container_images/<image>.sif

6. Run a container (example):

.. code-block:: bash

   apptainer exec /hpc_tools/container_images/hpc-benchmarks_25.09.sif --help

**Verify GPU Visibility Inside the Container**

To ensure GPUs are accessible within the container, run:

.. code-block:: bash

   apptainer exec --nv /hpc_tools/container_images/hpc-benchmarks_25.09.sif nvidia-smi

**HPL-MxP Quick Compute Test (2 GPUs)**

Execute a quick HPL-MxP benchmark test using two GPUs:

.. code-block:: bash

   srun -N 1 --ntasks-per-node=2 --gres=gpu:2 --mpi=pmix \
     apptainer exec --nv /hpc_tools/container_images/hpc-benchmarks_25.09.sif \
     /workspace/hpl-mxp-linux-x86_64/hpl-mxp.sh \
     --n 5000 --nb 512 \
     --nprow 1 --npcol 2 --nporder row \
     --gpu-affinity 0:1

**References**:

- Apptainer User Documentation: `https://apptainer.org/docs/user/main/ <https://apptainer.org/docs/user/main/>`_
- NVIDIA HPC Benchmarks (NGC Catalog): `https://catalog.ngc.nvidia.com/orgs/nvidia/containers/hpc-benchmarks?version=25.09 <https://catalog.ngc.nvidia.com/orgs/nvidia/containers/hpc-benchmarks?version=25.09>`_

**HPC Benchmark Image Layer**

After Slurm setup, Omnia deploys runtime benchmark staging assets to shared storage:

- ``/hpc_tools/scripts/pull_benchmarks.sh``
- ``/hpc_tools/scripts/benchmark_tools.list``

**Staging Benchmark Artifacts**

Execute the runtime script:

.. code-block:: bash

   /hpc_tools/scripts/pull_benchmarks.sh

**Runtime Behavior**

- Reads tool list from ``/hpc_tools/scripts/benchmark_tools.list``
- Auto-detects architecture (uname -m)
- Skips msr-safe on aarch64
- Creates ``/hpc_tools/<tool>/`` if needed
- Pulls tarballs from the configured Pulp mirror path
- Uses wget by default, with curl fallback
- Skips tools already staged (non-empty destination directory)
- Writes per-tool status and summary to ``/var/log/pull_benchmarks.log``

**Benchmark Tools List**

- osu-micro-benchmarks
- imb
- likwid
- papi
- geopm
- sionlib (optional)
- msr-safe (x86_64 only)

**Container-First Benchmarks**

HPL, HPL-MxP, and STREAM remain container-first. Use approved registry endpoint and explicit tag:

.. code-block:: bash

   apptainer pull hpc-benchmarks.sif docker://<registry-endpoint>/<repository>:<tag>

**Quick Verification**

.. code-block:: bash

   ls -l /hpc_tools/scripts
   ls -l /hpc_tools
   tail -n 100 /var/log/pull_benchmarks.log

Slurm Configuration Utilities
-----------------------------

Once the slurm is deployed, Omnia provides utilities for managing Slurm configuration.

**Backup Slurm Configuration**

Create timestamped backups of Slurm configuration files.

**Steps**:

1. Run the following command to create a complete backup of Slurm configuration files with optional custom naming:

.. code-block:: bash

   ansible-playbook utils/slurm_config_util.yml --tags config_backup

2. Provide a backup base name or use a timestamp-only name. The backup is created at ``<NFS share path>/slurm_backups/<backup_name>/<controller_node>/``

**Example**:

.. code-block:: text

   Enter backup base name (leave empty for timestamp-only): pre_upgrade
   Creating backup: pre_upgrade
   Backup completed successfully

**Cleanup Slurm Configuration**

Remove existing Slurm configuration files and logs from the NFS share used by slurm cluster.

**Steps**:

Run the following command:

.. code-block:: bash

   ansible-playbook utils/slurm_config_util.yml --tags slurm_cleanup

**Important**:
- Before cleanup, take a config backup. It is recommended before deleting live configurations.
- The path where files are deleted: ``<client_share_path>/slurm/``

**Example**:

.. code-block:: text

   Before cleanup, take a config backup? (y/n): y
   Enter backup base name (leave empty for timestamp-only): safety_backup
   This will delete /share/slurm. Type YES to continue: YES
   Deleted SLURM configuration directory successfully

**Rollback Slurm Configuration**

Restore Slurm configuration from a previous backup with comprehensive validation.

**Steps**:

Run the rollback command and select from available backups. The utility will:
- List available backups
- Validate the selected backup
- Optionally create a safety backup of current configuration
- Restore configuration files
- Fix file permissions
- Restart slurmdbd if configuration changed
- Reconfigure SLURM controller

**Example**:

.. code-block:: text

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

Support
-------

For feedback or issues with Omnia documentation, please reach out at `omnia.readme@dell.com <mailto:omnia.readme@dell.com>`_.




 
