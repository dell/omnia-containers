# Create a Mapping File

## Overview

Nodes in Omnia are discovered and provisioned based on the **groups** and **functional groups** defined in a PXE mapping file. By combining both, Omnia provides a flexible approach to managing large-scale node infrastructures, ensuring both logical organization and physical optimization of resources.

- A **group** is based on the physical characteristics of nodes. Nodes in the same rack or Scalable Unit (SU) are grouped together with a shared `GROUP_NAME`. Groups help with physical organization and management.

- A **functional group** defines what a node does in the cluster. It categorizes nodes by their role, such as:
    - `service_kube_control_plane`
    - `service_kube_node`
    - `slurm_control_node`
    - `slurm_node`
    - `login_node`
    - `login_compiler_node`
    - `os` (Minimal OS)

## Prerequisites

- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete.
- PXE NIC MAC addresses and BMC IP addresses are available for each target node.
- You have planned the functional group assignments for each node.

## Procedure

Omnia supports two methods for discovering target nodes and creating PXE mapping files:

- **Manual PXE mapping** -- Manually collect PXE NIC information and define entries in `pxe_mapping_file.csv`. See [Create PXE file manually](#create-pxe-file-manually).
- **OME-based PXE file generation** (Recommended) -- Use OpenManage Enterprise (OME) to discover cluster nodes and auto-generate the mapping file via the `discovery.yml` playbook. See [Create PXE file using OME](#create-pxe-file-using-ome).

### Create PXE file manually

Manually collect PXE NIC information for each node and define it in `pxe_mapping_file.csv`. Provide the file path to the `pxe_mapping_file_path` variable in `/opt/omnia/input/project_default/provision_config.yml`.

Each node entry requires the following fields: `FUNCTIONAL_GROUP_NAME`, `GROUP_NAME`, `SERVICE_TAG`, `PARENT_SERVICE_TAG`, `HOSTNAME`, `ADMIN_MAC`, `ADMIN_IP`, `BMC_MAC`, `BMC_IP`, `IB_NIC_NAME`, and `IB_IP`.

### Column reference

| Column | Required | Description |
| --- | --- | --- |
| `FUNCTIONAL_GROUP_NAME` | Yes | Node role with architecture suffix (e.g., `slurm_node_x86_64`, `login_node_aarch64`). |
| `GROUP_NAME` | Yes | Physical grouping identifier (e.g., `grp0`, `grp1`). Nodes in the same group must share the same parent. |
| `SERVICE_TAG` | Yes | Dell service tag of the server. |
| `PARENT_SERVICE_TAG` | No | Service tag of the parent chassis for blade servers. Leave empty for rack servers. |
| `HOSTNAME` | Yes | Custom hostname for the node. Do not include the domain name. |
| `ADMIN_MAC` | Yes | MAC address of the PXE NIC on the admin network. |
| `ADMIN_IP` | Yes | Static IP address on the admin network. |
| `BMC_MAC` | Yes | MAC address of the BMC/iDRAC interface. |
| `BMC_IP` | Yes | Static IP address on the BMC network. |
| `IB_NIC_NAME` | No | FQDD of the InfiniBand NIC port (e.g., `InfiniBand.Slot.7-1`). Leave empty if no IB NIC is present. |
| `IB_IP` | No | Static IP address on the InfiniBand network. Leave empty if no IB NIC is present. |

### Sample mapping file (x86_64 cluster)

```text title="File: /opt/omnia/input/project_default/pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,ABCD12,,nid001,a1:b2:c3:d4:e5:f6,172.16.107.52,a2:b3:c4:d5:e6:f7,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
slurm_node_x86_64,grp1,ABCD34,ABFL82,nid002,b1:c2:d3:e4:f5:a6,172.16.107.43,b2:c3:d4:e5:f6:a7,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
slurm_node_x86_64,grp1,ABFG34,ABKD88,nid003,c1:d2:e3:f4:a5:b6,172.16.107.44,c2:d3:e4:f5:a6:b7,172.17.107.44,InfiniBand.Slot.7-1,192.168.0.102
login_compiler_node_x86_64,grp8,ABCD78,,nid004,d1:e2:f3:a4:b5:c6,172.16.107.41,d2:e3:f4:a5:b6:c7,172.17.107.41,InfiniBand.Slot.7-1,192.168.0.103
service_kube_control_plane_x86_64,grp3,ABFG79,,nid005,f1:a2:b3:c4:d5:e6,172.16.107.53,f2:a3:b4:c5:d6:e7,172.17.107.53,,
service_kube_node_x86_64,grp5,ABFL82,,nid006,33:44:55:66:77:88,172.16.107.56,34:45:56:67:78:89,172.17.107.56,InfiniBand.Slot.7-1,192.168.0.108
os_x86_64,grp6,ABEF56,,nid007,77:88:99:aa:bb:cc,172.16.107.60,78:89:aa:bb:cc:dd,172.17.107.60,,
```

### Sample mapping file (mixed x86_64 and aarch64 cluster)

```text title="File: /opt/omnia/input/project_default/pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,ABCD12,,nid001,a1:b2:c3:d4:e5:f6,172.16.107.52,a2:b3:c4:d5:e6:f7,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
slurm_node_aarch64,grp1,ABCD34,ABFL82,nid002,b1:c2:d3:e4:f5:a6,172.16.107.43,b2:c3:d4:e5:f6:a7,172.17.107.43,InfiniBand.Slot.7-2,192.168.0.101
login_compiler_node_aarch64,grp8,ABCD78,,nid003,d1:e2:f3:a4:b5:c6,172.16.107.41,d2:e3:f4:a5:b6:c7,172.17.107.41,InfiniBand.PCIe.Slot.8-1,192.168.0.103
login_node_aarch64,grp9,ABFG78,,nid004,e1:f2:a3:b4:c5:d6,172.16.107.42,e2:f3:a4:b5:c6:d7,172.17.107.42,NIC.InfiniBand.1-1,192.168.0.104
service_kube_control_plane_x86_64,grp3,ABFG79,,nid005,f1:a2:b3:c4:d5:e6,172.16.107.53,f2:a3:b4:c5:d6:e7,172.17.107.53,,
os_aarch64,grp7,ABEF78,,nid006,99:aa:bb:cc:dd:ee,172.16.107.61,9a:ab:bc:cd:de:ef,172.17.107.61,,
```

!!! note "Hostname format"

    - When `dns_enabled` is `false` in `provision_config.yml`, `HOSTNAME` values can be customized (e.g., `slurm-control-node1`).
    - When `dns_enabled` is `true` (the default for fresh installations), `HOSTNAME` values must follow the `nid00x` format (e.g., `nid001`, `nid002`).

!!! warning

    - Header fields are **case-sensitive**. Use uppercase exactly as shown.
    - IP addresses in the mapping file are **not validated** by Omnia. Incorrect IPs cause unexpected failures.
    - Service tags are **not validated** by Omnia. Verify correctness before discovery.
    - Hostnames must **not** include the domain name.
    - All fields are mandatory. Use an empty value (two consecutive commas) where a value is not applicable.
    - `ADMIN_MAC` and `BMC_MAC` must refer to the PXE NIC and BMC NIC on the target nodes respectively.
    - Target servers must be configured to boot in PXE mode with the appropriate NIC as the first boot device.
    - Nodes in the same group must have the same parent (`PARENT_SERVICE_TAG`).

!!! note "Minimal OS functional groups"

    The `os_x86_64` and `os_aarch64` functional groups provide a clean operating system baseline with only essential OS packages and LDMS telemetry packages -- no schedulers, container runtimes, or orchestration software. Administrators can optionally include additional packages by creating `additional_packages.json` files in `input/config/{arch}/rhel/10.0/`.

### Create PXE file using OME

OME-based BMC discovery is the recommended method for discovering target nodes. This method leverages OpenManage Enterprise to automatically discover servers through their BMC/iDRAC interfaces, reducing manual configuration effort.

!!! note

    In Dell Omnia deployments integrated with OME, server identification during PXE boot relies on information retrieved from OME and iDRAC inventory. Depending on the DNS environment, the `DnsName` value may not align with naming conventions required for cluster configuration. Users must explicitly define `GROUP_NAME` and `PARENT_SERVICE_TAG` in the `pxe_mapping_file` to ensure accurate PXE provisioning.

### Prerequisites

- OpenManage Enterprise is installed and accessible.
- All target servers have iDRAC configured with network connectivity.
- OME has discovered the devices (servers are visible in OME inventory).
- You have administrative access to OME.
- Servers have the correct NIC order and configuration. Verify NIC ordering in the server BIOS or iDRAC settings before discovery. Omnia uses the following NIC selection logic:
    - **Admin NIC**: Priority 1: First NIC that is active/UP. Priority 2: Second NIC if UP. Priority 3: First NIC regardless of link state (fallback).
    - **InfiniBand NIC**: If detected, IB NIC Name is captured and `IB_IP` is assigned. If absent, IB fields are left empty.
- For a deployment with N Scalable Units, ensure one dedicated `service_kube_node` per Scalable Unit.
- iDRAC hostnames must follow the Omnia naming convention:

    ```text title="Example"
    idrac-<SU><1-100>R<000-999>OU<1-54><Type><Instance>
    ```

    - **SU** -- Scalable Unit number (`SU1` through `SU100`, case-insensitive)
    - **R** -- Rack number within the SU (`R1` through `R999`)
    - **OU** -- ORv3 (Open Rack v3) Unit position (`OU1` through `OU54`)
    - **C** -- Compute Node number (`C1` through `C99`)

    ```text title="Example breakdown"
    SU02   R1   OU05   C7
    │      │     │      │
    │      │     │      └──  Compute Node number
    │      │     └─────────  ORv3 Unit position in the rack
    │      └───────────────  Rack number within the Scalable Unit
    └──────────────────────  Scalable Unit number
    ```

!!! warning

    If the iDRAC hostname is not set correctly using this convention before discovery, Omnia generates incorrect PXE mapping information. Accurate, consistent naming is mandatory.

## Verification

Verify the mapping file is correctly formatted and contains all required entries:

```bash title="Run on: omnia_core container"
cat /opt/omnia/input/project_default/<pxe_mapping_file>.csv
```

Confirm that each node entry has a valid `FUNCTIONAL_GROUP_NAME`, `GROUP_NAME`, `SERVICE_TAG`, `HOSTNAME`, `ADMIN_MAC`, `ADMIN_IP`, `BMC_MAC`, and `BMC_IP`.

## Next Steps

- [Configure Inputs](configure_inputs.md) -- Configure software and cluster input files.
- [Configure Credentials](configure_credentials.md) -- Set up encrypted provisioning credentials.
- [Discover Nodes](discover_nodes.md) -- Run the discovery playbook using this mapping file.

## Troubleshooting

- **Provisioning fails with "invalid mapping file"**: Verify that the CSV header fields are uppercase and match the expected column names exactly.
- **Nodes assigned to wrong functional group**: Review the `FUNCTIONAL_GROUP_NAME` column and correct the entries. Re-run the provisioning playbook after updating the file.

!!! info "Related References"

    - [Discover Nodes](discover_nodes.md) -- Run the discovery playbook.
    - [Provision Config](../../Reference/Configuration/provision_config.md) -- Configure `pxe_mapping_file_path` and other provisioning parameters.
