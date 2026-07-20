
# telemetry_config.yml

This file configures telemetry sources (iDRAC, LDMS, DCGM, PowerScale, UFM, VAST, OpenManage Enterprise), telemetry bridges (Vector-LDMS, Vector-OME), and telemetry sinks (VictoriaMetrics, VictoriaLogs, Kafka). It also includes component-specific configurations for each telemetry source.

## Supported Telemetry Sources, Bridges and Sinks


| Source | Description | Sinks |
| --- | --- | --- |
| [iDRAC](../../HowTo/Telemetry/configure_idrac.md) | Out-of-band hardware metrics (power, thermal, storage health) from Dell servers via Redfish | Kafka, VictoriaMetrics |
| [LDMS](../../HowTo/Telemetry/configure_ldms.md) | In-band OS metrics (CPU, memory, network, I/O) from Slurm compute nodes | Kafka, VictoriaMetrics (via Vector-LDMS) |
| [PowerScale](../../HowTo/Telemetry/configure_powerscale.md) | Storage performance metrics and logs from Dell PowerScale clusters | VictoriaMetrics, VictoriaLogs |
| [UFM](../../HowTo/Telemetry/configure_ufm.md) | NVIDIA UFM InfiniBand Fabric Manager metrics (IB port state, transmit/receive data, error counters, fabric topology) and syslog logs | VictoriaMetrics, VictoriaLogs |
| [VAST](../../HowTo/Telemetry/configure_vast.md) | Storage performance metrics and syslog events from VAST Storage appliances | VictoriaMetrics, VictoriaLogs |
| [OpenManage Enterprise (OME)](../../HowTo/Telemetry/telemetry_from_ome.md) | Server inventory, health, alerts, and audit logs from Dell OME via Kafka mTLS | Kafka, VictoriaMetrics, VictoriaLogs (via Vector-OME) |
| [SFM](../../HowTo/Telemetry/configure_sfm.md) | Network telemetry metrics from Smart Fabric Manager | VictoriaMetrics |

## Kafka PV Sizing Guidance

Set `persistence_size` in `input/telemetry_config.yml` under `telemetry_sinks.kafka` according to the table below. This value is applied per Kafka pod.

| Telemetry Sources | Node Count | Retention | Kafka PV Size |
|-------------------|------------|----------|----------------|
| iDRAC only | 50 nodes | 7 days | 128Gi per broker |
| iDRAC only | 200 nodes | 7 days | 512Gi per broker |
| iDRAC + LDMS | 50 nodes | 7 days | 200Gi per broker |
| iDRAC + LDMS | 200 nodes | 7 days | 800Gi per broker |
| iDRAC + LDMS + DCGM | 200 nodes | 7 days | 1Ti per broker |
| iDRAC + LDMS + DCGM | 500+ nodes | 7 days | 2Ti per broker |

!!! note

    - Kafka does not enable compression by default. All telemetry data (iDRAC, LDMS, DCGM) is stored uncompressed.
    - Each Kafka topic uses a replication factor of 2. The PV size recommendations already account for this.
    - Actual storage consumption varies based on iDRAC metric report group subscriptions, LDMS sampler plugin count, sampling intervals, and DCGM collection frequency.
    - Controllers use minimal storage (~100Mi for metadata) but share the same `persistence_size` setting as brokers.
    - If `log_retention_hours` is increased beyond the default of 168 (7 days), scale the PV size proportionally.

Monitor actual usage after deployment. If any broker exceeds 70% of its PV capacity within the first 3-4 days, increase `persistence_size` and redeploy to avoid filling the disk before the 7-day retention window.

## Parameter Reference
### Telemetry Configuration Parameters

--8<-- "html/telemetry_config.html"

### Telemetry Storage Configuration Parameters

--8<-- "html/telemetry_storage_config.html"


## Usage example

```yaml title="File: /opt/omnia/input/project_default/telemetry_config.yml"
---
telemetry_sources:

  idrac:
    metrics_enabled: true
    collection_targets:
      - "victoria_metrics"
      - "kafka"

  ldms:
    metrics_enabled: true
    collection_targets:
      - "kafka"

  dcgm:
    metrics_enabled: true

  powerscale:
    metrics_enabled: true
    logs_enabled: true
    collection_targets:
      - "victoria_metrics"
      - "victoria_logs"

  ufm:
    metrics_enabled: false
    logs_enabled: false
    collection_targets:
      - "victoria_metrics"
      - "victoria_logs"

  vast:
    metrics_enabled: false
    logs_enabled: false
    collection_targets:
      - "victoria_metrics"
      - "victoria_logs"

  ome:
    metrics_enabled: true
    logs_enabled: true
    collection_targets:
      - "kafka"

telemetry_bridges:

  vector_ldms:
    metrics_enabled: true

  vector_ome:
    metrics_enabled: true
    logs_enabled: true
    ome_identifier: "ome"

telemetry_sinks:

  victoria_metrics:
    persistence_size: "8Gi"
    retention_period: 168
    additional_metric_remote_write_endpoints: []

  victoria_logs:
    storage_size: "8Gi"
    retention_period: 168
    additional_log_write_endpoints: []

  kafka:
    persistence_size: "8Gi"
    log_retention_hours: 168
    log_retention_bytes: -1
    log_segment_bytes: 1073741824
    topic_partitions:
      idrac: 1
      ldms: 2

idrac_telemetry_configurations:
  mysqldb_storage: "1Gi"

ldms_configurations:
  agg_port: 6001
  store_port: 6001
  sampler_port: 10001
  sampler_plugins:
    - plugin_name: meminfo
      config_parameters: ""
      activation_parameters: "interval=30000000"

    - plugin_name: procstat2
      config_parameters: ""
      activation_parameters: "interval=30000000"

    - plugin_name: vmstat
      config_parameters: ""
      activation_parameters: "interval=30000000"

    - plugin_name: loadavg
      config_parameters: ""
      activation_parameters: "interval=30000000"

    - plugin_name: procnetdev2
      config_parameters: ""
      activation_parameters: "interval=30000000 offset=0"

powerscale_configurations:
  otel_collector_storage_size: "5Gi"
  csm_observability_values_file_path: ""

ufm_configuration:
  ufm_endpoint: ""
  ufm_metrics_port: 9001
  scrape_interval: "30s"
  scrape_timeout: "15s"
  tls_mode: "self_signed"
  ufm_ca_cert_path: ""
  auth_mode: "basic"

vast_configuration:
  vast_endpoint: ""
  vast_metrics_port: 443
  metrics_path: "/api/prometheusmetrics/all"
  scrape_interval: "30s"
  scrape_timeout: "15s"
  tls_mode: "self_signed"
  vast_ca_cert_path: ""
  auth_mode: "basic"
```

```yaml title="File: /opt/omnia/input/project_default/telemetry_storage_config.yml"
---
victoria_cluster_storage:
  vmstorage:
    replicas: 3
    resources:
      requests:
        memory: "1Gi"
        cpu: "250m"
      limits:
        memory: "2Gi"
        cpu: "1000m"
  vminsert:
    replicas: 2
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
  vmselect:
    replicas: 2
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
  vmagent:
    replicas: 2
    resources:
      requests:
        memory: "128Mi"
        cpu: "50m"
      limits:
        memory: "512Mi"
        cpu: "250m"

victoria_logs_cluster_storage:
  vlstorage:
    replicas: 3
    resources:
      requests:
        memory: "512Mi"
        cpu: "100m"
      limits:
        memory: "1Gi"
        cpu: "500m"
  vlinsert:
    replicas: 2
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
  vlselect:
    replicas: 2
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
  vlagent:
    replicas: 2
    pvc_size: "5Gi"
    resources:
      requests:
        memory: "64Mi"
        cpu: "25m"
      limits:
        memory: "256Mi"
        cpu: "100m"

vector_storage:
  ldms:
    replicas: 2
    resources:
      requests:
        memory: "128Mi"
        cpu: "50m"
      limits:
        memory: "256Mi"
        cpu: "250m"
  ome:
    replicas: 2
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "500m"
  vlagent_vector:
    replicas: 2
    pvc_size: "5Gi"
    resources:
      requests:
        memory: "128Mi"
        cpu: "50m"
      limits:
        memory: "256Mi"
        cpu: "250m"
  vmagent_vector:
    replicas: 2
    pvc_size: "5Gi"
    resources:
      requests:
        memory: "128Mi"
        cpu: "50m"
      limits:
        memory: "256Mi"
        cpu: "250m"

csi_volume_exporter_storage:
  resources:
    requests:
      cpu: "50m"
      memory: "64Mi"
    limits:
      cpu: "200m"
      memory: "256Mi"

csm_metrics_powerscale_storage:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"

idrac_telemetry_storage:
  mysqldb:
    resources:
      requests:
        cpu: "100m"
        memory: "256Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
  activemq:
    resources:
      requests:
        cpu: "100m"
        memory: "512Mi"
      limits:
        cpu: "500m"
        memory: "1536Mi"
  receiver:
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "256Mi"
  kafka_pump:
    resources:
      requests:
        cpu: "50m"
        memory: "128Mi"
      limits:
        cpu: "200m"
        memory: "512Mi"
  victoria_pump:
    resources:
      requests:
        cpu: "50m"
        memory: "128Mi"
      limits:
        cpu: "200m"
        memory: "512Mi"

kafka_storage:
  kafka:
    resources:
      requests:
        memory: "512Mi"
        cpu: "200m"
      limits:
        memory: "1Gi"
        cpu: "1000m"
  entity_operator:
    user_operator:
      resources:
        requests:
          memory: "512Mi"
          cpu: "200m"
        limits:
          memory: "512Mi"
          cpu: "1000m"
```

!!! info

    - [Idrac Metrics](../Metrics/idrac_metrics.md) -- iDRAC metric catalog.
    - [Ldms Metrics](../Metrics/ldms_metrics.md) -- LDMS sampler metric catalog.
    - [DCGM Metrics](../Metrics/dcgm_metrics.md) -- In-band GPU metric catalog (DCGM/ROCm).
    - [Ports](../../SecurityConfigurationGuide/network_security.md#telemetry-ports) -- Ports used by telemetry
      services.
