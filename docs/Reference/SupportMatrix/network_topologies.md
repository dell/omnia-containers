
# Network Topologies


Omnia v2.1 supports three network topology models. The choice of topology
determines how the OIM, cluster nodes, and switches are physically and
logically connected.

## Topology comparison


| Topology | OIM NIC Layout | Node NIC Layout | Best For |
| --- | --- | --- | --- |
| **Dedicated** | Separate NICs for admin and BMC networks (minimum 2 NICs, optionally 3+ for compute/public). | Separate NICs for admin and BMC; additional NICs for compute and public. | Production environments requiring full network isolation between management and data traffic. |
| **LOM** | LAN-on-Motherboard (LOM) ports carry both admin and BMC traffic on a single physical NIC using VLAN tagging. | LOM ports with VLAN-tagged admin and BMC traffic. | Environments with limited NIC availability; shares onboard ports for multiple functions. |
| **Hybrid** | LOM ports for admin/BMC (shared, VLAN-tagged) plus dedicated add-in NICs for compute and public networks. | LOM ports for admin/BMC; add-in NICs for compute/public. | Balanced approach: saves NIC slots for high-speed data while using onboard ports for management. |

## Detailed topology specifications


### Dedicated topology


| Network | OIM Interface | Node Interface | Description |
| --- | --- | --- | --- |
| Admin | Dedicated NIC (e.g., `eno1`) | Dedicated NIC (e.g., `eno1`) | Provisioning, Ansible, and SSH management traffic. Untagged. |
| BMC | Dedicated NIC (e.g., `eno2`) | iDRAC dedicated port | Out-of-band management (iDRAC). Separate physical network. |
| Compute | Optional add-in NIC | Add-in NIC (e.g., ConnectX-6) | High-speed data plane for MPI, NCCL, and storage I/O. |
| Public | Optional add-in NIC | Optional add-in NIC | Internet-facing or campus network. Not required for all deployments. |

### LOM topology


| Network | OIM Interface | Node Interface | Description |
| --- | --- | --- | --- |
| Admin | LOM port (e.g., `eno1`, VLAN tagged) | LOM port (VLAN tagged) | Shares the physical port with BMC using 802.1Q VLAN tagging. |
| BMC | LOM port (e.g., `eno1`, VLAN tagged) | iDRAC shared LOM | iDRAC configured in shared LOM mode; tagged on a separate VLAN. |
| Compute | Not applicable | Add-in NIC (if available) | Optional. If present, used for high-speed traffic. |
| Public | Optional | Optional | Uplink to external network if needed. |

!!! note

    In LOM topology, the switch ports must be configured as VLAN trunk ports
    carrying both admin and BMC VLANs. Configure the iDRAC to use **Shared
    LOM** mode in the BIOS/iDRAC settings.

### Hybrid topology


| Network | OIM Interface | Node Interface | Description |
| --- | --- | --- | --- |
| Admin | LOM port (VLAN tagged) | LOM port (VLAN tagged) | Shares LOM with BMC, as in the LOM topology. |
| BMC | LOM port (VLAN tagged) | iDRAC shared LOM | Same as LOM topology. |
| Compute | Dedicated add-in NIC | Dedicated add-in NIC (e.g., ConnectX-6) | High-speed dedicated fabric. Physically separate from management. |
| Public | Dedicated add-in NIC | Optional add-in NIC | Dedicated port for external connectivity. |

## Topology and `network_spec.yml` mapping


| `network_spec.yml` Field | Dedicated Topology Value | LOM / Hybrid Topology Value |
| --- | --- | --- |
| `admin_network.oim_nic_name` | Physical NIC name (e.g., `eno1`) | VLAN sub-interface or LOM port (e.g., `eno1`) |
| `admin_network.netmask_bits` | Subnet mask for admin VLAN (e.g., `20`) | Subnet mask for admin VLAN (e.g., `20`) |
| `bmc_network` | Separate physical subnet | VLAN-tagged subnet on the same LOM |
| `compute_network` | Dedicated add-in NIC | Dedicated add-in NIC (Hybrid) or absent (LOM) |

!!! info

    - [Network Spec](../Configuration/network_spec.md) -- Full `network_spec.yml`
      parameter reference.
    - [Switches](switches.md) -- Switch models and VLAN configuration.
    - [Nics](nics.md) -- Supported NIC models for each topology.
