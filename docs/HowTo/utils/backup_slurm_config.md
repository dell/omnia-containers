# Slurm Configuration Utilities

Back up, clean up, and rollback Slurm configuration files using Omnia
utility playbooks.

## Overview

Omnia provides the `slurm_config_util.yml` utility playbook with three
operations for managing Slurm configuration:

- **Backup** -- Create timestamped backups of all Slurm configuration files
- **Cleanup** -- Remove existing Slurm configuration from the live cluster directory
- **Rollback** -- Restore Slurm configuration from a previous backup

## Prerequisites

- A working Slurm cluster deployed via [Set Up Slurm](../orchestrator/deploy_slurm.md).

## Procedure

### Backup

Create a timestamped backup of all Slurm configuration files:

```bash title="Run on: OIM host"
cd /opt/omnia
ansible-playbook /opt/omnia/utils/slurm_config_util.yml --tags config_backup
```

Backups are stored at
`<client_share_path>/slurm_backups/<backup_name>/<controller_node>/`.

### Cleanup

Remove existing Slurm configuration files from the live cluster
directory:

```bash title="Run on: OIM host"
cd /opt/omnia
ansible-playbook /opt/omnia/utils/slurm_config_util.yml --tags slurm_cleanup
```

!!! warning
    Take a configuration backup before running cleanup. This action
    deletes `<client_share_path>/slurm/` and cannot be undone.

### Rollback

Restore Slurm configuration from a previous backup:

```bash title="Run on: OIM host"
cd /opt/omnia
ansible-playbook /opt/omnia/utils/slurm_config_util.yml --tags config_rollback
```

The utility performs the following steps:

1. Lists available backups
2. Validates the selected backup
3. Optionally creates a safety backup of the current configuration
4. Restores files from the selected backup
5. Fixes file permissions
6. Restarts Slurm services

## Verification

1. **Verify the current configuration is valid** after a rollback:

    ```bash title="Run on: Slurm controller node"
    sinfo
    scontrol ping
    ```

2. **Verify all nodes are healthy**:

    ```bash title="Run on: Slurm controller node"
    scontrol show nodes | grep State
    ```

## Next Steps

- [Add Slurm Nodes](../orchestrator/add_nodes.md) -- Back up before adding nodes
- [Remove Slurm Nodes](../orchestrator/remove_nodes.md) -- Back up before removing nodes

## Troubleshooting

**`slurmctld` fails to start after config rollback**
   The backup may reference nodes that no longer exist. Run cleanup and redeploy:

   ```bash title="Run on: OIM host container"
   ansible-playbook /opt/omnia/utils/slurm_config_util.yml --tags slurm_cleanup
   ansible-playbook provision.yml
   ```

For the complete list, see [Slurm Issues](../../Troubleshooting/orchestrator.md).


















