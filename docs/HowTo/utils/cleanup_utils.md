# Clean Up Utils

## Overview

The Utils domain provides separate cleanup workflows for cluster-log
collection, unattended operating-system installation, OIM log backups, and
Slurm configuration backups. Use a scoped tag when only one utility must be
cleaned. The general `cleanup` tag runs all four cleanup playbooks.

!!! warning

    Utils cleanup deletes artifacts. Copy any required support, OIM log, and
    Slurm configuration backups before cleaning them, and confirm whether
    installation credentials must be preserved before cleaning the OS-install
    workflow.

## Prerequisites

- Complete the [OIM setup](../main/setup_oim.md).
- Initialize the Utils domain with `./omnia.sh -i utils`.
- Confirm `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` select the intended
  project.
- Copy log archives and configuration backups that must be retained out of
  the Utils project output or custom backup destination.

## Procedure

To clean every Utils workflow, run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags cleanup
    ```

!!! danger

    The general `cleanup` tag removes cluster-log artifacts, OS-installation
    temporary files, OIM log-backup runs, and all Slurm configuration backup
    runs. The two backup cleanup playbooks do not apply retention or request
    confirmation. Use a scoped cleanup tag when backups must be preserved.

To clean only log-collection artifacts, run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup_logs
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags cleanup_logs
    ```

The log cleanup checks for `omnia_logs_*.tar.gz` archives older than seven days
by default. It then removes every `omnia_logs_*` run directory and the
temporary `k8s` and `slurm` workspaces under:

```text
$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/collect/
```

Because each archive and its `metadata.json` are stored inside a run directory,
copy required files elsewhere before running this command.

To clean only unattended-installation artifacts, run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup_install_os
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags cleanup_install_os
    ```

This workflow removes `/tmp/install_os`, unmounts `/tmp/install_os_nfs` when it
is mounted, and removes the temporary NFS mount point. By default, it also
removes `install_os_credentials.yml` and `.install_os_credentials_key`. To
explicitly remove or preserve both credential files, pass the applicable
value:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup_install_os -e cleanup_credentials=true
    ./omnia.sh --run utils --tags cleanup_install_os -e cleanup_credentials=false
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags cleanup_install_os -e cleanup_credentials=true
    ansible-playbook utils.yml --tags cleanup_install_os -e cleanup_credentials=false
    ```

To remove OIM log backups, run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup_backup_oim_logs
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags cleanup_backup_oim_logs
    ```

The workflow resolves the destination with the same priority used by
`backup_oim_logs`: command-line `backup_path`, configuration-file
`backup_path`, `OMNIA_BACKUP_PATH`, and then the default project output path.
For a custom or NFS destination, supply or configure the same path used when
the backups were created.

!!! danger

    `cleanup_backup_oim_logs` removes every directory matching
    `omnia_oim_logs_*` at the resolved destination. It does not apply a
    retention period or ask for confirmation. Preserve required backups before
    running it.

To remove stored Slurm configuration backups, run:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags cleanup_slurm_config_backups
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
    export ANSIBLE_CONFIG=../ansible.cfg
    ansible-playbook utils.yml --tags cleanup_slurm_config_backups
    ```

The workflow resolves the destination using command-line
`slurm_backup_path`, configuration-file `slurm_backup_path`,
`OMNIA_BACKUP_PATH`, and then the following default, in that order:

```text
$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/slurm_config_util
```

For a custom or NFS destination, supply or configure the same path used when
the Slurm configuration backups were created.

!!! danger

    `cleanup_slurm_config_backups` removes every directory immediately below
    the resolved destination. It does not apply a retention period or ask for
    confirmation. This operation deletes stored backups; it does not delete
    the active Slurm configuration. See
    [Slurm Configuration Utilities](backup_slurm_config.md) for the distinction
    between this tag and `slurm_config_cleanup`.

## Verification

Review the domain status and the applicable artifact locations:

```bash title="Run on: OIM"
cat "$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/utils_status.yml"
find "$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/collect" \
  -maxdepth 2 -type f 2>/dev/null
find "$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/backup_oim_logs" \
  -maxdepth 2 -type f 2>/dev/null
find "$OMNIA_DATA_PATH/utils/output/$OMNIA_PROJECT_NAME/slurm_config_util" \
  -maxdepth 2 -type f 2>/dev/null
find "$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME" \
  -maxdepth 1 \( -name 'install_os_credentials.yml' \
  -o -name '.install_os_credentials_key' \)
```

Confirm that required support bundles were preserved and that credential files
match the choice made during cleanup.

## Next steps

- [Collect cluster logs](../../Operations/collect_cluster_logs.md) again after
  correcting the condition under investigation.
- [Install an OS unattended](install_os_unattended.md) again after reviewing
  the target BMC, administrative address, and installation disk.
- [Back up OIM logs](backup_oim_logs.md) again after reviewing the selected
  domains and destination.
- [Manage Slurm configuration](backup_slurm_config.md) to create a new verified
  backup or restore a retained backup.

## Troubleshooting

- **A required log bundle was removed**: The cleanup does not retain run
  directories based on archive age. Restore the bundle from the external copy.
- **The NFS mount remains active**: Check `mountpoint /tmp/install_os_nfs`,
  unmount it safely, and rerun the scoped cleanup.
- **OIM or Slurm backups remain after cleanup**: A custom destination may have
  been resolved differently. Run the applicable scoped cleanup tag with the
  same `backup_path` or `slurm_backup_path` used to create the backups.
- **Required Slurm backups were removed**: Neither the general cleanup nor
  `cleanup_slurm_config_backups` provides retention. Restore the backup from
  an external copy; it cannot be recovered from the cleaned destination.
- **Credentials are requested on the next installation**: The encrypted
  credential file was removed. Run the installation interactively and provide
  the BMC username, BMC password, and OS root password again.
