# Perform Cleanup Operations

BuildStream supports a maximum of 50 build images. When the build image count exceeds this limit, you must manually perform cleanup operations to remove old images before creating new ones.

!!! note

    Do not cancel a running GitLab pipeline or stage. Cancellation prevents some pipeline steps from executing, which leaves the BuildStreaM job in an intermediate, inconsistent state. Note that backend BuildStreaM tasks already in progress will continue running to completion regardless of the cancellation.

## Prerequisites

Before performing cleanup operations, ensure the following:

* You have administrative access to the OIM
* BuildStream API server is running
* PostgreSQL database is accessible

## Procedure

1. Navigate to the GitLab project URL:

    ```text
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

2. Navigate to **Build** → **Pipelines**.

3. Click **New Pipeline**.

4. In the **Run new pipeline** dialog box, enter the variable name as **PIPELINE_TYPE** and enter the value as **cleanup**.

    ![GitLab Clean Pipeline Variable](../../assets/images/gitlab-clean-pipeline-variable.png)

5. Click **Run Pipeline** to execute the cleanup pipeline.

6. In the pipeline, select the image to be cleaned up from the `select_image` stage.

    ![GitLab Clean Select Image](../../assets/images/gitlab-clean-select-image.png)

7. Click the **Play** button on the cleanup stage to execute the cleanup.

    ![GitLab Clean Run Stage](../../assets/images/gitlab-clean-run-stage.png)

8. Monitor the pipeline progress through the GitLab web interface:

    a. Click on the running pipeline to view details.

    b. Monitor the cleanup stage as it progresses to completion.

    ![GitLab Clean Monitor Pipeline](../../assets/images/gitlab-clean-monitor-pipeline.png)

9. Review the stage status indicators:
    - **Green checkmark**: Stage completed successfully
    - **Red X**: Stage failed (click for error details)
    - **Blue circle**: Stage currently running

## Verification

1. Check the GitLab pipeline status to ensure the cleanup stage passed.

2. Verify the Image Group count is within the configured retention limit.

3. Review the cleanup pipeline logs in GitLab for specific details about which Image Groups were removed.

## Related Topics

* Retry Pipeline Operations
* Configuration Reference
