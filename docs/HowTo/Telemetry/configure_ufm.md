
# Configure UFM (NVIDIA Unified Fabric Manager) Telemetry


Configure NVIDIA Unified Fabric Manager (UFM) to securely stream telemetry metrics and logs to the Service Kubernetes cluster.

## Overview


UFM Telemetry collects InfiniBand fabric metrics and logs. UFM Telemetry includes the following components:

### Components

- **UFM Prometheus Exporter** -- Exposes InfiniBand fabric metrics on a Prometheus-compatible HTTPS endpoint (default port 9001).
- **vmagent (shared)** -- Scrapes the UFM Prometheus exporter endpoint over TLS and forwards metrics to VictoriaMetrics.
- **VMServiceScrape CR** -- Kubernetes custom resource that declares the UFM scrape target for the VictoriaMetrics operator.
- **VLAgent** -- Receives UFM syslog events (RFC 3164/5424) and forwards them to VictoriaLogs.
- **Kubernetes Service + Endpoints** -- Abstracts the external UFM appliance as a discoverable Kubernetes service for vmagent.

### Data Flow

```
UFM Fabric Manager → OTEL Collector → vmagent (shared) → VictoriaMetrics
UFM Fabric Manager → syslog → VLAgent → VictoriaLogs
```

### Supported Metrics and Logs

**Metrics:**

| Category | Metrics Collected |
| --- | --- |
| Port State | InfiniBand port operational state (up, down, disabled) |
| Traffic Counters | Transmit/receive data rates (bytes/sec), packet counts per port |
| Error Counters | Symbol errors, link error recovery, link downed, VL15 dropped, excessive buffer overrun errors |
| Fabric Topology | Switch information, port mapping, node GUIDs, LID assignments |
| Telemetry Health | Scrape success rate, scrape duration, ingest latency |

For the complete list of UFM telemetry metrics, see [UFM Metrics Reference](../../Reference/Metrics/ufm_metrics.md).

**Logs:**

| Category | Logs Collected |
| --- | --- |
| Fabric Events | Fabric topology change events, port state transitions, error/warning messages |
| Manager Events | SM (Subnet Manager) events, SHARP events, UFM health events |
| Labels | Events are labeled with hostname, severity, and facility |

!!! note

    UFM Telemetry supports independent feature flags for metric collection and log collection. You can enable or disable each independently.


## Prerequisites


Complete the following before you configure UFM telemetry. Provisioning the
cluster happens **after** this configuration, as part of the deployment sequence.

- The `omnia_core` container is deployed on the OIM. See
  [Deploy Omnia Core](../Setup/deploy_omnia_core.md).
- The mapping file (`pxe_mapping_file.csv`) is created. See
  [Create Mapping File](../Setup/create_mapping_file.md).
- Ensure that `provision.yml` has been executed successfully with
  `service_kube_control_plane` and `service_kube_node` in the mapping file.
- Ensure the service Kubernetes cluster has sufficient resources to run vmagent (shared instance) and VLAgent.
- Network connectivity between the service Kubernetes cluster and the NVIDIA UFM appliance.
- A running NVIDIA UFM appliance (Omnia does not deploy UFM itself).
- Ensure that `telemetry_config.yml` has UFM telemetry entries enabled. For details on configuring `telemetry_config.yml`, see the telemetry configuration reference.
- UFM telemetry must bind and listen on a specific designated IP address rather than the default localhost (127.0.0.1).
- The following ports must be allowed through the firewalld service on the UFM appliance: 9000, 9001, and 9002. Ensure the necessary firewall rules are created and enabled before deployment.
- UFM must be deployed with self-signed SSL/TLS certificates and configured to listen on a specific IP address and designated port for secure communication.


## Procedure


### Step 1: Add Required Software to software_config.json

UFM telemetry runs on the service Kubernetes cluster (Omnia configures the shared
vmagent to scrape the UFM Prometheus endpoint). Ensure the `service_k8s` entry is
present in `software_config.json`. Include an `aarch64` entry only if you have
aarch64 nodes.

```json title="software_config.json -- required for UFM telemetry"
{
    "softwares": [
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]}
    ]
}
```

For the full file structure, see the
[software_config.json reference](../../Reference/Configuration/software_config.md).

### Step 2: Add Required Nodes to the Mapping File

UFM telemetry requires a service Kubernetes cluster. In `pxe_mapping_file.csv`,
ensure the following functional groups are present:

- `service_kube_control_plane` (three control plane nodes)
- `service_kube_node` (at least one worker node)

```csv title="pxe_mapping_file.csv -- example service K8s rows"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
service_kube_control_plane_x86_64,grp4,H94M8F3,,kcp1,BC:97:E1:F0:94:F0,172.16.107.96,b0:7b:25:d8:4a:f4,100.10.1.99,,
service_kube_control_plane_x86_64,grp5,2LXT933,,kcp2,BC:97:E1:F0:95:10,172.16.107.97,b0:7b:25:d8:4b:04,100.10.1.100,,
service_kube_control_plane_x86_64,grp7,8X697C3,,kcp3,BC:97:E1:F0:95:30,172.16.107.98,b0:7b:25:d8:4b:14,100.10.1.101,,
service_kube_node_x86_64,grp6,GZF6ZS3,,kn,EC:2A:72:32:C6:98,172.16.107.95,ec:2a:72:3b:a8:52,100.10.0.209,,
```

For the full format, see the
[PXE mapping file reference](../../Reference/SampleFiles/pxe_mapping_file.md).

### Step 3: Configure the UFM Appliance

Enable UFM Telemetry in the `gv.cfg` configuration file on the UFM appliance:

```ini
[Telemetry]
telemetry_provider = telemetry
```

**(Optional) Configure SSL certificates** -- If using CA-signed TLS, set up SSL and CA certificates in UFM. For detailed steps, see [Setting Up SSL and CA Certificates in UFM](https://docs.nvidia.com/networking/display/ufmenterpriseumv6242/optional-configurations).

### Step 4: Configure UFM Log Forwarding

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

### Step 5: Enable UFM in telemetry_config.yml

Configure the UFM telemetry settings in `telemetry_config.yml`. For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

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

| Parameter | Description |
| --- | --- |
| `metrics_enabled` | Enable or disable UFM metric collection (`true` or `false`) |
| `logs_enabled` | Enable or disable UFM log collection (`true` or `false`) |
| `collection_targets` | Where UFM data is sent. Supported: `victoria_metrics`, `victoria_logs` |
| `ufm_endpoint` | IP address or hostname of the UFM appliance |
| `ufm_metrics_port` | Port for the UFM Prometheus exporter (default: `9001`) |
| `scrape_interval` / `scrape_timeout` | How often and how long to scrape UFM metrics |
| `tls_mode` | TLS verification mode: `self_signed` or `ca_signed` |
| `ufm_ca_cert_path` | Path to the CA certificate (required when `tls_mode` is `ca_signed`) |
| `auth_mode` | Authentication mode for UFM API: `basic` |

### Step 6: Deploy the Cluster

Deploy the cluster by running the full playbook sequence
(`prepare_oim.yml` -> `local_repo.yml` -> `build_image` -> `provision.yml`).
`provision.yml` configures the shared vmagent to scrape the UFM Prometheus
endpoint. See [Deploy the Telemetry Stack](deploy_telemetry.md).

!!! important

    If you enable UFM telemetry on an already-provisioned cluster, re-run `provision.yml` and then execute the `telemetry.sh` script on the K8s control plane. See [Update Telemetry on a Running Cluster](deploy_telemetry.md#update-telemetry-on-a-running-cluster).

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

    ```infiniband_CBW
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


- [Setup Telemetry](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
