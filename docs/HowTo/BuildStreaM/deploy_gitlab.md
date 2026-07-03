# Deploy GitLab for BuildStreaM

Deploy GitLab as the CI/CD automation engine for BuildStreaM pipelines. This procedure covers GitLab installation, project setup, pipeline configuration, and runner verification.

## Overview

BuildStreaM uses a **three-pipeline architecture** in GitLab:

- **Build Pipeline**: Triggered by catalog changes, creates images and establishes Job ID to Image Group ID mapping. Can also be executed manually.
- **Deploy Pipeline**: Triggered by PXE mapping changes, deploys images to cluster nodes. Can also be executed manually.
- **Cleanup Pipeline**: Triggered manually, allows users to delete selected Image Groups.

## Prerequisites

- Omnia BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed on the OIM node
- The node where GitLab will be deployed must have internet connectivity
- A dedicated node is required for BuildStreaM GitLab deployment
- Minimum 4 GB RAM, 2 CPU cores, 20 GB free disk space on the GitLab node
- OIM node must be accessible from the GitLab node
- BuildStreaM API server must be reachable from the GitLab node
- AppStream and Base OS repositories are configured and accessible from the GitLab node
- SELinux is disabled on the GitLab node

!!! important

    Omnia uses a dedicated GitLab instance for BuildStreaM. Currently, existing GitLab setups configured for other purposes are not supported.

!!! note

    Ensure that the `build_stream_port` is correctly configured in the `build_stream_config.yml` file. The BuildStreaM port cannot be modified after preparing the OIM. To modify the port after preparing the OIM, you need to cleanup the OIM first (using `cleanup_oim.yml`), and then prepare the OIM again with the required port number (using `prepare_oim.yml`).

## Procedure

1. Use SSH to connect to the `omnia_core` container:

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

2. Update the `gitlab_config.yml` file. Use the [GitLab configuration table](../../Reference/Configuration/gitlab_config.md) for reference.

    ```bash title="Run on: omnia_core container"
    vi /opt/omnia/input/project_default/gitlab_config.yml
    ```

!!! caution

    Ensure that all network ranges and NIC IP addresses provided in the configuration files are distinct with no overlap. All iDRACs must be reachable from the OIM.

3. Navigate to the GitLab directory and run the playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/gitlab
    ansible-playbook gitlab.yml
    ```

4. When prompted, enter the GitLab password. Note this password as it is required to access the GitLab project and instance.

    !!! note

        The installation may take 10-15 minutes to complete.

    The `gitlab.yml` playbook performs the following tasks:

    - Installs the GitLab instance on the host specified in `gitlab_config.yml`.
    - Creates a project with the specified name, visibility, and default branch.
    - Installs GitLab runner as a Podman container.
    - Generates a self-signed CA certificate at `/root/gitlab-certs/ca.crt` on the GitLab node.
    - Adds the project with the following files:
        - **Pipeline Configuration Files**:
            - `.gitlab-ci.yml` -- Parent router pipeline that dispatches to child pipelines
            - `.gitlab-ci-build.yml` -- Build pipeline for creating images
            - `.gitlab-ci-deploy.yml` -- Deploy pipeline for deploying images to nodes
            - `.gitlab-ci-cleanup.yml` -- Cleanup pipeline for removing old Image Groups
            - `.gitlab-ci-deploy-child-template.yml` -- Dynamic child pipeline template for deploy operations
        - **Catalog File**:
            - `catalog_rhel.json` -- Default catalog file containing build definitions for RHEL images
        - **Input Folder**:
            - `input/` -- Directory containing all BuildStreaM input configuration files

    ![BuildStream project](../../assets/images/buildstream_project.png)

    The input folder includes the following configuration files:

    - `build_stream_config.yml` -- BuildStreaM configuration file
    - `gitlab_config.yml` -- GitLab configuration file
    - `high_availability_config.yml` -- High availability configuration file
    - `local_repo_config.yml` -- Local repository configuration file
    - `network_config.yml` -- Network configuration file
    - `omnia_config.yml` -- Omnia configuration file
    - `provision_config.yml` -- Provision configuration file
    - `pxe_mapping_file.csv` -- PXE mapping file
    - `security_config.yml` -- Security configuration file
    - `storage_config.yml` -- Storage configuration file
    - `telemetry_config.yml` -- Telemetry configuration file
    - `telemetry_storage_config.yml` -- Telemetry storage configuration file

    ![BuildStream project input files structure](../../assets/images/buildstream_project_input_files.png)

5. To avoid **Not Secure** warnings when accessing the GitLab instance, download and import the CA certificate to your browser.

## Verification

After the installation completes, verify the following:

- Verify you can access the GitLab project URL:

    ```text title="GitLab project URL"
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

- Verify the project contains the expected files and folders.
- Verify runner status through GitLab web interface:

    1. Navigate to **Settings** → **CI/CD**.
    2. Expand **Runners** section.
    3. Verify the runner shows a **green** status indicator.
    4. Confirm runner is set to **Running Always** with **Podman Container`.

!!! note

    The `omnia_auth.service` runs only when OpenLDAP is specified in `/opt/omnia/input/project_default/software_config.json`.

!!! note

    The `omnia_build_stream.service`, `omnia_postgres.service`, and `playbook_watcher.service` run only when BuildStreaM is enabled in `/opt/omnia/input/project_default/build_stream_config.yml`.

## Next Steps

- [Execute Build Pipeline](execute_build_pipeline.md) -- Update catalog and trigger the build pipeline
- [Execute Deploy Pipeline](execute_deploy_pipeline.md) -- Deploy built images to cluster nodes

## Troubleshooting

- **GitLab not accessible**: Verify network connectivity between OIM and GitLab node. Check that the port specified in `gitlab_config.yml` is not blocked by firewall.
- **Runner not running**: Check runner status in GitLab UI under **Settings** → **CI/CD** → **Runners**. Verify the Podman container is running on the GitLab node.
- **SSH omnia_core fails after prepare_oim**: If `ssh omnia_core` fails after switching from a non-root to root user using `sudo`, log in directly as a `root` user before executing the playbook. See [General Troubleshooting](../../Troubleshooting/general.md) for details.
- For additional issues, see [BuildStreaM Troubleshooting](../../Troubleshooting/buildstream.md).
