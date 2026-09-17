# Discover nodes using OME

## Overview

The Omnia Discovery module connects to Dell OpenManage Enterprise (OME) from
the Omnia Infrastructure Manager (OIM), collects server and network-interface
inventory, and generates the node mapping used by the Orchestrator module.
Discovery runs locally on the OIM and supports OME as its discovery mechanism.

A complete untagged run:

1. Validates `discovery_config.yml`.
2. Creates or loads the OME credentials stored for the selected project.
3. Verifies that OME is reachable on TCP port 443.
4. Collects OME devices of server type `1000`, their iDRAC details, Ethernet
   interfaces, InfiniBand interfaces, and OME static-group membership.
5. Generates a timestamped PXE mapping file and a NIC-status report.
6. Once the OME discovery role starts, writes `discovery_status.yml` with the
   result of that role.

With the default data path and project, the generated files are under
`/opt/omnia/discovery/output/project_default/`:

| File | Purpose |
|------|---------|
| `bmc_pxe_mapping_file_<timestamp>.csv` | Timestamped node mapping for review and downstream use. |
| `bmc_pxe_mapping_file.csv` | Symbolic link to the latest timestamped mapping file. |
| `bmc_discovery_report_<timestamp>.csv` | Point-in-time report of BMC, Ethernet, and InfiniBand NIC status. |
| `discovery_status.yml` | OME role status, mapping-file path, discovered-server count, and timestamp. This file is not updated by earlier failures. |

Discovery generates the mapping required by the downstream deployment
workflow. It does not build OS images.

## Prerequisites

- Run Discovery on the OIM with permission to create files under the Omnia data
  path and `/var/log/omnia/discovery/discovery.log`.
- Complete [OIM setup](../main/setup_oim.md). The main setup runs the Discovery
  initialization script, installs its dependencies, creates its runtime and log
  directories, and stages its input templates.
- If Discovery was skipped during main setup, initialize it with
  `./omnia.sh --init discovery` from `src/main` before the first run.
- Use the module-initialized environment. `requirements.txt` requests Ansible
  Core 2.20 or later, Jinja 3.0 or later, and PyYAML 6.0.3 or later;
  `requirements.yml` requests `ansible.posix` 2.0.0 and `community.general`
  10.3.0. The `requests` Python library must also be importable by Ansible, and
  `openssl` must be available to generate a Vault password when the credential
  files do not exist.
- OME must be installed, powered on, and reachable from the OIM over HTTPS on
  TCP port 443.
- Credentials for an OME administrator, or an account with equivalent
  permissions to create an API session and read the required inventory, must be
  available. Discovery prompts for missing OME credentials, saves them in
  `discovery_credentials.yml`, and encrypts the file with Ansible Vault using
  `.discovery_credentials_key`.
- Every target server must have its BMC/iDRAC interface configured with network
  connectivity and must already be discovered and managed by OME as a server
  device. Each target must report a service tag. Devices without a service tag
  are not added to the discovered server list.
- OME must expose the device, group, device-management, and server network
  interface inventory used by Discovery.

### Network connectivity requirements

| Connection | Requirement |
|------------|-------------|
| OIM to OME | The OIM must be able to route to the configured `ome_ip` and establish an HTTPS connection on TCP port 443. Permit this outbound connection through intervening firewalls. |
| OME to target BMC/iDRAC | Each BMC/iDRAC interface must have working network configuration and be reachable from OME. Before running Discovery, confirm that OME lists the target as a server device and displays its service tag, management address, and network-interface inventory. |
| OIM to target BMC/iDRAC | The Discovery workflow does not connect directly to target BMC/iDRAC interfaces. It obtains their management and NIC data through the OME API. Direct or routed OIM-to-iDRAC connectivity can still be required by downstream provisioning and other Omnia operations. |

The OME account must be able to create an API session and read devices, static
groups and group membership, device-management details, and server
network-interface inventory. OME administrative access provides these
permissions. If a restricted account is used, grant equivalent read access to
these resources.

The subnets in the Discovery-owned `network_spec.yml` are used to derive
addresses written to the mapping file. They do not configure or validate the
network paths between the OIM, OME, and target BMC/iDRAC interfaces. For the
deployment-wide BMC network design, see [Network
topologies](../../Overview/network_topologies.md).

### NIC MAC address selection

Discovery uses the interface and port order returned by the OME
`serverNetworkInterfaces` inventory. It does not sort candidates by NIC name,
slot, port number, or MAC address. Within the same priority, the first candidate
returned by OME is selected. Review the NIC presentation and port ordering in
OME after changing adapter, BIOS, or iDRAC configuration.

For the Admin NIC, Discovery excludes an interface whose OME `NicId` contains
`InfiniBand`, using a case-insensitive comparison. A primary candidate must
contain a port with at least one partition and a nonempty
`CurrentMacAddress`; Discovery uses the first partition's current MAC address.
Always verify that the generated `ADMIN_MAC` is the intended admin/PXE
interface and is not a management interface before provisioning.

**Admin NIC selection priority:**

| Priority | Condition | Selection behavior |
|----------|-----------|--------------------|
| 1 | At least one usable candidate that passes the current `NicId` filter is reported as `Up` | Select the first `Up` candidate in OME inventory order. Earlier candidates reported as `Down`, `Unknown`, or another state are skipped. |
| 2 | No usable candidate is reported as `Up`, but the primary inventory contains a usable candidate that passes the current `NicId` filter | Select the first such candidate in OME inventory order, regardless of its reported state. This is the fallback when all usable candidates are `Down`, `Unknown`, or another non-`Up` state. |
| 3 | The primary inventory contains no usable candidate | Query the OME `deviceNics` inventory and select the first entry that passes the same `NicId` filter. If neither inventory supplies a usable MAC address, leave `ADMIN_MAC` empty. The secondary inventory does not supply the selected port's link status. |

The selected Admin MAC is written to `ADMIN_MAC` in the PXE mapping and to
`ETHERNET_NIC_MAC` in the discovery report. Its primary-inventory link state is
written only to `ETHERNET_NIC_LINK_STATUS` in the report.

For InfiniBand, Discovery evaluates interfaces whose OME `NicId` contains
`InfiniBand`, then evaluates their ports in the order returned by OME.

**InfiniBand NIC selection priority:**

| Priority | Condition | Selection behavior |
|----------|-----------|--------------------|
| 1 | An InfiniBand port is reported as `Up` | Select the first `Up` port in OME inventory order. |
| 2 | No port is `Up`, but a port is reported as `Unknown` or without a status | Select the first such port as the fallback. A missing status is normalized to `Unknown`. |
| 3 | No port is `Up` or `Unknown`, but an InfiniBand port has another state such as `Down` | Select the first port at this priority as the last resort. |

If OME reports no interface whose `NicId` contains `InfiniBand`, Discovery
leaves `IB_NIC_NAME` and `IB_NIC_LINK_STATUS` empty in the report and leaves
`IB_NIC_NAME` and `IB_IP` empty in the mapping. This is expected for servers
that do not require InfiniBand. If an interface is expected, refresh and verify
the server inventory in OME before rerunning Discovery.

### Input contract

Discovery resolves its runtime paths from the following values:

| Input | Required value or default |
|-------|---------------------------|
| `OMNIA_DATA_PATH` | Optional. Defaults to `/opt/omnia`. |
| `OMNIA_PROJECT_NAME` | Optional. Defaults to `project_default`. |
| `project_name` | Optional Ansible extra variable used when `OMNIA_PROJECT_NAME` is not set. |

Prepare the following files in
`<OMNIA_DATA_PATH>/discovery/input/<OMNIA_PROJECT_NAME>/`:

| Input | Requirement |
|-------|-------------|
| `discovery_config.yml` | Required. Contains the OME IPv4 address in `ome_ip`. |
| `network_spec.yml` | Required during execution. Discovery reads the admin and InfiniBand subnet values from this file to derive node IP addresses. |
| `discovery_credentials.yml` | Created automatically if absent. Contains `ome_username` and `ome_password` and is stored encrypted. |
| `.discovery_credentials_key` | Created automatically with the credential file and stored with mode `0400`. |

`discovery_config.yml` must contain `ome_ip` set to a valid, non-loopback OME
IPv4 address.

The credential workflow requires a nonempty OME username and password. The
username must contain between 1 and 64 characters and cannot contain a
backslash, single quote, double quote, or semicolon. The password must contain
between 1 and 128 characters. Discovery prompts only for values that are empty
or absent in the credential file.

### Plan iDRAC hostnames

Discovery uses the iDRAC hostname reported by OME to derive the physical
`GROUP_NAME` written to the PXE mapping file. Configure consistent iDRAC
hostnames before running Discovery so that generated physical-group values
match the intended topology.

Use the following complete naming convention when encoding the server's
physical location:

```text
idrac-<SU><1-100>R<000-999>OU<1-54><Type><Instance>
```

| Component | Description | Recommended format |
|-----------|-------------|--------------------|
| `SU` | Scalable Unit containing the server. | `SU1` through `SU100`; matching is case-insensitive. |
| `R` | Rack within the Scalable Unit. | `R1` through `R999`. |
| `OU` | Open Rack v3 unit position within the rack. | `OU1` through `OU54`. |
| `Type` | Server type at the rack position. | Use `C` for a compute node. |
| `Instance` | Individual server instance at the rack position. | `1` through `99`. |

For example:

```text title="Example breakdown"
SU02   R1   OU05   C7
│      │     │      │
│      │     │      └── Compute node instance
│      │     └───────── Open Rack v3 unit position
│      └─────────────── Rack within the Scalable Unit
└────────────────────── Scalable Unit
```

`idrac-SU02R1OU05C7` identifies compute node 7 at unit position 5 in rack 1
of Scalable Unit 02.

The current mapping generator searches the OME-reported hostname for a
case-insensitive `SU[optional-letter]<digits>R<digits>` sequence and writes the
matched `SU` portion in uppercase. The complete naming convention and numeric
ranges above are operational planning requirements; Discovery does not
validate the entire hostname or those ranges.

| OME-reported iDRAC hostname | Generated `GROUP_NAME` |
|-----------------------------|------------------------|
| `idrac-SU02R1OU05C7` | `SU02` |
| `idrac-SUA99R999OU30C2` | `SUA99` |
| `SU1R2OU1C5` | `SU1` |
| `idrac-JCGT033` | `grp0` |

!!! warning

    OME can report an instrumentation name, a DNS name, or its device name for
    the iDRAC. Verify the value visible in OME before running Discovery. If the
    reported hostname does not contain a recognized `SU...R...` sequence,
    Discovery uses `grp0`. Review every generated `GROUP_NAME` before using the
    mapping as Orchestrator input.

### Review generated parent metadata

Discovery may populate optional `PARENT_SERVICE_TAG` metadata in generated
Slurm compute rows. This is Discovery generation behavior, not an Orchestrator
grouping requirement. Orchestrator does not require a parent value or validate
it against `GROUP_NAME`; review, edit, or clear it as appropriate.

A service Kubernetes cluster must include `service_kube_node_x86_64` in the
mapping. The cluster-wide minimum also includes three
`service_kube_control_plane_x86_64` servers. For the complete service-cluster
requirements, see [Kubernetes
requirements](../../Reference/ClusterRequirements/kubernetes_requirements.md)
and [Deploy Service Kubernetes](../orchestrator/deploy_kubernetes.md).

!!! warning

    Review every generated parent value before copying the mapping to the
    Orchestrator input directory. Discovery-generated parent metadata does not
    create an Orchestrator validation requirement.

### Plan OME static groups

When OME exposes a `Static Groups` container, Discovery uses its immediate
child groups as functional-group assignments. If that container is absent,
Discovery falls back to non-system OME groups. A server can belong to no more
than one of the groups that Discovery processes; Discovery stops if a server
belongs to multiple processed groups.

The mapping generator accepts these exact, case-sensitive OME static-group
names:

- `service_kube_control_plane_x86_64`
- `service_kube_node_x86_64`
- `login_node_x86_64`
- `login_node_aarch64`
- `login_compiler_node_x86_64`
- `login_compiler_node_aarch64`
- `slurm_control_node_x86_64`
- `slurm_node_x86_64`
- `slurm_node_aarch64`
- `os_x86_64`
- `os_aarch64`

#### Create OME static groups

Create one static group for each Omnia functional group required by the
cluster:

1. In the OME left navigation menu, select **CUSTOM GROUPS > Static Groups**.
2. Select the ellipsis (**...**) next to **Static Groups**, and then select
   **Create Group**.
3. Enter one of the supported functional-group names exactly as listed above.
4. Enter a description that identifies the purpose of the group.
5. Select **Finish**.

Repeat these steps for each functional group required by the cluster. The
group name determines the value written to `FUNCTIONAL_GROUP_NAME`; the group
description does not affect Discovery behavior.

#### Assign devices to OME static groups

After creating the required static groups, assign the discovered servers:

1. Select the static group from the OME group list.
2. Select **Add Devices**.
3. In the **Add Devices to Group** dialog box, select the servers whose
   intended role matches the functional group.
4. Select **Finish**.

Repeat these steps for the remaining groups. Before running Discovery, verify
that each server is assigned to no more than one Omnia static group and that
each group is an immediate child of **Static Groups**.

A server without a static-group assignment is placed in
`slurm_node_aarch64`. A server assigned to a nonempty, unsupported static
group is skipped when the mapping file is generated, although it remains in
the discovery report.

For `slurm_node_x86_64` and `slurm_node_aarch64`, Discovery may populate
optional `PARENT_SERVICE_TAG` metadata. Review, edit, or clear that value as
appropriate before using the mapping as Orchestrator input.

## Procedure

1. In OME, discover or manage the target servers that Omnia will provision.
   Confirm that each target appears in OME as a server device and has a service
   tag, an iDRAC management address, and the expected network-interface
   inventory. Confirm that the account used by Discovery can view these
   details. Omnia queries the existing OME inventory; it does not add devices
   to OME. For the version-specific device-discovery procedure, see the
   [Dell OpenManage Enterprise documentation](https://www.dell.com/support/product-details/en-us/product/dell-openmanage-enterprise/docs){target="_blank"}.

2. [Configure the Main environment](../main/configure_environment.md). The
   examples on this page use `OMNIA_DATA_PATH=/opt/omnia` and
   `OMNIA_PROJECT_NAME=project_default`.

3. Complete OIM setup. If Discovery was skipped during setup, initialize only
   this domain:

    ```bash title="Run on: OIM host"
    cd src/main
    ./omnia.sh --init discovery
    ```

    Initialization installs the declared dependencies, creates the runtime and
    log directories, and copies `discovery_config.yml` and `network_spec.yml` to
    `<OMNIA_DATA_PATH>/discovery/input/<OMNIA_PROJECT_NAME>/`. Review its output
    and confirm that the dependencies are available.

    !!! warning

        If the destination already contains files, initialization asks before
        overwriting them. Preserve any project-specific changes when responding
        to the prompt.

4. [Create the required OME static groups](#create-ome-static-groups), and then
   [assign the discovered servers](#assign-devices-to-ome-static-groups). Use
   an exact supported functional-group name and place each server in no more
   than one Omnia static group. A server without a static-group assignment
   uses the default functional group.

5. Edit the staged `discovery_config.yml` and configure the OME appliance:

    ```yaml title="File: /opt/omnia/discovery/input/project_default/discovery_config.yml"
    ome_ip: "192.168.1.100"
    ```

    Configure `ome_ip` with a valid, non-loopback OME IPv4 address, which is the
    format defined by the Discovery configuration schema.

6. Edit the staged `network_spec.yml`. Discovery uses only
   `admin_network.subnet` and `ib_network.subnet`; preserve the `Networks` list
   and both network entries from the staged template.

    ```yaml title="File: /opt/omnia/discovery/input/project_default/network_spec.yml"
    Networks:
      - admin_network:
          subnet: "172.16.0.0"

      - ib_network:
          subnet: "192.168.0.0"
    ```

    Discovery derives `ADMIN_IP` by combining the first two octets of the admin
    subnet with the last two octets of the server's BMC IP. It derives `IB_IP`
    in the same way from the InfiniBand subnet, but only when an InfiniBand NIC
    was detected. The Discovery validator does not validate `network_spec.yml`,
    so review these subnet values before execution.

7. Validate `discovery_config.yml` before contacting OME:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run discovery --tags validate
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/discovery/playbooks
        ansible-playbook discovery.yml --tags validate
        ```

    A successful validation prints `Discovery configuration validation passed.`
    and displays the validation-log path. This phase does not request OME
    credentials.

8. Run the complete Discovery workflow:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run discovery
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/discovery/playbooks
        ansible-playbook discovery.yml
        ```

    When `discovery_credentials.yml` does not exist, Discovery creates it and
    creates its Vault key if needed. Enter the OME username and password when
    prompted. The password prompt asks for confirmation before the credential
    file is encrypted.

    The default untagged run performs setup, validation, credential handling,
    and OME discovery. The `execute` and `discovery` tags route to the same OME
    execution flow. The `credentials` tag updates credentials without running
    discovery. Use only one tag in a command. See [Run
    Discovery](index.md#run-discovery) for the complete tag table, including
    the supported precheck, cleanup operations, and lifecycle placeholders.

    The supported Discovery execution flow uses OME. The playbook sets
    `discovery_mechanism` to `ome` internally; do not pass
    `-e discovery_mechanism=ome`.

### Expected completion output

A successful run without BuildStreaM prints a completion summary in this form:

```text title="Representative success output"
============================================================
OME Discovery Complete
============================================================
BMC PXE mapping file generated: /opt/omnia/discovery/output/project_default/bmc_pxe_mapping_file_<timestamp>.csv
BMC discovery report generated: /opt/omnia/discovery/output/project_default/bmc_discovery_report_<timestamp>.csv
  (Lists link status of BMC, Ethernet, and InfiniBand NICs for each server)
Total servers discovered: <count>

Output directory: /opt/omnia/discovery/output/project_default

Next Steps:
1. Review and edit the generated PXE mapping file.
2. Review the discovery report for NIC link statuses.
3. Update HOSTNAME, FUNCTIONAL_GROUP_NAME, GROUP_NAME as needed.
4. Copy the mapping file to the Orchestrator input directory.
============================================================
```

The current Discovery implementation may print a BuildStreaM-specific
completion message only when a `build_stream_config.yml` is present in the
Discovery input directory. That file is not part of the Discovery input
contract. Follow the BuildStreaM handoff in [Next steps](#next-steps)
instead of copying another domain's configuration into this directory.

## BMC discovery report

Discovery generates a read-only CSV report from the OME inventory for every
discovered server that has a service tag. The report provides a point-in-time
view of the BMC, selected Ethernet, and selected InfiniBand interfaces and
their OME-reported link states. Review it before provisioning to identify
missing inventory or connectivity that can prevent management access or PXE
boot.

### Report location

The report is written to the Discovery-owned project output directory:

```text
<OMNIA_DATA_PATH>/discovery/output/<OMNIA_PROJECT_NAME>/bmc_discovery_report_<timestamp>.csv
```

With the standard data path and project name, the location is:

```text
/opt/omnia/discovery/output/project_default/bmc_discovery_report_<timestamp>.csv
```

The timestamp matches the timestamped PXE mapping generated by the same run.
Unlike the mapping, the report does not have a stable symbolic link. Use the
path printed in the completion output or substitute the mapping timestamp when
opening the report.

### Report columns

| Column | Description |
|--------|-------------|
| `SERVICE_TAG` | Dell service tag used to correlate the row with the physical server, OME inventory, and PXE mapping. |
| `BMC_MAC` | MAC address from the server's OME iDRAC management record. |
| `BMC_IP` | IP address from the server's OME iDRAC management record. |
| `BMC_NIC_STATUS` | `Up` when Discovery finds an iDRAC management record. This value represents OME inventory availability; it is not a live reachability test from the OIM. |
| `ETHERNET_NIC_MAC` | MAC address of the selected interface that passes the current `NicId` filter. Discovery excludes InfiniBand labels, prefers the first usable interface reported as `Up`, and then falls back to the first usable interface. Confirm that this is the intended admin/PXE interface and not a management interface. |
| `ETHERNET_NIC_LINK_STATUS` | OME-reported link state of the Ethernet interface selected for `ETHERNET_NIC_MAC`. |
| `IB_NIC_NAME` | OME identifier for the selected InfiniBand port. Empty when OME reports no InfiniBand interface. |
| `IB_NIC_LINK_STATUS` | OME-reported link state of the selected InfiniBand port. Empty when no InfiniBand interface is selected. |

### Sample report

```csv title="Illustrative bmc_discovery_report_<timestamp>.csv"
SERVICE_TAG,BMC_MAC,BMC_IP,BMC_NIC_STATUS,ETHERNET_NIC_MAC,ETHERNET_NIC_LINK_STATUS,IB_NIC_NAME,IB_NIC_LINK_STATUS
H94M8F3,B8:CE:F6:57:89:D0,172.16.0.101,Up,B0:7B:25:D8:4A:F4,Up,InfiniBand.Slot.3-1,Unknown
J7KN2G4,A4:BF:01:12:34:56,172.16.0.102,Up,E4:43:4B:01:23:45,Up,,
K5LP9H2,D0:94:66:AB:CD:EF,172.16.0.103,Up,24:6E:96:78:90:12,Unknown,InfiniBand.Slot.3-1,Up
```

The values are examples only. Compare each row with the corresponding server
and current OME inventory.

### Interpret NIC link status

- **BMC:** A value of `Up` means that Discovery found an iDRAC management
  record in OME. Confirm BMC connectivity in OME or with an approved network
  test when current reachability must be established. An empty value indicates
  that the required management record was not returned.
- **Ethernet:** `Up` indicates that OME reports a link for the selected
  Ethernet port. `Down` generally indicates no active physical link.
  `Unknown` means that OME did not provide a definitive state. When no usable
  Ethernet port is reported as `Up`, Discovery records the first usable
  candidate that passes the current `NicId` filter as a fallback. Confirm the
  selected MAC is the intended admin/PXE interface.
- **InfiniBand:** Discovery prefers a port reported as `Up`, then `Unknown`,
  then another reported state such as `Down`. An `Unknown` state can occur even
  when the fabric becomes available at the operating-system level. Confirm the
  fabric independently before provisioning workloads that require it.

### Pre-provisioning checks

Before copying the mapping to the Orchestrator input directory:

1. Confirm that every expected service tag appears in the report.
2. Confirm that `BMC_IP` and `BMC_MAC` match the intended server's iDRAC
   inventory.
3. Confirm that `ETHERNET_NIC_MAC` is the interface connected to the admin/PXE
   network and investigate `Down`, `Unknown`, or empty link states.
4. Confirm that servers requiring InfiniBand have an `IB_NIC_NAME`, and
   investigate an unexpected or empty link state.
5. Compare the report and mapping rows by `SERVICE_TAG`, using files with the
   same timestamp.

### Troubleshoot NIC connectivity

If the expected interface is missing or has an unexpected state:

1. Locate the server by `SERVICE_TAG` in the report and inspect the BMC,
   Ethernet, and InfiniBand fields together.
2. In OME, refresh the server inventory and confirm the iDRAC management
   record, NIC ordering, current MAC addresses, and port link states.
3. For an Ethernet state of `Down` or `Unknown`, inspect the cable, switch port,
   and server BIOS/iDRAC NIC settings. Confirm that the intended admin/PXE port
   is enabled and connected.
4. For an InfiniBand state of `Down` or `Unknown`, inspect the adapter, cable,
   fabric port, and fabric configuration. Validate the link at the operating
   system when OME cannot determine its state.
5. Rerun Discovery after OME shows the corrected inventory, then review the
   newly timestamped report and mapping together.

For selection-specific guidance, see [The admin MAC address is unexpected or
empty](#the-admin-mac-address-is-unexpected-or-empty) and [InfiniBand fields are
empty](#infiniband-fields-are-empty).

### Relationship to the PXE mapping

| Attribute | PXE mapping file | BMC discovery report |
|-----------|------------------|----------------------|
| Purpose | Reviewed input handed to Orchestrator for provisioning | Diagnostic and inventory snapshot used before provisioning |
| Rows | Servers in supported OME static groups, plus unassigned servers | Every discovered OME server that has a service tag |
| Editable | Review and correct values before the Orchestrator handoff | No; retain as a read-only record of the OME inventory |
| NIC link status | Not included | Includes BMC, selected Ethernet, and selected InfiniBand status |
| IP addresses | Includes `ADMIN_IP`, `BMC_IP`, and `IB_IP` | Includes `BMC_IP` only |
| Hostname | Includes the generated `HOSTNAME` | Not included |
| Downstream use | Copied to the Orchestrator input project as `pxe_mapping_file.csv` | Not consumed by Orchestrator |

## Verification

1. **Output contract:** After a successful OME discovery, confirm that the
   project output directory,
   `<OMNIA_DATA_PATH>/discovery/output/<OMNIA_PROJECT_NAME>/`, contains the
   following artifacts:

    | Artifact | Verification |
    |----------|--------------|
    | `bmc_pxe_mapping_file_<timestamp>.csv` | Timestamped PXE mapping containing discovered servers whose OME static-group assignment is supported or empty. |
    | `bmc_pxe_mapping_file.csv` | Symbolic link to the latest timestamped mapping file. |
    | `bmc_discovery_report_<timestamp>.csv` | NIC-status report generated from every discovered server that has a service tag. |
    | `discovery_status.yml` | Status of the OME discovery role, mapping-file path, discovered-server count, and timestamp. |

    With the standard data path and project name, check the status file:

    ```bash title="Run on: OIM host"
    cat /opt/omnia/discovery/output/project_default/discovery_status.yml
    ```

    A successful status file has this structure:

    ```yaml title="Expected structure"
    overall_status: "success"
    discovery_mechanism: "ome"
    bmc_pxe_mapping_file: "/opt/omnia/discovery/output/project_default/bmc_pxe_mapping_file_<timestamp>.csv"
    servers_discovered: <count>
    timestamp: "<ISO 8601 timestamp>"
    ```

    Confirm that `overall_status` is `success`, `discovery_mechanism` is `ome`,
    `bmc_pxe_mapping_file` identifies the timestamped mapping file, and
    `servers_discovered` matches the OME servers expected in the discovery
    report. Setup, validation, and credential failures occur before this status
    file is updated; for those failures, use the Ansible output and log instead
    of relying on an existing status file.

2. Confirm that the stable mapping-file link resolves to the latest
   timestamped file:

    ```bash title="Run on: OIM host"
    readlink /opt/omnia/discovery/output/project_default/bmc_pxe_mapping_file.csv
    ```

3. Review the generated mapping:

    ```bash title="Run on: OIM host"
    cat /opt/omnia/discovery/output/project_default/bmc_pxe_mapping_file.csv
    ```

    The mapping contains these columns:

    | Column | Generated value |
    |--------|-----------------|
    | `FUNCTIONAL_GROUP_NAME` | Supported OME static-group name, or `slurm_node_aarch64` when the server has no assignment. |
    | `GROUP_NAME` | `SU` identifier derived from the iDRAC hostname, or `grp0` when no identifier is found. |
    | `SERVICE_TAG` | Service tag reported by OME. |
    | `PARENT_SERVICE_TAG` | Optional parent-node service tag that Discovery may populate for a Slurm compute row; otherwise empty. Review this value before using the mapping. |
    | `HOSTNAME` | `nid` plus a three-digit sequence number based on discovery order. The supported range is `nid000` through `nid999`; automatic generation normally begins with `nid001`, and skipped devices can create gaps. |
    | `ADMIN_MAC` | MAC of the first candidate that passes the current `NicId` filter and has link status `Up`; otherwise the first usable candidate that passes the filter. Confirm that this is the intended admin/PXE interface and not a management interface. |
    | `ADMIN_IP` | Admin subnet's first two octets combined with the BMC IP's last two octets. |
    | `BMC_MAC` | iDRAC MAC address reported by OME. |
    | `BMC_IP` | iDRAC IP address reported by OME. |
    | `IB_NIC_NAME` | InfiniBand port identifier selected with priority `Up`, then `Unknown`, then another reported state; empty when no InfiniBand NIC is found. |
    | `IB_IP` | InfiniBand subnet's first two octets combined with the BMC IP's last two octets; empty when no InfiniBand NIC is found. |

4. **Server attribute checklist:** Use `SERVICE_TAG` to correlate every mapping
   row with the physical server and its OME inventory. Confirm the following
   values before handing the mapping to Orchestrator:

    | Attribute | Confirmation |
    |-----------|--------------|
    | Server coverage | Every expected service tag occurs exactly once. Investigate an absent server in the discovery report and its OME static-group assignment. |
    | `FUNCTIONAL_GROUP_NAME` | The value is the server's intended Omnia role and exactly matches a supported, case-sensitive functional-group name. An unassigned OME server defaults to `slurm_node_aarch64`; retain that default only when it is the intended role. |
    | `ADMIN_MAC` | The value is nonempty, unique, and matches the Ethernet port that the server will use on the admin/PXE network. Compare it with the OME interface inventory and `ETHERNET_NIC_MAC` in the discovery report. Prefer a port whose reported link status is `Up`. |
    | `BMC_IP` | The value is nonempty and matches the iDRAC management address reported for that service tag in OME. Discovery copies this value from OME; it does not confirm that the address is correct for the physical server. |
    | `HOSTNAME` | The value is unique and matches the deployment's hostname plan. Discovery generates a three-digit `nid` sequence beginning with `nid001`; edit the value when the generated assignment is not the intended one. |

    !!! warning

        A generated mapping can contain syntactically valid values that do not
        match the intended physical server or deployment role. Correct the
        reviewed mapping before copying it to the Orchestrator input directory.

5. Review the report with the same timestamp as the mapping file. Replace
   `<timestamp>` with the value in the mapping filename:

    ```bash title="Run on: OIM host"
    cat /opt/omnia/discovery/output/project_default/bmc_discovery_report_<timestamp>.csv
    ```

    The report contains `SERVICE_TAG`, `BMC_MAC`, `BMC_IP`, `BMC_NIC_STATUS`,
    `ETHERNET_NIC_MAC`, `ETHERNET_NIC_LINK_STATUS`, `IB_NIC_NAME`, and
    `IB_NIC_LINK_STATUS`. Use it to identify missing NIC inventory and links
    reported as `Down` or `Unknown` before using the mapping downstream.

    The report includes every discovered server with a service tag. The mapping
    can contain fewer rows when a server was assigned to an unsupported OME
    static group. See [BMC discovery report](#bmc-discovery-report) for the
    column definitions, status interpretation, pre-provisioning checks, and
    troubleshooting procedure.

## Next steps

1. Review and, where necessary, edit `HOSTNAME`, `FUNCTIONAL_GROUP_NAME`, and
   `GROUP_NAME` in the timestamped mapping file. Also confirm the generated
   service tags, optional parent metadata, MAC addresses, and IP addresses.

2. Without BuildStreaM, copy the reviewed mapping to the Orchestrator input
   directory:

    ```bash title="Run on: OIM host"
    source /etc/profile.d/omnia-env.sh
    discovery_path="${OMNIA_DATA_PATH}/discovery"
    orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
    cp "${discovery_path}/output/${OMNIA_PROJECT_NAME}/bmc_pxe_mapping_file.csv" \
      "${orchestrator_path}/input/${OMNIA_PROJECT_NAME}/pxe_mapping_file.csv"
    ```

3. With BuildStreaM enabled, build the images through the build pipeline first.
   If the GitLab server is not yet available, place the reviewed mapping at the
   Orchestrator input path shown above. If GitLab is available, copy it to
   `input/orchestrator/pxe_mapping_file.csv` in the GitLab project and commit
   the change; the commit triggers the deploy pipeline for the nodes in that
   mapping.

## Troubleshooting

### Discovery configuration validation fails

- Confirm that
  `<OMNIA_DATA_PATH>/discovery/input/<project>/discovery_config.yml` exists and
  contains `ome_ip` set to a valid, non-loopback OME IPv4 address.
- Correct YAML parsing errors reported by the playbook.
- Review
  `/var/log/omnia/discovery/discovery.log`, then rerun
  the `validate` tag.

### OME is unreachable

Discovery waits up to 30 seconds for `<ome_ip>:443`. Confirm that `ome_ip` is
correct, OME is powered on, and routing and firewall rules allow the OIM to
reach OME on TCP port 443.

From the OIM, test the same HTTPS endpoint used to create an OME API session:

```bash title="Run on: OIM host"
curl --insecure --silent --show-error --connect-timeout 10 \
  --output /dev/null --write-out "HTTP status: %{http_code}\n" \
  https://<ome-ip>/api/SessionService/Sessions
```

An HTTP status confirms that the OIM reached the OME web service. An HTTP
status such as `401` only indicates that this unauthenticated connectivity test
was rejected as expected. An `HTTP status: 000`, timeout, connection refusal,
or TLS error indicates that the OIM did not complete the HTTPS request; check
the address, route, firewall, OME service, and certificate configuration.

!!! warning

    Do not add an OME username or password to this command. Discovery obtains
    credentials from the Vault-encrypted project credential file.

Review the Discovery log for the port check or API error:

```bash title="Run on: OIM host"
tail -n 100 /var/log/omnia/discovery/discovery.log
```

### OME authentication fails

Correct the `ome_username` and `ome_password` values managed in
`discovery_credentials.yml` before running Discovery again. Rerunning alone
does not replace nonempty stored credentials. If the credential file is
Vault-encrypted, its matching `.discovery_credentials_key` must be present in
the same project input directory. Confirm that the OME account can create an
API session and read the required device, group, management, and interface
inventory.

### No servers are discovered

Confirm that OME manages the target devices as server type `1000` and that the
devices have nonempty service tags. Discovery fails when the filtered server
list is empty.

### BMC or iDRAC information is missing

Confirm that the target BMC/iDRAC interface has working network connectivity
and that OME can manage it. In OME, verify that the server exposes its iDRAC
management address, MAC address, and server network-interface inventory.
Discovery reads these values from OME and does not probe the target iDRAC
directly.

### A server belongs to multiple OME static groups

Discovery reports each conflicting service tag and its groups, then stops.
Remove the duplicate static-group memberships so that each server belongs to
no more than one static group and rerun Discovery.

### A server is missing from the mapping

Look for a warning that names an unsupported OME static group. Rename the group
to one of the supported functional-group names or remove the server's static
group assignment to use the default. The server remains visible in the
discovery report if OME supplied its service tag.

### The admin MAC address is unexpected or empty

1. Find the server by service tag in the timestamped discovery report and check
   its `ETHERNET_NIC_MAC` and `ETHERNET_NIC_LINK_STATUS` values.
2. In OME, inspect the server network-interface inventory. Verify the NIC
   ordering, the port state, and the current MAC address reported for each
   Ethernet interface. Discovery excludes InfiniBand-labelled interfaces and
   selects the first usable candidate reported as `Up`. Confirm the selected
   MAC is the intended admin/PXE interface and not a management interface.
3. If the intended port is `Down` or `Unknown`, check its cable, switch port,
   and server BIOS/iDRAC NIC settings. If no usable Ethernet port is `Up`,
   Discovery falls back to the first usable candidate that passes the current
   `NicId` filter in the OME inventory.
4. Refresh the server inventory in OME, verify that the updated port order,
   link state, and MAC address are visible, and rerun Discovery.

If the primary server network-interface inventory produces no MAC address,
Discovery attempts the OME `deviceNics` inventory as a final fallback. A blank
`ADMIN_MAC` after the OME inventory is refreshed indicates that neither
inventory returned a usable Ethernet MAC address.

### InfiniBand fields are empty

This is expected when OME does not report an interface whose identifier
contains `InfiniBand`. When an interface is present, Discovery prefers an `Up`
port, then `Unknown`, and then another reported state.

### Group names or parent service tags are incorrect

The generated `HOSTNAME` and the OME-reported iDRAC hostname serve different
purposes. Discovery generates `HOSTNAME` as an `nid` sequence. It uses the
iDRAC hostname reported by OME only to derive `GROUP_NAME`.

1. In OME, inspect the iDRAC instrumentation name, DNS name, or device name
   displayed for the server. Discovery uses the first available value in that
   order.
2. Ensure that the value contains an `SU` identifier immediately followed by
   an `R` and rack number, such as `SU1R2OU1C5`. If no recognized `SU...R...`
   sequence is present, Discovery assigns `grp0`.
3. Correct the iDRAC hostname, refresh the server inventory in OME, and rerun
   Discovery. See [Plan iDRAC hostnames](#plan-idrac-hostnames) for the complete
   convention.
4. Review and, if necessary, edit the generated `HOSTNAME`, `GROUP_NAME`, and
   `PARENT_SERVICE_TAG` before copying the mapping to the Orchestrator input
   directory. Orchestrator does not require `PARENT_SERVICE_TAG` or validate it
   against `GROUP_NAME`.

### OME discovery execution fails

If OME execution started, inspect `discovery_status.yml`; a failed OME phase
records `failed_task` and `failure_reason`. Setup, validation, or credential
failures can leave that file absent or unchanged from a previous run. For all
phases, inspect the Ansible output and
`/var/log/omnia/discovery/discovery.log`.

### Discovery is blocked by an upgrade lock

Complete the Omnia upgrade before rerunning Discovery. The workflow does not
run normally while `/opt/omnia/.data/upgrade_in_progress.lock` exists.
