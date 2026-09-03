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

## Deployment Paths at a Glance


| Path | Name | Workload | Nodes | Time | Description |
| --- | --- | --- | --- | --- | --- |
| **A** | [Slurm Quickstart](slurm_quickstart.md) | Traditional HPC (Slurm) | 4+ | ~2 hrs | Overview page with links to detailed Slurm deployment guides. Covers Slurm setup, GPU provisioning, node management, configuration backup, and HPC benchmarks. Ideal for first-time users and large-scale HPC workloads. |
| **B** | [K8S Telemetry Only](k8s_telemetry_only.md) | Kubernetes + Telemetry (no Slurm) | 5 | ~2 hrs | Deploys a 3-control-plane + 1-worker Kubernetes cluster with the complete telemetry pipeline (For example: iDRAC metrics, LDMS, Kafka, VictoriaMetrics). No Slurm. Use this when you need infrastructure monitoring without a job scheduler. |
| **C** | [Full Deployment](full_deployment.md) | Slurm + Service K8s + Telemetry | 8 | ~4 hrs | Production-grade deployment with Slurm scheduling, a highly available 3-node Kubernetes service cluster, LDAP authentication, and full telemetry (For example: iDRAC, VictoriaMetrics). Best for teams running mixed HPC/AI workloads with monitoring requirements. |
| **D** | [Buildstream Deployment](buildstream_deployment.md) | BuildStreaM (Catalog-Driven CI/CD) | 8+ | ~6 hrs | Automated, catalog-driven deployment using GitLab CI/CD pipelines. BuildStreaM reads a declarative catalog to provision and configure the entire cluster. Best for organizations with GitOps workflows or repeated, reproducible deployments at scale.

## Omnia Domains

Omnia v2.3 uses a domain-based architecture where each domain handles a specific aspect of cluster deployment. Domains communicate via YAML contracts and can be executed independently using the `omnia.sh` CLI.

|| Domain | Description |
|| --- | --- |
|| [discovery](../HowTo/discovery/index.md) | BMC discovery and PXE mapping file generation using OME or manual methods |
|| [repo_manager](../HowTo/repo_manager/index.md) | Local repository creation and package management for air-gapped deployments |
|| [image_build_manager](../HowTo/image_build_manager/index.md) | Diskless OS image building for each functional group |
|| [orchestrator](../HowTo/orchestrator/index.md) | Node provisioning, boot configuration, and cluster setup |
|| [telemetry](../HowTo/Telemetry/index.md) | Telemetry pipeline deployment (iDRAC, LDMS, Kafka, VictoriaMetrics, VictoriaLogs) |
|| [utils](../HowTo/utils/index.md) | Utility operations including aarch64 node preparation and configuration backup |

!!! info

    For detailed information on domain execution order and dependencies, see [Domain Execution](../Overview/domain_execution.md). |

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
    Use [Buildstream Deployment](buildstream_deployment.md) (Path D). BuildStreaM automates the
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
