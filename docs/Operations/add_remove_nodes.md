
# Add and Remove Nodes


Omnia supports dynamically scaling your Slurm cluster by adding new compute
nodes or removing existing ones without disrupting running workloads. This
procedure uses the `add_node` and `remove_node` playbooks from inside the
`omnia_core` Podman container on the OIM.

## Adding compute nodes


Use this procedure when new servers have been racked, cabled, and discovered by
the OIM, and you want to include them in the Slurm cluster.

### Prerequisites


- The new nodes have been provisioned with an operating system via
  [Discover Nodes](../HowTo/Setup/discover_nodes.md) and [Pxe Boot Nodes](../HowTo/Setup/pxe_boot_nodes.md).
- Network connectivity between the OIM and the new nodes is verified (SSH
  access works).
- The Slurm cluster is already operational (`slurmctld` is running on the
  control node).

### Procedure


1. **Update the node mapping file.** Add the new node entries (MAC address,
   hostname, IP) to the mapping file used during initial deployment:

   ```text
   # /omnia/input/mapping_file.csv
   AA:BB:CC:DD:EE:F1,compute-05,10.5.0.105
   AA:BB:CC:DD:EE:F2,compute-06,10.5.0.106
   ```


2. **Access the omnia_core container** on the OIM:

   ```bash
   ssh omnia_core
   ```


3. **Run the add_node playbook:**

   ```bash
   cd /omnia
   ansible-playbook playbooks/add_node.yml
   ```


   The playbook will:

   - Install and configure `slurmd` on each new node.
   - Register the nodes with the Slurm controller.
   - Apply any GPU drivers or additional packages as specified in the
     configuration.

4. **Verify the new nodes** are visible to Slurm:

   ```bash
   sinfo
   ```


   Expected output shows the new nodes in an `idle` state:

   ```text
   PARTITION  AVAIL  TIMELIMIT  NODES  STATE  NODELIST
   normal*       up   infinite      6   idle  compute-[01-06]
   ```



## Removing compute nodes


Use this procedure when decommissioning servers or temporarily removing nodes
from the scheduling pool.

### Prerequisites


- You have `root` or `sudo` access to the OIM.
- No critical jobs are running on the nodes to be removed (or you are prepared
  to let them drain).

### Procedure


1. **Drain the node** to allow running jobs to complete and prevent new jobs
   from being scheduled:

   ```bash
   scontrol update NodeName=compute-05 State=DRAIN Reason="Decommissioning"
   ```


   Verify the node enters the `drained` state:

   ```bash
   sinfo -n compute-05
   ```


   ```text
   PARTITION  AVAIL  TIMELIMIT  NODES  STATE    NODELIST
   normal*       up   infinite      1  drained  compute-05
   ```


2. **Access the omnia_core container** on the OIM:

   ```bash
   ssh omnia_core
   ```


3. **Run the remove_node playbook:**

   ```bash
   cd /omnia
   ansible-playbook playbooks/remove_node.yml -e "target_nodes=compute-05"
   ```


4. **Update the mapping file.** Remove the decommissioned node entry from
   `/omnia/input/mapping_file.csv` to prevent it from being re-added in
   future operations.

5. **Verify the node has been removed:**

   ```bash
   sinfo
   ```


   The removed node should no longer appear in the node list.


## Verification


After adding or removing nodes, confirm the cluster state:

```bash title="Run on: Slurm control node"
# Check overall cluster health
sinfo

# Verify controller sees all expected nodes
scontrol show nodes | grep NodeName

# Submit a test job to verify scheduling
srun -N 1 hostname
```



!!! info

    - [Add Slurm Nodes](../HowTo/Slurm/add_slurm_nodes.md) -- Detailed how-to for adding Slurm nodes.
    - [Remove Slurm Nodes](../HowTo/Slurm/remove_slurm_nodes.md) -- Detailed how-to for removing Slurm nodes.
    - [Reprovision Cluster](reprovision_cluster.md) -- Re-image nodes instead of just adding/removing them.
