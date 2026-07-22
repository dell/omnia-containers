
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

### Functional group prefix

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

## Prerequisites

- Access to edit `storage_config.yml` on the OIM host.
- NFS server IP address or DNS-resolvable hostname and export path, for NFS mounts.
- VAST storage appliance configured with NFS exports and access policies, for VAST mounts. See [Configure VAST Storage](configure_vast.md).
- iSCSI initiator setup and network connectivity to the PowerVault controllers, for PowerVault volumes.
- Functional group names defined in the PXE mapping file, to target mounts, swap, and PowerVault entries to specific node groups. See [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md).

## Procedure

### Mounts

Each mount entry specifies a source, mount point, and optional filesystem parameters.

--8<-- "html/storage_config-mounts.html"

**Example**

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

#### Configuring NFS shares

NFS is the most widely used storage mount type in Omnia clusters. NFS shares provide shared filesystems across compute, login, and controller nodes for home directories, application data, and Slurm spool directories.

When defining an NFS mount, the `source` field must use the format `server_ip:/export/path`. The NFS server IP or DNS-resolvable hostname must be reachable from all target nodes at boot time.

!!! tip

    - Use `hard,intr` mount options for production NFS shares. The `hard` option ensures the client retries indefinitely on server failure, while `intr` allows interrupted system calls.
    - Set `nconnect=16` for high-throughput workloads to open multiple TCP connections per mount.
    - Use `rsize=1048576,wsize=1048576` (1 MB) for large sequential I/O patterns common in HPC.
    - Set `mount_on_oim: true` if the OIM needs access to the same share (e.g., for Slurm accounting or shared configuration).

**NFS share for Slurm home directories with per-node isolation:**

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
mounts:
  - name: "nfs_home"
    source: "172.16.0.254:/mnt/share/home"
    mount_point: "/home"
    fs_type: "nfs"
    mnt_opts: "nfsvers=4.1,hard,intr,noatime,nconnect=16,rsize=1048576,wsize=1048576"
    mount_on_oim: true
    functional_group_prefix: ["slurm", "login"]
```

**NFS share using a named mount_params profile:**

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
mounts:
  - name: "nfs_app_data"
    source: "172.16.0.254:/mnt/share/appdata"
    mount_point: "/opt/appdata"
    mount_params: "default"
    mount_on_oim: false
    functional_group_prefix: ["slurm_node"]
```

When `mount_params` is specified, the `fs_type` and `mnt_opts` values are inherited from the named profile in the `mount_params` section. Inline `fs_type` and `mnt_opts` values override the profile.

!!! warning

    - NFS paths must be resolvable at boot time. Use IP addresses or DNS-resolvable hostnames.
    - Mount point paths must be unique across all mount entries.
    - Avoid system directories (`/etc`, `/sys`, `/proc`, `/boot`, `/root`, `/tmp`) as mount points.

#### Configuring VAST storage with RDMA

VAST Data Platform provides high-performance NFS storage that supports RDMA (Remote Direct Memory Access) transport. RDMA bypasses the kernel TCP/IP stack and transfers data directly between the NFS client and the VAST storage appliance memory, delivering significantly lower latency and higher throughput compared to standard TCP-based NFS.

RDMA-based VAST mounts are recommended for latency-sensitive HPC workloads such as AI/ML training, large-scale simulations, and checkpoint/restart operations on Slurm compute nodes.

**VAST mount with RDMA transport:**

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
mounts:
  - name: "vast_storage"
    source: "172.16.107.77:/share/vast"
    mount_point: "/mnt/vast"
    mount_params: "vast_rdma"
    mount_on_oim: true
    functional_group_prefix: ["slurm_node", "login"]
```

The `vast_rdma` mount_params profile uses `proto=rdma` to enable RDMA transport. The `nconnect=16` option opens multiple RDMA connections for parallel I/O, and `rsize=1048576,wsize=1048576` sets 1 MB read/write buffer sizes for optimal throughput.

**VAST mount with standard TCP transport (fallback):**

If the cluster network does not support RDMA (no InfiniBand or RoCE), use the `vast_nfs` profile with standard TCP transport:

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
mounts:
  - name: "vast_storage_tcp"
    source: "172.16.107.77:/share/vast"
    mount_point: "/mnt/vast"
    mount_params: "vast_nfs"
    mount_on_oim: true
    functional_group_prefix: ["slurm_node", "login"]
```

!!! note

    - RDMA transport requires InfiniBand or RoCE (RDMA over Converged Ethernet) connectivity between cluster nodes and the VAST appliance.
    - The VAST storage appliance must be configured with NFS exports and appropriate access policies before defining mounts. See [Configure VAST Storage](configure_vast.md) for VAST appliance setup.
    - The `slurm_cluster` section in `omnia_config.yml` should reference VAST storage via the `vast_storage_name` parameter.

#### K8s storage mounts

Service Kubernetes deployments require NFS mounts for persistent storage, Helm chart distribution, and shared application data. The `service_k8s_cluster` section in `omnia_config.yml` references these mounts by name.

**Primary NFS mount (`nfs_storage_name`)**

This mount stores Kubernetes persistent volumes, Helm charts, and shared application data. The NFS subdir provisioner creates persistent volumes backed by this share, allowing pods to store data that persists across pod restarts and node failures.

- Target all K8s control-plane and worker nodes using `functional_group_prefix: ["service_kube"]`.
- Set `mount_on_oim: true` so the OIM can populate initial configuration and Helm charts.
- The `name` field must match the `nfs_storage_name` value in `omnia_config.yml`.

```yaml title="Example: K8s NFS mount"
mounts:
  - name: "nfs_k8s"
    source: "172.16.0.254:/mnt/share/k8s"
    mount_point: "/mnt/k8s"
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard,intr"
    mount_on_oim: true
    functional_group_prefix: ["service_kube"]
```

For a complete explanation of what data lives on this mount, see [K8s Storage Architecture](../Kubernetes/setup_service_k8s.md#k8s-storage-architecture).

### Mount params

Named profiles that provide default values for filesystem type and mount options. Referenced by mounts and PowerVault entries via the `mount_params` field.

--8<-- "html/storage_config-mount_params.html"

**Example**

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

  vast_nfs:
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard"
    dump_freq: "0"
    fsck_pass: "0"

  powervault_iscsi:
    fs_type: "xfs"
    mnt_opts: "defaults,_netdev,noatime,x-systemd.requires=iscsi.service"
    dump_freq: "0"
    fsck_pass: "0"
```

### PowerVault config

Defines PowerVault iSCSI volume connection parameters.

!!! warning

    PowerVault configuration requires proper iSCSI initiator setup and network connectivity to the PowerVault controllers.

--8<-- "html/storage_config-powervault_config.html"

**Example**

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

### Swap

Defines swap file configurations created during node provisioning.

--8<-- "html/storage_config-swap.html"

**Example**

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

## Verification

1. Verify mounts are applied on target nodes:

    ```bash title="Run on: Target node"
    mount | grep <mount_point>
    ```

    Expected output shows the mount source, mount point, and filesystem type configured in `storage_config.yml`.

2. Verify NFS shares specifically:

    ```bash title="Run on: Target node"
    df -h <mount_point>
    ```

3. Verify PowerVault iSCSI sessions are active:

    ```bash title="Run on: Target node"
    iscsiadm -m session
    ```

4. Verify swap is enabled:

    ```bash title="Run on: Target node"
    swapon --show
    ```

    Expected output lists the configured swap file with its size.

## Troubleshooting

- **Mount does not appear on the target node**: Confirm the node's functional group name matches a `functional_group_prefix` value, and re-run the provisioning playbook. See [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md) to verify functional group names.
- **NFS mount fails or times out**: Verify the NFS server IP/hostname is reachable and resolvable from the target node at boot time, and that the export path exists on the server.
- **VAST RDMA mount fails to connect**: Confirm InfiniBand or RoCE connectivity between the node and the VAST appliance, and that the VAST appliance has NFS exports and access policies configured. See [Configure VAST Storage](configure_vast.md).
- **PowerVault volume does not mount**: Verify iSCSI initiator configuration and network connectivity to the PowerVault controllers. See [Configure PowerVault](configure_powervault.md).

!!! info

    - [Storage Config Reference](../../Reference/Configuration/storage_config.md) -- `storage_config.yml` parameter tables and usage example.
    - [Configure VAST](configure_vast.md) -- VAST storage setup.
    - [Configure PowerVault](configure_powervault.md) -- PowerVault iSCSI setup.
    - [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md) -- Functional groups and `GROUP_NAME` values.
