
# PXE Mapping File (CSV)


File path: Specified by `pxe_mapping_file_path` in `provision_config.yml`
(e.g., `/opt/omnia/input/project_default/pxe_mapping.csv`)

The PXE mapping file is a CSV that assigns each physical server to a
functional group, hostname, and admin network addresses via mac addresses. Omnia reads this file during `provision.yml` to determine which role eachserver plays and how it is addressed on the network.

## Column reference

| Column | Required | Description |
| --- | --- | --- |
| `FUNCTIONAL_GROUP_NAME` | Yes | The role and architecture this node plays in the cluster. Must match a group name in `software_config.json`. Values: `slurm_control_node_x86_64`, `slurm_node_x86_64`, `slurm_node_aarch64`, `login_node_x86_64`, `login_node_aarch64`, `login_compiler_node_aarch64`, `service_kube_control_plane_x86_64`, `service_kube_node_x86_64`, `os_x86_64`, `os_aarch64`. |
| `GROUP_NAME` | Yes | A logical sub-group for organizing nodes (e.g., `grp0`, `grp1`, `grp2`, `grp3`, `grp4`, `grp5`, `grp6`, `grp7`, `grp8`, `grp9`). Used for rack inventory grouping. |
| `SERVICE_TAG` | Yes | Dell service tag of the server (7-character alphanumeric string found on the server chassis or in iDRAC). Used for unique node identification. |
| `PARENT_SERVICE_TAG` | No | Service tag of the parent chassis for multi-node systems (e.g., C6620, C6625). Leave blank for standalone servers. |
| `HOSTNAME` | Yes | Hostname to assign to the node. Must comply with hostname rules (see [Hostname Requirements](../Appendices/hostname_requirements.md)). |
| `ADMIN_MAC` | Yes | MAC address of the admin network NIC (used for PXE boot). Format: `xx:yy:zz:aa:bb:cc`. |
| `ADMIN_IP` | Yes | Static IP address on the admin network. Must be within the admin subnet defined in `network_spec.yml` and outside the `dynamic_range`. |
| `BMC_MAC` | No | MAC address of the BMC/iDRAC interface. Used for BMC discovery and address assignment. |
| `BMC_IP` | No | Static IP address for the BMC/iDRAC interface. Must be within the BMC subnet. |
| `IB_NIC_NAME` | No | InfiniBand NIC identifier (e.g., `InfiniBand.Slot.7-1`, `NIC.InfiniBand.1-3`). Used for InfiniBand network configuration. Leave blank if node does not have InfiniBand. |
| `IB_IP` | No | Static IP address on the InfiniBand network (e.g., `192.168.0.100`). Must be within the InfiniBand subnet defined in `network_spec.yml`. Leave blank if node does not have InfiniBand. |

## Sample csv files
### pxe_mapping_file.csv
```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,xx:yy:zz:aa:bb:cc,172.16.107.52,xx:yy:zz:aa:bb:dd,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
slurm_node_aarch64,grp1,ABCD34,ABFL82,slurm-node1,aa:bb:cc:dd:ee:ff,172.16.107.43,aa:bb:cc:dd:ee:gg,172.17.107.43,InfiniBand.Slot.7-2,192.168.0.101
slurm_node_aarch64,grp2,ABFG34,ABKD88,slurm-node2,aa:bb:cc:dd:ee:ff,172.16.107.44,aa:bb:cc:dd:ff:gg,172.17.107.44,NIC.InfiniBand.1-3,192.168.0.102
login_compiler_node_aarch64,grp8,ABCD78,,login-compiler-node1,aa:bb:cc:dd:ee:gg,172.16.107.41,aa:bb:cc:dd:ee:bb,172.17.107.41,InfiniBand.PCIe.Slot.8-1,192.168.0.103
login_node_aarch64,grp9,ABFG78,,login-node1,aa:bb:cc:dd:ee:gg,172.16.107.42,aa:bb:cc:dd:ee:bb,172.17.107.42,NIC.InfiniBand.1-1,192.168.0.104
service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,aa:bb:cc:dd:ee:ff,172.16.107.53,xx:yy:zz:aa:bb:ff,172.17.107.53,,
service_kube_control_plane_x86_64,grp4,ABFH78,,service-kube-control-plane2,aa:bb:cc:dd:ee:hh,172.16.107.54,xx:yy:zz:aa:bb:hh,172.17.107.54,,
service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,aa:bb:cc:dd:ee:jj,172.16.107.56,xx:yy:zz:aa:bb:jj,172.17.107.56,,
os_x86_64,grp6,ABEF56,,os-node1,xx:yy:zz:aa:bb:ll,172.16.107.60,xx:yy:zz:aa:bb:ee,172.17.107.60,,
os_aarch64,grp7,ABEF78,,os-node2,xx:yy:zz:aa:bb:ab,172.16.107.61,xx:yy:zz:aa:bb:ac,172.17.107.61,,
```
### pxe_mapping_file.csv for single subnet DHCP
```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,xx:yy:zz:aa:bb:cc,172.16.107.52,xx:yy:zz:aa:bb:dd,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
slurm_node_x86_64,grp2,ABCD34,ABFL82,slurm-node1,aa:bb:cc:dd:ee:ff,172.16.107.43,aa:bb:cc:dd:ee:aa,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
slurm_node_x86_64,grp1,ABFG34,ABKD88,slurm-node2,aa:bb:cc:dd:ee:gg,172.16.107.44,aa:bb:cc:dd:ff:bb,172.17.107.44,InfiniBand.Slot.7-1,192.168.0.102
slurm_node_x86_64,grp1,BBFG35,ABKD88,slurm-node3,aa:bb:cc:dd:ee:hh,172.16.107.46,aa:bb:cc:dd:ff:cc,172.17.107.46,InfiniBand.Slot.7-1,192.168.0.103
login_node_x86_64,grp8,ABCD78,,login-compiler-node1,aa:bb:cc:dd:ee:gg,172.16.107.41,aa:bb:cc:dd:ee:bb,172.17.107.41,InfiniBand.Slot.7-1,192.168.0.104
login_compiler_node_x86_64,grp9,ABFG78,,login-compiler-node2,aa:bb:cc:dd:ee:gg,172.16.107.42,aa:bb:cc:dd:ee:bb,172.17.107.42,InfiniBand.Slot.7-1,192.168.0.105
service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,aa:bb:cc:dd:ee:ff,172.16.107.53,xx:yy:zz:aa:bb:ff,172.17.107.53,,InfiniBand.Slot.7-1,192.168.0.106
service_kube_control_plane_x86_64,grp4,ABFH78,,service-kube-control-plane2,aa:bb:cc:dd:ee:hh,172.16.107.54,xx:yy:zz:aa:bb:hh,172.17.107.54,,InfiniBand.Slot.7-1,192.168.0.107
service_kube_control_plane_x86_64,grp4,ABFH80,,service-kube-control-plane3,aa:bb:cc:dd:ee:ii,172.16.107.55,xx:yy:zz:aa:bb:ii,172.17.107.55,,InfiniBand.Slot.7-1,192.168.0.108
service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,aa:bb:cc:dd:ee:jj,172.16.107.56,xx:yy:zz:aa:bb:jj,172.17.107.56,InfiniBand.Slot.7-1,192.168.0.109
service_kube_node_x86_64,grp5,ABKD88,,service-kube-node2,aa:bb:cc:dd:ee:kk,172.16.107.57,xx:yy:zz:aa:bb:ff,172.17.107.57,InfiniBand.Slot.7-1,192.168.0.110
os_x86_64,grp7,EFG123,,os-node1,aa:bb:cc:dd:ee:21,10.41.0.12,aa:bb:cc:dd:ee:22,10.40.0.12,InfiniBand.Slot.7-11,10.42.0.12
os_aarch_64,grp8,EFG123,,os-node2,aa:bb:cc:dd:ee:21,10.41.0.12,aa:bb:cc:dd:ee:22,10.40.0.12,InfiniBand.Slot.7-11,10.42.0.12
```

### pxe_mapping_file.csv for multiple subnet DHCP

```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
service_kube_control_plane_x86_64,grp1,DEF456,,service-kube-control-plane1,aa:bb:cc:dd:ee:03,10.41.1.15,aa:bb:cc:dd:ee:04,10.40.1.15,InfiniBand.Slot.7-2,10.42.1.15
service_kube_control_plane_x86_64,grp1,GHI789,,service-kube-control-plane2,aa:bb:cc:dd:ee:05,10.41.1.16,aa:bb:cc:dd:ee:06,10.40.1.16,InfiniBand.Slot.7-3,10.42.1.16
service_kube_control_plane_x86_64,grp1,JKL012,,service-kube-control-plane3,aa:bb:cc:dd:ee:07,10.41.1.17,aa:bb:cc:dd:ee:08,10.40.1.17,InfiniBand.Slot.7-4,10.42.1.17
service_kube_node_x86_64,grp2,MNO345,,service-kube-node1,aa:bb:cc:dd:ee:09,10.41.1.18,aa:bb:cc:dd:ee:10,10.40.1.18,InfiniBand.Slot.7-5,10.42.1.18
service_kube_node_x86_64,grp2,PQR678,,service-kube-node2,aa:bb:cc:dd:ee:11,10.41.1.19,aa:bb:cc:dd:ee:12,10.40.1.19,InfiniBand.Slot.7-6,10.42.1.19
slurm_control_node_x86_64,grp3,ABC123,,slurm-control-node1,aa:bb:cc:dd:ee:01,10.41.0.10,aa:bb:cc:dd:ee:02,10.40.0.10,InfiniBand.Slot.7-1,10.42.0.10
slurm_node_x86_64,grp4,STU901,2LY0B33,slurm-node1,aa:bb:cc:dd:ee:13,10.41.2.22,aa:bb:cc:dd:ee:14,10.40.2.22,InfiniBand.Slot.7-7,10.42.2.22
slurm_node_x86_64,grp4,VWX234,2LY0B33,slurm-node2,aa:bb:cc:dd:ee:15,10.41.2.23,aa:bb:cc:dd:ee:16,10.40.2.23,InfiniBand.Slot.7-8,10.42.2.23
login_compiler_node_x86_64,grp5,YZA567,,login-compiler-node1,aa:bb:cc:dd:ee:17,10.41.2.24,aa:bb:cc:dd:ee:18,10.40.2.24,InfiniBand.Slot.7-9,10.42.2.24
login_node_x86_64,grp6,BCD890,,login-node1,aa:bb:cc:dd:ee:19,10.41.0.11,aa:bb:cc:dd:ee:20,10.40.0.11,InfiniBand.Slot.7-10,10.42.0.11
os_x86_64,grp7,EFG123,,os-node1,aa:bb:cc:dd:ee:21,10.41.0.12,aa:bb:cc:dd:ee:22,10.40.0.12,InfiniBand.Slot.7-11,10.42.0.12
os_aarch_64,grp8,EFG123,,os-node2,aa:bb:cc:dd:ee:21,10.41.0.12,aa:bb:cc:dd:ee:22,10.40.0.12,InfiniBand.Slot.7-11,10.42.0.12
```

## Node Role Examples

**Slurm control node (x86_64)**

```text title="Example: Slurm control node"
slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,xx:yy:zz:aa:bb:cc,172.16.107.52,xx:yy:zz:aa:bb:dd,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
```

- Runs `slurmctld` and `slurmdbd`.
- Exactly one node should have this functional group per Slurm cluster.
- `PARENT_SERVICE_TAG` is empty (standalone server).
- Includes InfiniBand NIC for high-speed cluster communication.

**Slurm compute nodes (AArch64)**

```text title="Example: Slurm compute nodes with parent chassis"
slurm_node_aarch64,grp1,ABCD34,ABFL82,slurm-node1,aa:bb:cc:dd:ee:ff,172.16.107.43,aa:bb:cc:dd:ee:gg,172.17.107.43,InfiniBand.Slot.7-2,192.168.0.101
slurm_node_aarch64,grp2,ABFG34,ABKD88,slurm-node2,aa:bb:cc:dd:ee:ff,172.16.107.44,aa:bb:cc:dd:ff:gg,172.17.107.44,NIC.InfiniBand.1-3,192.168.0.102
```

- Runs `slurmd`.
- `PARENT_SERVICE_TAG` identifies the shared chassis (multi-node systems like C6620).
- Each node has its own service tag, hostname, and network addresses.
- Includes InfiniBand NIC for high-speed cluster communication.

**Login node (AArch64)**

```text title="Example: Login node"
login_node_aarch64,grp9,ABFG78,,login-node1,aa:bb:cc:dd:ee:gg,172.16.107.42,aa:bb:cc:dd:ee:bb,172.17.107.42,NIC.InfiniBand.1-1,192.168.0.104
```

- Provides interactive SSH access for users to submit jobs.
- Does not run `slurmd`; configured as a Slurm client only.
- Includes InfiniBand for cluster communication.

**Kubernetes control plane (x86_64)**

```text title="Example: Kubernetes control plane"
service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,aa:bb:cc:dd:ee:ff,172.16.107.53,xx:yy:zz:aa:bb:ff,172.17.107.53,,
```

- Runs the Kubernetes API server, etcd, scheduler, and controller-manager.
- For HA, use 3 control plane nodes (see [HA Config](../Configuration/high_availability_config.md)).
- InfiniBand is optional for control plane nodes.

**Kubernetes worker nodes (x86_64)**

```text title="Example: Kubernetes worker nodes"
service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,aa:bb:cc:dd:ee:jj,172.16.107.56,xx:yy:zz:aa:bb:jj,172.17.107.56,,
```

- Runs `kubelet` and `kube-proxy`; hosts application pods.
- InfiniBand is optional for worker nodes.

**Generic OS nodes (x86_64 and AArch64)**

```text title="Example: Generic OS nodes"
os_x86_64,grp6,ABEF56,,os-node1,xx:yy:zz:aa:bb:ll,172.16.107.60,xx:yy:zz:aa:bb:ee,172.17.107.60,,
os_aarch64,grp7,ABEF78,,os-node2,xx:yy:zz:aa:bb:ab,172.16.107.61,xx:yy:zz:aa:bb:ac,172.17.107.61,,
```

- Generic nodes with no specific cluster role.
- Useful for standalone compute, storage, or utility nodes.
- InfiniBand is optional.

## Validation rules

| Rule | Description |
| --- | --- |
| Unique `SERVICE_TAG` | No two rows may share the same service tag. |
| Unique `HOSTNAME` | Each hostname must be unique across the entire file. |
| Unique `ADMIN_IP` | Admin IP addresses must not overlap with each other or with the OIM's admin IP. |
| Unique `ADMIN_MAC` | Each admin MAC address must be unique. |
| Valid `FUNCTIONAL_GROUP_NAME` | Must be one of the recognized group names listed above. |
| Hostname format | Lowercase, no domain suffix, RFC 952/1123 compliant. See [Hostname Requirements](../Appendices/hostname_requirements.md). |
| IP within subnet | `ADMIN_IP` must fall within the admin network subnet and outside the `dynamic_range`. `BMC_IP` must fall within the BMC subnet. |

!!! info

    - [Provision Config](../Configuration/provision_config.md) -- Where the mapping
      file path is specified.
    - [Software Config](../Configuration/software_config.md) -- Software packages
      per functional group.
    - [Hostname Requirements](../Appendices/hostname_requirements.md) -- Hostname rules.
