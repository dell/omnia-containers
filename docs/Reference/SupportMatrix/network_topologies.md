
# Network Topologies

Omnia v2.2 supports three network topology models. The choice of topology determines how the OIM, cluster nodes, and switches are physically and logically connected.

## Topology comparison

| Topology | OIM NIC Layout | Node NIC Layout |
| --- | --- | --- |
| **Dedicated** | Separate NICs for admin and BMC networks (minimum 2 NICs, optionally 3+ for compute/public). | Separate NICs for admin and BMC; additional NICs for compute and public. |
| **LOM** | LAN-on-Motherboard (LOM) ports carry both admin and BMC traffic on a single physical NIC using VLAN tagging. | LOM ports with VLAN-tagged admin and BMC traffic. |
| **Hybrid** | LOM ports for admin/BMC (shared, VLAN-tagged) plus dedicated add-in NICs for compute and public networks. | LOM ports for admin/BMC; add-in NICs for compute/public. |

!!! info

    - [Network Spec](../Configuration/network_spec.md) -- Full `network_spec.yml`
      parameter reference.
    - [Switches](switches.md) -- Switch models and VLAN configuration.
    - [Nics](nics.md) -- Supported NIC models for each topology.
