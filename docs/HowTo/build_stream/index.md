# BuildStreaM

## Overview

BuildStreaM provides the customer-facing GitLab CI/CD workflow for catalog-driven HPC image creation and deployment. The deployment creates the following components:

- A PostgreSQL container for BuildStreaM state.
- The BuildStreaM Manager (BSM) FastAPI container and the `playbook-watcher.service` on the Omnia Infrastructure Manager (OIM).
- GitLab CE on the configured GitLab host.
- A GitLab project containing the BuildStreaM build, deploy, and cleanup pipelines.

The parent `.gitlab-ci.yml` routes requests to one of three child pipelines. A change to `catalog_rhel.json` starts the image-build pipeline, a change to `input/orchestrator/pxe_mapping_file.csv` starts the deploy pipeline, and cleanup is started manually or through an API trigger. The infrastructure deployment described on this page prepares this workflow; the OS image is built in the subsequent build-pipeline procedure.

## Prerequisites

- Run BuildStreaM on an OIM host that meets the source requirements: RHEL 10.x, Python 3.12 or later, Ansible Core 2.20 or later, and Podman 5.0 or later.
- Ensure the GitLab host can ping `build_stream_host_ip` and that the OIM can reach the GitLab host.
- Ensure the selected GitLab HTTPS port is unused. The role enables `firewalld` and opens the configured HTTPS port and TCP port 22.
- Allow the GitLab host to reach `packages.gitlab.com`, `docker.io`, and `registry.gitlab.com`. These locations provide GitLab CE and the runner, helper, and default CI images used by the deployment.
- Meet or exceed the configurable GitLab-host minimums. The supplied configuration checks for 4 GB RAM, 2 CPU cores, and 20 GB free space on `/`.

!!! note

    The BuildStreaM validator warns when `build_stream_host_ip` and `gitlab_host` are the same. Use a separate GitLab host unless you have deliberately designed and validated a shared-host deployment.

### Input contract

The current entry playbook reads the following fixed runtime file:

```text
/opt/omnia/build_stream/input/project_default/build_stream_config.yml
```

If `OMNIA_DATA_PATH` is changed, replace `/opt/omnia` with that value. Use `OMNIA_PROJECT_NAME=project_default` when initializing this module so that staged inputs and the entry playbook use the same project directory.

`build_stream_config.yml` is the single consolidated BuildStreaM and GitLab configuration file. Do not create a separate `gitlab_config.yml`, and do not remove parameters from the supplied file.

| Parameter | Required value or default | Purpose |
|---|---|---|
| `enable_build_stream` | Set to `true` | Enables validation and deployment. |
| `build_stream_host_ip` | Required | IP address of the OIM host that serves the BSM API. |
| `build_stream_port` | `8010`; valid range `1`–`65535` | BSM HTTPS port. |
| `gitlab_host` | Required | IP address of the target GitLab host. |
| `gitlab_project_name` | `omnia-catalog` | Project created and managed by Omnia. |
| `gitlab_project_visibility` | `private` | Accepted values are `private`, `internal`, and `public`. |
| `gitlab_default_branch` | `main` | Branch used for repository and API operations. |
| `gitlab_https_port` | `443`; valid range `1`–`65535` | GitLab HTTPS port. |
| `gitlab_min_storage_gb` | `20` | Minimum free space checked on the GitLab host root file system. |
| `gitlab_min_memory_gb` | `4` | Minimum GitLab-host memory. |
| `gitlab_min_cpu_cores` | `2` | Minimum GitLab-host CPU count. |
| `gitlab_puma_workers` | `2` | GitLab Puma worker count. |
| `gitlab_sidekiq_concurrency` | `10` | GitLab Sidekiq concurrency. |

BuildStreaM creates and manages the following encrypted credential inputs during the credential phase:

```text
/opt/omnia/build_stream/input/project_default/build_stream_credentials.yml
/opt/omnia/build_stream/input/project_default/.build_stream_credentials_key
```

Provide each requested value when prompted:

| Credential | Purpose |
|---|---|
| `gitlab_root_password` | Password assigned to the GitLab `root` account. |
| `gitlab_ssh_password` | Current root SSH password for the GitLab host. |
| `build_stream_auth_username` | Username used by GitLab pipelines to register with the BSM API. |
| `build_stream_auth_password` | BSM registration password; it must contain at least eight characters. |
| `postgres_user` | PostgreSQL user for BuildStreaM; the source credential rules do not permit `root`. |
| `postgres_password` | PostgreSQL password for BuildStreaM. |

The credential utility encrypts the file with Ansible Vault and assigns mode `0600` to the credential and key files. Do not place credential values in `build_stream_config.yml`.

During GitLab project creation, the role copies the following module inputs when they exist under `<OMNIA_DATA_PATH>/<domain>/input/<OMNIA_PROJECT_NAME>/`:

- `repo_manager/repo_manager_config.yml`
- `repo_manager/repo_manager_endpoint_config.yml`
- `image_build_manager/image_build_config.yml`
- `image_build_manager/package_groups.yml`
- `orchestrator/omnia_config.yml`
- `orchestrator/orchestrator_config.yml`
- `orchestrator/network_spec.yml`
- `orchestrator/security_config.yml`
- `orchestrator/storage_config.yml`
- `orchestrator/high_availability_config.yml`
- `orchestrator/additional_cloud_init.yml`
- `orchestrator/pxe_mapping_file.csv`
- `orchestrator/set_pxe_boot_config.yml`

Configure the repo-manager and image-build-manager inputs before starting an image build. The build pipeline refreshes these files from the GitLab branch and uploads them, together with `catalog_rhel.json` and `omnia.env`, to the BSM API.

## Procedure

1. Configure the staged input files for the three base domains. The files are
   located under
   `$OMNIA_DATA_PATH/<domain>/input/$OMNIA_PROJECT_NAME/`.

    | Domain | Configuration references |
    |---|---|
    | Repo Manager | [Repository configuration](../../Reference/Configuration/repo_manager_config.md) and [Pulp endpoint configuration](../../Reference/Configuration/repo_manager_endpoint_config.md) |
    | Image Build Manager | [Image-build configuration](../../Reference/Configuration/image_build_manager_config.md) and, when `functional_groups_source: config` is selected, [package groups](../../Reference/Configuration/package_groups.md) |
    | Orchestrator | Review the complete [Orchestrator input summary](../orchestrator/index.md#input-summary) and configure the files required for the selected deployment. |

2. From the Main source directory, prepare the base infrastructure:

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --prepare-base
    ```

    The command validates, collects credentials for, and prepares Repo Manager,
    Image Build Manager, and Orchestrator in dependency order. It stops if any
    domain or phase fails. For command behavior, options, and verification, see
    [Prepare base infrastructure](../main/prepare_base.md).

3. Edit the staged BuildStreaM configuration:

    ```bash title="Run on: OIM host"
    vi /opt/omnia/build_stream/input/project_default/build_stream_config.yml
    ```

    At minimum, set `enable_build_stream: true`, `build_stream_host_ip`, and `gitlab_host`. Confirm that `build_stream_port` and `gitlab_https_port` are available.

4. Deploy the complete BuildStreaM stack:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run build_stream
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/build_stream/playbooks
        ansible-playbook build_stream.yml
        ```

    Enter the six BuildStreaM credentials listed in the input contract when
    prompted. The default BuildStreaM flow validates the configuration,
    collects credentials, prepares PostgreSQL, the BSM API, and the playbook
    watcher, and then configures GitLab and the CI/CD project.

5. Retrieve `/root/gitlab-certs/ca.crt` from the GitLab host and import it into the client browser trust store if the browser must trust the self-signed Omnia CA.

## Verification

1. **Output contract:** On the OIM, inspect the status file produced by the `prepare` phase:

    ```bash title="Run on: OIM host"
    cat /opt/omnia/build_stream/output/project_default/build_stream_status.yml
    ```

    A successful prepare operation produces this structure with values from `build_stream_config.yml`:

    ```yaml
    ---
    overall_status: "prepared"
    build_stream_host: "<build_stream_host_ip>"
    build_stream_port: 8010
    gitlab_host: "<gitlab_host>"
    gitlab_https_port: 443
    gitlab_url: "https://<gitlab_host>:443"
    bsm_api_url: "https://<build_stream_host_ip>:8010"
    ```

    `overall_status: "prepared"` is the value written by the current implementation; GitLab deployment does not change this field.

2. Verify that the OIM services required by the GitLab phase are active:

    ```bash title="Run on: OIM host"
    systemctl is-active omnia_postgres.service
    systemctl is-active omnia_build_stream.service
    systemctl is-active playbook-watcher.service
    ```

3. Verify the BSM health endpoint with its generated certificate:

    ```bash title="Run on: OIM host"
    curl --cacert /opt/omnia/build_stream_ssl/ssl/bs_cert.pem \
      https://<build_stream_host_ip>:<build_stream_port>/health
    ```

4. On the GitLab host, verify GitLab and its Quadlet runner service:

    ```bash title="Run on: GitLab host"
    gitlab-ctl status
    systemctl is-active gitlab-runner.service
    ```

5. Sign in as `root` and open the project:

    ```text
    https://<gitlab_host>/root/<gitlab_project_name>
    ```

    For a non-default HTTPS port, use `https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>`.

6. Confirm that the project contains `catalog_rhel.json`, `omnia.env`, the `input/` directory, and these CI/CD files:

    ```text
    .gitlab-ci.yml
    .gitlab-ci-build.yml
    .gitlab-ci-deploy.yml
    .gitlab-ci-deploy-child-template.yml
    .gitlab-ci-cleanup.yml
    .gitlab-ci-cleanup-child-template.yml
    ```

7. In the GitLab project, open **Settings** > **CI/CD**, expand **Runners**, and confirm that **Omnia Hosted Runner** is online. The deployment itself fails if it cannot detect an online project runner.

## Next steps

- [Execute Build Pipeline](execute_build_pipeline.md) to update `catalog_rhel.json` and create HPC OS images.
- [Execute Deploy Pipeline](execute_deploy_pipeline.md) to select and deploy a built image.
- [Cleanup Operations](../../Operations/build_stream/cleanup_operations.md) to remove selected build jobs and image groups through the cleanup pipeline.

## Troubleshooting

- **The project input directory does not exist:** Export `OMNIA_DATA_PATH=/opt/omnia` and `OMNIA_PROJECT_NAME=project_default`, then run `src/build_stream/domain-init.sh`. The current entry playbook requires `/opt/omnia/build_stream/input/project_default`.
- **The precheck reports missing containers or credentials:** Ensure `pulp`, `minio-server`, and `registry` are running and that the repo-manager and image-build-manager credential files listed in the input contract exist. The precheck directs the operator to run `omnia.sh --prepare-base` when these dependencies are absent.
- **Configuration validation fails:** Use the consolidated `build_stream_config.yml`, set `enable_build_stream` to `true`, provide both host values, and keep both ports in the range `1`–`65535`. The configuration schema does not allow unsupported extra keys.
- **`sshpass` or another package cannot be installed:** Run `dnf makecache` and correct the BaseOS/AppStream repository configuration on the affected host before retrying.
- **The GitLab HTTPS port is in use:** Choose an unused `gitlab_https_port` in `build_stream_config.yml` before deployment.
- **GitLab-host validation fails:** Disable SELinux, provide at least the configured CPU, memory, and free-space minimums, and verify that the GitLab host can ping `build_stream_host_ip`.
- **The GitLab phase reports an inactive OIM service or a missing BSM certificate:** Run the `prepare` phase and verify `omnia_postgres.service`, `omnia_build_stream.service`, and `playbook-watcher.service`. The required certificate is `/opt/omnia/build_stream_ssl/ssl/bs_cert.pem` when `OMNIA_DATA_PATH=/opt/omnia`.
- **The GitLab API is unreachable:** Verify the configured host and HTTPS port, firewall access, and the generated TLS files under `/root/gitlab-certs` on the GitLab host.
- **Runner image deployment fails:** Verify outbound access to Docker Hub and the GitLab registry, available disk space, and any applicable registry pull limits. The source retries each image pull five times.
- **The runner is not online:** Check `gitlab-runner.service`, the Podman socket, and the runner configuration under `/srv/gitlab-runner/config`. Changes to the GitLab port or project identity can invalidate the existing runner registration.
- **A GitLab port or project-name reconfiguration is required:** The source requires cleanup before redeployment. The supported `cleanup` tag removes the complete BuildStreaM deployment, including GitLab, BSM, PostgreSQL, credentials, and runtime data; back up required data before using it.
