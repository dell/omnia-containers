
# Configure SFM Telemetry


Configure Smart Fabric Manager (SFM) to securely stream telemetry metrics to VictoriaMetrics in the Service Kubernetes cluster.

## Overview


SFM collects network telemetry metrics including transceiver DOM readings, queue statistics, interface counters, and error counters from the managed fabric. SFM streams data directly to VictoriaMetrics via Prometheus Remote Write.

### Components

- **SFM Prometheus Exporter** -- Collects network telemetry metrics from the managed fabric and exports them via Prometheus Remote Write.
- **vminsert** -- VictoriaMetrics ingestion endpoint that receives metrics over TLS from SFM.

### Data Flow

```
SFM (Smart Fabric Manager) → Prometheus Remote Write → vminsert → VictoriaMetrics
```

### Supported Metrics

- **Transceiver DOM** -- Optical power (TX/RX), temperature, voltage, bias current
- **Queue Statistics** -- Queue depth, egress queue counters, multicast queue counters
- **Interface Counters** -- Interface throughput (TX/RX bytes), packet counts, error counts, drop counts
- **Error Counters** -- CRC errors, alignment errors, symbol errors, FCS errors


## Prerequisites


- VictoriaMetrics is deployed in cluster mode in the telemetry namespace. For more information, see [VictoriaMetrics cluster mode documentation](https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/).
- `pod_external_ip_range` must be set in `provision_config.yml` and `provision.yml` must be executed after the external IP is configured.
- SFM must be operational and accessible from the service Kubernetes cluster.


## Procedure


### Retrieve VictoriaMetrics Connection Details

1. Log in to the Service Kubernetes control plane.

2. Run the following commands to retrieve the VictoriaMetrics connection details:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vminsert
    ```

3. Note the **External IP** of the `vminsert` LoadBalancer service.

4. Run the following command to extract the VictoriaMetrics TLS certificates:

    ```bash title="Run on K8s control plane"
    kubectl get secret -n telemetry vminsert-tls -o jsonpath='{.data.ca\.crt}' | base64 --decode > ca.crt
    kubectl get secret -n telemetry vminsert-tls -o jsonpath='{.data.tls\.crt}' | base64 --decode > tls.crt
    kubectl get secret -n telemetry vminsert-tls -o jsonpath='{.data.tls\.key}' | base64 --decode > tls.key
    ```

### Configure SFM Prometheus Remote Write

1. Log in to the SFM web UI.

2. Navigate to **Settings > Observability**.

    ![SFM Observability Settings](../../assets/images/sfm_observability_settings.png)

3. Select **Prometheus Remote Write** to configure remote write settings.

    ![SFM Prometheus Remote Write](../../assets/images/sfm_observability_settings_prometheus_remote_write.png)

4. Configure the remote write settings:

    - **Remote Write URL**: `https://<vminsert external IP>:8480/insert/0/prometheus/api/v1/write`
    - **Write Interval**: Set based on desired metric frequency

    ![SFM Remote Write Settings](../../assets/images/sfm_observability_remote_write_settings.png)

5. Upload the TLS certificates (`ca.crt`, `tls.crt`, `tls.key`) extracted in the previous step.

    ![SFM TLS Configuration](../../assets/images/sfm_observability_TLS_config.png)

6. Save and apply the configuration.

### Update /etc/hosts in the Kubernetes Prometheus Pod

After configuring the SFM remote write settings, update the `/etc/hosts` file in the Kubernetes Prometheus pod to ensure proper DNS resolution:

1. Identify the Prometheus pod:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry | grep prometheus
    ```

    ![Identify Prometheus Pod](../../assets/images/telemetry_sfm_identify_propmetheus_pod.png)

2. Access the Prometheus pod:

    ```bash title="Run on K8s control plane"
    kubectl exec -it -n telemetry <prometheus-pod-name> -- /bin/sh
    ```

    ![Prometheus Pod Shell](../../assets/images/telemetry_sfm_propmetheus_pod.png)

3. Add the vminsert entry to `/etc/hosts`:

    ```bash
    echo "<vminsert external IP> vminsert-victoria-cluster" >> /etc/hosts
    ```

    ![vminsert Hosts Entry](../../assets/images/telemetry_sfm_vminsert.png)


## Verification


For detailed SFM telemetry verification steps including VMUI queries and key metrics, see the SFM section in the [Telemetry Overview](setup_telemetry.md).


## Next Steps


- [Telemetry Overview](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
