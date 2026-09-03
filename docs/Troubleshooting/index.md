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
| [repo_manager Domain Issues](repo_manager/index.md) | Repository mirroring and synchronization issues |

### image_build_manager Domain

Image building and S3 storage issues - OS image creation, MinIO uploads, architecture-specific builds

| Topic | Description |
| --- | --- |
| [image_build_manager Domain Issues](image_build_manager/index.md) | Image building and S3 storage issues |

### discovery Domain

Node discovery and mapping file generation issues - OME integration, PXE mapping file creation

| Topic | Description |
| --- | --- |
| [discovery Domain Issues](discovery/index.md) | Node discovery and mapping file generation issues |

### orchestrator Domain

Slurm, Kubernetes, networking, storage, and authentication issues - Node provisioning, cluster configuration

| Topic | Description |
| --- | --- |
| [orchestrator Domain Issues](orchestrator/index.md) | Slurm, Kubernetes, networking, storage, and authentication issues |

### telemetry Domain

Monitoring and metrics collection issues - iDRAC telemetry, LDMS samplers, Kafka, VictoriaMetrics, VictoriaLogs

| Topic | Description |
| --- | --- |
| [telemetry Domain Issues](telemetry/index.md) | Monitoring and metrics collection issues |

### build_stream Domain

GitOps-based CI/CD pipeline issues - BuildStreaM execution, GitLab integration, catalog validation

| Topic | Description |
| --- | --- |
| [build_stream Domain Issues](build_stream/index.md) | GitOps-based CI/CD pipeline issues |

### utils Domain

Helper utilities issues - Backup, install, and prepare operations

| Topic | Description |
| --- | --- |
| [utils Domain Issues](utils/index.md) | Helper utilities issues |

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



















