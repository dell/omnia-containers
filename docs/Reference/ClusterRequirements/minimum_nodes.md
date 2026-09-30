# Minimum Node Counts

This page lists the minimum number of servers required for each Omnia deployment scenario, categorized by functional role and architecture.

## Slurm + Kubernetes -- x86_64 and aarch64

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

## Slurm + Kubernetes -- x86_64

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

!!! note

    The Service Kubernetes Node quantity in the Slurm and Kubernetes tables is
    the baseline minimum. Size the service Kubernetes cluster for the required
    availability and workload capacity.

## Slurm -- x86_64

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

## Kubernetes + Telemetry -- x86_64

| Role | Architecture | Quantity |
| --- | --- | --- |
| Omnia Infrastructure Manager (OIM) | x86_64 | 1 |
| Service Kubernetes Control Plane | x86_64 | 3 |
| Service Kubernetes Node | x86_64 | 1 |

**Total: 5 nodes**

### Role descriptions

| Role | Functional Group | Description |
| --- | --- | --- |
| OIM | -- | Management node. Runs Pulp, OpenCHAMI, provisioning services, and local MinIO when selected. Always exactly 1. Cannot be co-located with cluster roles. |
| Service K8s Control Plane | `service_kube_control_plane_<os>_<version>_x86_64` | Runs Kubernetes API server, etcd, scheduler, and controller-manager. 3 required for HA quorum. |
| Service K8s Node | `service_kube_node_<os>_<version>_x86_64` | Kubernetes worker node. Hosts telemetry pods and application workloads. |
| Slurm Control Node | `slurm_control_node_<os>_<version>_x86_64` | Runs `slurmctld`, `slurmdbd`, and MariaDB for job accounting. |
| Slurm Node | `slurm_node_<os>_<version>_<architecture>` | Compute nodes running `slurmd`. Scale out as needed. |
| Login Node | `login_node_<os>_<version>_<architecture>` | Interactive SSH access for users to submit jobs. Runs `slurmd`. |
| Login Compiler Node | `login_compiler_node_<os>_<version>_<architecture>` | Login node with compiler toolchain. |

Kubernetes rows in the PXE mapping must use catalog-qualified names, such as
`service_kube_control_plane_rhel_10_0_x86_64` or
`service_kube_control_plane_rhel_10_2_x86_64`. Use the same catalog-selected
RHEL minor version for every Kubernetes control-plane and worker node. Other
supported roles can use the naming form defined by their selected catalog.

!!! note

    The OIM must remain a dedicated, standalone server. Do not co-locate Slurm or Kubernetes roles on the OIM.

!!! info

    - [Disk Space](disk_space.md) -- Disk and memory requirements per node role.
    - [Ports](../../SecurityConfigurationGuide/network_security.md#firewall-settings) -- Network ports required per role.
    - [HA Config](../Configuration/high_availability_config.md) -- Kubernetes HA settings.
