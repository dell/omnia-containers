# General Troubleshooting Steps

Common troubleshooting steps for upgrade and rollback operations.

## Check Playbook Logs

Increase Ansible verbosity for detailed output:

```bash title="Run on: omnia_core container"
cd /omnia/upgrade
ansible-playbook upgrade.yml -vvv
```

## Review State Files

All state files are stored in `/opt/omnia/.data/`:

```bash title="Run on: omnia_core container"
ls -la /opt/omnia/.data/
cat /opt/omnia/.data/upgrade_manifest.yml
cat /opt/omnia/.data/rollback_manifest.yml
cat /opt/omnia/.data/oim_metadata.yml
```

## Check Archived Manifests

Previous manifests are archived for history:

```bash title="Run on: omnia_core container"
ls /opt/omnia/.data/archive/
```

## Reset Upgrade/Rollback State

To completely reset the upgrade/rollback state and start fresh:

!!! caution

    This will discard all upgrade/rollback progress. Use only as a last resort.

```bash title="Run on: omnia_core container"
rm -f /opt/omnia/.data/upgrade_manifest.yml
rm -f /opt/omnia/.data/rollback_manifest.yml
rm -f /opt/omnia/.data/upgrade_in_progress.lock
rm -f /opt/omnia/.data/rollback_in_progress.lock
```

## Verify oim_metadata.yml

The `oim_metadata.yml` file is the source of truth for version information.
Ensure it contains the correct values:

```bash title="Run on: omnia_core container"
cat /opt/omnia/.data/oim_metadata.yml
```

Expected fields:

- `omnia_version` — Currently installed version.
- `previous_omnia_version` — Previous version.
- `upgrade_backup_dir` — Path to the backup directory.

!!! note

    `oim_metadata.yml` is read-only for upgrade and rollback flows. It is
    never modified by the playbooks. If the version information is incorrect,
    it must be fixed manually before rerunning.

!!! info "Related Documentation"

    - [Upgrade Omnia](../Operations/upgrade_omnia.md) — Upgrade procedure.
    - [Rollback Omnia](../Operations/rollback_omnia.md) — Rollback procedure.
