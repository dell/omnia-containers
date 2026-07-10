# Configure Vector-LDMS Pipeline


Configure Vector-LDMS to consume LDMS metrics from the Kafka `ldms` topic, transform them to Prometheus format, and route to VictoriaMetrics.

## Overview


Vector-LDMS provides Kafka-to-VictoriaMetrics ingestion for LDMS telemetry data. The deployment includes the following components:

### Components

- **Vector-LDMS** -- Kafka consumer for LDMS metrics. Consumes from the `ldms` topic, transforms Avro-encoded LDMS data to Prometheus metric format, and routes to VictoriaMetrics via vmagent-vector.
- **vmagent-vector** -- Dedicated vmagent instance as a write-buffer between Vector pods and vminsert. Accepts `prometheus_remote_write` on port 8429, buffers to disk, and forwards to vminsert. Separate from the existing scraper vmagent to isolate failure domains.

For more details on Vector, see [Vector Documentation](https://vector.dev/docs/).

### Data Flow

```
LDMS Store (store_avro_kafka) → Kafka 'ldms' topic → Vector-LDMS → vmagent-vector → vminsert → VictoriaMetrics
```


## Prerequisites


Complete the following before you configure Vector-LDMS. Provisioning the cluster
happens **after** this configuration, as part of the deployment sequence.

- The `omnia_core` container is deployed on the OIM. See
  [Deploy Omnia Core](../Setup/deploy_omnia_core.md).
- The mapping file (`pxe_mapping_file.csv`) is created. See
  [Create Mapping File](../Setup/create_mapping_file.md).
- LDMS telemetry is configured. See [Configure LDMS Telemetry](configure_ldms.md).


## Procedure


### Step 1: Add Required Software to software_config.json

Ensure the `service_k8s` and `ldms` entries are present in `software_config.json`.
Include an `aarch64` entry only if you have aarch64 nodes.

```json title="software_config.json -- required for Vector-LDMS"
{
    "softwares": [
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
        {"name": "ldms", "arch": ["x86_64", "aarch64"]}
    ]
}
```

For the full file structure, see the
[software_config.json reference](../../Reference/Configuration/software_config.md).

### Step 2: Add Required Nodes to the Mapping File

The bridge runs on the service Kubernetes cluster. In `pxe_mapping_file.csv`,
ensure the following functional groups are present:

- `service_kube_control_plane` (three control plane nodes)
- `service_kube_node` (at least one worker node)

```text title="pxe_mapping_file.csv -- example service K8s rows"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
service_kube_control_plane_x86_64,grp4,H94M8F3,,kcp1,BC:97:E1:F0:94:F0,172.16.107.96,b0:7b:25:d8:4a:f4,100.10.1.99,,
service_kube_control_plane_x86_64,grp5,2LXT933,,kcp2,BC:97:E1:F0:95:10,172.16.107.97,b0:7b:25:d8:4b:04,100.10.1.100,,
service_kube_control_plane_x86_64,grp7,8X697C3,,kcp3,BC:97:E1:F0:95:30,172.16.107.98,b0:7b:25:d8:4b:14,100.10.1.101,,
service_kube_node_x86_64,grp6,GZF6ZS3,,kn,EC:2A:72:32:C6:98,172.16.107.95,ec:2a:72:3b:a8:52,100.10.0.209,,
```

For the full format, see the
[PXE mapping file reference](../../Reference/SampleFiles/pxe_mapping_file.md).

### Step 3: Enable Vector-LDMS in telemetry_config.yml

Configure `telemetry_config.yml` to enable Vector-LDMS:

```yaml title="telemetry_config.yml -- Vector-LDMS bridge"
telemetry_bridges:
  vector_ldms:
    metrics_enabled: true
```

For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

The following components are deployed when `vector_ldms > metrics_enabled = true`:

- **vmagent-vector** -- Dedicated vmagent instance for Vector write-buffer.
- **Vector-LDMS** -- Kafka consumer pod for LDMS metrics.

!!! note

    Vector-LDMS reuses the existing `kafkapump` KafkaUser for mTLS credentials.

### Step 4: Deploy the Cluster

Deploy the cluster by running the full playbook sequence
(`prepare_oim.yml` -> `local_repo.yml` -> `build_image` -> `provision.yml`).
`provision.yml` deploys the Vector-LDMS bridge and its vmagent-vector instance. See
[Deploy the Telemetry Stack](deploy_telemetry.md).

!!! important

    If you enable Vector-LDMS on an already-provisioned cluster, re-run `provision.yml` and then execute the `telemetry.sh` script on the K8s control plane. See [Update Telemetry on a Running Cluster](deploy_telemetry.md#update-telemetry-on-a-running-cluster).

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Verification


### Verify Vector-LDMS Telemetry Pods

1. Verify that the Vector-LDMS pod is running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry | grep vector-ldms
    ```

    ![Vector-LDMS Pod](../../assets/images/victoria_metrics_ldms_1.png)

2. Verify that the vmagent-vector pod is running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry | grep vmagent-vector
    ```

    ![vmagent-vector Pod](../../assets/images/victoria_metrics_ldms_2.png)

3. Verify that the VictoriaMetrics service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry | grep vm
    ```

    ![VictoriaMetrics Service](../../assets/images/victoria_metrics_ldms_3.png)

### View LDMS Metrics in VictoriaMetrics UI (VMUI)

1. Note the **External IP** and **port number** of the VictoriaMetrics service.

2. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

3. Verify that metrics are reaching VictoriaMetrics by querying the VMUI. For example, the following query displays LDMS-related metrics:

    ```
    {__name__=~"ldms_.*"}
    ```

    ![LDMS Metrics in VMUI](../../assets/images/victoria_metrics_ldms_ui_login.png)


## Next Steps


- [Configure LDMS](configure_ldms.md) -- Set up LDMS telemetry.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
