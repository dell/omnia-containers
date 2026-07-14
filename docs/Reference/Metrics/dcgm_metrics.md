
# DCGM Metrics


This page catalogs the in-band GPU telemetry metrics collected by the Omnia telemetry
pipeline using DCGM (NVIDIA) and ROCm SMI (AMD). These metrics are collected
directly from the GPU driver on each compute node.

## Collection Method


| Property | NVIDIA | AMD |
| --- | --- | --- |
| **Collection tool** | DCGM (Data Center GPU Manager) | `rocm-smi` or ROCm SMI library |
| **Protocol** | DCGM exporter (Prometheus-compatible) | ROCm exporter (Prometheus-compatible) |
| **Default interval** | 10 seconds | 10 seconds |
| **Storage** | VictoriaMetrics | VictoriaMetrics |

!!! note

    For GPU metrics collected out-of-band via iDRAC Redfish, see [iDRAC Metrics — GPU metrics](idrac_metrics.md#gpu-metrics-via-idrac).

## NVIDIA GPU Metrics


### Utilization metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `DCGM_FI_DEV_GPU_UTIL` | Percent | GPU utilization (percentage of time one or more kernels were executing). |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | Percent | Memory utilization (percentage of time the memory controller was active). |
| `DCGM_FI_DEV_ENC_UTIL` | Percent | Hardware video encoder utilization. |
| `DCGM_FI_DEV_DEC_UTIL` | Percent | Hardware video decoder utilization. |

### Temperature metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `DCGM_FI_DEV_GPU_TEMP` | Celsius | Current GPU die temperature. |
| `DCGM_FI_DEV_MEMORY_TEMP` | Celsius | HBM (High Bandwidth Memory) temperature. Available on A100, H100, and similar data center GPUs. |
| `DCGM_FI_DEV_GPU_MAX_OP_TEMP` | Celsius | Maximum operating temperature (shutdown threshold). |
| `DCGM_FI_DEV_SLOWDOWN_TEMP` | Celsius | Temperature at which the GPU begins throttling clocks. |

### Memory metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `DCGM_FI_DEV_FB_TOTAL` | MiB | Total GPU framebuffer memory (e.g., 40960 MiB for A100 40 GB). |
| `DCGM_FI_DEV_FB_USED` | MiB | GPU framebuffer memory currently allocated by processes. |
| `DCGM_FI_DEV_FB_FREE` | MiB | GPU framebuffer memory available for allocation. |
| `DCGM_FI_DEV_BAR1_TOTAL` | MiB | Total BAR1 memory (used for CPU-GPU memory mapping). |
| `DCGM_FI_DEV_BAR1_USED` | MiB | BAR1 memory currently in use. |

### Power metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `DCGM_FI_DEV_POWER_USAGE` | Watts | Current GPU power consumption. |
| `DCGM_FI_DEV_ENFORCED_POWER_LIMIT` | Watts | Current enforced power limit. |
| `DCGM_FI_DEV_DEFAULT_POWER_LIMIT` | Watts | Factory default power limit. |
| `DCGM_FI_DEV_POWER_MGMT_LIMIT_MAX` | Watts | Maximum power limit configurable for this GPU. |
| `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` | Joules | Cumulative energy consumed since last driver reload. |
| `DCGM_FI_DEV_POWER_VIOLATION` | Microseconds | Duration of power limit throttling. |

### Clock and performance metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `DCGM_FI_DEV_SM_CLOCK` | MHz | Current SM (Streaming Multiprocessor) clock frequency. |
| `DCGM_FI_DEV_MEM_CLOCK` | MHz | Current memory clock frequency. |
| `DCGM_FI_DEV_PSTATE` | Enum | GPU performance state (P0 = maximum performance, P12 = idle). |
| `DCGM_FI_DEV_CLOCK_THROTTLE_REASONS` | Bitmask | Active clock throttle reasons (thermal, power, API-initiated). |

### Error metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `DCGM_FI_DEV_ECC_SBE_VOL_TOTAL` | Count | Corrected (single-bit) ECC errors since last driver reload. |
| `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL` | Count | Uncorrected (double-bit) ECC errors since last driver reload. |
| `DCGM_FI_DEV_RETIRED_SBE` | Count | GPU memory pages retired due to single-bit ECC errors. |
| `DCGM_FI_DEV_RETIRED_DBE` | Count | GPU memory pages retired due to double-bit ECC errors. |
| `DCGM_FI_DEV_XID_ERRORS` | Count | NVIDIA Xid error events (logged by the GPU driver). |

### PCIe metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `DCGM_FI_DEV_PCIE_TX_THROUGHPUT` | KB/s | PCIe transmit throughput. |
| `DCGM_FI_DEV_PCIE_RX_THROUGHPUT` | KB/s | PCIe receive throughput. |
| `DCGM_FI_DEV_PCIE_REPLAY_COUNTER` | Count | PCIe replay errors (cumulative). |

## AMD GPU Metrics


### Utilization metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `amd_gpu_utilization` | Percent | GPU compute unit utilization over the sampling interval. |
| `amd_gpu_memory_utilization` | Percent | GPU memory controller utilization. |

### Temperature metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `amd_gpu_temperature_edge` | Celsius | GPU edge temperature. |
| `amd_gpu_temperature_junction` | Celsius | GPU junction (hotspot) temperature. |
| `amd_gpu_temperature_memory` | Celsius | HBM temperature. |

### Memory metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `amd_gpu_memory_total` | MiB | Total GPU memory. |
| `amd_gpu_memory_used` | MiB | GPU memory currently allocated. |
| `amd_gpu_memory_free` | MiB | Available GPU memory. |

### Power metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `amd_gpu_power_draw` | Watts | Current GPU power consumption. |
| `amd_gpu_power_cap` | Watts | Current power cap. |
| `amd_gpu_power_cap_default` | Watts | Factory default power cap. |

### Clock metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `amd_gpu_clock_sclk` | MHz | Current GPU engine (shader) clock frequency. |
| `amd_gpu_clock_mclk` | MHz | Current memory clock frequency. |

## Metric Labels


All DCGM metrics include the following common labels:

| Label | Description |
| --- | --- |
| `host` | Hostname of the compute node. |
| `gpu` | GPU index on the node (0, 1, 2, ...). |
| `UUID` | Unique identifier for the GPU. |
| `modelName` | GPU model name (e.g., `NVIDIA A100-SXM4-80GB`). |
| `pci_bus_id` | PCI bus address of the GPU. |

!!! info

    - [Telemetry Config](../Configuration/telemetry_config.md) -- Telemetry pipeline
      configuration.
    - [Idrac Metrics](idrac_metrics.md) -- Server-level hardware metrics (includes
      out-of-band GPU metrics via iDRAC Redfish).
    - [Ldms Metrics](ldms_metrics.md) -- OS-level metrics from LDMS.
