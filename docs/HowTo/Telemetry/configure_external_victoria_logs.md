# Collect Logs from External Clients to VictoriaLogs


Stream logs from external client nodes (network devices, storage systems, fabric managers) to VictoriaLogs deployed in the Service Kubernetes cluster.

## Overview


This procedure describes how to configure external log sources to send logs to VictoriaLogs (cluster mode) for centralized log collection and analysis.

VictoriaLogs accepts syslog (plaintext and TLS) and HTTP forwarding for log ingestion via the VLAgent LoadBalancer service.


## Prerequisites


This is a post-deployment procedure. The Omnia telemetry stack (including VictoriaLogs) must already be deployed and running before you connect external log sources.

- A Service Kubernetes cluster is running with VictoriaLogs deployed in the `telemetry` namespace.
- `pod_external_ip_range` is set in `omnia_config.yml` so MetalLB can assign an external IP to the VLAgent service.
- Network connectivity exists from external log sources to the Service Kubernetes cluster.
- The TLS CA certificate for VictoriaLogs is available.

!!! important

    Ensure that `pod_external_ip_range` in `omnia_config.yml` is reachable from external log sources.


## Procedure


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


## Verification


### Verify Log Ingestion

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


## Troubleshooting

No troubleshooting information is currently available for this procedure.


## Next Steps


- [External VictoriaMetrics](configure_external_victoria.md) -- Stream metrics from external clients to VictoriaMetrics.
- [External Kafka](configure_external_kafka.md) -- Stream data from external clients to Kafka.
- [Setup Telemetry](setup_telemetry.md) -- Overview of all telemetry sources.
