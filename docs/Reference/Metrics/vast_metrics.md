
# VAST Metrics


This page catalogs the storage telemetry metrics collected from VAST Storage
appliances via the Prometheus-compatible exporter. These metrics are scraped
by vmagent and stored in VictoriaMetrics.

## Collection method


| Property | Value |
| --- | --- |
| **Collection tool** | VAST Prometheus Exporter |
| **Protocol** | Prometheus scrape over HTTPS |
| **Default port** | 443 |
| **Metrics path** | `/api/prometheusmetrics/all` |
| **Default interval** | 30 seconds (configurable via `scrape_interval` in `telemetry_config.yml`) |
| **Storage** | VictoriaMetrics time-series database |

## Storage performance metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `vast_read_throughput` | Bytes/s | Read throughput in bytes per second. |
| `vast_write_throughput` | Bytes/s | Write throughput in bytes per second. |
| `vast_read_iops` | IOPS | Read I/O operations per second per volume. |
| `vast_write_iops` | IOPS | Write I/O operations per second per volume. |
| `vast_read_latency` | Microseconds | Average read latency per operation. |
| `vast_write_latency` | Microseconds | Average write latency per operation. |

## Capacity metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `vast_capacity_total_bytes` | Bytes | Total storage capacity. |
| `vast_capacity_used_bytes` | Bytes | Storage capacity currently consumed. |
| `vast_capacity_avail_bytes` | Bytes | Storage capacity available for allocation. |
| `vast_capacity_thin_provisioning_ratio` | Ratio | Thin provisioning ratio (logical / physical). |

## Volume metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `vast_volume_state` | Enum | Volume operational state. |
| `vast_volume_read_iops` | IOPS | Per-volume read I/O operations per second. |
| `vast_volume_write_iops` | IOPS | Per-volume write I/O operations per second. |
| `vast_volume_read_bw` | Bytes/s | Per-volume read throughput. |
| `vast_volume_write_bw` | Bytes/s | Per-volume write throughput. |
| `vast_snapshot_count` | Count | Number of snapshots per volume. |

## Device metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `vast_device_health` | Enum | Device health status (healthy, degraded, failed). |
| `vast_device_read_iops` | IOPS | Per-device read I/O operations per second. |
| `vast_device_write_iops` | IOPS | Per-device write I/O operations per second. |
| `vast_device_errors` | Count | Total device error count. |

## Cluster health metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `vast_node_status` | Enum | Node health status (online, offline, degraded). |
| `vast_cluster_connectivity` | Enum | Cluster network connectivity status. |
| `vast_replication_status` | Enum | Data replication status. |

## Telemetry health metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `scrape_duration_seconds` | Seconds | Duration of the Prometheus scrape for VAST endpoint. |
| `up` | Enum | Whether the VAST scrape target is reachable (1=up, 0=down). |

## Metric labels


All VAST metrics include the following common labels:

| Label | Description |
| --- | --- |
| `instance` | VAST appliance endpoint (IP:port). |
| `volume` | Volume name (volume-level metrics only). |
| `device` | Device identifier (device-level metrics only). |
| `node` | VAST cluster node identifier. |

!!! info

    - [Telemetry Config](../Configuration/telemetry_config.md) -- VAST telemetry
      configuration parameters.
    - [VAST Data Documentation](https://support.vastdata.com/s/) -- VAST platform documentation.
    - [Idrac Metrics](idrac_metrics.md) -- Hardware-level metrics from iDRAC.
    - [Ldms Metrics](ldms_metrics.md) -- OS-level metrics from LDMS.
