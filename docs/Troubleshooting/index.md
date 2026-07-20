# Troubleshooting Guide

A structured guide for diagnosing and resolving issues across Omnia deployment, provisioning, Kubernetes, Slurm, storage, authentication, and telemetry workflows. Each entry follows a consistent **Symptom > Cause > Resolution** format so you can quickly identify the problem and apply the fix.

## Troubleshooting Approach

When you encounter an issue, follow this general diagnostic flow:

1. **Check logs first.** Most issues leave a clear trace in the logs. For comprehensive logging information, see [Log Management](../Operations/log_management.md).

2. **Verify prerequisites.** Many failures stem from unmet prerequisites (missing packages, wrong OS version, misconfigured networks). Re-check the [Prerequisites Checklist](../GetStarted/prerequisites_checklist.md) for your deployment path.

3. **Inspect container and service status.** Verify that OIM containers and services are running:

    ```bash title="Run on: OIM host"
    podman ps --format 'table {{.Names}}\t{{.Status}}'
    ```

4. **Use the ochami CLI.** For provisioning issues, the `ochami-cli` provides direct access to the OpenCHAMI state manager for inspecting node inventory, boot status, and hardware state:

    ```bash title="Run on: omnia_core container"
    ochami smd component get
    ochami bss boot params get
    ```

5. **Search this section.** Browse the topic-specific pages below or use your browser's search (Ctrl+F) to find your symptom.

## Troubleshooting Topics

| Topic | Description |
| --- | --- |
| [General](general.md) | Core container failures, OIM issues, OpenCHAMI certificates, system recovery, InfiniBand, and Ansible Vault errors |
| [Provisioning](provisioning.md) | PXE boot failures, node discovery, cloud-init, local repository and Pulp issues |
| [Slurm](slurm.md) | Controller failures, node state issues, GPU/CUDA/DCGM, job submission, benchmarks, and accounting |
| [Kubernetes](kubernetes.md) | Control plane initialization, pod scheduling, DNS, storage, CSI drivers, and networking |
| [Telemetry](telemetry.md) | iDRAC telemetry, LDMS samplers, Kafka, VictoriaMetrics (cluster mode), VictoriaLogs, and Grafana |
| [Authentication](authentication.md) | LDAP bind failures, user login, OpenLDAP, and TLS certificate errors |
| [BuildStreaM](buildstream.md) | BuildStreaM pipeline stage failures, API registration, catalog parsing, and image deployment |
| [Upgrade and Rollback](upgrade_rollback.md) | Lock file conflicts, manifest tracking, component-specific upgrade/rollback failures, and kernel version override |
| [Known Limitations](known_limitations.md) | Current limitations, constraints, and known issues |

!!! tip

    If you cannot resolve an issue using this guide, open an issue on the
    [Omnia GitHub repository](https://github.com/dell/omnia/issues) with
    the relevant log output and a description of your environment.
