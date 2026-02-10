Step 11: Set up Slurm on nodes
==============

**Prerequisites**

* Provide the repository with slurm v25.X rpms.
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

**Slurm with GPU:**

**Prerequisites**

* You must have the ``user_repo`` which is compiled with nvml and cgroup-v2. If slurm-nodes have GPU then you must provide at least one ``login_compiler_node``.


.. note:: If the iDRAC of a Slurm node is not accessible through OIM—because of issues such as an incorrect iDRAC port configuration or invalid credentials—the node configuration specified in ``/etc/slurm/slurm.conf`` for ``NodeName`` will default to: ``Sockets=1 CoresPerSocket=1 ThreadsPerCore=1 RealMemory=3774873``. Update ``slurm.conf`` with the correct hardware values and run ``scontrol reconfigure`` to apply the changes.

Add new Slurm nodes
----------------------------

Omnia supports dynamic addition of Slurm compute nodes to an existing cluster. The process automatically updates the Slurm configuration and integrates new nodes into the cluster.

1. Update the PXE mapping file with new node entries. Add entries for new nodes with appropriate functional group assignments ``slurm_node_x86_64``.

.. note:: Addition of new ``slurm_control_node`` is not supported.

2. Run the discovery playbook.
3. PXE reboot the newly added node.

Remove Slurm nodes
-----------------------

Omnia automatically handles node removal when nodes are deleted from the PXE mapping file or functional groups.

1. Update the PXE mapping file. Remove or reassign nodes that should no longer be part of the Slurm cluster.
2. Run the discovery playbook.

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

6. Run a container (example). ::

        apptainer exec /hpc_tools/container_images/hpc-benchmarks_25.09.sif --help





Slurm configuration validation and defaults
----------------------------------------------

Omnia includes a built-in validation system that checks Slurm configuration files for correctness before deployment. The ``slurm_conf`` module validates all configuration files (slurm.conf, slurmdbd.conf, cgroup.conf, gres.conf, etc.) against Slurm 25.X specifications, ensuring parameter names are valid and values match expected types (integers, strings, booleans, arrays, etc.). You can provide custom configurations in ``omnia_config.yml`` > ``slurm_cluster`` > ``config_sourcesalidation and Defaults``.

Default Slurm configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia provides a comprehensive default configuration optimized for HPC clusters. These defaults are automatically applied and can be overridden via custom configuration files.

Default slurm.conf parameters ::

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

Default slurmdbd.conf parameters ::

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
        StoragePass=<encrypted>

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




