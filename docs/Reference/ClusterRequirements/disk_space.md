
# Disk Space Requirements


This page documents the minimum disk space requirements for each node role
in an Omnia deployment.

## Disk space summary


| Node Role | Minimum Disk | Breakdown |
| --- | --- | --- |
| **OIM (Management Node)** | 256 GB | OS: ~20 GB. Pulp repo mirror: ~150 GB. Container images: ~30 GB. Logs and working space: ~56 GB. SSD recommended for Pulp performance. |
| **Slurm Control Node** | 50 GB | OS: ~10 GB. Slurm state (`StateSaveLocation`): ~5 GB. MariaDB (job accounting): ~20 GB. Logs: ~15 GB. |
| **Slurm Compute Node** | 50 GB | OS: ~10 GB. Slurm spool: ~5 GB. Temporary job data: ~30 GB. GPU drivers (if applicable): ~5 GB. |
| **Login Node** | 50 GB | OS: ~10 GB. User tools and compilers: ~20 GB. Logs: ~20 GB. |
| **K8s Control Plane** | 200 GB | OS: ~10 GB. etcd data: ~20 GB. Container images: ~50 GB. Telemetry data (VictoriaMetrics): ~100 GB. Logs: ~20 GB. |
| **K8s Worker Node** | 200 GB | OS: ~10 GB. Container images: ~50 GB. Persistent volumes (local): ~120 GB. Logs: ~20 GB. |
| **Auth Server** | 50 GB | OS: ~10 GB. LDAP database: ~5 GB. Logs: ~35 GB. |
| **NFS Server (external)** | 200 GB+ | Repository mirror data (if serving as Pulp mirror target): ~150 GB. Shared home directories and scratch: remainder. |

## Detailed OIM disk allocation


| Component | Space | Notes |
| --- | --- | --- |
| RHEL 10.0 OS | ~20 GB | Server with GUI installation profile. |
| Pulp repository mirror | ~150 GB | Mirrors RHEL BaseOS, AppStream, EPEL, CUDA/ROCm, K8s repos. Size varies with enabled repositories. |
| Container images (Podman) | ~30 GB | OpenCHAMI, Pulp, omnia_core, and other OIM containers. |
| ISO images | ~10 GB | RHEL 10.0 ISO(s) used for image building. |
| Provisioning images | ~20 GB | Built images (x86_64 and/or AArch64). |
| Logs and temp | ~26 GB | Ansible logs, OpenCHAMI logs, DHCP/TFTP logs. |

!!! note

    The 256 GB minimum assumes a single architecture (x86_64). If provisioning
    both x86_64 and AArch64 nodes, add approximately 80 GB for the second
    repository mirror and image.

## Telemetry data sizing


| Component | Growth Rate | Notes |
| --- | --- | --- |
| Kafka logs | ~1 GB/day per 100 nodes | Retained for `kafka_retention_hours` (default 168 hours). Purged automatically. |
| VictoriaMetrics | ~500 MB/day per 100 nodes | Retained for `victoriametrics_retention` months. Compressed on disk. |
| Grafana | Negligible | Dashboard definitions only; no metric data stored in Grafana. |

!!! tip

    For clusters with 200+ nodes and 6-month retention, allocate at least
    500 GB on the telemetry K8s node for VictoriaMetrics data.

## Filesystem recommendations


| Mount Point | Recommended FS | Notes |
| --- | --- | --- |
| `/` (root) | XFS | Default RHEL filesystem. Supports large files efficiently. |
| `/var/lib/pulp` | XFS on SSD | High I/O during repository sync. SSD strongly recommended. |
| `/var/lib/victoria-metrics` | XFS on SSD | Sequential write workload benefits from SSD. |
| `/home` (shared) | NFS (PowerScale) | Shared across all nodes via NFS. |

!!! info

    - [Minimum Nodes](minimum_nodes.md) -- Minimum node counts per scenario.
    - [Storage Config](../Configuration/storage_config.md) -- NFS and BeeGFS mount
      configuration.
    - [Local Repo Config](../Configuration/local_repo_config.md) -- Pulp repository
      storage path.
