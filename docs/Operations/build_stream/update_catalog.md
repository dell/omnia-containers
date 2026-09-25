# Update the BuildStreaM Catalog

Update the BuildStreaM catalog file to modify build specifications and trigger new pipeline runs.

## Overview

The `catalog_rhel.json` file defines your build requirements, including functional groups, architecture types, operating systems, and software packages. Modifying this file triggers the build pipeline automatically.

## Prerequisites


Complete the following before you update the BuildStreaM catalog:

- **Deploy GitLab for BuildStreaM** -- GitLab must be deployed and configured for BuildStreaM. See [BuildStreaM](../../HowTo/build_stream/index.md).

- **No conflicting build pipeline** -- The current GitLab configuration allows
  pipelines to run concurrently. Wait for a build using the same catalog or
  image resources to complete before committing another catalog change.

- **Catalog file location** -- `catalog_rhel.json` is at the root of the
  managed GitLab project. Source catalog samples are available under
  `src/main/samples/`. Only a committed change to the root
  `catalog_rhel.json` automatically selects the build pipeline.

## Choose an authoring workflow

Use either of these workflows to prepare the catalog change:

- **Manual authoring** -- Edit `catalog_rhel.json` directly and follow the
  procedure on this page.
- **AI-assisted authoring** -- Use NERSC AI Skills to generate, edit, analyze,
  or review the catalog on a working branch. See
  [Author BuildStreaM Catalogs with NERSC AI Skills](../../HowTo/build_stream/ai_catalog_authoring.md).

Both workflows use the same catalog schema, unique-identifier requirement,
GitLab review process, and BuildStreaM pipeline. Review and validate
AI-generated catalog content before committing it.

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

    Ensure that the catalog follows
    `src/build_stream/app/core/catalog/resources/CatalogSchema.json` in the
    Omnia source tree. Invalid entries cause catalog parsing to fail.

!!! warning

    **Unique Catalog Identifier Required**

    Every catalog must have a unique `identifier` attribute. When you modify `catalog_rhel.json`, always update the `identifier` field with a new unique value. Build pipelines triggered from the GitLab portal rely on this identifier to track catalog versions. If the identifier is not unique, the pipeline will fail during the "Parse Catalog" stage.

## Next steps

- [NERSC AI Catalog Authoring](../../HowTo/build_stream/ai_catalog_authoring.md) -- AI-assisted catalog generation, editing, and analysis
- [Execute Build Pipeline](../../HowTo/build_stream/execute_build_pipeline.md) -- Detailed build pipeline operations
- [Execute Deploy Pipeline](../../HowTo/build_stream/execute_deploy_pipeline.md) -- Detailed deploy pipeline operations
- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipeline operations

## Troubleshooting


**Parse-Catalog stage failing**

Ensure the catalog JSON follows
`src/build_stream/app/core/catalog/resources/CatalogSchema.json`. Use the
catalog staged in the managed GitLab project and the samples under
`src/main/samples/` as source-backed references.













