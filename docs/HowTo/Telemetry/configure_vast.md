# Configure VAST Telemetry

Configure VAST Storage to securely stream Telemetry metrics and logs to the
Service Kubernetes cluster.

## Overview

VAST Telemetry collects storage metrics and logs from an existing VAST Storage
system.

### Components

- **VAST Prometheus Exporter** -- Exposes storage metrics through a
  Prometheus-compatible HTTPS endpoint. The default port is `443`.
- **vmagent (shared)** -- Scrapes the VAST Prometheus endpoint over TLS and
  forwards metrics to VictoriaMetrics.
- **VMServiceScrape** -- Declares the VAST scrape target for the
  VictoriaMetrics operator.
- **VLAgent** -- Receives RFC 3164 or RFC 5424 syslog events from VAST and
  forwards them to VictoriaLogs.
- **Kubernetes Service and Endpoints** -- Represent the external VAST system
  as the `vast-external` service in the `telemetry` namespace.

Omnia does not deploy or configure the VAST system.

### Data flow

```text
VAST Storage system -> VAST Prometheus Exporter -> vmagent (shared) -> VictoriaMetrics
VAST Storage system -> syslog -> VLAgent -> VictoriaLogs
```

### Supported metrics and logs

| Metrics category | Metrics collected |
|---|---|
| Storage performance | Read and write throughput, IOPS per volume, and latency |
| Capacity | Total, used, and available capacity and thin-provisioning ratios |
| Volume | Volume state, performance counters, and snapshot metrics |
| Device | Device health, performance, and error counters |
| Cluster health | Node status, cluster connectivity, and replication status |
| Telemetry health | Scrape success, scrape duration, and ingestion latency |

For the complete list, see the
[VAST Metrics reference](../../Reference/Metrics/vast_metrics.md).

| Log category | Logs collected |
|---|---|
| Storage events | Volume creation or deletion, snapshot events, and capacity threshold alerts |
| System events | Node health, cluster state changes, and replication events |
| Alarm events | Critical, warning, and informational alarms |
| Labels | Hostname, severity, and facility metadata |

The configuration provides separate flags for metrics and logs. In the current
deployment workflow, keep `metrics_enabled: true` when collecting VAST logs
because VAST source deployment is gated by the metrics flag.

## Prerequisites

- Complete the common [Telemetry deployment prerequisites](deploy_telemetry.md#prerequisites).
- Provide a VAST endpoint that the Kubernetes cluster can reach.
- Enable the VAST Prometheus metrics API and know its port and path.
- For basic authentication, provide `vast_username` and `vast_password` when
  prompted.
- For CA-signed TLS, place the PEM CA certificate on the OIM and record its
  path.

## Procedure

### Step 1: Configure the VAST Appliance

Verify that the VAST Prometheus exporter endpoints are accessible:

```text
https://<vast_ip>:443/api/prometheusmetrics/all
https://<vast_ip>:443/api/prometheusmetrics/views
https://<vast_ip>:443/api/prometheusmetrics/devices
https://<vast_ip>:443/api/prometheusmetrics/alarms
```

**(Optional) Configure SSL certificates** -- If using CA-signed TLS, set up SSL and CA certificates. For details, see [VAST Data Documentation - Security Configuration](https://support.vastdata.com/s/).

### Step 2: Configure VAST Telemetry

1. Enable VAST metrics and VictoriaMetrics in `telemetry_config.yml`:

    ```yaml
    telemetry_sources:
      vast:
        metrics_enabled: true
        logs_enabled: false
        collection_targets:
          - victoria_metrics

    vast_configuration:
      vast_endpoint: "172.18.44.171"
      vast_metrics_port: 443
      metrics_path: "/api/prometheusmetrics/all"
      scrape_interval: "30s"
      scrape_timeout: "15s"
      tls_mode: "self_signed"
      vast_ca_cert_path: ""
      auth_mode: "basic"
    ```

    `tls_mode` accepts `self_signed` or `ca_signed`; `auth_mode` accepts
    `basic` or `none`. When `ca_signed` is selected, set
    `vast_ca_cert_path` to the PEM file.

### Step 3: Validate and Deploy VAST Telemetry

1. Run the Telemetry precheck. Choose one execution method; do not run both
   commands for the same operation.

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd src/main
        ./omnia.sh --run telemetry --tags precheck
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd src/telemetry
        ansible-playbook playbooks/telemetry.yml --tags precheck
        ```

2. Validate the Telemetry inputs and collect the required credentials:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd src/main
        ./omnia.sh --run telemetry --tags validate
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd src/telemetry
        ansible-playbook playbooks/telemetry.yml --tags validate
        ```

3. Deploy the enabled Telemetry configuration:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd src/main
        ./omnia.sh --run telemetry --tags deploy
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd src/telemetry
        ansible-playbook playbooks/telemetry.yml --tags deploy
        ```

4. To run validation and deployment in one invocation, omit the tag:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd src/main
        ./omnia.sh --run telemetry
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd src/telemetry
        ansible-playbook playbooks/telemetry.yml
        ```

    The untagged flow does not run the opt-in precheck. Run step 1 separately
    when an environment precheck is required.

### Step 4: Configure VAST Log Forwarding (Optional)

To collect VAST logs:

1. Keep metrics enabled, set `logs_enabled: true`, add `victoria_logs` to
   `collection_targets`, and deploy Telemetry. The source role is imported only
   when metrics are enabled; a logs-only configuration is not supported.

2. Export the VLAgent target. Choose one execution method; do not run both
   commands for the same operation.

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd src/main
        ./omnia.sh --run telemetry --tags external_victoria
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd src/telemetry
        ansible-playbook playbooks/telemetry.yml --tags external_victoria
        ```

3. Retrieve the VLAgent LoadBalancer IP:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vlagent
    ```

4. From the left navigation menu of the VAST appliance, select
   **Settings > Notifications**.

5. Select **Syslog Setup** and complete the fields:

    - **Syslog Host**: Enter the VLAgent LoadBalancer IP address
    - **Syslog Port**: Enter 514 (default)
    - **Syslog Protocol**: Select UDP or TCP based on your requirements

6. Click **Save**.

For detailed information on VAST syslog configuration parameters, see
[VAST Data Documentation - Default Notification Actions](https://kb.vastdata.com/documentation/docs/default-notification-actions-6).

Configure the existing VAST system to send logs to the generated
`vlagent.syslog_endpoint`. The Telemetry source exposes this endpoint but does
not configure VAST itself.

VAST log forwarding is an external system configuration step; the Telemetry
source does not deploy a VAST log collector.

## Verification

### Verify VAST Telemetry resources

1. Verify that the VictoriaMetrics pods are running:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get pods -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics pods](../../assets/images/vast_telemetry_1.png)

2. Verify that the VictoriaMetrics services are running:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get service -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics services](../../assets/images/vast_telemetry_3.png)

3. Check the shared vmagent logs for recent VAST scrape activity:

    ```bash title="Run on: Kubernetes control plane"
    VMAGENT_POD=$(kubectl get pods -n telemetry \
      -l app.kubernetes.io/name=vmagent \
      -o jsonpath='{.items[0].metadata.name}')
    kubectl logs "$VMAGENT_POD" -n telemetry -c vmagent --tail=10
    ```

    ![vmagent logs](../../assets/images/vast_telemetry_4.png)

4. Confirm that the service for the external VAST system was created:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get service vast-external -n telemetry
    ```

### View VAST metrics in VictoriaMetrics UI

1. Identify the external `vmselect` service:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get svc -n telemetry | grep vmselect
    ```

    ![vmselect service](../../assets/images/vast_telemetry_5.png)

2. Access the VMUI in a web browser:

    ```text
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

3. Query a VAST metric, such as
   `vast_cluster_metrics_EStoreMigrateMetrics_physical_size_count`, to confirm
   that VAST metrics are being collected.

    ![VAST metrics in VMUI](../../assets/images/vast_telemetry_7.png)

### View VAST logs in VictoriaLogs

Complete these steps only when VAST log collection is enabled.

1. Retrieve the VLAgent LoadBalancer IP and configure the VAST system to send
   syslog messages to it:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get svc -n telemetry | grep -E '(vlagent|victoria-logs)'
    ```

    ![VLAgent and VictoriaLogs services](../../assets/images/view_vast_logs_1.png)

2. Identify the external `vlselect` service:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get svc -n telemetry | grep vlselect
    ```

    ![vlselect service](../../assets/images/view_vast_logs_3.png)

3. Access the VictoriaLogs UI in a web browser:

    ```text
    https://<external vlselect loadbalancer IP>:9471/select/vmui
    ```

4. Query the VAST hostnames to confirm that logs are reaching VictoriaLogs.
   For example:

    ```text
    {hostname=~"vast-.*"}
    ```

    ![VAST logs in VictoriaLogs](../../assets/images/view_vast_logs_4.png)

Confirm `sources.vast.metrics: deployed` in `telemetry_status.yml`. This status
records the integration resource state; successful metric queries provide the
end-to-end validation. When logs are enabled, `sources.vast.logs: deployed`
records the configured log path; a successful log query confirms that the VAST
system is sending data.

## Next steps

- Use [Export VictoriaMetrics Connection Details](configure_external_victoria.md)
  to obtain the query endpoint and UI URL.

## Troubleshooting

- **The endpoint is rejected:** Set a non-empty VAST IP address and a port from
  `1` through `65535`.
- **Credentials are missing:** Supply VAST credentials when `auth_mode: basic`.
- **Credentials are requested with `auth_mode: none`:** The current credential
  collection is gated by enabled VAST metrics, not by `auth_mode`. Complete the
  prompt while this source behavior remains in place.
- **The CA file is rejected:** With `tls_mode: ca_signed`, provide an existing
  PEM certificate path on the OIM.
- **Deployment fails with `auth_mode: none` and self-signed TLS:** The current
  source can render an empty Secret while still attempting to apply it. Use
  basic authentication or CA-signed TLS until that source limitation is fixed.
- **No metrics arrive:** Confirm the VAST endpoint and metrics path are
  reachable from Kubernetes and that authentication and TLS settings are
  correct.
- **Logs do not arrive:** Confirm that VAST is sending to the exported VLAgent
  syslog endpoint and that `victoria_logs` remains in its collection targets.
