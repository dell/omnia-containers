
# telemetry_config.yml Reference


File path: `/opt/omnia/input/project_default/telemetry_config.yml`

This file configures the Omnia telemetry pipeline: iDRAC metric collection,
Kafka message streaming, VictoriaMetrics time-series storage, Grafana
dashboards, and LDMS node-level samplers.

## General telemetry settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `enable_telemetry` | Boolean | No | `false` | Master switch for the telemetry pipeline. When `false`, all telemetry components are skipped. |
| `telemetry_entry_node` | String | Conditional | (none) | Hostname or IP of the node where telemetry services (Kafka, VictoriaMetrics, Grafana) are deployed. Required when `enable_telemetry` is `true`. |

## Kafka settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `kafka_broker_port` | Integer | No | `9092` | Port on which Kafka listens for producer/consumer connections. |
| `kafka_topic_idrac` | String | No | `idrac_telemetry` | Kafka topic name for iDRAC telemetry data. |
| `kafka_topic_ldms` | String | No | `ldms_telemetry` | Kafka topic name for LDMS node-level metrics. |
| `kafka_retention_hours` | Integer | No | `168` | Number of hours to retain messages in Kafka topics (default: 7 days). |
| `kafka_log_dir` | String | No | `/var/lib/kafka/data` | Directory for Kafka commit logs. Ensure sufficient disk space. |

## VictoriaMetrics settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `victoriametrics_port` | Integer | No | `8428` | HTTP port for VictoriaMetrics query and ingestion API. |
| `victoriametrics_retention` | String | No | `6` | Data retention period in months. Older data is automatically purged. |
| `victoriametrics_storage_path` | String | No | `/var/lib/victoria-metrics` | Persistent data directory for VictoriaMetrics. |

## Grafana settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `grafana_port` | Integer | No | `3000` | HTTP port for the Grafana web interface. |
| `grafana_admin_user` | String | No | `admin` | Grafana administrator username. |
| `grafana_admin_password` | String | No | (vault-managed) | Grafana administrator password. Set via `credentials_utility.yml`. |

## iDRAC telemetry settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `enable_idrac_telemetry` | Boolean | No | `true` | Collect power, thermal, and health metrics from iDRAC via Redfish. Only effective when `enable_telemetry` is `true`. |
| `idrac_telemetry_interval` | Integer | No | `300` | Collection interval in seconds (default: 5 minutes). |
| `idrac_username` | String | Conditional | (none) | iDRAC username for Redfish API access. Set via `credentials_utility.yml`. |
| `idrac_password` | String | Conditional | (vault-managed) | iDRAC password. Set via `credentials_utility.yml`. |

## LDMS settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `enable_ldms` | Boolean | No | `true` | Enable LDMS metric samplers on compute nodes. Only effective when `enable_telemetry` is `true`. |
| `ldms_samplers` | List | No | `[meminfo, vmstat, procstat, procnetdev]` | List of LDMS sampler plugins to activate. See [Ldms Metrics](../Metrics/ldms_metrics.md) for the full catalog. |
| `ldms_sample_interval` | Integer | No | `10` | Sampling interval in seconds. |
| `ldms_aggregator_port` | Integer | No | `10001` | Port for the LDMS aggregator daemon. |

## Usage example


```yaml title="File: /opt/omnia/input/project_default/telemetry_config.yml"
enable_telemetry: true
telemetry_entry_node: "kube-cp-01"

kafka_broker_port: 9092
kafka_retention_hours: 168

victoriametrics_port: 8428
victoriametrics_retention: "6"

grafana_port: 3000

enable_idrac_telemetry: true
idrac_telemetry_interval: 300

enable_ldms: true
ldms_samplers:
  - meminfo
  - vmstat
  - procstat
  - procnetdev
ldms_sample_interval: 10
```


!!! info

    - [Idrac Metrics](../Metrics/idrac_metrics.md) -- iDRAC metric catalog.
    - [Ldms Metrics](../Metrics/ldms_metrics.md) -- LDMS sampler metric catalog.
    - [Gpu Metrics](../Metrics/gpu_metrics.md) -- GPU metric catalog.
    - [Ports](../ClusterRequirements/ports.md) -- Ports used by telemetry
      services.
