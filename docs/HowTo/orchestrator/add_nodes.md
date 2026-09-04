# Add Slurm Nodes

Add new compute nodes to a running Slurm cluster. Omnia automatically
updates the Slurm configuration and integrates new nodes.

## Overview

Omnia supports dynamic addition of compute nodes to an existing Slurm
cluster. The process involves updating the PXE mapping file, running
the orchestrator provision tag, and PXE booting the new nodes. Omnia handles Slurm
configuration updates automatically.

!!! note

    Only `slurm_node` additions are supported. Adding new controller or
    login nodes requires a full redeployment.

## Prerequisites

- The [Deploy Slurm](deploy_slurm.md) procedure is complete
- The [Deploy OpenCHAMI](deploy_openchami.md) procedure is complete
- New server(s) are physically racked, cabled, and have BMC connectivity
- New nodes have been discovered via [Discover Nodes](../discovery/discover_nodes.md)

## Procedure

1. **Add new entries to the PXE mapping file**:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/discovery/output/project_default/discovery/bmc_pxe_mapping_file.csv
    ```

    Add new rows with the `slurm_node_x86_64` or `slurm_node_aarch64`
    functional group:

    ```text title="File: bmc_pxe_mapping_file.csv"
    slurm_node_x86_64,slurm_cluster,NEWSVCTG1,,,aa:bb:cc:dd:ee:10,10.5.0.110,aa:bb:cc:dd:ff:10,10.3.0.110,,
    slurm_node_x86_64,slurm_cluster,NEWSVCTG2,,,aa:bb:cc:dd:ee:11,10.5.0.111,aa:bb:cc:dd:ff:11,10.3.0.111,,
    ```

2. **Run the orchestrator provision tag**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --run orchestrator --tags provision
    ```

3. **PXE boot the newly added nodes**.

Omnia automatically updates the Slurm configuration and integrates the
new nodes into the cluster during provisioning.

## Verification

1. **Check that new nodes appear in the cluster**:

    ```bash title="Run on: Slurm controller node"
    sinfo
    ```

    New nodes should appear in the `normal`(default) partition with `idle` state.

2. **Run a test job on the new nodes**:

    ```bash title="Run on: Slurm controller node"
    srun -w <new-node-hostname> hostname
    ```

3. **Check slurmd is running** on the new nodes:

    ```bash title="Run on: new compute node"
    systemctl status slurmd
    ```

## Next Steps

- [Slurm with GPU](../Configure/slurm_with_gpu.md) -- Verify GPU support on the new nodes

## Troubleshooting

**New nodes show DOWN after adding**

   Verify `slurmd` is running and cloud-init completed on the new node:

   ```bash title="Run on: new compute node"
   systemctl status slurmd
   journalctl -u slurmd --no-pager -n 20
   cat /var/log/cloud-init-output.log | tail -20
   ```

   Resume the node from the controller:

   ```bash title="Run on: Slurm controller node"
   scontrol update nodename=<node> state=resume reason="added"
   ```

For the complete list, see [Slurm Issues](../../Troubleshooting/orchestrator.md).


















