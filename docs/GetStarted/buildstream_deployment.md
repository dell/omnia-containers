# Path D: BuildStreaM Automated Deployment

## Overview

Use this deployment path to automate image building and node provisioning with
BuildStreaM and its managed GitLab pipelines.

The workflow prepares the Omnia Infrastructure Manager (OIM) and the base
module services before deploying BuildStreaM. A change to the catalog starts
the build pipeline, which synchronizes repository content and builds the
selected images. A change to the PXE mapping starts the deploy pipeline, which
deploys the selected image, restarts the target nodes, and validates the
deployment. Deploying BuildStreaM prepares the automation environment; image
building and node provisioning occur when you run the corresponding pipeline.

## BuildStreaM workflow

<div class="of-wrap">
<div class="of-root">
  <div class="of-hdr">
    <div class="of-h2">Source-defined BuildStreaM and pipeline flow</div>
  </div>
  <div class="of-flow">
    <div class="of-pill">Start on the OIM</div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Configure and set up the OIM</div>
      <div class="d"><code>omnia.env</code> &rarr; <code>omnia.sh --setup-venv</code></div>
      <div class="of-more"><a href="../HowTo/main/setup_oim.html">Learn more: OIM setup &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Prepare the base module services</div>
      <div class="d">Pulp, MinIO, registry, and required credentials</div>
      <div class="of-more"><a href="../HowTo/build_stream/index.html#prerequisites">Learn more: Base prerequisites &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Configure and deploy BuildStreaM</div>
      <div class="d">PostgreSQL, BSM, watcher, GitLab, project, and runner</div>
      <div class="of-more"><a href="../HowTo/build_stream/index.html">Learn more: Deploy BuildStreaM &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Commit the catalog</div>
      <div class="d">Build pipeline &rarr; Repository Manager &rarr; Image Build Manager</div>
      <div class="of-more"><a href="../HowTo/build_stream/execute_build_pipeline.html">Learn more: Build pipeline &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Commit the PXE mapping CSV</div>
      <div class="d">Deploy pipeline &rarr; select, deploy, restart, and validate</div>
      <div class="of-more"><a href="../HowTo/build_stream/execute_deploy_pipeline.html">Learn more: Deploy pipeline &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Verify GitLab and BSM results</div>
      <div class="d">Pipeline state, module contracts, and job logs</div>
      <div class="of-more"><a href="../HowTo/build_stream/index.html#verification">Learn more: Verify BuildStreaM &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-pill">Automated image lifecycle ready</div>
  </div>
</div>
</div>

## Prerequisites

- Use an Omnia source checkout on the OIM. For the documented validated RC1
  baseline, run BuildStreaM on RHEL 10.0 with Python 3.12 or later, Ansible
  Core 2.20 or later, and Podman 5.0 or later. See the
  [Operating Systems Matrix](../Reference/SupportMatrix/operating_systems.md).
- Set `SYSTEM_ADMIN_NIC_IPV4` in `src/main/omnia.env` to an IPv4 address
  assigned to an OIM interface. Keep `OMNIA_PROJECT_NAME=project_default` for
  this workflow because the current BuildStreaM setup role fixes its project
  input and output directories to that name.
- Prepare the Repository Manager and Image Build Manager base services. The
  BuildStreaM precheck specifically requires running `pulp`, `minio-server`,
  and `registry` containers and the two modules' credential files.
- Provide a GitLab host reachable from the OIM through SSH and HTTPS. Provide
  its root SSH password during BuildStreaM credential collection.
- Disable SELinux on the GitLab host and reboot it before deployment. The
  source prerequisite check stops when SELinux is enabled.
- Ensure the GitLab host meets the minimum CPU, memory, and free-storage values
  configured in `build_stream_config.yml`. The supplied defaults are 2 CPU
  cores, 4 GB of memory, and 20 GB free on `/`.
- Ensure the configured BSM and GitLab HTTPS ports are available. The GitLab
  host must be able to reach `build_stream_host_ip`.
- Provide working package repositories on the OIM and GitLab host. GitLab
  deployment also requires access to the configured GitLab package source and
  the registries used for the runner, helper, and default CI images.
- Avoid overlapping pipelines that operate on the same catalog, image, mapping,
  or deployment state. The generated GitLab configuration permits concurrent
  pipelines.

## Procedure

### 1. Configure and set up the OIM

1. Edit the environment configuration from the Omnia source tree:

    ```bash title="Run on: OIM host"
    cd src/main
    vi omnia.env
    ```

2. Create the shared virtual environment, install module dependencies, and
   stage the module input files and BuildStreaM application:

    ```bash title="Run on: OIM host"
    ./omnia.sh --setup-venv
    ```

    This command runs the selected modules' `domain-init.sh` scripts. With the
    standard environment, BuildStreaM stages its configuration at:

    ```text
    <OMNIA_DATA_PATH>/build_stream/input/<OMNIA_PROJECT_NAME>/build_stream_config.yml
    ```

    BuildStreaM derives its data directory directly from `OMNIA_DATA_PATH`.
    Set `OMNIA_DATA_PATH` to customize the common data root.

3. Load the installed environment and activate the shared virtual environment
   in the current shell:

    ```bash title="Run on: OIM host"
    source /etc/profile.d/omnia-env.sh
    source "$OMNIA_DATA_PATH/activate-omnia.sh"
    build_stream_path="${OMNIA_DATA_PATH}/build_stream"
    repo_manager_path="${OMNIA_DATA_PATH}/repo_manager"
    image_build_manager_path="${OMNIA_DATA_PATH}/image_build_manager"
    orchestrator_path="${OMNIA_DATA_PATH}/orchestrator"
    ```

    This workflow currently requires `OMNIA_PROJECT_NAME=project_default`, but
    using the loaded variables keeps the data root portable.

For all environment and setup options, see
[Configure the environment](../HowTo/main/configure_environment.md) and
[Set up the OIM](../HowTo/main/setup_oim.md).

### 2. Configure and prepare the base modules

BuildStreaM does not consume an upstream status file during its own
preparation, but its precheck and generated pipelines depend on the base
module services and inputs.

1. Review the staged project inputs that the GitLab deployment copies into the
   managed repository:

    | Deployment module | Inputs used by the managed pipelines |
    |---|---|
    | Repository Manager | `repo_manager_config.yml`, `repo_manager_endpoint_config.yml` |
    | Image Build Manager | `image_build_config.yml`, `package_groups.yml` |
    | Orchestrator | `omnia_config.yml`, `orchestrator_config.yml`, `network_spec.yml`, `security_config.yml`, `storage_config.yml`, `high_availability_config.yml`, `additional_cloud_init.yml`, `pxe_mapping_file.csv`, `set_pxe_boot_config.yml` |

    Repository and image-build inputs must be ready before the first build
    pipeline. Orchestrator inputs and the mapping must be ready before the
    deploy pipeline.

2. Prepare the base services and credentials in the order implemented by
   `omnia.sh`:

    ```bash title="Run on: OIM host"
    cd src/main
    ./omnia.sh --prepare-base
    ```

    The BuildStreaM precheck expects `pulp`, `minio-server`, and `registry` to
    be running. It also checks for:

    ```text
    $repo_manager_path/input/$OMNIA_PROJECT_NAME/repo_manager_config_credentials.yml
    $image_build_manager_path/input/$OMNIA_PROJECT_NAME/image_build_credentials.yml
    ```

### 3. Configure BuildStreaM

1. Edit the staged consolidated configuration:

    ```bash title="Run on: OIM host"
    vi "$build_stream_path/input/$OMNIA_PROJECT_NAME/build_stream_config.yml"
    ```

2. Set `enable_build_stream: true` and provide `build_stream_host_ip` and
   `gitlab_host`. Review the following values in the same file:

    | Setting | Purpose |
    |---|---|
    | `build_stream_port` | HTTPS port for the BSM API; supplied default is `8010`. |
    | `gitlab_project_name` | Managed project name; supplied default is `omnia-catalog`. |
    | `gitlab_project_visibility` | `private`, `internal`, or `public`. |
    | `gitlab_default_branch` | Branch used for repository and API operations. |
    | `gitlab_https_port` | HTTPS port exposed by GitLab; supplied default is `443`. |
    | `gitlab_min_storage_gb` | Minimum free space checked on the GitLab host. |
    | `gitlab_min_memory_gb` | Minimum memory checked on the GitLab host. |
    | `gitlab_min_cpu_cores` | Minimum CPU count checked on the GitLab host. |
    | `gitlab_puma_workers` | GitLab Puma worker count. |
    | `gitlab_sidekiq_concurrency` | GitLab Sidekiq concurrency. |

    Do not create a separate `gitlab_config.yml` and do not add unsupported
    keys; the source schema rejects unknown fields.

For the complete input and credential contract, see
[BuildStreaM](../HowTo/build_stream/index.md) and the
[BuildStreaM contract](../Reference/domain_contracts/build_stream_contract.md).

### 4. Validate and deploy BuildStreaM

1. Run the opt-in base-service precheck:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run build_stream --tags precheck
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/build_stream/playbooks
        ansible-playbook build_stream.yml --tags precheck
        ```

2. Run the complete untagged BuildStreaM flow:

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

    The flow validates `build_stream_config.yml`, collects or reuses the
    encrypted BuildStreaM credentials, prepares PostgreSQL, the BSM API, and
    the playbook watcher on the OIM, and then deploys and configures GitLab.
    The GitLab phase creates the managed project and trigger, sets the BSM
    project variables, pushes the pipeline and available module input files,
    and deploys an online project runner.

    Credential collection requests the GitLab root and SSH passwords, BSM
    authentication username and password, and PostgreSQL username and password.
    These values are written to an Ansible Vault-protected file beside the
    BuildStreaM configuration.

3. Confirm that preparation wrote:

    ```text
    $build_stream_path/output/$OMNIA_PROJECT_NAME/build_stream_status.yml
    ```

    The current writer records `overall_status: prepared`. GitLab deployment
    does not change that field to `running`.

### 5. Review the managed GitLab project

1. Open the URL reported as `gitlab_url` in `build_stream_status.yml` and sign
   in as `root`. The project path uses the configured project name:

    ```text
    https://<gitlab_host>:<gitlab_https_port>/root/<gitlab_project_name>
    ```

2. Confirm that the project contains `catalog_rhel.json`, `omnia.env`, the
   `input/` directory, and these pipeline definitions:

    ```text
    .gitlab-ci.yml
    .gitlab-ci-build.yml
    .gitlab-ci-deploy.yml
    .gitlab-ci-deploy-child-template.yml
    .gitlab-ci-cleanup.yml
    .gitlab-ci-cleanup-child-template.yml
    ```

3. Under **Settings** > **CI/CD** > **Runners**, confirm that the
   **Omnia Hosted Runner** is online.

### 6. Run the build pipeline

1. Review the root `catalog_rhel.json` against the catalog schema in:

    ```text
    src/build_stream/app/core/catalog/resources/CatalogSchema.json
    ```

    When creating a new catalog revision, use a unique catalog `identifier`.
    Configure the repository and image-build files under `input/` for the
    catalog content and functional groups being built.

2. Commit a change to `catalog_rhel.json`. The parent pipeline automatically
   selects the build pipeline. Alternatively, start a web pipeline and choose
   its manual build action, or invoke it with `PIPELINE_TYPE=build`.

3. Monitor the source-defined build stages:

    ```text
    initialization
      -> parse-catalog
      -> configure-local-repository
      -> build-images
      -> summary
    ```

    The pipeline uses BSM jobs to invoke Repository Manager and Image Build
    Manager. Do not start the deploy pipeline until the build pipeline and its
    module status contracts are successful.

For detailed operation and retry guidance, see
[Execute the Build Pipeline](../HowTo/build_stream/execute_build_pipeline.md).

### 7. Run the deploy pipeline

1. Edit `input/orchestrator/pxe_mapping_file.csv` in the managed project. Keep
   the source-defined header and assign only functional groups that have built
   images:

    ```text
    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    ```

    The following example uses the mixed x86_64 and aarch64 functional groups
    in the default RHEL 10.0 catalog:

    ```csv title="Example: input/orchestrator/pxe_mapping_file.csv"
    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    slurm_control_node_rhel_10_0_x86_64,grp0,BSM001,,nid001,02:00:00:00:31:01,172.16.107.81,02:00:00:00:32:01,172.17.107.81,,
    slurm_node_rhel_10_0_aarch64,grp1,BSM002,BSM006,nid002,02:00:00:00:31:02,172.16.107.82,02:00:00:00:32:02,172.17.107.82,InfiniBand.Slot.7-2,192.168.0.121
    login_compiler_node_rhel_10_0_aarch64,grp8,BSM003,,nid003,02:00:00:00:31:03,172.16.107.83,02:00:00:00:32:03,172.17.107.83,InfiniBand.PCIe.Slot.8-1,192.168.0.122
    service_kube_control_plane_rhel_10_0_x86_64,grp3,BSM004,,nid004,02:00:00:00:31:04,172.16.107.84,02:00:00:00:32:04,172.17.107.84,,
    service_kube_control_plane_rhel_10_0_x86_64,grp3,BSM005,,nid005,02:00:00:00:31:05,172.16.107.85,02:00:00:00:32:05,172.17.107.85,,
    service_kube_node_rhel_10_0_x86_64,grp1,BSM006,,nid006,02:00:00:00:31:06,172.16.107.86,02:00:00:00:32:06,172.17.107.86,,
    service_kube_control_plane_rhel_10_0_x86_64,grp3,BSM007,,nid007,02:00:00:00:31:07,172.16.107.87,02:00:00:00:32:07,172.17.107.87,,
    os_rhel_10_0_x86_64,grp6,BSM008,,nid008,02:00:00:00:31:08,172.16.107.88,02:00:00:00:32:08,172.17.107.88,,
    os_rhel_10_0_aarch64,grp7,BSM009,,nid009,02:00:00:00:31:09,172.16.107.89,02:00:00:00:32:09,172.17.107.89,,
    ```

    !!! important

        Replace every sample service tag, MAC address, IP address, and hostname
        with values from the target servers. Keep the exact 11-column header;
        leave optional fields empty with consecutive commas. In the example,
        the Slurm compute node and its service Kubernetes parent share `grp1`,
        and the compute node's `PARENT_SERVICE_TAG` identifies that worker.
        Populate `IB_NIC_NAME` and `IB_IP` together, or leave both empty. Use
        unique lowercase hostnames without a domain suffix; when `dns_enabled`
        is `true`, use `nid001` through `nid999`. Ensure the admin addresses
        belong to a configured admin subnet and every functional group exists
        in `catalog_rhel.json` and has a successful image-build result.

    For the complete schema, validation rules, and OME-generated workflow, see
    [Create a Mapping File](../HowTo/discovery/create_mapping_file.md) and the
    [PXE Mapping File reference](../Reference/SampleFiles/pxe_mapping_file.md).

2. Commit the mapping change. The parent pipeline automatically selects the
   deploy pipeline. Alternatively, start a web pipeline and choose its manual
   deploy action, or invoke it with `PIPELINE_TYPE=deploy`.

3. The deploy parent lists the available image groups and generates a child
   pipeline. Select the intended image group, then start its manual deploy
   action. Monitor the child stages:

    ```text
    select_image
      -> deploy
      -> restart
      -> validate
      -> summary
    ```

    The restart stage performs the PXE restart workflow. Do not run a separate
    PXE utility step for this BuildStreaM deployment.

For the complete procedure, see
[Execute the Deploy Pipeline](../HowTo/build_stream/execute_deploy_pipeline.md).

## Verification

1. Inspect the BuildStreaM output contract on the OIM:

    ```bash title="Run on: OIM host"
    cat "$build_stream_path/output/$OMNIA_PROJECT_NAME/build_stream_status.yml"
    ```

    Confirm `overall_status: prepared` and verify that `gitlab_url` and
    `bsm_api_url` match `build_stream_config.yml`.

2. Verify the OIM services:

    ```bash title="Run on: OIM host"
    systemctl is-active omnia_postgres.service
    systemctl is-active omnia_build_stream.service
    systemctl is-active playbook-watcher.service
    ```

3. Verify the BSM health endpoint with its generated certificate:

    ```bash title="Run on: OIM host"
    curl --cacert "$OMNIA_DATA_PATH/build_stream_ssl/ssl/bs_cert.pem" \
      https://<build_stream_host_ip>:<build_stream_port>/health
    ```

4. Verify GitLab and its runner on the GitLab host:

    ```bash title="Run on: GitLab host"
    gitlab-ctl status
    systemctl is-active gitlab-runner.service
    ```

5. After a build pipeline, confirm the GitLab summary and BSM job state. Also
   inspect the module outputs generated for `project_default`:

    ```bash title="Run on: OIM host"
    grep '^overall_status:' "$repo_manager_path/output/$OMNIA_PROJECT_NAME/repo_status.yml"
    grep '^overall_status:' "$image_build_manager_path/output/$OMNIA_PROJECT_NAME/build_status.yml"
    ```

6. After a deploy pipeline, confirm its child-pipeline summary and BSM job
   state, then inspect Orchestrator's output:

    ```bash title="Run on: OIM host"
    grep '^overall_status:' "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_status.yml"
    cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/provisioning_report.yml"
    ```

BuildStreaM does not write `pipeline_status.yml` or `catalog_manifest.yml` to
its project output directory. GitLab and BSM job state are the authoritative
pipeline results.

## Next steps

- [Update the Catalog](../Operations/build_stream/update_catalog.md) for subsequent
  catalog revisions.
- [Add Nodes](../Operations/build_stream/add_nodes.md) by updating the mapping and
  running the deploy pipeline again.
- [Retry Pipelines](../Operations/build_stream/retry_pipelines.md) after correcting
  a failed stage.
- [Clean Up Pipeline Resources](../Operations/build_stream/cleanup_operations.md)
  with the manual/API-only cleanup pipeline. It is never selected by a catalog
  or mapping file change.
- [Deploy Telemetry](../HowTo/Telemetry/deploy_telemetry.md) after a service
  Kubernetes cluster is available.

## Troubleshooting

- If the BuildStreaM input directory is missing, keep
  `OMNIA_PROJECT_NAME=project_default` and rerun OIM setup or the BuildStreaM
  `domain-init.sh`. The current executable role does not select another project.
- If the precheck fails, ensure `pulp`, `minio-server`, and `registry` are
  running and the two upstream credential files exist. The source precheck
  directs the operator to run `omnia.sh --prepare-base`.
- If configuration validation fails, use only the keys in the staged
  `build_stream_config.yml`, set `enable_build_stream: true`, provide both host
  addresses, and confirm both ports are available.
- If GitLab-host validation fails, disable SELinux, meet the configured CPU,
  memory, and storage minimums, and verify that the GitLab host can reach the
  BSM address.
- If the GitLab phase reports an inactive OIM service or missing certificate,
  verify `omnia_postgres.service`, `omnia_build_stream.service`,
  `playbook-watcher.service`, and
  `<OMNIA_DATA_PATH>/build_stream_ssl/ssl/bs_cert.pem`.
- If a commit does not select the expected pipeline, use the exact paths
  `catalog_rhel.json` for build and
  `input/orchestrator/pxe_mapping_file.csv` for deploy. Cleanup has no
  file-change trigger.
- If a module stage fails, open its GitLab job log, follow the BSM job and log
  path reported there, and inspect the corresponding module status contract.
- If restart has partial node failures, review
  `miscellaneous/failed_nodes.json`, correct the BMC or PXE issue, and follow
  the deploy-pipeline retry procedure.
- Do not cancel a running stage or start an overlapping pipeline against the
  same resources; either action can leave shared workflow state incomplete.
- See [BuildStreaM troubleshooting](../Troubleshooting/build_stream/build_stream.md)
  for detailed investigations.
