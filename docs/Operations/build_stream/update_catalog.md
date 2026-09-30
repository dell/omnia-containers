# Update the BuildStreaM Catalog

Update the BuildStreaM catalog file to modify build specifications and trigger new pipeline runs.

## Overview

The `catalog_rhel.json` file defines your build requirements, including
functional groups, architecture types, operating systems, and software
packages. Modifying this file triggers the independent build pipeline.

The root `cadence_catalog_rhel.json` is a separate input for the unified
cadence pipeline. Committing that file triggers image build, deployment,
restart, and validation in one pipeline. Periodic cadence operation updates it
only after RPM reconciliation detects package changes.

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
- **AI-assisted authoring** -- Select the `SKILL.md` file for the required
  operation and invoke it through an approved AI assistant. See
  [Use AI-Assisted Catalog Authoring Skills](../../HowTo/build_stream/ai_catalog_authoring.md).

Review AI-generated content and approve any proposed catalog edit before it is
applied. Then follow the same validation, Git review, and BuildStreaM pipeline
procedure used for a manually authored catalog.

## Procedure


1. Go to the GitLab project URL:

    ```text title="GitLab project URL"
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

2. Navigate to **Code** → **Repository**.

3. Locate the catalog to update:

    - Use `catalog_rhel.json` for an independent image build.
    - Use `cadence_catalog_rhel.json` only when you intend to start the unified
      cadence pipeline.

4. Modify the `catalog_rhel.json` file to define your build requirements.
   Follow the lowercase field names and structure in the release-matched
   samples under `src/main/samples/`. For an AI-assisted workflow, copy only
   the reviewed and validated result into this root file; editing a source
   sample or a file under `catalog/` does not trigger the build pipeline. For a
   new revision of the same catalog family, retain `identifier` and increment
   `version`.

5. Commit the catalog changes. GitLab selects the pipeline associated with the
   changed root catalog.

## Verification


After committing the catalog changes, verify that the update was successful:

1. Navigate to **Build** → **Pipelines** in the GitLab project.

2. Confirm that GitLab selected the expected pipeline: build for
   `catalog_rhel.json`, or cadence for `cadence_catalog_rhel.json`.

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

- [AI-Assisted Catalog Authoring](../../HowTo/build_stream/ai_catalog_authoring.md) -- Select and invoke a catalog-authoring skill
- [Execute Build Pipeline](../../HowTo/build_stream/execute_build_pipeline.md) -- Detailed build pipeline operations
- [Execute Deploy Pipeline](../../HowTo/build_stream/execute_deploy_pipeline.md) -- Detailed deploy pipeline operations
- [Automate Build and Deployment with Cadence](../../HowTo/build_stream/execute_cadence_pipeline.md) -- Unified cadence pipeline operations
- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipeline operations

## Troubleshooting


**Parse-Catalog stage failing**

Compare the catalog with the catalog staged in the managed GitLab project and
the release-matched samples under `src/main/samples/`. Confirm that
`schema_version` is supported and that `<identifier>-v<version>` has not
already been used. Then correct the reported structure or reference error and
commit a new catalog revision.

**The wrong pipeline started**

Confirm which root catalog was committed. `catalog_rhel.json` selects build;
`cadence_catalog_rhel.json` selects cadence. A catalog under `catalog/` does
not select either pipeline.







