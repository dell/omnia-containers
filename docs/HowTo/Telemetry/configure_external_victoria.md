
# Collect Telemetry Data from External Clients to VictoriaMetrics and VictoriaLogs


Stream telemetry metrics and logs from external client nodes to VictoriaMetrics and VictoriaLogs deployed in the Service Kubernetes cluster.

## Overview


This procedure describes how to collect telemetry data from external client nodes and stream it to VictoriaMetrics (cluster mode) and VictoriaLogs (cluster mode) in the Service Kubernetes cluster.

- **VictoriaMetrics** -- Accepts Prometheus remote write and import endpoints for metrics ingestion.
- **VictoriaLogs** -- Accepts syslog (plaintext and TLS) and HTTP forwarding for log ingestion.


## Prerequisites


- VictoriaMetrics is deployed in cluster mode in the telemetry namespace.
- VictoriaLogs is deployed in cluster mode in the telemetry namespace (for log collection).
- `pod_external_ip_range` must be set in `provision_config.yml` and `provision.yml` must be executed after the external IP is configured.


## Collect Metrics to VictoriaMetrics


### Retrieve VictoriaMetrics Connection Details

1. Log in to the Service Kubernetes control plane.

2. Retrieve the `vmselect` LoadBalancer IP address (for querying data):

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vmselect
    ```

    Note the **External IP** (port 8481).

3. Retrieve the `vminsert` LoadBalancer IP address (for ingesting data):

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vminsert
    ```

    Note the **External IP** (port 8480).

4. Extract the VictoriaMetrics TLS CA certificate:

    ```bash title="Run on K8s control plane"
    kubectl get secret -n telemetry vminsert-tls -o jsonpath='{.data.ca\.crt}' | base64 --decode > ca.crt
    ```

### Push Sample Metrics from the Omnia Core Container

1. Create a test metric file:

    ```bash title="Run on omnia_core container"
    cat <<EOF > test_metric.txt
    # HELP test_metric A test metric
    # TYPE test_metric gauge
    test_metric{job="test",instance="external_node"} 42
    EOF
    ```

2. Push the metric to VictoriaMetrics using the `vminsert` LoadBalancer IP:

    ```bash title="Run on omnia_core container"
    curl --cacert ca.crt -X POST \
      "https://<vminsert external IP>:8480/insert/0/prometheus/api/v1/import/prometheus" \
      --data-binary @test_metric.txt
    ```

3. Query the inserted data from VictoriaMetrics:

    ```bash title="Run on omnia_core container"
    curl --cacert ca.crt -s \
      "https://<vmselect external IP>:8481/select/0/prometheus/api/v1/query?query=test_metric" \
      | python3 -m json.tool
    ```


## Collect Logs to VictoriaLogs


### Retrieve VLAgent Endpoint Information

1. Log in to the Service Kubernetes control plane.

2. Retrieve the VLAgent LoadBalancer service details:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vlagent
    ```

    Note the following ports:

    - **Port 514** -- Syslog plaintext (TCP/UDP)
    - **Port 6514** -- Syslog TLS (TCP)
    - **Port 9481** -- HTTP forwarder
    - **Port 9471** -- VictoriaLogs UI

3. Extract the VLAgent TLS CA certificate:

    ```bash title="Run on K8s control plane"
    kubectl get secret -n telemetry vlagent-tls -o jsonpath='{.data.ca\.crt}' | base64 --decode > ca.crt
    ```

### Configure Plaintext Syslog Source

To configure an external client to send syslog messages over plaintext:

```bash title="Run on external client node"
logger -n <vlagent external IP> -P 514 -t myapp "Test syslog message from external client"
```

For persistent configuration, update the client's rsyslog or syslog-ng configuration to forward to `<vlagent external IP>:514`.

### Configure TLS Syslog Source

To configure an external client to send syslog messages over TLS:

1. Copy the `ca.crt` to the external client node.

2. Configure rsyslog with TLS:

    ```text title="File: /etc/rsyslog.d/remote-tls.conf on external client"
    global(
        DefaultNetstreamDriverCAFile="/path/to/ca.crt"
    )

    action(
        type="omfwd"
        target="<vlagent external IP>"
        port="6514"
        protocol="tcp"
        StreamDriver="gtls"
        StreamDriverMode="1"
        StreamDriverAuthMode="x509/name"
    )
    ```

3. Restart rsyslog:

    ```bash title="Run on external client node"
    systemctl restart rsyslog
    ```

### Configure HTTP Forwarding Source

To forward logs via HTTP:

```bash title="Run on external client node"
curl -X POST "http://<vlagent external IP>:9481/insert/jsonline" \
  -H "Content-Type: application/json" \
  -d '{"_msg": "Test log from external client", "_time": "2024-01-01T00:00:00Z", "source": "external"}'
```

### Verify Log Ingestion

1. Retrieve the vlselect LoadBalancer IP:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vlselect
    ```

2. Query VictoriaLogs for the ingested logs:

    ```bash title="Run on K8s control plane"
    curl --cacert ca.crt -s \
      "https://<vlselect external IP>:9471/select/logsql/query?query=*&limit=10"
    ```

3. Access the VictoriaLogs UI in a web browser:

    ```
    https://<external vlselect loadbalancer IP>:9471/select/vmui
    ```


## Next Steps


- [External Kafka](configure_external_kafka.md) -- Stream data from external clients to Kafka.
- [Telemetry Overview](setup_telemetry.md) -- Overview of all telemetry sources.
