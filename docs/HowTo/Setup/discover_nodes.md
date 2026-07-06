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

## Prerequisites

- OpenManage Enterprise (OME) is installed and accessible from the OIM.
- All target servers have iDRAC configured with network connectivity.
- OME has discovered the devices (servers are visible in OME inventory).
- You have administrative access to OME.
- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete.
- OME credentials (username/password) are available. The `discovery.yml`
  playbook will prompt for them automatically via the credential utility.
- For a deployment with N Scalable Units, ensure one dedicated
  `service_kube_node` (Kubernetes worker node) for each Scalable Unit.
- Servers have the correct NIC order and configuration in BIOS/iDRAC
  settings to match your intended IP assignment scheme. Verify NIC
  ordering in the server BIOS or iDRAC settings before running discovery.

### NIC MAC address selection

When Omnia performs OME-based discovery, it uses the following logic:

- **Admin IP**: The first discoverable NIC (typically the first Ethernet
  interface) is used to generate the admin IP address in the PXE mapping
  file.
- **InfiniBand IP**: The first discoverable InfiniBand NIC is used to
  generate the InfiniBand IP address in the PXE mapping file.

**Admin (non-iDRAC) NIC selection:**

- Priority 1: First NIC that is active/UP
- Priority 2: If first NIC is down, use second NIC if UP
- Priority 3: If all NICs are down, default to first NIC regardless of
  link state
- Scans server NICs excluding the iDRAC/BMC NIC
- NIC order determined by BIOS/iDRAC settings

**InfiniBand (IB) NIC selection:**

- If IB NIC detected: IB NIC Name captured and IB_IP assigned
- If no IB NIC: IB fields left empty in CSV (expected behavior, does not
  affect provisioning)

### iDRAC hostname convention

Ensure iDRAC hostnames follow the Omnia naming convention. In Omnia, the
node name is the anchor identity for every compute node. It encodes the
physical and logical location of the server, read left to right from the
largest grouping down to the individual node. The iDRAC hostname should
follow this pattern:

```text
idrac-<SU><1-100>R<000-999>OU<1-54><Type><Instance>
```

| Component | Description | Format |
| --- | --- | --- |
| **Scalable Unit (SU)** | Logical block of infrastructure -- a group of racks deployed and managed together as a single unit | `SU1` through `SU100` |
| **R -- Rack** | Physical rack cabinet housing servers and networking equipment within the Scalable Unit | `R1` through `R999` |
| **OU -- ORv3 Unit Position** | Vertical slot position in an ORv3-compliant rack | `OU1` through `OU54` |
| **C -- Compute Node** | Individual compute server at a rack position; a dense chassis can hold multiple nodes | `C1` through `C99` |

**Example breakdown:**

```text
SU02   R1   OU05   C7
│      │     │      │
│      │     │      └──  Compute Node number
│      │     └─────────  ORv3 (Open Rack v3) Unit position in the rack
│      └───────────────  Rack number within the Scalable Unit
└──────────────────────  Scalable Unit number
```

`SU02R1OU05C7` = Scalable Unit 02 → Rack 1 → ORv3 Unit position 5 →
Compute Node 7.

!!! warning

    If the iDRAC hostname is not set correctly using this convention
    before discovery, Omnia will generate incorrect PXE mapping
    information. Accurate, consistent naming is mandatory.

## Procedure

1. **Discover devices in OME**: In OpenManage Enterprise, discover the
   cluster nodes that you want to provision with Omnia. For more
   information on discovering devices in OME, see the
   [OpenManage Enterprise User Guide](https://www.dell.com/support/manuals/en-us/dell-openmanage-enterprise/ome_4_2_online_help_and_user_guide){target="_blank"}.

2. **Create static groups in OME** for each Omnia functional group you plan
   to use. The group names must exactly match the functional group names:

    - `slurm_control_node_x86_64`
    - `slurm_node_x86_64`
    - `slurm_node_aarch64`
    - `login_node_x86_64` / `login_node_aarch64`
    - `login_compiler_node_x86_64` / `login_compiler_node_aarch64`
    - `service_kube_control_plane_x86_64`
    - `service_kube_node_x86_64`
    - `os_x86_64` / `os_aarch64`

    To create static groups in OME:

    - Navigate to **CUSTOM GROUPS > Static Groups**.
    - Click the ellipsis (**…**) next to Static Groups and select
      **Create Group**.
    - Enter the group name exactly matching the functional group name.
    - Add a description for the group.
    - Click **Finish**.

    Repeat this process for each functional group type you plan to use in
    your Omnia deployment.

3. **Add discovered servers to the static groups** in OME:

    - Select the static functional group from the list.
    - Click **Add Devices**.
    - In the **Add Devices to Group** dialog box, select the servers that
      belong to that functional group.
    - Click **Finish**.

    Repeat for all functional groups, ensuring each server is assigned to
    the correct static group based on its intended role in the Omnia
    cluster.

    !!! note

        Devices not assigned to any Omnia-supported custom static group
        will default to `slurm_node_aarch64` in the auto-generated
        mapping file.

4. **Configure the discovery input file**:

    ```bash title="Run on: omnia_core container"
    vi /opt/omnia/input/project_default/discovery_config.yml
    ```

    ```yaml title="File: /opt/omnia/input/project_default/discovery_config.yml"
    enable_bmc_discovery: true
    ome_ip: "<ome-ip-address>"
    ```

    | Parameter | Mandatory | Description |
    | --- | --- | --- |
    | `enable_bmc_discovery` | Optional | Set to `true` to enable BMC discovery via OME. When `false`, OME credentials are not prompted during `prepare_oim`. Default: `false` |
    | `ome_ip` | Conditional | IP address of the OME instance. Required when `enable_bmc_discovery` is `true`. Example: `"192.168.1.100"` |

    For the full parameter reference, see
    [discovery_config.yml Reference](../../Reference/Configuration/discovery_config.md){target="_blank"}.

5. **Run the discovery playbook**:

    ```bash title="Run on: omnia_core container"
    cd /omnia/discovery
    ansible-playbook discovery.yml -e "discovery_mechanism=ome"
    ```

    The playbook will prompt for OME credentials if not already configured.

6. **Verify and edit the generated mapping file**:

    ```bash title="Run on: omnia_core container"
    ls /opt/omnia/input/project_default/bmc_pxe_mapping_file_*.csv
    cat /opt/omnia/input/project_default/bmc_pxe_mapping_file_*.csv
    ```

    Review the file and update `HOSTNAME`, `FUNCTIONAL_GROUP_NAME`,
    `GROUP_NAME`, and `PARENT_SERVICE_TAG` columns as needed for your
    deployment.

### Completion message

After discovery completes, a summary message is displayed with paths to
both output files:

```text
============================================================
OME Discovery Complete
============================================================
BMC PXE mapping file generated:
  /opt/omnia/input/project_default/bmc_pxe_mapping_file_<timestamp>.csv
BMC discovery report generated:
  /opt/omnia/discovery/bmc_discovery_report_<timestamp>.csv
  (Lists link status of BMC, Ethernet, and InfiniBand NICs for each server)
Total servers discovered: <count>
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

## BMC discovery report

The discovery playbook also generates a BMC discovery report CSV with NIC
link statuses for all discovered servers. Use this report to verify NIC
connectivity before provisioning. The report shares the same timestamp as
the PXE mapping file for easy correlation.

**Output file:** `/opt/omnia/discovery/bmc_discovery_report_<timestamp>.csv`

Where `<timestamp>` is in `YYYYMMDDTHHMMSS` format (e.g.,
`20260601T120000`).

| Column | Description |
| --- | --- |
| `SERVICE_TAG` | Dell service tag uniquely identifying the server |
| `BMC_MAC` | MAC address of the BMC (iDRAC) network interface |
| `BMC_IP` | IP address assigned to the BMC (iDRAC) |
| `BMC_NIC_STATUS` | Link status of the BMC NIC (typically `Up` if the server is managed by OME) |
| `ETHERNET_NIC_MAC` | MAC address of the first Ethernet NIC (excluding iDRAC and InfiniBand NICs) |
| `ETHERNET_NIC_LINK_STATUS` | Link status of the Ethernet NIC (`Up`, `Down`, `Unknown`) |
| `IB_NIC_NAME` | FQDD of the InfiniBand NIC port (e.g., `InfiniBand.Slot.3-1`). Empty if no InfiniBand NIC is present |
| `IB_NIC_LINK_STATUS` | Link status of the InfiniBand NIC (`Up`, `Down`, `Unknown`). Empty if no InfiniBand NIC is present |

### NIC link statuses

**BMC NIC status**: Indicates whether the iDRAC is reachable from OME.
Since OME manages the server, this is typically `Up`.

**Ethernet NIC link status**: Reflects the physical link state of the first
non-iDRAC, non-InfiniBand network port:

- **Up** -- Cable connected and link established
- **Down** -- No link detected (cable disconnected or switch port down)
- **Unknown** -- iDRAC cannot determine the link state. This can occur
  when the NIC firmware has not been initialized or the server is powered
  off

!!! note

    When all Ethernet NICs report `Unknown` status, Omnia selects the
    first available Ethernet NIC as a fallback. InfiniBand NICs are never
    selected as the Ethernet/admin NIC.

**InfiniBand NIC link status**: Reflects the state of the IB port:

- **Up** -- InfiniBand link is active
- **Down** -- No InfiniBand link detected
- **Unknown** -- iDRAC reports the link state as unknown. This is common
  for InfiniBand NICs even when they are active at the OS level, as iDRAC
  may not have full visibility into InfiniBand link state

!!! note

    InfiniBand NIC selection uses a priority-based fallback: `Up` is
    preferred, followed by `Unknown`, then `Down`. This ensures an IB NIC
    is reported even when iDRAC cannot determine its link state.

### Use cases

**Pre-provisioning health check**: Before running `provision.yml`, review
the discovery report to verify:

- All servers have valid BMC IPs and MAC addresses
- Ethernet NICs are in `Up` state (required for PXE boot)
- InfiniBand NICs are detected on servers that require IB connectivity

**Troubleshooting NIC connectivity**: If a server fails to PXE boot during
provisioning:

1. Check the `ETHERNET_NIC_LINK_STATUS` in the discovery report
2. If the status is `Down` or `Unknown`, verify the physical cable
   connection and switch port configuration
3. If the `ETHERNET_NIC_MAC` appears incorrect, check NIC ordering in
   BIOS/iDRAC settings

**Inventory auditing**: The report serves as a point-in-time snapshot of
the cluster's NIC inventory, useful for:

- Verifying InfiniBand fabric connectivity across all nodes
- Tracking which servers have IB NICs installed
- Auditing MAC addresses for network security compliance

### Relationship to PXE mapping file

| Attribute | PXE Mapping File | Discovery Report |
| --- | --- | --- |
| Purpose | Input for provisioning | Diagnostic and auditing |
| Editable | Yes (user edits hostnames, groups) | No (read-only reference) |
| Contains NIC link status | No | Yes |
| Contains IP assignments | Yes (`ADMIN_IP`, `BMC_IP`, `IB_IP`) | Yes (`BMC_IP` only) |
| Contains hostnames | Yes | No |
| Used by `provision.yml` | Yes | No |

## Next Steps

- [Configure Inputs](configure_inputs.md) -- Configure Omnia input files.
- [Configure Credentials](configure_credentials.md) -- Set up encrypted
  credentials.

## Troubleshooting

**`ome_ip must be provided in discovery_config.yml`**

Set `enable_bmc_discovery: true` and provide a valid `ome_ip` in
`discovery_config.yml`.

**Devices appear as `slurm_node_aarch64` in the mapping file**

Ensure the devices are assigned to the correct static group in OME. Devices
not in any Omnia-supported custom static group default to
`slurm_node_aarch64`.

**Missing Ethernet NIC MAC in the mapping file**

Verify NIC ordering in the server BIOS/iDRAC settings. Omnia selects the
first active Ethernet NIC (excluding iDRAC and InfiniBand NICs).

**Incorrect hostnames in the generated file**

Ensure iDRAC hostnames follow the Omnia naming convention
(`idrac-<SU>R<Rack>OU<Position><Type><Instance>`) before running discovery.

**OME connection failure**

Verify OME is accessible from the OIM:

```bash title="Run on: OIM host"
curl -sk https://<ome-ip>/api/SessionService/Sessions -X POST \
  -H "Content-Type: application/json" \
  -d '{"UserName":"<user>","Password":"<pass>"}'
```
