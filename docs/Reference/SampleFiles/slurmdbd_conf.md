
# Slurm Database Daemon Configuration

The Slurm Database Daemon (`slurmdbd`) stores job accounting, user associations, and
cluster usage data in a database. The configuration file (`/etc/slurm/slurmdbd.conf`) defines how `slurmdbd` connects to the database and manages accounting data.

## Complete sample


```bash title="File: /etc/slurm/slurmdbd.conf"
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
```

## Key parameter reference


| Parameter | Description |
| --- | --- |
| `DbdHost` | Hostname or IP where `slurmdbd` listens. Usually the Slurm control node. |
| `StorageHost` | Database server address. Use `localhost` when co-located with `slurmdbd`. |


!!! info

    - [Slurm Conf](slurm_conf.md) -- Companion `slurm.conf` configuration.
    - [Omnia Config](../Configuration/omnia_config.md) -- Omnia-level Slurm
      settings.
    - [Ports](../../Overview/security_configuration_guide.md#slurm-port-requirements) -- Port 6819 for slurmdbd.
    - [Slurm documentation](https://slurm.schedmd.com/slurmdbd.conf.html) --
      Upstream parameter reference.
