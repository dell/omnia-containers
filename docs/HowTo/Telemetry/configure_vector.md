
# Configure Vector Telemetry Pipeline


Configure Vector as a high-performance data pipeline for routing telemetry data from Kafka to VictoriaMetrics and VictoriaLogs.

## Overview


Vector provides Kafka-to-Victoria ingestion for LDMS and OpenManage Enterprise (OME) sources.

For more details on Vector, see [Vector Documentation](https://vector.dev/docs/).

### Data Flow

```
LDMS Store (store_avro_kafka) → Kafka 'ldms' topic → Vector-LDMS → vmagent-vector → vminsert → VictoriaMetrics
OME → Kafka 'ome.*' topics → Vector-OME → vmagent-vector → vminsert → VictoriaMetrics
OME → Kafka 'ome.*' topics → Vector-OME → vlagent-vector → vlinsert → VictoriaLogs
```

### Components

- **Vector-LDMS** -- Kafka consumer for LDMS metrics. Consumes from the `ldms` topic and routes to VictoriaMetrics via vmagent-vector.
- **Vector-OME** -- Kafka consumer for OME telemetry. Consumes from `ome.*` topics and routes metrics to VictoriaMetrics and logs to VictoriaLogs.
- **vmagent-vector** -- Dedicated vmagent instance as a write-buffer between Vector pods and vminsert. Accepts `prometheus_remote_write` on port 8429, buffers to disk, and forwards to vminsert. Separate from the existing scraper vmagent to isolate failure domains.
- **vlagent-vector** -- Dedicated VictoriaLogs forwarding agent deployed as a log write-buffer for Vector pods. Accepts JSON Lines on an HTTP endpoint (port 9427), buffers to disk, and forwards to vlinsert. Required for Vector-OME log/event sinks.


## Prerequisites


- `provision.yml` has been executed successfully with `service_kube_control_plane` and `service_kube_node` in the mapping file.
- Kafka is deployed and operational via Strimzi operator.
- VictoriaMetrics cluster mode is deployed with vminsert, vmstorage, and vmselect components.
- VictoriaLogs cluster mode is deployed with vlinsert, vlstorage, and vlselect components (required for Vector-OME logs).


## Procedure


1. **Specify the following entries in `software_config.json`**. If any entry is missing, Omnia skips Vector deployment and logs an informational message.

    ```json
    {"name": "service_k8s", "version": "1.34.1", "arch": ["x86_64"]}
    ```

2. **Configure `telemetry_config.yml` to enable Vector telemetry bridges**:

    !!! note

        Vector telemetry bridges are controlled by feature flags in `telemetry_config.yml`:

        - Set `telemetry_bridges > vector_ldms > metrics_enabled` to enable Vector-LDMS.
        - Set `telemetry_bridges > vector_ome > metrics_enabled` to enable Vector-OME metrics routing.
        - Set `telemetry_bridges > vector_ome > logs_enabled` to enable Vector-OME log routing.

    For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

3. **For Vector-LDMS**, ensure that LDMS is configured and the `store_avro_kafka` plugin is producing to the Kafka `ldms` topic. Vector-LDMS consumes from this topic.

4. **For Vector-OME**, ensure that OME is configured externally and producing to Kafka `ome.*` topics via the external mTLS listener (port 9094). Run the `external_kafka_connect_details.yml` playbook to configure OME connectivity.

The following components are deployed based on configured feature flags:

- **vmagent-vector** -- Deployed when `vector_ome_metrics_enabled` or `vector_ldms_metrics_enabled` is set to `true`.
- **Vector-LDMS** -- Deployed when `telemetry_bridges > vector_ldms > metrics_enabled = true`.
- **Vector-OME** -- Deployed when `telemetry_bridges > vector_ome > metrics_enabled = true` or `telemetry_bridges > vector_ome > logs_enabled = true`.
- **vlagent-vector** -- Deployed when `telemetry_bridges > vector_ome > logs_enabled = true`.
- **Kafka topics and ACLs** -- For OME topics (deployed when Vector-OME is enabled).
- **KafkaUser resources** -- For Vector-OME mTLS credentials (deployed when Vector-OME is enabled).

!!! note

    Vector-LDMS reuses the existing `kafkapump` KafkaUser for mTLS credentials. Vector-OME requires a new KafkaUser (`vector-ome-user`) because OME is an external producer with a different security domain.

!!! important

    If you enable Vector bridges after the initial deployment, execute the `telemetry.sh` script on the K8s control plane:

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Verification


For detailed verification steps including Vector-LDMS pod checks, vmagent-vector logs, and VMUI queries, see [Verify Telemetry - LDMS Flow](verify_telemetry.md#verify-ldms-telemetry-flow) and [Verify Telemetry - OME Flow](verify_telemetry.md#verify-ome-telemetry-flow).


## Next Steps


- [Configure LDMS](configure_ldms.md) -- Set up LDMS telemetry.
- [Configure OpenManage Enterprise Telemetry](telemetry_from_ome.md) -- Integrate OME with Kafka.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
