
# Configure UFM Telemetry


Configure NVIDIA Unified Fabric Manager (UFM) to securely stream telemetry metrics and logs to the Service Kubernetes cluster.

## Overview


UFM Telemetry collects InfiniBand fabric metrics and logs. UFM Telemetry includes the following components:

### Data Flow

```
UFM Fabric Manager → OTEL Collector → vmagent (shared) → VictoriaMetrics
UFM Fabric Manager → syslog → VLAgent → VictoriaLogs
```

### Components

- **UFM Prometheus Exporter** -- Exposes InfiniBand fabric metrics on a Prometheus-compatible HTTPS endpoint (default port 9001).
- **vmagent (shared)** -- Scrapes the UFM Prometheus exporter endpoint over TLS and forwards metrics to VictoriaMetrics.
- **VMServiceScrape CR** -- Kubernetes custom resource that declares the UFM scrape target for the VictoriaMetrics operator.
- **VLAgent** -- Receives UFM syslog events (RFC 3164/5424) and forwards them to VictoriaLogs.
- **Kubernetes Service + Endpoints** -- Abstracts the external UFM appliance as a discoverable Kubernetes service for vmagent.

### Supported Metrics and Logs

**Metrics:**

- **Port State** -- InfiniBand port operational state (up, down, disabled)
- **Traffic Counters** -- Transmit/receive data rates (bytes/sec), packet counts per port
- **Error Counters** -- Symbol errors, link error recovery, link downed, VL15 dropped, excessive buffer overrun errors
- **Fabric Topology** -- Switch information, port mapping, node GUIDs, LID assignments
- **Telemetry Health** -- Scrape success rate, scrape duration, ingest latency

**Logs:**

- Fabric topology change events, port state transitions, error/warning messages
- SM (Subnet Manager) events, SHARP events, UFM health events
- Events are labeled with hostname, severity, and facility

!!! note

    UFM Telemetry supports independent feature flags for metric collection and log collection. You can enable or disable each independently.


## Prerequisites


- `provision.yml` has been executed successfully with `service_kube_control_plane` and `service_kube_node` in the mapping file.
- The service Kubernetes cluster has sufficient resources to run vmagent (shared instance) and VLAgent.
- Network connectivity between the service Kubernetes cluster and the NVIDIA UFM appliance.
- `telemetry_config.yml` has the entries specific for UFM Telemetry deployment enabled. For details, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

**For UFM metrics collection, configure the following on the UFM appliance:**

- **Enable UFM Telemetry** -- Ensure UFM Telemetry is enabled in the `gv.cfg` configuration file:

    ```ini
    [Telemetry]
    telemetry_provider = telemetry
    ```

- **Verify Prometheus endpoint** -- Confirm that the UFM Prometheus exporter is accessible at `https://<ufm_ip>:9001/metrics`.
- **Configure SSL certificates (optional)** -- If using CA-signed TLS, set up SSL and CA certificates in UFM. For detailed steps, see [Setting Up SSL and CA Certificates in UFM](https://docs.nvidia.com/networking/display/ufmenterpriseumv6242/optional-configurations).

**For UFM log collection, configure the following on the UFM appliance:**

**Using the UFM Web UI:**

1. From the left navigation menu, select **Settings > Data Streaming**.
2. Select **System log** and complete the fields:
    - **Destination**: Enter the VLAgent LoadBalancer IP address
    - **Syslog Port**: Enter 514 (default)
    - **System logs Level**: Select syslog level from the dropdown based on your requirements
    - **Streaming Data**: Select UFM logs
3. Click **Save**.

**Using the UFM CLI:**

Modify the `[Logging]` section in `/opt/ufm/conf/gv.cfg`:

```ini
[Logging]
syslog = true
syslog_addr = <external vlagent loadbalancer IP>:514
ufm_syslog = true
event_syslog = true
syslog_level = WARNING
```

For detailed information on UFM syslog configuration parameters, see [NVIDIA UFM Enterprise User Manual - Configuring Syslog](https://docs.nvidia.com/networking/display/ufmenterpriseumv6242/optional-configurations#src-4813172567_OptionalConfigurations-ConfiguringSyslog).

**Set VLAgent LoadBalancer IP** -- Retrieve the VLAgent external IP:

```bash title="Run on K8s control plane"
kubectl get svc -n telemetry | grep vlagent
```


## Procedure


1. **Ensure that `telemetry_config.yml` has the entries specific for UFM Telemetry deployment enabled**. For details, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

    ```yaml title="telemetry_config.yml -- UFM section"
    telemetry_sources:
      ufm:
        metrics_enabled: true
        logs_enabled: true
        collection_targets:
          - "victoria_metrics"
          - "victoria_logs"

    ufm_configuration:
      ufm_endpoint: ""
      ufm_metrics_port: 9001
      scrape_interval: "30s"
      scrape_timeout: "15s"
      tls_mode: "self_signed"
      ufm_ca_cert_path: ""
      auth_mode: "basic"
    ```

    - `metrics_enabled` -- Enable or disable UFM metric collection (`true` or `false`).
    - `logs_enabled` -- Enable or disable UFM log collection (`true` or `false`).
    - `collection_targets` -- Define where UFM data is sent. Supported values: `victoria_metrics`, `victoria_logs`.
    - `ufm_endpoint` -- IP address or hostname of the UFM appliance.
    - `ufm_metrics_port` -- Port for the UFM Prometheus exporter (default: `9001`).
    - `scrape_interval` / `scrape_timeout` -- How often and how long to scrape UFM metrics.
    - `tls_mode` -- TLS verification mode: `self_signed` or `ca_signed`.
    - `ufm_ca_cert_path` -- Path to the CA certificate (required when `tls_mode` is `ca_signed`).
    - `auth_mode` -- Authentication mode for UFM API: `basic`.

!!! important

    If you enable UFM telemetry after the initial deployment, execute the `telemetry.sh` script on the K8s control plane:

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Verification


### Verify UFM Telemetry Pods

1. Verify that the VictoriaMetrics pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Pods](../../assets/images/verify_umf_telemetry_1.png)

2. Verify that the VictoriaMetrics service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Service](../../assets/images/verify_umf_telemetry_2.png)

3. Verify VMagent logs for UFM scraping to view recent logs:

    ```bash title="Run on K8s control plane"
    VMAGENT_POD=$(kubectl get pods -n telemetry -l app.kubernetes.io/name=vmagent -o jsonpath='{.items[0].metadata.name}')
    kubectl logs $VMAGENT_POD -n telemetry -c vmagent --tail=50
    ```

    ![VMAgent UFM Logs](../../assets/images/verify_umf_telemetry_3.png)


### View UFM Metrics in VictoriaMetrics UI (VMUI)

Use the VMUI to validate that UFM telemetry data is being collected.

1. Note the **External IP** and **port number** of the VictoriaMetrics service:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vmselect
    ```

    ![vmselect Service](../../assets/images/verify_umf_telemetry_4.png)

2. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/vmui
    ```

    ![VMUI for UFM](../../assets/images/verify_umf_telemetry_5.png)

3. Filter and view UFM InfiniBand metrics using queries in VMUI. For example:

    ```
    {source="ufm", subsystem="infiniband"}
    ```

### View UFM Logs in VictoriaLogs

1. Retrieve the VLAgent LoadBalancer IP and configure it on the UFM appliance:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep -E "(vlagent|victoria-logs)"
    ```

    ![VLAgent Service](../../assets/images/view_umf_telemetry_1.png)

2. Retrieve the external IP and port of the vlselect service:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vlselect
    ```

    ![vlselect Service](../../assets/images/view_umf_telemetry_2.png)

3. Access the VictoriaLogs UI in a web browser:

    ```
    https://<external vlselect loadbalancer IP>:9471/select/0/vmui
    ```

    ![UFM Logs in VictoriaLogs](../../assets/images/view_umf_telemetry_3.png)


## Next Steps


- [Telemetry Overview](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
