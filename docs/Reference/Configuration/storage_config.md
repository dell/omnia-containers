
# storage_config.yml Reference

File path: `/opt/omnia/input/project_default/storage_config.yml`

This file configures shared storage for the cluster, including NFS mounts,
Dell PowerScale/PowerVault and swap configuration.

## Mounts
--8<-- "html/storage_config-mounts.html"
## Mount_params
--8<-- "html/storage_config-mount_params.html"
## PowerVault
--8<-- "html/storage_config-powervault_config.html"
## Swap
--8<-- "html/storage_config-swap.html"
## S3
--8<-- "html/storage_config-s3_configurations.html"
## Usage example
```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
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

s3_configurations:
  provider: "powerscale"
  endpoint_url: ""
```


!!! info

    - [Storage](../SupportMatrix/storage.md) -- Supported storage platforms.
    - [Disk Space](../ClusterRequirements/disk_space.md) -- Disk space requirements.
