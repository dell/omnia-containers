# Servers

## PowerEdge NVIDIA Grace CPUs servers

| Model | Generation | Form Factor | Notes | Status |
| --- | --- | --- | --- | --- |
| XE8712 with GB200 | 17G | 1U rack | AI rack solution with NVIDIA GB200 NVL4 Superchip. | Certified |

!!! note

    For aarch64 architecture platforms, limited validation has been performed on early access systems.

## PowerEdge AMD servers

| Model | Generation | Form Factor | Notes | Status |
| --- | --- | --- | --- | --- |
| R6625 | 16G | 1U rack | Dual-socket; high core density for parallel workloads. | Supported |
| R7625 | 16G | 2U rack | Dual-socket; balanced compute and storage. | Certified |
| R6725 | 17G | 1U rack | Dual-socket; up to 192 cores per processor. | Certified |
| R7725 | 17G | 2U rack | Dual-socket; GPU-ready with PCIe Gen5 expansion. | Certified |
| R6715 | 17G | 1U rack | Single-socket; cost-effective compute. | Certified |
| R7715 | 17G | 2U rack | Single-socket; flexible storage and accelerator options. | Certified |
| R7725xd | 17G | 2U rack | Dual-socket; NVMe-optimized with U.2 and E3.S drive support. | Certified |

## PowerEdge Intel servers

| Model | Generation | Form Factor | Notes | Status |
| --- | --- | --- | --- | --- |
| C6620 | 16G | 2U multi-node (4 sleds) | High-density; 4 independent dual-socket sleds per 2U chassis. | Certified |
| R660 | 16G | 1U rack | Dual-socket; suitable for OIM, Slurm control, or login nodes. | Certified |
| R760 | 16G | 2U rack | Dual-socket; general-purpose compute and storage. | Certified |
| R760xa | 16G | 2U rack | GPU-accelerated variant; supports up to 4 double-width GPUs. | Certified |
| R760xd2 | 16G | 2U rack | Dual-socket; storage-optimized for file/object storage and content delivery. | Certified |
| R260 | 16G | 1U rack (short-depth) | Single-socket; short-depth for near-edge and SMB. | Supported |
| R360 | 16G | 1U rack | Single-socket; entry-level for versatile workloads. | Certified |

!!! info

    - [Operating Systems](operating_systems.md) -- Supported operating system versions per server.
    - [NICs](nics.md) -- Supported network interface cards.
    - [Switches](switches.md) -- Supported switches.
    - [Disk Space](../ClusterRequirements/disk_space.md) -- Disk space requirements.
