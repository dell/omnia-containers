
# Configure Mounts

Configure storage mounts, PowerVault iSCSI volumes, and swap space for cluster nodes. All storage configuration is defined in `storage_config.yml`.

## Overview

The `storage_config.yml` file contains four sections:

- **mounts** -- Network and local storage mount definitions
- **mount_params** -- Named profiles for filesystem types and mount options
- **powervault_config** -- PowerVault iSCSI volume connection definitions
- **swap** -- Swap file configurations

!!! note

    Storage configuration is applied during node provisioning. Entries in
    `mounts` must use exactly one targeting method: `functional_group_prefix`
    or exact `groups`.
    `powervault_config` and `swap` use `functional_group_prefix`.

### Functional group prefix

The `functional_group_prefix` parameter uses **prefix matching** against the `FUNCTIONAL_GROUP_NAME` column in the PXE mapping file. All nodes whose functional group name **starts with** any listed prefix receive the mount, swap, or PowerVault configuration.

### Available functional group names

The following examples match the staged RHEL 10.0 input and include its
operating-system, version, and architecture suffixes. Always copy the exact
`FUNCTIONAL_GROUP_NAME` from the active project's PXE mapping file.

| Functional group name | Role |
| --- | --- |
| `os_rhel_10_0_x86_64` | Generic OS node (x86_64) |
| `slurm_control_node_rhel_10_0_x86_64` | Slurm controller (`slurmctld`, `slurmdbd`) |
| `login_node_rhel_10_0_x86_64` | Login/SSH access node (x86_64) |
| `service_kube_control_plane_rhel_10_0_x86_64` | Kubernetes control-plane node |
| `service_kube_node_rhel_10_0_x86_64` | Kubernetes worker node |
| `os_rhel_10_0_aarch64` | Generic OS node (AArch64) |
| `slurm_node_rhel_10_0_aarch64` | Slurm compute node (AArch64) |
| `login_compiler_node_rhel_10_0_aarch64` | Login node with compiler toolchain (AArch64) |

During provisioning, Orchestrator internally renames the first control-plane
group to `service_kube_control_plane_first_rhel_10_0_x86_64`. That internal
name is not a catalog entry and must not be placed in the PXE mapping file.
Other supplied catalogs can define additional role-and-architecture
combinations; use only names supported by the active catalog.

### Prefix matching examples

| Prefix value | Matches |
| --- | --- |
| `["slurm"]` | All names beginning with `slurm_`, including controller and compute groups |
| `["slurm_node"]` | All names beginning with `slurm_node_` (compute nodes only) |
| `["slurm_control_node"]` | All names beginning with `slurm_control_node_` (controllers only) |
| `["login"]` | All names beginning with `login_node_` or `login_compiler_node_` |
| `["service_kube"]` | All names beginning with `service_kube_` (control-plane and worker groups) |
| `["service_kube_node"]` | All names beginning with `service_kube_node_` (workers only) |
| `["os"]` | All names beginning with `os_` (generic OS nodes) |
| `["slurm", "login"]` | All Slurm nodes **and** all login nodes |
| `["slurm_node", "login"]` | Slurm compute nodes **and** login nodes (excludes Slurm controller) |

!!! tip

    Use shorter prefixes to target broader groups. For example, `["slurm"]` targets all Slurm roles, while `["slurm_node"]` targets only compute nodes.

## Prerequisites

- Access to edit `storage_config.yml` on the OIM host.
- NFS server IP address or DNS-resolvable hostname and export path, for NFS mounts.
- VAST storage appliance configured separately with NFS exports and access
  policies, for VAST mounts. The Telemetry VAST guide configures metrics and
  log collection; it does not configure the storage appliance.
- For VAST mounts, select a with-VAST catalog that supplies the `vastnfs`
  package for every targeted architecture. The shipped default catalog is a
  no-VAST catalog and does not contain that client package.
- iSCSI initiator setup and network connectivity to the PowerVault controllers, for PowerVault volumes.
- Functional group names defined in the PXE mapping file, to target mounts, swap, and PowerVault entries to specific node groups. See [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md).

## Procedure

### Mounts

Each mount entry specifies a source, mount point, and optional filesystem parameters.

--8<-- "html/storage_config-mounts.html"

**Example**

```yaml title="File: storage_config.yml"
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

### OIM mount selection

Orchestrator distinguishes storage referenced by Slurm or service Kubernetes
from an independent OIM mount:

- When provisioning Slurm, the OIM mounts the NFS storage
  named by `slurm_cluster[].nfs_storage_name` and the optional VAST storage
  named by `slurm_cluster[].vast_storage_name`. Each referenced mount must set
  `mount_on_oim: true`.
- When provisioning service Kubernetes, the OIM mounts the NFS storage
  named by a `service_k8s_cluster` entry only when that entry has
  `deployment: true`. The referenced mount must set `mount_on_oim: true`.
- A storage name referenced by either workload is not selected through the
  generic `mount_on_oim` rule for a different or inactive workload. For
  example, a Slurm-only run does not contact an unused Kubernetes NFS endpoint,
  even if that storage entry has `mount_on_oim: true`.
- A storage entry that is not referenced by Slurm or service Kubernetes is an
  independent mount and is selected when `mount_on_oim: true`.

!!! important

    Storage referenced by a workload must set `mount_on_oim: true` to pass
    input validation. That flag alone does not select storage from another or
    inactive workload during the current provisioning phase. To disable
    optional Slurm VAST storage, omit `vast_storage_name` or set it to an empty
    string in the active `slurm_cluster` entry.

#### Slurm storage mounts

Slurm deployments require specific NFS and optional VAST mounts for configuration distribution, authentication, and HPC tools. The `slurm_cluster` section in `omnia_config.yml` references these mounts by name.

**Primary NFS mount (`nfs_storage_name`)**

This mount stores Slurm configuration files (`slurm.conf`, `slurmdbd.conf`, `cgroup.conf`, `gres.conf`), munge authentication keys, and shared state. The OIM writes these files during provisioning and all nodes read them at boot.

- Target all Slurm and login nodes using `functional_group_prefix: ["slurm", "login"]`.
- Set `mount_on_oim: true`. The `nfs_storage_name` reference and active Slurm
  target select this mount on the OIM so it can populate configuration and
  munge keys.
- The `name` field must match the `nfs_storage_name` value in `omnia_config.yml`.

```yaml title="Example: Slurm NFS mount"
mounts:
  - name: "nfs_slurm"
    source: "172.16.0.254:/mnt/share/omnia"
    mount_point: "/share_omnia"
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard,intr"
    mount_on_oim: true
    functional_group_prefix: ["slurm", "login"]
```

**VAST storage mount (`vast_storage_name`) — optional**

If a VAST storage appliance is available, configure a separate mount for HPC tools and benchmarks (`/hpc_tools`). This mount provides RDMA-optimized I/O for latency-sensitive workloads. If `vast_storage_name` is not specified in `omnia_config.yml`, Omnia uses the primary NFS mount for HPC tools.

- Target compute and login nodes using `functional_group_prefix: ["slurm_node", "login"]`.
- Set `mount_on_oim: true`. The nonempty `vast_storage_name` reference and
  active Slurm target select this mount on the OIM so it can populate HPC tools
  and benchmark artifacts.
- Use the `vast_rdma` mount_params profile for RDMA transport over InfiniBand.
- Use the standard `name: "vast_storage"`, and set
  `vast_storage_name: vast_storage` in `omnia_config.yml` to enable the mount.
- If `vast_storage_name` is empty or omitted, Orchestrator skips the standard
  `vast_storage` entry and reuses `nfs_storage_name` for Slurm shared-data and
  HPC-tools paths. An unused VAST endpoint is therefore not contacted.
- When `vast_storage_name` is set, it must match exactly one mount entry. The
  referenced storage is validated and must be reachable.

```yaml title="Example: VAST storage mount for HPC tools"
mounts:
  - name: "vast_storage"
    source: "172.16.107.77:/share/vast"
    mount_point: "/mnt/vast"
    mount_params: "vast_rdma"
    mount_on_oim: true
    functional_group_prefix: ["slurm_node", "login"]
```

For a complete explanation of what data lives on each mount, see [Slurm Storage Architecture](deploy_slurm.md#slurm-storage-architecture).

#### Configuring NFS shares

NFS is the most widely used storage mount type in Omnia clusters. NFS shares provide shared filesystems across compute, login, and controller nodes for home directories, application data, and Slurm spool directories.

When defining an NFS mount, the `source` field must use the format `server_ip:/export/path`. The NFS server IP or DNS-resolvable hostname must be reachable from all target nodes at boot time.

!!! tip

    - Use `hard,intr` mount options for production NFS shares. The `hard` option ensures the client retries indefinitely on server failure, while `intr` allows interrupted system calls.
    - Set `nconnect=16` for high-throughput workloads to open multiple TCP connections per mount.
    - Use `rsize=1048576,wsize=1048576` (1 MB) for large sequential I/O patterns common in HPC.
    - Set `mount_on_oim: true` if the OIM needs access to the same share (e.g., for Slurm accounting or shared configuration).

**NFS share for Slurm home directories with per-node isolation:**

```yaml title="File: storage_config.yml"
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

```yaml title="File: storage_config.yml"
mounts:
  - name: "nfs_app_data"
    source: "172.16.0.254:/mnt/share/appdata"
    mount_point: "/opt/appdata"
    mount_params: "nfs_default"
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

```yaml title="File: storage_config.yml"
mounts:
  - name: "vast_storage"
    source: "172.16.107.77:/share/vast"
    mount_point: "/mnt/vast"
    mount_params: "vast_rdma"
    mount_on_oim: true
    functional_group_prefix: ["slurm_node", "login"]
```

The source-provided `vast_rdma` mount profile uses `proto=rdma`, `nconnect=8`,
`timeo=600`, `retrans=2`, and 1 MB read/write buffers. You may define a
different named profile after validating its options with the VAST appliance
and client kernel.

**VAST mount with standard TCP transport (fallback):**

If the cluster network does not support RDMA (no InfiniBand or RoCE), use the
source-provided `vast_tcp` profile with standard TCP transport:

```yaml title="File: storage_config.yml"
mounts:
  - name: "vast_storage"
    source: "172.16.107.77:/share/vast"
    mount_point: "/mnt/vast"
    mount_params: "vast_tcp"
    mount_on_oim: true
    functional_group_prefix: ["slurm_node", "login"]
```

!!! note

    - RDMA transport requires InfiniBand or RoCE (RDMA over Converged Ethernet) connectivity between cluster nodes and the VAST appliance.
    - The VAST storage appliance must be configured with NFS exports and
      appropriate access policies before defining mounts.
    - The `slurm_cluster` section in `omnia_config.yml` should reference VAST storage via the `vast_storage_name` parameter.

#### K8s storage mounts

Service Kubernetes deployments require NFS mounts for persistent storage, Helm chart distribution, and shared application data. The `service_k8s_cluster` section in `omnia_config.yml` references these mounts by name.

**Primary NFS mount (`nfs_storage_name`)**

This mount stores Kubernetes persistent volumes, Helm charts, and shared application data. The NFS subdir provisioner creates persistent volumes backed by this share, allowing pods to store data that persists across pod restarts and node failures.

- Target all K8s control-plane and worker nodes using `functional_group_prefix: ["service_kube"]`.
- Set `mount_on_oim: true`. An enabled `service_k8s_cluster` entry and active
  Kubernetes target select this mount on the OIM so it can populate initial
  configuration and Helm charts.
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

For a complete explanation of what data lives on this mount, see [K8s Storage Architecture](deploy_kubernetes.md#k8s-storage-architecture).

### Mount params

Named profiles that provide default values for filesystem type and mount options. Referenced by mounts and PowerVault entries via the `mount_params` field.

--8<-- "html/storage_config-mount_params.html"

**Example custom profiles**

```yaml title="File: storage_config.yml"
mount_params:
  nfs_default:
    fs_type: "nfs"
    mnt_opts: "nfsvers=4.1,hard,intr,noatime,nconnect=16,rsize=1048576,wsize=1048576"
    dump_freq: "0"
    fsck_pass: "0"

  vast_rdma:
    fs_type: "nfs"
    mnt_opts: "proto=rdma,nconnect=8,timeo=600,retrans=2,rsize=1048576,wsize=1048576,hard"
    dump_freq: "0"
    fsck_pass: "0"

  vast_tcp:
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

```yaml title="File: storage_config.yml"
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

```yaml title="File: storage_config.yml"
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

## Next steps

- [Configure VAST Telemetry](../Telemetry/configure_vast.md) -- Collect VAST
  metrics and logs after the storage appliance is configured.
- [Provision Nodes](provision_nodes.md) -- Provision cluster nodes with the configured storage mounts.

## Troubleshooting

- **Mount does not appear on the target node**: Confirm the node's functional group name matches a `functional_group_prefix` value, and re-run the provisioning playbook. See [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md) to verify functional group names.
- **NFS mount fails or times out**: Verify the NFS server IP/hostname is reachable and resolvable from the target node at boot time, and that the export path exists on the server.
- **VAST RDMA mount fails to connect**: Confirm InfiniBand or RoCE connectivity between the node and the VAST appliance, and that the VAST appliance has NFS exports and access policies configured.
- **PowerVault volume does not mount**: Verify iSCSI initiator configuration and network connectivity to the PowerVault controllers.

!!! info

    - [Storage Config Reference](../../Reference/Configuration/storage_config.md) -- `storage_config.yml` parameter tables and usage example.
    - [Slurm Storage Architecture](deploy_slurm.md#slurm-storage-architecture) -- How Slurm uses NFS and VAST mounts.
    - [K8s Storage Architecture](deploy_kubernetes.md#k8s-storage-architecture) -- How service K8s uses NFS mounts.
    - [Storage Requirements](../../Reference/../Reference/../Reference/ClusterRequirements/storage_requirements.md) -- Storage sizing and prerequisites.
    - [Configure VAST Telemetry](../Telemetry/configure_vast.md) -- Metrics
      and log collection from a configured VAST appliance.
    - [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md) -- Functional groups and `GROUP_NAME` values.





