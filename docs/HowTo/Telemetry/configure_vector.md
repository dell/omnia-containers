# Configure Vector Telemetry Pipeline


Configure Vector as a high-performance data pipeline for routing telemetry data from Kafka to VictoriaMetrics and VictoriaLogs.

## Overview


Vector provides Kafka-to-Victoria ingestion for LDMS and OpenManage Enterprise (OME) sources.

For more details on Vector, see [Vector Documentation](https://vector.dev/docs/).

### Components

- **Vector-LDMS** -- Kafka consumer for LDMS metrics. Consumes from the `ldms` topic and routes to VictoriaMetrics via vmagent-vector.
- **Vector-OME** -- Kafka consumer for OME telemetry. Consumes from `ome.*` topics and routes metrics to VictoriaMetrics and logs to VictoriaLogs.
- **vmagent-vector** -- Dedicated vmagent instance as a write-buffer between Vector pods and vminsert. Accepts `prometheus_remote_write` on port 8429, buffers to disk, and forwards to vminsert. Separate from the existing scraper vmagent to isolate failure domains.
- **vlagent-vector** -- Dedicated VictoriaLogs forwarding agent deployed as a log write-buffer for Vector pods. Accepts JSON Lines on an HTTP endpoint (port 9427), buffers to disk, and forwards to vlinsert. Required for Vector-OME log/event sinks.

### Data Flow

```
LDMS Store (store_avro_kafka) → Kafka 'ldms' topic → Vector-LDMS → vmagent-vector → vminsert → VictoriaMetrics
OME → Kafka 'ome.*' topics → Vector-OME → vmagent-vector → vminsert → VictoriaMetrics
OME → Kafka 'ome.*' topics → Vector-OME → vlagent-vector → vlinsert → VictoriaLogs
```


## Prerequisites


Complete the following before you configure the Vector bridges. Provisioning the
cluster happens **after** this configuration, as part of the deployment sequence.

- The `omnia_core` container is deployed on the OIM. See
  [Deploy Omnia Core](../Setup/deploy_omnia_core.md).
- The mapping file (`pxe_mapping_file.csv`) is created. See
  [Create Mapping File](../Setup/create_mapping_file.md).
- The upstream source for each bridge is configured:
  [LDMS](configure_ldms.md) for Vector-LDMS, and
  [OpenManage Enterprise](telemetry_from_ome.md) for Vector-OME.


## Procedure


### Step 1: Add Required Software to software_config.json

The Vector bridges run on the service Kubernetes cluster. Ensure the `service_k8s`
entry is present in `software_config.json`. If it is missing, Omnia skips Vector
deployment and logs an informational message. Include an `aarch64` entry only if
you have aarch64 nodes.

```json title="software_config.json -- required for Vector bridges"
{
    "softwares": [
        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]}
    ]
}
```

For the full file structure, see the
[software_config.json reference](../../Reference/Configuration/software_config.md).

### Step 2: Add Required Nodes to the Mapping File

The Vector bridges require a service Kubernetes cluster. In `pxe_mapping_file.csv`,
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

### Step 3: Enable Vector Bridges in telemetry_config.yml

Configure the Vector telemetry bridges in `telemetry_config.yml`.

```yaml title="telemetry_config.yml -- Vector bridges"
telemetry_bridges:
  vector_ldms:
    metrics_enabled: true
  vector_ome:
    metrics_enabled: true
    logs_enabled: true
```

- Set `telemetry_bridges > vector_ldms > metrics_enabled` to enable Vector-LDMS.
- Set `telemetry_bridges > vector_ome > metrics_enabled` to enable Vector-OME metrics routing.
- Set `telemetry_bridges > vector_ome > logs_enabled` to enable Vector-OME log routing.

For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

The following components are deployed based on the configured feature flags:

- **vmagent-vector** -- Deployed when `vector_ome > metrics_enabled` or `vector_ldms > metrics_enabled` is set to `true`.
- **Vector-LDMS** -- Deployed when `telemetry_bridges > vector_ldms > metrics_enabled = true`.
- **Vector-OME** -- Deployed when `telemetry_bridges > vector_ome > metrics_enabled = true` or `telemetry_bridges > vector_ome > logs_enabled = true`.
- **vlagent-vector** -- Deployed when `telemetry_bridges > vector_ome > logs_enabled = true`.
- **Kafka topics and ACLs** -- For OME topics (deployed when Vector-OME is enabled).
- **KafkaUser resources** -- For Vector-OME mTLS credentials (deployed when Vector-OME is enabled).

!!! note

    Vector-LDMS reuses the existing `kafkapump` KafkaUser for mTLS credentials. Vector-OME requires a new KafkaUser (`vector-ome-user`) because OME is an external producer with a different security domain.

### Step 4: Verify the Upstream Data Sources

**For Vector-LDMS**, ensure that LDMS is configured and the `store_avro_kafka` plugin is producing to the Kafka `ldms` topic. Vector-LDMS consumes from this topic.

**For Vector-OME**, ensure that OME is configured externally and producing to Kafka `ome.*` topics via the external mTLS listener (port 9094). See [Configure OpenManage Enterprise Telemetry](telemetry_from_ome.md).

### Step 5: Deploy the Cluster

Deploy the cluster by running the full playbook sequence
(`prepare_oim.yml` -> `local_repo.yml` -> `build_image` -> `provision.yml`).
`provision.yml` deploys the enabled Vector bridges and their supporting
vmagent-vector/vlagent-vector instances. See
[Deploy the Telemetry Stack](deploy_telemetry.md).

!!! important

    If you enable Vector bridges on an already-provisioned cluster, re-run `provision.yml` and then execute the `telemetry.sh` script on the K8s control plane. See [Update Telemetry on a Running Cluster](deploy_telemetry.md#update-telemetry-on-a-running-cluster).

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Verification


For detailed verification steps including Vector-LDMS pod checks, vmagent-vector logs, and VMUI queries, see [Verify Telemetry - LDMS Flow](verify_telemetry.md#verify-ldms-telemetry-flow) and [Verify Telemetry - OME Flow](verify_telemetry.md#verify-ome-telemetry-flow).


## Next Steps


- [Configure LDMS](configure_ldms.md) -- Set up LDMS telemetry.
- [Configure OpenManage Enterprise Telemetry](telemetry_from_ome.md) -- Integrate OME with Kafka.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
