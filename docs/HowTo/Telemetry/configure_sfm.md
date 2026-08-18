# Configure SFM (Smart Fabric Manager) Telemetry


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

| Category | Metrics Collected |
| --- | --- |
| Transceiver DOM | Optical power (TX/RX), temperature, voltage, bias current |
| Queue Statistics | Queue depth, egress queue counters, multicast queue counters |
| Interface Counters | Interface throughput (TX/RX bytes), packet counts, error counts, drop counts |
| Error Counters | CRC errors, alignment errors, symbol errors, FCS errors |

For the complete list of SFM telemetry metrics, see [SFM Metrics Reference](../../Reference/Metrics/sfm_metrics.md).


## Prerequisites


Complete the following before you configure SFM telemetry. You provision the
cluster first (which deploys VictoriaMetrics), then configure SFM to push metrics
to it via Prometheus Remote Write.

- The `omnia_core` container is deployed on the OIM. See
  [Deploy Omnia Core](../Setup/deploy_omnia_core.md).
- The mapping file (`pxe_mapping_file.csv`) is created. See
  [Create Mapping File](../Setup/create_mapping_file.md).
- SFM (Smart Fabric Manager) must be operational and accessible from the service
  Kubernetes cluster.
- Ensure that Secure Shell (SSH) is enabled on the SFM virtual machine. For detailed steps, see the [Smart Fabric Manager documentation](https://www.dell.com/support/manuals/en-in/smartfabric-manager-for-sonic/sfm-141-user-guide-pub/enable-secure-shell-access-for-admin-user?guid=guid-a381d8a7-2f41-42c5-b597-aa651321e588&lang=en-us){target="_blank"}.
- Ensure that `pod_external_ip_range` is set in `omnia_config.yml` for the Service Kubernetes cluster and is reachable from the SFM network.


## Procedure


### Step 1: Add Required Software to software_config.json

SFM streams metrics to VictoriaMetrics running on the service Kubernetes cluster.
Ensure the `service_k8s` entry is present in `software_config.json`. Include an
`aarch64` entry only if you have aarch64 nodes.

```json title="software_config.json -- required for SFM telemetry"
{
    "softwares": [
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]}
    ]
}
```

For the full file structure, see the
[software_config.json reference](../../Reference/Configuration/software_config.md).

### Step 2: Add Required Nodes to the Mapping File

SFM telemetry requires a service Kubernetes cluster with VictoriaMetrics exposed
over a MetalLB LoadBalancer. In `pxe_mapping_file.csv`, ensure the following
functional groups are present:

- `service_kube_control_plane` (three control plane nodes)
- `service_kube_node` (at least one worker node)

```csv title="pxe_mapping_file.csv -- example service K8s rows"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
service_kube_control_plane_x86_64,grp4,H94M8F3,,kcp1,BC:97:E1:F0:94:F0,172.16.107.96,b0:7b:25:d8:4a:f4,100.10.1.99,,
service_kube_control_plane_x86_64,grp5,2LXT933,,kcp2,BC:97:E1:F0:95:10,172.16.107.97,b0:7b:25:d8:4b:04,100.10.1.100,,
service_kube_control_plane_x86_64,grp7,8X697C3,,kcp3,BC:97:E1:F0:95:30,172.16.107.98,b0:7b:25:d8:4b:14,100.10.1.101,,
service_kube_node_x86_64,grp6,GZF6ZS3,,kn,EC:2A:72:32:C6:98,172.16.107.95,ec:2a:72:3b:a8:52,100.10.0.209,,
```

Ensure `pod_external_ip_range` is set in `omnia_config.yml` so MetalLB can assign
an external IP to the `vminsert` service. For the full mapping file format, see the
[PXE mapping file reference](../../Reference/SampleFiles/pxe_mapping_file.md).

### Step 3: Deploy the Cluster

Deploy the cluster by running the full playbook sequence
(`prepare_oim.yml` -> `local_repo.yml` -> `build_image` -> `provision.yml`).
`provision.yml` deploys VictoriaMetrics in the telemetry namespace. See
[Deploy the Telemetry Stack](deploy_telemetry.md).

Once the cluster is provisioned and VictoriaMetrics is running, configure SFM to
stream metrics to it using the following steps.

### Step 4: Retrieve VictoriaMetrics Connection Details

Run the following playbook to retrieve the VictoriaMetrics connection details and TLS certificate from the Service Kubernetes cluster:

```bash title="Run on omnia_core container"
cd /omnia/utils
ansible-playbook external_victoria_connect_details.yml
```

The `external_victoria_connect_details.yml` playbook does the following:

- Retrieves the VictoriaMetrics `vminsert` and `vmselect` LoadBalancer IPs.
- Extracts the server CA certificate for TLS.
- Writes the connection details to `/opt/omnia/telemetry/external_victoria_connect_details.yml`.
- Saves the CA certificate at `/opt/omnia/telemetry/victoria-certs/ca.crt`.

### Step 5: Configure SFM Prometheus Remote Write

1. In the Smart Fabric Manager for SONiC UI, navigate to **Observability**, and then select the **Settings** tab.

    ![SFM Observability Settings](../../assets/images/sfm_observability_settings.png)

2. Under **Prometheus Remote Write**, select the option button next to `vminsert-target`, and then select **Edit**.

3. Configure the following settings:

    - **Enable**: ON
    - **URL**: `https://vminsert-victoria-cluster.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write`
    - **Message Version**: v1
    - **TLS Config**: Upload `ca.crt` from `/opt/omnia/telemetry/Victoria-certs/` as the Server Certificate File

    !!! note

        If SFM is installed on a different system than the OIM host, copy `ca.crt` from `/opt/omnia/telemetry/Victoria-certs/` to that system before uploading it in the UI.

    ![SFM Prometheus Remote Write](../../assets/images/sfm_observability_settings_prometheus_remote_write.png)

    ![SFM Remote Write Settings](../../assets/images/sfm_observability_remote_write_settings.png)

    ![SFM TLS Configuration](../../assets/images/sfm_observability_TLS_config.png)

### Step 6: Update /etc/hosts in the SFM Prometheus Pod

Update the `/etc/hosts` file of the Kubernetes Prometheus pod in the SFM VM to resolve the VictoriaMetrics endpoint:

1. Log in to the SFM VM. Run the following command to connect using SSH with your admin credentials:

    ```bash
    ssh <admin_user>@<sfm_vm_ip>
    ```

2. From the **SFM - Main Menu**, enter **6** to select **Debug Menu**.

    ![SFM Main Menu](../../assets/images/telemetry_sfm_main_menu.png)

3. From the **Debug Menu**, enter **12** to select **Enter Secure Shell**. This opens a shell session on the SFM host VM.

    ![SFM Debug Menu](../../assets/images/telemetry_sfm_debug_menu.png)

4. Identify the Prometheus pod:

    ```bash
    kubectl get pods -A | grep prometheus
    ```

    ![Identify Prometheus Pod](../../assets/images/telemetry_sfm_identify_propmetheus_pod.png)

5. Inside the Prometheus pod, add the VictoriaMetrics insert LoadBalancer IP to `/etc/hosts`:

    ```bash
    kubectl exec -it -n <Prometheus Namespace> <Prometheus Pod Name> -- /bin/sh
    echo "<vminsert loadbalancer IP> vminsert-victoria-cluster.telemetry.svc.cluster.local" >> /etc/hosts
    ```

    ![Prometheus Pod Shell](../../assets/images/telemetry_sfm_propmetheus_pod.png)

    ![vminsert Hosts Entry](../../assets/images/telemetry_sfm_vminsert.png)


## Verification


### View SFM Telemetry Data in VictoriaMetrics UI (VMUI)

To view the SFM telemetry data streamed to VictoriaMetrics:

1. Verify that the VictoriaMetrics pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Pods](../../assets/images/victoria_metrics_pod_cluster_mode.png)

2. Verify that all VictoriaMetrics cluster services are running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Services](../../assets/images/victoria_metrics_service_cluster.png)

3. Note the **External IP** and **port number** of the `vmselect` service.

4. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

5. Filter and view telemetry metrics using queries in VMUI. For example, the following query displays transceiver DOM temperature values:

    ```
    transceiver_dom_temperature_value
    ```

    ![SFM DOM Temperature Metrics](../../assets/images/victoria_metrics_dom_temperature.png)

The following are some of the key metrics that can be queried:

| Metric | Description |
| --- | --- |
| `transceiver_dom_temperature_value` | Monitors optical transceiver temperature for hardware health |
| `queue_tx_pkts` | Tracks transmitted packets per queue for performance monitoring |
| `queue_drop_pkts` | Counts dropped packets per queue to identify congestion issues |
| `queue_tx_bits_per_second` | Measures queue throughput in bits per second |
| `ifcounters_in_octets` | Monitors incoming data volume in bytes per interface |
| `ifcounters_out_octets` | Monitors outgoing data volume in bytes per interface |
| `ifcounters_in_pkts` | Counts incoming packets per interface |
| `ifcounters_out_pkts` | Counts outgoing packets per interface |
| `ifcounters_in_errors` | Tracks input errors per interface for fault detection |
| `ifcounters_out_errors` | Tracks output errors per interface for fault detection |

For the complete list of SFM telemetry metrics, see [SFM Metrics Reference](../../Reference/Metrics/sfm_metrics.md).


## Next Steps


- [Setup Telemetry](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
