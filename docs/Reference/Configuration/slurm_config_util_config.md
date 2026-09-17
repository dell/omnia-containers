# Slurm Config Utility Configuration

The optional `slurm_config_util_config.yml` file controls input-path,
Slurm-share, backup-destination, and interactive behavior overrides for the
Utils Slurm configuration workflows.

After initializing Utils, edit:

```text
$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/slurm_config_util_config.yml
```

When this file is absent, the utility derives its inputs and output locations
from the active Omnia project.

## Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `omnia_config_path` | Absolute path | No | `$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/omnia_config.yml` | Omnia configuration containing `slurm_cluster` and its `nfs_storage_name`. |
| `storage_config_path` | Absolute path | No | `$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/storage_config.yml` | Storage configuration containing the matching NFS entry in `mounts`. |
| `pxe_mapping_path` | Absolute path | No | `$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/nodes_slurm.yaml` | YAML `nodes_slurm.yaml` or CSV `pxe_mapping_file.csv` used to find the first `slurm_control_node_*` controller. The format is selected from the filename extension (`.csv` selects CSV; every other extension selects YAML). |
| `slurm_share_dir_name` | String | No | `slurm` | Active configuration directory below the selected NFS `mount_point`. |
| `slurm_backups_dir_name` | String | No | `slurm_backups` | Reserved directory-name setting. The current workflow selects its backup root through `slurm_backup_path`; do not use this field to change the backup destination. |
| `nfs_storage_name` | String | No | First `slurm_cluster` entry's `nfs_storage_name` | Selects a specific `storage_config.yml` mount by name. |
| `slurm_backup_path` | String | No | Utils project output | Absolute local directory or raw NFS export in `server:/export/path` format. |
| `backup_base_name` | String | No | `slurm_config` | Intended prefix for timestamped backup directories. For a reliable per-run override in the current source, pass `-e backup_base_name=<name>`. |
| `slurm_cleanup_confirm_token` | String | No | `YES` | Exact token required before deleting the active Slurm configuration. |
| `rollback_backup_list_limit` | Integer | No | `20` | Maximum number of backups displayed, newest first, during rollback selection. |

## Example

```yaml title="slurm_config_util_config.yml"
omnia_config_path: ""
storage_config_path: ""
pxe_mapping_path: ""

slurm_share_dir_name: "slurm"
slurm_backups_dir_name: "slurm_backups"
nfs_storage_name: ""

slurm_backup_path: "192.0.2.20:/exports/omnia/slurm"
backup_base_name: "slurm_config"

slurm_cleanup_confirm_token: "YES"
rollback_backup_list_limit: 20
```

## Input resolution

The three Slurm configuration operations resolve `omnia_config_path`,
`storage_config_path`, and `pxe_mapping_path` in this order:

1. Command-line extra variable.
2. Value in `slurm_config_util_config.yml`.
3. Project-derived default.

## Input file sourcing

By default, place the following files in
`$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/`:

| Utils input | Source |
|---|---|
| `omnia_config.yml` | Copy from `$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/omnia_config.yml`. |
| `storage_config.yml` | Copy from `$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/storage_config.yml`. |
| `nodes_slurm.yaml` | Copy the OpenCHAMI-generated mapping from `$OMNIA_DATA_PATH/openchami/workdir/nodes/nodes_slurm.yaml`. |
| `pxe_mapping_file.csv` | As a CSV alternative, copy from `$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv`. |

Copy the files into the Utils input directory; do not create symbolic links.
Alternatively, set the three path parameters in this file or pass them as
command-line extra variables to read the source files from another location.

The backup destination uses a separate order:

1. Command-line `slurm_backup_path`.
2. `slurm_backup_path` in this configuration file.
3. `OMNIA_BACKUP_PATH`.
4. `$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/slurm_config_util`.

For example:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags slurm_config_backup \
      -e slurm_backup_path="/mnt/omnia-backups/slurm" \
      -e backup_base_name="before_upgrade"
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags slurm_config_backup \
      -e slurm_backup_path="/mnt/omnia-backups/slurm" \
      -e backup_base_name="before_upgrade"
    ```

!!! warning

    Ensure the configured active Slurm path and backup destination are
    different. `slurm_config_cleanup` deletes the complete active Slurm
    configuration path, while `cleanup_slurm_config_backups` deletes every run
    directory below the resolved backup destination.

## Related documentation

- [Slurm Configuration Utilities](../../HowTo/utils/backup_slurm_config.md)
- [Clean Up Utils](../../HowTo/utils/cleanup_utils.md)
- [Utils Contract](../domain_contracts/utils_contract.md)
