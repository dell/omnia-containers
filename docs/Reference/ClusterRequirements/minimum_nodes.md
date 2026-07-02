
# Minimum Node Counts


This page lists the minimum number of servers required for each Omnia
deployment scenario. The OIM (management node) is always required in addition
to the cluster nodes listed below.

## Node count summary


| Deployment Scenario | Min. Nodes | Node Breakdown |
| --- | --- | --- |
| **Slurm-only (Path A)** | 4 | 1 OIM + 1 Slurm control + 1 Slurm compute + 1 login node |
| **Full deployment (Path B)** | 8 | 1 OIM + 1 Slurm control + 1 Slurm compute + 1 login + 3 K8s control plane + 1 K8s worker (auth server may be co-located) |
| **K8s + Telemetry only (Path C)** | 5 | 1 OIM + 3 K8s control plane + 1 K8s worker |
| **BuildStreaM (Path D)** | 8+ | 1 OIM + 1 Slurm control + 1 Slurm compute + 1 login + 3 K8s control plane + 1 K8s worker (GitLab and runners on K8s) |

## Detailed breakdown by role


| Node Role | Slurm Only | Full | K8s + Tel. | BuildStreaM | Notes |
| --- | --- | --- | --- | --- | --- |
| OIM | 1 | 1 | 1 | 1 | Always exactly 1. Cannot be co-located with cluster roles. |
| slurm_control_node | 1 | 1 | -- | 1 | Runs slurmctld, slurmdbd, MariaDB. |
| slurm_node | 1+ | 1+ | -- | 1+ | Compute nodes. Scale out as needed. |
| login_node | 1 | 1 | -- | 1 | Optional but recommended. Can be omitted; users then SSH to the control node. |
| kube_control_plane | -- | 3 | 3 | 3 | 3 required for HA quorum. 1 is acceptable for non-HA (development only). |
| kube_node | -- | 1+ | 1+ | 1+ | Worker nodes for K8s pods. |
| auth_server | 0--1 | 0--1 | -- | 0--1 | Optional dedicated node. Authentication can run on an existing Slurm or K8s node. |

## Scaling guidelines


| Cluster Size | Recommendation |
| --- | --- |
| < 50 nodes | Standard OIM (4 cores, 32 GB RAM). Single Slurm control node. |
| 50--200 nodes | Upgraded OIM (8 cores, 64 GB RAM). Consider dedicated auth server. |
| 200--500 nodes | High-spec OIM (16 cores, 128 GB RAM). Dedicated login node(s). Add K8s workers for monitoring load. |
| 500+ nodes | Multiple login nodes. External NFS or PowerScale for /home. Increase Pulp storage. Consider external etcd for K8s HA. |

!!! note

    The OIM must remain a dedicated, standalone server. Do not co-locate
    Slurm or Kubernetes roles on the OIM -- this is unsupported and will
    cause resource contention with the management services.

!!! info

    - [Disk Space](disk_space.md) -- Disk requirements per node role.
    - [Ports](../../Overview/security_configuration_guide.md#host-port-requirements) -- Network ports required per role.
    - [Ha Config](../Configuration/ha_config.md) -- Kubernetes HA settings.
