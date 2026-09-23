# Get Started

## Omnia Deployment Flow

<div class="of-wrap">
<div class="of-root" id="ofRoot">
  <div class="of-hdr">
    <div class="of-h2">Select options to see your deployment path</div>
  </div>
  <div class="of-flow" id="omniaDeploymentFlowchart"></div>
</div>
</div>

<!-- End of Omnia Deployment Flow -->

Choose your deployment path based on your cluster requirements, available
hardware, and desired workload. Each path is a self-contained, end-to-end
tutorial that takes you from a bare set of PowerEdge servers to a fully
operational cluster.

!!! note

    Before selecting a path, complete the [Prerequisites Checklist](prerequisites_checklist.md) to
    ensure your hardware, networking, and software environment are ready.

!!! important "Select a catalog for the deployment path"

    Catalog selection is mandatory because it determines which functional
    groups, software groups, packages, operating-system versions, and node
    architectures Omnia builds and provisions.

    - **Slurm Quickstart** requires Slurm controller and compute functional
      layers, including the mandatory `slurm_custom_group` component.
    - **K8S Telemetry Only** requires service Kubernetes control-plane and
      worker functional layers with the service Kubernetes and Telemetry
      components.
    - **Full Deployment** requires a combined catalog containing both Slurm
      and service Kubernetes functional layers.
    - **BuildStreaM Deployment** requires a catalog that matches every
      functional group requested by its automated workflow.

    See [Select or update the catalog](../HowTo/main/update_catalog.md) for the
    shipped catalog choices. The [Slurm Quickstart](slurm_quickstart.md) and
    [K8S Telemetry Only](k8s_telemetry_only.md) paths provide the exact minimum
    layer names, required components, and verification commands.

## Deployment Paths at a Glance


| Path | Name | Workload | Nodes | Time | Description |
| --- | --- | --- | --- | --- | --- |
| **A** | [Slurm Quickstart](slurm_quickstart.md) | Traditional HPC (Slurm) | 4+ | ~2 hrs | Overview page with links to detailed Slurm deployment guides. Covers Slurm setup, GPU provisioning, node management, configuration backup, and HPC benchmarks. Ideal for first-time users and large-scale HPC workloads. |
| **B** | [K8S Telemetry Only](k8s_telemetry_only.md) | Kubernetes + Telemetry (no Slurm) | 5 | ~2 hrs | Deploys a 3-control-plane + 1-worker Kubernetes cluster with the complete telemetry pipeline (For example: iDRAC metrics, LDMS, Kafka, VictoriaMetrics). No Slurm. Use this when you need infrastructure monitoring without a job scheduler. |
| **C** | [Full Deployment](full_deployment.md) | Slurm + Service K8s + Telemetry | 8 | ~4 hrs | Production-grade deployment with Slurm scheduling, a highly available 3-node Kubernetes service cluster, LDAP authentication, and full telemetry (For example: iDRAC, VictoriaMetrics). Best for teams running mixed HPC/AI workloads with monitoring requirements. |
| **D** | [BuildStreaM Deployment](buildstream_deployment.md) | BuildStreaM (Catalog-Driven CI/CD) | 8+ | ~6 hrs | Automated, catalog-driven deployment using GitLab CI/CD pipelines. BuildStreaM reads a declarative catalog to provision and configure the entire cluster. Best for organizations with GitOps workflows or repeated, reproducible deployments at scale.

## Omnia deployment modules

Omnia uses a modular, capability-based architecture in which each deployment
module handles a specific part of cluster deployment. Modules exchange
documented input/output contracts and can be invoked separately using the
`omnia.sh` CLI. End-to-end paths run the required modules in dependency order.

| Deployment module | Description |
| --- | --- |
| [Repository Manager](../HowTo/repo_manager/index.md) (`repo_manager`) | Local repository creation and package management for air-gapped deployments |
| [Image Build Manager](../HowTo/image_build_manager/index.md) (`image_build_manager`) | Diskless OS image building for each functional group |
| [Discovery](../HowTo/discovery/index.md) (`discovery`) | BMC discovery and PXE mapping generation through OME; manual mappings are supplied directly to Orchestrator |
| [Orchestrator](../HowTo/orchestrator/index.md) (`orchestrator`) | Node provisioning, boot configuration, and cluster setup |
| [Telemetry](../HowTo/Telemetry/index.md) (`telemetry`) | Telemetry pipeline deployment (iDRAC, LDMS, Kafka, VictoriaMetrics, VictoriaLogs) |
| [BuildStreaM](../HowTo/build_stream/index.md) (`build_stream`) | GitLab CI/CD automation for catalog-driven build and deployment pipelines |
| [Utilities](../HowTo/utils/index.md) (`utils`) | Utility operations including unattended OS installation and log collection |

!!! info

    For detailed information on module execution order and dependencies, see
    [Running Deployment Modules](../Overview/domain_execution.md).

## Which Path Should I Choose?


**"I just want Slurm running as fast as possible."**
    Start with [Slurm Quickstart](slurm_quickstart.md) (Path A). You can always add
    Kubernetes and telemetry later.

**"I only need telemetry dashboards -- no job scheduler."**
    Choose [K8S Telemetry Only](k8s_telemetry_only.md) (Path B). This gives you
    iDRAC-to-Victoria Metrics visibility without the overhead of Slurm.

**"I need a production cluster with monitoring and authentication."**
    Go with [Full Deployment](full_deployment.md) (Path C). This is the canonical Omnia
    deployment that exercises every major subsystem.

**"I want CI/CD-driven, repeatable infrastructure."**
    Use [BuildStreaM Deployment](buildstream_deployment.md) (Path D). BuildStreaM automates the
    entire lifecycle through GitLab pipelines and a declarative catalog.

## Before You Begin


Every path assumes you have completed the items in
[Prerequisites Checklist](prerequisites_checklist.md). That page covers:

- Supported hardware and firmware versions
- OIM (management node) requirements (RAM, OS, Podman, NICs)
- Network switch configuration (admin + BMC VLANs)
- NFS / storage preparation
- BIOS and iDRAC settings on target nodes
- Required RHEL subscriptions and Docker credentials

!!! tip

    Print or bookmark the [Prerequisites Checklist](prerequisites_checklist.md) -- it doubles as a
    day-of-deployment runbook you can hand to a datacenter technician.
