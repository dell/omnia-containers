
# storage_config.yml

This file configures shared storage for the cluster, including NFS and VAST
Data mounts, Dell PowerScale/PowerVault, and swap configuration.

## Parameter Reference
### Mounts Configuration
--8<-- "html/storage_config-mounts.html"
### Mount_params Configuration
--8<-- "html/storage_config-mount_params.html"
### PowerVault Configuration
--8<-- "html/storage_config-powervault_config.html"
### Swap Configuration
--8<-- "html/storage_config-swap.html"

S3 endpoint configuration is not part of `storage_config.yml`. Orchestrator
loads the authoritative S3 endpoint and bucket from Image Build Manager's
generated `build_status.yml` contract.

## Usage example
```yaml title="File: $OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/storage_config.yml"
---
mounts:
  - name: "nfs_slurm"
    source: "172.16.107.168:/mnt/share/omnia"
    mount_point: "/share_omnia"
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard,intr"
    mount_on_oim: true
    functional_group_prefix: ["slurm", "login"]

  - name: "nfs_k8s"
    source: "172.16.107.121:/mnt/share/omnia_k8s"
    mount_point: "/opt/omnia/k8s_mount"
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard,intr"
    mount_on_oim: true
    functional_group_prefix: ["service_kube"]

  # Optional: include only when using a separate VAST storage appliance
  - name: "vast_storage"
    source: "172.16.107.77:/share/vast"
    mount_point: "/mnt/vast"
    mount_params: "vast_rdma"
    mount_on_oim: true
    functional_group_prefix: ["slurm_node", "login"]

mount_params:
  # Default NFS mount
  nfs_default:
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard"
    dump_freq: "0"
    fsck_pass: "0"

  # VAST NFS RDMA storage over IB - standard configuration
  vast_rdma:
    fs_type: "nfs"
    mnt_opts: "proto=rdma,nconnect=8,timeo=600,retrans=2,rsize=1048576,wsize=1048576,hard"

  vast_tcp:
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard"

  # PowerScale NFS share (Kubernetes or Slurm nfs_storage_name)
  powerscale_nfs:
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard,intr,rsize=946176,wsize=946176,nosharecache"
    node_nfs_mnt_opts: "rsize=946176,wsize=946176,nosharecache"

  # PowerVault iSCSI storage - block device with XFS
  powervault_iscsi:
    fs_type: "xfs"
    mnt_opts: "defaults,_netdev,noatime,x-systemd.requires=iscsi.service"
    dump_freq: "0"
    fsck_pass: "0"

powervault_config:
  - name: powervault1
    ip:
      - 172.1.2.3
    port: 3260
    iscsi_initiator: iqn.2025-01.com.dell:scontrol-node
    volume_id: 00c0ff4343f1f1f1001c8c4e6901000000
    # mount params
    mount_point: "/mnt/slurm"
    mount_params: "powervault_iscsi"
    node_key: "local_hostname" # per_node_id,node_subdir_key
    node_mount_point: # bind_paths, sub_mounts
      - "/var/lib/mysql" # /mnt/slurm/<local_hostname>/var/lib/mysql
      - "/var/spool/slurm" # /mnt/slurm/<local_hostname>/var/spool/slurm
    functional_group_prefix: ["slurm_control_node"]
    permissions:
      owner: "slurm"
      group: "slurm"
      mode: "0750"

swap:
  - name: "compute_swap"
    filename: "/swapfile"
    size: "2G"
    maxsize: "4G"
    functional_group_prefix: ["slurm_node"]
```

The standard optional Slurm VAST mount uses `name: vast_storage`. Orchestrator
includes it only when `slurm_cluster[0].vast_storage_name` is non-empty and
references that name. When `vast_storage_name` is empty or omitted, the
standard `vast_storage` entry is skipped and the selected Slurm NFS mount
supplies the shared-data and HPC-tools paths. No additional storage role field
is supported or required.

### PowerScale NFS mount options

Orchestrator creates per-node NFS sub-mounts from the storage entry named by
`nfs_storage_name` in `omnia_config.yml`. Use `node_nfs_mnt_opts` to set their
mount options:

- Kubernetes: `/var/lib/kubelet`, `/var/lib/etcd`, `/etc/kubernetes`,
  `/var/log/pods`, and `/var/lib/packages`. The value is also passed to the
  nfs-client provisioner. Default: `noatime,nolock`.
- Slurm and login nodes: `/etc/slurm`, `/etc/munge`, `/var/spool/slurmd`,
  `/var/log/slurm`, and `/cert`. Default: `defaults,_netdev`.

A `node_nfs_mnt_opts` value on a mount entry takes priority over the
`mount_params` profile and replaces the defaults instead of being appended to
them.

!!! warning

    For Slurm mounts, a custom `node_nfs_mnt_opts` value on a mount entry
    replaces `defaults,_netdev`. Include `defaults,_netdev` in the value to keep
    network-dependent boot ordering, for example
    `defaults,_netdev,rsize=946176,wsize=946176,nosharecache`.

RHEL 10.x clients can return Input/output errors on PowerScale at the default
1 MiB NFS transfer size. For a PowerScale NFS share, set `mount_params` to the
`powerscale_nfs` profile and remove `mnt_opts` and `node_nfs_mnt_opts` from the
mount entry. The profile sets `rsize` and `wsize` to 946176 (924 KiB) and adds
`nosharecache` so the transfer size takes effect even when the same export is
already mounted on the node. Over TCP, the kernel rounds `rsize` and `wsize`
down to a multiple of 4096 (946176 = 231 x 4096).

```yaml
mounts:
  - name: "nfs_k8s"
    source: "<powerscale_ip>:/ifs/<path>"
    mount_point: "/opt/omnia/k8s_mount"
    mount_params: "powerscale_nfs"
    functional_group_prefix: ["service_kube"]
```

PowerScale CSI volumes are configured separately through
`csi_powerscale_mount_options` in `omnia_config.yml`.

!!! note "VAST storage is not enabled by default"

    The default `storage_config.yml` does not include a `vast_storage` mount.
    To use a separate VAST mount for HPC tools and benchmarks, add a mount
    named `vast_storage` with `mount_on_oim: true` and
    `functional_group_prefix: ["slurm_node", "login"]`, and set
    `vast_storage_name: vast_storage` in `omnia_config.yml`. For RDMA over
    InfiniBand, set `mount_params: "vast_rdma"`. The VAST server must be
    reachable from the OIM during provisioning.


!!! info

    - [Configure Mounts](../../HowTo/orchestrator/configure_storage.md) -- Detailed how-to for mounts, mount_params, PowerVault, and swap.
    - [Slurm Storage Architecture](../../HowTo/orchestrator/deploy_slurm.md#slurm-storage-architecture) -- How Slurm uses NFS and VAST mounts.
    - [K8s Storage Architecture](../../HowTo/orchestrator/deploy_kubernetes.md#k8s-storage-architecture) -- How service K8s uses NFS mounts.
    - [Storage Requirements](../../Reference/../Reference/ClusterRequirements/storage_requirements.md) -- Storage sizing and prerequisites.
    - [Storage](../SupportMatrix/storage.md) -- Supported storage platforms.
    - [Disk Space](../../Reference/../Reference/ClusterRequirements/disk_space.md) -- Disk space requirements.















