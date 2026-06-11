.. _sample-files:

Sample Files
=============      


Inventory file for PXE Boot Order
---------------------------------

::

    [bmc]
    10.3.0.1
    10.3.0.2

software_config.json for RHEL
-------------------------------------------

::

    {
        "cluster_os_type": "rhel",
        "cluster_os_version": "10.0",
        "repo_config": "always",
        "softwares": [
            {"name": "default_packages", "arch": ["x86_64","aarch64"]},
            {"name": "openldap", "arch": ["x86_64","aarch64"]},
            {"name": "nfs", "arch": ["x86_64","aarch64"]},
            {"name": "service_k8s","version": "1.34.1", "arch": ["x86_64"]},
            {"name": "slurm_custom", "arch": ["x86_64","aarch64"]},
            {"name": "ucx", "version": "1.19.0", "arch": ["x86_64","aarch64"]},
            {"name": "openmpi", "version": "5.0.8", "arch": ["x86_64","aarch64"]},
            {"name": "csi_driver_powerscale", "version":"v2.15.0", "arch": ["x86_64"]},
            {"name": "ldms", "arch": ["x86_64","aarch64"]}
        ],
        "slurm_custom": [
            {"name": "slurm_control_node"},
            {"name": "slurm_node"},
            {"name": "login_node"},
            {"name": "login_compiler_node"}
        ],
        "service_k8s": [
            {"name": "service_kube_control_plane_first"},
            {"name": "service_kube_control_plane"},
            {"name": "service_kube_node"}
        ]

    }
 

pxe_mapping_file.csv for single subnet DHCP
------------------------------------

::

    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,xx:yy:zz:aa:bb:cc,172.16.107.52,xx:yy:zz:aa:bb:dd,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
    slurm_node_x86_64,grp2,ABCD34,ABFL82,slurm-node1,aa:bb:cc:dd:ee:ff,172.16.107.43,aa:bb:cc:dd:ee:aa,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
    slurm_node_x86_64,grp1,ABFG34,ABKD88,slurm-node2,aa:bb:cc:dd:ee:gg,172.16.107.44,aa:bb:cc:dd:ff:bb,172.17.107.44,InfiniBand.Slot.7-1,192.168.0.102
    slurm_node_x86_64,grp1,BBFG35,ABKD88,slurm-node3,aa:bb:cc:dd:ee:hh,172.16.107.46,aa:bb:cc:dd:ff:cc,172.17.107.46,InfiniBand.Slot.7-1,192.168.0.103
    login_node_x86_64,grp8,ABCD78,,login-compiler-node1,aa:bb:cc:dd:ee:gg,172.16.107.41,aa:bb:cc:dd:ee:bb,172.17.107.41,InfiniBand.Slot.7-1,192.168.0.104
    login_compiler_node_x86_64,grp9,ABFG78,,login-compiler-node2,aa:bb:cc:dd:ee:gg,172.16.107.42,aa:bb:cc:dd:ee:bb,172.17.107.42,InfiniBand.Slot.7-1,192.168.0.105
    service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,aa:bb:cc:dd:ee:ff,172.16.107.53,xx:yy:zz:aa:bb:ff,172.17.107.53,,InfiniBand.Slot.7-1,192.168.0.106
    service_kube_control_plane_x86_64,grp4,ABFH78,,service-kube-control-plane2,aa:bb:cc:dd:ee:hh,172.16.107.54,xx:yy:zz:aa:bb:hh,172.17.107.54,,InfiniBand.Slot.7-1,192.168.0.107
    service_kube_control_plane_x86_64,grp4,ABFH80,,service-kube-control-plane3,aa:bb:cc:dd:ee:ii,172.16.107.55,xx:yy:zz:aa:bb:ii,172.17.107.55,,InfiniBand.Slot.7-1,192.168.0.108
    service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,aa:bb:cc:dd:ee:jj,172.16.107.56,xx:yy:zz:aa:bb:jj,172.17.107.56,InfiniBand.Slot.7-1,192.168.0.109
    service_kube_node_x86_64,grp5,ABKD88,,service-kube-node2,aa:bb:cc:dd:ee:kk,172.16.107.57,xx:yy:zz:aa:bb:ff,172.17.107.57,InfiniBand.Slot.7-1,192.168.0.110

pxe_mapping_file.csv for multiple subnet DHCP
----------------------------------------------

::

    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    service_kube_control_plane_x86_64,grp1,DEF456,,service-kube-control-plane1,aa:bb:cc:dd:ee:03,10.40.2.11,aa:bb:cc:dd:ee:04,10.41.1.15,InfiniBand.Slot.7-2,192.168.2.11
    service_kube_control_plane_x86_64,grp1,GHI789,,service-kube-control-plane2,aa:bb:cc:dd:ee:05,10.40.2.12,aa:bb:cc:dd:ee:06,10.41.1.16,InfiniBand.Slot.7-3,192.168.2.12
    service_kube_control_plane_x86_64,grp1,JKL012,,service-kube-control-plane3,aa:bb:cc:dd:ee:07,10.40.2.13,aa:bb:cc:dd:ee:08,10.41.1.17,InfiniBand.Slot.7-4,192.168.2.13
    service_kube_node_x86_64,grp2,MNO345,,service-kube-node1,aa:bb:cc:dd:ee:09,10.40.2.14,aa:bb:cc:dd:ee:10,10.41.1.18,InfiniBand.Slot.7-5,192.168.2.14
    service_kube_node_x86_64,grp2,PQR678,,service-kube-node2,aa:bb:cc:dd:ee:11,10.40.2.15,aa:bb:cc:dd:ee:12,10.41.1.19,InfiniBand.Slot.7-6,192.168.2.15
    slurm_control_node_x86_64,grp3,ABC123,,slurm-control-node1,aa:bb:cc:dd:ee:01,10.40.1.21,aa:bb:cc:dd:ee:02,10.41.0.10,InfiniBand.Slot.7-1,192.168.1.10
    slurm_node_x86_64,grp4,STU901,2LY0B33,slurm-node1,aa:bb:cc:dd:ee:13,10.40.3.31,aa:bb:cc:dd:ee:14,10.41.2.22,InfiniBand.Slot.7-7,192.168.3.22
    slurm_node_x86_64,grp4,VWX234,2LY0B33,slurm-node2,aa:bb:cc:dd:ee:15,10.40.3.32,aa:bb:cc:dd:ee:16,10.41.2.23,InfiniBand.Slot.7-8,192.168.3.23
    login_compiler_node_x86_64,grp5,YZA567,,login-compiler-node1,aa:bb:cc:dd:ee:17,10.40.3.33,aa:bb:cc:dd:ee:18,10.41.2.24,InfiniBand.Slot.7-9,192.168.3.24
    login_node_x86_64,grp6,BCD890,,login-node1,aa:bb:cc:dd:ee:19,10.40.1.22,aa:bb:cc:dd:ee:20,10.41.0.11,InfiniBand.Slot.7-10,192.168.1.11
    os_x86_64,grp7,EFG123,,os-node1,aa:bb:cc:dd:ee:21,10.40.1.23,aa:bb:cc:dd:ee:22,10.41.0.12,InfiniBand.Slot.7-11,192.168.1.12
    os_aarch_64,grp8,EFG123,,os-node2,aa:bb:cc:dd:ee:21,10.40.1.23,aa:bb:cc:dd:ee:22,10.41.0.12,InfiniBand.Slot.7-11,192.168.1.12

Slurm configuration files (optional)
------------------------------------

You can provide custom configurations in ``omnia_config.yml`` > ``slurm_cluster`` > ``config_sources`` as a file path. Omnia merges these custom configuration files with system defaults and existing configurations.

slurm.conf
^^^^^^^^^^

::

    # Sample Slurm Configuration File
    # Replace values marked with <PLACEHOLDER> with your actual values
    # This is a sample configuration - customize according to your environment

    # By default, Omnia merges custom configuration sources with defaults
    # and existing configurations to ensure a complete and valid setup.

    # For supported conf parameters, see https://slurm.schedmd.com/slurm.conf.html

    # CLUSTER IDENTITY
    ClusterName=slurm_cluster
    SlurmctldHost=<CONTROLLER_HOSTNAME>

    # AUTHENTICATION
    AuthType=auth/munge
    CredType=cred/munge

    # SLURM USER
    SlurmUser=slurm

    # DIRECTORIES AND FILES
    StateSaveLocation=/var/spool/slurmctld
    SlurmdSpoolDir=/var/spool/slurmd
    SlurmctldPidFile=/var/run/slurmctld.pid
    SlurmdPidFile=/var/run/slurmd.pid
    Epilog=/etc/slurm/epilog.sh

    # PORTS
    SlurmctldPort=6817
    SlurmdPort=6818

    # PLUGINS
    PluginDir=/usr/lib64/slurm
    ProctrackType=proctrack/cgroup
    PrologFlags=contain
    TaskPlugin=task/cgroup
    MpiDefault=none
    JobAcctGatherType=jobacct_gather/linux
    JobAcctGatherFrequency=30

    # SCHEDULING
    SchedulerType=sched/backfill
    SelectType=select/cons_tres

    # TIMEOUTS
    SlurmctldTimeout=120
    SlurmdTimeout=300

    # PARAMETERS
    ReturnToService=2
    SlurmctldParameters=enable_configless

    # ACCOUNTING (Optional)
    AccountingStorageHost=<SLURMDBD_HOSTNAME>
    AccountingStoragePort=6819
    AccountingStorageType=accounting_storage/slurmdbd

    # COMPUTE NODES
    NodeName=<NODE_HOSTNAME> Sockets=2 CoresPerSocket=8 ThreadsPerCore=2 RealMemory=32000 State=UNKNOWN

    # PARTITIONS
    # Define at least one partition
    PartitionName=DEFAULT Nodes=ALL MaxTime=INFINITE State=UP
    PartitionName=normal Nodes=<NODE_LIST> Default=YES MaxTime=INFINITE State=UP

slurmdbd.conf
^^^^^^^^^^^^^

::

    # Sample SlurmDBD Configuration File
    # Replace values marked with <PLACEHOLDER> with your actual values
    # This is a sample configuration - customize according to your environment
    # For more information, see https://slurm.schedmd.com/slurmdbd.conf.html

    # Authentication
    AuthType=auth/munge
    SlurmUser=slurm

    # Database Daemon Configuration
    DbdHost=<DBD_HOST>
    DbdPort=6819
    LogFile=/var/log/slurm/slurmdbd.log
    PidFile=/var/run/slurmdbd.pid
    PluginDir=/usr/lib64/slurm

    # Database Connection
    StorageType=accounting_storage/mysql
    StorageHost=<DB_HOST>
    StoragePort=3306
    StorageLoc=slurm_acct_db
    StorageUser=slurm
    StoragePass=<db_password>