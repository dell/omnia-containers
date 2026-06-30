
# Remove Slurm Nodes


Safely remove compute nodes from a running Slurm cluster without disrupting
active workloads.

## Overview


Removing a node from a Slurm cluster involves:

1. Draining the node so no new jobs are scheduled on it.
2. Waiting for any running jobs to complete (or canceling them).
3. Removing the node from `slurm.conf` on the control node.
4. Stopping Slurm services on the target node.
5. Reconfiguring the Slurm controller.


## Prerequisites


- A working Slurm cluster deployed via [Setup Slurm](setup_slurm.md).
- `root` or `sudo` access to the Slurm control node and the target
  compute node(s).
- Identify which node(s) to remove (hostname and IP address).


## Procedure


1. **Drain the target node** to prevent new jobs from being scheduled:

   ```bash title="Run on: Slurm control node"
   scontrol update nodename=<node-to-remove> state=drain reason="Decommissioning"
   ```


2. **Verify the node is draining** and check for running jobs:

   ```bash title="Run on: Slurm control node"
   sinfo -n <node-to-remove>
   squeue -w <node-to-remove>
   ```


   Wait for all jobs on the node to complete. If immediate removal is needed,
   cancel running jobs:

   ```bash title="Run on: Slurm control node"
   # Cancel all jobs on the target node
   scancel -w <node-to-remove>
   ```


3. **Set the node to down**:

   ```bash title="Run on: Slurm control node"
   scontrol update nodename=<node-to-remove> state=down reason="Removed from cluster"
   ```


4. **Stop Slurm services on the target node**:

   ```bash title="Run on: node being removed"
   systemctl stop slurmd
   systemctl disable slurmd
   systemctl stop munge
   systemctl disable munge
   ```


5. **Remove the node from slurm.conf** on the control node:

   ```bash title="Run on: Slurm control node"
   vi /etc/slurm/slurm.conf
   ```


   Remove or comment out the `NodeName=` line for the target node. Also
   update the `PartitionName=` line to remove the node from the `Nodes=`
   list.

6. **Reconfigure Slurm** to apply changes:

   ```bash title="Run on: Slurm control node"
   scontrol reconfigure
   ```


7. **(Optional) Remove the node from the mapping file**:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/pxe_mapping_file.csv
   ```


   Remove or comment out the row for the decommissioned node.


## Verification


1. **Confirm the node is no longer in the cluster**:

   ```bash title="Run on: Slurm control node"
   sinfo
   scontrol show nodes
   ```


   The removed node should no longer appear.

2. **Run a test job** to confirm remaining nodes are functional:

   ```bash title="Run on: Slurm control node"
   srun -N 1 hostname
   ```


3. **Verify no orphaned jobs** reference the removed node:

   ```bash title="Run on: Slurm control node"
   squeue -t all
   ```



## Next Steps


- [Add Slurm Nodes](add_slurm_nodes.md) -- Add replacement nodes if needed.
- [Slurm Config Backup](slurm_config_backup.md) -- Back up the updated Slurm configuration.


## Troubleshooting


**Node still appears in sinfo after removal**
   Ensure you ran `scontrol reconfigure` after editing `slurm.conf`:

   ```bash title="Run on: Slurm control node"
   scontrol reconfigure
   ```


**Jobs were running on the removed node**
   If jobs were not properly drained, they may show as `FAILED` or
   `NODE_FAIL` in the accounting:

   ```bash title="Run on: Slurm control node"
   sacct --starttime=today --state=FAILED,NODE_FAIL
   ```


   Resubmit affected jobs as needed.

**slurm.conf syntax error after editing**
   Validate the configuration:

   ```bash title="Run on: Slurm control node"
   slurmd -C  # Show computed node configuration
   slurmctld -t  # Test configuration file syntax
   ```


**Cannot connect to the removed node to stop services**
   If the node is unreachable, the Slurm controller will time it out
   automatically. Simply remove it from `slurm.conf` and reconfigure.
