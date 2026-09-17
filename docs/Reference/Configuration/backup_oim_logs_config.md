# OIM Log Backup Configuration

The optional `backup_oim_logs_config.yml` file selects the Omnia domain logs
to archive on the OIM and the local or NFS backup destination.

After initializing Utils, edit:

```text
$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/backup_oim_logs_config.yml
```

## Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `domains` | List of strings | No | All supported domains | Domains whose `$OMNIA_DATA_PATH/<domain>/log` directories are included. Supported values are `repo_manager`, `image_build_manager`, `orchestrator`, `discovery`, `telemetry`, `build_stream`, and `utils`. An empty list selects all supported domains. |
| `backup_path` | String | No | `$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/backup_oim_logs` | Destination directory. Use an absolute path for local storage or `server:/export/path` for NFS. |

## Example

```yaml title="backup_oim_logs_config.yml"
domains:
  - repo_manager
  - image_build_manager
  - orchestrator
  - utils
backup_path: "/mnt/omnia-backups/oim-logs"
```

To use NFS, change `backup_path` to a raw NFS export:

```yaml
backup_path: "192.0.2.20:/exports/omnia/oim-logs"
```

## Destination precedence

The workflow resolves the destination in this order:

1. `backup_path` passed with `-e`
2. `backup_path` in this configuration file
3. `OMNIA_BACKUP_PATH`
4. The default Utils project output path

For example, the following command overrides both the configuration file and
environment value for that run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags backup_oim_logs \
      -e backup_path="/mnt/temporary-oim-backup"
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils
    ansible-playbook playbooks/utils.yml --tags backup_oim_logs \
      -e backup_path="/mnt/temporary-oim-backup"
    ```

!!! warning

    Restrict access to the destination. The generated archive can contain
    sensitive operational information from every selected domain.

!!! note

    `OMNIA_PROJECT_NAME` scopes the default backup destination and the
    configuration-file location. It does not filter the source domain log
    directories by project.

## Related documentation

- [Back Up OIM Logs](../../HowTo/utils/backup_oim_logs.md)
- [Clean Up Utils](../../HowTo/utils/cleanup_utils.md)
- [Utils Contract](../domain_contracts/utils_contract.md)

