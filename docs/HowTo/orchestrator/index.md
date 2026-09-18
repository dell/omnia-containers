# Orchestrator

## Overview

Orchestrator manages the post-discovery lifecycle for an Omnia cluster. It
deploys OpenCHAMI and, when selected by the catalog, OpenLDAP; converts the PXE
mapping into functional groups; registers nodes in OpenCHAMI; creates boot and
cloud-init configuration; prepares Kubernetes and Slurm configuration; and can
start physical servers through Dell iDRAC PXE boot.

Orchestrator does not discover hardware, synchronize repositories, or build
node images. It consumes the outputs of those workflows.

```text
repo_status.yml + catalog JSON       build_status.yml       pxe_mapping_file.csv
              \                          |                          /
               \_________________________|_________________________/
                                           |
                                           v
                   deploy services -> provision -> optional PXE boot
                                           |
                                           v
                    status, inventory, and failure reports
```

## Prerequisites

- Run Orchestrator on the Omnia Infrastructure Manager (OIM).
- Install the dependencies declared by the module: `ansible-core>=2.20`,
  Python packages from `requirements.txt`, and the Ansible collections from
  `requirements.yml`.
- Before running a flow that consumes repository content, complete Repo Manager
  and provide a successful `repo_status.yml` and its public certificate. These
  flows are `precheck`, `provision`, `execute`, `pxeboot`, `upgrade`, and an
  untagged full run.
- Provide the selected deployment catalog for `precheck`, `credentials`,
  `prepare`, `deploy`, `provision`, `execute`, `validate-deployment`, and an
  untagged full run. Orchestrator uses `catalog_file_path` from
  `orchestrator_config.yml`, when configured; otherwise, it uses
  `CATALOG_FILE_PATH`, or `$OMNIA_DATA_PATH/catalog/catalog_rhel.json`.
- Before running `precheck`, `provision`, `execute`, or an untagged full run,
  complete Image Build Manager and provide a successful `build_status.yml`
  containing images for every functional group in the mapping.
- Place the discovery-produced PXE mapping in the active project's
  Orchestrator input directory, or configure an override in
  `orchestrator_config.yml`.
- Configure the OIM environment, including `SYSTEM_ADMIN_NIC_IPV4`,
  `SYSTEM_HOSTNAME`, `SYSTEM_DOMAIN_NAME`, `OMNIA_DATA_PATH`, the optional
  `ORCHESTRATOR_DATA_PATH`, and `OMNIA_PROJECT_NAME`. `OMNIA_DATA_PATH`
  defaults to `/opt/omnia`, and `OMNIA_PROJECT_NAME` defaults to
  `project_default`. When `ORCHESTRATOR_DATA_PATH` is unset, the Orchestrator
  root is the `orchestrator` directory beneath `OMNIA_DATA_PATH`.
- Review the
  [Orchestrator configuration reference](../../Reference/Configuration/orchestrator_config.md)
  and provide the inputs required by the selected workflow. The `validate`
  workflow checks the project configuration and resolved PXE mapping; it does
  not require credentials, a catalog, or upstream status files.

### Input summary

Project inputs are staged in the active project's Orchestrator input
directory. Upstream outputs remain in the producing domain unless a path
override is configured.

| Input | Requirement | Purpose |
|---|---|---|
| `orchestrator_config.yml` | Required | Selects upstream paths and provisioning, DNS, kernel boot parameters, cloud-init, catalog, DCGM, and PXE behavior. |
| `network_spec.yml` | Required | Defines the admin network and optional relay and InfiniBand networks. |
| `pxe_mapping_file.csv` | Required at the default or configured override path | Maps nodes to functional groups and supplies admin and BMC identities. |
| `omnia_config.yml` | Required | Defines Slurm and service-Kubernetes clusters, optional bolt-on overrides, and storage references. Retain both top-level arrays; use `[]` for an unselected workload. |
| `storage_config.yml` | Conditional | Defines storage mounts used by selected clusters. |
| `security_config.yml` | Required | Supplies security settings for Orchestrator services, including the LDAP connection type and its TLS or SSL behavior. |
| `high_availability_config.yml` | Required for service Kubernetes | Defines the Kubernetes control-plane virtual IP. |
| Additional cloud-init YAML | Optional | Adds validated common and per-functional-group `write_files` and `runcmd` directives during provisioning. Set its absolute path in `additional_cloud_init_config_file`; `additional_cloud_init.yml` is the example filename. |
| `set_pxe_boot_config.yml` | Optional for PXE boot | Overrides node-registration timing and PXE-boot settings. |
| `orchestrator_credentials.yml` and `.orchestrator_credentials_key` | Created or updated by `credentials` and `prepare`; required by later credential-consuming flows | Store encrypted provisioning, BMC, Slurm, OpenLDAP, and PowerScale credentials and the Vault key. |
| `repo_status.yml` | Required for precheck, provision, execute, PXE boot, upgrade, and full runs | Supplies repository URLs, including the PowerScale CSI artifacts, and the Repo Manager public certificate. |
| `build_status.yml` | Required for precheck, provisioning, execute, and full runs | Supplies functional-group images and S3 endpoint information. The standalone `pxeboot` phase does not read this file. |
| Catalog JSON | Required for precheck, credentials, prepare, deploy, provision, execute, validate-deployment, and full runs | Supplies OS metadata and enables supported services and software. |

### Catalog feature selection

Orchestrator derives the following feature support from catalog names:

| Feature | Catalog entry | Selection rule |
|---|---|---|
| Kubernetes | `catalog.functionallayer[].name` | The name contains `kube` or `k8s`. |
| Slurm | `catalog.functionallayer[].name` | The name contains `slurm`. |
| OpenLDAP | `catalog.groups` name | The name contains `openldap`. |
| UCX | `catalog.groups` name | The name contains `ucx`. |
| OpenMPI | `catalog.groups` name | The name contains `openmpi`. |

These catalog name matches are case-sensitive. DCGM support is controlled by
`dcgm_enabled` in `orchestrator_config.yml`, not by the catalog. PowerScale CSI
is not a catalog-selected feature. It is enabled only by setting
`enable_powerscale_csi: true` on the one `service_k8s_cluster` entry whose
`deployment` value is `true`; catalog content does not enable the driver. When
enabled, Orchestrator resolves exactly one `csi-powerscale`, `helm-charts`, and
`external-snapshotter` artifact from `repo_status.yml` under
`file_repos.x86_64.git`.

### OIM storage mount selection

During provisioning, Orchestrator selects OIM mounts according to the workload
being provisioned instead of mounting every storage entry marked
`mount_on_oim: true`:

- Slurm provisioning selects the NFS and optional VAST storage referenced by
  the active `slurm_cluster` configuration. Each referenced entry must set
  `mount_on_oim: true`.
- Service Kubernetes provisioning selects the NFS storage referenced by a
  `service_k8s_cluster` entry whose `deployment` value is `true`. The
  referenced entry must set `mount_on_oim: true`.
- Storage referenced by an inactive Slurm or service Kubernetes workload is
  not mounted as an independent OIM mount, even when its `mount_on_oim` value
  is `true`.
- An entry with `mount_on_oim: true` that is not referenced by either workload
  remains an independent OIM mount.

See [Configure Mounts](configure_storage.md#oim-mount-selection) for the full
selection rules and examples.

## Procedure

Choose the guide that matches the operation you need to perform.

Run customer-facing Orchestrator commands from `src/main`. Initialize the
shared virtual environment and stage domain inputs before the first run:

```bash title="Run on: OIM"
cd src/main
./omnia.sh --setup-venv
source /etc/profile.d/omnia-env.sh
orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
source "$OMNIA_DATA_PATH/activate-omnia.sh"
```

The setup command stages inputs under
`$orchestrator_path/input/$OMNIA_PROJECT_NAME/` without changing
the domain-scoped input and output contract. Use `./omnia.sh --run
orchestrator --tags <tag>` for the workflows below. Direct
`ansible-playbook` commands from `src/orchestrator` remain available for
advanced or component-specific operations.

The profile loads `/etc/omnia/omnia.env` and exports the configured paths and
project name into the current shell. The `orchestrator_path` assignment honors
an explicit `ORCHESTRATOR_DATA_PATH` and otherwise resolves the Orchestrator
root beneath `OMNIA_DATA_PATH`. The activation command then activates the
shared Python environment.

### Workflow tags

For predictable lifecycle execution, run one Orchestrator workflow tag at a
time. The playbook rejects its explicitly defined conflicting combinations.
The documented combined cleanup is `cleanup,cleanup_credentials`.

| Tag | Implemented behavior | Required state before the phase |
|---|---|---|
| `validate` | Validate input-file schemas and configuration logic only. | Complete project inputs, including `orchestrator_config.yml`, `network_spec.yml`, `omnia_config.yml`, `security_config.yml`, and the resolved PXE mapping CSV; also include the HA or storage file when selected configuration requires it. This phase does not require credentials, the catalog, or upstream status files. |
| `precheck` | Validate inputs, mapping and storage relationships, OIM timezone and cluster identity settings, and functional-group images. | Current PXE mapping and catalog, successful `repo_status.yml` and `build_status.yml`, and reachable image artifacts. |
| `credentials` | Create or load the Vault-encrypted Orchestrator credentials. Missing values and stored values that fail the current credential rules are prompted for and securely replaced; valid stored values are retained. Password prompts require confirmation. | Current catalog and the applicable credential values. Upstream status files are not required. |
| `prepare` | Collect credentials, deploy OpenCHAMI and catalog-selected OpenLDAP, and validate deployment readiness. | Current catalog and PXE mapping. Upstream status files are not required for this service-preparation phase. |
| `deploy` | Deploy or retry OpenCHAMI and catalog-selected OpenLDAP together with their readiness checks, without collecting credentials. | A completed `prepare` phase, including stored credentials, and the current catalog. Use this tag to retry service deployment, not for initial preparation. |
| `provision` | Configure SSH access, provision Kubernetes, Slurm, login, OS-only, and custom functional groups, and run post-provision validation. This workflow does not initiate PXE boot. | Successful `precheck` and `prepare` phases, healthy OpenCHAMI and any selected OpenLDAP service, stored credentials, and successful Repository Manager and Image Build Manager outputs. |
| `execute` | Run provisioning followed by PXE boot when `enable_pxe_boot` is `true`. | The same state as `provision`; when PXE is enabled, reachable mapped iDRACs and BMC credentials are also required. |
| `validate-deployment` | Restore persisted validation context, obtain a fresh OpenCHAMI access token, and validate OpenCHAMI and catalog-selected OpenLDAP readiness. It can ensure the cluster hostname entry in `/etc/hosts`; it is not a purely read-only check. | A complete valid project input set, including conditional storage, HA, and additional cloud-init inputs; the current catalog; generated `.data/functional_groups_config.yml`; `$OMNIA_DATA_PATH/openchami/configs_vars.yaml`; and a healthy deployed OpenCHAMI instance capable of issuing a fresh access token. Orchestrator credential files, `repo_status.yml`, and `build_status.yml` are not required. |
| `pxeboot` | Set the boot source and restart selected Dell iDRAC nodes when PXE boot is enabled. A direct run without `pxeboot_inventory` selects every row in the active PXE mapping; a custom inventory limits the operation to a subset. | Completed provisioning, stored BMC credentials, current mapping and PXE configuration, reachable iDRACs, and successful `repo_status.yml`. The standalone phase does not read `build_status.yml`. |
| `cleanup` | Remove all enabled Orchestrator components and, by default, the Orchestrator credentials. OpenCHAMI cleanup also removes its managed persistent service volumes. | Review the destructive cleanup scope and data-retention settings first. Use `-e cleanup_credentials=false` with full cleanup to preserve credentials. Component-specific cleanup is available only through the standalone cleanup playbook. |
| `cleanup_credentials` | Remove the Orchestrator credential file and Vault key. | No deployment or upstream output is required. |
| `upgrade` | Run the current OpenCHAMI migration and OpenLDAP image-refresh workflows. The operator must verify the resulting package, Quadlet image, and service versions; the workflow does not guarantee every target-version transition. | A supported deployed source version and successful `repo_status.yml`. |
| `rollback` | Enter the reserved rollback workflows. Both OpenCHAMI and OpenLDAP rollback are unsupported in this release and intentionally stop with an error. | None; this operation is unavailable in this release. |

!!! caution "PXE defaults"

    The shipped PXE configuration restarts selected hosts, uses a forced
    restart, and sets a continuous network-boot override. On a direct run,
    the default inventory is the complete active PXE mapping. Review
    `set_pxe_boot_config.yml`, or pass `pxeboot_inventory` to target a subset,
    before running the workflow.

!!! danger "Full cleanup"

    Full cleanup removes `orchestrator_credentials.yml` and
    `.orchestrator_credentials_key` unless
    `-e cleanup_credentials=false` is supplied. OpenCHAMI cleanup uninstalls
    the `openchami` and `ochami` RPMs and permanently removes the
    `boot-service-data`, `metadata-service-data`, and `postgres-data` Podman
    volumes. Back up any required state first.

Running a phase tag does not automatically run its prerequisite phases. For a
new deployment, the recommended staged order is `validate`, `precheck`,
`prepare`, and `execute`. Use `provision` followed by `pxeboot` instead of
`execute` only when the two operations must be separated.

An untagged run is also supported, but its order is the literal playbook order:
shared setup and input validation, functional-group generation, precheck,
standalone credential collection, preparation, deployment and service
readiness, provisioning, and conditional PXE boot. Cleanup, upgrade, and
rollback are tagged `never` and do not run in this mode.

### Deployment and node lifecycle

| Task | Use it to |
|---|---|
| [Deploy OpenCHAMI](deploy_openchami.md) | Deploy and validate the OpenCHAMI services on the OIM. |
| [Deploy OpenLDAP](deploy_openldap.md) | Enable the catalog-selected OpenLDAP service and validate its container. |
| [Deploy Slurm](deploy_slurm.md) | Configure Slurm and login functional groups, storage, and Slurm configuration. |
| [Deploy Kubernetes](deploy_kubernetes.md) | Configure service Kubernetes functional groups, HA, networking, and storage. |
| [Provision Nodes](provision_nodes.md) | Run the complete or staged provisioning and PXE-boot workflow. |
| [Upgrade Orchestrator](upgrade_orchestrator.md) | Review the current OpenCHAMI and OpenLDAP upgrade workflow, its automation limits, and the mandatory post-upgrade checks. |
| [Clean Up Orchestrator](cleanup_orchestrator.md) | Review and run full, credential-only, or component-specific destructive cleanup. |
| [Add Nodes](../../Operations/add_nodes.md) | Register and configure new nodes, then boot only the new physical nodes through a custom PXE inventory. |
| [Remove Slurm Nodes](../../Operations/remove_slurm_nodes.md) | Drain and remove Slurm compute nodes omitted from the current PXE mapping. |

### Networking

| Task | Use it to |
|---|---|
| [Configure InfiniBand](configure_infiniband.md) | Configure the InfiniBand network and node interface mappings. |
| [Configure Cluster DNS](configure_cluster_dns.md) | Enable or disable CoreDNS for provisioned nodes. |
| [Configure Multi-Subnet DHCP](configure_multi_subnet_dhcp.md) | Add DHCP-relay subnets to the admin network. |
| [Configure PXE Boot](configure_pxe_boot.md) | Start mapped nodes through the Orchestrator PXE-boot workflow. |

### Storage and high availability

| Task | Use it to |
|---|---|
| [Configure Storage](configure_storage.md) | Configure shared mounts, PowerVault volumes, and swap. |
| [Deploy PowerScale CSI](deploy_powerscale_csi.md) | Configure PowerScale storage for a service Kubernetes cluster. |
| [Configure Kubernetes HA](configure_kubernetes_ha.md) | Configure the Kubernetes API virtual IP provided by kube-vip. |

### Slurm and advanced HPC setup

| Task | Use it to |
|---|---|
| [Configure Slurm](configure_slurm.md) | Supply or merge custom Slurm configuration files. |
| [Configure Custom UCX and OpenMPI](custom_ucx_openmpi_setup.md) | Build and expose a custom UCX and OpenMPI toolchain. |
| [Set Up NVIDIA HPC SDK](setup_nvhpc_sdk.md) | Configure the NVIDIA HPC SDK on Slurm nodes. |
| [Configure Slurm with GPUs](slurm_with_gpu.md) | Verify the GPU software and Slurm GRES configuration created during provisioning. |
| [Use Apptainer](use_apptainer.md) | Pull and run container images through the configured registry mirror. |

### Cloud-init and performance

| Task | Use it to |
|---|---|
| [Configure Additional Cloud-Init](configure_additional_cloud_init.md) | Add global or functional-group cloud-init directives. |
| [Run HPC Benchmarks](run_hpc_benchmarks.md) | Stage and run the benchmark assets installed by Orchestrator. |

## Verification

The provisioning and PXE-boot workflows write results and project-scoped
runtime records under `$orchestrator_path/output/$OMNIA_PROJECT_NAME/`:

| Output | Meaning |
|---|---|
| `orchestrator_status.yml` | Overall status and per-node results. The PXE flow records the PXE or node-registration failure stage. |
| `provisioning_report.yml` | Expected and SMD-registered node counts plus missing boot and metadata configurations. |
| `orchestrator_inventory.yaml` | Generated inventory for all mapped nodes. `kube_vip_group` is included only when a `service_kube_` functional group is mapped and a valid HA configuration supplies the VIP. |
| `bmc_group_data.csv` | Generated BMC inventory data. The OIM is included only when `primary_oim_bmc_ip` is set in `network_spec.yml`. |
| `failed_nodes.json` | Detailed failures from iDRAC PXE boot or node-registration. |
| `pxeboot_status.yml` | PXE initiation and optional node-registration verification for every node selected by the PXE inventory. |

Orchestrator also generates
`$orchestrator_path/output/$OMNIA_PROJECT_NAME/.data/functional_groups_config.yml`
and stores its runtime state in `orchestrator_state.yml` in the project output
directory. Inventory
generation, OpenCHAMI configuration, Slurm and Kubernetes provisioning, and
validation consume the generated functional-groups configuration.

Confirm that the generated artifacts meet the
[Orchestrator output contract](../../Reference/domain_contracts/orchestrator_contract.md#output-contract).

## Next steps

- Use [Provision Nodes](provision_nodes.md) for the end-to-end workflow.
- Use the configuration guides on this page for DNS, additional cloud-init,
  InfiniBand, storage, Slurm, GPU, and PXE options.
- After provisioning, use [Add Nodes](../../Operations/add_nodes.md) and
  [Remove Slurm Nodes](../../Operations/remove_slurm_nodes.md) for supported
  lifecycle changes.
- Use [Upgrade Orchestrator](upgrade_orchestrator.md) or
  [Clean Up Orchestrator](cleanup_orchestrator.md) only after reviewing their
  lifecycle and data-retention behavior.

## Troubleshooting

- Run one Orchestrator tag at a time for predictable lifecycle execution. The
  top-level playbook rejects unsupported tags and its explicitly defined
  conflicting combinations. Use `cleanup,cleanup_credentials` for the
  documented combined cleanup.
- Review `/var/log/omnia/orchestrator/orchestrator.log` when a play fails.
- Use `--tags validate` for input schema and logic checks,
  `--tags precheck` for inputs, OIM identity and timezone, mapping, storage, and
  image checks, and `--tags validate-deployment` for OpenCHAMI and OpenLDAP
  health checks.
- See [Orchestrator troubleshooting](../../Troubleshooting/orchestrator/index.md)
  for component-specific investigations.
