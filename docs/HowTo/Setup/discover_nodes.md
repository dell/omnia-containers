# Discover Nodes Using OME

Use OpenManage Enterprise (OME) to discover cluster nodes and auto-generate
the PXE mapping file using the `discovery.yml` playbook. This is the
recommended method for creating the mapping file, as it reduces manual
configuration effort by querying OME for server inventory and NIC details.

## Overview

The `discovery.yml` playbook performs the following steps:

1. Authenticates with OpenManage Enterprise using OME credentials.
2. Collects server inventory from OME (service tags, MAC addresses, NIC
   details).
3. Generates a `bmc_pxe_mapping_file_<timestamp>.csv` in
   `/opt/omnia/input/project_default/`.
4. Generates a `bmc_discovery_report_<timestamp>.csv` in
   `/opt/omnia/discovery/` with NIC link statuses for pre-provisioning
   health checks.

!!! note

    In Dell Omnia deployments integrated with OME, server identification
    and mapping during PXE boot rely on information retrieved from OME and
    iDRAC inventory. Depending on the DNS environment, the `DnsName` value
    may match the intended iDRAC hostname, or may return a reverse DNS name
    (for example, `pool-<IP-based>`), which may not align with naming
    conventions required for cluster configuration. Due to differences
    between iDRAC configuration and OME-reported hostnames, you must
    explicitly define `GROUP_NAME` and `PARENT_SERVICE_TAG` in the
    `pxe_mapping_file` to ensure accurate PXE provisioning and cluster
    setup.

## Prerequisites

- OpenManage Enterprise (OME) is installed and accessible from the OIM.
- All target servers have iDRAC configured with network connectivity.
- OME has discovered the devices (servers are visible in OME inventory).
  For more information on discovering devices in OME, see the
  [OpenManage Enterprise User Guide](https://dl.dell.com/content/manual4/en/openmanage-enterprise-user-guide-en){target="_blank"}.
- You have administrative access to OME.
- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete.
- For a deployment with N Scalable Units, ensure one dedicated
  `service_kube_node` (Kubernetes worker node) for each Scalable Unit.

### NIC MAC address selection

Servers must have the correct NIC order and configuration in BIOS or
iDRAC settings to match your intended IP assignment scheme. During
OME-based discovery, Omnia collects MAC addresses using priority-based
selection:

**Admin (non-iDRAC) NIC selection:**

| Priority | Condition | Action |
| --- | --- | --- |
| 1 | First Ethernet NIC is active (UP) | Use first NIC |
| 2 | First NIC is down, second NIC is UP | Use second NIC |
| 3 | All Ethernet NICs are down | Default to first NIC regardless of link state |

Omnia scans server NICs excluding the iDRAC/BMC NIC. NIC order is
determined by BIOS/iDRAC settings.

**InfiniBand (IB) NIC selection:**

| Priority | Condition | Action |
| --- | --- | --- |
| 1 | IB NIC link status is UP | Use this IB NIC |
| 2 | IB NIC link status is Unknown | Use as fallback |
| 3 | IB NIC link status is Down | Use as last resort |

If no InfiniBand NIC is detected, the IB fields are left empty in the
generated CSV. This is expected behavior and does not affect provisioning
for clusters without InfiniBand.

### iDRAC hostname naming convention

Omnia uses the iDRAC hostname as the anchor identity for every compute
node. The hostname encodes the physical and logical location of the
server, read left to right from the largest grouping down to the
individual node. The iDRAC hostname must follow this pattern:

```text
idrac-<SU><1-100>R<000-999>OU<1-54><Type><Instance>
```

| Component | Description | Format |
| --- | --- | --- |
| **SU** (Scalable Unit) | A logical block of infrastructure -- a group of racks deployed and managed together as a single unit. | `SU1` through `SU100` (case-insensitive) |
| **R** (Rack) | The physical rack cabinet housing servers and networking equipment within the Scalable Unit. | `R1` through `R999` |
| **OU** (ORv3 Unit Position) | The vertical slot position in an ORv3-compliant rack. | `OU1` through `OU54` |
| **C** (Compute Node) | Distinguishes individual compute servers at a rack position. A dense chassis can hold multiple nodes. | `C1` through `C99` |

**Example breakdown:**

```text
SU02   R1   OU05   C7
│      │     │      │
│      │     │      └──  Compute Node number
│      │     └─────────  ORv3 Unit position in the rack
│      └───────────────  Rack number within the Scalable Unit
└──────────────────────  Scalable Unit number
```

`SU02R1OU05C7` = Scalable Unit 02, Rack 1, ORv3 Unit position 5,
Compute Node 7.

!!! warning

    If the iDRAC hostname is not set correctly using this convention
    before discovery, Omnia will generate incorrect PXE mapping
    information. Accurate, consistent naming is mandatory.

## Procedure

1. **Discover servers in OME.** In OpenManage Enterprise, discover the
   cluster nodes you want to provision with Omnia. For more information,
   see the
   [OpenManage Enterprise User Guide](https://dl.dell.com/content/manual4/en/openmanage-enterprise-user-guide-en){target="_blank"}.

2. **Create static groups in OME** for each Omnia functional group you
   plan to use. The group names must exactly match the functional group
   names listed in
   [Functional groups](#functional-groups).

    To create static groups in OME:

    1. In the left navigation menu, navigate to **CUSTOM GROUPS > Static Groups**.
    2. Click the ellipsis (**…**) next to Static Groups and select
       **Create Group**.
    3. Provide the group name exactly matching the functional group name.
    4. Add a description for the group.
    5. Click **Finish**.

    Repeat for each functional group type you plan to use.

3. **Add discovered servers to the static groups** in OME:

    1. Select the static functional group from the list.
    2. Click **Add Devices**.
    3. In the **Add Devices to Group** dialog box, select the servers
       that belong to that functional group.
    4. Click **Finish**.

    Repeat for all functional groups, ensuring each server is assigned to
    the correct static group based on its intended role in the cluster.

    !!! note

        Devices not assigned to any Omnia-supported static group will
        default to `slurm_node_aarch64` in the auto-generated mapping
        file.

4. **Configure the discovery input file:**

    ```bash title="Run on: omnia_core container"
    vi /opt/omnia/input/project_default/discovery_config.yml
    ```

    | Parameter | Mandatory / Optional | Details |
    | --- | --- | --- |
    | `enable_bmc_discovery` | Optional | **Type:** Boolean. Set to `true` to enable BMC discovery via OME. When `false`, OME credentials will not be prompted during `prepare_oim`. **Default:** `false` |
    | `ome_ip` | Conditional Mandatory | **Type:** String. IP address of the Dell OME instance. **Required when** `enable_bmc_discovery` is `true`. **Example:** `"192.168.1.100"` **Default:** `""` |

    ```yaml title="Example: discovery_config.yml"
    enable_bmc_discovery: true
    ome_ip: "192.168.1.100"
    ```

5. **Run the discovery playbook:**

    ```bash title="Run on: omnia_core container"
    cd /omnia/discovery
    ansible-playbook discovery.yml -e "discovery_mechanism=ome"
    ```

    The playbook will prompt for OME credentials if not already
    configured. After completion, a summary message is displayed:

    ```text title="Expected output"
    ============================================================
    OME Discovery Complete
    ============================================================
    BMC PXE mapping file generated: /opt/omnia/input/project_default/bmc_pxe_mapping_file_<timestamp>.csv
    BMC discovery report generated: /opt/omnia/discovery/bmc_discovery_report_<timestamp>.csv
      (Lists link status of BMC, Ethernet, and InfiniBand NICs for each server)
    Total servers discovered: <N>

    Next Steps:
    1. Review and edit the generated PXE mapping file.
    2. Review the discovery report for NIC link statuses.
    3. Update HOSTNAME, FUNCTIONAL_GROUP_NAME, GROUP_NAME as needed.
    4. If fresh installation of Omnia, Run:
         ansible-playbook prepare_oim/prepare_oim.yml
       If Slurm add node scenario, Run:
         ansible-playbook provision/provision.yml
    ============================================================
    ```

6. **Verify and edit the generated mapping file:**

    ```bash title="Run on: omnia_core container"
    cat /opt/omnia/input/project_default/bmc_pxe_mapping_file_*.csv
    ```

    Review the file and update `HOSTNAME`, `FUNCTIONAL_GROUP_NAME`,
    `GROUP_NAME`, and `PARENT_SERVICE_TAG` columns as needed for your
    deployment.

## Groups

Nodes located in the same physical location or with similar hardware can
be grouped together. Each group in the PXE mapping file has the following
attributes:

| Attribute | Mandatory / Optional | Description |
| --- | --- | --- |
| `GROUP_NAME` (`grpN`) | Mandatory | User-defined group name. Range for `N` is `0`--`99`. Example: `grp0`, `grp1`, `grp2`. |
| `PARENT_SERVICE_TAG` | Conditional Mandatory | Service tag of the parent (active service) node. **Required** for nodes in the `slurm_node_x86_64` and `slurm_node_aarch64` functional groups. Must be the service tag of the `service_kube_node` associated with that group. |

## Functional groups

Nodes with similar functional roles are grouped into functional groups.
The following table lists all functional groups supported in Omnia.

!!! note

    - At least one functional group is mandatory. You must not change the
      name of functional groups.
    - Each node must be associated with exactly one functional group. Do
      not assign a node to multiple functional groups.
    - Functional group names are **case-sensitive**.
    - To set up a service cluster, the `service_kube_node` must be present
      in the mapping file.

| Functional Group Name | Layer | Description |
| --- | --- | --- |
| `slurm_control_node_x86_64` | Management | Slurm head node. Nodes in this group are configured to run the Slurm controller. |
| `slurm_node_x86_64` | Compute | Slurm compute nodes on x86_64 architecture. |
| `slurm_node_aarch64` | Compute | Slurm compute nodes on aarch64 architecture. |
| `service_kube_control_plane_x86_64` | Management | Kubernetes control plane nodes on the service cluster. HA requires a minimum of 3 nodes. |
| `service_kube_node_x86_64` | Management | Kubernetes worker nodes on the service cluster. |
| `login_node_x86_64` | Management | User login nodes on x86_64. Handles user login sessions. |
| `login_node_aarch64` | Management | User login nodes on aarch64. Handles user login sessions. |
| `login_compiler_node_x86_64` | Management | Login and compiler nodes on x86_64. Includes compilation tools. |
| `login_compiler_node_aarch64` | Management | Login and compiler nodes on aarch64. Includes compilation tools. |
| `os_x86_64` | Compute | Minimal OS baseline for x86_64. Clean environment for downstream platform software. |
| `os_aarch64` | Compute | Minimal OS baseline for aarch64. Clean environment for downstream platform software. |

### Recommended software by functional groups

!!! caution

    Ensure that the `software_config.json` file contains all required
    inputs for the software to be deployed on each functional group. For
    more information, see
    [software_config.json](../../Reference/Configuration/software_config.md){target="_blank"}.

| Functional Group Name | Recommended Software |
| --- | --- |
| `service_kube_control_plane_x86_64` | `service_k8s` |
| `service_kube_node_x86_64` | `service_k8s` |
| `slurm_control_node_x86_64` | `slurm_custom`, `openldap`, `ldms` |
| `slurm_node_x86_64` | `slurm_custom`, `openldap`, `ldms` |
| `slurm_node_aarch64` | `slurm_custom`, `openldap`, `ldms` |
| `login_node_x86_64` | `slurm_custom`, `openldap`, `ldms` |
| `login_node_aarch64` | `slurm_custom`, `openldap`, `ldms` |
| `login_compiler_node_x86_64` | `slurm_custom`, `openldap`, `ucx`, `openmpi`, `ldms` |
| `login_compiler_node_aarch64` | `slurm_custom`, `openldap`, `ucx`, `openmpi`, `ldms` |
| `os_x86_64` | `default_packages`, `ldms` |
| `os_aarch64` | `default_packages`, `ldms` |

!!! note

    The `os_x86_64` and `os_aarch64` functional groups support optional
    additional packages via `additional_packages.json` files. Create these
    files in `input/config/<arch>/rhel/10.0/` to include custom packages.
    If no additional packages are needed, the images build successfully
    with the standard packages.

## BMC discovery report

The BMC discovery report is a CSV file generated automatically at the end
of the OME discovery process. It provides a consolidated view of all
discovered servers along with the link status of each NIC type (BMC,
Ethernet, and InfiniBand), enabling administrators to quickly identify
connectivity issues before provisioning.

### Output file location

```text
/opt/omnia/discovery/bmc_discovery_report_<timestamp>.csv
```

Where `<timestamp>` is in `YYYYMMDDTHHMMSS` format (for example,
`20260601T120000`), matching the PXE mapping file timestamp.

### Report columns

| Column | Description |
| --- | --- |
| `SERVICE_TAG` | Dell service tag uniquely identifying the server. |
| `BMC_MAC` | MAC address of the BMC (iDRAC) network interface. |
| `BMC_IP` | IP address assigned to the BMC (iDRAC). |
| `BMC_NIC_STATUS` | Link status of the BMC NIC. Typically `Up` if the server is managed by OME. |
| `ETHERNET_NIC_MAC` | MAC address of the first Ethernet NIC (excluding iDRAC and InfiniBand NICs). |
| `ETHERNET_NIC_LINK_STATUS` | Link status of the Ethernet NIC (`Up`, `Down`, `Unknown`). |
| `IB_NIC_NAME` | FQDD of the InfiniBand NIC port (for example, `InfiniBand.Slot.3-1`). Empty if no InfiniBand NIC is present. |
| `IB_NIC_LINK_STATUS` | Link status of the InfiniBand NIC (`Up`, `Down`, `Unknown`). Empty if no InfiniBand NIC is present. |

### Sample output

```csv title="bmc_discovery_report_20260601T120000.csv"
SERVICE_TAG,BMC_MAC,BMC_IP,BMC_NIC_STATUS,ETHERNET_NIC_MAC,ETHERNET_NIC_LINK_STATUS,IB_NIC_NAME,IB_NIC_LINK_STATUS
H94M8F3,B8:CE:F6:57:89:D0,172.16.0.101,UP,b0:7b:25:d8:4a:f4,Up,InfiniBand.Slot.3-1,Unknown
J7KN2G4,A4:BF:01:12:34:56,172.16.0.102,UP,e4:43:4b:01:23:45,Up,,
K5LP9H2,D0:94:66:AB:CD:EF,172.16.0.103,UP,24:6e:96:78:90:12,Unknown,InfiniBand.Slot.3-1,Up
```

### NIC link statuses

**BMC NIC status:** Indicates whether the iDRAC is reachable from OME.
Typically `Up` since OME manages the server.

**Ethernet NIC link status:** Reflects the physical link state of the
first non-iDRAC, non-InfiniBand network port:

- **Up** -- Cable connected and link established.
- **Down** -- No link detected (cable disconnected or switch port down).
- **Unknown** -- iDRAC cannot determine the link state. This can occur
  when the NIC firmware has not been initialized or the server is powered
  off.

!!! note

    When all Ethernet NICs report `Unknown` status, Omnia selects the
    first available Ethernet NIC as a fallback. InfiniBand NICs are never
    selected as the Ethernet/admin NIC.

**InfiniBand NIC link status:** Reflects the state of the IB port:

- **Up** -- InfiniBand link is active.
- **Down** -- No InfiniBand link detected.
- **Unknown** -- iDRAC reports the link state as unknown. This is common
  for InfiniBand NICs even when they are active at the OS level, as
  iDRAC may not have full visibility into InfiniBand link state.

!!! note

    InfiniBand NIC selection uses a priority-based fallback: `Up` is
    preferred, followed by `Unknown`, then `Down`. This ensures an IB NIC
    is reported even when iDRAC cannot determine its link state.

### Use cases

**Pre-provisioning health check:** Before running `provision.yml`, review
the discovery report to verify:

- All servers have valid BMC IPs and MAC addresses.
- Ethernet NICs are in `Up` state (required for PXE boot).
- InfiniBand NICs are detected on servers that require IB connectivity.

**Troubleshooting NIC connectivity:** If a server fails to PXE boot
during provisioning:

1. Check the `ETHERNET_NIC_LINK_STATUS` in the discovery report.
2. If the status is `Down` or `Unknown`, verify the physical cable
   connection and switch port configuration.
3. If the `ETHERNET_NIC_MAC` appears incorrect, check NIC ordering in
   BIOS/iDRAC settings.

**Inventory auditing:** The report serves as a point-in-time snapshot of
the cluster NIC inventory, useful for verifying InfiniBand fabric
connectivity, tracking which servers have IB NICs installed, and auditing
MAC addresses.

### Relationship to PXE mapping file

| Attribute | PXE Mapping File | Discovery Report |
| --- | --- | --- |
| **Purpose** | Input for provisioning | Diagnostic and auditing |
| **Editable** | Yes (user edits hostnames, groups) | No (read-only reference) |
| **Contains NIC link status** | No | Yes |
| **Contains IP assignments** | Yes (`ADMIN_IP`, `BMC_IP`, `IB_IP`) | Yes (`BMC_IP` only) |
| **Contains hostnames** | Yes | No |
| **Used by provision.yml** | Yes | No |

## Next Steps

- [Configure Inputs](configure_inputs.md) -- Configure Omnia input files.
- [Configure Credentials](configure_credentials.md) -- Set up encrypted
  credentials.

## Troubleshooting

**`ome_ip must be provided in discovery_config.yml`**

Set `enable_bmc_discovery: true` and provide a valid `ome_ip` in
`discovery_config.yml`.

**Devices appear as `slurm_node_aarch64` in the mapping file**

Ensure the devices are assigned to the correct static group in OME.
Devices not in any Omnia-supported static group default to
`slurm_node_aarch64`.

**Missing Ethernet NIC MAC in the mapping file**

Verify NIC ordering in the server BIOS/iDRAC settings. Omnia selects the
first active Ethernet NIC (excluding iDRAC and InfiniBand NICs). If all
NICs are down, it falls back to the first NIC regardless of link state.

**Incorrect hostnames in the generated file**

Ensure iDRAC hostnames follow the Omnia naming convention
(`idrac-<SU>R<Rack>OU<Position><Type><Instance>`) before running
discovery. See [iDRAC hostname naming convention](#idrac-hostname-naming-convention).

**OME connection failure**

Verify OME is accessible from the OIM:

```bash title="Run on: OIM host"
curl -sk https://<ome-ip>/api/SessionService/Sessions -X POST \
  -H "Content-Type: application/json" \
  -d '{"UserName":"<user>","Password":"<pass>"}'
```
