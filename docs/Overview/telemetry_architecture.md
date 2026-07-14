
# Telemetry Architecture
Omnia supports telemetry collection to monitor and manage your HPC infrastructure. The telemetry components, data flows, and architecture diagram below describe the supported telemetry sources and how data is collected, transported, and stored.

!!! note

    To enable any telemetry and log collections (iDRAC, LDMS, PowerScale, DCGM, UFM, VAST, or Vector), ensure that the `service_k8s` entry is mentioned in the `software_config.json` file and the corresponding telemetry source fields are set to `true` in the `telemetry_config.yml` file. For example, set `telemetry_sources > idrac > metrics_enabled = true` to enable iDRAC telemetry, or `telemetry_sources > powerscale > metrics_enabled = true` to enable PowerScale telemetry.


## Omnia Telemetry Architecture


Omnia collects telemetry data from HPC cluster nodes using: LDMS for OS-level metrics and iDRAC for hardware telemetry.

The following diagram illustrates the telemetry services that can be deployed using Omnia and the data flow between the components.

![Omnia Telemetry Architecture](../assets/images/telemetry_arch_s.svg)


## Telemetry Components


The following components are involved in the telemetry services deployed by Omnia:

**OIM (Omnia Infrastructure Manager)**

Central management node that deploys and configures all telemetry services across the cluster.

**Service Kubernetes Cluster**

Hosts telemetry collection and storage services:

- **LDMS Aggregator** -- Receives metrics from slurm compute node samplers.
- **LDMS Store** -- Stores aggregated LDMS data.
- **iDRAC Collector** -- Collects hardware telemetry via Redfish API.
- **Kafka Broker** -- Streams telemetry data.
- **VMAgent** -- Forwards metrics to VictoriaMetrics.
- **VictoriaMetrics** -- Time-series database for metric storage.
- **vmstorage-victoria-cluster** -- Storage backend for VictoriaMetrics cluster.
- **vminsert-victoria-cluster** -- Ingestion component for VictoriaMetrics cluster.
- **vmselect-victoria-cluster** -- Query component for VictoriaMetrics cluster.
- **VictoriaLogs Cluster** -- Distributed log storage system with vlstorage, vlinsert, vlselect components.
- **vlstorage-victoria-logs-cluster** -- Storage backend for VictoriaLogs cluster.
- **vlinsert-victoria-logs-cluster** -- Ingestion component for VictoriaLogs cluster.
- **vlselect-victoria-logs-cluster** -- Query component for VictoriaLogs cluster.
- **VLAgent** -- Platform-managed log collection agent that receives logs from external sources.
- **karavi-metrics-powerscale** -- Collects PowerScale metrics via Karavi Observability.
- **csm-metrics** -- Collects PowerScale metrics.
- **csi-volume-exporter** -- Exports CSI volume metrics.
- **otel-collector** -- Forwards metrics to VictoriaMetrics and VictoriaLogs.
- **CSI Driver for Dell PowerScale** -- Driver required for communication between PowerScale and service Kubernetes nodes.
- **Vector** -- High-performance data pipeline tool for collecting, transforming, and routing logs and metrics.
- **Vector-LDMS** -- Kafka consumer for LDMS metrics, routes to VictoriaMetrics via vmagent-vector.
- **Vector-OME** -- Kafka consumer for OME telemetry, routes metrics to VictoriaMetrics and logs to VictoriaLogs.
- **vmagent-vector** -- Dedicated vmagent instance as a write-buffer between Vector pods and vminsert.
- **vlagent-vector** -- Dedicated VictoriaLogs forwarding agent for log/event data from Vector pods.

**Slurm Cluster**

Each slurm compute node runs:

- **LDMS Sampler** -- Collects OS metrics (CPU, memory, network, and I/O).
- **iDRAC** -- Provides hardware health data (temperature, power, and fans).


## Telemetry Data Flows


### iDRAC and LDMS Telemetry Data Flows

**LDMS Flow (OS Metrics)**

```text
Slurm Compute Nodes (LDMS Sampler) → LDMS Aggregator → LDMS Store → Kafka
```

**iDRAC Flow (Hardware Metrics)**

```text
iDRAC (BMC) → iDRAC Collector → Kafka
iDRAC (BMC) → iDRAC Collector → VMAgent → Victoria Metrics
```

### UFM Telemetry Data Flows

```text
UFM Fabric Manager → OTEL Collector → vmagent(shared) → VictoriaMetrics
UFM Fabric Manager forwards syslog → vlagent → VictoriaLogs
```

### VAST Telemetry Data Flows

```text
VAST Storage Appliances → OTEL Collector → vmagent(shared) → VictoriaMetrics
VAST Storage Appliances forwards syslog → vlagent → VictoriaLogs
```

### DCGM Telemetry Data Flows

```text
GPU Nodes → DCGM → VMAgent → VictoriaMetrics
```

### Vector Telemetry Data Flows

```text
LDMS Store (store_avro_kafka) → Kafka 'ldms' topic → Vector-LDMS → vmagent-vector → vminsert → VictoriaMetrics
OME → Kafka '*.inventory', '*.telemetry', '*.health', '*.alerts', '*.auditlogs' topics → Vector-OME → vmagent-vector (metrics) → vminsert → VictoriaMetrics
OME → Kafka '*.inventory', '*.telemetry', '*.health', '*.alerts', '*.auditlogs' topics → Vector-OME → vlagent-vector (logs) → vlinsert → VictoriaLogs
```

!!! note

    To list all Kafka topics (including LDMS, iDRAC, and OME topics), run the following command:

    ```bash
    curl -s -X GET "http://$KAFKA_LB_IP:8080/topics" | jq '.'
    ```

### PowerScale Telemetry Data Flows

```text
PowerScale Nodes → CSM Metrics PowerScale → OTEL Collector → vmagent(shared) → VictoriaMetrics
PowerScale Nodes forwards syslog → vlagent → VictoriaLogs
```
