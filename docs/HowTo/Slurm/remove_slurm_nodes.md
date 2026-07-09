# Remove Slurm Nodes

Remove compute nodes from a running Slurm cluster. Omnia handles Slurm
configuration updates and provides job protection for busy nodes.

## Overview

Omnia supports dynamic removal of compute nodes from an existing Slurm
cluster. The process involves removing entries from the PXE mapping file
and running `provision.yml`. Omnia automatically updates the Slurm
configuration.

If removed nodes have active running jobs, Omnia prompts you to either
abort (remove only idle nodes) or force-remove (cancel all jobs on
affected nodes).

!!! note
    Only `slurm_node` removals are supported. Removing controller or
    login nodes requires a full redeployment.

## Prerequisites

- A working Slurm cluster deployed via [Set Up Slurm](setup_slurm.md).

!!! tip
    Take a configuration backup before removing nodes. See
    [Config Backup](slurm_config_backup.md).

## Procedure

1. **Remove node entries from the PXE mapping file**:

    ```bash title="Run on: omnia_core"
    vi /opt/omnia/input/project_default/pxe_mapping_file.csv
    ```

    Remove the rows for the nodes you want to decommission.

2. **Run provision.yml**:

    ```bash title="Run on: omnia_core"
    cd /opt/omnia
    ansible-playbook provision/provision.yml
    ```

    If the removed nodes have active running jobs, Omnia prompts:

    - **Abort** -- Removes only idle nodes, keeps busy nodes in the cluster
    - **Force-remove** -- Cancels all jobs on affected nodes and removes them

Omnia automatically updates `slurm.conf` and reconfigures the Slurm
controller.

## Verification

1. **Confirm the node is no longer in the cluster**:

    ```bash title="Run on: Slurm controller node"
    sinfo
    ```

    The removed node should no longer appear.

2. **Run a test job** to confirm remaining nodes are functional:

    ```bash title="Run on: Slurm controller node"
    srun -N 1 hostname
    ```

3. **Verify no orphaned jobs** reference the removed node:

    ```bash title="Run on: Slurm controller node"
    squeue -t all
    ```

## Next Steps

- [Add Slurm Nodes](add_slurm_nodes.md) -- Add replacement nodes if needed
- [Config Backup](slurm_config_backup.md) -- Back up the updated configuration

## Troubleshooting

For Slurm troubleshooting, see
[Slurm Issues](../../Troubleshooting/slurm.md).
