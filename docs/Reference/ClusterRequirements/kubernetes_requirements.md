# Kubernetes Requirements

This section outlines the key requirements for the Service Kubernetes Cluster used by Omnia to deploy HPC clusters. For more information about the supported devices and software, see [Support Matrix](../index.md#support-matrix).

## Service Kubernetes Cluster

- A minimum of **three Kubernetes controller nodes** and **one kube node** must be available.
- Ensure that each Service Kubernetes Cluster node has at least 64 GB RAM.

### ETCD Storage Configuration

ETCD storage can be configured on local disk or NFS based on the `etcd_on_local_disk` parameter in `omnia_config.yml`. For detailed configuration information, see [Input Parameters for the Cluster](../Configuration/omnia_config.md) and [Set up High Availability (HA) Kubernetes on the Service Cluster](../../HowTo/Kubernetes/setup_service_k8s.md).

**When etcd_on_local_disk is set to true:**

- ETCD is deployed on the local disk of each Kubernetes service master node.
- The `/var/lib/etcd` directory is mounted on the selected local disk.
- **Disk Selection Priority**: The system prioritizes BOSS card (BOSS-N1/N2) if available. If BOSS card is not present, it falls back to SSD or SATA disks.
- **RAID Configuration**: BOSS cards must have RAID pre-configured (RAID 1 or RAID 10) before deployment. Omnia does not configure RAID automatically.
- Minimum disk size of 20 GB is recommended for ETCD data partition.

!!! warning

    Migration from NFS to local disk is not supported during upgrades. The `etcd_on_local_disk` configuration is only applicable for fresh installations.

**When etcd_on_local_disk is set to false or omitted:**

- ETCD storage is provisioned using NFS.
- No local disk configuration is performed for ETCD.
- Ensure the NFS server is reachable and has sufficient storage for ETCD data.

**Hardware Prerequisites for Local Disk Deployment:**

- Dell BOSS Card (BOSS-N1/N2) with pre-configured RAID 1 or RAID 10, OR
- SSD or SATA disks if BOSS card is not available
- Minimum disk size of 20 GB for ETCD data partition
- RAID must be pre-configured on BOSS cards before deployment (Omnia does not configure RAID automatically)
