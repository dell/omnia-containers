# Collect Telemetry Data from External Clients to VictoriaMetrics


Stream telemetry metrics from external client nodes to VictoriaMetrics deployed in the Service Kubernetes cluster.

## Overview


This procedure describes how to configure an external telemetry producer to stream metrics securely into VictoriaMetrics (cluster mode) in the Service Kubernetes cluster using TLS.

VictoriaMetrics accepts Prometheus remote write and import endpoints for metrics ingestion. For more details, see the [VictoriaMetrics Cluster Mode documentation](https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/){target="_blank"}.

!!! note

    For collecting telemetry data from Smart Fabric Manager (SFM) to VictoriaMetrics, see [SFM Telemetry](configure_sfm.md).


## Prerequisites


This is a post-deployment procedure. The Omnia telemetry stack (including VictoriaMetrics) must already be deployed and running before you connect external clients.

- A Service Kubernetes cluster is running with VictoriaMetrics deployed in the `telemetry` namespace.
- `pod_external_ip_range` is set in `omnia_config.yml` so MetalLB can assign external IPs to the `vminsert` and `vmselect` services.
- External access to VictoriaMetrics is available through:
    - LoadBalancer port `8480` for ingesting (inserting) data.
    - LoadBalancer port `8481` for querying data.


## Procedure


### Step 1: Retrieve VictoriaMetrics Connection Details

Run the following playbook to retrieve the VictoriaMetrics connection details and TLS certificate from the Service Kubernetes cluster:

```bash title="Run on omnia_core container"
cd /opt/omnia/telemetry
ansible-playbook external_victoria_connect_details.yml
```

The `external_victoria_connect_details.yml` playbook does the following:

- Retrieves the VictoriaMetrics `vminsert` and `vmselect` LoadBalancer IPs.
- Extracts the server CA certificate for TLS.
- Writes the connection details to `/opt/omnia/telemetry/external_victoria_connect_details.yml`.
- Saves the CA certificate at `/opt/omnia/telemetry/victoria-certs/ca.crt`.

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

        Use `https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write` to push metrics from an external client such as [Smart Fabric Manager (SFM)](https://www.dell.com/en-in/shop/ipovw/smartfabric-manager-for-sonic){target="_blank"}.

3. Push sample test metrics to VictoriaMetrics:

    ```bash title="Run on omnia_core container"
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

    ```bash title="Run on omnia_core container"
    curl --cacert ca.crt -s \
      "https://vmselect.telemetry.svc.cluster.local:8481/select/0/prometheus/api/v1/query?query=test_metric"
    ```

2. Query a range of metrics:

    ```bash title="Run on omnia_core container"
    curl --cacert ca.crt -s \
      "https://vmselect.telemetry.svc.cluster.local:8481/select/0/prometheus/api/v1/query_range?query=cpu_usage&start=$(date -d '1 hour ago' +%s)&end=$(date +%s)&step=600s"
    ```

3. Verify that the query results contain the metrics pushed in the previous steps.


## Next Steps


- [External VictoriaLogs](configure_external_victoria_logs.md) -- Stream logs from external clients to VictoriaLogs.
- [External Kafka](configure_external_kafka.md) -- Stream data from external clients to Kafka.
- [Setup Telemetry](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting

No troubleshooting information is currently available for this procedure.
