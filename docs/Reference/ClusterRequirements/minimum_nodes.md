# Minimum Node Counts

This page lists the minimum number of servers required for each Omnia deployment scenario, categorized by functional role and architecture.

## Full deployment (Slurm + Service Kubernetes) -- x86_64 and aarch64

| Role | Architecture | Quantity |
| --- | --- | --- |
| Omnia Infrastructure Manager (OIM) | x86_64 | 1 |
| Service Kubernetes Control Plane | x86_64 | 3 |
| Service Kubernetes Node | x86_64 | 1 |
| Slurm Control Node | x86_64 | 1 |
| Slurm Node | aarch64 | 1 |
| Login Node | aarch64 | 1 |
| Login Compiler Node | aarch64 | 1 |

**Total: 9 nodes**

## Full deployment (Slurm + Service Kubernetes) -- x86_64 only

| Role | Architecture | Quantity |
| --- | --- | --- |
| Omnia Infrastructure Manager (OIM) | x86_64 | 1 |
| Service Kubernetes Control Plane | x86_64 | 3 |
| Service Kubernetes Node | x86_64 | 1 |
| Slurm Control Node | x86_64 | 1 |
| Slurm Node | x86_64 | 1 |
| Login Node | x86_64 | 1 |
| Login Compiler Node | x86_64 | 1 |

**Total: 9 nodes**

## Slurm-only deployment -- x86_64

| Role | Architecture | Quantity |
| --- | --- | --- |
| Omnia Infrastructure Manager (OIM) | x86_64 | 1 |
| Slurm Control Node | x86_64 | 1 |
| Slurm Node | x86_64 | 1 |
| Login Node | x86_64 | 1 |
| Login Compiler Node | x86_64 | 1 |

!!! note
    One of either Login Node or Login Compiler Node is required.

**Total: 5 nodes**

## Kubernetes + Telemetry deployment -- x86_64

| Role | Architecture | Quantity |
| --- | --- | --- |
| Omnia Infrastructure Manager (OIM) | x86_64 | 1 |
| Service Kubernetes Control Plane | x86_64 | 3 |
| Service Kubernetes Node | x86_64 | 1 |

**Total: 5 nodes**

## Role descriptions

| Role | Functional Group | Description |
| --- | --- | --- |
| OIM | -- | Management node. Runs Pulp, OpenCHAMI, MinIO, and provisioning services. Always exactly 1. Cannot be co-located with cluster roles. |
| Service K8s Control Plane | `service_kube_control_plane_x86_64` | Runs Kubernetes API server, etcd, scheduler, and controller-manager. 3 required for HA quorum. |
| Service K8s Node | `service_kube_node_x86_64` | Kubernetes worker node. Hosts telemetry pods (Kafka, VictoriaMetrics, Grafana) and application workloads. |
| Slurm Control Node | `slurm_control_node_x86_64` | Runs `slurmctld`, `slurmdbd`, and MariaDB for job accounting. |
| Slurm Node | `slurm_node_x86_64`, `slurm_node_aarch64` | Compute nodes running `slurmd`. Scale out as needed. |
| Login Node | `login_node_x86_64`, `login_node_aarch64` | Interactive SSH access for users to submit jobs. Runs `slurmd`. |
| Login Compiler Node | `login_compiler_node_aarch64` | Login node with compiler toolchain for cross-compilation on AArch64. |

!!! note

    The OIM must remain a dedicated, standalone server. Do not co-locate Slurm or Kubernetes roles on the OIM.

!!! info

    - [Disk Space](disk_space.md) -- Disk and memory requirements per node role.
    - [Ports](ports.md) -- Network ports required per role.
    - [HA Config](../Configuration/high_availability_config.md) -- Kubernetes HA settings.
