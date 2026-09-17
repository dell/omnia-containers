# Path B: Kubernetes and Telemetry

## Overview

Use this deployment path to provision a service Kubernetes cluster and deploy
Omnia Telemetry without deploying Slurm.

The workflow prepares the Omnia Infrastructure Manager (OIM), synchronizes
catalog content with Repository Manager, and builds the Kubernetes node images
with Image Build Manager. After you provide a reviewed PXE mapping,
Orchestrator provisions the cluster and generates the inventory required by
Telemetry. The final stages deploy the enabled telemetry components and verify
the Kubernetes cluster and Telemetry deployment.

## Kubernetes and Telemetry deployment workflow

<div class="of-wrap">
<div class="of-root">
  <div class="of-hdr">
    <div class="of-h2">Required module sequence and output handoffs</div>
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
      <div class="t">Synchronize catalog content</div>
      <div class="d">Make catalog repositories available for image builds</div>
      <div class="of-more"><a href="../HowTo/repo_manager/configure_repos.html">Learn more: Repository Manager &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Build Kubernetes node images</div>
      <div class="d">Create images for the selected Kubernetes functional groups</div>
      <div class="of-more"><a href="../HowTo/image_build_manager/build_images.html">Learn more: Build OS images &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Provide the PXE mapping</div>
      <div class="d">OME Discovery or a manual CSV</div>
      <div class="of-more"><a href="../HowTo/discovery/create_mapping_file.html">Learn more: Create the PXE mapping &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Provision service Kubernetes</div>
      <div class="d">Provision the cluster and generate its inventory</div>
      <div class="of-more"><a href="../HowTo/orchestrator/deploy_kubernetes.html">Learn more: Deploy Kubernetes &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Select and deploy telemetry sources</div>
      <div class="d">Deploy the enabled sources and Kubernetes sinks</div>
      <div class="of-more"><a href="../HowTo/Telemetry/deploy_telemetry.html">Learn more: Deploy Telemetry &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Verify Kubernetes and Telemetry</div>
      <div class="d"><code>kubectl get nodes</code> and telemetry pod state</div>
      <div class="of-more">Learn more: <a href="../HowTo/orchestrator/deploy_kubernetes.html#verification">Kubernetes &gt;&gt;</a> &middot; <a href="../HowTo/Telemetry/deploy_telemetry.html#verification">Telemetry &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-pill">Kubernetes telemetry platform ready</div>
  </div>
</div>
</div>

## Prerequisites

- Use an Omnia source checkout on the OIM.
- For the Telemetry module, use Python 3.12 or later, Ansible 2.20 or later,
  and RHEL 10.x on the OIM.
- Set `SYSTEM_ADMIN_NIC_IPV4` in `src/main/omnia.env` to an IPv4 address
  assigned to an OIM interface. Review the project name, shared data path,
  hostname, domain, Omnia version, and catalog path in the same file.
- Select a catalog whose functional layers include service Kubernetes. For an
  offline Telemetry deployment, ensure its package manifest artifacts are
  available through the Pulp repository configured in
  `telemetry_packages.yml`.
- Prepare the admin-network values required by Orchestrator and a shared NFS
  mount for Kubernetes configuration and Telemetry packages.
- Prepare at least one supported Telemetry source: iDRAC, PowerScale, UFM,
  VAST, or OME. This path intentionally excludes LDMS because the source
  requires Slurm nodes in the Orchestrator inventory.
- For OME discovery, have the OME address and credentials available. For
  automated PXE boot, the mapping must contain the applicable BMC information
  and Orchestrator must be able to collect the BMC credentials.

## Procedure

### 1. Configure and set up the OIM

1. Edit the environment configuration from the Omnia source tree:

    ```bash title="Run on: OIM host"
    cd src/main
    vi omnia.env
    ```

2. Create the shared virtual environment, install module dependencies, stage
   the module input templates, and copy the catalog samples:

    ```bash title="Run on: OIM host"
    ./omnia.sh --setup-venv
    ```

    This command runs each selected module's `domain-init.sh`. Do not run the
    individual initialization scripts again unless a module was skipped or
    setup used `--deps-only`.

3. Load the installed environment and activate the shared virtual environment
   in the current shell:

    ```bash title="Run on: OIM host"
    source /etc/profile.d/omnia-env.sh
    source "$OMNIA_DATA_PATH/activate-omnia.sh"
    repo_manager_path="${OMNIA_DATA_PATH}/repo_manager"
    image_build_manager_path="${IMAGE_BUILD_MANAGER_DATA_PATH:-${OMNIA_DATA_PATH}/image_build_manager}"
    discovery_path="${OMNIA_DATA_PATH}/discovery"
    orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
    telemetry_path="${OMNIA_DATA_PATH}/telemetry"
    ```

    Run these commands in each new shell before using the paths based on
    environment variables in this guide.

For all environment and setup options, see
[Configure the environment](../HowTo/main/configure_environment.md) and
[Set up the OIM](../HowTo/main/setup_oim.md).

### 2. Configure and run Repository Manager

1. Review these staged inputs:

    - `$repo_manager_path/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml`
    - `$repo_manager_path/input/$OMNIA_PROJECT_NAME/repo_manager_endpoint_config.yml`
    - The catalog JSON identified by `CATALOG_FILE_PATH`

    Ensure the selected catalog includes the service Kubernetes functional
    layers and that each selected package source resolves through the
    configured RPM repository, container registry, or artifact URL.

    At minimum, this Kubernetes and Telemetry path requires both of these
    x86_64 functional layers for the selected operating-system version:

    | Required functional layer | Required Kubernetes components |
    |---|---|
    | `service_kube_control_plane_rhel_<major>_<minor>_x86_64` | `service_k8s_common_group`, `service_k8s_telemetry_group`, `service_k8s_cluster_group`, and `service_kube_control_plane_group` |
    | `service_kube_node_rhel_<major>_<minor>_x86_64` | `service_k8s_common_group`, `service_k8s_telemetry_group`, and `service_kube_node_group` |

    For example, an RHEL 10.2 deployment requires
    `service_kube_control_plane_rhel_10_2_x86_64` and
    `service_kube_node_rhel_10_2_x86_64`. Select the shipped
    `src/main/samples/catalogs/10.2/service_k8s_x86_64.json` catalog for this
    path; use the file under `10.0/` for RHEL 10.0. Do not create a catalog
    containing only the groups shown in this table; the shipped catalog
    includes the complete base OS, dependency, and package definitions.

    !!! warning

        Without the service Kubernetes functional layers, Orchestrator does
        not enable service Kubernetes or generate the Kubernetes inventory
        required by this Telemetry deployment path.

    Verify the selected catalog before continuing:

    ```bash title="Run on: OIM host"
    jq -r '.catalog.functionallayer[] | [.name, (.components | join(","))] | @tsv' \
      "$CATALOG_FILE_PATH"
    ```

2. Run the complete standard Repo Manager flow:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml
        ```

    The flow validates the environment and inputs, collects or reuses
    credentials, deploys Pulp, synchronizes the selected content, and writes:

    ```text
    $repo_manager_path/output/$OMNIA_PROJECT_NAME/repo_status.yml
    ```

    Do not continue until `overall_status` is `success`.

For the configuration and credential procedure, see
[Create Local Repositories](../HowTo/repo_manager/configure_repos.md).

### 3. Configure and run Image Build Manager

1. Review the staged `image_build_config.yml` under:

    ```text
    $image_build_manager_path/input/$OMNIA_PROJECT_NAME/
    ```

    Its `repo_manager_output_path` must identify the successful
    `repo_status.yml`. With `functional_groups_source: "catalog"`, the Image
    Build Manager resolves the image package sets from `CATALOG_FILE_PATH`.
    With `functional_groups_source: "config"`, also configure
    `package_groups.yml` in the same project input directory.

2. Run the complete standard image-build flow:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run image_build_manager
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
        ansible-playbook image_build_manager.yml
        ```

    The flow validates the configuration, collects or reuses the applicable
    S3 and aarch64 credentials, prepares MinIO when selected, deploys the local
    registry, builds the selected functional-group images, and writes:

    ```text
    $image_build_manager_path/output/$OMNIA_PROJECT_NAME/build_status.yml
    ```

    Confirm that `overall_status` is `success` and that every service
    Kubernetes functional group used in the PXE mapping has a corresponding
    image.

For configuration, build modes, and direct playbook alternatives, see
[Build Images](../HowTo/image_build_manager/build_images.md).

### 4. Provide the PXE mapping

Choose one method. Orchestrator consumes the reviewed file as
`$orchestrator_path/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv`.

=== "Discover nodes through OME"

    1. Configure `discovery_config.yml` and `network_spec.yml` under
       `$discovery_path/input/$OMNIA_PROJECT_NAME/`. Set
       `enable_bmc_discovery: true` and provide `ome_ip`.

    2. Run Discovery:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run discovery
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/discovery/playbooks
            ansible-playbook discovery.yml
            ```

    3. Review the timestamped mapping and discovery report under
       `$discovery_path/output/$OMNIA_PROJECT_NAME/`. Then copy the
       latest mapping to the Orchestrator input directory. With the installed
       environment active, run:

        ```bash title="Run on: OIM host"
        cp "$discovery_path/output/$OMNIA_PROJECT_NAME/bmc_pxe_mapping_file.csv" \
          "$orchestrator_path/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv"
        ```

    Discovery intentionally leaves this handoff to the operator so that node
    hostnames, functional groups, and group assignments can be reviewed before
    provisioning.

=== "Create the mapping manually"

    Edit the staged Orchestrator mapping directly:

    ```bash title="Run on: OIM host"
    vi "$orchestrator_path/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv"
    ```

    Preserve the source-defined header:

    ```text
    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    ```

    Assign the intended control-plane and worker nodes to functional groups
    beginning with `service_kube_control_plane` and `service_kube_node`. Do not
    add Slurm functional groups for this deployment path.

For the complete mapping schema and OME procedure, see
[Discover Nodes](../HowTo/discovery/discover_nodes.md) and
[Create a Mapping File](../HowTo/discovery/create_mapping_file.md).

### 5. Configure and run Orchestrator

1. Review the staged files under
   `$orchestrator_path/input/$OMNIA_PROJECT_NAME/`:

    | Input | Kubernetes requirement |
    |---|---|
    | `orchestrator_config.yml` | Confirm the mapping, Repo Manager, Image Build Manager, catalog, and PXE-boot settings. |
    | `network_spec.yml` | Configure the OIM interface, admin subnet, DHCP range, router, and any optional additional network. |
    | `omnia_config.yml` | Select exactly one `service_k8s_cluster` entry with `deployment: true`; configure its cluster networks, CNI, and storage name. Set `enable_powerscale_csi: true` only when CSI is required; both CSI file paths then become mandatory. |
    | `high_availability_config.yml` | Provide a `service_k8s_cluster_ha` entry whose `cluster_name` matches the selected Kubernetes cluster. |
    | `storage_config.yml` | Define the NFS mount named by `nfs_storage_name` and make it writable from the OIM where configured. |
    | `pxe_mapping_file.csv` | Assign the intended nodes to service Kubernetes functional groups and ensure corresponding images exist in `build_status.yml`. |
    | `security_config.yml` | Configure this file when the selected catalog enables OpenLDAP. |
    | [`additional_cloud_init.yml`](../Reference/Configuration/additional_cloud_init.md) (optional) | Add validated common and per-functional-group `write_files` and `runcmd` directives during provisioning. Set `additional_cloud_init_config_file` in `orchestrator_config.yml` to this file's absolute path to enable it. |
    | [`set_pxe_boot_config.yml`](../Reference/Configuration/set_pxe_boot_config.md) (optional) | Override server restart behavior, the PXE boot mode and target, and node-registration verification timing. When omitted, Orchestrator uses the documented defaults. |

    Orchestrator derives Kubernetes support and cluster OS metadata from the
    catalog.

2. Run the complete standard Orchestrator flow:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml
        ```

    The untagged flow performs prechecks, collects or reuses credentials,
    prepares OpenCHAMI and catalog-selected services, provisions the service
    Kubernetes groups, validates provisioning, and performs iDRAC PXE boot
    when `enable_pxe_boot: true`. Do not run a second PXE-boot command after
    this flow unless you intentionally need to repeat that operation.

3. Confirm that Orchestrator generated the inventory Telemetry consumes:

    ```text
    $orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_inventory.yaml
    ```

    The file must contain `kube_vip_group` and populated functional groups
    beginning with `service_kube_control_plane` and `service_kube_node`.

For the detailed Kubernetes and provisioning settings, see
[Deploy Service Kubernetes](../HowTo/orchestrator/deploy_kubernetes.md),
[Configure Kubernetes HA](../HowTo/orchestrator/configure_kubernetes_ha.md),
[Configure Storage](../HowTo/orchestrator/configure_storage.md), and
[Provision Nodes](../HowTo/orchestrator/provision_nodes.md).

### 6. Configure and run Telemetry

1. Review all three staged files under
   `$telemetry_path/input/$OMNIA_PROJECT_NAME/`:

    | Input | Kubernetes-only requirement |
    |---|---|
    | `telemetry_config.yml` | Set `cluster_inventory` to Orchestrator's generated inventory. Enable only sources available in this environment and configure their source-specific values. |
    | `telemetry_storage_config.yml` | Size the replicas, CPU, memory, and persistent storage for the selected sinks, sources, and bridges. |
    | `telemetry_packages.yml` | Select `online` or `offline`, configure the repository URL when offline, confirm `k8s_cluster_mount`, and review package and image references. |

2. In `telemetry_config.yml`, use the generated Orchestrator inventory. Resolve
   its absolute path for the active project:

    ```bash title="Run on: OIM host"
    printf '%s\n' "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_inventory.yaml"
    ```

    Copy the printed path into the configuration:

    ```yaml title="telemetry_config.yml"
    cluster_inventory: "<absolute path printed above>"
    ```

3. Disable LDMS and its Vector bridge because this path has no Slurm nodes:

    ```yaml title="telemetry_config.yml — edit the existing keys"
    telemetry_sources:
      ldms:
        metrics_enabled: false

    telemetry_bridges:
      vector_ldms:
        metrics_enabled: false
    ```

    Do not replace the full source file with this excerpt. Retain every key and
    set the `metrics_enabled` and `logs_enabled` fields to `false` for every
    other source that is not available or not configured. When OME metrics or
    logs are disabled, disable the corresponding `vector_ome` fields as well.

4. Complete the values required by each enabled source. In particular, when
   iDRAC is enabled, set `idrac_telemetry_configurations.bmc_group_data_path`
   to the `bmc_group_data.csv` produced by Orchestrator. Resolve the path for
   the active project and copy the printed value into that field:

    ```bash title="Run on: OIM host"
    printf '%s\n' "$orchestrator_path/output/$OMNIA_PROJECT_NAME/bmc_group_data.csv"
    ```

    The Telemetry credential role creates encrypted
    `telemetry_credentials.yml` and prompts only for empty credentials needed
    by the enabled sources.

5. In `telemetry_packages.yml`, keep `k8s_cluster_mount` aligned with the NFS
   mount configured for service Kubernetes. For the default offline mode, set
   `repo_url` to the Pulp content base that contains the packages named in the
   Telemetry package manifest. For online mode, leave `repo_url` empty.

6. Run the Telemetry environment precheck:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run telemetry --tags precheck
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
        ansible-playbook telemetry.yml --tags precheck
        ```

    The precheck validates access to the Kubernetes VIP, control-plane and
    worker readiness, non-Telemetry pod health, and the applicable PowerScale
    prerequisites. With LDMS disabled, its Slurm checks are skipped.

7. Run the complete standard Telemetry flow:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run telemetry
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
        ansible-playbook telemetry.yml
        ```

    The untagged flow validates the three runtime input files, deploys the
    sinks required by the selected collection targets, deploys each enabled
    source and bridge, checks pod state, and writes:

    ```text
    $telemetry_path/output/$OMNIA_PROJECT_NAME/telemetry_status.yml
    ```

For source-specific configuration and verification guides, see the
[Telemetry landing page](../HowTo/Telemetry/index.md).

## Verification

1. Confirm that all four module contracts report success:

    ```bash title="Run on: OIM host"
    grep '^overall_status:' "$repo_manager_path/output/$OMNIA_PROJECT_NAME/repo_status.yml"
    grep '^overall_status:' "$image_build_manager_path/output/$OMNIA_PROJECT_NAME/build_status.yml"
    grep '^overall_status:' "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_status.yml"
    grep '^overall_status:' "$telemetry_path/output/$OMNIA_PROJECT_NAME/telemetry_status.yml"
    ```

2. Review the provisioning summary and generated inventory:

    ```bash title="Run on: OIM host"
    cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/provisioning_report.yml"
    cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_inventory.yaml"
    ```

3. On the first Kubernetes control-plane node, confirm node and workload state:

    ```bash title="Run on: first Kubernetes control-plane node"
    kubectl get nodes -o wide
    kubectl get pods --all-namespaces -o wide
    ```

    All mapped nodes should appear. Workloads should reach `Running` or
    `Completed`.

4. On the Kubernetes VIP, inspect the Telemetry namespace:

    ```bash title="Run on: Kubernetes VIP"
    kubectl get pods -n telemetry
    ```

    In `telemetry_status.yml`, confirm `overall_status: success` and verify
    that every requested sink, source, and bridge is `deployed`. Components
    disabled in `telemetry_config.yml` are reported as `skipped`.

## Next steps

- Use the source-specific guides on the
  [Telemetry landing page](../HowTo/Telemetry/index.md) to configure and verify
  additional available data sources.
- [Export Kafka connection details](../HowTo/Telemetry/configure_external_kafka.md)
  when an external producer or consumer needs access.
- [Export VictoriaMetrics connection details](../HowTo/Telemetry/configure_external_victoria.md)
  or [VictoriaLogs connection details](../HowTo/Telemetry/configure_external_victoria_logs.md)
  for external queries and integrations.
- [Deploy the PowerScale CSI driver](../HowTo/orchestrator/deploy_powerscale_csi.md)
  when `enable_powerscale_csi: true` is set on the deployed
  `service_k8s_cluster` entry in `omnia_config.yml` and its input files have
  been prepared. The catalog supplies the required artifacts but does not
  enable the driver.
- Use [Add Nodes](../Operations/add_nodes.md) for supported Kubernetes
  node additions with matching source templates and image artifacts.
- Follow [Full Deployment](full_deployment.md) when adding a Slurm cluster and
  LDMS to the environment.

## Troubleshooting

- If a later module reports a missing upstream contract, verify that the
  preceding status file exists and has `overall_status: success`.
- If Kubernetes configuration is skipped, verify that the catalog contains a
  service Kubernetes functional layer and that the mapping includes both
  `service_kube_control_plane` and `service_kube_node` functional groups.
- If image validation fails, compare every mapping functional group with
  `functional_group_images` in `build_status.yml`.
- If physical nodes do not PXE boot, confirm `enable_pxe_boot: true`, review
  `failed_nodes.json`, and inspect `orchestrator_status.yml` in the
  Orchestrator project output directory.
- If Telemetry cannot resolve the Kubernetes VIP, verify that
  `cluster_inventory` names the generated `orchestrator_inventory.yaml` and
  that the file contains `all.children.kube_vip_group.hosts`.
- If Telemetry input validation fails, correct all reported schema and
  cross-field errors across the three Telemetry input files. Source and bridge
  enablement must agree; for example, a Vector-OME metrics bridge requires OME
  metrics to be enabled.
- If a Telemetry pod is in an error state, run
  `kubectl logs -n telemetry <pod-name>` on the Kubernetes VIP and correct the
  reported image, secret, storage, or source configuration problem.
- Review module logs under `/var/log/omnia/<domain>/` and project logs under
  `<OMNIA_DATA_PATH>/<domain>/log/`.
- See [Kubernetes troubleshooting](../Troubleshooting/orchestrator/kubernetes.md)
  and [Telemetry deployment troubleshooting](../HowTo/Telemetry/deploy_telemetry.md#troubleshooting)
  for component-specific investigations.
