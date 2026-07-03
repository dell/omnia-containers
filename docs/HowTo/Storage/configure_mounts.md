
# Configure Mounts

Configure storage mounts, PowerVault iSCSI volumes, and swap space for cluster nodes. All storage configuration is defined in `storage_config.yml`.

## Overview

The `storage_config.yml` file contains four sections:

- **mounts** -- Network and local storage mount definitions
- **mount_params** -- Named profiles for filesystem types and mount options
- **powervault_config** -- PowerVault iSCSI volume connection definitions
- **swap** -- Swap file configurations

!!! note

    Storage configuration is applied during node provisioning. Mounts can be targeted to specific node groups using `functional_group_prefix` or `groups`.

## Functional group prefix

The `functional_group_prefix` parameter uses **prefix matching** against the `FUNCTIONAL_GROUP_NAME` column in the PXE mapping file. All nodes whose functional group name **starts with** any listed prefix receive the mount, swap, or PowerVault configuration.

### Available functional group names

| Functional group name | Role |
| --- | --- |
| `slurm_control_node_x86_64` | Slurm controller (`slurmctld`, `slurmdbd`) |
| `slurm_node_x86_64` | Slurm compute node (x86_64) |
| `slurm_node_aarch64` | Slurm compute node (AArch64) |
| `login_node_x86_64` | Login/SSH access node (x86_64) |
| `login_node_aarch64` | Login/SSH access node (AArch64) |
| `login_compiler_node_aarch64` | Login node with compiler toolchain (AArch64) |
| `service_kube_control_plane_x86_64` | Kubernetes control plane |
| `service_kube_node_x86_64` | Kubernetes worker node |
| `os_x86_64` | Generic OS node (x86_64) |
| `os_aarch64` | Generic OS node (AArch64) |

### Prefix matching examples

| Prefix value | Matches |
| --- | --- |
| `["slurm"]` | `slurm_control_node_x86_64`, `slurm_node_x86_64`, `slurm_node_aarch64` (all Slurm nodes) |
| `["slurm_node"]` | `slurm_node_x86_64`, `slurm_node_aarch64` (compute nodes only, excludes controller) |
| `["slurm_control_node"]` | `slurm_control_node_x86_64` (controller only) |
| `["login"]` | `login_node_x86_64`, `login_node_aarch64`, `login_compiler_node_aarch64` (all login nodes) |
| `["service_kube"]` | `service_kube_control_plane_x86_64`, `service_kube_node_x86_64` (all Kubernetes nodes) |
| `["service_kube_node"]` | `service_kube_node_x86_64` (Kubernetes workers only) |
| `["os"]` | `os_x86_64`, `os_aarch64` (generic OS nodes only) |
| `["slurm", "login"]` | All Slurm nodes **and** all login nodes |
| `["slurm_node", "login"]` | Slurm compute nodes **and** login nodes (excludes Slurm controller) |

!!! tip

    Use shorter prefixes to target broader groups. For example, `["slurm"]` targets all Slurm roles, while `["slurm_node"]` targets only compute nodes.

## Mounts

Each mount entry specifies a source, mount point, and optional filesystem parameters.

--8<-- "html/storage_config-mounts.html"

### Example

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
mounts:
  - name: "nfs_slurm"
    source: "172.16.0.254:/mnt/share/omnia"
    mount_point: "/opt/omnia/slurm_mount"
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard,intr"
    mount_on_oim: true
    functional_group_prefix: ["slurm", "login"]

  - name: "nfs_k8s"
    source: "172.16.0.254:/mnt/share/omnia_k8s"
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
```

## Mount params

Named profiles that provide default values for filesystem type and mount options. Referenced by mounts and PowerVault entries via the `mount_params` field.

--8<-- "html/storage_config-mount_params.html"

### Example

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
mount_params:
  default:
    fs_type: "nfs"
    mnt_opts: "nfsvers=4.1,hard,intr,noatime,nconnect=16,rsize=1048576,wsize=1048576"
    dump_freq: "0"
    fsck_pass: "0"

  vast_rdma:
    fs_type: "nfs"
    mnt_opts: "proto=rdma,hard,intr,noatime,nconnect=16,rsize=1048576,wsize=1048576"
    dump_freq: "0"
    fsck_pass: "0"

  powervault_iscsi:
    fs_type: "xfs"
    mnt_opts: "defaults,_netdev,noatime,x-systemd.requires=iscsi.service"
    dump_freq: "0"
    fsck_pass: "0"
```

## PowerVault config

Defines PowerVault iSCSI volume connection parameters.

!!! warning

    PowerVault configuration requires proper iSCSI initiator setup and network connectivity to the PowerVault controllers.

--8<-- "html/storage_config-powervault_config.html"

### Example

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
powervault_config:
  - name: powervault1
    ip:
      - 172.1.2.3
    port: 3260
    iscsi_initiator: iqn.2025-01.com.dell:scontrol-node
    volume_id: 00c0ff4343f1f1f1001c8c4e6901000000
    mount_point: "/mnt/slurm"
    mount_params: "powervault_iscsi"
    node_key: "local_hostname"
    node_mount_point:
      - "/var/lib/mysql"
      - "/var/spool/slurm"
    functional_group_prefix: ["slurm_control_node"]
    permissions:
      owner: "slurm"
      group: "slurm"
      mode: "0750"
```

## Swap

Defines swap file configurations created during node provisioning.

--8<-- "html/storage_config-swap.html"

### Example

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
swap:
  - name: "compute_swap"
    filename: "/swapfile"
    size: "2G"
    maxsize: "4G"
    functional_group_prefix: ["slurm_node"]
```

!!! note

    After updating `storage_config.yml`, re-run the appropriate provisioning playbooks to apply the storage configuration to the nodes.

!!! info

    - [Storage Config Reference](../../Reference/Configuration/storage_config.md) -- `storage_config.yml` parameter tables and usage example.
    - [Configure NFS](configure_nfs.md) -- NFS-specific setup via `omnia_config.yml`.
    - [Configure PowerVault](configure_powervault.md) -- PowerVault storage integration.
    - [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md) -- Functional groups and `GROUP_NAME` values.
