
# Supported Network Interfaces

<style>
/* Widen the second column (Model / ConnectX-6) so text does not wrap */
.md-typeset table:not([class]) th:nth-child(2),
.md-typeset table:not([class]) td:nth-child(2) {
  white-space: nowrap;
}
</style>


Omnia v2.1 supports the following network interface cards (NICs) for
admin, BMC, compute, and high-speed data networks.

## NIC support matrix


| Manufacturer | Model | Speed | Ports | Notes |
| --- | --- | --- | --- | --- |
| NVIDIA (Mellanox) | ConnectX-6 | Up to 200 Gb/s | 1--2 | HDR InfiniBand and Ethernet modes. Supports SR-IOV, RDMA (RoCEv2 and InfiniBand), and GPUDirect. Recommended for high-speed compute and storage networks. |
| Intel | E810 | Up to 100 Gb/s | 1--4 | Ethernet only. Supports SR-IOV, RDMA (RoCEv2), and ADQ (Application Device Queues). Suitable for admin, compute, and storage networks. |

## NIC role mapping


| Network | ConnectX-6 | Intel E810 | Configuration Notes |
| --- | --- | --- | --- |
| Admin network | Yes | Yes | Specified as `oim_nic_name` in `network_spec.yml`. Typically a 1 GbE or 10 GbE port. |
| BMC network | -- | -- | BMC uses the iDRAC dedicated NIC (built-in); not a PCIe add-in card. |
| Compute / data network | Yes | Yes | High-speed fabric for MPI, NCCL, and storage traffic. |
| Public / external network | Yes | Yes | Internet-facing or campus-facing network. Optional depending on topology. |

## Firmware requirements


| NIC | Minimum Firmware | How to Update |
| --- | --- | --- |
| ConnectX-6 | Consult NVIDIA firmware release notes | Use `mlxfwmanager` from the Mellanox OFED package or Dell Update Package (DUP). |
| Intel E810 | Consult Intel Ethernet release notes | Use `nvmupdate64e` from the Intel NVM Update Tool or Dell Update Package (DUP). |

!!! warning

    Running mismatched firmware across NICs in the same cluster can cause
    intermittent link failures. Update all NICs to the same firmware version
    before running `discovery.yml`.

## InfiniBand considerations (ConnectX-6)


When using ConnectX-6 in InfiniBand mode:

- An InfiniBand subnet manager (e.g., OpenSM) must be running on at least one
  node in the fabric.
- Omnia does not deploy or configure the InfiniBand subnet manager
  automatically; this must be set up independently.
- RDMA and GPUDirect require the NVIDIA OFED driver stack, which can be
  included in the provisioning image via `software_config.json`.

!!! note

    For Ethernet-mode deployments, ConnectX-6 supports RoCEv2 (RDMA over
    Converged Ethernet). Priority Flow Control (PFC) and ECN must be configured
    on the switch ports to avoid packet loss under RDMA workloads.

## LOM (LAN on Motherboard) support


Most Dell PowerEdge servers include onboard 1 GbE or 10 GbE LOM ports. These
are supported for admin and BMC networks but are **not** listed as separately
qualified NICs. LOM ports are referenced by their system interface name
(e.g., `eno1`, `eno2`) in `network_spec.yml`.

!!! info

    - [Network Spec](../Configuration/network_spec.md) -- Network specification
      parameters including NIC names.
    - [Switches](switches.md) -- Supported switches for connecting NIC ports.
    - [Network Topologies](network_topologies.md) -- How NICs map to network topology models.
