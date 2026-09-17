# Utils Issues

Use these resolutions for the current Utils environment, cluster-log
collection, OIM domain-log backup, unattended operating-system installation,
Slurm configuration management, and cleanup workflows. The Utils Ansible log is
`/var/log/omnia/utils/utils.log`.

## Environment precheck fails

???+ note "Symptom"

    `./omnia.sh --run utils --tags precheck` reports a hostname, domain,
    administrative IP, data-path, or environment-file failure.

??? note "Resolution"

    1. Confirm `/etc/omnia/omnia.env` exists and contains the intended OIM
       values.
    2. Compare `SYSTEM_HOSTNAME` with `hostname -s` and
       `SYSTEM_DOMAIN_NAME` with `hostname -d`.
    3. Confirm `SYSTEM_ADMIN_NIC_IPV4` is assigned to an OIM interface.
    4. Confirm `OMNIA_DATA_PATH` exists and is writable.
    5. Rerun `./omnia.sh --setup-venv` only after preserving intentional
       environment customizations.

## Utils input file is missing

???+ note "Symptom"

    `collect_pxe.yml`, `install_os_config.yml`, `backup_oim_logs_config.yml`,
    or the optional `slurm_config_util_config.yml` is not present in the active
    project input directory.

??? note "Resolution"

    1. From `src/main`, run `./omnia.sh -i utils`.
    2. Confirm `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` select the expected
       project.
    3. Edit the staged file under
       `$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/`.

## Log collection is incomplete

???+ note "Symptom"

    The support archive contains warnings or an
    `SSH_COLLECTION_FAILED.txt` marker for one or more nodes.

??? note "Resolution"

    1. Verify that the administrative IP in `collect_pxe.yml` is correct.
    2. Confirm passwordless SSH access from the OIM to the affected node.
    3. Review the warning records in `metadata.json` for unreachable nodes,
       missing sources, or collection errors.
    4. Correct the reported issue and rerun
       `./omnia.sh --run utils --tags collect`.

## General Utils cleanup removes stored Slurm backups

???+ note "Symptom"

    `./omnia.sh --run utils --tags cleanup` completes, but
    Slurm configuration backup run directories have been removed.

??? note "Resolution"

    This is expected in the current source. The general `cleanup` tag includes
    `cleanup_slurm_config_backups`. Restore required content from an external
    copy. In future runs, use only the scoped cleanup tag for the workflow that
    must be cleaned.

## Slurm configuration input cannot be resolved

???+ note "Symptom"

    A Slurm configuration operation reports a missing `omnia_config.yml`,
    `storage_config.yml`, or PXE mapping file, or reports an empty
    `slurm_cluster` configuration.

??? note "Resolution"

    1. Confirm `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` select the deployed
       Slurm project.
    2. Review path overrides in
       `$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/slurm_config_util_config.yml`.
    3. When using the defaults, confirm that `omnia_config.yml`,
       `storage_config.yml`, and `nodes_slurm.yaml` were copied into
       `$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/`.
    4. Confirm that the selected `omnia_config.yml` contains a nonempty
       `slurm_cluster` list.
    5. Confirm that its `nfs_storage_name` matches a `mounts[].name` value in
       `storage_config.yml`.
    6. Confirm that the YAML or CSV node mapping exists at the resolved path.

## Slurm controller is not found in the mapping

???+ note "Symptom"

    The utility reports that the Slurm controller functional group is missing
    from the PXE mapping.

??? note "Resolution"

    1. For `nodes_slurm.yaml`, confirm that at least one node's `group` begins
       with `slurm_control_node_` and includes its administrative IP.
    2. For `pxe_mapping_file.csv`, confirm that `FUNCTIONAL_GROUP_NAME`,
       `HOSTNAME`, and `ADMIN_IP` are populated for a
       `slurm_control_node_*` row.
    3. Correct `pxe_mapping_path` when the wrong mapping was selected and rerun
       the operation.

## Slurm backup destination fails

???+ note "Symptom"

    `slurm_config_backup` cannot create the local destination or mount the
    configured NFS export.

??? note "Resolution"

    1. Confirm that `slurm_backup_path` is an absolute local path or uses
       `server:/export/path` NFS syntax.
    2. Confirm that the OIM can reach and mount the export and has write
       permission and sufficient capacity.
    3. Check whether a CLI `slurm_backup_path` or `OMNIA_BACKUP_PATH` is
       overriding `slurm_config_util_config.yml`.
    4. Verify that the completed run contains the controller directories,
       `slurm.conf`, `munge.key`, and checksum entries in `metadata.json`.

## No Slurm configuration backup is available

???+ note "Symptom"

    `slurm_config_rollback` reports that no backups were found or does not list
    an expected backup.

??? note "Resolution"

    1. Resolve the same `slurm_backup_path` used when the backup was created.
    2. Confirm that timestamped run directories exist immediately below the
       destination.
    3. Confirm the selected run contains
       `<controller>/etc/slurm/slurm.conf`; a backup without this file cannot
       be restored.
    4. Restore an externally retained backup to the destination when the
       backup cleanup workflow removed the original.

## Slurm rollback cannot recover a stale NFS mount

???+ note "Symptom"

    The on-disk restore completes, but `/etc/slurm`, `/etc/munge`, or
    `/etc/my.cnf.d` remains stale on the Slurm controller after the automatic
    remount attempt.

??? note "Resolution"

    1. On the Slurm controller, run the applicable command for each path
       reported as stale:

        ```bash title="Run on: Slurm controller node"
        umount -l /etc/slurm && mount /etc/slurm
        umount -l /etc/munge && mount /etc/munge
        umount -l /etc/my.cnf.d && mount /etc/my.cnf.d
        ```

    2. Confirm that the restored files can be read.
    3. Rerun rollback:

        === "Using omnia.sh (recommended)"

            ```bash
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run utils --tags slurm_config_rollback
            ```

        === "Using ansible-playbook"

            ```bash
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/utils/playbooks
            export ANSIBLE_CONFIG=../ansible.cfg
            ansible-playbook utils.yml --tags slurm_config_rollback
            ```

## Slurm rollback cannot reconfigure the controller

???+ note "Symptom"

    Rollback reports that `slurmctld` is inactive, `scontrol` is unavailable,
    or `scontrol reconfigure` failed after the files were restored.

??? note "Resolution"

    1. Treat the on-disk configuration as already changed.
    2. Run `systemctl status munge slurmdbd slurmctld --no-pager` on the
       controller.
    3. Review `journalctl -u slurmctld -n 50 --no-pager` and correct the
       restored configuration.
    4. Confirm that `scontrol` is installed and in `PATH`.
    5. Start the required services and run `scontrol reconfigure` again.

## Source ISO or checksum validation fails

???+ note "Symptom"

    The installation workflow reports that `source_iso_path` does not exist or
    that `source_iso_checksum` does not match.

??? note "Resolution"

    1. Confirm the source ISO is readable from the OIM.
    2. Calculate its SHA-256 checksum and compare it with
       `source_iso_checksum`.
    3. Replace a partial or corrupted ISO before rerunning the workflow.

## Custom ISO NFS path cannot be resolved

???+ note "Symptom"

    ISO build, Kickstart generation, or deployment cannot resolve
    `custom_iso_path` to a local NFS mount.

??? note "Resolution"

    1. Use `server:/export/path/file.iso` format.
    2. Confirm the export is mountable from the OIM.
    3. Confirm the path below the mounted export matches the path in
       `custom_iso_path`.
    4. Confirm the target iDRAC can reach the same NFS server and export.

## SSH public-key validation fails

???+ note "Symptom"

    The installation validator cannot find `ssh_public_key_path`.

??? note "Resolution"

    Create the default key or configure an existing public key:

    ```bash title="Run on: OIM"
    ssh-keygen -t rsa -b 4096 -N "" -f /root/.ssh/id_rsa
    ```

    The default public-key path is `/root/.ssh/id_rsa.pub`.

## Existing node blocks reinstallation

???+ note "Symptom"

    The target administrative IP already accepts SSH and the workflow stops.

??? note "Resolution"

    Keep `force_reinstall: false` when the node must be protected. Set it to
    `true` only after confirming that the selected node and `install_disk` may
    be reimaged.

## Installation does not become reachable

???+ note "Symptom"

    iDRAC starts the installation but SSH verification times out.

??? note "Resolution"

    1. Check the iDRAC virtual console and one-time virtual-CD boot status.
    2. Verify `target_admin_ip`, `network_device`, netmask, gateway, and DNS.
    3. Confirm the injected root public key is correct.
    4. Increase `ssh_verify_retries` or `ssh_verify_delay` when installation
       needs more time.

## Related documentation

- [Utils overview](../../HowTo/utils/index.md)
- [Install an OS unattended](../../HowTo/utils/install_os_unattended.md)
- [Back up OIM logs](../../HowTo/utils/backup_oim_logs.md)
- [Slurm configuration utilities](../../HowTo/utils/backup_slurm_config.md)
- [Slurm config utility configuration](../../Reference/Configuration/slurm_config_util_config.md)
- [Clean up Utils](../../HowTo/utils/cleanup_utils.md)
- [Collect cluster logs](../../Operations/collect_cluster_logs.md)
- [Log management](../../Operations/log_management.md)
