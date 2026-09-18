# Architecture

## OMNIA 2.3.0.0 Architecture

![OMNIA 2.3.0.0 Architecture](../assets/images/omnia_arch_updated.jpg)

Omnia is a modular infrastructure management platform for deploying,
configuring, and monitoring supported HPC environments. The Omnia
Infrastructure Manager (OIM) is the central management and execution node from
which administrators initialize deployment modules, run their playbooks, and
manage the generated inputs, outputs, and logs.

## OIM role and responsibilities

The OIM hosts the shared Python virtual environment, project input and output
directories, module logs, and selected OIM-local services. It also coordinates
services and configuration deployed to managed clusters and other configured
hosts.

- **Provisioning** — coordinates node registration, OpenCHAMI Boot Script
  Service (BSS) boot parameters, cloud-init configuration, and optional iDRAC
  PXE-boot operations.
- **Content and image management** — synchronizes selected software content and
  builds the operating-system images used by provisioned nodes.
- **Cluster configuration** — configures supported Slurm and service Kubernetes
  functional groups and their associated services.
- **Observability** — deploys and configures selected telemetry sources,
  collection bridges, Kafka, VictoriaMetrics, and VictoriaLogs on service
  Kubernetes.
- **Automation and operations** — supports BuildStreaM-driven pipelines and
  independent utilities such as log collection, OIM backup, and unattended OS
  installation.

## Managed node and system relationships

The OIM uses OpenCHAMI, Ansible, and cloud-init to register, provision, and
configure supported managed nodes when the corresponding workflows are
selected:

- **Service Kubernetes cluster** — control-plane and worker nodes that run
  selected platform and telemetry workloads.
- **Slurm control nodes** — run Slurm management services and dispatch jobs to
  compute nodes.
- **Compute nodes** — execute Slurm-managed workloads.
- **Login nodes** — provide user access for cluster interaction and job
  submission, including the `login_compiler_node` variant.
- **Storage systems and services** — provide shared storage consumed by the
  cluster. These can include NFS and external PowerScale or VAST systems. MinIO
  provides image-artifact storage for Image Build Manager on the OIM.

Omnia-provisioned nodes receive their operating-system image, hostname, network
configuration, and functional-group assignment through catalog, mapping,
OpenCHAMI, and cloud-init data. The OIM communicates with managed nodes over the
admin network and, when selected, uses the BMC network for out-of-band discovery,
inventory, telemetry, unattended installation, and PXE-boot control.

## Modular deployment architecture

Omnia separates deployment responsibilities into seven capability-based
deployment modules. The architecture uses the following shared conventions and
components:

- **Deployment modules** — provide domain-specific deployment behavior for
  Repository Manager, Image Build Manager, Discovery, Orchestrator, Telemetry,
  BuildStreaM, and Utils.
- **Module playbook** — provides each module's top-level Ansible entry point at
  `src/<domain>/playbooks/<domain>.yml`, where `<domain>` is the module's
  internal identifier.
- **Module initialization** — uses each module's `domain-init.sh` script to
  install declared dependencies and stage input templates.
- **Common controller (`main`)** — uses `src/main/omnia.sh` to create the shared
  environment, run module initialization, stage catalog files, activate the
  environment, and dispatch the requested module playbook.
- **Shared catalog** — defines functional layers, functional groups, packages,
  and content sources consumed by Repository Manager, Image Build Manager, and
  Orchestrator. The catalog is a shared input contract rather than a deployment
  module. Default Kubernetes and Slurm catalogs are available from
  [`src/main/samples/catalogs`](https://github.com/dell/omnia/tree/issue-4849-omnia-modernization/src/main/samples/catalogs)
  in the Omnia source repository.

## Deployment module responsibilities

| Deployment module | Responsibility | Primary customer-facing output or service |
|---|---|---|
| `repo_manager` | Deploy an HTTPS Pulp service and synchronize catalog-selected RPM, container, Python, and file content. | `repo_status.yml` and the Pulp distributions it describes |
| `image_build_manager` | Deploy MinIO and a local registry when selected, then build OS images for catalog or configured functional groups. | `build_status.yml` and image artifacts in S3 and the registry |
| `discovery` | Query OpenManage Enterprise for BMC inventory and generate an Orchestrator-compatible mapping. | `bmc_pxe_mapping_file.csv` and `bmc_discovery_report.csv` |
| `orchestrator` | Deploy OpenCHAMI and catalog-selected OpenLDAP, register mapped nodes, create boot and cloud-init configuration, configure Slurm or service Kubernetes, and optionally initiate iDRAC PXE boot. | `orchestrator_status.yml`, `orchestrator_inventory.yaml`, provisioning reports, and the deployed clusters |
| `telemetry` | Deploy the enabled telemetry sources, bridges, Kafka, VictoriaMetrics, and VictoriaLogs on a service Kubernetes cluster. | `telemetry_status.yml`, Kubernetes workloads, and optional external connection exports |
| `build_stream` | Deploy PostgreSQL, BuildStreaM Manager, the playbook watcher, GitLab integration, and the managed CI/CD project and runner. | `build_stream_status.yml`, the BSM API, and GitLab pipelines |
| `utils` | Run independent operational utilities, including cluster-log collection, OIM log backup, and unattended OS installation. | `utils_status.yml` and operation-specific results |

Modules can be invoked separately, but downstream workflows require the
contracts produced upstream. Discovery is optional when the administrator
provides a valid PXE mapping. Telemetry is optional and requires service
Kubernetes. Utils runs only when its operation is needed.

## Execution and contract flow

`omnia.sh` runs one requested module at a time. Administrators normally follow
this dependency order:

1. **Repository Manager** — synchronizes the content selected by the catalog.
2. **Image Build Manager** — uses the synchronized content to build operating
   system images.
3. **Discovery (optional)** — discovers server BMC information and produces the
   mapping consumed by Orchestrator. Administrators can provide the mapping
   instead.
4. **Orchestrator** — provisions and configures the selected Slurm or service
   Kubernetes cluster.
5. **Telemetry (optional)** — deploys selected telemetry workloads after service
   Kubernetes is available.

The following modules do not participate directly in that dependency chain:

- **BuildStreaM** — provides an alternate automation path for managed build and
  deployment pipelines.
- **Utils** — runs independently for the selected operational task.

The principal inputs and handoffs, beginning with the shared catalog, are:

| Producer or input | Consumer | Contract and purpose |
|---|---|---|
| Catalog | Repository Manager, Image Build Manager, and Orchestrator | JSON functional layers, groups, packages, and sources define the content and functional-group selections used by the deployment. |
| Repository Manager | Image Build Manager and Orchestrator | `repo_status.yml` records synchronized Pulp distributions and the endpoints used by downstream modules. |
| Image Build Manager | Orchestrator | `build_status.yml` records successfully built images and their artifact locations. |
| Discovery or administrator | Orchestrator | Discovery produces `bmc_pxe_mapping_file.csv`; the administrator copies it as the Orchestrator input `pxe_mapping_file.csv`, which maps systems to provisioning identities and functional groups. |
| Orchestrator | Telemetry | `orchestrator_inventory.yaml` describes the provisioned cluster; `bmc_group_data.csv` supplies BMC mappings when iDRAC telemetry is selected. |
| GitLab pipelines | BuildStreaM Manager | Uploaded catalog and module input files, together with API job requests, initiate managed build and deployment workflows. |

Contracts are not limited to YAML. Omnia uses YAML configuration and status
files, JSON catalogs and job data, and CSV mappings and reports.

## Runtime layout

`omnia.sh --setup-venv` installs the shared environment, runs the selected
modules' initialization scripts, and stages flat source inputs into a runtime
project layout. With the supplied defaults, that layout is:

```text
/opt/omnia/
├── venv/
├── .data/
├── catalog/
└── <domain>/
    ├── input/project_default/
    ├── output/project_default/
    └── log/project_default/
```

- `OMNIA_DATA_PATH` selects the root directory for persistent Omnia data. Module
  data directories are derived from this root unless a component-specific path
  overrides them.
- `OMNIA_PROJECT_NAME` selects the project subdirectory beneath each module's
  `input`, `output`, and `log` directories.

BuildStreaM currently fixes its entry-playbook input and output project to
`project_default`.

## OIM and managed services

The OIM is the execution point for module playbooks. Some selected services run
on the OIM, while others run on the service cluster or another configured host:

| Owner | Services or resources |
|---|---|
| Repository Manager | Pulp and its HTTPS content endpoints |
| Image Build Manager | MinIO S3 storage and a local OCI registry |
| Orchestrator | OpenCHAMI services, CoreDHCP, coresmd/CoreDNS, and optional OpenLDAP |
| BuildStreaM | PostgreSQL, the BSM API, and the playbook watcher; GitLab and its runner are deployed on the configured GitLab host |
| Telemetry | Kubernetes workloads on the service cluster, rather than an OIM-wide telemetry container |

Node operating-system images, hostnames, network data, and functional groups
are selected through the catalog and PXE mapping and are applied by
Orchestrator through OpenCHAMI boot parameters and cloud-init.

## Network relationships

Omnia distinguishes several network purposes:

- The **admin network** connects the OIM and managed nodes and carries content,
  provisioning, SSH, and cluster-management traffic.
- The optional **BMC network** provides out-of-band access to iDRAC for
  discovery, inventory, Telemetry, unattended installation, and PXE-boot
  control when those features are selected.
- The optional **InfiniBand network** provides the high-performance fabric for
  supported Slurm and storage workloads.
- Service Kubernetes pod and service networks are configured separately and
  must not overlap the management networks used by the deployment.

See [Network Topologies](network_topologies.md) for the supported layouts and
[Orchestrator configuration](../Reference/Configuration/orchestrator_config.md)
for the source-backed input fields.

## Kubernetes stack

![Omnia Kubernetes Stack](../assets/images/omnia-k8s.svg)

Orchestrator provisions the service Kubernetes control-plane and worker
functional groups selected through the catalog and PXE mapping. It configures
CRI-O storage for these nodes. Telemetry subsequently uses the generated
Orchestrator inventory and Kubernetes control-plane virtual IP to deploy its
selected workloads.

## Slurm stack

![Omnia Slurm Stack](../assets/images/omnia-slurm.svg)

Orchestrator provisions the Slurm control, compute, login, and login-compiler
functional groups selected through the catalog and PXE mapping. It configures
the applicable shared storage, Slurm services, authentication, optional GPU and
fabric software, and generated inventory. LDMS Telemetry additionally requires
reachable Slurm control and compute nodes.

## Related documentation

- [Running Deployment Modules](domain_execution.md)
- [Module Contracts](../Reference/index.md#module-contracts)
- [Get Started](../GetStarted/index.md)
- [How-to Guides](../HowTo/index.md)
