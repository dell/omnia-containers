
# Supported Servers


Omnia v2.1 supports the following Dell PowerEdge server models as cluster
nodes (OIM, Slurm, and Kubernetes). Servers are grouped by CPU architecture.

## Intel-based servers


| Model | CPU Generation | Form Factor | Notes |
| --- | --- | --- | --- |
| PowerEdge R660 | Intel 4th/5th Gen Xeon Scalable | 1U rack | Dual-socket; suitable for OIM, Slurm control, or login nodes. |
| PowerEdge R760 | Intel 4th/5th Gen Xeon Scalable | 2U rack | Dual-socket; general-purpose compute and storage. |
| PowerEdge R760xa | Intel 4th/5th Gen Xeon Scalable | 2U rack | GPU-accelerated variant; supports up to 4 double-width GPUs. |
| PowerEdge R770 | Intel 5th Gen Xeon Scalable | 2U rack | Dual-socket; next-generation general-purpose compute. |
| PowerEdge C6620 | Intel 4th/5th Gen Xeon Scalable | 2U multi-node (4 sleds) | High-density; 4 independent dual-socket sleds per 2U chassis. |
| PowerEdge XE9680 | Intel 4th/5th Gen Xeon Scalable | 6U rack | AI/ML optimized; supports up to 8 NVIDIA GPUs (SXM5 or PCIe). |
| PowerEdge XR7620 | Intel 4th/5th Gen Xeon Scalable | 1U short-depth | Edge-optimized; ruggedized, suitable for edge HPC deployments. |
| PowerEdge XR8620t | Intel 4th/5th Gen Xeon Scalable | 2U short-depth | Edge-optimized; supports GPU accelerators in edge environments. |
| PowerEdge XR8000r | Intel 4th/5th Gen Xeon Scalable | Modular | Modular edge platform with configurable sled options. |

## AMD-based servers


| Model | CPU Generation | Form Factor | Notes |
| --- | --- | --- | --- |
| PowerEdge R6615 | AMD EPYC 4th Gen (Genoa) | 1U rack | Single-socket; cost-effective for OIM or lightweight compute. |
| PowerEdge R7615 | AMD EPYC 4th Gen (Genoa) | 2U rack | Single-socket; extended storage capacity. |
| PowerEdge R6625 | AMD EPYC 4th Gen (Genoa) | 1U rack | Dual-socket; high core density for parallel workloads. |
| PowerEdge R7625 | AMD EPYC 4th Gen (Genoa) | 2U rack | Dual-socket; balanced compute and storage. |
| PowerEdge R7725 | AMD EPYC 4th Gen (Genoa) | 2U rack | Dual-socket; GPU-ready with PCIe Gen5 expansion. |
| PowerEdge C6625 | AMD EPYC 4th Gen (Genoa) | 2U multi-node | High-density; multiple independent compute sleds per chassis. |

## ARM-based servers (Grace CPU)


| Model | CPU | Form Factor | Notes |
| --- | --- | --- | --- |
| PowerEdge R770-G | NVIDIA Grace CPU (ARM, AArch64) | 2U rack | ARM architecture; requires `build_image_aarch64.yml` for image creation. Uses separate OS image from x86_64 nodes. |

!!! note

    ARM nodes require provisioning with the `build_image_aarch64.yml`
    playbook. The x86_64 image built by `build_image_x86_64.yml` is **not**
    compatible with ARM-based servers.

## Server role compatibility


| Server Model | OIM | Slurm Control | Slurm Node | Login Node | K8s Control | K8s Node |
| --- | --- | --- | --- | --- | --- | --- |
| R660 / R6615 / R6625 | Yes | Yes | Yes | Yes | Yes | Yes |
| R760 / R7615 / R7625 | Yes | Yes | Yes | Yes | Yes | Yes |
| R760xa / R7725 | -- | -- | Yes | -- | -- | Yes |
| R770 | Yes | Yes | Yes | Yes | Yes | Yes |
| C6620 / C6625 | -- | Yes | Yes | -- | Yes | Yes |
| XE9680 | -- | -- | Yes | -- | -- | Yes |
| XR7620 / XR8620t / XR8000r | -- | Yes | Yes | -- | Yes | Yes |
| R770-G (ARM) | -- | -- | Yes | -- | -- | Yes |

!!! info

    - [Operating Systems](operating_systems.md) -- Supported operating system versions per server.
    - [Nics](nics.md) -- Supported network interface cards.
    - [Minimum Nodes](../ClusterRequirements/minimum_nodes.md) -- Minimum node counts
      per deployment scenario.
