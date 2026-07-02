# Update Catalog & Pipelines

Update the BuildStreaM `catalog_rhel.json` file to modify build requirements
and trigger CI/CD pipeline runs to create and deploy images.

## Overview

The BuildStreaM catalog is a declarative JSON file (`catalog_rhel.json`) that
defines your build requirements:

- Functional group assignments and architecture types.
- Operating system type and version.
- Software packages and configurations.

When you update the catalog and commit changes to GitLab, the build pipeline
is automatically triggered. You can also trigger pipelines manually through
the GitLab interface.

BuildStreaM supports two primary pipeline triggers:

- **Build Pipeline**: Triggered by catalog changes (commit to `catalog_rhel.json`). Creates diskless images.
- **Deploy Pipeline**: Triggered by PXE mapping changes (update to `pxe_mapping_file.csv`). Deploys images to nodes.

## Prerequisites

- GitLab is deployed and configured (see [Deploy GitLab](deploy_gitlab.md)).
- The BuildStreaM catalog repository is initialized with `catalog_rhel.json`.
- A GitLab Runner is registered and active.
- You have access to the GitLab project repository.

## Procedure

### Update the catalog and trigger a build

1. **Navigate to the GitLab project URL**:

    ```text title="GitLab project URL"
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

2. Go to **Code** > **Repository** and locate `catalog_rhel.json`.

3. **Edit the catalog file** to define or modify build requirements.

    !!! note

        Ensure the catalog file contains valid values:

        - **Functional group names**: Use predefined functional group names only.
        - **Architecture type**: `x86_64` or `aarch64`.
        - **OS type**: `RHEL`.
        - **Package types**: `rpm`, `rpm_repo`, `image`, `iso`, `tarball`, `pip_module`, `git`, `manifest`.

    Reference examples are available at:
    `https://github.com/dell/omnia/tree/pub/build_stream/examples/catalog`

4. **Commit and push the changes** to trigger the build pipeline automatically.

5. **Monitor the pipeline** in GitLab:

    Navigate to **Build** > **Pipelines** and monitor the following stages:

    - **parse-catalog**: Parses and validates the catalog file.
    - **generate-input-files**: Generates input files and configuration data.
    - **create-local-repository**: Creates the local repository for build artifacts.
    - **build-image**: Builds diskless images based on catalog specifications.

### Update input configuration files

You can also update input configuration files in the GitLab repository's
`input/` folder:

1. Navigate to the `input/` folder in the GitLab repository.

2. Edit the relevant configuration file (e.g., `network_config.yml`, `provision_config.yml`).

3. Commit and push the changes.

### Manually trigger a build pipeline

1. Navigate to **Build** > **Pipelines** and click **New Pipeline**.

2. In the **Run new pipeline** dialog, enter the variable name as `PIPELINE_TYPE` and the value as `build`.

3. Click **Run Pipeline**.

### Trigger a deploy pipeline

1. Update the `pxe_mapping_file.csv` in the GitLab repository's `input/` folder with target node information.

2. Commit and push the changes to trigger the deploy pipeline automatically.

3. Alternatively, manually trigger by navigating to **Build** > **Pipelines** > **New Pipeline** and setting `PIPELINE_TYPE` to `deploy`.

!!! note

    - BuildStreaM supports only one catalog file and one pipeline trigger at a time.
    - Each pipeline processes changes independently. Once a pipeline completes, you can modify files and re-trigger.
    - Multiple pipelines cannot run simultaneously.

## Verification

1. **Verify the pipeline completed successfully**:

    In GitLab, navigate to **Build** > **Pipelines**. The latest pipeline
    should show all stages with green checkmarks.

2. **Review job logs**:

    Click on individual jobs to view execution logs, resource usage, and
    error messages (if any).

3. **For build pipelines**: Verify images were created successfully by checking the pipeline artifacts.

4. **For deploy pipelines**: Verify target nodes have been provisioned and are accessible.

## Next Steps

- [Cleanup Operations](cleanup_operations.md) -- Remove old Image Groups when the count exceeds 50.
- [Retry Pipelines](retry_pipelines.md) -- Retry failed pipeline operations.
- [Deploy GitLab](deploy_gitlab.md) -- Update GitLab or runner configuration.

## Troubleshooting

- **Pipeline fails at parse-catalog stage**: Ensure `catalog_rhel.json` has valid JSON syntax and matches the expected schema. Check job logs for specific validation errors.

- **Pipeline fails at create-local-repository stage**: Verify `local_repo_config.yml` settings. Check the API response log path for detailed error information.

- **Pipeline fails at build-image stage**: Ensure the catalog has predefined functional groups. Review job logs for Ansible playbook errors.

- **Pipeline not triggered on push**: Verify `.gitlab-ci.yml` exists in the repository root. Confirm the GitLab Runner is active and registered.

- **Git push is rejected**: Verify GitLab authentication and that the repository URL is correct.

!!! info "Related resources"

    - [BuildStreaM Deployment](../../GetStarted/buildstream_deployment.md) -- End-to-end deployment tutorial.
    - [BuildStreaM Troubleshooting](../../Troubleshooting/buildstream.md) -- Symptom/Cause/Resolution reference.
