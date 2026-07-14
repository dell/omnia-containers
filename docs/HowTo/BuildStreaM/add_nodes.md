# Add or Remove Nodes to Cluster

Omnia supports addition and removal of Slurm compute nodes from an existing cluster using BuildStreaM. Add new nodes to an existing cluster and deploy images to them without affecting previously provisioned nodes. Remove nodes from the cluster by updating the PXE mapping file.

!!! warning

    Addition of a new `slurm_control_node` is not supported.

## Overview

When you need to expand or modify your cluster by adding or removing nodes, use the PXE mapping file and deploy pipeline. This approach ensures that previously provisioned nodes remain unaffected during the deployment process.

## Prerequisites

- Existing cluster with deployed nodes
- For adding nodes: New nodes are powered on and accessible via BMC
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

### Remove Nodes from Cluster

To remove nodes from the cluster:

1. Update the `pxe_mapping_file.csv` file in GitLab by removing the entries for the nodes you want to remove.

2. Commit the changes to trigger the deploy pipeline. For more details, see [Execute Deploy Pipeline](execute_deploy_pipeline.md).

The removed nodes are removed from the cluster, but existing deployments on those nodes remain unchanged.

## Verification

After the deploy pipeline completes:

1. For added nodes: Verify that the new nodes have restarted and are accessible.
2. For added nodes: Log in to the new nodes to verify the correct image is loaded.
3. Check the BuildStreaM API for deployment status and confirm the node inventory matches your expectations.

## Next Steps

- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups

## Troubleshooting

- For additional issues, see [BuildStreaM Troubleshooting](../../Troubleshooting/buildstream.md).
