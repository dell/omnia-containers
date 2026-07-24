# Update Catalog

Update the BuildStreaM catalog file to modify build specifications and trigger new pipeline runs.

## Overview

The `catalog_rhel.json` file defines your build requirements, including functional groups, architecture types, operating systems, and software packages. Modifying this file triggers the build pipeline automatically.

## Prerequisites


Complete the following before you update the BuildStreaM catalog:

- **Deploy GitLab for BuildStreaM** -- GitLab must be deployed and configured for BuildStreaM. See [Deploy GitLab](deploy_gitlab.md).

- **No active build pipelines** -- Ensure that no build pipeline is currently running. If a build pipeline is in progress when you update the catalog, the existing pipeline will be cancelled and a new one will be triggered automatically. Wait for the current pipeline to complete before modifying the catalog.

- **Catalog file location** -- The `catalog_rhel.json` file is located at `/omnia/build_stream/catalog/catalog_rhel.json` on the OIM. Example predefined catalogs are available in the `/omnia/build_stream/catalog/examples/` directory for reference. Only modifications to `catalog_rhel.json` trigger the build pipeline; other files in the catalog directory do not.

## Procedure


1. Go to the GitLab project URL:

    ```text title="GitLab project URL"
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

2. Navigate to **Code** → **Repository**.

3. Locate the catalog file `catalog_rhel.json`.

4. Modify the `catalog_rhel.json` file to define your build requirements.

5. Commit the catalog changes. The build pipeline triggers automatically.

## Verification


After committing the catalog changes, verify that the update was successful:

1. Navigate to **Build** → **Pipelines** in the GitLab project.

2. Confirm that a new build pipeline has been triggered automatically.

3. Verify that the commit appears in the commit history with a successful status.

!!! note

    Ensure that the catalog file adheres to the catalog schema. The schema is available at `/omnia/build_stream/core/catalog/resources/CatalogSchema.json`. Invalid catalog entries will cause the pipeline to fail.

!!! warning

    **Unique Catalog Identifier Required**

    Every catalog must have a unique `identifier` attribute. When you modify `catalog_rhel.json`, always update the `identifier` field with a new unique value. Build pipelines triggered from the GitLab portal rely on this identifier to track catalog versions. If the identifier is not unique, the pipeline will fail during the "Parse Catalog" stage.

## Next Steps

- [Execute Build Pipeline](execute_build_pipeline.md) -- Detailed build pipeline operations
- [Execute Deploy Pipeline](execute_deploy_pipeline.md) -- Detailed deploy pipeline operations
- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipeline operations

## Troubleshooting


**Parse-Catalog stage failing**

Ensure the catalog JSON is aligned with the expected schema. Reference the catalog examples available in the GitLab project for valid structure and format. The schema is available at `/omnia/build_stream/core/catalog/resources/CatalogSchema.json` on the OIM.
