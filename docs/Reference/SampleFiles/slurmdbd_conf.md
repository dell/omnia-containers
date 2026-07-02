
# Sample slurmdbd.conf


This page provides a sample `slurmdbd.conf` with inline comments. The Slurm
Database Daemon (`slurmdbd`) stores job accounting, user associations, and
cluster usage data in a relational database.

## Complete sample


```bash title="File: /etc/slurm/slurmdbd.conf"
# ===========================================================================
# slurmdbd.conf -- Slurm Database Daemon configuration
# This file must be readable only by the SlurmUser (typically 'slurm').
# Permissions: 0600, owned by slurm:slurm.
# ===========================================================================

# ---------------------------------------------------------------------------
# Daemon identification
# ---------------------------------------------------------------------------
DbdHost=slurm-ctrl-01            # Hostname where slurmdbd runs.
                                 # Must match the SlurmctldHost or be
                                 # reachable from the controller.
DbdPort=6819                     # Port slurmdbd listens on.
                                 # Must match AccountingStoragePort in
                                 # slurm.conf.
SlurmUser=slurm                  # User account under which slurmdbd runs.

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AuthType=auth/munge              # Must match AuthType in slurm.conf.

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LogFile=/var/log/slurmdbd.log
DebugLevel=info                  # Log level: quiet, fatal, error, info,
                                 # verbose, debug, debug2-debug5.
PidFile=/var/run/slurmdbd.pid

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
StorageType=accounting_storage/mysql  # Database backend. MySQL/MariaDB
                                      # is the only supported option.
StorageHost=localhost                 # Database server hostname or IP.
                                      # Use localhost if the database runs
                                      # on the same node as slurmdbd.
StoragePort=3306                      # MySQL/MariaDB port.
StorageLoc=slurm_acct_db             # Database name. Omnia creates this
                                      # database automatically.
StorageUser=slurm_db_user            # Database username.
StoragePass=/run/secrets/slurmdbd_db_pass  # Path to a file containing the
                                            # database password, or the
                                            # password string directly.
                                            # File-based is recommended for
                                            # security.

# ---------------------------------------------------------------------------
# Purge settings
# ---------------------------------------------------------------------------
PurgeEventAfter=12months         # Purge cluster event records older than
                                 # this. Format: Nmonths, Ndays, Nhours.
PurgeJobAfter=12months           # Purge completed job records.
PurgeStepAfter=6months           # Purge job step records.
PurgeResvAfter=6months           # Purge reservation records.
PurgeSuspendAfter=1month         # Purge job suspend records.
PurgeTXNAfter=12months           # Purge transaction records.

# ---------------------------------------------------------------------------
# Archive settings (optional)
# ---------------------------------------------------------------------------
# ArchiveEvents=yes
# ArchiveJobs=yes
# ArchiveDir=/var/spool/slurmdbd/archive
# ArchiveScript=/usr/local/bin/slurm_archive.sh

# ---------------------------------------------------------------------------
# Performance tuning
# ---------------------------------------------------------------------------
CommitDelay=1                    # Seconds to batch database commits.
                                 # Reduces database write load at the
                                 # cost of slight data lag.
MessageTimeout=10                # Seconds before an RPC times out.
TCPTimeout=120                   # TCP connection timeout in seconds.
```



## Key parameter reference


| Parameter | Description |
| --- | --- |
| `DbdHost` | Hostname or IP where `slurmdbd` listens. Usually the Slurm control node. |
| `DbdPort` | TCP port for `slurmdbd` connections (default: `6819`). |
| `StorageType` | `accounting_storage/mysql` for MySQL/MariaDB backend. |
| `StorageHost` | Database server address. Use `localhost` when co-located with `slurmdbd`. |
| `StorageLoc` | Database name. Omnia creates this automatically during setup. |
| `StorageUser` | Database user with privileges on `StorageLoc`. |
| `StoragePass` | Database password or path to password file. |
| `PurgeJobAfter` | Retention period for completed job records. Prevents unbounded database growth. |
| `CommitDelay` | Batching interval for database writes. Higher values reduce I/O but increase data-loss risk on crash. |

## File permissions


!!! warning

    `slurmdbd.conf` contains database credentials and must have restrictive
    permissions:

    ```bash
    chown slurm:slurm /etc/slurm/slurmdbd.conf
    chmod 0600 /etc/slurm/slurmdbd.conf
    ```


    Slurmdbd refuses to start if the file is world-readable.

## Database prerequisites


| Requirement | Details |
| --- | --- |
| MariaDB or MySQL installed | Omnia installs MariaDB from the RHEL repository by default. |
| Database created | Omnia creates the `slurm_acct_db` database and grants privileges to `slurm_db_user` during `omnia.yml` execution. |
| innodb_buffer_pool_size | For clusters with > 500 nodes, increase this MySQL parameter to at least 1 GB for acceptable accounting query performance. |

!!! info

    - [Slurm Conf](slurm_conf.md) -- Companion `slurm.conf` configuration.
    - [Omnia Config](../Configuration/omnia_config.md) -- Omnia-level Slurm
      settings.
    - [Ports](../../Overview/security_configuration_guide.md#slurm-port-requirements) -- Port 6819 for slurmdbd.
    - [Slurm documentation](https://slurm.schedmd.com/slurmdbd.conf.html) --
      Upstream parameter reference.
