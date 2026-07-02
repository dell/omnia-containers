# Retry Pipeline Operations

Retry failed BuildStreaM pipelines after identifying and resolving the
root cause of the failure.

## Overview

You can retry a pipeline when one or more stages fail. Before retrying,
identify and resolve the issue that caused the failure. Retrying creates
a new job and re-executes the entire pipeline from the beginning.

!!! warning

    Do not cancel a running GitLab pipeline or stage. Cancellation prevents
    some pipeline steps from executing, which leaves the BuildStreaM job in
    an intermediate, inconsistent state. Backend BuildStreaM tasks already in
    progress continue running to completion regardless of cancellation.

## Prerequisites

- A job exists with one or more stages in `FAILED` state.
- The issue that caused the failure has been identified and resolved.
- Configuration files (PXE mapping and input files) have been corrected if needed.

## Procedure

1. Navigate to **Build** > **Pipelines** and identify the failed pipeline.

2. Identify the stage that failed and review the error logs.

3. Resolve the issue that caused the failure:
    1. Fix configuration errors if present.
    2. Resolve network connectivity issues.
    3. Clear resource constraints if applicable.
    4. Address any other specific error conditions.

4. Click the **Retry downstream pipeline** icon on the stage to re-execute the entire pipeline.

    ![Retry pipeline button](../../assets/images/retry-pipeline.png)

    !!! note

        This creates a new job and re-executes the entire pipeline from the
        beginning. It is recommended to retry the entire pipeline rather
        than individual stages.

5. Verify that the pipeline completes successfully.

## Verification

1. Check the GitLab pipeline status to ensure all stages passed.
2. Verify a new Pipeline ID is created for the retry operation.
3. For build pipelines, verify that images were created successfully.
4. For deploy pipelines, verify that nodes were deployed correctly.
5. Compare results with the original failed pipeline to confirm the issue is resolved.

## Next Steps

- [Perform Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups.
- [Update Catalog & Pipelines](update_catalog_pipeline.md) -- Modify catalogs and re-trigger pipelines.

## Troubleshooting

- **Retry button not displayed**: The Retry button may not appear for certain failed pipeline stages. Initiate a restart from the parent pipeline to resolve this issue. This restarts the entire pipeline from the beginning.

- **Retried pipeline fails again**: Ensure the root cause was fully resolved before retrying. Check the pipeline logs for new or different error messages.

!!! info "Related resources"

    - [BuildStreaM Deployment](../../GetStarted/buildstream_deployment.md) -- End-to-end deployment tutorial.
    - [BuildStreaM Troubleshooting](../../Troubleshooting/buildstream.md) -- Symptom/Cause/Resolution reference.
