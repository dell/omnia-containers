# Configure UFM Telemetry

Configure NVIDIA Unified Fabric Manager (UFM) to securely stream Telemetry
metrics and logs to the Service Kubernetes cluster.

## Overview

UFM Telemetry collects InfiniBand fabric metrics and logs from an existing
NVIDIA UFM appliance.

### Components

- **UFM Prometheus Exporter** -- Exposes InfiniBand metrics over a
  Prometheus-compatible HTTPS endpoint. The default port is `9001`.
- **vmagent (shared)** -- Scrapes the UFM exporter over TLS and forwards the
  metrics to VictoriaMetrics.
- **VMServiceScrape** -- Defines the UFM scrape target, authentication, TLS,
  interval, and timeout for vmagent.
- **VLAgent** -- Receives RFC 3164 or RFC 5424 syslog messages from UFM and
  sends them to VictoriaLogs.
- **Kubernetes Service and Endpoints** -- Represent the external UFM appliance
  as the `ufm-external` service in the `telemetry` namespace.

Omnia does not deploy or configure the UFM appliance.

### Data flow

```text
UFM Fabric Manager -> UFM Prometheus Exporter -> vmagent (shared) -> VictoriaMetrics
UFM Fabric Manager -> syslog -> VLAgent -> VictoriaLogs
```

### Supported metrics and logs

| Metrics category | Metrics collected |
|---|---|
| Port state | InfiniBand port operational state, including up, down, and disabled |
| Traffic counters | Transmit and receive rates, bytes per second, and packets per port |
| Error counters | Symbol errors, link recovery and link-down events, VL15 drops, and excessive buffer overruns |
| Fabric topology | Switch information, port mappings, node GUIDs, and LIDs |
| Telemetry health | Scrape success, scrape duration, and ingestion latency |

For the complete list, see the
[UFM Metrics reference](../../Reference/Metrics/ufm_metrics.md).

| Log category | Logs collected |
|---|---|
| Fabric events | Topology changes, port transitions, errors, and warnings |
| Manager events | Subnet Manager, SHARP, and UFM health events |
| Labels | Hostname, severity, and facility metadata |

UFM metrics and logs are controlled independently by `metrics_enabled` and
`logs_enabled`.

## Prerequisites

- Complete the common [Telemetry deployment prerequisites](deploy_telemetry.md#prerequisites).
- Ensure the service Kubernetes cluster has sufficient resources to run
  vmagent (shared instance) and VLAgent.
- Ensure network connectivity between the service Kubernetes cluster and the
  NVIDIA UFM appliance.
- Ensure that an NVIDIA UFM appliance is running. Omnia does not deploy UFM.
- Ensure that `telemetry_config.yml` has UFM telemetry entries enabled. For
  details, see the
  [telemetry configuration reference](../../Reference/Configuration/telemetry_config.md).
- UFM telemetry must bind and listen on a specific designated IP address
  rather than the default localhost (`127.0.0.1`).
- Allow ports `9000`, `9001`, and `9002` through the `firewalld` service on the
  UFM appliance. Create and enable the required firewall rules before
  deployment.
- Deploy UFM with self-signed SSL/TLS certificates and configure it to listen
  on a specific IP address and designated port for secure communication.
- Provide a UFM IP address that the Kubernetes cluster can reach.
- Enable the UFM Prometheus endpoint on the appliance and know its port.
- For basic authentication, provide `ufm_username` and `ufm_password` when
  prompted.
- For CA-signed TLS, place the PEM CA certificate on the OIM and record its
  path.

## Procedure

### Step 1: Configure the UFM Appliance

Enable UFM Telemetry in the `gv.cfg` configuration file on the UFM appliance:

```ini
[Telemetry]
telemetry_provider = telemetry
```

**(Optional) Configure SSL certificates** -- If using CA-signed TLS, set up SSL and CA certificates in UFM. For detailed steps, see [Setting Up SSL and CA Certificates in UFM](https://docs.nvidia.com/networking/display/ufmenterpriseumv6242/optional-configurations).

### Step 2: Configure UFM Log Forwarding

To collect UFM logs, configure syslog forwarding on the UFM appliance. First, retrieve the VLAgent LoadBalancer IP:

```bash title="Run on K8s control plane"
kubectl get svc -n telemetry | grep vlagent
```

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

### Step 3: Configure UFM Telemetry

1. Enable UFM metrics and VictoriaMetrics in `telemetry_config.yml`:

    ```yaml
    telemetry_sources:
      ufm:
        metrics_enabled: true
        logs_enabled: false
        collection_targets:
          - victoria_metrics

    ufm_configuration:
      ufm_endpoint: "172.20.44.180"
      ufm_metrics_port: 9001
      scrape_interval: "30s"
      scrape_timeout: "15s"
      tls_mode: "self_signed"
      ufm_ca_cert_path: ""
      auth_mode: "basic"
    ```

    `tls_mode` accepts `self_signed` or `ca_signed`; `auth_mode` accepts
    `basic` or `none`. When `ca_signed` is selected, set
    `ufm_ca_cert_path` to the PEM file.

### Step 4: Validate and Deploy UFM Telemetry

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

## Verification

### Verify UFM Telemetry pods

1. Verify that the VictoriaMetrics pods are running:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get pods -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics pods](../../assets/images/verify_umf_telemetry_1.png)

2. Verify that the VictoriaMetrics services are running:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get service -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics services](../../assets/images/verify_umf_telemetry_2.png)

3. Check the shared vmagent logs for successful UFM scrapes:

    ```bash title="Run on: Kubernetes control plane"
    VMAGENT_POD=$(kubectl get pods -n telemetry \
      -l app.kubernetes.io/name=vmagent \
      -o jsonpath='{.items[0].metadata.name}')
    kubectl logs "$VMAGENT_POD" -n telemetry -c vmagent --tail=50
    ```

    ![vmagent logs](../../assets/images/verify_umf_telemetry_3.png)

### View UFM metrics in VictoriaMetrics UI

1. Identify the external `vmselect` service:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get svc -n telemetry | grep vmselect
    ```

    ![vmselect service](../../assets/images/verify_umf_telemetry_4.png)

2. Export the VictoriaMetrics connection details:

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

3. Open the URL recorded in `victoria_metrics.endpoints.vmselect.ui_url` in
   the following file:

    ```text
    $OMNIA_DATA_PATH/telemetry/output/$OMNIA_PROJECT_NAME/external_victoria/external_victoria_connect_details.yml
    ```

4. Query a UFM metric, such as `infiniband_CBW`, to confirm that UFM metrics
   are reaching VictoriaMetrics. To filter InfiniBand metrics by their source
   labels, use:

    ```promql
    {source="ufm", subsystem="infiniband"}
    ```

    ![UFM metrics in VMUI](../../assets/images/verify_umf_telemetry_5.png)

### View UFM logs in VictoriaLogs

Complete these steps only when UFM log collection is enabled.

1. Verify that VLAgent and VictoriaLogs services are running:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get svc -n telemetry | grep -E '(vlagent|victoria-logs)'
    ```

    ![VLAgent and VictoriaLogs services](../../assets/images/view_umf_telemetry_1.png)

2. Identify the external `vlselect` service:

    ```bash title="Run on: Kubernetes control plane"
    kubectl get svc -n telemetry | grep vlselect
    ```

    ![vlselect service](../../assets/images/view_umf_telemetry_2.png)

3. If needed, export the Victoria connection details by using either command
   shown in step 2 of the previous section. Open the URL recorded in
   `victoria_logs.endpoints.vlselect.ui_url` in:

    ```text
    $OMNIA_DATA_PATH/telemetry/output/$OMNIA_PROJECT_NAME/external_victoria/external_victoria_connect_details.yml
    ```

4. Query `ufm` to confirm that UFM logs are reaching VictoriaLogs.

    ![UFM logs in VictoriaLogs](../../assets/images/view_umf_telemetry_3.png)

Confirm `sources.ufm.metrics: deployed` in `telemetry_status.yml`. This status
records the integration resource state; successful metric queries provide the
end-to-end validation. When logs are enabled, `sources.ufm.logs: deployed`
confirms that VLAgent is running; a successful log query confirms that the UFM
appliance has begun sending logs.

## Next steps

- Use [Export VictoriaMetrics Connection Details](configure_external_victoria.md)
  to obtain the query endpoint and UI URL.

## Troubleshooting

- **The endpoint is rejected:** Set a non-empty UFM IP address and a port from
  `1` through `65535`.
- **Credentials are missing:** Supply UFM credentials when `auth_mode: basic`.
- **Credentials are requested with `auth_mode: none`:** The current credential
  collection is gated by enabled UFM metrics, not by `auth_mode`. Complete the
  prompt while this source behavior remains in place.
- **The CA file is rejected:** With `tls_mode: ca_signed`, provide an existing
  PEM certificate path on the OIM.
- **Deployment fails with `auth_mode: none` and self-signed TLS:** The current
  source can render an empty Secret while still attempting to apply it. Use
  basic authentication or CA-signed TLS until that source limitation is fixed.
- **No metrics arrive:** Confirm the UFM endpoint is reachable from Kubernetes
  and that its authentication, TLS mode, scrape interval, and timeout are
  correct.
- **Logs do not arrive:** Confirm that UFM is sending to the exported VLAgent
  syslog endpoint and that `victoria_logs` remains in its collection targets.
