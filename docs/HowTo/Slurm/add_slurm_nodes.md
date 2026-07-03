
# Add Slurm Nodes


Dynamically add new compute nodes to a running Slurm cluster without
disrupting existing workloads.

## Overview


Omnia supports dynamic node addition to expand a running Slurm cluster. The
process involves:

1. Provisioning the new server(s) using the standard Omnia workflow.
2. Adding the new node(s) to the mapping file.
3. Running the add-node playbook to configure Slurm on the new nodes and
   update the controller's `slurm.conf`.


## Prerequisites


- A working Slurm cluster deployed via [Setup Slurm](setup_slurm.md).
- New server(s) are physically racked, cabled, and have BMC connectivity.
- The new server(s) have been provisioned and are reachable on the admin
  network.
- New node entries have been added to the `pxe_mapping_file.csv`.


## Procedure


1. **Update the mapping file** with new node entries:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/pxe_mapping_file.csv
   ```


   Add new rows for each new compute node:

   ```text title="File: /opt/omnia/input/project_default/pxe_mapping_file.csv"
   slurm_node,slurm_cluster,NEWSVCTG1,,,aa:bb:cc:dd:ee:10,10.5.0.110,aa:bb:cc:dd:ff:10,10.3.0.110
   slurm_node,slurm_cluster,NEWSVCTG2,,,aa:bb:cc:dd:ee:11,10.5.0.111,aa:bb:cc:dd:ff:11,10.3.0.111
   ```


2. **Provision the new nodes** if not already provisioned:

   ```bash title="Run on: omnia_core container"
   cd /omnia/discovery
   ansible-playbook discovery.yml --ask-vault-pass
   ```


3. **Run the add-node playbook**:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook omnia.yml --ask-vault-pass --limit "new_nodes"
   ```


   !!! note

       If a dedicated `add_node.yml` playbook is available in your Omnia
       version, use it instead:

       ```bash title="Run on: omnia_core container"
       ansible-playbook utils/add_node.yml --ask-vault-pass \
         -e "target_nodes=10.5.0.110,10.5.0.111"
       ```


4. **Update the Slurm configuration** on the control node to include the new
   nodes:

   ```bash title="Run on: Slurm control node"
   # Reconfigure Slurm to pick up new nodes
   scontrol reconfigure
   ```



## Verification


1. **Check that new nodes appear in the cluster**:

   ```bash title="Run on: Slurm control node"
   sinfo
   ```


   New nodes should appear in the `normal` partition with `idle` state.

2. **Run a test job on the new nodes**:

   ```bash title="Run on: Slurm control node"
   srun -w <new-node-hostname> hostname
   ```


3. **Verify Munge authentication** on the new nodes:

   ```bash title="Run on: Slurm control node"
   munge -n | ssh <new-node-ip> unmunge
   ```


4. **Check slurmd is running** on the new nodes:

   ```bash title="Run on: new compute node"
   systemctl status slurmd
   ```



## Next Steps


- [Slurm With Gpu](slurm_with_gpu.md) -- Configure GPU support on the new nodes if they have
  GPUs.
- [Configure Nfs](../Storage/configure_nfs.md) -- Mount shared storage on new nodes.
- [Deploy External LDAP](../Authentication/deploy_external_ldap.md) -- Ensure LDAP clients are
  configured on new nodes.


## Troubleshooting


**New nodes show "down" in sinfo**
   - Verify `slurmd` is running:

     ```bash title="Run on: new compute node"
     systemctl status slurmd
     journalctl -u slurmd --no-pager -n 20
     ```


   - Check that `slurm.conf` on the new node matches the control node's
     version:

     ```bash title="Run on: new compute node"
     grep "SlurmctldHost" /etc/slurm/slurm.conf
     ```


   - Resume the node from the controller:

     ```bash title="Run on: Slurm control node"
     scontrol update nodename=<node> state=resume reason="added"
     ```


**Munge key mismatch**
   Re-distribute the Munge key from the control node:

   ```bash title="Run on: omnia_core container"
   ansible new_nodes -m copy -a "src=/etc/munge/munge.key dest=/etc/munge/munge.key owner=munge group=munge mode=0400"
   ansible new_nodes -m service -a "name=munge state=restarted"
   ```


**New nodes not in Ansible inventory**
   Re-run discovery or manually add the nodes to the Ansible inventory:

   ```bash title="Run on: omnia_core container"
   ochami node list
   ```
