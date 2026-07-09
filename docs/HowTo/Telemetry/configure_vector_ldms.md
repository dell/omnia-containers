
# Configure Vector-LDMS Pipeline


Configure Vector-LDMS to consume LDMS metrics from the Kafka `ldms` topic, transform them to Prometheus format, and route to VictoriaMetrics.

## Overview


Vector-LDMS provides Kafka-to-VictoriaMetrics ingestion for LDMS telemetry data. The deployment includes the following components:

### Components

- **Vector-LDMS** -- Kafka consumer for LDMS metrics. Consumes from the `ldms` topic, transforms Avro-encoded LDMS data to Prometheus metric format, and routes to VictoriaMetrics via vmagent-vector.
- **vmagent-vector** -- Dedicated vmagent instance as a write-buffer between Vector pods and vminsert. Accepts `prometheus_remote_write` on port 8429, buffers to disk, and forwards to vminsert. Separate from the existing scraper vmagent to isolate failure domains.

For more details on Vector, see [Vector Documentation](https://vector.dev/docs/).

### Data Flow

```
LDMS Store (store_avro_kafka) → Kafka 'ldms' topic → Vector-LDMS → vmagent-vector → vminsert → VictoriaMetrics
```


## Prerequisites


- `provision.yml` has been executed successfully with `service_kube_control_plane_x86_64` and `service_kube_node_x86_64` in the mapping file.
- Kafka is deployed and operational via Strimzi operator.
- VictoriaMetrics cluster mode is deployed with vminsert, vmstorage, and vmselect components.
- LDMS is configured and the `store_avro_kafka` plugin is producing to the Kafka `ldms` topic.


## Procedure


1. **Specify the following entries in `software_config.json`**:

    ```json
    {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]}
    ```

2. **Configure `telemetry_config.yml` to enable Vector-LDMS**:

    ```yaml title="Example: Enable Vector-LDMS"
    telemetry_bridges:
      vector_ldms:
        metrics_enabled: true
    ```

    For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

The following components are deployed when `vector_ldms > metrics_enabled = true`:

- **vmagent-vector** -- Dedicated vmagent instance for Vector write-buffer.
- **Vector-LDMS** -- Kafka consumer pod for LDMS metrics.

!!! note

    Vector-LDMS reuses the existing `kafkapump` KafkaUser for mTLS credentials.

!!! important

    If you enable Vector-LDMS after the initial deployment, execute the `telemetry.sh` script on the K8s control plane:

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Verification


### Verify Vector-LDMS Telemetry Pods

1. Verify that the Vector-LDMS pod is running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry | grep vector-ldms
    ```

    ![Vector-LDMS Pod](../../assets/images/victoria_metrics_ldms_1.png)

2. Verify that the vmagent-vector pod is running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry | grep vmagent-vector
    ```

    ![vmagent-vector Pod](../../assets/images/victoria_metrics_ldms_2.png)

3. Verify that the VictoriaMetrics service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry | grep vm
    ```

    ![VictoriaMetrics Service](../../assets/images/victoria_metrics_ldms_3.png)

### View LDMS Metrics in VictoriaMetrics UI (VMUI)

1. Note the **External IP** and **port number** of the VictoriaMetrics service.

2. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

3. Verify that metrics are reaching VictoriaMetrics by querying the VMUI. For example, the following query displays LDMS-related metrics:

    ```
    {__name__=~"ldms_.*"}
    ```

    ![LDMS Metrics in VMUI](../../assets/images/victoria_metrics_ldms_ui_login.png)


## Next Steps


- [Configure LDMS](configure_ldms.md) -- Set up LDMS telemetry.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
