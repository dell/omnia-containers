# Collect Telemetry Data from External Clients to VictoriaMetrics

Send metrics from an external client to the VictoriaMetrics cluster deployed
in the Service Kubernetes cluster.

## Overview

External clients write metrics through the VictoriaMetrics `vminsert`
LoadBalancer and query them through the `vmselect` LoadBalancer. The
`external_victoria` utility validates VictoriaMetrics, discovers the
project-specific endpoints, detects TLS, and exports the CA certificate when
TLS is enabled.

## Prerequisites

- Deploy VictoriaMetrics through the Telemetry workflow.
- Ensure the VictoriaMetrics pods are Running in the `telemetry` namespace.
- Ensure `vminsert-victoria-cluster` and `vmselect-victoria-cluster` have
  LoadBalancer external IP addresses.
- External access to VictoriaMetrics is available through:

    - LoadBalancer port `8480` for ingesting (inserting) data.
    - LoadBalancer port `8481` for querying data.

- Ensure the external client can reach the vminsert and vmselect ports.
- Ensure the OIM can reach the Kubernetes VIP over root SSH.
- Export `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` for the project whose
  connection details must be retrieved.

## Procedure

### Step 1: Retrieve VictoriaMetrics Connection Details

1. Retrieve the Victoria connection details. Choose one execution method; do
   not run both commands for the same operation.

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd src/main
        ./omnia.sh --run telemetry --tags external_victoria
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source "$OMNIA_DATA_PATH/activate-omnia.sh"
        cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
        ansible-playbook telemetry.yml --tags external_victoria
        ```

2. Review the project-specific output:

    ```text
    $OMNIA_DATA_PATH/telemetry/output/$OMNIA_PROJECT_NAME/external_victoria/
    |-- ca.crt    # Present only when TLS is enabled
    `-- external_victoria_connect_details.yml
    ```

    In a multi-domain environment, always use the output below the applicable
    `OMNIA_PROJECT_NAME`. The file provides these VictoriaMetrics values:

    - `victoria_metrics.endpoints.vminsert.write_endpoint`
    - `victoria_metrics.endpoints.vmselect.query_endpoint`
    - `victoria_metrics.endpoints.vmselect.ui_url`
    - `victoria_metrics.tls.ca_crt`

    The generated endpoint scheme is `https` when the
    `victoria-tls-certs` Secret exists and `http` otherwise.

### Step 2: Validate VictoriaMetrics from an External Client

1. Add the LoadBalancer insert and select IP addresses to `/etc/hosts`:

    ```bash title="Run on external client node"
    echo "<vminsert-IP> vminsert.telemetry.svc.cluster.local" >> /etc/hosts
    echo "<vmselect-IP> vmselect.telemetry.svc.cluster.local" >> /etc/hosts
    ```

    For `vminsert` and `vmselect` IP, use the values retrieved by the `external_victoria_connect_details.yml` playbook.

    !!! note

        The `/etc/hosts` update must be repeated if the SFM Prometheus pod restarts.

2. Create a new test metric:

    ```bash title="Run on external client node"
    curl --cacert ca.crt -X POST \
      "https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/import/prometheus" \
      -H "Content-Type: text/plain" \
      -d "test_metric{source=\"external\"} 42"
    ```

    !!! note

        Use `https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write` to push metrics from an external client such as [Smart Fabric Manager (SFM)](https://www.dell.com/en-in/shop/ipovw/smartfabric-manager-for-sonic){target="_blank"}.

3. Push sample test metrics to VictoriaMetrics:

    ```bash title="Run on external client node"
    curl --cacert /opt/omnia/telemetry/victoria-certs/ca.crt -X POST \
      "https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/import/prometheus" \
      -H "Content-Type: text/plain" \
      -d 'cpu_usage{host="server1",job="new"} 75.5
    memory_usage{host="server1",job="new"} 1024
    disk_usage{host="server1",job="new"} 512
    network_rx{host="server1",interface="eth0"} 1000000
    network_tx{host="server1",interface="eth0"} 500000'
    ```

## Verification

### Verify Metrics in VictoriaMetrics

Query the inserted data from VictoriaMetrics to verify that metrics were ingested successfully:

1. Query a single metric:

    ```bash title="Run on external client node"
    curl --cacert ca.crt -s \
      "https://vmselect.telemetry.svc.cluster.local:8481/select/0/prometheus/api/v1/query?query=test_metric"
    ```

2. Query a range of metrics:

    ```bash title="Run on external client node"
    curl --cacert ca.crt -s \
      "https://vmselect.telemetry.svc.cluster.local:8481/select/0/prometheus/api/v1/query_range?query=cpu_usage&start=$(date -d '1 hour ago' +%s)&end=$(date +%s)&step=600s"
    ```

3. Verify that the query results contain the metrics pushed in the previous steps.

## Troubleshooting

- **No VictoriaMetrics pods are found:** Enable a metrics route and deploy
  Telemetry.
- **A pod is not Running:** Inspect the VictoriaMetrics pods in the
  `telemetry` namespace before rerunning the export.
- **An external IP is missing:** Assign external IP addresses to the vminsert
  and vmselect LoadBalancer services.
- **Certificate validation fails:** Use the `ca.crt` from the same project's
  latest export; do not reuse a certificate from another domain.
- **The VIP cannot be reached:** Restore root SSH access from the OIM to the
  configured Kubernetes VIP.

## Next steps

- Use the exported values to [connect SFM](configure_sfm.md) or another metrics
  producer.
- Use [Collect Logs from External Clients to VictoriaLogs](configure_external_victoria_logs.md)
  for log ingestion and syslog endpoints exported by the same utility.
