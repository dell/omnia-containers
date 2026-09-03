# Add Nodes to Cluster

Omnia supports addition of Slurm compute nodes to an existing cluster using Build Stream. Add new nodes to an existing cluster and deploy images to them without affecting previously provisioned nodes.

!!! warning

    Addition of a new `slurm_control_node` is not supported.

!!! warning

    Node removal is not supported. When you remove a node from the `pxe_mapping_file.csv`, the BMC IP is not cleaned up from the Build Stream `restart_state.json` file. If you later re-add the same node with a different hostname, the node will not be PXE booted and will retain its previous hostname. This can cause the node to enter an unknown state in the Slurm controller.

## Overview

When you need to expand your cluster by adding nodes, use the PXE mapping file and deploy pipeline. This approach ensures that previously provisioned nodes remain unaffected during the deployment process.

## Prerequisites

- Existing cluster with deployed nodes
- New nodes are powered on and accessible via BMC
- Build pipeline has completed successfully and images are available

## Procedure

### Add Nodes to Cluster

1. Update the `pxe_mapping_file.csv` file in GitLab with the details of the new nodes and commit the changes.

    ```csv title="pxe_mapping_file.csv"
    bmc_ip,hostname,service_tag,role
    172.17.107.50,new-node1,79WWJ95,compute
    172.17.107.51,new-node2,79WWJ96,compute
    ```

This automatically triggers the deploy pipeline. The system PXE boots only the newly added nodes, without impacting previously successful nodes.

For more details on triggering or monitoring the pipeline, see [Execute Deploy Pipeline](execute_deploy_pipeline.md).

## Verification

After the deploy pipeline completes:

1. For added nodes: Verify that the new nodes have restarted and are accessible.
2. For added nodes: Log in to the new nodes to verify the correct image is loaded.
3. Check the Build Stream API for deployment status and confirm the node inventory matches your expectations.

## Next Steps

- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups

## Troubleshooting

- For additional issues, see [Build Stream Troubleshooting](../../Troubleshooting/build_stream.md).



















