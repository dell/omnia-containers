# Add Slurm Nodes

Add new compute nodes to a running Slurm cluster. Omnia automatically
updates the Slurm configuration and integrates new nodes.

## Overview

Omnia supports dynamic addition of compute nodes to an existing Slurm
cluster. The process involves updating the PXE mapping file, running
`provision.yml`, and PXE booting the new nodes. Omnia handles Slurm
configuration updates automatically.

!!! note
    Only `slurm_node` additions are supported. Adding new controller or
    login nodes requires a full redeployment.

## Prerequisites

- A working Slurm cluster deployed via [Set Up Slurm](setup_slurm.md).
- New server(s) are physically racked, cabled, and have BMC connectivity.

## Procedure

1. **Add new entries to the PXE mapping file**:

    ```bash title="Run on: omnia_core"
    vi /opt/omnia/input/project_default/pxe_mapping_file.csv
    ```

    Add new rows with the `slurm_node_x86_64` or `slurm_node_aarch64`
    functional group:

    ```text title="File: /opt/omnia/input/project_default/pxe_mapping_file.csv"
    slurm_node_x86_64,slurm_cluster,NEWSVCTG1,,,aa:bb:cc:dd:ee:10,10.5.0.110,aa:bb:cc:dd:ff:10,10.3.0.110,,
    slurm_node_x86_64,slurm_cluster,NEWSVCTG2,,,aa:bb:cc:dd:ee:11,10.5.0.111,aa:bb:cc:dd:ff:11,10.3.0.111,,
    ```

2. **Run provision.yml**:

    ```bash title="Run on: omnia_core"
    cd /opt/omnia
    ansible-playbook provision/provision.yml
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

- [Slurm with GPU](slurm_with_gpu.md) -- Verify GPU support on the new nodes
- [Config Backup](slurm_config_backup.md) -- Back up the updated configuration

## Troubleshooting

For Slurm troubleshooting, see
[Slurm Issues](../../Troubleshooting/slurm.md).
