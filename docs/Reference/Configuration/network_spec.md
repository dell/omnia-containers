
# network_spec.yml Reference


File path: `/opt/omnia/input/project_default/network_spec.yml`

This file defines all network segments used by the Omnia cluster: admin, ib, and additional networks. Each network is described as an entry in the
`Networks` list.

## Top-level structure


`network_spec.yml` contains a single top-level key, `Networks`, which is a
YAML list of network definitions.

```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
Networks:
  - admin_network:
      ...
  - ib_network:
      ...
  - additional_subnets:
      ...
```
## admin_network parameters
--8<-- "html/network_spec-admin_network.html"

## ib_network parameters (optional)
--8<-- "html/network_spec-ib_network.html"

## additional_subnets parameters (optional)
--8<-- "html/network_spec-additional_subnets.html"


## Usage example

```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
---
Networks:
  - admin_network:
      oim_nic_name: "eno1"
      subnet: "172.16.0.0"
      netmask_bits: "24"
      primary_oim_admin_ip: "172.16.107.254"
      primary_oim_bmc_ip: ""
      dynamic_range: "172.16.107.201-172.16.107.250"
      dns: []
      ntp_servers: []
      additional_subnets: []

  - ib_network:
      subnet: "192.168.0.0"
      netmask_bits: "24"
      dns: []

  - additional_subnets:
      - subnet: "10.40.1.0"
        netmask_bits: "24"
        router: "10.40.1.1"
        dynamic_range: "10.40.1.100-10.40.1.200"
      - subnet: "10.40.3.0"
        netmask_bits: "24"
        router: "10.40.3.1"
        dynamic_range: "10.40.3.100-10.40.3.200"
```


!!! note

    - In LOM topology, `admin_network` and `bmc_network` may share the
      same `oim_nic_name` with different `vlan_id` values.
    - The `dynamic_range` must not overlap with any static IPs assigned
      in the PXE mapping file.

!!! info

    - [Network Topologies](../SupportMatrix/network_topologies.md) -- How topologies
      affect NIC and VLAN assignments.
    - [Nics](../SupportMatrix/nics.md) -- Supported NIC models.
