
# Integrate OME with Kafka for Telemetry Streaming


Configure OpenManage Enterprise (OME) to securely stream telemetry data to the Omnia Kafka pipeline using mutual TLS (mTLS).

## Overview


This procedure describes how to integrate OpenManage Enterprise (OME) with the Omnia Kafka pipeline for secure telemetry data streaming. OME connects to the Kafka external mTLS listener (port 9094) and publishes telemetry data (inventory, health, alerts, audit logs) to Kafka topics. To route OME telemetry from Kafka to VictoriaMetrics and VictoriaLogs, enable the [Vector-OME bridge](#enable-vector-ome-bridge).


## Prerequisites


- `pod_external_ip_range` must be set in `provision_config.yml` and `provision.yml` must be executed after the external IP is configured.
- Kafka is deployed and operational in the telemetry namespace.
- Nodes must be discovered in OME before configuring telemetry streaming.


## Procedure


### Retrieve Kafka Connection Details

1. Log in to the Service Kubernetes control plane.

2. Retrieve the Kafka LoadBalancer external IP:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep kafka
    ```

    Note the **External IP** of the Kafka LoadBalancer service (port 9094 for mTLS connections).

### Extract TLS Certificates

1. Extract the Kafka TLS certificates:

    ```bash title="Run on K8s control plane"
    kubectl get secret -n telemetry kafka-external-tls -o jsonpath='{.data.ca\.crt}' | base64 --decode > ca.crt
    kubectl get secret -n telemetry kafka-external-tls -o jsonpath='{.data.user\.crt}' | base64 --decode > user.crt
    kubectl get secret -n telemetry kafka-external-tls -o jsonpath='{.data.user\.key}' | base64 --decode > user.key
    ```

### Create Client Certificate in .pfx Format

OME requires a `.pfx` format client certificate for mTLS authentication:

```bash title="Run on K8s control plane"
openssl pkcs12 -export -in user.crt -inkey user.key -certfile ca.crt -out client.pfx -password pass:<password>
```

![OME Certificate PFX Format](../../assets/images/ome_certificate_pfx_format.png)

### Configure OME Kafka Connectivity

1. Log in to the OME web UI.

2. Navigate to **Application Settings > Data Streaming > Remote Connectivity**.

    ![OME Remote Connectivity](../../assets/images/ome_remote_connectivity.png)

3. Select **Kafka Connectivity** and configure:

    - **Bootstrap Server**: `<kafka-external-ip>:9094`
    - **Security Protocol**: `SSL`

    ![OME Kafka Connectivity](../../assets/images/ome_kafka_connectivity.png)

4. Upload the client certificate (`client.pfx`) and enter the password.

5. Configure **Data Configuration** to select the telemetry data types to stream:

    ![OME Data Configuration](../../assets/images/ome_data_configuration.png)

6. Configure **Group Configuration** to select the device groups to monitor:

    ![OME Group Configuration](../../assets/images/ome_group_configuration.png)

7. Save and verify the connectivity status shows as **Connected**:

    ![OME Connectivity Verification](../../assets/images/ome_connectivity_verification.png)


## Enable Vector-OME Bridge


To route OME telemetry from Kafka to VictoriaMetrics and VictoriaLogs, enable the Vector-OME bridge in `telemetry_config.yml`. Vector-OME consumes from `ome.*` topics and routes metrics to VictoriaMetrics and logs to VictoriaLogs via dedicated vmagent-vector and vlagent-vector instances.

For more details on Vector, see [Vector Documentation](https://vector.dev/docs/).

1. **Configure `telemetry_config.yml` to enable Vector-OME**:

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


### Verify OME Messages in Kafka

To verify that OME telemetry data is being successfully published to the OME Kafka topics:

1. Log in to the Service Kubernetes control plane.

2. Set the required variables:

    ```bash title="Run on K8s control plane"
    KAFKA_LB_IP=<external IP of bridge-bridge-lb service>
    TOPIC=<OME Topic Name>
    GROUP=ome-consumer-group
    INSTANCE=ome-consumer
    ```

3. Create a Kafka consumer:

    ```bash title="Run on K8s control plane"
    curl -s -X POST "http://$KAFKA_LB_IP:8080/consumers/$GROUP" \
      -H 'content-type: application/vnd.kafka.v2+json' \
      -d '{"name": "ome-consumer", "format": "json", "auto.offset.reset": "earliest"}'
    ```

4. View the list of OME Kafka topics configured:

    ```bash title="Run on K8s control plane"
    curl -s -X GET "http://$KAFKA_LB_IP:8080/topics" | jq '.'
    ```

5. Subscribe the consumer to the telemetry topic:

    ```bash title="Run on K8s control plane"
    curl -s -X POST "http://$KAFKA_LB_IP:8080/consumers/$GROUP/instances/$INSTANCE/subscription" \
      -H 'content-type: application/vnd.kafka.v2+json' \
      -d '{"topics": ["'"$TOPIC"'"]}'
    ```

6. Consume messages from the topic:

    ```bash title="Run on K8s control plane"
    while true; do
      curl -s -X GET "http://$KAFKA_LB_IP:8080/consumers/$GROUP/instances/$INSTANCE/records" \
        -H 'accept: application/vnd.kafka.json.v2+json' | jq '.'
      sleep 2
    done
    ```

7. (Optional) Cleanup the consumer:

    ```bash title="Run on K8s control plane"
    curl -s -X DELETE "http://$KAFKA_LB_IP:8080/consumers/$GROUP/instances/$INSTANCE"
    ```

!!! note

    - **From beginning**: Ensure `"auto.offset.reset": "earliest"` when creating the consumer if you want existing data.
    - **Message format**: Use `"format": "json"` only if producers publish JSON. Otherwise use `"binary"` and decode base64 payloads.
    - **Throughput**: Adjust polling interval; bridge returns empty array when no new records.
    - **404/409 errors**: 404 usually means wrong group/instance name; 409 means already subscribed.

### View OME Metrics in VictoriaMetrics UI (VMUI)

To verify that OME telemetry data is being successfully routed from Kafka to VictoriaMetrics using Vector:

1. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

2. Navigate to the **Explore** tab.

3. Run the following query to retrieve health metrics from OME:

    ```
    last_over_time({source_subsystem="ome", type="healty"}[24h])
    ```

    ![OME Metrics in VMUI](../../assets/images/external_kafka_ome_metrics_health.png)

!!! note

    `source_subsystem=ome` comes from the `ome_identifier` that the user has given in the `telemetry_config.yml` input file and the suffix after the dot (i.e., health, inventory, auditlogs) is coming from OME.

4. Verify that OME-related metrics are displayed in the results.

!!! note

    Ensure that the Vector-OME bridge is enabled in `telemetry_config.yml` (`telemetry_bridges > vector_ome > metrics_enabled: true`) for metrics data to flow from Kafka to VictoriaMetrics.

### View OME Logs in VictoriaLogs

To verify that OME telemetry data is being successfully routed from Kafka to VictoriaLogs using Vector:

1. Access the VictoriaLogs UI in a web browser:

    ```
    https://<external vlselect loadbalancer IP>:9471/select/vmui
    ```

2. Navigate to the **Select** tab.

3. In the query field, run the following query to filter for OME logs:

    ```
    _msg_topic:ome.auditlogs
    ```

    ![OME Logs in VictoriaLogs](../../assets/images/external_kafka_ome_logs_audit.png)

4. Verify that OME-related logs are displayed in the results.

!!! note

    Ensure that the Vector-OME bridge is enabled in `telemetry_config.yml` (`telemetry_bridges > vector_ome > logs_enabled: true`) for logs data to flow from Kafka to VictoriaLogs.


## Next Steps


- [Telemetry Overview](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
