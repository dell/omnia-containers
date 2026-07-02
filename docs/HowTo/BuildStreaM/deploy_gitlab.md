# Deploy GitLab

Deploy and configure a dedicated GitLab instance for BuildStreaM CI/CD
pipelines using the Omnia `gitlab.yml` playbook.

## Overview

BuildStreaM uses GitLab as the CI/CD engine to execute automated pipelines.
GitLab provides the **three-pipeline architecture**:

- **Build Pipeline**: Triggered by catalog changes, creates images and establishes Job ID to Image Group ID mapping. Can also be executed manually.
- **Deploy Pipeline**: Triggered by PXE mapping changes, deploys images to cluster nodes. Can also be executed manually.
- **Cleanup Pipeline**: Triggered manually, allows deletion of selected Image Groups.

Omnia deploys a dedicated GitLab instance specifically configured for
BuildStreaM using the `gitlab.yml` playbook. The playbook automates GitLab
installation, project creation, pipeline configuration, and runner setup.

## Prerequisites

- The BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed on the OIM (see [BuildStreaM Deployment](../../GetStarted/buildstream_deployment.md) Step 3).
- A dedicated node is required for BuildStreaM GitLab deployment.
- The GitLab node has internet connectivity.
- The GitLab node has minimum 4 GB RAM, 2 CPU cores, and 20 GB free disk space.
- GitLab requires a minimum of 2 CPU cores.
- The OIM node is accessible from the GitLab node.
- The BuildStreaM API server is reachable from the GitLab node.
- AppStream and BaseOS repositories are configured and accessible on the GitLab node.
- SELinux is disabled on the GitLab node.

!!! warning

    Omnia uses a dedicated GitLab instance for BuildStreaM. This procedure
    provisions a new GitLab instance specifically configured for BuildStreaM.
    Existing GitLab setups configured for other purposes are not supported.

## Procedure

1. **Connect to the omnia_core container**:

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

2. **Verify the GitLab configuration file**:

    ```bash title="Run on: OIM (inside omnia_core container)"
    cat /opt/omnia/input/project_default/gitlab_config.yml
    ```

    <!-- TODO: Add gitlab_config.yml parameter reference link when the configuration reference page is created -->

3. **Run the GitLab deployment playbook**:

    ```bash title="Run on: OIM (inside omnia_core container)"
    cd /omnia/gitlab
    ansible-playbook gitlab.yml
    ```

    When prompted, enter a GitLab password. Note this password -- it is
    required to access the GitLab project and instance.

    !!! note

        The installation takes 10--15 minutes to complete.

The `gitlab.yml` playbook performs the following:

- Installs GitLab on the host specified in `gitlab_config.yml`.
- Creates a project with the configured name, visibility, and default branch.
- Installs GitLab Runner as a Podman container.
- Generates a self-signed CA certificate at `/root/gitlab-certs/ca.crt` on the GitLab node.
- Adds the following files to the project:
    - **Pipeline configuration**: `.gitlab-ci.yml` (parent router), `.gitlab-ci-build.yml`, `.gitlab-ci-deploy.yml`, `.gitlab-ci-cleanup.yml`, `.gitlab-ci-deploy-child-template.yml`
    - **Catalog file**: `catalog_rhel.json` (default catalog for RHEL images)
    - **Input folder**: `input/` directory containing all BuildStreaM input configuration files

![BuildStreaM GitLab project structure](../../assets/images/buildstream_project.png)

The `input/` folder includes the following configuration files:

- `build_stream_config.yml` -- BuildStreaM configuration
- `gitlab_config.yml` -- GitLab configuration
- `high_availability_config.yml` -- High availability configuration
- `local_repo_config.yml` -- Local repository configuration
- `network_config.yml` -- Network configuration
- `omnia_config.yml` -- Omnia configuration
- `provision_config.yml` -- Provision configuration
- `pxe_mapping_file.csv` -- PXE mapping file
- `security_config.yml` -- Security configuration
- `storage_config.yml` -- Storage configuration
- `telemetry_config.yml` -- Telemetry configuration
- `telemetry_storage_config.yml` -- Telemetry storage configuration

![BuildStreaM project input files](../../assets/images/buildstream_project_input_files.png)

!!! tip

    To avoid "Not Secure" warnings when accessing the GitLab instance,
    download and import the CA certificate generated at
    `/root/gitlab-certs/ca.crt` on the GitLab node into your browser.

## Verification

1. **Verify you can access the GitLab project URL**:

    ```text title="GitLab project URL"
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

2. **Verify the project** contains the expected files and folders.

3. **Verify runner status** through the GitLab web interface:
    1. Navigate to **Settings** > **CI/CD**.
    2. Expand the **Runners** section.
    3. Verify the runner shows a **green** status indicator.
    4. Confirm the runner is set to **Running Always** with **Podman Container**.

## Next Steps

- [Update Catalog & Pipelines](update_catalog_pipeline.md) -- Update the catalog and trigger build pipelines.
- [BuildStreaM Troubleshooting](buildstream_troubleshooting.md) -- Troubleshoot pipeline issues.

## Troubleshooting

- **GitLab installation takes too long**: Check network connectivity on the GitLab node and ensure AppStream and BaseOS repositories are accessible. Review the Ansible playbook output for specific errors.

- **Cannot access GitLab URL**: Verify the `gitlab_host` and `gitlab_https_port` values in `gitlab_config.yml`. Ensure the GitLab node firewall allows traffic on the configured port.

- **Runner shows offline status**: Navigate to **Settings** > **CI/CD** > **Runners** in GitLab. Verify the runner container is running: `podman ps --filter name=runner` on the GitLab node.

- **Certificate warnings in browser**: Import the CA certificate from `/root/gitlab-certs/ca.crt` on the GitLab node into your browser's trusted certificates.

!!! info "Related resources"

    - [BuildStreaM Deployment](../../GetStarted/buildstream_deployment.md) -- End-to-end deployment tutorial.
    - [BuildStreaM Troubleshooting](../../Troubleshooting/buildstream.md) -- Symptom/Cause/Resolution reference.
