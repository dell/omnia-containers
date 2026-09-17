# Back Up OIM Logs

## Overview

Use the Utils `backup_oim_logs` workflow to create a compressed backup of
Omnia domain logs stored on the Omnia Infrastructure Manager (OIM). The backup
can be written to a local directory or an NFS export.

This workflow is different from the Utils `collect` workflow. `collect`
connects to provisioned Kubernetes and Slurm nodes to gather cluster logs;
`backup_oim_logs` archives the logs already stored below
`$OMNIA_DATA_PATH/<domain>/log` on the OIM.

!!! warning

    Log archives can contain hostnames, addresses, configuration details, and
    other sensitive operational data. Store them in a restricted location and
    share them only with authorized users.

## Prerequisites

- Complete the [OIM setup](../main/setup_oim.md).
- Initialize Utils with `./omnia.sh -i utils`.
- Ensure that the account running Omnia can read the selected domain log
  directories and write to the backup destination.
- For an NFS destination, ensure that the OIM can resolve and reach the NFS
  server and mount the export.
- Estimate the size of the selected domain logs and provide sufficient free
  space at the destination.

## Configure the backup

The configuration file is:

```text
$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/backup_oim_logs_config.yml
```

To back up selected domains to a local directory, configure:

```yaml title="backup_oim_logs_config.yml"
domains:
  - repo_manager
  - image_build_manager
  - orchestrator
  - utils
backup_path: "/mnt/omnia-backups/oim-logs"
```

For an NFS export, use `server:/export/path` format:

```yaml title="backup_oim_logs_config.yml"
domains:
  - repo_manager
  - image_build_manager
  - orchestrator
  - discovery
  - telemetry
  - build_stream
  - utils
backup_path: "192.0.2.20:/exports/omnia/oim-logs"
```

When `domains` is empty or omitted, the workflow attempts to include all seven
supported domains. When `backup_path` is empty or omitted, the default is:

```text
$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/backup_oim_logs
```

The backup destination is resolved in this order:

1. `backup_path` supplied as an Ansible extra variable
2. `backup_path` in `backup_oim_logs_config.yml`
3. `OMNIA_BACKUP_PATH` in the environment
4. The default Utils project output directory shown above

See [OIM Log Backup Configuration](../../Reference/Configuration/backup_oim_logs_config.md)
for the complete input reference.

!!! note

    The source paths are domain-level log directories, not project-filtered
    paths. A selected domain backup can therefore include logs associated with
    more than one Omnia project when they exist below that domain's `log`
    directory.

## Run the backup

Choose one execution method:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags backup_oim_logs
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    ansible-playbook utils.yml --tags backup_oim_logs
    ```

To override only the destination for one run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags backup_oim_logs \
      -e backup_path="192.0.2.20:/exports/omnia/oim-logs"
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    ansible-playbook utils.yml --tags backup_oim_logs \
      -e backup_path="192.0.2.20:/exports/omnia/oim-logs"
    ```

The workflow skips a selected domain whose log directory does not exist and
records a warning in the metadata. It fails when none of the requested domain
log directories exist.

Temporary files with the suffixes `.tmp`, `.temp`, and `.bak` are excluded
from the archive.

## Verify the backup

Each run creates the following layout at the resolved destination:

```text
omnia_oim_logs_<YYYYMMDD-HHMMSS>/
├── omnia_oim_logs_<YYYYMMDD-HHMMSS>.tar.gz
└── metadata.json
```

`metadata.json` records the included and skipped domains, generation times,
triggering user, OIM operating system, destination, exclusions, warnings, and
archive SHA-256 checksum.

For a local destination, verify the archive against its recorded checksum:

```bash title="Run on: OIM"
cd <backup_path>/omnia_oim_logs_<timestamp>
sha256sum omnia_oim_logs_<timestamp>.tar.gz
cat metadata.json
```

Confirm that the calculated checksum matches `archive_sha256`, and inspect the
archive contents before transferring or relying on the backup:

```bash title="Run on: OIM"
tar -tzf omnia_oim_logs_<timestamp>.tar.gz
```

## Clean up backups

Use the dedicated cleanup tag only after preserving every required backup:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup_backup_oim_logs
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    ansible-playbook utils.yml --tags cleanup_backup_oim_logs
    ```

!!! danger

    This command removes every directory named `omnia_oim_logs_*` from the
    resolved backup destination. It does not apply a retention period or ask
    for confirmation. The general Utils `cleanup` tag does not run this backup
    cleanup workflow.

For custom or NFS storage, ensure that cleanup resolves the same destination
used for the backup. See [Clean Up Utils](cleanup_utils.md) for details.

## Troubleshooting

- **The NFS destination cannot be mounted**: Confirm DNS or IP connectivity,
  export permissions, firewall access, and `server:/export/path` syntax.
- **A domain is skipped**: Confirm that
  `$OMNIA_DATA_PATH/<domain>/log` exists and is readable on the OIM.
- **No logs are available**: Generate or restore the requested domain logs,
  or select a domain that has an existing `log` directory.
- **The destination is not writable**: Correct directory or NFS export
  permissions and verify available space before rerunning the workflow.
- **Checksum verification fails**: Do not use or transfer the archive. Remove
  the incomplete run directory and create a new backup.
