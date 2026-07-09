
# Configure PowerScale Telemetry


Configure deployment of PowerScale Telemetry to collect storage performance metrics and logs from Dell PowerScale storage nodes.

## Overview


PowerScale Telemetry collects storage performance metrics and logs. PowerScale Telemetry includes the following components:

### Components

- **CSM Metrics for PowerScale** -- Queries the OneFS API and emits metrics to an OpenTelemetry Collector.
- **OpenTelemetry Collector** -- Receives metrics from CSM Metrics and exposes a Prometheus endpoint for scraping.
- **vmagent** -- Scrapes the OpenTelemetry Collector Prometheus endpoint over TLS and forwards metrics to VictoriaMetrics.
- **VLAgent** -- Receives PowerScale syslog events and forwards them to VictoriaLogs.
- **CSI Driver for Dell PowerScale** -- Required for Omnia-orchestrated deployment mode.
- **cert-manager** -- Required for TLS certificate management in Omnia-orchestrated mode.

### Data Flow

```
PowerScale Nodes → CSM Metrics PowerScale → OTEL Collector → vmagent (shared) → VictoriaMetrics
PowerScale Nodes → syslog → VLAgent → VictoriaLogs
```

### Supported Metrics and Logs

**Metrics:**

- **Performance** -- Protocol-level IOPS (NFS, SMB, S3), throughput (bytes/s), read/write latency
- **Capacity** -- Total cluster capacity, used capacity, available capacity, per-node capacity
- **Health** -- Node online/offline status, disk health, cluster rebalance status, protection group status
- **Topology** -- Cluster node membership, node roles, interconnect layout, protection domain mapping

For more details on PowerScale metrics, see [Supported PowerScale Metrics](https://dell.github.io/csm-docs/docs/concepts/observability/metrics/powerscale/).

**Logs:**

- Capacity warnings, disk failures, node state changes, protocol errors
- Events are labeled with host/cluster, severity, and facility

### Health Monitor Metrics

When the CSI PowerScale health monitor is enabled (`controller > healthMonitor > enabled: true` and `node > healthMonitor > enabled: true` in the CSI PowerScale values.yaml), Omnia collects the following additional health metrics:

**PV Metrics:**

- `powerscale_volume_status` - PV phase (1=Bound, 0=Other) [pv_name, phase]
- `powerscale_volume_count` - Total PowerScale PVs by phase [phase]
- `powerscale_volume_capacity_bytes` - PV capacity in bytes [pv_name]
- `powerscale_volume_info` - PV metadata [pv_name, phase, storage_class, reclaim_policy, access_modes, volume_handle, pvc_name, pvc_namespace]
- `powerscale_volume_age_seconds` - Seconds since PV creation [pv_name]

**PVC Metrics:**

- `powerscale_pvc_status_phase` - PVC phase (1=Bound, 0=Other) [pvc_name, pvc_namespace, phase]
- `powerscale_pvc_requested_bytes` - PVC requested storage in bytes [pvc_name, pvc_namespace]
- `powerscale_pvc_count` - Total PowerScale PVCs by phase [phase]

**Health Event Metrics:**

- `powerscale_volume_health_abnormal` - Volume condition abnormal (1=abnormal, 0=healthy) [pvc_name, pvc_namespace, pv_name]
- `powerscale_volume_abnormal_events_total` - Total VolumeConditionAbnormal events [pvc_name, pvc_namespace]
- `powerscale_node_failure_events_total` - Total node failure events [node]

**Node Metrics:**

- `powerscale_node_ready` - Node Ready condition (1=True, 0=False) [node]

**Storage Class Metrics:**

- `powerscale_storageclass_info` - StorageClass metadata [storageclass, provisioner, reclaim_policy, volume_binding_mode, allow_volume_expansion]

**Aggregate Summary:**

- `powerscale_total_capacity_bytes` - Total capacity of all PowerScale PVs in bytes


## Prerequisites


- `provision.yml` has been executed successfully with `service_kube_control_plane` and `service_kube_node` in the mapping file.
- For Omnia-orchestrated mode, the service Kubernetes cluster has sufficient resources to run CSM Metrics, OpenTelemetry Collector, CSI Driver, and cert-manager.
- For operator-provided mode, the external OpenTelemetry Collector endpoint is accessible from the service cluster over TLS.
- Network connectivity between the PowerScale cluster and the Omnia log agent for syslog integration.

**For PowerScale log collection**, configure the following settings on the PowerScale cluster:

1. Enable syslog forwarding from PowerScale:

    ```bash title="Run on PowerScale CLI"
    isi audit setting modify --syslog-forwarding-enabled true
    ```

    ![PowerScale Syslog Prereq](../../assets/images/powerscale_syslog_logs_prereq.png)

2. Enable for required zones:

    ```bash title="Run on PowerScale CLI"
    isi audit settings global modify --add-audited-zones=<comma separated zone names>
    ```

3. Configure the VLAgent LoadBalancer IP address for log delivery:

    ```bash title="Run on PowerScale CLI"
    isi audit settings global modify --config-syslog-enabled=1 --config-syslog-servers=<vlagent loadbalancer ip>:514 --config-syslog-tls-enabled=0
    isi audit settings global modify --protocol-syslog-servers=<vlagent loadbalancer ip>:514 --protocol-syslog-tls-enabled=0
    isi audit settings global modify --system-syslog-enabled=1 --system-syslog-servers=<vlagent loadbalancer ip>:514 --system-syslog-tls-enabled=0
    ```

    ![PowerScale Audited Zones Prereq](../../assets/images/powerscale_audited_zones_logs_prereq.png)


## Procedure


1. **Specify the following entries in `software_config.json`**:

    !!! note

        The entry must be present when `telemetry_sources > powerscale > metrics_enabled` is set to `true` in the `telemetry_config.yml` file.

    ```json
    {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
    {"name": "csi_driver_powerscale", "version": "2.17.0", "arch": ["x86_64"]}
    ```

2. **Ensure that `telemetry_config.yml` has the entries specific for PowerScale Telemetry deployment**. For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

    ```yaml title="telemetry_config.yml -- PowerScale section"
    telemetry_sources:
      powerscale:
        metrics_enabled: true
        logs_enabled: true
        collection_targets:
          - "victoria_metrics"
          - "victoria_logs"

    powerscale_configurations:
      otel_collector_storage_size: "5Gi"
      csm_observability_values_file_path: ""
    ```

    - `metrics_enabled` -- Enable or disable PowerScale metric collection (`true` or `false`).
    - `logs_enabled` -- Enable or disable PowerScale log collection (`true` or `false`).
    - `collection_targets` -- Define where PowerScale data is sent. Supported values: `victoria_metrics`, `victoria_logs`.
    - `otel_collector_storage_size` -- Persistent storage size for the OpenTelemetry Collector.
    - `csm_observability_values_file_path` -- Path to the CSM Observability (Karavi) values.yaml file.

    !!! note

        PowerScale Telemetry supports independent feature flags for metric collection and log collection. You can enable or disable each independently.

3. **Configure the CSM Observability values file**:

    - Provide the path to the CSM Observability (Karavi Observability) values.yaml file in `telemetry_config.yml`.
    - Reference: `https://raw.githubusercontent.com/dell/helm-charts/refs/heads/release-v1.17.1/charts/karavi-observability/values.yaml`
    - **Important**: In the values.yaml file, only set `karaviMetricsPowerscale > enabled: true`. Set the following parameters to `false`: `karaviMetricsPowerflex > enabled`, `karaviMetricsPowerstore > enabled`, `karaviMetricsPowerscale.authorization > enabled`, `karaviMetricsPowermax > enabled`.
    - **Health Metrics**: For CSI PowerScale health metrics, enable `controller > healthMonitor > enabled: true` and `node > healthMonitor > enabled: true` in the [CSI PowerScale values.yaml](https://raw.githubusercontent.com/dell/helm-charts/csi-isilon-2.17.0/charts/csi-isilon/values.yaml).

    !!! note

        The karavi-metrics-powerscale pod may go into CrashLoopBackOff state when CSM is enabled with Basic authentication. To check the current authentication type on PowerScale:

        ```bash title="Run on PowerScale CLI"
        isi http settings view
        ```

        If Basic authentication is enabled, update the `isiAuthType` in the CSM Observability values.yaml file to use session-based authentication.

4. **(Optional) Configure dual-destination delivery**: Specify the external VictoriaMetrics endpoint in `telemetry_config.yml`. Metrics will be delivered to both the internal time-series database and the external endpoint independently.

!!! important

    If you enable PowerScale telemetry after the initial deployment, execute the `telemetry.sh` script on the K8s control plane:

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Enable and Disable PowerScale Telemetry


**To disable PowerScale telemetry:**

```bash title="Run on omnia_core container"
ansible-playbook telemetry/telemetry_disable.yml --tags powerscale
```

**To enable PowerScale telemetry again after disabling:**

```bash title="Run on omnia_core container"
ansible-playbook telemetry/telemetry_enable.yml --tags powerscale
```

!!! note

    - Set `powerscale.metrics_enabled` to `true` or `false` in the `telemetry_config.yml` file.
    - The `powerscale` tag is mandatory to perform the action.

**To disable PowerScale logs:**

```bash title="Run on PowerScale CLI"
isi audit settings global modify --config-syslog-enabled=0 --clear-config-syslog-servers
isi audit settings global modify --system-syslog-enabled=0 --clear-system-syslog-servers
isi audit settings global modify --clear-protocol-syslog-servers
isi audit setting modify --syslog-forwarding-enabled false
```

**To enable PowerScale logs again after disabling:**

```bash title="Run on PowerScale CLI"
isi audit setting modify --syslog-forwarding-enabled true
isi audit settings global modify --config-syslog-enabled=1 --config-syslog-servers=<vlagent loadbalancer ip>:514 --config-syslog-tls-enabled=0
isi audit settings global modify --protocol-syslog-servers=<vlagent loadbalancer ip>:514 --protocol-syslog-tls-enabled=0
isi audit settings global modify --system-syslog-enabled=1 --system-syslog-servers=<vlagent loadbalancer ip>:514 --system-syslog-tls-enabled=0
```


## Verification


### Verify PowerScale Telemetry Pods

1. Verify that the VictoriaMetrics pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Pods](../../assets/images/victoria_metrics_pod_cluster_mode.png)

2. Verify that the VictoriaMetrics service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Service](../../assets/images/victoria_metrics_service_cluster.png)


### View PowerScale Metrics in VictoriaMetrics UI (VMUI)

Use the VMUI to validate that PowerScale telemetry data is being collected and stored successfully.

1. Note the **External IP** and **port number** of the VictoriaMetrics service.

2. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

3. Filter and view telemetry metrics using queries in VMUI. For example, the following query displays detailed PowerScale metrics for each hardware component:

    ```
    {__name__=~"powerscale"}
    ```

    ![PowerScale Metrics in VMUI](../../assets/images/powerscale_metrics_vmui_cluster.png)

### View PowerScale Logs in VictoriaLogs

Use the VictoriaLogs UI to validate that PowerScale log data is being collected.

1. Verify that the VictoriaLogs pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -o wide | grep vl
    ```

    ![VictoriaLogs Pods](../../assets/images/victoria_logs_pod_cluster_mode.png)

2. Verify that the VictoriaLogs service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry -o wide | grep vl
    ```

    ![VictoriaLogs Service](../../assets/images/victoria_logs_service_cluster.png)

3. Note the **External IP** and **port number** of the VictoriaLogs service.

4. Access the VictoriaLogs UI in a web browser:

    ```
    https://<external vlselect loadbalancer IP>:9471/select/vmui
    ```

5. Filter and view PowerScale logs using queries in VictoriaLogs UI. For example, use the `*` query to display all logs.

    ![PowerScale Logs in VictoriaLogs UI](../../assets/images/powerscale_logs_vlui_cluster.png)


## Next Steps


- [Telemetry Overview](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
