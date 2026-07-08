
# Slurm Configuration File

This section provides a sample slurm.conf file with detailed inline comments explaining the purpose and usage of each configuration parameter.
If a custom slurm.conf is not supplied, Omnia automatically generates one based on the cluster inventory and deployment settings. The generated configuration is suitable for most standard deployments and serves as the primary source of configuration for the Slurm controller and compute nodes.
Use this reference when customizing scheduler behavior, defining partitions, tuning resource management, configuring accounting settings, or modifying node and cluster parameters to meet specific workload requirements. Reviewing and understanding these settings is especially important in large-scale or heterogeneous HPC environments, where scheduler configuration directly impacts job placement, resource utilization, and cluster performance.

## slurm.conf


```bash title="File: /etc/slurm/slurm.conf"
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
```

!!! note

    - Adjust `CPUs`, `RealMemory`, `Sockets`, `CoresPerSocket`, and
      `Gres` to match your actual hardware. Mismatched values cause nodes to
      register as `DRAIN`.
    - Node names must match the hostnames in the PXE mapping file.

!!! info

    - [Slurmdbd Conf](slurmdbd_conf.md) -- Companion `slurmdbd.conf` configuration.
    - [Omnia Config](../Configuration/omnia_config.md) -- Omnia-level Slurm settings.
    - [Slurm documentation](https://slurm.schedmd.com/slurm.conf.html) --
      Upstream parameter reference.
