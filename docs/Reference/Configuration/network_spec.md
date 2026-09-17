
# network_spec.yml

This file defines the admin network, the optional InfiniBand network, and any
additional DHCP subnets. Orchestrator and Discovery stage independent copies
of this file in their respective project input directories.

## Location

```text
$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/network_spec.yml
$OMNIA_DATA_PATH/discovery/input/$OMNIA_PROJECT_NAME/network_spec.yml
```

The Orchestrator data root is `$OMNIA_DATA_PATH/orchestrator`. Discovery
derives its input directory from
`$OMNIA_DATA_PATH/discovery`. Configure the Discovery copy for node discovery
and the Orchestrator copy for provisioning.

Discovery currently reads only `admin_network.subnet` and
`ib_network.subnet`. It uses their first two octets with the last two octets of
each server's BMC address to derive `ADMIN_IP` and `IB_IP`. The Discovery
`validate` tag does not validate this file. Orchestrator consumes and validates
the remaining network fields from its own copy.

## Top-level structure

`network_spec.yml` contains a single top-level key, `Networks`, which is a
YAML list of network definitions.

Define exactly one `admin_network` entry and no more than one `ib_network`
entry. Although the schema represents these definitions as list items, the
runtime combines them into one network mapping; a later duplicate network type
would replace the earlier definition.

```yaml title="File: $OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/network_spec.yml"
Networks:
  - admin_network:
      oim_nic_name: "eno1"
      subnet: "172.16.107.0"
      netmask_bits: "24"
      primary_oim_admin_ip: "172.16.107.254"
      primary_oim_bmc_ip: ""
      router: "172.16.107.254"
      dynamic_range: "172.16.107.201-172.16.107.250"
      dns: []
      ntp_servers: []
      additional_subnets: []
```

Omit the `ib_network` list item when InfiniBand is not used. When it is present,
both `subnet` and `netmask_bits` must contain valid values; an empty
`ib_network` object does not satisfy the schema.

Every subnet must be its canonical IPv4 network address. Each router and DHCP
range must belong to its declared admin subnet, and ranges must be ordered.
Primary and additional admin subnets must be pairwise non-overlapping and must
not overlap the optional InfiniBand subnet. Configured DHCP ranges must also be
pairwise non-overlapping. The OIM admin address must be inside its primary
admin subnet and outside its DHCP range. A non-empty OIM BMC address must
differ from every OIM admin address and remain outside every configured DHCP
range.

## Admin Network Configuration Parameters
--8<-- "html/network_spec-admin_network.html"

## Infiniband Network Configuration Parameters (optional)
--8<-- "html/network_spec-ib_network.html"

## Additional Subnets Configuration Parameters (optional)
--8<-- "html/network_spec-additional_subnets.html"


## Usage example

```yaml title="File: $OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/network_spec.yml"
---
Networks:
  - admin_network:
      oim_nic_name: "eno1"
      subnet: "172.16.107.0"
      netmask_bits: "24"
      primary_oim_admin_ip: "172.16.107.254"
      primary_oim_bmc_ip: ""
      router: "172.16.107.254"
      dynamic_range: "172.16.107.201-172.16.107.250"
      dns: []
      ntp_servers: []
      additional_subnets:
        - subnet: "10.40.1.0"
          netmask_bits: "24"
          router: "10.40.1.1"
          dynamic_range: "10.40.1.100-10.40.1.200"
        - subnet: "10.40.3.0"
          netmask_bits: "24"
          router: "10.40.3.1"
          dynamic_range: "10.40.3.100-10.40.3.200"

  - ib_network:
      subnet: "192.168.0.0"
      netmask_bits: "24"
      dns: []
```


!!! note

    - The `router` field is required and specifies the gateway IP address advertised to nodes through DHCP option 3 as their default gateway.
    - In connected deployments, set `router` to the external rack gateway (such as a SONiC switch) which provides connectivity beyond the rack network.
    - In air-gapped deployments, set `router` to the OIM's IP address if the OIM is acting as the rack gateway. If a dedicated router or gateway is available, specify its IP address instead.
    - Sample value: `172.16.107.254`. The schema requires `router`; the runtime
      does not supply this value when it is omitted.
    - Every primary and additional `dynamic_range` must be contained within its
      subnet, must not overlap another configured DHCP range, and must not
      contain the OIM admin or BMC address. Orchestrator does not currently
      cross-check these DHCP pools against static `ADMIN_IP` values in the PXE
      mapping file, so reserve those addresses outside the pools.
    - When `ib_network` is configured, its subnet must not overlap an admin
      subnet. Its `netmask_bits` value is applied independently to node
      InfiniBand interfaces and may differ from the admin-network prefix.

!!! info

    - [Network Topologies](../SupportMatrix/network_topologies.md) -- How topologies
      affect NIC and VLAN assignments.
    - [Nics](../SupportMatrix/nics.md) -- Supported NIC models.


