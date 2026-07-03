# Step 5: Execute Build Pipeline

Update the `catalog_rhel.json` file and execute the Omnia BuildStreaM build pipeline through GitLab. This procedure covers catalog modifications, pipeline triggering (automatic and manual), and verification of pipeline status and job execution.

The BuildStream build pipeline automates the creation of diskless images based on catalog specifications. The pipeline consists of four sequential stages:

* **parse-catalog**: Parses and validates the catalog file for build requirements
* **generate-input-files**: Generates input files and configuration data for image building
* **create-local-repository**: Creates and configures the local repository for build artifacts
* **build-image**: Builds the diskless images based on catalog specifications

The build pipeline is automatically triggered when you update the `catalog_rhel.json` file in the GitLab repository, or can be manually initiated through the GitLab interface.

!!! note

    Do not cancel a running GitLab pipeline or stage. Cancellation prevents some pipeline steps from executing, which leaves the BuildStreaM job in an intermediate, inconsistent state. Note that backend BuildStreaM tasks already in progress will continue running to completion regardless of the cancellation.

## Prerequisites

Before updating catalogs and checking pipelines:

* Deploy and Configure BuildStreaM Container on OIM Node (see [Step 3: Prepare the OIM](../../GetStarted/buildstream_deployment.md#step-3-prepare-the-omnia-infrastructure-manager))
* GitLab deployment for BuildStreaM is completed (see [Deploy GitLab](deploy_gitlab.md))
* Confirm that you can access GitLab project repository

## Procedure

1. Go to the GitLab project URL:

    ```bash title="GitLab project URL"
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

2. Go to **Code** → **Repository**.

3. Locate the catalog file `catalog_rhel.json`.

4. Modify the `catalog_rhel.json` file to define your build requirements.

    !!! note

        Ensure that the catalog file is updated with valid functional group names, architecture types, operating system types and versions, and package types. The pipeline fails if invalid details are provided.

        The following are the supported values:

        - **Functional group names**: For supported functional group names, see the functional groups section.
        - **Architecture type**: `x86_64` and `aarch64`.
        - **OS type**: `RHEL`, see supported OS types and versions.
        - **OS version**: `10.0`, see supported OS types and versions.
        - **Package types**: `rpm`, `rpm_repo`, `image`, `iso`, `tarball`, `pip_module`, `git`, `manifest`.

5. Trigger the build pipeline by committing and pushing the catalog changes. The pipeline triggers automatically when catalog changes are committed. This pipeline can also be executed manually through the GitLab UI. See [Execute Build Pipeline Manually](#execute-build-pipeline-manually) for detailed instructions.

    ![BuildStreaM Build Trigger](../../assets/images/buildstream-build-trigger.png)

6. Monitor the pipeline progress to ensure it completes successfully. See [Monitor Build Pipeline Progress](#monitor-build-pipeline-progress) for detailed instructions.

    ![BuildStreaM Pipeline Execution](../../assets/images/buildstream-buid-success.png)

!!! note

    * Currently, BuildStreaM supports only one catalog file and one pipeline trigger. BuildStreaM pipeline behavior is controlled by the GitLab CI/CD configuration in your environment.
    * Each pipeline processes the catalog changes independently and builds the specified images based on the catalog requirements. Once a pipeline execution is complete, users can modify the catalog and re-trigger the pipeline as needed. However, multiple pipeline triggers cannot be executed simultaneously.

### Execute Build Pipeline Manually

To manually execute the build pipeline, follow these steps:

**Procedure**

1. Review the pipeline logs in GitLab to check the current status.

    a. Navigate to **Build** → **Pipelines**.

    b. Click on the desired pipeline.

    c. Click on the stage to view logs.

2. Update the input configuration files in the GitLab repository.

    a. Navigate to the `input/` folder in the GitLab repository.

    b. Edit the relevant configuration file.

    c. Commit and push the changes.

3. Manually trigger the pipeline with the updated parameters.

    a. Navigate to **Build** → **Pipelines**.

    b. Click **New Pipeline**.

    c. In the **Run new pipeline** dialog box, enter the variable name as **PIPELINE_TYPE** and enter the value as **build**.

    ![GitLab Build Manual Configuration](../../assets/images/gitlab-build-manual-config.png)

    d. Click **Run Pipeline** to execute the build pipeline.

4. Monitor the pipeline progress to ensure it completes successfully. See [Monitor Build Pipeline Progress](#monitor-build-pipeline-progress) for detailed instructions.

For troubleshooting common pipeline issues, see the troubleshooting section.

### Monitor Build Pipeline Progress

Monitor the build pipeline progress through the GitLab web interface to track stage execution and identify any issues.

1. Navigate to **Build** → **Pipeline**.

2. Click on the running pipeline to view details.

3. Monitor each stage as it progresses:

    - **parse-catalog**: Parses and validates the catalog file for build requirements
    - **create-local-repository**: Creates and configures the local repository for build artifacts
    - **generate-input-files**: Generates input files and configuration data for image building
    - **build-image**: Builds the diskless images based on catalog specifications

4. Review the stage status indicators:

    - **Green checkmark**: Stage completed successfully
    - **Red X**: Stage failed (click for error details)
    - **Blue circle**: Stage currently running

5. If any stage fails, review the error logs by clicking on the failed job.

!!! note

    The build pipeline uses the catalog file to determine which images to build based on functional group assignments.

## Verification

After the pipeline is completed, you can check the overall pipeline status and job execution.

1. Navigate to **Build** → **Pipelines**

2. Review the job list and status.

3. Click on individual jobs to view:

    - Execution logs
    - Resource usage
    - Error messages (if any)

## Next Steps

After successful execution of the build pipeline, proceed with deploying the images to cluster nodes. See Step 6 below for detailed instructions on executing the deploy pipeline.

---

## Step 6: Execute Deploy Pipeline

Execute the BuildStream deploy pipeline to deploy images to cluster nodes. This procedure covers the three deploy stages: deploy, restart, and validate.

The BuildStream deploy pipeline automates the deployment of built images to target cluster nodes. The pipeline consists of three sequential stages:

* **deploy**: Deploys the built images to the target nodes
* **restart**: PXE-boots the target nodes to load the deployed images
* **validate**: Executes Molecule-based infrastructure tests to verify cluster deployment, network connectivity, and service health

The deploy pipeline is automatically triggered when you update the PXE mapping file (`pxe_mapping_file.csv`) in the GitLab repository, or can be manually initiated through the GitLab interface.

!!! note

    Do not cancel a running GitLab pipeline or stage. Cancellation prevents some pipeline steps from executing, which leaves the BuildStreaM job in an intermediate, inconsistent state. Note that backend BuildStreaM tasks already in progress will continue running to completion regardless of the cancellation.

### Prerequisites

Before executing the deploy pipeline, ensure the following:

* Build pipeline has completed successfully and images are available
* Target nodes are powered on and accessible via BMC
* PXE mapping file (`pxe_mapping_file.csv`) is correctly configured with target node information
* PXE mapping file is present in the GitLab repository `input/` folder for automatic triggering

### Procedure

1. Navigate to the GitLab project URL:

    ```bash title="GitLab project URL"
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

2. Trigger the deploy pipeline by updating the `pxe_mapping_file.csv` file in the GitLab repository and committing the changes. This pipeline can also be executed manually through the GitLab UI. See [Execute Deploy Pipeline Manually](#execute-deploy-pipeline-manually) for detailed instructions.

    ![GitLab Deploy Trigger](../../assets/images/gitlab-deploy-trigger.png)

3. In the deploy pipeline, select the image from the `select_image` stage and click the "Play" button.

    ![GitLab Deploy Select Image](../../assets/images/gitlab-deploy-select-image.png)

4. To deploy the image, click the "Play" button in the `deploy` stage.

    ![GitLab Deploy Play](../../assets/images/gitlab-deploy-play.png)

5. Monitor the pipeline progress to ensure it completes successfully. See [Monitor Deploy Pipeline Progress](#monitor-deploy-pipeline-progress) for detailed instructions.

### Execute Deploy Pipeline Manually

To manually execute the deploy pipeline, follow these steps:

**Procedure**

1. Review the pipeline logs in GitLab to check the current status.

    a. Navigate to **Deploy** → **Pipelines**.

    b. Click on the desired pipeline.

    c. Click on the stage to view logs.

2. Update the input parameters in the GitLab repository.

    a. Navigate to the `input/` folder in the GitLab repository.

    b. Edit the relevant configuration file.

    c. Commit and push the changes.

3. Manually trigger the pipeline with the updated parameters.

    a. Navigate to **Deploy** → **Pipelines**.

    b. Click **New Pipeline**.

    c. In the **Run new pipeline** dialog box, enter the variable name as **PIPELINE_TYPE** and enter the value as **deploy**.

    ![GitLab Deploy Manual Configuration](../../assets/images/gitlab-deploy-manual-config.png)

    d. Click **Run Pipeline** to execute the deploy pipeline.

4. Monitor the pipeline progress to ensure it completes successfully. See [Monitor Deploy Pipeline Progress](#monitor-deploy-pipeline-progress) for detailed instructions.

    ![GitLab Deploy Success](../../assets/images/gitlab-deploy-success.png)

!!! note

    When using manual retry, ensure that only the necessary parameters are updated. Unnecessary changes may cause additional pipeline failures.

For information on handling deploy failures with partial node failures, see [Handling Deploy Failures](#handling-deploy-failures-during-restart-stage-pxe-boot).

### Monitor Deploy Pipeline Progress

1. Monitor the deploy pipeline progress through the GitLab web interface:

    a. Click on the running pipeline to view details.

    b. Monitor each stage as it progresses:

        - **deploy**: Deploys images to target nodes based on catalog specifications
        - **restart**: PXE-boots the nodes to load the deployed images.
        - **validate**: Executes Molecule-based infrastructure tests to verify cluster deployment, network connectivity, and service health

2. Review the stage status indicators:

    - **Green checkmark**: Stage completed successfully
    - **Red X**: Stage failed (click for error details)
    - **Blue circle**: Stage currently running

3. If any stage fails, review the error logs by clicking on the failed job.

!!! note

    The deploy pipeline uses the PXE mapping file to determine which nodes receive which images based on functional group assignments.

### Verification

After the deploy pipeline completes, verify the deployment:

1. Check the overall pipeline status in GitLab to ensure all stages passed.

2. Verify that the target nodes have restarted and are accessible.

3. Log in to a sample of deployed nodes to verify the correct image is loaded.

4. Check the BuildStreaM API for deployment status and image group information.

### Handling Deploy Failures During Restart Stage (PXE Boot)

In the deploy pipeline, when the restart stage encounters partial failures (some nodes PXE booted successfully while others fail), BuildStream provides a `failed_nodes.json` mechanism to enable efficient retry operations.

`failed_nodes.json` is a structured JSON file that tracks which nodes failed to PXE boot during the restart stage. This file enables you to:

* Track failed nodes with detailed error messages
* Manually fix the failed nodes and update their entries as successful.
* Retry only the failed nodes instead of the entire inventory
* Maintain accurate state across pipeline runs

**Sample failed_nodes.json Schema**

```json title="failed_nodes.json"
{
  "job_id": "018f3c4b-7b5b-7a9d-b6c4-9f3b4f9b2c10",
  "stage_name": "restart",
  "timestamp": "2026-04-10T16:32:15Z",
  "total_nodes": 5,
  "failure_count": 2,
  "failed_nodes": [
    {
      "bmc_ip": "172.17.107.44",
      "hostname": "slurm-node2",
      "service_tag": "79WWJ93",
      "status": "failed",
      "message": "Failed. iDRAC is not ready. Retry again after iDRAC is ready"
    },
    {
      "bmc_ip": "172.17.107.45",
      "hostname": "slurm-node3",
      "service_tag": "79WWJ94",
      "status": "failed",
      "message": "iDRAC is unreachable. pxe boot might be set. Please check the host reboot status manually"
    }
  ]
}
```

**Procedure**

1. During the first run, the restart stage attempts to PXE boot all nodes automatically.

2. If all nodes succeed, the stage is marked successful and proceeds to the validation stage.

3. In case of partial failure, only failed nodes are recorded in `failed_nodes.json` in a directory called `miscellaneous` in GitLab. The file contains failed node details along with corresponding error messages.

    ![failed_nodes.json example](../../assets/images/buildstream_restart_failed_nodes_json.png)

4. Analyze failures and perform corrective actions:

    * Check iDRAC readiness
    * Verify BMC network connectivity
    * Validate PXE boot configuration

5. After resolving issues, retry the restart stage for failed nodes.

6. If automated retry is not feasible (for example, VM or manual dependency), manually PXE boot the affected nodes.

7. After manual boot of the nodes, update the node status as `success` in `failed_nodes.json` and click the **Retry donwstream pipline** icon to retry the failed pipeline. Updated nodes are excluded from further PXE attempts by the pipeline/API and are automatically added to the booted nodes list.

    ![updated failed_nodes.json example](../../assets/images/buildstream_restart_updated_failed_nodes_json.png)

The restart stage completes successfully only when all nodes are successful (automated or manual). Upon completion, the workflow proceeds to the validation stage.

![restart stage success example](../../assets/images/buildstream_restart_stage_success.png)

8. To view detailed logs for a validate stage, click on the Validate stage in the pipeline. This will display the execution logs, including whether the stage has passed or failed. Within these logs, the corresponding log file path is provided. Users can navigate to this path on the OIM to access the detailed test report of the cluster deployment. If any failure occurs, the logs will include a comprehensive report for further analysis
