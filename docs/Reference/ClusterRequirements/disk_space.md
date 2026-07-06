# Disk Space Requirements

Omnia 2.2 uses a stateless (diskless) provisioning model. Cluster nodes PXE boot from network-delivered images and run entirely from RAM. The OIM builds and serves these images, hosts all software repositories, and stores provisioning state. This page documents disk and memory requirements for each node role.

## Diskless provisioning model

Cluster nodes do not require local OS disks. During PXE boot, the OIM serves a kernel (`vmlinuz`), initial ramdisk (`initrd.img`), and root filesystem image (`rootfs.img`) over the network. The node loads the root filesystem into RAM and operates statelessly. Node replacement requires only a hardware swap and PXE reboot.

!!! warning

    Cluster nodes require sufficient RAM to hold the root filesystem image in memory in addition to workload requirements. At least **64 GB of RAM** is recommended.

## Disk space summary

| Node Role | Minimum Disk | Notes |
| --- | --- | --- |
| **OIM (Management Node)** | 256 GB | Hosts Pulp repos, boot images (S3), containers, PostgreSQL, ISO files, logs. SSD recommended. |
| **Service K8s Node** | 200 GB of shared storage | For container images, persistent volumes, and telemetry data (VictoriaMetrics, Kafka). |
| **NFS Server (external)** | 200 GB+ | Shared storage for `/home`, Slurm spool, scratch space. Size depends on user count and workload. |
| **Slurm / Login / OS Nodes** | No local disk required | Diskless boot from OIM. Persistent data stored on NFS. Optional local scratch disk for temporary job data. |

!!! note

    For nodes with limited or no local storage, configure NFS mounts in `storage_config.yml` to provide persistent storage for Slurm spool, job data, and user home directories. See [Configure Mounts](../../HowTo/Storage/configure_mounts.md).

## Detailed OIM disk allocation

The OIM is the most storage-intensive node in the cluster. All software packages, boot images, and provisioning infrastructure reside on this node.

| Component | Space | Notes |
| --- | --- | --- |
| RHEL OS | ~20 GB | Server installation profile. |
| Pulp repository mirror | ~150 GB | Mirrors RHEL BaseOS, AppStream, EPEL, CUDA/ROCm, Kubernetes repos. Size varies with enabled repositories. |
| Container images (Podman) | ~30 GB | OpenCHAMI, Pulp, omnia_core, and other OIM containers. |
| Boot images (S3) | ~10 GB | Built `rootfs.img`, `vmlinuz`, `initrd.img` per architecture and functional group. Stored in MinIO S3 (`s3://boot-images/`). |
| ISO images | ~10 GB | RHEL ISO(s) used for image building. |
| PostgreSQL (BuildStreaM) | ~30 GB | GitLab and BuildStreaM pipeline database. Required only when BuildStreaM is deployed. |
| Omnia logs and configuration | ~30 GB | Ansible logs, OpenCHAMI logs, DHCP/TFTP logs, configuration state. |

!!! note

    The 256 GB minimum assumes a single architecture (x86_64). If provisioning both x86_64 and AArch64 nodes, add approximately 80 GB for the second repository mirror and boot image set.

## Software package sizes on OIM / NFS share

The following table lists the disk utilization for software packages that Omnia installs and serves to cluster nodes.

| Software | Disk Utilization |
| --- | --- |
| Slurm | 5 GB |
| Kubernetes | 7 GB |
| Default packages | 1.2 GB |
| LDMS (Lightweight Distributed Metric Service) | 1 GB |

!!! tip

    Total software package footprint is approximately **15 GB**. Boot images for all functional groups require an additional **~10 GB**. These are included in the OIM 256 GB minimum.

## Telemetry data sizing

Telemetry components run on Service Kubernetes nodes and require local disk for time-series data and log retention.

| Component | Growth Rate | Notes |
| --- | --- | --- |
| Kafka logs | ~1 GB/day per 100 nodes | Retained for `kafka_retention_hours` (default 168 hours). Purged automatically. |
| VictoriaMetrics | ~500 MB/day per 100 nodes | Retained for `victoriametrics_retention` months. Compressed on disk. |
| Grafana | Negligible | Dashboard definitions only; no metric data stored in Grafana. |

!!! tip

    For clusters with 200+ nodes and 6-month retention, allocate at least 500 GB on the telemetry K8s node for VictoriaMetrics data.

## Filesystem recommendations

| Mount Point | Recommended FS | Applies To | Notes |
| --- | --- | --- | --- |
| `/` (root) | XFS | OIM, K8s nodes | Default RHEL filesystem. Supports large files efficiently. |
| `/var/lib/pulp` | XFS on SSD | OIM | High I/O during repository sync. SSD strongly recommended. |
| `/var/lib/victoria-metrics` | XFS on SSD | K8s telemetry node | Sequential write workload benefits from SSD. |
| `k8s_shared_storage` | NFS | Service K8s nodes | Shared storage for container images, persistent volumes, and telemetry data. |
| `slurm_mount` | NFS | Slurm nodes | Slurm spool and shared state via NFS mount. |

## Memory requirements

Since cluster nodes run diskless with the root filesystem in RAM, memory sizing is critical.

| Node Role | Minimum RAM | Notes |
| --- | --- | --- |
| OIM | 64 GB | Runs Pulp, OpenCHAMI, MinIO, and build processes concurrently. |
| Slurm compute node | 64 GB | Root filesystem in RAM (~3 GB) plus workload memory. |
| Service K8s node | 64 GB | Root filesystem in RAM plus container workloads (telemetry, monitoring). |
| Login node | 64 GB | Root filesystem in RAM plus user sessions and compilers. |

!!! info

    - [Minimum Nodes](minimum_nodes.md) -- Minimum node counts per scenario.
    - [Storage Config](../Configuration/storage_config.md) -- NFS configuration.
    - [Local Repo Config](../Configuration/local_repo_config.md) -- Pulp repository storage path.
    - [Configure Mounts](../../HowTo/Storage/configure_mounts.md) -- Mount configuration for diskless nodes.
