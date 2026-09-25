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
- **AI-assisted authoring** -- Use the standalone AI-Assisted Catalog
  Authoring Skills to generate, edit, analyze, or compare catalogs on a working
  branch. See
  [Author BuildStreaM Catalogs with AI-Assisted Skills](../../HowTo/build_stream/ai_catalog_authoring.md).

Both workflows use the same catalog structure, catalog-revision identity,
GitLab review process, and BuildStreaM pipeline. Review and validate
AI-generated catalog content before committing it.

For an AI-assisted edit, review the impact and compatibility findings and
explicitly approve the proposed change before it is applied. The skills prefer
approved online sources. If they use only the delivered master reference file,
verify that the result discloses the reduced analysis scope. After the edit,
validate each changed catalog and review the generated or updated changelog.
For a bulk operation, review the separate lists of changed, skipped, and
unaffected catalogs; a catalog that fails validation remains unchanged.

## Procedure


1. Go to the GitLab project URL:

    ```text title="GitLab project URL"
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

2. Navigate to **Code** → **Repository**.

3. Locate the catalog file `catalog_rhel.json`.

4. Modify the `catalog_rhel.json` file to define your build requirements.
   Follow the lowercase field names and structure in the release-matched
   samples under `src/main/samples/`. For a new revision of the same catalog
   family, retain `identifier` and increment `version`.

5. Commit the catalog changes. The build pipeline triggers automatically.

## Verification


After committing the catalog changes, verify that the update was successful:

1. Navigate to **Build** → **Pipelines** in the GitLab project.

2. Confirm that a new build pipeline has been triggered automatically.

3. Verify that the commit appears in the commit history with a successful status.

!!! note

    Compare the catalog with the release-matched samples under
    `src/main/samples/` and the
    [Catalog JSON reference](../../Reference/SampleFiles/catalog_json.md).
    Validate its structure, references, package sources, and business rules
    before committing it. Invalid entries cause catalog processing to fail.

!!! warning

    **Unique Catalog Revision Required**

    BuildStreaM identifies a catalog revision as
    `<identifier>-v<version>`. This composite value must be unique. Keep the
    `identifier` when revising the same catalog family and increment
    `version`. Use a new `identifier` only for a different catalog family.
    Reusing an existing composite value causes the **Parse Catalog** stage to
    fail.

## Next steps

- [AI-Assisted Catalog Authoring](../../HowTo/build_stream/ai_catalog_authoring.md) -- Catalog generation, editing, and analysis
- [Execute Build Pipeline](../../HowTo/build_stream/execute_build_pipeline.md) -- Detailed build pipeline operations
- [Execute Deploy Pipeline](../../HowTo/build_stream/execute_deploy_pipeline.md) -- Detailed deploy pipeline operations
- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipeline operations

## Troubleshooting


**Parse-Catalog stage failing**

Compare the catalog with the catalog staged in the managed GitLab project and
the release-matched samples under `src/main/samples/`. Confirm that
`schema_version` is supported and that `<identifier>-v<version>` has not
already been used. Then correct the reported structure or reference error and
commit a new catalog revision.










