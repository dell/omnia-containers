
# PowerScale Metrics


This page catalogs the metrics collected by the Omnia PowerScale telemetry
pipeline via the CSM Observability framework. These metrics are stored
in VictoriaMetrics for visualization in Grafana.

## Collection method


| Property | Value |
| --- | --- |
| **Collection tool** | CSM Metrics for PowerScale (Karavi Observability) |
| **Protocol** | OneFS REST API → OpenTelemetry Collector → Prometheus scrape |
| **Default interval** | 30 seconds (configurable via `scrape_interval` in CSM Observability values.yaml) |
| **Storage** | VictoriaMetrics time-series database |

## Performance metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `powerscale_cluster_protocol_read_iops` | IOPS | Read I/O operations per second at the protocol level (NFS, SMB, S3). |
| `powerscale_cluster_protocol_write_iops` | IOPS | Write I/O operations per second at the protocol level. |
| `powerscale_cluster_protocol_read_bw` | Bytes/s | Read throughput (bytes per second) at the protocol level. |
| `powerscale_cluster_protocol_write_bw` | Bytes/s | Write throughput (bytes per second) at the protocol level. |
| `powerscale_cluster_protocol_read_latency` | Microseconds | Average read latency per protocol operation. |
| `powerscale_cluster_protocol_write_latency` | Microseconds | Average write latency per protocol operation. |

## Capacity metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `powerscale_cluster_capacity_total_bytes` | Bytes | Total raw storage capacity of the PowerScale cluster. |
| `powerscale_cluster_capacity_used_bytes` | Bytes | Storage capacity currently consumed. |
| `powerscale_cluster_capacity_avail_bytes` | Bytes | Storage capacity available for allocation. |
| `powerscale_node_capacity_total_bytes` | Bytes | Total capacity per node. |
| `powerscale_node_capacity_used_bytes` | Bytes | Capacity consumed per node. |

## Health metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `powerscale_node_status` | Enum | Node health status (online, offline, degraded). |
| `powerscale_disk_health` | Enum | Physical disk health status per node. |
| `powerscale_cluster_rebalance_status` | Enum | Cluster data rebalance/restripe status. |
| `powerscale_protection_group_status` | Enum | Protection group health. |

## CSI health monitor metrics


When the CSI PowerScale health monitor is enabled, the following additional metrics are collected:

**PV Metrics:**

| Metric | Unit | Description |
| --- | --- | --- |
| `powerscale_volume_status` | Enum | PV phase (1=Bound, 0=Other). Labels: `pv_name`, `phase`. |
| `powerscale_volume_count` | Count | Total PowerScale PVs by phase. |
| `powerscale_volume_capacity_bytes` | Bytes | PV capacity in bytes. |
| `powerscale_volume_info` | Info | PV metadata. Labels: `pv_name`, `phase`, `storage_class`, `reclaim_policy`, `access_modes`, `volume_handle`, `pvc_name`, `pvc_namespace`. |
| `powerscale_volume_age_seconds` | Seconds | Seconds since PV creation. |

**PVC Metrics:**

| Metric | Unit | Description |
| --- | --- | --- |
| `powerscale_pvc_status_phase` | Enum | PVC phase (1=Bound, 0=Other). Labels: `pvc_name`, `pvc_namespace`, `phase`. |
| `powerscale_pvc_requested_bytes` | Bytes | PVC requested storage in bytes. |
| `powerscale_pvc_count` | Count | Total PowerScale PVCs by phase. |

**Health Event Metrics:**

| Metric | Unit | Description |
| --- | --- | --- |
| `powerscale_volume_health_abnormal` | Enum | Volume condition abnormal (1=abnormal, 0=healthy). |
| `powerscale_volume_abnormal_events_total` | Count | Total VolumeConditionAbnormal events. |
| `powerscale_node_failure_events_total` | Count | Total node failure events. |
| `powerscale_node_ready` | Enum | Node Ready condition (1=True, 0=False). |

**Storage Class Metrics:**

| Metric | Unit | Description |
| --- | --- | --- |
| `powerscale_storageclass_info` | Info | StorageClass metadata. Labels: `storageclass`, `provisioner`, `reclaim_policy`, `volume_binding_mode`, `allow_volume_expansion`. |
| `powerscale_total_capacity_bytes` | Bytes | Total capacity of all PowerScale PVs in bytes. |

## Metric labels


All PowerScale metrics include the following common labels:

| Label | Description |
| --- | --- |
| `cluster` | PowerScale cluster name. |
| `node` | PowerScale node identifier. |
| `protocol` | Protocol type (NFS, SMB, S3) for protocol-level metrics. |

!!! info

    - [Telemetry Config](../Configuration/telemetry_config.md) -- PowerScale telemetry
      configuration parameters.
    - [Supported PowerScale Metrics](https://dell.github.io/csm-docs/docs/concepts/observability/metrics/powerscale/) -- Dell CSM Observability metrics documentation.
    - [Idrac Metrics](idrac_metrics.md) -- Hardware-level metrics from iDRAC.
    - [Ldms Metrics](ldms_metrics.md) -- OS-level metrics from LDMS.
