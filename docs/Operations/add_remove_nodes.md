
# Add and Remove Nodes

Omnia supports addition and removal of Slurm compute nodes from an existing cluster. You can add or remove nodes using either OME-based BMC discovery or mapping file discovery.

!!! warning

    Addition of a new `slurm_control_node` is not supported.

## Adding Slurm nodes

### Prerequisites

- The Slurm cluster is already operational (`slurmctld` is running on the control node).
- Network connectivity between the OIM and the new nodes is verified.
- For OME-based discovery: the new node is added and configured in OpenManage Enterprise (OME).

### Using mapping file discovery

1. Update the PXE mapping file with new Slurm node entries. Add entries for new nodes with the appropriate functional group (e.g., `slurm_node_x86_64`).

    !!! warning

        Do not remove existing nodes from the mapping file when adding new entries.

2. Run the `provision.yml` playbook:

    ```bash title="Run on: omnia_core container"
    ssh omnia_core
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

3. PXE boot the newly added nodes.

4. To enable iDRAC telemetry collection on the new nodes, run the `telemetry.yml` playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/telemetry
    ansible-playbook telemetry.yml
    ```

    !!! note

        You do not need to run `telemetry.yml` if the service Kubernetes cluster nodes are configured to collect telemetry data only using LDMS. LDMS begins collection automatically after `provision.yml` is executed.

### Using OME-based BMC discovery

1. Ensure the new node is added and configured in OpenManage Enterprise (OME).

2. Run the `discovery.yml` playbook with the OME discovery mechanism:

    ```bash title="Run on: omnia_core container"
    ssh omnia_core
    cd /omnia/discovery
    ansible-playbook discovery.yml -e "discovery_mechanism=ome"
    ```

3. Update the PXE mapping file path in `provision_config.yml`.

4. Run the `provision.yml` playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

5. PXE boot the newly added nodes.

6. To enable iDRAC telemetry collection, run the `telemetry.yml` playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/telemetry
    ansible-playbook telemetry.yml
    ```

## Removing Slurm nodes

### Using mapping file discovery

1. Update the PXE mapping file. Remove or reassign nodes that should no longer be part of the Slurm cluster.

2. Run the `provision.yml` playbook:

    ```bash title="Run on: omnia_core container"
    ssh omnia_core
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

3. To stop iDRAC telemetry collection from the removed nodes, run the `telemetry.yml` playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/telemetry
    ansible-playbook telemetry.yml
    ```

    !!! note

        You do not need to run `telemetry.yml` to stop LDMS collection from removed nodes. LDMS stops collection automatically after `provision.yml` is executed.

### Using OME-based BMC discovery

1. Remove or reassign the node in OpenManage Enterprise (OME).

2. Run the `discovery.yml` playbook with the OME discovery mechanism:

    ```bash title="Run on: omnia_core container"
    ssh omnia_core
    cd /omnia/discovery
    ansible-playbook discovery.yml -e "discovery_mechanism=ome"
    ```

3. Update the PXE mapping file path in `provision_config.yml`.

4. Run the `provision.yml` playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

5. To stop iDRAC telemetry collection from the removed nodes, run the `telemetry.yml` playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/telemetry
    ansible-playbook telemetry.yml
    ```

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

    - [PXE Mapping File](../Reference/SampleFiles/pxe_mapping_file.md) -- PXE mapping CSV format and functional group reference.
    - [Provision Config](../Reference/Configuration/provision_config.md) -- Where the mapping file path is specified.
    - [Reprovision Cluster](reprovision_cluster.md) -- Re-image nodes instead of just adding/removing them.
