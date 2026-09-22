# Path C: Full Deployment

## Overview

Use this deployment path to provision Slurm and service Kubernetes clusters
and deploy Omnia Telemetry.

The workflow prepares the Omnia Infrastructure Manager (OIM), synchronizes
catalog content with Repository Manager, and builds the required node images
with Image Build Manager. After you provide a reviewed PXE mapping file (or
optionally use OME discovery to discover nodes), Orchestrator provisions the
Slurm and Kubernetes functional groups in the same run and generates the
combined inventory required by Telemetry. The final
stages deploy the enabled telemetry components and verify both clusters and
the Telemetry deployment.

## Full deployment workflow

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
      <div class="t">Build all cluster-node images</div>
      <div class="d">Create images for the selected cluster functional groups</div>
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
      <div class="t">Provision Slurm and service Kubernetes</div>
      <div class="d">Provision both clusters and generate their combined inventory</div>
      <div class="of-more"><a href="../HowTo/orchestrator/provision_nodes.html">Learn more: Provision nodes &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Configure and deploy Telemetry</div>
      <div class="d">Kubernetes sinks and enabled sources, including optional LDMS</div>
      <div class="of-more"><a href="../HowTo/Telemetry/deploy_telemetry.html">Learn more: Deploy Telemetry &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-s">
      <div class="t">Verify both clusters and Telemetry</div>
      <div class="d">Check Slurm, Kubernetes, and Telemetry health</div>
      <div class="of-more">Learn more: <a href="../HowTo/orchestrator/deploy_slurm.html#verification">Slurm &gt;&gt;</a> &middot; <a href="../HowTo/orchestrator/deploy_kubernetes.html#verification">Kubernetes &gt;&gt;</a> &middot; <a href="../HowTo/Telemetry/deploy_telemetry.html#verification">Telemetry &gt;&gt;</a></div>
    </div>
    <div class="of-c"></div>
    <div class="of-pill">Full Omnia platform ready</div>
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
- Select a catalog whose functional layers include Slurm and service
  Kubernetes. For an offline Telemetry deployment, ensure its package-manifest
  artifacts are available through the Pulp repository configured in
  `telemetry_packages.yml`. For guidance on updating catalogs, see
  [Update Catalog](../HowTo/main/update_catalog.md).
- Prepare the admin-network values required by Orchestrator. The deployment
  needs Slurm controller and compute groups plus service Kubernetes
  control-plane and worker groups. For configuration guidance, see
  [Network Specification](../Reference/Configuration/network_spec.md).
- Prepare the shared storage referenced by both cluster configurations.
  Telemetry requires the Kubernetes shared mount; LDMS also requires a shared
  path on the Slurm nodes. For configuration guidance, see
  [Storage Configuration](../Reference/Configuration/storage_config.md).
- Prepare the credentials and source-specific inputs for each enabled
  Telemetry source. Supported source configuration is provided for iDRAC,
  LDMS, PowerScale, UFM, VAST, OME, and SFM. For configuration guidance, see
  [Telemetry Configuration](../Reference/Configuration/telemetry_config.md).
- For OME discovery, have the OME address and credentials available. For
  automated PXE boot, the mapping must contain the applicable BMC information
  and Orchestrator must be able to collect the BMC credentials. For discovery
  guidance, see
  [Discovery](../HowTo/discovery/index.md).

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
    image_build_manager_path="${OMNIA_DATA_PATH}/image_build_manager"
    discovery_path="${OMNIA_DATA_PATH}/discovery"
    orchestrator_path="${OMNIA_DATA_PATH}/orchestrator"
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
    - The catalog JSON identified by `CATALOG_FILE_PATH` in the `omnia.env`
      file

    Ensure the selected catalog includes the Slurm and service Kubernetes
    functional layers and that every selected package source resolves through
    the configured RPM repository, container registry, or artifact URL.

    At minimum, this deployment path requires the following functional layers
    for the operating-system versions and architectures used in the PXE
    mapping:

    | Required functional layer | Required components |
    |---|---|
    | `slurm_control_node_rhel_<major>_<minor>_x86_64` | `slurm_custom_group` and `slurm_control_node_group` |
    | `slurm_node_rhel_<major>_<minor>_<arch>` | `slurm_custom_group` and `slurm_node_group` |
    | `service_kube_control_plane_rhel_<major>_<minor>_x86_64` | `service_k8s_common_group`, `service_k8s_telemetry_group`, `service_k8s_cluster_group`, and `service_kube_control_plane_group` |
    | `service_kube_node_rhel_<major>_<minor>_x86_64` | `service_k8s_common_group`, `service_k8s_telemetry_group`, and `service_kube_node_group` |

    The Slurm controller layer must match the controller operating-system
    version and use the x86_64 architecture. A compute layer must match each
    compute-node operating system and architecture in the mapping. Every mapped
    role must have a corresponding catalog layer and built image. The
    `slurm_custom_group` component is mandatory in both Slurm layers.

    For an all-x86_64 deployment, select `slurm_service_k8s_x86_64.json` or
    `slurm_service_k8s_x86_64_no_vast.json`. For a deployment with an x86_64
    Slurm controller, aarch64 Slurm compute nodes, and service Kubernetes on
    x86_64, select `slurm_service_k8s_combined.json` or
    `slurm_service_k8s_combined_no_vast.json`. These catalogs are available
    under both `src/main/samples/catalogs/10.0/` and
    `src/main/samples/catalogs/10.2/`. Do not create a catalog containing only
    the groups shown in this table; the shipped catalogs include the complete
    base OS, dependency, and package definitions required by the deployment.

    !!! warning

        Without the required service Kubernetes functional layers,
        Orchestrator does not enable service Kubernetes or generate the
        Kubernetes inventory required by Telemetry. Without the required
        Slurm functional layers, the Slurm cluster images cannot be built.

    Verify the selected catalog before continuing:

    ```bash title="Run on: OIM host"
    python3 - "$CATALOG_FILE_PATH" <<'PY'
    import json
    import sys

    try:
        with open(sys.argv[1], encoding="utf-8") as catalog_file:
            layers = json.load(catalog_file)["catalog"]["functionallayer"]
        for layer in layers:
            print(f"{layer['name']}\t{','.join(layer['components'])}")
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        print(f"Catalog validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
    PY
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
    Build Manager resolves image package sets from `CATALOG_FILE_PATH`. With
    `functional_groups_source: "config"`, also configure `package_groups.yml`
    in the same project input directory.

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

    Confirm that `overall_status` is `success` and that every Slurm and service
    Kubernetes functional group used in the PXE mapping has a corresponding
    image.

For configuration, build modes, and direct playbook alternatives, see
[Build Images](../HowTo/image_build_manager/build_images.md).

### 4. Provide the PXE mapping

Choose one method. Orchestrator consumes the reviewed file as
`$orchestrator_path/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv`.

=== "Discover nodes through OME"

    1. Configure `discovery_config.yml` and `network_spec.yml` under
       `$discovery_path/input/$OMNIA_PROJECT_NAME/`. Set `ome_ip` to a valid,
       non-loopback OME IPv4 address. For field definitions,
       see [Discovery Configuration](../Reference/Configuration/discovery_config.md)
       and [Network Specification](../Reference/Configuration/network_spec.md).

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

    Assign nodes to functional groups beginning with:

    - `slurm_control_node_rhel_<major>_<minor>_x86_64` for the Slurm controller.
    - `slurm_node_rhel_<major>_<minor>_<arch>` for Slurm compute nodes.
    - `service_kube_control_plane_rhel_<major>_<minor>_<arch>` for Kubernetes
      control-plane nodes.
    - `service_kube_node_rhel_<major>_<minor>_<arch>` for Kubernetes worker
      nodes.

    Login and login/compiler groups are optional. The LDMS precheck requires at
    least one populated Slurm controller group and one populated Slurm compute
    group when `telemetry_sources.ldms.metrics_enabled: true`.

    The following example uses the mixed-architecture functional groups in the
    default RHEL 10.0 catalog:

    ```csv title="Example: pxe_mapping_file.csv"
    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    slurm_control_node_rhel_10_0_x86_64,grp0,FULL001,,nid001,02:00:00:00:21:01,172.16.107.71,02:00:00:00:22:01,172.17.107.71,,
    service_kube_control_plane_rhel_10_0_x86_64,grp3,FULL002,,nid002,02:00:00:00:21:02,172.16.107.72,02:00:00:00:22:02,172.17.107.72,,
    service_kube_control_plane_rhel_10_0_x86_64,grp3,FULL003,,nid003,02:00:00:00:21:03,172.16.107.73,02:00:00:00:22:03,172.17.107.73,,
    service_kube_control_plane_rhel_10_0_x86_64,grp3,FULL004,,nid004,02:00:00:00:21:04,172.16.107.74,02:00:00:00:22:04,172.17.107.74,,
    service_kube_node_rhel_10_0_x86_64,grp1,FULL005,,nid005,02:00:00:00:21:05,172.16.107.75,02:00:00:00:22:05,172.17.107.75,,
    slurm_node_rhel_10_0_aarch64,grp1,FULL006,FULL005,nid006,02:00:00:00:21:06,172.16.107.76,02:00:00:00:22:06,172.17.107.76,InfiniBand.Slot.7-1,192.168.0.111
    login_compiler_node_rhel_10_0_aarch64,grp8,FULL007,,nid007,02:00:00:00:21:07,172.16.107.77,02:00:00:00:22:07,172.17.107.77,InfiniBand.PCIe.Slot.8-1,192.168.0.112
    login_node_rhel_10_0_x86_64,grp9,FULL008,,nid008,02:00:00:00:21:08,172.16.107.78,02:00:00:00:22:08,172.17.107.78,,
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
        in the selected catalog and successful image-build output. If another
        RHEL version or architecture is selected, use its exact catalog group
        names.

For the complete mapping schema and OME procedure, see
[Discover Nodes](../HowTo/discovery/discover_nodes.md) and
[Create a Mapping File](../HowTo/discovery/create_mapping_file.md).

### 5. Configure and run Orchestrator

1. Review the staged files under
   `$orchestrator_path/input/$OMNIA_PROJECT_NAME/`:

    | Input | Full-deployment requirement |
    |---|---|
    | `orchestrator_config.yml` | Confirm the mapping, Repo Manager, Image Build Manager, catalog, and PXE-boot settings. |
    | `network_spec.yml` | Configure the OIM interface, admin subnet, DHCP range, router, and any required additional or InfiniBand networks. |
    | `omnia_config.yml` | Configure `slurm_cluster` and select exactly one `service_k8s_cluster` entry with `deployment: true`. Configure their storage references and the Kubernetes network settings, including `pod_external_ip_range`. Set `enable_powerscale_csi: true` only when CSI is required; both CSI file paths then become mandatory. |
    | `high_availability_config.yml` | Provide a `service_k8s_cluster_ha` entry whose `cluster_name` matches the selected Kubernetes cluster and a `virtual_ip_address` in the admin NIC subnet range. |
    | `storage_config.yml` | Define every mount named by the Slurm and Kubernetes cluster entries. The applicable storage must be reachable from the OIM where configured. |
    | `pxe_mapping_file.csv` | Assign nodes to the Slurm and service Kubernetes functional groups and ensure corresponding images exist in `build_status.yml`. |
    | `security_config.yml` | Configure this file when the selected catalog enables OpenLDAP. |

    Orchestrator derives Slurm and Kubernetes support and cluster OS metadata
    from the catalog.

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
    prepares OpenCHAMI and catalog-selected services, provisions both cluster
    types, validates provisioning, and performs iDRAC PXE boot when
    `enable_pxe_boot: true`. Do not run a second PXE-boot command after this
    flow unless you intentionally need to repeat that operation.

3. Confirm that Orchestrator generated the inventory Telemetry consumes:

    ```text
    $orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_inventory.yml
    ```

    The file must contain `kube_vip_group`, populated functional groups
    beginning with `service_kube_control_plane` and `service_kube_node`, and,
    for LDMS, populated groups beginning with `slurm_control_node` and
    `slurm_node`.

For detailed cluster configuration, see
[Configure Slurm](../HowTo/orchestrator/configure_slurm.md),
[Deploy Service Kubernetes](../HowTo/orchestrator/deploy_kubernetes.md),
[Configure Kubernetes HA](../HowTo/orchestrator/configure_kubernetes_ha.md),
[Configure Storage](../HowTo/orchestrator/configure_storage.md), and
[Provision Nodes](../HowTo/orchestrator/provision_nodes.md).

### 6. Configure and run Telemetry

1. Review all three staged files under
   `$telemetry_path/input/$OMNIA_PROJECT_NAME/`:

    | Input | Full-deployment requirement |
    |---|---|
    | `telemetry_config.yml` | Set `cluster_inventory` to Orchestrator's generated inventory. Enable only available sources and configure their source-specific values. |
    | `telemetry_storage_config.yml` | Size replicas, CPU, memory, and persistent storage for the selected sinks, sources, and bridges. |
    | `telemetry_packages.yml` | Select `online` or `offline`, configure the repository URL when offline, and align both cluster mount paths with Orchestrator storage. |

2. In `telemetry_config.yml`, use the generated Orchestrator inventory. Resolve
   its absolute path for the active project:

    ```bash title="Run on: OIM host"
    printf '%s\n' "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_inventory.yml"
    ```

    Copy the printed path into the configuration:

    ```yaml title="telemetry_config.yml"
    cluster_inventory: "<absolute path printed above>"
    ```

3. To collect Slurm-node metrics through LDMS and route them from Kafka to
   VictoriaMetrics, keep the source and bridge enabled:

    ```yaml title="telemetry_config.yml — edit the existing keys"
    telemetry_sources:
      ldms:
        metrics_enabled: true
        collection_targets:
          - "kafka"

    telemetry_bridges:
      vector_ldms:
        metrics_enabled: true
    ```

    Do not replace the full source file with this excerpt. Retain every key.
    The Vector-LDMS bridge may be disabled when LDMS data should remain only in
    Kafka. Enable other Telemetry sources only after completing their required
    configuration. When OME metrics or logs are disabled, disable the
    corresponding `vector_ome` fields as well.

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

5. In `telemetry_packages.yml`:

    - Set `k8s_cluster_mount` to the shared mount path available on the service
      Kubernetes nodes.
    - Set `slurm_cluster_mount` to the shared mount path available on the Slurm
      nodes when LDMS is enabled.
    - For the default offline mode, set `repo_url` to the Pulp content base
      containing the packages named in the Telemetry package manifest. For
      online mode, leave `repo_url` empty.

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
    worker readiness, non-Telemetry pod health, and applicable source
    prerequisites. When LDMS is enabled, it also requires Slurm controller and
    compute groups and checks `slurmctld` and `slurmd` on those nodes.

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

2. Review the combined provisioning summary and inventory:

    ```bash title="Run on: OIM host"
    cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/provisioning_report.yml"
    cat "$orchestrator_path/output/$OMNIA_PROJECT_NAME/orchestrator_inventory.yml"
    ```

3. On the Slurm controller, verify the services and node state:

    ```bash title="Run on: Slurm controller"
    systemctl is-active slurmctld
    systemctl is-active slurmdbd
    sinfo
    ```

4. On each Slurm compute node, verify the node daemon:

    ```bash title="Run on: Slurm compute node"
    systemctl is-active slurmd
    ```

5. On the first Kubernetes control-plane node, confirm node and workload state:

    ```bash title="Run on: first Kubernetes control-plane node"
    kubectl get nodes -o wide
    kubectl get pods --all-namespaces -o wide
    ```

    All mapped Kubernetes nodes should appear. Workloads should reach
    `Running` or `Completed`.

6. On the Kubernetes VIP, inspect the Telemetry namespace:

    ```bash title="Run on: Kubernetes VIP"
    kubectl get pods -n telemetry
    ```

    In `telemetry_status.yml`, confirm `overall_status: success` and verify
    that every requested sink, source, and bridge is `deployed`. Components
    disabled in `telemetry_config.yml` are reported as `skipped`. When LDMS is
    enabled, also review `deploy_unreachable_nodes.ldms`.

7. Verify the enabled data paths with the source-specific guides on the
   [Telemetry landing page](../HowTo/Telemetry/index.md).

## Next steps

- [Configure Slurm](../HowTo/orchestrator/configure_slurm.md) to supply or
  merge custom Slurm configuration files.
- [Configure Slurm with GPUs](../HowTo/orchestrator/slurm_with_gpu.md) when the
  selected catalog and compute nodes include NVIDIA GPU support.
- [Set up NVIDIA HPC SDK](../HowTo/orchestrator/setup_nvhpc_sdk.md) when the
  catalog includes the required SDK content.
- Use the source-specific guides on the
  [Telemetry landing page](../HowTo/Telemetry/index.md) to configure and verify
  additional available data sources.
- [Deploy the PowerScale CSI driver](../HowTo/orchestrator/deploy_powerscale_csi.md)
  when `enable_powerscale_csi: true` is set on the deployed
  `service_k8s_cluster` entry in `omnia_config.yml` and its input files have
  been prepared. The catalog supplies the required artifacts but does not
  enable the driver.
- Use [Add Nodes](../Operations/add_nodes.md) and
  [Remove Slurm Nodes](../Operations/remove_slurm_nodes.md) for supported
  node lifecycle changes.
- Use [BuildStreaM Deployment](buildstream_deployment.md) when the separate
  BuildStreaM module is required.

## Troubleshooting

- If a later module reports a missing upstream contract, verify that the
  preceding status file exists and has `overall_status: success`.
- If Slurm or Kubernetes configuration is skipped, verify that the catalog
  contains the corresponding functional layers and that the mapping includes
  the required functional-group prefixes.
- If image validation fails, compare every mapping functional group with
  `functional_group_images` in `build_status.yml`.
- If physical nodes do not PXE boot, confirm `enable_pxe_boot: true`, review
  `failed_nodes.json`, and inspect `orchestrator_status.yml` in the
  Orchestrator project output directory.
- If Telemetry cannot resolve the Kubernetes VIP, verify that
  `cluster_inventory` names the generated `orchestrator_inventory.yml` and
  that the file contains `all.children.kube_vip_group.hosts`.
- If the LDMS precheck fails, verify that the inventory contains populated
  `slurm_control_node` and `slurm_node` groups, that the nodes are reachable,
  and that `slurmctld` and `slurmd` are active where required.
- If Telemetry input validation fails, correct all reported schema and
  cross-field errors across the three Telemetry input files. Source and bridge
  enablement must agree.
- If a Telemetry pod is in an error state, run
  `kubectl logs -n telemetry <pod-name>` on the Kubernetes VIP and correct the
  reported image, secret, storage, or source configuration problem.
- Review module logs under `/var/log/omnia/<domain>/` and project logs under
  `<OMNIA_DATA_PATH>/<domain>/log/`.
- See [Slurm troubleshooting](../Troubleshooting/orchestrator/slurm.md),
  [Kubernetes troubleshooting](../Troubleshooting/orchestrator/kubernetes.md),
  and [Telemetry deployment troubleshooting](../HowTo/Telemetry/deploy_telemetry.md#troubleshooting)
  for component-specific investigations.
