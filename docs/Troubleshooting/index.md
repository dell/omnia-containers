# Troubleshooting Guide

A structured guide for diagnosing and resolving issues across Omnia deployment, provisioning, Kubernetes, Slurm, storage, authentication, and telemetry workflows. Each entry follows a consistent **Symptom > Cause > Resolution** format so you can quickly identify the problem and apply the fix.

## Troubleshooting Approach

When you encounter an issue, follow this general diagnostic flow:

1. **Check logs first.** Most issues leave a clear trace in the logs. For comprehensive logging information, see [Log Management](../Operations/log_management.md).

2. **Verify prerequisites.** Many failures stem from unmet prerequisites (missing packages, wrong OS version, misconfigured networks). Re-check the [Prerequisites Checklist](../GetStarted/prerequisites_checklist.md) for your deployment path.

3. **Inspect container and service status.** Verify that OIM containers and services are running:

    **Execution context: OIM host**

    ```bash
    podman ps --format 'table {{.Names}}\t{{.Status}}'
    ```

4. **Use the ochami CLI.** For provisioning issues, the `ochami-cli` provides direct access to the OpenCHAMI state manager for inspecting node inventory, boot status, and hardware state:

    **Execution context: omnia_core container**

    ```bash
    ochami smd component get
    ochami bss boot params get
    ```

5. **Search this section.** Browse the topic-specific pages below or use your browser's search (Ctrl+F) to find your symptom.

## Troubleshooting Topics

### repo_manager Domain

Repository mirroring and synchronization issues - Pulp operations, package downloads, container registry sync

| Topic | Description |
| --- | --- |
| [Local Repository and Pulp Issues](repo_manager/repo_manager.md) | Pulp container operations, repository synchronization, and package downloads |

### image_build_manager Domain

Image building and S3 storage issues - OS image creation, MinIO uploads, architecture-specific builds

| Topic | Description |
| --- | --- |
| [Build Cluster Image Issues](image_build_manager/build_cluster_images.md) | OS image creation and S3 storage issues |
| [Image Build Manager Issues](image_build_manager/image_build_manager.md) | Image building and MinIO operations |

### discovery Domain

Node discovery and mapping file generation issues - OME integration, PXE mapping file creation

| Topic | Description |
| --- | --- |
| [Discovery Issues](discovery/discovery.md) | OME integration and PXE mapping file generation |

### orchestrator Domain

Slurm, Kubernetes, networking, storage, and authentication issues - Node provisioning, cluster configuration

| Topic | Description |
| --- | --- |
| [Orchestrator Issues](orchestrator/orchestrator.md) | General orchestrator domain issues |
| [Provisioning Issues](orchestrator/provisioning.md) | Node provisioning and PXE boot issues |
| [Slurm Issues](orchestrator/slurm.md) | Slurm job scheduling and configuration issues |
| [Kubernetes Issues](orchestrator/kubernetes.md) | Kubernetes service cluster issues |
| [OpenCHAMI Issues](orchestrator/openchami.md) | OpenCHAMI provisioning stack issues |
| [Authentication Issues](orchestrator/authentication.md) | LDAP and authentication issues |
| [Kernel Version Override](orchestrator/kernel_version_override.md) | Kernel version management issues |

### telemetry Domain

Monitoring and metrics collection issues - iDRAC telemetry, LDMS samplers, Kafka, VictoriaMetrics, VictoriaLogs

| Topic | Description |
| --- | --- |
| [Telemetry Issues](telemetry/telemetry.md) | iDRAC telemetry, LDMS samplers, Kafka, VictoriaMetrics, and VictoriaLogs |

### build_stream Domain

GitOps-based CI/CD pipeline issues - BuildStreaM execution, GitLab integration, catalog validation

| Topic | Description |
| --- | --- |
| [BuildStreaM Issues](build_stream/build_stream.md) | BuildStreaM pipeline stage failures, API registration, and catalog parsing |
| [BuildStream Issues](build_stream/buildstream.md) | BuildStream pipeline execution issues |

### utils Domain

Helper utilities issues - Backup, install, and prepare operations

| Topic | Description |
| --- | --- |
| [Utils Issues](utils/utils.md) | Backup, install, and prepare operations |

### Cross-Domain Issues

| Topic | Description |
| --- | --- |
| [General](general.md) | Core container failures, OIM issues, OpenCHAMI certificates, system recovery, InfiniBand, and Ansible Vault errors |
| [General Troubleshooting](general_troubleshooting.md) | General troubleshooting steps and procedures |
| [Upgrade and Rollback](upgrade_rollback.md) | Lock file conflicts, manifest tracking, component-specific upgrade/rollback failures, and kernel version override |
| [Known Limitations](known_limitations.md) | Current limitations, constraints, and known issues |

!!! tip

    If you cannot resolve an issue using this guide, open an issue on the
    [Omnia GitHub repository](https://github.com/dell/omnia/issues) with
    the relevant log output and a description of your environment.



















