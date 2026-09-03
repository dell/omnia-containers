# Remove Slurm Nodes

Remove compute nodes from a running Slurm cluster. Omnia handles Slurm
configuration updates and provides job protection for busy nodes.

## Overview

Omnia supports dynamic removal of compute nodes from an existing Slurm
cluster. The process involves removing entries from the PXE mapping file
and running the orchestrator provision tag. Omnia automatically updates the Slurm
configuration.

If removed nodes have active running jobs, Omnia prompts you to either
abort (remove only idle nodes) or force-remove (cancel all jobs on
affected nodes).

!!! note

    Only `slurm_node` removals are supported. Removing controller or
    login nodes requires a full redeployment.

## Prerequisites

- The [Deploy Slurm](deploy_slurm.md) procedure is complete

!!! tip

    Take a configuration backup before removing nodes.

## Procedure

1. **Remove node entries from the PXE mapping file**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/discovery/output/project_default/discovery/bmc_pxe_mapping_file.csv
    ```

    Remove the rows for the nodes you want to decommission.

2. **Run the orchestrator provision tag**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run orchestrator --tags provision
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

- [Add Slurm Nodes](add_nodes.md) -- Add replacement nodes if needed

## Troubleshooting

**Node still appears in sinfo after removal**

   Verify that the provision tag completed and check the controller logs:

   ```bash title="Run on: Slurm controller node"
   journalctl -u slurmctld --no-pager -n 20
   ```

   Check for failed jobs on the removed node and resubmit as needed:

   ```bash title="Run on: Slurm controller node"
   sacct --starttime=today --state=FAILED,NODE_FAIL
   ```

For the complete list, see [Slurm Issues](../../Troubleshooting/orchestrator.md).


















