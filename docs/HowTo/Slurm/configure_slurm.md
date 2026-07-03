
# Slurm Configuration Files

Omnia provides flexible mechanisms to manage Slurm configuration files (`slurm.conf`, `slurmdbd.conf`, `cgroup.conf`, `gres.conf`). You can use the default configurations or supply custom configurations through the `config_sources` parameter in `omnia_config.yml`.

## Default configuration

Omnia applies a default configuration optimized for HPC clusters. These defaults are used unless overridden via `config_sources`.

### Default partition and node settings

| Setting | Default value |
| --- | --- |
| Partition name | `normal` (all compute nodes from PXE mapping file) |
| Partition config | `PartitionName=normal Nodes=<compute_nodes> MaxTime=INFINITE State=UP` |
| Node config (iDRAC unreachable) | `NodeName=<nodename> Sockets=1 CoresPerSocket=1 ThreadsPerCore=1 RealMemory=3686` |

### Default slurm.conf

!!! note

    The parameters `ClusterName`, `SlurmctldHost`, and `AccountingStorageHost` are auto-detected and cannot be modified.

```bash title="File: /etc/slurm/slurm.conf (defaults)"
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
```

### Default slurmdbd.conf

!!! note

    The parameters `DbdHost` and `StorageHost` are auto-detected and cannot be modified.

```bash title="File: /etc/slurm/slurmdbd.conf (defaults)"
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
```

### Default cgroup.conf

```bash title="File: /etc/slurm/cgroup.conf (defaults)"
CgroupPlugin=autodetect
ConstrainCores=yes
ConstrainDevices=yes
ConstrainRAMSpace=yes
ConstrainSwapSpace=yes
```

### Default gres.conf

```bash title="File: /etc/slurm/gres.conf (defaults)"
AutoDetect=nvml
```

## Custom configuration sources

Custom configuration files are supplied through the `config_sources` parameter in `omnia_config.yml`. Two methods are available:

### Parameter-based configuration

Specify individual parameters directly. Omnia merges these values with the defaults:

```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
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
```

### File-based configuration

Provide complete custom configuration files:

```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
slurm_cluster:
  - cluster_name: slurm_cluster
    nfs_storage_name: nfs_slurm
    config_sources:
      slurm: /path/to/custom_slurm.conf
      cgroup: /path/to/custom_cgroup.conf
      slurmdbd: /path/to/custom_slurmdbd.conf
      gres: /path/to/custom_gres.conf
```

## Merge behavior (skip_merge)

By default, Omnia merges user-provided configurations with defaults to produce a complete configuration. Set `skip_merge: true` to deploy file-based configurations directly without merging:

```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
slurm_cluster:
  - cluster_name: slurm_cluster
    nfs_storage_name: nfs_slurm
    skip_merge: true
    config_sources:
      slurm: /path/to/custom_slurm.conf
      cgroup: /path/to/custom_cgroup.conf
      slurmdbd: /path/to/custom_slurmdbd.conf
      gres: /path/to/custom_gres.conf
```

!!! warning

    When `skip_merge: true` is set:

    - Only file-based `config_sources` are supported (not parameter-based).
    - The provided configuration file must be complete and valid.
    - Omnia does not supplement missing values from defaults.

## Configuration validation

Omnia validates Slurm configuration files (`slurm.conf`, `slurmdbd.conf`, `cgroup.conf`, `gres.conf`) before deployment. The validator checks that:

- Parameters are recognized by the supported Slurm version.
- Parameter values match expected data types.
- Common configuration errors are detected before deployment.

!!! info

    - [slurm.conf Reference](../../Reference/SampleFiles/slurm_conf.md) -- Sample `slurm.conf` with inline comments.
    - [slurmdbd.conf Reference](../../Reference/SampleFiles/slurmdbd_conf.md) -- Sample `slurmdbd.conf`.
    - [Omnia Config](../../Reference/Configuration/omnia_config.md) -- `slurm_cluster` and `config_sources` parameters.
    - [Slurm documentation](https://slurm.schedmd.com/slurm.conf.html) -- Upstream parameter reference.
