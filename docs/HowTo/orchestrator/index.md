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
- Complete Repo Manager and provide a successful `repo_status.yml` and its
  public certificate. Also provide the selected deployment catalog.
  Orchestrator uses `catalog_file_path` from `orchestrator_config.yml`, when
  configured; otherwise, it uses `CATALOG_FILE_PATH`, or
  `$OMNIA_DATA_PATH/catalog/catalog_rhel.json`.
- Complete Image Build Manager and provide a successful `build_status.yml`
  containing images for every functional group in the mapping.
- Place the discovery-produced PXE mapping in the active project's
  Orchestrator input directory, or configure an override in
  `orchestrator_config.yml`.
- Configure the OIM environment, including `SYSTEM_ADMIN_NIC_IPV4`,
  `SYSTEM_HOSTNAME`, `SYSTEM_DOMAIN_NAME`, `OMNIA_DATA_PATH`, and
  `OMNIA_PROJECT_NAME`. `OMNIA_DATA_PATH` defaults to `/opt/omnia`,
  `OMNIA_PROJECT_NAME` defaults to `project_default`, and the Orchestrator root
  is `<OMNIA_DATA_PATH>/orchestrator`.
- Review the
  [Orchestrator configuration reference](../../Reference/Configuration/orchestrator_config.md)
  and provide the required Orchestrator, Discovery, Image Build Manager, Repo
  Manager, credential, and shared project inputs before running validation.

### Input summary

Project inputs are staged in the active project's Orchestrator input
directory. Upstream outputs remain in the producing domain unless a path
override is configured.

| Input | Requirement | Purpose |
|---|---|---|
| `orchestrator_config.yml` | Required | Selects upstream paths and provisioning, DNS, kernel, cloud-init, catalog, DCGM, and PXE behavior. |
| `network_spec.yml` | Required | Defines the admin network and optional relay and InfiniBand networks. |
| `pxe_mapping_file.csv` | Required unless overridden | Maps nodes to functional groups and supplies admin and BMC identities. |
| `omnia_config.yml` | Required | Defines Slurm and service-Kubernetes clusters, optional bolt-on overrides, and storage references. Retain both top-level arrays; use `[]` for an unselected workload. |
| `storage_config.yml` | Conditional | Defines storage mounts used by selected clusters. |
| `security_config.yml` | Conditional | Supplies security settings for enabled services. |
| `high_availability_config.yml` | Required for service Kubernetes | Defines the Kubernetes control-plane virtual IP. |
| `additional_cloud_init.yml` | Optional | Adds validated common and per-functional-group `write_files` and `runcmd` directives during provisioning when `additional_cloud_init_config_file` is configured. |
| `set_pxe_boot_config.yml` | Optional for PXE boot | Overrides node-registration timing and PXE-boot settings. |
| `orchestrator_credentials.yml` and `.orchestrator_credentials_key` | Required for credential-consuming flows | Store encrypted provisioning, BMC, Slurm, OpenLDAP, and PowerScale credentials and the Vault key. |
| `repo_status.yml` | Required for precheck, provisioning/PXE, and full runs | Supplies repository URLs and the Repo Manager public certificate. |
| `build_status.yml` | Required for precheck, provisioning, execute, and full runs | Supplies functional-group images and S3 endpoint information. The standalone `pxeboot` phase does not read this file. |
| Catalog JSON | Required for catalog-selected features | Supplies OS metadata and enables supported services and software. |

### Catalog feature selection

Orchestrator derives the following feature support from catalog names:

| Feature | Catalog entry | Selection rule |
|---|---|---|
| Kubernetes | `catalog.functionallayer[].name` | The name contains `kube` or `k8s`. |
| Slurm | `catalog.functionallayer[].name` | The name contains `slurm`. |
| OpenLDAP | `catalog.groups` name | The name contains `openldap`. |
| UCX | `catalog.groups` name | The name contains `ucx`. |
| OpenMPI | `catalog.groups` name | The name contains `openmpi`. |
| PowerScale CSI artifacts | `catalog.groups` and package content | The selected catalog must provide the CSI driver, Helm chart, and snapshot-controller artifacts. Catalog content does not enable the driver. |

These catalog name matches are case-sensitive. DCGM support is controlled by
`dcgm_enabled` in `orchestrator_config.yml`, not by the catalog. PowerScale CSI
is enabled only by setting `enable_powerscale_csi: true` on the one
`service_k8s_cluster` entry whose `deployment` value is `true`; catalog content
only makes the required artifacts available.

## Procedure

Choose the guide that matches the operation you need to perform.

Run customer-facing Orchestrator commands from `src/main`. Initialize the
shared virtual environment and stage domain inputs before the first run:

```bash title="Run on: OIM"
cd src/main
./omnia.sh --setup-venv
source /etc/profile.d/omnia-env.sh
orchestrator_path="${OMNIA_DATA_PATH}/orchestrator"
source "$OMNIA_DATA_PATH/activate-omnia.sh"
```

The setup command stages inputs under
`$orchestrator_path/input/$OMNIA_PROJECT_NAME/` without changing
the domain-scoped input and output contract. Use `./omnia.sh --run
orchestrator --tags <tag>` for the workflows below. Direct
`ansible-playbook` commands from `src/orchestrator` remain available for
advanced or component-specific operations.

The profile loads `/etc/omnia/omnia.env` and exports the configured paths and
project name into the current shell. The `orchestrator_path` assignment
resolves the Orchestrator root beneath `OMNIA_DATA_PATH`. The activation
command then activates the shared Python environment.

### Workflow tags

Run one Orchestrator workflow tag at a time, except when using the supported
`cleanup,cleanup_credentials` combination.

| Tag | Implemented behavior | Required state before the phase |
|---|---|---|
| `validate` | Validate input-file schemas and configuration logic only. | Staged Orchestrator YAML inputs. This phase does not require the catalog or upstream status files. |
| `precheck` | Validate inputs, mapping data, storage prerequisites, environment settings, and functional-group images. | Current PXE mapping and catalog, successful `repo_status.yml` and `build_status.yml`, and reachable image artifacts. |
| `credentials` | Create or load the Vault-encrypted Orchestrator credentials. Missing values and stored values that fail the current credential rules are prompted for and securely replaced; valid stored values are retained. Password prompts require confirmation. | Current catalog and the applicable credential values. Upstream status files are not required. |
| `prepare` | Collect credentials, deploy OpenCHAMI and catalog-selected OpenLDAP, and validate deployment readiness. | Current catalog and PXE mapping. Upstream status files are not required for this service-preparation phase. |
| `deploy` | Deploy or retry OpenCHAMI and catalog-selected OpenLDAP together with their readiness checks, without collecting credentials. | A completed `prepare` phase, including stored credentials, and the current catalog. Use this tag to retry service deployment, not for initial preparation. |
| `provision` | Configure SSH access, provision Kubernetes, Slurm, login, OS-only, and custom functional groups, and run post-provision validation. This workflow does not initiate PXE boot. | Successful `precheck` and `prepare` phases, healthy OpenCHAMI and any selected OpenLDAP service, stored credentials, and successful Repository Manager and Image Build Manager outputs. |
| `execute` | Run provisioning followed by PXE boot when `enable_pxe_boot` is `true`. | The same state as `provision`; when PXE is enabled, reachable mapped iDRACs and BMC credentials are also required. |
| `validate-deployment` | Restore persisted validation context, authenticate to OpenCHAMI, and validate OpenCHAMI and catalog-selected OpenLDAP readiness. It can ensure the cluster hostname entry in `/etc/hosts`; it is not a purely read-only check. | A completed service deployment, current catalog, network specification and PXE mapping, generated `.data/functional_groups_config.yml`, `$OMNIA_DATA_PATH/openchami/configs_vars.yaml`, and stored authentication state. Upstream status files are not required. |
| `pxeboot` | Set the boot source and restart mapped Dell iDRAC nodes when PXE boot is enabled. | Completed provisioning, stored BMC credentials, current mapping and PXE configuration, reachable iDRACs, and successful `repo_status.yml`. The standalone phase does not read `build_status.yml`. |
| `cleanup` | Remove all enabled Orchestrator components. | Review the cleanup scope and data-retention settings first. Component-specific cleanup is available only through the standalone cleanup playbook. |
| `cleanup_credentials` | Remove the Orchestrator credential file and Vault key. | No deployment or upstream output is required. |
| `upgrade` | Run the current OpenCHAMI migration and OpenLDAP image-refresh workflows. The operator must verify the resulting package, Quadlet image, and service versions; the workflow does not guarantee every target-version transition. | A supported deployed source version and successful `repo_status.yml`. |
| `rollback` | Enter the reserved rollback workflows. Both OpenCHAMI and OpenLDAP rollback are unsupported in this release and intentionally stop with an error. | None; this operation is unavailable in this release. |

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

### Kernel, Slurm, and advanced HPC setup

| Task | Use it to |
|---|---|
| [Configure Kernel Version Override](configure_kernel_version_override.md) | Select a specific built kernel during provisioning. |
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

The provisioning and PXE-boot workflows write customer-readable results under
`$orchestrator_path/output/$OMNIA_PROJECT_NAME/`:

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

- Run one Orchestrator tag at a time. The top-level playbook rejects unsupported
  and conflicting combinations, except for the documented
  `cleanup,cleanup_credentials` combination.
- Review `/var/log/omnia/orchestrator/orchestrator.log` when a play fails.
- Use `--tags validate` for input schema and logic checks,
  `--tags precheck` for inputs, environment, mapping, storage, and image checks,
  and `--tags validate-deployment` for OpenCHAMI and OpenLDAP health checks.
- See [Orchestrator troubleshooting](../../Troubleshooting/orchestrator/index.md)
  for component-specific investigations.
