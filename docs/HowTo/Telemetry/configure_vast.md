
# Configure VAST Telemetry


Configure VAST Storage to securely stream telemetry metrics and logs to the Service Kubernetes cluster.

## Overview


VAST Telemetry collects storage metrics and logs. VAST Telemetry includes the following components:

### Data Flow

```
VAST Storage Appliances → OTEL Collector → vmagent (shared) → VictoriaMetrics
VAST Storage Appliances → syslog → VLAgent → VictoriaLogs
```

### Components

- **VAST Prometheus Exporter** -- Exposes storage metrics on a Prometheus-compatible HTTPS endpoint (default port 443).
- **vmagent (shared)** -- Scrapes the VAST Prometheus exporter endpoint over TLS and forwards metrics to VictoriaMetrics.
- **VMServiceScrape CR** -- Kubernetes custom resource that declares the VAST scrape target for the VictoriaMetrics operator.
- **VLAgent** -- Receives VAST syslog events (RFC 3164/5424) and forwards them to VictoriaLogs.
- **Kubernetes Service + Endpoints** -- Abstracts the external VAST appliance as a discoverable Kubernetes service for vmagent.

### Supported Metrics and Logs

**Metrics:**

- **Storage Performance** -- Read/write throughput (bytes/sec), IOPS per volume, latency metrics
- **Capacity Metrics** -- Total capacity, used capacity, available capacity, thin provisioning ratios
- **Volume Metrics** -- Volume state, volume performance counters, snapshot metrics
- **Device Metrics** -- Device health status, device performance, device error counters
- **Cluster Health** -- Node status, cluster connectivity, replication status
- **Telemetry Health** -- Scrape success rate, scrape duration, ingest latency

**Logs:**

- **Storage Events** -- Volume creation/deletion events, snapshot events, capacity threshold alerts
- **System Events** -- Node health events, cluster state changes, replication events
- **Alarm Events** -- Critical alarms, warning alarms, informational events
- Events are labeled with hostname, severity, and facility

!!! note

    VAST Telemetry supports independent feature flags for metric collection and log collection. You can enable or disable each independently.


## Prerequisites


- `telemetry_config.yml` has the entries specific for VAST Telemetry deployment enabled. For details, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).
- `provision.yml` has been executed successfully with `service_kube_control_plane` and `service_kube_node` in the mapping file.
- The service Kubernetes cluster has sufficient resources to run vmagent (shared instance) and VLAgent.
- Network connectivity between the service Kubernetes cluster and the VAST Storage appliance.

**For VAST metrics collection**, configure the following on the VAST appliance:

- **Enable VAST Telemetry** -- Ensure VAST Telemetry is enabled in the VAST cluster configuration.
- **Verify Prometheus endpoint** -- Confirm that the VAST Prometheus exporter is accessible at:

    ```
    https://<vast_ip>:443/api/prometheusmetrics/all
    https://<vast_ip>:443/api/prometheusmetrics/views
    https://<vast_ip>:443/api/prometheusmetrics/devices
    https://<vast_ip>:443/api/prometheusmetrics/alarms
    ```

- **Configure SSL certificates (optional)** -- If using CA-signed TLS, set up SSL and CA certificates. For details, see [VAST Data Documentation - Security Configuration](https://support.vastdata.com/s/).

**For VAST log collection**, configure the following on the VAST appliance:

1. From the left navigation menu, select **Settings > Notifications**.
2. Select **Syslog Setup** and complete the fields:
    - **Syslog Host**: Enter the VLAgent LoadBalancer IP address
    - **Syslog Port**: Enter 514 (default)
    - **Syslog Protocol**: Select UDP or TCP based on your requirements
3. Click **Save**.

For detailed information on VAST syslog configuration parameters, see [VAST Data Documentation - Default Notification Actions](https://kb.vastdata.com/documentation/docs/default-notification-actions-6).

**Set VLAgent LoadBalancer IP** -- Retrieve the VLAgent external IP:

```bash title="Run on K8s control plane"
kubectl get svc -n telemetry | grep vlagent
```


## Procedure


1. **Ensure that `telemetry_config.yml` has the entries specific for VAST Telemetry deployment enabled**. For details, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

    ```yaml title="telemetry_config.yml -- VAST section"
    telemetry_sources:
      vast:
        metrics_enabled: true
        logs_enabled: true
        collection_targets:
          - "victoria_metrics"
          - "victoria_logs"

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

    - `metrics_enabled` -- Enable or disable VAST metric collection (`true` or `false`).
    - `logs_enabled` -- Enable or disable VAST log collection (`true` or `false`).
    - `collection_targets` -- Define where VAST data is sent. Supported values: `victoria_metrics`, `victoria_logs`.
    - `vast_endpoint` -- IP address or hostname of the VAST Storage appliance.
    - `vast_metrics_port` -- Port for the VAST Prometheus exporter (default: `443`).
    - `metrics_path` -- URL path for Prometheus metrics endpoint.
    - `scrape_interval` / `scrape_timeout` -- How often and how long to scrape VAST metrics.
    - `tls_mode` -- TLS verification mode: `self_signed` or `ca_signed`.
    - `vast_ca_cert_path` -- Path to the CA certificate (required when `tls_mode` is `ca_signed`).
    - `auth_mode` -- Authentication mode for VAST API: `basic`.

!!! important

    If you enable VAST telemetry after the initial deployment, execute the `telemetry.sh` script on the K8s control plane:

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Verification


### Verify VAST Telemetry Pods

1. Verify that the VictoriaMetrics pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Pods](../../assets/images/vast_telemetry_1.png)

2. Verify that the VictoriaMetrics service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Service](../../assets/images/vast_telemetry_2.png)
    ![VictoriaMetrics Service Detail](../../assets/images/vast_telemetry_3.png)

3. Verify VMagent logs for VAST scraping to view recent logs:

    ```bash title="Run on K8s control plane"
    VMAGENT_POD=$(kubectl get pods -n telemetry -l app.kubernetes.io/name=vmagent -o jsonpath='{.items[0].metadata.name}')
    kubectl logs $VMAGENT_POD -n telemetry -c vmagent --tail=10
    ```

    ![VMAgent VAST Logs](../../assets/images/vast_telemetry_4.png)


### View VAST Metrics in VictoriaMetrics UI (VMUI)

Use the VMUI to validate that VAST telemetry data is being collected.

1. Note the **External IP** and **port number** of the VictoriaMetrics service:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vmselect
    ```

    ![vmselect Service](../../assets/images/vast_telemetry_5.png)

2. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

    ![VMUI for VAST](../../assets/images/vast_telemetry_7.png)

### View VAST Logs in VictoriaLogs

1. Retrieve the VLAgent LoadBalancer IP and configure it on the VAST appliance:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep -E "(vlagent|victoria-logs)"
    ```

    ![VLAgent Service](../../assets/images/view_vast_logs_1.png)

2. Retrieve the external IP and port of the vlselect service:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vlselect
    ```

    ![vlselect Service](../../assets/images/view_vast_logs_3.png)

3. Access the VictoriaLogs UI in a web browser:

    ```
    https://<external vlselect loadbalancer IP>:9471/select/vmui
    ```

    ![VAST Logs in VictoriaLogs](../../assets/images/view_vast_logs_4.png)


## Next Steps


- [Telemetry Overview](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
