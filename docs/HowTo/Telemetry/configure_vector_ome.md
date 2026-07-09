
# Configure Vector-OME Pipeline


Configure Vector-OME to consume OpenManage Enterprise telemetry from Kafka `ome.*` topics and route metrics to VictoriaMetrics and logs to VictoriaLogs.

## Overview


Vector-OME provides Kafka-to-Victoria ingestion for OpenManage Enterprise telemetry data. The deployment includes the following components:

### Data Flow

```
OME → Kafka 'ome.*' topics → Vector-OME → vmagent-vector (metrics) → vminsert → VictoriaMetrics
OME → Kafka 'ome.*' topics → Vector-OME → vlagent-vector (logs) → vlinsert → VictoriaLogs
```

### Components

- **Vector-OME** -- Kafka consumer for OME telemetry. Consumes from `ome.*` topics and routes metrics to VictoriaMetrics and logs to VictoriaLogs.
- **vmagent-vector** -- Dedicated vmagent instance as a write-buffer between Vector pods and vminsert. Accepts `prometheus_remote_write` on port 8429, buffers to disk, and forwards to vminsert.
- **vlagent-vector** -- Dedicated VictoriaLogs forwarding agent deployed as a log write-buffer for Vector pods. Accepts JSON Lines on an HTTP endpoint (port 9427), buffers to disk, and forwards to vlinsert. Required for Vector-OME log/event sinks.

For more details on Vector, see [Vector Documentation](https://vector.dev/docs/).


## Prerequisites


- `provision.yml` has been executed successfully with `service_kube_control_plane_x86_64` and `service_kube_node_x86_64` in the mapping file.
- Kafka is deployed and operational via Strimzi operator.
- VictoriaMetrics cluster mode is deployed with vminsert, vmstorage, and vmselect components.
- VictoriaLogs cluster mode is deployed with vlinsert, vlstorage, and vlselect components (required for Vector-OME logs).
- OME is configured externally and producing to Kafka `ome.*` topics via the external mTLS listener (port 9094). See [Configure OpenManage Enterprise Telemetry](telemetry_from_ome.md).


## Procedure


1. **Specify the following entries in `software_config.json`**:

    ```json
    {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]}
    ```

2. **Configure `telemetry_config.yml` to enable Vector-OME**:

    ```yaml title="Example: Enable Vector-OME"
    telemetry_bridges:
      vector_ome:
        metrics_enabled: true
        logs_enabled: true
    ```

    For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

The following components are deployed based on configured feature flags:

- **vmagent-vector** -- Deployed when `vector_ome_metrics_enabled` is set to `true`.
- **Vector-OME** -- Deployed when `vector_ome > metrics_enabled = true` or `vector_ome > logs_enabled = true`.
- **vlagent-vector** -- Deployed when `vector_ome > logs_enabled = true`.
- **Kafka topics and ACLs** -- For OME topics (deployed when Vector-OME is enabled).
- **KafkaUser resources** -- For Vector-OME mTLS credentials (`vector-ome-user`).

!!! note

    Vector-OME requires a new KafkaUser (`vector-ome-user`) because OME is an external producer with a different security domain.

!!! important

    If you enable Vector-OME after the initial deployment, execute the `telemetry.sh` script on the K8s control plane:

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Verification


For OME telemetry verification steps including Kafka consumer tests, VictoriaMetrics queries, and VictoriaLogs checks, see the [Verification section in Configure OpenManage Enterprise Telemetry](telemetry_from_ome.md#verification).


## Next Steps


- [Configure OpenManage Enterprise Telemetry](telemetry_from_ome.md) -- Integrate OME with Kafka.
- [Telemetry Overview](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
