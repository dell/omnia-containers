# PXE mapping file

The PXE mapping file is the node-inventory contract consumed by Orchestrator.
It assigns each physical server to a group and functional role and supplies
the hostname and network identities used during provisioning.

The default project-scoped location is:

```text
$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv
```

The Orchestrator data root is `$OMNIA_DATA_PATH/orchestrator`.

Set `pxe_mapping_file_path` in `orchestrator_config.yml` to select another
absolute path.

## Column reference

Retain every column in this header, including optional columns:

```text
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
```

| Column | Required | Description |
| --- | --- | --- |
| `FUNCTIONAL_GROUP_NAME` | Yes | Supported role name ending in `_x86_64` or `_aarch64`. Discovery-style and matching version-qualified catalog names are accepted. |
| `GROUP_NAME` | Yes | Scalable Unit or logical group identifier. |
| `SERVICE_TAG` | No | Dell server service tag. A nonempty value must be alphanumeric and unique. |
| `PARENT_SERVICE_TAG` | No | Optional parent-node service tag. Orchestrator does not require this value or validate it against `GROUP_NAME`. |
| `HOSTNAME` | Yes | Unique lowercase hostname without a domain suffix. |
| `ADMIN_MAC` | Yes | Unique MAC address of the admin/PXE NIC. |
| `ADMIN_IP` | Yes | Unique IPv4 address in a configured admin subnet. |
| `BMC_MAC` | No | BMC/iDRAC MAC address. |
| `BMC_IP` | No | BMC/iDRAC IPv4 address. |
| `IB_NIC_NAME` | No | InfiniBand NIC FQDD, such as `InfiniBand.Slot.7-1` or `NIC.InfiniBand.1-3`. |
| `IB_IP` | No | InfiniBand IPv4 address. |

Discovery-style names such as `service_kube_node_x86_64` and
`slurm_node_aarch64` are valid. With the default RHEL 10.0 catalog, the
corresponding case-sensitive version-qualified names include:

- `os_rhel_10_0_x86_64`
- `slurm_control_node_rhel_10_0_x86_64`
- `login_node_rhel_10_0_x86_64`
- `service_kube_control_plane_rhel_10_0_x86_64`
- `service_kube_node_rhel_10_0_x86_64`
- `os_rhel_10_0_aarch64`
- `slurm_node_rhel_10_0_aarch64`
- `login_compiler_node_rhel_10_0_aarch64`

Other catalog variants can define different functional layers. Orchestrator
matches catalog-managed names by role and architecture; an explicit OS/version
segment must match the selected catalog. During validation and provisioning,
Orchestrator promotes the first name beginning with
`service_kube_control_plane_` to an internal
`service_kube_control_plane_first_...` group. Do not put that internal name in
the source mapping. When using a Discovery-generated mapping, review each role
and ensure that the selected catalog supplies its architecture.

## Sample file

The sample below uses the functional layers in the default RHEL 10.0 catalog
installed by Main.

```csv title="pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_rhel_10_0_x86_64,grp0,ABCD12,,nid001,02:00:00:00:01:01,172.16.107.52,02:00:00:00:02:01,172.17.107.52,InfiniBand.Slot.7-1,192.168.0.100
service_kube_node_rhel_10_0_x86_64,grp2,ABFL82,,nid002,02:00:00:00:01:02,172.16.107.56,02:00:00:00:02:02,172.17.107.56,,
slurm_node_rhel_10_0_aarch64,grp1,ABCD34,,nid003,02:00:00:00:01:03,172.16.107.43,02:00:00:00:02:03,172.17.107.43,InfiniBand.Slot.7-2,192.168.0.101
login_compiler_node_rhel_10_0_aarch64,grp8,ABCD78,,nid004,02:00:00:00:01:04,172.16.107.41,02:00:00:00:02:04,172.17.107.41,NIC.InfiniBand.1-1,192.168.0.103
service_kube_control_plane_rhel_10_0_x86_64,grp3,ABFG79,,nid005,02:00:00:00:01:05,172.16.107.53,02:00:00:00:02:05,172.17.107.53,,
os_rhel_10_0_aarch64,grp7,ABEF78,,nid006,02:00:00:00:01:06,172.16.107.61,02:00:00:00:02:06,172.17.107.61,,
```

## Validation rules

The current Orchestrator input validator checks:

- Exact presence, spelling, case, and order of all 11 canonical headers.
- Required values for `FUNCTIONAL_GROUP_NAME`, `GROUP_NAME`, `HOSTNAME`,
  `ADMIN_MAC`, and `ADMIN_IP`; `SERVICE_TAG` may be empty.
- Uniqueness of nonempty `SERVICE_TAG`, `HOSTNAME`, normalized `ADMIN_MAC`,
  `ADMIN_IP`, and nonempty `IB_IP` values.
- MAC and IPv4 syntax for the applicable required and optional fields.
- Paired `IB_NIC_NAME` and `IB_IP` values.
- Functional-group syntax, supported logical-group combinations,
  Slurm/compiler architecture compatibility, and catalog-managed role
  compatibility when the catalog is available.
- Membership of `ADMIN_IP` values in the primary or additional admin subnets
  from the Orchestrator `network_spec.yml`.

Provisioning also consumes the remaining values. Verify service tags, MAC
addresses, BMC addresses, functional groups, optional parent metadata, and
InfiniBand information against the physical inventory even when initial
validation passes.

When `dns_enabled` is `true`, use the `nidxxx` hostname format, such as
`nid001`. When it is `false`, custom lowercase hostnames are supported. In
both cases, do not include a domain suffix.

## Related documentation

- [Create a mapping file](../../HowTo/discovery/create_mapping_file.md)
- [Discover nodes using OME](../../HowTo/discovery/discover_nodes.md)
- [Orchestrator contract](../domain_contracts/orchestrator_contract.md)
- [Hostname requirements](../Appendices/hostname_requirements.md)
