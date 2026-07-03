
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

## Mounts

Each mount entry specifies a source, mount point, and optional filesystem parameters.

### Required fields

| Parameter | Description |
| --- | --- |
| `name` | Unique identifier (pattern: `[a-zA-Z0-9_-]`, 1--64 characters). |
| `source` | Device or network path. NFS: `192.168.1.100:/export/share`. Local: `/dev/sdc`, `UUID=xxx`, `LABEL=xxx`. CIFS: `//server/share`. |
| `mount_point` | Absolute path for the mount point. Must be unique across all entries. Avoid system directories (`/etc`, `/sys`, `/proc`, `/boot`, `/root`, `/tmp`). |

One of the following node targeting parameters is required (mutually exclusive):

| Parameter | Description |
| --- | --- |
| `functional_group_prefix` | List of functional group name prefixes. All nodes whose group name starts with any listed prefix receive this mount. Example: `["slurm"]` matches `slurm_control_node`, `slurm_node`, etc. |
| `groups` | List of `GROUP_NAME` values from the PXE mapping file. Only nodes in the listed groups receive this mount. |

### Optional fields

| Parameter | Default | Description |
| --- | --- | --- |
| `fs_type` | `auto` | Filesystem type: `auto`, `ext2`, `ext3`, `ext4`, `xfs`, `nfs`, `nfs4`, `cifs`, `tmpfs`, `cephfs`, `vfat`, `ntfs`, `none`, `fuse.s3fs`. Overrides `mount_params` profile. |
| `mnt_opts` | -- | Mount options string (e.g., `defaults,noexec,nofail`). Takes priority over `mount_params` profile. |
| `dump_freq` | `0` | Dump frequency (`0`, `1`, or `2`). |
| `fsck_pass` | `0` | Fsck pass number (`0` through `9`). |
| `mount_params` | -- | Name of a `mount_params` profile to use for unspecified fields. |
| `mount_on_oim` | `false` | Mount this filesystem on the OIM node. Ensure storage is network-accessible from OIM. |

### Node-specific bind mounts

| Parameter | Description |
| --- | --- |
| `node_key` | Per-node subdirectory variable: `local_hostname`, `local_ipv4`, or `instance_id`. When set, `node_mount_point` is required. Generates bind mounts: `<mount_point>/<node_key_value>/<target>` → `<target>`. |
| `node_mount_point` | List of bind mount target paths. Required when `node_key` is set. Values must be unique absolute paths. |

!!! note

    When `node_key` is specified, `fs_type` is forced to `none` and `mnt_opts` is forced to `bind`.

### Permissions

| Parameter | Default | Description |
| --- | --- | --- |
| `permissions.owner` | `root` | User owner of the mount point. |
| `permissions.group` | `root` | Group owner of the mount point. |
| `permissions.mode` | `0755` | Octal permission string (e.g., `0755`, `1777`). |

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

| Parameter | Description |
| --- | --- |
| `fs_type` | Filesystem type (e.g., `nfs`, `xfs`, `ext4`). |
| `mnt_opts` | Mount options (comma-separated). |
| `dump_freq` | Dump frequency (usually `0`). |
| `fsck_pass` | Fsck pass number (usually `0` or `2`). |

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

### Parameters

| Parameter | Required | Description |
| --- | --- | --- |
| `name` | Yes | Unique identifier for this PowerVault volume. |
| `ip` | Yes | List of target controller IP addresses for iSCSI discovery. |
| `port` | No | TCP port for iSCSI target (default: `3260`). |
| `iscsi_initiator` | Yes | iSCSI initiator IQN. |
| `volume_id` | Yes | Volume identifier (hex string / WWN) for multipath device matching. |
| `mount_point` | Yes | Where the discovered device gets mounted. |
| `fs_type` | No | Filesystem type (overrides `mount_params` profile). |
| `mnt_opts` | No | Mount options (overrides `mount_params` profile). |
| `mount_params` | No | Named profile for `fs_type`/`mnt_opts`. |
| `node_key` | No | Per-node subdirectory variable (same behavior as mounts). |
| `node_mount_point` | No | Bind mount target paths (required when `node_key` is set). |
| `functional_group_prefix` | No | List of functional group prefixes for node targeting. |
| `permissions` | No | Directory ownership and mode (`owner`, `group`, `mode`). |

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

| Parameter | Required | Description |
| --- | --- | --- |
| `filename` | Yes | Path to the swap file to create. |
| `size` | Yes | Size in bytes, `auto`, or human-readable format (`2G`, `512M`). |
| `maxsize` | No | Maximum size (used with `size: auto`). |
| `functional_group_prefix` | No | List of functional group prefixes to apply this swap to. |

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
