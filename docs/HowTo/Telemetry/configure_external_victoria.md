# Collect Telemetry Data from External Clients to VictoriaMetrics and VictoriaLogs


Stream telemetry metrics and logs from external client nodes to VictoriaMetrics and VictoriaLogs deployed in the Service Kubernetes cluster.

## Overview


This procedure describes how to collect telemetry data from external client nodes and stream it to VictoriaMetrics (cluster mode) and VictoriaLogs (cluster mode) in the Service Kubernetes cluster.

- **VictoriaMetrics** -- Accepts Prometheus remote write and import endpoints for metrics ingestion.
- **VictoriaLogs** -- Accepts syslog (plaintext and TLS) and HTTP forwarding for log ingestion.


## Prerequisites


This is a post-deployment procedure. The Omnia telemetry stack (including
VictoriaMetrics and VictoriaLogs) must already be deployed and running before you
connect external clients.

- A Service Kubernetes cluster is running with VictoriaMetrics deployed in the `telemetry` namespace.
- `pod_external_ip_range` is set in `omnia_config.yml` so MetalLB can assign
  external IPs to the `vminsert`, `vmselect`, and VictoriaLogs services.
- External access to VictoriaMetrics is available through:
    - LoadBalancer port `8480` for ingesting (inserting) data.
    - LoadBalancer port `8481` for querying data.
- VictoriaLogs is deployed in cluster mode in the `telemetry` namespace (for log collection).
- Network connectivity exists from external log sources to the Service Kubernetes cluster.

!!! important

    Ensure that `pod_external_ip_range` in `omnia_config.yml` is reachable from external log sources.


## Collect Metrics to VictoriaMetrics


### Step 1: Retrieve VictoriaMetrics Connection Details

Run the following playbook to retrieve the VictoriaMetrics connection details and TLS certificate from the Service Kubernetes cluster:

```bash title="Run on omnia_core container"
cd /omnia/utils
ansible-playbook external_victoria_connect_details.yml
```

The `external_victoria_connect_details.yml` playbook does the following:

- Retrieves the VictoriaMetrics `vminsert` and `vmselect` LoadBalancer IPs.
- Extracts the server CA certificate for TLS.
- Writes the connection details to `/omnia/utils/external_victoria_connect_details.yml`.
- Saves the CA certificate at `/omnia/utils/victoria-certs/ca.crt`.

### Step 2: Push Sample Metrics from the Omnia Core Container

1. Add the LoadBalancer insert and select IP addresses to `/etc/hosts`:

    ```bash title="Run on omnia_core container"
    echo "<vminsert-IP> vminsert.telemetry.svc.cluster.local" >> /etc/hosts
    echo "<vmselect-IP> vmselect.telemetry.svc.cluster.local" >> /etc/hosts
    ```

    For `vminsert` and `vmselect` IP, use the values retrieved by the `external_victoria_connect_details.yml` playbook.

    !!! note

        The `/etc/hosts` update must be repeated if the SFM Prometheus pod restarts.

2. Create a new test metric:

    ```bash title="Run on omnia_core container"
    curl --cacert ca.crt -X POST \
      "https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/import/prometheus" \
      -H "Content-Type: text/plain" \
      -d "test_metric{source=\"external\"} 42"
    ```

    !!! note

        Use `https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write` to push the metrics from an external client, such as [Smart Fabric Manager (SFM)](https://www.dell.com/en-in/shop/ipovw/smartfabric-manager-for-sonic){target="_blank"}. For collecting telemetry data from SFM to Victoria DB, see [SFM Telemetry](configure_sfm.md).

3. Push sample test metrics to Victoria DB:

    ```bash title="Run on omnia_core container"
    curl --cacert ca.crt -X POST \
      "https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/import/prometheus" \
      -H "Content-Type: text/plain" \
      -d 'cpu_usage{host="server1",job="new"} 75.5
    memory_usage{host="server1",job="new"} 1024
    disk_usage{host="server1",job="new"} 512
    network_rx{host="server1",interface="eth0"} 1000000
    network_tx{host="server1",interface="eth0"} 500000'
    ```

4. Query the inserted data from Victoria DB:

    ```bash title="Run on omnia_core container"
    curl --cacert ca.crt -s \
      "https://vmselect.telemetry.svc.cluster.local:8481/select/0/prometheus/api/v1/query?query=new_metric"

    curl --cacert ca.crt -s \
      "https://vmselect.telemetry.svc.cluster.local:8481/select/0/prometheus/api/v1/query_range?query=cpu_usage&start=$(date -d '1 hour ago' +%s)&end=$(date +%s)&step=600s"
    ```


## Collect Logs to VictoriaLogs


### Step 1: Obtain Endpoint Information

Retrieve the VLAgent endpoint information from the VictoriaLogs deployment.

1. Check the `vlagent` LoadBalancer service to get the external IP:

    ```bash title="Run on K8s control plane"
    kubectl get svc vlagent -n telemetry
    ```

2. Record the following endpoints:

    - **Syslog plaintext**: `<LoadBalancer IP>:514`
    - **Syslog TLS**: `<LoadBalancer IP>:6514`
    - **HTTP forwarder**: `https://<LoadBalancer IP>:9481/insert/jsonline`

3. Retrieve the TLS CA certificate from the `victoria-tls-certs` secret:

    ```bash title="Run on K8s control plane"
    kubectl get secret victoria-tls-certs -n telemetry -o jsonpath='{.data.ca\.crt}' | base64 -d > victoria-ca.crt
    ```

!!! note

    VLAgent provides platform-managed syslog receivers. No additional configuration is needed on the Omnia side.

### Step 2: Configure Syslog Sources

Configure external devices to send syslog messages to VLAgent.

**Plaintext Syslog (Port 514)**

1. Access the configuration interface of your log source device.
2. Configure syslog forwarding to the VLAgent plaintext endpoint.

    Example configuration:

    ```text
    Syslog server: <LoadBalancer IP>
    Port: 514
    Protocol: TCP or UDP
    ```

!!! note

    DNS mapping may be required in some devices for TLS certificate validation. Use the LoadBalancer IP if DNS is not configured.

**TLS Syslog (Port 6514)**

1. Copy the VictoriaLogs CA certificate to the log source device.
2. Access the configuration interface of your log source device.
3. Configure syslog forwarding to the VLAgent TLS endpoint.

    Example configuration:

    ```text
    Syslog server: <LoadBalancer IP>
    Port: 6514
    Protocol: TCP
    TLS: Enabled
    CA certificate: victoria-ca.crt
    ```

4. Verify TLS handshake:

    ```bash title="Run on external client node"
    openssl s_client -connect <LoadBalancer IP>:6514 -CAfile victoria-ca.crt
    ```

### Step 3: Configure HTTP Forwarding Sources

Configure log sources that support HTTP forwarding to send logs in JSON Lines format to the `vlinsert` endpoint.

1. Configure HTTP log forwarding to the vlinsert endpoint.

    Example configuration:

    ```text
    Endpoint URL: https://<LoadBalancer IP>:9481/insert/jsonline
    Method: POST
    Format: JSON Lines
    Headers:
      Content-Type: application/json
    ```

2. Example JSON Lines payload format:

    ```json
    {"time":"2024-01-01T12:00:00Z","stream":"device-01","_msg":"System started"}
    {"time":"2024-01-01T12:01:00Z","stream":"device-01","_msg":"Connection established"}
    ```

!!! note

    The `vlinsert` endpoint expects one JSON object per line (JSON Lines format).

### Step 4: Verify Log Ingestion

1. Access the VictoriaLogs query interface:

    ```bash title="Run on K8s control plane or omnia_core container"
    curl -k https://<LoadBalancer IP>:9491/select/logsql/query -d 'query="{}"'
    ```

2. Query for logs from a configured source:

    ```text
    query="{_stream='device-01'}"
    ```

3. Verify that logs from the external source appear in the query results.

!!! note

    Query latency depends on time range and data volume. Narrow the time range for faster results.

!!! note

    VictoriaLogs does not return an error when log entries with timestamps outside the configured retention window are submitted. Log entries will be automatically removed from VictoriaLogs after the retention period.


## Next Steps


- [External Kafka](configure_external_kafka.md) -- Stream data from external clients to Kafka.
- [Setup Telemetry](setup_telemetry.md) -- Overview of all telemetry sources.
