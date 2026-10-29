# Kubernetes Requirements

This section outlines the key requirements for the Service Kubernetes Cluster used by Omnia to deploy HPC clusters.

## Minimum Requirements

- A minimum of **three Kubernetes controller nodes** and **one kube node** must be available.
- Ensure that each Service Kubernetes Cluster node has at least 64 GB RAM.

## ETCD Storage Configuration

ETCD storage can be configured on local disk or NFS based on the `etcd_on_local_disk` parameter in `omnia_config.yml`. For detailed configuration information, see [Input Parameters for the Cluster](../Configuration/omnia_config.md) and [Set up Service Kubernetes](../../HowTo/orchestrator/deploy_kubernetes.md).

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
- Ensure virtual disk is configured on all the nodes if SSD or SATA enabled and if BOSS is not available
- Minimum disk size of 20 GB for ETCD data partition
- RAID must be pre-configured on BOSS cards before deployment (Omnia does not configure RAID automatically). This applies to SSD or SATA disks as well.

## Shared Storage Requirements

Service Kubernetes requires shared storage mounts for persistent storage, Helm chart distribution, and shared application data. Omnia uses NFS mounts for the service K8s cluster.

### Primary NFS mount

- An NFS server with at least **200 GB** of available storage is required for
  the supported small-cluster baseline. Increase it based on cluster size,
  application data, and telemetry retention.
- The NFS share must be accessible from the OIM, all K8s control-plane nodes, and all K8s worker nodes.
- The NFS share must be exported with `no_root_squash` and **755 permissions**.
- Omnia uses this mount to store and distribute:
    - Kubernetes persistent volumes (backed by NFS subdir provisioner)
    - Helm charts and their values files
    - Shared application data and configuration
- Set `mount_on_oim: true` in `storage_config.yml` so the OIM can write initial configuration and Helm charts during provisioning.
- The `name` field in `storage_config.yml` must match the `nfs_storage_name` value in `omnia_config.yml`.

For details on what data lives on this mount, see [K8s Storage Architecture](../../HowTo/orchestrator/deploy_kubernetes.md#k8s-storage-architecture).

!!! info

    - [Set Up Service Kubernetes](../../HowTo/orchestrator/deploy_kubernetes.md) -- For detailed information on setting up the Service Kubernetes cluster with ETCD storage configuration.
    - [Kubernetes Configuration](../Configuration/omnia_config.md#kubernetes-configuration-parameters) -- For detailed information on Kubernetes configuration parameters.

















