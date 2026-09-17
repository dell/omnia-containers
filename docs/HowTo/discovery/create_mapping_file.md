# Create a mapping file

## Overview

Orchestrator provisions nodes from `pxe_mapping_file.csv`. Each row identifies
a node, its physical group, functional role, hostname, and network interfaces.

The mapping is an Orchestrator-owned input. Create it in either of these ways:

- Run Discovery against OME, review its generated
  `bmc_pxe_mapping_file.csv`, and copy the reviewed file to Orchestrator.
- Collect the node information and create the Orchestrator input directly.
  This manual method does not run Discovery.

## Prerequisites

- Complete [OIM setup](../main/setup_oim.md).
- Collect the service tag, admin/PXE NIC MAC and IP, and any BMC and
  InfiniBand information required for each target node.
- Plan the functional-group and physical-group assignments.
- Ensure that an image exists for every functional group that Orchestrator
  will provision.

## Create the file manually

Create the file at the project-scoped Orchestrator input path:

```text
$ORCHESTRATOR_DATA_PATH/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv
```

Source `/etc/profile.d/omnia-env.sh` before resolving the path.
`ORCHESTRATOR_DATA_PATH` defaults to `$OMNIA_DATA_PATH/orchestrator`. To use
another absolute mapping-file path, set `pxe_mapping_file_path` in the
project-scoped `orchestrator_config.yml`.

Use the following header and retain all columns, including optional columns:

```text
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
```

| Column | Required | Description |
| --- | --- | --- |
| `FUNCTIONAL_GROUP_NAME` | Yes | Supported role name ending in `_x86_64` or `_aarch64`. Use either the Discovery-style role-and-architecture name or its version-qualified catalog form, as described below. |
| `GROUP_NAME` | Yes | Scalable Unit or logical group identifier. |
| `SERVICE_TAG` | No | Dell server service tag. When supplied, it must be alphanumeric and unique. Leave it empty when the inventory does not provide a service tag. |
| `PARENT_SERVICE_TAG` | No | Optional parent-node service tag. Orchestrator does not require this value or validate it against `GROUP_NAME`. |
| `HOSTNAME` | Yes | Unique node hostname without a domain suffix. |
| `ADMIN_MAC` | Yes | Unique MAC address of the PXE NIC on the admin network. |
| `ADMIN_IP` | Yes | Unique static IPv4 address in a configured admin subnet. |
| `BMC_MAC` | No | MAC address of the BMC/iDRAC interface. |
| `BMC_IP` | No | Static IPv4 address of the BMC/iDRAC interface. |
| `IB_NIC_NAME` | No | InfiniBand NIC FQDD, such as `InfiniBand.Slot.7-1`. |
| `IB_IP` | No | Static InfiniBand IPv4 address. Leave empty when no InfiniBand NIC is used. |

Discovery generates these role-and-architecture names:

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

The default RHEL 10.0 catalog uses the corresponding version-qualified names:

- `os_rhel_10_0_x86_64`
- `slurm_control_node_rhel_10_0_x86_64`
- `login_node_rhel_10_0_x86_64`
- `service_kube_control_plane_rhel_10_0_x86_64`
- `service_kube_node_rhel_10_0_x86_64`
- `os_rhel_10_0_aarch64`
- `slurm_node_rhel_10_0_aarch64`
- `login_compiler_node_rhel_10_0_aarch64`

The source templates also support `login_node_aarch64`,
`login_compiler_node_x86_64`, and `slurm_node_x86_64` roles. To select one of
those role-and-architecture combinations, use a catalog that defines it and
build the corresponding image before provisioning.

Orchestrator accepts either form for catalog-managed roles. It matches the
role and architecture to the active catalog; when the mapping includes an
operating-system/version segment, that segment must also match. Other catalog
variants can use different operating-system and version segments. Confirm that
Image Build Manager produced an image for every selected role and architecture.

## Sample x86_64 mapping for a custom catalog

This sample illustrates the source-supported x86_64 roles. The active catalog
must define every listed role-and-architecture combination; the shipped
default catalog does not include x86_64 Slurm compute or compiler-login
layers.

```csv title="File: <ORCHESTRATOR_DATA_PATH>/input/<OMNIA_PROJECT_NAME>/pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,ABCD12,,nid001,02:00:00:00:01:01,172.16.107.52,02:00:00:00:02:01,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
service_kube_node_x86_64,grp2,ABFL82,,nid002,02:00:00:00:01:02,172.16.107.56,02:00:00:00:02:02,172.17.107.56,,
slurm_node_x86_64,grp1,ABCD34,,nid003,02:00:00:00:01:03,172.16.107.43,02:00:00:00:02:03,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
login_compiler_node_x86_64,grp8,ABCD78,,nid004,02:00:00:00:01:04,172.16.107.41,02:00:00:00:02:04,172.17.107.41,InfiniBand.Slot.7-1,192.168.0.103
service_kube_control_plane_x86_64,grp3,ABFG79,,nid005,02:00:00:00:01:05,172.16.107.53,02:00:00:00:02:05,172.17.107.53,,
os_x86_64,grp6,ABEF56,,nid006,02:00:00:00:01:06,172.16.107.60,02:00:00:00:02:06,172.17.107.60,,
```

## Sample default mixed-architecture mapping

The following sample uses only role-and-architecture combinations supplied by
the default RHEL 10.0 catalog.

```csv title="File: <ORCHESTRATOR_DATA_PATH>/input/<OMNIA_PROJECT_NAME>/pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,ABCD12,,nid001,02:00:00:00:11:01,172.16.107.52,02:00:00:00:12:01,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
service_kube_node_x86_64,grp2,ABFL82,,nid002,02:00:00:00:11:02,172.16.107.56,02:00:00:00:12:02,172.17.107.56,,
slurm_node_aarch64,grp1,ABCD34,,nid003,02:00:00:00:11:03,172.16.107.43,02:00:00:00:12:03,172.17.107.43,InfiniBand.Slot.7-2,192.168.0.101
login_compiler_node_aarch64,grp8,ABCD78,,nid004,02:00:00:00:11:04,172.16.107.41,02:00:00:00:12:04,172.17.107.41,InfiniBand.PCIe.Slot.8-1,192.168.0.103
login_node_x86_64,grp9,ABFG78,,nid005,02:00:00:00:11:05,172.16.107.42,02:00:00:00:12:05,172.17.107.42,NIC.InfiniBand.1-1,192.168.0.104
service_kube_control_plane_x86_64,grp3,ABFG79,,nid006,02:00:00:00:11:06,172.16.107.53,02:00:00:00:12:06,172.17.107.53,,
os_aarch64,grp7,ABEF78,,nid007,02:00:00:00:11:07,172.16.107.61,02:00:00:00:12:07,172.17.107.61,,
```

## Mapping rules

- Retain the exact uppercase header names and column order shown above.
- Keep nonempty `SERVICE_TAG`, `HOSTNAME`, normalized `ADMIN_MAC`, `ADMIN_IP`,
  and nonempty `IB_IP` values unique. Colon- and hyphen-delimited forms of the
  same admin MAC are treated as duplicates.
- When `dns_enabled` is `true`, use the three-digit `nidxxx` format, such as
  `nid001`. When it is `false`, custom lowercase hostnames are supported.
- Do not include a domain suffix in `HOSTNAME`.
- Leave an optional value empty by using consecutive commas; do not remove its
  column. `IB_NIC_NAME` and `IB_IP` must either both be populated or both be
  empty for a row.
- Keep every `ADMIN_IP` within the primary or additional admin subnets in the
  Orchestrator `network_spec.yml`.
- Assign each node its intended `GROUP_NAME`. Populate `PARENT_SERVICE_TAG`
  only when parent metadata is required; otherwise leave it empty.
- Verify BMC addresses, service tags, optional parent metadata, and InfiniBand
  values manually. Validation does not prove that those values match the
  physical server.
- Configure each target to boot from the NIC identified by `ADMIN_MAC`.

Orchestrator requires the exact 11-column header and checks required cell
values, names, optional service-tag syntax, MAC and IPv4 syntax, duplicate
identities, supported logical-group combinations, Slurm/compiler architecture
compatibility, catalog-managed roles, paired IB fields, and admin-subnet
membership. Later provisioning steps use the physical inventory, so a file can
still fail when otherwise valid values do not describe the target hardware.

## Generate the file with OME

For OME-based generation, follow [Discover nodes using
OME](discover_nodes.md). Discovery assigns functional groups from supported
OME static groups, derives `GROUP_NAME` from the OME-reported iDRAC hostname,
generates `nid` hostnames with three digits, and selects admin and InfiniBand
interfaces from OME inventory.

Always review the generated mapping. In particular, confirm its functional
groups, group names, optional parent metadata, selected NICs, and derived IP
addresses before copying it to Orchestrator. Discovery-style role names may be
retained; version-qualified names may also be used when they match the active
catalog.

## Verification

Run the Orchestrator input-validation flow:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags validate
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator
    ansible-playbook playbooks/orchestrator.yml --tags validate
    ```

Resolve validation errors before provisioning. Then inspect the final file:

```bash title="Run on: OIM host"
source /etc/profile.d/omnia-env.sh
orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
cat "${orchestrator_path}/input/${OMNIA_PROJECT_NAME}/pxe_mapping_file.csv"
```

## Next steps

- [Provision nodes](../orchestrator/provision_nodes.md)
- [Orchestrator contract](../../Reference/domain_contracts/orchestrator_contract.md)
- [PXE mapping file reference](../../Reference/SampleFiles/pxe_mapping_file.md)
