# Slurm Configuration Utilities

## Overview

Use the Utils domain to back up, remove, and restore the active Slurm
configuration stored on the configured Slurm NFS share. You can also remove
stored Slurm configuration backups when they are no longer required.

Run one operation tag at a time:

| Operation | Tag |
|---|---|
| Back up the active Slurm configuration | `slurm_config_backup` |
| Delete the active Slurm configuration | `slurm_config_cleanup` |
| Restore a stored configuration | `slurm_config_rollback` |
| Delete all stored configuration backups | `cleanup_slurm_config_backups` |

!!! note

    The Utils lifecycle tag `rollback` is a placeholder. Use
    `slurm_config_rollback` to restore a Slurm configuration backup.

## Prerequisites

- Complete the [OIM setup](../main/setup_oim.md).
- Deploy and verify a working Slurm cluster.
- Initialize the Utils domain after updating the source:

  ```bash title="Run from: <omnia-repository>/src/main"
  ./omnia.sh -i utils
  ```

- Confirm that the Utils project input directory contains valid
  `omnia_config.yml` and `storage_config.yml` files. The first
  `slurm_cluster` entry must reference an NFS storage name that exists in the
  `mounts` list in `storage_config.yml`.
- Confirm that the Slurm NFS `mount_point` is mounted and writable on the OIM.
- Provide a PXE mapping containing a `slurm_control_node_*` functional group.
  The default mapping is
  `$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/nodes_slurm.yaml`. A CSV
  `pxe_mapping_file.csv` can be selected through the optional configuration.
- For rollback, confirm passwordless root SSH access from the OIM to the first
  Slurm controller in the mapping. The controller must have `slurmctld`,
  `slurmdbd`, and `scontrol` available as applicable.
- Schedule cleanup and rollback during an approved maintenance window.

## Configure the utility

The optional project configuration is:

```text
$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/slurm_config_util_config.yml
```

Defaults are used when the file is absent or its path overrides are empty. See
[Slurm Config Utility Configuration](../../Reference/Configuration/slurm_config_util_config.md)
for all parameters.

### Source the input files

The Slurm configuration workflows expect their default inputs in:

```text
$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/
├── omnia_config.yml
├── storage_config.yml
└── nodes_slurm.yaml
```

These files are normally generated in other Omnia domains. Copy the applicable
files into the Utils input directory:

| Required input | Source location |
|---|---|
| `omnia_config.yml` | `$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/omnia_config.yml` |
| `storage_config.yml` | `$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/storage_config.yml` |
| `nodes_slurm.yaml` | `$OMNIA_DATA_PATH/openchami/workdir/nodes/nodes_slurm.yaml` |

As an alternative to `nodes_slurm.yaml`, copy the Orchestrator-generated
`$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv`
into the Utils input directory and set `pxe_mapping_path` to the copied file.
The mapping format is detected from its extension: `.csv` selects CSV, and
every other extension selects YAML.

!!! note

    Copy these inputs rather than creating symbolic links. To keep them in
    their source locations, override `omnia_config_path`, `storage_config_path`,
    and `pxe_mapping_path` in `slurm_config_util_config.yml` or with
    command-line extra variables.

The backup destination is selected in this order:

1. `slurm_backup_path` supplied as a command-line extra variable.
2. `slurm_backup_path` in `slurm_config_util_config.yml`.
3. `OMNIA_BACKUP_PATH`.
4. `$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/slurm_config_util`.

The destination can be an absolute local path or a raw NFS export in
`server:/export/path` format.

## Back up the Slurm configuration

Run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags slurm_config_backup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils
    ansible-playbook playbooks/utils.yml --tags slurm_config_backup
    ```

To select a destination or backup prefix for one run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags slurm_config_backup \
      -e slurm_backup_path="192.0.2.20:/exports/omnia/slurm" \
      -e backup_base_name="before_maintenance"
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils
    ansible-playbook playbooks/utils.yml --tags slurm_config_backup \
      -e slurm_backup_path="192.0.2.20:/exports/omnia/slurm" \
      -e backup_base_name="before_maintenance"
    ```

The utility identifies the first Slurm controller in the PXE mapping and
copies these directories from the active Slurm configuration:

- `etc/slurm`
- `etc/munge`
- `etc/my.cnf.d`

The default output layout is:

```text
$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/slurm_config_util/
└── slurm_config_<YYYYMMDD-HHMMSS>/
    ├── <controller-hostname>/
    │   ├── etc/slurm/
    │   ├── etc/munge/
    │   └── etc/my.cnf.d/
    └── metadata.json
```

`metadata.json` records the backup ID, generation time, controller, source and
destination, included directories, and SHA-256 checksums of copied files.

!!! important

    The current backup task continues when an individual copy or checksum
    command fails. Verify the expected directories, `slurm.conf`, `munge.key`,
    and checksum entries before treating the backup as recoverable.

## Delete the active Slurm configuration

Run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags slurm_config_cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils
    ansible-playbook playbooks/utils.yml --tags slurm_config_cleanup
    ```

The workflow asks whether to create a backup first. It then requires the exact
configured confirmation token, `YES` by default.

!!! danger

    `slurm_config_cleanup` recursively deletes the complete active Slurm
    configuration directory resolved from the configured NFS mount point and
    `slurm_share_dir_name`. This affects all controller directories below that
    path and cannot be undone without a verified backup.

## Restore a Slurm configuration

Run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags slurm_config_rollback
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils
    ansible-playbook playbooks/utils.yml --tags slurm_config_rollback
    ```

After the command starts:

1. Review the displayed backups and enter the number of the backup to restore.
2. Review any missing-file warnings. A backup without `slurm.conf` cannot be
   restored. Continue past other missing-file warnings only after confirming
   that the missing content is not required.
3. When prompted, choose whether to create a safety backup of the current
   configuration before continuing.
4. Wait for the restore and controller reconfiguration to complete.
5. Run the commands in [Verification](#verification) before resuming workload
   operations.

During the restore, the utility restores `etc/slurm`, `etc/munge`, and
`etc/my.cnf.d`, attempts to remount stale controller mounts, repairs required
file permissions, conditionally restarts `slurmdbd`, and runs
`scontrol reconfigure`.

!!! warning

    If the workflow reports that the on-disk restore completed but controller
    reconfiguration failed, correct the controller service or configuration
    issue before attempting another rollback.

## Delete stored Slurm configuration backups

To remove every backup-run directory from the resolved backup destination,
run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup_slurm_config_backups
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils
    ansible-playbook playbooks/utils.yml --tags cleanup_slurm_config_backups
    ```

For a custom destination, use the same `slurm_backup_path` used to create the
backups.

!!! danger

    `cleanup_slurm_config_backups` has no retention period and does not request
    confirmation. It removes every run directory immediately below the
    resolved backup destination. Copy required backups elsewhere first.

    The general Utils `cleanup` tag also includes this operation.

## Verification

Review the latest Utils status and the backup content:

```bash title="Run on: OIM"
cat "$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/utils_status.yml"
find "$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/slurm_config_util" \
  -maxdepth 4 -type f
```

After rollback, verify the controller and node state:

```bash title="Run on: Slurm controller node"
systemctl status munge slurmdbd slurmctld --no-pager
scontrol ping
sinfo
scontrol show nodes
```

## Next steps

- [Clean up Utils](cleanup_utils.md) when stored utility artifacts are no
  longer required.
- [Verify the cluster](../../Operations/verify_cluster.md) before resuming
  workload operations after a rollback.
- [Configure Slurm](../orchestrator/configure_slurm.md) when the desired
  configuration must be changed rather than restored.

## Troubleshooting

- **An input file is not found**: Confirm the active project and the paths in
  `slurm_config_util_config.yml`. Confirm that the required files were copied
  into the Utils project input directory, or configure explicit source paths.
  Run `./omnia.sh -i utils` to stage the latest optional Utils configuration.
- **No Slurm controller is found**: Confirm that the YAML or CSV mapping
  contains a functional group beginning with `slurm_control_node_`.
- **The backup NFS destination cannot be mounted**: Confirm DNS or IP
  reachability, export permissions, NFS client packages, and
  `server:/export/path` syntax.
- **No backups are listed**: Supply the same `slurm_backup_path` used for the
  backup and confirm that run directories exist immediately below it.
- **Rollback reports missing content**: Do not continue unless the missing
  files are understood. A selected backup without `slurm.conf` cannot be used.
- **Rollback cannot recover a stale mount**: On the Slurm controller, run the
  applicable command for each path reported as stale:

  ```bash title="Run on: Slurm controller node"
  umount -l /etc/slurm && mount /etc/slurm
  umount -l /etc/munge && mount /etc/munge
  umount -l /etc/my.cnf.d && mount /etc/my.cnf.d
  ```

  Then rerun rollback:

  === "Using omnia.sh (recommended)"

      ```bash title="Run on: OIM host"
      cd <OMNIA_SOURCE_PATH>/src/main
      ./omnia.sh --run utils --tags slurm_config_rollback
      ```

  === "Using ansible-playbook"

      ```bash title="Run on: OIM host"
      source /opt/omnia/activate-omnia.sh
      cd <OMNIA_SOURCE_PATH>/src/utils
      ansible-playbook playbooks/utils.yml --tags slurm_config_rollback
      ```
- **`scontrol reconfigure` fails**: Review
  `journalctl -u slurmctld -n 50`, verify Munge and Slurm services, correct
  configuration errors, and run `scontrol reconfigure` again.

See [Utils Issues](../../Troubleshooting/utils/utils.md) for additional
resolutions.
